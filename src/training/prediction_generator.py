"""
Prediction Generator for NFL Training System

This module implements the prediction generation system that takes expert configurations,
game data, and retrieved memories to produce predictions with reasoning chains.
"""

import asyncio
import logging
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
from dotenv import load_dotenv

from training.expert_configuration import ExpertType, ExpertConfiguration, ExpertConfigurationManager
from training.temporal_decay_calculator import TemporalDecayCalculator
from training.memory_retrieval_system import MemoryRetrievalSystem, RetrievedMemory, MemoryRetrievalResult

# Load environment variables
load_dotenv()


class PredictionType(Enum):
    WINNER = "winner"
    SPREAD = "spread"
    TOTAL = "total"


@dataclass
class GamePrediction:
    """A prediction made by an expert for a specific game"""
    expert_type: ExpertType
    prediction_type: PredictionType

    # Winner prediction
    predicted_winner: Optional[str] = None
    win_probability: Optional[float] = None

    # Spread prediction
    predicted_spread: Optional[float] = None  # Positive = home favored
    spread_confidence: Optional[float] = None

    # Total prediction
    predicted_total: Optional[float] = None
    total_confidence: Optional[float] = None

    # Reasoning and metadata
    reasoning_chain: List[str] = None
    key_factors: List[str] = None
    confidence_level: float = 0.0
    prediction_timestamp: datetime = None

    # Supporting data
    retrieved_memories_used: int = 0
    primary_analytical_factors: List[str] = None

    def __post_init__(self):
        if self.reasoning_chain is None:
            self.reasoning_chain = []
        if self.key_factors is None:
            self.key_factors = []
        if self.primary_analytical_factors is None:
            self.primary_analytical_factors = []
        if self.prediction_timestamp is None:
            self.prediction_timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary"""
        return {
            'expert_type': self.expert_type.value,
            'prediction_type': self.prediction_type.value,
            'predicted_winner': self.predicted_winner,
            'win_probability': self.win_probability,
            'predicted_spread': self.predicted_spread,
            'spread_confidence': self.spread_confidence,
            'predicted_total': self.predicted_total,
            'total_confidence': self.total_confidence,
            'reasoning_chain': self.reasoning_chain,
            'key_factors': self.key_factors,
            'confidence_level': self.confidence_level,
            'prediction_timestamp': self.prediction_timestamp.isoformat(),
            'retrieved_memories_used': self.retrieved_memories_used,
            'primary_analytical_factors': self.primary_analytical_factors
        }


class PredictionGenerator:
    """
    Generates predictions using expert configurations, game data, and retrieved memories
    """

    def __init__(
        self,
        config_manager: ExpertConfigurationManager,
        temporal_calculator: TemporalDecayCalculator,
        memory_retrieval_system: MemoryRetrievalSystem
    ):
        self.config_manager = config_manager
        self.temporal_calculator = temporal_calculator
        self.memory_retrieval_system = memory_retrieval_system
        self.logger = logging.getLogger(__name__)

        # Initialize OpenRouter LLM integration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.use_llm = bool(self.openrouter_api_key)

        if self.use_llm:
            self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

            # Model selection - can be configured via environment variable
            # Default to DeepSeek Chat v3.1 which is free and excellent for reasoning
            self.model = os.getenv('LLM_MODEL', "deepseek/deepseek-chat-v3.1:free")

            # Rate limiting based on model tier
            if ":free" in self.model:
                self.requests_per_minute = 20  # Conservative for free tier
            else:
                self.requests_per_minute = 60  # Higher for paid models

            self.logger.info(f"✅ OpenRouter LLM integration enabled with model: {self.model}")
        else:
            self.logger.warning("⚠️ No OpenRouter API key - using enhanced simulation")

        # Rate limiting
        self.last_request_times = []

    async def generate_prediction(
        self,
        expert_type: ExpertType,
        game_context: Dict[str, Any],
        prediction_types: List[PredictionType] = None,
        current_date: datetime = None
    ) -> List[GamePrediction]:
        """
        Generate predictions for a game using expert's methodology

        Args:
            expert_type: Type of expert making predictions
            game_context: Complete game context and data
            prediction_types: Types of predictions to make (default: all)
            current_date: Current date for temporal calculations

        Returns:
            List of GamePrediction objects
        """
        if prediction_types is None:
            prediction_types = [PredictionType.WINNER, PredictionType.SPREAD, PredictionType.TOTAL]

        if current_date is None:
            current_date = datetime.now()

        config = self.config_manager.get_configuration(expert_type)
        if not config:
            raise ValueError(f"No configuration found for expert type: {expert_type}")

        # Retrieve relevant memories
        memory_result = await self.memory_retrieval_system.retrieve_memories_for_expert(
            expert_type, game_context, current_date
        )

        # Log detailed memory retrieval for this expert
        await self._log_expert_memory_retrieval(expert_type, game_context, memory_result)

        # Generate predictions for each requested type
        predictions = []

        for pred_type in prediction_types:
            prediction = await self._generate_single_prediction(
                expert_type, pred_type, game_context, memory_result, config
            )
            predictions.append(prediction)

        return predictions

    async def _generate_single_prediction(
        self,
        expert_type: ExpertType,
        prediction_type: PredictionType,
        game_context: Dict[str, Any],
        memory_result: MemoryRetrievalResult,
        config: ExpertConfiguration
    ) -> GamePrediction:
        """Generate a single prediction of specified type"""

        # Use LLM if available, otherwise fall back to enhanced simulation
        if self.use_llm:
            return await self._generate_llm_prediction(
                expert_type, prediction_type, game_context, memory_result, config
            )
        else:
            return await self._generate_simulation_prediction(
                expert_type, prediction_type, game_context, memory_result, config
            )

    async def _generate_llm_prediction(
        self,
        expert_type: ExpertType,
        prediction_type: PredictionType,
        game_context: Dict[str, Any],
        memory_result: MemoryRetrievalResult,
        config: ExpertConfiguration
    ) -> GamePrediction:
        """Generate prediction using real LLM calls"""

        try:
            # Build expert system prompt
            system_prompt = self._build_expert_system_prompt(config)

            # Build game analysis prompt
            user_prompt = self._build_game_analysis_prompt(
                game_context, memory_result.retrieved_memories, prediction_type
            )

            # Make LLM API call
            llm_response = await self._call_openrouter_llm(system_prompt, user_prompt)

            # Parse LLM response into GamePrediction
            prediction = self._parse_llm_response(
                llm_response, expert_type, prediction_type, memory_result
            )

            return prediction

        except Exception as e:
            self.logger.error(f"❌ LLM prediction failed for {expert_type.value}: {e}")
            # Fall back to simulation
            return await self._generate_simulation_prediction(
                expert_type, prediction_type, game_context, memory_result, config
            )

    async def _generate_simulation_prediction(
        self,
        expert_type: ExpertType,
        prediction_type: PredictionType,
        game_context: Dict[str, Any],
        memory_result: MemoryRetrievalResult,
        config: ExpertConfiguration
    ) -> GamePrediction:
        """Generate prediction using enhanced simulation (original logic)"""

        # Initialize prediction
        prediction = GamePrediction(
            expert_type=expert_type,
            prediction_type=prediction_type,
            retrieved_memories_used=len(memory_result.retrieved_memories)
        )

        # Analyze game context using expert's analytical focus
        analytical_insights = self._analyze_game_context(game_context, config, expert_type)

        # Incorporate memory insights
        memory_insights = self._analyze_retrieved_memories(memory_result.retrieved_memories, config)

        # Generate prediction based on type
        if prediction_type == PredictionType.WINNER:
            await self._generate_winner_prediction(prediction, game_context, analytical_insights, memory_insights, config)
        elif prediction_type == PredictionType.SPREAD:
            await self._generate_spread_prediction(prediction, game_context, analytical_insights, memory_insights, config)
        elif prediction_type == PredictionType.TOTAL:
            await self._generate_total_prediction(prediction, game_context, analytical_insights, memory_insights, config)

        # Build reasoning chain
        prediction.reasoning_chain = self._build_reasoning_chain(
            expert_type, prediction_type, analytical_insights, memory_insights, game_context
        )

        # Identify key factors
        prediction.key_factors = self._identify_key_factors(analytical_insights, memory_insights, config)

        # Set primary analytical factors
        prediction.primary_analytical_factors = self._get_primary_analytical_factors(config)

        return prediction

    def _analyze_game_context(
        self,
        game_context: Dict[str, Any],
        config: ExpertConfiguration,
        expert_type: ExpertType
    ) -> Dict[str, Any]:
        """Analyze game context through expert's analytical lens"""

        insights = {
            'weighted_factors': {},
            'key_observations': [],
            'concern_areas': [],
            'confidence_modifiers': []
        }

        # Analyze each factor based on expert's focus weights
        for factor, weight in config.analytical_focus.items():
            if weight < 0.3:  # Skip low-weight factors
                continue

            factor_insight = self._analyze_specific_factor(factor, game_context, weight, expert_type)
            if factor_insight:
                insights['weighted_factors'][factor] = {
                    'weight': weight,
                    'insight': factor_insight,
                    'impact_direction': factor_insight.get('impact_direction', 'neutral'),
                    'confidence_impact': factor_insight.get('confidence_impact', 0.0)
                }

                if factor_insight.get('observation'):
                    insights['key_observations'].append(factor_insight['observation'])

                if factor_insight.get('concern'):
                    insights['concern_areas'].append(factor_insight['concern'])

        return insights

    def _analyze_specific_factor(
        self,
        factor: str,
        game_context: Dict[str, Any],
        weight: float,
        expert_type: ExpertType
    ) -> Optional[Dict[str, Any]]:
        """Analyze a specific analytical factor"""

        if factor == 'weather_temperature':
            temp = game_context.get('weather', {}).get('temperature', 70)
            if temp <= 32:
                return {
                    'observation': f"Freezing temperature ({temp}°F) favors ground game",
                    'impact_direction': 'under' if expert_type == ExpertType.TOTAL_PREDICTOR else 'home',
                    'confidence_impact': 0.1 * weight
                }
            elif temp >= 85:
                return {
                    'observation': f"Hot weather ({temp}°F) may affect player stamina",
                    'impact_direction': 'under',
                    'confidence_impact': 0.05 * weight
                }

        elif factor == 'wind_speed_direction':
            wind = game_context.get('weather', {}).get('wind_speed', 0)
            if wind >= 15:
                return {
                    'observation': f"High winds ({wind} mph) will impact passing game",
                    'impact_direction': 'under',
                    'confidence_impact': 0.15 * weight
                }

        elif factor == 'line_movement_patterns':
            line_data = game_context.get('line_movement', {})
            if line_data:
                opening = line_data.get('opening', 0)
                current = line_data.get('current', 0)
                movement = current - opening

                if abs(movement) >= 2.0:
                    direction = "toward favorite" if movement < 0 else "toward underdog"
                    return {
                        'observation': f"Significant line movement ({movement:+.1f}) {direction}",
                        'impact_direction': 'away' if movement < 0 else 'home',
                        'confidence_impact': 0.1 * weight
                    }

        elif factor == 'public_betting_percentages':
            public_data = game_context.get('public_betting', {})
            if public_data:
                home_pct = public_data.get('home', 50)
                if home_pct >= 75:
                    return {
                        'observation': f"Heavy public betting on home team ({home_pct}%)",
                        'impact_direction': 'away' if expert_type == ExpertType.CONTRARIAN_EXPERT else 'home',
                        'confidence_impact': 0.08 * weight
                    }
                elif home_pct <= 25:
                    return {
                        'observation': f"Heavy public betting on away team ({100-home_pct}%)",
                        'impact_direction': 'home' if expert_type == ExpertType.CONTRARIAN_EXPERT else 'away',
                        'confidence_impact': 0.08 * weight
                    }

        elif factor == 'divisional_rivalry_history':
            if game_context.get('division_game'):
                return {
                    'observation': "Divisional rivalry game - expect closer contest",
                    'impact_direction': 'under',
                    'confidence_impact': 0.12 * weight
                }

        elif factor == 'recent_win_loss_trends':
            momentum = game_context.get('momentum', {})
            if momentum:
                home_trend = momentum.get('home', '')
                away_trend = momentum.get('away', '')

                if 'hot' in home_trend.lower():
                    return {
                        'observation': f"Home team on hot streak: {home_trend}",
                        'impact_direction': 'home',
                        'confidence_impact': 0.1 * weight
                    }
                elif 'hot' in away_trend.lower():
                    return {
                        'observation': f"Away team on hot streak: {away_trend}",
                        'impact_direction': 'away',
                        'confidence_impact': 0.1 * weight
                    }

        return None

    def _analyze_retrieved_memories(
        self,
        retrieved_memories: List[RetrievedMemory],
        config: ExpertConfiguration
    ) -> Dict[str, Any]:
        """Analyze insights from retrieved memories"""

        insights = {
            'memory_patterns': [],
            'historical_outcomes': [],
            'confidence_adjustments': [],
            'learned_lessons': []
        }

        for retrieved_mem in retrieved_memories:
            memory = retrieved_mem.memory
            score = retrieved_mem.decay_score.final_weighted_score

            # Extract patterns from memory content
            if 'favor' in memory.content.lower():
                insights['memory_patterns'].append({
                    'pattern': memory.content,
                    'weight': score,
                    'age_days': retrieved_mem.decay_score.age_days
                })

            # Historical outcomes
            if memory.outcome_data:
                insights['historical_outcomes'].append({
                    'outcome': memory.outcome_data,
                    'context': memory.game_context,
                    'weight': score
                })

            # Learning memories provide confidence adjustments
            if memory.memory_type == 'learning':
                insights['learned_lessons'].append({
                    'lesson': memory.content,
                    'confidence_adjustment': -0.05 * score  # Learning from mistakes reduces confidence
                })

        return insights

    async def _generate_winner_prediction(
        self,
        prediction: GamePrediction,
        game_context: Dict[str, Any],
        analytical_insights: Dict[str, Any],
        memory_insights: Dict[str, Any],
        config: ExpertConfiguration
    ):
        """Generate winner prediction with expert personality-driven logic"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        expert_type = config.expert_type

        # Expert-specific base probability and confidence
        if expert_type == ExpertType.CHAOS_THEORY_BELIEVER:
            home_win_prob = 0.50  # Chaos believes anything can happen
            base_confidence = 0.30  # Low confidence due to chaos belief
        elif expert_type == ExpertType.CONSERVATIVE_ANALYZER:
            home_win_prob = 0.52  # Slight conservative lean toward data
            base_confidence = 0.70  # High confidence in analysis
        elif expert_type == ExpertType.CONTRARIAN_REBEL:
            # Check public betting to be contrarian
            public_home = game_context.get('public_betting', {}).get('home', 50)
            if public_home >= 70:
                home_win_prob = 0.35  # Fade heavy public home betting
            elif public_home <= 30:
                home_win_prob = 0.65  # Fade heavy public away betting
            else:
                home_win_prob = 0.50
            base_confidence = 0.60  # Moderate confidence in contrarian approach
        elif expert_type == ExpertType.FUNDAMENTALIST_SCHOLAR:
            home_win_prob = 0.53  # Slight edge from research
            base_confidence = 0.80  # Very high confidence in research
        elif expert_type == ExpertType.GUT_INSTINCT_EXPERT:
            # Random gut feeling simulation
            import random
            home_win_prob = 0.45 + random.random() * 0.10  # 45-55% range
            base_confidence = 0.85  # Paradoxically high confidence in gut
        elif expert_type == ExpertType.MOMENTUM_RIDER:
            # Heavy weight on momentum
            momentum = game_context.get('momentum', {})
            home_momentum = momentum.get('home', '')
            away_momentum = momentum.get('away', '')

            if 'hot' in home_momentum.lower():
                home_win_prob = 0.70  # Ride the hot team
            elif 'hot' in away_momentum.lower():
                home_win_prob = 0.30  # Ride the hot away team
            else:
                home_win_prob = 0.55
            base_confidence = 0.75  # High confidence in momentum
        elif expert_type == ExpertType.UNDERDOG_CHAMPION:
            # Always lean toward underdog
            current_line = game_context.get('line_movement', {}).get('current', 0)
            if current_line < -3:  # Home favored by more than 3
                home_win_prob = 0.35  # Champion the away underdog
            elif current_line > 3:  # Away favored by more than 3
                home_win_prob = 0.65  # Champion the home underdog
            else:
                home_win_prob = 0.50
            base_confidence = 0.55  # Moderate confidence in upsets
        elif expert_type == ExpertType.RISK_TAKING_GAMBLER:
            # Extreme positions for big payouts
            import random
            if random.random() < 0.3:  # 30% chance of extreme position
                home_win_prob = 0.25 if random.random() < 0.5 else 0.75
            else:
                home_win_prob = 0.55
            base_confidence = 0.80  # High confidence (overconfidence)
        elif expert_type == ExpertType.CONSENSUS_FOLLOWER:
            # Follows market consensus
            home_win_prob = 0.55  # Slight home field edge
            base_confidence = 0.50  # Moderate confidence in consensus
        elif expert_type == ExpertType.MARKET_INEFFICIENCY_EXPLOITER:
            # Looks for market edges
            current_line = game_context.get('line_movement', {}).get('current', 0)
            opening_line = game_context.get('line_movement', {}).get('opening', 0)
            line_movement = current_line - opening_line

            if abs(line_movement) >= 2.0:  # Significant line movement
                if line_movement > 0:  # Line moved toward away team
                    home_win_prob = 0.40  # Sharp money on away
                else:  # Line moved toward home team
                    home_win_prob = 0.60  # Sharp money on home
            else:
                home_win_prob = 0.55
            base_confidence = 0.75  # High confidence in market reading
        elif expert_type == ExpertType.POPULAR_NARRATIVE_FADER:
            # Fades popular narratives - similar to contrarian but narrative-focused
            public_home = game_context.get('public_betting', {}).get('home', 50)
            if public_home >= 65:
                home_win_prob = 0.40  # Fade popular home narrative
            elif public_home <= 35:
                home_win_prob = 0.60  # Fade popular away narrative
            else:
                home_win_prob = 0.50
            base_confidence = 0.65  # Moderate-high confidence in narrative fading
        elif expert_type == ExpertType.SHARP_MONEY_FOLLOWER:
            # Follows professional betting patterns
            current_line = game_context.get('line_movement', {}).get('current', 0)
            opening_line = game_context.get('line_movement', {}).get('opening', 0)
            line_movement = current_line - opening_line

            if abs(line_movement) >= 1.5:  # Follow sharp money movement
                if line_movement > 0:  # Sharp money on away
                    home_win_prob = 0.35
                else:  # Sharp money on home
                    home_win_prob = 0.65
            else:
                home_win_prob = 0.55
            base_confidence = 0.80  # High confidence in sharp money
        elif expert_type == ExpertType.STATISTICS_PURIST:
            # Pure mathematical approach
            home_win_prob = 0.52  # Slight analytical edge
            base_confidence = 0.75  # High confidence in math
        elif expert_type == ExpertType.TREND_REVERSAL_SPECIALIST:
            # Looks for trend reversals
            momentum = game_context.get('momentum', {})
            home_momentum = momentum.get('home', '')
            away_momentum = momentum.get('away', '')

            if 'hot' in home_momentum.lower():
                home_win_prob = 0.40  # Expect reversal of hot streak
            elif 'cold' in home_momentum.lower():
                home_win_prob = 0.60  # Expect reversal of cold streak
            else:
                home_win_prob = 0.50
            base_confidence = 0.60  # Moderate confidence in reversals
        elif expert_type == ExpertType.VALUE_HUNTER:
            # Seeks value opportunities
            current_line = game_context.get('line_movement', {}).get('current', 0)
            if abs(current_line) >= 7:  # Large spread suggests value on underdog
                if current_line < 0:  # Home heavily favored
                    home_win_prob = 0.45  # Value on away underdog
                else:  # Away heavily favored
                    home_win_prob = 0.55  # Value on home underdog
            else:
                home_win_prob = 0.52
            base_confidence = 0.65  # Moderate-high confidence in value
        else:
            # Default for any missing experts
            home_win_prob = 0.55
            base_confidence = 0.60

        # Apply memory insights with expert-specific weighting
        total_memory_weight = 0
        for retrieved_mem in memory_insights.get('memory_patterns', []):
            memory_score = retrieved_mem['weight']
            memory_content = retrieved_mem['pattern'].lower()

            # Expert-specific memory interpretation
            if expert_type == ExpertType.MOMENTUM_RIDER:
                # Momentum rider heavily weights recent performance memories
                if 'momentum' in memory_content or 'streak' in memory_content or 'hot' in memory_content:
                    adjustment = 0.15 * memory_score  # Large adjustment for momentum memories
                else:
                    adjustment = 0.02 * memory_score  # Small adjustment for other memories
            elif expert_type == ExpertType.CONTRARIAN_REBEL:
                # Contrarian interprets memories oppositely
                if 'public' in memory_content or 'popular' in memory_content:
                    adjustment = -0.10 * memory_score  # Fade popular sentiment
                else:
                    adjustment = 0.05 * memory_score
            elif expert_type == ExpertType.FUNDAMENTALIST_SCHOLAR:
                # Scholar weights all memories heavily due to research focus
                adjustment = 0.08 * memory_score
            else:
                # Default memory weighting
                adjustment = 0.05 * memory_score

            if 'home' in memory_content:
                home_win_prob += adjustment
            elif 'away' in memory_content or 'underdog' in memory_content:
                home_win_prob -= adjustment

            total_memory_weight += abs(adjustment)

        # Clamp probability
        home_win_prob = max(0.15, min(0.85, home_win_prob))

        # Determine winner
        if home_win_prob > 0.5:
            prediction.predicted_winner = home_team
            prediction.win_probability = home_win_prob
        else:
            prediction.predicted_winner = away_team
            prediction.win_probability = 1.0 - home_win_prob

        # Expert-specific confidence calculation
        decisiveness = abs(home_win_prob - 0.5) * 2.0

        # Adjust base confidence based on how much memory supported the decision
        memory_confidence_boost = min(0.20, total_memory_weight * 2.0)

        prediction.confidence_level = base_confidence * decisiveness + memory_confidence_boost
        prediction.confidence_level = max(0.05, min(0.95, prediction.confidence_level))

    async def _generate_spread_prediction(
        self,
        prediction: GamePrediction,
        game_context: Dict[str, Any],
        analytical_insights: Dict[str, Any],
        memory_insights: Dict[str, Any],
        config: ExpertConfiguration
    ):
        """Generate spread prediction"""

        # Start with current line as baseline
        current_line = game_context.get('line_movement', {}).get('current', -3.0)
        predicted_spread = current_line

        # Adjust based on analytical insights
        total_adjustment = 0.0

        for factor, insight_data in analytical_insights['weighted_factors'].items():
            impact = insight_data['impact_direction']
            weight = insight_data['weight']

            if impact == 'home':
                total_adjustment -= 1.0 * weight  # Home covers more
            elif impact == 'away':
                total_adjustment += 1.0 * weight  # Away covers more

        # Memory-based adjustments
        for outcome in memory_insights['historical_outcomes']:
            outcome_data = outcome['outcome']
            weight = outcome['weight']

            if outcome_data:
                # Simple heuristic based on historical margin
                home_score = outcome_data.get('home_score', 0)
                away_score = outcome_data.get('away_score', 0)
                historical_margin = home_score - away_score

                # Adjust toward historical patterns
                total_adjustment += (historical_margin - current_line) * 0.1 * weight

        predicted_spread = current_line + total_adjustment

        prediction.predicted_spread = round(predicted_spread * 2) / 2  # Round to nearest 0.5
        prediction.spread_confidence = min(0.9, config.confidence_threshold + abs(total_adjustment) * 0.05)

    async def _generate_total_prediction(
        self,
        prediction: GamePrediction,
        game_context: Dict[str, Any],
        analytical_insights: Dict[str, Any],
        memory_insights: Dict[str, Any],
        config: ExpertConfiguration
    ):
        """Generate total points prediction"""

        # Start with current total as baseline
        current_total = game_context.get('total_line', 45.0)
        predicted_total = current_total

        # Adjust based on analytical insights
        total_adjustment = 0.0

        for factor, insight_data in analytical_insights['weighted_factors'].items():
            impact = insight_data['impact_direction']
            weight = insight_data['weight']

            if impact == 'over':
                total_adjustment += 2.0 * weight
            elif impact == 'under':
                total_adjustment -= 2.0 * weight

        # Weather heavily impacts totals
        weather = game_context.get('weather', {})
        temp = weather.get('temperature', 70)
        wind = weather.get('wind_speed', 0)

        if temp <= 32:
            total_adjustment -= 3.0  # Cold weather reduces scoring
        if wind >= 15:
            total_adjustment -= 2.0  # Wind reduces passing

        # Memory-based adjustments
        for outcome in memory_insights['historical_outcomes']:
            outcome_data = outcome['outcome']
            weight = outcome['weight']

            if outcome_data:
                historical_total = outcome_data.get('total', current_total)
                total_adjustment += (historical_total - current_total) * 0.15 * weight

        predicted_total = current_total + total_adjustment

        prediction.predicted_total = round(predicted_total * 2) / 2  # Round to nearest 0.5
        prediction.total_confidence = min(0.9, config.confidence_threshold + abs(total_adjustment) * 0.02)

    def _build_reasoning_chain(
        self,
        expert_type: ExpertType,
        prediction_type: PredictionType,
        analytical_insights: Dict[str, Any],
        memory_insights: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> List[str]:
        """Build expert-specific reasoning chain"""

        reasoning = []
        config = self.config_manager.get_configuration(expert_type)

        # Expert-specific reasoning approach
        if expert_type == ExpertType.CHAOS_THEORY_BELIEVER:
            reasoning.append(f"As {config.name}, chaos theory suggests this game is inherently unpredictable:")
            reasoning.append("  • Random events and butterfly effects dominate outcomes")
            reasoning.append("  • Traditional analysis fails in chaotic systems")
            reasoning.append("  • Embracing uncertainty over false precision")

        elif expert_type == ExpertType.CONTRARIAN_REBEL:
            public_home = game_context.get('public_betting', {}).get('home', 50)
            reasoning.append(f"As {config.name}, I fade the crowd and popular narratives:")
            if public_home >= 70:
                reasoning.append(f"  • Public heavily on home team ({public_home}%) - FADE THEM")
                reasoning.append("  • When everyone thinks the same, no one thinks at all")
            elif public_home <= 30:
                reasoning.append(f"  • Public heavily on away team ({100-public_home}%) - FADE THEM")
                reasoning.append("  • Contrarian value in the unpopular home team")
            else:
                reasoning.append("  • Public split - looking for other contrarian angles")

        elif expert_type == ExpertType.FUNDAMENTALIST_SCHOLAR:
            reasoning.append(f"As {config.name}, my research-driven analysis shows:")
            reasoning.append("  • Deep statistical models reveal underlying patterns")
            reasoning.append("  • Historical data provides the foundation for prediction")
            if memory_insights['memory_patterns']:
                reasoning.append("  • Research validates these key findings:")
                for pattern in memory_insights['memory_patterns'][:2]:
                    reasoning.append(f"    - {pattern['pattern']} (validated {pattern['age_days']} days ago)")

        elif expert_type == ExpertType.GUT_INSTINCT_EXPERT:
            reasoning.append(f"As {config.name}, my intuition tells me:")
            reasoning.append("  • Gut feeling overrides statistical noise")
            reasoning.append("  • Emotional and intangible factors matter most")
            reasoning.append("  • Sometimes you just know - and I know")

        elif expert_type == ExpertType.MOMENTUM_RIDER:
            momentum = game_context.get('momentum', {})
            home_momentum = momentum.get('home', '')
            away_momentum = momentum.get('away', '')
            reasoning.append(f"As {config.name}, momentum is everything:")
            if 'hot' in home_momentum.lower():
                reasoning.append(f"  • Home team is {home_momentum} - RIDE THE WAVE")
                reasoning.append("  • Hot teams stay hot until they don't")
            elif 'hot' in away_momentum.lower():
                reasoning.append(f"  • Away team is {away_momentum} - RIDE THE WAVE")
                reasoning.append("  • Momentum creates its own reality")
            else:
                reasoning.append("  • No clear momentum - waiting for the next wave")

        elif expert_type == ExpertType.UNDERDOG_CHAMPION:
            current_line = game_context.get('line_movement', {}).get('current', 0)
            reasoning.append(f"As {config.name}, I champion the underdog:")
            if current_line < -3:
                reasoning.append(f"  • Away team getting {abs(current_line)} points - LOVE THE DOG")
                reasoning.append("  • Underdogs have heart, favorites have pressure")
            elif current_line > 3:
                reasoning.append(f"  • Home team getting {current_line} points - LOVE THE DOG")
                reasoning.append("  • David vs Goliath - I'm always with David")
            else:
                reasoning.append("  • No clear underdog - looking for value elsewhere")

        elif expert_type == ExpertType.RISK_TAKING_GAMBLER:
            reasoning.append(f"As {config.name}, I'm here for the big score:")
            reasoning.append("  • Fortune favors the bold")
            reasoning.append("  • Playing it safe is the riskiest move of all")
            reasoning.append("  • Go big or go home - and I'm not going home")

        elif expert_type == ExpertType.CONSENSUS_FOLLOWER:
            reasoning.append(f"As {config.name}, I follow the wisdom of crowds:")
            reasoning.append("  • Market consensus reflects collective intelligence")
            reasoning.append("  • Popular opinion exists for good reasons")
            reasoning.append("  • Swimming with the current, not against it")

        elif expert_type == ExpertType.MARKET_INEFFICIENCY_EXPLOITER:
            line_movement = game_context.get('line_movement', {})
            current = line_movement.get('current', 0)
            opening = line_movement.get('opening', 0)
            movement = current - opening
            reasoning.append(f"As {config.name}, I exploit market inefficiencies:")
            if abs(movement) >= 2.0:
                direction = "toward away team" if movement > 0 else "toward home team"
                reasoning.append(f"  • Line moved {abs(movement)} points {direction} - SHARP MONEY")
                reasoning.append("  • Following the smart money trail")
            else:
                reasoning.append("  • No significant line movement - market efficient")

        elif expert_type == ExpertType.POPULAR_NARRATIVE_FADER:
            public_home = game_context.get('public_betting', {}).get('home', 50)
            reasoning.append(f"As {config.name}, I fade popular narratives:")
            if public_home >= 65:
                reasoning.append(f"  • Media loves the home team story ({public_home}%) - FADE IT")
                reasoning.append("  • Popular narratives are usually wrong")
            else:
                reasoning.append("  • No dominant narrative to fade - staying neutral")

        elif expert_type == ExpertType.SHARP_MONEY_FOLLOWER:
            line_movement = game_context.get('line_movement', {})
            movement = line_movement.get('current', 0) - line_movement.get('opening', 0)
            reasoning.append(f"As {config.name}, I follow the sharp money:")
            if abs(movement) >= 1.5:
                direction = "away team" if movement > 0 else "home team"
                reasoning.append(f"  • Sharp money moving toward {direction}")
                reasoning.append("  • Professional bettors know something")
            else:
                reasoning.append("  • No clear sharp money signal yet")

        elif expert_type == ExpertType.STATISTICS_PURIST:
            reasoning.append(f"As {config.name}, mathematics doesn't lie:")
            reasoning.append("  • Statistical models reveal true probabilities")
            reasoning.append("  • Emotions and narratives are noise")
            reasoning.append("  • Numbers tell the complete story")

        elif expert_type == ExpertType.TREND_REVERSAL_SPECIALIST:
            momentum = game_context.get('momentum', {})
            home_momentum = momentum.get('home', '')
            reasoning.append(f"As {config.name}, I identify trend reversals:")
            if 'hot' in home_momentum.lower():
                reasoning.append(f"  • Home team {home_momentum} - DUE FOR REVERSAL")
                reasoning.append("  • Hot streaks always end eventually")
            elif 'cold' in home_momentum.lower():
                reasoning.append(f"  • Home team {home_momentum} - DUE FOR BOUNCE BACK")
                reasoning.append("  • Mean reversion is inevitable")
            else:
                reasoning.append("  • No clear trend to reverse - waiting for signal")

        elif expert_type == ExpertType.VALUE_HUNTER:
            current_line = game_context.get('line_movement', {}).get('current', 0)
            reasoning.append(f"As {config.name}, I hunt for value:")
            if abs(current_line) >= 7:
                underdog = "away team" if current_line < 0 else "home team"
                reasoning.append(f"  • Large spread ({abs(current_line)} points) creates value on {underdog}")
                reasoning.append("  • Market overreacting - value in the dog")
            else:
                reasoning.append("  • Reasonable spread - looking for other value angles")

        else:
            # Default reasoning for any missing experts
            reasoning.append(f"As {config.name}, I analyze this {prediction_type.value} prediction:")
            if analytical_insights.get('key_observations'):
                reasoning.append("Key factors I'm considering:")
                for obs in analytical_insights['key_observations'][:2]:
                    reasoning.append(f"  • {obs}")

        return reasoning

    def _identify_key_factors(
        self,
        analytical_insights: Dict[str, Any],
        memory_insights: Dict[str, Any],
        config: ExpertConfiguration
    ) -> List[str]:
        """Identify the key factors driving this prediction"""

        factors = []

        # Top weighted analytical factors
        sorted_factors = sorted(
            analytical_insights['weighted_factors'].items(),
            key=lambda x: x[1]['weight'],
            reverse=True
        )

        for factor_name, factor_data in sorted_factors[:3]:
            if factor_data['weight'] >= 0.7:
                factors.append(factor_name.replace('_', ' ').title())

        # Memory-based factors
        if len(memory_insights['memory_patterns']) >= 2:
            factors.append("Historical Pattern Recognition")

        if len(memory_insights['learned_lessons']) >= 1:
            factors.append("Learning from Past Mistakes")

        return factors

    def _get_primary_analytical_factors(self, config: ExpertConfiguration) -> List[str]:
        """Get expert's primary analytical factors"""

        # Return top 3 analytical focus areas
        sorted_focus = sorted(
            config.analytical_focus.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [factor.replace('_', ' ').title() for factor, weight in sorted_focus[:3]]

    def _build_expert_system_prompt(self, config: ExpertConfiguration) -> str:
        """Build system prompt for the expert's personality"""

        return f"""You are {config.name}, an NFL prediction expert with the following personality and approach:

PERSONALITY: {config.description}

ANALYTICAL FOCUS: You prioritize these factors in your analysis:
{self._format_analytical_focus(config.analytical_focus)}

CONFIDENCE STYLE: Your base confidence threshold is {config.confidence_threshold:.1%}. You tend to be {'more confident' if config.confidence_threshold > 0.6 else 'more cautious'} in your predictions.

DECISION MAKING: {config.decision_making_style}

Your job is to analyze NFL games and make predictions that reflect your unique analytical approach and personality. Always stay in character and provide reasoning that matches your expertise and style.

RESPONSE FORMAT:
PREDICTION: [Winner/Spread/Total prediction]
CONFIDENCE: [0.0-1.0]
KEY_FACTORS: [comma-separated list of 3-5 key factors]"""

    def _format_analytical_focus(self, focus: Dict[str, float]) -> str:
        """Format analytical focus for prompt"""

        # Sort by weight (highest first)
        sorted_focus = sorted(focus.items(), key=lambda x: x[1], reverse=True)

        # Format as bullet points
        formatted = []
        for factor, weight in sorted_focus[:5]:  # Top 5 factors
            factor_name = factor.replace('_', ' ').title()
            formatted.append(f"- {factor_name}: {weight:.1%} priority")

        return '\n'.join(formatted)

    def _build_game_analysis_prompt(self, game_context: Dict[str, Any],
                                  memories: List[RetrievedMemory],
                                  prediction_type: PredictionType) -> str:
        """Build the game analysis prompt with context and memories"""

        # Basic game information
        home_team = game_context.get('home_team', 'Unknown')
        away_team = game_context.get('away_team', 'Unknown')
        week = game_context.get('week', 'Unknown')

        prompt = f"""
GAME ANALYSIS REQUEST:
{away_team} @ {home_team} (Week {week})

PREDICTION TYPE: {prediction_type.value.upper()}

GAME CONTEXT:
- Home Team: {home_team}
- Away Team: {away_team}
- Week: {week}
- Season: {game_context.get('season', 'Unknown')}

RELEVANT MEMORIES:
"""

        # Add retrieved memories
        if memories:
            for i, memory in enumerate(memories[:5], 1):
                prompt += f"\n{i}. {memory.content[:200]}..."
        else:
            prompt += "\nNo specific memories retrieved for this matchup."

        prompt += f"""

ANALYSIS REQUIRED:
Based on your expertise and the above context, provide your {prediction_type.value} prediction.
Focus on the factors most important to your analytical approach.
Provide clear reasoning for your prediction.

Remember to stay in character and use your unique analytical perspective.
"""

        return prompt

    async def _call_openrouter_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to OpenRouter"""

        await self._enforce_rate_limit()

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional: for tracking
            "X-Title": "NFL Expert System"  # Optional: for tracking
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        try:
            response = requests.post(
                self.openrouter_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ OpenRouter API call failed: {e}")
            raise

    def _parse_llm_response(self, llm_text: str, expert_type: ExpertType,
                          prediction_type: PredictionType,
                          memory_result: MemoryRetrievalResult) -> GamePrediction:
        """Parse LLM response into GamePrediction object"""

        # Initialize prediction
        prediction = GamePrediction(
            expert_type=expert_type,
            prediction_type=prediction_type
        )

        # Parse the response (basic implementation)
        lines = llm_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('PREDICTION:'):
                prediction_text = line.replace('PREDICTION:', '').strip()
                # Parse based on prediction type
                if prediction_type == PredictionType.WINNER:
                    prediction.predicted_winner = prediction_text
                elif prediction_type == PredictionType.SPREAD:
                    try:
                        prediction.predicted_spread = float(prediction_text)
                    except ValueError:
                        prediction.predicted_spread = 0.0
                elif prediction_type == PredictionType.TOTAL:
                    try:
                        prediction.predicted_total = float(prediction_text)
                    except ValueError:
                        prediction.predicted_total = 45.0

            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                    if prediction_type == PredictionType.WINNER:
                        prediction.win_probability = confidence
                    elif prediction_type == PredictionType.SPREAD:
                        prediction.spread_confidence = confidence
                    elif prediction_type == PredictionType.TOTAL:
                        prediction.total_confidence = confidence
                except ValueError:
                    # Default confidence
                    if prediction_type == PredictionType.WINNER:
                        prediction.win_probability = 0.6
                    elif prediction_type == PredictionType.SPREAD:
                        prediction.spread_confidence = 0.6
                    elif prediction_type == PredictionType.TOTAL:
                        prediction.total_confidence = 0.6

            elif line.startswith('KEY_FACTORS:'):
                factors_text = line.replace('KEY_FACTORS:', '').strip()
                prediction.key_factors = [f.strip() for f in factors_text.split(',')]

        # Add reasoning chain from LLM response
        prediction.reasoning_chain = [llm_text[:200] + "..." if len(llm_text) > 200 else llm_text]

        # Add memory information
        prediction.retrieved_memories_used = len(memory_result.retrieved_memories)

        return prediction

    async def _enforce_rate_limit(self):
        """Enforce rate limiting for API calls"""

        current_time = datetime.now()

        # Remove requests older than 1 minute
        self.last_request_times = [
            req_time for req_time in self.last_request_times
            if (current_time - req_time).total_seconds() < 60
        ]

        # Check if we're at the limit
        if len(self.last_request_times) >= self.requests_per_minute:
            # Calculate sleep time
            sleep_time = 60 - (current_time - self.last_request_times[0]).total_seconds()
            if sleep_time > 0:
                self.logger.info(f"⏱️ Rate limiting: sleeping {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)

        # Record this request
        self.last_request_times.append(current_time)

    def _build_expert_system_prompt(self, config: ExpertConfiguration) -> str:
        """Build system prompt for the expert's personality"""

        return f"""You are {config.name}, an NFL prediction expert with the following personality and approach:

PERSONALITY: {config.description}

ANALYTICAL FOCUS: You prioritize these factors in your analysis:
{self._format_analytical_focus(config.analytical_focus)}

CONFIDENCE STYLE: Your base confidence threshold is {config.confidence_threshold:.1%}. You tend to be {'more confident' if config.confidence_threshold > 0.6 else 'more cautious'} in your predictions.

DECISION MAKING: {config.decision_making_style}

Your job is to analyze NFL games and make predictions that reflect your unique analytical approach and personality. Always stay in character and provide reasoning that matches your expertise and style.

Respond in this EXACT format:
WINNER: [HOME or AWAY]
WIN_PROBABILITY: [0.15 to 0.85 as decimal]
CONFIDENCE: [0.05 to 0.95 as decimal]
REASONING:
1. [First key factor and analysis]
2. [Second key factor and analysis]
3. [Third key factor and analysis]
KEY_FACTORS: [comma-separated list of 3-5 key factors]"""

    def _format_analytical_focus(self, focus: Dict[str, float]) -> str:
        """Format analytical focus for prompt"""

        sorted_factors = sorted(focus.items(), key=lambda x: x[1], reverse=True)
        formatted = []

        for factor, weight in sorted_factors[:5]:  # Top 5 factors
            factor_name = factor.replace('_', ' ').title()
            importance = "Very High" if weight > 0.8 else "High" if weight > 0.6 else "Moderate" if weight > 0.4 else "Low"
            formatted.append(f"- {factor_name}: {importance} ({weight:.1%})")

        return '\n'.join(formatted)

    def _build_game_analysis_prompt(self, game_context: Dict[str, Any],
                                  memories: List[RetrievedMemory],
                                  prediction_type: PredictionType) -> str:
        """Build game analysis prompt"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        week = game_context.get('week', 'Unknown')
        season = game_context.get('season', 'Unknown')

        prompt = f"""Analyze this NFL game and make your prediction:

GAME: {away_team} @ {home_team}
SEASON: {season}, Week {week}
DATE: {game_context.get('game_date', 'Unknown')}

GAME CONTEXT:
"""

        # Add available context
        if game_context.get('weather'):
            weather = game_context['weather']
            prompt += f"Weather: {weather.get('temperature', 'Unknown')}°F"
            if weather.get('wind_speed'):
                prompt += f", Wind: {weather['wind_speed']} mph"
            prompt += "\n"

        if game_context.get('spread_line'):
            prompt += f"Spread: {home_team} {game_context['spread_line']:+.1f}\n"

        if game_context.get('total_line'):
            prompt += f"Total: {game_context['total_line']}\n"

        if game_context.get('division_game'):
            prompt += "Division Game: Yes\n"

        # Add relevant memories
        if memories:
            prompt += f"\nRELEVANT MEMORIES FROM YOUR PAST ANALYSIS:\n"
            for i, memory in enumerate(memories[:3], 1):  # Top 3 memories
                prompt += f"{i}. {memory.memory.content} (Age: {memory.decay_score.age_days} days)\n"

        prompt += f"\nProvide your analysis focusing on {prediction_type.value} prediction."

        return prompt

    async def _log_expert_memory_retrieval(self, expert_type: ExpertType, game_context: Dict[str, Any], memory_result: MemoryRetrievalResult):
        """Log detailed memory retrieval information for expert decision-making transparency"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')

        self.logger.info(f"🧠 MEMORY RETRIEVAL - {expert_type.value} for {away_team} @ {home_team}")
        self.logger.info(f"   📊 Retrieved {len(memory_result.retrieved_memories)} memories in {memory_result.retrieval_time_ms:.1f}ms")
        self.logger.info(f"   🔍 Evaluated {memory_result.total_candidates_evaluated} total candidates")

        if memory_result.retrieved_memories:
            self.logger.info(f"   📚 MEMORIES USED FOR CONTEXT:")
            for i, retrieved_memory in enumerate(memory_result.retrieved_memories[:5], 1):  # Top 5 memories
                memory = retrieved_memory.memory
                decay_score = retrieved_memory.decay_score

                # Determine memory source
                source_info = "Unknown source"
                if hasattr(memory, 'source_table'):
                    source_info = f"Supabase:{memory.source_table}"
                elif hasattr(memory, 'vector_id'):
                    source_info = f"Vector:{memory.vector_id}"
                elif hasattr(memory, 'neo4j_node'):
                    source_info = f"Neo4j:{memory.neo4j_node}"

                self.logger.info(f"      {i}. [{source_info}] {memory.memory_type}")
                self.logger.info(f"         Content: {memory.content[:100]}...")
                self.logger.info(f"         Relevance: {decay_score.final_weighted_score:.3f} (similarity: {decay_score.similarity_score:.3f}, age: {decay_score.age_days}d)")

                # Log what teams this memory relates to
                if hasattr(memory, 'game_context') and memory.game_context:
                    home_team = memory.game_context.get('home_team', '')
                    away_team = memory.game_context.get('away_team', '')
                    teams = f"{away_team} @ {home_team}" if home_team and away_team else 'General'
                    self.logger.info(f"         Teams: {teams}")
        else:
            self.logger.info(f"   ❌ No relevant memories found for this matchup")

        self.logger.info(f"   📝 Summary: {memory_result.retrieval_summary}")


async def test_prediction_generator():
    """Test the prediction generator"""

    print("Testing Prediction Generator")
    print("=" * 50)

    # Initialize all components
    config_manager = ExpertConfigurationManager()
    temporal_calculator = TemporalDecayCalculator(config_manager)
    memory_retrieval_system = MemoryRetrievalSystem(config_manager, temporal_calculator)
    prediction_generator = PredictionGenerator(config_manager, temporal_calculator, memory_retrieval_system)

    # Test game context
    test_game_context = {
        'home_team': 'KC',
        'away_team': 'DEN',
        'week': 12,
        'season': 2024,
        'weather': {
            'temperature': 28,
            'wind_speed': 18,
            'conditions': 'snow'
        },
        'division_game': True,
        'line_movement': {
            'opening': -7.0,
            'current': -4.5
        },
        'total_line': 42.5,
        'public_betting': {
            'home': 78,
            'away': 22
        },
        'momentum': {
            'home': 'hot_3_game_win_streak',
            'away': 'cold_2_losses'
        }
    }

    # Test ALL fifteen expert types for comprehensive validation
    test_experts = [
        ExpertType.CHAOS_THEORY_BELIEVER,
        ExpertType.CONSENSUS_FOLLOWER,
        ExpertType.CONSERVATIVE_ANALYZER,
        ExpertType.CONTRARIAN_REBEL,
        ExpertType.FUNDAMENTALIST_SCHOLAR,
        ExpertType.GUT_INSTINCT_EXPERT,
        ExpertType.MARKET_INEFFICIENCY_EXPLOITER,
        ExpertType.MOMENTUM_RIDER,
        ExpertType.POPULAR_NARRATIVE_FADER,
        ExpertType.RISK_TAKING_GAMBLER,
        ExpertType.SHARP_MONEY_FOLLOWER,
        ExpertType.STATISTICS_PURIST,
        ExpertType.TREND_REVERSAL_SPECIALIST,
        ExpertType.UNDERDOG_CHAMPION,
        ExpertType.VALUE_HUNTER
    ]

    print(f"Test Game: {test_game_context['away_team']} @ {test_game_context['home_team']}")
    print(f"Line: {test_game_context['home_team']} {test_game_context['line_movement']['current']}")
    print(f"Total: {test_game_context['total_line']}")
    print(f"Weather: {test_game_context['weather']['temperature']}°F, {test_game_context['weather']['wind_speed']} mph wind")
    print()

    for expert_type in test_experts:
        print(f"=== {expert_type.value.replace('_', ' ').title()} ===")

        predictions = await prediction_generator.generate_prediction(
            expert_type, test_game_context, [PredictionType.WINNER, PredictionType.TOTAL]
        )

        for prediction in predictions:
            print(f"\\n{prediction.prediction_type.value.title()} Prediction:")

            if prediction.prediction_type == PredictionType.WINNER:
                print(f"  Winner: {prediction.predicted_winner} ({prediction.win_probability:.1%})")
                print(f"  Confidence: {prediction.confidence_level:.1%}")
            elif prediction.prediction_type == PredictionType.TOTAL:
                print(f"  Total: {prediction.predicted_total}")
                print(f"  Confidence: {prediction.total_confidence:.1%}")

            print(f"  Key Factors: {', '.join(prediction.key_factors)}")
            print(f"  Memories Used: {prediction.retrieved_memories_used}")

            print("  Reasoning:")
            for reason in prediction.reasoning_chain:
                print(f"    {reason}")

        print()


    def _build_expert_system_prompt(self, config: ExpertConfiguration) -> str:
        """Build system prompt for the expert's personality"""

        return f"""You are {config.name}, an NFL prediction expert with the following personality and approach:

PERSONALITY: {config.description}

ANALYTICAL FOCUS: You prioritize these factors in your analysis:
{self._format_analytical_focus(config.analytical_focus)}

CONFIDENCE STYLE: Your base confidence threshold is {config.confidence_threshold:.1%}. You tend to be {'more confident' if config.confidence_threshold > 0.6 else 'more cautious'} in your predictions.

DECISION MAKING: {config.decision_making_style}

Your job is to analyze NFL games and make predictions that reflect your unique analytical approach and personality. Always stay in character and provide reasoning that matches your expertise and style.

Respond in this EXACT format:
WINNER: [HOME or AWAY]
WIN_PROBABILITY: [0.15 to 0.85 as decimal]
CONFIDENCE: [0.05 to 0.95 as decimal]
REASONING:
1. [First key factor and analysis]
2. [Second key factor and analysis]
3. [Third key factor and analysis]
KEY_FACTORS: [comma-separated list of 3-5 key factors]"""

    def _format_analytical_focus(self, focus: Dict[str, float]) -> str:
        """Format analytical focus for prompt"""

        sorted_factors = sorted(focus.items(), key=lambda x: x[1], reverse=True)
        formatted = []

        for factor, weight in sorted_factors[:5]:  # Top 5 factors
            factor_name = factor.replace('_', ' ').title()
            importance = "Very High" if weight > 0.8 else "High" if weight > 0.6 else "Moderate" if weight > 0.4 else "Low"
            formatted.append(f"- {factor_name}: {importance} ({weight:.1%})")

        return '\n'.join(formatted)

    def _build_game_analysis_prompt(self, game_context: Dict[str, Any],
                                  memories: List[RetrievedMemory],
                                  prediction_type: PredictionType) -> str:
        """Build game analysis prompt"""

        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        week = game_context.get('week', 'Unknown')
        season = game_context.get('season', 'Unknown')

        prompt = f"""Analyze this NFL game and make your prediction:

GAME: {away_team} @ {home_team}
SEASON: {season}, Week {week}
DATE: {game_context.get('game_date', 'Unknown')}

GAME CONTEXT:
"""

        # Add available context
        if game_context.get('weather'):
            weather = game_context['weather']
            prompt += f"Weather: {weather.get('temperature', 'Unknown')}°F"
            if weather.get('wind_speed'):
                prompt += f", Wind: {weather['wind_speed']} mph"
            prompt += "\n"

        if game_context.get('spread_line'):
            prompt += f"Spread: {home_team} {game_context['spread_line']:+.1f}\n"

        if game_context.get('total_line'):
            prompt += f"Total: {game_context['total_line']}\n"

        if game_context.get('division_game'):
            prompt += "Division Game: Yes\n"

        # Add relevant memories
        if memories:
            prompt += f"\nRELEVANT MEMORIES FROM YOUR PAST ANALYSIS:\n"
            for i, memory in enumerate(memories[:3], 1):  # Top 3 memories
                prompt += f"{i}. {memory.memory.content} (Age: {memory.decay_score.age_days} days)\n"

        prompt += f"\nProvide your analysis focusing on {prediction_type.value} prediction."

        return prompt

    async def _call_openrouter_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to OpenRouter"""

        # Rate limiting
        await self._enforce_rate_limit()

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        # Get model for this specific expert
        model = self._get_model_for_expert(expert_type)

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            response = requests.post(
                self.openrouter_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                raise ValueError("Invalid response format from OpenRouter")

        except Exception as e:
            self.logger.error(f"❌ OpenRouter API call failed: {e}")
            raise

    def _parse_llm_response(self, llm_text: str, expert_type: ExpertType,
                          prediction_type: PredictionType,
                          memory_result: MemoryRetrievalResult) -> GamePrediction:
        """Parse LLM response into GamePrediction"""

        try:
            lines = llm_text.strip().split('\n')

            # Initialize defaults
            predicted_winner = None
            win_probability = 0.5
            confidence_level = 0.5
            reasoning_chain = []
            key_factors = []

            # Parse structured response
            current_section = None

            for line in lines:
                line = line.strip()

                if line.startswith('WINNER:'):
                    winner_text = line.replace('WINNER:', '').strip().upper()
                    predicted_winner = winner_text.lower()

                elif line.startswith('WIN_PROBABILITY:'):
                    try:
                        prob_text = line.replace('WIN_PROBABILITY:', '').strip()
                        win_probability = float(prob_text)
                        win_probability = max(0.15, min(0.85, win_probability))
                    except ValueError:
                        pass

                elif line.startswith('CONFIDENCE:'):
                    try:
                        conf_text = line.replace('CONFIDENCE:', '').strip()
                        confidence_level = float(conf_text)
                        confidence_level = max(0.05, min(0.95, confidence_level))
                    except ValueError:
                        pass

                elif line.startswith('REASONING:'):
                    current_section = 'reasoning'

                elif line.startswith('KEY_FACTORS:'):
                    factors_text = line.replace('KEY_FACTORS:', '').strip()
                    key_factors = [f.strip() for f in factors_text.split(',') if f.strip()]

                elif current_section == 'reasoning' and line and not line.startswith('KEY_FACTORS:'):
                    clean_line = line.lstrip('0123456789. -').strip()
                    if clean_line:
                        reasoning_chain.append(clean_line)

            # Create GamePrediction
            prediction = GamePrediction(
                expert_type=expert_type,
                prediction_type=prediction_type,
                predicted_winner=predicted_winner,
                win_probability=win_probability,
                confidence_level=confidence_level,
                reasoning_chain=reasoning_chain,
                key_factors=key_factors,
                retrieved_memories_used=len(memory_result.retrieved_memories),
                prediction_timestamp=datetime.now()
            )

            return prediction

        except Exception as e:
            self.logger.error(f"❌ Failed to parse LLM response: {e}")
            # Return fallback prediction
            return GamePrediction(
                expert_type=expert_type,
                prediction_type=prediction_type,
                predicted_winner='home',
                win_probability=0.55,
                confidence_level=0.5,
                reasoning_chain=[f"Analysis by {expert_type.value} (LLM parsing failed)"],
                key_factors=["team_analysis"],
                retrieved_memories_used=len(memory_result.retrieved_memories),
                prediction_timestamp=datetime.now()
            )

    async def _enforce_rate_limit(self):
        """Enforce rate limiting for API calls"""

        current_time = datetime.now()

        # Remove requests older than 1 minute
        self.last_request_times = [
            t for t in self.last_request_times
            if (current_time - t).total_seconds() < 60
        ]

        # Check if we're at the limit
        if len(self.last_request_times) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_times[0]).total_seconds()
            if sleep_time > 0:
                self.logger.info(f"⏱️ Rate limiting: sleeping {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)

        # Record this request
        self.last_request_times.append(current_time)

    def _initialize_expert_models(self) -> Dict[ExpertType, str]:
        """Initialize model assignments for each expert type"""

        # Default model assignment - can be overridden by environment variables
        default_models = {
            # Analytical experts - use Claude Sonnet 4.5 for best reasoning
            ExpertType.FUNDAMENTALIST_SCHOLAR: "anthropic/claude-sonnet-4.5",
            ExpertType.CONSERVATIVE_ANALYZER: "anthropic/claude-sonnet-4.5",
            ExpertType.STATISTICS_PURIST: "anthropic/claude-sonnet-4.5",

            # Personality-driven experts - mix of premium and free models
            ExpertType.CONTRARIAN_REBEL: "x-ai/grok-4-fast:free",
            ExpertType.CHAOS_THEORY_BELIEVER: "meta-llama/llama-3.1-8b-instruct:free",
            ExpertType.MOMENTUM_RIDER: "deepseek/deepseek-chat-v3.1:free",

            # Specialized experts - use reasoning models
            # Removed WEATHER_SPECIALIST reference - expert type no longer exists
            ExpertType.UNDERDOG_CHAMPION: "x-ai/grok-4-fast:free",
            ExpertType.RISK_TAKING_GAMBLER: "meta-llama/llama-3.1-8b-instruct:free",

            # Market experts - use Claude for complex market analysis
            ExpertType.MARKET_INEFFICIENCY_EXPLOITER: "anthropic/claude-sonnet-4.5",
            ExpertType.SHARP_MONEY_FOLLOWER: "deepseek/deepseek-chat-v3.1:free",
            ExpertType.CONSENSUS_FOLLOWER: "x-ai/grok-4-fast:free",

            # Trend experts - mix of models for diverse perspectives
            ExpertType.TREND_REVERSAL_SPECIALIST: "anthropic/claude-sonnet-4.5",
            ExpertType.POPULAR_NARRATIVE_FADER: "x-ai/grok-4-fast:free",
            ExpertType.VALUE_HUNTER: "qwen/qwen-2.5-7b-instruct:free"
        }

        # Allow environment variable overrides for specific experts
        expert_models = {}
        for expert_type in ExpertType:
            env_var = f"LLM_MODEL_{expert_type.value.upper()}"
            model = os.getenv(env_var, default_models.get(expert_type, "x-ai/grok-4-fast:free"))
            expert_models[expert_type] = model

        return expert_models

    def _get_model_for_expert(self, expert_type: ExpertType) -> str:
        """Get the assigned model for a specific expert"""
        return self.expert_models.get(expert_type, "x-ai/grok-4-fast:free")
