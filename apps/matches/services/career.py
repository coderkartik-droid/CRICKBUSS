from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.matches.models import Match, PlayerMatchInnings, BowlerMatchInnings
from apps.players.models import BattingStat, BowlingStat, CricketFormat, Player


def _format_for_match(match):
    return {
        Match.MatchType.TEST: CricketFormat.TEST,
        Match.MatchType.ODI: CricketFormat.ODI,
        Match.MatchType.T20: CricketFormat.T20I,
        Match.MatchType.T10: CricketFormat.T20I,
    }.get(match.match_type, CricketFormat.T20I)


def _ratio(numerator, denominator):
    if not denominator:
        return Decimal('0.00')
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


@transaction.atomic
def process_completed_match(match_id):
    match = Match.objects.select_for_update().get(pk=match_id)
    if match.status != Match.Status.COMPLETED or match.stats_processed:
        return False

    fmt = _format_for_match(match)
    innings = list(match.innings.filter(is_completed=True).prefetch_related('batters', 'bowlers'))
    team1_ids = set(match.team1_playing_xi.values_list('id', flat=True))
    team2_ids = set(match.team2_playing_xi.values_list('id', flat=True))
    player_ids = team1_ids | team2_ids

    for player_id in player_ids:
        player = Player.objects.select_for_update().get(pk=player_id)
        won = bool(match.winning_team_id and (
            (player_id in team1_ids and match.winning_team_id == match.team1_id)
            or (player_id in team2_ids and match.winning_team_id == match.team2_id)
        ))
        player_matches = 1
        player.matches_won += int(won)
        player.matches_lost += int(bool(match.winning_team_id) and not won)

        if player_id in (match.team1_captain_id, match.team2_captain_id):
            captain_won = bool(match.winning_team_id and (
                (player_id == match.team1_captain_id and match.winning_team_id == match.team1_id)
                or (player_id == match.team2_captain_id and match.winning_team_id == match.team2_id)
            ))
            player.wins_as_captain += int(captain_won)
            player.losses_as_captain += int(bool(match.winning_team_id) and not captain_won)

        batting_rows = [
            row for inn in innings for row in inn.batters.all() if row.player_id == player_id
        ]
        bowling_rows = [
            row for inn in innings for row in inn.bowlers.all() if row.player_id == player_id
        ]
        player.run_outs += sum(
            row.dismissal == PlayerMatchInnings.DismissalType.RUN_OUT
            for row in batting_rows
        )
        player.save(update_fields=[
            'matches_won', 'matches_lost', 'run_outs',
            'wins_as_captain', 'losses_as_captain',
        ])
        stat, _ = BattingStat.objects.select_for_update().get_or_create(
            player_id=player_id, format=fmt
        )
        stat.matches += player_matches
        if batting_rows:
            stat.innings += len(batting_rows)
            stat.not_outs += sum(row.dismissal == PlayerMatchInnings.DismissalType.NOT_OUT for row in batting_rows)
            stat.runs += sum(row.runs for row in batting_rows)
            stat.balls_faced += sum(row.balls_faced for row in batting_rows)
            stat.fours += sum(row.fours for row in batting_rows)
            stat.sixes += sum(row.sixes for row in batting_rows)
            scores = [row.runs for row in batting_rows]
            stat.highest_score = str(max(int(stat.highest_score or 0), max(scores, default=0)))
            stat.fifties += sum(50 <= row.runs < 100 for row in batting_rows)
            stat.hundreds += sum(row.runs >= 100 for row in batting_rows)
            stat.batting_average = _ratio(stat.runs, stat.innings - stat.not_outs)
            stat.strike_rate = _ratio(stat.runs * 100, stat.balls_faced)
        stat.save()

        stat, _ = BowlingStat.objects.select_for_update().get_or_create(
            player_id=player_id, format=fmt
        )
        stat.matches += player_matches
        if bowling_rows:
            stat.innings += len(bowling_rows)
            legal_balls = sum(row.overs * 6 + row.balls for row in bowling_rows)
            stat.overs = Decimal(str(stat.overs or 0)) + (
                Decimal(legal_balls) / Decimal(6)
            )
            stat.maidens += sum(row.maidens for row in bowling_rows)
            stat.runs_conceded += sum(row.runs_conceded for row in bowling_rows)
            stat.wickets += sum(row.wickets for row in bowling_rows)
            stat.four_wickets += sum(row.wickets >= 4 for row in bowling_rows)
            stat.five_wickets += sum(row.wickets >= 5 for row in bowling_rows)
            best = max(bowling_rows, key=lambda row: (row.wickets, -row.runs_conceded))
            best_value = (best.wickets, best.runs_conceded)
            old_wickets, _, old_runs = (stat.best_bowling or '0/0').partition('/')
            if best_value[0] > int(old_wickets or 0) or (
                best_value[0] == int(old_wickets or 0) and best_value[1] < int(old_runs or 0)
            ):
                stat.best_bowling = f'{best.wickets}/{best.runs_conceded}'
            stat.economy = _ratio(stat.runs_conceded * 6, legal_balls)
            stat.bowling_average = _ratio(stat.runs_conceded, stat.wickets)
            stat.strike_rate = _ratio(legal_balls, stat.wickets)
        stat.save()

    match.stats_processed = True
    match.save(update_fields=['stats_processed', 'updated_at'])
    return True
