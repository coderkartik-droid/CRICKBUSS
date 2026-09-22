import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('stadium name'), max_length=150)
    address = models.CharField(_('address'), max_length=250, blank=True)
    city = models.CharField(_('city'), max_length=80)
    state = models.CharField(_('state'), max_length=80, blank=True)
    country = models.CharField(_('country'), max_length=80)
    description = models.TextField(_('description'), blank=True)
    capacity = models.PositiveIntegerField(_('seating capacity'), default=30000)
    pitch_type = models.CharField(_('pitch characteristic'), max_length=100, default='Batting friendly with early bounce')
    avg_first_innings_score = models.PositiveIntegerField(_('average 1st innings score (T20/ODI)'), default=175)
    image = models.ImageField(upload_to='venues/', blank=True, null=True)

    class Meta:
        verbose_name = _('Cricket Stadium / Venue')
        verbose_name_plural = _('Venues & Stadiums')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.city}"

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800&q=80'


class Ground(models.Model):
    name = models.CharField(max_length=150)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='grounds')
    surface = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} - {self.venue.name}'


class Tournament(models.Model):
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overs_per_innings = models.PositiveSmallIntegerField(default=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date', 'name']

    def __str__(self):
        return self.name


class Official(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=80)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.role})'


class Sponsor(models.Model):
    name = models.CharField(max_length=150, unique=True)
    logo = models.ImageField(upload_to='sponsors/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', _('Scheduled / Upcoming')
        LIVE = 'live', _('LIVE in Progress')
        INNINGS_BREAK = 'break', _('Innings Break')
        COMPLETED = 'completed', _('Match Completed')
        DELAYED = 'delayed', _('Delayed (Rain/Weather)')
        ABANDONED = 'abandoned', _('Abandoned / No Result')

    class MatchType(models.TextChoices):
        TEST = 'TEST', _('Test Match (5 Days)')
        ODI = 'ODI', _('ODI (50 Overs)')
        T20 = 'T20', _('T20 (20 Overs)')
        T10 = 'T10', _('T10 (10 Overs)')

    class TossDecision(models.TextChoices):
        BAT = 'bat', _('Elected to Bat First')
        BOWL = 'bowl', _('Elected to Bowl First')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('match title'), max_length=200, help_text='e.g. India vs Australia - 2nd ODI')
    slug = models.SlugField(_('slug URL'), max_length=220, unique=True, blank=True)
    match_number = models.CharField(_('match stage'), max_length=50, default='1st Match')
    match_type = models.CharField(max_length=15, choices=MatchType.choices, default=MatchType.T20)
    series = models.ForeignKey('series.Series', on_delete=models.CASCADE, related_name='matches', null=True, blank=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, related_name='matches', null=True, blank=True)

    team1 = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='home_matches')
    team2 = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='away_matches')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='hosted_matches')
    ground = models.ForeignKey(Ground, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    overs_limit = models.PositiveSmallIntegerField(default=20)
    ball_type = models.CharField(max_length=50, default='Leather')
    pitch_type = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING, db_index=True)
    current_innings_number = models.PositiveIntegerField(default=1)

    # Toss
    toss_winner = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='toss_won_matches')
    toss_decision = models.CharField(max_length=10, choices=TossDecision.choices, blank=True)

    # Officials
    umpire_one = models.CharField(max_length=80, blank=True, default='Richard Kettleborough')
    umpire_two = models.CharField(max_length=80, blank=True, default='Kumar Dharmasena')
    tv_umpire = models.CharField(max_length=80, blank=True, default='Nitin Menon')
    match_referee = models.CharField(max_length=80, blank=True, default='Javagal Srinath')
    scorer = models.CharField(max_length=80, blank=True)
    assigned_scorers = models.ManyToManyField(
        'accounts.CustomUser', blank=True, related_name='assigned_matches',
        limit_choices_to={'role': 'scorer'},
    )
    officials = models.ManyToManyField(Official, blank=True, related_name='matches')
    sponsors = models.ManyToManyField(Sponsor, blank=True, related_name='matches')

    # Conditions
    pitch_report = models.TextField(blank=True, default='Hard deck with consistent bounce. Expected to assist stroke-play initially, with spin coming into play under lights.')
    weather_report = models.CharField(max_length=120, blank=True, default='Clear Skies, 28°C, Humidity 45%, Precipitation 0%')

    # Result & Awards
    winning_team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='victories')
    result_text = models.CharField(_('result summary'), max_length=200, blank=True)
    man_of_match = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='potm_awards')

    # Schedule
    start_datetime = models.DateTimeField(_('start date & time'))
    end_datetime = models.DateTimeField(_('scheduled end time'), null=True, blank=True)

    # Lineups (Playing XI)
    team1_playing_xi = models.ManyToManyField('players.Player', blank=True, related_name='team1_matches')
    team2_playing_xi = models.ManyToManyField('players.Player', blank=True, related_name='team2_matches')
    team1_captain = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='captained_team1_matches')
    team1_vice_captain = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='vice_captained_team1_matches')
    team2_captain = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='captained_team2_matches')
    team2_vice_captain = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='vice_captained_team2_matches')

    is_featured = models.BooleanField(_('featured match on hero section'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Match')
        verbose_name_plural = _('Matches')
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['status', '-start_datetime']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.team1.short_name}-vs-{self.team2.short_name}-{self.match_number}"
            self.slug = slugify(base)[:200]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.status.upper()})"

    def get_absolute_url(self):
        return reverse('matches:match_detail', kwargs={'slug': self.slug})

    @property
    def current_innings(self):
        return self.innings.filter(innings_number=self.current_innings_number).first()

    @property
    def latest_innings(self):
        return self.innings.order_by('-innings_number').first()


