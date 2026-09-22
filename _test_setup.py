import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
django.setup()

from datetime import timedelta
from django.utils import timezone
from apps.matches.models import Match, Innings
from apps.teams.models import Team
from apps.players.models import Player
from apps.matches.services.scoring import record_delivery

result = []
result.append(f"Matches: {Match.objects.count()}")
result.append(f"Teams: {Team.objects.count()}")
result.append(f"Players: {Player.objects.count()}")
for m in Match.objects.all()[:5]:
    inns = ', '.join([f"Inn{i.innings_number}:{i.batting_team.short_name}" for i in m.innings.all()])
    result.append(f"  {m.title} | slug={m.slug} | status={m.status} | {m.team1.short_name} vs {m.team2.short_name} | [{inns}]")

# Create a test match if none exists
if Match.objects.count() == 0 or not Match.objects.filter(status='live').exists():
    t1 = Team.objects.first()
    t2 = Team.objects.exclude(pk=t1.pk).first() if t1 else None
    result.append(f"Teams for match: {t1} vs {t2}")
    if t1 and t2:
        p1s = list(t1.players.filter(is_active=True)[:11])
        p2s = list(t2.players.filter(is_active=True)[:11])
        result.append(f"Team {t1.short_name} players: {len(p1s)} | Team {t2.short_name} players: {len(p2s)}")
        start = timezone.now()
        match = Match.objects.create(
            title=f"TEST {t1.short_name} vs {t2.short_name} - Bug Fix Test",
            match_type='T20',
            team1=t1, team2=t2,
            status=Match.Status.LIVE,
            current_innings_number=1,
            toss_winner=t1, toss_decision='bat',
            start_datetime=start,
            end_datetime=start + timedelta(hours=3),
            overs_limit=20,
        )
        match.team1_playing_xi.set(p1s)
        match.team2_playing_xi.set(p2s)
        inn = Innings.objects.create(
            match=match, innings_number=1,
            batting_team=t1, bowling_team=t2,
        )
        result.append(f"CREATED test match: {match.slug} | innings: {inn.id}")
else:
    live = Match.objects.filter(status='live').first()
    result.append(f"Using LIVE match: {live.slug if live else 'NONE'}")

with open('test_setup_log.txt', 'w') as f:
    f.write('\n'.join(result))
print('\n'.join(result))