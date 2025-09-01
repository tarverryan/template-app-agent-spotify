# Track Selection Process

This diagram illustrates the track selection process, showing how tracks are discovered, scored, and selected for playlists in the Spotify App Agent Template.

```mermaid
flowchart TD
    %% Discovery Sources
    subgraph "Track Discovery"
        NEW_RELEASES[New Releases API]
        TRENDING[Trending Charts]
        GENRE_SEARCH[Genre-based Search]
        USER_PLAYLISTS[User Playlists]
    end
    
    %% Initial Processing
    subgraph "Initial Processing"
        MERGE[Merge Track Sources]
        FILTER_BASIC[Basic Filtering]
        REMOVE_DUPS[Remove Duplicates]
    end
    
    %% Scoring Components
    subgraph "Scoring System"
        POPULARITY[Popularity Score<br/>0-100]
        RECENCY[Recency Boost<br/>Newer = Higher]
        FEATURES[Audio Features<br/>Energy, Danceability]
        DELTA[Popularity Delta<br/>Change over time]
        TERRITORY[Territory Weighting<br/>US vs Global]
    end
    
    %% Scoring Calculation
    subgraph "Score Calculation"
        CALCULATE[Calculate Final Score]
        WEIGHTS[Apply Scoring Weights]
        NORMALIZE[Normalize Scores]
    end
    
    %% Selection Process
    subgraph "Selection Process"
        RANK[Rank by Score]
        ARTIST_CAP[Apply Artist Caps]
        GENRE_ALLOCATE[Genre Allocation]
        DIVERSITY[Diversity Floor]
        FINAL_SELECT[Final Selection]
    end
    
    %% Configuration
    subgraph "Configuration"
        SCORING_CONFIG[Scoring Weights]
        GENRE_CONFIG[Genre Buckets]
        CAPS_CONFIG[Artist Caps]
        DIVERSITY_CONFIG[Diversity Settings]
    end
    
    %% Database
    subgraph "Database"
        CURRENT_PLAYLIST[Current Playlist State]
        HISTORY[Track History]
        METRICS[Performance Metrics]
    end
    
    %% Flow
    NEW_RELEASES --> MERGE
    TRENDING --> MERGE
    GENRE_SEARCH --> MERGE
    USER_PLAYLISTS --> MERGE
    
    MERGE --> FILTER_BASIC
    FILTER_BASIC --> REMOVE_DUPS
    
    REMOVE_DUPS --> POPULARITY
    REMOVE_DUPS --> RECENCY
    REMOVE_DUPS --> FEATURES
    REMOVE_DUPS --> DELTA
    REMOVE_DUPS --> TERRITORY
    
    POPULARITY --> CALCULATE
    RECENCY --> CALCULATE
    FEATURES --> CALCULATE
    DELTA --> CALCULATE
    TERRITORY --> CALCULATE
    
    SCORING_CONFIG --> WEIGHTS
    CALCULATE --> WEIGHTS
    WEIGHTS --> NORMALIZE
    NORMALIZE --> RANK
    
    RANK --> ARTIST_CAP
    CAPS_CONFIG --> ARTIST_CAP
    
    ARTIST_CAP --> GENRE_ALLOCATE
    GENRE_CONFIG --> GENRE_ALLOCATE
    
    GENRE_ALLOCATE --> DIVERSITY
    DIVERSITY_CONFIG --> DIVERSITY
    
    DIVERSITY --> FINAL_SELECT
    
    CURRENT_PLAYLIST --> FINAL_SELECT
    HISTORY --> FINAL_SELECT
    METRICS --> FINAL_SELECT
    
    %% Styling
    classDef discovery fill:#e3f2fd
    classDef processing fill:#f3e5f5
    classDef scoring fill:#e8f5e8
    classDef selection fill:#fff3e0
    classDef config fill:#ffebee
    classDef database fill:#f1f8e9
    
    class NEW_RELEASES,TRENDING,GENRE_SEARCH,USER_PLAYLISTS discovery
    class MERGE,FILTER_BASIC,REMOVE_DUPS processing
    class POPULARITY,RECENCY,FEATURES,DELTA,TERRITORY,CALCULATE,WEIGHTS,NORMALIZE scoring
    class RANK,ARTIST_CAP,GENRE_ALLOCATE,DIVERSITY,FINAL_SELECT selection
    class SCORING_CONFIG,GENRE_CONFIG,CAPS_CONFIG,DIVERSITY_CONFIG config
    class CURRENT_PLAYLIST,HISTORY,METRICS database
```

