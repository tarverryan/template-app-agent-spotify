"""
Database Initialization for Spotify App Agent Template

This script creates the necessary database tables for the bot's
analytics, logging, and state management functionality.

LEARNING OBJECTIVES:
- Understand database schema design
- Learn about SQLite database management
- Practice working with database migrations
- Understand data persistence patterns
"""

import os
import sqlite3
from pathlib import Path

def init_database():
    """
    Initialize the database with required tables.
    
    This function creates all necessary tables for the bot's
    functionality including run logs, playlist snapshots, and
    track history.
    """
    # Create state directory if it doesn't exist
    state_dir = Path(__file__).parent.parent / 'state'
    state_dir.mkdir(exist_ok=True)
    
    db_path = state_dir / 'bot_state.db'
    
    print(f"🗄️  Initializing database at: {db_path}")
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create bot_runs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_type TEXT NOT NULL,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            status TEXT DEFAULT 'running',
            tracks_added INTEGER DEFAULT 0,
            tracks_removed INTEGER DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create playlist_snapshots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id TEXT NOT NULL,
            playlist_type TEXT NOT NULL,
            snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            track_count INTEGER DEFAULT 0,
            total_duration INTEGER DEFAULT 0,
            avg_popularity REAL DEFAULT 0,
            genres TEXT,  -- JSON array of genres
            artists TEXT, -- JSON array of artists
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create track_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS track_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT NOT NULL,
            track_name TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            popularity INTEGER DEFAULT 0,
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            playlist_type TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_runs_start_time ON bot_runs(start_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_runs_status ON bot_runs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_playlist_snapshots_time ON playlist_snapshots(snapshot_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_playlist_snapshots_type ON playlist_snapshots(playlist_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_track_history_date ON track_history(added_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_track_history_playlist ON track_history(playlist_type)')
    
    # Commit changes
    conn.commit()
    
    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("✅ Database initialized successfully!")
    print("📋 Created tables:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Insert sample data for testing
    insert_sample_data(cursor)
    
    conn.close()
    print("🎉 Database setup complete!")

def insert_sample_data(cursor):
    """
    Insert sample data for testing and demonstration.
    
    This function adds some sample records to demonstrate
    the analytics functionality.
    """
    print("📝 Inserting sample data for testing...")
    
    # Sample bot runs
    sample_runs = [
        ('playlist1', 'success', 15, 5, None),
        ('playlist2', 'success', 12, 3, None),
        ('playlist3', 'failed', 0, 0, 'API rate limit exceeded'),
        ('playlist1', 'success', 18, 2, None),
        ('playlist4', 'success', 10, 8, None),
    ]
    
    for playlist_type, status, added, removed, error in sample_runs:
        cursor.execute('''
            INSERT INTO bot_runs (playlist_type, status, tracks_added, tracks_removed, error_message, end_time)
            VALUES (?, ?, ?, ?, ?, datetime('now', '-1 hour'))
        ''', (playlist_type, status, added, removed, error))
    
    # Sample playlist snapshots
    sample_snapshots = [
        ('sample-playlist-1', 'playlist1', 50, 7200, 75.5, '["pop", "indie pop"]', '["Artist1", "Artist2"]'),
        ('sample-playlist-2', 'playlist2', 45, 6800, 72.3, '["rock", "alternative"]', '["Artist3", "Artist4"]'),
        ('sample-playlist-3', 'playlist3', 40, 6000, 68.9, '["electronic", "edm"]', '["Artist5", "Artist6"]'),
        ('sample-playlist-4', 'playlist4', 55, 8000, 78.2, '["hip hop", "rap"]', '["Artist7", "Artist8"]'),
    ]
    
    for playlist_id, playlist_type, track_count, duration, popularity, genres, artists in sample_snapshots:
        cursor.execute('''
            INSERT INTO playlist_snapshots (playlist_id, playlist_type, track_count, total_duration, avg_popularity, genres, artists)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (playlist_id, playlist_type, track_count, duration, popularity, genres, artists))
    
    # Sample track history
    sample_tracks = [
        ('track1', 'Amazing Song', 'Artist1', 85, 'playlist1'),
        ('track2', 'Great Track', 'Artist2', 78, 'playlist1'),
        ('track3', 'Awesome Music', 'Artist3', 92, 'playlist2'),
        ('track4', 'Cool Beat', 'Artist4', 71, 'playlist2'),
        ('track5', 'Electronic Vibes', 'Artist5', 88, 'playlist3'),
        ('track6', 'Hip Hop Flow', 'Artist7', 95, 'playlist4'),
    ]
    
    for track_id, track_name, artist_name, popularity, playlist_type in sample_tracks:
        cursor.execute('''
            INSERT INTO track_history (track_id, track_name, artist_name, popularity, playlist_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (track_id, track_name, artist_name, popularity, playlist_type))
    
    print("✅ Sample data inserted!")

def reset_database():
    """
    Reset the database by dropping all tables and recreating them.
    
    WARNING: This will delete all existing data!
    """
    state_dir = Path(__file__).parent.parent / 'state'
    db_path = state_dir / 'bot_state.db'
    
    if db_path.exists():
        db_path.unlink()
        print(f"🗑️  Deleted existing database: {db_path}")
    
    init_database()

def main():
    """
    Main function to run database initialization.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Initialization Tool')
    parser.add_argument('--reset', action='store_true', help='Reset database (delete all data)')
    
    args = parser.parse_args()
    
    if args.reset:
        print("⚠️  WARNING: This will delete all existing data!")
        confirm = input("Are you sure you want to reset the database? (y/N): ")
        if confirm.lower() == 'y':
            reset_database()
        else:
            print("Database reset cancelled.")
    else:
        init_database()

if __name__ == '__main__':
    main()
