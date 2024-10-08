"""
This script is used to zip the archive folders and store them locally in the media folder.
"""
import os

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import zipfile
from arch_app.models import Archive, Album, Record


class Command(BaseCommand):
    help = 'zips the archive folders and stores them locally in the media folder'

    def add_arguments(self, parser):
        parser.add_argument('archive_id', nargs='?', type=int, help='id of the Archive to zip')
        parser.add_argument('--all', action='store_true', help='zip all archives')

    def handle(self, *args, **options):
        self.stdout.write('Start zipping archive folders ...')
        if options['archive_id']:
            try:
                archive = Archive.objects.get(id=options['archive_id'])
            except Archive.DoesNotExist:
                raise CommandError('Archive "%s" does not exist' % options['archive_id'])
            archives = [archive]
        elif options['all']:
            archives = Archive.objects.all()
        else:
            raise CommandError('Please provide an archive id or use the --all flag to zip all albums.')

        for archive in archives:
            self.stdout.write(f"zipping archive folder {archive.name} ...")
            archive_path = os.path.join(settings.MEDIA_ROOT, f"archive_{archive.id}")
            if not os.path.exists(archive_path):
                self.stdout.write(f"Archive folder {archive.name} does not exist.")
                continue
            zip_file_path = os.path.join(archive_path, f"archive_{archive.name}.zip")
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                albums = Album.objects.filter(archive=archive, is_inbox=False)
                for album in albums:
                    records = Record.objects.filter(album=album)
                    for record in records:
                        zipf.write(
                            record.media_file.path,
                            os.path.join(album.title, record.title)
                        )
                    # create json file in the zip album folder with the metadata
                    metadata = {
                        "title": album.title,
                        "description": album.description,
                        "creator": str(album.creator),
                        "start_date": str(album.get_start_date),
                        "end_date": str(album.get_end_date),
                        "members": [str(u) for u in album.group.user_set.all()],
                        "records": [r.title for r in records]
                    }
                    zipf.writestr(os.path.join(album.title, 'metadata.json'), str(metadata))
                    serialized_album = serializers.serialize('json', [album])
                    zipf.writestr(os.path.join(album.title, 'album_serialized.json'), serialized_album)
            self.stdout.write(self.style.SUCCESS(f'Successfully created zip files for the archive {archive.name}.'))

        self.stdout.write(self.style.SUCCESS('Successfully created zip files for the archive locally.'))
