
# SportsData.io Integration

<cite>
**Referenced Files in This Document**   
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py)
- [client_manager.py](file://src/api/client_manager.py)
- [cache_manager.py](file://src/cache/cache_manager.py)
- [fantasy_optimizer.py](file://src/ml/fantasy_optimizer.py)
- [player_props_engine.py](file://src/ml/player_props_engine.py)
- [prediction_api.py](file://src/ml/prediction_api.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [SportsDataIOClient Overview](#sportsdataioclient-overview)
3. [Player Prop Data Processing](#player-prop-data-processing)
4. [Fantasy Data Extraction and Optimization](#fantasy-data-extraction-and-optimization)
5. [Data Validation and Quality Assurance](#data-validation-and-quality-assurance)
6. [Rate Limit Management and Error Recovery](#rate-limit-management-and-error-recovery)
7. [Caching Strategy](#caching-strategy)
8. [Integration with Prediction Models](#integration-with-prediction-models)
9. [Conclusion](#conclusion)

## Introduction
The SportsData.io integration provides a comprehensive solution for accessing player prop bets, DFS salaries, and fantasy projections for NFL games. This documentation details the architecture and implementation of the SportsDataIOClient, which serves as the primary interface for retrieving and processing sports data. The system is designed to support fantasy optimization, expert predictions, and machine learning model training through robust data extraction, validation, and caching mechanisms.

**Section sources**
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py#L1-L50)

## SportsDataIOClient Overview
The SportsDataIOClient class serves as the primary interface for interacting with the SportsData.io API. It provides methods for fetching player props, DFS salaries, and player statistics for NFL games. The client is initialized with an APIClientManager that handles HTTP requests, rate limiting, and error recovery.

The client supports multiple data types through dedicated methods:
- `fetch_player_props()`: Retrieves player prop bets including passing yards, rushing yards, receptions, and touchdowns
- `fetch_dfs_salaries()`: Obtains DFS salary and projection data from DraftKings and FanDuel
- `fetch_player_stats()`: Fetches historical player statistics used for prediction modeling

The client uses a standardized API response format and includes comprehensive error handling for network issues, rate limiting, and data validation failures.

```mermaid
classDiagram
class SportsDataIOClient {
+fetch_player_props(week : int, year : int) APIResponse
+fetch_dfs_salaries(week : int, year : int) APIResponse
+fetch_player_stats(week : int, year : int) APIResponse
-_extract_prop_data(prop_data : Dict) PropBet
-_extract_fantasy_data(player_data : Dict) FantasyPlayer
-_validate_props_response(data : Any) bool
-_validate_fantasy_response(data : Any) bool
}
class PropBet {
+player : str
+prop_type : PropType
+units : str
+line : float
+pick : str
+confidence : float
+bookmaker : str
+team : str
+opponent : str
+game_date : datetime
+market_id : str
}
class FantasyPlayer {
+player : str
+position : Position
+team : str
+salary : int
+projected_points : float
+value_score : float
+opponent : str
+game_date : datetime
+injury_status : str
}
class PropType {
PASSING_YARDS
RUSHING_YARDS
RECEIVING_YARDS
RECEPTIONS
TOUCHDOWNS
FANTASY_POINTS
}
class Position {
QB
RB
WR
TE
K
DST
}
SportsDataIOClient --> PropBet : "creates"
SportsDataIOClient --> FantasyPlayer : "creates"
SportsDataIOClient --> PropType : "uses"
SportsDataIOClient --> Position : "uses"
```

**Diagram sources **
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py#L66-L429)

**Section sources**
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py#L66-L429)

## Player Prop Data Processing
The SportsDataIOClient extracts player prop bet data from the SportsData.io API and transforms it into structured PropBet objects. The data extraction process begins with a call to the PlayerPropsByWeek endpoint, which returns raw prop data for all players in a given week.

The `_extract_prop_data()` method parses the API response and creates PropBet objects with the following fields:
- Player name and team information
- Prop type (passing yards, rushing yards, receptions, touchdowns)
- Betting line and over/under pick
- Confidence score based on line movement analysis
- Bookmaker information and game date

The system determines the prop type by analyzing the market name in the API response. For example, "Passing Yards" markets are identified by checking for "passing" and "yard" in the market name. The confidence score is calculated using a base confidence of 0.55 with an additional factor based on the absolute value of the betting line (higher lines receive higher confidence).

```mermaid
flowchart TD
A[API Request to PlayerPropsByWeek] --> B{Response Valid?}
B --> |Yes| C[Parse Individual Prop Data]
B --> |No| D[Throw Validation Error]
C --> E[Extract Player Information]
E --> F[Determine Prop Type from Market Name]
F --> G[Calculate Confidence Score]
G --> H[Create PropBet Object]
H --> I[Add to Results Array]
I --> J{More Props?}
J --> |Yes| C
J --> |No| K[Sort by Confidence]
K --> L[Return Structured Response]
```

**Diagram sources **
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py#L166-L205)

**Section sources**
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py#L166-L205)

## Fantasy Data Extraction and Optimization
The SportsDataIOClient retrieves DFS salary and projection data through the DfsSlatesByWeek endpoint. This data is processed by the `_extract_fantasy_data()` method, which creates structured FantasyPlayer objects containing salary information, projected points, and value metrics.

The fantasy optimization engine uses this data to construct optimal DFS lineups. The FantasyOptimizer class implements advanced algorithms for lineup construction, including:
- Linear programming optimization for maximum projected points within salary constraints
- Greedy optimization as a fallback when advanced libraries are unavailable
- Multiple lineup generation with different strategies (cash, GPP, contrarian)

The optimizer considers various factors when constructing lineups:
- Salary cap constraints ($50,000 for DraftKings)
- Roster requirements (1 QB, 2-3 RB, 3-4 WR, 1-2 TE, 1 FLEX, 1 DST)
- Player correlations and stacking opportunities
- Ownership percentages for leverage plays
- Weather and game environment factors

```mermaid
sequenceDiagram
participant Client as "Client App"
participant SportsDataIO as "SportsDataIOClient"
participant Optimizer as "FantasyOptimizer"
participant Response as "API Response"
Client->>SportsDataIO : fetch_dfs_salaries(week=2)
SportsDataIO->>SportsDataIO : fetch_with_cache()
SportsDataIO->>SportsDataIO : validate_fantasy_response()
SportsDataIO->>SportsDataIO : extract_fantasy_data()
SportsDataIO->>Optimizer : optimize_lineup(player_pool)
Optimizer->>Optimizer : calculate_correlations()
Optimizer->>Optimizer : apply_strategy_adjustments()
Optimizer->>Optimizer : linear_programming_optimization()
Optimizer-->>SportsDataIO : optimized_lineup
SportsDataIO-->>Client : APIResponse with structured data
```

**Diagram sources **
- [sportsdata_io_client.py](file://src/api/sportsdata_io_client.py#L248-L290)
- [fantasy_optimizer.py](file://src/ml/fantasy_optimizer.py#L23-L600)

**Section sources**
- [sportsdata_io_client.py](file://src