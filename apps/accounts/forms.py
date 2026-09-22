from django import forms
from django.contrib.auth import authenticate, password_validation
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class AdminUserCreationForm(forms.ModelForm):
    """Creation form for the email-based CustomUser used by Django Admin."""

    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=_('Use at least 8 characters and avoid common or numeric-only passwords.'),
    )
    password2 = forms.CharField(
        label=_('Password confirmation'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'username', 'role', 'password1', 'password2')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _('A user with this email already exists. Enter a different email address.')
            )
        return email

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if username and CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                _('A user with this username already exists. Enter a different username.')
            )
        return username or None

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password1')
        confirmation = cleaned.get('password2')

        if password:
            self.instance.email = cleaned.get('email', '')
            self.instance.first_name = cleaned.get('first_name', '')
            self.instance.last_name = cleaned.get('last_name', '')
            self.instance.username = cleaned.get('username', '')
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as exc:
                self.add_error('password1', exc)

        if password and confirmation and password != confirmation:
            self.add_error(
                'password2',
                _('Password confirmation does not match the password above.')
            )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': 'Create password',
        }),
    )
    confirm_password = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': 'Confirm your password',
        }),
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Create username',
                'autocomplete': 'username',
            }),
        }
        widgets['email'] = forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email',
            'placeholder': 'Enter your email address',
        })

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username or not username.replace('_', '').isalnum():
            raise forms.ValidationError(_('Use only letters, numbers, and underscores.'))
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_('That username is already in use.'))
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('An account with this email address already exists.'))
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as exc:
                self.add_error('password', exc)
        if password and cleaned.get('confirm_password') and password != cleaned['confirm_password']:
            self.add_error('confirm_password', _('Passwords do not match.'))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_active = True
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(label=_('Email or Username'), widget=forms.TextInput(attrs={
        'class': 'form-control',
        'autocomplete': 'username',
        'placeholder': 'Enter username or email',
    }))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'autocomplete': 'current-password',
        'placeholder': 'Enter password',
    }))
    remember_me = forms.BooleanField(required=False, label=_('Remember me'), widget=forms.CheckboxInput(
        attrs={'class': 'form-check-input'},
    ))

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        identifier, password = cleaned.get('username'), cleaned.get('password')
        if identifier and password:
            self.user = authenticate(self.request, username=identifier, password=password)
            if not self.user:
                raise forms.ValidationError(_('Invalid credentials or temporarily locked account.'))
        return cleaned

    def get_user(self):
        return getattr(self, 'user', None)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'avatar', 'first_name', 'last_name', 'username', 'email',
            'phone_number', 'date_of_birth', 'gender', 'country', 'state',
            'city', 'bio', 'favorite_team', 'favorite_player',
        ]
        widgets = {
            field: forms.TextInput(attrs={'class': 'form-control'})
            for field in [
                'first_name', 'last_name', 'username', 'phone_number',
                'country', 'state', 'city', 'favorite_team', 'favorite_player',
            ]
        }
        widgets['email'] = forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'Enter email address',
        })
        widgets['date_of_birth'] = forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
        })
        widgets['gender'] = forms.Select(attrs={'class': 'form-select'}, choices=[
            ('', 'Select gender'),
            ('female', 'Female'),
            ('male', 'Male'),
            ('non_binary', 'Non-binary'),
            ('prefer_not_to_say', 'Prefer not to say'),
        ])
        widgets['bio'] = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        widgets['avatar'] = forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'first_name': 'Enter your first name',
            'last_name': 'Enter your last name',
            'username': 'Enter username',
            'phone_number': 'Enter phone number',
            'email': 'Enter email address',
            'city': 'Enter city',
            'country': 'Enter country',
            'state': 'Enter state',
            'bio': 'Write something about yourself',
            'favorite_team': 'Select favorite team',
            'favorite_player': 'Select favorite player',
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs['placeholder'] = placeholder

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if CustomUser.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('That username is already in use.'))
        return username

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('That email address is already in use.'))
        return email


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter current password',
    }))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter new password',
    }))
    confirm_new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm new password',
    }))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        value = self.cleaned_data['current_password']
        if not self.user.check_password(value):
            raise forms.ValidationError(_('Your current password is incorrect.'))
        return value

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('new_password')
        if password:
            try:
                password_validation.validate_password(password, self.user)
            except forms.ValidationError as exc:
                self.add_error('new_password', exc)
        if password and cleaned.get('confirm_new_password') and password != cleaned['confirm_new_password']:
            self.add_error('confirm_new_password', _('New passwords do not match.'))
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save(update_fields=['password', 'updated_at'])
        return self.user

