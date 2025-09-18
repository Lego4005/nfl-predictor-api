# NFL Predictor WebSocket Server

## Overview

The NFL Predictor WebSocket server provides real-time updates for live games, predictions, and odds data. It integrates with Supabase realtime to automatically broadcast database changes to connected clients.

## Features

- **Real-time Game Updates**: Live scores, quarter changes, game status
- **Prediction Updates**: AI model predictions with confidence levels
- **Odds Updates**: Sportsbook odds and line movements
- **Channel Subscriptions**: Targeted updates for specific games or data types
- **Connection Management**: Automatic heartbeat, reconnection, and cleanup
- **Supabase Integration**: Direct connection to database changes

## Quick Start

### 1. Install Dependencies

```bash
npm install ws @types/ws concurrently
```

### 2. Environment Setup

Ensure your `.env` file contains Supabase credentials:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
WS_PORT=8080  # Optional, defaults to 8080
```

### 3. Start WebSocket Server

```bash
# Start WebSocket server only
npm run ws-server

# Start WebSocket server with auto-restart (development)
npm run ws-dev

# Start both frontend and WebSocket server
npm run dev-full

# Use convenience script
./scripts/start-dev.sh
```

### 4. Test Connection

```bash
# Test WebSocket connectivity
node scripts/test-websocket.js
```

## Server Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_PORT` | 8080 | WebSocket server port |
| `VITE_SUPABASE_URL` | Required | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Required | Supabase anonymous key |

### Server Settings

- **Port**: 8080 (configurable via `WS_PORT`)
- **Heartbeat Interval**: 30 seconds
- **Connection Timeout**: 60 seconds (2 missed heartbeats)
- **Max Connections**: Unlimited (OS limited)

## WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8080?user_id=123&token=abc');
```

### Message Format

All messages follow this JSON structure:

```json
{
  "event_type": "game_update",
  "data": { /* event-specific data */ },
  "timestamp": "2024-09-14T21:38:29.128Z",
  "message_id": "msg_1726347509128_xyz123",
  "channel": "games",
  "user_id": "optional_user_id"
}
```

## Event Types

### Game Events

- `game_started` - New game begins
- `game_ended` - Game completed
- `game_update` - General game information change
- `score_update` - Score change detected
- `quarter_change` - Quarter/period change

### Prediction Events

- `prediction_update` - AI prediction updated
- `prediction_refresh` - Model recalculated
- `model_update` - New model version deployed

### Odds Events

- `odds_update` - Sportsbook odds changed
- `line_movement` - Significant spread/line movement

### System Events

- `connection_ack` - Connection established
- `heartbeat` - Keep-alive ping/pong
- `error` - Error occurred
- `notification` - System notification

### User Events

- `user_subscription` - Subscribe to channel
- `user_unsubscription` - Unsubscribe from channel

## Channel Subscriptions

### Available Channels

| Channel | Description | Example Events |
|---------|-------------|----------------|
| `games` | All game updates | score_update, game_ended |
| `game_{id}` | Specific game | game_401547439 updates |
| `predictions` | All predictions | prediction_update |
| `predictions_{id}` | Game predictions | predictions_401547439 |
| `odds` | All odds changes | odds_update, line_movement |
| `odds_{id}` | Game-specific odds | odds_401547439 |

### Subscription Example

```javascript
// Subscribe to all games
ws.send(JSON.stringify({
  event_type: 'user_subscription',
  data: { channel: 'games' },
  timestamp: new Date().toISOString()
}));

// Subscribe to specific game
ws.send(JSON.stringify({
  event_type: 'user_subscription',
  data: { channel: 'game_401547439' },
  timestamp: new Date().toISOString()
}));
```

## Data Structures

### Game Update

```json
{
  "game_id": "nfl_2024_week_1_chiefs_ravens",
  "home_team": "Kansas City Chiefs",
  "away_team": "Baltimore Ravens",
  "home_score": 14,
  "away_score": 7,
  "quarter": 2,
  "time_remaining": "8:45",
  "game_status": "in_progress",
  "updated_at": "2024-09-14T21:38:29.128Z"
}
```

### Prediction Update

```json
{
  "game_id": "nfl_2024_week_1_chiefs_ravens",
  "home_team": "Kansas City Chiefs",
  "away_team": "Baltimore Ravens",
  "home_win_probability": 0.65,
  "away_win_probability": 0.35,
  "predicted_spread": -3.5,
  "confidence_level": 0.82,
  "model_version": "v2.1.0",
  "updated_at": "2024-09-14T21:38:29.128Z"
}
```

### Odds Update

```json
{
  "game_id": "nfl_2024_week_1_chiefs_ravens",
  "sportsbook": "DraftKings",
  "home_team": "Kansas City Chiefs",
  "away_team": "Baltimore Ravens",
  "spread": -3.5,
  "moneyline_home": -165,
  "moneyline_away": 140,
  "over_under": 48.5,
  "updated_at": "2024-09-14T21:38:29.128Z"
}
```

## Supabase Integration

The server automatically subscribes to database changes:

### Tables Monitored

- `games` - Game information and scores
- `predictions` - AI predictions and model outputs
- `odds` - Sportsbook odds and lines

### Realtime Triggers

Database changes trigger immediate WebSocket broadcasts:

1. **INSERT** on `games` → `game_started` event
2. **UPDATE** on `games` with score change → `score_update` event
3. **UPDATE** on `games` with status=FINAL → `game_ended` event
4. **UPDATE** on `predictions` → `prediction_update` event
5. **UPDATE** on `odds` → `odds_update` event

## Client Integration

### React Hook Usage

```javascript
import { useWebSocket, WebSocketEventType } from '../services/websocketService';

