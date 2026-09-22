import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class Series(models.Model):
    class Category(models.TextChoices):
        INTERNATIONAL = 'international', _('International Bilateral / Tour')
        ICC_TOURNAMENT = 'icc_tournament', _('ICC Global Tournament')
        IPL = 'ipl', _('IPL (Indian Premier League)')
        PSL = 'psl', _('PSL (Pakistan Super League)')
        BBL = 'bbl', _('BBL (Big Bash League)')
        BPL = 'bpl', _('BPL (Bangladesh Premier League)')
        CPL = 'cpl', _('CPL (Caribbean Premier League)')
        SA20 = 'sa20', _('SA20 League')
        ILT20 = 'ilt20', _('ILT20 League')
        HUNDRED = 'hundred', _('The Hundred')
        WOMEN = 'women', _("Women's Cricket Tournament")
        UNDER19 = 'under19', _('Under-19 Cricket')
        DOMESTIC = 'domestic', _('Domestic Championship')

    class Format(models.TextChoices):
        TEST = 'TEST', _('Test')
        ODI = 'ODI', _('ODI')
        T20 = 'T20', _('T20')
        MIXED = 'MIXED', _('Multi-Format Tour')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('series / tournament title'), max_length=150, unique=True)
    short_name = models.CharField(_('short title'), max_length=50)
    slug = models.SlugField(_('slug URL'), max_length=160, unique=True, blank=True)
    category = models.CharField(_('competition category'), max_length=30, choices=Category.choices, default=Category.INTERNATIONAL)
    cricket_format = models.CharField(_('format'), max_length=15, choices=Format.choices, default=Format.T20)
    host_country = models.CharField(_('host nation / region'), max_length=100)
    start_date = models.DateField(_('tournament start date'))
    end_date = models.DateField(_('tournament end date'))
    total_matches = models.PositiveIntegerField(_('total scheduled matches'), default=0)
    banner_image = models.ImageField(_('series hero banner'), upload_to='series/banners/', blank=True, null=True)

    participating_teams = models.ManyToManyField(
        'teams.Team', blank=True, related_name='tournaments', verbose_name=_('participating teams')
    )

    is_featured = models.BooleanField(_('featured series'), default=False)
    is_active = models.BooleanField(_('ongoing or upcoming'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Series / Tournament')
        verbose_name_plural = _('Series & Tournaments')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active', 'is_featured']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('series:series_detail', kwargs={'slug': self.slug})


class PointsTableEntry(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='points_table')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='standings')
    matches_played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    tied_no_result = models.PositiveIntegerField(default=0)
    net_run_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0.000)
    points = models.PositiveIntegerField(default=0)
    recent_form = models.CharField(max_length=20, default='-', help_text='e.g. W,W,L,W,L')
    position = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('series', 'team')
        ordering = ['position', '-points', '-net_run_rate']
        verbose_name = _('Points Table Entry')
        verbose_name_plural = _('Points Table Standings')

    def __str__(self):
        return f"{self.position}. {self.team.name} ({self.points} pts) - {self.series.short_name}"
