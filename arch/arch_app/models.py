import os

from django.conf import global_settings
from django.conf import settings
import uuid
import datetime

from django.core.exceptions import ObjectDoesNotExist
# from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm, remove_perm
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _
from .file_validators import FileValidator
from .manager import TrackerManager, RecordManager


# from django.core.mail import send_mail

#######################
###  Basic Models  ###

class Location(models.Model):
    """ Basic Location model """
    name = models.CharField(max_length=120, null=True, blank=True)
    country = models.CharField(max_length=120, null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    state = models.CharField(max_length=120, null=True, blank=True)
    region = models.CharField(max_length=120, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.name} ({self.country_code})"


#######################
###  User & Groups  ###


def upload_archive_picture_get_path(instance, filename):
    """ returns the relative path where to upload house profile picture """
    return os.path.join(f"archive_{str(instance.id)}",
                        'archive_info',
                        f"profile_picture_{str(instance.id)}.jpg"
                        )


class Archive(models.Model):
    """ an archive is a collection of albums """
    name = models.CharField(max_length=128, unique=True)
    # this group is used for permission control
    moderators = models.OneToOneField(Group, on_delete=models.SET_NULL, null=True, blank=True)
    inbox = models.OneToOneField("Album", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="archive_of_inbox")
    location = models.OneToOneField(Location, on_delete=models.SET_NULL, null=True, blank=True)
    institution_name = models.CharField(max_length=128)
    profile_picture = models.ImageField(upload_to=upload_archive_picture_get_path, null=True, default=None, blank=True)
    description = models.TextField(max_length=2500, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Archives"
        permissions = (
            ("is_moderator", "Has moderator permissions."),
        )

    def get_members(self):
        return self.members.distinct()

    def get_active_members(self):
        memberships = Membership.objects.filter(archive=self)
        memberships = [membership for membership in memberships if membership.is_active]
        active_members = User.objects.filter(
            membership__in=memberships
        )
        return active_members.distinct()

    def get_active_moderators(self):
        # memberships = Membership.objects.filter(archive=self, role="staff")
        # memberships = [membership for membership in memberships if membership.is_active]
        # active_staff_members = User.objects.filter(
        #     membership__in=memberships
        # )
        # return active_staff_members.distinct()
        return self.moderators.user_set.all()

    def __str__(self):
        return self.name


@receiver(post_save, sender=Archive)
def create_inbox_and_moderator_group(sender, instance, created, **kwargs):
    """ Automatically create an inbox and moderator group if an archive is created """
    if created:
        instance.inbox = Album.objects.create(
            title=f"{instance.name} Inbox",
            archive=instance,
            is_inbox=True
        )
        instance.moderators = Group.objects.create(name=instance.name + " Moderators")
        # add permissions
        assign_perm('is_moderator', instance.moderators, instance)
        instance.save()


@receiver(pre_delete, sender=Archive)
def delete_inbox_and_moderator_group(sender, instance, **kwargs):
    """ Automatically delete an inbox and moderator group if an archive is deleted """
    if instance.inbox:
        instance.inbox.delete()
    if instance.moderators:
        instance.moderators.delete()


def upload_profile_picture_get_path(instance, filename):
    """ returns the relative path where to upload profile picture """
    return os.path.join('user_info', f"profile_picture_{str(instance.id)}.jpg")


class User(AbstractUser):
    """ a custom User class extending the Django User """
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    archives = models.ManyToManyField(Archive, through='Membership', related_name='members')
    bio = models.TextField(max_length=500, null=True, blank=True)
    #language = models.CharField(max_length=20, choices=global_settings.LANGUAGES, null=True, blank=True)
    country = models.CharField(max_length=30, null=True, blank=True)
    location = models.OneToOneField(Location, on_delete=models.SET_NULL, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    # FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # i.e. 2.5 MB
    image_validator = FileValidator(max_size=settings.MAX_FILE_SIZE,
                                    content_types="image",
                                    supported_formats=['png', 'jpeg']
                                    )
    profile_picture = models.ImageField(upload_to=upload_profile_picture_get_path,
                                        validators=[image_validator],
                                        null=True, default=None, blank=True)
    consent = models.BooleanField(null=False, default=False)
    visible = models.BooleanField(null=False, default=True)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def __str__(self):
        name_parts = [part for part in [self.first_name, self.last_name] if part]
        full_name = ' '.join(name_parts)
        return f"{self.username} ({full_name})" if full_name else self.username


@receiver(models.signals.post_delete, sender=User)
def auto_delete_profile_picture_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when corresponding User object is deleted.
    """
    if instance.profile_picture:
        # check if the old file was not the default file
        if not instance.profile_picture.name == '/arch_app/icons/person-circle.svg':
            if os.path.isfile(instance.profile_picture.path):
                os.remove(instance.profile_picture.path)
    else:
        return False


@receiver(models.signals.pre_save, sender=User)
def auto_delete_profile_picture_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem when User object is updated with new profile picture file.
    """
    if not instance.pk:
        return False
    try:
        old_file = User.objects.get(pk=instance.pk).profile_picture
    except Record.DoesNotExist:
        # if the old file does not exist, no need to delete it
        return True

    if old_file:
        new_file = instance.profile_picture
        # check if the file was actually changed
        if not old_file == new_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)


class Membership(models.Model):
    """ a Membership relation between a User and an Archive"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    archive = models.ForeignKey(Archive, on_delete=models.CASCADE, null=True, related_name='memberships')
    ROLES = (
        ('moderator', _('moderator')),
        ('member', _('member'))
    )
    role = models.CharField(max_length=19, choices=ROLES, default="member")
    start_date = models.DateField(_('begin'), default=datetime.date.today)
    end_date = models.DateField(_('end'), null=True, blank=True)
    consent = models.BooleanField(default=False, null=False)

    @property
    def is_active(self):
        """" checks if a membership is active """
        if self.end_date and self.end_date < datetime.date.today():
            return False
        return True

    def is_moderator(self):
        """ checks if a membership is a moderator """
        if self.role == 'moderator':
            return True
        return False

    def __str__(self):
        if self.is_active:
            return f"{self.user.username} is member of {self.archive.name} " \
                   f"since {self.start_date}"
        return f"{self.user.username} was member of {self.archive.name} " \
               f"from {self.start_date} until {self.end_date}."


@receiver(post_save, sender=Membership)
def new_membership(sender, instance, created, **kwargs):
    """ Handles adding a new member to an archive
    - add the user to the archive inbox group
    - give user permissions to view the archive
    - if role is moderator, add to the archive moderators group
    """
    if created:
        instance.archive.inbox.group.user_set.add(instance.user)
        # set permissions using django guardian
        assign_perm('view_archive', instance.user, instance.archive)
        if instance.role == 'moderator' and instance.is_active:
            instance.archive.moderators.user_set.add(instance.user)


@receiver(post_save, sender=Membership)
def update_membership(sender, instance, **kwargs):
    """ Handles updating a membership
    - if role is moderator, add to the archive moderators group
    """
    if instance.role == 'moderator' and instance.is_active:
        if not instance.archive.moderators.user_set.filter(pk=instance.user.pk).exists():
            instance.archive.moderators.user_set.add(instance.user)
    else:
        # check if there is another membership with the same user for the archive with a moderator membership
        if instance.archive.memberships.filter(user=instance.user).exclude(pk=instance.pk).filter(role='moderator').exists():
            # if there is a moderator membership, do nothing
            pass
        else:
            # if there is no moderator membership, try to remove the user from the staff group
            try:
                instance.archive.moderators.user_set.remove(instance.user)
            except ObjectDoesNotExist:
                pass


@receiver(post_delete, sender=Membership)
def delete_membership(sender, instance, **kwargs):
    """ Handles deleting a membership """
    # check if user exists and is not currently being deleted
    try:
        instance.user
    except ObjectDoesNotExist:
        return True
    # get the memberships of the user for the archive
    memberships = Membership.objects.filter(user=instance.user, archive=instance.archive).exclude(pk=instance.pk)
    # check if user still has a membership for the archive
    if not memberships.exists():
        # if not, remove permissions using django guardian
        remove_perm('view_archive', instance.user, instance.archive)
        # remove user from the archive inbox group
        instance.archive.inbox.group.user_set.remove(instance.user)
    # check if user still has a moderator membership for the archive
    if not memberships.filter(role='moderator').exists():
        # if not, remove user from the archive moderators group
        instance.archive.moderators.user_set.remove(instance.user)
    return True


#####################
### Record & Album ###

class Album(models.Model):
    """ an album consisting of a collection of records """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50, default="")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='albums')
    description = models.TextField(max_length=1024, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)  # users who can access the album
    archive = models.ForeignKey(Archive, on_delete=models.CASCADE, null=True, related_name='albums')
    is_inbox = models.BooleanField(default=False)
    date_created = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('title', 'archive')
        ordering = ['-date_created']

    def __str__(self):
        return self.title

    @property
    def get_start_date(self):
        """ returns the start date of the album """
        if self.record_list.exists():
            # filter out None values for date_created
            records = self.record_list.filter(date_created__isnull=False)
            if records:
                return records.order_by('date_created').first().date_created
            return None
        return None

    @property
    def get_end_date(self):
        """ returns the end date of the album """
        if self.record_list.exists():
            # filter out None values for date_created
            records = self.record_list.filter(date_created__isnull=False)
            if records:
                return records.order_by('date_created').last().date_created
            return None
        return None

    def get_number_of_records(self):
        """ returns the number of records in the album """
        return self.record_list.count()


