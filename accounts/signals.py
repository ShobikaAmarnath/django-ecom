from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account, UserProfile

@receiver(post_save, sender=Account)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        print(f"--- SIGNAL FIRED: Creating profile for new user {instance.email} ---")
        UserProfile.objects.create(user=instance)