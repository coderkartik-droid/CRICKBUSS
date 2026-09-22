from django.contrib import admin
from .models import Series, PointsTableEntry

class PointsTableInline(admin.TabularInline):
    model = PointsTableEntry
    extra = 4
    ordering = ('position',)

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'category', 'cricket_format', 'start_date', 'end_date', 'total_matches', 'is_featured', 'is_active')
    list_filter = ('category', 'cricket_format', 'is_featured', 'is_active')
    search_fields = ('name', 'short_name', 'host_country')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('participating_teams',)
    inlines = [PointsTableInline]
    ordering = ('-start_date',)

@admin.register(PointsTableEntry)
class PointsTableEntryAdmin(admin.ModelAdmin):
    list_display = ('position', 'team', 'series', 'matches_played', 'won', 'lost', 'net_run_rate', 'points')
    list_filter = ('series',)
    search_fields = ('team__name', 'series__name')
