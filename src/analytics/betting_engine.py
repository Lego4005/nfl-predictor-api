"""
Comprehensive Betting Analytics Engine for NFL Predictions

This module provides advanced betting analytics including:
- Value bet identification using Kelly Criterion
- Arbitrage opportunity detection
- Line movement analysis and sharp money tracking
- Public betting vs money percentage analysis
- Historical ROI tracking
- Bankroll management recommendations
- Risk assessment for parlays and teasers
- Live betting opportunity alerts
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import redis
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BetType(Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PROP = "prop"
    PARLAY = "parlay"
    TEASER = "teaser"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class OddsData:
    """Represents odds data from a sportsbook"""
    sportsbook: str
    odds: float
    line: Optional[float] = None
    timestamp: datetime = None
    volume: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ValueBet:
    """Represents a value betting opportunity"""
    game_id: str
    bet_type: BetType
    selection: str
    true_probability: float
    implied_probability: float
    odds: float
    kelly_fraction: float
    expected_value: float
    confidence: float
    risk_level: RiskLevel
    recommended_stake: float
    max_stake: float
    sportsbook: str

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage betting opportunity"""
    game_id: str
    bet_type: BetType
    selections: List[str]
    odds: List[float]
    sportsbooks: List[str]
    profit_margin: float
    total_stake: float
    stakes: List[float]
    guaranteed_profit: float
    risk_level: RiskLevel

@dataclass
class LineMovement:
    """Tracks line movement data"""
    game_id: str
    bet_type: BetType
    selection: str
    opening_line: float
    current_line: float
    movement: float
    movement_percentage: float
    sharp_money_indicator: bool
    public_percentage: Optional[float]
    money_percentage: Optional[float]
    reverse_line_movement: bool
    steam_move: bool

