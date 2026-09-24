import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Player, PlayerRegistrationRequest


# ---------------------------------------------------------------------------
# Widget attribute helpers
# ---------------------------------------------------------------------------

def _fc(placeholder='', **attrs):
    base = {'class': 'form-control'}
    if placeholder:
        base['placeholder'] = placeholder
    base.update(attrs)
    return base


def _fs(**attrs):
    base = {'class': 'form-select'}
    base.update(attrs)
    return base


# ---------------------------------------------------------------------------
# Public Registration Form  →  writes to PlayerRegistrationRequest only
# ---------------------------------------------------------------------------

class PlayerRegistrationRequestForm(forms.ModelForm):
    """
    The public-facing form that visitors fill in to register a player.
    On save() it creates a PlayerRegistrationRequest record (status=pending).
    It NEVER touches the Player table.
    """

    # Extra non-model field: team FK rendered as a searchable select.
    team = forms.ModelChoiceField(
        queryset=None,           # set in __init__
        required=False,
        empty_label='— No team / not listed —',
        widget=forms.Select(attrs={**_fs(), 'id': 'id_team_select'}),
        label='Team',
    )

    class Meta:
        model  = PlayerRegistrationRequest
        fields = (
            'full_name',
            'mobile_number',
            'email_address',
            'full_address',
            'date_of_birth',
            'jersey_number',
            'playing_role',
            'batting_style',
            'bowling_style',
            'photo',
            'country',
            'short_bio',
        )
        labels = {
            'full_name':     'Full Name',
            'mobile_number': 'Mobile Number',
            'email_address': 'Email Address',
            'full_address':  'Address',
            'date_of_birth': 'Date of Birth',
            'jersey_number': 'Jersey Number',
            'playing_role':  'Playing Role',
            'batting_style': 'Batting Style',
            'bowling_style': 'Bowling Style',
            'photo':         'Player Photo',
            'country':       'Country',
            'short_bio':     'Short Bio',
        }
        widgets = {
            'full_name':     forms.TextInput(attrs=_fc(placeholder='Enter full player name', autocomplete='off')),
            'mobile_number': forms.TextInput(attrs=_fc(placeholder='+91 98765 43210', inputmode='tel')),
            'email_address': forms.EmailInput(attrs=_fc(placeholder='player@example.com')),
            'full_address':  forms.Textarea(attrs={**_fc(placeholder='House / Flat, Street, Area, Pin Code'), 'rows': 2}),
            'date_of_birth': forms.DateInput(attrs={**_fc(), 'type': 'date'}),
            'jersey_number': forms.NumberInput(attrs=_fc(placeholder='e.g. 7', min='1', max='999')),
            'playing_role':  forms.Select(attrs=_fs()),
            'batting_style': forms.Select(attrs=_fs()),
            'bowling_style': forms.Select(attrs=_fs()),
            'photo':         forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'country':       forms.TextInput(attrs=_fc(placeholder='e.g. India', autocomplete='off')),
            'short_bio':     forms.Textarea(attrs={**_fc(placeholder="A short introduction about the player…"), 'rows': 3}),
        }

    def __init__(self, *args, teams_qs=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Required
        self.fields['full_name'].required     = True
        self.fields['mobile_number'].required = True
        self.fields['playing_role'].required  = True
        self.fields['batting_style'].required = True
        self.fields['country'].required       = True

        # Optional
        for f in ('email_address', 'full_address', 'date_of_birth',
                  'jersey_number', 'bowling_style', 'photo', 'short_bio'):
            self.fields[f].required = False

        # Team dropdown
        from apps.teams.models import Team
        if teams_qs is None:
            teams_qs = Team.objects.filter(is_active=True).order_by('name')
        self.fields['team'].queryset = teams_qs
        self.has_teams = teams_qs.exists()

    # ── Validation ────────────────────────────────────────────────────────

    def clean_mobile_number(self):
        raw = (self.cleaned_data.get('mobile_number') or '').strip()
        if not raw:
            raise ValidationError('Mobile number is required.')
        digits = re.sub(r'[\s\-\(\)\+]', '', raw)
        if not digits.isdigit():
            raise ValidationError('Mobile number may only contain digits, spaces, +, - or ().')
        if not (7 <= len(digits) <= 15):
            raise ValidationError('Enter a valid mobile number (7–15 digits).')
        # Duplicate check: reject if another *pending or approved* request shares it
        qs = PlayerRegistrationRequest.objects.filter(
            mobile_number=raw,
            status__in=(
                PlayerRegistrationRequest.Status.PENDING,
                PlayerRegistrationRequest.Status.APPROVED,
            ),
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                'A registration with this mobile number already exists. '
                'Please contact the admin if this is an error.'
            )
        return raw

    def clean_date_of_birth(self):
        from django.utils import timezone
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob >= timezone.now().date():
            raise ValidationError('Date of birth must be in the past.')
        return dob

    # ── Save ──────────────────────────────────────────────────────────────

    def save(self, commit=True):
        req = super().save(commit=False)

        # Map the extra team field
        selected_team = self.cleaned_data.get('team')
        req.team = selected_team
        if selected_team:
            req.team_name_raw = selected_team.name
        else:
            req.team_name_raw = ''

        req.status = PlayerRegistrationRequest.Status.PENDING
        if commit:
            req.save()
        return req


# ---------------------------------------------------------------------------
# Keep the old name as an alias so any existing imports don't break
# ---------------------------------------------------------------------------
PlayerRegistrationForm = PlayerRegistrationRequestForm
