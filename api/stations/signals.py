from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Episode


@receiver(post_save, sender=Episode)
def episode_post_save(sender, instance, **kwargs):
    print("Post save ep!")
