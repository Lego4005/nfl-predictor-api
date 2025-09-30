# API Reference

<cite>
**Referenced Files in This Document**   
- [app.py](file://src/api/app.py)
- [performance_endpoints.py](file://src/api/performance_endpoints.py)
- [clean_predictions_endpoints.py](file://src/api/clean_predictions_endpoints.py)
- [real_data_endpoints.py](file://src/api/real_data_endpoints.py)
- [websocket_manager.py](file://src/websocket/websocket_manager.py)
- [websocket_events.py](file://src/websocket/websocket_events.py)
- [api.types.ts](file://src/types/api.types.ts)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [REST API Endpoints](#rest-api-endpoints)
3. [WebSocket API](#websocket-api)
4. [Request/Response Examples](#requestresponse-examples)
5. [Rate Limiting and Error Handling](#rate-limiting-and-error-handling)
6. [API Versioning](#api-versioning)
7. [Client Implementation Guidelines](#client-implementation-guidelines)
8. [Security Considerations](#security-considerations)
9. [Performance Optimization](#performance-optimization)

## Introduction
The NFL Predictor API provides comprehensive access to AI-driven football predictions, expert analysis, and real-time game data. The API is built on FastAPI and offers both RESTful and WebSocket interfaces for accessing prediction data, betting insights, and live game updates. The system supports high-performance batch processing, real-time updates, and detailed expert analysis with comprehensive data models.

**Section sources**
- [app.py](file://src/api/app.py#L1-L227)

## REST API Endpoints

### Real-Time Game Predictions
The API provides multiple endpoints for accessing game predictions with varying levels of optimization and detail.

#### Performance-Optimized Predictions
```mermaid
flowchart TD
A[Client Request] --> B{Endpoint Type}
B --> C[/api/v2/performance/predictions/batch]
B --> D[/api/v2/performance/predictions/game/{game_id}]
B --> E[/api/v2/performance/predictions/live]
C --> F[Batch Processing]
D --> G[Single Game]
E --> H[Live Games]
F --> I[Parallel Expert Processing]
G --> I
H --> I
I --> J[Redis Cache Check]
J --> K{Cache Hit?}
K --> |Yes| L[Return Cached Data]
K --> |No| M[Generate Predictions]
M --> N[Store in Cache]
N --> O[Return Response]
```

**Diagram sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)

**Section sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)

#### Clean Predictions Endpoints
The clean predictions endpoints provide access to verified database-stored predictions with proper expert integration.

```mermaid
classDiagram
class CleanPredictionsAPI {
+get_game_predictions(home_team, away_team)
+get_experts()
+health_check()
+test_prediction(home_team, away_team)
}
class DatabasePredictionService {
+generate_all_predictions_for_game(home_team, away_team, game_data)
+get_experts_from_database()
}
CleanPredictionsAPI --> DatabasePredictionService : "uses"
```

**Diagram sources**
- [clean_predictions_endpoints.py](file://src/api/clean_predictions_endpoints.py#L1-L186)

**Section sources**
- [clean_predictions_endpoints.py](file://src/api/clean_predictions_endpoints.py#L1-L186)

### Expert Analysis Endpoints
The API provides comprehensive access to expert analysis and deep dives into prediction methodologies.

```mermaid
sequenceDiagram
participant Client
participant API
participant ExpertService
participant Database
Client->>API : GET /api/expert-analysis/{expert_id}
API->>ExpertService : fetch_expert_profile(expert_id)
ExpertService->>Database : Query expert data
Database-->>ExpertService : Return expert profile
ExpertService->>ExpertService : Generate analysis report
ExpertService-->>API : Return analysis
API-->>Client : Return expert analysis
```

**Section sources**
- [expert_deep_dive_endpoints.py](file://src/api/expert_deep_dive_endpoints.py#L1-L100)

### Betting Insights Endpoints
The real data endpoints provide enhanced betting insights with market data integration.

```mermaid
classDiagram
class BettingInsightsAPI {
+get_enhanced_predictions(week, season)
+get_betting_odds(game_id)
+get_injury_impact_analysis(team)
+get_weather_impact_analysis()
}
class RealDataNFLPredictionService {
+get_enhanced_game_predictions(week, season)
+get_injury_impact_analysis(team)
+get_weather_impact_analysis()
}
class SportsDataIOConnector {
+get_betting_data(game_id)
+get_injuries(team)
+get_team_stats(team_id)
}
BettingInsightsAPI --> RealDataNFLPredictionService : "uses"
BettingInsightsAPI --> SportsDataIOConnector : "uses"
```

**Diagram sources**
- [real_data_endpoints.py](file://src/api/real_data_endpoints.py#L1-L468)

**Section sources**
- [real_data_endpoints.py](file://src/api/real_data_endpoints.py#L1-L468)

### Live Game Updates Endpoints
The API provides real-time access to live game data and updates.

```mermaid
flowchart LR
A[Client] --> B[/api/real-data/games/current]
A --> C[/api/real-data/predictions/live]
A --> D[/api/real-data/live]
B --> E[SportsDataIOConnector]
C --> F[RealDataNFLPredictionService]
D --> F
E --> G[SportsData.io API]
F --> E
G --> H[Real-time Data]
H --> I[Formatted Response]
I --> A
```

**Section sources**
- [real_data_endpoints.py](file://src/api/real_data_endpoints.py#L1-L468)

## WebSocket API

### Connection Handling
The WebSocket API provides real-time updates for game events, prediction changes, and system notifications.

```mermaid
sequenceDiagram
participant Client
participant WebSocketManager
participant ConnectionManager
Client->>WebSocketManager : Connect to wss : //api.nflpredictor.com/ws
WebSocketManager->>ConnectionManager : Create new connection
ConnectionManager-->>WebSocketManager : Connection ID
WebSocketManager-->>Client : Connection acknowledgment
Client->>WebSocketManager : Subscribe to channels
WebSocketManager->>ConnectionManager : Register subscriptions
loop Heartbeat
Client->>WebSocketManager : Heartbeat message
WebSocketManager-->>Client : Heartbeat response
end
```

**Diagram sources**
- [websocket_manager.py](file://src/websocket/websocket_manager.py#L1-L364)
- [websocket_events.py](file://src/websocket/websocket_events.py#L1-L120)

**Section sources**
- [websocket_manager.py](file://src/websocket/websocket_manager.py#L1-L364)
- [websocket_events.py](file://src/websocket/websocket_events.py#L1-L120)

### Message Formats
The WebSocket API uses standardized message formats for different event types.

```mermaid
classDiagram
class WebSocketMessage {
+event_type : WebSocketEventType
+data : Dict[str, Any]
+timestamp : datetime
+message_id : Optional[str]
+user_id : Optional[str]
+channel : Optional[str]
}
class GameUpdateMessage {
+game_id : str
+home_team : str
+away_team : str
+home_score : int
+away_score : int
+quarter : int
+time_remaining : str
+game_status : str
+updated_at : datetime
}
class PredictionUpdateMessage {
+game_id : str
+home_team : str
+away_team : str
+home_win_probability : float
+away_win_probability : float
+predicted_spread : float
+confidence_level : float
+model_version : str
+updated_at : datetime
}
class OddsUpdateMessage {
+game_id : str
+sportsbook : str
+home_team : str
+away_team : str
+spread : float
+moneyline_home : int
+moneyline_away : int
+over_under : float
+updated_at : datetime
}
WebSocketMessage <|-- GameUpdateMessage
WebSocketMessage <|-- PredictionUpdateMessage
WebSocketMessage <|-- OddsUpdateMessage
```

**Diagram sources**
- [websocket_events.py](file://src/websocket/websocket_events.py#L1-L120)

**Section sources**
- [websocket_events.py](file://src/websocket/websocket_events.py#L1-L120)

### Real-Time Interaction Patterns
The WebSocket API supports various subscription patterns for real-time data.

```mermaid
flowchart TD
A[Client] --> B[Connect to WebSocket]
B --> C{Subscribe to Channels}
C --> D[game_{game_id}]
C --> E[predictions_{game_id}]
C --> F[odds_{game_id}]
C --> G[games]
C --> H[predictions]
C --> I[odds]
D --> J[Receive Game Updates]
E --> K[Receive Prediction Updates]
F --> L[Receive Odds Updates]
G --> M[Receive All Game Updates]
H --> N[Receive All Prediction Updates]
I --> O[Receive All Odds Updates]
```

**Section sources**
- [websocket_manager.py](file://src/websocket/websocket_manager.py#L1-L364)

## Request/Response Examples

### REST API Example: Batch Predictions
```json
{
  "game_ids": ["KC-BAL", "BUF-MIA"],
  "include_experts": true,
  "include_ml": true,
  "expert_count": 15
}
```

Response:
```json
{
  "predictions": [
    {
      "game_id": "KC-BAL",
      "home_team": "KC",
      "away_team": "BAL",
      "home_win_probability": 0.67,
      "away_win_probability": 0.33,
      "predicted_spread": -3.5,
      "confidence_level": 0.85,
      "experts": [
        {
          "expert_id": "1",
          "name": "Statistical Analyst",
          "prediction": "KC",
          "confidence": 0.9
        }
      ]
    }
  ],
  "metadata": {
    "generated_at": "2025-09-16T09:30:34Z",
    "model_version": "2.1.0"
  },
  "performance_metrics": {
    "response_time_ms": 234,
    "total_predictions": 375,
    "cache_hit": true
  }
}
```

**Section sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)

### WebSocket Example: Game Update
```json
{
  "event_type": "game_update",
  "data": {
    "game_id": "KC-BAL",
    "home_team": "KC",
    "away_team": "BAL",
    "home_score": 14,
    "away_score": 7,
    "quarter": 2,
    "time_remaining": "7:32",
    "game_status": "in_progress",
    "updated_at": "2025-09-16T20:15:30Z"
  },
  "timestamp": "2025-09-16T20:15:30Z"
}
```

**Section sources**
- [websocket_events.py](file://src/websocket/websocket_events.py#L1-L120)

## Rate Limiting and Error Handling

### Rate Limiting Strategy
The API implements rate limiting to ensure fair usage and system stability.

```mermaid
flowchart LR
A[Client Request] --> B{Rate Limit Check}
B --> |Within Limits| C[Process Request]
B --> |Exceeded| D[Return 429 Error]
C --> E[Update Rate Counter]
D --> F[Retry-After Header]
F --> G[Client Waits]
G --> A
```

The rate limiting is implemented using Redis for distributed rate tracking across multiple instances.

**Section sources**
- [app.py](file://src/api/app.py#L1-L227)
- [middleware/rate_limiting.py](file://src/middleware/rate_limiting.py#L1-L50)

### Error Handling Codes
The API returns standardized error codes for different failure scenarios.

```mermaid
classDiagram
class APIResponse {
+data : T
+source : DataSource
+cached : boolean
+timestamp : string
+notifications : Notification[]
}
class Notification {
+type : 'error' | 'warning' | 'info' | 'success'
+message : string
+source : DataSource
+retryable : boolean
}
class ErrorContext {
+source : DataSource
+endpoint : string
+week : number
+retry_count : number
+timestamp : string
}
APIResponse --> Notification
Notification --> ErrorContext
```

**Diagram sources**
- [api.types.ts](file://src/types/api.types.ts#L1-L57)

**Section sources**
- [api.types.ts](file://src/types/api.types.ts#L1-L57)

## API Versioning
The API uses a versioning strategy with both URL-based and header-based versioning options.

```mermaid
flowchart LR
A[Client Request] --> B{Versioning Method}
B --> C[URL Path: /api/v2/...]
B --> D[Header: Accept: application/vnd.api.v2+json]
C --> E[Version 2 Router]
D --> E
E --> F[Process Request]
```

The current version is v2, with v1 endpoints maintained for backward compatibility. The versioning allows for gradual migration to new features and breaking changes.

**Section sources**
- [app.py](file://src/api/app.py#L1-L227)
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)

## Client Implementation Guidelines

### REST API Client (Python)
```python
import requests
import asyncio
import aiohttp

class NFLPredictorClient:
    def __init__(self, api_key: str, base_url: str = "https://api.nflpredictor.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_batch_predictions(self, game_ids: list, include_experts: bool = True):
        url = f"{self.base_url}/api/v2/performance/predictions/batch"
        payload = {
            "game_ids": game_ids,
            "include_experts": include_experts,
            "expert_count": 15
        }
        response = requests.get(url, headers=self.headers, params=payload)
        return response.json()
    
    async def get_batch_predictions_async(self, game_ids: list):
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v2/performance/predictions/batch"
            params = {
                "game_ids": ",".join(game_ids),
                "include_experts": "true"
            }
            async with session.get(url, headers=self.headers, params=params) as response:
                return await response.json()
```

**Section sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)

### REST API Client (JavaScript)
```javascript
class NFLPredictorClient {
    constructor(apiKey, baseUrl = 'https://api.nflpredictor.com') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async getBatchPredictions(gameIds, includeExperts = true) {
        const params = new URLSearchParams({
            game_ids: gameIds.join(','),
            include_experts: includeExperts.toString(),
            expert_count: 15
        });

        const response = await fetch(
            `${this.baseUrl}/api/v2/performance/predictions/batch?${params}`,
            { headers: this.headers }
        );

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async getLivePredictions() {
        const response = await fetch(
            `${this.baseUrl}/api/v2/performance/predictions/live?week=2`,
            { headers: this.headers }
        );

        return await response.json();
    }
}
```

**Section sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)

### WebSocket Client (JavaScript)
```javascript
class NFLPredictorWebSocket {
    constructor(apiKey, url = 'wss://api.nflpredictor.com/ws') {
        this.apiKey = apiKey;
        this.url = url;
        this.socket = null;
        this.listeners = new Map();
    }

    async connect() {
        this.socket = new WebSocket(`${this.url}?api_key=${this.apiKey}`);

        this.socket.onopen = () => {
            console.log('Connected to NFL Predictor WebSocket');
            this._sendHeartbeat();
        };

        this.socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this._dispatchEvent(message);
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected', event);
            this._reconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    subscribe(channel) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                event_type: 'user_subscription',
                data: { channel }
            }));
        }
    }

    unsubscribe(channel) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                event_type: 'user_unsubscription',
                data: { channel }
            }));
        }
    }

    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, new Set());
        }
        this.listeners.get(eventType).add(callback);
    }

    off(eventType, callback) {
        if (this.listeners.has(eventType)) {
            this.listeners.get(eventType).delete(callback);
        }
    }

    _sendHeartbeat() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                event_type: 'heartbeat',
                data: { client_time: new Date().toISOString() }
            }));
            setTimeout(() => this._sendHeartbeat(), 30000); // Every 30 seconds
        }
    }

    _dispatchEvent(message) {
        const listeners = this.listeners.get(message.event_type) || new Set();
        for (const listener of listeners) {
            listener(message);
        }
    }

    _reconnect() {
        setTimeout(() => {
            this.connect();
        }, 5000);
    }
}
```

**Section sources**
- [websocket_manager.py](file://src/websocket/websocket_manager.py#L1-L364)
- [websocket_events.py](file://src/websocket/websocket_events.py#L1-L120)

## Security Considerations

### API Key Management
The API uses bearer token authentication with API keys for access control.

```mermaid
sequenceDiagram
participant Client
participant API
participant AuthService
Client->>API : Request with Authorization : Bearer <api_key>
API->>AuthService : Validate API key
AuthService->>AuthService : Check key validity and permissions
AuthService-->>API : Return validation result
alt Valid Key
API-->>Client : Process request
else Invalid Key
API-->>Client : 401 Unauthorized
end
```

API keys should be stored securely and never exposed in client-side code or public repositories. The system supports key rotation and revocation through the configuration system.

**Section sources**
- [app.py](file://src/api/app.py#L1-L227)
- [config/key_rotation.py](file://config/key_rotation.py#L1-L30)

### Data Privacy
The API implements data privacy measures to protect user information and prediction data.

```mermaid
flowchart LR
A[Client Data] --> B[Encryption in Transit]
B --> C[Secure Storage]
C --> D[Access Control]
D --> E[Audit Logging]
E --> F[Data Retention Policy]
```

All data is transmitted over HTTPS with TLS 1.3 encryption. Sensitive data is encrypted at rest using AES-256. Access to data is controlled through role-based access control (RBAC) with detailed audit logging.

**Section sources**
- [app.py](file://src/api/app.py#L1-L227)
- [middleware/rate_limiting.py](file://src/middleware/rate_limiting.py#L1-L50)

## Performance Optimization

### High-Frequency API Consumer Tips
For clients making high-frequency API calls, the following optimization strategies are recommended:

```mermaid
flowchart TD
A[High-Frequency Client] --> B[Use Batch Endpoints]
A --> C[Implement Local Caching]
A --> D[Use WebSocket for Real-Time Data]
A --> E[Optimize Request Frequency]
A --> F[Use Compression]
B --> G[Reduce Number of Requests]
C --> H[Reduce API Calls]
D --> I[Eliminate Polling]
E --> J[Avoid Rate Limiting]
F --> K[Reduce Bandwidth]
G --> L[Improved Performance]
H --> L
I --> L
J --> L
K --> L
```

**Section sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)
- [websocket_manager.py](file://src/websocket/websocket_manager.py#L1-L364)

### Caching Strategies
The API implements a multi-layer caching strategy to optimize performance.

```mermaid
flowchart LR
A[Client Request] --> B{Cache Layer}
B --> C[CDN Cache]
B --> D[API Gateway Cache]
B --> E[Redis Cache]
B --> F[Database Cache]
C --> |Hit| G[Return Response]
D --> |Hit| G
E --> |Hit| G
F --> |Hit| G
C --> |Miss| D
D --> |Miss| E
E --> |Miss| F
F --> |Miss| H[Generate Response]
H --> I[Store in Caches]
I --> G
```

Clients can leverage the caching system by paying attention to the `cached` flag in responses and implementing appropriate cache invalidation strategies based on the `timestamp` field.

**Section sources**
- [performance_endpoints.py](file://src/api/performance_endpoints.py#L1-L539)
- [websocket_manager.py](file://src/websocket/websocket_manager.py#L1-L364)