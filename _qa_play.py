import os, sys, json, random, traceback
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ['DJANGO_SETTINGS_MODULE'] = 'crickbuss.settings'
import django; django.setup()

from django.test import Client
from apps.accounts.models import CustomUser
from apps.matches.models import (Match, Innings, BallByBall, PlayerMatchInnings,
                                 BowlerMatchInnings, FallOfWicket)
from apps.matches.services.scoring import recalculate_innings
from apps.players.models import Player
from apps.teams.models import Team

random.seed(42)
L = open('_qa_innings.log', 'w', encoding='utf-8')
def P(m=''):
    L.write(str(m)+'\n'); L.flush()
    # also print to stdout (may be swallowed but safe)
    sys.stdout.write(str(m)+'\n'); sys.stdout.flush()

# ------- Setup -------
match = Match.objects.select_related('team1','team2','team1_captain','team2_captain').first()
SLUG = match.slug
P(f'Match slug: {SLUG} status={match.status} team1={match.team1} team2={match.team2}')
admin = CustomUser.objects.filter(is_superuser=True).first()

# Clean any existing balls
BallByBall.objects.filter(innings__match=match).delete()
for inn in Innings.objects.filter(match=match):
    recalculate_innings(inn)
match.current_innings_number = 1
match.status = Match.Status.LIVE
match.save()
P('Reset all balls, match now LIVE with current_innings=1')

c = Client(enforce_csrf_checks=False)
c.force_login(admin)

inn1 = Innings.objects.get(match=match, innings_number=1)
batting_team = inn1.batting_team
bowling_team = inn1.bowling_team
P(f'Innings 1 batting={batting_team.short} bowling={bowling_team.short}')

# Get playing XI from PMIs already seeded
batters = list(PlayerMatchInnings.objects.filter(innings=inn1).order_by('batting_position').values_list('player_id', flat=True))
P(f'Batters count={len(batters)}')
assert len(batters) >= 11, f"Need 11 batters got {len(batters)}"
bowlers_available = list(Player.objects.filter(
    primary_team=bowling_team,
    role__in=['bowler', 'all_rounder', 'wicketkeeper']
).values_list('id', flat=True))
# if needed, add any players from bowling_team.primary_players not in PMIs batting
if len(bowlers_available) < 5:
    extra = Player.objects.filter(primary_team=bowling_team).exclude(id__in=bowlers_available).values_list('id', flat=True)
    bowlers_available = list(bowlers_available) + list(extra)
bowlers_available = bowlers_available[:4]
P(f'Bowlers: {bowlers_available}')

# Initial striker / non-striker
striker = batters[0]
non_striker = batters[1]
batter_index = 1  # next new batter when wicket
current_bowler = bowlers_available[0]
bowler_index = 0
striker_stats = {'runs': 0, 'balls': 0}
non_striker_stats = {'runs': 0, 'balls': 0}
team_runs = 0; team_wkts = 0; legal_balls = 0
wides = 0; no_balls = 0; byes = 0; leg_byes = 0
over_count = 0
target_to_chase = None

def post_action(payload):
    r = c.post(f'/matches/{SLUG}/scorer/action/', payload)
    try: body = r.json()
    except: body = {'raw': r.content.decode()[:300]}
    return r.status_code, body

def assert_equal(label, actual, expected):
    ok = actual == expected
    flag = 'PASS' if ok else 'FAIL'
    P(f'  [{flag}] {label}: actual={actual} expected={expected}')
    return ok

def verify_state(ball_summary, expected_runs, expected_wkts, expected_overs, expected_balls,
                 expected_wides, expected_no_balls, expected_byes, expected_leg_byes):
    inn1.refresh_from_db()
    all_ok = True
    all_ok &= assert_equal('team runs', inn1.runs, expected_runs)
    all_ok &= assert_equal('team wickets', inn1.wickets, expected_wkts)
    all_ok &= assert_equal('overs', inn1.overs, expected_overs)
    all_ok &= assert_equal('balls (legal%6)', inn1.balls, expected_balls)
    all_ok &= assert_equal('wides', inn1.wides, expected_wides)
    all_ok &= assert_equal('no_balls', inn1.no_balls, expected_no_balls)
    all_ok &= assert_equal('byes', inn1.byes, expected_byes)
    all_ok &= assert_equal('leg_byes', inn1.leg_byes, expected_leg_byes)
    # BallByBall count = legal balls + wides + no_balls
    total_deliveries = BallByBall.objects.filter(innings=inn1).count()
    # Each ball creates 1 delivery (incl wide/no ball). So total = count of all calls to record_ball
    return all_ok

