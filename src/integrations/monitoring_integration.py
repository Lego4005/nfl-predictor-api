"""
Performance Monitoring Integration

Demonstrates how to integte the Performance Monitoring Service
with other Expert Council Betting System components.

This module provides decorators and utilities for automatic
telemetry collection from existing services.

Requirements: 3.3 - Performance monitoring and alerting
"""

import time
import functools
import logging
from typing import Callable, Any, Dict, Optional
from datetime import datetime
import asyncio

from ..services.performance_monitoring_complete import (
    PerformanceMonitoringService, MetricType, AlertSeverity
)

logger = logging.getLogger(__name__)

# Global monitoring service instance
_monitoring_service: Optional[PerformanceMonitoringService] = None

def get_monitoring_service() -> PerformanceMonitoringService:
    """Get or create the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = PerformanceMonitoringService()
    return _monitoring_service

def monitor_performance(
    metric_name: str,
    service: str = "",
    tags: Dict[str, str] = None,
    record_errors: bool = True,
    record_success_rate: bool = True
):
    """
    Decorator to automatically monitor function performance

    Args:
        metric_name: Base name for the metric
        service: Service name for grouping
        tags: Additional tags to include
        record_errors: Whether to record error metrics
        record_success_rate: Whether to record success rate metrics
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitoring = get_monitoring_service()
            start_time = time.time()

            # Prepare tags
            metric_tags = tags.copy() if tags else {}
            metric_tags['function'] = func.__name__
            if service:
                metric_tags['service'] = service

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Record success metrics
                duration_ms = (time.time() - start_time) * 1000
                monitoring.record_metric(f"{metric_name}_latency_ms", duration_ms, metric_tags)

                if record_success_rate:
                    monitoring.record_metric(f"{metric_name}_success_count", 1, metric_tags)

                return result

            except Exception as e:
                # Record error metrics
                if record_errors:
                    monitoring.record_metric(f"{metric_name}_error_count", 1, metric_tags)
                    monitoring.record_metric(f"{metric_name}_errors", 1, {**metric_tags, 'error_type': type(e).__name__})

                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitoring = get_monitoring_service()
            start_time = time.time()

            # Prepare tags
            metric_tags = tags.copy() if tags else {}
            metric_tags['function'] = func.__name__
            if service:
                metric_tags['service'] = service

            try:
                # Execute async function
                result = await func(*args, **kwargs)

                # Record success metrics
                duration_ms = (time.time() - start_time) * 1000
                monitoring.record_metric(f"{metric_name}_latency_ms", duration_ms, metric_tags)

                if record_success_rate:
                    monitoring.record_metric(f"{metric_name}_success_count", 1, metric_tags)

                return result

            except Exception as e:
                # Record error metrics
                if record_errors:
                    monitoring.record_metric(f"{metric_name}_error_count", 1, metric_tags)
                    monitoring.record_metric(f"{metric_name}_errors", 1, {**metric_tags, 'error_type': type(e).__name__})

                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class MonitoringContext:
    """Context manager for monitoring operations"""

    def __init__(self, operation_name: str, service: str = "", tags: Dict[str, str] = None):
        self.operation_name = operation_name
        self.service = service
        self.tags = tags or {}
        self.start_time = None
        self.monitoring = get_monitoring_service()

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000

            # Prepare tags
            metric_tags = self.tags.copy()
            if self.service:
                metric_tags['service'] = self.service

            # Record metrics
            self.monitoring.record_metric(f"{self.operation_name}_latency_ms", duration_ms, metric_tags)

            if exc_type is None:
                # Success
                self.monitoring.record_metric(f"{self.operation_name}_success_count", 1, metric_tags)
            else:
                # Error
                self.monitoring.record_metric(f"{self.operation_name}_error_count", 1, metric_tags)
                self.monitoring.record_metric(f"{self.operation_name}_errors", 1, {**metric_tags, 'error_type': exc_type.__name__})

# Example integrations with existing services

