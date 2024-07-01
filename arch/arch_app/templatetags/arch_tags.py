from django import template
from django.conf import settings
from arch_app.models import Archive, Album
from arch_app.forms import FileUploadForm, UpdateAlbumForm, SearchForm, SelectAlbumForm, AddMemberForm, \
    ArchiveForm, CreateTagForm, UpdateTagForm, UpdateAlbumMembersForm, FeedbackForm, MembershipDateForm

register = template.Library()



@register.simple_tag()
def get_random_int():
    """ returns a random integer """
    import random
    return random.randint(0, 10000)

@register.simple_tag()
def get_number_comments(media_id):
    """ returns the number of comments for a given media id """
    from arch_app.models import Comment

    return Comment.objects.select_related('record').filter(record__id=media_id).count()




@register.simple_tag()
def get_archives_for_user(user):
    """ retrieves unique archives from the database which belong to the given user """

    return user.archives.all().distinct()


@register.simple_tag()
def get_contact_email():
    """ returns the admin email address """
    return settings.CONTACT_EMAIL

@register.simple_tag()
def get_feedback_form():
    """ returns a feedback form """
    return FeedbackForm()


@register.simple_tag()
def get_membership_date_form(instance):
    """ returns a membership date form """
    return MembershipDateForm(instance=instance)


@register.simple_tag()
def get_upload_form():
    """ returns an upload form """
    return FileUploadForm()


@register.simple_tag()
def get_album_form(album):
    """ returns an album form """
    if album is None:
        return UpdateAlbumForm()
    # album = Album.objects.get(id=album_id)
    album_form = UpdateAlbumForm(instance=album)
    return album_form


@register.simple_tag()
def get_album_members_form(album):
    """ returns an album form """
    if album is None:
        return UpdateAlbumMembersForm()
    # album = Album.objects.get(id=album_id)
    album_members_form = UpdateAlbumMembersForm(instance=album)
    return album_members_form


@register.simple_tag()
def get_archive_form(archive):
    """ returns an archive form """
    if archive is None:
        return ArchiveForm()
    return ArchiveForm(instance=archive)


@register.simple_tag()
def get_search_form():
    """ returns a search form """
    return SearchForm()


@register.simple_tag()
def get_select_album_form(record, user):
    """ returns a form to select an album """
    return SelectAlbumForm(instance=record, user=user)


@register.simple_tag()
def get_create_add_member_form():
    """ returns a form to create or add a member """
    return AddMemberForm()


@register.simple_tag()
def get_tag_form(tag=None, *args, **kwargs):
    """ returns a form to tag a user on a record """
    if tag:
        return UpdateTagForm(instance=tag, *args, **kwargs)
    return CreateTagForm(*args, **kwargs)


@register.simple_tag()
def generate_query_string(query, start_date, end_date, location, media_type, album_mode=None):
    query_string = ''
    if query:
        query_string += f'query={query}&'
    if start_date:
        query_string += f'start_date={start_date}&'
    if end_date:
        query_string += f'end_date={end_date}&'
    if location:
        query_string += f'location={location}&'
    if media_type:
        query_string += f'media_type={media_type}&'
    if query_string:
        query_string += f'cache_form=True&'
    if album_mode:
        query_string += f'album_mode={album_mode}&'

    return '?' + query_string.rstrip('&')
