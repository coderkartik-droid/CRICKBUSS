from django.contrib import admin
from .models import SavedMatch, NotificationPreference

@admin.register(SavedMatch)
class SavedMatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'match', 'created_at')
    search_fields = ('user__email', 'match__title')

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_match_start', 'browser_live_score', 'sound_effects', 'updated_at')
