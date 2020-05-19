from celery.utils.log import get_task_logger
from stations.models import Episode

logger = get_task_logger(__name__)


def contains_keywords(episode_id):
    try:
        episode = Episode.objects.get(pk=episode_id)
        if "Paul" in episode.title:
            episode.has_book = True
            episode.save(update_fields=["has_book"])
        logger.info("episode %s" % (episode.__dict__))
    except Episode.DoesNotExist:
        logger.info("episode_id %s Does Not Exist" % (episode_id))
