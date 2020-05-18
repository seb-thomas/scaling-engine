from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.utils.log import get_task_logger


@shared_task(name="sum_two_numbers")
def call_func(x, y):
    logger.info("Sent feedback email")
    return x + y
