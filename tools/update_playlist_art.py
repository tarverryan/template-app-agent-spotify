#!/usr/bin/env python3
"""
Script to update playlist cover art with images from playlist_art folder

This script allows you to customize the cover art for your Spotify playlists
by uploading custom images. It handles image processing, resizing, and
uploading to Spotify's API.

LEARNING OBJECTIVES:
- Understand image processing and manipulation
- Learn about file handling and binary data
- Practice working with external APIs for file uploads
- Understand base64 encoding and data transmission
- Learn about image format requirements and constraints
"""

import os
import sys
import yaml
import base64
from PIL import Image
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

def get_playlist_art_mapping(config):
    """
    Create a mapping of playlist IDs to cover art files.
    
    This function creates a dictionary mapping playlist IDs to their
    corresponding cover art image files.
    
    Args:
        config: The configuration data
        
    Returns:
        dict: Mapping of playlist IDs to image file paths
    """
    # Define image file mapping based on playlist types
    image_mapping = {
        'playlist1': 'playlist_art/your_bot_playlist1.png',
        'playlist2': 'playlist_art/your_bot_playlist2.png',
        'playlist3': 'playlist_art/your_bot_playlist3.png',
        'playlist4': 'playlist_art/your_bot_playlist4.png'
    }
    
    # Create mapping from playlist IDs to image files
    playlist_art_mapping = {}
    playlists = config.get('playlists', {})
    
    for playlist_key, playlist_config in playlists.items():
        playlist_id = playlist_config.get('id', '')
        
        # Skip if playlist ID is not configured or is a placeholder
        if not playlist_id or playlist_id.startswith('your-') or playlist_id.endswith('-id'):
            continue
            
        if playlist_key in image_mapping:
            image_path = image_mapping[playlist_key]
            playlist_art_mapping[playlist_id] = image_path
    
    return playlist_art_mapping

def process_image(image_path, target_size=(300, 300)):
    """
    Process and resize an image for Spotify playlist cover art.
    
    This function loads an image, resizes it to the required dimensions,
    and converts it to JPEG format for upload to Spotify.
    
    Args:
        image_path: Path to the source image file
        target_size: Target dimensions (width, height)
        
    Returns:
        bytes: Processed image data in JPEG format
    """
    try:
        # Open and process the image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (JPEG doesn't support transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize the image
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save to bytes in JPEG format
            import io
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
    except Exception as e:
        print(f"❌ Error processing image {image_path}: {e}")
        return None

