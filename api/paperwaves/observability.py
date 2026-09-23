"""
Error tracking: ERROR-level log records and uncaught exceptions go to PostHog
(EU), from the web app and the Celery workers.

Most failures here are caught and logged (scrapes, AI extraction), so a
logging handler catches far more than exception autocapture alone. When a
record is logged inside an `except` block without exc_info, the exception
being handled is still attached.

Enabled only when POSTHOG_KEY is set (production .env.prod), so dev and tests
never send anything.
"""

import logging
import os
import sys

from posthog import Posthog

POSTHOG_KEY = os.environ.get("POSTHOG_KEY", "")

_client = None


def get_client():
    global _client
    if _client is None and POSTHOG_KEY:
        service = "celery" if "celery" in os.path.basename(sys.argv[0]) else "web"
        _client = Posthog(
            POSTHOG_KEY,
            host="https://eu.i.posthog.com",
            enable_exception_autocapture=True,
            super_properties={"service": service},
            # Send on the calling thread: gunicorn and Celery fork workers, and
            # a background sender thread doesn't survive a fork. Errors are rare.
            sync_mode=True,
            timeout=5,
        )
    return _client


class LoggedError(Exception):
    """Stands in for an error that was logged without an exception."""


class PostHogErrorHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)

    def emit(self, record):
        client = get_client()
        # The SDK logs its own failures; don't feed those back in
        if client is None or record.name.startswith("posthog"):
            return
        try:
            exc = record.exc_info[1] if record.exc_info else sys.exc_info()[1]
            if exc is None:
                exc = LoggedError(record.getMessage())
            client.capture_exception(
                exc,
                properties={
                    "logger": record.name,
                    "log_message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                },
            )
        except Exception:
            pass
