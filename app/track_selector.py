"""
Enhanced Track Selection Logic with Date-Based Filtering
Implements previous day, previous week, month-to-date, and year-to-date logic.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from .spotify_client import SpotifyClient

logger = logging.getLogger(__name__)

class TrackSelector:
    """Enhanced track selector with date-based filtering and period-specific logic."""
    
    def __init__(self, spotify_client: SpotifyClient, config: Dict[str, Any]):
        self.spotify_client = spotify_client
        self.config = config
        self.genres = config.get('genres', {}).get('buckets', {})
        self.scoring_weights = config.get('scoring', {}).get('weights', {})
        self.territory_weighting = config.get('selection', {}).get('territory_weighting', {})
        self.date_filtering = config.get('selection', {}).get('date_filtering', {})
        
    def discover_tracks_for_period(self, playlist_type: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Discover tracks based on the specific playlist type and period."""
        tracks = []
        
        if playlist_type == 'previous_day':
            tracks = self._discover_previous_day_tracks(limit)
        elif playlist_type == 'previous_week':
            tracks = self._discover_previous_week_tracks(limit)
        elif playlist_type == 'month_to_date':
            tracks = self._discover_month_to_date_tracks(limit)
        elif playlist_type == 'year_to_date':
            tracks = self._discover_year_to_date_tracks(limit)
        else:
            tracks = self._discover_general_tracks(limit)
        
        # Remove duplicates
        seen_ids = set()
        unique_tracks = []
        for track in tracks:
            if track['id'] not in seen_ids:
                seen_ids.add(track['id'])
                unique_tracks.append(track)
        
        logger.info(f"Discovered {len(unique_tracks)} unique tracks for {playlist_type}")
        return unique_tracks[:limit]
    
    def _discover_previous_day_tracks(self, limit: int) -> List[Dict[str, Any]]:
        """Discover tracks from the previous day (last 24 hours)."""
        logger.info("Discovering tracks from previous day...")
        tracks = []
        
        # Get new releases from yesterday
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        # Search for tracks released yesterday
        new_releases = self.spotify_client.get_new_releases(country='US', limit=50)
        for album in new_releases:
            if album.get('release_date') == yesterday_str:
                album_tracks = self.spotify_client.search_tracks(
                    f"album:{album['name']} artist:{album['artists'][0]['name']}", 
                    limit=20
                )
                tracks.extend(album_tracks)
        
        # Search for trending tracks (popular in last 24 hours)
        for genre_bucket, genre_terms in self.genres.items():
            for genre in genre_terms[:2]:  # Top 2 terms per bucket
                # Search for popular tracks with recent activity
                genre_tracks = self.spotify_client.search_tracks(
                    f"genre:{genre} year:2025", 
                    limit=15
                )
                tracks.extend(genre_tracks)
        
        return tracks
    
    def _discover_previous_week_tracks(self, limit: int) -> List[Dict[str, Any]]:
        """Discover tracks from the previous week (last 7 days)."""
        logger.info("Discovering tracks from previous week...")
        tracks = []
        
        # Get new releases from last week
        week_ago = datetime.now() - timedelta(days=7)
        
        new_releases = self.spotify_client.get_new_releases(country='US', limit=50)
        for album in new_releases:
            try:
                release_date = datetime.strptime(album.get('release_date', ''), '%Y-%m-%d')
                if release_date >= week_ago:
                    album_tracks = self.spotify_client.search_tracks(
                        f"album:{album['name']} artist:{album['artists'][0]['name']}", 
                        limit=15
                    )
                    tracks.extend(album_tracks)
            except:
                continue
        
        # Search for popular tracks by genre from last week
        for genre_bucket, genre_terms in self.genres.items():
            for genre in genre_terms[:3]:  # Top 3 terms per bucket
                genre_tracks = self.spotify_client.search_tracks(
                    f"genre:{genre} year:2025", 
                    limit=20
                )
                tracks.extend(genre_tracks)
        
        return tracks
    
    def _discover_month_to_date_tracks(self, limit: int) -> List[Dict[str, Any]]:
        """Discover tracks from the current month (month-to-date)."""
        logger.info("Discovering month-to-date tracks...")
        tracks = []
        
        # Get current month start date
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        # Get new releases from this month
        new_releases = self.spotify_client.get_new_releases(country='US', limit=50)
        for album in new_releases:
            try:
                release_date = datetime.strptime(album.get('release_date', ''), '%Y-%m-%d')
                if release_date >= month_start:
                    album_tracks = self.spotify_client.search_tracks(
                        f"album:{album['name']} artist:{album['artists'][0]['name']}", 
                        limit=10
                    )
                    tracks.extend(album_tracks)
            except:
                continue
        
        # Search for popular tracks by genre from this month
        for genre_bucket, genre_terms in self.genres.items():
            for genre in genre_terms[:3]:  # Top 3 terms per bucket
                genre_tracks = self.spotify_client.search_tracks(
                    f"genre:{genre} year:2025", 
                    limit=25
                )
                tracks.extend(genre_tracks)
        
        return tracks
    
    def _discover_year_to_date_tracks(self, limit: int) -> List[Dict[str, Any]]:
        """Discover tracks from the current year (year-to-date)."""
        logger.info("Discovering year-to-date tracks...")
        tracks = []
        
        # Get current year start date
        now = datetime.now()
        year_start = datetime(now.year, 1, 1)
        
        # Get new releases from this year
        new_releases = self.spotify_client.get_new_releases(country='US', limit=50)
        for album in new_releases:
            try:
                release_date = datetime.strptime(album.get('release_date', ''), '%Y-%m-%d')
                if release_date >= year_start:
                    album_tracks = self.spotify_client.search_tracks(
                        f"album:{album['name']} artist:{album['artists'][0]['name']}", 
                        limit=8
                    )
                    tracks.extend(album_tracks)
            except:
                continue
        
        # Search for popular tracks by genre from this year
        for genre_bucket, genre_terms in self.genres.items():
            for genre in genre_terms[:3]:  # Top 3 terms per bucket
                genre_tracks = self.spotify_client.search_tracks(
                    f"genre:{genre} year:2025", 
                    limit=30
                )
                tracks.extend(genre_tracks)
        
        return tracks
    
    def _discover_general_tracks(self, limit: int) -> List[Dict[str, Any]]:
        """Fallback general track discovery."""
        logger.info("Discovering general tracks...")
        tracks = []
        
        # Get new releases
        new_releases = self.spotify_client.get_new_releases(country='US', limit=50)
        for album in new_releases:
            album_tracks = self.spotify_client.search_tracks(
                f"album:{album['name']} artist:{album['artists'][0]['name']}", 
                limit=20
            )
            tracks.extend(album_tracks)
        
        # Search for popular tracks by genre
        for genre_bucket, genre_terms in self.genres.items():
            for genre in genre_terms[:3]:  # Top 3 terms per bucket
                genre_tracks = self.spotify_client.search_tracks(
                    f"genre:{genre} year:2025", 
                    limit=20
                )
                tracks.extend(genre_tracks)
        
        return tracks
    
    def calculate_track_scores(self, tracks: List[Dict[str, Any]], 
                             previous_snapshot: Optional[Dict[str, Any]] = None,
                             playlist_type: str = 'general') -> List[Dict[str, Any]]:
        """Calculate scores for tracks with period-specific weighting."""
        if not tracks:
            return []
        
        scored_tracks = []
        for track in tracks:
            # Calculate popularity score
            popularity = track.get('popularity', 0) / 100.0
            
            # Calculate popularity delta
            popularity_delta = 0.0
            if previous_snapshot and isinstance(previous_snapshot, dict):
                tracks_list = previous_snapshot.get('tracks', [])
                if isinstance(tracks_list, list):
                    prev_track = next((t for t in tracks_list 
                                     if t.get('id') == track['id']), None)
                    if prev_track:
                        prev_popularity = prev_track.get('popularity', 0) / 100.0
                        popularity_delta = popularity - prev_popularity
            
            # Calculate recency boost based on playlist type
            release_date = track['album'].get('release_date', '')
            recency_boost = 0.0
            if release_date:
                try:
                    release_dt = datetime.strptime(release_date, '%Y-%m-%d')
                    days_old = (datetime.now() - release_dt).days
                    
                    # Adjust recency boost based on playlist type
                    if playlist_type == 'daily' and days_old <= 1:
                        recency_boost = 0.15  # Higher boost for daily
                    elif playlist_type == 'weekly' and days_old <= 7:
                        recency_boost = 0.12  # Medium boost for weekly
                    elif playlist_type == 'monthly' and days_old <= 30:
                        recency_boost = 0.10  # Standard boost for monthly
                    elif playlist_type == 'yearly' and days_old <= 365:
                        recency_boost = 0.08  # Lower boost for yearly
                        
                except:
                    pass
            
            # Apply period-specific scoring
            weights = self.scoring_weights.copy()
            if playlist_type == 'daily':
                weights['recency_boost'] = 0.20  # Emphasize recency for daily
                weights['popularity'] = 0.50
            elif playlist_type == 'weekly':
                weights['recency_boost'] = 0.15  # Medium recency for weekly
                weights['popularity'] = 0.55
            elif playlist_type == 'monthly':
                weights['recency_boost'] = 0.10  # Standard recency for monthly
                weights['popularity'] = 0.55
            elif playlist_type == 'yearly':
                weights['recency_boost'] = 0.08  # Lower recency for yearly
                weights['popularity'] = 0.60  # Emphasize overall popularity
            
            # Calculate final score
            score = (
                weights.get('popularity', 0.55) * popularity +
                weights.get('popularity_delta', 0.30) * popularity_delta +
                weights.get('recency_boost', 0.10) * recency_boost +
                0.05 * 0.5  # Default audio feature fit
            )
            
            track['score'] = score
            scored_tracks.append(track)
        
        # Sort by score
        scored_tracks.sort(key=lambda x: x['score'], reverse=True)
        return scored_tracks
    
    def apply_artist_caps(self, tracks: List[Dict[str, Any]], artist_cap: int) -> List[Dict[str, Any]]:
        """Apply artist caps to limit tracks per artist."""
        if not tracks:
            return []
        
        artist_counts = {}
        capped_tracks = []
        
        for track in tracks:
            artist_id = track['artists'][0]['id']
            if artist_id not in artist_counts:
                artist_counts[artist_id] = 0
            
            if artist_counts[artist_id] < artist_cap:
                artist_counts[artist_id] += 1
                capped_tracks.append(track)
        
        logger.info(f"Applied artist cap {artist_cap}: {len(tracks)} -> {len(capped_tracks)} tracks")
        return capped_tracks
    
    def dedupe_tracks(self, tracks: List[Dict[str, Any]], 
                     existing_tracks: List[Dict[str, Any]], 
                     dedupe_days: int) -> List[Dict[str, Any]]:
        """Remove tracks that exist in recent playlists."""
        if not existing_tracks:
            return tracks
        
        # Create set of existing track IDs
        existing_ids = set()
        for track in existing_tracks:
            if track and 'track' in track and track['track'] and 'id' in track['track']:
                existing_ids.add(track['track']['id'])
        
        # Filter out existing tracks
        new_tracks = [track for track in tracks if track['id'] not in existing_ids]
        
        logger.info(f"Deduplication: {len(tracks)} -> {len(new_tracks)} tracks")
        return new_tracks
    
    def apply_genre_allocation(self, tracks: List[Dict[str, Any]], 
                             target_size: int,
                             diversity_floor_pct: Optional[int] = None) -> List[Dict[str, Any]]:
        """Apply genre allocation to ensure diversity."""
        if not tracks:
            return []
        
        # Count tracks by genre
        genre_counts = {}
        for track in tracks:
            genre = track.get('genre', 'Other')
            if genre not in genre_counts:
                genre_counts[genre] = []
            genre_counts[genre].append(track)
        
        # Calculate allocation
        total_tracks = len(tracks)
        allocated_tracks = []
        
        if diversity_floor_pct:
            # Apply diversity floor (for yearly playlists)
            floor_count = max(1, int(target_size * diversity_floor_pct / 100))
            
            for genre, genre_tracks in genre_counts.items():
                # Ensure minimum representation
                min_tracks = min(floor_count, len(genre_tracks))
                allocated_tracks.extend(genre_tracks[:min_tracks])
                
                # Remove allocated tracks
                genre_counts[genre] = genre_tracks[min_tracks:]
        else:
            # For daily/weekly playlists, use a more lenient approach
            # Take top tracks from each genre, ensuring we get close to target size
            available_tracks = sum(len(tracks) for tracks in genre_counts.values())
            
            if available_tracks <= target_size:
                # If we have fewer tracks than target, take all of them
                for genre_tracks in genre_counts.values():
                    allocated_tracks.extend(genre_tracks)
            else:
                # Distribute tracks more evenly across genres
                genres = list(genre_counts.keys())
                tracks_per_genre = max(1, target_size // len(genres))
                
                for genre, genre_tracks in genre_counts.items():
                    # Take top tracks from each genre
                    allocated_tracks.extend(genre_tracks[:tracks_per_genre])
                
                # If we still have room, fill with highest scoring tracks
                if len(allocated_tracks) < target_size:
                    remaining_tracks = []
                    for genre_tracks in genre_counts.values():
                        remaining_tracks.extend(genre_tracks[tracks_per_genre:])
                    
                    # Sort remaining tracks by score and add until we reach target
                    remaining_tracks.sort(key=lambda x: x['score'], reverse=True)
                    needed = target_size - len(allocated_tracks)
                    allocated_tracks.extend(remaining_tracks[:needed])
        
        # Sort by score and limit to target size
        allocated_tracks.sort(key=lambda x: x['score'], reverse=True)
        return allocated_tracks[:target_size]
    
    def select_tracks_for_playlist(self, playlist_type: str, target_size: int) -> List[Dict[str, Any]]:
        """Select tracks for a playlist (simplified for tests)."""
        try:
            # Get seeding artists for this playlist type
            seeding_artists = self._get_seeding_artists(playlist_type)
            
            tracks = []
            for artist in seeding_artists:
                artist_tracks = self._search_tracks_by_artist(artist, limit=10)
                tracks.extend(artist_tracks)
            
            # Apply filters
            tracks = self._filter_tracks_by_popularity(tracks, min_popularity=50)
            tracks = self._filter_tracks_by_explicit(tracks, max_explicit=False)
            
            # Apply artist caps
            artist_cap = self._get_artist_cap(playlist_type)
            tracks = self._apply_artist_caps(tracks, max_per_artist=artist_cap)
            
            # Deduplicate
            tracks = self._deduplicate_tracks(tracks)
            
            # Score and sort
            tracks = self._score_tracks(tracks)
            
            return tracks[:target_size]
        except Exception as e:
            logger.error(f"Error selecting tracks for playlist {playlist_type}: {e}")
            return []
    
    def _search_tracks_by_artist(self, artist: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tracks by artist."""
        try:
            tracks = self.spotify_client.search_tracks(f"artist:{artist}", limit=limit)
            return tracks
        except Exception as e:
            logger.error(f"Error searching tracks for artist {artist}: {e}")
            return []
    
    def _filter_tracks_by_popularity(self, tracks: List[Dict[str, Any]], min_popularity: int = 50) -> List[Dict[str, Any]]:
        """Filter tracks by popularity."""
        return [track for track in tracks if track.get('popularity', 0) >= min_popularity]
    
    def _filter_tracks_by_explicit(self, tracks: List[Dict[str, Any]], max_explicit: bool = False) -> List[Dict[str, Any]]:
        """Filter tracks by explicit content."""
        if max_explicit:
            return tracks
        return [track for track in tracks if not track.get('explicit', False)]
    
    def _apply_artist_caps(self, tracks: List[Dict[str, Any]], max_per_artist: int = 3) -> List[Dict[str, Any]]:
        """Apply artist caps to limit tracks per artist."""
        artist_counts = {}
        capped_tracks = []
        
        for track in tracks:
            artist_name = track.get('artists', [{}])[0].get('name', 'Unknown')
            if artist_counts.get(artist_name, 0) < max_per_artist:
                capped_tracks.append(track)
                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
        
        return capped_tracks
    
    def _deduplicate_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate tracks by ID."""
        seen_ids = set()
        unique_tracks = []
        
        for track in tracks:
            track_id = track.get('id')
            if track_id and track_id not in seen_ids:
                seen_ids.add(track_id)
                unique_tracks.append(track)
        
        return unique_tracks
    
    def _score_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score tracks based on popularity."""
        for track in tracks:
            track['score'] = track.get('popularity', 0)
        
        return sorted(tracks, key=lambda x: x.get('score', 0), reverse=True)
    
    def _get_seeding_artists(self, playlist_type: str) -> List[str]:
        """Get seeding artists for playlist type."""
        seeding = self.config.get('seeding', {})
        return seeding.get(playlist_type, [])
    
    def _get_artist_cap(self, playlist_type: str) -> int:
        """Get artist cap for playlist type."""
        artist_caps = self.config.get('artist_caps', {})
        return artist_caps.get(playlist_type, 5)  # Default to 5
    
    def _validate_track(self, track: Dict[str, Any]) -> bool:
        """Validate track has required fields."""
        required_fields = ['id', 'name', 'artists']
        return all(field in track for field in required_fields)
    
    def _validate_config(self) -> bool:
        """Validate configuration."""
        return self.config is not None and isinstance(self.config, dict)
    
    def _extract_track_metadata(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Extract track metadata."""
        return {
            'id': track.get('id'),
            'name': track.get('name'),
            'artist': track.get('artists', [{}])[0].get('name', 'Unknown'),
            'album': track.get('album', {}).get('name', 'Unknown'),
            'duration': track.get('duration_ms', 0),
            'popularity': track.get('popularity', 0)
        }
    
    def _randomize_selection(self, tracks: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """Randomly select tracks."""
        import random
        if len(tracks) <= count:
            return tracks
        return random.sample(tracks, count)
    
    def _filter_tracks_by_genre(self, tracks: List[Dict[str, Any]], genres: List[str]) -> List[Dict[str, Any]]:
        """Filter tracks by genre."""
        # This is a simplified implementation since we don't have genre data
        return tracks
