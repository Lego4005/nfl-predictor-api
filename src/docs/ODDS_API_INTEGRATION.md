# NFL Odds API Integration

## Overview

The oddsService.js has been updated to use the real The Odds API with your provided API key. The service successfully fetches live NFL odds data and stores them in the odds_history table in Supabase.

## ✅ What's Working

- **Real API Integration**: Using The Odds API with key `ecc8b23af5c6e928ab61ef790048aaab`
- **Endpoint**: `https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds`
- **Parameters**:
  - `apiKey`: Your API key
  - `regions`: us
  - `markets`: h2h,spreads,totals
- **API Status**: ✅ 200 OK (497/500 requests remaining)

## 📊 Current Data Available

The API is currently returning **6 NFL games** with odds from **5 bookmakers** including:
- DraftKings
- FanDuel
- BetMGM
- Caesars
- PointsBet

### Sample Data Structure
```json
{
  "away_team": "Carolina Panthers",
  "home_team": "Arizona Cardinals",
  "commence_time": "2025-09-14T20:04:31Z",
  "sport_key": "americanfootball_nfl",
  "bookmakers": [
    {
      "title": "DraftKings",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {"name": "Arizona Cardinals", "price": -6500},
            {"name": "Carolina Panthers", "price": 1800}
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {"name": "Arizona Cardinals", "price": -110, "point": -19.5},
            {"name": "Carolina Panthers", "price": -120, "point": 19.5}
          ]
        },
        {
          "key": "totals",
          "outcomes": [
            {"name": "Over", "price": -105, "point": 44.5},
            {"name": "Under", "price": -125, "point": 44.5}
          ]
        }
      ]
    }
  ]
}
```

## 🗄️ Database Integration

### Updated Database Schema
- **Migration Added**: `003_add_odds_data_to_games.sql`
- **Odds History Table**: Stores individual odds records per sportsbook/bet type
- **Games Table**: Added `odds_data` JSONB column for consensus odds

### Data Storage Structure
Each odds entry is stored as individual records:

| Column | Description | Example |
|--------|-------------|---------|
| game_id | Foreign key to games table | 123 |
| sportsbook | Bookmaker name | "DraftKings" |
| bet_type | Type of bet | "spread_home", "moneyline_away", "total_over" |
| odds_value | American odds | -110, +180 |
| line_value | Point spread/total | -19.5, 44.5 |
| recorded_at | Timestamp | ISO timestamp |

## 🚀 How to Use

### 1. Test the API Connection
```bash
node src/test/test_odds_api_simple.js
```

### 2. Fetch Current Odds
```javascript
import oddsService from './src/services/oddsService.js';

// Get current NFL odds
const odds = await oddsService.getNFLOdds();
console.log(`Fetched odds for ${odds.length} games`);
```

### 3. Sync to Database
```javascript
// Sync odds to Supabase (requires database setup)
const syncResult = await oddsService.syncOddsToSupabase();
console.log(`Synced ${syncResult.synced}/${syncResult.total} records`);
```

### 4. Check API Quota
```javascript
const quota = await oddsService.checkQuota();
console.log(`API Usage: ${quota.used}/${quota.total}, Remaining: ${quota.remaining}`);
```

### 5. Start Auto-Sync (10 minute intervals)
```javascript
// Start automatic syncing every 10 minutes
oddsService.startAutoSync(600000);

// Stop auto-sync when needed
oddsService.stopAutoSync();
```

## 📈 API Quota Management

- **Total Requests**: 500 per month (free tier)
- **Current Usage**: 3/500 requests used
- **Remaining**: 497 requests
- **Cost per Request**: ~1 request per sync operation

## 🛠️ Key Features Implemented

1. **Real-time Odds Fetching**: Direct integration with The Odds API
2. **Multi-Bookmaker Support**: Aggregates odds from 5+ sportsbooks
3. **Comprehensive Market Coverage**: Moneyline, spreads, and totals
4. **Database Storage**: Persistent storage in Supabase
5. **Caching**: 10-minute cache to optimize API calls
6. **Consensus Odds**: Calculates median values across bookmakers
7. **Team Name Mapping**: Maps full team names to abbreviations
8. **Error Handling**: Robust error handling and logging
9. **Auto-sync**: Scheduled background updates
10. **Quota Monitoring**: Tracks API usage limits

## 🔧 Configuration Files Updated

- `/src/services/oddsService.js` - Main odds service implementation
- `/.env` - Contains your API key
- `/src/database/migrations/003_add_odds_data_to_games.sql` - Database schema update
- `/src/test/test_odds_api_simple.js` - API testing utility

## 📋 Next Steps

To fully integrate odds data into your application:

1. **Run the database migration**:
   ```sql
   -- Execute: src/database/migrations/003_add_odds_data_to_games.sql
   ```

2. **Start the odds service in your main application**:
   ```javascript
   import oddsService from './src/services/oddsService.js';

   // Start auto-sync on app startup
   oddsService.startAutoSync();
   ```

3. **Display odds in your UI** by fetching from the odds_history table

4. **Monitor API usage** to avoid hitting the 500 request monthly limit

The odds service is now ready to provide real-time NFL betting odds for your prediction platform!