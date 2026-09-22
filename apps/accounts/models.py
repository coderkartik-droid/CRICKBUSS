import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field is required.'))
        email = self.normalize_email(email)
        privileged_roles = {
            getattr(self.model.Role, 'SUPER_ADMIN', 'super_admin'),
            getattr(self.model.Role, 'ADMIN', 'admin'),
            getattr(self.model.Role, 'SCORER', 'scorer'),
        }
        if extra_fields.get('role') in privileged_roles and not extra_fields.get('is_superuser'):
            raise ValueError(_('Privileged accounts must be created through an authorized management flow.'))
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.Role.SUPER_ADMIN)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', _('Super Admin')
        ADMIN = 'admin', _('Admin')
        SCORER = 'scorer', _('Scorer')
        USER = 'user', _('Normal User')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    username = models.CharField(_('username'), max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)
    role = models.CharField(_('user role'), max_length=20, choices=Role.choices, default=Role.USER)
    avatar = models.ImageField(_('avatar image'), upload_to='avatars/%Y/%m/', null=True, blank=True)
    bio = models.TextField(_('bio summary'), max_length=500, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=20, blank=True)
    country = models.CharField(_('country'), max_length=80, blank=True)
    state = models.CharField(_('state'), max_length=80, blank=True)
    city = models.CharField(_('city'), max_length=80, blank=True)
    favorite_team = models.CharField(_('favorite cricket team'), max_length=100, blank=True)
    favorite_player = models.CharField(_('favorite cricket player'), max_length=100, blank=True)


    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_user_agent = models.CharField(max_length=512, blank=True)

    is_active = models.BooleanField(_('active status'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_deleted = models.BooleanField(_('soft delete flag'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active', 'is_deleted']),
            models.Index(fields=['locked_until']),
        ]

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.email.split('@')[0]

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default-avatar.svg'

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def soft_delete(self):
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=['is_deleted', 'is_active'])


class LoginHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_history')
    successful = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]
