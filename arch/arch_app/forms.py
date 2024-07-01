# from pyexpat.errors import messages

from django import forms
from django.forms import Textarea, TextInput, DateInput, ClearableFileInput, FileInput, Select
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse, reverse_lazy
from .models import *
from django.core.exceptions import ValidationError
from datetime import date


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


class FeedbackForm(forms.Form):
    """
    Form for feedback
    """

    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5,
                                                           'class': 'form-control',
                                                           'placeholder': _('Your message'),
                                                           'id': 'feedback-message-id'}))


class ArchiveForm(forms.ModelForm):
    class Meta:
        model = Archive
        fields = ('description', 'profile_picture')
        widgets = {
            'description': Textarea(attrs={'rows': 10,
                                           'class': 'form-control editable-title no-border submit-on-enter',
                                           'style': "width: 100%;",
                                           'placeholder': _('here you can describe the group.'),
                                           'id': 'archive-description-id'}),
            'profile_picture': FileInput(attrs={'class': 'form-control',
                                                'style': "width: 100%;",
                                                'id': 'profile-picture-input'}),
        }


class MembershipDateForm(forms.ModelForm):
    """
    Form for membership dates
    """

    class Meta:
        model = Membership
        fields = ('start_date', 'end_date')
        widgets = {
            'start_date': DateInput(attrs={'type': 'date',
                                           },
                                    format='%Y-%m-%d'),
            'end_date': DateInput(attrs={'type': 'date',},
                                  format='%Y-%m-%d'),
        }
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(_('Start date cannot be later than end date.'), code='invalid')

        return cleaned_data

class AddMemberForm(forms.Form):
    ROLE_CHOICES = [
        ('member', _('member')),
        ('moderator', _('moderator')),
    ]
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))


class SearchForm(forms.Form):
    MEDIA_TYPES = [
        ('All', 'All'),
        ('Image', 'Image'),
        ('Audio', 'Audio'),
        ('Video', 'Video'),
        ('Text', 'Text')
    ]
    search_query = forms.CharField(
        label=_('Search'),
        max_length=500,
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'search_input',
                'class': 'form-control',
            }
        )
    )

    depicted_users = forms.CharField(
        label=_('depicted_users'),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                # 'placeholder': _("Search"),
                'id': 'search_depicted_users',
                'class': 'form-control',
            }
        )
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.widgets.DateInput(
            attrs={'type': 'date',
                   'id': 'search_start_date',
                   'class': 'form-control',
                   }
        )
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.widgets.DateInput(
            attrs={'type': 'date',
                   'id': 'search_end_date',
                   'class': 'form-control',
                   }
        )
    )
    location = forms.CharField(required=False,
                               max_length=100,
                               widget=forms.TextInput(
                                   attrs={'id': 'search_location',
                                          'class': 'form-control',

                                          }
                               ))
    media_type = forms.ChoiceField(choices=MEDIA_TYPES,
                                   required=False,
                                   widget=forms.Select(
                                       attrs={'id': 'search_media_type',
                                              'class': 'form-control', }
                                   ))

    def clean(self):
        cleaned_data = super().clean()
        search_query = cleaned_data.get("search_query")
        depicted_users = cleaned_data.get("depicted_users")
        location = cleaned_data.get("location")
        media_type = cleaned_data.get("media_type")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(_('Start date cannot be later than end date.'), code='invalid')

        if media_type == 'All':
            if not search_query and not location and not start_date and not end_date and not depicted_users:
                raise ValidationError(_('Please enter a search query or select a filter.'), code='invalid')

        return cleaned_data


class FileUploadForm(forms.Form):
    file_validator = FileValidator(
        max_size=settings.MAX_FILE_SIZE,
        supported_formats=[],
        content_types=[]
    )
    files = forms.FileField(
        validators=[file_validator],
        widget=forms.FileInput(
            attrs={'multiple': True, 'directory': True, 'name': 'files-input'}
        )
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

        widgets = {
            # dynamic text area size
            'text': Textarea(attrs={'rows': 2,
                                    'style': "width: 100%;",
                                    # make text area grow dynamically with text
                                    # 'oninput': "this.style.height=''; this.style.height=this.scrollHeight + 'px'",
                                    'class': 'submit-on-enter',
                                    'id': 'comment-text',
                                    'placeholder': _('Add a comment...')
                                    }),
        }


class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['date_created', 'title', 'user_caption', 'location']
        widgets = {
            'date_created': DateInput(attrs={'type': 'date',
                                             'style': "width: 100%; color: gray;"},
                                      format='%Y-%m-%d'),
            'user_caption': Textarea(attrs={'rows': 2,
                                            'style': "width: 100%",
                                            'placeholder': _('... add a description')
                                            }),
            'title': TextInput(attrs={'class': 'editable-title no-border',
                                      'style': "width: 100%",
                                      'placeholder': _('... add title')})
        }

    def clean(self):
        cleaned_data = super().clean()
        date_created = cleaned_data.get("date_created")
        if date_created:
            if date_created > date.today():
                raise ValidationError(_("The record's creation date cannot be later than today's date."), code='invalid')

        return cleaned_data


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'state', 'country']
        widgets = {
            'name': TextInput(attrs={'style': "width: 100%",
                                     'placeholder': _('... add a name of the street, city or place')}),
            'state': TextInput(attrs={'style': "width: 100%;",
                                      'placeholder': _('... add a state or region')}),
            'country': TextInput(attrs={'style': "width: 100%;",
                                        'placeholder': _('... add a country')}),
        }


class CreateTagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['user']
        widgets = {'user': Select(attrs={'form': 'create-tag-form'})}

    def __init__(self, *args, **kwargs):
        users = kwargs.pop("users").all() if "users" in kwargs else None
        super(CreateTagForm, self).__init__(*args, **kwargs)
        # restrain the possible users to be tagged
        if users:
            self.fields["user"].queryset = users.filter(visible=True)
        elif self.instance and self.instance.record:
            self.fields["user"].queryset = self.instance.record.album.archive.get_members().filter(visible=True)
        else:
            self.fields["user"].queryset = User.objects.none()


class UpdateTagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['user']

    def __init__(self, *args, **kwargs):
        users = kwargs.pop("users").all() if "users" in kwargs else None
        super(UpdateTagForm, self).__init__(*args, **kwargs)
        # restrain the possible users to be tagged
        if users:
            self.fields["user"].queryset = users
        elif self.instance and self.instance.record:
            self.fields["user"].queryset = self.instance.record.album.archive.get_members().filter(visible=True)
        else:
            self.fields["user"].queryset = User.objects.none()


class TagBoxForm(forms.ModelForm):
    """ Form for creating a new tag box """
    class Meta:
        model = TagBox
        fields = ['x1', 'y1', 'x2', 'y2', 'width', 'height']


class ProfilePictureForm(forms.ModelForm):
    """
    Form for the user to change their profile picture
    """
    class Meta:
        model = User
        fields = ['profile_picture']

        widgets = {
               'profile_picture': FileInput(attrs={'class': 'account-settings-fileinput',
                                                   'id': 'profile-picture-input', }),
           }


class ProfileForm(forms.ModelForm):
    """
    Form for the user to change their profile information
    """

    class Meta:
        model = User
        fields = ['username',
                  'first_name',
                  'last_name',
                  'bio',
                  # 'language',
                  'country',
                  'birth_date',
                  # 'consent'
                  ]

        widgets = {
            'username': TextInput(attrs={'class': 'form-control',

                                         'placeholder': _('... add username')}),
            'last_name': TextInput(attrs={'class': 'form-control',

                                          'placeholder': _('... add last name')}),
            'first_name': TextInput(attrs={'class': 'form-control',

                                           'placeholder': _('... add first name')}),
            'birth_date': DateInput(attrs={'type': 'date',
                                           'class': 'form-control'},
                                    format='%Y-%m-%d'),
            'bio': Textarea(attrs={'rows': 3,
                                   'class': 'editable-title',
                                   'style': "width: 100%",
                                   'placeholder': _('Add a description of yourself.')}),
            'country': TextInput(attrs={'class': 'editable-title no-border',
                                        'placeholder': _('... add location')}),


            # 'language': Select(attrs={'class': 'form-control'}),
        }


class UpdateAlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description']
        widgets = {
            'title': TextInput(attrs={'class': 'editable-title no-border edit-album-title text-primary',
                                      'style': "width: 100%;",
                                      'placeholder': _('... add title')}),
            'description': Textarea(attrs={'class': 'editable-title no-border edit-album-description',
                                           'rows': 3,
                                           'style': "width: 100%; resize: none;",
                                           'placeholder': _('Add a description of this album.')
                                           }),
        }



class UpdateAlbumMembersForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = []
    def __init__(self, *args, **kwargs):
        super(UpdateAlbumMembersForm, self).__init__(*args, **kwargs)
        initial_users = self.instance.group.user_set.all()
        # get all active users in the archive
        users = self.instance.archive.get_members().order_by('username','first_name', 'last_name')
        self.fields["users"] = forms.ModelMultipleChoiceField(queryset=users,
                                                              initial=initial_users,
                                                              widget = forms.CheckboxSelectMultiple,)

    def save(self, commit=True):
        album = super().save(commit=False)
        if commit:
            album.save()
        album.group.user_set.set(self.cleaned_data['users'])

        return album



class CreateAlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title']
        widgets = {
            'title': TextInput(attrs={'class': 'editable-title no-border',
                                      'style': "width: 80%",
                                      'placeholder': _('... add title')})
        }


class SelectAlbumForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['album']
        # widgets = {
        #     'album': Select(attrs={'class': 'form-control', 'style': "width: 100%"})
        # }

    def __init__(self, user, *args, **kwargs):
        super(SelectAlbumForm, self).__init__(*args, **kwargs)
        albums = Album.objects.filter(archive=self.instance.album.archive)
        # remove the current album from the list
        albums = albums.exclude(id=self.instance.album.id)
        # remove the inbox album from the list
        albums = albums.exclude(id=self.instance.album.archive.inbox.id)
        self.fields["album"].queryset = albums
