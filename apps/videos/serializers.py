from rest_framework import serializers
from .models import CricketVideo, VideoCategory

class VideoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCategory
        fields = ['id', 'name', 'slug', 'description']

class CricketVideoSerializer(serializers.ModelSerializer):
    category = VideoCategorySerializer(read_only=True)
    thumbnail_url = serializers.CharField(source='get_thumbnail_url', read_only=True)
    video_file_url = serializers.SerializerMethodField()

    class Meta:
        model = CricketVideo
        fields = [
            'id', 'title', 'slug', 'category', 'description', 'thumbnail_url',
            'video_file_url', 'duration', 'views_count', 'likes_count', 'is_featured', 'created_at'
        ]

    def get_video_file_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            url = obj.video_file.url
            return request.build_absolute_uri(url) if request else url
        return None
