# Historical Data Management Scripts

## Overview

This directory contains scripts for fetching, processing, and managing historical NFL data for ML model training.

## Scripts

### 1. fetch_historical_data.py

Downloads historical NFL data from SportsData.io API for the last 3+ seasons.

**Features:**
- Fetches games, box scores, play-by-play data
- Downloads weather, injury, and betting information
- Rate-limited API requests (respects API limits)
- Saves raw JSON data for backup and debugging
- Supports both PostgreSQL and SQLite databases

**Usage:**
```bash
# Set your API key in .env file
export SPORTSDATA_API_KEY=your_key_here

# Run the fetcher
python scripts/fetch_historical_data.py
```

**Data Sources:**
- Game scores and basic info
- Team statistics per game
- Individual player performances
- Weather conditions
- Injury reports
- Betting lines and outcomes

### 2. populate_database.py

Processes raw JSON data and populates the database with structured records.

**Features:**
- Processes raw API data into normalized database records
- Calculates advanced metrics (EPA, success rates)
- Creates performance indexes for fast querying
- Validates data integrity
- Handles duplicate prevention

**Usage:**
```bash
# After running fetch_historical_data.py
python scripts/populate_database.py
```

**Processed Data:**
- Games table with scores, weather, betting data
- Team stats with offensive/defensive metrics
- Player stats for skill position players
- Betting outcomes and line movements
- Injury impacts on game outcomes

## Database Schema

The historical data is stored in 5 main tables:

1. **historical_games**: Core game information, scores, weather, stadium
2. **team_stats**: Team performance metrics per game
3. **player_stats**: Individual player statistics
4. **betting_data**: Historical betting lines and outcomes
5. **injuries**: Injury reports and player availability

## Configuration

Update your `.env` file with the following variables:

```env
# API Key
SPORTSDATA_API_KEY=your_sportsdata_io_key

# Database Type
DB_TYPE=sqlite  # or postgresql

# SQLite (Development)
DB_PATH=data/nfl_historical.db

# PostgreSQL (Production)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nfl_predictor
DB_USER=postgres
DB_PASSWORD=your_password
```

## Data Flow

1. **Fetch** → Raw JSON files saved to `data/raw/`
2. **Process** → Structured data inserted into database
3. **Index** → Performance indexes created for fast ML queries
4. **Validate** → Data integrity checks and statistics

## ML Model Training

Once populated, the database provides:

- 3+ seasons of game outcomes for training
- Advanced metrics (EPA, success rates, efficiency)
- Weather and injury context
- Betting market information for validation
- Player-level performance data

## Performance Optimizations

The system includes several optimizations:

- **Indexes**: Optimized for common ML queries
- **Batch Processing**: Commits data in batches for speed
- **Error Handling**: Graceful handling of API failures
- **Duplicate Prevention**: Avoids re-processing existing data
- **Memory Efficient**: Processes data in chunks

## Monitoring and Validation

Built-in monitoring includes:

- API rate limit compliance
- Data integrity checks
- Season/game distribution analysis
- Orphaned record detection
- Performance benchmarking

## Troubleshooting

**Common Issues:**

1. **API Rate Limits**: Increase `request_delay` in fetcher
2. **Database Errors**: Check connection settings in `.env`
3. **Missing Data**: Verify API key and endpoint availability
4. **Performance**: Ensure indexes are created after population

**Logs Location**: Check console output for detailed error messages and progress updates.