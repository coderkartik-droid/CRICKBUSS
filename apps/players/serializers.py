from rest_framework import serializers
from .models import Player, BattingStat, BowlingStat
from apps.teams.serializers import TeamSimpleSerializer

class BattingStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = BattingStat
        exclude = ['id', 'player']

class BowlingStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = BowlingStat
        exclude = ['id', 'player']

class PlayerSerializer(serializers.ModelSerializer):
    primary_team = TeamSimpleSerializer(read_only=True)
    teams = TeamSimpleSerializer(many=True, read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    batting_stats = BattingStatSerializer(many=True, read_only=True)
    bowling_stats = BowlingStatSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'name', 'slug', 'nickname', 'image_url', 'primary_team',
            'teams', 'role', 'batting_style', 'bowling_style', 'jersey_number',
            'born_date', 'birth_place', 'biography', 'achievements', 'records',
            'batting_stats', 'bowling_stats', 'is_featured'
        ]

class PlayerSimpleSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(source='get_image_url', read_only=True)

    class Meta:
        model = Player
        fields = ['id', 'name', 'slug', 'role', 'image_url']
