from django.contrib import admin
from django import forms
from .models import Player, BattingStat, BowlingStat

class BattingStatInline(admin.TabularInline):
    model = BattingStat
    extra = 1

class BowlingStatInline(admin.TabularInline):
    model = BowlingStat
    extra = 1

class PlayerAdminForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = '__all__'

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname', '').strip()
        
        # Allow blank nicknames
        if not nickname:
            return nickname
        
        # Check for duplicate nickname (excluding current instance when editing)
        queryset = Player.objects.filter(nickname__iexact=nickname)
        
        # If editing, exclude the current player instance
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('A player with this nickname already exists. Please choose a different nickname.')
        
        return nickname

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    form = PlayerAdminForm
    list_display = ('name', 'role', 'primary_team', 'batting_style', 'bowling_style', 'is_featured', 'is_active')
    list_filter = ('role', 'batting_style', 'bowling_style', 'primary_team', 'is_featured', 'is_active')
    search_fields = ('name', 'nickname', 'birth_place')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('teams',)
    inlines = [BattingStatInline, BowlingStatInline]
    ordering = ('name',)

@admin.register(BattingStat)
class BattingStatAdmin(admin.ModelAdmin):
    list_display = ('player', 'format', 'matches', 'innings', 'runs', 'highest_score', 'batting_average', 'strike_rate', 'hundreds')
    list_filter = ('format',)
    search_fields = ('player__name',)

@admin.register(BowlingStat)
class BowlingStatAdmin(admin.ModelAdmin):
    list_display = ('player', 'format', 'matches', 'overs', 'wickets', 'best_bowling', 'bowling_average', 'economy')
    list_filter = ('format',)
    search_fields = ('player__name',)
