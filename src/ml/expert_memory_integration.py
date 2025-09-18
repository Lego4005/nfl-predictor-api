"""
Expert Memory Integration Service
Coordinates all three memory services with the existing expert system
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from .reasoning_chain_logger import ReasoningChainLogger
from .belief_revision_service import BeliefRevisionService
from .episodic_memory_manager import EpisodicMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertMemoryIntegration:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.reasoning_logger = ReasoningChainLogger(db_config)
        self.belief_service = BeliefRevisionService(db_config)
        self.memory_manager = EpisodicMemoryManager(db_config)
        self.initialized = False

    async def initialize(self):
        """Initialize all memory services"""
        try:
            await self.reasoning_logger.initialize()
            await self.belief_service.initialize()
            await self.memory_manager.initialize()
            self.initialized = True
            logger.info("✅ Expert Memory Integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Expert Memory Integration: {e}")
            raise

    async def process_expert_prediction(self, expert_id: str, game_id: str,
                                      prediction_data: Dict[str, Any],
                                      previous_prediction: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a new expert prediction through all memory services"""

        if not self.initialized:
            await self.initialize()

        results = {}

        try:
            # 1. Log reasoning chain
            reasoning_entry = await self.reasoning_logger.log_reasoning_chain(
                expert_id=expert_id,
                game_id=game_id,
                prediction_data=prediction_data,
                reasoning_chain=prediction_data.get("reasoning_chain", []),
                confidence=prediction_data.get("confidence", 0.5),
                internal_monologue=prediction_data.get("internal_monologue", "")
            )
            results["reasoning_logged"] = True
            results["reasoning_id"] = reasoning_entry.get("id")

            # 2. Check for belief revision
            if previous_prediction:
                revision = await self.belief_service.detect_belief_revision(
                    expert_id=expert_id,
                    game_id=game_id,
                    original_prediction=previous_prediction,
                    new_prediction=prediction_data,
                    trigger_data=prediction_data.get("trigger_data")
                )

                if revision:
                    results["belief_revision"] = {
                        "detected": True,
                        "type": revision.revision_type.value,
                        "emotional_state": revision.emotional_state,
                        "impact_score": revision.impact_score
                    }
                else:
                    results["belief_revision"] = {"detected": False}
            else:
                results["belief_revision"] = {"detected": False, "reason": "no_previous_prediction"}

            # 3. Retrieve similar memories for context
            similar_memories = await self.memory_manager.retrieve_similar_memories(
                expert_id=expert_id,
                current_situation={
                    "home_team": prediction_data.get("home_team"),
                    "away_team": prediction_data.get("away_team"),
                    "confidence": prediction_data.get("confidence", 0.5),
                    "predicted_winner": prediction_data.get("winner"),
                    "reasoning_chain": prediction_data.get("reasoning_chain", [])
                },
                limit=5
            )
            results["similar_memories"] = {
                "count": len(similar_memories),
                "memories": similar_memories[:3]  # Return top 3 for API response
            }

            # 4. Enhance prediction with memory insights
            enhanced_prediction = await self._enhance_prediction_with_memory(
                prediction_data, similar_memories
            )
            results["enhanced_prediction"] = enhanced_prediction

            logger.info(f"✅ Processed prediction for expert {expert_id}, game {game_id}")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to process expert prediction: {e}")
            raise

    async def process_game_outcome(self, game_id: str, actual_outcome: Dict[str, Any],
                                 expert_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process game outcome and create episodic memories for all experts"""

        if not self.initialized:
            await self.initialize()

        results = {
            "memories_created": 0,
            "expert_results": {}
        }

        try:
            for expert_pred in expert_predictions:
                expert_id = expert_pred.get("expert_id")
                if not expert_id:
                    continue

                # Create episodic memory
                memory = await self.memory_manager.create_episodic_memory(
                    expert_id=expert_id,
                    game_id=game_id,
                    prediction_data=expert_pred,
                    actual_outcome=actual_outcome,
                    contextual_factors=expert_pred.get("contextual_factors")
                )

                # Update reasoning chain with outcome
                await self.reasoning_logger.update_reasoning_outcome(
                    expert_id=expert_id,
                    game_id=game_id,
                    actual_outcome=actual_outcome
                )

                results["expert_results"][expert_id] = {
                    "memory_created": True,
                    "emotional_state": memory.emotional_state.value,
                    "memory_vividness": memory.memory_vividness,
                    "lessons_learned": len(memory.lessons_learned)
                }
                results["memories_created"] += 1

            logger.info(f"✅ Processed game outcome for {results['memories_created']} experts")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to process game outcome: {e}")
            raise

    async def _enhance_prediction_with_memory(self, prediction_data: Dict[str, Any],
                                            similar_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance prediction with insights from similar memories"""

        enhanced = prediction_data.copy()

        if not similar_memories:
            return enhanced

        # Analyze memory patterns
        memory_insights = {
            "similar_situations": len(similar_memories),
            "confidence_adjustments": [],
            "risk_factors": [],
            "success_patterns": []
        }

        for memory in similar_memories:
            memory_prediction = json.loads(memory.get("prediction_data", "{}"))
            memory_outcome = json.loads(memory.get("actual_outcome", "{}"))

            # Check prediction accuracy
            was_correct = (memory_prediction.get("winner") == memory_outcome.get("winner"))

            if was_correct:
                memory_insights["success_patterns"].append({
                    "confidence": memory_prediction.get("confidence", 0.5),
                    "emotional_state": memory.get("emotional_state"),
                    "similarity": memory.get("similarity_score", 0)
                })
            else:
                memory_insights["risk_factors"].append({
                    "confidence": memory_prediction.get("confidence", 0.5),
                    "emotional_state": memory.get("emotional_state"),
                    "similarity": memory.get("similarity_score", 0)
                })

        # Calculate confidence adjustment
        if memory_insights["success_patterns"] and memory_insights["risk_factors"]:
            success_rate = len(memory_insights["success_patterns"]) / len(similar_memories)
            avg_success_confidence = sum(p["confidence"] for p in memory_insights["success_patterns"]) / len(memory_insights["success_patterns"])

            if success_rate > 0.6 and avg_success_confidence > 0.7:
                memory_insights["confidence_adjustments"].append({
                    "type": "boost",
                    "factor": 0.05,
                    "reason": "Similar situations had high success rate"
                })
            elif success_rate < 0.4:
                memory_insights["confidence_adjustments"].append({
                    "type": "reduce",
                    "factor": -0.05,
                    "reason": "Similar situations had low success rate"
                })

        enhanced["memory_insights"] = memory_insights
        return enhanced

    async def get_expert_memory_summary(self, expert_id: str) -> Dict[str, Any]:
        """Get comprehensive memory summary for an expert"""

        if not self.initialized:
            await self.initialize()

        try:
            # Get reasoning chain stats
            reasoning_stats = await self.reasoning_logger.get_expert_stats(expert_id)

            # Get belief revision patterns
            revision_patterns = await self.belief_service.analyze_revision_patterns(expert_id)

            # Get episodic memory stats
            memory_stats = await self.memory_manager.get_memory_stats(expert_id)

            summary = {
                "expert_id": expert_id,
                "reasoning_chains": {
                    "total_predictions": reasoning_stats.get("total_predictions", 0),
                    "avg_confidence": reasoning_stats.get("avg_confidence", 0),
                    "avg_factors_considered": reasoning_stats.get("avg_factors_considered", 0)
                },
                "belief_revisions": {
                    "total_revisions": revision_patterns.get(expert_id, {}).get("total_revisions", 0),
                    "revision_types": revision_patterns.get(expert_id, {}).get("revision_types", {}),
                    "avg_impact": revision_patterns.get(expert_id, {}).get("avg_impact", 0)
                },
                "episodic_memories": {
                    "total_memories": memory_stats.get("total_memories", 0),
                    "avg_emotional_intensity": memory_stats.get("avg_emotional_intensity", 0),
                    "avg_vividness": memory_stats.get("avg_vividness", 0),
                    "memory_types": memory_stats.get("memory_types", {}),
                    "emotional_states": memory_stats.get("emotional_states", {})
                }
            }

            return summary

        except Exception as e:
            logger.error(f"❌ Failed to get expert memory summary: {e}")
            return {}

    async def consolidate_expert_memories(self, expert_id: str):
        """Consolidate memories for an expert across all services"""

        if not self.initialized:
            await self.initialize()

        try:
            # Consolidate episodic memories
            await self.memory_manager.consolidate_memories(expert_id)

            # Could add consolidation for reasoning chains and belief revisions here

            logger.info(f"✅ Consolidated memories for expert {expert_id}")

        except Exception as e:
            logger.error(f"❌ Failed to consolidate memories: {e}")

    async def get_game_memory_timeline(self, game_id: str) -> Dict[str, Any]:
        """Get complete memory timeline for a game across all experts"""

        if not self.initialized:
            await self.initialize()

        try:
            # Get reasoning chains for the game
            reasoning_chains = await self.reasoning_logger.get_game_reasoning_chains(game_id)

            # Get belief revisions for the game
            revision_timeline = await self.belief_service.get_game_revision_timeline(game_id)

            timeline = {
                "game_id": game_id,
                "reasoning_chains": reasoning_chains,
                "belief_revisions": revision_timeline,
                "total_events": len(reasoning_chains) + len(revision_timeline)
            }

            return timeline

        except Exception as e:
            logger.error(f"❌ Failed to get game memory timeline: {e}")
            return {}

    async def search_expert_memories(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Search across all memory services with unified query"""

        if not self.initialized:
            await self.initialize()

        try:
            results = {
                "reasoning_chains": [],
                "belief_revisions": [],
                "episodic_memories": []
            }

            expert_id = query_params.get("expert_id")
            game_id = query_params.get("game_id")
            date_range = query_params.get("date_range")

            # Search reasoning chains
            if expert_id:
                reasoning_results = await self.reasoning_logger.get_expert_reasoning_history(
                    expert_id, limit=query_params.get("limit", 20)
                )
                results["reasoning_chains"] = reasoning_results

            # Search belief revisions
            if expert_id:
                revision_results = await self.belief_service.get_expert_revision_history(
                    expert_id, limit=query_params.get("limit", 20)
                )
                results["belief_revisions"] = revision_results

            # Search episodic memories
            if expert_id and query_params.get("situation"):
                memory_results = await self.memory_manager.retrieve_similar_memories(
                    expert_id, query_params["situation"], limit=query_params.get("limit", 10)
                )
                results["episodic_memories"] = memory_results

            return results

        except Exception as e:
            logger.error(f"❌ Failed to search expert memories: {e}")
            return {}

    async def close(self):
        """Close all memory services"""
        try:
            await self.reasoning_logger.close()
            await self.belief_service.close()
            await self.memory_manager.close()
            logger.info("✅ Expert Memory Integration closed")
        except Exception as e:
            logger.error(f"❌ Error closing services: {e}")

# Example usage
async def main():
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'your_user',
        'password': 'your_password',
        'database': 'nfl_predictor'
    }

    integration = ExpertMemoryIntegration(db_config)
    await integration.initialize()

    # Example prediction processing
    prediction_data = {
        "expert_id": "1",
        "winner": "Chiefs",
        "confidence": 0.75,
        "home_team": "Chiefs",
        "away_team": "Bills",
        "home_score": 28,
        "away_score": 21,
        "reasoning_chain": [
            {"factor": "Offensive EPA", "value": "+0.35", "weight": 0.4, "confidence": 0.85},
            {"factor": "Home Field", "value": "Strong", "weight": 0.3, "confidence": 0.75}
        ],
        "internal_monologue": "Chiefs have been strong at home this season..."
    }

    results = await integration.process_expert_prediction(
        expert_id="1",
        game_id="game_789",
        prediction_data=prediction_data
    )

    print(f"Prediction processed: {results['reasoning_logged']}")
    print(f"Similar memories found: {results['similar_memories']['count']}")

    # Example outcome processing
    actual_outcome = {
        "winner": "Bills",
        "home_score": 24,
        "away_score": 31
    }

    outcome_results = await integration.process_game_outcome(
        game_id="game_789",
        actual_outcome=actual_outcome,
        expert_predictions=[prediction_data]
    )

    print(f"Memories created: {outcome_results['memories_created']}")

    # Get expert summary
    summary = await integration.get_expert_memory_summary("1")
    print(f"Expert has {summary['episodic_memories']['total_memories']} memories")

    await integration.close()

if __name__ == "__main__":
    asyncio.run(main())