# 🔍 Vector Search Service Documentation

## Overview

The Vector Search Service provides comprehensive semantic search capabilities for your NFL Predictor API, enabling intelligent analysis of expert research, betting patterns, news articles, and prediction data using vector embeddings.

## 🏗️ Architecture

### Core Components

- **VectorSearchService Class**: Main service for all vector operations
- **Supabase Integration**: Database operations and RPC function calls
- **Edge Functions**: Embedding generation via `generate-embeddings`
- **HNSW Indexes**: Optimized vector similarity search

### Database Tables with Vector Support

- `knowledge_base` - Expert knowledge and research
- `expert_research` - Research data from experts
- `expert_bets` - Betting history with reasoning
- `news_sentiment` - News articles with sentiment analysis
- `predictions` - ML predictions with analysis embeddings
- `team_embeddings` - Team performance vectors

## 🚀 Usage

### Basic Setup

```javascript
import vectorSearchService from './src/services/vectorSearchService.js'

// The service is a singleton, ready to use immediately
```

### 1. Generate Embeddings

```javascript
const text = "Kansas City Chiefs vs Buffalo Bills analysis"
const embedding = await vectorSearchService.generateEmbedding(text)
// Returns 384-dimensional vector array
```

### 2. Search Knowledge Base

```javascript
const results = await vectorSearchService.searchKnowledgeBase(
  "NFL team performance analysis",
  {
    matchThreshold: 0.8,    // Similarity threshold (0-1)
    matchCount: 5,          // Number of results
    categoryFilter: "team_stats" // Optional category filter
  }
)

console.log(results.results) // Array of matching knowledge entries
```

### 3. Search Expert Research

```javascript
const results = await vectorSearchService.searchExpertResearch(
  "betting strategies and weather impact",
  {
    matchThreshold: 0.8,
    matchCount: 10,
    expertIdFilter: "expert_001",        // Optional expert filter
    researchTypeFilter: "weather_analysis" // Optional type filter
  }
)
```

### 4. Search News Articles

```javascript
const results = await vectorSearchService.searchNewsArticles(
  "NFL injury reports and team news",
  {
    matchThreshold: 0.8,
    matchCount: 5
  }
)
```

### 5. Search Similar Betting Patterns

```javascript
const results = await vectorSearchService.searchSimilarBets(
  "spread betting analysis and reasoning",
  {
    matchThreshold: 0.8,
    matchCount: 10,
    expertIdFilter: "expert_001", // Optional
    onlyWinners: true            // Only winning bets
  }
)
```

### 6. Search Prediction Analysis

```javascript
const results = await vectorSearchService.searchPredictionAnalysis(
  "ML model predictions and confidence scores",
  {
    matchThreshold: 0.8,
    matchCount: 5
  }
)
```

### 7. Multi-Source Search

```javascript
const results = await vectorSearchService.searchAllContent(
  "NFL predictions and betting analysis",
  {
    matchThreshold: 0.8,
    matchCount: 20
  }
)

// Results grouped by source
console.log(results.sources)
// {
//   knowledge_base: [...],
//   expert_research: [...],
//   news_sentiment: [...]
// }
```

## 📝 Data Management

### Store Expert Research

```javascript
const result = await vectorSearchService.storeExpertResearch(
  'expert_001',                    // Expert ID
  'team_analysis',                 // Research type
  'Chiefs have strong offense...', // Content
  { teams: ['Chiefs'], type: 'offensive' } // Metadata
)
```

### Store Expert Bet

```javascript
const result = await vectorSearchService.storeExpertBet(
  'expert_001',                    // Expert ID
  'game-uuid-here',               // Game ID
  'spread',                       // Bet type
  3.5,                           // Bet value
  85,                            // Confidence (1-100)
  'Chiefs have home field advantage...' // Reasoning
)
```

### Add Knowledge

```javascript
const result = await vectorSearchService.addKnowledge(
  'team_stats',                   // Category
  'Chiefs Offensive Performance', // Title
  'Chiefs led NFL in passing...', // Content
  'https://example.com/stats',    // Source URL
  85                             // Trust score (0-100)
)
```

