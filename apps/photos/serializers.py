from rest_framework import serializers
from .models import PhotoAlbum, PhotoItem

class PhotoItemSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(source='image.url', read_only=True)

    class Meta:
        model = PhotoItem
        fields = ['id', 'image_url', 'caption', 'photo_credit', 'order']

class PhotoAlbumSerializer(serializers.ModelSerializer):
    cover_url = serializers.CharField(source='get_cover_url', read_only=True)
    photos = PhotoItemSerializer(many=True, read_only=True)

    class Meta:
        model = PhotoAlbum
        fields = ['id', 'title', 'slug', 'category', 'description', 'cover_url', 'photos', 'created_at']
