from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.matches.models import (
    BowlerMatchInnings,
    Innings,
    Match,
    Partnership,
    PlayerMatchInnings,
)
from apps.matches.services.career import process_completed_match
from apps.matches.services.scoring import record_delivery


class Command(BaseCommand):
    help = "Complete the generated demo match through the live scoring engine."

    def add_arguments(self, parser):
        parser.add_argument(
            "--match",
            default="delhi-warriors-vs-mumbai-tigers-1st-match",
            help="Match slug to simulate.",
        )

    def _setup_innings(self, match, innings_number, striker, non_striker, bowler):
        innings = Innings.objects.get(match=match, innings_number=innings_number)
        innings.striker = striker
        innings.non_striker = non_striker
        innings.current_bowler = bowler
        innings.save(update_fields=["striker", "non_striker", "current_bowler"])

        xi = match.team1_playing_xi.all() if innings_number == 1 else match.team2_playing_xi.all()
        bowling_xi = match.team2_playing_xi.all() if innings_number == 1 else match.team1_playing_xi.all()
        for position, player in enumerate(xi, start=1):
            PlayerMatchInnings.objects.get_or_create(
                innings=innings, player=player, defaults={"batting_position": position}
            )
        for player in bowling_xi:
            BowlerMatchInnings.objects.get_or_create(innings=innings, player=player)
        return innings

    def _available_batter(self, innings, xi):
        used = set(
            innings.batters.exclude(
                dismissal=PlayerMatchInnings.DismissalType.NOT_OUT
            ).values_list("player_id", flat=True)
        )
        used.update([innings.striker_id, innings.non_striker_id])
        return next(player for player in xi if player.pk not in used)

    def _next_bowler(self, bowling_xi, ball_index):
        return bowling_xi[(ball_index // 6) % len(bowling_xi)]

    def _events(self, legal_balls, wickets, target, innings_no):
        extra_points = {
            9: ("wide", 1),
            27: ("no_ball", 1),
            51: ("bye", 2),
            75: ("leg_bye", 1),
        }
        extras_total = sum(extra for extra_type, extra in extra_points.values())
        batting_target = target - extras_total
        values = [1, 1, 2, 0, 4, 1] * ((legal_balls // 6) + 1)
        values = values[:legal_balls]
        current = sum(values)
        index = 0
        while current < batting_target:
            if index in wickets or index in extra_points:
                index += 1
                continue
            increase = min(6 - values[index], batting_target - current)
            values[index] += increase
            current += increase
            index += 1
        while current > batting_target:
            if index in wickets or index in extra_points:
                index += 1
                continue
            decrease = min(values[index], current - batting_target)
            values[index] -= decrease
            current -= decrease
            index += 1

        events = []
        for index, runs in enumerate(values):
            extra_type, extra_runs = extra_points.get(index, ("", 0))
            events.append(
                {
                    "runs": 0 if extra_type else runs,
                    "extra_type": extra_type,
                    "extra_runs": extra_runs,
                    "wicket": index in wickets,
                    "dismissal_position": "striker",
                }
            )
        return events

    def _simulate_innings(self, match, innings, batting_xi, bowling_xi, events):
        dismissed = set()
        for ball_index, event in enumerate(events):
            innings.refresh_from_db()
            if innings.is_completed:
                break
            bowler = self._next_bowler(bowling_xi, ball_index)
            if not innings.striker_id or not innings.non_striker_id:
                replacement = self._available_batter(innings, batting_xi)
                if innings.striker_id:
                    innings.non_striker = replacement
                else:
                    innings.striker = replacement
                innings.save(update_fields=["striker", "non_striker"])

            dismissed_player = innings.striker if event["wicket"] else None
            commentary = (
                f"{innings.striker.name} is out, bowled by {bowler.name}."
                if dismissed_player
                else f"{innings.striker.name} faces {bowler.name}: "
                f"{event['extra_runs'] if event['extra_type'] else event['runs']} run(s)."
            )
            record_delivery(
                match.pk,
                batter_id=innings.striker_id,
                bowler_id=bowler.pk,
                runs_off_bat=event["runs"],
                extra_runs=event["extra_runs"],
                extra_type=event["extra_type"],
                is_wicket=event["wicket"],
                dismissed_player_id=dismissed_player.pk if dismissed_player else None,
                dismissal_position=event["dismissal_position"],
                commentary=commentary,
            )
            innings.refresh_from_db()
            if dismissed_player:
                dismissed.add(dismissed_player.pk)
                if not innings.is_completed:
                    replacement = self._available_batter(innings, batting_xi)
                    innings.striker = replacement
                    innings.save(update_fields=["striker"])
        return innings

    def _create_partnerships(self, innings):
        deliveries = list(
            innings.ball_deliveries.select_related("batter", "non_striker").order_by(
                "timestamp", "over_number", "ball_number"
            )
        )
        current = None
        runs = balls = wicket_number = 0
        for delivery in deliveries:
            pair = tuple(sorted((delivery.batter_id, delivery.non_striker_id)))
            if current is None:
                current = pair
            if pair != current:
                if current[0] and current[1]:
                    Partnership.objects.create(
                        innings=innings,
                        wicket_number=wicket_number,
                        batter1_id=current[0],
                        batter2_id=current[1],
                        runs=runs,
                        balls=balls,
                    )
                current = pair
                runs = balls = 0
            runs += delivery.runs_off_bat + delivery.extra_runs
            balls += 1
            if delivery.is_wicket:
                if current[0] and current[1]:
                    Partnership.objects.create(
                        innings=innings,
                        wicket_number=wicket_number,
                        batter1_id=current[0],
                        batter2_id=current[1],
                        runs=runs,
                        balls=balls,
                    )
                wicket_number += 1
                current = None
                runs = balls = 0
        if current and current[0] and current[1]:
            Partnership.objects.create(
                innings=innings,
                wicket_number=wicket_number,
                batter1_id=current[0],
                batter2_id=current[1],
                runs=runs,
                balls=balls,
            )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            match = Match.objects.select_for_update().get(slug=options["match"])
        except Match.DoesNotExist as exc:
            raise CommandError(f"Match {options['match']!r} does not exist.") from exc
        if match.stats_processed:
            self.stdout.write(self.style.WARNING("This match has already processed career statistics; no changes made."))
            return
        if match.status == Match.Status.COMPLETED and match.innings.count() >= 2:
            raise CommandError("The match is completed but statistics are not marked processed.")

        team1_xi = list(match.team1_playing_xi.all())
        team2_xi = list(match.team2_playing_xi.all())
        if len(team1_xi) < 11 or len(team2_xi) < 11:
            raise CommandError("Both teams need an assigned Playing XI before simulation.")

        match.toss_winner = match.team1
        match.toss_decision = Match.TossDecision.BAT
        match.status = Match.Status.LIVE
        match.actual_start_datetime = timezone.now()
        match.current_innings_number = 1
        match.opening_batter_one = team1_xi[0]
        match.opening_batter_two = team1_xi[1]
        match.opening_bowler = team2_xi[0]
        match.save(update_fields=[
            "toss_winner", "toss_decision", "status", "actual_start_datetime",
            "current_innings_number", "opening_batter_one", "opening_batter_two",
            "opening_bowler", "updated_at",
        ])

        innings = Innings.objects.create(
            match=match,
            innings_number=1,
            batting_team=match.team1,
            bowling_team=match.team2,
        )
        self._setup_innings(match, 1, team1_xi[0], team1_xi[1], team2_xi[0])
        self._simulate_innings(
            match, innings, team1_xi, team2_xi,
            self._events(122, {31, 55, 74, 86, 101, 113}, 170, 1),
        )
        innings.refresh_from_db()
        if not innings.is_completed:
            raise CommandError(
                f"First innings did not complete: {innings.runs}/{innings.wickets} "
                f"at {innings.overs_formatted} after {innings.ball_deliveries.count()} deliveries."
            )
        self._create_partnerships(innings)

        second = Innings.objects.get(match=match, innings_number=2)
        match.current_innings_number = 2
        match.status = Match.Status.LIVE
        match.save(update_fields=["current_innings_number", "status", "updated_at"])
        self._setup_innings(match, 2, team2_xi[0], team2_xi[1], team1_xi[0])
        self._simulate_innings(
            match, second, team2_xi, team1_xi,
            self._events(120, {22, 48, 69, 91}, second.target_runs + 1, 2),
        )
        second.refresh_from_db()
        self._create_partnerships(second)

        first = match.innings.get(innings_number=1)
        winner = match.team2 if second.runs >= (first.runs + 1) else match.team1
        if winner == match.team2:
            margin = 11 - second.wickets
            result = f"{winner.name} won by {margin} wickets"
        else:
            result = f"{winner.name} won by {first.runs - second.runs} runs"
        match.winning_team = winner
        match.result_text = result
        match.status = Match.Status.COMPLETED
        match.end_datetime = timezone.now()
        match.save(update_fields=["winning_team", "result_text", "status", "end_datetime", "updated_at"])
        process_completed_match(match.pk)

        for team in (match.team1, match.team2):
            team.total_matches += 1
            if team == winner:
                team.total_wins += 1
            else:
                team.total_losses += 1
            team.save(update_fields=["total_matches", "total_wins", "total_losses", "updated_at"])

        self.stdout.write(self.style.SUCCESS(
            f"{result}. Scorecard: {first.runs}/{first.wickets} ({first.overs_formatted}), "
            f"{second.runs}/{second.wickets} ({second.overs_formatted})."
        ))
