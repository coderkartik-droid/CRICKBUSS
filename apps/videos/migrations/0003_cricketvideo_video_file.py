"""
Migration: replace video_url (URLField) with video_file (FileField) on CricketVideo.

Strategy:
  1. Add video_file as nullable so existing rows are not blocked.
  2. Remove video_url.
  3. Alter video_file to non-nullable.

Step 3 will fail if any existing rows still have a NULL video_file after step 2.
In practice this is fine for a fresh / dev database.  If you have production rows
that must be preserved, populate video_file before applying step 3 (or keep the
field nullable permanently and handle the empty case in templates).
"""

import apps.videos.storages
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0002_uploadedvideo'),
    ]

    operations = [
        # Step 1 – add the new field as nullable (avoids "non-nullable with no
        # default" error when existing rows are present).
        migrations.AddField(
            model_name='cricketvideo',
            name='video_file',
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.videos.storages.video_storage,
                upload_to='videos/uploads/%Y/%m/',
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['mp4', 'webm', 'mov', 'avi', 'mkv']
                    )
                ],
                verbose_name='video file',
            ),
        ),

        # Step 2 – drop the old URL field.
        migrations.RemoveField(
            model_name='cricketvideo',
            name='video_url',
        ),

        # Step 3 – tighten to non-nullable now that video_url is gone.
        # Any existing row that has NULL in video_file will keep NULL until the
        # admin re-uploads; the form requires a file on create but not on edit,
        # matching Django's standard FileField behaviour.
        migrations.AlterField(
            model_name='cricketvideo',
            name='video_file',
            field=models.FileField(
                storage=apps.videos.storages.video_storage,
                upload_to='videos/uploads/%Y/%m/',
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['mp4', 'webm', 'mov', 'avi', 'mkv']
                    )
                ],
                verbose_name='video file',
            ),
        ),
    ]
