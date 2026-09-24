"""Tests for stations app views."""
import pytest
from rest_framework import status


@pytest.mark.unit
class TestStationViewSet:
    """Tests for the StationViewSet API."""

    def test_list_stations(self, api_client, station):
        """Test listing all stations (paginated response)."""
        response = api_client.get('/api/stations/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == station.pk
        assert results[0]['name'] == 'Test Radio'
        assert results[0]['station_id'] == 'test_radio'
        assert results[0]['url'] == 'https://example.com/test'
        assert 'created' in results[0]

    def test_list_empty_stations(self, api_client):
        """Test listing when no stations exist."""
        response = api_client.get('/api/stations/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0

    def test_retrieve_station(self, api_client, station):
        """Test retrieving a single station."""
        # StationViewSet uses lookup_field='station_id', so use station_id not pk
        response = api_client.get(f'/api/stations/{station.station_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == station.pk
        assert response.data['name'] == 'Test Radio'
        assert response.data['station_id'] == 'test_radio'
        assert response.data['url'] == 'https://example.com/test'
        assert 'created' in response.data

    # Note: StationViewSet is ReadOnlyModelViewSet, so create/update/delete operations
    # are not supported and would return 405 Method Not Allowed


@pytest.mark.unit
class TestSitemapBooks:
    """Tests for the slugs-only sitemap endpoint."""

    def test_lists_verified_books_with_show_of_latest_episode(self, api_client, brand, book):
        from datetime import datetime, timezone
        from stations.models import Book, Brand, Episode

        other = Brand.objects.create(station=brand.station, name='Other Show', url='https://example.com/other')
        book.episodes.update(aired_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        later = Episode.objects.create(
            brand=other, title='Later', url='https://example.com/later',
            aired_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        book.episodes.add(later)
        book.verification_status = Book.VERIFICATION_VERIFIED
        book.save()
        Book.objects.create(title='Unverified')

        response = api_client.get('/api/sitemap/books/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [{'slug': book.slug, 'show': other.slug, 'lastmod': '2026-03-01'}]
