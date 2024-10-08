from urllib.parse import urlencode
from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.db.models.functions import Trunc
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Case, When, Q, Count
from django.db.utils import IntegrityError, DataError
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic, View
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.generic.edit import FormMixin, FormView
from django.utils.encoding import force_bytes, force_str
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from itertools import chain

from .forms import *
from .utils import send_email
from PIL import Image
# import modules
from .modules.metadata_extraction.file_processing import extract_metadata, determine_type
from .modules.search.helpers import SearchMixin
from .modules.computer_vision.blur_image import blur_image, unblur_image
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm
from datetime import datetime
import logging
from django.conf import settings

from django_q.tasks import async_task
from .tasks import create_tagboxes_and_save, generate_preview_and_save, generate_image_embedding_and_save


console_logger = logging.getLogger('ARCH_console_logger')
file_logger = logging.getLogger('ARCH_file_logger')
PAGINATE_BY = 20


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.pk) + str(timestamp) +
                str(user.is_active)
        )


account_activation_token = TokenGenerator()


class IndexView(generic.TemplateView):
    template_name = 'arch_app/home.html'


class CustomLoginView(LoginView):
    """
    Login view
    handles data restoration for hidden users (sets visible to True and shows comments, tags, blurred images)
    tracks the login of the user.
    """

    def form_valid(self, form):
        user = form.get_user()

        if not user.visible:
            # if user is hidden, restore hidden data
            user.visible = True
            user.save()
            for comment in Comment.objects.filter(user=user):
                if comment.visible == 'hidden_by_user':
                    comment.visible = 'visible'
                    comment.save()
            for tagbox in TagBox.objects.filter(user=user):
                if tagbox.visible == 'hidden_by_user':
                    unblur_image(
                        image_path=tagbox.record.preview_file.path,
                        original_file_path=tagbox.record.media_file.path,
                        coordinates=(tagbox.x1, tagbox.y1, tagbox.x2, tagbox.y2))
            for tag in Tag.objects.filter(user=user):
                if tag.visible == 'hidden_by_user':
                    tag.visible = 'visible'
                    tag.save()
            messages.success(self.request, _('Your data was successfully restored and made visible again.'))

        Tracker.objects.create_from_request(request=self.request, content_object=user, user=user)
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """
    View for changing the password of a user.
    """
    template_name = './arch_app/forms/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        # send email to user notifying them that their password has been changed
        user = self.request.user
        email_status = send_email(user.email,
                                  subject='Password Changed',
                                  html_message=render_to_string('arch_app/emails/password_changed_email.html',
                                                                {'user': user,
                                                                 'hostname': self.request.META['HTTP_HOST']}),
                                  )
        if email_status:
            messages.success(self.request, _('Your password has been successfully changed.'))
        else:
            messages.error(self.request,
                           _('An error occurred while sending the email. Please Contact the Administrator.'))

        return super().form_valid(form)


class ActivateAccountView(View):
    """
    View for activating a user account.
    checks if the activation link is valid and activates the user account.
    """

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            # send email to user notifying them that their account has been activated
            email_status = send_email(user.email,
                                      subject='Welcome to ARCH!',
                                      html_message=render_to_string('registration/welcome_email.html',
                                                                    {'user': user}
                                                                    ),
                                      )
            if email_status:
                messages.success(request, _('Your account has been activated! You can now log in.'))
            else:
                messages.error(request,
                               _('An error occurred while sending the email. Please Contact the Administrator.'))
            return redirect('login')

        else:
            return HttpResponse('Activation link is invalid!')


class CreateAddMemberView(LoginRequiredMixin, generic.TemplateView):
    """
    View for creating a new user and/or adding a user to an archive from the members page
    """
    template_name = 'arch_app/forms/create_add_member_form.html'

    @staticmethod
    def generate_html_message(user, password, request):
        """
        Generate the HTML message for the activation email.
        Creates a token for the activation link and builds the activation URL.

        :param user: the user object
        :param password: the password of the user
        :param request: the request object
        :return: the HTML message
        """
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        domain = get_current_site(request).domain
        activation_url = reverse('arch_app:activate', kwargs={'uidb64': uid, 'token': token})
        activation_link = f'http://{domain}{activation_url}'  # must be http

        html_message = render_to_string('registration/activation_email.html', {
            'user': user,
            'activation_link': activation_link,
            'password': password,

        })
        return html_message

    def post(self, request, *args, **kwargs):
        """
        Post method for creating a new user or adding an existing user to an archive.
        checks if the user has permission to add members to the archive and handles the form submission.
        """

        if not request.user.has_perm('is_moderator', Archive.objects.get(id=request.POST['archive'])):
            messages.error(request, _('You do not have permission to add members to this archive.'))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        add_member_form = AddMemberForm(request.POST)
        if add_member_form.is_valid():
            cleaned_data = add_member_form.cleaned_data

            if User.objects.filter(username=cleaned_data['username'], email=cleaned_data['email']).exists():
                # create membership for existing user
                user = User.objects.get(username=cleaned_data['username'], email=cleaned_data['email'])
                archive = Archive.objects.get(id=request.POST['archive'])
                # check if membership with this role already exists
                membership, created = Membership.objects.get_or_create(user=user,
                                                                       archive=archive,
                                                                       role=cleaned_data['role'])
                if created:
                    messages.success(request, _('An existing user with the given username and email was added.'))
                else:
                    messages.warning(request,
                                     _('An existing user with the given username and email is already a member of this group.'))

            else:
                # check if username or email are already taken
                if User.objects.filter(username=cleaned_data['username']).exists():
                    messages.warning(request, _('Username is already taken.'))
                    return redirect(request.META.get('HTTP_REFERER'))
                if User.objects.filter(email=cleaned_data['email']).exists():
                    messages.warning(request, _('Email is already taken.'))
                    return redirect(request.META.get('HTTP_REFERER'))

                # create new user and membership
                password = User.objects.make_random_password()
                user = User.objects.create_user(username=cleaned_data['username'],
                                                email=cleaned_data['email'],
                                                password=password,
                                                is_active=False)
                membership = Membership.objects.create(user=user,
                                                       archive=Archive.objects.get(
                                                           id=request.POST['archive']),
                                                       role=cleaned_data['role']
                                                       )
                # send activation email to user
                html_message = CreateAddMemberView.generate_html_message(user=user, password=password,
                                                                         request=self.request)
                email_status = send_email(user.email,
                                          subject='Activate Your Account',
                                          html_message=html_message,
                                          )
                if email_status:
                    messages.success(request,
                                     _('User was created successfully. An email with an activation link was sent to the user.'))
                else:
                    messages.error(request,
                                   _('An error occurred while sending the email. Please Contact the Administrator.'))
            return redirect(request.META.get('HTTP_REFERER'))

        else:  # form is not valid
            return redirect(request.META.get('HTTP_REFERER'))


