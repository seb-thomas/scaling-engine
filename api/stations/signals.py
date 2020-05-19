from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Episode
from .tasks import contains_keywords_task


@receiver(post_save, sender=Episode)
def episode_post_save(sender, instance, **kwargs):
    if not instance.has_book:
        contains_keywords_task.delay(instance.pk)
