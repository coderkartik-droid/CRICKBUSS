from django.contrib import admin
from .models import RankingEntry

@admin.register(RankingEntry)
class RankingEntryAdmin(admin.ModelAdmin):
    list_display = ('rank', 'name', 'country', 'gender', 'cricket_format', 'category', 'rating', 'points', 'trend')
    list_filter = ('gender', 'cricket_format', 'category', 'country')
    search_fields = ('name', 'country')
    ordering = ('gender', 'cricket_format', 'category', 'rank')
