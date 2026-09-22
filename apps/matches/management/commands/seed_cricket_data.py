import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from apps.accounts.models import CustomUser
from apps.teams.models import Team
from apps.players.models import Player, BattingStat, BowlingStat
from apps.series.models import Series, PointsTableEntry
from apps.rankings.models import RankingEntry
from apps.news.models import NewsCategory, NewsArticle
from apps.videos.models import VideoCategory, CricketVideo
from apps.photos.models import PhotoAlbum, PhotoItem
from apps.matches.models import (
    Venue, Match, Innings, PlayerMatchInnings,
    BowlerMatchInnings, BallByBall, Partnership, FallOfWicket
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds complete sample data for CrickScore Live application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Beginning database seeding...'))

        # 1. Superuser & Standard Users
        admin_user, _ = CustomUser.objects.get_or_create(
            email='admin@crickscore.local',
            defaults={
                'username': 'admin',
                'first_name': 'Chief',
                'last_name': 'Editor',
                'role': CustomUser.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin1234')
        admin_user.save()

        editor_user, _ = CustomUser.objects.get_or_create(
            email='editor@crickscore.local',
            defaults={
                'username': 'editor_sam',
                'first_name': 'Samantha',
                'last_name': 'Ray',
                'role': CustomUser.Role.USER,
                'is_staff': False,
            }
        )
        editor_user.set_password('editor1234')
        editor_user.save()

        fan_user, _ = CustomUser.objects.get_or_create(
            email='fan@crickscore.local',
            defaults={
                'username': 'cricket_fan99',
                'first_name': 'Rohit',
                'last_name': 'Kumar',
                'role': CustomUser.Role.USER,
                'favorite_team': 'India',
            }
        )
        fan_user.set_password('fan12345')
        fan_user.save()
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Users (admin, editor, fan)'))

        # 2. Venues
        v_wankhede, _ = Venue.objects.get_or_create(
            name='Wankhede Stadium',
            city='Mumbai',
            country='India',
            defaults={
                'capacity': 33108,
                'pitch_type': 'Red soil pitch with true bounce and carry, batting paradise under lights',
                'avg_first_innings_score': 188
            }
        )
        v_eden, _ = Venue.objects.get_or_create(
            name='Eden Gardens',
            city='Kolkata',
            country='India',
            defaults={'capacity': 68000, 'pitch_type': 'Sporting wicket with turn later in day', 'avg_first_innings_score': 180}
        )
        v_mcg, _ = Venue.objects.get_or_create(
            name='Melbourne Cricket Ground (MCG)',
            city='Melbourne',
            country='Australia',
            defaults={'capacity': 100024, 'pitch_type': 'Drop-in pitch with good pace and bounce', 'avg_first_innings_score': 172}
        )
        v_lords, _ = Venue.objects.get_or_create(
            name="Lord's Cricket Ground",
            city='London',
            country='England',
            defaults={'capacity': 31100, 'pitch_type': 'Natural slope offering lateral seam movement', 'avg_first_innings_score': 165}
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Venues'))

        # 3. Teams
        india, _ = Team.objects.get_or_create(
            name='India',
            short_name='IND',
            defaults={
                'team_type': Team.TeamType.INTERNATIONAL,
                'country': 'India',
                'primary_color': '#0f766e',
                'secondary_color': '#f59e0b',
                'captain_name': 'Rohit Sharma',
                'coach_name': 'Gautam Gambhir',
                'home_venue': 'Wankhede Stadium, Mumbai',
                'total_matches': 602,
                'total_wins': 378,
                'total_losses': 195,
                'total_ties_draws': 29,
                'trophies_count': 6,
                'history': 'India joined Test cricket in 1932. They won the ODI World Cup in 1983 and 2011, and T20 World Cup in 2007 and 2024.',
                'records': 'Highest team total in T20I: 297/6 against Bangladesh (2024).',
                'is_featured': True
            }
        )

        australia, _ = Team.objects.get_or_create(
            name='Australia',
            short_name='AUS',
            defaults={
                'team_type': Team.TeamType.INTERNATIONAL,
                'country': 'Australia',
                'primary_color': '#eab308',
                'secondary_color': '#15803d',
                'captain_name': 'Pat Cummins',
                'coach_name': 'Andrew McDonald',
                'home_venue': 'MCG, Melbourne',
                'total_matches': 650,
                'total_wins': 415,
                'total_losses': 202,
                'total_ties_draws': 33,
                'trophies_count': 10,
                'history': 'Australia is the most successful nation in cricket history with 6 ODI World Cup titles.',
                'is_featured': True
            }
        )

        england, _ = Team.objects.get_or_create(
            name='England',
            short_name='ENG',
            defaults={
                'team_type': Team.TeamType.INTERNATIONAL,
                'country': 'England',
                'primary_color': '#1e3a8a',
                'captain_name': 'Jos Buttler',
                'coach_name': 'Brendon McCullum',
                'home_venue': "Lord's, London",
                'total_matches': 580,
                'total_wins': 310,
                'is_featured': True
            }
        )

        csk, _ = Team.objects.get_or_create(
            name='Chennai Super Kings',
            short_name='CSK',
            defaults={
                'team_type': Team.TeamType.IPL,
                'country': 'India',
                'primary_color': '#facc15',
                'captain_name': 'Ruturaj Gaikwad',
                'coach_name': 'Stephen Fleming',
                'home_venue': 'MA Chidambaram Stadium, Chennai',
                'trophies_count': 5,
                'is_featured': True
            }
        )

        mi, _ = Team.objects.get_or_create(
            name='Mumbai Indians',
            short_name='MI',
            defaults={
                'team_type': Team.TeamType.IPL,
                'country': 'India',
                'primary_color': '#2563eb',
                'captain_name': 'Hardik Pandya',
                'coach_name': 'Mahela Jayawardene',
                'home_venue': 'Wankhede Stadium, Mumbai',
                'trophies_count': 5,
                'is_featured': True
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Teams'))

        # 4. Players
        kohli, _ = Player.objects.get_or_create(
            name='Virat Kohli',
            defaults={
                'primary_team': india,
                'nickname': 'King Kohli',
                'role': Player.Role.BATTER,
                'batting_style': Player.BattingStyle.RIGHT_HAND,
                'jersey_number': 18,
                'born_date': datetime.date(1988, 11, 5),
                'birth_place': 'Delhi, India',
                'biography': 'Virat Kohli is an Indian international cricketer and regarded as one of the greatest batsmen in modern cricket history.',
                'achievements': 'Player of the Tournament in 2014 & 2016 T20 World Cups and 2023 ODI World Cup. Over 50 ODI centuries.',
                'records': 'Fastest to 8,000, 9,000, 10,000, 11,000, 12,000 and 13,000 runs in ODI cricket.',
                'is_featured': True
            }
        )
        kohli.teams.add(india)

        rohit, _ = Player.objects.get_or_create(
            name='Rohit Sharma',
            defaults={
                'primary_team': india,
                'nickname': 'Hitman',
                'role': Player.Role.BATTER,
                'batting_style': Player.BattingStyle.RIGHT_HAND,
                'jersey_number': 45,
                'born_date': datetime.date(1987, 4, 30),
                'biography': 'Captain of India and five-time IPL champion skipper.',
                'records': 'Highest individual score in ODI history: 264 vs Sri Lanka. Most centuries in a single World Cup (5 in 2019).',
                'is_featured': True
            }
        )
        rohit.teams.add(india, mi)

        bumrah, _ = Player.objects.get_or_create(
            name='Jasprit Bumrah',
            defaults={
                'primary_team': india,
                'nickname': 'Boom Boom',
                'role': Player.Role.BOWLER,
                'batting_style': Player.BattingStyle.RIGHT_HAND,
                'bowling_style': Player.BowlingStyle.RIGHT_FAST,
                'jersey_number': 93,
                'born_date': datetime.date(1993, 12, 6),
                'biography': 'Premier fast bowler known for his pinpoint yorkers and unorthodox action.',
                'is_featured': True
            }
        )
        bumrah.teams.add(india, mi)

        cummins, _ = Player.objects.get_or_create(
            name='Pat Cummins',
            defaults={
                'primary_team': australia,
                'nickname': 'Cummo',
                'role': Player.Role.ALL_ROUNDER,
                'batting_style': Player.BattingStyle.RIGHT_HAND,
                'bowling_style': Player.BowlingStyle.RIGHT_FAST,
                'jersey_number': 30,
                'born_date': datetime.date(1993, 5, 8),
                'is_featured': True
            }
        )
        cummins.teams.add(australia)

        head, _ = Player.objects.get_or_create(
            name='Travis Head',
            defaults={
                'primary_team': australia,
                'role': Player.Role.BATTER,
                'batting_style': Player.BattingStyle.LEFT_HAND,
                'jersey_number': 62,
                'is_featured': True
            }
        )
        head.teams.add(australia)

        # Player Batting Stats
        BattingStat.objects.get_or_create(
            player=kohli, format='ODI',
            defaults={
                'matches': 295, 'innings': 283, 'runs': 13906, 'highest_score': '183',
                'batting_average': Decimal('58.18'), 'balls_faced': 14850,
                'strike_rate': Decimal('93.64'), 'hundreds': 50, 'fifties': 72,
                'fours': 1302, 'sixes': 151
            }
        )
        BattingStat.objects.get_or_create(
            player=kohli, format='TEST',
            defaults={
                'matches': 113, 'innings': 191, 'runs': 8848, 'highest_score': '254*',
                'batting_average': Decimal('49.15'), 'strike_rate': Decimal('55.56'),
                'hundreds': 29, 'fifties': 30
            }
        )
        BattingStat.objects.get_or_create(
            player=rohit, format='ODI',
            defaults={
                'matches': 265, 'innings': 257, 'runs': 10866, 'highest_score': '264',
                'batting_average': Decimal('49.16'), 'strike_rate': Decimal('92.44'),
                'hundreds': 31, 'fifties': 57
            }
        )

        # Player Bowling Stats
        BowlingStat.objects.get_or_create(
            player=bumrah, format='ODI',
            defaults={
                'matches': 89, 'innings': 88, 'overs': Decimal('734.2'),
                'maidens': 60, 'runs_conceded': 3350, 'wickets': 149,
                'best_bowling': '6/19', 'bowling_average': Decimal('22.48'),
                'economy': Decimal('4.56')
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Players & Career Statistics'))

        # 5. Series & Tournaments
        series_tour, _ = Series.objects.get_or_create(
            name='Australia Tour of India 2026',
            short_name='AUS in IND',
            defaults={
                'category': Series.Category.INTERNATIONAL,
                'cricket_format': Series.Format.ODI,
                'host_country': 'India',
                'start_date': timezone.now().date() - datetime.timedelta(days=5),
                'end_date': timezone.now().date() + datetime.timedelta(days=15),
                'total_matches': 3,
                'is_featured': True,
                'is_active': True
            }
        )
        series_tour.participating_teams.add(india, australia)

        series_ipl, _ = Series.objects.get_or_create(
            name='Indian Premier League 2026',
            short_name='IPL 2026',
            defaults={
                'category': Series.Category.IPL,
                'cricket_format': Series.Format.T20,
                'host_country': 'India',
                'start_date': timezone.now().date() + datetime.timedelta(days=20),
                'end_date': timezone.now().date() + datetime.timedelta(days=75),
                'total_matches': 74,
                'is_featured': True,
                'is_active': True
            }
        )
        series_ipl.participating_teams.add(csk, mi)

        # Points Table for IPL
        PointsTableEntry.objects.get_or_create(
            series=series_ipl, team=csk,
            defaults={'matches_played': 4, 'won': 3, 'lost': 1, 'net_run_rate': Decimal('+0.845'), 'points': 6, 'recent_form': 'W,W,L,W', 'position': 1}
        )
        PointsTableEntry.objects.get_or_create(
            series=series_ipl, team=mi,
            defaults={'matches_played': 4, 'won': 2, 'lost': 2, 'net_run_rate': Decimal('+0.120'), 'points': 4, 'recent_form': 'L,W,W,L', 'position': 2}
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Series & Points Table'))

        # 6. Matches (1 LIVE, 1 COMPLETED, 1 UPCOMING)
        # LIVE MATCH
        live_match, _ = Match.objects.get_or_create(
            title='India vs Australia - 2nd ODI',
            defaults={
                'match_number': '2nd ODI',
                'match_type': Match.MatchType.ODI,
                'series': series_tour,
                'team1': india,
                'team2': australia,
                'venue': v_wankhede,
                'status': Match.Status.LIVE,
                'current_innings_number': 2,
                'toss_winner': australia,
                'toss_decision': Match.TossDecision.BAT,
                'start_datetime': timezone.now() - datetime.timedelta(hours=4),
                'is_featured': True,
                'pitch_report': 'True bounce under floodlights. High scoring chase expected.',
                'weather_report': '26°C Clear, Wind 10km/h'
            }
        )
        live_match.team1_playing_xi.add(rohit, kohli, bumrah)
        live_match.team2_playing_xi.add(head, cummins)

        # 1st Innings (Australia 284/9)
        inn1, _ = Innings.objects.get_or_create(
            match=live_match, innings_number=1,
            defaults={
                'batting_team': australia,
                'bowling_team': india,
                'runs': 284,
                'wickets': 9,
                'overs': 50,
                'balls': 0,
                'wides': 6,
                'no_balls': 2,
                'byes': 4,
                'leg_byes': 3,
                'is_completed': True
            }
        )
        PlayerMatchInnings.objects.get_or_create(
            innings=inn1, player=head,
            defaults={'batting_position': 1, 'dismissal': 'caught', 'dismissal_text': 'c Rohit b Bumrah', 'runs': 88, 'balls_faced': 74, 'fours': 9, 'sixes': 3}
        )
        BowlerMatchInnings.objects.get_or_create(
            innings=inn1, player=bumrah,
            defaults={'overs': 10, 'maidens': 1, 'runs_conceded': 44, 'wickets': 3}
        )

        # 2nd Innings (India 215/3 in 38.2 overs - Live chasing)
        inn2, _ = Innings.objects.get_or_create(
            match=live_match, innings_number=2,
            defaults={
                'batting_team': india,
                'bowling_team': australia,
                'runs': 215,
                'wickets': 3,
                'overs': 38,
                'balls': 2,
                'wides': 4,
                'no_balls': 1,
                'byes': 2,
                'leg_byes': 1,
                'is_completed': False
            }
        )
        PlayerMatchInnings.objects.get_or_create(
            innings=inn2, player=rohit,
            defaults={'batting_position': 1, 'dismissal': 'caught', 'dismissal_text': 'c Head b Cummins', 'runs': 65, 'balls_faced': 58, 'fours': 7, 'sixes': 2}
        )
        PlayerMatchInnings.objects.get_or_create(
            innings=inn2, player=kohli,
            defaults={'batting_position': 3, 'dismissal': 'not_out', 'dismissal_text': 'not out', 'runs': 84, 'balls_faced': 76, 'fours': 8, 'sixes': 1}
        )
        BowlerMatchInnings.objects.get_or_create(
            innings=inn2, player=cummins,
            defaults={'overs': 8, 'maidens': 0, 'runs_conceded': 46, 'wickets': 2}
        )

        # Ball by ball commentary items for live chase
        BallByBall.objects.get_or_create(
            innings=inn2, over_number=38, ball_number=1,
            defaults={
                'batter': kohli, 'bowler': cummins, 'runs_off_bat': 4,
                'is_four': True, 'commentary': 'FOUR! Elegant cover drive by Virat Kohli! Leans into the half-volley and sends it racing to the fence.'
            }
        )
        BallByBall.objects.get_or_create(
            innings=inn2, over_number=38, ball_number=2,
            defaults={
                'batter': kohli, 'bowler': cummins, 'runs_off_bat': 1,
                'commentary': 'Punched off the backfoot towards deep point for a single. Rotates the strike effortlessly.'
            }
        )

        # COMPLETED MATCH
        completed_match, _ = Match.objects.get_or_create(
            title='India vs Australia - 1st ODI',
            defaults={
                'match_number': '1st ODI',
                'match_type': Match.MatchType.ODI,
                'series': series_tour,
                'team1': india,
                'team2': australia,
                'venue': v_eden,
                'status': Match.Status.COMPLETED,
                'result_text': 'India won by 4 wickets',
                'winning_team': india,
                'man_of_match': kohli,
                'start_datetime': timezone.now() - datetime.timedelta(days=3),
                'is_featured': True
            }
        )

        # UPCOMING MATCH
        Match.objects.get_or_create(
            title='Chennai Super Kings vs Mumbai Indians - IPL 2026 Match 1',
            defaults={
                'match_number': 'Match 1',
                'match_type': Match.MatchType.T20,
                'series': series_ipl,
                'team1': csk,
                'team2': mi,
                'venue': v_wankhede,
                'status': Match.Status.UPCOMING,
                'start_datetime': timezone.now() + datetime.timedelta(days=21),
                'is_featured': True
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Matches, Innings, Scorecards & Ball by Ball'))

        # 7. ICC Rankings
        RankingEntry.objects.get_or_create(
            rank=1, gender=RankingEntry.Gender.MEN, cricket_format='TEST', category='batters',
            defaults={'name': 'Kane Williamson', 'country': 'New Zealand', 'rating': 883, 'points': 2650}
        )
        RankingEntry.objects.get_or_create(
            rank=2, gender=RankingEntry.Gender.MEN, cricket_format='TEST', category='batters',
            defaults={'name': 'Joe Root', 'country': 'England', 'rating': 859, 'previous_rank': 3, 'points': 2570}
        )
        RankingEntry.objects.get_or_create(
            rank=3, gender=RankingEntry.Gender.MEN, cricket_format='TEST', category='batters',
            defaults={'name': 'Steve Smith', 'country': 'Australia', 'rating': 825, 'previous_rank': 2, 'points': 2470}
        )
        RankingEntry.objects.get_or_create(
            rank=4, gender=RankingEntry.Gender.MEN, cricket_format='TEST', category='batters',
            defaults={'name': 'Virat Kohli', 'country': 'India', 'rating': 805, 'previous_rank': 4, 'points': 2410}
        )
        RankingEntry.objects.get_or_create(
            rank=1, gender=RankingEntry.Gender.MEN, cricket_format='TEST', category='teams',
            defaults={'name': 'India', 'country': 'India', 'rating': 120, 'points': 3450}
        )
        RankingEntry.objects.get_or_create(
            rank=2, gender=RankingEntry.Gender.MEN, cricket_format='TEST', category='teams',
            defaults={'name': 'Australia', 'country': 'Australia', 'rating': 118, 'points': 3380}
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded ICC Rankings'))

        # 8. News Articles
        cat_tour, _ = NewsCategory.objects.get_or_create(name='Tournaments', defaults={'description': 'Series and major event coverage'})
        cat_analysis, _ = NewsCategory.objects.get_or_create(name='Match Analysis', defaults={'description': 'Tactical breakdowns and player ratings'})
        cat_interviews, _ = NewsCategory.objects.get_or_create(name='Interviews', defaults={'description': 'Exclusive conversations with players and coaches'})

        NewsArticle.objects.get_or_create(
            title='Kohli Guides India In Thrilling Chase Under Wankhede Floodlights',
            defaults={
                'category': cat_tour,
                'author': editor_user,
                'excerpt': 'A composed half-century from Virat Kohli puts India in commanding position in the second ODI against Australia.',
                'content': """Virat Kohli produced yet another masterclass in run-chasing as India tightened their grip on the 2nd ODI against Australia at the iconic Wankhede Stadium.

Chasing Australia's imposing total of 284, India began briskly with captain Rohit Sharma striking seven boundaries before Travis Head took a tumbling catch at mid-off.

Kohli then anchored the middle overs with trademark wrist-work and quick running between the wickets, bringing up his 73rd fifty-plus score in ODI cricket. With support from the middle order, India look firmly on course to seal the bilateral series.""",
                'is_featured': True,
                'is_breaking': True,
                'is_trending': True,
                'views_count': 1420,
                'likes_count': 94,
                'is_published': True
            }
        )

        NewsArticle.objects.get_or_create(
            title='Tactical Breakdown: How Bumrah Deceived Australia In Death Overs',
            defaults={
                'category': cat_analysis,
                'author': editor_user,
                'excerpt': 'Analyzing Jasprit Bumrah’s lethal change of pace and reverse-swinging yorkers that choked Australia’s late surge.',
                'content': """Jasprit Bumrah once again demonstrated why he is the gold standard in modern fast bowling. Delivering 10 overs for just 44 runs on a flat Wankhede surface, his subtle off-cutters and searing yorkers pegged Australia back in the final ten overs.""",
                'is_trending': True,
                'views_count': 820,
                'likes_count': 56,
                'is_published': True
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded News Articles'))

        # 9. Videos
        vcat_hi, _ = VideoCategory.objects.get_or_create(name='Match Highlights')
        vcat_int, _ = VideoCategory.objects.get_or_create(name='Press Conferences')

        CricketVideo.objects.get_or_create(
            title='India vs Australia 2nd ODI: Virat Kohli 84 Runs Special Highlights',
            defaults={
                'category': vcat_hi,
                'description': 'Watch every boundary and glorious stroke from Virat Kohli’s fluent innings against the Australian pace attack in Mumbai.',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration': '06:45',
                'views_count': 3240,
                'likes_count': 210,
                'is_featured': True,
                'is_active': True
            }
        )

        CricketVideo.objects.get_or_create(
            title='Post-Match Press Conference: Rohit Sharma on Pitch and Strategy',
            defaults={
                'category': vcat_int,
                'description': 'Indian skipper Rohit Sharma discusses the team combinations and preparation ahead of the mega season.',
                'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'duration': '12:10',
                'views_count': 1120,
                'is_active': True
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Videos'))

        # 10. Photo Albums
        alb1, _ = PhotoAlbum.objects.get_or_create(
            title='Action Moments: IND vs AUS 2nd ODI at Wankhede',
            defaults={
                'category': PhotoAlbum.AlbumCategory.MATCH,
                'description': 'Spectacular photographic capture of boundaries, celebrations, and crowd energy under lights.',
                'is_featured': True,
                'is_active': True
            }
        )
        PhotoItem.objects.get_or_create(
            album=alb1, order=1,
            defaults={
                'caption': 'Virat Kohli celebrates his half century',
                'photo_credit': 'ICC Media',
                'image': 'photos/gallery/sample1.jpg'
            }
        )
        PhotoItem.objects.get_or_create(
            album=alb1, order=2,
            defaults={
                'caption': 'Jasprit Bumrah castles the stumps with a trademark yorker',
                'photo_credit': 'BCCI Photo',
                'image': 'photos/gallery/sample2.jpg'
            }
        )
        self.stdout.write(self.style.SUCCESS('[OK] Seeded Photo Albums'))

        self.stdout.write(self.style.SUCCESS('[SUCCESS] Entire database seeded with complete cricket data!'))
