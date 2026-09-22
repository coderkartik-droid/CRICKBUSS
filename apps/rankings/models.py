import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class RankingEntry(models.Model):
    class Gender(models.TextChoices):
        MEN = 'men', _("Men's Cricket")
        WOMEN = 'women', _("Women's Cricket")

    class Format(models.TextChoices):
        TEST = 'TEST', _('Test')
        ODI = 'ODI', _('ODI')
        T20I = 'T20I', _('T20I')

    class Category(models.TextChoices):
        TEAMS = 'teams', _('Team Rankings')
        BATTERS = 'batters', _('Batters')
        BOWLERS = 'bowlers', _('Bowlers')
        ALL_ROUNDERS = 'all_rounders', _('All-Rounders')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MEN)
    cricket_format = models.CharField(max_length=10, choices=Format.choices, default=Format.TEST)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.BATTERS)

    rank = models.PositiveIntegerField(_('rank position'))
    previous_rank = models.PositiveIntegerField(_('previous rank position'), null=True, blank=True)

    # Either a player or a team can be associated
    player = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='rankings')
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='rankings')

    # Fallback/Direct fields
    name = models.CharField(_('display name'), max_length=120)
    country = models.CharField(_('country / nation'), max_length=100)
    rating = models.PositiveIntegerField(_('rating score'), default=0)
    points = models.PositiveIntegerField(_('total points'), default=0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('ICC Ranking Entry')
        verbose_name_plural = _('ICC Rankings')
        ordering = ['gender', 'cricket_format', 'category', 'rank']
        indexes = [
            models.Index(fields=['gender', 'cricket_format', 'category']),
            models.Index(fields=['rank']),
        ]

    def __str__(self):
        return f"#{self.rank} {self.name} ({self.country}) - {self.gender.title()} {self.cricket_format} {self.category.title()}"

    @property
    def trend(self):
        """Returns 'up', 'down', or 'same' compared to previous rank."""
        if self.previous_rank is None or self.previous_rank == self.rank:
            return 'same'
        elif self.rank < self.previous_rank:
            return 'up'
        else:
            return 'down'
