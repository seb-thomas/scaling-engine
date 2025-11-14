"""Tests for stations app views."""
import pytest
from rest_framework import status


@pytest.mark.unit
class TestStationViewSet:
    """Tests for the StationViewSet API."""

    def test_list_stations(self, api_client, station):
        """Test listing all stations."""
        response = api_client.get('/api/stations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == station.pk
        assert response.data[0]['name'] == 'Test Radio'
        assert response.data[0]['station_id'] == 'test_radio'
        assert response.data[0]['url'] == 'https://example.com/test'
        assert 'created' in response.data[0]

    def test_list_empty_stations(self, api_client):
        """Test listing when no stations exist."""
        response = api_client.get('/api/stations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_retrieve_station(self, api_client, station):
        """Test retrieving a single station."""
        response = api_client.get(f'/api/stations/{station.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == station.pk
        assert response.data['name'] == 'Test Radio'
        assert response.data['station_id'] == 'test_radio'
        assert response.data['url'] == 'https://example.com/test'
        assert 'created' in response.data

    def test_create_station(self, api_client):
        """Test creating a new station."""
        data = {
            'name': 'New Station',
            'station_id': 'new_station',
            'url': 'https://example.com/new'
        }
        response = api_client.post('/api/stations/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['name'] == 'New Station'
        assert response.data['station_id'] == 'new_station'
        assert 'created' in response.data

    def test_update_station(self, api_client, station):
        """Test updating a station."""
        data = {
            'name': 'Updated Station',
            'station_id': station.station_id,
            'url': station.url
        }
        response = api_client.put(f'/api/stations/{station.pk}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == station.pk
        assert response.data['name'] == 'Updated Station'
        assert 'created' in response.data

    def test_delete_station(self, api_client, station):
        """Test deleting a station."""
        response = api_client.delete(f'/api/stations/{station.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's deleted
        response = api_client.get(f'/api/stations/{station.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
