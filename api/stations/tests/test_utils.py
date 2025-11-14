"""Tests for stations app utilities."""
import pytest
from stations.models import Episode, Phrase
from stations.utils import contains_keywords


@pytest.mark.unit
class TestContainsKeywords:
    """Tests for the contains_keywords utility function."""

    def test_episode_with_book_keyword(self, episode_with_book_keyword, phrases):
        """Test episode with 'book' keyword is detected."""
        result = contains_keywords(episode_with_book_keyword.pk)
        assert result is True

        episode_with_book_keyword.refresh_from_db()
        assert episode_with_book_keyword.has_book is True

    def test_episode_without_keywords(self, episode, phrases):
        """Test episode without keywords returns False."""
        result = contains_keywords(episode.pk)
        assert result is False

        episode.refresh_from_db()
        assert episode.has_book is False

    def test_episode_with_novel_keyword(self, brand, phrases):
        """Test episode with 'novel' keyword is detected."""
        ep = Episode.objects.create(
            brand=brand,
            title='A great novel from 1984',
            url='https://example.com/novel-episode'
        )
        result = contains_keywords(ep.pk)
        assert result is True

        ep.refresh_from_db()
        assert ep.has_book is True

    def test_episode_with_author_keyword(self, brand, phrases):
        """Test episode with 'author' keyword is detected."""
        ep = Episode.objects.create(
            brand=brand,
            title='Interview with author Jane Smith',
            url='https://example.com/author-episode'
        )
        result = contains_keywords(ep.pk)
        assert result is True

    def test_no_phrases_configured(self, episode):
        """Test when no phrases are configured."""
        Phrase.objects.all().delete()
        result = contains_keywords(episode.pk)
        assert result is False

    def test_nonexistent_episode(self):
        """Test with nonexistent episode ID."""
        result = contains_keywords(99999)
        assert result is False

    def test_case_sensitivity(self, brand, phrases):
        """Test keyword matching is case-sensitive."""
        ep = Episode.objects.create(
            brand=brand,
            title='Episode about BOOK in caps',
            url='https://example.com/caps-episode'
        )
        # Our implementation is case-sensitive (substring match)
        result = contains_keywords(ep.pk)
        # This will be False because we check for lowercase 'book'
        # But title has 'BOOK' in caps
        assert result is False
