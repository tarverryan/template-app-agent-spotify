#!/usr/bin/env python3
"""
Spotify Bot Dashboard
Monitor bot performance and show statistics

This script provides a comprehensive dashboard for monitoring your Spotify bot.
It shows performance metrics, playlist status, and scheduled runs.

LEARNING OBJECTIVES:
- Understand database queries and SQL
- Learn about data analysis with pandas
- Practice working with APIs and authentication
- Understand monitoring and observability
- Learn about data visualization and reporting
"""

import os  # For file operations and environment variables
import sqlite3  # For connecting to SQLite database
import json  # For parsing JSON data
from datetime import datetime, timedelta  # For date/time operations
from dotenv import load_dotenv  # For loading environment variables from .env file
import requests  # For making HTTP requests to Spotify API
import pandas as pd  # For data analysis and manipulation

# =============================================================================
# LOAD ENVIRONMENT VARIABLES
# =============================================================================
# Load credentials and configuration from .env file
load_dotenv()

def get_bot_stats():
    """
    Get bot statistics from SQLite database.
    
    This function connects to the bot's database and retrieves:
    - Recent playlist update runs
    - Playlist snapshots
    - Performance metrics
    
    Returns:
        tuple: (runs_df, snapshots_df) or None if database doesn't exist
    """
    # Path to the SQLite database file
    db_path = 'state/playlist_state.db'
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print("❌ Database not found. Bot may not have run yet.")
        return None
    
    # =============================================================================
    # CONNECT TO DATABASE
    # =============================================================================
    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # =============================================================================
    # QUERY RECENT RUNS
    # =============================================================================
    # Get the last 20 playlist update runs with their results
    # This shows the bot's recent activity and success rate
    
    runs_df = pd.read_sql_query("""
        SELECT playlist_type, run_timestamp, tracks_count, success, error_message
        FROM playlist_runs 
        ORDER BY run_timestamp DESC 
        LIMIT 20
    """, conn)
    
    # =============================================================================
    # QUERY SNAPSHOT STATISTICS
    # =============================================================================
    # Get the last 10 playlist snapshots
    # Snapshots are saved copies of playlist data for analysis
    
    snapshots_df = pd.read_sql_query("""
        SELECT playlist_type, snapshot_date, tracks_data
        FROM playlist_snapshots 
        ORDER BY snapshot_date DESC 
        LIMIT 10
    """, conn)
    
    # Close the database connection
    conn.close()
    
    # Return the data as pandas DataFrames
    return runs_df, snapshots_df

