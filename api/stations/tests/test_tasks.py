"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, MagicMock
from stations.tasks import contains_keywords_task
from stations.models import Episode


@pytest.mark.celery
@pytest.mark.unit
class TestContainsKeywordsTask:
    """Tests for the contains_keywords Celery task."""

    def test_task_calls_utils_function(self, episode, phrases):
        """Test task calls the utils.contains_keywords function."""
        with patch('stations.tasks.contains_keywords') as mock_contains:
            mock_contains.return_value = True

            result = contains_keywords_task(episode.pk)

            mock_contains.assert_called_once_with(episode.pk)
            assert result is True

    def test_task_with_valid_episode(self, episode_with_book_keyword, phrases):
        """Test task execution with valid episode."""
        result = contains_keywords_task(episode_with_book_keyword.pk)
        assert result is True

        episode_with_book_keyword.refresh_from_db()
        assert episode_with_book_keyword.has_book is True

    def test_task_with_nonexistent_episode(self):
        """Test task handles nonexistent episode gracefully."""
        result = contains_keywords_task(99999)
        assert result is False

    def test_task_retry_on_database_error(self, episode):
        """Test task retries on database errors."""
        with patch('stations.tasks.contains_keywords') as mock_contains:
            from django.db import DatabaseError
            mock_contains.side_effect = DatabaseError('Connection lost')

            with pytest.raises(DatabaseError):
                contains_keywords_task(episode.pk)
