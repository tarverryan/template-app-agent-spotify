#!/usr/bin/env python3
"""
Spotify OAuth Token Generator
Run this script to get your refresh token for the Spotify API.

This script implements a complete OAuth 2.0 flow with a local web server.
It's more advanced than the manual version because it automatically handles
the callback from Spotify.

LEARNING OBJECTIVES:
- Understand OAuth 2.0 authorization code flow
- Learn how to create a simple HTTP server
- Practice handling web callbacks
- Understand threading and web browsers
- Learn about HTTP requests and responses
"""

import os  # For file operations and environment variables
import base64  # For encoding/decoding (not used in this script but common in OAuth)
import requests  # For making HTTP requests to Spotify's API
from urllib.parse import urlencode  # For encoding URL parameters
import webbrowser  # For automatically opening the browser
from http.server import HTTPServer, BaseHTTPRequestHandler  # For creating a local web server
import threading  # For running the server in the background
import time  # For adding delays
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

# REDIRECT_URI: Where Spotify will send the user after they authorize
# We use localhost because we're running a local server
REDIRECT_URI = "http://localhost:8888/callback"

# SCOPE: Defines what permissions your app needs
SCOPE = "playlist-modify-public playlist-modify-private user-read-private ugc-image-upload"

class SpotifyAuthHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for processing Spotify's OAuth callback.
    
    This class handles the HTTP requests that come back from Spotify
    after the user authorizes your app. It's like a mini web server
    that only handles one specific type of request.
    
    INHERITANCE: This class inherits from BaseHTTPRequestHandler,
    which provides basic HTTP server functionality.
    """
    
    def do_GET(self):
        """
        Handle GET requests from the browser.
        
        This method is called whenever someone makes a GET request to our server.
        In OAuth, Spotify redirects the user's browser to our server with
        the authorization code in the URL.
        """
        # Check if this is the callback from Spotify
        if self.path.startswith('/callback'):
            # =============================================================================
            # EXTRACT AUTHORIZATION CODE FROM URL
            # =============================================================================
            # The URL will look like: /callback?code=AQD...&state=...
            # We need to extract the 'code' parameter
            
            # Split the URL to get the query parameters
            query = self.path.split('?')[1] if '?' in self.path else ''
            
            # Parse the query parameters into a dictionary
            # Example: "code=AQD&state=123" becomes {"code": "AQD", "state": "123"}
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            
            # Check if we got an authorization code
            if 'code' in params:
                auth_code = params['code']
                print(f"\n✅ Authorization code received: {auth_code[:20]}...")
                
                # =============================================================================
                # EXCHANGE AUTHORIZATION CODE FOR TOKENS
                # =============================================================================
                # Now we use the authorization code to get access and refresh tokens
                # This is the same process as in the manual script
                
                # Get credentials from environment variables
                client_id, client_secret = get_credentials()
                
                token_response = requests.post('https://accounts.spotify.com/api/token', data={
                    'grant_type': 'authorization_code',  # We're exchanging an auth code
                    'code': auth_code,  # The code we just received
                    'redirect_uri': REDIRECT_URI,  # Must match what we used in the auth URL
                    'client_id': client_id,  # Your app's ID (from environment)
                    'client_secret': client_secret  # Your app's secret (from environment)
                })
                
                # Check if the token exchange was successful
                if token_response.status_code == 200:
                    # Parse the JSON response to get the tokens
                    tokens = token_response.json()
                    refresh_token = tokens.get('refresh_token')  # Long-lived token
                    access_token = tokens.get('access_token')    # Short-lived token
                    
                    print(f"✅ Refresh token: {refresh_token}")
                    print(f"✅ Access token: {access_token[:20]}...")
                    
                    # Save the refresh token to the .env file
                    self.update_env_file(refresh_token)
                    
                    # =============================================================================
                    # SEND SUCCESS RESPONSE TO BROWSER
                    # =============================================================================
                    # Send a nice HTML page back to the browser to show success
                    self.send_response(200)  # HTTP 200 = OK
                    self.send_header('Content-type', 'text/html')  # Tell browser this is HTML
                    self.end_headers()  # End the headers section
                    
                    # Send the HTML content
                    self.wfile.write(b"""
                    <html>
                    <body>
                    <h1>Authentication Successful!</h1>
                    <p>Your refresh token has been saved to .env file.</p>
                    <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                    """)
                else:
                    # If token exchange failed, show error
                    print(f"❌ Token exchange failed: {token_response.text}")
                    self.send_error(400, "Token exchange failed")
            else:
                # If no authorization code was received
                print("❌ No authorization code received")
                self.send_error(400, "No authorization code")
        else:
            # If someone tries to access any other URL, return 404
            self.send_error(404, "Not found")
    
    def update_env_file(self, refresh_token):
        """
        Update the .env file with the refresh token.
        
        This method reads the existing .env file, updates the refresh token,
        and writes it back. This keeps the token persistent for future use.
        
        Args:
            refresh_token (str): The refresh token to save
        """
        env_path = '.env'
        
        # Check if .env file exists
        if os.path.exists(env_path):
            # Read all lines from the existing file
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # =============================================================================
            # UPDATE THE REFRESH TOKEN LINE
            # =============================================================================
            # Go through each line and update the SPOTIFY_REFRESH_TOKEN line
            updated_lines = []
            for line in lines:
                if line.startswith('SPOTIFY_REFRESH_TOKEN='):
                    # Replace the old token with the new one
                    updated_lines.append(f'SPOTIFY_REFRESH_TOKEN={refresh_token}\n')
                else:
                    # Keep all other lines unchanged
                    updated_lines.append(line)
            
            # Write the updated content back to the file
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            print(f"✅ Updated {env_path} with refresh token")
        else:
            # If .env file doesn't exist, show error
            print(f"❌ .env file not found at {env_path}")

def main():
    """
    Main function that orchestrates the entire OAuth flow.
    
    This function:
    1. Creates the authorization URL
    2. Starts a local web server
    3. Opens the browser for user authorization
    4. Waits for the callback
    """
    print("🎵 Spotify OAuth Token Generator")
    print("=" * 40)
    
    # =============================================================================
    # SECURITY: GET CREDENTIALS SAFELY
    # =============================================================================
    # Load credentials from environment variables instead of hardcoding
    client_id, client_secret = get_credentials()
    
    # =============================================================================
    # CREATE AUTHORIZATION URL
    # =============================================================================
    # Build the URL that will take the user to Spotify's authorization page
    
    auth_params = {
        'client_id': client_id,  # Your app's ID (from environment)
        'response_type': 'code',  # We want an authorization code back
        'redirect_uri': REDIRECT_URI,  # Where to send the user after approval
        'scope': SCOPE,  # What permissions we're asking for
        'show_dialog': 'true'  # Always show the approval dialog
    }
    
    # Build the authorization URL by encoding the parameters
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    
    print(f"🔗 Authorization URL: {auth_url}")
    print("\n📋 Steps:")
    print("1. Click the URL above (will open in browser)")
    print("2. Log in to Spotify and authorize the app")
    print("3. You'll be redirected back here")
    print("4. The refresh token will be saved to .env")
    
    # =============================================================================
    # START LOCAL WEB SERVER
    # =============================================================================
    # Create an HTTP server that will handle the callback from Spotify
    # The server runs on localhost (127.0.0.1) port 8888
    
    server = HTTPServer(('localhost', 8888), SpotifyAuthHandler)
    
    # Start the server in a separate thread so it doesn't block the main program
    # daemon=True means the thread will stop when the main program stops
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"\n🌐 Starting local server on http://localhost:8888")
    print("⏳ Waiting for authorization...")
    
    # =============================================================================
    # OPEN BROWSER FOR AUTHORIZATION
    # =============================================================================
    # Automatically open the user's default browser to the authorization URL
    webbrowser.open(auth_url)
    
    try:
        # =============================================================================
        # WAIT FOR CALLBACK
        # =============================================================================
        # Keep the program running until the user interrupts it (Ctrl+C)
        # or until the callback is received and processed
        while True:
            time.sleep(1)  # Sleep for 1 second to avoid using 100% CPU
    except KeyboardInterrupt:
        # If the user presses Ctrl+C, stop the server gracefully
        print("\n🛑 Stopping server...")
        server.shutdown()

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# This block runs when the script is executed directly
if __name__ == "__main__":
    main()
