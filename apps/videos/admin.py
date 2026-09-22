from django.contrib import admin
from .models import VideoCategory, CricketVideo, VideoLike, VideoBookmark

@admin.register(VideoCategory)
class VideoCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CricketVideo)
class CricketVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration', 'views_count', 'likes_count', 'is_featured', 'is_active', 'created_at')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_active')

admin.site.register(VideoLike)
admin.site.register(VideoBookmark)
