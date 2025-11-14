from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from .utils import contains_keywords
from .ai_utils import extract_books_from_episode

logger = get_task_logger(__name__)


@shared_task(
    name="stations.tasks.contains_keywords_task",
    bind=True,
    autoretry_for=(DatabaseError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    max_retries=3,
)
def contains_keywords_task(self, episode_id):
    """Legacy keyword-based book detection task."""
    logger.info(f"Processing keywords for episode {episode_id}")
    try:
        return contains_keywords(episode_id)
    except Exception as e:
        logger.error(f"Error processing episode {episode_id}: {e}")
        raise


@shared_task(
    name="stations.tasks.ai_extract_books_task",
    bind=True,
    autoretry_for=(DatabaseError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def ai_extract_books_task(self, episode_id):
    """
    AI-powered book extraction task using Claude.

    This task uses Claude AI to intelligently extract book mentions
    from episode titles, replacing simple keyword matching with
    context-aware natural language understanding.
    """
    logger.info(f"AI extracting books for episode {episode_id}")
    try:
        result = extract_books_from_episode(episode_id)
        logger.info(f"AI extraction complete for episode {episode_id}: "
                   f"has_book={result['has_book']}, books={len(result.get('books', []))}")
        return result
    except Exception as e:
        logger.error(f"Error in AI extraction for episode {episode_id}: {e}")
        raise
