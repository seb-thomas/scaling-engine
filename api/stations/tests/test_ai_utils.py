"""Tests for AI-powered book extraction."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from anthropic import APIError, APITimeoutError, RateLimitError

from stations.ai_utils import (
    BookExtractor,
    get_book_extractor,
    extract_books_from_episode,
)


class TestBookExtractor:
    """Test BookExtractor class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        extractor = BookExtractor(api_key="test-key")
        assert extractor.api_key == "test-key"
        assert extractor.client is not None

    def test_init_without_api_key(self, monkeypatch):
        """Test initialization without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        extractor = BookExtractor()
        assert extractor.api_key is None
        assert extractor.client is None

    def test_init_with_env_api_key(self, monkeypatch):
        """Test initialization with API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        extractor = BookExtractor()
        assert extractor.api_key == "env-key"
        assert extractor.client is not None

    def test_is_available_with_key(self):
        """Test is_available returns True when client is initialized."""
        extractor = BookExtractor(api_key="test-key")
        assert extractor.is_available() is True

    def test_is_available_without_key(self, monkeypatch):
        """Test is_available returns False when no API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        extractor = BookExtractor()
        assert extractor.is_available() is False

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_success(self, mock_anthropic):
        """Test successful book extraction."""
        # Mock the Claude API response
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "has_book": True,
            "books": [
                {"title": "1984", "author": "George Orwell", "confidence": 0.95}
            ],
            "reasoning": "Clear mention of a book"
        })
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Episode about 1984 by George Orwell")

        assert result["has_book"] is True
        assert len(result["books"]) == 1
        assert result["books"][0]["title"] == "1984"
        assert result["books"][0]["author"] == "George Orwell"
        assert result["reasoning"] == "Clear mention of a book"

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_no_book(self, mock_anthropic):
        """Test extraction when no books are found."""
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "has_book": False,
            "books": [],
            "reasoning": "Episode is about music, not books"
        })
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Episode about classical music")

        assert result["has_book"] is False
        assert len(result["books"]) == 0

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_multiple_books(self, mock_anthropic):
        """Test extraction with multiple books."""
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "has_book": True,
            "books": [
                {"title": "1984", "author": "George Orwell", "confidence": 0.95},
                {"title": "Brave New World", "author": "Aldous Huxley", "confidence": 0.90}
            ],
            "reasoning": "Discussion of two dystopian novels"
        })
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Comparing 1984 and Brave New World")

        assert result["has_book"] is True
        assert len(result["books"]) == 2

    def test_extract_books_no_client(self, monkeypatch):
        """Test extraction when client is not initialized."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        extractor = BookExtractor()
        result = extractor.extract_books("Some text")

        assert result["has_book"] is False
        assert result["books"] == []
        assert "API key not configured" in result["reasoning"]

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_json_decode_error(self, mock_anthropic):
        """Test handling of JSON decode errors."""
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "This is not valid JSON"
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Some text")

        assert result["has_book"] is False
        assert "JSON parse error" in result["reasoning"]

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_general_error(self, mock_anthropic):
        """Test handling of general exceptions."""
        mock_client = Mock()
        # General exceptions don't retry - they return immediately
        mock_client.messages.create.side_effect = ValueError("Simulated error")
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Some text")

        assert result["has_book"] is False
        assert "Error" in result["reasoning"]
        # Verify it was only called once (no retry for general exceptions)
        assert mock_client.messages.create.call_count == 1

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_json_retry(self, mock_anthropic):
        """Test JSON parse error retry logic."""
        mock_client = Mock()

        # First call returns invalid JSON, second returns valid JSON
        mock_message_invalid = Mock()
        mock_content_invalid = Mock()
        mock_content_invalid.text = "Not valid JSON"
        mock_message_invalid.content = [mock_content_invalid]

        mock_message_valid = Mock()
        mock_content_valid = Mock()
        mock_content_valid.text = json.dumps({
            "has_book": True,
            "books": [{"title": "Test", "author": "Author", "confidence": 0.9}],
            "reasoning": "Success"
        })
        mock_message_valid.content = [mock_content_valid]

        mock_client.messages.create.side_effect = [
            mock_message_invalid,
            mock_message_valid
        ]
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Some text")

        # Should succeed on retry after JSON parse error
        assert result["has_book"] is True
        assert len(result["books"]) == 1
        assert mock_client.messages.create.call_count == 2

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_missing_has_book_field(self, mock_anthropic):
        """Test handling of response missing required fields."""
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({"books": []})  # Missing has_book
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Some text")

        assert result["has_book"] is False
        assert "Error" in result["reasoning"]  # Gets caught as unexpected error

    @patch("stations.ai_utils.Anthropic")
    def test_extract_books_defaults_optional_fields(self, mock_anthropic):
        """Test that optional fields get default values."""
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "has_book": True
            # Missing books and reasoning
        })
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        extractor = BookExtractor(api_key="test-key")
        result = extractor.extract_books("Some text")

        assert result["has_book"] is True
        assert result["books"] == []
        assert result["reasoning"] == "No reasoning provided"


