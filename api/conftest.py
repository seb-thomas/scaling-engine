"""
Pytest configuration and shared fixtures for the project.
"""
import pytest
from django.conf import settings


@pytest.fixture(scope='session')
def celery_config():
    """Configure Celery for testing."""
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,
        'task_eager_propagates': True,
    }


@pytest.fixture
def celery_enable_logging():
    """Enable Celery logging during tests."""
    return True


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Give all tests access to the database."""
    pass


@pytest.fixture
def api_client():
    """DRF API test client."""
    from rest_framework.test import APIClient
    return APIClient()