class Innings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='innings')
    batting_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='batting_innings')
    bowling_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='bowling_innings')

    innings_number = models.PositiveSmallIntegerField(default=1)
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveSmallIntegerField(default=0)
    overs = models.PositiveIntegerField(default=0)
    balls = models.PositiveSmallIntegerField(default=0)  # 0 to 5 for remaining legal balls in over

    # Extras
    wides = models.PositiveSmallIntegerField(default=0)
    no_balls = models.PositiveSmallIntegerField(default=0)
    byes = models.PositiveSmallIntegerField(default=0)
    leg_byes = models.PositiveSmallIntegerField(default=0)

    is_declared = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    target_runs = models.PositiveIntegerField(null=True, blank=True)
    free_hit = models.BooleanField(default=False)
    powerplay_overs = models.PositiveSmallIntegerField(default=6)
    break_reason = models.CharField(max_length=80, blank=True)

    class Meta:
        unique_together = ('match', 'innings_number')
        ordering = ['innings_number']
        verbose_name = _('Match Innings')
        verbose_name_plural = _('Match Innings')

    def __str__(self):
        return f"{self.batting_team.short_name} {self.runs}/{self.wickets} ({self.overs_formatted}) - Innings {self.innings_number}"

    @property
    def total_extras(self):
        return self.wides + self.no_balls + self.byes + self.leg_byes

    @property
    def overs_formatted(self):
        return f"{self.overs}.{self.balls}"

    @property
    def current_run_rate(self):
        total_legal_balls = (self.overs * 6) + self.balls
        if total_legal_balls > 0:
            return round((self.runs / total_legal_balls) * 6, 2)
        return 0.00


