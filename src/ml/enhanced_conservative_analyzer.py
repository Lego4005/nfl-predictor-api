#!/usr/bin/env python3
"""
Enhanced ConservativeAnalyzer for Self-Heng AI System

This implementation integrates:
1. Local 20B parameter LLM for reasoning
2. Episodic memory retrieval and application
3. Detailed reasoning chains for each prediction
4. Comprehensive logging system

Requirements: 7.1, 7.2, 6.1, 6.2, 2.3, 6.3, 6.4, 9.1, 9.2, 9.3
"""

import logging
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..personality_driven_experts import PersonalityDrivenExpert, PersonalityProfile, PersonalityTrait
from ..services.local_llm_service import LocalLLMService
from ..validation.data_validator import validate_and_fix_universal_data

logger = logging.getLogger(__name__)


@dataclass
class PredictionMetrics:
    """Metrics for tracking prediction performance"""
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_rate: float = 0.0
    avg_confidence: float = 0.0
    memory_usage_count: int = 0
    reasoning_chain_length: int = 0
    llm_response_time: float = 0.0


@dataclass
class ReasoningChain:
    """Structured reasoning chain for predictions"""
    expert_id: str
    game_context: Dict[str, Any]
    memories_consulted: List[Dict[str, Any]]
    reasoning_steps: List[str]
    confidence_factors: List[str]
    uncertainty_factors: List[str]
    final_prediction: Dict[str, Any]
    timestamp: str


