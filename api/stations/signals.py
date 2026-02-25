from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import post_save
from django.conf import settings
from .models import Episode
from .tasks import contains_keywords_task, ai_extract_books_task


@receiver(post_save, sender=Episode)
def episode_post_save(sender, instance, created, **kwargs):
    """
    Trigger book extraction when a NEW episode is created.

    Only fires on creation (not every save) to prevent duplicate tasks
    during backfill and status updates.

    Supports three modes via BOOK_EXTRACTION_MODE setting:
    - 'keyword': Legacy keyword matching (default)
    - 'ai': AI-powered extraction using Claude
    - 'both': Run both methods
    """
    if not created:
        return

    if not instance.has_book:
        mode = getattr(settings, "BOOK_EXTRACTION_MODE", "keyword")

        if mode == "keyword":
            transaction.on_commit(lambda: contains_keywords_task.delay(instance.pk))
        elif mode == "ai":
            transaction.on_commit(lambda: ai_extract_books_task.delay(instance.pk))
        elif mode == "both":
            # Run both tasks - AI is more accurate, keywords is fast fallback
            transaction.on_commit(lambda: ai_extract_books_task.delay(instance.pk))
            transaction.on_commit(lambda: contains_keywords_task.delay(instance.pk))
        else:
            # Default to keyword if invalid mode
            transaction.on_commit(lambda: contains_keywords_task.delay(instance.pk))
