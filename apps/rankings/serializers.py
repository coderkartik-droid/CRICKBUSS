from rest_framework import serializers
from .models import RankingEntry

class RankingEntrySerializer(serializers.ModelSerializer):
    trend = serializers.CharField(read_only=True)

    class Meta:
        model = RankingEntry
        fields = [
            'id', 'gender', 'cricket_format', 'category', 'rank',
            'previous_rank', 'trend', 'name', 'country', 'rating', 'points'
        ]