@monitor_performance("vector_retrieval", service="memory_retrieval")
def monitor_vector_retrieval(expert_id: str, game_id: str, k: int = 10):
    """Example: Monitor vector retrieval operations"""
    # Simulate vector retrieval
    import random
    time.sleep(random.uniform(0.05, 0.15))  # 50-150ms

    if random.random() < 0.02:  # 2% failure rate
        raise Exception("Vector retrieval timeout")

    return {
        'memories': [f'memory_{i}' for i in range(k)],
        'similarities': [random.uniform(0.7, 0.95) for _ in range(k)]
    }

@monitor_performance("expert_prediction", service="expert_prediction")
async def monitor_expert_prediction(expert_id: str, game_id: str, context: Dict[str, Any]):
    """Example: Monitor expert prediction generation"""
    # Simulate prediction generation
    import random
    await asyncio.sleep(random.uniform(1.0, 4.0))  # 1-4 seconds

    # Simulate schema validation
    schema_pass = random.random() > 0.02  # 98% pass rate
    if not schema_pass:
        raise ValueError("Schema validation failed")

    # Record additional metrics
    monitoring = get_monitoring_service()
    monitoring.record_metric("schema_validation_pass_rate", 98.5 if schema_pass else 0)
    monitoring.record_metric("critic_repair_loops", random.uniform(0.8, 1.5))

    return {
        'predictions': {'winner': 'home', 'total': 45.5},
        'confidence': random.uniform(0.7, 0.9),
        'schema_valid': schema_pass
    }

@monitor_performance("council_selection", service="council_selection")
def monitor_council_selection(game_id: str, available_experts: list):
    """Example: Monitor council selection process"""
    # Simulate council selection
    import random
    time.sleep(random.uniform(0.02, 0.08))  # 20-80ms

    selected_experts = random.sample(available_experts, min(5, len(available_experts)))

    return {
        'selected_experts': selected_experts,
        'selection_criteria': 'performance_based'
    }

@monitor_performance("coherence_projection", service="coherence_projection")
def monitor_coherence_projection(predictions: Dict[str, Any]):
    """Example: Monitor coherence projection"""
    # Simulate coherence projection
    import random
    time.sleep(random.uniform(0.03, 0.12))  # 30-120ms

    # Record projection latency specifically
    monitoring = get_monitoring_service()
    projection_time = random.uniform(30, 120)
    monitoring.record_metric("coherence_projection_latency_ms", projection_time)

    return {
        'coherent_predictions': predictions,
        'constraints_satisfied': True,
        'projection_time_ms': projection_time
    }

def simulate_system_load():
    """Simulate system load for testing monitoring"""

    print("🔄 Simulating Expert Council Betting System load...")

    experts = ['conservative_analyzer', 'momentum_rider', 'contrarian_rebel', 'value_hunter']
    games = ['KC_vs_BUF_2025_W1', 'DAL_vs_NYG_2025_W1', 'SF_vs_LAR_2025_W1']

    monitoring = get_monitoring_service()

    # Simulate various operations
    for i in range(20):
        try:
            # Vector retrieval
            expert_id = random.choice(experts)
            game_id = random.choice(games)

            with MonitoringContext("memory_lookup", service="memory_retrieval", tags={'expert_id': expert_id}):
                memories = monitor_vector_retrieval(expert_id, game_id, k=random.randint(10, 20))

            # Expert prediction (async simulation)
            async def run_prediction():
                return await monitor_expert_prediction(expert_id, game_id, {'memories': memories})

            # Run async prediction (simplified for demo)
            prediction_result = {
                'predictions': {'winner': 'home', 'total': 45.5},
                'confidence': random.uniform(0.7, 0.9),
                'schema_valid': True
            }

            # Council selection
            council = monitor_council_selection(game_id, experts)

            # Coherence projection
            coherent_slate = monitor_coherence_projection(prediction_result['predictions'])

            # API metrics
            monitoring.record_metric("api_request_count", 1, {'endpoint': '/api/expert/predictions'})
            monitoring.record_metric("api_response_time_ms", random.uniform(100, 500))

            # Occasionally trigger alerts
            if random.random() < 0.1:  # 10% chance
                # High latency
                monitoring.record_metric("vector_retrieval_latency_ms", random.uniform(120, 200))

            if random.random() < 0.05:  # 5% chance
                # Schema failure
                monitoring.record_metric("schema_validation_pass_rate", random.uniform(95, 98))

            if random.random() < 0.03:  # 3% chance
                # API error
                monitoring.record_metric("api_error_rate", random.uniform(6, 12))

            print(f"   Processed operation {i+1}/20: {expert_id} -> {game_id}")
            time.sleep(0.2)  # Brief pause between operations

        except Exception as e:
            print(f"   Operation {i+1} failed: {e}")
            continue

    print("✅ System load simulation complete")

    # Get performance summary
    summary = monitoring.get_performance_summary()
    print(f"\n📊 Performance Summary:")
    print(f"   SLA Compliance: {summary.get('overall_sla_compliance', 0):.1%}")
    print(f"   Active Alerts: {len([a for a in monitoring.alerts.values() if a.is_active])}")
    print(f"   Recommendations: {len(summary.get('recommendations', []))}")

    if summary.get('recommendations'):
        print(f"   Top Recommendation: {summary['recommendations'][0]}")