def update_playlist_art(spotify_client, playlist_id, image_path):
    """
    Update a playlist's cover art with a custom image.
    
    This function uploads a custom image to replace the playlist's
    cover art on Spotify.
    
    Args:
        spotify_client: The Spotify client instance
        playlist_id: The ID of the playlist to update
        image_path: Path to the image file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if image file exists
        if not os.path.exists(image_path):
            print(f"⚠️  Image file not found: {image_path}")
            print("   Please create custom images in the playlist_art folder")
            return False
        
        print(f"🎨 Processing image: {image_path}")
        
        # Process the image
        image_data = process_image(image_path)
        if not image_data:
            print(f"❌ Failed to process image: {image_path}")
            return False
        
        # Encode image data as base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Upload to Spotify
        success = spotify_client.upload_playlist_cover_image(playlist_id, image_base64)
        
        if success:
            print(f"✅ Updated cover art for playlist {playlist_id}")
            return True
        else:
            print(f"❌ Failed to update cover art for playlist {playlist_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating playlist art for {playlist_id}: {e}")
        return False

def create_sample_images():
    """
    Create sample cover art images for playlists.
    
    This function creates simple placeholder images that users can
    customize for their playlists.
    """
    playlist_art_dir = Path("playlist_art")
    playlist_art_dir.mkdir(exist_ok=True)
    
    # Create sample images for each playlist type
    sample_images = {
        'your_bot_playlist1.png': 'Playlist 1',
        'your_bot_playlist2.png': 'Playlist 2', 
        'your_bot_playlist3.png': 'Playlist 3',
        'your_bot_playlist4.png': 'Playlist 4'
    }
    
    for filename, text in sample_images.items():
        image_path = playlist_art_dir / filename
        
        if not image_path.exists():
            # Create a simple image with text
            img = Image.new('RGB', (300, 300), color=(73, 109, 137))
            
            # Add text (simplified - in production you'd use a proper font)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Simple text placement
            text_bbox = draw.textbbox((0, 0), text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (300 - text_width) // 2
            y = (300 - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255))
            
            img.save(image_path)
            print(f"✅ Created sample image: {image_path}")

def main():
    """
    Main function to update playlist cover art.
    
    This function orchestrates the playlist cover art update process:
    1. Loads the configuration
    2. Connects to Spotify
    3. Creates playlist mapping
    4. Updates cover art for each playlist
    5. Provides feedback on results
    """
    print("🎨 Updating Playlist Cover Art for Spotify App Agent Template")
    print("=" * 70)
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    
    # Get persona information
    persona = config.get('persona', {})
    bot_name = persona.get('name', 'Your Bot')
    
    print(f"🤖 Bot: {bot_name}")
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
    playlist_art_mapping = get_playlist_art_mapping(config)
    
    if not playlist_art_mapping:
        print("⚠️  No playlists found to update")
        print("Please configure your playlist IDs in config.yaml first")
        sys.exit(1)
    
    print(f"📋 Found {len(playlist_art_mapping)} playlist(s) to update:")
    for playlist_id, image_path in playlist_art_mapping.items():
        print(f"   - {playlist_id} → {image_path}")
    print()
    
    # Check if playlist_art directory exists
    playlist_art_dir = Path("playlist_art")
    if not playlist_art_dir.exists():
        print("📁 Creating playlist_art directory...")
        playlist_art_dir.mkdir(exist_ok=True)
        create_sample_images()
        print("✅ Created sample images")
        print("   Please customize these images before running the script again")
        sys.exit(0)
    
    # Check for missing images
    missing_images = []
    for playlist_id, image_path in playlist_art_mapping.items():
        if not os.path.exists(image_path):
            missing_images.append(image_path)
    
    if missing_images:
        print("⚠️  Missing image files:")
        for image_path in missing_images:
            print(f"   - {image_path}")
        print()
        print("Creating sample images...")
        create_sample_images()
        print("✅ Created sample images")
        print("   Please customize these images before running the script again")
        sys.exit(0)
    
    # Confirm with user
    response = input("Do you want to proceed with updating playlist cover art? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cover art update cancelled")
        sys.exit(0)
    
    print()
    
    # Update playlist cover art
    successful_updates = 0
    failed_updates = 0
    
    for playlist_id, image_path in playlist_art_mapping.items():
        success = update_playlist_art(spotify_client, playlist_id, image_path)
        if success:
            successful_updates += 1
        else:
            failed_updates += 1
    
    # Summary
    print()
    print("=" * 70)
    print("📊 Cover Art Update Summary:")
    print(f"✅ Successful updates: {successful_updates}")
    print(f"❌ Failed updates: {failed_updates}")
    
    if successful_updates > 0:
        print("\n🎉 Cover art updates completed!")
        print("Your playlists now have custom cover art.")
    
    if failed_updates > 0:
        print("\n⚠️  Some playlists could not be updated.")
        print("This might be due to:")
        print("- Missing or invalid image files")
        print("- Insufficient permissions")
        print("- Network connectivity issues")
    
    print("\n🎯 Next steps:")
    print("1. Verify the new cover art on Spotify")
    print("2. Customize images in the playlist_art folder")
    print("3. Run this script again to update with new images")
    print("4. Test your bot with: python tools/test_bot.py")

if __name__ == "__main__":
    main()
