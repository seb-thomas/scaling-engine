from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name="stations.tasks.call_func")
def call_func(x, y):
    logger.info("Sent feedback email")
    print("call_func %s" % (x + y))
    return x + y
