# Deployment Architecture

This diagram shows the deployment architecture of the Spotify App Agent Template, including Docker containerization, volume mounts, and external dependencies.

```mermaid
graph TB
    %% Host System
    subgraph "Host System"
        HOST[Linux/macOS/Windows Host]
        DOCKER_ENGINE[Docker Engine]
        NETWORK[Network Interface]
    end
    
    %% Docker Container
    subgraph "Spotify App Agent Container"
        CONTAINER[spotify-app-agent-template:latest]
        
        %% Application Components
        subgraph "Application Layer"
            PYTHON[Python 3.11 Runtime]
            APP[Main Application]
            SCHEDULER[APScheduler]
            LOGGER[Logging System]
        end
        
        %% Application Modules
        subgraph "Modules"
            SPOTIFY_CLIENT[Spotify Client]
            TRACK_SELECTOR[Track Selector]
            PLAYLIST_MANAGER[Playlist Manager]
        end
        
        %% Internal Storage
        subgraph "Internal Storage"
            TEMP[/tmp]
            CACHE[Cache Directory]
        end
    end
    
    %% Volume Mounts
    subgraph "Persistent Volumes"
        CONFIG_VOLUME[config/]
        STATE_VOLUME[state/]
        SNAPSHOTS_VOLUME[snapshots/]
        LOGS_VOLUME[logs/]
        PLAYLIST_ART_VOLUME[playlist_art/]
    end
    
    %% Environment
    subgraph "Environment"
        ENV_FILE[.env File]
        ENV_VARS[Environment Variables]
    end
    
    %% External Services
    subgraph "External Services"
        SPOTIFY_API[Spotify Web API]
        DOCKER_REGISTRY[Docker Hub Registry]
    end
    
    %% Network Connections
    subgraph "Network"
        HTTP[HTTP/HTTPS]
        DOCKER_NETWORK[Docker Network]
    end
    
    %% Connections
    HOST --> DOCKER_ENGINE
    DOCKER_ENGINE --> CONTAINER
    
    CONTAINER --> PYTHON
    PYTHON --> APP
    APP --> SCHEDULER
    APP --> LOGGER
    APP --> SPOTIFY_CLIENT
    APP --> TRACK_SELECTOR
    APP --> PLAYLIST_MANAGER
    
    %% Volume Mounts
    CONFIG_VOLUME -.-> CONTAINER
    STATE_VOLUME -.-> CONTAINER
    SNAPSHOTS_VOLUME -.-> CONTAINER
    LOGS_VOLUME -.-> CONTAINER
    PLAYLIST_ART_VOLUME -.-> CONTAINER
    
    %% Environment
    ENV_FILE --> ENV_VARS
    ENV_VARS --> CONTAINER
    
    %% External Connections
    CONTAINER --> SPOTIFY_API
    DOCKER_REGISTRY --> CONTAINER
    
    %% Network
    CONTAINER --> HTTP
    CONTAINER --> DOCKER_NETWORK
    
    %% Styling
    classDef host fill:#e8f5e8
    classDef container fill:#e3f2fd
    classDef volumes fill:#f3e5f5
    classDef external fill:#ffebee
    classDef network fill:#fff3e0
    
    class HOST,DOCKER_ENGINE,NETWORK host
    class CONTAINER,PYTHON,APP,SCHEDULER,LOGGER,SPOTIFY_CLIENT,TRACK_SELECTOR,PLAYLIST_MANAGER,TEMP,CACHE container
    class CONFIG_VOLUME,STATE_VOLUME,SNAPSHOTS_VOLUME,LOGS_VOLUME,PLAYLIST_ART_VOLUME volumes
    class SPOTIFY_API,DOCKER_REGISTRY external
    class HTTP,DOCKER_NETWORK network
```

## Container Architecture

### Base Image
- **Python 3.11**: Official Python runtime
- **Alpine Linux**: Lightweight base image
- **Multi-stage Build**: Optimized for production

### Application Components
- **Main Application**: Core bot orchestration
- **APScheduler**: Automated task scheduling
- **Logging System**: Structured logging and monitoring
- **Spotify Client**: API integration and authentication
- **Track Selector**: Intelligent track selection
- **Playlist Manager**: Playlist operations and management

