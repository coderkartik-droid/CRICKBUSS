from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

from apps.matches.models import Ground, Match, Official, Tournament, Venue
from apps.players.models import Player
from apps.teams.models import Team


TEAM_SPECS = (
    {
        "name": "Delhi Warriors",
        "short_name": "DEL",
        "country": "India",
        "state": "Delhi",
        "primary_color": "#0F172A",
        "secondary_color": "#F59E0B",
        "captain_index": 0,
        "vice_index": 1,
        "names": [
            ("Arjun Mehra", "batter"), ("Rohan Kapoor", "batter"),
            ("Yash Malhotra", "batter"), ("Kabir Sethi", "batter"),
            ("Nikhil Bansal", "batter"), ("Aarav Khanna", "wicketkeeper"),
            ("Dev Rajput", "wicketkeeper"), ("Vikram Solanki", "all_rounder"),
            ("Manav Chawla", "all_rounder"), ("Ishaan Dutt", "all_rounder"),
            ("Samar Gill", "all_rounder"), ("Kunal Rawat", "bowler"),
            ("Aditya Rana", "bowler"), ("Harsh Vaid", "bowler"),
            ("Mohit Ahuja", "bowler"),
        ],
    },
    {
        "name": "Mumbai Tigers",
        "short_name": "MUM",
        "country": "India",
        "state": "Maharashtra",
        "primary_color": "#1E3A8A",
        "secondary_color": "#22C55E",
        "captain_index": 0,
        "vice_index": 1,
        "names": [
            ("Neil Deshmukh", "batter"), ("Vihaan Patil", "batter"),
            ("Sameer Joshi", "batter"), ("Rajiv Naik", "batter"),
            ("Omkar Shinde", "batter"), ("Ayaan Kulkarni", "wicketkeeper"),
            ("Pranav Bhide", "wicketkeeper"), ("Atharv Jadhav", "all_rounder"),
            ("Siddhant More", "all_rounder"), ("Ritvik Sawant", "all_rounder"),
            ("Tanmay Gokhale", "all_rounder"), ("Rudra Pawar", "bowler"),
            ("Akash Mhatre", "bowler"), ("Shreyas Nene", "bowler"),
            ("Mihir Lad", "bowler"),
        ],
    },
)


class Command(BaseCommand):
    help = "Create a complete, realistic upcoming demo cricket environment."

    def _avatar(self, player):
        initials = "".join(part[0] for part in player.name.split()[:2]).upper()
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="640">
<rect width="640" height="640" fill="#0f172a"/>
<circle cx="320" cy="270" r="190" fill="#22c55e"/>
<text x="320" y="300" text-anchor="middle" font-family="Arial" font-size="120"
 fill="white" font-weight="bold">{initials}</text>
<text x="320" y="570" text-anchor="middle" font-family="Arial" font-size="28"
 fill="white">{player.name}</text>