## Track Discovery Methods

### 1. New Releases
- **API Endpoint**: `/browse/new-releases`
- **Purpose**: Find latest releases from artists
- **Parameters**: Country, limit, offset
- **Frequency**: Daily updates

### 2. Trending Charts
- **API Endpoint**: `/playlists/37i9dQZEVXbMDoHDwVN2tF` (Global Top 50)
- **Purpose**: Get currently popular tracks
- **Parameters**: Market, limit
- **Frequency**: Real-time popularity

### 3. Genre-based Search
- **API Endpoint**: `/search`
- **Purpose**: Find tracks by specific genres
- **Parameters**: Query, type, market, limit
- **Genres**: Pop, Hip-Hop, Rock, EDM, etc.

### 4. User Playlists
- **API Endpoint**: `/users/{user_id}/playlists`
- **Purpose**: Source from user's existing playlists
- **Parameters**: User ID, limit, offset
- **Use Case**: Seeding new playlists

## Scoring Algorithm

### Scoring Components

#### 1. Popularity Score (55% weight)
- **Source**: Spotify popularity metric (0-100)
- **Calculation**: Direct value from API
- **Purpose**: Prioritize popular tracks

#### 2. Popularity Delta (30% weight)
- **Source**: Change in popularity over time
- **Calculation**: Current popularity - Previous popularity
- **Purpose**: Identify trending tracks

#### 3. Recency Boost (10% weight)
- **Source**: Track release date
- **Calculation**: Boost for newer releases
- **Purpose**: Favor recent releases

#### 4. Audio Features (5% weight)
- **Source**: Spotify audio analysis
- **Features**: Energy, danceability, valence
- **Purpose**: Match target audio profile

### Territory Weighting
- **US Popularity**: 70% weight
- **Global Popularity**: 30% weight
- **Purpose**: Balance local and global trends

## Selection Process

### 1. Artist Capping
- **Daily Playlists**: Maximum 1 track per artist
- **Weekly/Monthly**: Maximum 2 tracks per artist
- **Yearly**: Maximum 2 tracks per artist (with override)
- **Override**: Allow up to 3 tracks for dominant artists

### 2. Genre Allocation
- **Adaptive Allocation**: Popular genres get more slots
- **Diversity Floor**: Minimum 3% per genre for yearly playlists
- **Genre Buckets**: Grouped genres for better categorization

### 3. Deduplication
- **Time-based**: Remove tracks from recent playlists
- **Artist-based**: Limit tracks per artist
- **Playlist-based**: Avoid duplicate tracks within playlist

### 4. Final Selection
- **Size Limits**: Respect playlist size configuration
- **Quality Threshold**: Minimum score requirements
- **Diversity Balance**: Ensure genre variety

## Configuration Options

### Scoring Weights
```yaml
scoring:
  weights:
    popularity: 0.55
    popularity_delta: 0.30
    recency_boost: 0.10
    audio_feature_fit: 0.05
```

### Genre Configuration
```yaml
genres:
  buckets:
    Pop: ["pop", "indie pop", "dance pop"]
    HipHop: ["hip hop", "rap", "trap"]
    Rock: ["rock", "alternative rock", "indie rock"]
```

### Artist Caps
```yaml
artist_caps:
  playlist1: 1
  playlist2: 2
  playlist3: 2
  playlist4: 2
```

## Performance Optimization

### Caching
- **Track Cache**: Cache track data to reduce API calls
- **Score Cache**: Cache calculated scores
- **Genre Cache**: Cache genre classifications

### Batch Processing
- **API Batching**: Batch multiple API requests
- **Parallel Processing**: Process tracks in parallel
- **Memory Management**: Efficient memory usage

### Error Handling
- **API Failures**: Retry with exponential backoff
- **Missing Data**: Handle incomplete track information
- **Rate Limiting**: Respect API rate limits
