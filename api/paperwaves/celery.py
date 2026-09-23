import os
from celery import Celery
from celery.signals import after_setup_logger


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "paperwaves.settings")

app = Celery("paperwaves")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@after_setup_logger.connect
def send_errors_to_posthog(logger, **kwargs):
    # Celery replaces the root logger's handlers, so re-add the PostHog one
    # (task failures are logged through root)
    if os.environ.get("POSTHOG_KEY"):
        from paperwaves.observability import PostHogErrorHandler

        logger.addHandler(PostHogErrorHandler())


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
