import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class PhotoAlbum(models.Model):
    class AlbumCategory(models.TextChoices):
        MATCH = 'match', _('Match Action Photos')
        PLAYER = 'player', _('Player Portraits & Moments')
        TEAM = 'team', _('Team Celebrations & Squads')
        STADIUM = 'stadium', _('Venues & Stadiums')
        CEREMONY = 'ceremony', _('Awards & Ceremonies')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('album title'), max_length=150)
    slug = models.SlugField(_('slug URL'), max_length=170, unique=True, blank=True)
    category = models.CharField(_('album category'), max_length=20, choices=AlbumCategory.choices, default=AlbumCategory.MATCH)
    description = models.TextField(_('album description'), blank=True)
    cover_image = models.ImageField(_('album cover image'), upload_to='photos/covers/%Y/%m/', blank=True, null=True)

    match = models.ForeignKey('matches.Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='photo_albums')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Photo Album')
        verbose_name_plural = _('Photo Albums')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:160]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('photos:album_detail', kwargs={'slug': self.slug})

    def get_cover_url(self):
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        first_photo = self.photos.first()
        if first_photo and first_photo.image:
            return first_photo.image.url
        return 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800&q=80'


class PhotoItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(_('photo image'), upload_to='photos/gallery/%Y/%m/')
    caption = models.CharField(_('caption'), max_length=255, blank=True)
    photo_credit = models.CharField(_('credit / photographer'), max_length=100, default='CrickScore Media')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Photo Item')
        verbose_name_plural = _('Photo Items')
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.caption or f"Photo in {self.album.title}"
