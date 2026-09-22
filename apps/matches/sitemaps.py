from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Match
from apps.teams.models import Team
from apps.players.models import Player
from apps.news.models import NewsArticle
from apps.series.models import Series

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return [
            'home',
            'matches:match_list',
            'rankings:rankings_list',
            'teams:team_list',
            'players:player_list',
            'series:series_list',
            'news:news_list',
            'videos:video_list',
            'photos:album_list',
            'about',
            'contact',
            'privacy_policy',
            'terms'
        ]

    def location(self, item):
        return reverse(item)


class MatchSitemap(Sitemap):
    changefreq = 'always'
    priority = 1.0

    def items(self):
        return Match.objects.all().order_by('-start_datetime')

    def lastmod(self, obj):
        return obj.updated_at


class TeamSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Team.objects.filter(is_active=True)


class PlayerSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Player.objects.filter(is_active=True)


class NewsSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return NewsArticle.objects.filter(is_published=True).order_by('-published_at')

    def lastmod(self, obj):
        return obj.updated_at


class SeriesSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Series.objects.filter(is_active=True)
