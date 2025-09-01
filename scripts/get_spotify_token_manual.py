#!/usr/bin/env python3
"""
Manual Spotify OAuth Token Generator
Provides step-by-step instructions for getting your refresh token manually.

This script helps you authenticate with Spotify's API using OAuth 2.0.
OAuth 2.0 is a security protocol that allows applications to access user data
without storing their username and password.

LEARNING OBJECTIVES:
- Understand OAuth 2.0 flow
- Learn how to handle API authentication
- Practice working with environment variables
- Understand HTTP requests and responses
"""

import requests  # Library for making HTTP requests to APIs
from urllib.parse import urlencode  # For encoding URL parameters
import os  # For environment variables and file operations
import sys  # For system exit

# =============================================================================
# SPOTIFY API CREDENTIALS
# =============================================================================
# SECURITY: These credentials should be loaded from environment variables
# NEVER hardcode credentials in source code for public repositories

def get_credentials():
    """
    Get Spotify API credentials from environment variables.
    
    This function safely retrieves credentials from environment variables
    instead of hardcoding them in the source code.
    
    Returns:
        tuple: (client_id, client_secret) or exits if not found
    """
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Validate that credentials are provided
    if not client_id or not client_secret:
        print("❌ CRITICAL SECURITY ERROR: Missing Spotify credentials!")
        print()
        print("🔒 SECURITY SETUP REQUIRED:")
        print("1. Create a .env file in the project root")
        print("2. Add your Spotify credentials:")
        print("   SPOTIFY_CLIENT_ID=your_client_id_here")
        print("   SPOTIFY_CLIENT_SECRET=your_client_secret_here")
        print()
        print("📚 See TEMPLATE_SETUP.md for detailed instructions")
        print("🔗 Get credentials from: https://developer.spotify.com/dashboard")
        sys.exit(1)
    
    return client_id, client_secret

# SCOPE: Defines what permissions your app needs
# - playlist-modify-public: Can modify public playlists
# - playlist-modify-private: Can modify private playlists  
# - user-read-private: Can read user's private info
# - ugc-image-upload: Can upload images (for playlist covers)
SCOPE = "playlist-modify-public playlist-modify-private user-read-private ugc-image-upload"

