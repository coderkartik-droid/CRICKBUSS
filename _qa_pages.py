import os, sys, json, traceback
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
import django
django.setup()

from django.test import Client
from django.db.models import Count
from apps.accounts.models import CustomUser
from apps.matches.models import Match, Innings, PlayerMatchInnings, BallByBall
from apps.teams.models import Team
from apps.players.models import Player
from apps.series.models import Series
from apps.news.models import NewsArticle
from apps.videos.models import CricketVideo
from apps.photos.models import PhotoAlbum
from apps.rankings.models import RankingEntry

REPORT = []
LOG = open('_qa_pages.log', 'w', encoding='utf-8')
def P(m=''):
    REPORT.append(m)
    LOG.write(m + '\n')
    LOG.flush()
    print(m)

# DB summary
P('========== DATABASE SUMMARY ==========')
P(f'Users:     {CustomUser.objects.count()}')
P(f'Teams:     {Team.objects.count()}')
P(f'Players:   {Player.objects.count()}')
P(f'Series:    {Series.objects.count()}')
P(f'Matches:   {Match.objects.count()}')
P(f'Innings:   {Innings.objects.count()}')
P(f'Batting scorecards: {PlayerMatchInnings.objects.count()}')
P(f'BallByBall: {BallByBall.objects.count()}')
P(f'News:      {NewsArticle.objects.count()}')
P(f'Videos:    {CricketVideo.objects.count()}')
P(f'Albums:    {PhotoAlbum.objects.count()}')
P(f'Rankings:  {RankingEntry.objects.count()}')

match = Match.objects.first()
SLUG = match.slug
series_slug = match.series.slug if match.series else None
team1_slug = match.team1.slug
team2_slug = match.team2.slug
any_player = Player.objects.first().slug
news_slug = NewsArticle.objects.first().slug
video_slug = CricketVideo.objects.first().slug
album_slug = PhotoAlbum.objects.first().slug
P(f'\nKey slugs: match={SLUG} series={series_slug} t1={team1_slug} t2={team2_slug} player={any_player}')

# ---- PHASE A: Anonymous pages ----
P('\n========== PHASE A: Anonymous Public Pages ==========')
c = Client()

anon_pages = [
    ('Home', '/', 200),
    ('Matches list', '/matches/', 200),
    ('Match detail', f'/matches/{SLUG}/', 200),
    ('Match live JSON', f'/matches/{SLUG}/live-json/', 200),
    ('Search page', '/search/', 200),
    ('Search suggest JSON', '/search/suggest/?q=Royal', 200),
    ('Teams list', '/teams/', 200),
    ('Team detail 1', f'/teams/{team1_slug}/', 200),
    ('Team detail 2', f'/teams/{team2_slug}/', 200),
    ('Players list', '/players/', 200),
    ('Player detail', f'/players/{any_player}/', 200),
    ('Series list', '/series/', 200),
    ('Series detail', f'/series/{series_slug}/', 200),
    ('Rankings', '/rankings/', 200),
    ('News list', '/news/', 200),
    ('News detail', f'/news/{news_slug}/', 200),
    ('Videos list', '/videos/', 200),
    ('Video detail', f'/videos/{video_slug}/', 200),
    ('Photos list', '/photos/', 200),
    ('Album detail', f'/photos/{album_slug}/', 200),
    ('About', '/about/', 200),
    ('Contact', '/contact/', 200),
    ('Privacy', '/privacy-policy/', 200),
    ('Terms', '/terms/', 200),
    ('Login', '/accounts/login/', 200),
    ('Register', '/accounts/register/', 200),
    ('Sitemap', '/sitemap.xml', 200),
    ('Robots', '/robots.txt', 200),
    ('404 test (expect 404)', '/this-page-does-not-exist-xyz/', 404),
]

FAIL_ANON = []
for name, path, expected in anon_pages:
    try:
        r = c.get(path, follow=False)
        ok = r.status_code == expected
        line = f'  [{"OK" if ok else "FAIL"}] {r.status_code:3d} (expected {expected}) {name} -> {path}'
        P(line)
        if not ok:
            FAIL_ANON.append((name, path, expected, r.status_code))
            if 500 <= r.status_code < 600:
                P('     !!! TRACEBACK captured (see below via template debug)')
                try:
                    P('     ' + (r.content.decode('utf-8', errors='ignore')[:1500].replace('\n', ' ')[:1500]))
                except Exception:
                    pass
    except Exception as e:
        FAIL_ANON.append((name, path, expected, f'EXCEPTION:{e!r}'))
        P(f'  [CRASH] EXCEPTION {e!r} for {name} -> {path}')

# ---- PHASE B: Authenticated pages (admin superuser) ----
P('\n========== PHASE B: Authenticated Admin/Dashboard Pages ==========')
admin = CustomUser.objects.filter(is_superuser=True).first()
c2 = Client()
c2.force_login(admin)

