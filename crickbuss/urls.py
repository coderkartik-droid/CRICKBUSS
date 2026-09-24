"""
Main URL Configuration for crickbuss project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

admin.site.site_header = "CrickScore Live Administration"
admin.site.site_title = "CrickScore Live Admin Portal"
admin.site.index_title = "Cricket Database & Live Match Operations"

from django.contrib.sitemaps.views import sitemap
from apps.matches.views import HomePageView
from apps.dashboard.views import ContactView
from apps.matches.sitemaps import (
    StaticViewSitemap, MatchSitemap, TeamSitemap,
    PlayerSitemap, NewsSitemap, SeriesSitemap
)

sitemaps = {
    'static': StaticViewSitemap,
    'matches': MatchSitemap,
    'teams': TeamSitemap,
    'players': PlayerSitemap,
    'news': NewsSitemap,
    'series': SeriesSitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Top-level Home
    path('', HomePageView.as_view(), name='home'),

    # Main Web Pages & Match Live Scores
    path('', include('apps.matches.urls')),

    # Accounts / Authentication
    path('accounts/', include('apps.accounts.urls')),

    # Teams & Players
    path('teams/', include('apps.teams.urls')),
    path('players/', include('apps.players.urls')),

    # Series & Tournaments
    path('series/', include('apps.series.urls')),

    # ICC Rankings
    path('rankings/', include('apps.rankings.urls')),

    # News & Editorial
    path('news/', include('apps.news.urls')),

    # Media: Videos & Photo Galleries
    path('videos/', include('apps.videos.urls')),
    path('photos/', include('apps.photos.urls')),

    # User Dashboard & Saved Items
    path('dashboard/', include('apps.dashboard.urls')),

    # REST APIs v1
    path('api/v1/', include('apps.api.urls')),

    # Static Pages (About, Contact, Privacy, Terms)
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('privacy-policy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    # SEO: robots.txt and sitemap.xml
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
