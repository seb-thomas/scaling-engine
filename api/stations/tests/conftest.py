"""Fixtures for stations app tests."""
import pytest
from stations.models import Station, Brand, Episode, Phrase, Book


@pytest.fixture
def station():
    """Create a test station."""
    return Station.objects.create(
        name='Test Radio',
        station_id='test_radio',
        url='https://example.com/test'
    )


@pytest.fixture
def brand(station):
    """Create a test brand."""
    return Brand.objects.create(
        station=station,
        name='Test Show',
        url='https://example.com/test-show'
    )


@pytest.fixture
def episode(brand):
    """Create a test episode."""
    return Episode.objects.create(
        brand=brand,
        title='Test Episode',
        url='https://example.com/test-episode'
    )


@pytest.fixture
def episode_with_book_keyword(brand):
    """Create an episode with a book keyword in title."""
    return Episode.objects.create(
        brand=brand,
        title='Episode about a great book',
        url='https://example.com/episode-with-book'
    )


@pytest.fixture
def phrases():
    """Create test keyword phrases."""
    return [
        Phrase.objects.create(text='book'),
        Phrase.objects.create(text='novel'),
        Phrase.objects.create(text='author'),
    ]


@pytest.fixture
def book(episode):
    """Create a test book."""
    book = Book.objects.create(
        title='Test Book Title'
    )
    book.episodes.add(episode)
    return book
