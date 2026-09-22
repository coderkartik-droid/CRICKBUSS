from rest_framework import serializers
from .models import CricketVideo, VideoCategory

class VideoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCategory
        fields = ['id', 'name', 'slug', 'description']

class CricketVideoSerializer(serializers.ModelSerializer):
    category = VideoCategorySerializer(read_only=True)
    thumbnail_url = serializers.CharField(source='get_thumbnail_url', read_only=True)

    class Meta:
        model = CricketVideo
        fields = [
            'id', 'title', 'slug', 'category', 'description', 'thumbnail_url',
            'video_url', 'duration', 'views_count', 'likes_count', 'is_featured', 'created_at'
        ]
