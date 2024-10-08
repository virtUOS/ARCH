"""
This script loads the AI models and stores them locally in the project folder.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from sentence_transformers import SentenceTransformer


class Command(BaseCommand):
    help = 'loads AI models and stores them locally in the project folder'

    def handle(self, *args, **options):
        print("load AI models ...")
        img_model_path = os.path.join(settings.BASE_DIR, 'arch_app/ai_models/clip-ViT-B-32')
        text_model_path = os.path.join(settings.BASE_DIR, 'arch_app/ai_models/clip-ViT-B-32-multilingual-v1')
        SentenceTransformer('clip-ViT-B-32').save(img_model_path)
        SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1').save(text_model_path)
        self.stdout.write(self.style.SUCCESS('Successfully saved AI models locally.'))
