"""
Post-Game Reflection Service

Implements optional reflection LLM calls for the Expert Counci System.
Provides post-game analysis and learning insights with environment flag gating,
reflection storage, Neo4j emission with retry/backoff logic, and degraded fallback.

Features:
- Optional reflection LLM calls with environment flag control
- Post-game analysis and learning insights generation
- Reflection storage with comprehensive metadata
- Neo4j emission with retry/backoff logic
- Degraded fallback when reflection fails
- Performance tracking and monitoring

Requirements: 2.6 - Learning & calibration (reflection component)
"""

import logging
import uuid
import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)

class ReflectionStatus(Enum):
    """Status of reflection processing"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

class ReflectionTrigger(Enum):
    """What triggered the reflection"""
    POST_GAME = "post_game"
    POOR_PERFORMANCE = "poor_performance"
    CALIBRATION_DRIFT = "calibration_drift"
    MANUAL = "manual"
    SCHEDULED = "scheduled"

@dataclass
class ReflectionInsight:
    """Individual insight from reflection"""
    insight_id: str
    category: str
    insight_text: str
    confidence: float
    actionable: bool
    factor_adjustments: Dict[str, float] = field(default_factory=dict)
    learning_cues: List[str] = field(default_factory=list)

@dataclass
class ReflectionResult:
    """Result of a reflection session"""
    reflection_id: str
    expert_id: str
    game_id: str
    trigger: ReflectionTrigger

    # Reflection content
    lessons_learned: List[str]
    performance_analysis: str
    factor_recommendations: Dict[str, float]
    calibration_insights: List[str]
    insights: List[ReflectionInsight]

    # Metadata
    reflection_status: ReflectionStatus
    processing_time_ms: float
    model_used: str
    prompt_tokens: int
    completion_tokens: int

    # Context
    game_context: Dict[str, Any]
    performance_metrics: Dict[str, float]
    learning_summary: Dict[str, Any]

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Neo4j emission
    neo4j_emitted: bool = False
    neo4j_emission_attempts: int = 0
    neo4j_last_attempt: Optional[datetime] = None

@dataclass
class ReflectionConfig:
    """Configuration for reflection service"""
    enabled: bool = True
    model_provider: str = "anthropic"
    model_name: str = "claude-3-sonnet-20240229"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout_seconds: int = 30

    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0

    # Neo4j emission
    neo4j_enabled: bool = True
    neo4j_max_retries: int = 5
    neo4j_retry_delay: float = 2.0
    neo4j_backoff_multiplier: float = 1.5

    # Triggering conditions
    trigger_on_poor_performance: bool = True
    poor_performance_threshold: float = 0.3
    trigger_on_calibration_drift: bool = True
    calibration_drift_threshold: float = 0.1

    # Environment flags
    env_flag_key: str = "ENABLE_REFLECTION"
    fallback_mode: str = "graceful"  # "graceful" or "silent"

class ReflectionService:
    """
    Service for post-game reflection and learning insights

    Provides optional reflection LLM calls with environment flag gating,
    reflection storage, and Neo4j emission with retry/backoff logic
    """

    def __init__(self, config: Optional[ReflectionConfig] = None):
        self.config = config or ReflectionConfig()

        # Check environment flag
        self.enabled = self._check_environment_flag()

        # Storage (in production, these would be in database)
        self.reflections: List[ReflectionResult] = []
        self.reflection_queue: List[Dict[str, Any]] = []

        # Performance tracking
        self.processing_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.skip_count = 0
        self.timeout_count = 0

        # Neo4j emission tracking
        self.neo4j_success_count = 0
        self.neo4j_failure_count = 0
        self.neo4j_retry_count = 0

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Mock LLM client (in production, would be real LLM client)
        self.llm_client = None
        self.neo4j_client = None

        logger.info(f"ReflectionService initialized: enabled={self.enabled}")

    def _check_environment_flag(self) -> bool:
        """Check if reflection is enabled via environment flag"""
        try:
            env_value = os.getenv(self.config.env_flag_key, "false").lower()
            enabled = env_value in ["true", "1", "yes", "on", "enabled"]

            if not enabled and self.config.enabled:
                logger.info(f"Reflection disabled by environment flag {self.config.env_flag_key}={env_value}")

            return enabled and self.config.enabled

        except Exception as e:
            logger.error(f"Error checking environment flag: {e}")
            return False

    def trigger_reflection(
        self,
        expert_id: str,
        game_id: str,
        trigger: ReflectionTrigger,
        game_context: Dict[str, Any],
        performance_metrics: Dict[str, float],
        learning_summary: Dict[str, Any]
    ) -> Optional[ReflectionResult]:
        """
        Trigger a reflection session for an expert after a game

        Args:
            expert_id: Expert identifier
            game_id: Game identifier
            trigger: What triggered the reflection
            game_context: Game context information
            performance_metrics: Expert performance metrics
            learning_summary: Summary from learning service

        Returns:
            ReflectionResult if successful, None if skipped or failed
        """
        start_time = datetime.utcnow()

        try:
            # Check if reflection is enabled
            if not self.enabled:
                logger.debug(f"Reflection skipped for {expert_id} - service disabled")
                self.skip_count += 1
                return self._create_skipped_reflection(
                    expert_id, game_id, trigger, "Service disabled"
                )

            # Check triggering conditions
            if not self._should_trigger_reflection(trigger, performance_metrics, learning_summary):
                logger.debug(f"Reflection skipped for {expert_id} - conditions not met")
                self.skip_count += 1
                return self._create_skipped_reflection(
                    expert_id, game_id, trigger, "Triggering conditions not met"
                )

            logger.info(f"Starting reflection for expert {expert_id} in game {game_id}")

            # Create reflection record
            reflection_id = str(uuid.uuid4())

            reflection = ReflectionResult(
                reflection_id=reflection_id,
                expert_id=expert_id,
                game_id=game_id,
                trigger=trigger,
                lessons_learned=[],
                performance_analysis="",
                factor_recommendations={},
                calibration_insights=[],
                insights=[],
                reflection_status=ReflectionStatus.IN_PROGRESS,
                processing_time_ms=0.0,
                model_used=f"{self.config.model_provider}/{self.config.model_name}",
                prompt_tokens=0,
                completion_tokens=0,
                game_context=game_context,
                performance_metrics=performance_metrics,
                learning_summary=learning_summary,
                created_at=start_time
            )

            # Perform reflection with timeout
            try:
                reflection = self._perform_reflection_with_timeout(reflection)

                if reflection.reflection_status == ReflectionStatus.COMPLETED:
                    self.success_count += 1

                    # Emit to Neo4j asynchronously
                    if self.config.neo4j_enabled:
                        self._schedule_neo4j_emission(reflection)

                elif reflection.reflection_status == ReflectionStatus.TIMEOUT:
                    self.timeout_count += 1
                else:
                    self.failure_count += 1

            except Exception as e:
                logger.error(f"Reflection failed for {expert_id}: {e}")
                reflection.reflection_status = ReflectionStatus.FAILED
                reflection.performance_analysis = f"Reflection failed: {str(e)}"
                self.failure_count += 1

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            reflection.processing_time_ms = processing_time
            reflection.completed_at = datetime.utcnow()

            self.processing_times.append(processing_time)

            # Store reflection
            self.reflections.append(reflection)

            logger.info(f"Reflection completed for {expert_id}: "
                       f"status={reflection.reflection_status.value}, "
                       f"time={processing_time:.1f}ms")

            return reflection

        except Exception as e:
            logger.error(f"Reflection trigger failed for {expert_id}: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.processing_times.append(processing_time)
            self.failure_count += 1

            # Return degraded fallback
            return self._create_fallback_reflection(
                expert_id, game_id, trigger, str(e), processing_time
            )

    def _should_trigger_reflection(
        self,
        trigger: ReflectionTrigger,
        performance_metrics: Dict[str, float],
        learning_summary: Dict[str, Any]
    ) -> bool:
        """Determine if reflection should be triggered based on conditions"""

        try:
            # Always trigger manual and scheduled reflections
            if trigger in [ReflectionTrigger.MANUAL, ReflectionTrigger.SCHEDULED]:
                return True

            # Always trigger post-game reflections
            if trigger == ReflectionTrigger.POST_GAME:
                return True

            # Check poor performance trigger
            if trigger == ReflectionTrigger.POOR_PERFORMANCE:
                if not self.config.trigger_on_poor_performance:
                    return False

                avg_score = performance_metrics.get('average_score', 0.5)
                return avg_score < self.config.poor_performance_threshold

            # Check calibration drift trigger
            if trigger == ReflectionTrigger.CALIBRATION_DRIFT:
                if not self.config.trigger_on_calibration_drift:
                    return False

                calibration_change = abs(learning_summary.get('calibration_improvement', 0.0))
                return calibration_change > self.config.calibration_drift_threshold

            return True

        except Exception as e:
            logger.error(f"Error checking trigger conditions: {e}")
            return True  # Default to triggering on error

    def _perform_reflection_with_timeout(self, reflection: ReflectionResult) -> ReflectionResult:
        """Perform reflection with timeout handling"""

        try:
            # Submit reflection task to thread pool with timeout
            future = self.executor.submit(self._perform_reflection, reflection)

            # Wait for completion with timeout
            result = future.result(timeout=self.config.timeout_seconds)
            return result

        except FutureTimeoutError:
            logger.warning(f"Reflection timeout for {reflection.expert_id}")
            reflection.reflection_status = ReflectionStatus.TIMEOUT
            reflection.performance_analysis = "Reflection timed out"
            return reflection

        except Exception as e:
            logger.error(f"Reflection execution error: {e}")
            reflection.reflection_status = ReflectionStatus.FAILED
            reflection.performance_analysis = f"Reflection execution failed: {str(e)}"
            return reflection

    def _perform_reflection(self, reflection: ReflectionResult) -> ReflectionResult:
        """Perform the actual reflection using LLM"""

        try:
            # Generate reflection prompt
            prompt = self._generate_reflection_prompt(reflection)

            # Mock LLM call (in production, would be real LLM API call)
            llm_response = self._mock_llm_call(prompt, reflection.expert_id)

            # Parse LLM response
            parsed_response = self._parse_reflection_response(llm_response)

            # Update reflection with results
            reflection.lessons_learned = parsed_response.get('lessons_learned', [])
            reflection.performance_analysis = parsed_response.get('performance_analysis', '')
            reflection.factor_recommendations = parsed_response.get('factor_recommendations', {})
            reflection.calibration_insights = parsed_response.get('calibration_insights', [])
            reflection.insights = self._create_insights_from_response(parsed_response)

            # Mock token counts
            reflection.prompt_tokens = len(prompt.split()) * 2  # Rough estimate
            reflection.completion_tokens = len(str(parsed_response).split()) * 2

            reflection.reflection_status = ReflectionStatus.COMPLETED

            return reflection

        except Exception as e:
            logger.error(f"Reflection processing failed: {e}")
            reflection.reflection_status = ReflectionStatus.FAILED
            reflection.performance_analysis = f"Processing failed: {str(e)}"
            return reflection

    def _generate_reflection_prompt(self, reflection: ReflectionResult) -> str:
        """Generate reflection prompt for LLM"""

        try:
            expert_id = reflection.expert_id
            game_context = reflection.game_context
            performance_metrics = reflection.performance_metrics
            learning_summary = reflection.learning_summary

            prompt = f"""