class BettingAnalyticsEngine:
    """Main betting analytics engine"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.cache_ttl = 300  # 5 minutes
        self.min_kelly_threshold = 0.01  # Minimum Kelly fraction to consider
        self.max_kelly_fraction = 0.25   # Maximum Kelly fraction for safety
        self.min_arbitrage_profit = 0.01 # Minimum 1% profit for arbitrage
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        return f"betting_analytics:{prefix}:{':'.join(map(str, args))}"

    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data"""
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def _set_cached(self, key: str, data: Dict, ttl: int = None) -> None:
        """Set cached data"""
        try:
            ttl = ttl or self.cache_ttl
            self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def american_to_decimal(self, american_odds: int) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    def decimal_to_probability(self, decimal_odds: float) -> float:
        """Convert decimal odds to implied probability"""
        return 1 / decimal_odds

    def kelly_criterion(self, true_prob: float, decimal_odds: float) -> float:
        """
        Calculate Kelly Criterion fraction

        Args:
            true_prob: True probability of winning (0-1)
            decimal_odds: Decimal odds from sportsbook

        Returns:
            Kelly fraction (0-1)
        """
        if true_prob <= 0 or true_prob >= 1:
            return 0

        # Kelly formula: f = (bp - q) / b
        # where b = decimal_odds - 1, p = true_prob, q = 1 - true_prob
        b = decimal_odds - 1
        p = true_prob
        q = 1 - true_prob

        kelly_fraction = (b * p - q) / b

        # Cap at maximum fraction for safety
        return max(0, min(kelly_fraction, self.max_kelly_fraction))

    def calculate_expected_value(self, true_prob: float, decimal_odds: float) -> float:
        """Calculate expected value of a bet"""
        win_amount = decimal_odds - 1
        lose_amount = -1
        return (true_prob * win_amount) + ((1 - true_prob) * lose_amount)

    def identify_value_bets(self,
                          game_id: str,
                          true_probabilities: Dict[str, float],
                          odds_data: List[OddsData],
                          bankroll: float = 10000) -> List[ValueBet]:
        """
        Identify value betting opportunities using Kelly Criterion

        Args:
            game_id: Unique game identifier
            true_probabilities: Dict mapping selections to true probabilities
            odds_data: List of odds from different sportsbooks
            bankroll: Total bankroll for stake calculations

        Returns:
            List of ValueBet objects
        """
        cache_key = self._cache_key("value_bets", game_id, hash(str(true_probabilities)))
        cached = self._get_cached(cache_key)
        if cached:
            return [ValueBet(**bet) for bet in cached]

        value_bets = []

        for odds in odds_data:
            for selection, true_prob in true_probabilities.items():
                if true_prob <= 0 or true_prob >= 1:
                    continue

                decimal_odds = self.american_to_decimal(odds.odds) if odds.odds > 0 or odds.odds < 0 else odds.odds
                implied_prob = self.decimal_to_probability(decimal_odds)

                # Only consider if true probability is higher than implied
                if true_prob <= implied_prob:
                    continue

                kelly_fraction = self.kelly_criterion(true_prob, decimal_odds)

                if kelly_fraction < self.min_kelly_threshold:
                    continue

                expected_value = self.calculate_expected_value(true_prob, decimal_odds)
                confidence = (true_prob - implied_prob) / implied_prob

                # Determine risk level
                if kelly_fraction < 0.05:
                    risk_level = RiskLevel.LOW
                elif kelly_fraction < 0.10:
                    risk_level = RiskLevel.MEDIUM
                elif kelly_fraction < 0.20:
                    risk_level = RiskLevel.HIGH
                else:
                    risk_level = RiskLevel.EXTREME

                # Calculate recommended stakes
                recommended_stake = bankroll * kelly_fraction
                max_stake = bankroll * 0.05  # Never bet more than 5% of bankroll
                recommended_stake = min(recommended_stake, max_stake)

                value_bet = ValueBet(
                    game_id=game_id,
                    bet_type=BetType.MONEYLINE,  # This would be determined by context
                    selection=selection,
                    true_probability=true_prob,
                    implied_probability=implied_prob,
                    odds=odds.odds,
                    kelly_fraction=kelly_fraction,
                    expected_value=expected_value,
                    confidence=confidence,
                    risk_level=risk_level,
                    recommended_stake=recommended_stake,
                    max_stake=max_stake,
                    sportsbook=odds.sportsbook
                )

                value_bets.append(value_bet)

        # Cache results
        self._set_cached(cache_key, [asdict(bet) for bet in value_bets])

        return sorted(value_bets, key=lambda x: x.expected_value, reverse=True)

    def detect_arbitrage_opportunities(self,
                                     game_id: str,
                                     odds_matrix: Dict[str, List[OddsData]]) -> List[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunities across multiple sportsbooks

        Args:
            game_id: Unique game identifier
            odds_matrix: Dict mapping selections to list of odds from different books

        Returns:
            List of ArbitrageOpportunity objects
        """
        cache_key = self._cache_key("arbitrage", game_id)
        cached = self._get_cached(cache_key)
        if cached:
            return [ArbitrageOpportunity(**arb) for arb in cached]

        arbitrage_opportunities = []

        selections = list(odds_matrix.keys())
        if len(selections) < 2:
            return arbitrage_opportunities

        # Find best odds for each selection
        best_odds = {}
        best_books = {}

        for selection, odds_list in odds_matrix.items():
            best_odd = max(odds_list, key=lambda x: x.odds)
            decimal_odds = self.american_to_decimal(best_odd.odds) if isinstance(best_odd.odds, int) else best_odd.odds
            best_odds[selection] = decimal_odds
            best_books[selection] = best_odd.sportsbook

        # Check for arbitrage opportunity
        implied_probs = [self.decimal_to_probability(odds) for odds in best_odds.values()]
        total_implied_prob = sum(implied_probs)

        if total_implied_prob < 1.0:  # Arbitrage opportunity exists
            profit_margin = (1 / total_implied_prob) - 1

            if profit_margin >= self.min_arbitrage_profit:
                # Calculate optimal stakes
                total_stake = 1000  # Base stake amount
                stakes = []

                for prob in implied_probs:
                    stake = total_stake * (prob / total_implied_prob)
                    stakes.append(stake)

                guaranteed_profit = total_stake * profit_margin

                # Determine risk level based on profit margin and book reliability
                if profit_margin > 0.05:
                    risk_level = RiskLevel.LOW
                elif profit_margin > 0.02:
                    risk_level = RiskLevel.MEDIUM
                else:
                    risk_level = RiskLevel.HIGH

                arbitrage = ArbitrageOpportunity(
                    game_id=game_id,
                    bet_type=BetType.MONEYLINE,  # Would be determined by context
                    selections=selections,
                    odds=list(best_odds.values()),
                    sportsbooks=list(best_books.values()),
                    profit_margin=profit_margin,
                    total_stake=total_stake,
                    stakes=stakes,
                    guaranteed_profit=guaranteed_profit,
                    risk_level=risk_level
                )

                arbitrage_opportunities.append(arbitrage)

        # Cache results
        self._set_cached(cache_key, [asdict(arb) for arb in arbitrage_opportunities])

        return arbitrage_opportunities

    def analyze_line_movement(self,
                            game_id: str,
                            historical_odds: List[Dict]) -> List[LineMovement]:
        """
        Analyze line movement and detect sharp money indicators

        Args:
            game_id: Unique game identifier
            historical_odds: List of historical odds data with timestamps

        Returns:
            List of LineMovement objects
        """
        cache_key = self._cache_key("line_movement", game_id)
        cached = self._get_cached(cache_key)
        if cached:
            return [LineMovement(**move) for move in cached]

        movements = []

        # Group odds by selection and bet type
        grouped_odds = {}
        for odds_point in historical_odds:
            key = f"{odds_point['selection']}_{odds_point['bet_type']}"
            if key not in grouped_odds:
                grouped_odds[key] = []
            grouped_odds[key].append(odds_point)

        for key, odds_history in grouped_odds.items():
            if len(odds_history) < 2:
                continue

            # Sort by timestamp
            odds_history.sort(key=lambda x: x['timestamp'])

            opening_line = odds_history[0]['line']
            current_line = odds_history[-1]['line']

            movement = current_line - opening_line
            movement_percentage = (movement / abs(opening_line)) * 100 if opening_line != 0 else 0

            # Detect sharp money indicators
            sharp_money_indicator = self._detect_sharp_money(odds_history)

            # Detect reverse line movement
            reverse_line_movement = self._detect_reverse_line_movement(odds_history)

            # Detect steam moves (rapid line movement)
            steam_move = self._detect_steam_move(odds_history)

            selection, bet_type = key.split('_', 1)

            line_movement = LineMovement(
                game_id=game_id,
                bet_type=BetType(bet_type),
                selection=selection,
                opening_line=opening_line,
                current_line=current_line,
                movement=movement,
                movement_percentage=movement_percentage,
                sharp_money_indicator=sharp_money_indicator,
                public_percentage=odds_history[-1].get('public_percentage'),
                money_percentage=odds_history[-1].get('money_percentage'),
                reverse_line_movement=reverse_line_movement,
                steam_move=steam_move
            )

            movements.append(line_movement)

        # Cache results
        self._set_cached(cache_key, [asdict(move) for move in movements])

        return movements

    def _detect_sharp_money(self, odds_history: List[Dict]) -> bool:
        """Detect if sharp money is moving the line"""
        if len(odds_history) < 3:
            return False

        # Look for line movement against public betting percentage
        recent_data = odds_history[-3:]

        for data in recent_data:
            public_pct = data.get('public_percentage', 50)
            money_pct = data.get('money_percentage', 50)

            # If public is heavily on one side but money is on the other
            if abs(public_pct - money_pct) > 20:
                return True

        return False

    def _detect_reverse_line_movement(self, odds_history: List[Dict]) -> bool:
        """Detect reverse line movement (line moves opposite to public betting)"""
        if len(odds_history) < 2:
            return False

        latest = odds_history[-1]
        previous = odds_history[-2]

        public_pct = latest.get('public_percentage', 50)
        line_movement = latest['line'] - previous['line']

        # If public is betting one way but line moves the other way
        if public_pct > 60 and line_movement < 0:  # Public on favorite, line moves away
            return True
        elif public_pct < 40 and line_movement > 0:  # Public on underdog, line moves away
            return True

        return False

    def _detect_steam_move(self, odds_history: List[Dict]) -> bool:
        """Detect steam moves (rapid significant line movement)"""
        if len(odds_history) < 2:
            return False

        # Check for rapid movement in short time period
        recent_window = odds_history[-5:] if len(odds_history) >= 5 else odds_history

        if len(recent_window) < 2:
            return False

        total_movement = abs(recent_window[-1]['line'] - recent_window[0]['line'])
        time_span = (recent_window[-1]['timestamp'] - recent_window[0]['timestamp']).total_seconds() / 3600

        # Steam move criteria: significant movement in short time
        return total_movement > 2 and time_span < 1  # 2+ point move in under 1 hour

    def analyze_public_vs_money(self,
                              betting_data: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze public betting percentage vs money percentage

        Args:
            betting_data: List of betting data with public and money percentages

        Returns:
            Dict with analysis results
        """
        cache_key = self._cache_key("public_money_analysis", hash(str(betting_data)))
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        analysis = {
            'contrarian_opportunities': [],
            'sharp_consensus': [],
            'public_traps': [],
            'summary_stats': {}
        }

        for data in betting_data:
            game_id = data['game_id']
            selection = data['selection']
            public_pct = data.get('public_percentage', 50)
            money_pct = data.get('money_percentage', 50)

            # Calculate the difference
            public_money_diff = money_pct - public_pct

            # Identify patterns
            if abs(public_money_diff) > 15:
                if money_pct > public_pct:
                    # Sharp money on this side
                    analysis['sharp_consensus'].append({
                        'game_id': game_id,
                        'selection': selection,
                        'public_pct': public_pct,
                        'money_pct': money_pct,
                        'edge': public_money_diff
                    })
                else:
                    # Potential contrarian opportunity
                    analysis['contrarian_opportunities'].append({
                        'game_id': game_id,
                        'selection': selection,
                        'public_pct': public_pct,
                        'money_pct': money_pct,
                        'edge': abs(public_money_diff)
                    })

            # Identify public traps (heavy public betting with poor line value)
            if public_pct > 70:
                analysis['public_traps'].append({
                    'game_id': game_id,
                    'selection': selection,
                    'public_pct': public_pct,
                    'money_pct': money_pct,
                    'trap_score': public_pct - money_pct
                })

        # Calculate summary statistics
        public_percentages = [d.get('public_percentage', 50) for d in betting_data]
        money_percentages = [d.get('money_percentage', 50) for d in betting_data]

        analysis['summary_stats'] = {
            'avg_public_pct': np.mean(public_percentages),
            'avg_money_pct': np.mean(money_percentages),
            'public_money_correlation': np.corrcoef(public_percentages, money_percentages)[0, 1],
            'contrarian_opportunities_count': len(analysis['contrarian_opportunities']),
            'sharp_consensus_count': len(analysis['sharp_consensus']),
            'public_traps_count': len(analysis['public_traps'])
        }

        # Cache results
        self._set_cached(cache_key, analysis)

        return analysis

    def calculate_historical_roi(self,
                               bet_history: List[Dict],
                               group_by: str = 'bet_type') -> Dict[str, Dict]:
        """
        Calculate historical ROI by various groupings

        Args:
            bet_history: List of historical bet records
            group_by: How to group the analysis ('bet_type', 'sportsbook', 'selection', 'month')

        Returns:
            Dict with ROI analysis by group
        """
        cache_key = self._cache_key("roi_analysis", group_by, hash(str(bet_history)))
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(bet_history)

        if df.empty:
            return {}

        # Ensure required columns exist
        required_cols = ['stake', 'payout', 'result', group_by]
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")

        # Calculate net profit for each bet
        df['net_profit'] = df.apply(
            lambda row: row['payout'] - row['stake'] if row['result'] == 'win' else -row['stake'],
            axis=1
        )

        # Group analysis
        grouped = df.groupby(group_by)

        roi_analysis = {}

        for group_name, group_data in grouped:
            total_staked = group_data['stake'].sum()
            total_profit = group_data['net_profit'].sum()
            roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

            wins = len(group_data[group_data['result'] == 'win'])
            total_bets = len(group_data)
            win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0

            avg_odds = group_data['odds'].mean() if 'odds' in group_data.columns else 0
            avg_stake = group_data['stake'].mean()

            # Calculate streaks
            results = group_data['result'].tolist()
            current_streak = self._calculate_current_streak(results)
            max_winning_streak = self._calculate_max_streak(results, 'win')
            max_losing_streak = self._calculate_max_streak(results, 'loss')

            # Risk metrics
            profits = group_data['net_profit'].tolist()
            max_drawdown = self._calculate_max_drawdown(profits)
            volatility = np.std(profits)
            sharpe_ratio = (np.mean(profits) / volatility) if volatility > 0 else 0

            roi_analysis[str(group_name)] = {
                'total_bets': total_bets,
                'total_staked': total_staked,
                'total_profit': total_profit,
                'roi_percentage': roi,
                'win_rate': win_rate,
                'avg_odds': avg_odds,
                'avg_stake': avg_stake,
                'current_streak': current_streak,
                'max_winning_streak': max_winning_streak,
                'max_losing_streak': max_losing_streak,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'profitability_score': roi * (win_rate / 100)  # Combined metric
            }

        # Cache results
        self._set_cached(cache_key, roi_analysis)

        return roi_analysis

    def _calculate_current_streak(self, results: List[str]) -> Dict[str, int]:
        """Calculate current winning/losing streak"""
        if not results:
            return {'type': 'none', 'count': 0}

        current_result = results[-1]
        streak_count = 1

        for i in range(len(results) - 2, -1, -1):
            if results[i] == current_result:
                streak_count += 1
            else:
                break

        return {'type': current_result, 'count': streak_count}

    def _calculate_max_streak(self, results: List[str], streak_type: str) -> int:
        """Calculate maximum streak of specified type"""
        if not results:
            return 0

        max_streak = 0
        current_streak = 0

        for result in results:
            if result == streak_type:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def _calculate_max_drawdown(self, profits: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not profits:
            return 0

        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative

        return float(np.max(drawdown))

    def recommend_bankroll_management(self,
                                   bankroll: float,
                                   risk_tolerance: str = "medium",
                                   betting_history: Optional[List[Dict]] = None) -> Dict:
        """
        Provide bankroll management recommendations

        Args:
            bankroll: Current bankroll amount
            risk_tolerance: "conservative", "medium", "aggressive"
            betting_history: Optional historical betting data for personalization

        Returns:
            Dict with bankroll management recommendations
        """
        cache_key = self._cache_key("bankroll_mgmt", bankroll, risk_tolerance)
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Base recommendations by risk tolerance
        base_recommendations = {
            "conservative": {
                "max_bet_percentage": 2,
                "max_daily_risk": 5,
                "kelly_multiplier": 0.25,
                "stop_loss_percentage": 10
            },
            "medium": {
                "max_bet_percentage": 3,
                "max_daily_risk": 8,
                "kelly_multiplier": 0.5,
                "stop_loss_percentage": 15
            },
            "aggressive": {
                "max_bet_percentage": 5,
                "max_daily_risk": 12,
                "kelly_multiplier": 0.75,
                "stop_loss_percentage": 20
            }
        }

        base_rec = base_recommendations.get(risk_tolerance, base_recommendations["medium"])

        # Adjust based on betting history if available
        if betting_history:
            roi_analysis = self.calculate_historical_roi(betting_history, 'bet_type')

            # Calculate overall performance metrics
            total_roi = sum(data['roi_percentage'] for data in roi_analysis.values()) / len(roi_analysis) if roi_analysis else 0
            avg_win_rate = sum(data['win_rate'] for data in roi_analysis.values()) / len(roi_analysis) if roi_analysis else 0

            # Adjust recommendations based on performance
            if total_roi > 10 and avg_win_rate > 55:  # Strong performance
                base_rec["max_bet_percentage"] = min(base_rec["max_bet_percentage"] * 1.2, 8)
                base_rec["kelly_multiplier"] = min(base_rec["kelly_multiplier"] * 1.1, 1.0)
            elif total_roi < -5 or avg_win_rate < 45:  # Poor performance
                base_rec["max_bet_percentage"] = max(base_rec["max_bet_percentage"] * 0.7, 1)
                base_rec["kelly_multiplier"] = max(base_rec["kelly_multiplier"] * 0.8, 0.1)

        recommendations = {
            "bankroll": bankroll,
            "risk_tolerance": risk_tolerance,
            "max_bet_amount": bankroll * (base_rec["max_bet_percentage"] / 100),
            "max_daily_risk": bankroll * (base_rec["max_daily_risk"] / 100),
            "suggested_unit_size": bankroll * 0.01,  # 1% unit size
            "kelly_multiplier": base_rec["kelly_multiplier"],
            "stop_loss_threshold": bankroll * (base_rec["stop_loss_percentage"] / 100),
            "bankroll_allocation": {
                "value_bets": 60,
                "arbitrage": 20,
                "speculative": 15,
                "emergency_fund": 5
            },
            "rebalancing_rules": {
                "frequency": "weekly",
                "profit_threshold": 20,  # Rebalance when up 20%
                "loss_threshold": -10    # Rebalance when down 10%
            }
        }

        # Cache results
        self._set_cached(cache_key, recommendations, ttl=3600)  # Cache for 1 hour

        return recommendations

    def assess_parlay_risk(self,
                          legs: List[Dict],
                          correlation_matrix: Optional[np.ndarray] = None) -> Dict:
        """
        Assess risk for parlay and teaser bets

        Args:
            legs: List of bet legs with probabilities and odds
            correlation_matrix: Optional correlation matrix between legs

        Returns:
            Dict with risk assessment
        """
        cache_key = self._cache_key("parlay_risk", hash(str(legs)))
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if not legs:
            return {"error": "No legs provided"}

        num_legs = len(legs)

        # Calculate individual probabilities
        individual_probs = []
        individual_odds = []

        for leg in legs:
            prob = leg.get('probability', 0.5)
            odds = leg.get('odds', 2.0)
            individual_probs.append(prob)
            individual_odds.append(odds)

        # Calculate parlay probability (assuming independence if no correlation matrix)
        if correlation_matrix is None:
            parlay_prob = np.prod(individual_probs)
        else:
            # Adjust for correlations (simplified approach)
            base_prob = np.prod(individual_probs)
            avg_correlation = np.mean(correlation_matrix[np.triu_indices(num_legs, k=1)])
            correlation_adjustment = 1 + (avg_correlation * 0.1)  # Simplified adjustment
            parlay_prob = base_prob * correlation_adjustment

        # Calculate parlay odds
        parlay_odds = np.prod(individual_odds)
        parlay_implied_prob = 1 / parlay_odds

        # Risk assessment metrics
        probability_gap = parlay_implied_prob - parlay_prob
        expected_value = (parlay_prob * (parlay_odds - 1)) - (1 - parlay_prob)

        # Variance calculation
        individual_variances = [p * (1 - p) for p in individual_probs]
        if correlation_matrix is None:
            parlay_variance = np.sum(individual_variances)
        else:
            # Adjusted variance calculation with correlations
            parlay_variance = sum(individual_variances) * (1 + np.mean(correlation_matrix))

        parlay_std = np.sqrt(parlay_variance)

        # Risk level determination
        if expected_value > 0.1 and parlay_prob > 0.3:
            risk_level = RiskLevel.LOW
        elif expected_value > 0 and parlay_prob > 0.2:
            risk_level = RiskLevel.MEDIUM
        elif expected_value > -0.1 and parlay_prob > 0.1:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME

        # Calculate breakeven win rate
        breakeven_rate = 1 / parlay_odds

        # Simulation results
        simulation_results = self._simulate_parlay(individual_probs, correlation_matrix, 10000)

        risk_assessment = {
            "num_legs": num_legs,
            "individual_probabilities": individual_probs,
            "parlay_probability": parlay_prob,
            "parlay_odds": parlay_odds,
            "parlay_implied_probability": parlay_implied_prob,
            "expected_value": expected_value,
            "probability_gap": probability_gap,
            "variance": parlay_variance,
            "standard_deviation": parlay_std,
            "risk_level": risk_level.value,
            "breakeven_win_rate": breakeven_rate,
            "kelly_fraction": max(0, self.kelly_criterion(parlay_prob, parlay_odds)),
            "simulation_results": simulation_results,
            "recommendations": {
                "max_stake_percentage": min(2.0 / num_legs, 1.0),  # Decrease with more legs
                "confidence_interval": [
                    max(0, parlay_prob - 1.96 * parlay_std),
                    min(1, parlay_prob + 1.96 * parlay_std)
                ],
                "alternative_strategies": [
                    "Consider individual bets instead",
                    "Reduce number of legs",
                    "Look for correlated legs to remove"
                ]
            }
        }

        # Cache results
        self._set_cached(cache_key, risk_assessment)

        return risk_assessment

    def _simulate_parlay(self,
                        probabilities: List[float],
                        correlation_matrix: Optional[np.ndarray],
                        num_simulations: int = 10000) -> Dict:
        """Simulate parlay outcomes using Monte Carlo"""
        wins = 0

        for _ in range(num_simulations):
            if correlation_matrix is None:
                # Independent outcomes
                outcomes = [np.random.random() < p for p in probabilities]
            else:
                # Correlated outcomes (simplified approach)
                base_outcomes = [np.random.random() < p for p in probabilities]
                # Apply correlation effects (simplified)
                outcomes = base_outcomes  # More complex correlation modeling would go here

            if all(outcomes):
                wins += 1

        win_rate = wins / num_simulations

        return {
            "simulated_win_rate": win_rate,
            "simulated_wins": wins,
            "total_simulations": num_simulations,
            "confidence_95": [
                max(0, win_rate - 1.96 * np.sqrt(win_rate * (1 - win_rate) / num_simulations)),
                min(1, win_rate + 1.96 * np.sqrt(win_rate * (1 - win_rate) / num_simulations))
            ]
        }

    async def generate_live_alerts(self,
                                 monitoring_games: List[str],
                                 alert_thresholds: Dict) -> List[Dict]:
        """
        Generate live betting opportunity alerts

        Args:
            monitoring_games: List of game IDs to monitor
            alert_thresholds: Thresholds for different alert types

        Returns:
            List of alert objects
        """
        alerts = []

        for game_id in monitoring_games:
            # Check for value bet opportunities
            value_alerts = await self._check_value_bet_alerts(game_id, alert_thresholds)
            alerts.extend(value_alerts)

            # Check for arbitrage opportunities
            arb_alerts = await self._check_arbitrage_alerts(game_id, alert_thresholds)
            alerts.extend(arb_alerts)

            # Check for line movement alerts
            movement_alerts = await self._check_line_movement_alerts(game_id, alert_thresholds)
            alerts.extend(movement_alerts)

            # Check for steam move alerts
            steam_alerts = await self._check_steam_move_alerts(game_id, alert_thresholds)
            alerts.extend(steam_alerts)

        # Sort by priority and timestamp
        alerts.sort(key=lambda x: (x.get('priority', 0), x.get('timestamp')), reverse=True)

        return alerts

    async def _check_value_bet_alerts(self, game_id: str, thresholds: Dict) -> List[Dict]:
        """Check for value bet alerts"""
        # This would integrate with live odds feeds
        alerts = []

        # Mock implementation - would connect to real odds APIs
        mock_odds = [
            OddsData("DraftKings", -110),
            OddsData("FanDuel", -105),
            OddsData("BetMGM", -115)
        ]

        mock_true_probs = {"Team A": 0.58, "Team B": 0.42}

        value_bets = self.identify_value_bets(game_id, mock_true_probs, mock_odds)

        for bet in value_bets:
            if bet.expected_value > thresholds.get('min_expected_value', 0.05):
                alert = {
                    'type': 'value_bet',
                    'game_id': game_id,
                    'selection': bet.selection,
                    'sportsbook': bet.sportsbook,
                    'odds': bet.odds,
                    'expected_value': bet.expected_value,
                    'kelly_fraction': bet.kelly_fraction,
                    'priority': min(10, int(bet.expected_value * 100)),
                    'timestamp': datetime.utcnow(),
                    'message': f"Value bet alert: {bet.selection} at {bet.odds} (EV: {bet.expected_value:.3f})"
                }
                alerts.append(alert)

        return alerts

    async def _check_arbitrage_alerts(self, game_id: str, thresholds: Dict) -> List[Dict]:
        """Check for arbitrage opportunity alerts"""
        alerts = []

        # Mock implementation
        mock_odds_matrix = {
            "Team A": [OddsData("Book1", 1.95), OddsData("Book2", 2.10)],
            "Team B": [OddsData("Book1", 1.90), OddsData("Book2", 1.85)]
        }

        arbitrage_ops = self.detect_arbitrage_opportunities(game_id, mock_odds_matrix)

        for arb in arbitrage_ops:
            if arb.profit_margin > thresholds.get('min_arbitrage_profit', 0.01):
                alert = {
                    'type': 'arbitrage',
                    'game_id': game_id,
                    'selections': arb.selections,
                    'sportsbooks': arb.sportsbooks,
                    'profit_margin': arb.profit_margin,
                    'guaranteed_profit': arb.guaranteed_profit,
                    'priority': min(10, int(arb.profit_margin * 200)),
                    'timestamp': datetime.utcnow(),
                    'message': f"Arbitrage opportunity: {arb.profit_margin:.2%} profit guaranteed"
                }
                alerts.append(alert)

        return alerts

    async def _check_line_movement_alerts(self, game_id: str, thresholds: Dict) -> List[Dict]:
        """Check for significant line movement alerts"""
        alerts = []

        # Mock line movement data
        mock_historical = [
            {'selection': 'Team A', 'bet_type': 'spread', 'line': -3.5, 'timestamp': datetime.utcnow() - timedelta(hours=2)},
            {'selection': 'Team A', 'bet_type': 'spread', 'line': -2.5, 'timestamp': datetime.utcnow() - timedelta(hours=1)},
            {'selection': 'Team A', 'bet_type': 'spread', 'line': -1.5, 'timestamp': datetime.utcnow()}
        ]

        movements = self.analyze_line_movement(game_id, mock_historical)

        for movement in movements:
            if abs(movement.movement) > thresholds.get('min_line_movement', 1.0):
                alert = {
                    'type': 'line_movement',
                    'game_id': game_id,
                    'selection': movement.selection,
                    'bet_type': movement.bet_type.value,
                    'movement': movement.movement,
                    'sharp_money': movement.sharp_money_indicator,
                    'reverse_line_movement': movement.reverse_line_movement,
                    'priority': min(10, int(abs(movement.movement) * 2)),
                    'timestamp': datetime.utcnow(),
                    'message': f"Line movement alert: {movement.selection} {movement.bet_type.value} moved {movement.movement:+.1f}"
                }
                alerts.append(alert)

        return alerts

    async def _check_steam_move_alerts(self, game_id: str, thresholds: Dict) -> List[Dict]:
        """Check for steam move alerts"""
        alerts = []

        # Mock implementation - would detect rapid line movements across multiple books
        # This would require real-time odds monitoring

        return alerts