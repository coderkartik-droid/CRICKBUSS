from django.contrib import admin
from .models import PhotoAlbum, PhotoItem

class PhotoItemInline(admin.TabularInline):
    model = PhotoItem
    extra = 3

@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_featured', 'is_active', 'created_at')
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PhotoItemInline]

@admin.register(PhotoItem)
class PhotoItemAdmin(admin.ModelAdmin):
    list_display = ('caption', 'album', 'photo_credit', 'order', 'created_at')
    list_filter = ('album__category',)
