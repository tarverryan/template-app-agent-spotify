# Data Flow

This diagram illustrates the flow of data through the Spotify App Agent Template, from initial configuration to playlist updates.

```mermaid
flowchart TD
    %% Start
    START([User Starts Bot]) --> CONFIG[Load Configuration]
    
    %% Configuration Loading
    CONFIG --> YAML{config.yaml}
    CONFIG --> ENV{.env File}
    CONFIG --> PERSONA{Persona Config}
    
    %% Authentication
    YAML --> AUTH[Initialize Spotify Client]
    ENV --> AUTH
    AUTH --> OAUTH[OAuth 2.0 Authentication]
    OAUTH --> TOKEN[Get Access Token]
    TOKEN --> REFRESH[Store Refresh Token]
    
    %% Scheduler
    PERSONA --> SCHEDULER[Initialize Scheduler]
    SCHEDULER --> CRON[Load Cron Jobs]
    CRON --> WAIT[Wait for Scheduled Time]
    
    %% Playlist Update Trigger
    WAIT --> TRIGGER[Playlist Update Triggered]
    TRIGGER --> DISCOVER[Track Discovery]
    
    %% Track Discovery Process
    DISCOVER --> NEW_RELEASES[Get New Releases]
    DISCOVER --> TRENDING[Get Trending Tracks]
    DISCOVER --> SEARCH[Genre-based Search]
    
    NEW_RELEASES --> MERGE[Merge Track Sources]
    TRENDING --> MERGE
    SEARCH --> MERGE
    
    %% Track Processing
    MERGE --> FILTER[Filter Tracks]
    FILTER --> SCORE[Score Tracks]
    SCORE --> RANK[Rank by Score]
    RANK --> DEDUPE[Remove Duplicates]
    DEDUPE --> CAP[Apply Artist Caps]
    CAP --> ALLOCATE[Genre Allocation]
    
    %% Scoring Components
    SCORE --> POPULARITY[Popularity Score]
    SCORE --> RECENCY[Recency Boost]
    SCORE --> FEATURES[Audio Features]
    SCORE --> DELTA[Popularity Delta]
    
    %% Database Operations
    ALLOCATE --> DB_READ[Read Current Playlist]
    DB_READ --> COMPARE[Compare with New Selection]
    COMPARE --> DIFF{Changes Detected?}
    
    %% Update Decision
    DIFF -->|Yes| UPDATE[Update Playlist]
    DIFF -->|No| SKIP[Skip Update]
    
    %% Playlist Update
    UPDATE --> API_CALL[Spotify API Call]
    API_CALL --> SUCCESS{Update Successful?}
    
    %% Success Path
    SUCCESS -->|Yes| SNAPSHOT[Save Snapshot]
    SNAPSHOT --> LOG[Log Success]
    LOG --> METRICS[Update Metrics]
    METRICS --> DB_WRITE[Write to Database]
    
    %% Error Path
    SUCCESS -->|No| ERROR[Log Error]
    ERROR --> RETRY{Retry Available?}
    RETRY -->|Yes| API_CALL
    RETRY -->|No| FAIL[Mark as Failed]
    FAIL --> DB_WRITE
    
    %% Completion
    DB_WRITE --> NEXT[Next Scheduled Job]
    SKIP --> NEXT
    NEXT --> WAIT
    
    %% Styling
    classDef start fill:#e8f5e8
    classDef process fill:#e3f2fd
    classDef decision fill:#fff3e0
    classDef data fill:#f3e5f5
    classDef external fill:#ffebee
    classDef success fill:#e8f5e8
    classDef error fill:#ffebee
    
    class START start
    class CONFIG,AUTH,OAUTH,TOKEN,REFRESH,SCHEDULER,CRON,WAIT,TRIGGER,DISCOVER,NEW_RELEASES,TRENDING,SEARCH,MERGE,FILTER,SCORE,RANK,DEDUPE,CAP,ALLOCATE,DB_READ,COMPARE,UPDATE,API_CALL,SNAPSHOT,LOG,METRICS,DB_WRITE,NEXT process
    class YAML,ENV,PERSONA,DIFF,SUCCESS,RETRY decision
    class POPULARITY,RECENCY,FEATURES,DELTA data
    class SPOTIFY_API external
    class LOG,DB_WRITE success
    class ERROR,FAIL error
```

## Data Flow Stages

### 1. Initialization
- **Configuration Loading**: Load settings from YAML, environment variables, and persona config
- **Authentication**: Initialize Spotify client with OAuth 2.0 credentials
- **Scheduler Setup**: Configure cron jobs for automated updates

### 2. Track Discovery
- **New Releases**: Fetch latest releases from Spotify
- **Trending Tracks**: Get popular tracks from charts
- **Genre Search**: Search for tracks by genre preferences
- **Source Merging**: Combine tracks from all sources

### 3. Track Processing
- **Filtering**: Remove tracks that don't meet criteria
- **Scoring**: Calculate scores based on popularity, recency, and features
- **Ranking**: Sort tracks by calculated scores
- **Deduplication**: Remove duplicate tracks
- **Artist Capping**: Limit tracks per artist for diversity
- **Genre Allocation**: Ensure genre diversity in final selection

### 4. Scoring Components
- **Popularity Score**: Based on Spotify popularity metric
- **Recency Boost**: Bonus for newer releases
- **Audio Features**: Energy, danceability, and other features
- **Popularity Delta**: Change in popularity over time

### 5. Update Decision
- **Database Read**: Get current playlist state
- **Comparison**: Compare new selection with current playlist
- **Change Detection**: Determine if update is needed

### 6. Playlist Update
- **API Call**: Make Spotify API request to update playlist
- **Success Handling**: Save snapshots and update metrics
- **Error Handling**: Log errors and retry if possible

### 7. Data Persistence
- **Snapshot Storage**: Save playlist state as JSON/CSV
- **Database Write**: Update SQLite database with metrics
- **Logging**: Record all operations for monitoring

## Key Data Points

### Input Data
- **Configuration**: YAML settings, environment variables
- **Spotify API**: Track metadata, popularity, audio features
- **User Preferences**: Genre preferences, scoring weights

### Processed Data
- **Track Scores**: Calculated scores for each track
- **Selection Results**: Final track selection for playlists
- **Update Decisions**: Whether updates are needed

### Output Data
- **Playlist Updates**: Modified Spotify playlists
- **Snapshots**: Historical playlist states
- **Metrics**: Performance and usage statistics
- **Logs**: Operation audit trail

## Error Handling

- **API Failures**: Retry with exponential backoff
- **Authentication Errors**: Refresh tokens automatically
- **Rate Limiting**: Respect API limits and wait
- **Data Validation**: Validate all inputs and outputs
- **Graceful Degradation**: Continue operation with partial data
