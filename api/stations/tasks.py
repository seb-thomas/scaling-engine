from celery import shared_task
from celery.utils.log import get_task_logger
from stations.utils import contains_keywords

logger = get_task_logger(__name__)


@shared_task(name="stations.tasks.contains_keywords_task")
def contains_keywords_task(episode_id):
    logger.info("contains_keywords_task %s" % (episode_id))
    return contains_keywords(episode_id)