class TestGetBookExtractor:
    """Test get_book_extractor singleton function."""

    def test_singleton_returns_same_instance(self):
        """Test that get_book_extractor returns the same instance."""
        # Reset the singleton
        import stations.ai_utils
        stations.ai_utils._extractor = None

        extractor1 = get_book_extractor()
        extractor2 = get_book_extractor()

        assert extractor1 is extractor2


@pytest.mark.django_db
class TestExtractBooksFromEpisode:
    """Test extract_books_from_episode function."""

    @patch("stations.utils.verify_book_exists")
    @patch("stations.ai_utils.get_book_extractor")
    def test_extract_books_from_episode_success(self, mock_get_extractor, mock_verify, brand):
        """Test successful extraction from episode."""
        from stations.models import Episode

        episode = Episode.objects.create(
            brand=brand,
            title="Book Club: Discussion of 1984",
            url="http://test.com/episode-1",
            has_book=False
        )

        # Mock the extractor
        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_books.return_value = {
            "has_book": True,
            "books": [{"title": "1984", "author": "George Orwell", "confidence": 0.95}],
            "reasoning": "Clear book mention"
        }
        mock_get_extractor.return_value = mock_extractor
        mock_verify.return_value = {"exists": True, "title": "1984", "author": "George Orwell", "cover_url": "", "isbn": None}

        result = extract_books_from_episode(episode.pk)

        assert result["has_book"] is True
        assert len(result["books"]) == 1

        # Verify episode was updated
        episode.refresh_from_db()
        assert episode.has_book is True

    @patch("stations.ai_utils.get_book_extractor")
    def test_extract_books_from_episode_no_book_found(self, mock_get_extractor, brand):
        """Test extraction when no books found."""
        from stations.models import Episode

        episode = Episode.objects.create(
            brand=brand,
            title="Music show",
            url="http://test.com/episode-2",
            has_book=False
        )

        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_books.return_value = {
            "has_book": False,
            "books": [],
            "reasoning": "No books mentioned"
        }
        mock_get_extractor.return_value = mock_extractor

        result = extract_books_from_episode(episode.pk)

        assert result["has_book"] is False

        # Verify episode was NOT updated
        episode.refresh_from_db()
        assert episode.has_book is False

    @patch("stations.utils.verify_book_exists")
    @patch("stations.ai_utils.get_book_extractor")
    def test_extract_books_from_episode_already_has_book(self, mock_get_extractor, mock_verify, brand):
        """Test extraction when episode already has_book=True."""
        from stations.models import Episode

        episode = Episode.objects.create(
            brand=brand,
            title="Book review",
            url="http://test.com/episode-3",
            has_book=True  # Already marked
        )

        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_books.return_value = {
            "has_book": True,
            "books": [{"title": "Test", "author": "Author", "confidence": 0.9}],
            "reasoning": "Book found"
        }
        mock_get_extractor.return_value = mock_extractor
        mock_verify.return_value = {"exists": True, "title": "Test", "author": "Author", "cover_url": "", "isbn": None}

        result = extract_books_from_episode(episode.pk)

        # Should still return result even if already marked
        assert result["has_book"] is True
        episode.refresh_from_db()
        assert episode.has_book is True

    @patch("stations.ai_utils.get_book_extractor")
    def test_extract_books_from_episode_not_available(self, mock_get_extractor, brand):
        """Test extraction when API is not available."""
        from stations.models import Episode

        episode = Episode.objects.create(
            brand=brand,
            title="Test episode",
            url="http://test.com/episode-4",
            has_book=False
        )

        mock_extractor = Mock()
        mock_extractor.is_available.return_value = False
        mock_get_extractor.return_value = mock_extractor

        result = extract_books_from_episode(episode.pk)

        assert result["has_book"] is False
        assert "API not configured" in result["reasoning"]

    @patch("stations.ai_utils.get_book_extractor")
    def test_extract_books_from_episode_not_found(self, mock_get_extractor):
        """Test extraction when episode doesn't exist."""
        result = extract_books_from_episode(99999)

        assert result["has_book"] is False
        assert "Episode not found" in result["reasoning"]

    @patch("stations.ai_utils.get_book_extractor")
    def test_extract_books_from_episode_extraction_error(self, mock_get_extractor, brand):
        """Test handling of extraction errors: episode marked FAILED and exception re-raised."""
        from stations.models import Episode

        episode = Episode.objects.create(
            brand=brand,
            title="Test episode",
            url="http://test.com/episode-5",
            has_book=False,
        )

        mock_extractor = Mock()
        mock_extractor.is_available.return_value = True
        mock_extractor.extract_books.side_effect = Exception("Test error")
        mock_get_extractor.return_value = mock_extractor

        with pytest.raises(Exception, match="Test error"):
            extract_books_from_episode(episode.pk)

        episode.refresh_from_db()
        assert episode.status == Episode.STATUS_FAILED
        assert "Test error" in (episode.last_error or "")
