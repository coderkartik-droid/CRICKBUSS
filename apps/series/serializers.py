from rest_framework import serializers
from .models import Series, PointsTableEntry
from apps.teams.serializers import TeamSimpleSerializer

class PointsTableEntrySerializer(serializers.ModelSerializer):
    team = TeamSimpleSerializer(read_only=True)

    class Meta:
        model = PointsTableEntry
        exclude = ['series']

class SeriesSerializer(serializers.ModelSerializer):
    participating_teams = TeamSimpleSerializer(many=True, read_only=True)
    points_table = PointsTableEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Series
        fields = [
            'id', 'name', 'short_name', 'slug', 'category', 'cricket_format',
            'host_country', 'start_date', 'end_date', 'total_matches',
            'participating_teams', 'points_table', 'is_featured', 'is_active'
        ]

class SeriesSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Series
        fields = ['id', 'name', 'short_name', 'slug', 'category', 'cricket_format', 'start_date', 'end_date']
