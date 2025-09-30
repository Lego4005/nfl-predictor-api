# Betting Engine

<cite>
**Referenced Files in This Document**   
- [betting_engine.py](file://src/analytics/betting_engine.py)
- [odds_api_client.py](file://src/api/odds_api_client.py)
- [api_endpoints.py](file://src/analytics/api_endpoints.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Core Algorithms](#core-algorithms)
3. [Value Bet Identification](#value-bet-identification)
4. [Risk Assessment and Expected Value](#risk-assessment-and-expected-value)
5. [Confidence-Based Wager Sizing](#confidence-based-wager-sizing)
6. [Integration with Odds API Client](#integration-with-odds-api-client)
7. [Configuration Options](#configuration-options)
8. [False Positive and Overfitting Indicators](#false-positive-and-overfitting-indicators)
9. [Troubleshooting Guide](#troubleshooting-guide)

## Introduction

The Betting Analytics Engine is a sophisticated system designed to identify profitable betting opportunities by comparing model-generated predictions against market odds. The engine analyzes prediction data across multiple dimensions including spreads, totals, and moneyline probabilities to detect value bets, arbitrage opportunities, and line movement patterns. It integrates with the Odds API client to retrieve real-time market data and applies advanced algorithms for risk assessment, expected value calculation, and confidence-based wager sizing. The system provides comprehensive bankroll management recommendations and supports various stake sizing strategies based on risk tolerance levels.

**Section sources**
- [betting_engine.py](file://src/analytics/betting_engine.py#L1-L50)

## Core Algorithms

The Betting Analytics Engine employs several key algorithms to identify value betting opportunities and assess risk. The primary algorithm is the Kelly Criterion, which calculates the optimal fraction of bankroll to wager based on the edge between true probability and implied probability from market odds. The engine also implements expected value calculation to quantify the profitability of potential bets. For arbitrage detection, the system analyzes odds across multiple sportsbooks to identify guaranteed profit opportunities. Line movement analysis tracks how betting lines change over time, detecting patterns that indicate sharp money or steam moves. The engine uses Redis for caching to improve performance and reduce API calls.

```mermaid
classDiagram
class BettingAnalyticsEngine {
+redis_client Redis
+cache_ttl int
+min_kelly_threshold float
+max_kelly_fraction float
+min_arbitrage_profit float
+executor ThreadPoolExecutor
+identify_value_bets(game_id, true_probabilities, odds_data, bankroll) ValueBet[]
+detect_arbitrage_opportunities(game_id, odds_matrix) ArbitrageOpportunity[]
+analyze_line_movement(game_id, historical_odds) LineMovement[]
+recommend_bankroll_management(bankroll, risk_tolerance, betting_history) Dict
+assess_parlay_risk(legs, correlation_matrix) Dict
}
class ValueBet {
+game_id str
+bet_type BetType
+selection str
+true_probability float
+implied_probability float
+odds float
+kelly_fraction float
+expected_value float
+confidence float
+risk_level RiskLevel
+recommended_stake float
+max_stake float
+sportsbook str
}
class ArbitrageOpportunity {
+game_id str
+bet_type BetType
+selections str[]
+odds float[]
+sportsbooks str[]
+profit_margin float
+total_stake float
+stakes float[]
+guaranteed_profit float
+risk_level RiskLevel
}
class LineMovement {
+game_id str
+bet_type BetType
+selection str
+opening_line float
+current_line float
+movement float
+movement_percentage float
+sharp_money_indicator bool
+public_percentage Optional~float~
+money_percentage Optional~float~
+reverse_line_movement bool
+steam_move bool
}
class OddsData {
+sportsbook str
+odds float
+line Optional~float~
+timestamp datetime
+volume Optional~float~
}
class BetType {
+MONEYLINE
+SPREAD
+TOTAL
+PROP
+PARLAY
+TEASER
}
class RiskLevel {
+LOW
+MEDIUM
+HIGH
+EXTREME
}
BettingAnalyticsEngine --> ValueBet : "creates"
BettingAnalyticsEngine --> ArbitrageOpportunity : "creates"
BettingAnalyticsEngine --> LineMovement : "creates"
BettingAnalyticsEngine --> OddsData : "uses"
BettingAnalyticsEngine --> BetType : "references"
BettingAnalyticsEngine --> RiskLevel : "references"
```

**Diagram sources **
- [betting_engine.py](file://src/analytics/betting_engine.py#L105-L1046)

## Value Bet Identification

The engine identifies value betting opportunities by comparing model-generated true probabilities against market-implied probabilities derived from sportsbook odds. The process begins with the `identify_value_bets` method, which takes game identifiers, true probabilities from prediction models, and odds data from multiple sportsbooks. The engine converts American odds to decimal format and calculates implied probabilities. It then applies the Kelly Criterion to determine the optimal bet size when the true probability exceeds the implied probability. The system filters out opportunities below the minimum Kelly threshold (0.01) and sorts results by expected value. Value bets are cached in Redis to avoid redundant calculations and improve response times.

**Section sources**
- [betting_engine.py](file://src/analytics/betting_engine.py#L179-L259)

## Risk Assessment and Expected Value

Risk assessment in the Betting Analytics Engine is multi-faceted, incorporating Kelly Criterion fractions, expected value calculations, and confidence metrics. The `calculate_expected_value` method computes the mathematical expectation of a bet by considering both potential winnings and losses weighted by their respective probabilities. The engine categorizes risk levels based on Kelly fractions: LOW (below 0.05), MEDIUM (0.05-0.10), HIGH (0.10-0.20), and EXTREME (above 0.20). The system also implements safety caps, ensuring recommended stakes never exceed 5% of the bankroll regardless of Kelly calculations. For parlays and teasers, the engine assesses risk by considering leg correlations and calculates adjusted probabilities accordingly.

```mermaid
flowchart TD
Start([Start Risk Assessment]) --> ConvertOdds["Convert American Odds to Decimal"]
ConvertOdds --> CalculateImplied["Calculate Implied Probability"]
CalculateImplied --> CalculateEV["Calculate Expected Value"]
CalculateEV --> CalculateKelly["Calculate Kelly Fraction"]
CalculateKelly --> CheckThreshold["Kelly ≥ min_kelly_threshold?"]
CheckThreshold --> |No| Reject["Reject Bet"]
CheckThreshold --> |Yes| DetermineRisk["Determine Risk Level"]
DetermineRisk --> LowRisk{"Kelly < 0.05?"}
LowRisk --> |Yes| RiskLevelLow["Risk Level: LOW"]
LowRisk --> |No| MediumRisk{"Kelly < 0.10?"}
MediumRisk --> |Yes| RiskLevelMedium["Risk Level: MEDIUM"]
MediumRisk --> |No| HighRisk{"Kelly < 0.20?"}
HighRisk --> |Yes| RiskLevelHigh["Risk Level: HIGH"]
HighRisk --> |No| RiskLevelExtreme["Risk Level: EXTREME"]
RiskLevelLow --> CalculateStake["Calculate Recommended Stake"]
RiskLevelMedium --> CalculateStake
RiskLevelHigh --> CalculateStake
RiskLevelExtreme --> CalculateStake
CalculateStake --> ApplyCap["Apply 5% Bankroll Cap"]
ApplyCap --> Output["Output Value Bet"]
Reject --> Output
Output --> End([End])
```

**Diagram sources **
- [betting_engine.py](file://src/analytics/betting_engine.py#L148-L177)
- [betting_engine.py](file://src/analytics/betting_engine.py#L211-L236)

## Confidence-Based Wager Sizing

The engine implements confidence-based wager sizing through a combination of the Kelly Criterion and risk tolerance adjustments. The `recommend_bankroll_management` method provides personalized recommendations based on user-defined risk tolerance (conservative, medium, aggressive). For conservative profiles, the system applies a 0.25 Kelly multiplier with a maximum bet percentage of 2%, while aggressive profiles use a 0.75 multiplier with up to 5% of bankroll per bet. The engine dynamically adjusts these parameters based on historical performance, increasing bet sizes for consistently profitable strategies and reducing them during losing periods. The system also considers daily risk limits and stop-loss thresholds to prevent catastrophic losses.

**Section sources**
- [betting_engine.py](file://src/analytics/betting_engine.py#L680-L759)

## Integration with Odds API Client

The Betting Analytics Engine integrates with the Odds API Client to retrieve real-time market odds for NFL games. The `OddsAPIClient` fetches data from The Odds API, parsing responses to extract spreads, totals, and moneylines from multiple sportsbooks. The client handles authentication, response validation, and team name standardization, converting full team names to standard abbreviations. It implements caching through the client manager to minimize API calls and rate limit usage. The betting engine uses this data to compare model predictions against market odds, flagging discrepancies that indicate value opportunities. The integration supports fetching odds for specific weeks and filtering by market type (spreads, totals, or moneylines).

```mermaid
sequenceDiagram
participant Engine as BettingAnalyticsEngine
participant Client as OddsAPIClient
participant Manager as APIClientManager
participant API as The Odds API
Engine->>Client : fetch_games_odds(week=2)
Client->>Client : _get_week_date_range(week=2)
Client->>Manager : fetch_with_cache(source=ODDS_API, endpoint="/sports/americanfootball_nfl/odds", params)
Manager->>API : HTTP GET with API key
API-->>Manager : Return odds data
Manager-->>Client : Return cached response
Client->>Client : _validate_response(data)
Client->>Client : _extract_odds_data(game_data)
Client-->>Engine : Return structured GameOdds
Engine->>Engine : identify_value_bets() with model probabilities
Engine-->>User : Return ValueBet recommendations
```

**Diagram sources **
- [odds_api_client.py](file://src/api/odds_api_client.py#L225-L279)
- [betting_engine.py](file://src/analytics/betting_engine.py#L179-L259)

## Configuration Options

The Betting Analytics Engine provides several configurable parameters to customize its behavior according to user preferences and risk profiles. Key configuration options include `min_kelly_threshold` (default 0.01), which sets the minimum Kelly fraction required to consider a bet; `max_kelly_fraction` (default 0.25), which caps the maximum recommended bet size; and `min_arbitrage_profit` (default 0.01), which defines the minimum profit margin for arbitrage opportunities. The engine also supports risk tolerance levels (conservative, medium, aggressive) that adjust Kelly multipliers and maximum bet percentages. Bankroll management configurations include daily risk limits, stop-loss thresholds, and rebalancing rules based on profit or loss percentages