import os
from django.db import models
from django.http import HttpRequest
from django.core.files.base import ContentFile


class RecordManager(models.Manager):
    """
    Manager for Record model
    """

    def create_record(self, media_type, title, album, creator, file_read, file_name, date_created=None):
        """
        creates a record object and saves it to the database
        params:
            media_type: type of media e.g. image, video, audio, text, other
            title: title of the record
            album: album the record belongs to
            creator: creator of the record
            file_read: file object
            file_name: name of the file
            date_created: date of creation of the record
        """
        file_name_ext = os.path.basename(file_name)
        record = self.model.objects.create(title=title,
                                           type=media_type,
                                           album=album,
                                           creator=creator,
                                           date_created=date_created
                                           )
        record.media_file.save(file_name_ext, ContentFile(file_read))
        record.save()
        return record


# adapted from https://github.com/jose-lpa/django-tracking-analyzer
class TrackerManager(models.Manager):
    """
    Custom ``Tracker`` model manager that implements a method to create a new
    object instance from an HTTP request.
    """

    def create_from_request(self, request, content_object, user=None):
        """
        Given an ``HTTPRequest`` object and a generic content, it creates a
        ``Tracker`` object to store the data of that request.

        :param request: A Django ``HTTPRequest`` object.
        :param content_object: A Django model instance. Any object can be
        related.
        :param user: A Django ``User`` instance. It can be ``None``.
        :return: A newly created ``Tracker`` instance.
        """
        # Sanity checks.
        assert isinstance(request, HttpRequest), \
            '`request` object is not an `HTTPRequest`'
        assert issubclass(content_object.__class__, models.Model), \
            '`content_object` is not a Django model'

        # if request.user_agent.is_mobile:
        #     device_type = self.model.MOBILE
        # elif request.user_agent.is_tablet:
        #     device_type = self.model.TABLET
        # elif request.user_agent.is_pc:
        #     device_type = self.model.PC
        # elif request.user_agent.is_bot:
        #     device_type = self.model.BOT
        # else:
        #     device_type = self.model.UNKNOWN

        tracker = self.model.objects.create(
            content_object=content_object,
            referrer=request.META.get('HTTP_REFERER', ''),
            # device_type=device_type,
            # device=request.user_agent.device.family,
            # browser=request.user_agent.browser.family[:30],
            # browser_version=request.user_agent.browser.version_string,
            # system=request.user_agent.os.family,
            # system_version=request.user_agent.os.version_string,
            user=user
        )

        return tracker