class EnhancedConservativeAnalyzer(PersonalityDrivenExpert):
    """
    Enhanced Conservative Analyzer with LLM integration and episodic memory

    Features:
    - Local 20B parameter LLM for detailed reasoning
    - Episodic memory retrieval and application
    - Comprehensive reasoning chain generation
    - Performance tracking and validation
    """

    def __init__(self, memory_service=None, llm_service=None):
        # Initialize personality profile for conservative analysis
        personality = PersonalityProfile(
            traits={
                'risk_tolerance': PersonalityTrait('risk_tolerance', 0.2, 0.8, 0.9),
                'analytics_trust': PersonalityTrait('analytics_trust', 0.9, 0.7, 0.8),
                'contrarian_tendency': PersonalityTrait('contrarian_tendency', 0.3, 0.6, 0.6),
                'recent_bias': PersonalityTrait('recent_bias', 0.2, 0.5, 0.7),
                'confidence_level': PersonalityTrait('confidence_level', 0.4, 0.8, 0.7),
                'optimism': PersonalityTrait('optimism', 0.3, 0.6, 0.6),
                'chaos_comfort': PersonalityTrait('chaos_comfort', 0.1, 0.9, 0.8),
                'market_trust': PersonalityTrait('market_trust', 0.8, 0.7, 0.7),
                'authority_respect': PersonalityTrait('authority_respect', 0.8, 0.8, 0.6)
            },
            decision_style="analytical",
            confidence_level=0.4,
            learning_rate=0.05
        )

        super().__init__(
            expert_id="enhanced_conservative_analyzer",
            name="Enhanced Conservative Analyzer",
            personality_profile=personality,
            memory_service=memory_service
        )

        # Enhanced services
        self.llm_service = llm_service or LocalLLMService()
        self.metrics = PredictionMetrics()
        self.reasoning_chains: List[ReasoningChain] = []

        # Logging setup
        self.prediction_logger = logging.getLogger(f"{__name__}.predictions")
        self.memory_logger = logging.getLogger(f"{__name__}.memory")
        self.performance_logger = logging.getLogger(f"{__name__}.performance")

        logger.info(f"✅ {self.name} initialized with LLM and memory integration")

    def make_enhanced_prediction(self, universal_data) -> Dict[str, Any]:
        """
        Make enhanced prediction with LLM reasoning and memory integration

        This is the main entry point for the enhanced prediction system.
        """
        start_time = time.perf_counter()

        try:
            # Step 1: Validate and fix input data
            validation_result = validate_and_fix_universal_data(universal_data)
            if validation_result.fixes_applied:
                logger.info(f"🔧 Applied {len(validation_result.fixes_applied)} data fixes")

            # Step 2: Retrieve relevant episodic memories
            memories = self._retrieve_relevant_memories(universal_data)
            self.memory_logger.info(f"Retrieved {len(memories)} relevant memories")

            # Step 3: Generate LLM-powered reasoning
            reasoning_result = self._generate_llm_reasoning(universal_data, memories)

            # Step 4: Create structured prediction
            prediction = self._create_structured_prediction(
                universal_data, memories, reasoning_result
            )

            # Step 5: Log reasoning chain
            reasoning_chain = self._create_reasoning_chain(
                universal_data, memories, reasoning_result, prediction
            )
            self.reasoning_chains.append(reasoning_chain)

            # Step 6: Update metrics
            self._update_metrics(prediction, time.perf_counter() - start_time)

            # Step 7: Log prediction details
            self._log_prediction_details(prediction, reasoning_chain)

            return prediction

        except Exception as e:
            logger.error(f"❌ Error in enhanced prediction: {e}")
            # Fallback to deterministic prediction
            return self._create_fallback_prediction(universal_data)

    def _retrieve_relevant_memories(self, universal_data) -> List[Dict[str, Any]]:
        """Retrieve relevant episodic memories for the current game context"""
        if not self.memory_service:
            return []

        try:
            game_context = {
                'home_team': universal_data.home_team,
                'away_team': universal_data.away_team,
                'weather': getattr(universal_data, 'weather', {}),
                'injuries': getattr(universal_data, 'injuries', {}),
                'line_movement': getattr(universal_data, 'line_movement', {})
            }

            # Use sync wrapper for memory retrieval
            memories = self.retrieve_relevant_memories(game_context)

            self.memory_logger.info(f"🧠 Retrieved {len(memories)} memories for context")
            for i, memory in enumerate(memories[:3]):  # Log first 3
                self.memory_logger.debug(f"  Memory {i+1}: {memory.get('memory_type', 'unknown')}")

            return memories

        except Exception as e:
            self.memory_logger.warning(f"⚠️ Error retrieving memories: {e}")
            return []

    def _generate_llm_reasoning(self, universal_data, memories: List[Dict]) -> Dict[str, Any]:
        """Generate detailed reasoning using local LLM"""
        if not self.llm_service:
            return self._generate_deterministic_reasoning(universal_data)

        try:
            # Build simplified prompt for LLM reasoning
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(universal_data, memories)

            logger.info(f"🤖 Generating LLM reasoning for {universal_data.away_team} @ {universal_data.home_team}")

            # Make synchronous LLM call (we'll handle async later)
            response = self._make_sync_llm_call(system_prompt, user_prompt)

            # Parse LLM response
            reasoning_result = self._parse_llm_response(response)

            logger.info(f"✅ LLM reasoning generated in {response.response_time:.2f}s")
            return reasoning_result

        except Exception as e:
            logger.warning(f"⚠️ LLM reasoning failed, using deterministic: {e}")
            return self._generate_deterministic_reasoning(universal_data)

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return f"""You are {self.name}, a conservative NFL prediction expert.

Your personality:
- Risk tolerance: Very Low (20%) - You avoid uncertainty and prefer safe approaches
- Analytics trust: Very High (90%) - You heavily weight statistical data
- Confidence level: Moderate-Low (40%) - You express measured confidence

Provide a brief analysis (2-3 sentences) and make these predictions:
1. Winner (home/away)
2. Confidence (0-100)
3. Spread prediction (positive = home favored)
4. Total points prediction

Respond in JSON format:
{{
    "reasoning": "Your 2-3 sentence analysis",
    "winner": "home" or "away",
    "confidence": 65,
    "spread": -3.5,
    "total": 42.5
}}"""

    def _build_user_prompt(self, universal_data, memories: List[Dict]) -> str:
        """Build user prompt with game data and memories"""
        prompt = f"""Analyze this NFL matchup:

GAME: {universal_data.away_team} @ {universal_data.home_team}

TEAM STATS:
Home ({universal_data.home_team}):
- Record: {getattr(universal_data.team_stats.get('home', {}), 'wins', 0)}-{getattr(universal_data.team_stats.get('home', {}), 'losses', 0)}
- Points/Game: {getattr(universal_data.team_stats.get('home', {}), 'points_per_game', 'N/A')}
- Points Allowed: {getattr(universal_data.team_stats.get('home', {}), 'points_allowed_per_game', 'N/A')}

Away ({universal_data.away_team}):
- Record: {getattr(universal_data.team_stats.get('away', {}), 'wins', 0)}-{getattr(universal_data.team_stats.get('away', {}), 'losses', 0)}
- Points/Game: {getattr(universal_data.team_stats.get('away', {}), 'points_per_game', 'N/A')}
- Points Allowed: {getattr(universal_data.team_stats.get('away', {}), 'points_allowed_per_game', 'N/A')}

WEATHER: {getattr(universal_data, 'weather', {}).get('conditions', 'Clear')}, {getattr(universal_data, 'weather', {}).get('temperature', 70)}°F

BETTING LINE: {getattr(universal_data, 'line_movement', {}).get('current_line', 'N/A')}"""

        if memories:
            prompt += f"\n\nRELEVANT MEMORIES ({len(memories)} found):"
            for i, memory in enumerate(memories[:2]):  # Include top 2 memories
                prompt += f"\n{i+1}. {memory.get('prediction_summary', 'Previous prediction')}"

        prompt += "\n\nProvide your conservative analysis and predictions in JSON format."
        return prompt

    def _make_sync_llm_call(self, system_prompt: str, user_prompt: str):
        """Make synchronous LLM call (wrapper for async)"""
        try:
            # Load JSON schema for structured output
            json_schema = {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Brief 2-3 sentence analysis of the matchup",
                        "minLength": 20,
                        "maxLength": 500
                    },
                    "winner": {
                        "type": "string",
                        "description": "Predicted winner of the game",
                        "enum": ["home", "away"]
                    },
                    "confidence": {
                        "type": "integer",
                        "description": "Confidence level in the prediction (0-100)",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "spread": {
                        "type": "number",
                        "description": "Point spread prediction (negative = home favored, positive = away favored)",
                        "minimum": -50.0,
                        "maximum": 50.0
                    },
                    "total": {
                        "type": "number",
                        "description": "Total points prediction for the game",
                        "minimum": 0.0,
                        "maximum": 100.0
                    }
                },
                "required": ["reasoning", "winner", "confidence", "spread", "total"],
                "additionalProperties": False
            }

            # For now, use a simple synchronous approach
            # In production, this would be properly async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    self.llm_service.generate_completion(
                        system_message=system_prompt,
                        user_message=user_prompt,
                        temperature=0.3,  # Conservative temperature
                        max_tokens=500,
                        json_schema=json_schema  # Force structured output
                    )
                )
                return response
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"❌ Sync LLM call failed: {e}")
            raise

    def _parse_llm_response(self, response) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Try to parse as JSON
            content = response.content.strip()

            # Handle potential markdown formatting
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()

            parsed = json.loads(content)

            # Validate required fields
            required_fields = ['reasoning', 'winner', 'confidence', 'spread', 'total']
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")

            return {
                'reasoning': parsed['reasoning'],
                'winner': parsed['winner'],
                'confidence': max(0, min(100, int(parsed['confidence']))),
                'spread': float(parsed['spread']),
                'total': float(parsed['total']),
                'llm_powered': True
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"⚠️ Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response.content[:200]}...")

            # Extract basic info from text if possible
            return self._extract_from_text_response(response.content)

    def _extract_from_text_response(self, content: str) -> Dict[str, Any]:
        """Extract prediction info from text response as fallback"""
        # Simple text parsing fallback
        reasoning = content[:200] + "..." if len(content) > 200 else content

        # Default conservative predictions
        return {
            'reasoning': reasoning,
            'winner': 'home',  # Conservative: favor home team
            'confidence': 45,   # Low confidence
            'spread': -2.5,     # Small home advantage
            'total': 43.0,      # Conservative total
            'llm_powered': False
        }

    def _generate_deterministic_reasoning(self, universal_data) -> Dict[str, Any]:
        """Generate deterministic reasoning as fallback"""
        # Conservative deterministic analysis
        home_stats = universal_data.team_stats.get('home', {})
        away_stats = universal_data.team_stats.get('away', {})

        home_ppg = home_stats.get('points_per_game', 22)
        away_ppg = away_stats.get('points_per_game', 22)

        # Conservative logic: favor home team slightly, low totals
        winner = 'home' if home_ppg >= away_ppg else 'away'
        confidence = 50  # Neutral confidence
        spread = 2.5 if winner == 'home' else -2.5
        total = min(45, (home_ppg + away_ppg) * 0.9)  # Conservative total

        return {
            'reasoning': f"Conservative analysis based on scoring averages. {winner.title()} team has slight statistical edge.",
            'winner': winner,
            'confidence': confidence,
            'spread': spread,
            'total': total,
            'llm_powered': False
        }

    def _create_structured_prediction(self, universal_data, memories: List[Dict],
                                    reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create final structured prediction"""
        return {
            'expert_name': self.name,
            'expert_id': self.expert_id,
            'game_context': {
                'home_team': universal_data.home_team,
                'away_team': universal_data.away_team,
                'game_date': getattr(universal_data, 'game_date', None),
                'week': getattr(universal_data, 'week', None),
                'season': getattr(universal_data, 'season', None)
            },
            'winner_prediction': reasoning_result['winner'],
            'winner_confidence': reasoning_result['confidence'] / 100.0,
            'spread_prediction': reasoning_result['spread'],
            'total_prediction': reasoning_result['total'],
            'reasoning_discussion': reasoning_result['reasoning'],
            'llm_powered': reasoning_result.get('llm_powered', False),
            'memories_consulted': len(memories),
            'personality_profile': {
                trait_name: trait.value for trait_name, trait in self.personality.traits.items()
            },
            'timestamp': datetime.now().isoformat()
        }

    def _create_reasoning_chain(self, universal_data, memories: List[Dict],
                              reasoning_result: Dict[str, Any], prediction: Dict[str, Any]) -> ReasoningChain:
        """Create detailed reasoning chain for logging"""
        return ReasoningChain(
            expert_id=self.expert_id,
            game_context={
                'matchup': f"{universal_data.away_team} @ {universal_data.home_team}",
                'weather': getattr(universal_data, 'weather', {}),
                'betting_line': getattr(universal_data, 'line_movement', {})
            },
            memories_consulted=memories,
            reasoning_steps=[reasoning_result['reasoning']],
            confidence_factors=[f"Statistical analysis, {len(memories)} memories consulted"],
            uncertainty_factors=["Limited recent data", "Weather variability"],
            final_prediction=prediction,
            timestamp=datetime.now().isoformat()
        )

    def _create_fallback_prediction(self, universal_data) -> Dict[str, Any]:
        """Create safe fallback prediction when everything fails"""
        return {
            'expert_name': self.name,
            'expert_id': self.expert_id,
            'winner_prediction': 'home',
            'winner_confidence': 0.5,
            'spread_prediction': 0.0,
            'total_prediction': 45.0,
            'reasoning_discussion': 'Fallback prediction due to system error',
            'llm_powered': False,
            'memories_consulted': 0,
            'error_fallback': True,
            'timestamp': datetime.now().isoformat()
        }

    def _update_metrics(self, prediction: Dict[str, Any], processing_time: float):
        """Update performance metrics"""
        self.metrics.total_predictions += 1
        self.metrics.avg_confidence = (
            (self.metrics.avg_confidence * (self.metrics.total_predictions - 1) +
             prediction['winner_confidence']) / self.metrics.total_predictions
        )
        self.metrics.memory_usage_count += prediction.get('memories_consulted', 0)
        self.metrics.llm_response_time = processing_time

        self.performance_logger.info(f"📊 Prediction #{self.metrics.total_predictions} completed in {processing_time:.2f}s")

    def _log_prediction_details(self, prediction: Dict[str, Any], reasoning_chain: ReasoningChain):
        """Log detailed prediction information"""
        self.prediction_logger.info(f"🎯 PREDICTION: {prediction['game_context']['away_team']} @ {prediction['game_context']['home_team']}")
        self.prediction_logger.info(f"   Winner: {prediction['winner_prediction']} (confidence: {prediction['winner_confidence']:.1%})")
        self.prediction_logger.info(f"   Spread: {prediction['spread_prediction']:+.1f}")
        self.prediction_logger.info(f"   Total: {prediction['total_prediction']:.1f}")
        self.prediction_logger.info(f"   LLM Powered: {prediction.get('llm_powered', False)}")
        self.prediction_logger.info(f"   Memories Used: {prediction.get('memories_consulted', 0)}")
        self.prediction_logger.debug(f"   Reasoning: {prediction['reasoning_discussion']}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'total_predictions': self.metrics.total_predictions,
            'accuracy_rate': self.metrics.accuracy_rate,
            'avg_confidence': self.metrics.avg_confidence,
            'memory_usage_rate': self.metrics.memory_usage_count / max(1, self.metrics.total_predictions),
            'avg_processing_time': self.metrics.llm_response_time,
            'reasoning_chains_stored': len(self.reasoning_chains)
        }

    def validate_prediction_accuracy(self, prediction: Dict[str, Any], actual_outcome: Dict[str, Any]) -> bool:
        """Validate prediction accuracy against actual outcome"""
        try:
            predicted_winner = prediction.get('winner_prediction')
            actual_winner = actual_outcome.get('winner')

            is_correct = predicted_winner == actual_winner

            if is_correct:
                self.metrics.correct_predictions += 1

            self.metrics.accuracy_rate = self.metrics.correct_predictions / self.metrics.total_predictions

            self.performance_logger.info(f"📈 Prediction accuracy: {self.metrics.accuracy_rate:.1%} ({self.metrics.correct_predictions}/{self.metrics.total_predictions})")

            return is_correct

        except Exception as e:
            logger.error(f"❌ Error validating prediction accuracy: {e}")
            return False

    def process_through_personality_lens(self, universal_data) -> Dict[str, float]:
        """Conservative processing: Emphasizes proven patterns, avoids uncertainty"""
        weights = {}

        # Heavily weight historical data and proven metrics
        weights['historical_emphasis'] = 0.9
        weights['uncertainty_avoidance'] = 0.8
        weights['proven_patterns_only'] = 0.85

        # De-emphasize volatile factors
        weights['weather_discount'] = 0.3  # "Weather is unpredictable"
        weights['news_discount'] = 0.4     # "News is often hype"
        weights['market_trust'] = 0.8      # "Market reflects consensus wisdom"

        return weights


# Factory function for easy instantiation
def create_enhanced_conservative_analyzer(memory_service=None, llm_service=None) -> EnhancedConservativeAnalyzer:
    """Create an enhanced conservative analyzer with all services"""
    if llm_service is None:
        llm_service = LocalLLMService()

    return EnhancedConservativeAnalyzer(
        memory_service=memory_service,
        llm_service=llm_service
    )