function GameComponent({ gameId }) {
  const { isConnected, subscribe, on, off } = useWebSocket({ autoConnect: true });

  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to game updates
    subscribe(`game_${gameId}`);

    // Handle score updates
    const handleScoreUpdate = (data) => {
      console.log('Score update:', data);
      // Update your component state
    };

    on(WebSocketEventType.SCORE_UPDATE, handleScoreUpdate);

    return () => {
      off(WebSocketEventType.SCORE_UPDATE, handleScoreUpdate);
    };
  }, [isConnected, gameId]);

  return (
    <div>
      {isConnected ? '🟢 Live' : '🔴 Disconnected'}
    </div>
  );
}
```

### Manual Connection

```javascript
import { websocketService, WebSocketEventType } from '../services/websocketService';

// Connect manually
await websocketService.connect();

// Subscribe to channels
websocketService.subscribeToChannel('games');

// Listen for events
websocketService.on(WebSocketEventType.SCORE_UPDATE, (data) => {
  console.log('Score update:', data);
});

// Send custom message
websocketService.send(WebSocketEventType.USER_SUBSCRIPTION, {
  channel: 'predictions'
});
```

## Monitoring & Debugging

### Server Logs

The server provides detailed logging:

```bash
[2024-09-14T21:38:29.128Z] New WebSocket connection: client_123 (User: test_user)
[2024-09-14T21:38:30.150Z] Client client_123 subscribed to channel: games
[2024-09-14T21:38:31.200Z] Game update received: UPDATE game_123
[2024-09-14T21:38:31.201Z] Broadcasting to channel games (5 subscribers)
```

### Connection Status

Get server status programmatically:

```javascript
// In your WebSocket server code
const status = server.getStatus();
console.log(status);
// {
//   port: 8080,
//   connectedClients: 5,
//   activeChannels: 3,
//   supabaseSubscriptions: 3,
//   uptime: 3600,
//   startTime: "2024-09-14T21:38:29.128Z"
// }
```

### Testing Connection

Use the provided test script:

```bash
node scripts/test-websocket.js
```

Expected output:
```
🔧 NFL Predictor WebSocket Connection Test
📡 Connecting to: ws://localhost:8080

✅ Connection established
📩 Received: connection_ack
   ✅ Connection ID: client_1726347509128_xyz123
   ⏱️  Heartbeat interval: 30s
   🎯 Supported events: 11

📊 Test Results:
================
Connection Acknowledgment: ✅ PASS
Heartbeat Response: ✅ PASS
Overall Result: ✅ PASS
🎉 WebSocket server is working correctly!
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill existing process
   lsof -ti:8080 | xargs kill -9
   # Or change port
   export WS_PORT=8081
   ```

2. **Supabase Connection Failed**
   - Verify `.env` file has correct Supabase credentials
   - Check Supabase project status
   - Ensure realtime is enabled in Supabase dashboard

3. **Frontend Can't Connect**
   - Verify WebSocket URL in `websocketService.ts`
   - Check browser console for CORS errors
   - Ensure both frontend and WebSocket server are running

4. **No Database Updates**
   - Verify Supabase realtime subscriptions are active
   - Check database table names match server configuration
   - Ensure database changes are actually occurring

### Debug Mode

Enable verbose logging:

```bash
DEBUG=ws* npm run ws-server
```

### Health Check

The server automatically logs connection statistics every 30 seconds:

```
[2024-09-14T21:38:59.128Z] Active connections: 3, Active channels: 5
```

## Production Deployment

### Environment Setup

```env
NODE_ENV=production
WS_PORT=8080
VITE_SUPABASE_URL=your_production_supabase_url
VITE_SUPABASE_ANON_KEY=your_production_key
```

### Process Management

Use PM2 for production deployment:

```bash
# Install PM2
npm install -g pm2

# Start WebSocket server
pm2 start src/websocket/websocketServer.js --name nfl-websocket

# Monitor
pm2 monit

# Logs
pm2 logs nfl-websocket
```

### Scaling Considerations

- Use Redis for multi-instance message broadcasting
- Implement connection limits and rate limiting
- Add authentication middleware for production
- Monitor memory usage with many concurrent connections
- Consider using clusters for CPU-bound operations

## API Reference

### WebSocket Server Class

```javascript
import NFLWebSocketServer from './src/websocket/websocketServer.js';

const server = new NFLWebSocketServer();
server.start();

// Get status
const status = server.getStatus();

// Graceful shutdown
server.shutdown();
```

### Events API

All events follow the same pattern:

```javascript
{
  event_type: string,
  data: object,
  timestamp: string,
  message_id?: string,
  user_id?: string,
  channel?: string
}
```

For detailed event schemas, see the TypeScript definitions in `websocketService.ts`.