## Volume Mounts

### Configuration Volume (`config/`)
- **Purpose**: Configuration files and settings
- **Contents**: `config.yaml`, persona configuration
- **Permissions**: Read-only for security
- **Persistence**: Survives container restarts

### State Volume (`state/`)
- **Purpose**: Application state and database
- **Contents**: SQLite database, bot state files
- **Permissions**: Read-write for data persistence
- **Backup**: Critical for data preservation

### Snapshots Volume (`snapshots/`)
- **Purpose**: Playlist snapshots and analytics
- **Contents**: JSON/CSV snapshot files
- **Permissions**: Read-write for data collection
- **Retention**: Configurable cleanup policies

### Logs Volume (`logs/`)
- **Purpose**: Application logs and monitoring
- **Contents**: Log files, error reports
- **Permissions**: Write-only for logging
- **Rotation**: Automatic log rotation

### Playlist Art Volume (`playlist_art/`)
- **Purpose**: Custom playlist cover art
- **Contents**: Image files for playlist covers
- **Permissions**: Read-write for image management
- **Formats**: PNG, JPEG, WebP

## Environment Configuration

### Environment Variables
```bash
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REFRESH_TOKEN=your_refresh_token
SPOTIFY_USER_ID=your_user_id

# Application Settings
TZ=America/New_York
LOG_LEVEL=INFO
```

### Security Considerations
- **No Hardcoded Secrets**: All credentials in environment variables
- **Secure Storage**: Credentials stored outside container
- **Minimal Permissions**: Container runs with limited privileges
- **Network Isolation**: Containerized network access

## Deployment Options

### Local Development
```bash
# Build and run locally
make build
make run

# Development mode with volume mounts
docker run -v $(pwd)/config:/app/config \
           -v $(pwd)/state:/app/state \
           -v $(pwd)/logs:/app/logs \
           spotify-app-agent-template
```

### Production Deployment
```bash
# Production build
docker build -t spotify-app-agent-template:latest .

# Production run with restart policy
docker run -d \
  --name spotify-app-agent \
  --restart unless-stopped \
  -v /opt/spotify-bot/config:/app/config \
  -v /opt/spotify-bot/state:/app/state \
  -v /opt/spotify-bot/logs:/app/logs \
  -v /opt/spotify-bot/snapshots:/app/snapshots \
  --env-file .env \
  spotify-app-agent-template:latest
```

### Docker Compose
```yaml
version: '3.8'
services:
  spotify-app-agent:
    build: .
    container_name: spotify-app-agent
    restart: unless-stopped
    volumes:
      - ./config:/app/config
      - ./state:/app/state
      - ./logs:/app/logs
      - ./snapshots:/app/snapshots
      - ./playlist_art:/app/playlist_art
    env_file:
      - .env
    environment:
      - TZ=America/New_York
```

## Monitoring and Health Checks

### Health Check Configuration
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"
```

### Monitoring Endpoints
- **Health Check**: `/health` - Basic health status
- **Metrics**: `/metrics` - Performance metrics
- **Status**: `/status` - Application status

### Logging Configuration
- **Log Level**: Configurable (DEBUG, INFO, WARNING, ERROR)
- **Log Format**: Structured JSON logging
- **Log Rotation**: Automatic rotation and cleanup
- **Log Aggregation**: Compatible with log aggregation systems

## Security Features

### Container Security
- **Non-root User**: Container runs as non-root user
- **Read-only Root**: Root filesystem is read-only
- **Capability Dropping**: Minimal Linux capabilities
- **Network Policies**: Restricted network access

### Data Security
- **Volume Encryption**: Encrypted volume mounts
- **Secret Management**: Environment variable secrets
- **Access Control**: File permission restrictions
- **Audit Logging**: Comprehensive audit trails

## Scaling Considerations

### Horizontal Scaling
- **Stateless Design**: Application is stateless
- **Database Sharing**: Shared SQLite database
- **Load Balancing**: Multiple container instances
- **Service Discovery**: Container orchestration support

### Resource Management
- **Memory Limits**: Configurable memory limits
- **CPU Limits**: CPU usage restrictions
- **Storage Limits**: Volume size limits
- **Network Limits**: Bandwidth restrictions
