from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate by email or username with account lockout protection."""

    max_failures = 5
    lockout_minutes = 15

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get('email')
        if not identifier or not password:
            return None
        user = User.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier),
            is_deleted=False,
        ).first()
        if not user:
            User().set_password(password)
            return None
        if user.is_locked():
            return None
        if not user.check_password(password):
            user.failed_login_attempts += 1
            update_fields = ['failed_login_attempts', 'updated_at']
            if user.failed_login_attempts >= self.max_failures:
                user.locked_until = timezone.now() + timedelta(minutes=self.lockout_minutes)
                user.failed_login_attempts = 0
                update_fields += ['locked_until']
            user.save(update_fields=update_fields)
            return None
        if user.failed_login_attempts or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until', 'updated_at'])
        return user if self.user_can_authenticate(user) else None