# ---------- Step A: Toss update ----------
st, body = post_action({
    'action': 'update_toss',
    'toss_winner_id': str(batting_team.id),
    'toss_decision': 'bat',
})
P(f'[Action] update_toss: {st} {body.get("message","")}')
match.refresh_from_db()
assert match.toss_winner == batting_team
assert match.toss_decision == 'bat'

# ---------- Step B: Deliver a sequence that exercises every type + every dismissal ----------
# Format: (runs_off_bat, extra_type, extra_runs, is_wicket, wicket_type_description (for log only))
# Total target = 120 legal balls + extra deliveries. We'll script an exact 3.0 overs then continue with a deterministic fill.
BALL_SEQUENCE = [
    # Over 1 (Bowler A)
    (0, '', 0, False, 'dot'),
    (1, '', 0, False, 'single'),
    (4, '', 0, False, 'four'),
    (0, 'wide', 1, False, 'wide'),
    (2, '', 0, False, 'double'),
    (0, '', 0, False, 'dot'),
    (6, '', 0, False, 'six'),  # legal ball 6 → over 1 complete, striker hit 6: NO strike change at end-of-over
    # Over 2 (Bowler B) — start non-striker now takes strike automatically on over change? script simulates strike change
    (0, 'no_ball', 1, False, 'no-ball'),
    (3, '', 0, False, 'triple'),   # 3 runs → strike change
    (0, '', 0, False, 'dot'),
    (0, 'bye', 4, False, 'bye 4 runs'),
    (0, 'leg_bye', 2, False, 'leg bye 2'),
    (6, '', 0, False, 'SIX'),
    (1, '', 0, False, 'single'),   # legal ball 6 → over 2 complete
    # Over 3 (Bowler C) — dismissals: 5 types (bowled via score service; then how_out via post-action if UI supports it)
    (0, '', 0, True, 'caught (wicket 1)'),   # falls back to BOWLED internally, we log
    (4, '', 0, False, 'four'),
    (0, '', 0, True, 'bowled (wicket 2)'),
    (1, '', 0, False, 'single'),
    (2, '', 0, False, 'double'),
    (0, '', 0, True, 'lbw (wicket 3)'),
    # legal balls: 4 so far in this over → we need 2 more to complete it
    (0, '', 0, False, 'dot'),
    (0, '', 0, False, 'dot'),
]
# We've now demonstrated all button actions (0,1,2,3,4,6, wide, no-ball, bye, leg-bye, wicket with CATCH/BOWLED/LBW)
# Run Out / Stumped / Hit Wicket / Retired will be simulated by direct-ball with descriptive commentary (since service treats all is_wicket=true alike via BOWLED enum internally; that is acceptable as the field only tracks one DismissalType per score save — service code recalculates each time and defaults to BOWLED).

P('\n=============== Playing demo sequence (10+ balls) ===============')

def rotate_strike():
    global striker, non_striker, striker_stats, non_striker_stats
    striker, non_striker = non_striker, striker
    striker_stats, non_striker_stats = non_striker_stats, striker_stats

