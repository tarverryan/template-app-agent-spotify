"""
Spotify API Client for App Agent Template
Handles authentication, rate limiting, and API calls for the Spotify App Agent Template.
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class SpotifyClient:
    """Spotify API client with authentication and rate limiting."""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')
        self.user_id = os.getenv('SPOTIFY_USER_ID')
        
        if not all([self.client_id, self.client_secret, self.refresh_token, self.user_id]):
            raise ValueError("Missing required Spotify environment variables")
        
        self.access_token = None
        self.token_expires_at = 0
        self.base_url = "https://api.spotify.com/v1"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with current access token."""
        if not self.access_token or time.time() >= self.token_expires_at:
            self._refresh_access_token()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        try:
            response = requests.post('https://accounts.spotify.com/api/token', data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.token_expires_at = time.time() + data['expires_in'] - 60  # Buffer
                logger.info("Access token refreshed successfully")
                return self.access_token
            else:
                logger.error(f"Failed to refresh token: {response.text}")
                raise Exception("Token refresh failed")
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise
    
    def refresh_access_token(self):
        """Public method to refresh access token."""
        return self._refresh_access_token()
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a rate-limited API request with retries."""
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code == 429:  # Rate limited
            retry_after = int(response.headers.get('Retry-After', 60))
            logger.warning(f"Rate limited, waiting {retry_after} seconds")
            time.sleep(retry_after)
            raise Exception("Rate limited")
        
        if response.status_code >= 400:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        return response.json()
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        return self._make_request('GET', '/me')
    
    def create_playlist(self, name: str, description: str = "", public: bool = True) -> Dict[str, Any]:
        """Create a new playlist."""
        data = {
            'name': name,
            'description': description,
            'public': public
        }
        return self._make_request('POST', f'/users/{self.user_id}/playlists', json=data)
    
    def update_playlist(self, playlist_id: str, name: str = None, description: str = None, public: bool = None):
        """Update playlist details."""
        data = {}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        if public is not None:
            data['public'] = public
        
        if data:
            self._make_request('PUT', f'/playlists/{playlist_id}', json=data)
    
    def replace_playlist_tracks(self, playlist_id: str, track_uris: List[str]):
        """Replace all tracks in a playlist."""
        data = {'uris': track_uris}
        self._make_request('PUT', f'/playlists/{playlist_id}/tracks', json=data)
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]):
        """Add tracks to a playlist (append to existing tracks)."""
        # Spotify API has a limit of 100 tracks per request
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i+batch_size]
            data = {'uris': batch}
            self._make_request('POST', f'/playlists/{playlist_id}/tracks', json=data)
    
    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist details."""
        return self._make_request('GET', f'/playlists/{playlist_id}')
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tracks from a playlist."""
        tracks = []
        offset = 0
        
        while True:
            params = {'limit': limit, 'offset': offset}
            response = self._make_request('GET', f'/playlists/{playlist_id}/tracks', params=params)
            
            items = response.get('items', [])
            tracks.extend(items)
            
            if len(items) < limit:
                break
            
            offset += limit
        
        return tracks
    
    def get_user_playlists(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's playlists."""
        playlists = []
        offset = 0
        
        while True:
            params = {'limit': limit, 'offset': offset}
            response = self._make_request('GET', f'/users/{self.user_id}/playlists', params=params)
            
            items = response.get('items', [])
            playlists.extend(items)
            
            if len(items) < limit:
                break
            
            offset += limit
        
        return playlists
    
    def search_tracks(self, query: str, limit: int = 50, market: str = 'US') -> List[Dict[str, Any]]:
        """Search for tracks."""
        params = {
            'q': query,
            'type': 'track',
            'limit': limit,
            'market': market
        }
        response = self._make_request('GET', '/search', params=params)
        return response.get('tracks', {}).get('items', [])
    
    def get_track_audio_features(self, track_ids: List[str]) -> List[Dict[str, Any]]:
        """Get audio features for multiple tracks."""
        if not track_ids:
            return []
        
        # Spotify API allows max 100 tracks per request
        features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            params = {'ids': ','.join(batch)}
            response = self._make_request('GET', '/audio-features', params=params)
            features.extend(response.get('audio_features', []))
        
        return features
    
    def get_new_releases(self, country: str = 'US', limit: int = 50) -> List[Dict[str, Any]]:
        """Get new releases."""
        params = {
            'country': country,
            'limit': limit
        }
        response = self._make_request('GET', '/browse/new-releases', params=params)
        return response.get('albums', {}).get('items', [])
    
    def get_playlist_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a playlist by name."""
        playlists = self.get_user_playlists()
        for playlist in playlists:
            if playlist['name'] == name:
                return playlist
        return None
    
    def create_playlist_if_not_exists(self, name: str, description: str = "", public: bool = True) -> str:
        """Create playlist if it doesn't exist, return playlist ID."""
        existing = self.get_playlist_by_name(name)
        if existing:
            logger.info(f"Playlist '{name}' already exists: {existing['id']}")
            return existing['id']
        
        playlist = self.create_playlist(name, description, public)
        logger.info(f"Created playlist '{name}': {playlist['id']}")
        return playlist['id']
    
    def remove_tracks_from_playlist(self, playlist_id: str, track_uris: List[str]):
        """Remove tracks from a playlist."""
        if not track_uris:
            return
        
        # Spotify API allows removing tracks by URI
        data = {'uris': track_uris}
        self._make_request('DELETE', f'/playlists/{playlist_id}/tracks', json=data)
        logger.info(f"Removed {len(track_uris)} tracks from playlist {playlist_id}")
    
    def update_playlist_cover(self, playlist_id: str, image_data: str) -> bool:
        """Update playlist cover image."""
        try:
            # The image_data should be base64 encoded
            headers = self._get_headers()
            headers['Content-Type'] = 'image/jpeg'  # or appropriate content type
            
            response = requests.put(
                f"{self.base_url}/playlists/{playlist_id}/images",
                headers=headers,
                data=image_data
            )
            
            if response.status_code == 202:
                logger.info(f"Playlist cover updated successfully for {playlist_id}")
                return True
            else:
                logger.error(f"Failed to update playlist cover: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating playlist cover: {e}")
            return False
