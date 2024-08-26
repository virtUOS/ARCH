"""

"""
import os
from sentence_transformers import SentenceTransformer
from django.conf import settings
from PIL import Image, UnidentifiedImageError

# global variables
img_model = None
text_model = None


def init_ai_models():
    """
    Load the AI models for image and text embeddings.
    """
    # get directory from settings
    global img_model, text_model
    img_model_path = os.path.join(settings.BASE_DIR, 'arch_app/ai_models/clip-ViT-B-32')
    text_model_path = os.path.join(settings.BASE_DIR, 'arch_app/ai_models/clip-ViT-B-32-multilingual-v1')
    print("load AI models ...")
    try:
        img_model = SentenceTransformer(img_model_path, local_files_only=True)
        text_model = SentenceTransformer(text_model_path, local_files_only=True)
        print('AI search models loaded locally')
    except ValueError:
        img_model = SentenceTransformer('clip-ViT-B-32')
        img_model.save(img_model_path)
        text_model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')
        text_model.save(text_model_path)
        print('AI search models loaded from huggingface.co')
    # Quantize the models
    if settings.QUANTIZE_CLIP_MODELS:
        from torch.quantization import quantize_dynamic
        import torch
        import torch.nn as nn
        img_model = quantize_dynamic(img_model, {nn.Linear}, dtype=torch.qint8)
        text_model = quantize_dynamic(text_model, {nn.Linear}, dtype=torch.qint8)


def generate_image_embedding(image_path):
    """ Generate an image embedding for a given image.
    :param image_path: path to the image
    returns image embedding or False
    """
    if img_model is None:
        init_ai_models()
    try:
        img = Image.open(image_path)
    except UnidentifiedImageError:
        return False
    img_emb = img_model.encode(img, show_progress_bar=True)
    img.close()
    return img_emb


def generate_text_embedding(sentences):
    """
    Encode a text query:
    :param sentences: string
    """
    if text_model is None:
        init_ai_models()
    text_emb = text_model.encode(sentences)
    return text_emb
