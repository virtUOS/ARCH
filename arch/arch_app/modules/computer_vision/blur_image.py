from PIL import Image, ImageFilter


def blur_image(image_path, coordinates=(0, 0, 0, 0)):
    """
    Blur image at the given box coordinates
    :param image_path: path to image
    :param coordinates: box coordinates (x1, y1, x2, y2)
    """
    (x1, y1, x2, y2) = coordinates  # x1 is lower than x2 and y1 is lower than y2
    # get image
    img = Image.open(image_path)
    # # rotate image if necessary
    img = rotate_image(img)
    # crop rectangle at tag box coordinates.
    crop_img = img.crop(box=(x1, y1, x2, y2))
    # get radius based on the size of the tagbox
    radius = max(5, int((x2 - x1 + y2 - y1) / 20))
    # blur the cropped image
    blurred_image = crop_img.filter(ImageFilter.BoxBlur(radius=radius))
    # paste the blurred image back into the original image.
    img.paste(blurred_image, box=(x1, y1, x2, y2))
    # # rotate image back to original orientation
    img = rotate_image(img, reverse=True)
    # if image is not RGB, convert it to RGB (to prevent errors when saving png or jpg in RGBA)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    try:
        img.save(image_path, exif=img.info['exif'])
    except KeyError or AttributeError:
        img.save(image_path)
    img.close()
    return True


def unblur_image(image_path, original_file_path, coordinates=(0, 0, 0, 0)):
    """
    Unblur image at the given box coordinates and replace it with the original image
    :param image_path: path to image which should be unblurred
    :param original_file_path: path to original image
    :param coordinates: box coordinates (x1, y1, x2, y2)
    """
    (x1, y1, x2, y2) = coordinates
    # get blurred image
    blurred_img = Image.open(image_path)
    # rotate image if necessary
    blurred_img = rotate_image(blurred_img)
    # get original image
    original_img = Image.open(original_file_path)
    # rotate image if necessary
    original_img = rotate_image(original_img)
    # crop rectangle at tag box coordinates
    crop_img = original_img.crop((x1, y1, x2, y2))
    # replace the pixels of the blurred image with the pixels of the original image
    blurred_img.paste(crop_img, (x1, y1, x2, y2))
    # rotate image back to original orientation
    blurred_img = rotate_image(blurred_img, reverse=True)
    # if image is not RGB, convert it to RGB (to prevent errors when saving png or jpg in RGBA)
    if blurred_img.mode in ("RGBA"):
        blurred_img = blurred_img.convert("RGB")
    # save image
    try:
        blurred_img.save(image_path, exif=blurred_img.info['exif'])
    except KeyError or AttributeError:
        blurred_img.save(image_path)
    blurred_img.close()
    original_img.close()
    return True


def rotate_image(image, reverse=False):
    """
    Rotate image according to orientation tag in exif data
    :param image: image, opened with PIL.Image.open()
    :param reverse: boolean, whether to rotate image in reverse direction
    """
    exif_data = image.getexif()
    degree = 0
    if exif_data and exif_data.get(274) and exif_data[274] != 1:
        if exif_data[274] == 3:
            degree = 180
        elif exif_data[274] == 6:
            degree = 270
        elif exif_data[274] == 8:
            degree = 90
    if reverse and degree != 0:
        degree = 360 - degree
    image = image.rotate(degree, expand=True)
    return image
