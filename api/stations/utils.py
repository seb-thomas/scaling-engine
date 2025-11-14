from celery.utils.log import get_task_logger
from django.db import DatabaseError
from .models import Episode, Phrase

logger = get_task_logger(__name__)


def contains_keywords(episode_id):
    try:
        episode = Episode.objects.get(pk=episode_id)

        # Get keyword list once instead of creating new Phrase instance
        keyword_list = list(Phrase.objects.values_list("text", flat=True))

        if not keyword_list:
            logger.warning(f"No keywords configured. Episode {episode_id} cannot be checked.")
            return False

        if any(keyword in episode.title for keyword in keyword_list):
            episode.has_book = True
            episode.save(update_fields=["has_book"])
            logger.info(f"Episode {episode_id} '{episode.title}' contains book keywords")
            return True
        else:
            logger.debug(f"Episode {episode_id} '{episode.title}' has no book keywords")
            return False

    except Episode.DoesNotExist:
        logger.warning(f"Episode {episode_id} does not exist")
        return False
    except DatabaseError as e:
        logger.error(f"Database error checking episode {episode_id}: {e}")
        raise  # Re-raise to trigger Celery retry
