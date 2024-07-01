import os
from django.core.management.base import BaseCommand
from arch_app.models import Record
from arch_app.modules.embeddings.text_image_embedding import generate_image_embedding


class Command(BaseCommand):
    help = 'regenerate embeddings for all records'

    def handle(self, *args, **options):
        print("start regenerating image embeddings ...")

        count = 0
        records = Record.objects.filter(type='Image')
        for r in records:
            img_emb = generate_image_embedding(r.media_file.path)
            if img_emb is False:
                return False
            r.embedding = img_emb.tolist()
            r.save()
            count += 1

        print("finished regenerating image embeddings.")
        print(f"Regenerated {count} image embeddings.")
