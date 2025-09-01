#!/usr/bin/env python3
"""
Debug script to understand track selection issues.

This script helps you understand how the track selection process works
by breaking it down into individual steps and showing the results of
each step. It's useful for debugging when the bot isn't selecting
tracks as expected.

LEARNING OBJECTIVES:
- Understand the track selection pipeline
- Learn about debugging complex algorithms
- Practice working with data processing steps
- Understand scoring and filtering mechanisms
- Learn about genre allocation and artist caps
"""

import sys  # For system path manipulation and exit
import os  # For file operations and environment variables
sys.path.insert(0, '/app')  # Add the app directory to Python path

# =============================================================================
# IMPORT APPLICATION MODULES
# =============================================================================
# Import the main application classes that handle track selection
# These are the same classes used by the main bot application

from app.spotify_client import SpotifyClient  # Handles Spotify API interactions
from app.track_selector_enhanced import EnhancedTrackSelector  # Handles track selection logic
import yaml  # For reading YAML configuration files

def debug_track_selection():
    """
    Debug the track selection process step by step.
    
    This function walks through each step of the track selection process
    and shows the results, making it easier to understand where issues
    might be occurring.
    
    The track selection process involves:
    1. Discovering tracks from Spotify
    2. Calculating scores for each track
    3. Applying artist caps to limit repetition
    4. Deduplicating tracks
    5. Allocating tracks by genre
    6. Final selection
    """
    
    # =============================================================================
    # LOAD CONFIGURATION
    # =============================================================================
    # Read the current configuration from the YAML file
    # This contains the bot's settings and track selection parameters
    
    with open('/app/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # =============================================================================
    # INITIALIZE COMPONENTS
    # =============================================================================
    # Create instances of the main application classes
    # These are the same components used by the main bot
    
    spotify_client = SpotifyClient()  # Handles Spotify API authentication and requests
    track_selector = EnhancedTrackSelector(spotify_client, config)  # Handles track selection logic
    
    print("=== TRACK SELECTION DEBUG ===")
    
    # =============================================================================
    # STEP 1: DISCOVER TRACKS
    # =============================================================================
    # Find tracks from Spotify that match our criteria
    # This is the first step in the selection process
    
    print("\n1. Discovering tracks for 'previous_day'...")
    tracks = track_selector.discover_tracks_for_period('previous_day', limit=150)
    print(f"   Discovered {len(tracks)} tracks")
    
    # Check if we found any tracks
    if not tracks:
        print("   ❌ No tracks discovered!")
        print("   This might indicate:")
        print("   - No recent listening activity")
        print("   - API authentication issues")
        print("   - Network connectivity problems")
        return
    
    # =============================================================================
    # STEP 2: CALCULATE SCORES
    # =============================================================================
    # Calculate scores for each track based on various factors
    # Higher scores mean tracks are more likely to be selected
    
    print("\n2. Calculating track scores...")
    scored_tracks = track_selector.calculate_track_scores(tracks, None, 'daily')
    print(f"   Scored {len(scored_tracks)} tracks")
    
    # Check if scoring produced any results
    if not scored_tracks:
        print("   ❌ No tracks after scoring!")
        print("   This might indicate:")
        print("   - Scoring algorithm issues")
        print("   - Missing track data")
        print("   - Configuration problems")
        return
    
    # =============================================================================
    # STEP 3: APPLY ARTIST CAPS
    # =============================================================================
    # Limit the number of tracks per artist to avoid repetition
    # This ensures variety in the playlist
    
    print("\n3. Applying artist caps (cap=1)...")
    capped_tracks = track_selector.apply_artist_caps(scored_tracks, 1)
    print(f"   After artist cap: {len(capped_tracks)} tracks")
    
    # Check if artist capping produced results
    if not capped_tracks:
        print("   ❌ No tracks after artist cap!")
        print("   This might indicate:")
        print("   - Too many tracks from the same artist")
        print("   - Artist cap is too restrictive")
        print("   - Scoring favored one artist too heavily")
        return
    
    # =============================================================================
    # STEP 4: APPLY DEDUPLICATION
    # =============================================================================
    # Remove duplicate tracks that might already be in playlists
    # This prevents the same track from being added multiple times
    
    print("\n4. Applying deduplication...")
    deduped_tracks = track_selector.dedupe_tracks(capped_tracks, [], 1)
    print(f"   After deduplication: {len(deduped_tracks)} tracks")
    
    # Check if deduplication produced results
    if not deduped_tracks:
        print("   ❌ No tracks after deduplication!")
        print("   This might indicate:")
        print("   - All tracks are already in playlists")
        print("   - Deduplication is too aggressive")
        print("   - Need to expand track discovery")
        return
    
    # =============================================================================
    # STEP 5: APPLY GENRE ALLOCATION
    # =============================================================================
    # Distribute tracks across different genres for variety
    # This ensures the playlist has a good mix of music styles
    
    print("\n5. Applying genre allocation...")
    allocated_tracks = track_selector.apply_genre_allocation(deduped_tracks, 50)
    print(f"   After genre allocation: {len(allocated_tracks)} tracks")
    
    # =============================================================================
    # STEP 6: SHOW GENRE DISTRIBUTION
    # =============================================================================
    # Display how tracks are distributed across genres
    # This helps understand the variety in the selection
    
    print("\n6. Genre distribution:")
    genre_counts = {}
    
    # Count tracks by genre
    for track in allocated_tracks:
        genre = track.get('genre', 'Other')  # Default to 'Other' if no genre
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # Display genre distribution
    for genre, count in sorted(genre_counts.items()):
        print(f"   {genre}: {count} tracks")
    
    # =============================================================================
    # STEP 7: SHOW TOP TRACKS
    # =============================================================================
    # Display the top-scoring tracks to understand what's being selected
    # This helps verify the scoring algorithm is working correctly
    
    print("\n7. Top 5 tracks by score:")
    for i, track in enumerate(allocated_tracks[:5]):
        # Extract track information
        track_name = track['name']
        artist_name = track['artists'][0]['name']  # First artist
        score = track.get('score', 0)  # Get the calculated score
        
        print(f"   {i+1}. {track_name} by {artist_name} (score: {score:.3f})")
    
    # =============================================================================
    # FINAL SUMMARY
    # =============================================================================
    # Show the final result of the track selection process
    
    print(f"\n=== FINAL RESULT: {len(allocated_tracks)} tracks selected ===")
    
    # Provide guidance based on the results
    if len(allocated_tracks) < 10:
        print("⚠️  Warning: Few tracks selected. Consider:")
        print("   - Expanding track discovery limits")
        print("   - Adjusting scoring weights")
        print("   - Relaxing artist caps or deduplication")
    elif len(allocated_tracks) > 100:
        print("⚠️  Warning: Many tracks selected. Consider:")
        print("   - Reducing discovery limits")
        print("   - Tightening artist caps")
        print("   - Adjusting genre allocation")

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# This block runs when the script is executed directly
if __name__ == "__main__":
    debug_track_selection()
