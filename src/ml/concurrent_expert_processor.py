#!/usr/bin/env python3
"""
Concurrent Expert Analysis Processor

Implements concurrent processing of expert analysis to improve performance
while respecting rate limits ance constraints.

Requirements: 10.1, 10.2, 10.3
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Awaitable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

from .performance_monitor import PerformanceMonitor, PerformanceMetricType, performance_timer
from .api_rate_limiter import APICallManager, get_api_call_manager

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Expert processing strategies"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BATCH = "batch"
    PRIORITY_BASED = "priority_based"


@dataclass
class ExpertTask:
    """Individual expert analysis task"""
    expert_id: str
    expert_name: str
    game_context: Any  # GameContext object
    priority: int = 5  # 1-10, higher is more important
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None

    def __post_init__(self):
        if not 1 <= self.priority <= 10:
            raise ValueError(f"Priority must be between 1 and 10, got {self.priority}")

    @property
    def duration_ms(self) -> Optional[float]:
        """Get task duration in milliseconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.completed_at is not None

    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully"""
        return self.is_completed and self.error is None


@dataclass
class ProcessingResult:
    """Result of concurrent expert processing"""
    total_experts: int
    successful_experts: int
    failed_experts: int
    total_duration_ms: float
    expert_results: Dict[str, Any]
    expert_errors: Dict[str, Exception]
    processing_stats: Dict[str, Any]


class ConcurrentExpertProcessor:
    """
    Manages concurrent processing of expert analysis with intelligent
    resource management and performance optimization.
    """

    def __init__(
        self,
        max_concurrent_experts: int = 5,
        max_concurrent_per_provider: int = 2,
        performance_monitor: Optional[PerformanceMonitor] = None,
        api_call_manager: Optional[APICallManager] = None
    ):
        self.max_concurrent_experts = max_concurrent_experts
        self.max_concurrent_per_provider = max_concurrent_per_provider
        self.performance_monitor = performance_monitor
        self.api_call_manager = api_call_manager or get_api_call_manager()

        # Provider tracking for rate limiting
        self.provider_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.provider_usage: Dict[str, int] = {}

        # Task queue and processing state
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_tasks: Dict[str, ExpertTask] = {}
        self.completed_tasks: List[ExpertTask] = []

        # Threading and async coordination
        self._processing_lock = threading.Lock()

        # Initialize provider semaphores for common providers
        common_providers = ['openai', 'anthropic', 'google', 'x-ai', 'deepseek']
        for provider in common_providers:
            self.provider_semaphores[provider] = asyncio.Semaphore(max_concurrent_per_provider)
            self.provider_usage[provider] = 0

        logger.info(f"✅ Concurrent Expert Processor initialized "
                   f"(max_concurrent={max_concurrent_experts}, "
                   f"max_per_provider={max_concurrent_per_provider})")

    def _get_provider_from_expert_model(self, expert_id: str, expert_model_mapping: Dict[str, Any]) -> str:
        """Extract provider from expert model assignment"""
        if expert_id in expert_model_mapping:
            model = expert_model_mapping[expert_id].get('model', '')
            if '/' in model:
                return model.split('/')[0]
        return 'unknown'

    async def process_experts_concurrent(
        self,
        expert_tasks: List[ExpertTask],
        orchestrator_function: Callable[[str, Any], Awaitable[Any]],
        expert_model_mapping: Dict[str, Any],
        strategy: ProcessingStrategy = ProcessingStrategy.PARALLEL
    ) -> ProcessingResult:
        """
        Process multiple experts concurrently with intelligent resource management.

        Args:
            expert_tasks: List of expert tasks to process
            orchestrator_function: Function to call for each expert analysis
            expert_model_mapping: Mapping of expert IDs to model configurations
            strategy: Processing strategy to use

        Returns:
            ProcessingResult with all expert results and statistics
        """
        start_time = time.time()

        logger.info(f"🚀 Starting concurrent processing of {len(expert_tasks)} experts using {strategy.value} strategy")

        # Choose processing method based on strategy
        if strategy == ProcessingStrategy.SEQUENTIAL:
            result = await self._process_sequential(expert_tasks, orchestrator_function, expert_model_mapping)
        elif strategy == ProcessingStrategy.PARALLEL:
            result = await self._process_parallel(expert_tasks, orchestrator_function, expert_model_mapping)
        elif strategy == ProcessingStrategy.BATCH:
            result = await self._process_batch(expert_tasks, orchestrator_function, expert_model_mapping)
        elif strategy == ProcessingStrategy.PRIORITY_BASED:
            result = await self._process_priority_based(expert_tasks, orchestrator_function, expert_model_mapping)
        else:
            raise ValueError(f"Unknown processing strategy: {strategy}")

        total_duration = (time.time() - start_time) * 1000
        result.total_duration_ms = total_duration

        # Record performance metrics
        if self.performance_monitor:
            self.performance_monitor.record_metric(
                metric_type=PerformanceMetricType.THROUGHPUT,
                operation_name="concurrent_expert_processing",
                duration_ms=total_duration,
                metadata={
                    'strategy': strategy.value,
                    'total_experts': len(expert_tasks),
                    'successful_experts': result.successful_experts,
                    'failed_experts': result.failed_experts
                }
            )

        logger.info(f"✅ Concurrent processing completed in {total_duration:.0f}ms: "
                   f"{result.successful_experts}/{len(expert_tasks)} successful")

        return result

    async def _process_sequential(
        self,
        expert_tasks: List[ExpertTask],
        orchestrator_function: Callable[[str, Any], Awaitable[Any]],
        expert_model_mapping: Dict[str, Any]
    ) -> ProcessingResult:
        """Process experts sequentially (fallback for debugging)"""
        expert_results = {}
        expert_errors = {}

        for task in expert_tasks:
            try:
                task.started_at = datetime.now()

                with performance_timer(
                    PerformanceMetricType.RESPONSE_TIME,
                    f"expert_analysis_{task.expert_id}",
                    task.expert_id
                ) if self.performance_monitor else nullcontext():
                    result = await orchestrator_function(task.expert_id, task.game_context)

                task.result = result
                task.completed_at = datetime.now()
                expert_results[task.expert_id] = result

            except Exception as e:
                task.error = e
                task.completed_at = datetime.now()
                expert_errors[task.expert_id] = e
                logger.error(f"❌ Expert {task.expert_id} failed: {e}")

        return ProcessingResult(
            total_experts=len(expert_tasks),
            successful_experts=len(expert_results),
            failed_experts=len(expert_errors),
            total_duration_ms=0.0,  # Will be set by caller
            expert_results=expert_results,
            expert_errors=expert_errors,
            processing_stats={'strategy': 'sequential'}
        )

    async def _process_parallel(
        self,
        expert_tasks: List[ExpertTask],
        orchestrator_function: Callable[[str, Any], Awaitable[Any]],
        expert_model_mapping: Dict[str, Any]
    ) -> ProcessingResult:
        """Process experts in parallel with provider-based rate limiting"""
        semaphore = asyncio.Semaphore(self.max_concurrent_experts)
        expert_results = {}
        expert_errors = {}

        async def process_single_expert(task: ExpertTask) -> Tuple[str, Any, Optional[Exception]]:
            """Process a single expert with rate limiting"""
            provider = self._get_provider_from_expert_model(task.expert_id, expert_model_mapping)
            provider_semaphore = self.provider_semaphores.get(provider, asyncio.Semaphore(1))

            async with semaphore:  # Global concurrency limit
                async with provider_semaphore:  # Provider-specific limit
                    try:
                        task.started_at = datetime.now()

                        # Track provider usage
                        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1

                        with performance_timer(
                            PerformanceMetricType.RESPONSE_TIME,
                            f"expert_analysis_{task.expert_id}",
                            task.expert_id
                        ) if self.performance_monitor else nullcontext():
                            result = await orchestrator_function(task.expert_id, task.game_context)

                        task.result = result
                        task.completed_at = datetime.now()

                        return task.expert_id, result, None

                    except Exception as e:
                        task.error = e
                        task.completed_at = datetime.now()
                        logger.error(f"❌ Expert {task.expert_id} failed: {e}")
                        return task.expert_id, None, e

                    finally:
                        # Decrease provider usage
                        self.provider_usage[provider] = max(0, self.provider_usage.get(provider, 0) - 1)

        # Create tasks for all experts
        tasks = [process_single_expert(task) for task in expert_tasks]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                # Handle gather exceptions
                expert_id = "unknown"
                expert_errors[expert_id] = result
            else:
                expert_id, expert_result, error = result
                if error:
                    expert_errors[expert_id] = error
                else:
                    expert_results[expert_id] = expert_result

        return ProcessingResult(
            total_experts=len(expert_tasks),
            successful_experts=len(expert_results),
            failed_experts=len(expert_errors),
            total_duration_ms=0.0,  # Will be set by caller
            expert_results=expert_results,
            expert_errors=expert_errors,
            processing_stats={
                'strategy': 'parallel',
                'max_concurrent': self.max_concurrent_experts,
                'provider_usage': dict(self.provider_usage)
            }
        )

    async def _process_batch(
        self,
        expert_tasks: List[ExpertTask],
        orchestrator_function: Callable[[str, Any], Awaitable[Any]],
        expert_model_mapping: Dict[str, Any]
    ) -> ProcessingResult:
        """Process experts in batches to manage resource usage"""
        batch_size = min(self.max_concurrent_experts, len(expert_tasks))
        expert_results = {}
        expert_errors = {}

        # Process in batches
        for i in range(0, len(expert_tasks), batch_size):
            batch = expert_tasks[i:i + batch_size]
            logger.info(f"📦 Processing batch {i//batch_size + 1}: {len(batch)} experts")

            # Process current batch in parallel
            batch_result = await self._process_parallel(batch, orchestrator_function, expert_model_mapping)

            # Merge results
            expert_results.update(batch_result.expert_results)
            expert_errors.update(batch_result.expert_errors)

            # Small delay between batches to prevent overwhelming APIs
            if i + batch_size < len(expert_tasks):
                await asyncio.sleep(0.5)

        return ProcessingResult(
            total_experts=len(expert_tasks),
            successful_experts=len(expert_results),
            failed_experts=len(expert_errors),
            total_duration_ms=0.0,  # Will be set by caller
            expert_results=expert_results,
            expert_errors=expert_errors,
            processing_stats={
                'strategy': 'batch',
                'batch_size': batch_size,
                'total_batches': (len(expert_tasks) + batch_size - 1) // batch_size
            }
        )

    async def _process_priority_based(
        self,
        expert_tasks: List[ExpertTask],
        orchestrator_function: Callable[[str, Any], Awaitable[Any]],
        expert_model_mapping: Dict[str, Any]
    ) -> ProcessingResult:
        """Process experts based on priority, with high-priority experts first"""
        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(expert_tasks, key=lambda t: t.priority, reverse=True)

        # Group by priority levels
        priority_groups = {}
        for task in sorted_tasks:
            if task.priority not in priority_groups:
                priority_groups[task.priority] = []
            priority_groups[task.priority].append(task)

        expert_results = {}
        expert_errors = {}

        # Process each priority group
        for priority in sorted(priority_groups.keys(), reverse=True):
            group = priority_groups[priority]
            logger.info(f"⭐ Processing priority {priority} group: {len(group)} experts")

            # Process group in parallel
            group_result = await self._process_parallel(group, orchestrator_function, expert_model_mapping)

            # Merge results
            expert_results.update(group_result.expert_results)
            expert_errors.update(group_result.expert_errors)

            # Small delay between priority groups
            if priority > min(priority_groups.keys()):
                await asyncio.sleep(0.2)

        return ProcessingResult(
            total_experts=len(expert_tasks),
            successful_experts=len(expert_results),
            failed_experts=len(expert_errors),
            total_duration_ms=0.0,  # Will be set by caller
            expert_results=expert_results,
            expert_errors=expert_errors,
            processing_stats={
                'strategy': 'priority_based',
                'priority_groups': {str(p): len(g) for p, g in priority_groups.items()}
            }
        )

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'max_concurrent_experts': self.max_concurrent_experts,
            'max_concurrent_per_provider': self.max_concurrent_per_provider,
            'provider_usage': dict(self.provider_usage),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'provider_semaphores': {p: s._value for p, s in self.provider_semaphores.items()}
        }


# Utility context manager for null context when performance monitor is not available
class nullcontext:
    """Null context manager for when performance monitoring is disabled"""
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# Global processor instance
_global_processor: Optional[ConcurrentExpertProcessor] = None


def get_concurrent_expert_processor() -> ConcurrentExpertProcessor:
    """Get the global concurrent expert processor instance"""
    global _global_processor
    if _global_processor is None:
        _global_processor = ConcurrentExpertProcessor()
    return _global_processor