@receiver(post_save, sender=Album)
def create_album_group(sender, instance, created, **kwargs):
    """ Automatically creates a Group of Users who can access the album """
    if created:
        instance.group = Group.objects.create(
            name=f"Album Group ({instance.id})"
        )
        # set permissions using django guardian
        assign_perm('view_album', instance.group, instance)
        # add all active members to the album
        if instance.archive:
            instance.group.user_set.add(*instance.archive.get_active_members())
        instance.save()


@receiver(post_delete, sender=Album)
def delete_group(sender, instance, **kwargs):
    """ Automatically deletes the group of users who can access the album """
    if instance.id:
        try:
            instance.group.delete()
        except Exception as e:
            # throws an Exception if the group is already deleted (e.g. the group for inbox when deleting an archive)
            pass


def media_get_path(instance, filename):
    """
    returns the relative path where to upload files
    Args:
         instance: Type <class 'arch_app.models.Photo'>
         filename: Record name (includes the file extension) e.g., my_file.png
    """
    return os.path.join(f"archive_{str(instance.album.archive.id)}",
                        'records',
                        f"{str(instance.id)}_{filename}"
                        )


class Record(models.Model):
    """ Record parent class
    a Record is one record in the archive
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_file = models.FileField(upload_to=media_get_path, null=True)
    preview_file = models.FileField(upload_to=media_get_path, null=True, blank=True)
    title = models.CharField(max_length=80, null=True, blank=True)
    MEDIA_TYPES = (
        ('Image', 'Image'),
        ('Audio', 'Audio'),
        ('Video', 'Video'),
        ('Text', 'Text'),
        ('Other', 'Other')
    )
    type = models.CharField(max_length=19, choices=MEDIA_TYPES, null=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=False, related_name='record_list')
    depicted_users = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    manifest_path = models.CharField(max_length=1024, null=True, editable=False)  # ToDo change to file fields
    metadata_path = models.CharField(max_length=1024, null=True, editable=False)

    # metadata
    user_caption = models.TextField(max_length=1024, null=True, blank=True)
    date_uploaded = models.DateField(auto_now_add=True)
    date_created = models.DateField(null=True, blank=True)
    creator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    location = models.OneToOneField(Location, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.CharField(max_length=20, choices=global_settings.LANGUAGES, null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)

    objects = RecordManager()

    def __str__(self):
        if self.title:
            return self.title
        return str(self.id)

    @property
    def get_file_extension(self):
        """ returns the file extension of the record file """
        return self.media_file.name.split('.')[-1].lower()

    @property
    def get_tagboxes(self):
        """
        return all the TagBox objects related to this record
        """
        return TagBox.objects.filter(record=self)

    def get_preview_url(self):
        """ returns the path to the file which is used as a preview_file in the template """
        if self.preview_file:
            return self.preview_file.url
        elif self.media_file:
            return self.media_file.url
        else:
            return settings.STATIC_URL + f"{settings.STATIC_URL}/arch_app/icons/{self.type.lower()}_preview.png"


@receiver(models.signals.post_save, sender=Record)
def create_user_group(sender, instance, created, **kwargs):
    """ Automatically creates a Group of Users who can access the record """
    if created:
        instance.depicted_users = Group.objects.create(
            name=f"Record Group ({str(instance.id)})"
        )
        assign_perm('view_record', instance.depicted_users, instance)
        instance.save()


@receiver(models.signals.post_delete, sender=Record)
def delete_user_group(sender, instance, **kwargs):
    """ Automatically deletes the group of users who can access the record """
    if instance.depicted_users:
        instance.depicted_users.delete()


@receiver(models.signals.post_delete, sender=Record)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when corresponding Record object is deleted.
    """
    if instance.media_file:
        media_file_path = instance.media_file.path
        if os.path.isfile(media_file_path):
            os.remove(media_file_path)
    if instance.preview_file:
        preview_file_path = instance.preview_file.path
        if os.path.isfile(preview_file_path):
            os.remove(preview_file_path)
    else:
        return False


