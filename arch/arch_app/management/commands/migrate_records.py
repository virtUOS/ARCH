import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from arch_app.models import *
from shutil import copyfile


class Command(BaseCommand):
    help = 'moves records to a different folder structure'

    def handle(self, *args, **options):
        print("start moving records ...")

        records = Record.objects.all()
        for r in records:
            old_path = r.media_file.path
            new_path = old_path.replace(
                "archive",
                f"archive_{str(r.album.archive.id)}/records"
            )

            # create new folder if it doesn't exist
            if not os.path.exists(os.path.dirname(new_path)):
                os.makedirs(os.path.dirname(new_path))
            copyfile(old_path, new_path)

            # open new file and save it to the record
            with open(new_path, 'rb') as f:
                # process file
                file_read = f.read()
                r.media_file.save(os.path.basename(f.name), ContentFile(file_read))

            r.save()

        print("finished moving records ...")