class FileUploadView(LoginRequiredMixin, FormMixin, generic.TemplateView):
    """
    View for uploading files to an archive.
    """
    template_name = 'arch_app/forms/file_upload_form.html'
    form_class = FileUploadForm
    success_message = _("Upload was successful.")

    def get_success_url(self):
        # redirect to Inbox
        archive = Archive.objects.get(id=self.kwargs['archive_id'])
        return reverse('arch_app:album', kwargs={"pk": str(archive.inbox.id)})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        archive = Archive.objects.get(id=self.kwargs['archive_id'])
        context['archive'] = archive

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle file upload and file processing.
        """
        form = self.get_form()

        if form.is_valid():
            files = self.request.FILES.getlist('files')
            for file in files:
                with (file.open() as f):
                    # process file
                    file_read = f.read()

                    # step 1: determine type
                    mime_type, subtype, file_extension = determine_type(file_read, f.name)

                    # step 2: extract meta data (e.g. location from EXIF)
                    metadata = extract_metadata(f)

                    # step 3: create record instance
                    record = None
                    try:
                        record = Record.objects.create_record(
                            media_type=mime_type.capitalize(),
                            title=f.name.split('.' + file_extension)[0],
                            album=Archive.objects.get(id=self.kwargs['archive_id']).inbox,
                            creator=self.request.user,
                            file_read=file_read,
                            file_name=f.name,
                            date_created=metadata['date_created']
                        )
                        # add location if available
                        if metadata['location']:
                            location = metadata['location']
                            record.location = Location.objects.create(
                                name=location['name'],
                                country=location['cc'],
                                country_code=location['cc'],
                                state=location['admin1'],
                                region=location['admin2'],
                                latitude=location['lat'],
                                longitude=location['lon']
                            )
                            record.location.save()
                            record.save()
                    except DataError:
                        message = _("The file could not be uploaded. Please check if the file name is too long: ")
                        message += f.name
                        messages.error(request, message)
                        continue

                    if not record:
                        message = _(f"File could not be uploaded: ")
                        message += f.name
                        messages.error(request, message)
                        continue
                    # step 4: add permissions
                    # for the creator
                    assign_perm('view_record', request.user, record)
                    assign_perm('change_record', request.user, record)
                    assign_perm('delete_record', request.user, record)
                    # for moderators
                    assign_perm('view_record', record.album.archive.moderators, record)
                    assign_perm('change_record', record.album.archive.moderators, record)
                    assign_perm('delete_record', record.album.archive.moderators, record)

                    # step 5: generate image dense vector representation if AI search is activated
                    if mime_type == 'image' and settings.ACTIVATE_AI_SEARCH:
                        async_task(generate_image_embedding_and_save, record.id, sync=True)
                        # Note: This only works synchronously, because the model is loaded in the task

                    # step 6: generate preview file
                    async_task(generate_preview_and_save, record.id, file_extension, mime_type, subtype)

                    # step 7: detect faces
                    if mime_type == 'image' and file_extension in ['jpg', 'jpeg', 'png', 'PNG', 'JPG'] \
                            and settings.ACTIVATE_FACE_DETECTION:
                        async_task(create_tagboxes_and_save, record.id)
            return self.form_valid(form)

        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        return super(FileUploadView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("The file could not be uploaded."))
        return super(FileUploadView, self).form_invalid(form)


class ArchiveDetailView(LoginRequiredMixin, generic.DetailView):
    """
    View for displaying the details of an archive.
    """
    model = Archive
    template_name = 'arch_app/partials/archive_home.html'

    def get(self, request, *args, **kwargs):
        """ Get method for the archive detail view,
        checks if user has permission to view the archive and tracks the access to the archive
        """
        archive = Archive.objects.get(id=self.kwargs['pk'])
        if not request.user.has_perm('view_archive', archive):
            messages.error(request, _('You do not have permission to view this page.'))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        Tracker.objects.create_from_request(request=self.request, content_object=archive, user=request.user)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """ Post method for the archive detail view,
        checks if user is a moderator and handles the form submission for the archive form
        """
        archive = get_object_or_404(Archive, id=self.kwargs['pk'])
        if not self.request.user.has_perm('is_moderator', archive):
            messages.error(request, _("You are not allowed to apply these changes."))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        archive_form = ArchiveForm(request.POST, request.FILES, instance=archive)
        if archive_form.is_valid():
            archive_form.save()
            messages.success(request, _("Changes were saved successfully."))
        else:
            messages.error(request, _("Changes could not be saved."))
        return redirect('arch_app:archive', archive_name=archive.name, pk=archive.id)


class MembersViews(LoginRequiredMixin, generic.ListView):
    model = Membership
    template_name = 'arch_app/members.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        archive = Archive.objects.get(id=self.kwargs['pk'])
        context['archive'] = archive
        return context

    def get_queryset(self):
        archive = Archive.objects.get(id=self.kwargs['pk'])

        # check if user has is_moderator permission in this archive
        if self.request.user.has_perm('is_moderator', archive):
            # return all members of this archive
            return Membership.objects.filter(archive=archive).order_by("-start_date")
        else:
            all_memberships = Membership.objects.filter(archive=self.kwargs['pk'])
            user_memberships = [m for m in all_memberships if m.user == self.request.user]
            memberships = Membership.objects.none()
            for um in user_memberships:
                # filter memberships for the timespan to be within the timespan of the user_membership
                for m in all_memberships:
                    if (um.end_date and m.start_date <= um.end_date) or (m.end_date and m.end_date >= um.start_date):
                        # add membership to memberships
                        memberships |= Membership.objects.filter(id=m.id)

            return Membership.objects.filter(archive=archive).order_by("-start_date")

    def get(self, request, *args, **kwargs):
        """
        Get method for the members view.
        Checks if the user has permission to view the members of the archive.
        """
        archive = Archive.objects.get(id=self.kwargs['pk'])
        if not request.user.has_perm('view_archive', archive):
            messages.error(request, _('You do not have permission to view this page.'))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return super().get(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    """
    View for displaying the profile of the currently logged-in user
    """
    template_name = 'arch_app/forms/profile_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['profile_form'] = ProfileForm(instance=self.request.user)
        context['profile_picture_form'] = ProfilePictureForm(instance=self.request.user)
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # check which form was submitted
        if request.POST['action'] == 'profilePicture':
            profile_picture_form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
            if profile_picture_form.is_valid():
                profile_picture_form.save()
                messages.success(request, _('Your profile picture was successfully saved!'))
                return HttpResponseRedirect(reverse('arch_app:profile'))

            messages.error(request, _('Could not be saved. Please try again.'))
            return HttpResponseRedirect(reverse('arch_app:profile'))

        elif request.POST['action'] == 'Delete':
            # delete profile picture
            request.user.profile_picture.delete()
            messages.success(request, _('Your profile picture was successfully deleted!'))
            return HttpResponseRedirect(reverse('arch_app:profile'))

        else:
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _('Your profile was successfully saved!'))
                return HttpResponseRedirect(reverse('arch_app:profile'))

            messages.error(request, _('Could not be saved. Please try again.'))
            return HttpResponseRedirect(reverse('arch_app:profile'))


class PrivacySettingsView(LoginRequiredMixin, generic.TemplateView):
    """
    View for displaying the privacy settings of the currently logged-in user
    """
    template_name = 'arch_app/partials/privacy_settings.html'


class RecordUpdateView(LoginRequiredMixin, View):
    """
    View for updating the album of a record object.
    handles Drag and Drop and form submission
    """

    def post(self, request, *args, **kwargs):
        """
        Post method for updating the album of a record object.
        checks if the user has permission to update the record and updates the album of the record.
        """
        # check if the request is an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            response = JsonResponse({'success': True})
            album = get_object_or_404(Album, id=self.request.POST['album_id'])
        else:
            try:
                response = redirect(request.META.get('HTTP_REFERER'))
            except TypeError:
                response = redirect(reverse('arch_app:record', kwargs={'pk': self.request.POST['record_id']}))
            album = get_object_or_404(Album, id=self.request.POST['album'])

        record_id = self.request.POST['record_id']
        record = get_object_or_404(Record, id=record_id)

        if not request.user.has_perm('is_moderator', album.archive) or \
                not request.user.has_perm('is_moderator', record.album.archive):
            messages.error(request, _('You do not have the permission to add this record to this Album.'))
            return response

        if record.album.id == album.id:
            messages.error(request, _('This record is already in this album.'))
            return response

        # remove permissions from the old album group, update the album of the record and save
        remove_perm('view_record', record.album.group, record)
        record.album = album
        record.save()
        # add permissions to the album group
        assign_perm('view_record', album.group, record)

        # update nav_ctx (remove record from nav_ctx)
        if 'nav_ctx' in self.request.session:
            nav_ctx = self.request.session.get('nav_ctx', [])
            if record_id in nav_ctx:
                nav_ctx.remove(record_id)
                self.request.session['nav_ctx'] = nav_ctx
        return response


class RecordView(LoginRequiredMixin, generic.TemplateView):
    """
    Handles the get and post request for a single record object.
    Handles updating the details of the record and adding comments.
    """
    template_name = 'arch_app/record.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_record = get_object_or_404(Record, id=self.kwargs['pk'])
        if 'nav_ctx' in self.request.session:
            if self.request.session['nav_ctx']:
                try:
                    index = self.request.session['nav_ctx'].index(str(current_record.id))
                except ValueError:
                    # the record is not in the nav_ctx
                    index = None

                if index is not None:
                    context['current_page'] = index // PAGINATE_BY + 1
                    # this is to prevent the index to take the last item in case the current record is the first one
                    if index == 0:
                        context['prev_record'] = None
                    else:
                        try:
                            context['prev_record'] = Record.objects.get(id=self.request.session['nav_ctx'][index - 1])
                        except IndexError:
                            context['prev_record'] = None
                    try:
                        context['next_record'] = Record.objects.get(id=self.request.session['nav_ctx'][index + 1])
                    except IndexError:
                        context['next_record'] = None

        context['record_form'] = RecordForm(instance=current_record)
        context['location_form'] = LocationForm(instance=current_record.location)
        context['comment_form'] = CommentForm()
        context['archive'] = current_record.album.archive
        context['album'] = current_record.album
        context['record'] = current_record
        context['album_mode'] = self.request.GET.get('album_mode')

        return context

    def get(self, request, *args, **kwargs):
        """
        Get method for the record view.
        Checks if the user has permission to view the record and tracks the access to the record.
        """
        record = Record.objects.get(id=self.kwargs['pk'])
        if not request.user.has_perm('view_record', record):
            messages.error(request, _('You do not have permission to view this record.'))
            return HttpResponseRedirect(reverse('arch_app:search'))
        # track access to record
        Tracker.objects.create_from_request(request=request, content_object=record, user=request.user)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Post method for the record view.
        Handles updating the record details and adding new comments.
        """
        record = Record.objects.get(id=self.kwargs['pk'])

        if request.POST['action'] == 'comment':
            if not request.user.has_perm('view_record', record):
                messages.error(request, _('You do not have permission to comment on this record.'))
                return HttpResponseRedirect(reverse('arch_app:record', kwargs=self.kwargs))
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.record = record
                if settings.HIDE_COMMENTS:
                    comment.visible = 'hidden_by_mod'
                comment.save()
            else:
                messages.error(request, _('Comment could not be posted.'))

        elif request.POST['action'] == 'save':
            if not request.user.has_perm('is_moderator', record.album.archive) and \
                    not request.user.has_perm('change_record', record):
                messages.error(request, _('You do not have permission to edit this record.'))
                return HttpResponseRedirect(reverse('arch_app:record', kwargs=self.kwargs))
            record_form = RecordForm(request.POST, request.FILES, instance=record)
            location_form = LocationForm(request.POST, instance=record.location)
            if record_form.is_valid() and location_form.is_valid():
                record = record_form.save(commit=False)
                record.location = location_form.save()
                record.save()
                messages.success(request, _('Record was saved!'))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.error(request, _('Record could not be saved. Please try again.'))
                # add (the form) error messages to the messages framework
                for field, error in record_form.errors.items():
                    for e in error:
                        messages.error(request, e)

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def delete_record(request, pk):
    """ View for deleting a record """
    record_id = None  # store the id of the previous record in the navigation context
    record = Record.objects.get(id=pk)
    # check permissions
    if not request.user.has_perm('delete_record', record):
        messages.error(request, _('You do not have the permission to delete this record.'))
        # redirect where the user came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # store album of the record in case we need to redirect there
    album = record.album
    try:
        record.delete()
    except Exception as e:
        console_logger.error(e)
        file_logger.error(e)
        messages.error(request, _('Record could not be deleted.'))

    # update the navigation context when deleting a record
    nav_ctx = request.session.get('nav_ctx')
    if nav_ctx:
        index = nav_ctx.index(str(pk))
        if index == 0:
            pass
        else:
            try:
                record_id = request.session['nav_ctx'][index - 1]
            except IndexError:
                pass
        request.session['nav_ctx'].remove(str(pk))
        request.session.modified = True
    else:
        index = None

    messages.success(request, _('Record was deleted.'))

    # check if user came from record or search or album page
    if 'HTTP_REFERER' in request.META:
        album_mode = request.GET.get('album_mode') == "True"
        # if record was deleted from record page, redirect to previous record
        if 'record' in request.META['HTTP_REFERER']:
            if record_id:  # if there is still a record in the nav_ctx, redirect to the previous record
                return redirect(reverse('arch_app:record', kwargs={'pk': record_id}) +
                                '?album_mode=' + str(album_mode))
            elif album_mode:  # else, redirect to album or search
                return redirect(reverse('arch_app:album', kwargs={'pk': album.id}))
            else:
                return redirect(reverse('arch_app:search'))
        # if record was deleted from album or search page, redirect to album or search with the same page
        else:
            # get page based on the index of the previous record in the nav_ctx
            page = index // PAGINATE_BY + 1 if index else 1
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') + "&page=" + str(page))
    # default: redirect to search
    return redirect(reverse('arch_app:search'))


