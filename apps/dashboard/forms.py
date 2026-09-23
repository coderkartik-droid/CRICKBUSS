from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from apps.accounts.models import CustomUser
from apps.matches.models import Ground, Match, Tournament, Venue
from apps.players.models import Player
from apps.teams.models import Team
from apps.photos.models import PhotoItem
from apps.news.models import NewsArticle


class ManagedUserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'email', 'password', 'is_active')

    def __init__(self, *args, role, **kwargs):
        self.role = role
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'is_active':
                label = field.label or name.replace('_', ' ')
                field.widget.attrs.setdefault('placeholder', f'Enter {label.lower()}')
        self.fields['email'].widget.attrs.setdefault('placeholder', 'scorer@example.com')
        self.fields['password'].widget.attrs.setdefault('placeholder', 'Set a secure password')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('That email is already in use.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            password_validation.validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.role
        if user.pk is None:
            user.is_active = True
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ScorerAssignmentForm(forms.Form):
    match = forms.ModelChoiceField(
        queryset=Match.objects.all(),
        empty_label='Select match to assign',
        to_field_name='slug',
    )
    scorers = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role=CustomUser.Role.SCORER, is_deleted=False),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select one or more scorer accounts.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.fields['match'].queryset.exists():
            self.fields['match'].help_text = 'No matches available. Create a match first.'
        if not self.fields['scorers'].queryset.exists():
            self.fields['scorers'].help_text = 'No scorers available. Add a scorer account first.'


class LocalTeamForm(forms.ModelForm):
    DEFAULTS = {
        'team_type': Team.TeamType.DOMESTIC,
        'primary_color': '#0f766e',
        'secondary_color': '#f59e0b',
        'total_matches': 0,
        'total_wins': 0,
        'total_losses': 0,
        'total_ties_draws': 0,
        'trophies_count': 0,
    }

    class Meta:
        model = Team
        exclude = ('slug', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, initial in self.DEFAULTS.items():
            self.fields[name].required = False
            self.fields[name].initial = initial
        for name, field in self.fields.items():
            label = field.label or name.replace('_', ' ')
            field.widget.attrs.setdefault('placeholder', f'Enter {label.lower()}')
        self.fields['name'].widget.attrs.setdefault('placeholder', 'e.g. Riverside Cricket Club')
        self.fields['short_name'].widget.attrs.setdefault('placeholder', 'e.g. RCC')
        self.fields['team_type'].empty_label = 'Select team category'
        self.fields['country'].widget.attrs.setdefault('placeholder', 'Enter country or region')
        self.fields['logo'].help_text = 'Optional. Upload a PNG, JPG, or WEBP team logo.'
        self.fields['established_year'].help_text = 'Optional four-digit year.'
        self.fields['history'].help_text = 'Optional background about the local team.'
        self.fields['records'].help_text = 'Optional notable records or achievements.'
        self.fields['is_featured'].help_text = 'Show this team in featured local team lists.'
        self.fields['is_active'].help_text = 'Inactive teams are hidden from new selections.'
        if self.is_bound:
            for name, field in self.fields.items():
                if self.errors.get(name):
                    field.widget.attrs['class'] = (
                        f"{field.widget.attrs.get('class', '')} is-invalid"
                    ).strip()

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Enter a team name.')
        if Team.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A team with this name already exists.')
        slug = slugify(name)
        if slug and Team.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                'This team name creates a URL that is already in use. Choose a more specific name.'
            )
        return name

    def clean(self):
        cleaned = super().clean()
        for name, default in self.DEFAULTS.items():
            if cleaned.get(name) in (None, ''):
                cleaned[name] = default
        return cleaned


class LocalPlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        exclude = ('slug', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.SelectMultiple, forms.CheckboxInput, forms.ClearableFileInput)):
                label = field.label or name.replace('_', ' ')
                field.widget.attrs.setdefault('placeholder', f'Enter {label.lower()}')
        team = self.fields.get('primary_team')
        if team:
            team.empty_label = (
                'No teams available. Create a team first.'
                if not team.queryset.exists() else 'Select primary team'
            )
            team.help_text = 'Assign this player to a local team, if applicable.'
        teams = self.fields.get('teams')
        if teams and not teams.queryset.exists():
            teams.help_text = 'No teams available. Create a team first.'

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


class LocalTournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        exclude = ('slug',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('placeholder', f'Enter {field.label.lower()}')
        self.fields['name'].widget.attrs.setdefault('placeholder', 'e.g. Riverside Summer Cup')


class LocalGroundForm(forms.ModelForm):
    class Meta:
        model = Ground
        fields = ('name', 'venue', 'surface', 'capacity', 'is_active')

    def __init__(self, *args, creating_venue=False, **kwargs):
        self.creating_venue = creating_venue
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.setdefault('placeholder', 'Enter ground name')
        self.fields['surface'].widget.attrs.setdefault('placeholder', 'Enter pitch surface')
        self.fields['capacity'].required = False
        self.fields['capacity'].widget.attrs.setdefault('placeholder', 'Enter seating capacity')
        venue = self.fields['venue']
        venue.required = not creating_venue
        venue.empty_label = (
            'No venues found. Create one below.'
            if not venue.queryset.exists() else 'Select venue'
        )
        venue.help_text = (
            'Select an existing venue, or use Add Venue to create one here.'
            if venue.queryset.exists()
            else 'No venues exist yet. Create one below — Django Admin is not required.'
        )
        if self.is_bound:
            for name, field in self.fields.items():
                if self.errors.get(name):
                    field.widget.attrs['class'] = (
                        f"{field.widget.attrs.get('class', '')} is-invalid"
                    ).strip()

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Enter a ground name.')
        return name

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity in (None, ''):
            return 0
        return capacity

    def clean_venue(self):
        venue = self.cleaned_data.get('venue')
        if venue is None and self.creating_venue:
            return None
        if venue is None:
            raise forms.ValidationError('Select a venue or create a new one below.')
        return venue


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ('name', 'address', 'city', 'state', 'country', 'description', 'image')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter venue name'}),
            'address': forms.TextInput(attrs={'placeholder': 'Enter street address'}),
            'city': forms.TextInput(attrs={'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'placeholder': 'Enter state'}),
            'country': forms.TextInput(attrs={'placeholder': 'Enter country'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe the venue (optional)', 'rows': 3,
            }),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('prefix', 'venue')
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Venue Name'
        self.fields['address'].label = 'Address'
        self.fields['city'].label = 'City'
        self.fields['state'].label = 'State'
        self.fields['country'].label = 'Country'
        self.fields['description'].label = 'Description'
        self.fields['image'].label = 'Image'
        self.fields['address'].required = True
        self.fields['state'].required = True
        self.fields['description'].help_text = 'Optional venue details for local administrators.'
        self.fields['image'].help_text = 'Optional PNG, JPG, or WEBP image.'


class LocalMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        exclude = ('slug', 'created_at', 'updated_at', 'winning_team', 'result_text', 'man_of_match', 'scorer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.SelectMultiple, forms.CheckboxInput, forms.ClearableFileInput)):
                label = field.label or name.replace('_', ' ')
                field.widget.attrs.setdefault('placeholder', f'Enter {label.lower()}')
        choices = {
            'tournament': 'Select tournament first',
            'ground': 'Select ground',
            'team1': 'Select Team A',
            'team2': 'Select Team B',
            'toss_winner': 'Select toss winner (optional)',
            'team1_captain': 'Select Team A captain (optional)',
            'team2_captain': 'Select Team B captain (optional)',
            'team1_vice_captain': 'Select Team A vice-captain (optional)',
            'team2_vice_captain': 'Select Team B vice-captain (optional)',
        }
        for name, label in choices.items():
            field = self.fields.get(name)
            if field is not None and hasattr(field, 'empty_label'):
                field.empty_label = label

        tournament = self.fields['tournament']
        ground = self.fields['ground']
        scorers = self.fields['assigned_scorers']
        tournament.required = True
        ground.required = True
        scorers.required = True
        scorers.label = 'Scorer'
        scorers.help_text = (
            'No scorers available. Create a scorer account first.'
            if not scorers.queryset.exists()
            else 'Select at least one scorer assigned to this match.'
        )
        if not tournament.queryset.exists():
            tournament.help_text = 'No tournaments available. Create tournament first.'
        if not ground.queryset.exists():
            ground.help_text = 'No grounds available. Add a ground first.'
        if not self.fields['team1'].queryset.exists() or not self.fields['team2'].queryset.exists():
            self.fields['team1'].help_text = 'No teams available. Create a team first.'
            self.fields['team2'].help_text = 'No teams available. Create a team first.'
        if not self.fields['team1_playing_xi'].queryset.exists():
            self.fields['team1_playing_xi'].help_text = 'No players available. Add players first.'
            self.fields['team2_playing_xi'].help_text = 'No players available. Add players first.'
            for name in (
                'team1_captain', 'team1_vice_captain',
                'team2_captain', 'team2_vice_captain',
            ):
                self.fields[name].help_text = 'No players available. Add players first.'

    def clean(self):
        cleaned = super().clean()
        team1 = cleaned.get('team1')
        team2 = cleaned.get('team2')
        if team1 and team2 and team1 == team2:
            message = 'Team A and Team B must be different teams.'
            self.add_error('team1', message)
            self.add_error('team2', message)
        if cleaned.get('assigned_scorers'):
            cleaned['scorer'] = ', '.join(
                scorer.get_full_name() or scorer.email
                for scorer in cleaned['assigned_scorers']
            )
        return cleaned

    def save(self, commit=True):
        match = super().save(commit=False)
        match.scorer = self.cleaned_data.get('scorer', '')
        if commit:
            match.save()
            self.save_m2m()
        return match


class SimplePhotoForm(forms.ModelForm):
    """Simplified form for dashboard photo management - Photo + Title only"""
    class Meta:
        model = PhotoItem
        fields = ('image', 'caption')
        labels = {
            'image': 'Photo',
            'caption': 'Title'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.setdefault('accept', 'image/*')
        self.fields['image'].widget.attrs.setdefault('class', 'form-control')
        self.fields['caption'].widget.attrs.setdefault('placeholder', 'Enter photo title')
        self.fields['caption'].widget.attrs.setdefault('class', 'form-control')
        self.fields['caption'].required = True
        self.fields['caption'].label = 'Title'


class SimpleNewsForm(forms.ModelForm):
    """Simplified form for dashboard news management - Author, Image, Title, Description only"""
    class Meta:
        model = NewsArticle
        fields = ('author_name_fallback', 'featured_image', 'title', 'content')
        labels = {
            'author_name_fallback': 'Author Name',
            'featured_image': 'News Image',
            'title': 'News Title',
            'content': 'News Description'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up author name field
        self.fields['author_name_fallback'].widget.attrs.setdefault('placeholder', 'Enter author name')
        self.fields['author_name_fallback'].widget.attrs.setdefault('class', 'form-control')
        self.fields['author_name_fallback'].required = True
        
        # Set up image field
        self.fields['featured_image'].widget.attrs.setdefault('accept', 'image/*')
        self.fields['featured_image'].widget.attrs.setdefault('class', 'form-control')
        self.fields['featured_image'].required = False
        
        # Set up title field
        self.fields['title'].widget.attrs.setdefault('placeholder', 'Enter news title')
        self.fields['title'].widget.attrs.setdefault('class', 'form-control')
        self.fields['title'].required = True
        
        # Set up content field
        self.fields['content'].widget.attrs.setdefault('placeholder', 'Enter news description')
        self.fields['content'].widget.attrs.setdefault('class', 'form-control')
        self.fields['content'].widget = forms.Textarea(attrs={'rows': 6, 'class': 'form-control'})
        self.fields['content'].required = True

    def save(self, commit=True):
        news = super().save(commit=False)
        # Auto-generate slug from title
        if not news.slug:
            news.slug = slugify(news.title)[:210]
        # Set default category if not set
        if not hasattr(news, 'category') or not news.category:
            from apps.news.models import NewsCategory
            default_category, created = NewsCategory.objects.get_or_create(
                name='General',
                defaults={'slug': 'general'}
            )
            news.category = default_category
        # Set published time automatically
        if not news.published_at:
            from django.utils import timezone
            news.published_at = timezone.now()
        if commit:
            news.save()
        return news
