from django.db import transaction
from django.utils import timezone

from apps.players.models import Player
from apps.matches.models import BallByBall, BowlerMatchInnings, Innings, Match, PlayerMatchInnings


EXTRA_TYPES = {'wide', 'no_ball', 'bye', 'leg_bye'}


def _next_delivery_number(innings, legal):
    last = innings.ball_deliveries.order_by('-over_number', '-ball_number', '-timestamp').first()
    if not last:
        return 1, 1
    over = last.over_number
    ball = last.ball_number
    if legal:
        ball += 1
        if ball > 6:
            over += 1
            ball = 1
    return over, ball


@transaction.atomic
def record_delivery(match_id, *, batter_id=None, bowler_id=None, runs_off_bat=0,
                    extra_runs=0, extra_type='', is_wicket=False,
                    commentary='', is_free_hit=False, dismissed_player_id=None,
                    dismissal_position=''):
    match = Match.objects.select_for_update().get(pk=match_id)
    innings = Innings.objects.select_for_update().get(
        match=match, innings_number=match.current_innings_number,
    )
    extra_type = extra_type if extra_type in EXTRA_TYPES else ''
    legal = extra_type not in {'wide', 'no_ball'}
    over, ball = _next_delivery_number(innings, legal)
    # The locked innings state is authoritative. The client-side selection can
    # be stale after a strike rotation, so never attribute a delivery from it.
    batter = innings.striker
    bowler = Player.objects.filter(pk=bowler_id).first() if bowler_id else None
    dismissed_player = (
        Player.objects.filter(pk=dismissed_player_id).first()
        if is_wicket and dismissed_player_id else (batter if is_wicket else None)
    )
    if not batter:
        raise ValueError('Select the current striker before recording a delivery.')
    if not (
        innings.batting_team.players.filter(pk=batter.pk).exists()
        or innings.batting_team.primary_players.filter(pk=batter.pk).exists()
    ):
        raise ValueError('The batter must belong to the batting team.')
    if bowler and not (
        innings.bowling_team.players.filter(pk=bowler.pk).exists()
        or innings.bowling_team.primary_players.filter(pk=bowler.pk).exists()
    ):
        raise ValueError('The bowler must belong to the bowling team.')
    batting_xi = (
        match.team1_playing_xi if innings.batting_team_id == match.team1_id
        else match.team2_playing_xi
    )
    bowling_xi = (
        match.team1_playing_xi if innings.bowling_team_id == match.team1_id
        else match.team2_playing_xi
    )
    if not batting_xi.filter(pk=batter.pk).exists():
        raise ValueError('The striker must belong to the assigned Playing XI.')
    if bowler and not bowling_xi.filter(pk=bowler.pk).exists():
        raise ValueError('The bowler must belong to the assigned Playing XI.')
    if not innings.striker or not innings.non_striker:
        raise ValueError('Select both batsmen before recording a delivery.')
    if not bowler:
        raise ValueError('Select a new bowler before recording a delivery.')
    if dismissed_player and dismissed_player not in (innings.striker, innings.non_striker):
        raise ValueError('The dismissed player must be on the crease.')
    if dismissal_position not in ('striker', 'non_striker'):
        dismissal_position = 'striker'
    if is_wicket and dismissed_player != (
        innings.non_striker if dismissal_position == 'non_striker' else innings.striker
    ):
        raise ValueError('The dismissed player does not match the selected wicket position.')
    runs_off_bat = max(0, int(runs_off_bat))
    extra_runs = max(0, int(extra_runs))
    total = runs_off_bat + extra_runs
    if not commentary:
        commentary = (
            'Wicket! ' if is_wicket else
            'FOUR! ' if runs_off_bat == 4 else
            'SIX! ' if runs_off_bat == 6 else ''
        ) + (f'{total} run{"s" if total != 1 else ""} scored.' if total else 'Dot ball.')
    delivery = BallByBall.objects.create(
        innings=innings, over_number=over, ball_number=ball, batter=batter, bowler=bowler,
        non_striker=innings.non_striker,
        dismissed_player=dismissed_player if is_wicket else None,
        dismissal_position=dismissal_position if is_wicket else '',
        runs_off_bat=runs_off_bat, extra_runs=extra_runs, extra_type=extra_type,
        is_four=runs_off_bat == 4, is_six=runs_off_bat == 6, is_wicket=is_wicket,
        is_wide=extra_type == 'wide', is_no_ball=extra_type == 'no_ball',
        is_bye=extra_type == 'bye', is_leg_bye=extra_type == 'leg_bye',
        is_free_hit=is_free_hit, commentary=commentary,
    )
    recalculate_innings(innings)
    next_striker = innings.striker
    next_non_striker = innings.non_striker
    if is_wicket:
        if dismissal_position == 'non_striker':
            next_non_striker = None
        else:
            next_striker = None
    elif (runs_off_bat + extra_runs) % 2:
        next_striker, next_non_striker = next_non_striker, next_striker

    legal_ball_completed_over = legal and innings.balls == 0
    if legal_ball_completed_over and not innings.is_completed:
        next_striker, next_non_striker = next_non_striker, next_striker
        next_bowler = None
    else:
        next_bowler = bowler
    innings.striker = next_striker
    innings.non_striker = next_non_striker
    innings.current_bowler = next_bowler
    innings.save(update_fields=['striker', 'non_striker', 'current_bowler'])
    if innings.is_completed:
        if innings.innings_number == 1:
            next_innings, _ = Innings.objects.get_or_create(
                match=match, innings_number=2,
                defaults={
                    'batting_team': innings.bowling_team,
                    'bowling_team': innings.batting_team,
                    'target_runs': innings.runs + 1,
                    'striker': None,
                    'non_striker': None,
                    'current_bowler': None,
                },
            )
            match.current_innings_number = 2
            match.status = Match.Status.INNINGS_BREAK
            match.save(update_fields=['current_innings_number', 'status', 'updated_at'])
        else:
            match.status = Match.Status.COMPLETED
            match.save(update_fields=['status', 'updated_at'])
    else:
        match.status = Match.Status.LIVE
        match.save(update_fields=['status', 'updated_at'])
    return delivery, innings