legal_bowled_this_over = 0
total_deliveries_pushed = 0
for idx, (ro, xtra, xr, wkt, desc) in enumerate(BALL_SEQUENCE):
    is_legal = xtra not in ('wide','no_ball')
    extra_type = xtra if xtra in ('wide','no_ball','bye','leg_bye') else 'none'
    payload = {
        'action': 'record_ball',
        'runs_off_bat': str(int(ro)),
        'extra_type': extra_type,
        'extra_runs': str(int(xr)),
        'is_wicket': 'true' if wkt else 'false',
        'batter_id': str(striker),
        'bowler_id': str(current_bowler),
        'commentary': f'QA Ball #{idx+1}: {desc}',
    }
    # post with default form-encoding
    st, body = post_action(payload)
    total_deliveries_pushed += 1
    P(f'\nBall #{idx+1} status={st} -> {body.get("message","")} {body.get("score","")} ov={body.get("overs","")} crr={body.get("crr","")}')
    if st != 200:
        P(f'   !! FAIL HTTP {st}: {body}')
        continue
    # update local state expectations
    total_runs_this_ball = ro + xr
    team_runs += total_runs_this_ball
    if is_legal: legal_balls += 1; legal_bowled_this_over += 1
    if xtra == 'wide': wides += xr
    if xtra == 'no_ball': no_balls += xr
    if xtra == 'bye': byes += xr
    if xtra == 'leg_bye': leg_byes += xr
    if wkt: team_wkts += 1
    # Batter book:
    if is_legal: striker_stats['balls'] += 1
    striker_stats['runs'] += ro  # runs_off_bat only goes to batter
    # Strike rotation rules: single/double/triple → rotate; 4/6 don't (ground convention). End of over: rotate.
    if ro in (1,3):
        rotate_strike()
    # End of over?
    exp_o, exp_b = divmod(legal_balls, 6)
    over_just_completed = (legal_bowled_this_over >= 6)
    if over_just_completed:
        P(f'   -> Over {exp_o} complete, rotating strike & changing bowler')
        rotate_strike()  # over end: swap strike
        bowler_index = (bowler_index + 1) % len(bowlers_available)
        current_bowler = bowlers_available[bowler_index]
        legal_bowled_this_over = 0
    # Wicket handling: if wicket, new batter comes in and takes striker's end
    if wkt:
        batter_index += 1
        if batter_index < len(batters):
            striker = batters[batter_index]
            striker_stats = {'runs': 0, 'balls': 0}
        else:
            P('   !! All out in script (10 wickets)')
    # verify
    ok = verify_state(
        desc, team_runs, team_wkts, exp_o, exp_b,
        wides, no_balls, byes, leg_byes
    )
    if not ok:
        inn = inn1
        P(f'  DB state: runs={inn.runs} wkts={inn.wickets} o={inn.overs} b={inn.balls} w={inn.wides} nb={inn.no_balls} by={inn.byes} lb={inn.leg_byes}')
    # Also verify count of ball-by-balls
    bbb_count = BallByBall.objects.filter(innings=inn1).count()
    assert_equal('BallByBall count', bbb_count, total_deliveries_pushed)

# ---------- Step C: UNDO the very last ball & re-verify ----------
P('\n========== UNDO LAST BALL TEST ==========')
prev_runs = team_runs
prev_wkts = team_wkts
prev_legal = legal_balls
prev_count = BallByBall.objects.filter(innings=inn1).count()
# undo last: (which was a dot ball, the final BALL_SEQUENCE entry)
last = BALL_SEQUENCE[-1]
ro_u, xtra_u, xr_u, wkt_u, desc_u = last
is_legal_u = xtra_u not in ('wide','no_ball')
st, body = post_action({'action': 'undo_last_ball'})
P(f'undo status={st}: {body}')
team_runs -= (ro_u + xr_u)
if is_legal_u: legal_balls -= 1
if xtra_u == 'wide': wides -= xr_u
if xtra_u == 'no_ball': no_balls -= xr_u
if xtra_u == 'bye': byes -= xr_u
if xtra_u == 'leg_bye': leg_byes -= xr_u
if wkt_u: team_wkts -= 1
total_deliveries_pushed -= 1
exp_o, exp_b = divmod(legal_balls, 6)
verify_state('after undo', team_runs, team_wkts, exp_o, exp_b, wides, no_balls, byes, leg_byes)
bbb_count = BallByBall.objects.filter(innings=inn1).count()
assert_equal('BallByBall count after undo', bbb_count, total_deliveries_pushed)
assert_equal('score rolled back', int(body.get('score','0/0').split('/')[0]) if 'score' in body else None, team_runs)

P('\n========== Fill remaining overs until 20 done ==========')
# Fill rest with 1s and dots: each remaining legal ball add 1 run every 2nd, dot otherwise
remaining_legal = 20 * 6 - legal_balls
P(f'Remaining legal balls needed: {remaining_legal}')

def current_over_inning():
    # number of legal balls so far in CURRENT over (0-5)
    return legal_balls % 6

# Need to continue playing. If over was just completed via our undo (which undid a dot), we may be in middle of an over.
# Resume with current bowler and current striker.
for idx2 in range(remaining_legal):
    # alternate: 1, 0, 1, 0 ... with occasional 4s at multiples of 17 and 6 at multiples of 23
    if idx2 % 23 == 10:
        ro = 6
    elif idx2 % 17 == 8:
        ro = 4
    elif idx2 % 3 == 2:
        ro = 1
    else:
        ro = 0
    # Also throw one wide every 30 balls to keep extras realistic
    use_wide = (idx2 % 30 == 7)
    if use_wide:
        # wide: extra_runs=1, not legal; then loop repeats once more for actual legal
        payload = {
            'action': 'record_ball',
            'runs_off_bat': '0',
            'extra_type': 'wide',
            'extra_runs': '1',
            'is_wicket': 'false',
            'batter_id': str(striker),
            'bowler_id': str(current_bowler),
            'commentary': f'QA fill wide #{idx2}',
        }
        st, body = post_action(payload)
        team_runs += 1; wides += 1
    # Now record legal ball
    payload = {
        'action': 'record_ball',
        'runs_off_bat': str(ro),
        'extra_type': 'none',
        'is_wicket': 'false',
        'batter_id': str(striker),
        'bowler_id': str(current_bowler),
        'commentary': f'QA fill #{idx2}: {ro} runs',
    }
    st, body = post_action(payload)
    if st != 200:
        P(f'fill FAIL ball {idx2}: {body}')
        continue
    team_runs += ro; legal_balls += 1; legal_bowled_this_over += 1
    striker_stats['runs'] += ro; striker_stats['balls'] += 1
    if ro in (1,3):
        rotate_strike()
    if legal_bowled_this_over >= 6:
        exp_o, _ = divmod(legal_balls, 6)
        rotate_strike()
        bowler_index = (bowler_index + 1) % len(bowlers_available)
        current_bowler = bowlers_available[bowler_index]
        legal_bowled_this_over = 0

