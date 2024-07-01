import exifread
from exifread.heic import NoParser
import magic  # https://pypi.org/project/python-magic/')
# install libmagic: sudo apt-get install libmagic1
import reverse_geocoder as rg  # https://pypi.org/project/reverse_geocoder/
# Reverse Geocoding uses data from the GeoNames geographical database (https://www.geonames.org/ )
from datetime import datetime

import logging
console_logger = logging.getLogger('ARCH_console_logger')


def extract_metadata(f):
    """""
    extracts metadata from file and returns it as a dictionary
    params:
        f = file, assumes the file is already opened
    """""
    metadata = {'date_created': None,
                'location': None}
    try:
        # Get the metadata tags using exifread
        tags = exifread.process_file(f)
    except NoParser as err:
        console_logger.error(f'Error extracting metadata: {err}')
        return metadata
    except Exception as err:
        print(f'Error extracting metadata: {err}')
        return metadata

    # extract date of creation
    if 'EXIF DateTimeOriginal' in tags.keys():
        metadata['date_created'] = datetime.strptime(str(tags['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
    elif 'QuickTime:CreationDate' in tags.keys():
        metadata['date_created'] = datetime.strptime(str(tags['QuickTime:CreationDate']), '%Y:%m:%d %H:%M:%S')

    # extract location
    if 'GPS GPSLatitude' in tags.keys() and 'GPS GPSLongitude' in tags.keys():
        latitude_tag = tags.get('GPS GPSLatitude').values
        longitude_tag = tags.get('GPS GPSLongitude').values
        coordinates = (convert_to_degrees(latitude_tag),
                       convert_to_degrees(longitude_tag))
        # latitudes and longitudes are reverse geocoded to determine City, State, and Country.
        results = rg.search(coordinates, mode=1)  # mode 1 is for Single-threaded K-D Tree processing
        metadata['location'] = results[0]
    elif 'QuickTime:Location' in tags.keys():
        metadata["location"] = tags['QuickTime:Location']

    return metadata


def convert_to_degrees(value):
    """ Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format """
    degrees = value[0].num / value[0].den if value[0].den else 0
    minutes = value[1].num / value[1].den / 60.0 if value[1].den else 0
    seconds = value[2].num / value[2].den / 3600.0 if value[2].den else 0
    return degrees + minutes + seconds


def determine_type(file_read, file_name):
    """
    returns the mime_type, subtype and extension of the file e.g. ('image', 'jpeg', 'jpg')
    """
    mime = magic.Magic(mime=True)
    mime_type, subtype = mime.from_buffer(file_read).split('/')  # e.g. ['image', 'jpeg']
    file_extension = file_name.split('.')[-1]

    if mime_type in ['image', 'video', 'audio']:
        if file_extension in ['wma']:
            return 'audio', subtype, file_extension
        return mime_type, subtype, file_extension
    elif mime_type == "text" or file_extension in ['pdf', 'txt', 'odt', 'doc', 'docx']:
        return 'text', subtype, file_extension
    else:
        return 'other', subtype, file_extension
