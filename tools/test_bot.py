#!/usr/bin/env python3
"""
Simple test script to verify the bot is working

This script provides comprehensive testing for the Spotify bot to ensure
all components are working correctly before running the main application.

LEARNING OBJECTIVES:
- Understand API testing and validation
- Learn about error handling and debugging
- Practice working with external APIs
- Understand authentication testing
- Learn about playlist management testing
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

def test_spotify_connection(spotify_client):
    """
    Test the Spotify API connection.
    
    This function tests the basic connectivity to the Spotify API
    by making a simple API call to get the user's profile.
    
    Args:
        spotify_client: The Spotify client instance
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        print("🔗 Testing Spotify API connection...")
        
        # Test basic API call
        user_profile = spotify_client.get_user_profile()
        if user_profile:
            print(f"✅ Connected to Spotify as: {user_profile.get('display_name', 'Unknown')}")
            print(f"   User ID: {user_profile.get('id', 'Unknown')}")
            print(f"   Email: {user_profile.get('email', 'Not provided')}")
            return True
        else:
            print("❌ Failed to get user profile")
            return False
            
    except Exception as e:
        print(f"❌ Spotify connection failed: {e}")
        return False

def test_playlist_access(spotify_client, config):
    """
    Test access to configured playlists.
    
    This function tests whether the bot can access all the playlists
    specified in the configuration file.
    
    Args:
        spotify_client: The Spotify client instance
        config: The configuration data
        
    Returns:
        bool: True if all playlists accessible, False otherwise
    """
    print("\n📋 Testing playlist access...")
    
    playlists = config.get('playlists', {})
    if not playlists:
        print("⚠️  No playlists configured in config.yaml")
        return True
    
    all_accessible = True
    
    for playlist_key, playlist_config in playlists.items():
        playlist_id = playlist_config.get('id', '')
        
        # Skip if playlist ID is not configured
        if not playlist_id or playlist_id.startswith('your-') or playlist_id.endswith('-id'):
            print(f"⏭️  Skipping {playlist_key}: Not configured (ID: {playlist_id})")
            continue
        
        try:
            print(f"🎵 Testing access to {playlist_key}...")
            
            # Test playlist access
            playlist = spotify_client.get_playlist(playlist_id)
            if playlist:
                print(f"✅ {playlist_key}: {playlist.get('name', 'Unknown')}")
                print(f"   Tracks: {playlist.get('tracks', {}).get('total', 0)}")
                print(f"   Public: {playlist.get('public', False)}")
            else:
                print(f"❌ {playlist_key}: Failed to access playlist")
                all_accessible = False
                
        except Exception as e:
            print(f"❌ {playlist_key}: Error accessing playlist - {e}")
            all_accessible = False
    
    return all_accessible

def test_configuration(config):
    """
    Test the configuration file for validity.
    
    This function validates the configuration file structure and
    checks for required fields and valid values.
    
    Args:
        config: The configuration data
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    print("\n⚙️  Testing configuration...")
    
    # Check required sections
    required_sections = ['persona', 'playlists']
    for section in required_sections:
        if section not in config:
            print(f"❌ Missing required section: {section}")
            return False
    
    # Check persona configuration
    persona = config.get('persona', {})
    required_persona_fields = ['name', 'prefix', 'bio']
    for field in required_persona_fields:
        if field not in persona:
            print(f"❌ Missing persona field: {field}")
            return False
    
    print(f"✅ Persona: {persona.get('name', 'Unknown')}")
    print(f"   Prefix: {persona.get('prefix', 'Unknown')}")
    print(f"   Bio: {persona.get('bio', 'Unknown')}")
    
    # Check playlists configuration
    playlists = config.get('playlists', {})
    if not playlists:
        print("⚠️  No playlists configured")
    else:
        print(f"✅ Found {len(playlists)} playlist(s) configured")
        for playlist_key, playlist_config in playlists.items():
            print(f"   - {playlist_key}: {playlist_config.get('size', 'Unknown size')} tracks")
    
    return True

def test_environment_variables():
    """
    Test that required environment variables are set.
    
    This function checks that all required environment variables
    are present and not empty.
    
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    print("\n🔐 Testing environment variables...")
    
    required_vars = [
        'SPOTIFY_CLIENT_ID',
        'SPOTIFY_CLIENT_SECRET', 
        'SPOTIFY_REFRESH_TOKEN',
        'SPOTIFY_USER_ID'
    ]
    
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ Missing environment variable: {var}")
            all_set = False
        else:
            # Show first few characters for verification
            display_value = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}: {display_value}")
    
    return all_set

def main():
    """
    Main function to run all tests.
    
    This function orchestrates the testing process:
    1. Tests environment variables
    2. Tests configuration file
    3. Tests Spotify connection
    4. Tests playlist access
    5. Provides summary and recommendations
    """
    print("🧪 Spotify App Agent Template - Test Suite")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    if not env_ok:
        print("\n❌ Environment variables test failed!")
        print("Please check your .env file and ensure all required variables are set.")
        sys.exit(1)
    
    # Test configuration
    try:
        config = load_config()
        config_ok = test_configuration(config)
        if not config_ok:
            print("\n❌ Configuration test failed!")
            print("Please check your config.yaml file.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Test Spotify connection
    try:
        spotify_client = SpotifyClient()
        spotify_client.authenticate()
        
        connection_ok = test_spotify_connection(spotify_client)
        if not connection_ok:
            print("\n❌ Spotify connection test failed!")
            print("Please check your credentials and try again.")
            sys.exit(1)
        
        # Test playlist access
        playlists_ok = test_playlist_access(spotify_client, config)
        if not playlists_ok:
            print("\n⚠️  Some playlist access tests failed!")
            print("Please check your playlist IDs and permissions.")
        
    except Exception as e:
        print(f"\n❌ Spotify client initialization failed: {e}")
        print("Please check your credentials and try again.")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Environment Variables: {'PASS' if env_ok else 'FAIL'}")
    print(f"✅ Configuration: {'PASS' if config_ok else 'FAIL'}")
    print(f"✅ Spotify Connection: {'PASS' if connection_ok else 'FAIL'}")
    print(f"✅ Playlist Access: {'PASS' if playlists_ok else 'FAIL'}")
    
    if env_ok and config_ok and connection_ok and playlists_ok:
        print("\n🎉 All tests passed! Your bot is ready to run.")
        print("\n🎯 Next steps:")
        print("1. Run the bot: make run")
        print("2. Monitor logs: make logs")
        print("3. Check dashboard: python tools/dashboard.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running the bot.")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file for missing credentials")
        print("2. Verify your config.yaml file is valid")
        print("3. Ensure your Spotify app is properly configured")
        print("4. Check that your playlists are public and accessible")

if __name__ == "__main__":
    main()
