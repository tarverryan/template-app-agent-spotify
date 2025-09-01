"""Tests for Spotify client functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.spotify_client import SpotifyClient


class TestSpotifyClient:
    """Test cases for SpotifyClient class."""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Mock environment variables."""
        env_vars = {
            "SPOTIFY_CLIENT_ID": "test_client_id",
            "SPOTIFY_CLIENT_SECRET": "test_client_secret",
            "SPOTIFY_REFRESH_TOKEN": "test_refresh_token",
            "SPOTIFY_USER_ID": "test_user_id"
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    @pytest.fixture
    def spotify_client(self, mock_env_vars):
        """Create a SpotifyClient instance for testing."""
        return SpotifyClient()

    def test_init_with_valid_credentials(self, mock_env_vars):
        """Test client initialization with valid credentials."""
        client = SpotifyClient()
        assert client.client_id == "test_client_id"
        assert client.client_secret == "test_client_secret"
        assert client.refresh_token == "test_refresh_token"
        assert client.user_id == "test_user_id"

    def test_init_with_missing_credentials(self, monkeypatch):
        """Test client initialization with missing credentials."""
        # Clear all environment variables
        for key in ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN", "SPOTIFY_USER_ID"]:
            monkeypatch.delenv(key, raising=False)
        
        with pytest.raises(ValueError, match="Missing required Spotify environment variables"):
            SpotifyClient()

    @patch('app.spotify_client.requests.post')
    def test_refresh_access_token_success(self, mock_post, spotify_client):
        """Test successful access token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        result = spotify_client.refresh_access_token()
        
        assert result == "new_access_token"
        assert spotify_client.access_token == "new_access_token"
        mock_post.assert_called_once()

    @patch('app.spotify_client.requests.post')
    def test_refresh_access_token_failure(self, mock_post, spotify_client):
        """Test access token refresh failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="Bad Request"):
            spotify_client.refresh_access_token()

    @patch('app.spotify_client.requests.get')
    def test_get_user_playlists_success(self, mock_get, spotify_client):
        """Test successful user playlists retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"id": "playlist1", "name": "Test Playlist 1"},
                {"id": "playlist2", "name": "Test Playlist 2"}
            ]
        }
        mock_get.return_value = mock_response

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.get_user_playlists()
        
        assert len(result["items"]) == 2
        assert result["items"][0]["name"] == "Test Playlist 1"
        mock_get.assert_called_once()

    @patch('app.spotify_client.requests.get')
    def test_get_playlist_tracks_success(self, mock_get, spotify_client):
        """Test successful playlist tracks retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"track": {"id": "track1", "name": "Test Track 1"}},
                {"track": {"id": "track2", "name": "Test Track 2"}}
            ]
        }
        mock_get.return_value = mock_response

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.get_playlist_tracks("test_playlist_id")
        
        assert len(result["items"]) == 2
        assert result["items"][0]["track"]["name"] == "Test Track 1"
        mock_get.assert_called_once()

    @patch('app.spotify_client.requests.get')
    def test_search_tracks_success(self, mock_get, spotify_client):
        """Test successful track search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tracks": {
                "items": [
                    {"id": "search_track1", "name": "Search Track 1"}
                ]
            }
        }
        mock_get.return_value = mock_response

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.search_tracks("test query")
        
        assert len(result["tracks"]["items"]) == 1
        assert result["tracks"]["items"][0]["name"] == "Search Track 1"
        mock_get.assert_called_once()

    @patch('app.spotify_client.requests.post')
    def test_add_tracks_to_playlist_success(self, mock_post, spotify_client):
        """Test successful track addition to playlist."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.add_tracks_to_playlist("test_playlist_id", ["track1", "track2"])
        
        assert result is True
        mock_post.assert_called_once()

    @patch('app.spotify_client.requests.put')
    def test_replace_playlist_tracks_success(self, mock_put, spotify_client):
        """Test successful playlist track replacement."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_put.return_value = mock_response

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.replace_playlist_tracks("test_playlist_id", ["track1", "track2"])
        
        assert result is True
        mock_put.assert_called_once()

    @patch('app.spotify_client.requests.put')
    def test_update_playlist_cover_success(self, mock_put, spotify_client):
        """Test successful playlist cover update."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_put.return_value = mock_response

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.update_playlist_cover("test_playlist_id", "base64_image_data")
        
        assert result is True
        mock_put.assert_called_once()

    def test_get_headers(self, spotify_client):
        """Test header generation."""
        spotify_client.access_token = "test_token"
        headers = spotify_client._get_headers()
        
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"

    @patch('app.spotify_client.requests.post')
    def test_handle_rate_limit(self, mock_post, spotify_client):
        """Test rate limit handling."""
        # First call returns rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}
        
        # Second call succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"access_token": "new_token"}
        
        mock_post.side_effect = [rate_limit_response, success_response]

        # Mock access token
        spotify_client.access_token = "test_token"

        result = spotify_client.refresh_access_token()
        
        assert result == "new_token"
        assert mock_post.call_count == 2
