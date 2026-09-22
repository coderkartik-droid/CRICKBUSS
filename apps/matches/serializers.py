from rest_framework import serializers
from .models import (
    Match, Innings, BallByBall, PlayerMatchInnings,
    BowlerMatchInnings, Partnership, FallOfWicket, Venue
)
from apps.teams.serializers import TeamSimpleSerializer
from apps.players.serializers import PlayerSimpleSerializer

class VenueSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(source='get_image_url', read_only=True)

    class Meta:
        model = Venue
        fields = ['id', 'name', 'city', 'country', 'capacity', 'pitch_type', 'avg_first_innings_score', 'image_url']


class BallByBallSerializer(serializers.ModelSerializer):
    batter_name = serializers.CharField(source='batter.name', read_only=True)
    bowler_name = serializers.CharField(source='bowler.name', read_only=True)

    class Meta:
        model = BallByBall
        fields = [
            'id', 'over_number', 'ball_number', 'batter_name', 'bowler_name',
            'runs_off_bat', 'is_four', 'is_six', 'is_wicket', 'wicket_description',
            'extra_runs', 'commentary', 'timestamp'
        ]


class PlayerMatchInningsSerializer(serializers.ModelSerializer):
    player = PlayerSimpleSerializer(read_only=True)
    strike_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = PlayerMatchInnings
        fields = [
            'id', 'player', 'batting_position', 'dismissal', 'dismissal_text',
            'runs', 'balls_faced', 'fours', 'sixes', 'dots', 'strike_rate'
        ]


class BowlerMatchInningsSerializer(serializers.ModelSerializer):
    player = PlayerSimpleSerializer(read_only=True)
    economy_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = BowlerMatchInnings
        fields = [
            'id', 'player', 'overs', 'balls', 'maidens', 'runs_conceded',
            'wickets', 'wides', 'no_balls', 'economy_rate'
        ]


class InningsSerializer(serializers.ModelSerializer):
    batting_team = TeamSimpleSerializer(read_only=True)
    bowling_team = TeamSimpleSerializer(read_only=True)
    batters = PlayerMatchInningsSerializer(many=True, read_only=True)
    bowlers = BowlerMatchInningsSerializer(many=True, read_only=True)
    overs_formatted = serializers.CharField(read_only=True)
    current_run_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Innings
        fields = [
            'id', 'innings_number', 'batting_team', 'bowling_team',
            'runs', 'wickets', 'overs_formatted', 'current_run_rate',
            'total_extras', 'batters', 'bowlers'
        ]


class MatchSerializer(serializers.ModelSerializer):
    team1 = TeamSimpleSerializer(read_only=True)
    team2 = TeamSimpleSerializer(read_only=True)
    venue = VenueSerializer(read_only=True)
    innings = InningsSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'title', 'slug', 'match_number', 'match_type', 'status',
            'team1', 'team2', 'venue', 'pitch_report', 'weather_report',
            'result_text', 'start_datetime', 'innings', 'is_featured'
        ]
