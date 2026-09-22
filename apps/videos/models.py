import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

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
    video_url = models.URLField(_('video streaming or embed link (YouTube / MP4)'), max_length=300)
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:190]
        super().save(*args, **kwargs)

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