</svg>"""
        return ContentFile(svg.encode("utf-8"), name=f"{slugify(player.name)}.svg")

    def _logo(self, label, primary, secondary):
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">
<rect width="512" height="512" rx="96" fill="{primary}"/>
<circle cx="256" cy="220" r="120" fill="{secondary}"/>
<text x="256" y="270" text-anchor="middle" font-family="Arial" font-size="92"
 fill="white" font-weight="bold">{label}</text>
</svg>"""
        return ContentFile(svg.encode("utf-8"), name=f"{label.lower()}-logo.svg")

    def handle(self, *args, **options):
        today = timezone.localdate()
        tournament, _ = Tournament.objects.update_or_create(
            slug="champions-trophy-2026",
            defaults={
                "name": "Champions Trophy 2026",
                "description": "A showcase T20 competition featuring two elite domestic cricket teams.",
                "start_date": today + timedelta(days=7),
                "end_date": today + timedelta(days=21),
                "overs_per_innings": 20,
                "is_active": True,
            },
        )
        venue, _ = Venue.objects.update_or_create(
            name="Green Valley Cricket Stadium",
            defaults={
                "address": "Stadium Road, Dwarka",
                "city": "New Delhi",
                "state": "Delhi",
                "country": "India",
                "description": "A modern floodlit cricket venue with a balanced sporting surface.",
                "capacity": 42000,
                "pitch_type": "True bounce with good carry and even pace",
                "avg_first_innings_score": 176,
            },
        )
        ground, _ = Ground.objects.update_or_create(
            name="Green Valley Main Ground",
            defaults={"venue": venue, "surface": "Natural grass, sporting wicket", "capacity": 42000, "is_active": True},
        )

        teams = []
        players_by_team = {}
        for spec in TEAM_SPECS:
            team, _ = Team.objects.update_or_create(
                slug=slugify(spec["name"]),
                defaults={
                    "name": spec["name"],
                    "short_name": spec["short_name"],
                    "team_type": Team.TeamType.DOMESTIC,
                    "country": spec["country"],
                    "primary_color": spec["primary_color"],
                    "secondary_color": spec["secondary_color"],
                    "coach_name": "Rahul Iyer",
                    "home_venue": ground.name,
                    "established_year": 2020,
                    "history": f"{spec['name']} are a competitive domestic T20 side built around local talent.",
                    "is_featured": True,
                    "is_active": True,
                },
            )
            if not team.logo:
                team.logo.save(
                    f"{spec['short_name'].lower()}-logo.svg",
                    self._logo(spec["short_name"], spec["primary_color"], spec["secondary_color"]),
                    save=True,
                )
            players = []
            for jersey, (name, role) in enumerate(spec["names"], start=1):
                player, _ = Player.objects.update_or_create(
                    slug=slugify(name),
                    defaults={
                        "name": name,
                        "primary_team": team,
                        "role": role,
                        "batting_style": Player.BattingStyle.LEFT_HAND if jersey % 3 == 0 else Player.BattingStyle.RIGHT_HAND,
                        "bowling_style": (
                            Player.BowlingStyle.RIGHT_FAST if role == "bowler" and jersey % 2 else
                            Player.BowlingStyle.RIGHT_MEDIUM if role in ("bowler", "all_rounder") else
                            Player.BowlingStyle.NONE
                        ),
                        "jersey_number": jersey,
                        "born_date": date(1990 + jersey % 9, (jersey % 12) + 1, (jersey % 25) + 1),
                        "birth_place": f"{spec['state']}, India",
                        "biography": f"{name} is a {dict(Player.Role.choices)[role].lower()} representing {spec['name']}.",
                        "country": "India",
                        "state": spec["state"],
                        "is_active": True,
                        "is_featured": True,
                        "registration_status": Player.RegistrationStatus.APPROVED,
                    },
                )
                if not player.image:
                    player.image.save(f"{slugify(name)}.png", self._avatar(player), save=True)
                team.players.add(player)
                players.append(player)
            team.captain_name = players[spec["captain_index"]].name
            team.save(update_fields=["captain_name", "updated_at"])
            teams.append(team)
            players_by_team[team.pk] = players

        tournament_match, _ = Match.objects.update_or_create(
            slug="delhi-warriors-vs-mumbai-tigers-1st-match",
            defaults={
                "title": "Delhi Warriors vs Mumbai Tigers",
                "match_number": "1st Match",
                "match_type": Match.MatchType.T20,
                "team1": teams[0],
                "team2": teams[1],
                "tournament": tournament,
                "venue": venue,
                "ground": ground,
                "overs_limit": 20,
                "status": Match.Status.UPCOMING,
                "start_datetime": timezone.make_aware(
                    timezone.datetime.combine(today + timedelta(days=10), timezone.datetime.min.time().replace(hour=19, minute=30))
                ),
                "toss_winner": None,
                "toss_decision": "",
                "winning_team": None,
                "result_text": "",
                "stats_processed": False,
            },
        )
        for team, spec in zip(teams, TEAM_SPECS):
            players = players_by_team[team.pk]
            tournament_match.team1_playing_xi.set(players[:11]) if team == teams[0] else tournament_match.team2_playing_xi.set(players[:11])
            if team == teams[0]:
                tournament_match.team1_captain = players[spec["captain_index"]]
                tournament_match.team1_vice_captain = players[spec["vice_index"]]
            else:
                tournament_match.team2_captain = players[spec["captain_index"]]
                tournament_match.team2_vice_captain = players[spec["vice_index"]]
        tournament_match.save(update_fields=["team1_captain", "team1_vice_captain", "team2_captain", "team2_vice_captain", "updated_at"])

        scorer = get_user_model().objects.filter(role="scorer", is_active=True).first()
        if scorer:
            tournament_match.assigned_scorers.set([scorer])
        else:
            self.stdout.write(self.style.WARNING("No existing active scorer account found; match was created unassigned."))
        official, _ = Official.objects.get_or_create(
            name="Anil Menon",
            defaults={"role": "Umpire", "email": "anil.menon@example.com", "is_active": True},
        )
        tournament_match.officials.set([official])

        self.stdout.write(self.style.SUCCESS(
            f"Created demo environment: 1 tournament, 1 ground, 2 teams, 30 players, 1 upcoming match."
        ))
