import logging
from unittest import mock

from paperwaves import observability


def _logger_with_handler():
    logger = logging.getLogger("test.observability")
    logger.handlers = [observability.PostHogErrorHandler()]
    logger.propagate = False
    return logger


def test_logged_error_inside_except_sends_the_handled_exception():
    client = mock.Mock()
    logger = _logger_with_handler()
    with mock.patch.object(observability, "get_client", return_value=client):
        try:
            raise ValueError("feed broke")
        except ValueError as e:
            # How tasks.py logs: no exc_info, message only
            logger.error(f"Error scraping Front Row: {e}")

    exc = client.capture_exception.call_args.args[0]
    assert isinstance(exc, ValueError)
    assert client.capture_exception.call_args.kwargs["properties"]["log_message"] == "Error scraping Front Row: feed broke"


def test_error_without_exception_is_sent_as_logged_error():
    client = mock.Mock()
    logger = _logger_with_handler()
    with mock.patch.object(observability, "get_client", return_value=client):
        logger.error("No episodes found")

    exc = client.capture_exception.call_args.args[0]
    assert isinstance(exc, observability.LoggedError)
    assert str(exc) == "No episodes found"


def test_warnings_are_not_sent():
    client = mock.Mock()
    logger = _logger_with_handler()
    with mock.patch.object(observability, "get_client", return_value=client):
        logger.warning("Slow response")

    client.capture_exception.assert_not_called()


def test_disabled_without_key():
    with mock.patch.object(observability, "POSTHOG_KEY", ""), mock.patch.object(observability, "_client", None):
        assert observability.get_client() is None
