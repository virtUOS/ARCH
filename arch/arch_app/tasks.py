""" Django Q2 tasks for asynchronous processing of tasks """
import os
from .models import Record, TagBox
from PIL import Image

from django.conf import settings
if settings.ACTIVATE_AI_SEARCH:
    from .modules.embeddings.text_image_embedding import generate_image_embedding
if settings.ACTIVATE_FACE_DETECTION:
    from .modules.computer_vision.face_detection import detect_faces

import logging
console_logger = logging.getLogger('ARCH_console_logger')
file_logger = logging.getLogger('ARCH_file_logger')


def create_tagboxes_and_save(record_id):
    """
    Create TagBox objects for a given record, based on the detected faces.
    :param record_id: id of the record
    """
    try:
        record = Record.objects.get(id=record_id)
    except Record.DoesNotExist:
        console_logger.error(f"Error when trying to create tagboxes. Record with id {record_id} does not exist.")
        file_logger.error(f"Error when trying to create tagboxes. Record with id {record_id} does not exist.")
        return False
    img = Image.open(record.media_file.path)
    width, height = img.size
    faces = detect_faces(image_path=record.media_file.path)
    for face in faces:
        x1, y1, x2, y2 = face
        record = Record.objects.get(id=record_id)  # reload record to avoid concurrency issues
        tagbox = TagBox(record=record, x1=x1, y1=y1, x2=x2, y2=y2, height=height, width=width)
        tagbox.save()
    img.close()
    return True


def generate_preview_and_save(record_id, file_extension, mime_type, subtype):
    """ Generate a preview file for a given record.

    Generates MP4 preview for MOV, MPG, AVI and WMV video files.
    Generates MP3 preview for WMA and AAC audio files.
    """
    try:
        record = Record.objects.get(id=record_id)
    except Record.DoesNotExist:
        console_logger.error(f"Error when trying to generate preview. Record with id {record_id} does not exist.")
        file_logger.error(f"Error when trying to generate preview. Record with id {record_id} does not exist.")
        return False

    to_convert = ["quicktime", "mov", "mpeg", "avi", "wmv", "x-msvideo", "x-ms-asf", "x-ms-wmv"]
    if record.type == 'Video' and file_extension in to_convert or subtype in to_convert:
        try:
            source = record.media_file.path
            target = os.path.splitext(source)[0] + ".mp4"
            os.system(f"ffmpeg -i {source} -qscale 0 {target}")
            with open(target, 'rb') as target_file:
                record = Record.objects.get(id=record_id)  # reload record to avoid concurrency issues
                record.preview_file.save("preview.mp4", target_file, save=True)
            os.remove(target)
        except Exception as e:
            console_logger.error(f"Error while converting video file: {e}")
            file_logger.error(f"Error while converting video file: {e}")
            pass
    if record.type == 'Audio' and file_extension in ['wma', 'aac']:
        try:
            source = record.media_file.path
            target = os.path.splitext(source)[0] + ".mp3"
            os.system(f"ffmpeg -i {source} -qscale 0 {target}")
            with open(target, 'rb') as target_file:
                record = Record.objects.get(id=record_id)  # reload record to avoid concurrency issues
                record.preview_file.save("preview.mp3", target_file, save=True)
            os.remove(target)
        except Exception as e:
            console_logger.error(f"Error while converting audio file: {e}")
            file_logger.error(f"Error while converting audio file: {e}")
            pass
    if record.type == 'Image':
        try:
            with open(record.media_file.path, 'rb') as media_file:
                record = Record.objects.get(id=record_id)  # reload record to avoid concurrency issues
                record.preview_file.save(f"preview.{file_extension}", media_file, save=True)
        except Exception as e:
            console_logger.error(f"Error while saving image preview: {e}")
            file_logger.error(f"Error while saving image preview: {e}")
            pass
    return True


def generate_image_embedding_and_save(record_id):
    """
    Generate an image embedding for a given record and save it.
    :param record_id: id of the record
    """
    try:
        record = Record.objects.get(id=record_id)
    except Record.DoesNotExist:
        console_logger.error(f"Error when trying to generate image embedding. Record with id {record_id} does not exist.")
        file_logger.error(f"Error when trying to generate image embedding. Record with id {record_id} does not exist.")
        return False
    img_emb = generate_image_embedding(record.media_file.path)
    if img_emb is False:
        return False
    record = Record.objects.get(id=record_id)  # reload record to avoid concurrency issues
    record.embedding = img_emb.tolist()
    record.save()
    return True
