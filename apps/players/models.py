import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class Player(models.Model):
    class Role(models.TextChoices):
        BATTER = 'batter', _('Top-order Batter')
        WICKET_KEEPER = 'wicketkeeper', _('Wicketkeeper Batter')
        ALL_ROUNDER = 'all_rounder', _('All-Rounder')
        BOWLER = 'bowler', _('Bowler')

    class BattingStyle(models.TextChoices):
        RIGHT_HAND = 'right_hand', _('Right Handed Bat')
        LEFT_HAND = 'left_hand', _('Left Handed Bat')

    class BowlingStyle(models.TextChoices):
        RIGHT_FAST = 'right_fast', _('Right-arm Fast')
        RIGHT_MEDIUM = 'right_medium', _('Right-arm Medium')
        RIGHT_OFF_SPIN = 'right_off_spin', _('Right-arm Offbreak')
        RIGHT_LEG_SPIN = 'right_leg_spin', _('Right-arm Legbreak')
        LEFT_FAST = 'left_fast', _('Left-arm Fast')
        LEFT_MEDIUM = 'left_medium', _('Left-arm Medium')
        LEFT_ORTHODOX = 'left_orthodox', _('Slow Left-arm Orthodox')
        LEFT_CHINAMAN = 'left_chinaman', _('Left-arm Unorthodox (Chinaman)')
        NONE = 'none', _('None / Non-Bowler')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('full player name'), max_length=120)
    slug = models.SlugField(_('slug URL'), max_length=140, unique=True, blank=True)
    nickname = models.CharField(_('nickname / popular name'), max_length=60, blank=True)
    image = models.ImageField(_('player portrait photo'), upload_to='players/photos/', blank=True, null=True)

    # Affiliations
    primary_team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='primary_players', verbose_name=_('national country team')
    )
    teams = models.ManyToManyField(
        'teams.Team', blank=True, related_name='players', verbose_name=_('teams & franchises')
    )

    # Personal Attributes
    role = models.CharField(_('primary playing role'), max_length=30, choices=Role.choices, default=Role.BATTER)
    batting_style = models.CharField(_('batting style'), max_length=30, choices=BattingStyle.choices, default=BattingStyle.RIGHT_HAND)
    bowling_style = models.CharField(_('bowling style'), max_length=30, choices=BowlingStyle.choices, default=BowlingStyle.NONE)
    jersey_number = models.PositiveIntegerField(_('jersey number'), null=True, blank=True)
    born_date = models.DateField(_('date of birth'), null=True, blank=True)
    birth_place = models.CharField(_('birth place'), max_length=100, blank=True)

    # Narratives
    biography = models.TextField(_('biography summary'), blank=True)
    achievements = models.TextField(_('career highlights & milestones'), blank=True)
    records = models.TextField(_('major records held'), blank=True)

    # Status
    is_featured = models.BooleanField(_('featured player'), default=False)
    is_active = models.BooleanField(_('currently active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Player')
        verbose_name_plural = _('Players')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['role']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or slugify(self.nickname) or 'player'
        # Uniquify the slug so players sharing a name never collide; only nickname is validated as unique.
        base_slug = self.slug
        counter = 2
        while self._slug_taken():
            self.slug = f'{base_slug}-{counter}'
            counter += 1
        super().save(*args, **kwargs)

    def _slug_taken(self):
        queryset = Player.objects.filter(slug=self.slug)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        return queryset.exists()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('players:player_detail', kwargs={'slug': self.slug})

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return f"https://ui-avatars.com/api/?name={self.name.replace(' ', '+')}&background=0f766e&color=ffffff&bold=true"


class CricketFormat(models.TextChoices):
    TEST = 'TEST', _('Test Cricket')
    ODI = 'ODI', _('One Day International (ODI)')
    T20I = 'T20I', _('Twenty20 International (T20I)')
    IPL = 'IPL', _('Indian Premier League (IPL)')


class BattingStat(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='batting_stats')
    format = models.CharField(max_length=10, choices=CricketFormat.choices)
    matches = models.PositiveIntegerField(default=0)
    innings = models.PositiveIntegerField(default=0)
    not_outs = models.PositiveIntegerField(default=0)
    runs = models.PositiveIntegerField(default=0)
    highest_score = models.CharField(max_length=10, default='0')
    batting_average = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    balls_faced = models.PositiveIntegerField(default=0)
    strike_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    hundreds = models.PositiveIntegerField(default=0)
    fifties = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('player', 'format')
        verbose_name = _('Batting Statistic')
        verbose_name_plural = _('Batting Statistics')

    def __str__(self):
        return f"{self.player.name} - {self.format} Batting"


class BowlingStat(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bowling_stats')
    format = models.CharField(max_length=10, choices=CricketFormat.choices)
    matches = models.PositiveIntegerField(default=0)
    innings = models.PositiveIntegerField(default=0)
    overs = models.DecimalField(max_digits=7, decimal_places=1, default=0.0)
    maidens = models.PositiveIntegerField(default=0)
    runs_conceded = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    best_bowling = models.CharField(max_length=15, default='0/0')
    bowling_average = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    economy = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    strike_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    four_wickets = models.PositiveIntegerField(default=0)
    five_wickets = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('player', 'format')
        verbose_name = _('Bowling Statistic')
        verbose_name_plural = _('Bowling Statistics')

    def __str__(self):
        return f"{self.player.name} - {self.format} Bowling"
