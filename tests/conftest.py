"""Pytest configuration and fixtures for Spotify App Agent Template tests."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "timezone": "America/New_York",
        "persona": {
            "name": "Test Bot",
            "prefix": "Test",
            "bio": "A test bot for testing"
        },
        "playlists": {
            "playlist1": {
                "id": "test_playlist_1_id",
                "name": "Test Playlist 1",
                "description": "Test playlist 1"
            },
            "playlist2": {
                "id": "test_playlist_2_id", 
                "name": "Test Playlist 2",
                "description": "Test playlist 2"
            }
        },
        "artist_caps": {
            "playlist1": 3,
            "playlist2": 2
        },
        "seeding": {
            "playlist1": ["test_artist_1", "test_artist_2"],
            "playlist2": ["test_artist_3"]
        }
    }


@pytest.fixture
def mock_spotify_client():
    """Mock Spotify client for testing."""
    mock_client = Mock()
    mock_client.get_user_playlists.return_value = {
        "items": [
            {"id": "test_playlist_1_id", "name": "Test Playlist 1"},
            {"id": "test_playlist_2_id", "name": "Test Playlist 2"}
        ]
    }
    mock_client.get_playlist_tracks.return_value = {
        "items": [
            {"track": {"id": "track1", "name": "Test Track 1", "artists": [{"name": "Test Artist 1"}]}},
            {"track": {"id": "track2", "name": "Test Track 2", "artists": [{"name": "Test Artist 2"}]}}
        ]
    }
    mock_client.search_tracks.return_value = {
        "tracks": {
            "items": [
                {"id": "search_track1", "name": "Search Track 1", "artists": [{"name": "Search Artist 1"}]}
            ]
        }
    }
    return mock_client


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "SPOTIFY_CLIENT_ID": "test_client_id",
        "SPOTIFY_CLIENT_SECRET": "test_client_secret", 
        "SPOTIFY_REFRESH_TOKEN": "test_refresh_token",
        "SPOTIFY_USER_ID": "test_user_id"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def test_database():
    """Create a test database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_playlist_data():
    """Sample playlist data for testing."""
    return {
        "playlist1": {
            "id": "test_playlist_1_id",
            "name": "Test Playlist 1",
            "tracks": [
                {"id": "track1", "name": "Test Track 1", "artists": [{"name": "Test Artist 1"}]},
                {"id": "track2", "name": "Test Track 2", "artists": [{"name": "Test Artist 2"}]}
            ]
        },
        "playlist2": {
            "id": "test_playlist_2_id",
            "name": "Test Playlist 2", 
            "tracks": [
                {"id": "track3", "name": "Test Track 3", "artists": [{"name": "Test Artist 3"}]}
            ]
        }
    }


@pytest.fixture
def mock_requests_response():
    """Mock requests response for testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_access_token"}
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def test_log_file():
    """Create a test log file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_log:
        log_path = tmp_log.name
    
    yield log_path
    
    # Cleanup
    if os.path.exists(log_path):
        os.unlink(log_path)


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "spotify_api: marks tests that use Spotify API")
