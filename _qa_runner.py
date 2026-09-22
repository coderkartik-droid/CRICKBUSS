import os, sys, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')

import django
django.setup()

log_file = os.path.join(BASE, '_qa_seed.log')
LOG = open(log_file, 'w', encoding='utf-8')
def log(s):
    LOG.write(str(s) + '\n')
    LOG.flush()
    print(s)

# _qa_seed.py script is imported, __main__ won't auto-fire, so run its logic inline
import datetime
from pathlib import Path
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from apps.dashboard.models import SavedMatch
from apps.matches.models import (
    BallByBall, BowlerMatchInnings, FallOfWicket, Ground,
    Innings, Match, Official, Partnership, PlayerMatchInnings,
    Sponsor, Tournament, Venue,
)
from apps.news.models import NewsArticle, NewsCategory
from apps.photos.models import PhotoAlbum, PhotoItem
from apps.players.models import BattingStat, BowlingStat, Player
from apps.rankings.models import RankingEntry
from apps.series.models import PointsTableEntry, Series
from apps.teams.models import Team
from apps.videos.models import CricketVideo, VideoCategory
from apps.accounts.models import CustomUser

User = get_user_model()

try:
    with transaction.atomic():
        BallByBall.objects.all().delete()
        FallOfWicket.objects.all().delete()
        Partnership.objects.all().delete()
        BowlerMatchInnings.objects.all().delete()
        PlayerMatchInnings.objects.all().delete()
        Innings.objects.all().delete()
        SavedMatch.objects.all().delete()
        Match.objects.all().delete()
        PointsTableEntry.objects.all().delete()
        RankingEntry.objects.all().delete()
        Series.objects.all().delete()
        BattingStat.objects.all().delete()
        BowlingStat.objects.all().delete()
        Player.objects.all().delete()
        Team.objects.all().delete()
        PhotoItem.objects.all().delete()
        PhotoAlbum.objects.all().delete()
        VideoCategory.objects.all().delete()
        CricketVideo.objects.all().delete()
        NewsArticle.objects.all().delete()
        NewsCategory.objects.all().delete()
        Ground.objects.all().delete()
        Venue.objects.all().delete()
        Official.objects.all().delete()
        Sponsor.objects.all().delete()
        Tournament.objects.all().delete()
    log('[CLEAR] OK')

    admin, _ = User.objects.get_or_create(email='admin@crickscore.local', defaults={
        'username': 'admin', 'first_name': 'Chief', 'last_name': 'Admin',
        'role': CustomUser.Role.ADMIN, 'is_staff': True, 'is_superuser': True,
    })
    if not admin.check_password('admin1234'):
        admin.set_password('admin1234')
        admin.save()

    scorer, _ = User.objects.get_or_create(email='scorer@crickscore.local', defaults={
        'username': 'official_scorer', 'first_name': 'Match', 'last_name': 'Scorer',
        'role': 'scorer', 'is_staff': False,
    })
    if not scorer.check_password('scorer1234'):
        scorer.set_password('scorer1234')
        scorer.save()
    log('[USERS] OK: admin / scorer')

    RW = [
        ('Arjun Mehta','The Wall',Player.Role.BATTER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_OFF_SPIN,7,1992,5,14,'Mumbai, India',True),
        ('Kabir Rao','Killer Kabir',Player.Role.BATTER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_MEDIUM,45,1995,9,21,'Delhi, India',False),
        ('Siddharth Verma','Sixer Sid',Player.Role.BATTER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.LEFT_ORTHODOX,3,1993,12,2,'Chandigarh, India',False),
        ('Raghav Kapoor','Raghav The Rock',Player.Role.WICKET_KEEPER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.NONE,11,1994,2,28,'Jaipur, India',True),
        ('Ishaan Shah','Stylish Ishaan',Player.Role.BATTER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.RIGHT_LEG_SPIN,22,1997,7,30,'Pune, India',False),
        ('Yash Thakur','Yash The Finisher',Player.Role.ALL_ROUNDER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_MEDIUM,8,1996,11,11,'Nagpur, India',False),
        ('Manav Singh','Magic Manav',Player.Role.ALL_ROUNDER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_OFF_SPIN,17,1991,3,17,'Surat, India',False),
        ('Dev Joshi','Deadly Dev',Player.Role.BOWLER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_FAST,99,1998,6,6,'Baroda, India',False),
        ('Aarav Patel','Yorker King',Player.Role.BOWLER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_FAST,10,1994,8,20,'Ahmedabad, India',True),
        ('Veer Malhotra','Spin Veer',Player.Role.BOWLER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.LEFT_ORTHODOX,27,1993,1,23,'Kanpur, India',False),
        ('Rohan Iyer','Rocket Rohan',Player.Role.BOWLER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_FAST,78,1999,4,1,'Indore, India',False),
    ]
    TK = [
        ('Vikram Shetty','Viru',Player.Role.BATTER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_OFF_SPIN,9,1990,9,18,'Chennai, India',True),
        ('Prateek Nair','Power Play Prateek',Player.Role.BATTER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.LEFT_MEDIUM,18,1995,11,12,'Kochi, India',False),
        ('Anubhav Gupta','Annie G',Player.Role.BATTER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_LEG_SPIN,31,1994,4,15,'Lucknow, India',False),
        ('Karthik Iyengar','Dynamo DK',Player.Role.WICKET_KEEPER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.NONE,6,1992,8,8,'Bangalore, India',True),
        ('Sameer Khan','Sultan Sameer',Player.Role.BATTER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.LEFT_CHINAMAN,24,1996,10,24,'Hyderabad, India',False),
        ('Nikhil Reddy','The Finisher',Player.Role.ALL_ROUNDER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_MEDIUM,44,1991,12,5,'Vizag, India',False),
        ('Harsh Vardhan','Hurricane Harsh',Player.Role.ALL_ROUNDER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.LEFT_MEDIUM,12,1997,5,19,'Patna, India',False),
        ('Ritesh Pandey','Pacy Pandey',Player.Role.BOWLER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_FAST,77,1993,3,26,'Bhopal, India',False),
        ('Arvind Kumar','Thunder AK',Player.Role.BOWLER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_FAST,55,1995,6,16,'Raipur, India',True),
        ('Balaji Rao','Spin King Bala',Player.Role.BOWLER,Player.BattingStyle.RIGHT_HAND,Player.BowlingStyle.RIGHT_LEG_SPIN,88,1990,9,3,'Coimbatore, India',False),
        ('Chirag Desai','CD Swing',Player.Role.BOWLER,Player.BattingStyle.LEFT_HAND,Player.BowlingStyle.LEFT_MEDIUM,36,1998,2,10,'Rajkot, India',False),
    ]

    venue, _ = Venue.objects.get_or_create(name='Royal Thunder Arena', city='Mumbai', state='Maharashtra', country='India', defaults={
        'capacity': 48000, 'address': 'Marine Drive, Mumbai 400020',
        'description': 'State-of-the-art cricket stadium with hybrid pitch and premium hospitality.',
        'pitch_type': 'True bounce batting friendly with slight spin under lights.',
        'avg_first_innings_score': 186,
    })
    ground = Ground.objects.create(name='Main Oval', venue=venue, surface='Hybrid Bermuda grass', capacity=48000, is_active=True)
    log(f'[VENUE] {venue.name} + {ground.name}')

    rw = Team.objects.create(name='Royal Warriors', short_name='RW', team_type=Team.TeamType.DOMESTIC, country='India',
        primary_color='#1e3a8a', secondary_color='#f59e0b', captain_name=RW[0][0], coach_name='Rajesh Khanna',
        home_venue=f'{venue.name}, {venue.city}', established_year=2012,
        history='Founded 2012, consistent knockout performers in domestic T20.',
        records='Highest chase: 231/4 vs Thunder Kings 2024.',
        total_matches=142, total_wins=81, total_losses=56, total_ties_draws=5, trophies_count=2,
        is_featured=True, is_active=True)
    tk = Team.objects.create(name='Thunder Kings', short_name='TK', team_type=Team.TeamType.DOMESTIC, country='India',
        primary_color='#7c2d12', secondary_color='#eab308', captain_name=TK[0][0], coach_name='Srinivasan Iyer',
        home_venue=f'{venue.name}, {venue.city}', established_year=2013,
        history='Power-packed batting side known for death-over finishing.',
        records='Highest total: 258/5 (20 overs) in 2023.',
        total_matches=138, total_wins=75, total_losses=59, total_ties_draws=4, trophies_count=1,
        is_featured=True, is_active=True)
    log(f'[TEAMS] {rw.name} / {tk.name}')

    def mk_players(team, specs):
        out = []
        for (name, nick, role, bat, bowl, jnum, yr, mo, dy, bp, feat) in specs:
            p = Player.objects.create(name=name, nickname=nick, role=role, batting_style=bat, bowling_style=bowl,
                jersey_number=jnum, born_date=datetime.date(yr, mo, dy), birth_place=bp,
                primary_team=team, is_featured=feat,
                biography=f'{nick} ({name}) is a pro cricketer with {team.name}.')
            p.teams.add(team)
            BattingStat.objects.create(player=p, format='T20I', matches=25, innings=24, runs=500+jnum*5,
                highest_score=str(50+jnum), batting_average=Decimal('30.00')+Decimal(jnum)/Decimal('10'),
                balls_faced=400+jnum*8, strike_rate=Decimal('135.00'),
                hundreds=1 if jnum < 15 else 0, fifties=3+(jnum%5), fours=40+jnum, sixes=12+(jnum//3))
            if bowl != Player.BowlingStyle.NONE:
                BowlingStat.objects.create(player=p, format='T20I', matches=25, innings=22,
                    overs=Decimal('50.0')+Decimal(jnum), maidens=2, runs_conceded=1100+jnum*6,
                    wickets=12+(jnum%7), best_bowling='3/18', bowling_average=Decimal('26.50'),
                    economy=Decimal('7.80'), strike_rate=Decimal('20.00'))
            out.append(p)
        return out

    rw_p = mk_players(rw, RW)
    tk_p = mk_players(tk, TK)
    rw_cap, rw_vice, rw_wk = rw_p[0], rw_p[3], rw_p[3]
    tk_cap, tk_vice, tk_wk = tk_p[0], tk_p[3], tk_p[3]
    log(f'[PLAYERS] RW={len(rw_p)} TK={len(tk_p)}')

    series = Series.objects.create(name='Thunder Warrior Cup 2026', short_name='TWC 2026',
        category=Series.Category.DOMESTIC, cricket_format=Series.Format.T20, host_country='India',
        start_date=timezone.now().date()-datetime.timedelta(days=2),
        end_date=timezone.now().date()+datetime.timedelta(days=10),
        total_matches=5, is_featured=True, is_active=True)
    series.participating_teams.add(rw, tk)
    PointsTableEntry.objects.create(series=series, team=rw, matches_played=1, won=1, lost=0, net_run_rate=Decimal('+1.240'), points=2, recent_form='W', position=1)
    PointsTableEntry.objects.create(series=series, team=tk, matches_played=1, won=0, lost=1, net_run_rate=Decimal('-1.240'), points=0, recent_form='L', position=2)
    log(f'[SERIES] {series.name}')

    Sponsor.objects.create(name='ThunderBolt Energy Drink', website='https://example.com/bolt', is_active=True)
    for name, role in [('Anil Chaudhary','On-field Umpire'),('Sanjay Hazare','On-field Umpire'),('Nitin Pandit','TV Umpire'),('Devendra Sharma','Match Referee')]:
        Official.objects.create(name=name, role=role)

    match = Match.objects.create(
        title='Royal Warriors vs Thunder Kings - Match 2',
        match_number='Match 2 - T20', match_type=Match.MatchType.T20,
        series=series, team1=rw, team2=tk, venue=venue, ground=ground,
        overs_limit=20, ball_type='Leather - Kookaburra T20',
        pitch_type='True bounce, slight spin towards end of innings',
        status=Match.Status.LIVE, current_innings_number=1,
        toss_winner=rw, toss_decision=Match.TossDecision.BAT,
        umpire_one='Anil Chaudhary', umpire_two='Sanjay Hazare',
        tv_umpire='Nitin Pandit', match_referee='Devendra Sharma',
        scorer='Official Scorer',
        pitch_report='Fresh strip with consistent bounce. Fast bowlers get early movement.',
        weather_report='28°C Partly Cloudy, Wind 12km/h, Humidity 55%',
        start_datetime=timezone.now()-datetime.timedelta(minutes=30),
        end_datetime=timezone.now()+datetime.timedelta(hours=3),
        is_featured=True,
        team1_captain=rw_cap, team1_vice_captain=rw_vice,
        team2_captain=tk_cap, team2_vice_captain=tk_vice,
    )
    match.team1_playing_xi.add(*rw_p)
    match.team2_playing_xi.add(*tk_p)
    match.assigned_scorers.add(scorer)
    log(f'[MATCH] {match.title} slug={match.slug}')

    inn1 = Innings.objects.create(match=match, innings_number=1, batting_team=rw, bowling_team=tk,
        overs=0, balls=0, runs=0, wickets=0, wides=0, no_balls=0, byes=0, leg_byes=0,
        is_completed=False, powerplay_overs=6)
    for i, p in enumerate(rw_p, start=1):
        PlayerMatchInnings.objects.create(innings=inn1, player=p, batting_position=i,
            dismissal='not_out', dismissal_text='not out', runs=0, balls_faced=0, fours=0, sixes=0, dots=0)
    for bp in [tk_p[7], tk_p[8], tk_p[9], tk_p[10]]:
        BowlerMatchInnings.objects.create(innings=inn1, player=bp, overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    Partnership.objects.create(innings=inn1, wicket_number=0, batter1=rw_p[0], batter2=rw_p[1], runs=0, balls=0)
    log('[INN1] Ready - RW openers at crease')

    inn2 = Innings.objects.create(match=match, innings_number=2, batting_team=tk, bowling_team=rw,
        overs=0, balls=0, runs=0, wickets=0, wides=0, no_balls=0, byes=0, leg_byes=0,
        is_completed=False, target_runs=None, powerplay_overs=6)
    for i, p in enumerate(tk_p, start=1):
        PlayerMatchInnings.objects.create(innings=inn2, player=p, batting_position=i,
            dismissal='not_out', dismissal_text='not out', runs=0, balls_faced=0, fours=0, sixes=0, dots=0)
    for bp in [rw_p[7], rw_p[8], rw_p[9], rw_p[10]]:
        BowlerMatchInnings.objects.create(innings=inn2, player=bp, overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    log('[INN2] Setup - ready for TK chase')

    cat_match, _ = NewsCategory.objects.get_or_create(name='Match Coverage')
    NewsArticle.objects.create(title='Royal Warriors Win Toss & Elect to Bat First', category=cat_match, author=admin,
        excerpt='Royal Warriors captain won the toss and chose to set a target.',
        content='Under clear skies after a brief rain delay.', is_featured=True, is_trending=True,
        views_count=58, likes_count=4, is_published=True)
    vcat, _ = VideoCategory.objects.get_or_create(name='T20 Highlights')
    CricketVideo.objects.create(title='TWC 2026: Match 1 Highlights', category=vcat,
        description='Relive Match 1 final over thriller.',
        video_url='https://www.youtube.com/embed/dQw4w9WgXcQ', duration='08:20',
        views_count=1203, likes_count=72, is_featured=True, is_active=True)
    alb, _ = PhotoAlbum.objects.get_or_create(title='TWC 2026 - Match Day', defaults={
        'category': PhotoAlbum.AlbumCategory.MATCH, 'description': 'TWC 2026 moments.',
        'is_featured': True, 'is_active': True})
    PhotoItem.objects.create(album=alb, order=1, caption='Captains toss', photo_credit='CrickScore Live', image='photos/gallery/toss.jpg')

    RankingEntry.objects.create(rank=1, gender='men', cricket_format='T20I', category='teams',
        name='Royal Warriors', country='India', rating=282, points=9840, previous_rank=1)
    RankingEntry.objects.create(rank=2, gender='men', cricket_format='T20I', category='teams',
        name='Thunder Kings', country='India', rating=274, points=9620, previous_rank=2)
    RankingEntry.objects.create(rank=1, gender='men', cricket_format='T20I', category='batters',
        name=rw_cap.name, country='India', rating=852, points=2556, previous_rank=1)
    log('[CONTENT] News/Video/Photo/Ranking seeded')

    # Save slug for next stage
    with open(os.path.join(BASE, '_qa_slug.txt'), 'w') as f:
        f.write(match.slug)

    log('')
    log('===== SEEDING COMPLETE =====')
    log('MATCH SLUG: ' + match.slug)
    log('Scorer: /matches/' + match.slug + '/scorer/')
    log('Admin login: admin@crickscore.local / admin1234')

except Exception as e:
    log('EXCEPTION: ' + repr(e))
    traceback.print_exc(file=LOG)
    LOG.flush()
    LOG.close()
    sys.exit(1)

LOG.flush()
LOG.close()
