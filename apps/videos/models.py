import uuid
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .storages import video_storage
from .media_processing import extract_video_metadata

CRICKET_VIDEO_EXTENSIONS = ['mp4', 'webm', 'mov', 'avi', 'mkv']


class VideoCategory(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Video Category')
        verbose_name_plural = _('Video Categories')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CricketVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('video title'), max_length=180)
    slug = models.SlugField(_('slug URL'), max_length=200, unique=True, blank=True)
    category = models.ForeignKey(VideoCategory, on_delete=models.CASCADE, related_name='videos')
    description = models.TextField(_('video description'), blank=True)

    thumbnail = models.ImageField(_('thumbnail'), upload_to='videos/thumbnails/%Y/%m/', blank=True, null=True)
    video_file = models.FileField(
        _('video file'),
        upload_to='videos/uploads/%Y/%m/',
        storage=video_storage,
        validators=[FileExtensionValidator(allowed_extensions=CRICKET_VIDEO_EXTENSIONS)],
    )
    duration = models.CharField(_('duration (e.g. 05:42)'), max_length=15, default='04:30')

    # Relations
    match = models.ForeignKey('matches.Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    series = models.ForeignKey('series.Series', on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')

    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Cricket Video')
        verbose_name_plural = _('Cricket Videos')
        ordering = ['-created_at']

    def _get_unique_slug(self):
        base_slug = slugify(self.title) or 'video'
        base_slug = base_slug[:200]
        candidate = base_slug
        suffix = 1

        existing = type(self).objects.filter(slug=candidate)
        if self.pk:
            existing = existing.exclude(pk=self.pk)

        while existing.exists():
            suffix_text = f'-{suffix}'
            candidate = f'{base_slug[:200 - len(suffix_text)]}{suffix_text}'
            existing = type(self).objects.filter(slug=candidate)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            suffix += 1

        return candidate

    def save(self, *args, **kwargs):
        previous_file_name = None
        previous_title = None
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).only(
                'title', 'video_file', 'thumbnail', 'slug'
            ).first()
            if previous:
                previous_title = previous.title
                previous_file_name = previous.video_file.name if previous.video_file else None
        metadata_required = bool(
            self.video_file
            and (
                not self.thumbnail
                or not self.duration
                or previous_file_name != self.video_file.name
            )
        )
        if not self.pk or not self.slug or previous_title != self.title:
            self.slug = self._get_unique_slug()
        super().save(*args, **kwargs)
        if metadata_required:
            duration, thumbnail = extract_video_metadata(self.video_file)
            self.duration = duration
            self.thumbnail.save(
                f'{self.slug or self.pk}.jpg',
                thumbnail,
                save=False,
            )
            super().save(update_fields=['duration', 'thumbnail'])

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('videos:video_detail', kwargs={'slug': self.slug})

    def get_thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        return 'https://images.unsplash.com/photo-1531415074868-036b1c5f53ec?w=800&q=80'


class VideoLike(models.Model):
    video = models.ForeignKey(CricketVideo, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'user')


class VideoBookmark(models.Model):
    video = models.ForeignKey(CricketVideo, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'user')


class UploadedVideo(models.Model):
    """A video file uploaded straight from the admin portal.

    This covers the simple upload-and-play workflow (video title and video file
    only).  It is deliberately kept separate from :class:`CricketVideo`, whose
    records point at an external streaming link and require a category.
    """

    ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv', 'webm']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('video title'), max_length=180)
    video_file = models.FileField(
        _('video file'),
        upload_to='videos/uploads/%Y/%m/',
        storage=video_storage,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_VIDEO_EXTENSIONS)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Uploaded Video')
        verbose_name_plural = _('Uploaded Videos')
        ordering = ['-created_at']

    def __str__(self):
        return self.title
