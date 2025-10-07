#!/usr/bin/env python3
"""
Training Performance Monitor - Advanced Monitoring and Reporting

Extends existing training_stats tracking with comprehensive performance analysis,
accuracy trends, expert development metrics, usage monitoring, and training
interruption/resumption logic.

Requirements: 7.6, 10.1, 10.2, 10.6
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import logging
import json
import time
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics
from pathlib import Path

from src.ml.training_loop_orchestrator import TrainingStats, TrainingPhase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class PerformanceMetric(Enum):
    """Types of performance metrics to track"""
    API_RESPONSE_TIME = "api_response_time"
    MEMORY_RETRIEVAL_TIME = "memory_retrieval_time"
    PREDICTION_ACCURACY = "prediction_accuracy"
    REFLECTION_QUALITY = "reflection_quality"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

@dataclass
class APIPerformanceMetrics:
    """Detailed API performance tracking"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0

    # Response time statistics
    response_times: List[float] = field(default_factory=list)
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    avg_response_time: float = 0.0
    median_response_time: float = 0.0

    # API usage by model
    model_usage: Dict[str, int] = field(default_factory=dict)
    model_response_times: Dict[str, List[float]] = field(default_factory=dict)

    # Rate limiting tracking
    rate_limit_hits: int = 0
    rate_limit_delays: List[float] = field(default_factory=list)

    def add_api_call(self, model: str, response_time: float, success: bool, timeout: bool = False):
        """Add API call metrics"""
        self.total_calls += 1

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        if timeout:
            self.timeout_calls += 1

        # Track response times for successful calls
        if success and response_time > 0:
            self.response_times.append(response_time)
            self.min_response_time = min(self.min_response_time, response_time)
            self.max_response_time = max(self.max_response_time, response_time)

            # Update averages
            if self.response_times:
                self.avg_response_time = statistics.mean(self.response_times)
                self.median_response_time = statistics.median(self.response_times)

        # Track by model
        if model not in self.model_usage:
            self.model_usage[model] = 0
            self.model_response_times[model] = []

        self.model_usage[model] += 1
        if success and response_time > 0:
            self.model_response_times[model].append(response_time)

    def get_success_rate(self) -> float:
        """Calculate API success rate"""
        return self.successful_calls / max(1, self.total_calls)

    def get_model_performance(self, model: str) -> Dict[str, Any]:
        """Get performance metrics for specific model"""
        if model not in self.model_usage:
            return {}

        response_times = self.model_response_times.get(model, [])

        return {
            'total_calls': self.model_usage[model],
            'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
            'median_response_time': statistics.median(response_times) if response_times else 0.0,
            'min_response_time': min(response_times) if response_times else 0.0,
            'max_response_time': max(response_times) if response_times else 0.0
        }

@dataclass
class ExpertDevelopmentMetrics:
    """Track expert learning and development over time"""
    expert_id: str
    expert_name: str

    # Accuracy progression
    accuracy_history: List[Tuple[datetime, float]] = field(default_factory=list)
    category_accuracy_trends: Dict[str, List[float]] = field(default_factory=dict)

    # Memory utilization
    memories_created: int = 0
    memories_accessed: int = 0
    memory_effectiveness_scores: List[float] = field(default_factory=list)

    # Prediction patterns
    prediction_count: int = 0
    high_confidence_predictions: int = 0
    high_confidence_accuracy: float = 0.0

    # Learning indicators
    improvement_rate: float = 0.0
    consistency_score: float = 0.0
    specialization_strength: float = 0.0

    def add_accuracy_measurement(self, accuracy: float, timestamp: datetime = None):
        """Add accuracy measurement with timestamp"""
        if timestamp is None:
            timestamp = datetime.now()

        self.accuracy_history.append((timestamp, accuracy))

        # Calculate improvement rate (last 10 vs first 10 measurements)
        if len(self.accuracy_history) >= 20:
            recent_scores = [score for _, score in self.accuracy_history[-10:]]
            early_scores = [score for _, score in self.accuracy_history[:10]]

            recent_avg = statistics.mean(recent_scores)
            early_avg = statistics.mean(early_scores)

            self.improvement_rate = recent_avg - early_avg

    def add_category_accuracy(self, category: str, accuracy: float):
        """Add category-specific accuracy"""
        if category not in self.category_accuracy_trends:
            self.category_accuracy_trends[category] = []

        self.category_accuracy_trends[category].append(accuracy)

    def calculate_consistency_score(self) -> float:
        """Calculate prediction consistency (lower variance = higher consistency)"""
        if len(self.accuracy_history) < 5:
            return 0.0

        accuracies = [score for _, score in self.accuracy_history]
        variance = statistics.variance(accuracies)

        # Convert variance to consistency score (0-1, higher is better)
        self.consistency_score = max(0.0, 1.0 - (variance * 4))  # Scale variance
        return self.consistency_score

    def get_current_accuracy(self) -> float:
        """Get most recent accuracy measurement"""
        if not self.accuracy_history:
            return 0.0
        return self.accuracy_history[-1][1]

    def get_accuracy_trend(self) -> str:
        """Determine if expert is improving, declining, or stable"""
        if len(self.accuracy_history) < 10:
            return "insufficient_data"

        recent_scores = [score for _, score in self.accuracy_history[-5:]]
        earlier_scores = [score for _, score in self.accuracy_history[-10:-5]]

        recent_avg = statistics.mean(recent_scores)
        earlier_avg = statistics.mean(earlier_scores)

        diff = recent_avg - earlier_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

