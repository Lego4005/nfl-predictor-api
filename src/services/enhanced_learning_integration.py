"""
Enhanced Learning System Integration

Integrates the comprehensive NFL analytics with the expert learning systems:
- Reasoning Chain Logger with enhanced game context
- Belief Revision Service with detailed performance metrics
- Episodic Memory Manager with rich game experiences
- Expert prediction verification with comprehensive accuracy

This service coordinates between the enhanced data pipeline and the learning systems
to provide rich context for expert improvement and adaptation.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics
from decimal import Decimal

from .enhanced_data_pipeline import EnhancedDataPipeline
from .comprehensive_verification_service import ComprehensiveVerificationService, ComprehensiveAccuracy
from .enhanced_data_storage import EnhancedDataStorage

# Import learning system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml'))

try:
    from reasoning_chain_logger import ReasoningChainLogger, ReasoningFactor, ConfidenceBreakdown
    from belief_revision_service import BeliefRevisionService
    from episodic_memory_manager import EpisodicMemoryManager, GameExperience, EmotionalEncoding
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import learning system components: {e}")
    # Create placeholder classes for development
    class ReasoningChainLogger:
        def __init__(self, *args, **kwargs): pass
        async def log_reasoning_chain(self, *args, **kwargs): return "placeholder"
        async def analyze_factor_success_rates(self, *args, **kwargs): return {}

    class BeliefRevisionService:
        def __init__(self, *args, **kwargs): pass
        async def trigger_belief_revision(self, *args, **kwargs): return {}
        async def calculate_revision_impact(self, *args, **kwargs): return {}

    class EpisodicMemoryManager:
        def __init__(self, *args, **kwargs): pass
        async def store_game_experience(self, *args, **kwargs): return "placeholder"
        async def extract_lessons(self, *args, **kwargs): return []
        async def get_similar_experiences(self, *args, **kwargs): return []

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedLearningIntegration:
    """Integrates enhanced NFL analytics with expert learning systems"""

    def __init__(self, database_url: str, sportsdata_api_key: str):
        # Initialize core components
        self.storage = EnhancedDataStorage(database_url)
        self.pipeline = EnhancedDataPipeline(sportsdata_api_key, database_url)

        # Initialize learning system components
        self.reasoning_logger = ReasoningChainLogger(database_url)
        self.belief_revision = BeliefRevisionService(database_url)
        self.episodic_memory = EpisodicMemoryManager(database_url)

        # Initialize verification service
        self.verification_service = None  # Will be set after storage initialization

        self.initialized = False

    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize storage and pipeline
            await self.storage.initialize()
            await self.pipeline.initialize()

            # Initialize verification service
            self.verification_service = ComprehensiveVerificationService(self.storage)

            # Initialize learning components (if they have async init)
            if hasattr(self.reasoning_logger, 'initialize'):
                await self.reasoning_logger.initialize()
            if hasattr(self.belief_revision, 'initialize'):
                await self.belief_revision.initialize()
            if hasattr(self.episodic_memory, 'initialize'):
                await self.episodic_memory.initialize()

            self.initialized = True
            logger.info("Enhanced learning integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize enhanced learning integration: {e}")
            raise

    async def close(self):
        """Close all resources"""
        try:
            if self.pipeline:
                await self.pipeline.close()
            if self.storage:
                await self.storage.close()
            logger.info("Enhanced learning integration closed")
        except Exception as e:
            logger.error(f"Error closing resources: {e}")

    async def process_game_learning_cycle(self, game_id: str, expert_predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Complete learning cycle for a game using enhanced analytics"""
        if not self.initialized:
            await self.initialize()

        logger.info(f"Processing enhanced learning cycle for game {game_id}")

        cycle_result = {
            "game_id": game_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "experts_processed": 0,
            "reasoning_chains_logged": 0,
            "belief_revisions_triggered": 0,
            "episodic_memories_created": 0,
            "learning_insights": [],
            "success": False,
            "errors": []
        }

        try:
            # Step 1: Ensure enhanced game data is available
            await self._ensure_enhanced_game_data(game_id)

            # Step 2: Verify expert predictions with comprehensive analytics
            verification_results = await self.verification_service.verify_all_expert_predictions(
                game_id, expert_predictions
            )

            if not verification_results:
                cycle_result["errors"].append("No verification results obtained")
                return cycle_result

            # Step 3: Process each expert's learning cycle
            for expert_id, accuracy in verification_results.items():
                try:
                    expert_result = await self._process_expert_learning_cycle(
                        expert_id, game_id, expert_predictions.get(expert_id, {}), accuracy
                    )

                    # Update cycle results
                    if expert_result["reasoning_chain_logged"]:
                        cycle_result["reasoning_chains_logged"] += 1
                    if expert_result["belief_revision_triggered"]:
                        cycle_result["belief_revisions_triggered"] += 1
                    if expert_result["episodic_memory_created"]:
                        cycle_result["episodic_memories_created"] += 1

                    cycle_result["learning_insights"].extend(expert_result.get("insights", []))
                    cycle_result["experts_processed"] += 1

                except Exception as e:
                    error_msg = f"Error processing expert {expert_id}: {e}"
                    logger.error(error_msg)
                    cycle_result["errors"].append(error_msg)

            # Step 4: Generate cross-expert learning insights
            cross_expert_insights = await self._generate_cross_expert_insights(
                game_id, verification_results
            )
            cycle_result["learning_insights"].extend(cross_expert_insights)

            # Step 5: Update expert models and patterns
            await self._update_expert_models(verification_results)

            cycle_result["success"] = len(cycle_result["errors"]) == 0
            logger.info(f"Completed enhanced learning cycle for {cycle_result['experts_processed']} experts")

        except Exception as e:
            error_msg = f"Error in learning cycle: {e}"
            logger.error(error_msg)
            cycle_result["errors"].append(error_msg)

        cycle_result["end_time"] = datetime.now(timezone.utc).isoformat()
        return cycle_result

    async def _ensure_enhanced_game_data(self, game_id: str):
        """Ensure enhanced game data is available for learning"""
        try:
            # Check if we have comprehensive data for this game
            game_data = await self.storage.get_game_verification_data(game_id)

            if not game_data or not game_data.get("game_data"):
                logger.warning(f"No enhanced data found for game {game_id}, attempting to fetch...")

                # Try to determine season/week from game_id or fetch recent data
                # For now, fetch current week data
                season = 2024
                week = 18

                pipeline_result = await self.pipeline.process_week_data(season, week, include_detailed=True)

                if not pipeline_result["success"]:
                    raise Exception(f"Failed to fetch enhanced data: {pipeline_result.get('errors', [])}")

        except Exception as e:
            logger.error(f"Error ensuring enhanced game data: {e}")
            raise

    async def _process_expert_learning_cycle(self, expert_id: str, game_id: str,
                                          predictions: Dict[str, Any],
                                          accuracy: ComprehensiveAccuracy) -> Dict[str, Any]:
        """Process learning cycle for a single expert"""
        logger.info(f"Processing learning cycle for expert {expert_id}")

        result = {
            "expert_id": expert_id,
            "reasoning_chain_logged": False,
            "belief_revision_triggered": False,
            "episodic_memory_created": False,
            "insights": [],
            "errors": []
        }

        try:
            # Step 1: Enhanced reasoning chain logging with rich context
            reasoning_factors = await self._extract_enhanced_reasoning_factors(
                expert_id, game_id, predictions, accuracy
            )

            if reasoning_factors:
                reasoning_chain_id = await self.reasoning_logger.log_reasoning_chain(
                    expert_id=expert_id,
                    game_id=game_id,
                    prediction_type="comprehensive_game_analysis",
                    factors=reasoning_factors,
                    confidence_breakdown=self._create_enhanced_confidence_breakdown(accuracy),
                    final_prediction=predictions,
                    reasoning_time_seconds=0,  # Would track actual time in production
                    context_data=await self._get_enhanced_context_data(game_id)
                )
                result["reasoning_chain_logged"] = True
                logger.info(f"Logged enhanced reasoning chain {reasoning_chain_id} for expert {expert_id}")

            # Step 2: Enhanced belief revision with detailed performance metrics
            belief_revision_result = await self._trigger_enhanced_belief_revision(
                expert_id, game_id, accuracy, reasoning_factors
            )

            if belief_revision_result.get("revision_triggered"):
                result["belief_revision_triggered"] = True
                result["insights"].extend(belief_revision_result.get("insights", []))

            # Step 3: Enhanced episodic memory with rich game experience
            episodic_result = await self._create_enhanced_episodic_memory(
                expert_id, game_id, predictions, accuracy
            )

            if episodic_result.get("memory_created"):
                result["episodic_memory_created"] = True
                result["insights"].extend(episodic_result.get("insights", []))

        except Exception as e:
            error_msg = f"Error in expert learning cycle: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    async def _extract_enhanced_reasoning_factors(self, expert_id: str, game_id: str,
                                                predictions: Dict[str, Any],
                                                accuracy: ComprehensiveAccuracy) -> List[ReasoningFactor]:
        """Extract reasoning factors with enhanced game analytics"""
        factors = []

        try:
            # Get comprehensive game data
            game_data = await self.storage.get_game_verification_data(game_id)
            enhanced_game = game_data.get("game_data", {})

            # Weather factors
            if enhanced_game.get("weather_condition"):
                weather_factor = ReasoningFactor(
                    factor="weather_impact",
                    value=f"{enhanced_game.get('weather_condition')} at {enhanced_game.get('weather_temperature')}°F",
                    weight=0.3,
                    confidence=0.8,
                    source="enhanced_game_data"
                )
                factors.append(weather_factor)

            # Team performance factors from enhanced stats
            if enhanced_game.get("home_total_yards") and enhanced_game.get("away_total_yards"):
                yards_differential = enhanced_game["home_total_yards"] - enhanced_game["away_total_yards"]
                performance_factor = ReasoningFactor(
                    factor="total_yards_differential",
                    value=f"Home team {'+' if yards_differential > 0 else ''}{yards_differential} yards",
                    weight=0.6,
                    confidence=0.9,
                    source="enhanced_team_stats"
                )
                factors.append(performance_factor)

            # Third down efficiency
            if all(enhanced_game.get(k) for k in ["home_third_down_attempts", "home_third_down_conversions",
                                                 "away_third_down_attempts", "away_third_down_conversions"]):
                home_third_down_pct = enhanced_game["home_third_down_conversions"] / enhanced_game["home_third_down_attempts"]
                away_third_down_pct = enhanced_game["away_third_down_conversions"] / enhanced_game["away_third_down_attempts"]

                efficiency_factor = ReasoningFactor(
                    factor="third_down_efficiency",
                    value=f"Home: {home_third_down_pct:.1%}, Away: {away_third_down_pct:.1%}",
                    weight=0.7,
                    confidence=0.85,
                    source="enhanced_efficiency_metrics"
                )
                factors.append(efficiency_factor)

            # Coaching decisions analysis
            coaching_decisions = game_data.get("coaching_decisions", [])
            if coaching_decisions:
                home_team = enhanced_game.get("home_team")
                away_team = enhanced_game.get("away_team")

                home_decisions = [d for d in coaching_decisions if d.get("team") == home_team]
                away_decisions = [d for d in coaching_decisions if d.get("team") == away_team]

                if home_decisions and away_decisions:
                    home_quality = statistics.mean([d.get("decision_quality_score", 0) for d in home_decisions])
                    away_quality = statistics.mean([d.get("decision_quality_score", 0) for d in away_decisions])

                    coaching_factor = ReasoningFactor(
                        factor="coaching_decision_quality",
                        value=f"{home_team}: {home_quality:.2f}, {away_team}: {away_quality:.2f}",
                        weight=0.5,
                        confidence=0.7,
                        source="coaching_decisions_analysis"
                    )
                    factors.append(coaching_factor)

            # Special teams performance
            special_teams = game_data.get("special_teams", [])
            if special_teams:
                for st_data in special_teams:
                    team = st_data.get("team")
                    st_score = st_data.get("special_teams_score", 0) or 0

                    if st_score > 0:
                        st_factor = ReasoningFactor(
                            factor="special_teams_performance",
                            value=f"{team}: {st_score:.1f} ST score",
                            weight=0.4,
                            confidence=0.6,
                            source="special_teams_analysis"
                        )
                        factors.append(st_factor)

            # Accuracy-based learning factors
            for category, cat_accuracy in accuracy.category_accuracies.items():
                if cat_accuracy < 0.5:  # Poor performance in this category
                    learning_factor = ReasoningFactor(
                        factor=f"prediction_challenge_{category}",
                        value=f"Low accuracy ({cat_accuracy:.1%}) in {category}",
                        weight=0.8,
                        confidence=0.9,
                        source="prediction_accuracy_analysis"
                    )
                    factors.append(learning_factor)

        except Exception as e:
            logger.error(f"Error extracting enhanced reasoning factors: {e}")

        return factors

    def _create_enhanced_confidence_breakdown(self, accuracy: ComprehensiveAccuracy) -> ConfidenceBreakdown:
        """Create confidence breakdown from comprehensive accuracy"""
        return ConfidenceBreakdown(
            winner=accuracy.category_accuracies.get("winner", 0.5),
            spread=accuracy.category_accuracies.get("spread_pick", 0.5),
            total=accuracy.category_accuracies.get("total_pick", 0.5),
            coaching=accuracy.category_accuracies.get("coaching_advantage", 0.5),
            special_teams=accuracy.category_accuracies.get("special_teams_edge", 0.5)
        )

    async def _get_enhanced_context_data(self, game_id: str) -> Dict[str, Any]:
        """Get enhanced context data for reasoning chain"""
        try:
            game_data = await self.storage.get_game_verification_data(game_id)
            return {
                "enhanced_game_data": game_data.get("game_data", {}),
                "coaching_decisions_count": len(game_data.get("coaching_decisions", [])),
                "special_teams_metrics": len(game_data.get("special_teams", [])),
                "situational_metrics": len(game_data.get("situational", [])),
                "data_richness_score": self._calculate_data_richness(game_data)
            }
        except Exception as e:
            logger.error(f"Error getting enhanced context data: {e}")
            return {}

    def _calculate_data_richness(self, game_data: Dict[str, Any]) -> float:
        """Calculate data richness score for enhanced analytics"""
        score = 0.0
        max_score = 100.0

        enhanced_game = game_data.get("game_data", {})

        # Basic game data (20 points)
        if enhanced_game.get("final_score_home") is not None:
            score += 20

        # Weather data (15 points)
        if enhanced_game.get("weather_condition"):
            score += 15

        # Team stats (25 points)
        if enhanced_game.get("home_total_yards"):
            score += 25

        # Coaching decisions (20 points)
        if game_data.get("coaching_decisions"):
            score += 20

        # Special teams (10 points)
        if game_data.get("special_teams"):
            score += 10

        # Situational data (10 points)
        if game_data.get("situational"):
            score += 10

        return score / max_score

    async def _trigger_enhanced_belief_revision(self, expert_id: str, game_id: str,
                                              accuracy: ComprehensiveAccuracy,
                                              reasoning_factors: List[ReasoningFactor]) -> Dict[str, Any]:
        """Trigger belief revision with enhanced performance metrics"""
        result = {
            "revision_triggered": False,
            "insights": [],
            "errors": []
        }

        try:
            # Check if belief revision is needed based on comprehensive accuracy
            if accuracy.overall_accuracy < 0.3 or accuracy.weighted_accuracy < 0.4:
                # Trigger belief revision with enhanced context
                revision_result = await self.belief_revision.trigger_belief_revision(
                    expert_id=expert_id,
                    failed_prediction_game_id=game_id,
                    contradiction_evidence={
                        "comprehensive_accuracy": accuracy.overall_accuracy,
                        "weighted_accuracy": accuracy.weighted_accuracy,
                        "category_accuracies": accuracy.category_accuracies,
                        "poor_categories": [cat for cat, acc in accuracy.category_accuracies.items() if acc < 0.3]
                    },
                    enhanced_context={
                        "reasoning_factors": [
                            {
                                "factor": rf.factor,
                                "value": rf.value,
                                "weight": rf.weight,
                                "confidence": rf.confidence,
                                "source": rf.source
                            } for rf in reasoning_factors
                        ],
                        "data_richness": await self._get_enhanced_context_data(game_id)
                    }
                )

                if revision_result:
                    result["revision_triggered"] = True
                    result["insights"].append(f"Belief revision triggered for expert {expert_id} due to poor performance")

            # Check for calibration issues
            if accuracy.confidence_calibration < 0.6:
                result["insights"].append(f"Expert {expert_id} has poor confidence calibration ({accuracy.confidence_calibration:.1%})")

        except Exception as e:
            error_msg = f"Error triggering enhanced belief revision: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    async def _create_enhanced_episodic_memory(self, expert_id: str, game_id: str,
                                             predictions: Dict[str, Any],
                                             accuracy: ComprehensiveAccuracy) -> Dict[str, Any]:
        """Create episodic memory with enhanced game experience"""
        result = {
            "memory_created": False,
            "insights": [],
            "errors": []
        }

        try:
            # Get comprehensive game data for rich experience
            game_data = await self.storage.get_game_verification_data(game_id)
            enhanced_game = game_data.get("game_data", {})

            # Create rich game experience
            game_experience = GameExperience(
                game_id=game_id,
                expert_id=expert_id,
                game_context={
                    "teams": f"{enhanced_game.get('away_team', 'AWAY')} @ {enhanced_game.get('home_team', 'HOME')}",
                    "final_score": f"{enhanced_game.get('final_score_away', 0)} - {enhanced_game.get('final_score_home', 0)}",
                    "weather": f"{enhanced_game.get('weather_condition', 'Unknown')} {enhanced_game.get('weather_temperature', 'N/A')}°F",
                    "stadium": enhanced_game.get("stadium_name", "Unknown"),
                    "attendance": enhanced_game.get("attendance"),
                    "game_duration": enhanced_game.get("game_duration_minutes"),
                    "overtime": enhanced_game.get("overtime_periods", 0) > 0
                },
                prediction_accuracy=accuracy.overall_accuracy,
                emotional_impact=self._calculate_enhanced_emotional_impact(accuracy, game_data),
                surprise_factor=self._calculate_enhanced_surprise_factor(predictions, game_data),
                lessons_learned=await self._extract_enhanced_lessons(expert_id, accuracy, reasoning_factors=[]),
                contextual_factors={
                    "weather_impact": enhanced_game.get("weather_condition") is not None,
                    "high_scoring": (enhanced_game.get("final_score_home", 0) + enhanced_game.get("final_score_away", 0)) > 50,
                    "close_game": abs(enhanced_game.get("final_score_home", 0) - enhanced_game.get("final_score_away", 0)) <= 7,
                    "coaching_advantage": game_data.get("coaching_advantage", {}).get("advantage_team"),
                    "special_teams_impact": len(game_data.get("special_teams", [])) > 0,
                    "data_richness": self._calculate_data_richness(game_data)
                }
            )

            # Store enhanced episodic memory
            memory_id = await self.episodic_memory.store_game_experience(
                game_experience=game_experience,
                expert_personality=expert_id.lower().replace("_", " "),  # Convert expert_id to personality
                enhanced_context=game_data
            )

            if memory_id:
                result["memory_created"] = True
                result["insights"].append(f"Created enhanced episodic memory {memory_id} for expert {expert_id}")

        except Exception as e:
            error_msg = f"Error creating enhanced episodic memory: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    def _calculate_enhanced_emotional_impact(self, accuracy: ComprehensiveAccuracy, game_data: Dict[str, Any]) -> float:
        """Calculate emotional impact with enhanced game context"""
        base_impact = 1.0 - accuracy.overall_accuracy  # Poor accuracy = high emotional impact

        # Enhance based on game context
        enhanced_game = game_data.get("game_data", {})

        # High-stakes games have higher emotional impact
        if enhanced_game.get("attendance", 0) > 70000:
            base_impact *= 1.2

        # Close games have higher emotional impact
        home_score = enhanced_game.get("final_score_home", 0)
        away_score = enhanced_game.get("final_score_away", 0)
        if abs(home_score - away_score) <= 3:
            base_impact *= 1.3

        # Weather games have higher emotional impact
        if enhanced_game.get("weather_condition") and "rain" in enhanced_game["weather_condition"].lower():
            base_impact *= 1.1

        return min(1.0, base_impact)

    def _calculate_enhanced_surprise_factor(self, predictions: Dict[str, Any], game_data: Dict[str, Any]) -> float:
        """Calculate surprise factor with enhanced game context"""
        surprise = 0.0

        enhanced_game = game_data.get("game_data", {})

        # Score surprise
        predicted_total = predictions.get("predicted_total", 45)
        actual_total = enhanced_game.get("final_score_home", 0) + enhanced_game.get("final_score_away", 0)
        score_surprise = abs(predicted_total - actual_total) / 21.0  # Normalize by 3 TDs

        # Winner surprise
        predicted_winner = predictions.get("winner")
        home_score = enhanced_game.get("final_score_home", 0)
        away_score = enhanced_game.get("final_score_away", 0)
        actual_winner = enhanced_game.get("home_team") if home_score > away_score else enhanced_game.get("away_team")

        winner_surprise = 1.0 if predicted_winner != actual_winner else 0.0

        # Combine surprises
        surprise = (score_surprise + winner_surprise) / 2.0

        return min(1.0, surprise)

    async def _extract_enhanced_lessons(self, expert_id: str, accuracy: ComprehensiveAccuracy, reasoning_factors: List[ReasoningFactor]) -> List[str]:
        """Extract lessons with enhanced analytics"""
        lessons = []

        # Category-specific lessons
        for category, cat_accuracy in accuracy.category_accuracies.items():
            if cat_accuracy < 0.3:
                lessons.append(f"Need to improve {category} predictions - current accuracy: {cat_accuracy:.1%}")

        # Confidence calibration lessons
        if accuracy.confidence_calibration < 0.7:
            lessons.append(f"Confidence calibration needs improvement - current: {accuracy.confidence_calibration:.1%}")

        # Factor-based lessons
        for factor in reasoning_factors:
            if factor.confidence < 0.5:
                lessons.append(f"Low confidence in {factor.factor} analysis - need more data or better models")

        # Overall performance lessons
        if accuracy.weighted_accuracy < 0.5:
            lessons.append("Overall prediction performance below 50% - fundamental approach needs revision")

        return lessons

    async def _generate_cross_expert_insights(self, game_id: str, verification_results: Dict[str, ComprehensiveAccuracy]) -> List[str]:
        """Generate insights across all experts"""
        insights = []

        if not verification_results:
            return insights

        # Best and worst performers
        accuracies = [(expert_id, acc.weighted_accuracy) for expert_id, acc in verification_results.items()]
        accuracies.sort(key=lambda x: x[1], reverse=True)

        best_expert = accuracies[0]
        worst_expert = accuracies[-1]

        insights.append(f"Best performer: {best_expert[0]} ({best_expert[1]:.1%})")
        insights.append(f"Worst performer: {worst_expert[0]} ({worst_expert[1]:.1%})")

        # Category analysis
        all_categories = set()
        for acc in verification_results.values():
            all_categories.update(acc.category_accuracies.keys())

        for category in all_categories:
            category_accuracies = [
                acc.category_accuracies[category]
                for acc in verification_results.values()
                if category in acc.category_accuracies
            ]

            if category_accuracies:
                avg_accuracy = statistics.mean(category_accuracies)
                if avg_accuracy < 0.4:
                    insights.append(f"All experts struggled with {category} (avg: {avg_accuracy:.1%})")
                elif avg_accuracy > 0.8:
                    insights.append(f"Strong performance across experts in {category} (avg: {avg_accuracy:.1%})")

        return insights

    async def _update_expert_models(self, verification_results: Dict[str, ComprehensiveAccuracy]):
        """Update expert models based on verification results"""
        try:
            for expert_id, accuracy in verification_results.items():
                # Update expert performance metrics in database
                async with self.storage.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE personality_experts
                        SET
                            last_game_accuracy = $1,
                            total_predictions = total_predictions + $2,
                            correct_predictions = correct_predictions + $3,
                            updated_at = NOW()
                        WHERE expert_id = $4
                    """, accuracy.overall_accuracy, accuracy.total_predictions,
                        accuracy.correct_predictions, expert_id)

                logger.info(f"Updated model for expert {expert_id}: {accuracy.overall_accuracy:.1%} accuracy")

        except Exception as e:
            logger.error(f"Error updating expert models: {e}")

# Example usage and testing
async def main():
    """Test enhanced learning integration"""

    # Configuration
    database_url = "postgresql://localhost/nfl_predictor"
    sportsdata_api_key = "bc297647c7aa4ef29747e6a85cb575dc"

    # Initialize integration
    integration = EnhancedLearningIntegration(database_url, sportsdata_api_key)

    try:
        await integration.initialize()

        # Test learning cycle
        game_id = "test_game_id"
        expert_predictions = {
            "the_analyst": {
                "winner": "LAC",
                "home_score": 23,
                "away_score": 27,
                "margin": 4,
                "predicted_total": 50,
                "coaching_advantage": "LAC"
            }
        }

        cycle_result = await integration.process_game_learning_cycle(game_id, expert_predictions)
        logger.info(f"Learning cycle result: {cycle_result}")

    except Exception as e:
        logger.error(f"Test failed: {e}")

    finally:
        await integration.close()

if __name__ == "__main__":
    asyncio.run(main())