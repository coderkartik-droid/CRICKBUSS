from django.core.management.base import BaseCommand
from django.db import transaction

from apps.dashboard.models import SavedMatch
from apps.matches.models import (
    BallByBall,
    BowlerMatchInnings,
    FallOfWicket,
    Ground,
    Innings,
    Match,
    Official,
    Partnership,
    PlayerMatchInnings,
    Sponsor,
    Tournament,
    Venue,
)
from apps.news.models import NewsArticle, NewsCategory
from apps.photos.models import PhotoAlbum, PhotoItem
from apps.players.models import BattingStat, BowlingStat, Player
from apps.rankings.models import RankingEntry
from apps.series.models import PointsTableEntry, Series
from apps.teams.models import Team
from apps.videos.models import CricketVideo, VideoCategory


class Command(BaseCommand):
    help = (
        'Delete cricket/demo content while preserving users, authentication data, '
        'and system settings.'
    )

    def handle(self, *args, **options):
        answer = input(
            'Are you sure you want to delete all demo data? (yes/no) '
        ).strip().lower()
        if answer != 'yes':
            self.stdout.write(self.style.WARNING('Demo data cleanup cancelled.'))
            return

        with transaction.atomic():
            deleted = {}

            def clear(label, queryset):
                deleted[label] = queryset.count()
                queryset.delete()

            # Remove dependent score/stat records explicitly so this remains
            # predictable even if a relation's on_delete policy changes later.
            clear('ball-by-ball deliveries', BallByBall.objects.all())
            clear('fall-of-wicket records', FallOfWicket.objects.all())
            clear('partnerships', Partnership.objects.all())
            clear('bowling innings records', BowlerMatchInnings.objects.all())
            clear('batting innings records', PlayerMatchInnings.objects.all())
            clear('innings', Innings.objects.all())
            clear('saved match entries', SavedMatch.objects.all())
            clear('matches', Match.objects.all())

            clear('points-table entries', PointsTableEntry.objects.all())
            clear('rankings', RankingEntry.objects.all())
            clear('series', Series.objects.all())
            clear('players batting stats', BattingStat.objects.all())
            clear('players bowling stats', BowlingStat.objects.all())
            clear('players', Player.objects.all())
            clear('teams', Team.objects.all())

            clear('photo items', PhotoItem.objects.all())
            clear('photo albums', PhotoAlbum.objects.all())
            clear('video categories', VideoCategory.objects.all())
            clear('videos', CricketVideo.objects.all())
            clear('news articles', NewsArticle.objects.all())
            clear('news categories', NewsCategory.objects.all())

            clear('grounds', Ground.objects.all())
            clear('venues', Venue.objects.all())
            clear('officials', Official.objects.all())
            clear('sponsors', Sponsor.objects.all())
            clear('tournaments', Tournament.objects.all())

        total = sum(deleted.values())
        self.stdout.write(
            self.style.SUCCESS(
                f'Demo data cleanup complete. Deleted {total} cricket/content records.'
            )
        )
        for label, count in deleted.items():
            if count:
                self.stdout.write(f'  {label}: {count}')
