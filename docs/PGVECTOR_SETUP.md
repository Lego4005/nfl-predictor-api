# 🧮 pgvector Setup for NFL Predictor API

## Overview

pgvector is now enabled in your Supabase database, providing powerful vector similarity search capabilities for machine learning and AI features in your NFL Predictor API.

## ✅ What's Enabled

- **pgvector extension v0.8.0** - Latest version with full functionality
- **Vector similarity search** - Cosine distance, L2 distance, inner product
- **IVFFlat indexing** - Optimized for fast similarity searches
- **Custom functions** - Team similarity and performance pattern matching

## 🏈 NFL-Specific Use Cases

### 1. Team Performance Similarity

Find teams with similar performance patterns across different seasons:

```sql
-- Find teams similar to Chiefs in 2023 Week 10
SELECT * FROM find_similar_performance_patterns('Kansas City Chiefs', 2023, 10, 5);
```

### 2. Player Embeddings

Store and search player performance vectors:

```sql
-- Create player embeddings table
CREATE TABLE player_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  player_name VARCHAR(100),
  position VARCHAR(20),
  season INTEGER,
  week INTEGER,
  stats_embedding VECTOR(384), -- Performance stats as vector
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Game Outcome Predictions

Use vector similarity to predict game outcomes:

```sql
-- Find similar game situations
SELECT 
  g.home_team,
  g.away_team,
  g.game_time,
  1 - (te.embedding <=> query_vector) AS similarity
FROM games g
JOIN team_embeddings te ON g.home_team = te.team_name
WHERE te.season = 2023
ORDER BY te.embedding <=> query_vector
LIMIT 10;
```

## 🔧 Available Functions

### `find_similar_teams(query_embedding, team_name_filter, season_filter, limit_count)`

Find teams with similar vector embeddings.

**Parameters:**

- `query_embedding`: VECTOR(384) - The embedding to search for
- `team_name_filter`: VARCHAR(50) - Optional team name filter
- `season_filter`: INTEGER - Optional season filter
- `limit_count`: INTEGER - Number of results (default: 5)

**Returns:**

- `team_name`: Team name
- `season`: Season year
- `week`: Week number
- `similarity_score`: Float (0-1, higher = more similar)
- `metadata`: JSONB with additional data

### `find_similar_performance_patterns(target_team, target_season, target_week, limit_count)`

Find teams with similar performance patterns to a target team.

**Parameters:**

- `target_team`: VARCHAR(50) - Team to find similar patterns for
- `target_season`: INTEGER - Season year
- `target_week`: INTEGER - Week number
- `limit_count`: INTEGER - Number of results (default: 5)

## 📊 Vector Operations

### Distance Functions

```sql
-- Cosine distance (0-2, lower = more similar)
SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector;

-- L2 distance (Euclidean)
SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector;

-- Inner product (higher = more similar)
SELECT '[1,2,3]'::vector <#> '[4,5,6]'::vector;
```

### Vector Functions

```sql
-- Get vector dimensions
SELECT vector_dims('[1,2,3,4,5]'::vector);

-- Normalize vector
SELECT '[1,2,3]'::vector / norm('[1,2,3]'::vector);
```

## 🚀 Integration Examples

### 1. Team Similarity Service

```javascript
// Find similar teams using Supabase client
const { data, error } = await supabase.rpc('find_similar_teams', {
  query_embedding: teamEmbedding, // 384-dimensional vector
  team_name_filter: 'Kansas City Chiefs',
  season_filter: 2023,
  limit_count: 5
});
```

### 2. Performance Pattern Matching

```javascript
// Find teams with similar performance patterns
const { data, error } = await supabase.rpc('find_similar_performance_patterns', {
  target_team: 'Kansas City Chiefs',
  target_season: 2023,
  target_week: 10,
  limit_count: 10
});
```

### 3. Vector Search with Filters

```javascript
// Search team embeddings with custom filters
const { data, error } = await supabase
  .from('team_embeddings')
  .select('*')
  .not('embedding', 'is', null)
  .eq('season', 2023)
  .order('embedding', { ascending: true }) // This will use vector similarity
  .limit(10);
```

## 🎯 ML Integration Ideas

### 1. Team Performance Clustering

- Group teams by similar performance patterns
- Identify "hot" and "cold" streaks
- Predict team trajectory based on similar teams

### 2. Player Similarity

- Find players with similar playing styles
- Predict player performance based on similar players
- Identify breakout candidates

### 3. Game Situation Analysis

- Find similar game situations from history
- Predict outcomes based on historical patterns
- Adjust predictions based on similar games

### 4. Betting Line Analysis

- Find games with similar betting patterns
- Identify value bets based on historical data
- Predict line movements

## 📈 Performance Optimization

### Indexing Strategy

```sql
-- IVFFlat index for fast similarity search
CREATE INDEX idx_team_embeddings_vector ON team_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- HNSW index for even faster search (if supported)
CREATE INDEX idx_team_embeddings_hnsw ON team_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

### Query Optimization

- Use `LIMIT` to reduce result set size
- Filter by season/week before vector search
- Cache frequently accessed embeddings
- Use batch operations for multiple queries

## 🧪 Testing

Run the updated test file to verify pgvector functionality:

```bash
node testSupabase.js
```

This will test:

- ✅ pgvector extension availability
- ✅ Vector operations (dimensions, distances)
- ✅ Vector table accessibility
- ✅ Custom similarity functions

## 🔗 Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Supabase Vector Search Guide](https://supabase.com/docs/guides/ai/vector-search)
- [Vector Similarity Search Best Practices](https://supabase.com/docs/guides/ai/vector-search#best-practices)

## 🎉 Next Steps

1. **Generate embeddings** for your historical data
2. **Implement similarity search** in your API endpoints
3. **Create ML models** that output vector embeddings
4. **Build recommendation systems** based on team/player similarity
5. **Add real-time vector updates** as new data comes in

Your NFL Predictor API now has powerful vector search capabilities for advanced ML features! 🏈🧮