@dataclass
class TrainingSession:
    """Represents a training session that can be interrupted and resumed"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Session configuration
    start_season: int = 2020
    end_season: int = 2023
    games_per_season: int = 50
    test_season: int = 2024
    test_games: int = 20

    # Progress tracking
    current_season: int = 2020
    current_game_index: int = 0
    completed_games: List[str] = field(default_factory=list)

    # Session state
    is_active: bool = True
    is_paused: bool = False
    interruption_reason: Optional[str] = None

    # Results
    training_stats: Optional[TrainingStats] = None
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)

    def save_checkpoint(self, file_path: str):
        """Save training session checkpoint"""
        checkpoint = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'start_season': self.start_season,
            'end_season': self.end_season,
            'games_per_season': self.games_per_season,
            'test_season': self.test_season,
            'test_games': self.test_games,
            'current_season': self.current_season,
            'current_game_index': self.current_game_index,
            'completed_games': self.completed_games,
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            'interruption_reason': self.interruption_reason,
            'training_stats': asdict(self.training_stats) if self.training_stats else None,
            'checkpoint_data': self.checkpoint_data
        }

        with open(file_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"💾 Training checkpoint saved: {file_path}")

    @classmethod
    def load_checkpoint(cls, file_path: str) -> 'TrainingSession':
        """Load training session from checkpoint"""
        with open(file_path, 'r') as f:
            checkpoint = json.load(f)

        session = cls(
            session_id=checkpoint['session_id'],
            start_time=datetime.fromisoformat(checkpoint['start_time']),
            end_time=datetime.fromisoformat(checkpoint['end_time']) if checkpoint['end_time'] else None,
            start_season=checkpoint['start_season'],
            end_season=checkpoint['end_season'],
            games_per_season=checkpoint['games_per_season'],
            test_season=checkpoint['test_season'],
            test_games=checkpoint['test_games'],
            current_season=checkpoint['current_season'],
            current_game_index=checkpoint['current_game_index'],
            completed_games=checkpoint['completed_games'],
            is_active=checkpoint['is_active'],
            is_paused=checkpoint['is_paused'],
            interruption_reason=checkpoint['interruption_reason'],
            checkpoint_data=checkpoint['checkpoint_data']
        )

        # Reconstruct training stats if available
        if checkpoint['training_stats']:
            stats_data = checkpoint['training_stats']
            session.training_stats = TrainingStats(
                training_games_processed=stats_data.get('training_games_processed', 0),
                test_games_processed=stats_data.get('test_games_processed', 0),
                total_predictions_made=stats_data.get('total_predictions_made', 0),
                total_memories_created=stats_data.get('total_memories_created', 0),
                total_reflections_generated=stats_data.get('total_reflections_generated', 0),
                expert_accuracies=stats_data.get('expert_accuracies', {}),
                expert_prediction_counts=stats_data.get('expert_prediction_counts', {}),
                expert_memory_counts=stats_data.get('expert_memory_counts', {}),
                category_accuracies=stats_data.get('category_accuracies', {}),
                start_time=stats_data.get('start_time'),
                end_time=stats_data.get('end_time'),
                total_api_calls=stats_data.get('total_api_calls', 0),
                total_api_time=stats_data.get('total_api_time', 0.0),
                average_prediction_time=stats_data.get('average_prediction_time', 0.0),
                errors=stats_data.get('errors', []),
                failed_predictions=stats_data.get('failed_predictions', 0),
                failed_reflections=stats_data.get('failed_reflections', 0),
                current_phase=TrainingPhase(stats_data.get('current_phase', 'initialization')),
                games_by_season=stats_data.get('games_by_season', {})
            )

        logger.info(f"📂 Training checkpoint loaded: {file_path}")
        return session

class TrainingPerformanceMonitor:
    """
    Comprehensive training performance monitor that extends existing training_stats
    tracking with advanced analytics, expert development metrics, and system monitoring.

    Key features:
    - Real-time performance monitoring
    - Expert development tracking
    - API usage and response time analysis
    - Training interruption and resumption
    - Comprehensive reporting and visualization
    """

    def __init__(self, checkpoint_dir: str = "training_checkpoints"):
        """Initialize performance monitor"""

        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

        # Performance tracking
        self.api_metrics = APIPerformanceMetrics()
        self.expert_metrics: Dict[str, ExpertDevelopmentMetrics] = {}

        # Session management
        self.current_session: Optional[TrainingSession] = None
        self.monitoring_active = False

        # Performance thresholds (configurable)
        self.performance_thresholds = {
            'max_api_response_time': 30.0,  # seconds
            'min_success_rate': 0.85,  # 85%
            'max_error_rate': 0.15,  # 15%
            'min_accuracy_improvement': 0.02  # 2% improvement expected
        }

        # Reporting configuration
        self.report_interval = 300  # 5 minutes
        self.last_report_time = time.time()

        logger.info("📊 Training Performance Monitor initialized")
        logger.info(f"   💾 Checkpoint directory: {self.checkpoint_dir}")
        logger.info(f"   📈 Performance thresholds: {self.performance_thresholds}")

    def start_monitoring_session(self, session_config: Dict[str, Any]) -> str:
        """Start a new training monitoring session"""

        session_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = TrainingSession(
            session_id=session_id,
            start_time=datetime.now(),
            start_season=session_config.get('start_season', 2020),
            end_season=session_config.get('end_season', 2023),
            games_per_season=session_config.get('games_per_season', 50),
            test_season=session_config.get('test_season', 2024),
            test_games=session_config.get('test_games', 20)
        )

        self.monitoring_active = True

        logger.info(f"🚀 Started monitoring session: {session_id}")
        logger.info(f"   📅 Training: {self.current_session.start_season}-{self.current_session.end_season}")
        logger.info(f"   🎯 Testing: {self.current_session.test_season}")

        return session_id

    def resume_monitoring_session(self, checkpoint_file: str) -> str:
        """Resume monitoring from checkpoint"""

        checkpoint_path = self.checkpoint_dir / checkpoint_file
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        self.current_session = TrainingSession.load_checkpoint(str(checkpoint_path))
        self.monitoring_active = True

        logger.info(f"🔄 Resumed monitoring session: {self.current_session.session_id}")
        logger.info(f"   📍 Current progress: Season {self.current_session.current_season}, "
                   f"Game {self.current_session.current_game_index}")

        return self.current_session.session_id

    def record_api_call(self, expert_id: str, model: str, response_time: float,
                       success: bool, timeout: bool = False):
        """Record API call performance metrics"""

        self.api_metrics.add_api_call(model, response_time, success, timeout)

        # Check performance thresholds
        if response_time > self.performance_thresholds['max_api_response_time']:
            logger.warning(f"⚠️ Slow API response: {model} took {response_time:.2f}s (threshold: {self.performance_thresholds['max_api_response_time']}s)")

        # Update expert metrics
        if expert_id not in self.expert_metrics:
            self.expert_metrics[expert_id] = ExpertDevelopmentMetrics(
                expert_id=expert_id,
                expert_name=expert_id  # Will be updated with proper name
            )

        self.expert_metrics[expert_id].prediction_count += 1

    def record_expert_accuracy(self, expert_id: str, category: str, accuracy: float,
                             confidence: float = None):
        """Record expert accuracy for performance tracking"""

        if expert_id not in self.expert_metrics:
            self.expert_metrics[expert_id] = ExpertDevelopmentMetrics(
                expert_id=expert_id,
                expert_name=expert_id
            )

        expert_metric = self.expert_metrics[expert_id]
        expert_metric.add_accuracy_measurement(accuracy)
        expert_metric.add_category_accuracy(category, accuracy)

        # Track high confidence predictions
        if confidence and confidence > 0.7:
            expert_metric.high_confidence_predictions += 1
            if accuracy > 0.8:  # High confidence and high accuracy
                expert_metric.high_confidence_accuracy = (
                    (expert_metric.high_confidence_accuracy * (expert_metric.high_confidence_predictions - 1) + accuracy) /
                    expert_metric.high_confidence_predictions
                )

    def record_memory_usage(self, expert_id: str, memories_retrieved: int,
                          memory_effectiveness: float = None):
        """Record memory system usage"""

        if expert_id not in self.expert_metrics:
            self.expert_metrics[expert_id] = ExpertDevelopmentMetrics(
                expert_id=expert_id,
                expert_name=expert_id
            )

        expert_metric = self.expert_metrics[expert_id]
        expert_metric.memories_accessed += memories_retrieved

        if memory_effectiveness is not None:
            expert_metric.memory_effectiveness_scores.append(memory_effectiveness)

    def record_training_progress(self, season: int, game_index: int, game_id: str):
        """Record training progress for checkpoint management"""

        if self.current_session:
            self.current_session.current_season = season
            self.current_session.current_game_index = game_index
            self.current_session.completed_games.append(game_id)

            # Auto-save checkpoint periodically
            if len(self.current_session.completed_games) % 10 == 0:  # Every 10 games
                self.save_checkpoint()

    def save_checkpoint(self):
        """Save current training checkpoint"""

        if not self.current_session:
            logger.warning("⚠️ No active session to checkpoint")
            return

        checkpoint_file = f"{self.current_session.session_id}_checkpoint.json"
        checkpoint_path = self.checkpoint_dir / checkpoint_file

        self.current_session.save_checkpoint(str(checkpoint_path))

    def interrupt_training(self, reason: str):
        """Handle training interruption"""

        if not self.current_session:
            logger.warning("⚠️ No active session to interrupt")
            return

        self.current_session.is_paused = True
        self.current_session.interruption_reason = reason

        # Save checkpoint immediately
        self.save_checkpoint()

        logger.warning(f"⏸️ Training interrupted: {reason}")
        logger.info(f"   💾 Checkpoint saved for resumption")

    def generate_performance_report(self, detailed: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive performance report with expert development metrics.

        Extends existing training_stats tracking with advanced performance analysis.

        Requirements: 7.6, 10.1, 10.2, 10.6
        """

        logger.info("📊 Generating comprehensive performance report...")

        report = {
            'report_timestamp': datetime.now().isoformat(),
            'session_info': {},
            'api_performance': {},
            'expert_development': {},
            'system_performance': {},
            'recommendations': []
        }

        # Session information
        if self.current_session:
            report['session_info'] = {
                'session_id': self.current_session.session_id,
                'start_time': self.current_session.start_time.isoformat(),
                'duration_minutes': (datetime.now() - self.current_session.start_time).total_seconds() / 60,
                'current_season': self.current_session.current_season,
                'games_completed': len(self.current_session.completed_games),
                'is_active': self.current_session.is_active,
                'is_paused': self.current_session.is_paused
            }

        # API Performance Analysis
        report['api_performance'] = {
            'total_calls': self.api_metrics.total_calls,
            'success_rate': self.api_metrics.get_success_rate(),
            'avg_response_time': self.api_metrics.avg_response_time,
            'median_response_time': self.api_metrics.median_response_time,
            'min_response_time': self.api_metrics.min_response_time,
            'max_response_time': self.api_metrics.max_response_time,
            'timeout_rate': self.api_metrics.timeout_calls / max(1, self.api_metrics.total_calls),
            'rate_limit_hits': self.api_metrics.rate_limit_hits,
            'model_performance': {}
        }

        # Model-specific performance
        for model in self.api_metrics.model_usage.keys():
            report['api_performance']['model_performance'][model] = self.api_metrics.get_model_performance(model)

        # Expert Development Analysis
        for expert_id, metrics in self.expert_metrics.items():
            expert_report = {
                'expert_name': metrics.expert_name,
                'predictions_made': metrics.prediction_count,
                'current_accuracy': metrics.get_current_accuracy(),
                'accuracy_trend': metrics.get_accuracy_trend(),
                'improvement_rate': metrics.improvement_rate,
                'consistency_score': metrics.calculate_consistency_score(),
                'memories_accessed': metrics.memories_accessed,
                'memories_created': metrics.memories_created,
                'high_confidence_predictions': metrics.high_confidence_predictions,
                'high_confidence_accuracy': metrics.high_confidence_accuracy,
                'category_performance': {}
            }

            # Category-specific performance
            for category, accuracies in metrics.category_accuracy_trends.items():
                if accuracies:
                    expert_report['category_performance'][category] = {
                        'average_accuracy': statistics.mean(accuracies),
                        'best_accuracy': max(accuracies),
                        'worst_accuracy': min(accuracies),
                        'predictions_count': len(accuracies),
                        'trend': self._calculate_trend(accuracies)
                    }

            report['expert_development'][expert_id] = expert_report

        # System Performance Metrics
        report['system_performance'] = {
            'monitoring_duration_minutes': (datetime.now() - (self.current_session.start_time if self.current_session else datetime.now())).total_seconds() / 60,
            'throughput_calls_per_minute': self.api_metrics.total_calls / max(1, report['system_performance']['monitoring_duration_minutes'] if 'monitoring_duration_minutes' in report['system_performance'] else 1),
            'error_rate': self.api_metrics.failed_calls / max(1, self.api_metrics.total_calls),
            'performance_threshold_violations': self._check_performance_thresholds(),
            'memory_efficiency': self._calculate_memory_efficiency(),
            'prediction_quality_score': self._calculate_prediction_quality_score()
        }

        # Generate recommendations
        report['recommendations'] = self._generate_performance_recommendations(report)

        # Log key insights
        logger.info("📊 PERFORMANCE REPORT SUMMARY:")
        logger.info(f"   🎯 API Success Rate: {report['api_performance']['success_rate']:.1%}")
        logger.info(f"   ⏱️  Avg Response Time: {report['api_performance']['avg_response_time']:.2f}s")
        logger.info(f"   📈 Active Experts: {len(self.expert_metrics)}")
        logger.info(f"   🔄 Total API Calls: {self.api_metrics.total_calls}")

        if detailed:
            # Log top performing experts
            expert_accuracies = [(eid, metrics.get_current_accuracy())
                               for eid, metrics in self.expert_metrics.items()
                               if metrics.prediction_count > 0]
            expert_accuracies.sort(key=lambda x: x[1], reverse=True)

            logger.info("   🏆 Top Performing Experts:")
            for i, (expert_id, accuracy) in enumerate(expert_accuracies[:3], 1):
                logger.info(f"      {i}. {expert_id}: {accuracy:.1%}")

        return report

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values"""
        if len(values) < 3:
            return "insufficient_data"

        # Compare first third vs last third
        first_third = values[:len(values)//3]
        last_third = values[-len(values)//3:]

        first_avg = statistics.mean(first_third)
        last_avg = statistics.mean(last_third)

        diff = last_avg - first_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def _check_performance_thresholds(self) -> List[str]:
        """Check for performance threshold violations"""
        violations = []

        # API response time threshold
        if self.api_metrics.avg_response_time > self.performance_thresholds['max_api_response_time']:
            violations.append(f"Average API response time ({self.api_metrics.avg_response_time:.2f}s) exceeds threshold ({self.performance_thresholds['max_api_response_time']}s)")

        # Success rate threshold
        success_rate = self.api_metrics.get_success_rate()
        if success_rate < self.performance_thresholds['min_success_rate']:
            violations.append(f"API success rate ({success_rate:.1%}) below threshold ({self.performance_thresholds['min_success_rate']:.1%})")

        # Error rate threshold
        error_rate = self.api_metrics.failed_calls / max(1, self.api_metrics.total_calls)
        if error_rate > self.performance_thresholds['max_error_rate']:
            violations.append(f"Error rate ({error_rate:.1%}) exceeds threshold ({self.performance_thresholds['max_error_rate']:.1%})")

        return violations

    def _calculate_memory_efficiency(self) -> float:
        """Calculate overall memory system efficiency"""
        if not self.expert_metrics:
            return 0.0

        total_effectiveness = 0.0
        total_experts = 0

        for metrics in self.expert_metrics.values():
            if metrics.memory_effectiveness_scores:
                total_effectiveness += statistics.mean(metrics.memory_effectiveness_scores)
                total_experts += 1

        return total_effectiveness / max(1, total_experts)

    def _calculate_prediction_quality_score(self) -> float:
        """Calculate overall prediction quality score"""
        if not self.expert_metrics:
            return 0.0

        total_accuracy = 0.0
        total_experts = 0

        for metrics in self.expert_metrics.values():
            if metrics.accuracy_history:
                total_accuracy += metrics.get_current_accuracy()
                total_experts += 1

        return total_accuracy / max(1, total_experts)

    def _generate_performance_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        # API performance recommendations
        api_perf = report['api_performance']
        if api_perf['success_rate'] < 0.9:
            recommendations.append("Consider implementing more robust error handling and retry logic for API calls")

        if api_perf['avg_response_time'] > 15.0:
            recommendations.append("API response times are high - consider optimizing prompts or switching to faster models")

        # Expert development recommendations
        expert_dev = report['expert_development']
        declining_experts = [eid for eid, metrics in expert_dev.items()
                           if metrics['accuracy_trend'] == 'declining']

        if declining_experts:
            recommendations.append(f"Review and adjust prompts/models for declining experts: {', '.join(declining_experts)}")

        low_consistency_experts = [eid for eid, metrics in expert_dev.items()
                                 if metrics['consistency_score'] < 0.6]

        if low_consistency_experts:
            recommendations.append(f"Improve prediction consistency for: {', '.join(low_consistency_experts)}")

        # System performance recommendations
        sys_perf = report['system_performance']
        if sys_perf['error_rate'] > 0.1:
            recommendations.append("High error rate detected - review logs and improve error handling")

        if sys_perf['memory_efficiency'] < 0.6:
            recommendations.append("Memory system efficiency is low - review memory retrieval and relevance scoring")

        return recommendations

    def export_detailed_report(self, file_path: str, format: str = 'json'):
        """Export detailed performance report to file"""

        report = self.generate_performance_report(detailed=True)

        if format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
        elif format.lower() == 'csv':
            # Export key metrics to CSV for analysis
            import csv

            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # Write expert performance data
                writer.writerow(['Expert ID', 'Predictions', 'Current Accuracy', 'Trend', 'Consistency'])
                for expert_id, metrics in report['expert_development'].items():
                    writer.writerow([
                        expert_id,
                        metrics['predictions_made'],
                        f"{metrics['current_accuracy']:.3f}",
                        metrics['accuracy_trend'],
                        f"{metrics['consistency_score']:.3f}"
                    ])

        logger.info(f"📄 Detailed report exported: {file_path}")

# Example usage and testing
async def main():
    """Example usage of the training performance monitor"""

    # Initialize monitor
    monitor = TrainingPerformanceMonitor()

    # Start monitoring session
    session_config = {
        'start_season': 2020,
        'end_season': 2021,
        'games_per_season': 10,
        'test_season': 2024,
        'test_games': 5
    }

    session_id = monitor.start_monitoring_session(session_config)

    # Simulate some training activity
    experts = ['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel']
    models = ['anthropic/claude-sonnet-4.5', 'x-ai/grok-4-fast', 'google/gemini-2.5-flash-preview-09-2025']

    logger.info("🧪 Simulating training activity...")

    for i in range(10):  # Simulate 10 API calls
        expert_id = experts[i % len(experts)]
        model = models[i % len(models)]

        # Simulate API call
        response_time = 5.0 + (i * 0.5)  # Increasing response times
        success = i < 8  # 2 failures out of 10

        monitor.record_api_call(expert_id, model, response_time, success)

        # Simulate accuracy measurement
        accuracy = 0.6 + (i * 0.02)  # Improving accuracy
        confidence = 0.7 + (i * 0.01)

        monitor.record_expert_accuracy(expert_id, 'game_winner', accuracy, confidence)

        # Simulate memory usage
        monitor.record_memory_usage(expert_id, 3 + (i % 3), 0.7 + (i * 0.01))

        # Record progress
        monitor.record_training_progress(2020, i, f"game_{i}")

        await asyncio.sleep(0.1)  # Brief pause

    # Generate and display report
    report = monitor.generate_performance_report(detailed=True)

    print("\\n🎉 Performance monitoring test completed!")
    print(f"📊 Report Summary:")
    print(f"   API Success Rate: {report['api_performance']['success_rate']:.1%}")
    print(f"   Average Response Time: {report['api_performance']['avg_response_time']:.2f}s")
    print(f"   Experts Monitored: {len(report['expert_development'])}")
    print(f"   Recommendations: {len(report['recommendations'])}")

    if report['recommendations']:
        print("\\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")

    # Export report
    monitor.export_detailed_report('test_performance_report.json')

    # Save final checkpoint
    monitor.save_checkpoint()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run the test
    asyncio.run(main())
