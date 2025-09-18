# 🚀 Supabase Setup Instructions

## Step 1: Create Supabase Account & Project

1. Go to <https://supabase.com>
2. Sign up with GitHub or Email
3. Click "New Project"
4. Fill in:
   - **Project Name**: `nfl-predictor` (or your choice)
   - **Database Password**: Save this securely! You'll need it.
   - **Region**: Choose closest to you (e.g., US East)
   - **Pricing Plan**: Free tier is fine

## Step 2: Run Database Schema

Once your project is created, go to the **SQL Editor** in Supabase dashboard and run these queries in order:

### Query 1: Core Tables

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Games table
CREATE TABLE games (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  espn_game_id VARCHAR(50) UNIQUE,
  home_team VARCHAR(50) NOT NULL,
  away_team VARCHAR(50) NOT NULL,
  home_score INTEGER DEFAULT 0,
  away_score INTEGER DEFAULT 0,
  game_time TIMESTAMP NOT NULL,
  week INTEGER,
  season INTEGER,
  season_type VARCHAR(20), -- preseason, regular, postseason
  status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, live, final
  quarter INTEGER,
  time_remaining VARCHAR(10),
  venue VARCHAR(100),
  venue_city VARCHAR(50),
  venue_state VARCHAR(2),
  weather_data JSONB,
  odds_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_games_espn_id ON games(espn_game_id);
CREATE INDEX idx_games_game_time ON games(game_time);
CREATE INDEX idx_games_week_season ON games(week, season);
CREATE INDEX idx_games_status ON games(status);
```

### Query 2: Predictions Table

```sql
-- Predictions table
CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  game_id UUID REFERENCES games(id) ON DELETE CASCADE,
  model_version VARCHAR(20) DEFAULT 'v1.0',
  prediction_type VARCHAR(50), -- spread, total, moneyline, player_prop
  home_win_prob DECIMAL(5,2),
  away_win_prob DECIMAL(5,2),
  predicted_spread DECIMAL(5,1),
  predicted_total DECIMAL(5,1),
  confidence DECIMAL(5,2),
  ml_features JSONB, -- Store feature values used
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_predictions_game_id ON predictions(game_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);
```

### Query 3: Odds History

```sql
-- Odds history table
CREATE TABLE odds_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  game_id UUID REFERENCES games(id) ON DELETE CASCADE,
  bookmaker VARCHAR(50),
  spread_home DECIMAL(5,1),
  spread_away DECIMAL(5,1),
  total_over DECIMAL(5,1),
  total_under DECIMAL(5,1),
  moneyline_home INTEGER,
  moneyline_away INTEGER,
  recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_odds_game_id ON odds_history(game_id);
CREATE INDEX idx_odds_recorded_at ON odds_history(recorded_at);
```

### Query 4: User Tables (If implementing auth)

```sql
-- User picks table
CREATE TABLE user_picks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  game_id UUID REFERENCES games(id) ON DELETE CASCADE,
  pick_type VARCHAR(20), -- spread, total, moneyline
  pick_value VARCHAR(100), -- team name or over/under
  units DECIMAL(5,2) DEFAULT 1,
  confidence INTEGER CHECK (confidence >= 1 AND confidence <= 10),
  result VARCHAR(20), -- pending, win, loss, push
  profit_loss DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- User stats table
CREATE TABLE user_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  total_picks INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  pushes INTEGER DEFAULT 0,
  total_units_wagered DECIMAL(10,2) DEFAULT 0,
  total_profit_loss DECIMAL(10,2) DEFAULT 0,
  roi DECIMAL(5,2) DEFAULT 0,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_picks_user_id ON user_picks(user_id);
CREATE INDEX idx_user_picks_game_id ON user_picks(game_id);
```

### Query 5: News & Sentiment

```sql
-- News and sentiment table
CREATE TABLE news_sentiment (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  article_url TEXT UNIQUE,
  title TEXT,
  source VARCHAR(100),
  published_at TIMESTAMP,
  teams_mentioned TEXT[], -- Array of team names
  sentiment_score DECIMAL(3,2), -- -1 to 1
  impact_teams JSONB, -- {"KC": 0.3, "BUF": -0.2}
  market_impact TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_news_published_at ON news_sentiment(published_at);
CREATE INDEX idx_news_teams ON news_sentiment USING GIN(teams_mentioned);
```

### Query 6: Model Performance Tracking

```sql
-- Model performance table
CREATE TABLE model_performance (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_version VARCHAR(20),
  prediction_type VARCHAR(50),
  total_predictions INTEGER DEFAULT 0,
  correct_predictions INTEGER DEFAULT 0,
  accuracy DECIMAL(5,2),
  roi DECIMAL(5,2),
  evaluation_date DATE,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_model_performance_date ON model_performance(evaluation_date);
```

## Step 3: Set Up Row Level Security (RLS)

Run these to enable security:

```sql
-- Enable RLS on all tables
ALTER TABLE games ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE odds_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_picks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_sentiment ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_performance ENABLE ROW LEVEL SECURITY;

-- Public read access for games, predictions, odds
CREATE POLICY "Public read access" ON games FOR SELECT USING (true);
CREATE POLICY "Public read access" ON predictions FOR SELECT USING (true);
CREATE POLICY "Public read access" ON odds_history FOR SELECT USING (true);
CREATE POLICY "Public read access" ON news_sentiment FOR SELECT USING (true);
CREATE POLICY "Public read access" ON model_performance FOR SELECT USING (true);

-- User-specific access for picks and stats
CREATE POLICY "Users can view own picks" ON user_picks
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own picks" ON user_picks
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view own stats" ON user_stats
  FOR SELECT USING (auth.uid() = user_id);
```

## Step 4: Create Database Functions

```sql
-- Function to update game status
CREATE OR REPLACE FUNCTION update_game_status()
RETURNS void AS $$
BEGIN
  -- Mark games as live if current time is past game_time
  UPDATE games
  SET status = 'live'
  WHERE status = 'scheduled'
    AND game_time <= NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to calculate user ROI
CREATE OR REPLACE FUNCTION calculate_user_roi(p_user_id UUID)
RETURNS DECIMAL AS $$
DECLARE
  v_roi DECIMAL;
BEGIN
  SELECT
    CASE
      WHEN total_units_wagered > 0
      THEN (total_profit_loss / total_units_wagered * 100)
      ELSE 0
    END INTO v_roi
  FROM user_stats
  WHERE user_id = p_user_id;

  RETURN COALESCE(v_roi, 0);
END;
$$ LANGUAGE plpgsql;
```

## Step 5: Create Realtime Subscriptions

In Supabase Dashboard, go to **Database > Replication** and enable realtime for:

- `games` table (for live score updates)
- `predictions` table (for new predictions)
- `odds_history` table (for line movements)

## Step 6: Get Your Connection Details

1. Go to **Settings > API** in your Supabase dashboard
2. Copy these values:

```env
# Add to your .env file
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_KEY=[YOUR-SERVICE-KEY]  # Only for backend, keep secret!
```

## Step 7: Test the Connection

Create a test file `testSupabase.js`:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_ANON_KEY

const supabase = createClient(supabaseUrl, supabaseKey)

// Test query
async function testConnection() {
  const { data, error } = await supabase
    .from('games')
    .select('*')
    .limit(1)

  if (error) {
    console.error('Error:', error)
  } else {
    console.log('Success! Connected to Supabase')
    console.log('Data:', data)
  }
}

testConnection()
```

## What I Need From You

### 1. After Creating Project, Send Me

```
SUPABASE_URL: [your-project-url]
SUPABASE_ANON_KEY: [your-anon-key]
```

(Keep the SERVICE_KEY private - don't share it)

### 2. Confirm These Tables Were Created

- [ ] games
- [ ] predictions
- [ ] odds_history
- [ ] user_picks
- [ ] user_stats
- [ ] news_sentiment
- [ ] model_performance

### 3. Enable These in Dashboard

- [ ] Realtime on games, predictions, odds_history tables
- [ ] Authentication (Email/Password or OAuth)

### 4. Optional: Custom Domain

If you have a custom domain, you can set it up in:
**Settings > Custom Domains**

## Next Steps After Setup

Once you provide the Supabase credentials, I will:

1. Create the data service layer (`/src/services/supabaseService.js`)
2. Set up real-time subscriptions for live games
3. Build the data pipeline to sync ESPN data
4. Create the prediction engine integration
5. Implement caching layer to minimize database calls

## Common Issues & Solutions

**Issue**: "relation "auth.users" does not exist"
**Solution**: Enable Authentication in your Supabase dashboard first

**Issue**: Cannot connect from frontend
**Solution**: Check that your URL and anon key are correct, and RLS policies are set

**Issue**: Realtime not working
**Solution**: Make sure you enabled replication for the tables in Database > Replication

---

**Questions?** The Supabase Discord and documentation are excellent resources:

- Docs: <https://supabase.com/docs>
- Discord: <https://discord.supabase.com>
