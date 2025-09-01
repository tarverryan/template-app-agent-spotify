#!/usr/bin/env python3
"""
Preseed Playlists Script
Fill all playlists with their target amounts of tracks

This script helps you quickly populate all your playlists with tracks
by running the update commands for each playlist type. It's useful
when you first set up the bot or want to fill empty playlists.

LEARNING OBJECTIVES:
- Understand batch operations and automation
- Learn about system command execution
- Practice working with multiple playlist types
- Understand error handling in batch processes
- Learn about using Makefile commands programmatically
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path

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

def run_make_command(command):
    """
    Run a make command and handle the result.
    
    This function executes a make command using subprocess and handles
    the output and error conditions. It provides feedback on success or failure.
    
    Args:
        command (str): The make command to run
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"🔄 Running: make {command}")
        
        # Run the make command
        result = subprocess.run(
            ['make', command],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), '..')
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully ran: make {command}")
            return True
        else:
            print(f"❌ Failed to run: make {command}")
            print(f"Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Make command not found. Please ensure you're in the project directory.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error running make {command}: {e}")
        return False

def get_active_playlists(config):
    """
    Get list of active playlists from configuration.
    
    This function extracts the active playlists from the configuration
    and returns them as a list. It filters out inactive playlists.
    
    Args:
        config (dict): The configuration data
        
    Returns:
        list: List of active playlist keys
    """
    playlists = config.get('playlists', {})
    active_playlists = []
    
    for playlist_key, playlist_config in playlists.items():
        if playlist_config.get('active', True):  # Default to active if not specified
            active_playlists.append(playlist_key)
    
    return active_playlists

def main():
    """
    Main function to preseed all playlists.
    
    This function orchestrates the playlist preseed process:
    1. Loads the configuration
    2. Identifies active playlists
    3. Runs update commands for each playlist
    4. Provides feedback on the results
    """
    print("🎵 Preseeding Playlists for Spotify App Agent Template")
    print("=" * 60)
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    
    # Get active playlists
    active_playlists = get_active_playlists(config)
    
    if not active_playlists:
        print("❌ No active playlists found in configuration")
        print("Please configure at least one playlist in config.yaml")
        sys.exit(1)
    
    print(f"📋 Found {len(active_playlists)} active playlist(s):")
    for playlist in active_playlists:
        print(f"   - {playlist}")
    print()
    
    # Track results
    successful_updates = []
    failed_updates = []
    
    # Update each playlist
    for playlist in active_playlists:
        # Construct the make command for this playlist
        make_command = f"update-{playlist}"
        
        # Run the update command
        success = run_make_command(make_command)
        
        if success:
            successful_updates.append(playlist)
        else:
            failed_updates.append(playlist)
        
        print()  # Add spacing between commands
    
    # Summary
    print("=" * 60)
    print("📊 Preseed Summary:")
    print(f"✅ Successful updates: {len(successful_updates)}")
    print(f"❌ Failed updates: {len(failed_updates)}")
    
    if successful_updates:
        print("\n✅ Successfully updated playlists:")
        for playlist in successful_updates:
            print(f"   - {playlist}")
    
    if failed_updates:
        print("\n❌ Failed to update playlists:")
        for playlist in failed_updates:
            print(f"   - {playlist}")
        
        print("\n🔧 Troubleshooting:")
        print("1. Check your Spotify credentials in .env file")
        print("2. Verify playlist IDs in config.yaml")
        print("3. Test individual playlists with: make update-{playlist_name}")
        print("4. Check logs for detailed error messages")
    
    print("\n🎯 Next steps:")
    print("1. Check your playlists on Spotify to verify the updates")
    print("2. Monitor the dashboard: python tools/dashboard.py")
    print("3. Set up automated scheduling with: make run")

if __name__ == "__main__":
    main()
