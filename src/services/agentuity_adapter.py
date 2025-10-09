"""
Agentuity Adapter - Thin wrapper for orchestrating expert predictions via Agentuity agents
Keeps hot path in Postgres/pgvector while leveraging Agentuity for parallelism and telemetry
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from loguru import logger

from src.config import settings


@dataclass
class OrchestrationResult:
    """Result of expert orchestration via Agentuity"""
    game_id: str
    experts_processed: List[str]
    experts_failed: List[str]
    total_duration_ms: int
    retrieval_duration_ms: int
    llm_duration_ms: int
    validation_duration_ms: int
    schema_compliance_rate: float
    shadow_results: Optional[Dict[str, Any]] = None


class AgentuityAdapter:
    """
    Adapter for Agentuity orchestration while keeping hot path in our services
    """

    def __init__(self):
        self.agentuity_base_url = settings.AGENTUITY_BASE_URL
        self.orchestrator_agent_id = settings.AGENTUITY_ORCHESTRATOR_AGENT_ID
        self.reflection_agent_id = settings.AGENTUITY_REFLECTION_AGENT_ID
        self.api_base_url = settings.API_BASE_URL

    async def run_game_orchestration(
        self,
        game_id: str,
        expert_ids: List[str],
        enable_shadow_runs: bool = False,
        shadow_models: Optional[Dict[str, str]] = None
    ) -> OrchestrationResult:
        """
        Orchestrate expert predictions for a game via Agentuity

        Args:
            game_id: NFL game identifier
            expert_ids: List of expert IDs to process
            enable_shadow_runs: Whether to run shadow models in parallel
            shadow_models: Dict mapping expert_id -> alternate_model_name

        Returns:
            OrchestrationResult with telemetry and outcomes
        """
        start_time = time.time()

        payload = {
            "game_id": game_id,
            "expert_ids": expert_ids,
            "api_base_url": self.api_base_url,
            "enable_shadow_runs": enable_shadow_runs,
            "shadow_models": shadow_models or {},
            "orchestration_id": f"orch_{game_id}_{int(start_time)}"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.agentuity_base_url}/agents/{self.orchestrator_agent_id}/run",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.AGENTUITY_API_KEY}"}
                )
                response.raise_for_status()
                result_data = response.json()

            total_duration = int((time.time() - start_time) * 1000)

            return OrchestrationResult(
                game_id=game_id,
                experts_processed=result_data.get("experts_processed", []),
                experts_failed=result_data.get("experts_failed", []),
                total_duration_ms=total_duration,
                retrieval_duration_ms=result_data.get("retrieval_duration_ms", 0),
                llm_duration_ms=result_data.get("llm_duration_ms", 0),
                validation_duration_ms=result_data.get("validation_duration_ms", 0),
                schema_compliance_rate=result_data.get("schema_compliance_rate", 0.0),
                shadow_results=result_data.get("shadow_results")
            )

        except Exception as e:
            logger.error(f"Agentuity orchestration failed for game {game_id}: {e}")
            # Fallback to local execution if Agentuity is unavailable
            return await self._fallback_local_orchestration(game_id, expert_ids)

    async def run_post_game_reflection(
        self,
        game_id: str,
        expert_id: str,
        game_outcome: Dict[str, Any],
        expert_predictions: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Optional post-game reflection via Agentuity ReflectionAgent

        Args:
            game_id: NFL game identifier
            expert_id: Expert who made predictions
            game_outcome: Actual game results
            expert_predictions: Expert's original predictions

        Returns:
            Reflection JSON or None if disabled/failed
        """
        if not settings.ENABLE_POST_GAME_REFLECTION:
            return None

        payload = {
            "game_id": game_id,
            "expert_id": expert_id,
            "game_outcome": game_outcome,
            "expert_predictions": expert_predictions
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.agentuity_base_url}/agents/{self.reflection_agent_id}/run",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.AGENTUITY_API_KEY}"}
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.warning(f"Post-game reflection failed for {expert_id} on game {game_id}: {e}")
            return None

    async def _fallback_local_orchestration(
        self,
        game_id: str,
        expert_ids: List[str]
    ) -> OrchestrationResult:
        """
        Fallback to local expert processing if Agentuity is unavailable
        Rate-limited and degraded functionality
        """
        logger.warning(f"Falling back to local orchestration for game {game_id}")

        start_time = time.time()
        experts_processed = []
        experts_failed = []

        # Import here to avoid circular dependencies
        from src.services.expert_prediction_service import ExpertPredictionService

        expert_service = ExpertPredictionService()

        # Process experts sequentially (degraded mode)
        for expert_id in expert_ids[:4]:  # Limit to 4 experts in fallback
            try:
                await expert_service.generate_predictions(expert_id, game_id)
                experts_processed.append(expert_id)
            except Exception as e:
                logger.error(f"Local expert processing failed for {expert_id}: {e}")
                experts_failed.append(expert_id)

        total_duration = int((time.time() - start_time) * 1000)

        return OrchestrationResult(
            game_id=game_id,
            experts_processed=experts_processed,
            experts_failed=experts_failed,
            total_duration_ms=total_duration,
            retrieval_duration_ms=0,  # Not tracked in fallback
            llm_duration_ms=0,
            validation_duration_ms=0,
            schema_compliance_rate=1.0 if experts_processed else 0.0
        )

    async def get_orchestration_health(self) -> Dict[str, Any]:
        """
        Check Agentuity orchestrator health and availability
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.agentuity_base_url}/agents/{self.orchestrator_agent_id}/health",
                    headers={"Authorization": f"Bearer {settings.AGENTUITY_API_KEY}"}
                )
                response.raise_for_status()
                return {
                    "status": "healthy",
                    "agentuity_available": True,
                    "orchestrator_agent_id": self.orchestrator_agent_id,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except Exception as e:
            return {
                "status": "degraded",
                "agentuity_available": False,
                "error": str(e),
                "fallback_mode": "local_sequential"
            }


# Singleton instance
agentuity_adapter = AgentuityAdapter()
