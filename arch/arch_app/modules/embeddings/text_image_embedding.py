from sentence_transformers import SentenceTransformer
from django.conf import settings
from PIL import Image, UnidentifiedImageError


model = SentenceTransformer('clip-ViT-B-32')

text_model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')
print('AI search models loaded...')

# Quantize the models
if settings.QUANTIZE_CLIP_MODELS:
    from torch.quantization import quantize_dynamic
    import torch
    import torch.nn as nn

    model = quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8)
    text_model = quantize_dynamic(text_model, {nn.Linear}, dtype=torch.qint8)


def generate_image_embedding(image_path):
    """ Generate an image embedding for a given image.
    :param image_path: path to the image
    returns image embedding or False
    """
    try:
        img = Image.open(image_path)
    except UnidentifiedImageError:
        return False
    img_emb = model.encode(img, show_progress_bar=True)
    img.close()
    return img_emb


def generate_text_embedding(sentences):
    """
    Encode a text query:
    :param sentences: string
    """
    text_emb = text_model.encode(sentences)
    return text_emb