@transaction.atomic
def undo_last_delivery(match_id):
    match = Match.objects.select_for_update().get(pk=match_id)
    innings = Innings.objects.select_for_update().get(
        match=match, innings_number=match.current_innings_number,
    )
    delivery = innings.ball_deliveries.order_by('-timestamp', '-over_number', '-ball_number').first()
    if not delivery:
        return None, innings
    delivery.delete()
    recalculate_innings(innings)
    return delivery, innings


def recalculate_innings(innings):
    from apps.matches.models import FallOfWicket
    deliveries = list(innings.ball_deliveries.select_related('batter', 'bowler').order_by(
        'over_number', 'ball_number', 'timestamp',
    ))
    totals = {'runs': 0, 'wickets': 0, 'wides': 0, 'no_balls': 0, 'byes': 0, 'leg_byes': 0}
    legal_balls = 0
    fow_entries = []
    for delivery in deliveries:
        totals['runs'] += delivery.runs_off_bat + delivery.extra_runs
        if delivery.is_wicket:
            totals['wickets'] += 1
            running_overs = legal_balls // 6
            running_balls_in_over = legal_balls % 6
            overs_str = f'{running_overs}.{running_balls_in_over}'
            if delivery.dismissed_player:
                fow_entries.append({
                    'wicket_number': totals['wickets'],
                    'player': delivery.dismissed_player,
                    'score': totals['runs'],
                    'overs': overs_str,
                })
        extra_counter = {
            'wide': 'wides',
            'no_ball': 'no_balls',
            'bye': 'byes',
            'leg_bye': 'leg_byes',
        }.get(delivery.extra_type)
        if extra_counter:
            totals[extra_counter] += delivery.extra_runs
        if not delivery.is_wide and not delivery.is_no_ball:
            legal_balls += 1
    innings.runs = totals['runs']
    innings.wickets = totals['wickets']
    innings.overs, innings.balls = divmod(legal_balls, 6)
    for field in ('wides', 'no_balls', 'byes', 'leg_byes'):
        setattr(innings, field, totals[field])
    innings.is_completed = innings.wickets >= 10 or (
        innings.match.overs_limit and innings.overs >= innings.match.overs_limit
    ) or (innings.target_runs is not None and innings.runs >= innings.target_runs)
    innings.save(update_fields=[
        'runs', 'wickets', 'overs', 'balls', 'wides', 'no_balls', 'byes',
        'leg_byes', 'is_completed',
    ])
    PlayerMatchInnings.objects.filter(innings=innings).update(
        runs=0, balls_faced=0, fours=0, sixes=0, dots=0,
        dismissal=PlayerMatchInnings.DismissalType.NOT_OUT,
        dismissal_bowler=None, dismissal_fielder=None,
        dismissal_text='not out',
    )
    BowlerMatchInnings.objects.filter(innings=innings).update(
        overs=0, balls=0, runs_conceded=0, wickets=0, wides=0, no_balls=0, dots=0,
    )
    FallOfWicket.objects.filter(innings=innings).delete()
    for fow in fow_entries:
        FallOfWicket.objects.create(
            innings=innings,
            wicket_number=fow['wicket_number'],
            player=fow['player'],
            score=fow['score'],
            overs=fow['overs'],
        )
    wicket_count = 0
    for delivery in deliveries:
        if delivery.batter:
            batter, _ = PlayerMatchInnings.objects.get_or_create(
                innings=innings, player=delivery.batter, defaults={'batting_position': 1},
            )
            batter.runs += delivery.runs_off_bat
            batter.fours += int(delivery.is_four)
            batter.sixes += int(delivery.is_six)
            batter.dots += int(delivery.runs_off_bat == 0 and not delivery.extra_type)
            batter.balls_faced += int(not delivery.is_wide and not delivery.is_no_ball)
            if delivery.is_wicket and delivery.dismissed_player == delivery.batter:
                batter.dismissal = (
                    PlayerMatchInnings.DismissalType.RUN_OUT
                    if delivery.dismissal_position in ('striker', 'non_striker')
                    else PlayerMatchInnings.DismissalType.BOWLED
                )
                batter.dismissal_bowler = delivery.bowler
                bowler_name = delivery.bowler.name if delivery.bowler else 'bowler'
                batter.dismissal_text = (
                    'run out' if delivery.dismissal_position in ('striker', 'non_striker')
                    else f'b {bowler_name}'
                )
            batter.save()
        if delivery.is_wicket and delivery.dismissed_player and delivery.dismissed_player != delivery.batter:
            dismissed, _ = PlayerMatchInnings.objects.get_or_create(
                innings=innings, player=delivery.dismissed_player,
                defaults={'batting_position': 1},
            )
            dismissed.dismissal = (
                PlayerMatchInnings.DismissalType.RUN_OUT
                if delivery.dismissal_position in ('striker', 'non_striker')
                else PlayerMatchInnings.DismissalType.BOWLED
            )
            dismissed.dismissal_text = 'run out'
            dismissed.save(update_fields=['dismissal', 'dismissal_text'])
        if delivery.is_wicket:
            wicket_count += 1
        if delivery.bowler:
            bowler, _ = BowlerMatchInnings.objects.get_or_create(innings=innings, player=delivery.bowler)
            bowler.runs_conceded += delivery.runs_off_bat + (
                delivery.extra_runs if delivery.extra_type in {'wide', 'no_ball'} else 0
            )
            bowler.wickets += int(delivery.is_wicket)
            bowler.wides += int(delivery.is_wide)
            bowler.no_balls += int(delivery.is_no_ball)
            legal = not delivery.is_wide and not delivery.is_no_ball
            if legal:
                bowler.balls += 1
                if bowler.balls >= 6:
                    bowler.overs += 1
                    bowler.balls = 0
            bowler.save()
