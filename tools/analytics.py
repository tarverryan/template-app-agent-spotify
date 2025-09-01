"""
Advanced Analytics System for Spotify App Agent Template

This script provides comprehensive analytics and monitoring capabilities
for the Spotify bot, including performance metrics, playlist analytics,
and trend analysis.

LEARNING OBJECTIVES:
- Understand data analysis and visualization
- Learn about time-series data processing
- Practice working with multiple data sources
- Understand performance monitoring and metrics
- Learn about trend analysis and pattern recognition
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import yaml
from collections import defaultdict, Counter
import numpy as np

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from spotify_client import SpotifyClient

class SpotifyAnalytics:
    """
    Comprehensive analytics system for Spotify bot performance and insights.
    
    This class provides methods for analyzing bot performance, playlist metrics,
    track popularity trends, and user engagement patterns.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the analytics system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        self.config = self._load_config()
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'bot_state.db')
        self.snapshots_dir = os.path.join(os.path.dirname(__file__), '..', 'snapshots')
        self.analytics_dir = os.path.join(os.path.dirname(__file__), '..', 'analytics')
        
        # Create analytics directory if it doesn't exist
        Path(self.analytics_dir).mkdir(exist_ok=True)
        
        # Ensure database exists
        self._ensure_database_exists()
        
        # Initialize Spotify client
        try:
            self.spotify_client = SpotifyClient()
            self.spotify_client.authenticate()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Spotify client: {e}")
            self.spotify_client = None
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}
    
    def _ensure_database_exists(self):
        """Ensure database exists and is properly initialized."""
        try:
            # Create state directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Check if database exists and has tables
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if bot_runs table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bot_runs'")
            if not cursor.fetchone():
                print("🗄️  Database not initialized, creating tables...")
                self._create_database_tables(cursor)
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error ensuring database exists: {e}")
    
    def _create_database_tables(self, cursor):
        """Create database tables."""
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
                genres TEXT,
                artists TEXT,
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
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_runs_start_time ON bot_runs(start_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_runs_status ON bot_runs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_playlist_snapshots_time ON playlist_snapshots(snapshot_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_playlist_snapshots_type ON playlist_snapshots(playlist_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_track_history_date ON track_history(added_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_track_history_playlist ON track_history(playlist_type)')
        
        print("✅ Database tables created successfully!")
    
    def get_bot_performance_metrics(self, days=30):
        """
        Get comprehensive bot performance metrics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict: Performance metrics
        """
        print("📊 Analyzing bot performance metrics...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get run statistics
            runs_df = pd.read_sql_query("""
                SELECT 
                    run_id,
                    playlist_type,
                    start_time,
                    end_time,
                    status,
                    tracks_added,
                    tracks_removed,
                    error_message
                FROM bot_runs 
                WHERE start_time >= datetime('now', '-{} days')
                ORDER BY start_time DESC
            """.format(days), conn)
            
            # Calculate metrics
            total_runs = len(runs_df)
            successful_runs = len(runs_df[runs_df['status'] == 'success'])
            failed_runs = len(runs_df[runs_df['status'] == 'failed'])
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            # Average execution time
            runs_df['duration'] = pd.to_datetime(runs_df['end_time']) - pd.to_datetime(runs_df['start_time'])
            avg_duration = runs_df['duration'].mean()
            
            # Tracks processed
            total_tracks_added = runs_df['tracks_added'].sum()
            total_tracks_removed = runs_df['tracks_removed'].sum()
            
            # Error analysis
            error_counts = runs_df['error_message'].value_counts()
            
            metrics = {
                'total_runs': total_runs,
                'successful_runs': successful_runs,
                'failed_runs': failed_runs,
                'success_rate': round(success_rate, 2),
                'avg_duration': str(avg_duration).split('.')[0] if pd.notna(avg_duration) else 'N/A',
                'total_tracks_added': total_tracks_added,
                'total_tracks_removed': total_tracks_removed,
                'net_tracks': total_tracks_added - total_tracks_removed,
                'top_errors': error_counts.head(5).to_dict() if len(error_counts) > 0 else {}
            }
            
            conn.close()
            return metrics
            
        except Exception as e:
            print(f"❌ Error getting performance metrics: {e}")
            return {}
    
    def get_playlist_analytics(self, playlist_type=None):
        """
        Get detailed analytics for playlists.
        
        Args:
            playlist_type: Specific playlist type to analyze
            
        Returns:
            dict: Playlist analytics
        """
        print("📋 Analyzing playlist performance...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get playlist snapshots
            query = """
                SELECT 
                    playlist_id,
                    playlist_type,
                    snapshot_time,
                    track_count,
                    total_duration,
                    avg_popularity,
                    genres,
                    artists
                FROM playlist_snapshots
            """
            
            if playlist_type:
                query += f" WHERE playlist_type = '{playlist_type}'"
            
            query += " ORDER BY snapshot_time DESC"
            
            snapshots_df = pd.read_sql_query(query, conn)
            
            if len(snapshots_df) == 0:
                print("⚠️  No playlist snapshots found")
                return {}
            
            # Analyze trends
            analytics = {}
            
            for playlist_type in snapshots_df['playlist_type'].unique():
                playlist_data = snapshots_df[snapshots_df['playlist_type'] == playlist_type]
                
                # Track count trends
                track_count_trend = playlist_data.groupby('snapshot_time')['track_count'].mean()
                
                # Popularity trends
                popularity_trend = playlist_data.groupby('snapshot_time')['avg_popularity'].mean()
                
                # Genre diversity
                genre_data = []
                for _, row in playlist_data.iterrows():
                    if row['genres']:
                        genres = json.loads(row['genres'])
                        genre_data.extend(genres)
                
                genre_diversity = Counter(genre_data)
                
                # Artist diversity
                artist_data = []
                for _, row in playlist_data.iterrows():
                    if row['artists']:
                        artists = json.loads(row['artists'])
                        artist_data.extend(artists)
                
                artist_diversity = Counter(artist_data)
                
                analytics[playlist_type] = {
                    'track_count_trend': track_count_trend.to_dict(),
                    'popularity_trend': popularity_trend.to_dict(),
                    'genre_diversity': dict(genre_diversity.most_common(10)),
                    'artist_diversity': dict(artist_diversity.most_common(10)),
                    'total_snapshots': len(playlist_data),
                    'avg_track_count': playlist_data['track_count'].mean(),
                    'avg_popularity': playlist_data['avg_popularity'].mean()
                }
            
            conn.close()
            return analytics
            
        except Exception as e:
            print(f"❌ Error getting playlist analytics: {e}")
            return {}
    
    def get_track_popularity_trends(self, days=30):
        """
        Analyze track popularity trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict: Popularity trend data
        """
        print("📈 Analyzing track popularity trends...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get track data from snapshots
            tracks_df = pd.read_sql_query("""
                SELECT 
                    track_id,
                    track_name,
                    artist_name,
                    popularity,
                    added_date,
                    playlist_type
                FROM track_history 
                WHERE added_date >= datetime('now', '-{} days')
                ORDER BY added_date DESC
            """.format(days), conn)
            
            if len(tracks_df) == 0:
                print("⚠️  No track history found")
                return {}
            
            # Analyze popularity trends
            trends = {}
            
            # Overall popularity trend
            daily_popularity = tracks_df.groupby('added_date')['popularity'].mean()
            trends['overall_popularity'] = daily_popularity.to_dict()
            
            # Popularity by playlist type
            for playlist_type in tracks_df['playlist_type'].unique():
                playlist_tracks = tracks_df[tracks_df['playlist_type'] == playlist_type]
                playlist_popularity = playlist_tracks.groupby('added_date')['popularity'].mean()
                trends[f'{playlist_type}_popularity'] = playlist_popularity.to_dict()
            
            # Top tracks by popularity
            top_tracks = tracks_df.groupby(['track_id', 'track_name', 'artist_name'])['popularity'].mean().sort_values(ascending=False).head(20)
            trends['top_tracks'] = top_tracks.to_dict()
            
            # Popularity distribution
            popularity_bins = [0, 20, 40, 60, 80, 100]
            popularity_labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
            tracks_df['popularity_category'] = pd.cut(tracks_df['popularity'], bins=popularity_bins, labels=popularity_labels)
            popularity_distribution = tracks_df['popularity_category'].value_counts()
            trends['popularity_distribution'] = popularity_distribution.to_dict()
            
            conn.close()
            return trends
            
        except Exception as e:
            print(f"❌ Error getting popularity trends: {e}")
            return {}
    
    def get_genre_analysis(self):
        """
        Analyze genre patterns and trends.
        
        Returns:
            dict: Genre analysis data
        """
        print("🎵 Analyzing genre patterns...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get genre data from snapshots
            snapshots_df = pd.read_sql_query("""
                SELECT genres, playlist_type, snapshot_time
                FROM playlist_snapshots
                WHERE genres IS NOT NULL
            """, conn)
            
            if len(snapshots_df) == 0:
                print("⚠️  No genre data found")
                return {}
            
            # Analyze genres
            all_genres = []
            genre_by_playlist = defaultdict(list)
            
            for _, row in snapshots_df.iterrows():
                if row['genres']:
                    genres = json.loads(row['genres'])
                    all_genres.extend(genres)
                    genre_by_playlist[row['playlist_type']].extend(genres)
            
            # Overall genre distribution
            genre_distribution = Counter(all_genres)
            
            # Genre by playlist type
            playlist_genres = {}
            for playlist_type, genres in genre_by_playlist.items():
                playlist_genres[playlist_type] = dict(Counter(genres).most_common(10))
            
            # Genre diversity over time
            genre_timeline = defaultdict(list)
            for _, row in snapshots_df.iterrows():
                if row['genres']:
                    genres = json.loads(row['genres'])
                    date = row['snapshot_time'][:10]  # Extract date
                    genre_timeline[date].extend(genres)
            
            # Calculate diversity for each date
            diversity_timeline = {}
            for date, genres in genre_timeline.items():
                diversity_timeline[date] = len(set(genres))
            
            analysis = {
                'overall_genre_distribution': dict(genre_distribution.most_common(20)),
                'playlist_genre_distribution': playlist_genres,
                'genre_diversity_timeline': diversity_timeline,
                'total_unique_genres': len(set(all_genres)),
                'most_common_genres': dict(genre_distribution.most_common(10))
            }
            
            conn.close()
            return analysis
            
        except Exception as e:
            print(f"❌ Error getting genre analysis: {e}")
            return {}
    
    def generate_analytics_report(self, output_format='json'):
        """
        Generate a comprehensive analytics report.
        
        Args:
            output_format: 'json', 'html', or 'pdf'
            
        Returns:
            str: Path to generated report
        """
        print("📊 Generating comprehensive analytics report...")
        
        # Collect all analytics data
        performance_metrics = self.get_bot_performance_metrics()
        playlist_analytics = self.get_playlist_analytics()
        popularity_trends = self.get_track_popularity_trends()
        genre_analysis = self.get_genre_analysis()
        
        # Compile report
        report = {
            'generated_at': datetime.now().isoformat(),
            'performance_metrics': performance_metrics,
            'playlist_analytics': playlist_analytics,
            'popularity_trends': popularity_trends,
            'genre_analysis': genre_analysis,
            'summary': {
                'total_playlists_analyzed': len(playlist_analytics),
                'success_rate': performance_metrics.get('success_rate', 0),
                'total_tracks_processed': performance_metrics.get('total_tracks_added', 0),
                'unique_genres_found': genre_analysis.get('total_unique_genres', 0)
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            report_path = os.path.join(self.analytics_dir, f'analytics_report_{timestamp}.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
        
        elif output_format == 'html':
            report_path = self._generate_html_report(report, timestamp)
        
        else:
            report_path = os.path.join(self.analytics_dir, f'analytics_report_{timestamp}.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
        
        print(f"✅ Analytics report generated: {report_path}")
        return report_path
    
    def _generate_html_report(self, report_data, timestamp):
        """Generate an HTML analytics report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spotify Bot Analytics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #1DB954; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; border-radius: 3px; }}
                .chart {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎵 Spotify Bot Analytics Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📊 Performance Summary</h2>
                <div class="metric">
                    <strong>Success Rate:</strong> {report_data['performance_metrics'].get('success_rate', 0)}%
                </div>
                <div class="metric">
                    <strong>Total Runs:</strong> {report_data['performance_metrics'].get('total_runs', 0)}
                </div>
                <div class="metric">
                    <strong>Tracks Added:</strong> {report_data['performance_metrics'].get('total_tracks_added', 0)}
                </div>
                <div class="metric">
                    <strong>Unique Genres:</strong> {report_data['summary']['unique_genres_found']}
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Playlist Analytics</h2>
                <p>Analyzed {report_data['summary']['total_playlists_analyzed']} playlists</p>
                <!-- Add playlist-specific charts here -->
            </div>
            
            <div class="section">
                <h2>📈 Popularity Trends</h2>
                <p>Track popularity analysis over time</p>
                <!-- Add popularity trend charts here -->
            </div>
            
            <div class="section">
                <h2>🎵 Genre Analysis</h2>
                <p>Genre distribution and diversity analysis</p>
                <!-- Add genre charts here -->
            </div>
        </body>
        </html>
        """
        
        report_path = os.path.join(self.analytics_dir, f'analytics_report_{timestamp}.html')
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        return report_path
    
    def create_visualizations(self):
        """Create visualizations for analytics data."""
        print("📊 Creating analytics visualizations...")
        
        try:
            # Set up plotting style
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # Get data
            performance_metrics = self.get_bot_performance_metrics()
            playlist_analytics = self.get_playlist_analytics()
            popularity_trends = self.get_track_popularity_trends()
            genre_analysis = self.get_genre_analysis()
            
            # Create visualizations
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Spotify Bot Analytics Dashboard', fontsize=16, fontweight='bold')
            
            # 1. Performance Metrics
            if performance_metrics:
                ax1 = axes[0, 0]
                metrics = ['Success Rate', 'Failed Runs', 'Successful Runs']
                values = [
                    performance_metrics.get('success_rate', 0),
                    performance_metrics.get('failed_runs', 0),
                    performance_metrics.get('successful_runs', 0)
                ]
                colors = ['#1DB954', '#FF6B6B', '#4ECDC4']
                ax1.bar(metrics, values, color=colors)
                ax1.set_title('Bot Performance Metrics')
                ax1.set_ylabel('Count / Percentage')
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # 2. Genre Distribution
            if genre_analysis and 'overall_genre_distribution' in genre_analysis:
                ax2 = axes[0, 1]
                genres = list(genre_analysis['overall_genre_distribution'].keys())[:10]
                counts = list(genre_analysis['overall_genre_distribution'].values())[:10]
                ax2.pie(counts, labels=genres, autopct='%1.1f%%', startangle=90)
                ax2.set_title('Top 10 Genres')
            
            # 3. Popularity Distribution
            if popularity_trends and 'popularity_distribution' in popularity_trends:
                ax3 = axes[1, 0]
                categories = list(popularity_trends['popularity_distribution'].keys())
                values = list(popularity_trends['popularity_distribution'].values())
                ax3.bar(categories, values, color='#1DB954')
                ax3.set_title('Track Popularity Distribution')
                ax3.set_ylabel('Number of Tracks')
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            
            # 4. Playlist Performance
            if playlist_analytics:
                ax4 = axes[1, 1]
                playlists = list(playlist_analytics.keys())
                avg_popularities = [data.get('avg_popularity', 0) for data in playlist_analytics.values()]
                ax4.bar(playlists, avg_popularities, color='#FF6B6B')
                ax4.set_title('Average Playlist Popularity')
                ax4.set_ylabel('Average Popularity Score')
                plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Save visualization
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            viz_path = os.path.join(self.analytics_dir, f'analytics_dashboard_{timestamp}.png')
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Analytics visualization saved: {viz_path}")
            return viz_path
            
        except Exception as e:
            print(f"❌ Error creating visualizations: {e}")
            return None

def main():
    """
    Main function to run analytics.
    
    This function provides a command-line interface for running
    various analytics operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Spotify Bot Analytics System')
    parser.add_argument('--performance', action='store_true', help='Show performance metrics')
    parser.add_argument('--playlists', action='store_true', help='Show playlist analytics')
    parser.add_argument('--trends', action='store_true', help='Show popularity trends')
    parser.add_argument('--genres', action='store_true', help='Show genre analysis')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive report')
    parser.add_argument('--visualize', action='store_true', help='Create visualizations')
    parser.add_argument('--format', choices=['json', 'html'], default='json', help='Report format')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    args = parser.parse_args()
    
    # Initialize analytics
    analytics = SpotifyAnalytics()
    
    print("🎵 Spotify Bot Analytics System")
    print("=" * 50)
    
    # Run requested analytics
    if args.performance:
        metrics = analytics.get_bot_performance_metrics(args.days)
        print("\n📊 Performance Metrics:")
        print(json.dumps(metrics, indent=2))
    
    if args.playlists:
        playlist_data = analytics.get_playlist_analytics()
        print("\n📋 Playlist Analytics:")
        print(json.dumps(playlist_data, indent=2))
    
    if args.trends:
        trends = analytics.get_track_popularity_trends(args.days)
        print("\n📈 Popularity Trends:")
        print(json.dumps(trends, indent=2))
    
    if args.genres:
        genre_data = analytics.get_genre_analysis()
        print("\n🎵 Genre Analysis:")
        print(json.dumps(genre_data, indent=2))
    
    if args.report:
        report_path = analytics.generate_analytics_report(args.format)
        print(f"\n📄 Report generated: {report_path}")
    
    if args.visualize:
        viz_path = analytics.create_visualizations()
        if viz_path:
            print(f"\n📊 Visualization created: {viz_path}")
    
    # If no specific options, run comprehensive analysis
    if not any([args.performance, args.playlists, args.trends, args.genres, args.report, args.visualize]):
        print("Running comprehensive analytics...")
        
        # Performance metrics
        metrics = analytics.get_bot_performance_metrics()
        print(f"\n📊 Success Rate: {metrics.get('success_rate', 0)}%")
        print(f"📊 Total Runs: {metrics.get('total_runs', 0)}")
        print(f"📊 Tracks Added: {metrics.get('total_tracks_added', 0)}")
        
        # Generate report
        report_path = analytics.generate_analytics_report()
        print(f"\n📄 Full report: {report_path}")
        
        # Create visualizations
        viz_path = analytics.create_visualizations()
        if viz_path:
            print(f"📊 Dashboard: {viz_path}")

if __name__ == "__main__":
    main()
