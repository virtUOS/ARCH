"""
module for converting media files to browser compatible formats
"""
import os
from pathlib import Path
from ffmpeg import FFmpeg
from arch_app.models import Record

import logging
console_logger = logging.getLogger('ARCH_console_logger')
file_logger = logging.getLogger('ARCH_file_logger')


def convert_file(source: Path, target: Path) -> Path:
    """
    Convert a media file to a given format.
    :param source: path to the source file
    :param target: path to the target file
    :return: path to the converted file
    """
    try:
        FFmpeg().input(source).output(target).execute()
        return target
    except Exception as e:
        console_logger.error(f"Error while converting file: {e}")
        file_logger.error(f"Error while converting file: {e}")
        raise e


video_formats_to_convert = ["quicktime", "mov", "mpeg", "avi", "wmv", "x-msvideo", "x-ms-asf", "x-ms-wmv"]
audio_formats_to_convert = ['wma', 'aac']

def generate_preview(record: Record, file_extension: str, subtype) -> Path | None:
    """
    Generate a preview file in a browser compatible format for a given record.
    :param record: record object
    :param file_extension: file extension of the media file
    :param subtype: subtype of the media file
    :return: path to the preview file or None
    """
    try:
        match record.type:
            case 'Video':  # convert to mp4 and save as preview
                if file_extension in video_formats_to_convert or subtype in video_formats_to_convert:
                    target = os.path.splitext(record.media_file.path)[0].replace(record.title, "preview.mp4")
                    return convert_file(source=record.media_file.path, target=target)
            case 'Audio':  # convert to mp3 and save as preview
                if file_extension in audio_formats_to_convert:
                    target = os.path.splitext(record.media_file.path)[0].replace(record.title, "preview.mp3")
                    return convert_file(source=record.media_file.path, target=target)
            case 'Image':  # save original image as preview
                with open(record.media_file.path, 'rb') as media_file:
                    record.preview_file.save(f"preview.{file_extension}", media_file, save=True)
                    return record.preview_file.path
            case _:  # no preview for other types, e.g. text documents, so return True
                return None
        return None
    except Exception as e:
        console_logger.error(f"Error while generating preview for {record.type}: {e}")
        file_logger.error(f"Error while generating preview {record.type}: {e}")
        return None
