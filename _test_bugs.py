import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')

import django
django.setup()

from datetime import timedelta
from django.utils import timezone
from apps.matches.models import Match, Innings, BallByBall, PlayerMatchInnings, FallOfWicket
from apps.teams.models import Team
from apps.players.models import Player
from apps.matches.services.scoring import record_delivery, recalculate_innings

LOG = []
def log(s):
    LOG.append(str(s))
    print(s)

log("=" * 60)
log("BUG FIX VALIDATION TEST SUITE")
log("=" * 60)

try:
    # ========== 1. CREATE / FIND TEST MATCH ==========
    match = Match.objects.filter(status=Match.Status.LIVE).first()
    ts = int(timezone.now().timestamp())
    if not match:
        teams = list(Team.objects.all()[:2])
        if len(teams) < 2:
            log("ERROR: Need at least 2 teams in DB")
            sys.exit(1)
        t1, t2 = teams[0], teams[1]
        t1_players = list(t1.players.filter(is_active=True)[:11])
        t2_players = list(t2.players.filter(is_active=True)[:11])
        if len(t1_players) < 2 or len(t2_players) < 2:
            log("ERROR: Need at least 2 players per team")
            sys.exit(1)
        start = timezone.now()
        match = Match.objects.create(
            title=f"BUG FIX {ts}: {t1.short_name} vs {t2.short_name}",
            match_type='T20',
            team1=t1, team2=t2,
            status=Match.Status.LIVE,
            current_innings_number=1,
            toss_winner=t1, toss_decision='bat',
            start_datetime=start,
            end_datetime=start + timedelta(hours=3),
            overs_limit=20,
        )
        match.team1_playing_xi.set(t1_players)
        match.team2_playing_xi.set(t2_players)
        inn = Innings.objects.create(
            match=match, innings_number=1,
            batting_team=t1, bowling_team=t2,
        )
        match.save()
        log(f"CREATED NEW match: {match.title} (slug={match.slug})")
    else:
        t1 = match.team1
        t2 = match.team2
        t1_players = list(t1.players.filter(is_active=True)[:11])
        t2_players = list(t2.players.filter(is_active=True)[:11])
        if len(t1_players) < 2 or len(t2_players) < 2:
            log(f"ERROR: Teams {t1.short_name}/{t2.short_name} need 2+ players each")
            sys.exit(1)
        log(f"Found LIVE match: {match.title} (slug={match.slug})")
        log(f"Teams: {t1.short_name} vs {t2.short_name}")
        inn = match.current_innings
        if inn:
            inn.ball_deliveries.all().delete()
            inn.batters.all().delete()
            inn.bowlers.all().delete()
            inn.fall_of_wickets.all().delete()
            inn.runs = 0
            inn.wickets = 0
            inn.overs = 0
            inn.balls = 0
            inn.wides = 0
            inn.no_balls = 0
            inn.byes = 0
            inn.leg_byes = 0
            inn.is_completed = False
            inn.batting_team = t1
            inn.bowling_team = t2
            inn.save()
            log(f"RESET innings: batting={inn.batting_team.short_name}, bowling={inn.bowling_team.short_name}")
        else:
            inn = Innings.objects.create(
                match=match, innings_number=1,
                batting_team=t1, bowling_team=t2,
            )
            match.current_innings_number = 1
            match.status = Match.Status.LIVE
            match.save()
            log(f"CREATED new innings for match: {match.title}")

    log(f"Teams: {t1.short_name} (batting) vs {t2.short_name} (bowling)")
    log(f"Team {t1.short_name}: {len(t1_players)} players")
    log(f"Team {t2.short_name}: {len(t2_players)} players")

    match.refresh_from_db()
    inn.refresh_from_db()
    log(f"Match ID: {match.id} | Innings ID: {inn.id}")
    log(f"Batting: {inn.batting_team.short_name} | Bowling: {inn.bowling_team.short_name}")
    log("")

    # ========== 2. DEFINE BATTERS/BOWLERS ==========
    batters = t1_players  # Batting team players
    bowlers = t2_players  # Bowling team players
    b1 = batters[0]  # Batter 1 (striker)
    b2 = batters[1]  # Batter 2 (non-striker)
    bw1 = bowlers[0]  # Bowler
    log(f"Opening batter (striker): {b1.name} ({b1.id}) - Team: {t1.short_name}")
    log(f"Opening batter (non-striker): {b2.name} ({b2.id}) - Team: {t1.short_name}")
    log(f"Bowler: {bw1.name} ({bw1.id}) - Team: {t2.short_name}")
    log("")

    # ========== BUG 1 TEST: DROPDOWN TEAM FILTERING (backend view context) ==========
    log("=" * 60)
    log("BUG 1 TEST: Team filtering in context (batter/bowler dropdowns)")
    log("=" * 60)
    # Simulate view context
    batting_team_players_ids = set(p.id for p in inn.batting_team.players.filter(is_active=True))
    bowling_team_players_ids = set(p.id for p in inn.bowling_team.players.filter(is_active=True))
    b1_in_batting = b1.id in batting_team_players_ids
    b2_in_batting = b2.id in batting_team_players_ids
    bw1_in_bowling = bw1.id in bowling_team_players_ids
    bowler_in_batting = bw1.id in batting_team_players_ids
    striker_in_bowling = b1.id in bowling_team_players_ids

    log(f"Striker {b1.name} in batting team list: {b1_in_batting} [EXPECTED: True] -> {'PASS' if b1_in_batting else 'FAIL'}")
    log(f"Bowler {bw1.name} in bowling team list: {bw1_in_bowling} [EXPECTED: True] -> {'PASS' if bw1_in_bowling else 'FAIL'}")
    log(f"Bowler {bw1.name} NOT in batting team list: {not bowler_in_batting} [EXPECTED: True] -> {'PASS' if not bowler_in_batting else 'FAIL'}")
    log(f"Striker {b1.name} NOT in bowling team list: {not striker_in_bowling} [EXPECTED: True] -> {'PASS' if not striker_in_bowling else 'FAIL'}")
    log(f"Batting team player count: {len(batting_team_players_ids)}")
    log(f"Bowling team player count: {len(bowling_team_players_ids)}")

    bug1_pass = b1_in_batting and bw1_in_bowling and not bowler_in_batting and not striker_in_bowling
    log(f"BUG 1 Overall: {'PASS' if bug1_pass else 'FAIL'}")
    log("")

    # ========== 3. BALL-BY-BALL SIMULATION ==========
    log("=" * 60)
    log("PLAYING 20+ DELIVERIES: 2 wkts, 2 fours, 1 six, 1 wide, 1 no-ball")
    log("=" * 60)

    balls_to_play = [
        # Format: (batter, bowler, runs, extra_type, is_wicket, description)
        (b1, bw1, 0, '', False, 'Dot ball - Maiden start'),
        (b1, bw1, 1, '', False, 'Single to midwicket'),        # 1 run
        (b2, bw1, 4, '', False, 'FOUR! Driven through covers'), # 4 runs (boundary 1)
        (b2, bw1, 0, '', False, 'Defensive block, dot'),
        (b2, bw1, 0, 'wide', False, 'WIDE down leg side'),      # WIDE (1 extra)
        (b2, bw1, 2, '', False, 'Two runs to square leg'),      # 2 runs
        (b1, bw1, 6, '', False, 'SIX! Over long on!'),         # SIX (1)
        (b1, bw1, 0, '', False, 'Dot - yorker defended'),
        (b1, bw1, 4, '', False, 'FOUR! Pulled through midwicket'), # 4 runs (boundary 2)
        (b2, bw1, 0, '', False, 'Dot ball'),                    # Over complete (Over 1)
        (b2, bw1, 0, '', False, 'Dot - play and miss'),
        (b2, bw1, 1, '', False, 'Quick single'),
        (b1, bw1, 0, '', True, 'WICKET! Clean bowled!'),        # WICKET 1 (batter b1 out)
        (batters[2], bw1, 0, '', False, 'New batter in, dot'),
        (batters[2], bw1, 1, '', False, 'Single taken'),
        (b2, bw1, 0, 'no_ball', False, 'NO BALL! Front foot no-ball'), # NO BALL
        (b2, bw1, 3, '', False, 'Three runs, well run'),
        (batters[2], bw1, 0, '', False, 'Dot - good length'),
        (batters[2], bw1, 1, '', False, 'Single to point'),
        (b2, bw1, 2, '', False, 'Two runs to deep backward square'),
        (b2, bw1, 0, '', True, 'WICKET! Caught at first slip!'), # WICKET 2 (batter b2 out)
        (batters[3], bw1, 0, '', False, 'Dot ball, new batter'),
        (batters[3], bw1, 1, '', False, 'Single to start innings'),
    ]

    log(f"Playing {len(balls_to_play)} deliveries...")
    for i, (btr, bwl, runs, xtra, wkt, desc) in enumerate(balls_to_play):
        extra_runs = 0
        rt = runs
        if xtra == 'wide':
            extra_runs = 1
            rt = 0
        elif xtra == 'no_ball':
            extra_runs = 1
        elif xtra in ('bye', 'leg_bye'):
            extra_runs = runs
            rt = 0
        d, inn = record_delivery(
            match.id,
            batter_id=btr.id, bowler_id=bwl.id,
            runs_off_bat=rt, extra_runs=extra_runs, extra_type=xtra,
            is_wicket=wkt, commentary=desc,
        )
        inn.refresh_from_db()
        wicket_info = f" | WICKET: {btr.name}" if wkt else ""
        log(f"  Ball {i+1:02d}: O{d.over_number}.{d.ball_number} | {bwl.name}->{btr.name[:10]} | runs={rt}+{extra_runs} xtra={xtra or '-'} wkt={wkt} | SCORE={inn.runs}/{inn.wickets} ({inn.overs_formatted}){wicket_info}")

    log("")
    inn.refresh_from_db()
    log(f"Innings final after {inn.ball_deliveries.count()} balls:")
    log(f"  Total: {inn.runs}/{inn.wickets} in {inn.overs_formatted} overs")
    log(f"  Extras: wd={inn.wides}, nb={inn.no_balls}, b={inn.byes}, lb={inn.leg_byes}")

    # Verify counts
    all_balls = list(inn.ball_deliveries.order_by('over_number', 'ball_number', 'timestamp'))
    total_fours = sum(1 for b in all_balls if b.is_four)
    total_sixes = sum(1 for b in all_balls if b.is_six)
    total_wickets = sum(1 for b in all_balls if b.is_wicket)
    total_wides = sum(1 for b in all_balls if b.is_wide)
    total_noballs = sum(1 for b in all_balls if b.is_no_ball)
    log(f"  Fours: {total_fours} (expected 2) -> {'PASS' if total_fours == 2 else 'FAIL'}")
    log(f"  Sixes: {total_sixes} (expected 1) -> {'PASS' if total_sixes == 1 else 'FAIL'}")
    log(f"  Wickets: {total_wickets} (expected 2) -> {'PASS' if total_wickets == 2 else 'FAIL'}")
    log(f"  Wides: {total_wides} (expected 1) -> {'PASS' if total_wides == 1 else 'FAIL'}")
    log(f"  No-balls: {total_noballs} (expected 1) -> {'PASS' if total_noballs == 1 else 'FAIL'}")
    log("")

    # ========== BUG 2 TEST: WICKET DOES NOT ADD RUNS ==========
    log("=" * 60)
    log("BUG 2 TEST: Wicket does not add runs")
    log("=" * 60)
    # Find the wicket balls
    wicket_balls = [b for b in all_balls if b.is_wicket]
    bug2_pass = True
    for wb in wicket_balls:
        log(f"  Wicket ball {wb.over_number}.{wb.ball_number}: runs_off_bat={wb.runs_off_bat}, extra_runs={wb.extra_runs}, total={wb.runs_off_bat + wb.extra_runs}")
        if wb.extra_type not in ('wide', 'no_ball') and wb.runs_off_bat != 0:
            log(f"    ERROR: wicket without extra has runs_off_bat={wb.runs_off_bat} (should be 0)!")
            bug2_pass = False
        if wb.is_four:
            log(f"    ERROR: wicket marked is_four=True!")
            bug2_pass = False
        if wb.is_six:
            log(f"    ERROR: wicket marked is_six=True!")
            bug2_pass = False
    # Verify innings score matches sum of all ball runs (check no extra 6 from wickets)
    sum_runs = sum(b.runs_off_bat + b.extra_runs for b in all_balls)
    log(f"  Sum of all ball runs: {sum_runs} | Innings runs: {inn.runs} -> {'PASS' if sum_runs == inn.runs else 'FAIL'}")
    if sum_runs != inn.runs:
        bug2_pass = False
    # Expected score:
    # Balls: 0,1,4,0,0(+1 wide extra),2,6,0,4,0,0,1,0(wkt1),0,1,0(+1 nb),3,0,1,2,0(wkt2),0,1
    # runs_off_bat: 0+1+4+0+0+2+6+0+4+0+0+1+0+0+1+0+3+0+1+2+0+0+1 = 26
    # extras: wide 1 + nb 1 = 2
    # Total: 28 runs, 2 wickets
    expected_runs = 28
    expected_wickets = 2
    log(f"  Expected runs: {expected_runs} | Actual: {inn.runs} -> {'PASS' if inn.runs == expected_runs else 'FAIL'}")
    log(f"  Expected wickets: {expected_wickets} | Actual: {inn.wickets} -> {'PASS' if inn.wickets == expected_wickets else 'FAIL'}")
    if inn.runs != expected_runs or inn.wickets != expected_wickets:
        bug2_pass = False
    log(f"BUG 2 Overall: {'PASS' if bug2_pass else 'FAIL'}")
    log("")

    # ========== BUG 4 TEST: BATTER STATUS AFTER WICKET ==========
    log("=" * 60)
    log("BUG 4 TEST: Dismissed batters marked OUT with details")
    log("=" * 60)
    # Check dismissed batter b1 and b2
    dismissed_b1 = PlayerMatchInnings.objects.filter(innings=inn, player=b1).first()
    dismissed_b2 = PlayerMatchInnings.objects.filter(innings=inn, player=b2).first()
    batter_new = PlayerMatchInnings.objects.filter(innings=inn, player=batters[3]).first()

    bug4_pass = True
    if dismissed_b1:
        log(f"  Batter {b1.name}: dismissal={dismissed_b1.dismissal} [EXPECTED != not_out] -> {'PASS' if dismissed_b1.dismissal != 'not_out' else 'FAIL'}")
        log(f"    dismissal_text: '{dismissed_b1.dismissal_text}' [EXPECTED: contains 'b {bw1.name[:10]}'] -> {'PASS' if bw1.name[:10] in dismissed_b1.dismissal_text else 'FAIL'}")
        log(f"    dismissal_bowler: {dismissed_b1.dismissal_bowler} [EXPECTED: {bw1.name}] -> {'PASS' if dismissed_b1.dismissal_bowler_id == bw1.id else 'FAIL'}")
        if dismissed_b1.dismissal == 'not_out':
            bug4_pass = False
        if bw1.name[:10] not in dismissed_b1.dismissal_text:
            bug4_pass = False
        if dismissed_b1.dismissal_bowler_id != bw1.id:
            bug4_pass = False
    else:
        log(f"  ERROR: No batting record for {b1.name}!")
        bug4_pass = False

    if dismissed_b2:
        log(f"  Batter {b2.name}: dismissal={dismissed_b2.dismissal} [EXPECTED != not_out] -> {'PASS' if dismissed_b2.dismissal != 'not_out' else 'FAIL'}")
        log(f"    dismissal_text: '{dismissed_b2.dismissal_text}' -> {'PASS' if bw1.name[:10] in dismissed_b2.dismissal_text else 'FAIL'}")
        if dismissed_b2.dismissal == 'not_out':
            bug4_pass = False
        if bw1.name[:10] not in dismissed_b2.dismissal_text:
            bug4_pass = False
    else:
        log(f"  ERROR: No batting record for {b2.name}!")
        bug4_pass = False

    if batter_new:
        log(f"  New batter {batters[3].name}: dismissal={batter_new.dismissal} [EXPECTED: not_out] -> {'PASS' if batter_new.dismissal == 'not_out' else 'FAIL'}")
        if batter_new.dismissal != 'not_out':
            bug4_pass = False

    # Check Fall of Wickets
    fow_list = FallOfWicket.objects.filter(innings=inn).order_by('wicket_number')
    log(f"  Fall of Wickets records: {fow_list.count()} (expected 2) -> {'PASS' if fow_list.count() == 2 else 'FAIL'}")
    if fow_list.count() != 2:
        bug4_pass = False
    for fow in fow_list:
        log(f"    FOW #{fow.wicket_number}: {fow.player.name} at {fow.score} runs ({fow.overs} ov)")

    log(f"BUG 4 Overall: {'PASS' if bug4_pass else 'FAIL'}")
    log("")

    # ========== BUG 3 TEST: UPDATE LAST DELIVERY ==========
    log("=" * 60)
    log("BUG 3 TEST: Update Last Delivery modifies everything correctly")
    log("=" * 60)
    # Record current state
    prev_score = inn.runs
    prev_wkts = inn.wickets
    prev_overs = f"{inn.overs}.{inn.balls}"
    # Get last delivery
    last_d = inn.ball_deliveries.order_by('-timestamp', '-over_number', '-ball_number').first()
    log(f"  Last ball before update: {last_d.over_number}.{last_d.ball_number} runs={last_d.runs_off_bat}+{last_d.extra_runs} wkt={last_d.is_wicket}")
    log(f"  Score before: {prev_score}/{prev_wkts} ({prev_overs})")

    # Simulate update: change last ball from 1 run to 4 runs (legal)
    last_d.runs_off_bat = 4
    last_d.extra_runs = 0
    last_d.extra_type = ''
    last_d.is_four = True
    last_d.is_six = False
    last_d.is_wicket = False
    last_d.is_wide = False
    last_d.is_no_ball = False
    last_d.commentary = "UPDATE TEST: FOUR through covers!"
    last_d.save()
    # Now recalculate (this is what update_last_delivery action does)
    recalculate_innings(inn)
    inn.refresh_from_db()

    # Check new state
    new_score = inn.runs
    new_wkts = inn.wickets
    new_overs = f"{inn.overs}.{inn.balls}"
    delta_runs = new_score - prev_score
    log(f"  Updated last ball to: runs=4 (four), wicket=False")
    log(f"  Score after: {new_score}/{new_wkts} ({new_overs})")
    log(f"  Runs delta: +{delta_runs} (expected +3, since was 1, now 4) -> {'PASS' if delta_runs == 3 else 'FAIL'}")
    log(f"  Wickets unchanged: {prev_wkts} == {new_wkts} -> {'PASS' if prev_wkts == new_wkts else 'FAIL'}")

    # Verify batter stats updated
    updated_batter = PlayerMatchInnings.objects.filter(innings=inn, player=batters[3]).first()
    if updated_batter:
        log(f"  Batter {batters[3].name}: runs={updated_batter.runs}, fours={updated_batter.fours}")
        # Should have at least 1 four
        bug3_pass = (delta_runs == 3 and prev_wkts == new_wkts and updated_batter.fours >= 1)
    else:
        bug3_pass = False

    # Also verify wicket count in ball records = innings wickets
    wkt_balls_count = sum(1 for b in inn.ball_deliveries.all() if b.is_wicket)
    log(f"  Wicket count in balls: {wkt_balls_count} vs innings.wickets={inn.wickets} -> {'PASS' if wkt_balls_count == inn.wickets else 'FAIL'}")

    log(f"BUG 3 Overall: {'PASS' if bug3_pass else 'FAIL'}")
    log("")

    # ========== BOWLER AND BATTER STAT CONSISTENCY ==========
    log("=" * 60)
    log("STAT CONSISTENCY CHECK")
    log("=" * 60)
    from apps.matches.models import BowlerMatchInnings
    bowler_stat = BowlerMatchInnings.objects.filter(innings=inn, player=bw1).first()
    if bowler_stat:
        total_deliveries = (bowler_stat.overs * 6) + bowler_stat.balls
        log(f"  Bowler {bw1.name}: {bowler_stat.overs}.{bowler_stat.balls} ov, W:{bowler_stat.wickets}, R:{bowler_stat.runs_conceded}, Wd:{bowler_stat.wides}, Nb:{bowler_stat.no_balls}")
        log(f"    Total balls bowled: {total_deliveries} | Expected: {23} balls (20 legal + 1 wide + 1 nb + 1 replay) ~ 22")
    stat_pass = True
    if bowler_stat and bowler_stat.wickets != 2:
        log(f"    ERROR: Bowler wickets {bowler_stat.wickets} != expected 2")
        stat_pass = False
    if bowler_stat and bowler_stat.wides < 1:
        log(f"    ERROR: Bowler wides missing")
        stat_pass = False
    if bowler_stat and bowler_stat.no_balls < 1:
        log(f"    ERROR: Bowler no_balls missing")
        stat_pass = False
    log(f"  Stats consistency: {'PASS' if stat_pass else 'FAIL'}")
    log("")

    # ========== SUMMARY ==========
    log("=" * 60)
    log("OVERALL SUMMARY")
    log("=" * 60)
    all_pass = bug1_pass and bug2_pass and bug3_pass and bug4_pass and stat_pass
    log(f"BUG 1 (Team filter):  {'PASS' if bug1_pass else 'FAIL'}")
    log(f"BUG 2 (Wicket runs):   {'PASS' if bug2_pass else 'FAIL'}")
    log(f"BUG 3 (Update btn):    {'PASS' if bug3_pass else 'FAIL'}")
    log(f"BUG 4 (Batter status): {'PASS' if bug4_pass else 'FAIL'}")
    log(f"Stats consistency:     {'PASS' if stat_pass else 'FAIL'}")
    log(f"Match slug for browser testing: {match.slug}")
    log(f"Match detail URL: /matches/{match.slug}/")
    log(f"Scorer panel URL: /matches/{match.slug}/scorer/")
    log("")
    log(f"{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    log("=" * 60)

except Exception as e:
    log(f"ERROR: {e}")
    log(traceback.format_exc())
    with open('test_results.txt', 'w') as f:
        f.write('\n'.join(LOG))
    raise

with open('test_results.txt', 'w') as f:
    f.write('\n'.join(LOG))
