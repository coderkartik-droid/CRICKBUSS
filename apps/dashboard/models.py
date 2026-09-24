import uuid

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ContactMessage(models.Model):
    """A message submitted through the public Contact Us form.

    Stored for review in the Admin Portal inbox. No login and no email are
    required from the visitor; the message is simply persisted here.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(_('full name'), max_length=120)
    mobile_number = models.CharField(_('mobile number'), max_length=30, default='')
    email = models.EmailField(_('email address'))
    subject = models.CharField(_('subject'), max_length=200)
    message = models.TextField(_('message'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_read = models.BooleanField(_('read'), default=False)
    is_replied = models.BooleanField(_('replied'), default=False)
    is_deleted = models.BooleanField(_('deleted'), default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Contact Message')
        verbose_name_plural = _('Contact Messages')

    def __str__(self):
        return f'{self.subject} — {self.full_name}'


class SavedMatch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_matches')
    match = models.ForeignKey('matches.Match', on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'match')
        ordering = ['-created_at']
        verbose_name = _('Saved Match')
        verbose_name_plural = _('Saved Matches')

    def __str__(self):
        return f"{self.user} saved {self.match}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')

    email_match_start = models.BooleanField(_('Email when favorite team match starts'), default=True)
    email_match_result = models.BooleanField(_('Email final match scorecard summary'), default=True)
    email_breaking_news = models.BooleanField(_('Email breaking cricket news digest'), default=False)

    browser_live_score = models.BooleanField(_('Real-time browser notifications for live matches'), default=True)
    browser_wicket_alerts = models.BooleanField(_('Instant alert when a wicket falls'), default=True)
    sound_effects = models.BooleanField(_('Play audio sound on boundary (4/6) or wicket'), default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')

    def __str__(self):
        return f"Notification settings for {self.user}"


class SiteSetting(models.Model):
    """
    Global website settings customizable via the Admin Portal without code editing.
    """
    site_name = models.CharField(_('website name'), max_length=100, default='CrickScore Live')
    site_tagline = models.CharField(_('site tagline'), max_length=200, default='Fastest Live Scores & Cricket Hub')
    about_us = models.TextField(_('about us description'), blank=True, default='')
    logo = models.ImageField(_('site logo'), upload_to='branding/', blank=True, null=True)
    favicon = models.ImageField(_('site favicon'), upload_to='branding/', blank=True, null=True)
    primary_color = models.CharField(_('primary theme color'), max_length=7, default='#047857')
    secondary_color = models.CharField(_('secondary accent color'), max_length=7, default='#f59e0b')
    banner_title = models.CharField(_('homepage hero banner title'), max_length=200, default='Real-Time Cricket Scores & Match Operations')
    banner_subtitle = models.CharField(_('homepage hero banner subtitle'), max_length=300, default='Ball by ball coverage, tournaments, statistics and ICC rankings.')
    banner_image = models.ImageField(_('hero banner background image'), upload_to='branding/', blank=True, null=True)
    footer_text = models.TextField(_('footer copyright text'), default='© 2026 CrickScore Live. All rights reserved. The modern cricket scoring platform.')
    contact_email = models.EmailField(_('contact email'), default='support@crickscore.local')
    contact_phone = models.CharField(_('contact phone'), max_length=30, default='+1 (800) 555-CRIC')
    address = models.CharField(_('headquarters address'), max_length=255, default='Cricket Center Boulevard, Sports District')
    facebook_url = models.URLField(_('facebook page'), blank=True, default='https://facebook.com')
    twitter_url = models.URLField(_('twitter / X profile'), blank=True, default='https://twitter.com')
    instagram_url = models.URLField(_('instagram profile'), blank=True, default='https://instagram.com')
    youtube_url = models.URLField(_('youtube channel'), blank=True, default='https://youtube.com')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Website Setting')
        verbose_name_plural = _('Website Settings')

    def __str__(self):
        return f"{self.site_name} Configuration"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


