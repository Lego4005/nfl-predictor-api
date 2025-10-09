"""
Orchestrator Model Switching Service
Implements multi-armed bandit policy for dynamic model selection per expert.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Op
Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import stats

from src.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    CLAUDE_SONNET = "anthropic/claude-sonnet-4.5"
    DEEPSEEK_CHAT = "deepseek/deepseek-chat-v3.1:free"
    GROK_FAST = "x-ai/grok-4-fast:free"
    GEMINI_FLASH = "google/gemini-2.5-flash-preview-09-2025"

@dataclass
class ModelMetrics:
    """Performance metrics for a model-expert-family combination"""
    json_validity_rate: float
    latency_p95: float
    brier_score: float
    mae_score: float
    roi: float
    coherence_delta: float
    games_count: int
    last_updated: datetime

@dataclass
class ModelAllocation:
    """Traffic allocation for a model"""
    model: ModelProvider
    allocation_pct: float
    is_primary: bool
    last_switch: Optional[datetime] = None

class OrchestratorModelSwitcher:
    """
    Manages dynamic model selection for expert agents using multi-armed bandit approach.
    Maintains SLOs while optimizing for performance across betting categories.
    """

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

        # SLO thresholds
        self.MIN_JSON_VALIDITY = 0.985
        self.MAX_LATENCY_P95_MS = 6000
        self.MIN_DWELL_TIME_HOURS = 2
        self.MIN_EXPLORATION_PCT = 0.10

        # Initial expert-model mapping
        self.initial_mapping = {
            "conservative_analyzer": {
                "primary": ModelProvider.CLAUDE_SONNET,
                "explore": [ModelProvider.GEMINI_FLASH, ModelProvider.DEEPSEEK_CHAT]
            },
            "momentum_rider": {
                "primary": ModelProvider.DEEPSEEK_CHAT,
                "explore": [ModelProvider.GEMINI_FLASH],
                "critic_repair": ModelProvider.CLAUDE_SONNET
            },
            "contrarian_rebel": {
                "primary": ModelProvider.GROK_FAST,
                "explore": [ModelProvider.DEEPSEEK_CHAT],
                "critic_repair": ModelProvider.CLAUDE_SONNET
            },
            "value_hunter": {
                "primary": ModelProvider.CLAUDE_SONNET,
                "explore": [ModelProvider.GEMINI_FLASH]
            }
        }

    async def get_model_metrics(
        self,
        expert_id: str,
        family: str,
        model: ModelProvider,
        lookback_days: int = 7
    ) -> Optional[ModelMetrics]:
        """Retrieve performance metrics for a model-expert-family combination"""

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Query expert predictions and outcomes
        query = """
        SELECT
            ep.json_valid,
            ep.latency_ms,
            ep.brier_score,
            ep.mae_score,
            ep.roi,
            ep.coherence_delta,
            ep.created_at
        FROM expert_predictions ep
        JOIN games g ON ep.game_id = g.game_id
        WHERE ep.expert_id = %s
        AND ep.family = %s
        AND ep.model_used = %s
        AND ep.created_at >= %s
        AND ep.settled = true
        ORDER BY ep.created_at DESC
        """

        try:
            result = await self.supabase.execute_query(
                query,
                (expert_id, family, model.value, cutoff_date)
            )

            if not result.data:
                return None

            # Calculate aggregated metrics
            records = result.data
            games_count = len(records)

            json_validity_rate = sum(1 for r in records if r['json_valid']) / games_count
            latency_p95 = np.percentile([r['latency_ms'] for r in records], 95)
            avg_brier = np.mean([r['brier_score'] for r in records if r['brier_score'] is not None])
            avg_mae = np.mean([r['mae_score'] for r in records if r['mae_score'] is not None])
            avg_roi = np.mean([r['roi'] for r in records if r['roi'] is not None])
            avg_coherence_delta = np.mean([r['coherence_delta'] for r in records if r['coherence_delta'] is not None])

            return ModelMetrics(
                json_validity_rate=json_validity_rate,
                latency_p95=latency_p95,
                brier_score=avg_brier or 0.5,
                mae_score=avg_mae or 1.0,
                roi=avg_roi or 0.0,
                coherence_delta=avg_coherence_delta or 0.0,
                games_count=games_count,
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error retrieving model metrics: {e}")
            return None

    def calculate_model_score(self, metrics: ModelMetrics, family_norms: Dict[str, float]) -> float:
        """
        Calculate composite score for model performance.
        Score = 0.35*(1-brier_norm) + 0.35*(1-mae_norm) + 0.20*roi_norm - 0.10*coherence_norm
        """

        # Normalize metrics against family averages
        brier_norm = metrics.brier_score / family_norms.get('brier', 0.5)
        mae_norm = metrics.mae_score / family_norms.get('mae', 1.0)
        roi_norm = metrics.roi / max(family_norms.get('roi', 0.01), 0.01)  # Avoid division by zero
        coherence_norm = abs(metrics.coherence_delta) / max(family_norms.get('coherence', 0.01), 0.01)

        score = (
            0.35 * (1 - min(brier_norm, 2.0)) +  # Cap at 2x worse than average
            0.35 * (1 - min(mae_norm, 2.0)) +
            0.20 * min(roi_norm, 3.0) -  # Cap at 3x better than average
            0.10 * min(coherence_norm, 2.0)
        )

        return max(score, -1.0)  # Floor at -1.0

    def is_model_eligible(self, metrics: ModelMetrics) -> bool:
        """Check if model meets SLO requirements for traffic allocation"""

        return (
            metrics.json_validity_rate >= self.MIN_JSON_VALIDITY and
            metrics.latency_p95 <= self.MAX_LATENCY_P95_MS and
            metrics.games_count >= 3  # Minimum sample size
        )

    async def get_current_allocations(self, expert_id: str, family: str) -> List[ModelAllocation]:
        """Retrieve current traffic allocations for expert-family combination"""

        query = """
        SELECT model_provider, allocation_pct, is_primary, last_switch
        FROM model_allocations
        WHERE expert_id = %s AND family = %s
        ORDER BY allocation_pct DESC
        """

        try:
            result = await self.supabase.execute_query(query, (expert_id, family))

            allocations = []
            for row in result.data:
                allocations.append(ModelAllocation(
                    model=ModelProvider(row['model_provider']),
                    allocation_pct=row['allocation_pct'],
                    is_primary=row['is_primary'],
                    last_switch=row['last_switch']
                ))

            return allocations

        except Exception as e:
            logger.error(f"Error retrieving current allocations: {e}")
            return self._get_default_allocations(expert_id)

    def _get_default_allocations(self, expert_id: str) -> List[ModelAllocation]:
        """Return default allocations based on initial mapping"""

        mapping = self.initial_mapping.get(expert_id, {})
        primary = mapping.get("primary", ModelProvider.CLAUDE_SONNET)
        explore = mapping.get("explore", [])

        allocations = [ModelAllocation(model=primary, allocation_pct=0.7, is_primary=True)]

        # Distribute exploration traffic
        if explore:
            explore_pct = 0.3 / len(explore)
            for model in explore:
                allocations.append(ModelAllocation(model=model, allocation_pct=explore_pct, is_primary=False))

        return allocations

    async def update_model_allocations(
        self,
        expert_id: str,
        family: str,
        force_evaluation: bool = False
    ) -> List[ModelAllocation]:
        """
        Update traffic allocations based on recent performance.
        Uses multi-armed bandit approach with eligibility gates.
        """

        try:
            # Get current allocations
            current_allocations = await self.get_current_allocations(expert_id, family)

            # Check dwell time for primary model
            primary_allocation = next((a for a in current_allocations if a.is_primary), None)
            if primary_allocation and primary_allocation.last_switch and not force_evaluation:
                time_since_switch = datetime.utcnow() - primary_allocation.last_switch
                if time_since_switch < timedelta(hours=self.MIN_DWELL_TIME_HOURS):
                    logger.info(f"Dwell time not met for {expert_id}/{family}, skipping evaluation")
                    return current_allocations

            # Get metrics for all available models
            available_models = [ModelProvider.CLAUDE_SONNET, ModelProvider.DEEPSEEK_CHAT,
                              ModelProvider.GROK_FAST, ModelProvider.GEMINI_FLASH]

            model_metrics = {}
            family_norms = {'brier': 0.5, 'mae': 1.0, 'roi': 0.0, 'coherence': 0.01}

            for model in available_models:
                metrics = await self.get_model_metrics(expert_id, family, model)
                if metrics:
                    model_metrics[model] = metrics

            if not model_metrics:
                logger.warning(f"No metrics available for {expert_id}/{family}, using defaults")
                return self._get_default_allocations(expert_id)

            # Calculate family norms for normalization
            if len(model_metrics) > 1:
                family_norms['brier'] = np.mean([m.brier_score for m in model_metrics.values()])
                family_norms['mae'] = np.mean([m.mae_score for m in model_metrics.values()])
                family_norms['roi'] = np.mean([m.roi for m in model_metrics.values()])
                family_norms['coherence'] = np.mean([abs(m.coherence_delta) for m in model_metrics.values()])

            # Score and filter eligible models
            eligible_models = []
            for model, metrics in model_metrics.items():
                if self.is_model_eligible(metrics):
                    score = self.calculate_model_score(metrics, family_norms)
                    eligible_models.append((model, score, metrics))

            if not eligible_models:
                logger.warning(f"No eligible models for {expert_id}/{family}, using fallback")
                return [ModelAllocation(model=ModelProvider.CLAUDE_SONNET, allocation_pct=1.0, is_primary=True)]

            # Sort by score (descending)
            eligible_models.sort(key=lambda x: x[1], reverse=True)

            # Allocate traffic using winner-gets-most with minimum exploration
            new_allocations = []
            best_model, best_score, _ = eligible_models[0]

            # Primary gets majority, but leave room for exploration
            primary_pct = max(0.6, 1.0 - self.MIN_EXPLORATION_PCT * (len(eligible_models) - 1))
            new_allocations.append(ModelAllocation(
                model=best_model,
                allocation_pct=primary_pct,
                is_primary=True,
                last_switch=datetime.utcnow() if primary_allocation is None or primary_allocation.model != best_model else primary_allocation.last_switch
            ))

            # Distribute remaining traffic among other eligible models
            if len(eligible_models) > 1:
                remaining_pct = 1.0 - primary_pct
                explore_pct = remaining_pct / (len(eligible_models) - 1)

                for model, score, _ in eligible_models[1:]:
                    new_allocations.append(ModelAllocation(
                        model=model,
                        allocation_pct=explore_pct,
                        is_primary=False
                    ))

            # Store updated allocations
            await self._store_allocations(expert_id, family, new_allocations)

            # Log allocation changes
            if primary_allocation is None or primary_allocation.model != best_model:
                logger.info(f"Model switch for {expert_id}/{family}: {primary_allocation.model if primary_allocation else 'None'} -> {best_model}")

            return new_allocations

        except Exception as e:
            logger.error(f"Error updating model allocations: {e}")
            return current_allocations or self._get_default_allocations(expert_id)

    async def _store_allocations(self, expert_id: str, family: str, allocations: List[ModelAllocation]):
        """Store updated allocations in database"""

        # Delete existing allocations
        delete_query = "DELETE FROM model_allocations WHERE expert_id = %s AND family = %s"
        await self.supabase.execute_query(delete_query, (expert_id, family))

        # Insert new allocations
        insert_query = """
        INSERT INTO model_allocations (expert_id, family, model_provider, allocation_pct, is_primary, last_switch, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for allocation in allocations:
            await self.supabase.execute_query(insert_query, (
                expert_id,
                family,
                allocation.model.value,
                allocation.allocation_pct,
                allocation.is_primary,
                allocation.last_switch,
                datetime.utcnow()
            ))

    async def select_model_for_prediction(self, expert_id: str, family: str) -> ModelProvider:
        """
        Select model for a prediction based on current traffic allocations.
        Uses weighted random selection.
        """

        allocations = await self.get_current_allocations(expert_id, family)

        if not allocations:
            # Fallback to initial mapping
            mapping = self.initial_mapping.get(expert_id, {})
            return mapping.get("primary", ModelProvider.CLAUDE_SONNET)

        # Weighted random selection
        models = [a.model for a in allocations]
        weights = [a.allocation_pct for a in allocations]

        selected_model = np.random.choice(models, p=weights)
        return selected_model

    async def get_critic_repair_model(self, expert_id: str) -> ModelProvider:
        """Get the designated model for Critic/Repair operations (usually Claude Sonnet)"""

        mapping = self.initial_mapping.get(expert_id, {})
        return mapping.get("critic_repair", ModelProvider.CLAUDE_SONNET)

    async def record_prediction_outcome(
        self,
        expert_id: str,
        family: str,
        model: ModelProvider,
        json_valid: bool,
        latency_ms: float,
        brier_score: Optional[float] = None,
        mae_score: Optional[float] = None,
        roi: Optional[float] = None,
        coherence_delta: Optional[float] = None
    ):
        """Record prediction outcome for model performance tracking"""

        insert_query = """
        INSERT INTO model_performance_log (
            expert_id, family, model_provider, json_valid, latency_ms,
            brier_score, mae_score, roi, coherence_delta, recorded_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            await self.supabase.execute_query(insert_query, (
                expert_id, family, model.value, json_valid, latency_ms,
                brier_score, mae_score, roi, coherence_delta, datetime.utcnow()
            ))
        except Exception as e:
            logger.error(f"Error recording prediction outcome: {e}")

    async def get_model_switching_report(self, lookback_days: int = 7) -> Dict:
        """Generate report on model switching activity and performance"""

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get recent switches
        switches_query = """
        SELECT expert_id, family, model_provider, last_switch
        FROM model_allocations
        WHERE is_primary = true AND last_switch >= %s
        ORDER BY last_switch DESC
        """

        switches_result = await self.supabase.execute_query(switches_query, (cutoff_date,))

        # Get performance summary
        performance_query = """
        SELECT
            expert_id, family, model_provider,
            AVG(CASE WHEN json_valid THEN 1.0 ELSE 0.0 END) as validity_rate,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as latency_p95,
            AVG(brier_score) as avg_brier,
            AVG(roi) as avg_roi,
            COUNT(*) as games_count
        FROM model_performance_log
        WHERE recorded_at >= %s
        GROUP BY expert_id, family, model_provider
        ORDER BY expert_id, family, avg_roi DESC
        """

        performance_result = await self.supabase.execute_query(performance_query, (cutoff_date,))

        return {
            "recent_switches": switches_result.data,
            "performance_summary": performance_result.data,
            "report_generated_at": datetime.utcnow().isoformat(),
            "lookback_days": lookback_days
        }
