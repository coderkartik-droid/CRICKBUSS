import datetime
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crickbuss.settings')
django.setup()

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


def clear_demo_data():
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
    print('[CLEAR] Demo data cleared successfully.')


def ensure_users():
    admin, _ = User.objects.get_or_create(
        email='admin@crickscore.local',
        defaults={
            'username': 'admin',
            'first_name': 'Chief',
            'last_name': 'Admin',
            'role': CustomUser.Role.ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if not admin.check_password('admin1234'):
        admin.set_password('admin1234')
        admin.save()

    scorer, _ = User.objects.get_or_create(
        email='scorer@crickscore.local',
        defaults={
            'username': 'official_scorer',
            'first_name': 'Match',
            'last_name': 'Scorer',
            'role': 'scorer',
            'is_staff': False,
        }
    )
    if not scorer.check_password('scorer1234'):
        scorer.set_password('scorer1234')
        scorer.save()
    print('[USERS] Admin + Scorer ready.')
    return admin, scorer


RW_PLAYERS = [
    ('Arjun Mehta', 'The Wall', Player.Role.BATTER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_OFF_SPIN, 7, 1992, 5, 14, 'Mumbai, India', True),
    ('Kabir Rao', 'Killer Kabir', Player.Role.BATTER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_MEDIUM, 45, 1995, 9, 21, 'Delhi, India', False),
    ('Siddharth Verma', 'Sixer Sid', Player.Role.BATTER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.LEFT_ORTHODOX, 3, 1993, 12, 2, 'Chandigarh, India', False),
    ('Raghav Kapoor', 'Raghav The Rock', Player.Role.WICKET_KEEPER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.NONE, 11, 1994, 2, 28, 'Jaipur, India', True),
    ('Ishaan Shah', 'Stylish Ishaan', Player.Role.BATTER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.RIGHT_LEG_SPIN, 22, 1997, 7, 30, 'Pune, India', False),
    ('Yash Thakur', 'Yash The Finisher', Player.Role.ALL_ROUNDER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_MEDIUM, 8, 1996, 11, 11, 'Nagpur, India', False),
    ('Manav Singh', 'Magic Manav', Player.Role.ALL_ROUNDER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_OFF_SPIN, 17, 1991, 3, 17, 'Surat, India', False),
    ('Dev Joshi', 'Deadly Dev', Player.Role.BOWLER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_FAST, 99, 1998, 6, 6, 'Baroda, India', False),
    ('Aarav Patel', 'Yorker King', Player.Role.BOWLER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_FAST, 10, 1994, 8, 20, 'Ahmedabad, India', True),
    ('Veer Malhotra', 'Spin Veer', Player.Role.BOWLER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.LEFT_ORTHODOX, 27, 1993, 1, 23, 'Kanpur, India', False),
    ('Rohan Iyer', 'Rocket Rohan', Player.Role.BOWLER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_FAST, 78, 1999, 4, 1, 'Indore, India', False),
]

TK_PLAYERS = [
    ('Vikram Shetty', 'Viru', Player.Role.BATTER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_OFF_SPIN, 9, 1990, 9, 18, 'Chennai, India', True),
    ('Prateek Nair', 'Power Play Prateek', Player.Role.BATTER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.LEFT_MEDIUM, 18, 1995, 11, 12, 'Kochi, India', False),
    ('Anubhav Gupta', 'Annie G', Player.Role.BATTER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_LEG_SPIN, 31, 1994, 4, 15, 'Lucknow, India', False),
    ('Karthik Iyengar', 'Dynamo DK', Player.Role.WICKET_KEEPER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.NONE, 6, 1992, 8, 8, 'Bangalore, India', True),
    ('Sameer Khan', 'Sultan Sameer', Player.Role.BATTER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.LEFT_CHINAMAN, 24, 1996, 10, 24, 'Hyderabad, India', False),
    ('Nikhil Reddy', 'The Finisher', Player.Role.ALL_ROUNDER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_MEDIUM, 44, 1991, 12, 5, 'Vizag, India', False),
    ('Harsh Vardhan', 'Hurricane Harsh', Player.Role.ALL_ROUNDER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.LEFT_MEDIUM, 12, 1997, 5, 19, 'Patna, India', False),
    ('Ritesh Pandey', 'Pacy Pandey', Player.Role.BOWLER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_FAST, 77, 1993, 3, 26, 'Bhopal, India', False),
    ('Arvind Kumar', 'Thunder AK', Player.Role.BOWLER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_FAST, 55, 1995, 6, 16, 'Raipur, India', True),
    ('Balaji Rao', 'Spin King Bala', Player.Role.BOWLER, Player.BattingStyle.RIGHT_HAND, Player.BowlingStyle.RIGHT_LEG_SPIN, 88, 1990, 9, 3, 'Coimbatore, India', False),
    ('Chirag Desai', 'CD Swing', Player.Role.BOWLER, Player.BattingStyle.LEFT_HAND, Player.BowlingStyle.LEFT_MEDIUM, 36, 1998, 2, 10, 'Rajkot, India', False),
]


def create_team_players(team, spec_list):
    players = []
    for (name, nick, role, bat_style, bowl_style, jnum, yr, mo, dy, birth_place, feat) in spec_list:
        p = Player.objects.create(
            name=name, nickname=nick, role=role, batting_style=bat_style,
            bowling_style=bowl_style, jersey_number=jnum,
            born_date=datetime.date(yr, mo, dy), birth_place=birth_place,
            primary_team=team, is_featured=feat,
            biography=f'{nick} ({name}) is a professional cricketer representing {team.name}.',
        )
        p.teams.add(team)
        BattingStat.objects.create(
            player=p, format='T20I', matches=25, innings=24, runs=500 + jnum * 5,
            highest_score=str(50 + jnum),
            batting_average=Decimal('30.00') + Decimal(jnum) / Decimal('10'),
            balls_faced=400 + jnum * 8,
            strike_rate=Decimal('135.00'),
            hundreds=1 if jnum < 15 else 0,
            fifties=3 + (jnum % 5),
            fours=40 + jnum, sixes=12 + (jnum // 3),
        )
        if bowl_style != Player.BowlingStyle.NONE:
            BowlingStat.objects.create(
                player=p, format='T20I', matches=25, innings=22,
                overs=Decimal('50.0') + Decimal(jnum),
                maidens=2, runs_conceded=1100 + jnum * 6,
                wickets=12 + (jnum % 7),
                best_bowling='3/18',
                bowling_average=Decimal('26.50'),
                economy=Decimal('7.80'),
                strike_rate=Decimal('20.00'),
                four_wickets=0, five_wickets=0,
            )
        players.append(p)
    return players


def seed_everything():
    clear_demo_data()
    admin, scorer = ensure_users()

    # Venue + Ground
    venue, _ = Venue.objects.get_or_create(
        name='Royal Thunder Arena',
        city='Mumbai', state='Maharashtra', country='India',
        defaults={
            'capacity': 48000,
            'address': 'Marine Drive, Mumbai 400020',
            'description': 'State-of-the-art cricket stadium with hybrid pitch, large LED replay screens and premium hospitality boxes.',
            'pitch_type': 'True bounce batting friendly with slight grip for spinners under lights.',
            'avg_first_innings_score': 186,
        }
    )
    ground = Ground.objects.create(
        name='Main Oval', venue=venue, surface='Hybrid Bermuda grass',
        capacity=48000, is_active=True,
    )
    print('[VENUE]', venue.name, '+', ground.name)

    # Teams
    rw = Team.objects.create(
        name='Royal Warriors', short_name='RW',
        team_type=Team.TeamType.DOMESTIC, country='India',
        primary_color='#1e3a8a', secondary_color='#f59e0b',
        captain_name=RW_PLAYERS[0][0], coach_name='Rajesh Khanna',
        home_venue=f'{venue.name}, {venue.city}',
        established_year=2012,
        history='Royal Warriors was founded in 2012 and has consistently reached the knockout stages of domestic T20 leagues.',
        records='Highest successful chase: 231/4 vs Thunder Kings in 2024.',
        total_matches=142, total_wins=81, total_losses=56,
        total_ties_draws=5, trophies_count=2,
        is_featured=True, is_active=True,
    )
    tk = Team.objects.create(
        name='Thunder Kings', short_name='TK',
        team_type=Team.TeamType.DOMESTIC, country='India',
        primary_color='#7c2d12', secondary_color='#eab308',
        captain_name=TK_PLAYERS[0][0], coach_name='Srinivasan Iyer',
        home_venue=f'{venue.name}, {venue.city}',
        established_year=2013,
        history='Thunder Kings is a power-packed batting side renowned for death-over finishing and aggressive fast-bowling.',
        records='Highest team total: 258/5 (20 overs) in 2023.',
        total_matches=138, total_wins=75, total_losses=59,
        total_ties_draws=4, trophies_count=1,
        is_featured=True, is_active=True,
    )
    print('[TEAMS]', rw.name, 'vs', tk.name)

    # Players
    rw_players = create_team_players(rw, RW_PLAYERS)
    tk_players = create_team_players(tk, TK_PLAYERS)
    rw_captain, rw_vice = rw_players[0], rw_players[3]
    tk_captain, tk_vice = tk_players[0], tk_players[3]
    rw_wk = rw_players[3]  # Raghav Kapoor - WICKET_KEEPER
    tk_wk = tk_players[3]  # Karthik Iyengar - WICKET_KEEPER
    print('[PLAYERS]', len(rw_players), '+', len(tk_players), 'rostered')

    # Series
    series = Series.objects.create(
        name='Thunder Warrior Cup 2026',
        short_name='TWC 2026',
        category=Series.Category.DOMESTIC,
        cricket_format=Series.Format.T20,
        host_country='India',
        start_date=timezone.now().date() - datetime.timedelta(days=2),
        end_date=timezone.now().date() + datetime.timedelta(days=10),
        total_matches=5,
        is_featured=True, is_active=True,
    )
    series.participating_teams.add(rw, tk)
    PointsTableEntry.objects.create(series=series, team=rw, matches_played=1, won=1, lost=0, net_run_rate=Decimal('+1.240'), points=2, recent_form='W', position=1)
    PointsTableEntry.objects.create(series=series, team=tk, matches_played=1, won=0, lost=1, net_run_rate=Decimal('-1.240'), points=0, recent_form='L', position=2)
    print('[SERIES]', series.name)

    # Sponsor + Officials
    Sponsor.objects.create(name='ThunderBolt Energy Drink', website='https://example.com/bolt', is_active=True)
    Official.objects.create(name='Anil Chaudhary', role='On-field Umpire')
    Official.objects.create(name='Sanjay Hazare', role='On-field Umpire')
    Official.objects.create(name='Nitin Pandit', role='TV Umpire')
    Official.objects.create(name='Devendra Sharma', role='Match Referee')
    print('[ADMIN] Sponsors + Officials set.')

    # Live Match - Royal Warriors vs Thunder Kings, T20
    match = Match.objects.create(
        title='Royal Warriors vs Thunder Kings - Match 2',
        match_number='Match 2 - T20',
        match_type=Match.MatchType.T20,
        series=series,
        team1=rw, team2=tk,
        venue=venue, ground=ground,
        overs_limit=20,
        ball_type='Leather - Kookaburra T20',
        pitch_type='True bounce, slight spin towards end of innings',
        status=Match.Status.LIVE,
        current_innings_number=1,
        toss_winner=rw,
        toss_decision=Match.TossDecision.BAT,
        umpire_one='Anil Chaudhary', umpire_two='Sanjay Hazare',
        tv_umpire='Nitin Pandit', match_referee='Devendra Sharma',
        scorer='Official Scorer',
        pitch_report='Fresh strip with consistent bounce. Fast bowlers will enjoy early movement. Second innings under lights is a par-score chase.',
        weather_report='28°C Partly Cloudy, Wind 12 km/h from West, Humidity 55%',
        start_datetime=timezone.now() - datetime.timedelta(minutes=30),
        end_datetime=timezone.now() + datetime.timedelta(hours=3),
        is_featured=True,
        team1_captain=rw_captain, team1_vice_captain=rw_vice,
        team2_captain=tk_captain, team2_vice_captain=tk_vice,
    )
    match.team1_playing_xi.add(*rw_players)
    match.team2_playing_xi.add(*tk_players)
    match.assigned_scorers.add(scorer)
    print('[MATCH]', match.title, '[LIVE, T20, 20 overs]')

    # Innings 1: Royal Warriors batting (setup empty, ready to be scored)
    inn1 = Innings.objects.create(
        match=match, innings_number=1,
        batting_team=rw, bowling_team=tk,
        overs=0, balls=0, runs=0, wickets=0,
        wides=0, no_balls=0, byes=0, leg_byes=0,
        is_completed=False, is_declared=False,
        powerplay_overs=6,
    )
    # Openers
    PlayerMatchInnings.objects.create(innings=inn1, player=rw_players[0], batting_position=1, dismissal='not_out', dismissal_text='not out', runs=0, balls_faced=0, fours=0, sixes=0, dots=0)
    PlayerMatchInnings.objects.create(innings=inn1, player=rw_players[1], batting_position=2, dismissal='not_out', dismissal_text='not out', runs=0, balls_faced=0, fours=0, sixes=0, dots=0)
    # Rest of batting lineup
    for idx, p in enumerate(rw_players[2:], start=3):
        PlayerMatchInnings.objects.create(innings=inn1, player=p, batting_position=idx, dismissal='not_out', dismissal_text='not out', runs=0, balls_faced=0, fours=0, sixes=0, dots=0)
    # Starting bowlers (two seamers + two spinners)
    BowlerMatchInnings.objects.create(innings=inn1, player=tk_players[7], overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    BowlerMatchInnings.objects.create(innings=inn1, player=tk_players[8], overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    BowlerMatchInnings.objects.create(innings=inn1, player=tk_players[9], overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    BowlerMatchInnings.objects.create(innings=inn1, player=tk_players[10], overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    # Opening partnership placeholder
    Partnership.objects.create(innings=inn1, wicket_number=0, batter1=rw_players[0], batter2=rw_players[1], runs=0, balls=0)
    print('[INNINGS 1] Ready - RW openers at crease.')

    # Innings 2: Thunder Kings batting (not started yet)
    inn2 = Innings.objects.create(
        match=match, innings_number=2,
        batting_team=tk, bowling_team=rw,
        overs=0, balls=0, runs=0, wickets=0,
        wides=0, no_balls=0, byes=0, leg_byes=0,
        is_completed=False, is_declared=False,
        target_runs=None,
        powerplay_overs=6,
    )
    for idx, p in enumerate(tk_players, start=1):
        PlayerMatchInnings.objects.create(innings=inn2, player=p, batting_position=idx, dismissal='not_out', dismissal_text='not out', runs=0, balls_faced=0, fours=0, sixes=0, dots=0)
    for bp in [rw_players[7], rw_players[8], rw_players[9], rw_players[10]]:
        BowlerMatchInnings.objects.create(innings=inn2, player=bp, overs=0, balls=0, maidens=0, runs_conceded=0, wickets=0, dots=0)
    print('[INNINGS 2] Setup complete.')

    # Lightweight supporting content so other pages still render nicely
    cat_match, _ = NewsCategory.objects.get_or_create(name='Match Coverage')
    NewsArticle.objects.create(
        title='Royal Warriors Win Toss & Elect to Bat First',
        category=cat_match, author=admin,
        excerpt='After a brief rain delay, Royal Warriors captain won the toss and chose to set a target under lights.',
        content='Under clear skies after a 15-minute rain interruption, skipper Arjun Mehta confidently opted to set a total.',
        is_featured=True, is_breaking=False, is_trending=True,
        views_count=58, likes_count=4, is_published=True,
    )
    vcat, _ = VideoCategory.objects.get_or_create(name='T20 Highlights')
    CricketVideo.objects.create(
        title='TWC 2026: Match 1 - Royal Warriors vs Thunder Kings Highlights',
        category=vcat,
        description='Relive the final over thriller from Match 1 of the Thunder Warrior Cup 2026.',
        video_url='https://www.youtube.com/embed/dQw4w9WgXcQ',
        duration='08:20', views_count=1203, likes_count=72,
        is_featured=True, is_active=True,
    )
    alb, _ = PhotoAlbum.objects.get_or_create(
        title='TWC 2026 - Match Day',
        defaults={'category': PhotoAlbum.AlbumCategory.MATCH,
                  'description': 'Highlights from the TWC 2026 tournament matches.',
                  'is_featured': True, 'is_active': True}
    )
    PhotoItem.objects.create(album=alb, order=1, caption='Captains toss at Royal Thunder Arena', photo_credit='CrickScore Live', image='photos/gallery/toss.jpg')

    # A couple of ranking entries so rankings page loads content
    RankingEntry.objects.create(rank=1, gender=RankingEntry.Gender.MEN, cricket_format='T20I', category='teams',
                                name='Royal Warriors', country='India', rating=282, points=9840, previous_rank=1)
    RankingEntry.objects.create(rank=2, gender=RankingEntry.Gender.MEN, cricket_format='T20I', category='teams',
                                name='Thunder Kings', country='India', rating=274, points=9620, previous_rank=2)
    RankingEntry.objects.create(rank=1, gender=RankingEntry.Gender.MEN, cricket_format='T20I', category='batters',
                                name=rw_captain.name, country='India', rating=852, points=2556, previous_rank=1)

    print('\n========= SEEDING COMPLETE =========')
    print('Match slug:', match.slug)
    print('Scorer Panel URL: /matches/{}/scorer/'.format(match.slug))
    print('Login -> admin@crickscore.local / admin1234')
    print('Scorer -> scorer@crickscore.local / scorer1234')
    return match


if __name__ == '__main__':
    m = seed_everything()
