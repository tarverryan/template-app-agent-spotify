"""Tests for playlist manager functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.playlist_manager import PlaylistManager


class TestPlaylistManager:
    """Test cases for PlaylistManager class."""

    @pytest.fixture
    def mock_spotify_client(self):
        """Create a mock Spotify client."""
        client = Mock()
        client.get_user_playlists.return_value = {
            "items": [
                {"id": "playlist1", "name": "Test Playlist 1"},
                {"id": "playlist2", "name": "Test Playlist 2"}
            ]
        }
        client.get_playlist_tracks.return_value = {
            "items": [
                {"track": {"id": "track1", "name": "Test Track 1", "artists": [{"name": "Artist 1"}]}},
                {"track": {"id": "track2", "name": "Test Track 2", "artists": [{"name": "Artist 2"}]}}
            ]
        }
        return client

    @pytest.fixture
    def playlist_manager(self, mock_spotify_client):
        """Create a PlaylistManager instance for testing."""
        return PlaylistManager(mock_spotify_client)

    def test_init(self, playlist_manager, mock_spotify_client):
        """Test PlaylistManager initialization."""
        assert playlist_manager.spotify_client == mock_spotify_client
        assert playlist_manager.db_path is not None

    def test_get_playlist_id_success(self, playlist_manager):
        """Test successful playlist ID retrieval."""
        playlist_id = playlist_manager.get_playlist_id("playlist1")
        assert playlist_id == "playlist1"

    def test_get_playlist_id_not_found(self, playlist_manager):
        """Test playlist ID retrieval when not found."""
        with pytest.raises(ValueError, match="Playlist 'nonexistent' not found"):
            playlist_manager.get_playlist_id("nonexistent")

    def test_get_playlist_tracks_success(self, playlist_manager, mock_spotify_client):
        """Test successful playlist tracks retrieval."""
        tracks = playlist_manager.get_playlist_tracks("playlist1")
        
        assert len(tracks) == 2
        assert tracks[0]["name"] == "Test Track 1"
        assert tracks[1]["name"] == "Test Track 2"
        mock_spotify_client.get_playlist_tracks.assert_called_once_with("playlist1")

    def test_get_playlist_tracks_empty(self, playlist_manager, mock_spotify_client):
        """Test playlist tracks retrieval for empty playlist."""
        mock_spotify_client.get_playlist_tracks.return_value = {"items": []}
        
        tracks = playlist_manager.get_playlist_tracks("playlist1")
        
        assert tracks == []
        mock_spotify_client.get_playlist_tracks.assert_called_once_with("playlist1")

    def test_add_tracks_to_playlist_success(self, playlist_manager, mock_spotify_client):
        """Test successful track addition to playlist."""
        track_ids = ["track1", "track2", "track3"]
        
        result = playlist_manager.add_tracks_to_playlist("playlist1", track_ids)
        
        assert result is True
        mock_spotify_client.add_tracks_to_playlist.assert_called_once_with("playlist1", track_ids)

    def test_add_tracks_to_playlist_empty(self, playlist_manager, mock_spotify_client):
        """Test track addition with empty track list."""
        result = playlist_manager.add_tracks_to_playlist("playlist1", [])
        
        assert result is True
        mock_spotify_client.add_tracks_to_playlist.assert_not_called()

    def test_replace_playlist_tracks_success(self, playlist_manager, mock_spotify_client):
        """Test successful playlist track replacement."""
        track_ids = ["track1", "track2", "track3"]
        
        result = playlist_manager.replace_playlist_tracks("playlist1", track_ids)
        
        assert result is True
        mock_spotify_client.replace_playlist_tracks.assert_called_once_with("playlist1", track_ids)

    def test_update_playlist_cover_success(self, playlist_manager, mock_spotify_client):
        """Test successful playlist cover update."""
        image_data = "base64_encoded_image_data"
        
        result = playlist_manager.update_playlist_cover("playlist1", image_data)
        
        assert result is True
        mock_spotify_client.update_playlist_cover.assert_called_once_with("playlist1", image_data)

    def test_log_playlist_update_success(self, playlist_manager):
        """Test successful playlist update logging."""
        playlist_type = "playlist1"
        track_count = 25
        success = True
        
        result = playlist_manager.log_playlist_update(playlist_type, track_count, success)
        
        assert result is True

    def test_log_playlist_update_failure(self, playlist_manager):
        """Test playlist update logging for failed updates."""
        playlist_type = "playlist1"
        track_count = 0
        success = False
        
        result = playlist_manager.log_playlist_update(playlist_type, track_count, success)
        
        assert result is True

    def test_get_playlist_update_history(self, playlist_manager):
        """Test playlist update history retrieval."""
        history = playlist_manager.get_playlist_update_history("playlist1", limit=5)
        
        # Should return a list (even if empty)
        assert isinstance(history, list)

    def test_get_playlist_statistics(self, playlist_manager):
        """Test playlist statistics retrieval."""
        stats = playlist_manager.get_playlist_statistics("playlist1")
        
        # Should return a dictionary with statistics
        assert isinstance(stats, dict)
        assert "total_updates" in stats
        assert "successful_updates" in stats
        assert "failed_updates" in stats

    @patch('app.playlist_manager.sqlite3.connect')
    def test_database_operations(self, mock_connect, playlist_manager):
        """Test database operations."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Test logging
        playlist_manager.log_playlist_update("playlist1", 10, True)
        
        # Verify database operations were called
        mock_connect.assert_called()
        mock_cursor.execute.assert_called()

    def test_validate_playlist_id_valid(self, playlist_manager):
        """Test playlist ID validation with valid ID."""
        result = playlist_manager.validate_playlist_id("playlist1")
        assert result is True

    def test_validate_playlist_id_invalid(self, playlist_manager):
        """Test playlist ID validation with invalid ID."""
        result = playlist_manager.validate_playlist_id("invalid_playlist")
        assert result is False

    def test_get_playlist_info_success(self, playlist_manager, mock_spotify_client):
        """Test successful playlist info retrieval."""
        mock_spotify_client.get_playlist.return_value = {
            "id": "playlist1",
            "name": "Test Playlist 1",
            "description": "A test playlist",
            "tracks": {"total": 25}
        }
        
        info = playlist_manager.get_playlist_info("playlist1")
        
        assert info["name"] == "Test Playlist 1"
        assert info["description"] == "A test playlist"
        mock_spotify_client.get_playlist.assert_called_once_with("playlist1")

    def test_get_playlist_info_not_found(self, playlist_manager, mock_spotify_client):
        """Test playlist info retrieval for non-existent playlist."""
        mock_spotify_client.get_playlist.side_effect = Exception("Playlist not found")
        
        with pytest.raises(Exception, match="Playlist not found"):
            playlist_manager.get_playlist_info("nonexistent")

    def test_batch_operations(self, playlist_manager, mock_spotify_client):
        """Test batch operations for multiple playlists."""
        playlists = ["playlist1", "playlist2"]
        track_ids = ["track1", "track2"]
        
        # Test batch add
        results = playlist_manager.batch_add_tracks(playlists, track_ids)
        
        assert len(results) == 2
        assert all(result is True for result in results)
        assert mock_spotify_client.add_tracks_to_playlist.call_count == 2

    def test_error_handling_network_error(self, playlist_manager, mock_spotify_client):
        """Test error handling for network errors."""
        mock_spotify_client.get_playlist_tracks.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            playlist_manager.get_playlist_tracks("playlist1")

    def test_error_handling_api_error(self, playlist_manager, mock_spotify_client):
        """Test error handling for API errors."""
        mock_spotify_client.add_tracks_to_playlist.return_value = False
        
        result = playlist_manager.add_tracks_to_playlist("playlist1", ["track1"])
        
        assert result is False

    @patch('app.playlist_manager.time')
    def test_rate_limiting(self, mock_time, playlist_manager, mock_spotify_client):
        """Test rate limiting functionality."""
        # Mock time to control rate limiting
        mock_time.time.return_value = 1000.0
        
        # Multiple rapid calls should be rate limited
        for _ in range(3):
            playlist_manager.get_playlist_tracks("playlist1")
        
        # Should have called the API multiple times
        assert mock_spotify_client.get_playlist_tracks.call_count == 3

    def test_playlist_metadata_operations(self, playlist_manager, mock_spotify_client):
        """Test playlist metadata operations."""
        # Test updating playlist name
        result = playlist_manager.update_playlist_name("playlist1", "New Name")
        assert result is True
        
        # Test updating playlist description
        result = playlist_manager.update_playlist_description("playlist1", "New description")
        assert result is True
        
        # Test making playlist public/private
        result = playlist_manager.set_playlist_public("playlist1", True)
        assert result is True

    def test_playlist_analysis(self, playlist_manager):
        """Test playlist analysis functionality."""
        # Test getting playlist diversity
        diversity = playlist_manager.get_playlist_diversity("playlist1")
        assert isinstance(diversity, float)
        assert 0.0 <= diversity <= 1.0
        
        # Test getting most common artists
        artists = playlist_manager.get_most_common_artists("playlist1", limit=5)
        assert isinstance(artists, list)
        
        # Test getting playlist mood analysis
        mood = playlist_manager.get_playlist_mood("playlist1")
        assert isinstance(mood, dict)
