import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class Team(models.Model):
    class TeamType(models.TextChoices):
        INTERNATIONAL = 'international', _('International (Men)')
        INTERNATIONAL_WOMEN = 'international_women', _("International (Women)")
        IPL = 'ipl', _('IPL (Indian Premier League)')
        DOMESTIC = 'domestic', _('Domestic First-Class')
        LEAGUE = 'league', _('T20 Global Leagues (BBL/PSL/CPL/SA20)')
        UNDER19 = 'under19', _('Under-19')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('team name'), max_length=100, unique=True)
    short_name = models.CharField(_('short code'), max_length=10)
    slug = models.SlugField(_('slug URL'), max_length=120, unique=True, blank=True)
    team_type = models.CharField(_('category'), max_length=30, choices=TeamType.choices, default=TeamType.INTERNATIONAL)
    country = models.CharField(_('country / region'), max_length=100)
    logo = models.ImageField(_('team logo'), upload_to='teams/logos/', blank=True, null=True)
    primary_color = models.CharField(_('primary color hex'), max_length=7, default='#0f766e')
    secondary_color = models.CharField(_('secondary color hex'), max_length=7, default='#f59e0b')

    # Personnel
    captain_name = models.CharField(_('captain'), max_length=100, blank=True)
    coach_name = models.CharField(_('head coach'), max_length=100, blank=True)
    home_venue = models.CharField(_('home ground'), max_length=150, blank=True)
    established_year = models.PositiveIntegerField(_('established year'), null=True, blank=True)

    # Narrative content
    history = models.TextField(_('team history'), blank=True)
    records = models.TextField(_('notable records & trophies'), blank=True)

    # Statistics overview
    total_matches = models.PositiveIntegerField(_('total matches'), default=0)
    total_wins = models.PositiveIntegerField(_('matches won'), default=0)
    total_losses = models.PositiveIntegerField(_('matches lost'), default=0)
    total_ties_draws = models.PositiveIntegerField(_('ties / draws / no result'), default=0)
    trophies_count = models.PositiveIntegerField(_('trophies won'), default=0)

    # Status
    is_featured = models.BooleanField(_('featured team'), default=False)
    is_active = models.BooleanField(_('active team'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['team_type']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.short_name})"

    def get_absolute_url(self):
        return reverse('teams:team_detail', kwargs={'slug': self.slug})

    def get_logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return f"https://ui-avatars.com/api/?name={self.short_name}&background={self.primary_color.replace('#','')}&color=ffffff&bold=true"

    @property
    def win_percentage(self):
        if self.total_matches > 0:
            return round((self.total_wins / self.total_matches) * 100, 1)
        return 0.0
