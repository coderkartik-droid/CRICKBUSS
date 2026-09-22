from django.contrib import admin
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'team_type', 'country', 'captain_name', 'total_matches', 'total_wins', 'is_featured', 'is_active')
    list_filter = ('team_type', 'country', 'is_featured', 'is_active')
    search_fields = ('name', 'short_name', 'country', 'captain_name', 'coach_name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_editable = ('is_featured', 'is_active')
