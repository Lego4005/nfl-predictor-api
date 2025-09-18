# 🗄️ NFL Predictor API - Database Schema Summary

## 📊 Complete Database Overview

Your Supabase database now contains **13 tables** with full vector search capabilities, realtime subscriptions, and comprehensive NFL prediction features.

## 🏗️ Table Structure

### Core NFL Data Tables

#### 1. **`teams`** - NFL Teams Information

```sql
- id (bigint, primary key)
- abbreviation (varchar(3), unique) - e.g., 'KC', 'BUF'
- name (varchar(100)) - e.g., 'Chiefs', 'Bills'
- city (varchar(100)) - e.g., 'Kansas City'
- full_name (varchar(200)) - e.g., 'Kansas City Chiefs'
- conference (varchar(3)) - 'AFC' or 'NFC'
- division (varchar(10)) - e.g., 'AFC West'
- primary_color, secondary_color, tertiary_color (varchar(7))
- logo_url, gradient (text)
- created_at, updated_at (timestamptz)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed

#### 2. **`games`** - NFL Games Information

```sql
- id (uuid, primary key)
- espn_game_id (varchar(50), unique)
- home_team, away_team (varchar(50))
- home_score, away_score (integer)
- game_time (timestamp)
- week, season (integer)
- season_type (varchar(20)) - 'preseason', 'regular', 'postseason'
- status (varchar(20)) - 'scheduled', 'live', 'final'
- quarter, time_remaining (varchar)
- venue, venue_city, venue_state (varchar)
- weather_data, odds_data (jsonb)
- created_at, updated_at (timestamp)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed

### Prediction & Analysis Tables

#### 3. **`predictions`** - AI Model Predictions

```sql
- id (uuid, primary key)
- game_id (uuid, foreign key)
- model_version (varchar(20)) - e.g., 'v1.0'
- prediction_type (varchar(50)) - 'spread', 'total', 'moneyline'
- home_win_prob, away_win_prob (decimal)
- predicted_spread, predicted_total (decimal)
- confidence (decimal)
- ml_features (jsonb) - ML feature values
- reasoning_text (text) - Human-readable reasoning
- analysis_embedding (vector(384)) - Vector for similarity search
- created_at (timestamp)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed | 🧮 Vector Search

#### 4. **`model_performance`** - AI Model Accuracy Tracking

```sql
- id (uuid, primary key)
- model_version (varchar(20))
- prediction_type (varchar(50))
- total_predictions, correct_predictions (integer)
- accuracy, roi (decimal)
- evaluation_date (date)
- metadata (jsonb)
- created_at (timestamp)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed

### Betting & User Data Tables

#### 5. **`odds_history`** - Betting Odds Tracking

```sql
- id (uuid, primary key)
- game_id (uuid, foreign key)
- bookmaker (varchar(50))
- spread_home, spread_away (decimal)
- total_over, total_under (decimal)
- moneyline_home, moneyline_away (integer)
- recorded_at (timestamp)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed

#### 6. **`user_picks`** - User Predictions/Picks

```sql
- id (uuid, primary key)
- user_id (uuid, foreign key to auth.users)
- game_id (uuid, foreign key)
- pick_type (varchar(20)) - 'spread', 'total', 'moneyline'
- pick_value (varchar(100))
- units (decimal) - Amount wagered
- confidence (integer) - 1-10 scale
- result (varchar(20)) - 'pending', 'win', 'loss', 'push'
- profit_loss (decimal)
- created_at (timestamp)
```

**Status**: ✅ RLS | ✅ Indexed

#### 7. **`user_stats`** - User Performance Tracking

```sql
- id (uuid, primary key)
- user_id (uuid, foreign key to auth.users, unique)
- total_picks, wins, losses, pushes (integer)
- total_units_wagered, total_profit_loss (decimal)
- roi (decimal)
- updated_at (timestamp)
```

**Status**: ✅ RLS | ✅ Indexed

### News & Content Tables

#### 8. **`news_articles`** - NFL News and Analysis

```sql
- id (bigint, primary key)
- title, content (text)
- author, source (varchar)
- published_at (timestamptz)
- url (text, unique)
- teams_mentioned (varchar(3)[]) - Array of team abbreviations
- sentiment_score (decimal) - -1 to 1
- created_at, updated_at (timestamptz)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed

#### 9. **`news_sentiment`** - News Sentiment Analysis

```sql
- id (uuid, primary key)
- article_url (text, unique)
- title, source (text/varchar)
- published_at (timestamp)
- teams_mentioned (text[]) - Array of team names
- sentiment_score (decimal) - -1 to 1
- impact_teams (jsonb) - Team-specific impact scores
- market_impact (text)
- embedding (vector(384)) - Vector for semantic search
- embedding_updated_at (timestamptz)
- created_at (timestamp)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed | 🧮 Vector Search

### Expert Analysis Tables

#### 10. **`expert_research`** - Expert Research Data

```sql
- id (bigint, primary key)
- expert_id (varchar(50))
- research_type (varchar(100)) - 'news', 'stats', 'weather', etc.
- content (text)
- metadata (jsonb)
- embedding (vector(384)) - Vector for semantic search
- relevance_score (float)
- created_at, updated_at (timestamptz)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed | 🧮 Vector Search

#### 11. **`expert_bets`** - Expert Betting History

