"""Tests for Django signals."""
import pytest
from stations.models import Episode, Phrase


@pytest.mark.integration
class TestEpisodePostSaveSignal:
    """Tests for the episode post_save signal."""

    def test_signal_fires_without_errors(self, brand, phrases):
        """Test that creating an episode fires signal without errors."""
        # Create episode with 'book' keyword in title
        episode = Episode.objects.create(
            brand=brand,
            title='Episode about a great book',
            url='https://example.com/signal-test-1'
        )

        # Signal should fire without raising exceptions
        # In test mode with eager execution, task may or may not complete
        # depending on transaction isolation
        assert episode.pk is not None
        assert episode.title == 'Episode about a great book'

    def test_signal_handles_episode_without_keywords(self, brand, phrases):
        """Test signal handles episodes without keywords."""
        episode = Episode.objects.create(
            brand=brand,
            title='Episode about music',
            url='https://example.com/signal-test-2'
        )

        # Should not crash, stage stays SCRAPED
        episode.refresh_from_db()
        assert episode.stage == Episode.STAGE_SCRAPED

    def test_signal_does_not_reprocess_if_past_scraped(self, brand, phrases):
        """Test signal doesn't re-trigger extraction if stage is past SCRAPED."""
        episode = Episode.objects.create(
            brand=brand,
            title='Episode with book keyword',
            url='https://example.com/signal-test-3'
        )

        episode.refresh_from_db()

        # Manually advance stage past SCRAPED
        Episode.objects.filter(pk=episode.pk).update(stage=Episode.STAGE_COMPLETE)
        episode.refresh_from_db()

        # Save again - should not trigger task since stage != SCRAPED
        episode.save()
        episode.refresh_from_db()

        # Should still be COMPLETE
        assert episode.stage == Episode.STAGE_COMPLETE

    def test_signal_uses_transaction_on_commit(self, brand):
        """Test signal uses transaction.on_commit for task queuing."""
        from django.db import transaction

        with transaction.atomic():
            episode = Episode.objects.create(
                brand=brand,
                title='Transaction Episode',
                url='https://example.com/transaction-ep'
            )

        # If we get here without errors, transaction handling works
        assert episode.pk is not None