def get_spotify_playlist_info():
    """
    Get current playlist information from Spotify API.
    
    This function authenticates with Spotify and fetches real-time
    information about your playlists, including track counts and follower counts.
    
    Returns:
        dict: Playlist information or None if authentication fails
    """
    # =============================================================================
    # GET CREDENTIALS FROM ENVIRONMENT
    # =============================================================================
    # Load Spotify API credentials from environment variables
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')
    
    # =============================================================================
    # AUTHENTICATE WITH SPOTIFY
    # =============================================================================
    # Use the refresh token to get a new access token
    # This is the same process the bot uses to authenticate
    
    response = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'refresh_token',  # We're using a refresh token
        'refresh_token': refresh_token,  # The long-lived token
        'client_id': client_id,         # Your app's ID
        'client_secret': client_secret  # Your app's secret
    })
    
    # Check if authentication was successful
    if response.status_code != 200:
        return None
    
    # Extract the access token from the response
    access_token = response.json()['access_token']
    
    # Set up headers for API requests
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # =============================================================================
    # PLAYLIST CONFIGURATION
    # =============================================================================
    # Define the playlist IDs to check
    # These should match the IDs in your config.yaml file
    
    playlists = {
        'daily': 'your-daily-playlist-id',
        'weekly': 'your-weekly-playlist-id', 
        'monthly': 'your-monthly-playlist-id',
        'yearly': 'your-yearly-playlist-id'
    }
    
    # =============================================================================
    # FETCH PLAYLIST INFORMATION
    # =============================================================================
    # Loop through each playlist and get its current information
    
    playlist_info = {}
    for playlist_type, playlist_id in playlists.items():
        # Skip playlists that haven't been configured yet
        if playlist_id.startswith('your-'):
            playlist_info[playlist_type] = {'error': 'Playlist ID not configured'}
            continue
            
        try:
            # Make a request to Spotify's API to get playlist details
            response = requests.get(
                f'https://api.spotify.com/v1/playlists/{playlist_id}',
                headers=headers
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                playlist = response.json()
                
                # Extract the information we want to display
                playlist_info[playlist_type] = {
                    'name': playlist['name'],  # Playlist name
                    'track_count': len(playlist['tracks']['items']),  # Number of tracks
                    'followers': playlist.get('followers', {}).get('total', 0),  # Follower count
                    'last_updated': playlist.get('snapshot_id', 'Unknown')  # Last update ID
                }
        except Exception as e:
            # If there's an error, store the error message
            playlist_info[playlist_type] = {'error': str(e)}
    
    return playlist_info

def display_dashboard():
    """
    Display the bot dashboard with performance metrics and playlist status.
    
    This function orchestrates the display of all dashboard information:
    - Bot performance statistics
    - Recent activity
    - Playlist status
    - Scheduled runs
    """
    print("🎵 Spotify App Agent Dashboard")
    print("=" * 50)
    print()
    
    # =============================================================================
    # GET BOT STATISTICS
    # =============================================================================
    # Retrieve performance data from the database
    stats = get_bot_stats()
    if stats:
        runs_df, snapshots_df = stats
        
        # =============================================================================
        # DISPLAY PERFORMANCE METRICS
        # =============================================================================
        print("📊 Bot Performance")
        print("-" * 30)
        
        if not runs_df.empty:
            # Calculate success rate from the data
            total_runs = len(runs_df)
            successful_runs = len(runs_df[runs_df['success'] == True])
            success_rate = (successful_runs / total_runs) * 100 if total_runs > 0 else 0
            
            # Display performance summary
            print(f"Total Runs: {total_runs}")
            print(f"Successful: {successful_runs}")
            print(f"Success Rate: {success_rate:.1f}%")
            
            # =============================================================================
            # DISPLAY RECENT ACTIVITY
            # =============================================================================
            # Show the last 5 runs with their status and details
            print(f"\nRecent Activity:")
            recent_runs = runs_df.head(5)  # Get the 5 most recent runs
            
            for _, run in recent_runs.iterrows():
                # Determine status emoji based on success
                status = "✅" if run['success'] else "❌"
                
                # Format timestamp for display (show only first 19 chars: YYYY-MM-DD HH:MM:SS)
                timestamp = run['run_timestamp'][:19] if run['run_timestamp'] else 'Unknown'
                
                # Display run information
                print(f"  {status} {run['playlist_type']} - {timestamp} ({run['tracks_count']} tracks)")
        else:
            print("No runs recorded yet.")
        
        print()
    
    # =============================================================================
    # DISPLAY PLAYLIST STATUS
    # =============================================================================
    # Show current information about each playlist from Spotify
    print("📋 Playlist Status")
    print("-" * 30)
    
    playlist_info = get_spotify_playlist_info()
    if playlist_info:
        for playlist_type, info in playlist_info.items():
            if 'error' not in info:
                # Display successful playlist information
                print(f"🎵 {info['name']}")
                print(f"   Tracks: {info['track_count']}")
                print(f"   Followers: {info['followers']}")
                print()
            else:
                # Display error information
                print(f"❌ {playlist_type}: {info['error']}")
    else:
        print("❌ Could not fetch playlist information")
    
    # =============================================================================
    # DISPLAY SCHEDULED RUNS
    # =============================================================================
    # Show when the next updates are scheduled to run
    print("⏰ Next Scheduled Runs")
    print("-" * 30)
    
    # Define the schedule for each playlist type
    # These should match the cron expressions in config.yaml
    schedules = {
        'daily': '04:00 daily',
        'weekly': 'Friday 04:00',
        'monthly': '1st of month 04:10',
        'yearly': 'Jan 1 04:15'
    }
    
    # Display each schedule
    for playlist_type, schedule in schedules.items():
        print(f"📅 {playlist_type.title()}: {schedule}")
    
    # =============================================================================
    # DISPLAY SYSTEM INFORMATION
    # =============================================================================
    # Show file locations and system status
    print()
    print("🔧 Bot Status: ✅ Running")
    print("📁 Logs: logs/spotify_bot.log")
    print("📊 Snapshots: snapshots/")
    print("💾 Database: state/playlist_state.db")

def show_recent_snapshots():
    """
    Show recent playlist snapshots.
    
    This function displays information about the most recent snapshot files
    that the bot has created. Snapshots are saved copies of playlist data
    for analysis and backup purposes.
    """
    print("\n📸 Recent Snapshots")
    print("-" * 30)
    
    # Path to the snapshots directory
    snapshot_dir = 'snapshots'
    
    # Check if the snapshots directory exists
    if not os.path.exists(snapshot_dir):
        print("No snapshots found.")
        return
    
    # =============================================================================
    # FIND SNAPSHOT FILES
    # =============================================================================
    # Get all JSON files in the snapshots directory
    # These are the snapshot files created by the bot
    snapshot_files = [f for f in os.listdir(snapshot_dir) if f.endswith('.json')]
    
    # Sort files by name (newest first, since they include timestamps)
    snapshot_files.sort(reverse=True)
    
    # =============================================================================
    # DISPLAY SNAPSHOT INFORMATION
    # =============================================================================
    # Show information about the 5 most recent snapshots
    for file in snapshot_files[:5]:
        file_path = os.path.join(snapshot_dir, file)
        
        try:
            # Read and parse the JSON snapshot file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Display snapshot information
            print(f"📄 {file}")
            print(f"   Type: {data.get('playlist_type', 'Unknown')}")
            print(f"   Tracks: {data.get('tracks_count', 0)}")
            print(f"   Date: {data.get('timestamp', 'Unknown')[:19]}")
            print()
            
        except Exception as e:
            # If there's an error reading the file, show the error
            print(f"❌ Error reading {file}: {e}")

def main():
    """
    Main function that runs the dashboard.
    
    This function displays the main dashboard and then shows recent snapshots.
    """
    display_dashboard()
    show_recent_snapshots()
    
    print("\n🎯 Quick Actions:")
    print("  make logs          - View bot logs")
    print("  make update-daily  - Manual daily update")
    print("  make update-weekly - Manual weekly update")
    print("  make stop          - Stop the bot")
    print("  make run           - Start the bot")

if __name__ == "__main__":
    main()