## 🔄 Bulk Operations

### Bulk Embedding Generation

```javascript
// Process all records without embeddings
const result = await vectorSearchService.bulkEmbedExistingContent(
  'knowledge_base',  // Table name
  'content',         // Text column
  'embedding'        // Embedding column
)

console.log(`Processed ${result.processed} records`)
```

## 🎯 Advanced Features

### Similarity Thresholds

- **0.9+**: Very high similarity (near duplicates)
- **0.8-0.9**: High similarity (very relevant)
- **0.7-0.8**: Good similarity (relevant)
- **0.6-0.7**: Moderate similarity (somewhat relevant)
- **<0.6**: Low similarity (may not be relevant)

### Filtering Options

- **Category Filter**: Search specific knowledge categories
- **Expert Filter**: Search specific expert's data
- **Type Filter**: Search specific research types
- **Winner Filter**: Only show winning bets

### Result Grouping

Multi-source search automatically groups results by source table for easy organization.

## 🧪 Testing

### Run Vector Search Tests

```bash
node testVectorSearchService.js
```

### Run Database Tests

```bash
node testSupabase.js
```

### Test Individual Functions

```javascript
import { testVectorSearchService } from './testVectorSearchService.js'

const success = await testVectorSearchService()
console.log('Tests passed:', success)
```

## 🔧 Configuration

### Environment Variables

```env
SUPABASE_URL=https://vaypgzvivahnfegnlinn.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

### Service Configuration

```javascript
class VectorSearchService {
  constructor() {
    this.embeddingDimensions = 384  // Vector dimension
  }
}
```

## 📊 Performance Optimization

### Indexing Strategy

- **HNSW Indexes**: Fast approximate nearest neighbor search
- **Cosine Similarity**: Optimized for semantic similarity
- **Batch Processing**: Bulk operations for efficiency

### Caching

- Embeddings are cached in the database
- Similarity searches use indexed vectors
- Results can be cached at application level

### Rate Limiting

- Bulk operations include 200ms delays
- Edge function calls are rate-limited
- Database queries are optimized

## 🚨 Error Handling

### Common Errors

- **Embedding Generation Failed**: Falls back to zero vector
- **Database Connection Error**: Returns error with details
- **Invalid Parameters**: Validates input before processing

### Error Response Format

```javascript
{
  success: false,
  error: "Error message",
  results: [],
  query: "original query",
  matchCount: 0
}
```

## 🔗 Integration Examples

### React Component

```jsx
import { useState, useEffect } from 'react'
import vectorSearchService from './services/vectorSearchService.js'

function ExpertAnalysis({ query }) {
  const [results, setResults] = useState([])
  
  useEffect(() => {
    const search = async () => {
      const data = await vectorSearchService.searchAllContent(query)
      setResults(data.results)
    }
    search()
  }, [query])
  
  return (
    <div>
      {results.map(result => (
        <div key={result.id}>
          <h3>{result.title}</h3>
          <p>{result.content}</p>
          <span>Similarity: {result.similarity}</span>
        </div>
      ))}
    </div>
  )
}
```

### API Endpoint

```javascript
app.get('/api/search', async (req, res) => {
  const { query, type } = req.query
  
  let results
  switch (type) {
    case 'knowledge':
      results = await vectorSearchService.searchKnowledgeBase(query)
      break
    case 'research':
      results = await vectorSearchService.searchExpertResearch(query)
      break
    case 'all':
    default:
      results = await vectorSearchService.searchAllContent(query)
  }
  
  res.json(results)
})
```

## 🎉 Next Steps

1. **Deploy Edge Functions**: Set up embedding generation
2. **Add Real Data**: Populate with actual NFL data
3. **Implement Caching**: Add Redis for performance
4. **Create UI**: Build search interface
5. **Monitor Performance**: Track search metrics

Your Vector Search Service is now ready for advanced NFL prediction analysis! 🏈🔍