You are an expert NFL analyst reflecting on your performance after game {reflection.game_id}.

EXPERT IDENTITY: {expert_id}
GAME CONTEXT: {json.dumps(game_context, indent=2)}

PERFORMANCE METRICS:
{json.dumps(performance_metrics, indent=2)}

LEARNING SUMMARY:
{json.dumps(learning_summary, indent=2)}

Please provide a structured reflection in JSON format with the following fields:

{{
  "lessons_learned": [
    "Key lesson 1",
    "Key lesson 2",
    "Key lesson 3"
  ],
  "performance_analysis": "Detailed analysis of what went well and what didn't",
  "factor_recommendations": {{
    "momentum_factor": 1.05,
    "offensive_efficiency_factor": 0.92
  }},
  "calibration_insights": [
    "Insight about prediction calibration",
    "Insight about confidence levels"
  ],
  "key_insights": [
    {{
      "category": "prediction_accuracy",
      "insight": "Specific insight about accuracy",
      "confidence": 0.8,
      "actionable": true
    }}
  ]
}}

Focus on:
1. What predictions were most/least accurate and why
2. How your confidence calibration performed
3. What factors should be adjusted for future games
4. Specific lessons that can improve future performance

Respond only with valid JSON.
"""

            return prompt.strip()

        except Exception as e:
            logger.error(f"Error generating reflection prompt: {e}")
            return "Error generating prompt"

    def _mock_llm_call(self, prompt: str, expert_id: str) -> Dict[str, Any]:
        """Mock LLM call (in production, would be real LLM API)"""

        try:
            # Simulate processing time
            time.sleep(0.1)

            # Generate mock response based on expert persona
            if "conservative" in expert_id.lower():
                return {
                    "lessons_learned": [
                        "Conservative approach worked well for high-confidence predictions",
                        "Should be more aggressive on clear value opportunities",
                        "Weather conditions affected passing game predictions"
                    ],
                    "performance_analysis": "Overall solid performance with good risk management. Missed some upside on high-confidence plays where being more aggressive could have paid off.",
                    "factor_recommendations": {
                        "momentum_factor": 1.01,
                        "offensive_efficiency_factor": 0.96,
                        "weather_factor": 1.05
                    },
                    "calibration_insights": [
                        "Confidence levels were well-calibrated for defensive predictions",
                        "Slightly overconfident on offensive efficiency metrics"
                    ],
                    "key_insights": [
                        {
                            "category": "risk_management",
                            "insight": "Conservative staking protected bankroll during uncertain game",
                            "confidence": 0.85,
                            "actionable": True
                        },
                        {
                            "category": "weather_impact",
                            "insight": "Weather conditions had larger impact on passing game than expected",
                            "confidence": 0.75,
                            "actionable": True
                        }
                    ]
                }

            elif "momentum" in expert_id.lower():
                return {
                    "lessons_learned": [
                        "Momentum shifts were correctly identified in second half",
                        "Early game momentum indicators were misleading",
                        "Team response to adversity was underestimated"
                    ],
                    "performance_analysis": "Strong performance on momentum-based predictions. Early game reads need improvement, but second-half adjustments were excellent.",
                    "factor_recommendations": {
                        "momentum_factor": 1.08,
                        "home_field_factor": 1.03
                    },
                    "calibration_insights": [
                        "Momentum predictions were well-calibrated in second half",
                        "First quarter momentum reads need recalibration"
                    ],
                    "key_insights": [
                        {
                            "category": "momentum_timing",
                            "insight": "Momentum shifts more predictable after first quarter",
                            "confidence": 0.9,
                            "actionable": True
                        }
                    ]
                }

            else:
                # Generic response
                return {
                    "lessons_learned": [
                        "Prediction accuracy was solid overall",
                        "Confidence calibration needs minor adjustment",
                        "Factor weights performed as expected"
                    ],
                    "performance_analysis": "Balanced performance across categories with room for improvement in calibration.",
                    "factor_recommendations": {
                        "momentum_factor": 1.02,
                        "offensive_efficiency_factor": 0.98
                    },
                    "calibration_insights": [
                        "Overall calibration was reasonable",
                        "High-confidence predictions were well-justified"
                    ],
                    "key_insights": [
                        {
                            "category": "general_performance",
                            "insight": "Consistent performance across prediction categories",
                            "confidence": 0.7,
                            "actionable": False
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Mock LLM call failed: {e}")
            return {
                "lessons_learned": ["Error in reflection processing"],
                "performance_analysis": f"Reflection failed: {str(e)}",
                "factor_recommendations": {},
                "calibration_insights": [],
                "key_insights": []
            }

    def _parse_reflection_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate reflection response"""

        try:
            # Validate required fields
            required_fields = ['lessons_learned', 'performance_analysis', 'factor_recommendations', 'calibration_insights']

            for field in required_fields:
                if field not in response:
                    response[field] = [] if field.endswith('s') else ""

            # Ensure lists are actually lists
            if not isinstance(response.get('lessons_learned'), list):
                response['lessons_learned'] = []

            if not isinstance(response.get('calibration_insights'), list):
                response['calibration_insights'] = []

            if not isinstance(response.get('key_insights'), list):
                response['key_insights'] = []

            # Ensure factor recommendations is a dict
            if not isinstance(response.get('factor_recommendations'), dict):
                response['factor_recommendations'] = {}

            return response

        except Exception as e:
            logger.error(f"Error parsing reflection response: {e}")
            return {
                "lessons_learned": [],
                "performance_analysis": f"Parse error: {str(e)}",
                "factor_recommendations": {},
                "calibration_insights": [],
                "key_insights": []
            }

    def _create_insights_from_response(self, response: Dict[str, Any]) -> List[ReflectionInsight]:
        """Create ReflectionInsight objects from response"""

        try:
            insights = []
            key_insights = response.get('key_insights', [])

            for insight_data in key_insights:
                if isinstance(insight_data, dict):
                    insight = ReflectionInsight(
                        insight_id=str(uuid.uuid4()),
                        category=insight_data.get('category', 'general'),
                        insight_text=insight_data.get('insight', ''),
                        confidence=float(insight_data.get('confidence', 0.5)),
                        actionable=bool(insight_data.get('actionable', False)),
                        factor_adjustments=insight_data.get('factor_adjustments', {}),
                        learning_cues=insight_data.get('learning_cues', [])
                    )
                    insights.append(insight)

            return insights

        except Exception as e:
            logger.error(f"Error creating insights: {e}")
            return []

    def _create_skipped_reflection(
        self,
        expert_id: str,
        game_id: str,
        trigger: ReflectionTrigger,
        reason: str
    ) -> ReflectionResult:
        """Create a skipped reflection record"""

        return ReflectionResult(
            reflection_id=str(uuid.uuid4()),
            expert_id=expert_id,
            game_id=game_id,
            trigger=trigger,
            lessons_learned=[],
            performance_analysis=f"Reflection skipped: {reason}",
            factor_recommendations={},
            calibration_insights=[],
            insights=[],
            reflection_status=ReflectionStatus.SKIPPED,
            processing_time_ms=0.0,
            model_used="none",
            prompt_tokens=0,
            completion_tokens=0,
            game_context={},
            performance_metrics={},
            learning_summary={},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

    def _create_fallback_reflection(
        self,
        expert_id: str,
        game_id: str,
        trigger: ReflectionTrigger,
        error: str,
        processing_time: float
    ) -> ReflectionResult:
        """Create a fallback reflection when processing fails"""

        return ReflectionResult(
            reflection_id=str(uuid.uuid4()),
            expert_id=expert_id,
            game_id=game_id,
            trigger=trigger,
            lessons_learned=["Reflection processing failed - using fallback"],
            performance_analysis=f"Degraded fallback: {error}",
            factor_recommendations={},
            calibration_insights=["Unable to generate calibration insights"],
            insights=[],
            reflection_status=ReflectionStatus.FAILED,
            processing_time_ms=processing_time,
            model_used="fallback",
            prompt_tokens=0,
            completion_tokens=0,
            game_context={},
            performance_metrics={},
            learning_summary={},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

    def _schedule_neo4j_emission(self, reflection: ReflectionResult) -> None:
        """Schedule Neo4j emission for reflection"""

        try:
            # Add to emission queue
            emission_task = {
                'reflection_id': reflection.reflection_id,
                'scheduled_at': datetime.utcnow(),
                'attempts': 0
            }

            self.reflection_queue.append(emission_task)

            # Submit to thread pool for async processing
            self.executor.submit(self._emit_to_neo4j, reflection)

        except Exception as e:
            logger.error(f"Error scheduling Neo4j emission: {e}")

    def _emit_to_neo4j(self, reflection: ReflectionResult) -> bool:
        """Emit reflection to Neo4j with retry logic"""

        max_retries = self.config.neo4j_max_retries
        retry_delay = self.config.neo4j_retry_delay

        for attempt in range(max_retries + 1):
            try:
                reflection.neo4j_emission_attempts = attempt + 1
                reflection.neo4j_last_attempt = datetime.utcnow()

                # Mock Neo4j emission (in production, would be real Neo4j client)
                success = self._mock_neo4j_emission(reflection)

                if success:
                    reflection.neo4j_emitted = True
                    self.neo4j_success_count += 1
                    logger.info(f"Neo4j emission successful for reflection {reflection.reflection_id}")
                    return True

                # If not the last attempt, wait before retrying
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= self.config.neo4j_backoff_multiplier
                    self.neo4j_retry_count += 1

            except Exception as e:
                logger.error(f"Neo4j emission attempt {attempt + 1} failed: {e}")

                if attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= self.config.neo4j_backoff_multiplier
                    self.neo4j_retry_count += 1

        # All attempts failed
        self.neo4j_failure_count += 1
        logger.error(f"Neo4j emission failed after {max_retries + 1} attempts for reflection {reflection.reflection_id}")
        return False

    def _mock_neo4j_emission(self, reflection: ReflectionResult) -> bool:
        """Mock Neo4j emission (in production, would be real Neo4j operations)"""

        try:
            # Simulate Neo4j operations
            time.sleep(0.05)  # Simulate network latency

            # Mock occasional failures for testing retry logic
            import random
            if random.random() < 0.1:  # 10% failure rate
                raise Exception("Mock Neo4j connection error")

            # Mock Neo4j node and relationship creation
            neo4j_operations = {
                'create_reflection_node': {
                    'reflection_id': reflection.reflection_id,
                    'expert_id': reflection.expert_id,
                    'game_id': reflection.game_id,
                    'status': reflection.reflection_status.value,
                    'created_at': reflection.created_at.isoformat()
                },
                'create_insights': [
                    {
                        'insight_id': insight.insight_id,
                        'category': insight.category,
                        'confidence': insight.confidence,
                        'actionable': insight.actionable
                    }
                    for insight in reflection.insights
                ],
                'create_relationships': [
                    f"(Expert:{reflection.expert_id})-[:REFLECTED_ON]->(Game:{reflection.game_id})",
                    f"(Reflection:{reflection.reflection_id})-[:LEARNED_FROM]->(Game:{reflection.game_id})"
                ]
            }

            logger.debug(f"Mock Neo4j emission: {json.dumps(neo4j_operations, indent=2)}")
            return True

        except Exception as e:
            logger.error(f"Mock Neo4j emission failed: {e}")
            return False

    def get_reflection_history(
        self,
        expert_id: Optional[str] = None,
        game_id: Optional[str] = None,
        status: Optional[ReflectionStatus] = None,
        limit: Optional[int] = None
    ) -> List[ReflectionResult]:
        """Get reflection history with optional filters"""

        try:
            filtered_reflections = self.reflections.copy()

            if expert_id:
                filtered_reflections = [r for r in filtered_reflections if r.expert_id == expert_id]

            if game_id:
                filtered_reflections = [r for r in filtered_reflections if r.game_id == game_id]

            if status:
                filtered_reflections = [r for r in filtered_reflections if r.reflection_status == status]

            # Sort by creation time (newest first)
            filtered_reflections.sort(key=lambda r: r.created_at, reverse=True)

            if limit:
                filtered_reflections = filtered_reflections[:limit]

            return filtered_reflections

        except Exception as e:
            logger.error(f"Error getting reflection history: {e}")
            return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get reflection service performance metrics"""

        try:
            total_reflections = self.success_count + self.failure_count + self.skip_count + self.timeout_count

            if not self.processing_times:
                return {
                    'enabled': self.enabled,
                    'total_reflections': total_reflections,
                    'success_rate': 0.0,
                    'average_time_ms': 0.0,
                    'counts': {
                        'success': self.success_count,
                        'failure': self.failure_count,
                        'skip': self.skip_count,
                        'timeout': self.timeout_count
                    },
                    'neo4j_metrics': {
                        'success': self.neo4j_success_count,
                        'failure': self.neo4j_failure_count,
                        'retry': self.neo4j_retry_count
                    }
                }

            import numpy as np
            times = np.array(self.processing_times)

            return {
                'enabled': self.enabled,
                'total_reflections': total_reflections,
                'success_rate': self.success_count / max(total_reflections, 1),
                'average_time_ms': float(np.mean(times)),
                'p95_time_ms': float(np.percentile(times, 95)),
                'p99_time_ms': float(np.percentile(times, 99)),
                'max_time_ms': float(np.max(times)),
                'counts': {
                    'success': self.success_count,
                    'failure': self.failure_count,
                    'skip': self.skip_count,
                    'timeout': self.timeout_count
                },
                'neo4j_metrics': {
                    'success': self.neo4j_success_count,
                    'failure': self.neo4j_failure_count,
                    'retry': self.neo4j_retry_count,
                    'success_rate': self.neo4j_success_count / max(self.neo4j_success_count + self.neo4j_failure_count, 1)
                },
                'config': {
                    'timeout_seconds': self.config.timeout_seconds,
                    'max_retries': self.config.max_retries,
                    'neo4j_enabled': self.config.neo4j_enabled,
                    'model': f"{self.config.model_provider}/{self.config.model_name}"
                }
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update reflection configuration"""

        try:
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    old_value = getattr(self.config, key)
                    setattr(self.config, key, value)
                    logger.info(f"Updated config {key}: {old_value} -> {value}")
                else:
                    logger.warning(f"Unknown config key: {key}")

            # Re-check environment flag if enabled status changed
            if 'enabled' in config_updates:
                self.enabled = self._check_environment_flag()

            return True

        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False

    def clear_all_data(self) -> None:
        """Clear all reflection data (for testing)"""
        self.reflections.clear()
        self.reflection_queue.clear()
        self.processing_times.clear()
        self.success_count = 0
        self.failure_count = 0
        self.skip_count = 0
        self.timeout_count = 0
        self.neo4j_success_count = 0
        self.neo4j_failure_count = 0
        self.neo4j_retry_count = 0

    def __del__(self):
        """Cleanup thread pool on destruction"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except:
            pass
