from django import forms
from django.db import models

from apps.players.models import Player


class PlayingXIForm(forms.Form):
    team1_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    team2_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, team1=None, team2=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team1_players'].queryset = self._team_players(team1)
        self.fields['team2_players'].queryset = self._team_players(team2)
        if team1:
            self.fields['team1_players'].label = f'{team1.name} players'
        if team2:
            self.fields['team2_players'].label = f'{team2.name} players'

    @staticmethod
    def _team_players(team):
        if not team:
            return Player.objects.none()
        return Player.objects.filter(
            is_active=True,
        ).filter(
            models.Q(primary_team=team) | models.Q(teams=team)
        ).distinct().order_by('name')

    def clean(self):
        cleaned = super().clean()
        for field_name, label in (
            ('team1_players', 'Team 1'),
            ('team2_players', 'Team 2'),
        ):
            if len(cleaned.get(field_name, [])) != 11:
                self.add_error(
                    field_name,
                    f'Select exactly 11 players for {label}.',
                )
        return cleaned
