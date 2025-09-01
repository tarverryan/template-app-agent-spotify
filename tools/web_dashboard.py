"""
Web Dashboard for Spotify App Agent Template

This script provides a web-based dashboard for monitoring and managing
the Spotify bot, including real-time status, configuration management,
and analytics visualization.

LEARNING OBJECTIVES:
- Understand web application development with Flask
- Learn about real-time monitoring and dashboards
- Practice working with web APIs and JSON
- Understand user interface design and UX
- Learn about data visualization in web applications
"""

import os
import sys
import json
import yaml
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import threading
import time
from prometheus_client import generate_latest, Counter, Histogram, Gauge, CONTENT_TYPE_LATEST

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from spotify_client import SpotifyClient
from analytics import SpotifyAnalytics

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('DASHBOARD_SECRET_KEY', 'your-secret-key-change-this')
socketio = SocketIO(app, cors_allowed_origins="*")

class DashboardManager:
    """
    Manages the dashboard functionality and data.
    
    This class handles all dashboard operations including data collection,
    real-time updates, and configuration management.
    """
    
    def __init__(self):
        """Initialize the dashboard manager."""
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'bot_state.db')
        self.config = self._load_config()
        
        # Auto-initialize database if it doesn't exist
        self._ensure_database_exists()
        
        self.analytics = SpotifyAnalytics()
        
        # Initialize Prometheus metrics
        self._init_metrics()
        
        # Initialize Spotify client
        try:
            self.spotify_client = SpotifyClient()
            self.spotify_client.authenticate()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Spotify client: {e}")
            self.spotify_client = None
    
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Counters
        self.metrics = {
            'http_requests_total': Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint']),
            'playlist_updates_total': Counter('playlist_updates_total', 'Total playlist updates', ['playlist_type', 'status']),
            'api_calls_total': Counter('api_calls_total', 'Total API calls', ['service', 'endpoint']),
            'errors_total': Counter('errors_total', 'Total errors', ['type']),
            
            # Histograms
            'http_request_duration_seconds': Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint']),
            'playlist_update_duration_seconds': Histogram('playlist_update_duration_seconds', 'Playlist update duration', ['playlist_type']),
            'api_call_duration_seconds': Histogram('api_call_duration_seconds', 'API call duration', ['service']),
            
            # Gauges
            'active_playlists': Gauge('active_playlists', 'Number of active playlists'),
            'total_tracks': Gauge('total_tracks', 'Total number of tracks across all playlists'),
            'bot_status': Gauge('bot_status', 'Bot status (1=running, 0=stopped)'),
            'database_connections': Gauge('database_connections', 'Number of active database connections')
        }
    
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
    
    def get_bot_status(self):
        """Get current bot status and health."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get latest run
            latest_run = conn.execute("""
                SELECT * FROM bot_runs 
                ORDER BY start_time DESC 
                LIMIT 1
            """).fetchone()
            
            # Get recent runs
            recent_runs = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM bot_runs 
                WHERE start_time >= datetime('now', '-24 hours')
                GROUP BY status
            """).fetchall()
            
            # Calculate health metrics
            total_runs_24h = sum(count for _, count in recent_runs)
            successful_runs_24h = sum(count for status, count in recent_runs if status == 'success')
            success_rate_24h = (successful_runs_24h / total_runs_24h * 100) if total_runs_24h > 0 else 0
            
            # Check Spotify connection
            spotify_status = "connected" if self.spotify_client else "disconnected"
            
            status = {
                'last_run': latest_run[2] if latest_run else None,
                'last_status': latest_run[4] if latest_run else 'unknown',
                'success_rate_24h': round(success_rate_24h, 2),
                'total_runs_24h': total_runs_24h,
                'spotify_status': spotify_status,
                'uptime': self._get_uptime(),
                'health': 'healthy' if success_rate_24h > 80 else 'warning' if success_rate_24h > 50 else 'critical'
            }
            
            conn.close()
            return status
            
        except Exception as e:
            print(f"❌ Error getting bot status: {e}")
            return {
                'last_run': None,
                'last_status': 'error',
                'success_rate_24h': 0,
                'total_runs_24h': 0,
                'spotify_status': 'error',
                'uptime': 'unknown',
                'health': 'critical'
            }
    
    def _get_uptime(self):
        """Get bot uptime information."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get first run
            first_run = conn.execute("""
                SELECT start_time FROM bot_runs 
                ORDER BY start_time ASC 
                LIMIT 1
            """).fetchone()
            
            if first_run:
                first_run_time = datetime.fromisoformat(first_run[0].replace('Z', '+00:00'))
                uptime = datetime.now() - first_run_time
                return str(uptime).split('.')[0]
            
            conn.close()
            return "unknown"
            
        except Exception as e:
            return "unknown"
    
    def get_playlist_status(self):
        """Get current playlist status and information."""
        try:
            playlists = self.config.get('playlists', {})
            playlist_status = {}
            
            for playlist_key, playlist_config in playlists.items():
                playlist_id = playlist_config.get('id', '')
                
                if not playlist_id or playlist_id.startswith('your-'):
                    playlist_status[playlist_key] = {
                        'status': 'not_configured',
                        'name': 'Not Configured',
                        'track_count': 0,
                        'last_updated': None
                    }
                    continue
                
                try:
                    if self.spotify_client:
                        playlist = self.spotify_client.get_playlist(playlist_id)
                        if playlist:
                            playlist_status[playlist_key] = {
                                'status': 'active',
                                'name': playlist.get('name', 'Unknown'),
                                'track_count': playlist.get('tracks', {}).get('total', 0),
                                'last_updated': datetime.now().isoformat(),
                                'public': playlist.get('public', False)
                            }
                        else:
                            playlist_status[playlist_key] = {
                                'status': 'error',
                                'name': 'Error',
                                'track_count': 0,
                                'last_updated': None
                            }
                    else:
                        playlist_status[playlist_key] = {
                            'status': 'disconnected',
                            'name': 'Disconnected',
                            'track_count': 0,
                            'last_updated': None
                        }
                        
                except Exception as e:
                    playlist_status[playlist_key] = {
                        'status': 'error',
                        'name': f'Error: {str(e)}',
                        'track_count': 0,
                        'last_updated': None
                    }
            
            return playlist_status
            
        except Exception as e:
            print(f"❌ Error getting playlist status: {e}")
            return {}
    
    def get_recent_activity(self, limit=10):
        """Get recent bot activity."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            recent_activity = conn.execute("""
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
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            activity = []
            for row in recent_activity:
                activity.append({
                    'run_id': row[0],
                    'playlist_type': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'status': row[4],
                    'tracks_added': row[5],
                    'tracks_removed': row[6],
                    'error_message': row[7]
                })
            
            conn.close()
            return activity
            
        except Exception as e:
            print(f"❌ Error getting recent activity: {e}")
            return []
    
    def get_analytics_summary(self):
        """Get analytics summary for dashboard."""
        try:
            performance_metrics = self.analytics.get_bot_performance_metrics(7)  # Last 7 days
            playlist_analytics = self.analytics.get_playlist_analytics()
            genre_analysis = self.analytics.get_genre_analysis()
            
            summary = {
                'performance': performance_metrics,
                'playlists': len(playlist_analytics),
                'unique_genres': genre_analysis.get('total_unique_genres', 0),
                'top_genres': list(genre_analysis.get('most_common_genres', {}).keys())[:5]
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ Error getting analytics summary: {e}")
            return {}

# Initialize dashboard manager
dashboard_manager = DashboardManager()

@app.route('/')
def index():
    """Main dashboard page."""
    bot_status = dashboard_manager.get_bot_status()
    playlist_status = dashboard_manager.get_playlist_status()
    recent_activity = dashboard_manager.get_recent_activity()
    analytics_summary = dashboard_manager.get_analytics_summary()
    
    return render_template('dashboard.html',
                         bot_status=bot_status,
                         playlist_status=playlist_status,
                         recent_activity=recent_activity,
                         analytics_summary=analytics_summary)

@app.route('/api/status')
def api_status():
    """API endpoint for bot status."""
    return jsonify(dashboard_manager.get_bot_status())

@app.route('/api/playlists')
def api_playlists():
    """API endpoint for playlist status."""
    return jsonify(dashboard_manager.get_playlist_status())

@app.route('/api/activity')
def api_activity():
    """API endpoint for recent activity."""
    limit = request.args.get('limit', 10, type=int)
    return jsonify(dashboard_manager.get_recent_activity(limit))

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics summary."""
    return jsonify(dashboard_manager.get_analytics_summary())

@app.route('/config')
def config_page():
    """Configuration management page."""
    config = dashboard_manager.config
    return render_template('config.html', config=config)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API endpoint for configuration management."""
    if request.method == 'POST':
        try:
            new_config = request.json
            
            # Validate configuration
            if 'persona' not in new_config or 'playlists' not in new_config:
                return jsonify({'error': 'Invalid configuration format'}), 400
            
            # Save configuration
            with open(dashboard_manager.config_path, 'w') as f:
                yaml.dump(new_config, f, default_flow_style=False)
            
            # Reload configuration
            dashboard_manager.config = new_config
            
            return jsonify({'success': True, 'message': 'Configuration updated successfully'})
            
        except Exception as e:
            return jsonify({'error': f'Failed to update configuration: {str(e)}'}), 500
    
    else:
        return jsonify(dashboard_manager.config)

@app.route('/analytics')
def analytics_page():
    """Analytics page with detailed charts."""
    return render_template('analytics.html')

@app.route('/api/analytics/detailed')
def api_analytics_detailed():
    """API endpoint for detailed analytics."""
    try:
        performance_metrics = dashboard_manager.analytics.get_bot_performance_metrics()
        playlist_analytics = dashboard_manager.analytics.get_playlist_analytics()
        popularity_trends = dashboard_manager.analytics.get_track_popularity_trends()
        genre_analysis = dashboard_manager.analytics.get_genre_analysis()
        
        return jsonify({
            'performance': performance_metrics,
            'playlists': playlist_analytics,
            'popularity': popularity_trends,
            'genres': genre_analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get analytics: {str(e)}'}), 500

@app.route('/logs')
def logs_page():
    """Logs viewing page."""
    return render_template('logs.html')

@app.route('/api/logs')
def api_logs():
    """API endpoint for log retrieval."""
    try:
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'spotify_bot.log')
        
        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'error': 'Log file not found'})
        
        # Get last N lines
        lines = request.args.get('lines', 100, type=int)
        
        with open(log_file, 'r') as f:
            log_lines = f.readlines()[-lines:]
        
        return jsonify({'logs': log_lines})
        
    except Exception as e:
        return jsonify({'error': f'Failed to get logs: {str(e)}'}), 500

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    try:
        # Generate metrics
        metrics_data = generate_latest()
        return metrics_data, 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except Exception as e:
        return f"Error generating metrics: {str(e)}", 500

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Basic health check
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected' if os.path.exists(dashboard_manager.db_path) else 'disconnected',
            'spotify_client': 'connected' if dashboard_manager.spotify_client else 'disconnected'
        }
        return jsonify(health_status), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

