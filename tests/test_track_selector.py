"""Tests for track selector functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.track_selector import TrackSelector


class TestTrackSelector:
    """Test cases for TrackSelector class."""

    @pytest.fixture
    def mock_spotify_client(self):
        """Create a mock Spotify client."""
        client = Mock()
        client.search_tracks.return_value = {
            "tracks": {
                "items": [
                    {
                        "id": "track1",
                        "name": "Test Track 1",
                        "artists": [{"name": "Artist 1"}],
                        "popularity": 80,
                        "explicit": False
                    },
                    {
                        "id": "track2",
                        "name": "Test Track 2",
                        "artists": [{"name": "Artist 2"}],
                        "popularity": 75,
                        "explicit": False
                    }
                ]
            }
        }
        return client

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "artist_caps": {
                "playlist1": 3,
                "playlist2": 2
            },
            "seeding": {
                "playlist1": ["Artist 1", "Artist 2"],
                "playlist2": ["Artist 3"]
            },
            "filters": {
                "min_popularity": 50,
                "max_explicit": False,
                "preferred_genres": ["pop", "rock"]
            }
        }

    @pytest.fixture
    def track_selector(self, mock_spotify_client, sample_config):
        """Create a TrackSelector instance for testing."""
        return TrackSelector(mock_spotify_client, sample_config)

    def test_init(self, track_selector, mock_spotify_client, sample_config):
        """Test TrackSelector initialization."""
        assert track_selector.spotify_client == mock_spotify_client
        assert track_selector.config == sample_config

    def test_select_tracks_for_playlist_success(self, track_selector, mock_spotify_client):
        """Test successful track selection for playlist."""
        playlist_type = "playlist1"
        target_size = 10
        
        tracks = track_selector.select_tracks_for_playlist(playlist_type, target_size)
        
        assert isinstance(tracks, list)
        assert len(tracks) <= target_size
        mock_spotify_client.search_tracks.assert_called()

    def test_select_tracks_for_playlist_empty_result(self, track_selector, mock_spotify_client):
        """Test track selection with empty search results."""
        mock_spotify_client.search_tracks.return_value = {"tracks": {"items": []}}
        
        tracks = track_selector.select_tracks_for_playlist("playlist1", 10)
        
        assert tracks == []

    def test_search_tracks_by_artist_success(self, track_selector, mock_spotify_client):
        """Test successful track search by artist."""
        artist = "Test Artist"
        limit = 5
        
        tracks = track_selector._search_tracks_by_artist(artist, limit)
        
        assert isinstance(tracks, list)
        assert len(tracks) <= limit
        mock_spotify_client.search_tracks.assert_called_with(f"artist:{artist}", limit=limit)

    def test_search_tracks_by_artist_no_results(self, track_selector, mock_spotify_client):
        """Test track search by artist with no results."""
        mock_spotify_client.search_tracks.return_value = {"tracks": {"items": []}}
        
        tracks = track_selector._search_tracks_by_artist("Unknown Artist", 5)
        
        assert tracks == []

    def test_filter_tracks_by_popularity(self, track_selector):
        """Test track filtering by popularity."""
        tracks = [
            {"popularity": 90, "name": "Popular Track"},
            {"popularity": 30, "name": "Unpopular Track"},
            {"popularity": 70, "name": "Medium Track"}
        ]
        
        filtered = track_selector._filter_tracks_by_popularity(tracks, min_popularity=50)
        
        assert len(filtered) == 2
        assert filtered[0]["name"] == "Popular Track"
        assert filtered[1]["name"] == "Medium Track"

    def test_filter_tracks_by_explicit(self, track_selector):
        """Test track filtering by explicit content."""
        tracks = [
            {"explicit": False, "name": "Clean Track"},
            {"explicit": True, "name": "Explicit Track"},
            {"explicit": False, "name": "Another Clean Track"}
        ]
        
        filtered = track_selector._filter_tracks_by_explicit(tracks, max_explicit=False)
        
        assert len(filtered) == 2
        assert filtered[0]["name"] == "Clean Track"
        assert filtered[1]["name"] == "Another Clean Track"

    def test_apply_artist_caps(self, track_selector):
        """Test artist cap application."""
        tracks = [
            {"artists": [{"name": "Artist 1"}], "name": "Track 1"},
            {"artists": [{"name": "Artist 1"}], "name": "Track 2"},
            {"artists": [{"name": "Artist 1"}], "name": "Track 3"},
            {"artists": [{"name": "Artist 2"}], "name": "Track 4"},
            {"artists": [{"name": "Artist 2"}], "name": "Track 5"}
        ]
        
        capped = track_selector._apply_artist_caps(tracks, max_per_artist=2)
        
        # Should have at most 2 tracks per artist
        artist_counts = {}
        for track in capped:
            artist_name = track["artists"][0]["name"]
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
        
        assert all(count <= 2 for count in artist_counts.values())

    def test_deduplicate_tracks(self, track_selector):
        """Test track deduplication."""
        tracks = [
            {"id": "track1", "name": "Track 1"},
            {"id": "track2", "name": "Track 2"},
            {"id": "track1", "name": "Track 1 Duplicate"},
            {"id": "track3", "name": "Track 3"}
        ]
        
        deduplicated = track_selector._deduplicate_tracks(tracks)
        
        assert len(deduplicated) == 3
        track_ids = [track["id"] for track in deduplicated]
        assert len(set(track_ids)) == 3

    def test_score_tracks(self, track_selector):
        """Test track scoring functionality."""
        tracks = [
            {"popularity": 90, "name": "High Popularity"},
            {"popularity": 50, "name": "Medium Popularity"},
            {"popularity": 30, "name": "Low Popularity"}
        ]
        
        scored = track_selector._score_tracks(tracks)
        
        assert len(scored) == 3
        # Should be sorted by score (popularity in this case)
        assert scored[0]["popularity"] >= scored[1]["popularity"]
        assert scored[1]["popularity"] >= scored[2]["popularity"]

    def test_get_seeding_artists(self, track_selector):
        """Test seeding artists retrieval."""
        playlist_type = "playlist1"
        
        artists = track_selector._get_seeding_artists(playlist_type)
        
        assert artists == ["Artist 1", "Artist 2"]

    def test_get_seeding_artists_not_found(self, track_selector):
        """Test seeding artists retrieval for unknown playlist."""
        artists = track_selector._get_seeding_artists("unknown_playlist")
        
        assert artists == []

    def test_get_artist_cap(self, track_selector):
        """Test artist cap retrieval."""
        playlist_type = "playlist1"
        
        cap = track_selector._get_artist_cap(playlist_type)
        
        assert cap == 3

    def test_get_artist_cap_default(self, track_selector):
        """Test artist cap retrieval with default value."""
        cap = track_selector._get_artist_cap("unknown_playlist")
        
        assert cap == 5  # Default value

    def test_validate_track(self, track_selector):
        """Test track validation."""
        valid_track = {
            "id": "track1",
            "name": "Valid Track",
            "artists": [{"name": "Artist 1"}],
            "popularity": 70,
            "explicit": False
        }
        
        assert track_selector._validate_track(valid_track) is True

    def test_validate_track_invalid(self, track_selector):
        """Test track validation with invalid track."""
        invalid_track = {
            "id": "track1",
            "name": "Invalid Track",
            # Missing required fields
        }
        
        assert track_selector._validate_track(invalid_track) is False

    def test_error_handling_search_failure(self, track_selector, mock_spotify_client):
        """Test error handling for search failures."""
        mock_spotify_client.search_tracks.side_effect = Exception("Search failed")
        
        tracks = track_selector.select_tracks_for_playlist("playlist1", 10)
        
        assert tracks == []

    def test_error_handling_api_error(self, track_selector, mock_spotify_client):
        """Test error handling for API errors."""
        mock_spotify_client.search_tracks.return_value = None
        
        tracks = track_selector.select_tracks_for_playlist("playlist1", 10)
        
        assert tracks == []

    def test_diverse_track_selection(self, track_selector):
        """Test diverse track selection algorithm."""
        # Mock multiple artists
        mock_spotify_client = track_selector.spotify_client
        mock_spotify_client.search_tracks.side_effect = [
            {"tracks": {"items": [{"id": f"track{i}", "artists": [{"name": f"Artist {i}"}]}]}}
            for i in range(1, 6)
        ]
        
        tracks = track_selector.select_tracks_for_playlist("playlist1", 5)
        
        assert len(tracks) <= 5
        # Should have tracks from different artists
        artist_names = [track["artists"][0]["name"] for track in tracks]
        assert len(set(artist_names)) > 1

    def test_playlist_size_limits(self, track_selector):
        """Test playlist size limit enforcement."""
        tracks = track_selector.select_tracks_for_playlist("playlist1", 0)
        
        assert tracks == []

    def test_config_validation(self, track_selector):
        """Test configuration validation."""
        # Test with valid config
        assert track_selector._validate_config() is True
        
        # Test with invalid config
        track_selector.config = None
        assert track_selector._validate_config() is False

    def test_track_metadata_extraction(self, track_selector):
        """Test track metadata extraction."""
        track = {
            "id": "track1",
            "name": "Test Track",
            "artists": [{"name": "Artist 1"}],
            "album": {"name": "Test Album"},
            "duration_ms": 180000,
            "popularity": 75
        }
        
        metadata = track_selector._extract_track_metadata(track)
        
        assert metadata["id"] == "track1"
        assert metadata["name"] == "Test Track"
        assert metadata["artist"] == "Artist 1"
        assert metadata["album"] == "Test Album"
        assert metadata["duration"] == 180000
        assert metadata["popularity"] == 75

    @patch('app.track_selector.random')
    def test_randomized_selection(self, mock_random, track_selector):
        """Test randomized track selection."""
        mock_random.shuffle.return_value = None
        
        tracks = [
            {"id": "track1", "name": "Track 1"},
            {"id": "track2", "name": "Track 2"},
            {"id": "track3", "name": "Track 3"}
        ]
        
        selected = track_selector._randomize_selection(tracks, 2)
        
        assert len(selected) == 2
        mock_random.shuffle.assert_called_once()

    def test_genre_based_filtering(self, track_selector):
        """Test genre-based track filtering."""
        tracks = [
            {"genres": ["pop", "dance"], "name": "Pop Track"},
            {"genres": ["rock", "alternative"], "name": "Rock Track"},
            {"genres": ["jazz"], "name": "Jazz Track"}
        ]
        
        filtered = track_selector._filter_tracks_by_genre(tracks, ["pop", "rock"])
        
        assert len(filtered) == 2
        assert filtered[0]["name"] == "Pop Track"
        assert filtered[1]["name"] == "Rock Track"