```sql
- id (bigint, primary key)
- expert_id (varchar(50))
- game_id (uuid, foreign key)
- bet_type (varchar(50)) - 'spread', 'total', 'moneyline', 'prop'
- bet_value (decimal)
- confidence_level (integer) - 1-100
- reasoning (text)
- reasoning_embedding (vector(384)) - Vector for similarity search
- points_wagered, points_won (integer)
- is_winner (boolean)
- created_at, updated_at (timestamptz)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed | 🧮 Vector Search

#### 12. **`knowledge_base`** - Expert Knowledge Repository

```sql
- id (bigint, primary key)
- category (varchar(100)) - 'team_stats', 'player_injury', etc.
- title, content (text)
- source_url (text)
- embedding (vector(384)) - Vector for semantic search
- trust_score (integer) - 0-100
- created_at, updated_at (timestamptz)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed | 🧮 Vector Search

#### 13. **`team_embeddings`** - Team Performance Vectors

```sql
- id (uuid, primary key)
- team_name (varchar(50))
- season, week (integer)
- embedding (vector(384)) - Team performance vector
- metadata (jsonb)
- created_at (timestamp)
```

**Status**: ✅ Realtime | ✅ RLS | ✅ Indexed | 🧮 Vector Search

## 🧮 Vector Search Capabilities

### Tables with Vector Embeddings

- `predictions.analysis_embedding` - ML prediction reasoning
- `news_sentiment.embedding` - News article content
- `expert_research.embedding` - Expert research content
- `expert_bets.reasoning_embedding` - Betting reasoning
- `knowledge_base.embedding` - Knowledge base content
- `team_embeddings.embedding` - Team performance patterns

### Vector Search Functions

- `search_knowledge_base()` - Search expert knowledge
- `search_expert_research()` - Search research data
- `search_news_articles()` - Search news content
- `search_similar_bets()` - Find similar betting patterns
- `search_prediction_analysis()` - Search prediction reasoning
- `search_all_content()` - Multi-source semantic search
- `find_similar_teams()` - Team similarity analysis
- `find_similar_performance_patterns()` - Performance pattern matching

## 📡 Realtime Subscriptions

### Tables with Live Updates

- ✅ `games` - Live score updates
- ✅ `predictions` - New ML predictions
- ✅ `odds_history` - Betting line movements
- ✅ `news_articles` - News updates
- ✅ `news_sentiment` - Sentiment analysis updates
- ✅ `expert_research` - Expert analysis updates
- ✅ `expert_bets` - Betting decision updates
- ✅ `knowledge_base` - Knowledge base updates
- ✅ `model_performance` - Performance metrics
- ✅ `team_embeddings` - Team data updates

## 🔒 Security & Access Control

### Row Level Security (RLS)

- **Public Read Access**: All core tables (games, predictions, odds, news, etc.)
- **User-Specific Access**: `user_picks`, `user_stats` (users can only see their own data)
- **Expert Data**: `expert_research`, `expert_bets`, `knowledge_base` (public read, controlled write)

### Indexes for Performance

- **Primary Keys**: All tables have efficient primary key indexes
- **Foreign Keys**: All foreign key relationships are indexed
- **Search Columns**: Game time, status, teams, seasons, etc.
- **Vector Indexes**: HNSW indexes for fast vector similarity search
- **Array Indexes**: GIN indexes for team mentions and keywords

## 🚀 Usage Examples

### Basic Queries

```sql
-- Get all games for current week
SELECT * FROM games WHERE week = 10 AND season = 2023;

-- Get team information
SELECT * FROM teams WHERE conference = 'AFC';

-- Get latest predictions
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;
```

### Vector Search Queries

```javascript
// Search for similar betting patterns
const results = await supabase.rpc('search_similar_bets', {
  query_embedding: embedding,
  only_winners: true,
  match_threshold: 0.8
});

// Multi-source semantic search
const results = await supabase.rpc('search_all_content', {
  query_embedding: embedding,
  match_threshold: 0.7,
  match_count: 20
});
```

### Realtime Subscriptions

```javascript
// Subscribe to live game updates
const subscription = supabase
  .channel('live-games')
  .on('postgres_changes', 
    { event: 'UPDATE', schema: 'public', table: 'games' },
    (payload) => console.log('Game updated:', payload.new)
  )
  .subscribe();
```

## 📈 Performance Optimizations

### Database Features

- **pgvector v0.8.0** - Advanced vector similarity search
- **HNSW Indexes** - Fast approximate nearest neighbor search
- **GIN Indexes** - Efficient array and JSONB operations
- **Realtime** - Live updates via WebSocket connections
- **RLS** - Secure data access control

### Query Optimization

- All foreign keys are indexed
- Vector searches use optimized HNSW indexes
- Array searches use GIN indexes
- Time-based queries are indexed by timestamp columns

## 🎯 Perfect for NFL Predictor API

Your database schema supports:

- **Real-time Game Data** - Live scores and updates
- **AI Predictions** - ML model predictions with reasoning
- **Expert Analysis** - Research and betting intelligence
- **User Management** - Picks, stats, and performance tracking
- **News Intelligence** - Sentiment analysis and content search
- **Vector Search** - Semantic similarity across all content types
- **Betting Data** - Odds tracking and line movements

The database is now fully optimized for your NFL Predictor API with advanced vector search capabilities! 🏈🧠