def background_updates():
    """Background task for real-time updates."""
    while True:
        try:
            # Get updated status
            bot_status = dashboard_manager.get_bot_status()
            playlist_status = dashboard_manager.get_playlist_status()
            
            # Emit updates via WebSocket
            socketio.emit('status_update', {
                'bot_status': bot_status,
                'playlist_status': playlist_status,
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            print(f"❌ Error in background updates: {e}")
            time.sleep(60)  # Wait longer on error

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    print('Client connected')
    emit('connected', {'message': 'Connected to dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print('Client disconnected')

if __name__ == '__main__':
    # Start background update thread
    update_thread = threading.Thread(target=background_updates, daemon=True)
    update_thread.start()
    
    # Try different ports if 5000 is in use (macOS AirPlay uses 5000)
    ports = [5001, 5002, 5003, 5004, 5005]
    for port in ports:
        try:
            print(f"🌐 Starting Spotify Bot Web Dashboard on port {port}...")
            print(f"📊 Dashboard available at: http://localhost:{port}")
            print(f"📈 Analytics at: http://localhost:{port}/analytics")
            print(f"⚙️  Configuration at: http://localhost:{port}/config")
            print(f"📝 Logs at: http://localhost:{port}/logs")
            socketio.run(app, host='0.0.0.0', port=port, debug=True)
            break
        except OSError as e:
            if "Address already in use" in str(e) and port < ports[-1]:
                print(f"⚠️  Port {port} in use, trying next port...")
                continue
            else:
                print(f"❌ Failed to start dashboard: {e}")
                raise e
