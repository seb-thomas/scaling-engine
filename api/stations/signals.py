from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Episode
from .tasks import call_func


@receiver(post_save, sender=Episode)
def episode_post_save(sender, instance, **kwargs):
    if not instance.has_book:
        call_func(1, 2)
        print("Post save ep!")
