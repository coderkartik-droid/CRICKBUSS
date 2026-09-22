from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def user_post_save(sender, instance, created, **kwargs):
    """
    Ensure user dashboard and notification settings exist.
    """
    if created:
        try:
            from apps.dashboard.models import NotificationPreference
            NotificationPreference.objects.get_or_create(user=instance)
        except Exception:
            pass