@login_required
def hide_comment(request, pk):
    """ View for hiding or showing a comment """
    comment = Comment.objects.get(id=pk)
    if not request.user.has_perm('is_moderator', comment.record.album.archive):
        messages.error(request, _('You do not have permission to hide this comment.'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    # toggle the visible attribute of the comment
    if comment.visible == "visible":
        comment.visible = "hidden_by_mod"
    elif comment.visible == "hidden_by_mod":
        comment.visible = "visible"
    else:
        messages.error(request, _('Cannot change visibility.'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    comment.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class SearchView(LoginRequiredMixin, SearchMixin, generic.ListView):
    """
    Handles the search request and displays the current navigation context
    """
    model = Record
    template_name = 'arch_app/search.html'
    paginate_by = PAGINATE_BY
    cache_form = False

    def get(self, request, *args, **kwargs):
        """
        Get method for the search view.

        """
        if 'nav_ctx' in self.request.session:
            if self.request.session['nav_ctx']:
                nav_ctx = self.request.session['nav_ctx']
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(nav_ctx)])
                # create a queryset of the current navigation context and filter by permissions
                self.search_results = get_objects_for_user(self.request.user,
                                                           "view_record",
                                                           Record.objects.filter(pk__in=nav_ctx)) \
                    .order_by(preserved)
                self.request.session['nav_ctx'] = [str(i.id) for i in self.search_results]
                paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
                # check if the page is out of range. If so, redirect to the last page
                if paginator.num_pages < int(self.request.GET.get('page', 1)):
                    # redirect to the last page
                    return redirect(reverse('arch_app:search', kwargs={}) + '?page=' + str(
                        paginator.num_pages))
                return super().get(request, *args, **kwargs)

        # empty nv_ctx
        self.search_results = Record.objects.none()
        if 'page' in self.request.GET:
            self.object_list = self.get_queryset()
            page = self.request.GET['page']
            paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
            try:
                # obtain page using the paginator
                record_list = paginator.page(page)
            except PageNotAnInteger:
                # if page is not an integer, defaults to first page
                record_list = paginator.page(1)
            except EmptyPage:
                # if page is out of range, defaults to the last page
                return redirect(reverse('arch_app:search'))

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Post method for the search view.
        Handles the search request and redirects to the search page with the query parameters.
        """
        self.search_results = []
        search_form = SearchForm(request.POST)

        if search_form.is_valid():
            # generate navigation context given the query parameters provided by the form
            cleaned_data = search_form.cleaned_data
            self.search_results = None
            search_results_ids, self.search_results = self.get_search_results(cleaned_data)
            nav_ctx = search_results_ids
            self.request.session['nav_ctx'] = nav_ctx

            query_params = {
                'query': cleaned_data['search_query'],
                'start_date': cleaned_data['start_date'],
                'end_date': cleaned_data['end_date'],
                'location': cleaned_data['location'],
                'media_type': cleaned_data['media_type'],
                'depicted_users': cleaned_data['depicted_users'],
                'cache_form': True
            }
            # Redirect to GET search view with query parameters
            url = reverse('arch_app:search') + '?' + urlencode(query_params)
            return redirect(url)

        else:
            # add (the form) error messages to the messages framework
            for field, error in search_form.errors.items():
                for e in error:
                    messages.error(request, e)
            return super().get(request, *args, **kwargs)

    def get_queryset(self):
        try:
            return self.search_results
        except AttributeError:
            return Record.objects.none()

    def populate_search_form(self, context):
        """
        Populates the search form with the query parameters from the url
        :param context: context dictionary
        :return: search form
        """
        search_form = SearchForm(initial=
                                 {'search_query': context['query'],
                                  'start_date': datetime.strptime(context['start_date'], '%Y-%m-%d').strftime(
                                      "%Y-%m-%d") if context['start_date'] != 'None' else None,
                                  'end_date': datetime.strptime(context['end_date'], '%Y-%m-%d').strftime(
                                      "%Y-%m-%d") if context['end_date'] != 'None' else None,
                                  'location': context['location'],
                                  'media_type': context['media_type'],
                                  'depicted_users': context['depicted_users']})
        return search_form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album_mode'] = "False"
        context['media_type'] = None
        # if the form is to be cached, populate the form with the query parameters
        if self.request.GET.get('cache_form'):
            context['populated_form'] = True
            context['query'] = self.request.GET.get('query', None)
            context['start_date'] = self.request.GET.get('start_date', None)
            context['end_date'] = self.request.GET.get('end_date', None)
            context['location'] = self.request.GET.get('location', None)
            context['media_type'] = self.request.GET.get('media_type', None)
            context['depicted_users'] = self.request.GET.get('depicted_users', None)
            context['search_form'] = self.populate_search_form(context)
        return context


class AlbumView(LoginRequiredMixin, generic.ListView):
    """
    displays album details and the records in an album
    """
    model = Record
    template_name = "arch_app/album.html"
    paginate_by = PAGINATE_BY

    def get_queryset(self):
        album = Album.objects.get(id=self.kwargs['pk'])
        if album.is_inbox:
            record_list = get_objects_for_user(self.request.user, "view_record", Record.objects.filter(album=album)) \
                .order_by('-date_created', '-date_uploaded')
        else:
            record_list = Record.objects.filter(album=album).order_by('-date_created', '-date_uploaded')
        nav_ctx = [str(m.id) for m in record_list]  # create navigation context session
        self.request.session['nav_ctx'] = nav_ctx
        return record_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album'] = Album.objects.get(id=self.kwargs['pk'])
        context['album_mode'] = "True"
        return context

    def get(self, request, *args, **kwargs):
        """
        Get method for the album view.
        Checks if the user has permission to view the album and tracks the access to the album.
        """
        try:
            album = Album.objects.get(id=self.kwargs['pk'])
        except Album.DoesNotExist:
            messages.error(request, _('The album you requested does not exist.'))
            return redirect('arch_app:index')

        if not request.user.has_perm('view_album', album) and not request.user.has_perm('is_moderator', album.archive):
            messages.error(request, _('You do not have permission to view this album.'))
            # try redirect to where the user came from, but check it is not the page of the album again
            if str(album.id) in request.META.get('HTTP_REFERER', '/'):
                return redirect(reverse('arch_app:archive',
                                        kwargs={'group_name': album.archive.name, 'pk': album.archive.id}))
            else:
                return redirect(request.META.get('HTTP_REFERER', '/'))

        paginator = self.get_paginator(self.get_queryset(), self.paginate_by)
        # check if the page is out of range
        if paginator.num_pages < int(self.request.GET.get('page', 1)):
            # redirect to the last page
            return redirect(reverse('arch_app:album', kwargs={'pk': self.kwargs['pk']}) + '?page=' + str(
                paginator.num_pages))
        # Track the user's visit to this album
        Tracker.objects.create_from_request(request=request, content_object=album, user=request.user)
        # redirect to the album at the right page
        return super().get(request, *args, **kwargs)


class AlbumCreateView(LoginRequiredMixin, generic.TemplateView):
    """
    manages Albums
    """
    template_name = "arch_app/album.html"

    def post(self, request, *args, **kwargs):
        """
        handles post request to create a new album
        checks if the user has the permission to create a new album
        """
        if request.POST['action'] == 'create':
            if not request.user.has_perm('is_moderator', Archive.objects.get(id=request.POST['archive'])):
                messages.error(request, _('Sorry, you do not have permission to create a new album.'))
                return redirect(reverse("arch_app:index"))

            album_form = CreateAlbumForm(request.POST)
            if album_form.is_valid():
                album = album_form.save(commit=False)
                album.creator = request.user
                album.archive = Archive.objects.get(id=request.POST['archive'])
                try:
                    album.save()
                except IntegrityError:
                    messages.warning(request, _("Could not create Album. Album with this name already exists."))
                    return redirect(reverse('arch_app:album_list', kwargs={
                        'archive_pk': request.POST['archive']
                    }))
                # assign permissions to the residential group moderators
                # (view permissions are already automatically assigned to all residential group members in models.py)
                assign_perm('delete_album', album.archive.moderators, album)
                assign_perm('change_album', album.archive.moderators, album)
                messages.success(request, _('New Album created!'))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                messages.warning(request, _("Could not create a new Album."))

        return redirect(reverse('arch_app:album_list', kwargs={
            'archive_pk': request.POST['archive']
        }))


class AlbumUpdateView(LoginRequiredMixin, SuccessMessageMixin, View):
    """
    Updates an album (e.g., adds/removes users from an album).
    Moderators have the permission to change the album.
    """

    def post(self, request, *args, **kwargs):
        """
        handles post request to update an album
        checks if the user has the permission to change the album
        """
        if not request.user.has_perm('is_moderator', Album.objects.get(id=self.kwargs['pk']).archive):
            messages.error(request, _('You do not have permission to change this album.'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if self.request.GET.get('type_of_form') and \
                self.request.GET.get('type_of_form') == 'update_album_members_form':
            form = UpdateAlbumMembersForm(request.POST, instance=Album.objects.get(id=self.kwargs['pk']))
        else:
            form = UpdateAlbumForm(request.POST, instance=Album.objects.get(id=self.kwargs['pk']))
        if form.is_valid():
            form.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def delete_album(request, pk):
    """
    deletes an album, if the user has the permission to do so
    """
    album = Album.objects.get(id=pk)
    archive = album.archive
    # check permission
    if not request.user.has_perm('delete_album', album):
        messages.error(request, _('You are not allowed to delete this Album.'))
        try:
            # redirect to where the user came from
            return redirect(request.META.get('HTTP_REFERER'))
        except TypeError:
            return redirect(reverse('arch_app:index'))
    try:
        album.delete()
        messages.success(request, _('Album was deleted.'))
    except:
        messages.error(request, _('Album could not be deleted.'))
    # redirect to the residential group home
    return redirect(reverse('arch_app:archive', kwargs={'archive_name': archive.name,
                                                        'pk': archive.id}))


def set_language(request):
    """
    sets the language of the website.
    Adds the language to the url and sets the language cookie
    """
    response = HttpResponseRedirect('/')
    if request.method == 'POST':
        language = request.POST.get('language')
        origin_url = request.POST.get('origin_url')
        for lang in [lang[0] for lang in settings.LANGUAGES]:
            if f'/{lang}/' in origin_url:
                origin_url = origin_url.replace(f'/{lang}/', '')
                break
        origin_url = origin_url.lstrip('/')

        if language:
            if language != settings.LANGUAGE_CODE and [lang for lang in settings.LANGUAGES if lang[0] == language]:
                redirect_path = f'/{language}/' + origin_url
            elif language == settings.LANGUAGE_CODE:
                redirect_path = '/' + origin_url
            else:
                return response
            translation.activate(language)
            response = HttpResponseRedirect(redirect_path)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
    return response


def generate_autocomplete_json(query_results, max_length=70):
    """
    generates a json object for the autocomplete function of the search bar
    query_results: QuerySet of the search results
    max_length: int. Truncates the results to the given length
    """
    query_results_json = []
    for q_result in query_results:
        for r in q_result:
            if r:
                query_results_json.append(r[:max_length] + ('...' if len(r) > max_length else ''))
    return query_results_json


@login_required
def autocomplete(request):
    """
    The function handles different autocomplete types ('search_location', 'search_depicted_users', 'search_input').
    Results are consumed by the autocomplete (jquery) function of the search bar.
    """
    if request.GET.get('autocomplete') == 'search_location':
        if 'term' in request.GET:
            q_list = [
                Q(location__name__icontains=request.GET['term']),
                Q(location__country__icontains=request.GET['term']),
                Q(location__state__icontains=request.GET['term']),
                Q(location__region__icontains=request.GET['term']),
            ]
            # filter record by permissions
            filtered_records = get_objects_for_user(
                request.user,
                'view_record',
                Record.objects.select_related('location').filter(Q(*q_list, _connector=Q.OR))
            )
            query_results = filtered_records.values_list('location__name',
                                                         'location__country',
                                                         'location__state',
                                                         'location__region').distinct()

            return JsonResponse(list(set(generate_autocomplete_json(query_results))), safe=False)

    if request.GET.get('autocomplete') == 'search_depicted_users':
        if 'term' in request.GET:
            q_list = [
                Q(depicted_users__user__username__icontains=request.GET['term']),
                Q(depicted_users__user__first_name__icontains=request.GET['term']),
                Q(depicted_users__user__last_name__icontains=request.GET['term']),
            ]
            # get residential groups of the user
            archives = User.objects.get(id=request.user.id).archives.all()
            active_members = [archive.get_active_members() for archive in archives]
            # merge query sets
            query_merged = chain.from_iterable(active_members)

            users_data = []
            for u in query_merged:
                if u.username:
                    users_data.append(u.username)
                if u.first_name:
                    users_data.append(u.first_name)
                if u.last_name:
                    users_data.append(u.last_name)

            filtered_records = get_objects_for_user(
                request.user,
                'view_record',
                Record.objects.select_related('depicted_users').filter(Q(*q_list, _connector=Q.OR))
            )
            query_results = filtered_records.values_list('depicted_users__user__username',
                                                         'depicted_users__user__first_name',
                                                         'depicted_users__user__last_name').distinct()

            query_results_json = []
            for q_result in query_results:
                for r in q_result:
                    if r:
                        if r in users_data:
                            query_results_json.append(r)
                        else:
                            break

            return JsonResponse(list(set(query_results_json)), safe=False)

    if request.GET.get('autocomplete') == 'search_input':
        if 'term' in request.GET:
            query = Q(title__icontains=request.GET['term']) | Q(user_caption__icontains=request.GET['term'])
            # filter record by permissions
            filtered_records = get_objects_for_user(
                request.user,
                'view_record',
                Record.objects.filter(query)
            )
            query_results = filtered_records.values_list('title', 'user_caption').distinct()

            return JsonResponse(list(set(generate_autocomplete_json(query_results))), safe=False)

    return JsonResponse([], safe=False)


class TagCreateView(LoginRequiredMixin, generic.View):
    """
    View to tag a user in a record object
    """
    form_class = CreateTagForm

    def post(self, request, *args, **kwargs):
        """
        Handles the post request to tag a user in a record object
        """
        try:
            tag = Tag(record=Record.objects.get(id=self.kwargs['pk']))
            form = self.form_class(request.POST, instance=tag)
            if form.is_valid():
                form.save()
                messages.success(request, _('Person was tagged successfully.'))
            else:
                messages.warning(request, _("Could not tag person."))
        except Exception as e:
            file_logger.error(e)
            console_logger.error(e)
            messages.warning(request, _("Error"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class UpdateTagView(LoginRequiredMixin, generic.UpdateView):
    """
    View to update a tag and change/add the user to the tag
    """
    model = Tag
    form_class = UpdateTagForm

    def post(self, request, *args, **kwargs):
        """
        Handles the post request to update a tag and change/add the user to the tag
        checks if the user is a moderator and has the permission to tag a person
        """
        if not request.user.has_perm('is_moderator', self.get_object().record.album.archive):
            messages.error(request, _('You do not have permission to tag this person.'))
            return redirect(request.META.get('HTTP_REFERER', '/'))
        try:
            form = self.form_class(request.POST, instance=self.get_object())
            if form.is_valid():
                form.save()
                messages.success(request, _('Person was tagged successfully.'))
            else:
                messages.warning(request, _("Could not tag person."))
        except Exception as e:
            file_logger.error(e)
            console_logger.error(e)
            messages.warning(request, _("Error."))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def create_tag_box(request, pk):
    """
    creates a tag boundary box via AJAX
    """
    if request.method == 'POST':
        # check permissions
        record = Record.objects.get(id=pk)
        if not request.user.has_perm('is_moderator', record.album.archive):
            messages.error(request, _('You do not have permission to tag someone.'))
            return JsonResponse({'success': False})
        try:
            tag_box = TagBox(record=record)
            img = Image.open(record.media_file)
            # get original image width and height
            w, h = img.size
            # change width and height according to orientation
            img_exif = img.getexif()
            # switch width and height if orientation is 90 or 270 degrees
            if img_exif and img_exif.get(274) and img_exif[274] in [6, 8]:
                w, h = h, w
            img.close()
            canvas_width = int(request.POST['width'])
            canvas_height = int(request.POST['height'])
            # adjust the coordinates of the tag box to the original image size
            data = {
                'x1': int(float(request.POST['x1']) / canvas_width * w),
                'y1': int(float(request.POST['y1']) / canvas_height * h),
                'x2': int(float(request.POST['x2']) / canvas_width * w),
                'y2': int(float(request.POST['y2']) / canvas_height * h),
                'width': w,
                'height': h
            }

            form = TagBoxForm(
                data=data,
                instance=tag_box
            )
            if form.is_valid():
                form.save()
                messages.success(request, _('Tag created successfully.'))
            else:
                messages.warning(request, _("Could not create Tag."))
        except Exception as e:
            # log error
            file_logger.error(e)
            console_logger.error(e)
            messages.warning(request, _("Error."))
        # reload the page
        return JsonResponse({'success': True})


@login_required
def delete_tag(request, pk):
    """
    deletes a tag
    """
    tag = Tag.objects.get(id=pk)
    record = tag.record
    try:
        tag.delete()
    except Exception as e:
        messages.error(request, _('Could not be deleted.'))
    messages.success(request, _('Tag was deleted successfully.'))
    # redirect to the record page
    return redirect(reverse('arch_app:record', kwargs={'pk': record.id}))


@login_required
def pixelate_image(request, pk):
    """
    pixelates a record image
    """
    # check permissions
    tag_box = TagBox.objects.get(id=pk)
    record = tag_box.record
    if not request.user.has_perm('is_moderator', record.album.archive):
        messages.error(request, _('You do not have permission to pixelate this image.'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if not record.type == 'Image' and record.get_file_extension() in ['jpg', 'jpeg', 'png']:
        messages.error(request, _('Only images can be pixelated.'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    blur_image(image_path=record.preview_file.path,
               coordinates=(tag_box.x1, tag_box.y1, tag_box.x2, tag_box.y2)
               )
    tag_box.visible = 'hidden_by_mod'
    tag_box.save()
    messages.success(request, _('Image was pixelated successfully.'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def show_tag(request, pk):
    """ shows a tag and removes the pixelation """
    tag_box = TagBox.objects.get(id=pk)
    record = tag_box.record
    # check permissions
    if not request.user.has_perm('is_moderator', record.album.archive):
        messages.error(request, _('You do not have permission to show this tag.'))
        # redirect to where the user came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    unblur_image(image_path=record.preview_file.path,
                 original_file_path=record.media_file.path,
                 coordinates=(tag_box.x1, tag_box.y1, tag_box.x2, tag_box.y2))
    tag_box.visible = 'visible'
    tag_box.save()
    messages.success(request, _('Tag was shown successfully.'))
    # reload the page
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class AlbumListView(LoginRequiredMixin, generic.ListView):
    """
    Handles album page of an archive. Displays all albums of an archive
    """
    model = Album
    template_name = 'arch_app/partials/album_list.html'
    paginate_by = 8

    def get_queryset(self):
        """ Return all albums of the archive without the inbox. """
        archive = Archive.objects.get(id=self.kwargs['archive_pk'])

        if self.request.user.has_perm('is_moderator', archive):
            # filter album by permissions
            filtered_albums = Album.objects.filter(archive=archive, is_inbox=False).order_by("-date_created")
        else:
            # filter album by permissions
            filtered_albums = get_objects_for_user(
                self.request.user,
                'view_album',
                Album.objects.filter(archive=archive, is_inbox=False)
            ).order_by("-date_created")

        return filtered_albums

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['archive'] = Archive.objects.get(id=self.kwargs['archive_pk'])
        return context

    def get(self, request, *args, **kwargs):
        # get archive or 404
        archive = get_object_or_404(Archive, id=self.kwargs['archive_pk'])
        # check permissions
        if not request.user.has_perm('view_archive', archive):
            messages.error(request, _('You do not have permission to view this page.'))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return super().get(request, *args, **kwargs)


@login_required
def feedback_view(request):
    """ View to send feedback to the administrator. """
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            context = {
                'timestamp': datetime.now(),
                'hostname': request.META['HTTP_HOST'],
                'message': form.cleaned_data['message'],
            }
            email_status = send_email(settings.CONTACT_EMAIL,
                                      subject="User's feedback!",
                                      html_message=render_to_string('arch_app/emails/feedback_email.html',
                                                                    context)
                                      )

            if email_status:
                messages.success(request, _('Feedback was sent successfully.'))
            else:
                messages.error(request, _('Feedback could not be sent.'))

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, _('Feedback could not be sent.'))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return None


@login_required
def hide_personal_data(request):
    """
    hides personal data from the archive, logs out user and sends confirmation email
    """
    user = request.user
    user.visible = False
    user.save()
    # hide all comments
    for comment in Comment.objects.filter(user=user):
        comment.visible = 'hidden_by_user'
        comment.save()
    # hide all tags
    for tag in Tag.objects.filter(user=user):
        tag.visible = 'hidden_by_user'
        tag.save()
    # blur all images
    for tagbox in TagBox.objects.filter(user=user):
        blur_image(image_path=tagbox.record.preview_file.path,
                   coordinates=(tagbox.x1, tagbox.y1, tagbox.x2, tagbox.y2)
                   )
    # send mail to user with information link to delete account
    # Build the URL to permanently delete the account
    # encode the user's primary key
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    domain = get_current_site(request).domain
    delete_account_url = reverse('arch_app:delete_account', kwargs={'uidb64': uid, 'token': token})
    delete_account_link = f'http://{domain}{delete_account_url}'  # must be http
    context = {
        'hostname': request.META['HTTP_HOST'],
        'delete_account_link': delete_account_link,
        'user': user,
    }

    email_status = send_email(user.email,
                              subject="Hide personal data",
                              html_message=render_to_string(
                                  'arch_app/emails/hide_personal_data_confirmation_email.html', context))

    if email_status:
        messages.success(request,
                         _('Your personal data was hidden successfully. You will receive a confirmation email.'))
    else:
        messages.error(request,
                       _('An error occurred while sending the confirmation email. Please contact the Administrator..'))

    # Log off user
    logout(request)
    # redirect to home
    return HttpResponseRedirect(reverse('arch_app:index'))


class DeleteAccountView(generic.TemplateView):
    """
    deletes the account of a user, removes all personal data and sends confirmation email
    """
    template_name = "arch_app/delete_account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uidb64 = self.kwargs['uidb64']
        context['uidb64'] = uidb64
        uid = force_str(urlsafe_base64_decode(uidb64))
        context['account'] = User.objects.get(pk=uid)
        context['token'] = self.kwargs['token']
        return context

    def post(self, request, *args, **kwargs):
        # get the user account and token from the url (which is sent per mail)
        uidb64 = self.kwargs['uidb64']
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        token = self.kwargs['token']
        # check if the token is valid
        if user is not None and default_token_generator.check_token(user, token):
            # delete all personal data
            # blur all images
            for tagbox in TagBox.objects.filter(user=user):
                blur_image(image_path=tagbox.record.media_file.path,
                           coordinates=(tagbox.x1, tagbox.y1, tagbox.x2, tagbox.y2)
                           )
            # delete user account (and all related data, e.g. comments, tags, etc.)
            user.delete()
            # send confirmation email
            email_status = send_email(user.email,
                                      subject="Account deleted",
                                      html_message=render_to_string(
                                          'arch_app/emails/delete_account_confirmation_email.html', context={
                                              'user': user,
                                          })
                                      )
            if email_status:
                messages.success(request,
                                 _('Your account was deleted successfully. You will receive a confirmation email.'))
            else:
                messages.error(request,
                               _('An error occurred while sending the confirmation email. Please contact the Administrator..'))

        else:
            messages.error(request, _('You cannot delete this account.'))
        return HttpResponseRedirect(reverse('arch_app:index'))


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    """ Dashboard for the admin to track usage statistics. """
    template_name = "arch_app/dashboard.html"

    def get_timeseries(self, model, field, window='month', filters=None):
        """
        Returns a timeseries of the given model and field.
        param: model: the model to query
        param: field: the field to query
        param: window: the window to group by (e.g., month, week, day)
        param: filters: additional filters to apply
        """
        filters = filters or {}
        dates = (model.objects.filter(**{f'{field}__isnull': False}, **filters)
                 .annotate(date_x=Trunc(field, kind=window))
                 .values('date_x')
                 .annotate(count=Count('date_x')))
        timeseries = {
            'x': [i['date_x'].strftime("%Y-%m-%d") for i in dates],
            'y': [i['count'] for i in dates],
        }
        return timeseries

    def get_context_data(self, **kwargs):
        """
        Returns the context for the dashboard.
        calculates the number of archives, records, users, comments, tags, albums, logins, record views, album views,
        archive views, and the number of uploads by moderators and members.
        """
        number_of_archives = Archive.objects.count()
        number_of_records = Record.objects.count()
        number_of_users = User.objects.count()
        number_of_comments = Comment.objects.count()
        number_of_tags = Tag.objects.count()
        number_of_albums = Album.objects.count()
        number_of_logins = Tracker.objects.filter(content_type__model='user').count()
        number_of_record_views = Tracker.objects.filter(content_type__model='record').count()
        number_of_album_views = Tracker.objects.filter(content_type__model='album').count()
        number_of_archive_views = Tracker.objects.filter(content_type__model='archive').count()

        timeseries_records = self.get_timeseries(Record, 'date_uploaded', 'week')
        timeseries_logins = self.get_timeseries(Tracker, 'timestamp', 'week',
                                                {'content_type__model': 'user'})
        timeseries_record_views = self.get_timeseries(Tracker, 'timestamp', 'week',
                                                {'content_type__model': 'record'})
        timeseries_albums = self.get_timeseries(Tracker, 'timestamp', 'week',
                                                {'content_type__model': 'album'})

        # get the number of records uploaded by a moderator
        uploads_mods = 0
        for archive in Archive.objects.all():
            mods = archive.moderators.user_set.all()
            for mod in mods:
                uploads_mods += Record.objects.filter(creator=mod).count()
        uploads_members = Record.objects.all().count() - uploads_mods

        # get the 10 most viewed albums with the number of views (exclude inbox)
        albums = Album.objects.filter(is_inbox=False)
        album_views = []
        for album in albums:
            album_views.append({
                'album': album,
                'views': Tracker.objects.filter(content_type__model='album', object_id=album.id).count()
            })
        most_viewed_albums = sorted(album_views, key=lambda k: k['views'], reverse=True)[:10]

        # get the 10 most viewed records with the number of views
        records = Record.objects.all()
        record_views = []
        for record in records:
            record_views.append({
                'record': record,
                'views': Tracker.objects.filter(content_type__model='record', object_id=record.id).count()
            })
        most_viewed_records = sorted(record_views, key=lambda k: k['views'], reverse=True)[:10]

        context = super().get_context_data(**kwargs)

        context['timeseries_records'] = timeseries_records
        context['timeseries_logins'] = timeseries_logins
        context['timeseries_record_views'] = timeseries_record_views
        context['timeseries_albums'] = timeseries_albums
        context['uploads_mods'] = uploads_mods
        context['uploads_members'] = uploads_members
        context['most_viewed_albums'] = most_viewed_albums
        context['most_viewed_records'] = most_viewed_records

        context['number_of_archives'] = number_of_archives
        context['number_of_records'] = number_of_records
        context['number_of_users'] = number_of_users
        context['number_of_comments'] = number_of_comments
        context['number_of_tags'] = number_of_tags
        context['number_of_albums'] = number_of_albums
        context['number_of_logins'] = number_of_logins
        context['number_of_record_views'] = number_of_record_views
        context['number_of_album_views'] = number_of_album_views
        context['number_of_archive_views'] = number_of_archive_views
        return context

    def get(self, request, *args, **kwargs):
        """
        Checks if the user is an admin. If not, redirects to the home page.
        """
        if not request.user.has_perm('is_admin'):
            messages.error(request, _('You do not have permission to view this page.'))
            return HttpResponseRedirect(reverse('arch_app:index'))
        return super().get(request, *args, **kwargs)


class MembershipDateFormView(generic.UpdateView):
    """
    View to change the membership (dates) of a user in an archive
    """
    model = Membership
    form_class = MembershipDateForm

    def form_valid(self, form):
        messages.success(self.request, _('Membership date was changed successfully.'))
        self.object = form.save()
        return redirect(reverse('arch_app:members', kwargs={'archive_name': self.object.archive.name,
                                                            'pk': self.object.archive.pk}))

    def form_invalid(self, form):
        for field, error in form.errors.items():
            for e in error:
                messages.error(self.request, e)
        return redirect(reverse('arch_app:members', kwargs={'archive_name': self.object.archive.name,
                                                            'pk': self.object.archive.pk}))
