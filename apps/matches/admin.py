from django.contrib import admin
from .models import (
    Venue, Ground, Tournament, Official, Sponsor, Match, Innings,
    PlayerMatchInnings, BowlerMatchInnings, BallByBall, Partnership, FallOfWicket
)


@admin.register(Ground)
class GroundAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue', 'surface', 'capacity', 'is_active')
    list_filter = ('is_active', 'venue')
    search_fields = ('name', 'venue__name')


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'overs_per_innings', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Official)
class OfficialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'email', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'email')


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

class InningsInline(admin.TabularInline):
    model = Innings
    extra = 1

class PlayerMatchInningsInline(admin.TabularInline):
    model = PlayerMatchInnings
    extra = 2

class BowlerMatchInningsInline(admin.TabularInline):
    model = BowlerMatchInnings
    extra = 2

class FallOfWicketInline(admin.TabularInline):
    model = FallOfWicket
    extra = 2

class PartnershipInline(admin.TabularInline):
    model = Partnership
    extra = 2

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'capacity', 'pitch_type', 'avg_first_innings_score')
    search_fields = ('name', 'city', 'country')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('title', 'tournament', 'series', 'match_type', 'status', 'start_datetime', 'venue', 'is_featured')
    list_filter = ('status', 'match_type', 'series', 'tournament', 'is_featured')
    search_fields = ('title', 'team1__name', 'team2__name', 'venue__name')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('team1_playing_xi', 'team2_playing_xi', 'officials', 'sponsors')
    inlines = [InningsInline]
    list_editable = ('status', 'is_featured')

@admin.register(Innings)
class InningsAdmin(admin.ModelAdmin):
    list_display = ('match', 'innings_number', 'batting_team', 'runs', 'wickets', 'overs', 'balls', 'is_completed')
    list_filter = ('innings_number', 'is_completed')
    inlines = [PlayerMatchInningsInline, BowlerMatchInningsInline, FallOfWicketInline, PartnershipInline]

@admin.register(BallByBall)
class BallByBallAdmin(admin.ModelAdmin):
    list_display = ('innings', 'over_number', 'ball_number', 'batter', 'bowler', 'runs_off_bat', 'extra_runs', 'is_wicket')
    list_filter = ('is_wicket', 'is_four', 'is_six')
    search_fields = ('commentary', 'batter__name', 'bowler__name')
