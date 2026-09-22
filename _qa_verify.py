import os, sys, json, traceback
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
import django
django.setup()

from django.test import Client
from apps.accounts.models import CustomUser
from apps.matches.models import Match, Innings, BallByBall, PlayerMatchInnings
from apps.players.models import Player
from apps.teams.models import Team

LOG = open('_qa_pages2.log', 'w', encoding='utf-8')
def P(m=''):
    LOG.write(str(m)+'\n')
    LOG.flush()
    print(m)

match = Match.objects.first()
SLUG = match.slug
admin = CustomUser.objects.filter(is_superuser=True).first()

P('=== Scorer action fixes verification ===')

# Test 1: record_ball
c = Client(enforce_csrf_checks=False)
c.force_login(admin)
pmi_inn1 = PlayerMatchInnings.objects.filter(innings__innings_number=1, innings__match=match).order_by('batting_position')
batter = pmi_inn1.first().player
bowler = Player.objects.filter(primary_team=match.team2, role__in=['bowler', 'all_rounder']).first()

pre_runs = Innings.objects.get(match=match, innings_number=1).runs
pre_balls = Innings.objects.get(match=match, innings_number=1).balls

resp = c.post(f'/matches/{SLUG}/scorer/action/', {
    'action': 'record_ball',
    'runs_off_bat': '1',
    'extra_type': 'none',
    'is_wicket': 'false',
    'commentary': 'QA ball 1: single to midwicket.',
    'batter_id': str(batter.id),
    'bowler_id': str(bowler.id),
})
P(f'record_ball (1 run) -> status {resp.status_code}')
P(resp.content.decode()[:500])

mid_runs = Innings.objects.get(match=match, innings_number=1).runs
mid_balls = Innings.objects.get(match=match, innings_number=1).balls
P(f'  state after: runs {pre_runs}->{mid_runs}, balls {pre_balls}->{mid_balls}')
P(f'  BallByBall count: {BallByBall.objects.filter(innings__match=match).count()}')

# Test 2: undo
resp = c.post(f'/matches/{SLUG}/scorer/action/', {'action': 'undo_last_ball'})
P(f'undo_last_ball -> status {resp.status_code}')
P(resp.content.decode()[:500])

post_runs = Innings.objects.get(match=match, innings_number=1).runs
post_balls = Innings.objects.get(match=match, innings_number=1).balls
P(f'  state after undo: runs {mid_runs}->{post_runs}, balls {mid_balls}->{post_balls}')
P(f'  BallByBall count: {BallByBall.objects.filter(innings__match=match).count()}')

# Test 3: update_toss
new_winner = match.team2 if match.toss_winner == match.team1 else match.team1
resp = c.post(f'/matches/{SLUG}/scorer/action/', {
    'action': 'update_toss',
    'toss_winner_id': str(new_winner.id),
    'toss_decision': 'bowl',
})
P(f'update_toss -> status {resp.status_code}')
P(resp.content.decode()[:500])
match.refresh_from_db()
P(f'  toss_winner: {match.toss_winner}, decision: {match.toss_decision}')

# Test 4: set_result
captain = match.team1_captain
resp = c.post(f'/matches/{SLUG}/scorer/action/', {
    'action': 'set_result',
    'result_text': 'Royal Warriors won by 7 wickets',
    'winning_team_id': str(match.team1.id),
    'man_of_match_id': str(captain.id),
})
P(f'set_result -> status {resp.status_code}')
P(resp.content.decode()[:500])
match.refresh_from_db()
P(f'  match.status = {match.status}')
P(f'  result_text = {match.result_text}')
P(f'  winning_team = {match.winning_team}')
P(f'  man_of_match = {match.man_of_match}')

# Revert match back to LIVE for subsequent browser tests
match.status = Match.Status.LIVE
match.save()

# Dashboard pages (correct hyphenated URLs)
P('\n=== Corrected dashboard URLs ===')
for (name, url) in [
    ('Managed users', '/dashboard/managed-users/'),
    ('Website settings', '/dashboard/website-settings/'),
    ('Local management venue (403 expected)','/dashboard/local/venue/'),
]:
    r = c.get(url, follow=False)
    P(f'  {r.status_code:3d} {name}: {url}')
    if r.status_code >= 500:
        P('     ' + r.content.decode('utf-8', errors='ignore')[:500].replace('\n',' '))

# Re-run the pages test that was fixed
P('\n=== Key pages second pass ===')
checks = [
    ('Home','/'), ('Scorer', f'/matches/{SLUG}/scorer/'),
    ('Match detail', f'/matches/{SLUG}/'), ('Live JSON', f'/matches/{SLUG}/live-json/'),
    ('Admin teams', '/admin/teams/team/'),
]
for name, pth in checks:
    r = c.get(pth, follow=False)
    P(f'  {r.status_code:3d} {name}: {pth}')

LOG.close()
