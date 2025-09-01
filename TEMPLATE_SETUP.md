# Template Setup Guide

This comprehensive guide will walk you through setting up your own Spotify App Agent using this template.

## Prerequisites

- **Python 3.11+** installed on your system
- **Docker** installed (optional, for containerized deployment)
- **Git** for cloning the template
- **Spotify Account** with a Premium subscription
- **Basic understanding** of command line operations

## Step 1: Get Spotify API Credentials

### 1.1 Create a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the app details:
   - **App name**: Your bot's name (e.g., "My Music Bot")
   - **App description**: Brief description of your bot
   - **Website**: Your website (optional)
   - **Redirect URI**: `http://localhost:8080/callback` (for local setup)
5. Accept the terms and click **"Save"**

### 1.2 Get Your Credentials

After creating the app, you'll see:
- **Client ID**: Copy this value
- **Client Secret**: Click "Show Client Secret" and copy this value

**Keep these credentials secure!** Never share them publicly.

## Step 2: Create Your Playlists

### 2.1 Plan Your Playlists

Decide what types of playlists you want your bot to manage. For example:
- **Playlist 1**: For frequent updates
- **Playlist 2**: For weekly compilations  
- **Playlist 3**: For monthly collections
- **Playlist 4**: For annual best-of lists

### 2.2 Create Playlists on Spotify

1. Open Spotify (web or desktop app)
2. Create new playlists with descriptive names
3. Make them **public** (required for the bot to access them)
4. Note down the playlist names and descriptions

### 2.3 Get Playlist IDs

1. Right-click on each playlist
2. Select **"Share"** → **"Copy link to playlist"**
3. The playlist ID is the long string after `/playlist/` and before `?si=`
4. Save these IDs for the next step

## Step 3: Configure Your Environment

### 3.1 Create Environment File

Create a `.env` file in the project root:

```bash
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_USER_ID=your_spotify_user_id

# Application Settings
TZ=America/New_York
LOG_LEVEL=INFO
```

### 3.2 Get Your Spotify User ID

1. Go to [Spotify Profile](https://open.spotify.com/user/your_username)
2. Your user ID is in the URL after `/user/`
3. Add it to your `.env` file

## Step 4: Generate Refresh Token

### 4.1 Run Authentication Script

Choose one of the authentication methods:

**Option A: Automated (Recommended)**
```bash
python scripts/get_spotify_token.py
```

**Option B: Manual**
```bash
python scripts/get_spotify_token_manual.py
```

**Option C: Secure (with ngrok)**
```bash
python scripts/get_spotify_token_secure.py
```

### 4.2 Complete OAuth Flow

1. The script will open a URL in your browser
2. Log in to Spotify and authorize the app
3. Copy the refresh token from the script output
4. Add it to your `.env` file:
   ```
   SPOTIFY_REFRESH_TOKEN=your_refresh_token_here
   ```

## Step 5: Configure Your Bot

### 5.1 Update Configuration File

Edit `config/config.yaml` with your settings:

```yaml
persona:
  name: "Your Bot Name"  # Change to your bot's name
  prefix: "Your Bot's "  # Change to your bot's prefix
  bio: "Your bot's description"  # Change to your bot's bio

playlists:
  playlist1:
    id: "your-playlist1-id"  # Replace with actual playlist ID
    size: 50
    schedule_cron: "0 4 * * *"  # 04:00 daily
    active: true
  playlist2:
    id: "your-playlist2-id"  # Replace with actual playlist ID
    size: 100
    schedule_cron: "0 4 * * 6"  # 04:00 Saturday
    active: true
  # Add more playlists as needed
```

### 5.2 Customize Playlist Settings

For each playlist, configure:
- **ID**: The Spotify playlist ID you copied earlier
- **Size**: Number of tracks in the playlist
- **Schedule**: When to update (cron format)
- **Active**: Whether the playlist should be updated

### 5.3 Update Project Metadata

Edit `pyproject.toml`:

```toml
[project]
name = "your-spotify-bot-name"
version = "1.0.0"
description = "Your personalized Spotify playlist curation bot"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
```

## Step 6: Test Your Setup

### 6.1 Test Connection

```bash
python tools/test_bot.py
```

This will verify:
- Spotify API connection
- Playlist access
- Configuration validity

### 6.2 Create Missing Playlists

If you haven't created playlists yet:

```bash
python tools/create_missing_playlists.py
```

This will create playlists with your bot's naming convention.

### 6.3 Test Individual Playlists

```bash
# Test playlist1
make update-playlist1

# Test playlist2  
make update-playlist2
```

## Step 7: Deploy Your Bot

### 7.1 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python -m app.main
```

### 7.2 Docker Deployment (Recommended)

```bash
# Build the container
make build

# Run the bot
make run

# Check logs
make logs
```

### 7.3 Production Deployment

For production, consider:
- **Cloud hosting** (AWS, Google Cloud, Azure)
- **Container orchestration** (Kubernetes, Docker Swarm)
- **Monitoring and logging** (Prometheus, Grafana)
- **Backup strategies** for your data

## Step 8: Monitor and Maintain

### 8.1 Check Bot Status

```bash
python tools/dashboard.py
```

### 8.2 View Logs

```bash
# View recent logs
tail -f logs/spotify_bot.log

# Or use Docker
make logs
```

### 8.3 Update Playlists Manually

```bash
# Update all playlists
python tools/preseed_playlists.py

# Update specific playlist
make update-playlist1
```

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify your credentials in `.env`
- Regenerate refresh token if needed
- Check that your Spotify app is properly configured

**Playlist Access Errors**
- Ensure playlists are public
- Verify playlist IDs are correct
- Check that your user ID is correct

**Configuration Errors**
- Validate YAML syntax in `config.yaml`
- Check that all required fields are present
- Verify cron expressions are valid

### Getting Help

1. **Check the logs** for detailed error messages
2. **Review the documentation** in the `docs/` folder
3. **Test individual components** using the provided tools
4. **Check GitHub Issues** for known problems and solutions

## Security Best Practices

- **Never commit** your `.env` file to version control
- **Rotate credentials** regularly
- **Use strong passwords** for your Spotify account
- **Monitor API usage** to stay within limits
- **Keep the template updated** with security patches

## Next Steps

Once your bot is running:

1. **Customize the track selection** algorithm to match your preferences
2. **Adjust playlist schedules** to fit your needs
3. **Add custom cover art** for your playlists
4. **Monitor performance** and adjust settings
5. **Share your playlists** with friends and family

Congratulations! You now have your own personalized Spotify playlist curation bot! 🎵
