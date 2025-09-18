"""
Learning Pipeline Integration

Integrates all continuous learning components to work seamlessly with the
existing NFL prediction system. This module provides a unified interface
for all learning activities.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import all learning components
try:
    from .continuous_learner import ContinuousLearner
    from .learning_coordinator import LearningCoordinator
    from .belief_revision_service import BeliefRevisionService
    from .episodic_memory_manager import EpisodicMemoryManager
    from .expert_memory_service import ExpertMemoryService
    from ..monitoring.prediction_monitor import PredictionMonitor
except ImportError as e:
    print(f"Warning: Could not import some learning components: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningPipelineIntegration:
    """
    Unified interface for all continuous learning components

    This class orchestrates the interaction between:
    - Continuous learner for online model updates
    - Learning coordinator for expert performance tracking
    - Belief revision service for expert belief updates
    - Episodic memory manager for experience storage
    - Expert memory service for knowledge management
    - Prediction monitor for real-time tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()

        # Initialize all components
        self.continuous_learner = None
        self.learning_coordinator = None
        self.belief_service = None
        self.memory_manager = None
        self.expert_memory = None
        self.prediction_monitor = None

        # Integration state
        self.active_experts = set()
        self.registered_models = {}
        self.learning_active = True

        self._initialize_components()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the learning pipeline"""
        return {
            'continuous_learning': {
                'enabled': True,
                'learning_rate': 0.01,
                'drift_threshold': 0.1,
                'window_size': 50
            },
            'belief_revision': {
                'enabled': True,
                'revision_threshold': 0.3,
                'min_evidence': 5
            },
            'memory_management': {
                'enabled': True,
                'compression_threshold': 100,
                'decay_rate': 0.995
            },
            'monitoring': {
                'enabled': True,
                'alert_thresholds': {
                    'accuracy': 0.6,
                    'drift': 0.3
                }
            },
            'integration': {
                'auto_register_experts': True,
                'sync_frequency': 60,  # seconds
                'batch_size': 10
            }
        }

    def _initialize_components(self):
        """Initialize all learning components"""
        try:
            logger.info("Initializing learning pipeline components...")

            # Initialize continuous learner
            if self.config['continuous_learning']['enabled']:
                self.continuous_learner = ContinuousLearner()
                logger.info("✅ Continuous learner initialized")

            # Initialize learning coordinator
            self.learning_coordinator = LearningCoordinator()
            logger.info("✅ Learning coordinator initialized")

            # Initialize belief revision service
            if self.config['belief_revision']['enabled']:
                self.belief_service = BeliefRevisionService()
                logger.info("✅ Belief revision service initialized")

            # Initialize memory components
            if self.config['memory_management']['enabled']:
                self.memory_manager = EpisodicMemoryManager()
                self.expert_memory = ExpertMemoryService(supabase_client=None)
                logger.info("✅ Memory components initialized")

            # Initialize prediction monitor
            if self.config['monitoring']['enabled']:
                self.prediction_monitor = PredictionMonitor()
                logger.info("✅ Prediction monitor initialized")

            logger.info("🚀 Learning pipeline integration ready!")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def register_expert(self, expert_id: str, expert_config: Optional[Dict[str, Any]] = None):
        """
        Register an expert with all learning components

        Args:
            expert_id: Unique identifier for the expert
            expert_config: Optional configuration for the expert
        """
        try:
            logger.info(f"Registering expert: {expert_id}")

            expert_config = expert_config or {}

            # Register with learning coordinator
            specialty_areas = expert_config.get('specialties', [])
            initial_weight = expert_config.get('initial_weight', 1.0)

            self.learning_coordinator.register_expert(
                expert_id=expert_id,
                initial_weight=initial_weight,
                specialty_areas=specialty_areas
            )

            # Add to active experts
            self.active_experts.add(expert_id)

            logger.info(f"✅ Expert {expert_id} registered successfully")

        except Exception as e:
            logger.error(f"Failed to register expert {expert_id}: {e}")

    def register_model(self, model_id: str, model, model_config: Optional[Dict[str, Any]] = None):
        """
        Register a model with the continuous learner

        Args:
            model_id: Unique identifier for the model
            model: The actual model object
            model_config: Optional configuration for the model
        """
        try:
            logger.info(f"Registering model: {model_id}")

            if self.continuous_learner:
                self.continuous_learner.register_model(model_id, model)
                self.registered_models[model_id] = {
                    'model': model,
                    'config': model_config or {},
                    'registered_at': datetime.now()
                }

                logger.info(f"✅ Model {model_id} registered successfully")

        except Exception as e:
            logger.error(f"Failed to register model {model_id}: {e}")

    def process_prediction_outcome(self, outcome_data: Dict[str, Any]):
        """
        Process a prediction outcome through all learning components

        Args:
            outcome_data: Comprehensive outcome data including:
                - prediction_id: Unique prediction identifier
                - expert_id: Expert who made the prediction
                - game_id: Game identifier
                - prediction_type: Type of prediction (spread, total, etc.)
                - predicted_value: The prediction value
                - confidence: Confidence level (0-1)
                - actual_value: The actual outcome
                - context: Additional context data
        """
        try:
            logger.info(f"Processing prediction outcome: {outcome_data.get('prediction_id')}")

            # Extract common data
            expert_id = outcome_data['expert_id']
            game_id = outcome_data['game_id']
            predicted_value = outcome_data['predicted_value']
            actual_value = outcome_data['actual_value']
            confidence = outcome_data['confidence']
            context = outcome_data.get('context', {})

            # 1. Update learning coordinator
            self.learning_coordinator.record_prediction_outcome(
                prediction_id=outcome_data['prediction_id'],
                expert_id=expert_id,
                game_id=game_id,
                prediction_type=outcome_data['prediction_type'],
                predicted_value=predicted_value,
                confidence=confidence,
                actual_value=actual_value,
                context=context
            )

            # 2. Update continuous learner if models are registered
            if self.continuous_learner and self.registered_models:
                features = self._extract_features_from_context(context)
                predictions = {expert_id: predicted_value}
                actuals = {expert_id: actual_value}

                self.continuous_learner.process_game_outcome(
                    game_id=game_id,
                    predictions=predictions,
                    actual_results=actuals,
                    features=features
                )

            # 3. Update prediction monitor
            if self.prediction_monitor:
                response_time = context.get('response_time', 0.0)
                self.prediction_monitor.record_prediction(
                    expert_id=expert_id,
                    prediction=predicted_value,
                    actual=actual_value,
                    confidence=confidence,
                    response_time=response_time
                )

            # 4. Update episodic memory
            if self.memory_manager:
                episode = {
                    'type': 'prediction_outcome',
                    'expert_id': expert_id,
                    'game_id': game_id,
                    'prediction_type': outcome_data['prediction_type'],
                    'was_correct': self._was_prediction_correct(predicted_value, actual_value),
                    'error_magnitude': abs(predicted_value - actual_value),
                    'confidence': confidence,
                    'context': context,
                    'timestamp': datetime.now()
                }

                self.memory_manager.store_episode(episode)

            # 5. Update expert memory
            if self.expert_memory:
                prediction_outcome = {
                    'was_correct': self._was_prediction_correct(predicted_value, actual_value),
                    'error_magnitude': abs(predicted_value - actual_value),
                    'confidence': confidence,
                    'prediction_type': outcome_data['prediction_type'],
                    'context': context
                }

                self.expert_memory.update_expert_knowledge_from_outcome(
                    expert_id=expert_id,
                    game_id=game_id,
                    prediction_outcome=prediction_outcome
                )

            logger.info(f"✅ Processed outcome for {expert_id} on game {game_id}")

        except Exception as e:
            logger.error(f"Failed to process prediction outcome: {e}")

    def trigger_learning_cycle(self, cycle_type: str = "weekly"):
        """
        Trigger a comprehensive learning cycle

        Args:
            cycle_type: Type of cycle ('daily', 'weekly', 'monthly')
        """
        try:
            logger.info(f"Triggering {cycle_type} learning cycle")

            # 1. Get learning summary from coordinator
            learning_summary = self.learning_coordinator.get_learning_summary(
                days=self._get_cycle_days(cycle_type)
            )

            # 2. Check for experts needing belief revision
            poor_performers = []
            for expert_id in self.active_experts:
                performance = self.learning_coordinator.get_expert_performance(expert_id)
                expert_perf = performance.get(expert_id)

                if expert_perf and expert_perf.recent_accuracy < self.config['belief_revision']['revision_threshold']:
                    poor_performers.append(expert_id)

            # 3. Process belief revisions
            if self.belief_service and poor_performers:
                logger.info(f"Processing belief revisions for {len(poor_performers)} experts")

                for expert_id in poor_performers:
                    # Create revision context
                    performance = self.learning_coordinator.get_expert_performance(expert_id)
                    revision_context = {
                        'expert_id': expert_id,
                        'trigger_outcome': {'was_correct': False},
                        'recent_performance': performance.get(expert_id).to_dict() if performance.get(expert_id) else {},
                        'evidence': []  # Would contain recent poor predictions
                    }

                    # Trigger revision
                    revision_result = self.belief_service.revise_beliefs(revision_context)
                    logger.info(f"Revised beliefs for {expert_id}: {revision_result.get('revisions_count', 0)} changes")

            # 4. Update model weights if needed
            if cycle_type in ['weekly', 'monthly']:
                self._update_model_weights()

            # 5. Generate cycle report
            report = self._generate_learning_cycle_report(cycle_type, learning_summary)
            self._save_learning_report(report, cycle_type)

            logger.info(f"✅ Completed {cycle_type} learning cycle")

        except Exception as e:
            logger.error(f"Failed to trigger learning cycle: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the learning system"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'learning_active': self.learning_active,
                'active_experts': len(self.active_experts),
                'registered_models': len(self.registered_models),
                'components': {}
            }

            # Check component status
            if self.continuous_learner:
                status['components']['continuous_learner'] = {
                    'active': True,
                    'models': len(self.continuous_learner.models)
                }

            if self.learning_coordinator:
                performances = self.learning_coordinator.get_expert_performance()
                status['components']['learning_coordinator'] = {
                    'active': True,
                    'tracked_experts': len(performances)
                }

            if self.prediction_monitor:
                dashboard = self.prediction_monitor.get_dashboard_data()
                status['components']['prediction_monitor'] = {
                    'active': True,
                    'system_health': dashboard.system_health if dashboard else 'unknown',
                    'active_alerts': dashboard.active_alerts if dashboard else 0
                }

            if self.belief_service:
                status['components']['belief_service'] = {'active': True}

            if self.memory_manager:
                status['components']['memory_manager'] = {'active': True}

            if self.expert_memory:
                status['components']['expert_memory'] = {'active': True}

            return status

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'learning_active': False
            }

    def get_expert_learning_insights(self, expert_id: str) -> Dict[str, Any]:
        """Get comprehensive learning insights for a specific expert"""
        try:
            insights = {
                'expert_id': expert_id,
                'timestamp': datetime.now().isoformat()
            }

            # Get performance from coordinator
            performance = self.learning_coordinator.get_expert_performance(expert_id)
            if expert_id in performance and performance[expert_id]:
                perf = performance[expert_id]
                insights['performance'] = {
                    'accuracy': perf.accuracy,
                    'recent_accuracy': perf.recent_accuracy,
                    'confidence_weighted_accuracy': perf.confidence_weighted_accuracy,
                    'trend': perf.trend,
                    'weight': perf.weight,
                    'total_predictions': perf.total_predictions
                }

            # Get monitoring metrics
            if self.prediction_monitor:
                metrics = self.prediction_monitor.get_expert_metrics(expert_id)
                insights['monitoring'] = metrics

            # Get beliefs
            if self.expert_memory:
                beliefs = self.expert_memory.get_expert_beliefs(expert_id)
                insights['beliefs'] = beliefs

            return insights

        except Exception as e:
            logger.error(f"Failed to get insights for {expert_id}: {e}")
            return {
                'expert_id': expert_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def export_learning_data(self, filepath: str, include_sensitive: bool = False):
        """Export comprehensive learning data for analysis"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'config': self.config,
                'system_status': self.get_system_status()
            }

            # Export coordinator data
            if self.learning_coordinator:
                export_data['learning_coordinator'] = {
                    'expert_performances': {
                        eid: perf.to_dict() if perf else None
                        for eid, perf in self.learning_coordinator.expert_performances.items()
                    },
                    'learning_summary': self.learning_coordinator.get_learning_summary()
                }

            # Export monitoring data if not sensitive
            if self.prediction_monitor and not include_sensitive:
                dashboard = self.prediction_monitor.get_dashboard_data()
                if dashboard:
                    export_data['monitoring'] = {
                        'system_health': dashboard.system_health,
                        'overall_accuracy': dashboard.overall_accuracy,
                        'active_alerts': dashboard.active_alerts,
                        'expert_count': len(dashboard.expert_accuracies)
                    }

            # Save export
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Exported learning data to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export learning data: {e}")

    # Helper methods

    def _extract_features_from_context(self, context: Dict[str, Any]) -> List[float]:
        """Extract numerical features from context for model learning"""
        features = []

        # Extract numerical features
        features.append(context.get('home_score', 0) / 50.0)  # Normalized
        features.append(context.get('away_score', 0) / 50.0)
        features.append(context.get('spread', 0) / 20.0)
        features.append(context.get('total', 0) / 70.0)
        features.append(1.0 if context.get('home_team_favorite') else 0.0)
        features.append(context.get('weather_score', 0.5))
        features.append(context.get('injury_impact', 0.0))

        # Pad to consistent length
        while len(features) < 10:
            features.append(0.0)

        return features[:10]

    def _was_prediction_correct(self, predicted: float, actual: float, threshold: float = 0.5) -> bool:
        """Simple binary correctness check"""
        return (predicted > threshold) == (actual > threshold)

    def _get_cycle_days(self, cycle_type: str) -> int:
        """Get number of days for cycle type"""
        cycle_map = {'daily': 1, 'weekly': 7, 'monthly': 30}
        return cycle_map.get(cycle_type, 7)

    def _update_model_weights(self):
        """Update weights for all registered models"""
        if not self.continuous_learner or not self.registered_models:
            return

        logger.info("Updating model weights based on recent performance")
        # This would implement model weight updates based on expert performance

    def _generate_learning_cycle_report(self, cycle_type: str, learning_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive learning cycle report"""
        return {
            'cycle_type': cycle_type,
            'timestamp': datetime.now().isoformat(),
            'learning_summary': learning_summary,
            'system_status': self.get_system_status(),
            'expert_insights': {
                expert_id: self.get_expert_learning_insights(expert_id)
                for expert_id in list(self.active_experts)[:5]  # Top 5 experts
            }
        }

    def _save_learning_report(self, report: Dict[str, Any], cycle_type: str):
        """Save learning report to file"""
        try:
            reports_dir = Path("reports/learning_cycles")
            reports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"{cycle_type}_cycle_{timestamp}.json"

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            # Also save as latest
            latest_path = reports_dir / f"latest_{cycle_type}_cycle.json"
            with open(latest_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Saved learning cycle report: {report_path}")

        except Exception as e:
            logger.error(f"Failed to save learning report: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize learning pipeline
    pipeline = LearningPipelineIntegration()

    # Register some experts
    pipeline.register_expert("momentum_expert", {"specialties": ["spread", "momentum"]})
    pipeline.register_expert("weather_expert", {"specialties": ["total", "weather"]})

    # Simulate processing some outcomes
    outcome_1 = {
        'prediction_id': 'pred_1',
        'expert_id': 'momentum_expert',
        'game_id': 'game_123',
        'prediction_type': 'spread',
        'predicted_value': 0.7,
        'confidence': 0.8,
        'actual_value': 1.0,
        'context': {'home_score': 24, 'away_score': 17, 'weather_score': 0.6}
    }

    pipeline.process_prediction_outcome(outcome_1)

    # Get system status
    status = pipeline.get_system_status()
    print(f"System Status: {json.dumps(status, indent=2)}")

    # Trigger learning cycle
    pipeline.trigger_learning_cycle("weekly")

    # Export data
    pipeline.export_learning_data("learning_export.json")

    logger.info("Learning pipeline integration test completed!")