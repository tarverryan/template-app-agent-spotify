"""
Spotify App Agent Template - Main Application
Main entry point for the automated playlist curation system.

This module provides the main SpotifyBot class that orchestrates all components
including the Spotify client, track selector, and playlist manager.
"""

import os
import sys
import logging
import signal
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .spotify_client import SpotifyClient
from .track_selector_enhanced import EnhancedTrackSelector as TrackSelector
from .playlist_manager import PlaylistManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/spotify_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SpotifyBot:
    """
    Main application class for the Spotify App Agent Template.
    
    This class orchestrates all components including initialization, scheduling,
    and graceful shutdown handling.
    """
    
    def __init__(self, config_path: str = "/app/config/config.yaml") -> None:
        """
        Initialize the bot with configuration.
        
        Args:
            config_path: Path to the configuration YAML file
            
        Raises:
            ValueError: If required environment variables are missing
            FileNotFoundError: If configuration file cannot be loaded
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.spotify_client: Optional[SpotifyClient] = None
        self.track_selector: Optional[TrackSelector] = None
        self.playlist_manager: Optional[PlaylistManager] = None
        self.running = False
        
        # Load environment variables
        load_dotenv()
        
        # Validate environment
        self._validate_environment()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _validate_environment(self) -> None:
        """
        Validate required environment variables.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = [
            'SPOTIFY_CLIENT_ID',
            'SPOTIFY_CLIENT_SECRET', 
            'SPOTIFY_REFRESH_TOKEN',
            'SPOTIFY_USER_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {missing_vars}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Environment validation passed")
    
    def initialize(self) -> None:
        """
        Initialize all components.
        
        This method sets up the Spotify client, track selector, and playlist manager.
        It also tests the Spotify connection to ensure credentials are valid.
        
        Raises:
            Exception: If any component fails to initialize
        """
        try:
            logger.info("Initializing Spotify App Agent...")
            
            # Initialize Spotify client
            self.spotify_client = SpotifyClient()
            
            # Test Spotify connection
            user_profile = self.spotify_client.get_user_profile()
            display_name = user_profile.get('display_name', 'Unknown')
            logger.info(f"Connected to Spotify as: {display_name}")
            
            # Initialize track selector
            self.track_selector = TrackSelector(self.spotify_client, self.config)
            
            # Initialize playlist manager
            self.playlist_manager = PlaylistManager(
                self.spotify_client, 
                self.track_selector, 
                self.config
            )
            
            logger.info("Bot initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    def start(self) -> None:
        """
        Start the bot and scheduler.
        
        This method starts the playlist manager scheduler and begins
        automated playlist updates according to the configured schedule.
        """
        try:
            if not all([self.spotify_client, self.track_selector, self.playlist_manager]):
                raise RuntimeError("Bot not initialized. Call initialize() first.")
            
            logger.info("Starting Spotify App Agent...")
            
            # Start the scheduler
            self.playlist_manager.start_scheduler()
            
            self.running = True
            logger.info("Bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    def stop(self) -> None:
        """
        Stop the bot and scheduler gracefully.
        """
        try:
            if self.running and self.playlist_manager:
                logger.info("Stopping Spotify App Agent...")
                self.playlist_manager.stop_scheduler()
                self.running = False
                logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    def run(self) -> None:
        """
        Run the bot in the main thread.
        
        This method starts the bot and keeps it running until interrupted.
        It sets up signal handlers for graceful shutdown.
        """
        try:
            # Set up signal handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # Start the bot
            self.start()
            
            # Keep running until interrupted
            try:
                while self.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
            finally:
                self.stop()
                
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def run_manual_update(self, playlist_type: str) -> None:
        """
        Run a manual update for a specific playlist type.
        
        Args:
            playlist_type: Type of playlist to update ('daily', 'weekly', 'monthly', 'yearly')
            
        Raises:
            ValueError: If playlist_type is invalid
        """
        valid_types = ['daily', 'weekly', 'monthly', 'yearly']
        if playlist_type not in valid_types:
            raise ValueError(f"Invalid playlist type. Must be one of: {valid_types}")
        
        try:
            logger.info(f"Running manual update for {playlist_type} playlist")
            # Initialize if not already done
            if not self.playlist_manager:
                self.initialize()
            
            self.playlist_manager.update_playlist(playlist_type)
            logger.info(f"Manual update completed for {playlist_type}")
        except Exception as e:
            logger.error(f"Manual update failed for {playlist_type}: {e}")
            raise


def main() -> None:
    """Main entry point for the application."""
    try:
        bot = SpotifyBot()
        bot.initialize()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