def main():
    """
    Main function that guides the user through the OAuth 2.0 process.
    
    OAuth 2.0 Flow:
    1. User authorizes your app (gets authorization code)
    2. App exchanges code for access token and refresh token
    3. App uses refresh token to get new access tokens when needed
    """
    print("🎵 Manual Spotify OAuth Token Generator")
    print("=" * 50)
    print()
    
    # =============================================================================
    # SECURITY: GET CREDENTIALS SAFELY
    # =============================================================================
    # Load credentials from environment variables instead of hardcoding
    client_id, client_secret = get_credentials()
    
    # =============================================================================
    # STEP 1: CREATE AUTHORIZATION URL
    # =============================================================================
    # This URL will take the user to Spotify's authorization page
    # where they can log in and approve your app's permissions
    
    # Parameters needed for the authorization URL
    auth_params = {
        'client_id': client_id,  # Your app's ID (from environment)
        'response_type': 'code',  # We want an authorization code back
        'redirect_uri': 'https://example.com/callback',  # Where Spotify sends the user after approval
        'scope': SCOPE,  # What permissions we're asking for
        'show_dialog': 'true'  # Always show the approval dialog
    }
    
    # Build the authorization URL by encoding the parameters
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    
    # =============================================================================
    # STEP 2: PROVIDE STEP-BY-STEP INSTRUCTIONS
    # =============================================================================
    print("📋 Step-by-Step Instructions:")
    print()
    print("1. Go to your Spotify app settings:")
    print("   https://developer.spotify.com/dashboard")
    print()
    print("2. Click on your app and go to 'Edit Settings'")
    print()
    print("3. Add this redirect URI:")
    print("   https://example.com/callback")
    print("   (This tells Spotify where to send the user after they approve)")
    print()
    print("4. Click 'Save'")
    print()
    print("5. Click this authorization URL:")
    print(f"   {auth_url}")
    print()
    print("6. Log in to Spotify and authorize the app")
    print("   (This is where the user gives your app permission)")
    print()
    print("7. You'll be redirected to a URL like:")
    print("   https://example.com/callback?code=AQD...")
    print("   (The 'code' parameter contains the authorization code)")
    print()
    print("8. Copy the 'code' parameter from the URL")
    print("   (This is the temporary code we'll exchange for tokens)")
    print()
    print("9. Enter the authorization code below:")
    print()
    
    # =============================================================================
    # STEP 3: GET AUTHORIZATION CODE FROM USER
    # =============================================================================
    # The user needs to manually copy the code from the URL
    # This is because we're not running a web server to receive it automatically
    
    auth_code = input("Enter the authorization code: ").strip()
    
    # Validate that we got a code
    if not auth_code:
        print("❌ No authorization code provided")
        return
    
    print()
    print("🔄 Exchanging code for tokens...")
    
    # =============================================================================
    # STEP 4: EXCHANGE AUTHORIZATION CODE FOR TOKENS
    # =============================================================================
    # Now we use the authorization code to get access and refresh tokens
    # This is done by making a POST request to Spotify's token endpoint
    
    try:
        # Make a POST request to exchange the code for tokens
        token_response = requests.post('https://accounts.spotify.com/api/token', data={
            'grant_type': 'authorization_code',  # We're exchanging an auth code
            'code': auth_code,  # The code we got from the user
            'redirect_uri': 'https://example.com/callback',  # Must match what we used before
            'client_id': client_id,  # Your app's ID (from environment)
            'client_secret': client_secret  # Your app's secret (from environment)
        })
        
        # Check if the request was successful
        if token_response.status_code == 200:
            # Parse the JSON response to get the tokens
            tokens = token_response.json()
            refresh_token = tokens.get('refresh_token')  # Long-lived token for getting new access tokens
            access_token = tokens.get('access_token')    # Short-lived token for API calls
            
            print("✅ Token exchange successful!")
            print(f"✅ Refresh token: {refresh_token}")
            print(f"✅ Access token: {access_token[:20]}...")  # Only show first 20 chars for security
            print()
            
            # Save the refresh token to the .env file
            update_env_file(refresh_token)
            
        else:
            # If the request failed, show the error
            print(f"❌ Token exchange failed: {token_response.text}")
            print("Common issues:")
            print("- Authorization code expired (they only last 10 minutes)")
            print("- Redirect URI doesn't match")
            print("- Invalid client credentials")
            
    except Exception as e:
        # Handle any other errors (network issues, etc.)
        print(f"❌ Error during token exchange: {e}")

def update_env_file(refresh_token):
    """
    Update the .env file with the refresh token.
    
    The .env file stores environment variables that the application needs.
    This keeps sensitive information like tokens out of the code.
    
    Args:
        refresh_token (str): The refresh token to save
    """
    try:
        env_path = '.env'  # Path to the environment file
        
        # =============================================================================
        # READ EXISTING .ENV FILE
        # =============================================================================
        # Read all lines from the existing .env file (if it exists)
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        # =============================================================================
        # UPDATE OR ADD REFRESH TOKEN
        # =============================================================================
        # Look for existing SPOTIFY_REFRESH_TOKEN line and update it
        # If not found, add a new line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('SPOTIFY_REFRESH_TOKEN='):
                # Replace the old token with the new one
                lines[i] = f'SPOTIFY_REFRESH_TOKEN={refresh_token}\n'
                updated = True
                break
        
        # If we didn't find an existing line, add a new one
        if not updated:
            lines.append(f'SPOTIFY_REFRESH_TOKEN={refresh_token}\n')
        
        # =============================================================================
        # WRITE BACK TO FILE
        # =============================================================================
        # Write all lines back to the .env file
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Updated {env_path} with refresh token")
        print()
        print("🎉 Authentication complete! You can now build and run the bot.")
        print()
        print("📚 What we learned:")
        print("- OAuth 2.0 is a secure way to authenticate with APIs")
        print("- Authorization codes are temporary and must be exchanged quickly")
        print("- Refresh tokens are long-lived and used to get new access tokens")
        print("- Environment variables keep sensitive data out of code")
        print("- Never hardcode credentials in source code!")
        
    except Exception as e:
        # If we can't write to the file, show manual instructions
        print(f"❌ Failed to update .env file: {e}")
        print(f"Please manually add this line to your .env file:")
        print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# This block runs when the script is executed directly
# (not when imported as a module)
if __name__ == "__main__":
    main()  # Call the main function
