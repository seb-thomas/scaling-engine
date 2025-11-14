from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from .utils import contains_keywords

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
    logger.info(f"Processing keywords for episode {episode_id}")
    try:
        return contains_keywords(episode_id)
    except Exception as e:
        logger.error(f"Error processing episode {episode_id}: {e}")
        raise