@receiver(models.signals.pre_save, sender=Record)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem when Record object is updated with new file.
    """
    if not instance.pk:
        return False
    try:
        old_file = instance.media_file
    except Record.DoesNotExist:
        return False

    new_file = instance.media_file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(models.signals.post_delete, sender=Record)
def auto_delete_location_on_delete(sender, instance, **kwargs):
    """
    Deletes location from database when corresponding Record object is deleted.
    """
    if instance.location:
        instance.location.delete()


class Tag(models.Model):
    """ a Tag to a Record """
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='tags', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    visibility_level = [
        ('visible', 'visible'),
        ('hidden_by_user', 'hidden_by_user'),
        ('hidden_by_mod', 'hidden_by_mod')
    ]
    visible = models.CharField(max_length=19, choices=visibility_level, default='visible')

    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} on {self.record.title}"


class TagBox(Tag):
    """ Boundary Box on an image """
    x1 = models.IntegerField()
    y1 = models.IntegerField()
    x2 = models.IntegerField()
    y2 = models.IntegerField()
    height = models.IntegerField()
    width = models.IntegerField()

    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} on {self.record.title}"


@receiver(pre_save, sender=Tag)
@receiver(pre_save, sender=TagBox)
def update_user_on_save(sender, instance, **kwargs):
    """
    Adds and updates the tagged user to the record
    """
    # get former user if it exists
    old_user = None
    if instance.id:
        old_user = Tag.objects.filter(id=instance.id).first().user
    # remove old user from record
    if old_user:
        # check if another tag or tagbox with the same user exists for that record
        if not (Tag.objects.filter(user=old_user, record=instance.record).exclude(pk=instance.pk).exists() or
                TagBox.objects.filter(user=old_user, record=instance.record).exclude(pk=instance.pk).exists()):
            instance.record.depicted_users.user_set.remove(old_user)
    # add new user to record
    if instance.user and instance.visible == 'visible':
        instance.record.depicted_users.user_set.add(instance.user)
    instance.record.save()
    return True


@receiver(models.signals.pre_delete, sender=Tag)
def remove_user_on_delete(sender, instance, **kwargs):
    """
    deletes the tagged user on the record
    """
    # check if user exists
    if instance.user:
        # check if another tag or tagbox with the same user exists for that record
        if not (Tag.objects.filter(user=instance.user, record=instance.record).exclude(pk=instance.pk).exists() or
                TagBox.objects.filter(user=instance.user, record=instance.record).exclude(pk=instance.pk).exists()):
            instance.record.depicted_users.user_set.remove(instance.user)
    instance.record.save()
    return True


class Reaction(models.Model):
    """ a Reaction to a Record """
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    REACTION_TYPES = (
        ('1', 'Smiley'),
        ('2', 'Laughing'),
        ('3', 'Sweat Smile'),
        ('4', 'Heart')
    )
    reaction_type = models.CharField(max_length=19, choices=REACTION_TYPES, null=True)


class Comment(models.Model):
    """ a comment on a Record entry """
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    text = models.TextField(max_length=1024)
    created_on = models.DateTimeField(auto_now_add=True)
    visibility_level = [
        ('visible', 'visible'),
        ('hidden_by_user', 'hidden_by_user'),
        ('hidden_by_mod', 'hidden_by_mod')
    ]
    visible = models.CharField(max_length=19, choices=visibility_level, default='visible')

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment "{}" by {}'.format(self.text, self.user.username)


# adapted from https://github.com/jose-lpa/django-tracking-analyzer
class Tracker(models.Model):
    """
    A generic tracker model, which can be related to any other model to track
    actions that involves it.
    """
    PC = 'pc'
    MOBILE = 'mobile'
    TABLET = 'tablet'
    BOT = 'bot'
    UNKNOWN = 'unknown'
    DEVICE_TYPE = (
        (PC, 'PC'),
        (MOBILE, 'Mobile'),
        (TABLET, 'Tablet'),
        (BOT, 'Bot'),
        (UNKNOWN, 'Unknown'),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    referrer = models.URLField(blank=True)
    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE,
        default=UNKNOWN
    )
    # device = models.CharField(max_length=30, blank=True)
    # browser = models.CharField(max_length=30, blank=True)
    # browser_version = models.CharField(max_length=30, blank=True)
    # system = models.CharField(max_length=30, blank=True)
    # system_version = models.CharField(max_length=30, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    objects = TrackerManager()

    def __str__(self):
        return '{0} :: {1}, {2}'.format(
            self.content_object, self.user, self.timestamp)