def setup_monitoring_for_service(service_name: str):
    """Set up monitoring for a specific service"""

    monitoring = get_monitoring_service()

    # Register service-specific metrics
    if service_name == "memory_retrieval":
        monitoring.register_metric(f"{service_name}_cache_hit_rate", MetricType.GAUGE, "Cache hit rate", "percentage", service_name)
        monitoring.register_metric(f"{service_name}_vector_index_size", MetricType.GAUGE, "Vector index size", "count", service_name)
        monitoring.register_metric(f"{service_name}_embedding_quality", MetricType.GAUGE, "Embedding quality score", "score", service_name)

    elif service_name == "expert_prediction":
        monitoring.register_metric(f"{service_name}_token_usage", MetricType.COUNTER, "LLM token usage", "tokens", service_name)
        monitoring.register_metric(f"{service_name}_model_temperature", MetricType.GAUGE, "Model temperature", "value", service_name)
        monitoring.register_metric(f"{service_name}_prompt_length", MetricType.HISTOGRAM, "Prompt length", "characters", service_name)

    elif service_name == "council_selection":
        monitoring.register_metric(f"{service_name}_expert_pool_size", MetricType.GAUGE, "Available expert pool size", "count", service_name)
        monitoring.register_metric(f"{service_name}_selection_diversity", MetricType.GAUGE, "Selection diversity score", "score", service_name)

    elif service_name == "coherence_projection":
        monitoring.register_metric(f"{service_name}_constraint_violations", MetricType.COUNTER, "Constraint violations", "count", service_name)
        monitoring.register_metric(f"{service_name}_projection_accuracy", MetricType.GAUGE, "Projection accuracy", "percentage", service_name)

    # Add service-specific alert rules
    monitoring.add_alert_rule(
        f"{service_name}_high_latency",
        f"{service_name}_latency_ms",
        service_name,
        "gt",
        1000,  # 1 second threshold
        AlertSeverity.WARNING,
        f"{service_name} latency ({{current_value:.1f}}ms) is high"
    )

    monitoring.add_alert_rule(
        f"{service_name}_high_error_rate",
        f"{service_name}_error_count",
        service_name,
        "gt",
        10,  # 10 errors threshold
        AlertSeverity.ERROR,
        f"{service_name} error count ({{current_value}}) is high"
    )

    logger.info(f"Monitoring setup complete for service: {service_name}")

if __name__ == "__main__":
    # Demo the monitoring integration
    print("🧪 Performance Monitoring Integration Demo")
    print("=" * 50)

    # Set up monitoring for all services
    services = ["memory_retrieval", "expert_prediction", "council_selection", "coherence_projection"]
    for service in services:
        setup_monitoring_for_service(service)

    # Simulate system load
    simulate_system_load()

    # Get final dashboard data
    monitoring = get_monitoring_service()
    dashboard_data = monitoring.get_dashboard_data(time_range_minutes=5)

    print(f"\n📈 Final Dashboard Summary:")
    print(f"   Total Metrics: {len(dashboard_data.get('metrics', {}))}")
    print(f"   Active Alerts: {dashboard_data.get('summary', {}).get('active_alerts', 0)}")
    print(f"   Services Monitored: {len(services)}")

    # Shutdown
    monitoring.shutdown()
    print("\n✅ Monitoring integration demo complete")