class PlayerMatchInnings(models.Model):
    class DismissalType(models.TextChoices):
        NOT_OUT = 'not_out', _('Not Out')
        BOWLED = 'bowled', _('b')
        CAUGHT = 'caught', _('c')
        LBW = 'lbw', _('lbw b')
        RUN_OUT = 'run_out', _('run out')
        STUMPED = 'stumped', _('st')
        HIT_WICKET = 'hit_wicket', _('hit wicket')
        RETIRED_HURT = 'retired_hurt', _('retired hurt')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='batters')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='match_batting_records')
    batting_position = models.PositiveSmallIntegerField(default=1)

    dismissal = models.CharField(max_length=20, choices=DismissalType.choices, default=DismissalType.NOT_OUT)
    dismissal_bowler = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='dismissals_bowled')
    dismissal_fielder = models.ForeignKey('players.Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='dismissals_fielded')
    dismissal_text = models.CharField(max_length=150, blank=True, default='not out')

    runs = models.PositiveIntegerField(default=0)
    balls_faced = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    dots = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('innings', 'player')
        ordering = ['batting_position']

    def __str__(self):
        return f"{self.player.name} {self.runs} ({self.balls_faced})"

    @property
    def strike_rate(self):
        if self.balls_faced > 0:
            return round((self.runs / self.balls_faced) * 100, 2)
        return 0.00


class BowlerMatchInnings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='bowlers')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='match_bowling_records')

    overs = models.PositiveIntegerField(default=0)
    balls = models.PositiveSmallIntegerField(default=0)
    maidens = models.PositiveIntegerField(default=0)
    runs_conceded = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    wides = models.PositiveIntegerField(default=0)
    no_balls = models.PositiveIntegerField(default=0)
    dots = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('innings', 'player')
        ordering = ['-wickets', 'runs_conceded']

    def __str__(self):
        return f"{self.player.name} {self.wickets}/{self.runs_conceded} ({self.overs}.{self.balls})"

    @property
    def economy_rate(self):
        legal_balls = (self.overs * 6) + self.balls
        if legal_balls > 0:
            return round((self.runs_conceded / legal_balls) * 6, 2)
        return 0.00


class BallByBall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='ball_deliveries')
    over_number = models.PositiveIntegerField()  # 1 to 20 or 50
    ball_number = models.PositiveSmallIntegerField()  # 1 to 6 (or extras)

    batter = models.ForeignKey('players.Player', on_delete=models.SET_NULL, related_name='balls_faced', null=True, blank=True)
    bowler = models.ForeignKey('players.Player', on_delete=models.SET_NULL, related_name='balls_bowled', null=True, blank=True)
    non_striker = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='balls_non_striker', null=True, blank=True)

    runs_off_bat = models.PositiveSmallIntegerField(default=0)
    is_four = models.BooleanField(default=False)
    is_six = models.BooleanField(default=False)
    is_wicket = models.BooleanField(default=False)
    wicket_description = models.CharField(max_length=150, blank=True)

    is_wide = models.BooleanField(default=False)
    is_no_ball = models.BooleanField(default=False)
    is_bye = models.BooleanField(default=False)
    is_leg_bye = models.BooleanField(default=False)
    extra_runs = models.PositiveSmallIntegerField(default=0)
    extra_type = models.CharField(max_length=20, blank=True)
    is_free_hit = models.BooleanField(default=False)
    review_taken = models.BooleanField(default=False)

    commentary = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-over_number', '-ball_number', '-timestamp']

    def __str__(self):
        return f"{self.over_number}.{self.ball_number}: {self.commentary[:50]}"


class Partnership(models.Model):
    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='partnerships')
    wicket_number = models.PositiveSmallIntegerField()
    batter1 = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='partnerships_as_first')
    batter2 = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='partnerships_as_second')
    runs = models.PositiveIntegerField(default=0)
    balls = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['wicket_number']

    def __str__(self):
        return f"{self.wicket_number}th wicket: {self.batter1.name} & {self.batter2.name} - {self.runs} runs ({self.balls}b)"


class FallOfWicket(models.Model):
    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='fall_of_wickets')
    wicket_number = models.PositiveSmallIntegerField()
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='dismissed_in_fow')
    score = models.PositiveIntegerField()
    overs = models.CharField(max_length=10)

    class Meta:
        ordering = ['wicket_number']

    def __str__(self):
        return f"{self.wicket_number}-{self.score} ({self.player.name}, {self.overs} ov)"
