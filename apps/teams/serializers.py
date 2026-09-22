from rest_framework import serializers
from .models import Team

class TeamSerializer(serializers.ModelSerializer):
    logo_url = serializers.CharField(source='get_logo_url', read_only=True)
    win_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'short_name', 'slug', 'team_type', 'country',
            'logo_url', 'primary_color', 'secondary_color', 'captain_name',
            'coach_name', 'home_venue', 'established_year', 'history',
            'records', 'total_matches', 'total_wins', 'total_losses',
            'total_ties_draws', 'trophies_count', 'win_percentage', 'is_featured'
        ]

class TeamSimpleSerializer(serializers.ModelSerializer):
    logo_url = serializers.CharField(source='get_logo_url', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'slug', 'country', 'logo_url', 'primary_color']
