"""
Playlist Manager
Handles playlist scheduling, rollovers, and main orchestration logic.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from .spotify_client import SpotifyClient
from .track_selector import TrackSelector

logger = logging.getLogger(__name__)

class PlaylistManager:
    """Manages playlist creation, updates, and scheduling."""
    
    def __init__(self, spotify_client: SpotifyClient, track_selector: TrackSelector = None, config: Dict[str, Any] = None):
        self.spotify_client = spotify_client
        self.track_selector = track_selector
        self.config = config or {}
        
        # Initialize database
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'playlist_state.db')
        self._init_database()
        
        # Load playlist IDs from config or create them
        self.playlist_ids = self._load_or_create_playlists() if config else {}
        
    def _init_database(self):
        """Initialize SQLite database for state tracking."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_type TEXT NOT NULL,
                run_timestamp TEXT NOT NULL,
                tracks_count INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_type TEXT NOT NULL,
                snapshot_date TEXT NOT NULL,
                tracks_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_ids (
                playlist_type TEXT PRIMARY KEY,
                playlist_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_or_create_playlists(self) -> Dict[str, str]:
        """Load existing playlist IDs or create new playlists."""
        playlist_ids = {}
        persona = self.config['persona']
        prefix = persona['prefix']
        
        for playlist_type, config in self.config['playlists'].items():
            if not config.get('active', True):
                continue
                
            playlist_name = f"{prefix}{playlist_type.title()} Hits"
            
            # Check if we have a stored playlist ID
            stored_id = self._get_stored_playlist_id(playlist_type)
            if stored_id:
                playlist_ids[playlist_type] = stored_id
                logger.info(f"Using existing playlist for {playlist_type}: {stored_id}")
                continue
            
            # Create new playlist
            try:
                playlist_id = self.spotify_client.create_playlist_if_not_exists(
                    name=playlist_name,
                    description=f"Automated {playlist_type} top hits playlist curated by {persona['name']}",
                    public=True
                )
                playlist_ids[playlist_type] = playlist_id
                self._store_playlist_id(playlist_type, playlist_id)
                logger.info(f"Created new playlist for {playlist_type}: {playlist_id}")
            except Exception as e:
                logger.error(f"Failed to create playlist for {playlist_type}: {e}")
                raise
        
        return playlist_ids
    
    def _get_stored_playlist_id(self, playlist_type: str) -> Optional[str]:
        """Get stored playlist ID from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT playlist_id FROM playlist_ids WHERE playlist_type = ?', (playlist_type,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def _store_playlist_id(self, playlist_type: str, playlist_id: str):
        """Store playlist ID in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO playlist_ids (playlist_type, playlist_id) 
            VALUES (?, ?)
        ''', (playlist_type, playlist_id))
        conn.commit()
        conn.close()
    
    def start_scheduler(self):
        """Start the scheduler with all configured jobs."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        
        # Add jobs for each playlist
        for playlist_type, config in self.config['playlists'].items():
            if not config.get('active', True):
                continue
            
            cron_expr = config['schedule_cron']
            trigger = CronTrigger.from_crontab(cron_expr)
            
            self.scheduler.add_job(
                func=self.update_playlist,
                trigger=trigger,
                args=[playlist_type],
                id=f"update_{playlist_type}",
                name=f"Update {playlist_type} playlist",
                replace_existing=True
            )
            
            logger.info(f"Added scheduled job for {playlist_type}: {cron_expr}")
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def update_playlist(self, playlist_type: str):
        """Update a specific playlist based on its logic type."""
        try:
            logger.info(f"Starting update for {playlist_type} playlist")
            
            playlist_config = self.config['playlists'][playlist_type]
            playlist_id = self.playlist_ids.get(playlist_type)
            
            if not playlist_id:
                logger.error(f"No playlist ID found for {playlist_type}")
                return
            
            # Get previous snapshot for delta calculation
            previous_snapshot = self._get_latest_snapshot(playlist_type)
            
            # Get existing tracks for deduplication
            existing_tracks = self.spotify_client.get_playlist_tracks(playlist_id)
            
            # Select new tracks based on playlist logic type
            selected_tracks = self.track_selector.select_tracks_for_playlist(
                playlist_config, 
                previous_snapshot,
                existing_tracks
            )
            
            if not selected_tracks:
                logger.info(f"No new tracks to add for {playlist_type}")
                return
            
            # Handle different logic types
            logic_type = playlist_config.get('logic', 'general')
            
            if logic_type == 'previous_day':
                # Daily: Replace with fresh tracks from previous day
                logger.info(f"Replacing {playlist_type} playlist with fresh tracks from previous day")
                self.spotify_client.replace_playlist_tracks(playlist_id, [])
                track_uris = [track['uri'] for track in selected_tracks]
                self.spotify_client.add_tracks_to_playlist(playlist_id, track_uris)
                
            elif logic_type == 'previous_week':
                # Weekly: Replace with fresh tracks from previous week
                logger.info(f"Replacing {playlist_type} playlist with fresh tracks from previous week")
                self.spotify_client.replace_playlist_tracks(playlist_id, [])
                track_uris = [track['uri'] for track in selected_tracks]
                self.spotify_client.add_tracks_to_playlist(playlist_id, track_uris)
                
            elif logic_type in ['month_to_date', 'year_to_date']:
                # Monthly/Yearly: Add new tracks to existing playlist (accumulate)
                logger.info(f"Adding {len(selected_tracks)} new tracks to {playlist_type} playlist")
                track_uris = [track['uri'] for track in selected_tracks]
                self.spotify_client.add_tracks_to_playlist(playlist_id, track_uris)
                
                # Check if we need to trim to stay under size limit
                current_tracks = self.spotify_client.get_playlist_tracks(playlist_id)
                max_size = playlist_config.get('size', 200)
                
                if len(current_tracks) > max_size:
                    # Remove oldest tracks to maintain size limit
                    tracks_to_remove = current_tracks[max_size:]
                    track_uris_to_remove = [t['track']['uri'] for t in tracks_to_remove]
                    self.spotify_client.remove_tracks_from_playlist(playlist_id, track_uris_to_remove)
                    logger.info(f"Trimmed {playlist_type} playlist to {max_size} tracks")
            else:
                # Fallback: Add tracks to existing playlist
                track_uris = [track['uri'] for track in selected_tracks]
                self.spotify_client.add_tracks_to_playlist(playlist_id, track_uris)
            
            # Save snapshot
            self._save_snapshot(playlist_type, selected_tracks)
            
            # Log success
            self._log_run(playlist_type, len(selected_tracks), True)
            
            logger.info(f"Successfully updated {playlist_type} playlist with {len(selected_tracks)} tracks")
            
        except Exception as e:
            logger.error(f"Failed to update {playlist_type} playlist: {e}")
            self._log_run(playlist_type, 0, False, str(e))
            raise
    
    def handle_rollover(self, playlist_type: str):
        """Handle monthly/yearly rollovers."""
        try:
            logger.info(f"Handling rollover for {playlist_type}")
            
            playlist_config = self.config['playlists'][playlist_type]
            playlist_id = self.playlist_ids.get(playlist_type)
            
            if not playlist_id:
                logger.error(f"No playlist ID found for {playlist_type}")
                return
            
            # Rename current playlist to "(Final)"
            current_playlist = self.spotify_client.get_playlist(playlist_id)
            current_name = current_playlist['name']
            
            if playlist_config.get('rollover', {}).get('rename_final', False):
                final_suffix = playlist_config['rollover'].get('final_suffix', ' (Final)')
                final_name = current_name + final_suffix
                self.spotify_client.update_playlist(playlist_id, name=final_name)
                logger.info(f"Renamed {playlist_type} playlist to: {final_name}")
            
            # Create new playlist
            persona = self.config['persona']
            prefix = persona['prefix']
            
            # Add year to name for yearly playlists
            if playlist_type == 'yearly':
                current_year = datetime.now().year
                new_playlist_name = f"{prefix}{playlist_type.title()} Hits — {current_year}"
            else:
                new_playlist_name = f"{prefix}{playlist_type.title()} Hits"
            
            new_playlist_id = self.spotify_client.create_playlist(
                name=new_playlist_name,
                description=f"Automated {playlist_type} top hits playlist curated by {persona['name']}",
                public=True
            )
            
            # Update stored playlist ID
            self.playlist_ids[playlist_type] = new_playlist_id['id']
            self._store_playlist_id(playlist_type, new_playlist_id['id'])
            
            # Seed with top tracks from other playlists
            self._seed_new_playlist(playlist_type, new_playlist_id['id'])
            
            logger.info(f"Created new {playlist_type} playlist: {new_playlist_id['id']}")
            
        except Exception as e:
            logger.error(f"Failed to handle rollover for {playlist_type}: {e}")
            raise
    
    def _seed_new_playlist(self, playlist_type: str, playlist_id: str):
        """Seed a new playlist with top tracks from other playlists."""
        seeding_config = self.config.get('seeding', {})
        
        if playlist_type == 'monthly':
            # Seed with top daily and weekly tracks
            top_daily = seeding_config.get('monthly', {}).get('top_daily', 25)
            top_weekly = seeding_config.get('monthly', {}).get('top_weekly', 50)
            
            seed_tracks = []
            
            # Get top daily tracks
            daily_id = self.playlist_ids.get('daily')
            if daily_id:
                daily_tracks = self.spotify_client.get_playlist_tracks(daily_id)
                seed_tracks.extend(daily_tracks[:top_daily])
            
            # Get top weekly tracks
            weekly_id = self.playlist_ids.get('weekly')
            if weekly_id:
                weekly_tracks = self.spotify_client.get_playlist_tracks(weekly_id)
                seed_tracks.extend(weekly_tracks[:top_weekly])
            
            if seed_tracks:
                track_uris = [track['track']['uri'] for track in seed_tracks]
                self.spotify_client.replace_playlist_tracks(playlist_id, track_uris)
                logger.info(f"Seeded {playlist_type} playlist with {len(track_uris)} tracks")
        
        elif playlist_type == 'yearly':
            # Similar seeding logic for yearly
            top_daily = seeding_config.get('yearly', {}).get('top_daily', 25)
            top_weekly = seeding_config.get('yearly', {}).get('top_weekly', 50)
            
            seed_tracks = []
            
            daily_id = self.playlist_ids.get('daily')
            if daily_id:
                daily_tracks = self.spotify_client.get_playlist_tracks(daily_id)
                seed_tracks.extend(daily_tracks[:top_daily])
            
            weekly_id = self.playlist_ids.get('weekly')
            if weekly_id:
                weekly_tracks = self.spotify_client.get_playlist_tracks(weekly_id)
                seed_tracks.extend(weekly_tracks[:top_weekly])
            
            if seed_tracks:
                track_uris = [track['track']['uri'] for track in seed_tracks]
                self.spotify_client.replace_playlist_tracks(playlist_id, track_uris)
                logger.info(f"Seeded {playlist_type} playlist with {len(track_uris)} tracks")
    
    def _save_snapshot(self, playlist_type: str, tracks: List[Dict[str, Any]]):
        """Save playlist snapshot to database and files."""
        timestamp = datetime.now().isoformat()
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO playlist_snapshots (playlist_type, snapshot_date, tracks_data)
            VALUES (?, ?, ?)
        ''', (playlist_type, timestamp, json.dumps(tracks)))
        conn.commit()
        conn.close()
        
        # Save to JSON file
        snapshot_dir = self.config['app']['snapshot_dir']
        os.makedirs(snapshot_dir, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = os.path.join(snapshot_dir, f"{playlist_type}_{date_str}.json")
        
        snapshot_data = {
            'playlist_type': playlist_type,
            'timestamp': timestamp,
            'tracks_count': len(tracks),
            'tracks': tracks
        }
        
        with open(json_path, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        # Save to CSV
        csv_path = os.path.join(snapshot_dir, f"{playlist_type}_{date_str}.csv")
        df = pd.DataFrame(tracks)
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Saved snapshot for {playlist_type}: {json_path}, {csv_path}")
    
    def _get_latest_snapshot(self, playlist_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot for a playlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tracks_data FROM playlist_snapshots 
            WHERE playlist_type = ? 
            ORDER BY snapshot_date DESC 
            LIMIT 1
        ''', (playlist_type,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def _log_run(self, playlist_type: str, tracks_count: int, success: bool, error_message: str = None):
        """Log a playlist update run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO playlist_runs (playlist_type, run_timestamp, tracks_count, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (playlist_type, datetime.now().isoformat(), tracks_count, success, error_message))
        conn.commit()
        conn.close()
    
    def get_playlist_id(self, playlist_type: str) -> str:
        """Get playlist ID by type."""
        if playlist_type in self.playlist_ids:
            return self.playlist_ids[playlist_type]
        else:
            raise ValueError(f"Playlist '{playlist_type}' not found")
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get tracks from a playlist."""
        return self.spotify_client.get_playlist_tracks(playlist_id)
    
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to a playlist."""
        if not track_ids:
            return True
        
        try:
            track_uris = [f"spotify:track:{track_id}" for track_id in track_ids]
            self.spotify_client.add_tracks_to_playlist(playlist_id, track_uris)
            return True
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist: {e}")
            return False
    
    def replace_playlist_tracks(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Replace all tracks in a playlist."""
        try:
            track_uris = [f"spotify:track:{track_id}" for track_id in track_ids]
            self.spotify_client.replace_playlist_tracks(playlist_id, track_uris)
            return True
        except Exception as e:
            logger.error(f"Failed to replace playlist tracks: {e}")
            return False
    
    def update_playlist_cover(self, playlist_id: str, image_data: str) -> bool:
        """Update playlist cover image."""
        return self.spotify_client.update_playlist_cover(playlist_id, image_data)
    
    def log_playlist_update(self, playlist_type: str, track_count: int, success: bool) -> bool:
        """Log playlist update to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO playlist_runs (playlist_type, run_timestamp, tracks_count, success)
                VALUES (?, ?, ?, ?)
            ''', (playlist_type, datetime.now().isoformat(), track_count, success))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to log playlist update: {e}")
            return False
    
    def get_playlist_update_history(self, playlist_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get playlist update history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT run_timestamp, tracks_count, success, error_message
                FROM playlist_runs
                WHERE playlist_type = ?
                ORDER BY run_timestamp DESC
                LIMIT ?
            ''', (playlist_type, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'timestamp': row[0],
                    'track_count': row[1],
                    'success': row[2],
                    'error': row[3]
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Failed to get playlist history: {e}")
            return []
    
    def get_playlist_statistics(self, playlist_type: str) -> Dict[str, Any]:
        """Get playlist statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_updates,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_updates,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_updates
                FROM playlist_runs
                WHERE playlist_type = ?
            ''', (playlist_type,))
            
            row = cursor.fetchone()
            conn.close()
            
            return {
                'total_updates': row[0] or 0,
                'successful_updates': row[1] or 0,
                'failed_updates': row[2] or 0
            }
        except Exception as e:
            logger.error(f"Failed to get playlist statistics: {e}")
            return {'total_updates': 0, 'successful_updates': 0, 'failed_updates': 0}
    
    def validate_playlist_id(self, playlist_id: str) -> bool:
        """Validate if playlist ID exists."""
        try:
            # Try to get playlist info
            self.spotify_client.get_playlist(playlist_id)
            return True
        except:
            return False
    
    def get_playlist_info(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist information."""
        return self.spotify_client.get_playlist(playlist_id)
    
    def batch_add_tracks(self, playlists: List[str], track_ids: List[str]) -> List[bool]:
        """Add tracks to multiple playlists."""
        results = []
        for playlist_id in playlists:
            result = self.add_tracks_to_playlist(playlist_id, track_ids)
            results.append(result)
        return results
    
    def update_playlist_name(self, playlist_id: str, name: str) -> bool:
        """Update playlist name."""
        try:
            self.spotify_client.update_playlist(playlist_id, name=name)
            return True
        except Exception as e:
            logger.error(f"Failed to update playlist name: {e}")
            return False
    
    def update_playlist_description(self, playlist_id: str, description: str) -> bool:
        """Update playlist description."""
        try:
            self.spotify_client.update_playlist(playlist_id, description=description)
            return True
        except Exception as e:
            logger.error(f"Failed to update playlist description: {e}")
            return False
    
    def set_playlist_public(self, playlist_id: str, public: bool) -> bool:
        """Set playlist public/private."""
        try:
            self.spotify_client.update_playlist(playlist_id, public=public)
            return True
        except Exception as e:
            logger.error(f"Failed to set playlist public: {e}")
            return False
    
    def get_playlist_diversity(self, playlist_id: str) -> float:
        """Calculate playlist diversity score."""
        try:
            tracks = self.get_playlist_tracks(playlist_id)
            if not tracks:
                return 0.0
            
            artists = set()
            for track in tracks:
                if 'track' in track and 'artists' in track['track']:
                    for artist in track['track']['artists']:
                        artists.add(artist['name'])
            
            return len(artists) / len(tracks) if tracks else 0.0
        except Exception as e:
            logger.error(f"Failed to calculate playlist diversity: {e}")
            return 0.0
    
    def get_most_common_artists(self, playlist_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common artists in playlist."""
        try:
            tracks = self.get_playlist_tracks(playlist_id)
            artist_counts = {}
            
            for track in tracks:
                if 'track' in track and 'artists' in track['track']:
                    for artist in track['track']['artists']:
                        artist_name = artist['name']
                        artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
            
            # Sort by count and return top artists
            sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
            return [{'name': name, 'count': count} for name, count in sorted_artists[:limit]]
        except Exception as e:
            logger.error(f"Failed to get most common artists: {e}")
            return []
    
    def get_playlist_mood(self, playlist_id: str) -> Dict[str, Any]:
        """Analyze playlist mood (placeholder implementation)."""
        try:
            tracks = self.get_playlist_tracks(playlist_id)
            return {
                'total_tracks': len(tracks),
                'mood_score': 0.5,  # Placeholder
                'energy_level': 'medium'  # Placeholder
            }
        except Exception as e:
            logger.error(f"Failed to analyze playlist mood: {e}")
            return {'total_tracks': 0, 'mood_score': 0.0, 'energy_level': 'unknown'}
