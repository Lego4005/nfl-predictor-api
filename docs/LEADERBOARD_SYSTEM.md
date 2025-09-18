# NFL Predictor Leaderboard System

## Overview

The NFL Predictor Leaderboard System tracks user prediction accuracy and displays competitive rankings with real-time updates.

## Features

### 🏆 Core Functionality
- **User Ranking**: Displays top users by prediction accuracy
- **Win/Loss Records**: Shows detailed W-L statistics for each user
- **Current Streaks**: Tracks winning and losing streaks
- **Real-time Updates**: WebSocket integration for live leaderboard updates
- **Multiple Sorting**: Sort by accuracy, wins, streak, or total picks
- **Time Filtering**: Filter by week, month, season, or all-time

### 📊 Statistics Tracked
- **Accuracy Percentage**: Calculated as (correct picks / total picks) × 100
- **Total Picks**: Number of predictions made
- **Win/Loss Record**: Correct vs incorrect predictions
- **Current Streak**: Active winning or losing streak
- **Best Streak**: Highest winning streak achieved
- **Points**: Scoring system based on confidence and accuracy

## Technical Implementation

### Database Schema

#### user_picks Table
```sql
CREATE TABLE user_picks (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default_user',
    game_id TEXT NOT NULL,
    winner TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    result TEXT DEFAULT NULL,
    points INTEGER DEFAULT 0,
    UNIQUE(user_id, game_id)
);
```

#### games Table
```sql
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'scheduled',
    start_time TEXT,
    winner TEXT DEFAULT NULL,
    completed BOOLEAN DEFAULT FALSE,
    week INTEGER,
    season INTEGER DEFAULT 2025
);
```

#### user_stats Table (Cached Statistics)
```sql
CREATE TABLE user_stats (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    total_picks INTEGER DEFAULT 0,
    correct_picks INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

#### GET `/api/leaderboard`
**Parameters:**
- `timeFilter`: "week" | "month" | "season" | "all" (default: "season")
- `sortBy`: "accuracy" | "wins" | "streak" | "total_picks" (default: "accuracy")
- `limit`: Number of results (default: 50)

**Response:**
```json
{
  "success": true,
  "leaderboard": [
    {
      "user_id": "user1",
      "username": "GridironGuru",
      "total_picks": 40,
      "wins": 29,
      "accuracy": 72.5,
      "current_streak": 5,
      "best_streak": 8,
      "points": 145,
      "losses": 11,
      "rank": 1,
      "avatar": null
    }
  ],
  "filters": {
    "timeFilter": "season",
    "sortBy": "accuracy",
    "limit": 50
  },
  "timestamp": "2025-09-14T17:45:00"
}
```

#### POST `/api/leaderboard/update-stats`
**Parameters:**
- `user_id`: User identifier
- `username`: Display name (optional)

**Response:**
```json
{
  "success": true,
  "user_id": "user1",
  "stats": {
    "total_picks": 40,
    "correct_picks": 29,
    "accuracy": 72.5,
    "current_streak": 5,
    "best_streak": 8,
    "total_points": 145
  },
  "message": "User statistics updated successfully"
}
```

#### GET `/api/leaderboard/user/{user_id}`
Get individual user statistics and ranking.

### WebSocket Integration

#### WebSocket Endpoint: `/ws/leaderboard`

**Real-time Features:**
- Live leaderboard updates when user stats change
- Automatic reconnection on connection loss
- Ping/pong heartbeat for connection health
- Filter-specific updates

**Message Format:**
```json
{
  "type": "leaderboard_update",
  "leaderboard": [...],
  "timestamp": "2025-09-14T17:45:00"
}
```

## Frontend Components

### Leaderboard Component (`/src/components/Leaderboard.jsx`)

**Features:**
- Responsive table layout with user rankings
- Real-time updates via WebSocket
- Interactive filtering and sorting
- User avatars and rank icons
- Streak indicators with visual cues
- Loading states and error handling
- Sample data fallback for development

**UI Elements:**
- Trophy icons for top 3 positions
- Color-coded accuracy badges
- Flame icons for winning streaks
- Clean, modern design with animations
- Responsive grid for statistics overview

### Integration with Main Dashboard

The leaderboard is integrated as a tab in the main NFLDashboard component:

```jsx
<TabsList className="grid w-full grid-cols-8">
  <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
</TabsList>

<TabsContent value="leaderboard" className="space-y-6">
  <Leaderboard />
</TabsContent>
```

## Accuracy Calculation

### Algorithm
1. **Fetch User Picks**: Get all picks with game results
2. **Compare Predictions**: Match pick winner with actual game winner
3. **Calculate Metrics**:
   - Accuracy = (Correct Picks / Total Picks) × 100
   - Current Streak = Latest consecutive wins/losses
   - Best Streak = Highest consecutive wins achieved
   - Points = Sum of confidence-weighted correct picks

### Streak Logic
- **Winning Streak**: Consecutive correct predictions
- **Losing Streak**: Consecutive incorrect predictions (negative value)
- **Broken Streak**: Reset when prediction result changes

### Points System
- Base points for correct prediction
- Bonus multiplier based on confidence level
- Penalty for incorrect high-confidence picks

## Usage Examples

### Basic Implementation
```javascript
import Leaderboard from './components/Leaderboard';

function App() {
  return (
    <div>
      <Leaderboard />
    </div>
  );
}
```

### API Usage
```javascript
// Fetch leaderboard data
const response = await fetch('/api/leaderboard?sortBy=accuracy&timeFilter=season');
const data = await response.json();

// Update user stats
await fetch('/api/leaderboard/update-stats', {
  method: 'POST',
  body: JSON.stringify({ user_id: 'user123', username: 'PlayerOne' }),
  headers: { 'Content-Type': 'application/json' }
});
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8084/ws/leaderboard');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'leaderboard_update') {
    updateLeaderboardUI(data.leaderboard);
  }
};
```

## Testing

### Database Tests
The system includes comprehensive testing for:
- Database initialization and schema creation
- Sample data population
- Query operations and sorting
- Accuracy calculations
- WebSocket connectivity

### Test Execution
```bash
python3 tests/test_leaderboard.py
```

## Performance Considerations

### Caching Strategy
- User statistics cached in `user_stats` table
- Real-time updates only when necessary
- Efficient database queries with proper indexing

### Optimization Features
- Limited WebSocket connections
- Batched database operations
- Lazy loading for large leaderboards
- Connection pooling for high traffic

## Future Enhancements

### Planned Features
- **User Profiles**: Extended user information and avatars
- **Achievements**: Badges and milestones
- **Historical Charts**: Accuracy trends over time
- **Group Competitions**: Team-based leaderboards
- **Social Features**: Following users and sharing picks
- **Advanced Metrics**: Confidence-weighted accuracy, ROI tracking
- **Mobile Optimization**: Touch-friendly interface

### Integration Possibilities
- **Authentication**: User login and registration
- **Notifications**: Real-time alerts for rank changes
- **Export Features**: Leaderboard data export
- **Analytics**: Advanced statistics and reporting
- **Betting Integration**: ROI and profit tracking