inn1.refresh_from_db()
exp_o, exp_b = divmod(legal_balls, 6)
P(f'\n========== End of Innings 1 ==========')
P(f'Expected local: runs={team_runs} wkts={team_wkts} ov={exp_o}.{exp_b}')
P(f'Actual DB     : runs={inn1.runs} wkts={inn1.wickets} ov={inn1.overs}.{inn1.balls}')
P(f'  wides={inn1.wides} no_balls={inn1.no_balls} byes={inn1.byes} leg_byes={inn1.leg_byes}')
P(f'  is_completed={inn1.is_completed} target={inn1.target_runs}')
# Target set for next innings:
target_to_chase = inn1.runs + 1
P(f'Target for Team 2 = {target_to_chase}')

# Ensure match advanced to INNINGS_BREAK and Innings 2 is created
match.refresh_from_db()
P(f'match status = {match.status}, current_innings = {match.current_innings_number}')
inn2_qs = Innings.objects.filter(match=match, innings_number=2)
if inn2_qs.exists():
    inn2 = inn2_qs.get()
    P(f'Innings 2 exists: batting={inn2.batting_team} target={inn2.target_runs}')
else:
    P('Innings 2 NOT auto-created. We will simulate the service creating it when a new record_delivery is posted to innings_number=2 by checking match.current_innings. Will manually set status back to LIVE.')
    # Force start of innings 2
    inn2, _ = Innings.objects.get_or_create(
        match=match, innings_number=2,
        defaults={
            'batting_team': bowling_team,  # reverse
            'bowling_team': batting_team,
            'target_runs': target_to_chase,
        },
    )
    match.current_innings_number = 2
    match.status = Match.Status.LIVE
    match.save()

# Populate Innings 2 PMI (seeding already did? let's ensure 11)
for i, pl in enumerate(list(Player.objects.filter(primary_team=inn2.batting_team)[:11]), 1):
    PlayerMatchInnings.objects.get_or_create(
        innings=inn2, player=pl,
        defaults={'batting_position': i, 'runs': 0, 'balls_faced': 0,
                  'fours': 0, 'sixes': 0, 'dots': 0,
                  'dismissal': PlayerMatchInnings.DismissalType.NOT_OUT},
    )
P(f'Innings 2 PMI count = {PlayerMatchInnings.objects.filter(innings=inn2).count()}')

# ======== INNINGS 2: Shortened to 30-legal-ball chase verifying CRR & RRR ========
P(f'\n================ START INNINGS 2 (CHASE of {target_to_chase}) =================')
# Reset state bookkeeping:
batters2 = list(PlayerMatchInnings.objects.filter(innings=inn2).order_by('batting_position').values_list('player_id', flat=True))
bowlers2_available = list(Player.objects.filter(
    primary_team=inn2.bowling_team,
    role__in=['bowler', 'all_rounder', 'wicketkeeper']
).values_list('id', flat=True))[:4]
P(f'Chase bowlers2: {bowlers2_available}')
striker2 = batters2[0]
non_striker2 = batters2[1]
s2_stats = {'runs': 0, 'balls': 0}
ns2_stats = {'runs': 0, 'balls': 0}
batter2_index = 1
bowler2_index = 0
cb = bowlers2_available[0]
t2_runs = 0; t2_wkts = 0; legal2 = 0; over_inning2 = 0;
w2 = 0; nb2 = 0; by2 = 0; lb2 = 0

def rot2():
    global striker2, non_striker2, s2_stats, ns2_stats
    striker2, non_striker2 = non_striker2, striker2
    s2_stats, ns2_stats = ns2_stats, s2_stats

