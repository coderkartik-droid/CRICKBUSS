import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class NewsCategory(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _('News Category')
        verbose_name_plural = _('News Categories')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('article headline'), max_length=200)
    slug = models.SlugField(_('slug URL'), max_length=220, unique=True, blank=True)
    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE, related_name='articles')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='written_articles'
    )
    author_name_fallback = models.CharField(max_length=100, default='CrickScore Editorial Team')

    featured_image = models.ImageField(upload_to='news/images/%Y/%m/', blank=True, null=True)
    excerpt = models.TextField(_('summary / deck line'), max_length=300)
    content = models.TextField(_('full article body (HTML/Markdown)'))

    # Relations
    related_series = models.ForeignKey('series.Series', on_delete=models.SET_NULL, null=True, blank=True, related_name='news')
    related_match = models.ForeignKey('matches.Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='news')

    # Metrics & Flags
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    is_breaking = models.BooleanField(_('breaking news ticker'), default=False)
    is_trending = models.BooleanField(_('trending story'), default=False)
    is_featured = models.BooleanField(_('lead hero story'), default=False)
    is_published = models.BooleanField(default=True)

    # SEO fields
    meta_keywords = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('News Article')
        verbose_name_plural = _('News Articles')
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_breaking', 'is_published']),
            models.Index(fields=['is_trending']),
            models.Index(fields=['-published_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:210]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:article_detail', kwargs={'slug': self.slug})

    def get_image_url(self):
        if self.featured_image and hasattr(self.featured_image, 'url'):
            return self.featured_image.url
        return 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800&q=80'


class ArticleComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField(_('comment message'), max_length=1000)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Article Comment')
        verbose_name_plural = _('Article Comments')

    def __str__(self):
        return f"Comment by {self.user} on {self.article.title[:30]}"


class ArticleLike(models.Model):
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'user')


class ArticleBookmark(models.Model):
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='news_bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'user')
        ordering = ['-created_at']
