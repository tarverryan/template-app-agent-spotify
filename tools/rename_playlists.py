#!/usr/bin/env python3
"""
Script to rename existing playlists to the new format

This script helps you rename your existing Spotify playlists to match
your bot's naming convention. It's useful when you want to standardize
playlist names across your account.

LEARNING OBJECTIVES:
- Understand API operations for playlist management
- Learn about HTTP PUT requests for updates
- Practice working with JSON data in API calls
- Understand playlist naming conventions
- Learn about batch operations and error handling
"""

import os
import sys
import yaml
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

def get_playlist_mapping(config):
    """
    Create a mapping of playlist IDs to new names.
    
    This function creates a dictionary mapping playlist IDs to their
    new names based on the configuration and persona settings.
    
    Args:
        config: The configuration data
        
    Returns:
        dict: Mapping of playlist IDs to new names
    """
    persona = config.get('persona', {})
    prefix = persona.get('prefix', 'Your Bot\'s ')
    
    # Define new playlist names based on persona
    new_names = {
        'playlist1': f"{prefix}Playlist 1 Hits",
        'playlist2': f"{prefix}Playlist 2 Hits",
        'playlist3': f"{prefix}Playlist 3 Hits",
        'playlist4': f"{prefix}Playlist 4 Hits"
    }
    
    # Create mapping from playlist IDs to new names
    playlist_mapping = {}
    playlists = config.get('playlists', {})
    
    for playlist_key, playlist_config in playlists.items():
        playlist_id = playlist_config.get('id', '')
        
        # Skip if playlist ID is not configured or is a placeholder
        if not playlist_id or playlist_id.startswith('your-') or playlist_id.endswith('-id'):
            continue
            
        if playlist_key in new_names:
            playlist_mapping[playlist_id] = new_names[playlist_key]
    
    return playlist_mapping

def rename_playlist(spotify_client, playlist_id, new_name):
    """
    Rename a Spotify playlist.
    
    This function uses the Spotify API to rename a playlist with the
    specified ID to the new name.
    
    Args:
        spotify_client: The Spotify client instance
        playlist_id: The ID of the playlist to rename
        new_name: The new name for the playlist
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current playlist info
        playlist = spotify_client.get_playlist(playlist_id)
        if not playlist:
            print(f"❌ Could not retrieve playlist {playlist_id}")
            return False
        
        current_name = playlist.get('name', 'Unknown')
        
        # Skip if name is already correct
        if current_name == new_name:
            print(f"⏭️  Playlist {playlist_id} already has correct name: {new_name}")
            return True
        
        # Rename the playlist
        success = spotify_client.update_playlist(playlist_id, name=new_name)
        
        if success:
            print(f"✅ Renamed playlist: {current_name} → {new_name}")
            return True
        else:
            print(f"❌ Failed to rename playlist {playlist_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error renaming playlist {playlist_id}: {e}")
        return False

def main():
    """
    Main function to rename playlists.
    
    This function orchestrates the playlist renaming process:
    1. Loads the configuration
    2. Connects to Spotify
    3. Creates playlist mapping
    4. Renames playlists
    5. Provides feedback on results
    """
    print("🎵 Renaming Playlists for Spotify App Agent Template")
    print("=" * 60)
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    
    # Get persona information
    persona = config.get('persona', {})
    bot_name = persona.get('name', 'Your Bot')
    prefix = persona.get('prefix', 'Your Bot\'s ')
    
    print(f"🤖 Bot: {bot_name}")
    print(f"📝 Prefix: {prefix}")
    print()
    
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
    
    # Get playlist mapping
    playlist_mapping = get_playlist_mapping(config)
    
    if not playlist_mapping:
        print("⚠️  No playlists found to rename")
        print("Please configure your playlist IDs in config.yaml first")
        sys.exit(1)
    
    print(f"📋 Found {len(playlist_mapping)} playlist(s) to rename:")
    for playlist_id, new_name in playlist_mapping.items():
        print(f"   - {playlist_id} → {new_name}")
    print()
    
    # Confirm with user
    response = input("Do you want to proceed with renaming these playlists? (y/N): ")
    if response.lower() != 'y':
        print("❌ Renaming cancelled")
        sys.exit(0)
    
    print()
    
    # Rename playlists
    successful_renames = 0
    failed_renames = 0
    
    for playlist_id, new_name in playlist_mapping.items():
        success = rename_playlist(spotify_client, playlist_id, new_name)
        if success:
            successful_renames += 1
        else:
            failed_renames += 1
    
    # Summary
    print()
    print("=" * 60)
    print("📊 Rename Summary:")
    print(f"✅ Successful renames: {successful_renames}")
    print(f"❌ Failed renames: {failed_renames}")
    
    if successful_renames > 0:
        print("\n🎉 Playlist renaming completed!")
        print("Your playlists now follow your bot's naming convention.")
    
    if failed_renames > 0:
        print("\n⚠️  Some playlists could not be renamed.")
        print("This might be due to:")
        print("- Invalid playlist IDs")
        print("- Insufficient permissions")
        print("- Network connectivity issues")
    
    print("\n🎯 Next steps:")
    print("1. Verify the new playlist names on Spotify")
    print("2. Test your bot with: python tools/test_bot.py")
    print("3. Run your bot with: make run")

if __name__ == "__main__":
    main()