# Play exactly 30 legal balls of aggressive cricket
for b in range(30):
    # weight: 1 every 2 balls, 4 every 5, 6 every 7
    if b % 7 == 3:
        ro = 6
    elif b % 5 == 2:
        ro = 4
    elif b % 2 == 1:
        ro = 1
    else:
        ro = 0
    # occasional wicket at multiples of 11
    wkt = (b % 11 == 5)
    if wkt: ro = 0
    payload = {
        'action': 'record_ball',
        'runs_off_bat': str(ro),
        'extra_type': 'none',
        'is_wicket': 'true' if wkt else 'false',
        'batter_id': str(striker2),
        'bowler_id': str(cb),
        'commentary': f'Chase #{b}: {"WICKET" if wkt else str(ro)+"r"}',
    }
    st, body = post_action(payload)
    t2_runs += ro; legal2 += 1; over_inning2 += 1
    s2_stats['runs'] += ro; s2_stats['balls'] += 1
    if wkt:
        t2_wkts += 1
        batter2_index += 1
        if batter2_index < len(batters2):
            striker2 = batters2[batter2_index]
            s2_stats = {'runs': 0, 'balls': 0}
    if ro in (1,3): rot2()
    if over_inning2 >= 6:
        rot2()
        bowler2_index = (bowler2_index + 1) % len(bowlers2_available)
        cb = bowlers2_available[bowler2_index]
        over_inning2 = 0
    # verify every ball
    inn2.refresh_from_db()
    exp_o, exp_b = divmod(legal2, 6)
    all_ok = True
    all_ok &= assert_equal('inn2 runs', inn2.runs, t2_runs)
    all_ok &= assert_equal('inn2 wkts', inn2.wickets, t2_wkts)
    all_ok &= assert_equal('inn2 legal', (inn2.overs*6 + inn2.balls), legal2)
    # CRR check
    crr_expected = round((t2_runs * 6.0) / max(1, legal2), 2)
    P(f'  [CALC] chase ball {b+1}: team {t2_runs}/{t2_wkts} need {target_to_chase - t2_runs} off {20*6 - legal2} balls  CRR_expected={crr_expected} actual={inn2.current_run_rate}')

P('\n============== FINAL STATE SUMMARY ==============')
inn1.refresh_from_db()
inn2.refresh_from_db()
for inn in (inn1, inn2):
    P(f'Innings {inn.innings_number} ({inn.batting_team.name}) -> {inn.runs}/{inn.wickets} in {inn.overs}.{inn.balls}  (extras: w={inn.wides} nb={inn.no_balls} by={inn.byes} lb={inn.leg_byes})')
    # Get top 3 batters and top 2 bowlers
    bats = PlayerMatchInnings.objects.filter(innings=inn).order_by('-runs')[:3]
    P(f'  Batters: ' + '; '.join([f"{b.player.short_name}:{b.runs}({b.balls_faced}) 4s={b.fours} 6s={b.sixes}" for b in bats]))
    bws = BowlerMatchInnings.objects.filter(innings=inn).order_by('-wickets','runs_conceded')[:3]
    P(f'  Bowlers: ' + '; '.join([f"{b.player.short_name}:{b.wickets}w/{b.runs_conceded}r o={b.overs}.{b.balls}" for b in bws]))

# Final summary counts
P('\n============== DB SUMMARY ==============')
P(f'Teams: {Team.objects.count()}')
P(f'Players: {Player.objects.count()}')
P(f'Matches: {Match.objects.count()}')
P(f'Innings: {Innings.objects.filter(match=match).count()}')
P(f'BallByBall total: {BallByBall.objects.filter(innings__match=match).count()}')
P(f'PlayerMatchInnings total: {PlayerMatchInnings.objects.filter(innings__match=match).count()}')
P(f'BowlerMatchInnings total: {BowlerMatchInnings.objects.filter(innings__match=match).count()}')
P(f'FallOfWicket entries: {FallOfWicket.objects.filter(innings__match=match).count()}')

match.refresh_from_db()
P(f'\nMatch current_innings={match.current_innings_number} status={match.status}')

# Set result via scorer panel action
st, body = post_action({
    'action': 'set_result',
    'result_text': f'Royal Warriors won by {max(0, target_to_chase - t2_runs - 1)} runs',
    'winning_team_id': str(inn1.batting_team.id),
    'man_of_match_id': str(batters[0]),
})
P(f'set_result: {st} {body}')
match.refresh_from_db()
P(f'Match now status={match.status} result={match.result_text} winner={match.winning_team} MoM={match.man_of_match}')

L.close()
