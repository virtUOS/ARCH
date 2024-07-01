import os
import magic
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat


@deconstructible
class FileValidator(object):
    """
    a File Validator class which validates the file size, content type and file format of a file.

    The class is initialized with the maximum file size, the acceptable content types, and the supported formats.
    When called, it checks if the file size is within the maximum limit, if the content type is in the acceptable types,
    and if the file format is among the supported formats. If any of these checks fail, it raises a ValidationError.
    The class also provides error messages for each of the checks.

    :param max_size: maximum file size in bytes
    :param content_types: list of acceptable content types
    :param supported_formats: list of supported formats
    """
    error_messages = {
        'max_size': ("Ensure this file size is not greater than %(max_size)s."
                     " Your file size is %(size)s."),
        'content_type': "Files of type %(content_type)s are not supported.",
        'file_format': "Files in the format %(file_format) are not supported.",
        'file_extension': "File extension %(file_extension)s does not match the file content."
                          "File content seems to be in the format %(file_format)s"
    }

    def __init__(self, max_size=None, content_types=(), supported_formats=()):
        self.max_size = max_size
        self.content_types = content_types
        self.supported_formats = supported_formats

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                'max_size': filesizeformat(self.max_size),
                'size': filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages['max_size'],
                                  'max_size', params)
        # extract file mime type
        mime = magic.Magic(mime=True)
        file = data.read()
        file_extension = os.path.splitext(data.name)[1][1:].lower()
        file_mime_type = mime.from_buffer(file)
        (file_content_type, file_format) = file_mime_type.split("/")

        # normalize file format extension
        if file_extension in ['jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi']:
            file_extension = 'jpeg'
        if file_extension in ['mov', 'qt']:
            file_extension = 'quicktime'

        if self.content_types:
            if file_content_type not in self.content_types:
                params = {'content_type': file_content_type}
                raise ValidationError(self.error_messages['content_type'],
                                      'content_type', params)

        # check if file extension matches
        # if file_extension not in file_format:
        #     params = {
        #         'file_format': file_format,
        #         'file_extension': file_extension
        #     }
        #     raise ValidationError(self.error_messages['file_extension'],
        #                           'file_extension', params)

        # check if format is supported
        if self.supported_formats:
            if file_format not in self.supported_formats:
                params = {'file_format': file_format}
                raise ValidationError(self.error_messages['file_format'],
                                      'file_format', params)

    def __eq__(self, other):
        return (
                isinstance(other, FileValidator) and
                self.max_size == other.max_size and
                self.content_types == other.content_types and
                self.supported_formats == other.supported_formats
        )
