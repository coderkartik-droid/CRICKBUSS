from django.db.models import Sum

from apps.matches.models import BowlerMatchInnings, Match, PlayerMatchInnings
from apps.series.models import PointsTableEntry


def match_statistics(match):
    """Return reusable scorecard leaders and aggregate statistics for a match."""
    batting = PlayerMatchInnings.objects.filter(
        innings__match=match,
    ).select_related('player').order_by('-runs', '-balls_faced')
    bowling = BowlerMatchInnings.objects.filter(
        innings__match=match,
    ).select_related('player').order_by('-wickets', 'runs_conceded')
    return {
        'batting': batting,
        'bowling': bowling,
        'highest_score': batting.first(),
        'best_bowling': bowling.first(),
        'total_runs': batting.aggregate(total=Sum('runs'))['total'] or 0,
        'total_wickets': bowling.aggregate(total=Sum('wickets'))['total'] or 0,
    }


def rebuild_points_table(series):
    """Recalculate standings from completed local matches in a series."""
    teams = series.participating_teams.all()
    for team in teams:
        matches = Match.objects.filter(
            series=series,
        ).filter(team1=team) | Match.objects.filter(series=series, team2=team)
        completed = matches.filter(status=Match.Status.COMPLETED)
        won = completed.filter(winning_team=team).count()
        played = completed.count()
        lost = completed.filter(winning_team__isnull=False).exclude(winning_team=team).count()
        entry, _ = PointsTableEntry.objects.get_or_create(series=series, team=team)
        entry.matches_played = played
        entry.won = won
        entry.lost = lost
        entry.points = won * 2
        entry.save(update_fields=['matches_played', 'won', 'lost', 'points'])
    entries = list(series.points_table.order_by('-points', '-net_run_rate', 'team__name'))
    for position, entry in enumerate(entries, start=1):
        if entry.position != position:
            entry.position = position
            entry.save(update_fields=['position'])
    return entries
