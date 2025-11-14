"""Tests for stations app models."""
import pytest
from stations.models import Station, Brand, Episode, Phrase, Book


@pytest.mark.unit
class TestStationModel:
    """Tests for the Station model."""

    def test_create_station(self, station):
        """Test creating a station."""
        assert station.name == 'Test Radio'
        assert station.station_id == 'test_radio'
        assert station.url == 'https://example.com/test'

    def test_station_str(self, station):
        """Test station string representation."""
        assert str(station) == 'Test Radio'

    def test_station_created_timestamp(self, station):
        """Test station has created timestamp."""
        assert station.created is not None


@pytest.mark.unit
class TestBrandModel:
    """Tests for the Brand model."""

    def test_create_brand(self, brand, station):
        """Test creating a brand."""
        assert brand.name == 'Test Show'
        assert brand.station == station
        assert brand.url == 'https://example.com/test-show'

    def test_brand_str(self, brand):
        """Test brand string representation."""
        assert str(brand) == 'Test Show'

    def test_brand_cascade_delete(self, station):
        """Test brand is deleted when station is deleted."""
        brand = Brand.objects.create(
            station=station,
            name='Temp Brand',
            url='https://example.com/temp'
        )
        brand_id = brand.pk
        station.delete()
        assert not Brand.objects.filter(pk=brand_id).exists()


@pytest.mark.unit
class TestEpisodeModel:
    """Tests for the Episode model."""

    def test_create_episode(self, episode, brand):
        """Test creating an episode."""
        assert episode.title == 'Test Episode'
        assert episode.brand == brand
        assert episode.url == 'https://example.com/test-episode'
        assert episode.has_book is False

    def test_episode_str(self, episode):
        """Test episode string representation."""
        assert str(episode) == 'Test Episode'

    def test_episode_url_unique(self, brand):
        """Test episode URL must be unique."""
        Episode.objects.create(
            brand=brand,
            title='Episode 1',
            url='https://example.com/unique'
        )
        with pytest.raises(Exception):  # IntegrityError
            Episode.objects.create(
                brand=brand,
                title='Episode 2',
                url='https://example.com/unique'  # Duplicate!
            )

    def test_episode_has_book_default(self, episode):
        """Test has_book defaults to False."""
        assert episode.has_book is False

    def test_episode_has_book_editable_false(self):
        """Test has_book field is not editable."""
        field = Episode._meta.get_field('has_book')
        assert field.editable is False


@pytest.mark.unit
class TestPhraseModel:
    """Tests for the Phrase model."""

    def test_create_phrase(self):
        """Test creating a phrase."""
        phrase = Phrase.objects.create(text='testing')
        assert phrase.text == 'testing'

    def test_phrase_str(self):
        """Test phrase string representation."""
        phrase = Phrase.objects.create(text='book')
        assert str(phrase) == 'book'


@pytest.mark.unit
class TestBookModel:
    """Tests for the Book model."""

    def test_create_book(self, book, episode):
        """Test creating a book."""
        assert book.title == 'Test Book Title'
        assert book.episode == episode

    def test_book_str(self, book):
        """Test book string representation."""
        assert str(book) == 'Test Book Title'
