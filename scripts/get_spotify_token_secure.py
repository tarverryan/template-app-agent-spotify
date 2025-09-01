#!/usr/bin/env python3
"""
Spotify OAuth Token Generator with Secure HTTPS Redirect
Uses ngrok to create a secure HTTPS tunnel for the redirect URI.

This is the most advanced version of the token generator. It uses ngrok
to create a secure HTTPS tunnel, which is useful for production-like
environments where you need a public HTTPS URL.

LEARNING OBJECTIVES:
- Understand HTTPS and security in OAuth flows
- Learn about tunneling and ngrok
- Practice working with external services
- Understand subprocess management
- Learn about API integration with ngrok
"""

import os  # For file operations and environment variables
import requests  # For making HTTP requests to Spotify's API and ngrok
from urllib.parse import urlencode  # For encoding URL parameters
import webbrowser  # For automatically opening the browser
from http.server import HTTPServer, BaseHTTPRequestHandler  # For creating a local web server
import threading  # For running the server in the background
import time  # For adding delays
import subprocess  # For running external commands (ngrok)
import json  # For parsing JSON responses from ngrok API
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

# LOCAL_PORT: The port where our local server will run
# ngrok will create a tunnel to this port
LOCAL_PORT = 8888

# SCOPE: Defines what permissions your app needs
SCOPE = "playlist-modify-public playlist-modify-private user-read-private ugc-image-upload"

class SpotifyAuthHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for processing Spotify's OAuth callback.
    
    This is similar to the basic version but uses the dynamic redirect URI
    from ngrok instead of a hardcoded localhost URL.
    """
    
    def do_GET(self):
        """
        Handle GET requests from the browser.
        
        This method processes the callback from Spotify after the user
        authorizes your app. The main difference from the basic version
        is that it uses the dynamic redirect URI stored in the server.
        """
        # Check if this is the callback from Spotify
        if self.path.startswith('/callback'):
            # =============================================================================
            # EXTRACT AUTHORIZATION CODE FROM URL
            # =============================================================================
            # Parse the URL parameters to get the authorization code
            query = self.path.split('?')[1] if '?' in self.path else ''
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            
            # Check if we got an authorization code
            if 'code' in params:
                auth_code = params['code']
                print(f"\n✅ Authorization code received: {auth_code[:20]}...")
                
                # =============================================================================
                # EXCHANGE AUTHORIZATION CODE FOR TOKENS
                # =============================================================================
                # Use the authorization code to get access and refresh tokens
                # Note: We use self.server.redirect_uri which is set dynamically
                
                # Get credentials from environment variables
                client_id, client_secret = get_credentials()
                
                token_response = requests.post('https://accounts.spotify.com/api/token', data={
                    'grant_type': 'authorization_code',  # We're exchanging an auth code
                    'code': auth_code,  # The code we just received
                    'redirect_uri': self.server.redirect_uri,  # Dynamic redirect URI from ngrok
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
                    # Send a nice HTML page back to the browser
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

def start_ngrok():
    """
    Start ngrok tunnel and return the public URL.
    
    Ngrok creates a secure tunnel from the internet to your local machine.
    This allows Spotify to send the OAuth callback to a public HTTPS URL
    instead of localhost.
    
    Returns:
        tuple: (public_url, ngrok_process) or (None, None) if failed
    """
    try:
        # =============================================================================
        # START NGROK PROCESS
        # =============================================================================
        # Start ngrok as a subprocess to create a tunnel to our local port
        # stdout=subprocess.PIPE captures the output (we don't need it here)
        # stderr=subprocess.PIPE captures error output
        # text=True makes the output text instead of bytes
        
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', str(LOCAL_PORT)],  # Command: ngrok http 8888
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for ngrok to start up
        time.sleep(3)
        
        # =============================================================================
        # GET THE PUBLIC URL FROM NGROK API
        # =============================================================================
        # Ngrok provides a local API that tells us the public URL
        # This is easier than parsing ngrok's output
        
        try:
            # Make a request to ngrok's API to get tunnel information
            response = requests.get('http://localhost:4040/api/tunnels')
            
            # Parse the JSON response
            tunnels = response.json()['tunnels']
            
            # Get the public URL from the first tunnel
            public_url = tunnels[0]['public_url']
            
            print(f"✅ Ngrok tunnel started: {public_url}")
            return public_url, ngrok_process
            
        except Exception as e:
            # If we can't get the URL from the API, show error and clean up
            print(f"❌ Failed to get ngrok URL: {e}")
            ngrok_process.terminate()  # Stop the ngrok process
            return None, None
            
    except Exception as e:
        # If we can't start ngrok at all, show error
        print(f"❌ Failed to start ngrok: {e}")
        return None, None

def main():
    """
    Main function that orchestrates the secure OAuth flow.
    
    This function:
    1. Starts ngrok to create a secure tunnel
    2. Creates the authorization URL with the ngrok URL
    3. Starts a local web server
    4. Opens the browser for user authorization
    5. Waits for the callback
    6. Cleans up when done
    """
    print("🎵 Spotify OAuth Token Generator (Secure)")
    print("=" * 50)
    
    # =============================================================================
    # SECURITY: GET CREDENTIALS SAFELY
    # =============================================================================
    # Load credentials from environment variables instead of hardcoding
    client_id, client_secret = get_credentials()
    
    # =============================================================================
    # START NGROK TUNNEL
    # =============================================================================
    # Create a secure tunnel that Spotify can reach
    print("🚀 Starting secure tunnel with ngrok...")
    public_url, ngrok_process = start_ngrok()
    
    # Check if ngrok started successfully
    if not public_url:
        print("❌ Failed to start ngrok tunnel")
        print("Make sure ngrok is installed: https://ngrok.com/download")
        return
    
    # =============================================================================
    # SET UP REDIRECT URI
    # =============================================================================
    # Use the ngrok URL as our redirect URI
    # This allows Spotify to send the callback to a public HTTPS URL
    redirect_uri = f"{public_url}/callback"
    
    # =============================================================================
    # CREATE AUTHORIZATION URL
    # =============================================================================
    # Build the URL that will take the user to Spotify's authorization page
    
    auth_params = {
        'client_id': client_id,  # Your app's ID (from environment)
        'response_type': 'code',  # We want an authorization code back
        'redirect_uri': redirect_uri,  # The ngrok URL where Spotify will send the user
        'scope': SCOPE,  # What permissions we're asking for
        'show_dialog': 'true'  # Always show the approval dialog
    }
    
    # Build the authorization URL by encoding the parameters
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    
    print(f"🔗 Authorization URL: {auth_url}")
    print(f"🔗 Redirect URI: {redirect_uri}")
    print("\n📋 Steps:")
    print("1. Add this redirect URI to your Spotify app settings:")
    print(f"   {redirect_uri}")
    print("2. Click the authorization URL above")
    print("3. Log in to Spotify and authorize the app")
    print("4. You'll be redirected back here")
    print("5. The refresh token will be saved to .env")
    
    # =============================================================================
    # START LOCAL WEB SERVER
    # =============================================================================
    # Create an HTTP server that will handle the callback from Spotify
    
    server = HTTPServer(('localhost', LOCAL_PORT), SpotifyAuthHandler)
    
    # Store the redirect URI in the server object so the handler can access it
    # This is a custom attribute we're adding to the server
    server.redirect_uri = redirect_uri
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"\n🌐 Starting local server on http://localhost:{LOCAL_PORT}")
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
        # =============================================================================
        # CLEANUP ON EXIT
        # =============================================================================
        # If the user presses Ctrl+C, stop everything gracefully
        print("\n🛑 Stopping server and ngrok...")
        server.shutdown()  # Stop the web server
        
        # Stop the ngrok process if it's running
        if ngrok_process:
            ngrok_process.terminate()
        
        print("✅ Cleanup completed")

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# This block runs when the script is executed directly
if __name__ == "__main__":
    main()
