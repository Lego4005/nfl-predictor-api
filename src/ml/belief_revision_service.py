"""
Belief Revision Service - Expert Mind Change Tracking
Tracks when experts change their minds with causal chains and reasoning analysis
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import asyncpg
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RevisionType(Enum):
    PREDICTION_CHANGE = "prediction_change"
    CONFIDENCE_SHIFT = "confidence_shift"
    REASONING_UPDATE = "reasoning_update"
    COMPLETE_REVERSAL = "complete_reversal"
    NUANCED_ADJUSTMENT = "nuanced_adjustment"

class RevisionTrigger(Enum):
    NEW_INFORMATION = "new_information"
    INJURY_REPORT = "injury_report"
    WEATHER_UPDATE = "weather_update"
    LINE_MOVEMENT = "line_movement"
    PUBLIC_SENTIMENT = "public_sentiment"
    EXPERT_INFLUENCE = "expert_influence"
    SELF_REFLECTION = "self_reflection"
    PATTERN_RECOGNITION = "pattern_recognition"

@dataclass
class BeliefRevision:
    expert_id: str
    game_id: str
    revision_type: RevisionType
    trigger: RevisionTrigger
    original_prediction: Dict[str, Any]
    revised_prediction: Dict[str, Any]
    causal_chain: List[Dict[str, Any]]
    confidence_delta: float
    reasoning_before: str
    reasoning_after: str
    emotional_state: str
    revision_timestamp: datetime
    impact_score: float

class BeliefRevisionService:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.db_pool = None
        self.expert_personalities = self._load_expert_personalities()

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(**self.db_config)
            logger.info("✅ Belief Revision Service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Belief Revision Service: {e}")
            raise

    def _load_expert_personalities(self) -> Dict[str, Dict[str, Any]]:
        """Load expert personality profiles for belief revision patterns"""
        return {
            "1": {"name": "The Analyst", "revision_tendency": "low", "triggers": ["new_information", "pattern_recognition"]},
            "2": {"name": "The Gambler", "revision_tendency": "high", "triggers": ["line_movement", "public_sentiment"]},
            "3": {"name": "The Rebel", "revision_tendency": "medium", "triggers": ["expert_influence", "self_reflection"]},
            "4": {"name": "The Hunter", "revision_tendency": "medium", "triggers": ["new_information", "line_movement"]},
            "5": {"name": "The Rider", "revision_tendency": "high", "triggers": ["public_sentiment", "expert_influence"]},
            "6": {"name": "The Scholar", "revision_tendency": "low", "triggers": ["new_information", "pattern_recognition"]},
            "7": {"name": "The Chaos", "revision_tendency": "very_high", "triggers": ["self_reflection", "weather_update"]},
            "8": {"name": "The Intuition", "revision_tendency": "medium", "triggers": ["self_reflection", "injury_report"]},
            "9": {"name": "The Quant", "revision_tendency": "low", "triggers": ["new_information", "pattern_recognition"]},
            "10": {"name": "The Reversal", "revision_tendency": "high", "triggers": ["pattern_recognition", "line_movement"]},
            "11": {"name": "The Fader", "revision_tendency": "medium", "triggers": ["public_sentiment", "expert_influence"]},
            "12": {"name": "The Sharp", "revision_tendency": "low", "triggers": ["line_movement", "new_information"]},
            "13": {"name": "The Underdog", "revision_tendency": "medium", "triggers": ["injury_report", "public_sentiment"]},
            "14": {"name": "The Consensus", "revision_tendency": "high", "triggers": ["expert_influence", "public_sentiment"]},
            "15": {"name": "The Exploiter", "revision_tendency": "medium", "triggers": ["line_movement", "pattern_recognition"]}
        }

    async def detect_belief_revision(self, expert_id: str, game_id: str,
                                   original_prediction: Dict[str, Any],
                                   new_prediction: Dict[str, Any],
                                   trigger_data: Optional[Dict[str, Any]] = None) -> Optional[BeliefRevision]:
        """Detect if expert has revised their beliefs and analyze the change"""

        # Check for significant changes
        revision_type = self._classify_revision_type(original_prediction, new_prediction)
        if not revision_type:
            return None

        # Determine trigger
        trigger = self._identify_trigger(expert_id, trigger_data)

        # Build causal chain
        causal_chain = await self._build_causal_chain(expert_id, game_id, original_prediction, new_prediction, trigger)

        # Calculate confidence delta
        confidence_delta = new_prediction.get("confidence", 0.5) - original_prediction.get("confidence", 0.5)

        # Generate reasoning analysis
        reasoning_before = await self._extract_reasoning(original_prediction)
        reasoning_after = await self._extract_reasoning(new_prediction)

        # Assess emotional state
        emotional_state = self._assess_emotional_state(expert_id, revision_type, confidence_delta)

        # Calculate impact score
        impact_score = self._calculate_impact_score(revision_type, confidence_delta, original_prediction, new_prediction)

        revision = BeliefRevision(
            expert_id=expert_id,
            game_id=game_id,
            revision_type=revision_type,
            trigger=trigger,
            original_prediction=original_prediction,
            revised_prediction=new_prediction,
            causal_chain=causal_chain,
            confidence_delta=confidence_delta,
            reasoning_before=reasoning_before,
            reasoning_after=reasoning_after,
            emotional_state=emotional_state,
            revision_timestamp=datetime.utcnow(),
            impact_score=impact_score
        )

        # Store in database
        await self._store_revision(revision)

        return revision

    def _classify_revision_type(self, original: Dict[str, Any], revised: Dict[str, Any]) -> Optional[RevisionType]:
        """Classify the type of belief revision"""

        # Check for winner change
        if original.get("winner") != revised.get("winner"):
            return RevisionType.COMPLETE_REVERSAL

        # Check for significant confidence change
        conf_delta = abs(revised.get("confidence", 0.5) - original.get("confidence", 0.5))
        if conf_delta > 0.2:
            return RevisionType.CONFIDENCE_SHIFT

        # Check for score prediction changes
        orig_spread = abs(original.get("home_score", 0) - original.get("away_score", 0))
        rev_spread = abs(revised.get("home_score", 0) - revised.get("away_score", 0))
        if abs(orig_spread - rev_spread) > 7:
            return RevisionType.PREDICTION_CHANGE

        # Check reasoning changes
        if original.get("reasoning") != revised.get("reasoning"):
            return RevisionType.REASONING_UPDATE

        # Small adjustments
        if conf_delta > 0.05 or abs(orig_spread - rev_spread) > 3:
            return RevisionType.NUANCED_ADJUSTMENT

        return None

    def _identify_trigger(self, expert_id: str, trigger_data: Optional[Dict[str, Any]]) -> RevisionTrigger:
        """Identify what triggered the belief revision"""

        if not trigger_data:
            # Default based on expert personality
            personality = self.expert_personalities.get(expert_id, {})
            default_triggers = personality.get("triggers", ["self_reflection"])
            return RevisionTrigger(default_triggers[0])

        # Analyze trigger data
        if "injury" in str(trigger_data).lower():
            return RevisionTrigger.INJURY_REPORT
        elif "weather" in str(trigger_data).lower():
            return RevisionTrigger.WEATHER_UPDATE
        elif "line" in str(trigger_data).lower() or "odds" in str(trigger_data).lower():
            return RevisionTrigger.LINE_MOVEMENT
        elif "public" in str(trigger_data).lower() or "sentiment" in str(trigger_data).lower():
            return RevisionTrigger.PUBLIC_SENTIMENT
        elif "expert" in str(trigger_data).lower():
            return RevisionTrigger.EXPERT_INFLUENCE
        elif "pattern" in str(trigger_data).lower() or "historical" in str(trigger_data).lower():
            return RevisionTrigger.PATTERN_RECOGNITION
        else:
            return RevisionTrigger.NEW_INFORMATION

    async def _build_causal_chain(self, expert_id: str, game_id: str,
                                original: Dict[str, Any], revised: Dict[str, Any],
                                trigger: RevisionTrigger) -> List[Dict[str, Any]]:
        """Build causal chain explaining the belief revision"""

        chain = []

        # Initial state
        chain.append({
            "step": 1,
            "event": "initial_belief",
            "description": f"Expert {expert_id} initially predicted {original.get('winner')} with {original.get('confidence', 0.5):.2f} confidence",
            "state": "stable",
            "timestamp": datetime.utcnow() - timedelta(minutes=30)
        })

        # Trigger event
        chain.append({
            "step": 2,
            "event": "trigger_received",
            "description": f"Received {trigger.value} information",
            "state": "processing",
            "timestamp": datetime.utcnow() - timedelta(minutes=15)
        })

        # Cognitive processing
        personality = self.expert_personalities.get(expert_id, {})
        processing_style = self._get_processing_style(personality)

        chain.append({
            "step": 3,
            "event": "cognitive_processing",
            "description": f"Processing new information using {processing_style} approach",
            "state": "analyzing",
            "timestamp": datetime.utcnow() - timedelta(minutes=10)
        })

        # Belief update
        chain.append({
            "step": 4,
            "event": "belief_revision",
            "description": f"Updated prediction to {revised.get('winner')} with {revised.get('confidence', 0.5):.2f} confidence",
            "state": "revised",
            "timestamp": datetime.utcnow()
        })

        return chain

    def _get_processing_style(self, personality: Dict[str, Any]) -> str:
        """Get cognitive processing style based on expert personality"""
        name = personality.get("name", "")

        if "Analyst" in name or "Quant" in name or "Scholar" in name:
            return "systematic_analytical"
        elif "Gambler" in name or "Chaos" in name:
            return "intuitive_rapid"
        elif "Rebel" in name or "Fader" in name:
            return "contrarian_skeptical"
        elif "Hunter" in name or "Exploiter" in name or "Sharp" in name:
            return "opportunity_focused"
        else:
            return "balanced_deliberative"

    async def _extract_reasoning(self, prediction: Dict[str, Any]) -> str:
        """Extract reasoning from prediction data"""
        reasoning_chain = prediction.get("reasoning_chain", [])
        if reasoning_chain:
            factors = [f"• {item.get('factor', 'Unknown')}: {item.get('value', 'N/A')}"
                      for item in reasoning_chain]
            return "Key factors:\n" + "\n".join(factors)
        return prediction.get("reasoning", "No detailed reasoning available")

    def _assess_emotional_state(self, expert_id: str, revision_type: RevisionType, confidence_delta: float) -> str:
        """Assess expert's emotional state during revision"""

        personality = self.expert_personalities.get(expert_id, {})
        revision_tendency = personality.get("revision_tendency", "medium")

        # High revision tendency experts are more comfortable with changes
        if revision_tendency in ["high", "very_high"]:
            if revision_type == RevisionType.COMPLETE_REVERSAL:
                return "confident_pivot"
            elif confidence_delta > 0:
                return "increasingly_confident"
            else:
                return "adaptive_recalibration"

        # Low revision tendency experts may feel more stress
        elif revision_tendency == "low":
            if revision_type == RevisionType.COMPLETE_REVERSAL:
                return "reluctant_acceptance"
            elif abs(confidence_delta) > 0.2:
                return "cognitive_dissonance"
            else:
                return "cautious_adjustment"

        # Medium tendency
        else:
            if revision_type == RevisionType.COMPLETE_REVERSAL:
                return "decisive_shift"
            elif confidence_delta > 0.1:
                return "growing_conviction"
            elif confidence_delta < -0.1:
                return "emerging_doubt"
            else:
                return "measured_revision"

    def _calculate_impact_score(self, revision_type: RevisionType, confidence_delta: float,
                              original: Dict[str, Any], revised: Dict[str, Any]) -> float:
        """Calculate impact score of the belief revision"""

        base_score = 0.0

        # Type-based scoring
        type_scores = {
            RevisionType.COMPLETE_REVERSAL: 1.0,
            RevisionType.PREDICTION_CHANGE: 0.7,
            RevisionType.CONFIDENCE_SHIFT: 0.5,
            RevisionType.REASONING_UPDATE: 0.3,
            RevisionType.NUANCED_ADJUSTMENT: 0.2
        }
        base_score += type_scores.get(revision_type, 0.2)

        # Confidence change impact
        base_score += abs(confidence_delta) * 0.5

        # Score prediction change impact
        orig_total = original.get("home_score", 20) + original.get("away_score", 20)
        rev_total = revised.get("home_score", 20) + revised.get("away_score", 20)
        total_change = abs(orig_total - rev_total) / 70.0  # Normalize to 0-1
        base_score += total_change * 0.3

        # Spread change impact
        orig_spread = abs(original.get("home_score", 20) - original.get("away_score", 20))
        rev_spread = abs(revised.get("home_score", 20) - revised.get("away_score", 20))
        spread_change = abs(orig_spread - rev_spread) / 30.0  # Normalize to 0-1
        base_score += spread_change * 0.4

        return min(1.0, base_score)

    async def _store_revision(self, revision: BeliefRevision):
        """Store belief revision in database"""

        query = """
        INSERT INTO expert_belief_revisions (
            expert_id, game_id, revision_type, trigger_type,
            original_prediction, revised_prediction, causal_chain,
            confidence_delta, reasoning_before, reasoning_after,
            emotional_state, impact_score, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    revision.expert_id,
                    revision.game_id,
                    revision.revision_type.value,
                    revision.trigger.value,
                    json.dumps(revision.original_prediction),
                    json.dumps(revision.revised_prediction),
                    json.dumps(revision.causal_chain),
                    revision.confidence_delta,
                    revision.reasoning_before,
                    revision.reasoning_after,
                    revision.emotional_state,
                    revision.impact_score,
                    revision.revision_timestamp
                )

            logger.info(f"✅ Stored belief revision for expert {revision.expert_id}, game {revision.game_id}")

        except Exception as e:
            logger.error(f"❌ Failed to store belief revision: {e}")
            raise

    async def get_expert_revision_history(self, expert_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get revision history for an expert"""

        query = """
        SELECT * FROM expert_belief_revisions
        WHERE expert_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, expert_id, limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to get revision history: {e}")
            return []

    async def analyze_revision_patterns(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze belief revision patterns across experts"""

        base_query = """
        SELECT
            expert_id,
            revision_type,
            trigger_type,
            emotional_state,
            AVG(confidence_delta) as avg_confidence_delta,
            AVG(impact_score) as avg_impact,
            COUNT(*) as revision_count
        FROM expert_belief_revisions
        """

        if expert_id:
            query = base_query + " WHERE expert_id = $1 GROUP BY expert_id, revision_type, trigger_type, emotional_state"
            params = [expert_id]
        else:
            query = base_query + " GROUP BY expert_id, revision_type, trigger_type, emotional_state"
            params = []

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            patterns = {}
            for row in rows:
                expert = row['expert_id']
                if expert not in patterns:
                    patterns[expert] = {
                        'total_revisions': 0,
                        'revision_types': {},
                        'triggers': {},
                        'emotional_states': {},
                        'avg_confidence_delta': 0,
                        'avg_impact': 0
                    }

                patterns[expert]['total_revisions'] += row['revision_count']
                patterns[expert]['revision_types'][row['revision_type']] = row['revision_count']
                patterns[expert]['triggers'][row['trigger_type']] = row['revision_count']
                patterns[expert]['emotional_states'][row['emotional_state']] = row['revision_count']
                patterns[expert]['avg_confidence_delta'] = row['avg_confidence_delta']
                patterns[expert]['avg_impact'] = row['avg_impact']

            return patterns

        except Exception as e:
            logger.error(f"❌ Failed to analyze revision patterns: {e}")
            return {}

    async def get_game_revision_timeline(self, game_id: str) -> List[Dict[str, Any]]:
        """Get timeline of all expert revisions for a specific game"""

        query = """
        SELECT
            expert_id,
            revision_type,
            trigger_type,
            confidence_delta,
            impact_score,
            emotional_state,
            created_at
        FROM expert_belief_revisions
        WHERE game_id = $1
        ORDER BY created_at ASC
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, game_id)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to get game revision timeline: {e}")
            return []

    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ Belief Revision Service closed")

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

    service = BeliefRevisionService(db_config)
    await service.initialize()

    # Example belief revision detection
    original_prediction = {
        "winner": "Chiefs",
        "confidence": 0.65,
        "home_score": 24,
        "away_score": 21,
        "reasoning": "Strong offensive line"
    }

    revised_prediction = {
        "winner": "Bills",
        "confidence": 0.72,
        "home_score": 21,
        "away_score": 28,
        "reasoning": "Key injury to Chiefs QB"
    }

    trigger_data = {"type": "injury_report", "details": "Mahomes questionable"}

    revision = await service.detect_belief_revision(
        expert_id="1",
        game_id="game_123",
        original_prediction=original_prediction,
        new_prediction=revised_prediction,
        trigger_data=trigger_data
    )

    if revision:
        print(f"Detected {revision.revision_type.value} with impact score {revision.impact_score:.2f}")

    await service.close()

if __name__ == "__main__":
    asyncio.run(main())