auth_pages = [
    ('Profile', '/accounts/profile/', 200),
    ('Dashboard home', '/dashboard/', 200),
    ('Scorer panel (logged)', f'/matches/{SLUG}/scorer/', 200),
    ('Admin dashboard index', '/admin/', 200),
    ('Admin accounts users', '/admin/accounts/customuser/', 200),
    ('Admin teams list', '/admin/teams/team/', 200),
    ('Admin players list', '/admin/players/player/', 200),
    ('Admin matches list', '/admin/matches/match/', 200),
    ('Admin venues list', '/admin/matches/venue/', 200),
    ('Admin series list', '/admin/series/series/', 200),
    ('Admin news list', '/admin/news/newsarticle/', 200),
    ('Admin rankings list', '/admin/rankings/rankingentry/', 200),
    ('Admin videos list', '/admin/videos/cricketvideo/', 200),
    ('Admin photos list', '/admin/photos/photoalbum/', 200),
    ('Dashboard local venue', '/dashboard/local/venue/', 200),
    ('Dashboard local series', '/dashboard/local/series/', 200),
    ('Dashboard local news', '/dashboard/local/news/', 200),
    ('Dashboard local match', '/dashboard/local/match/', 200),
    ('Dashboard local ground', '/dashboard/local/ground/', 200),
    ('Dashboard managed users', '/dashboard/managed/users/', 200),
    ('Dashboard website settings', '/dashboard/website/settings/', 200),
    ('Dashboard notifications', '/dashboard/notifications/', 200),
    ('Dashboard saved items', '/dashboard/saved/', 200),
]

FAIL_AUTH = []
for name, path, expected in auth_pages:
    try:
        r = c2.get(path, follow=False)
        ok = r.status_code == expected
        line = f'  [{"OK" if ok else "FAIL"}] {r.status_code:3d} (expected {expected}) {name} -> {path}'
        P(line)
        if not ok:
            FAIL_AUTH.append((name, path, expected, r.status_code))
            if 500 <= r.status_code < 600:
                try:
                    P('     ' + (r.content.decode('utf-8', errors='ignore')[:1500].replace('\n', ' ')[:1500]))
                except Exception:
                    pass
    except Exception as e:
        FAIL_AUTH.append((name, path, expected, f'EXCEPTION:{e!r}'))
        P(f'  [CRASH] EXCEPTION {e!r} for {name} -> {path}')

# ---- PHASE C: Scorer action smoke-test via POST ----
P('\n========== PHASE C: Scorer POST Action (ball recording) ==========')
from django.middleware.csrf import get_token
c3 = Client(enforce_csrf_checks=False)
c3.force_login(admin)

# Record a 1-run legal ball, batter = RW opener, bowler = TK bowler[0]
batter = PlayerMatchInnings.objects.filter(innings__innings_number=1).order_by('batting_position').first().player
bowler = Player.objects.filter(primary_team=match.team2, role__in=['bowler', 'all_rounder']).first()

payload = {
    'action': 'record_ball',
    'runs_off_bat': '1',
    'extra_type': 'none',
    'is_wicket': False,
    'commentary': 'QA smoke: pushed to midwicket for a single.',
    'batter_id': str(batter.id),
    'bowler_id': str(bowler.id),
}

try:
    r = c3.post(f'/matches/{SLUG}/scorer/action/', payload, content_type='application/x-www-form-urlencoded')
    P(f'  Scorer action status: {r.status_code}')
    if r.status_code == 200:
        data = json.loads(r.content)
        P(f'  JSON success={data.get("success")} msg={data.get("message","")}')
        P(f'  State snapshot: runs={data.get("runs")} wkts={data.get("wickets")} overs={data.get("overs")} crr={data.get("crr")}')
    else:
        FAIL_AUTH.append(('Scorer action', f'/matches/{SLUG}/scorer/action/', 200, r.status_code))
        P('  Response snippet: ' + r.content.decode('utf-8', errors='ignore')[:1000])
except Exception as e:
    P(f'  EXCEPTION: {e!r}')
    traceback.print_exc(file=LOG)
    FAIL_AUTH.append(('Scorer action', f'/matches/{SLUG}/scorer/action/', 200, f'EXCEPTION:{e!r}'))

# Final tally
P('\n========== SUMMARY ==========')
P(f'Anonymous pages tested: {len(anon_pages)}. Failures: {len(FAIL_ANON)}')
for f in FAIL_ANON:
    P('  ANON FAIL: ' + repr(f))
P(f'Auth pages tested: {len(auth_pages)}. Failures: {len(FAIL_AUTH)}')
for f in FAIL_AUTH:
    P('  AUTH FAIL: ' + repr(f))
P(f'Total failures: {len(FAIL_ANON) + len(FAIL_AUTH)}')

json.dump({
    'slug': SLUG, 'series_slug': series_slug,
    'team1_slug': team1_slug, 'team2_slug': team2_slug,
    'player_slug': any_player, 'news_slug': news_slug,
    'video_slug': video_slug, 'album_slug': album_slug,
    'anon_failures': FAIL_ANON, 'auth_failures': FAIL_AUTH,
}, open('_qa_pages.json', 'w', encoding='utf-8'), indent=2, default=str)

LOG.close()
