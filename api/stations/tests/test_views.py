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
