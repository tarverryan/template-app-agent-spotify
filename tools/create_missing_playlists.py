#!/usr/bin/env python3
"""
Script to create missing playlists for the Spotify bot.
This will create playlists based on your configuration if they don't exist.

This script automates the creation of playlists that the bot needs to function.
It creates playlists with proper naming conventions and updates the configuration
file with the new playlist IDs.

LEARNING OBJECTIVES:
- Understand playlist creation and management
- Learn about configuration file updates
- Practice working with YAML configuration
- Understand database operations for playlist tracking
- Learn about error handling in batch operations
"""

import os
import sys
import yaml
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from spotify_client import SpotifyClient

def load_config():
    """
    Load the configuration file.
    
    This function reads the YAML configuration file and returns the parsed
    configuration data. It handles file reading and YAML parsing.
    
    Returns:
        dict: The configuration data
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configuration file: {e}")
        sys.exit(1)

def create_playlist(spotify_client, name, description, public=True):
    """
    Create a new Spotify playlist.
    
    This function creates a new playlist on Spotify with the specified name
    and description. It handles the API call and returns the playlist data.
    
    Args:
        spotify_client: The Spotify client instance
        name (str): The name of the playlist
        description (str): The description of the playlist
        public (bool): Whether the playlist should be public
        
    Returns:
        dict: The created playlist data
    """
    try:
        playlist = spotify_client.create_playlist(name, description, public)
        print(f"✅ Created playlist: {name}")
        return playlist
    except Exception as e:
        print(f"❌ Failed to create playlist '{name}': {e}")
        return None

def update_config_with_playlist_ids(config, new_playlist_ids):
    """
    Update the configuration file with new playlist IDs.
    
    This function updates the configuration file by replacing placeholder
    playlist IDs with actual IDs from newly created playlists.
    
    Args:
        config (dict): The current configuration
        new_playlist_ids (dict): Dictionary mapping playlist keys to IDs
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    
    # Update the configuration with new playlist IDs
    for playlist_key, playlist_id in new_playlist_ids.items():
        if playlist_key in config.get('playlists', {}):
            config['playlists'][playlist_key]['id'] = playlist_id
    
    # Write the updated configuration back to the file
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print("✅ Updated configuration file with new playlist IDs")
    except Exception as e:
        print(f"❌ Failed to update configuration file: {e}")

def log_playlist_creation(playlist_data):
    """
    Log playlist creation to the database.
    
    This function logs the creation of playlists to the SQLite database
    for tracking and audit purposes.
    
    Args:
        playlist_data (dict): The playlist data to log
    """
    db_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'bot_state.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the playlists table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert or update the playlist record
        cursor.execute('''
            INSERT OR REPLACE INTO playlists (id, name, description, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (
            playlist_data['id'],
            playlist_data['name'],
            playlist_data.get('description', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to log playlist creation to database: {e}")

def main():
    """
    Main function to create missing playlists.
    
    This function orchestrates the playlist creation process:
    1. Loads the configuration
    2. Connects to Spotify
    3. Creates missing playlists
    4. Updates the configuration file
    5. Logs the creation to the database
    """
    print("🎵 Creating missing playlists for Spotify App Agent Template")
    print("=" * 60)
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    
    # Get persona information
    persona = config.get('persona', {})
    prefix = persona.get('prefix', 'Your Bot\'s ')
    bio = persona.get('bio', 'Your bot\'s description')
    
    # Get playlist configurations
    playlists_config = config.get('playlists', {})
    
    if not playlists_config:
        print("❌ No playlist configurations found in config.yaml")
        print("Please configure your playlists before running this script.")
        sys.exit(1)
    
    # Initialize Spotify client
    print("🔗 Connecting to Spotify...")
    try:
        spotify_client = SpotifyClient()
        spotify_client.authenticate()
    except Exception as e:
        print(f"❌ Failed to connect to Spotify: {e}")
        print("Please check your credentials and try again.")
        sys.exit(1)
    
    print("✅ Connected to Spotify successfully")
    print()
    
    # Track newly created playlists
    new_playlist_ids = {}
    
    # Create playlists for each configuration
    for playlist_key, playlist_config in playlists_config.items():
        playlist_id = playlist_config.get('id', '')
        
        # Skip if playlist ID is already configured (not a placeholder)
        if playlist_id and not playlist_id.startswith('your-') and not playlist_id.endswith('-id'):
            print(f"⏭️  Skipping {playlist_key}: Already configured (ID: {playlist_id})")
            continue
        
        # Generate playlist name and description
        playlist_name = f"{prefix}{playlist_key.title()} Hits"
        playlist_description = f"{bio} - {playlist_key.title()} playlist"
        
        print(f"🎵 Creating playlist: {playlist_name}")
        
        # Create the playlist
        playlist_data = create_playlist(spotify_client, playlist_name, playlist_description)
        
        if playlist_data:
            new_playlist_ids[playlist_key] = playlist_data['id']
            log_playlist_creation(playlist_data)
        else:
            print(f"❌ Failed to create playlist for {playlist_key}")
    
    # Update configuration file with new playlist IDs
    if new_playlist_ids:
        print()
        print("📝 Updating configuration file...")
        update_config_with_playlist_ids(config, new_playlist_ids)
        
        print()
        print("✅ Playlist creation completed!")
        print("📋 New playlist IDs:")
        for playlist_key, playlist_id in new_playlist_ids.items():
            print(f"   {playlist_key}: {playlist_id}")
        
        print()
        print("🎯 Next steps:")
        print("1. Review the updated config.yaml file")
        print("2. Test your bot with: python tools/test_bot.py")
        print("3. Run your bot with: make run")
    else:
        print()
        print("ℹ️  All playlists are already configured!")
        print("No new playlists were created.")

if __name__ == "__main__":
    main()
