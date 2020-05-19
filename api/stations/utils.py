from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def contains_keywords(episode_id):
    logger.info("UTIL contains_keywords_task %s" % (episode_id))
