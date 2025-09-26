"""
Adaptation Engine
Implements algorithm parameter tuning and expert adaptation mechanisms
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np
import json

logger = logging.getLogger(__name__)

class AdaptationType(Enum):
    """Types of adaptation strategies"""
    PARAMETER_TUNING = "parameter_tuning"
    ALGORITHM_RESET = "algorithm_reset"
    LEARNING_RATE_ADJUSTMENT = "learning_rate_adjustment"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    SPECIALIZATION_FOCUS = "specialization_focus"
    PERSONALITY_ADJUSTMENT = "personality_adjustment"

class AdaptationStatus(Enum):
    """Status of adaptation process"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class AdaptationStrategy:
    """Defines an adaptation strategy"""
    adaptation_type: AdaptationType
    target_parameters: List[str]
    adjustment_magnitude: float
    confidence_threshold: float
    rollback_threshold: float
    max_iterations: int = 3
    description: str = ""

@dataclass
class AdaptationRecord:
    """Record of an adaptation attempt"""
    expert_id: str
    adaptation_type: AdaptationType
    status: AdaptationStatus
    trigger_reason: str
    parameters_before: Dict[str, Any]
    parameters_after: Dict[str, Any]
    performance_before: float
    performance_after: Optional[float]
    improvement_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    rollback_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expert_id': self.expert_id,
            'adaptation_type': self.adaptation_type.value,
            'status': self.status.value,
            'trigger_reason': self.trigger_reason,
            'parameters_before': self.parameters_before,
            'parameters_after': self.parameters_after,
            'performance_before': self.performance_before,
            'performance_after': self.performance_after,
            'improvement_score': self.improvement_score,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'rollback_reason': self.rollback_reason
        }

class AdaptationEngine:
    """Manages expert adaptation and algorithm parameter tuning"""
    
    def __init__(self, supabase_client=None, accuracy_tracker=None, trend_analyzer=None):
        self.supabase = supabase_client
        self.accuracy_tracker = accuracy_tracker
        self.trend_analyzer = trend_analyzer
        
        # Adaptation strategies
        self.adaptation_strategies = self._initialize_adaptation_strategies()
        
        # Active adaptations
        self.active_adaptations: Dict[str, AdaptationRecord] = {}
        
        # Adaptation history
        self.adaptation_history: List[AdaptationRecord] = []
        
        # Configuration
        self.adaptation_cooldown_hours = 24  # Minimum time between adaptations
        self.performance_evaluation_days = 7  # Days to evaluate adaptation success
        self.max_concurrent_adaptations = 3  # Maximum experts adapting simultaneously
    
    def _initialize_adaptation_strategies(self) -> Dict[AdaptationType, AdaptationStrategy]:
        """Initialize available adaptation strategies"""
        return {
            AdaptationType.PARAMETER_TUNING: AdaptationStrategy(
                adaptation_type=AdaptationType.PARAMETER_TUNING,
                target_parameters=['risk_tolerance', 'analytics_trust', 'confidence_level'],
                adjustment_magnitude=0.1,
                confidence_threshold=0.6,
                rollback_threshold=0.8,
                description="Fine-tune personality trait parameters"
            ),
            AdaptationType.ALGORITHM_RESET: AdaptationStrategy(
                adaptation_type=AdaptationType.ALGORITHM_RESET,
                target_parameters=['all'],
                adjustment_magnitude=1.0,
                confidence_threshold=0.8,
                rollback_threshold=0.9,
                description="Reset algorithm to baseline parameters"
            ),
            AdaptationType.LEARNING_RATE_ADJUSTMENT: AdaptationStrategy(
                adaptation_type=AdaptationType.LEARNING_RATE_ADJUSTMENT,
                target_parameters=['learning_rate', 'adaptation_speed'],
                adjustment_magnitude=0.2,
                confidence_threshold=0.5,
                rollback_threshold=0.7,
                description="Adjust learning and adaptation rates"
            ),
            AdaptationType.CONFIDENCE_CALIBRATION: AdaptationStrategy(
                adaptation_type=AdaptationType.CONFIDENCE_CALIBRATION,
                target_parameters=['confidence_scaling', 'uncertainty_factor'],
                adjustment_magnitude=0.15,
                confidence_threshold=0.4,
                rollback_threshold=0.6,
                description="Recalibrate confidence estimation"
            ),
            AdaptationType.SPECIALIZATION_FOCUS: AdaptationStrategy(
                adaptation_type=AdaptationType.SPECIALIZATION_FOCUS,
                target_parameters=['category_weights', 'specialization_bonus'],
                adjustment_magnitude=0.2,
                confidence_threshold=0.7,
                rollback_threshold=0.8,
                description="Focus on best-performing categories"
            )
        }
    
    async def adapt_expert(self, expert: Any, performance_issue: str) -> bool:
        """Adapt an expert based on performance issues"""
        try:
            expert_id = expert.expert_id
            
            # Check adaptation eligibility
            if not await self._is_adaptation_eligible(expert_id):
                logger.info(f"Expert {expert_id} not eligible for adaptation")
                return False
            
            # Select adaptation strategy
            strategy = self._select_adaptation_strategy(performance_issue, expert)
            if not strategy:
                logger.warning(f"No suitable adaptation strategy for {performance_issue}")
                return False
            
            # Start adaptation
            adaptation_record = await self._start_adaptation(expert, strategy, performance_issue)
            if not adaptation_record:
                return False
            
            # Apply adaptation
            success = await self._apply_adaptation(expert, strategy, adaptation_record)
            
            if success:
                logger.info(f"Successfully adapted expert {expert_id} using {strategy.adaptation_type.value}")
                return True
            else:
                logger.error(f"Failed to adapt expert {expert_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to adapt expert: {e}")
            return False
    
    async def _is_adaptation_eligible(self, expert_id: str) -> bool:
        """Check if expert is eligible for adaptation"""
        try:
            # Check cooldown period
            last_adaptation = self._get_last_adaptation(expert_id)
            if last_adaptation:
                hours_since = (datetime.now() - last_adaptation.started_at).total_seconds() / 3600
                if hours_since < self.adaptation_cooldown_hours:
                    return False
            
            # Check concurrent adaptations limit
            active_count = len(self.active_adaptations)
            if active_count >= self.max_concurrent_adaptations:
                return False
            
            # Check if already adapting
            if expert_id in self.active_adaptations:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check adaptation eligibility: {e}")
            return False
    
    def _get_last_adaptation(self, expert_id: str) -> Optional[AdaptationRecord]:
        """Get the most recent adaptation for an expert"""
        expert_adaptations = [
            record for record in self.adaptation_history 
            if record.expert_id == expert_id
        ]
        
        if expert_adaptations:
            return max(expert_adaptations, key=lambda x: x.started_at)
        
        return None
    
    def _select_adaptation_strategy(self, performance_issue: str, expert: Any) -> Optional[AdaptationStrategy]:
        """Select appropriate adaptation strategy based on performance issue"""
        try:
            # Map performance issues to strategies
            issue_strategy_mapping = {
                'accuracy_drop': AdaptationType.PARAMETER_TUNING,
                'consistency_loss': AdaptationType.CONFIDENCE_CALIBRATION,
                'rank_decline': AdaptationType.SPECIALIZATION_FOCUS,
                'calibration_poor': AdaptationType.CONFIDENCE_CALIBRATION,
                'trend_declining': AdaptationType.LEARNING_RATE_ADJUSTMENT,
                'severe_decline': AdaptationType.ALGORITHM_RESET
            }
            
            strategy_type = issue_strategy_mapping.get(performance_issue, AdaptationType.PARAMETER_TUNING)
            return self.adaptation_strategies.get(strategy_type)
            
        except Exception as e:
            logger.error(f"Failed to select adaptation strategy: {e}")
            return None
    
    async def _start_adaptation(
        self, 
        expert: Any, 
        strategy: AdaptationStrategy, 
        trigger_reason: str
    ) -> Optional[AdaptationRecord]:
        """Start adaptation process"""
        try:
            expert_id = expert.expert_id
            
            # Get current performance baseline
            current_performance = await self._get_current_performance(expert_id)
            
            # Backup current parameters
            current_parameters = self._backup_expert_parameters(expert)
            
            # Create adaptation record
            adaptation_record = AdaptationRecord(
                expert_id=expert_id,
                adaptation_type=strategy.adaptation_type,
                status=AdaptationStatus.PENDING,
                trigger_reason=trigger_reason,
                parameters_before=current_parameters,
                parameters_after={},
                performance_before=current_performance,
                performance_after=None,
                improvement_score=None,
                started_at=datetime.now()
            )
            
            # Add to active adaptations
            self.active_adaptations[expert_id] = adaptation_record
            
            return adaptation_record
            
        except Exception as e:
            logger.error(f"Failed to start adaptation: {e}")
            return None
    
    async def _apply_adaptation(
        self, 
        expert: Any, 
        strategy: AdaptationStrategy, 
        record: AdaptationRecord
    ) -> bool:
        """Apply the adaptation strategy"""
        try:
            record.status = AdaptationStatus.IN_PROGRESS
            
            # Apply strategy-specific adaptation
            if strategy.adaptation_type == AdaptationType.PARAMETER_TUNING:
                success = self._apply_parameter_tuning(expert, strategy)
            elif strategy.adaptation_type == AdaptationType.ALGORITHM_RESET:
                success = self._apply_algorithm_reset(expert, strategy)
            elif strategy.adaptation_type == AdaptationType.LEARNING_RATE_ADJUSTMENT:
                success = self._apply_learning_rate_adjustment(expert, strategy)
            elif strategy.adaptation_type == AdaptationType.CONFIDENCE_CALIBRATION:
                success = self._apply_confidence_calibration(expert, strategy)
            elif strategy.adaptation_type == AdaptationType.SPECIALIZATION_FOCUS:
                success = self._apply_specialization_focus(expert, strategy)
            else:
                success = False
            
            if success:
                # Update record with new parameters
                record.parameters_after = self._backup_expert_parameters(expert)
                record.status = AdaptationStatus.COMPLETED
                record.completed_at = datetime.now()
                
                # Schedule performance evaluation
                await self._schedule_performance_evaluation(expert.expert_id, record)
                
            else:
                record.status = AdaptationStatus.FAILED
                record.completed_at = datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to apply adaptation: {e}")
            record.status = AdaptationStatus.FAILED
            record.completed_at = datetime.now()
            return False
    
    def _apply_parameter_tuning(self, expert: Any, strategy: AdaptationStrategy) -> bool:
        """Apply parameter tuning adaptation"""
        try:
            if not hasattr(expert, 'personality_traits'):
                return False
            
            # Adjust personality traits
            for param in strategy.target_parameters:
                if param in expert.personality_traits:
                    current_value = getattr(expert.personality_traits[param], 'value', 0.5)
                    
                    # Calculate adjustment based on performance
                    adjustment = np.random.uniform(-strategy.adjustment_magnitude, strategy.adjustment_magnitude)
                    new_value = max(0.0, min(1.0, current_value + adjustment))
                    
                    # Apply adjustment
                    if hasattr(expert.personality_traits[param], 'value'):
                        expert.personality_traits[param].value = new_value
                    else:
                        expert.personality_traits[param] = new_value
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply parameter tuning: {e}")
            return False
    
    def _apply_algorithm_reset(self, expert: Any, strategy: AdaptationStrategy) -> bool:
        """Apply algorithm reset adaptation"""
        try:
            # Reset to default personality traits
            default_traits = {
                'risk_tolerance': 0.5,
                'analytics_trust': 0.5,
                'contrarian_tendency': 0.3,
                'market_trust': 0.5,
                'confidence_level': 0.6,
                'chaos_comfort': 0.4,
                'intuition_weight': 0.3,
                'optimism': 0.5,
                'data_reliance': 0.6
            }
            
            for trait, value in default_traits.items():
                if hasattr(expert, 'personality_traits'):
                    if hasattr(expert.personality_traits.get(trait), 'value'):
                        expert.personality_traits[trait].value = value
                    else:
                        expert.personality_traits[trait] = value
            
            # Reset performance metrics
            if hasattr(expert, 'total_predictions'):
                expert.total_predictions = 0
                expert.correct_predictions = 0
                expert.overall_accuracy = 0.5
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply algorithm reset: {e}")
            return False
    
    def _apply_learning_rate_adjustment(self, expert: Any, strategy: AdaptationStrategy) -> bool:
        """Apply learning rate adjustment"""
        try:
            # Adjust learning-related parameters
            learning_rate = getattr(expert, 'learning_rate', 0.1)
            adaptation_speed = getattr(expert, 'adaptation_speed', 0.5)
            
            # Increase or decrease learning rate based on performance
            if hasattr(expert, 'recent_trend') and expert.recent_trend == 'declining':
                learning_rate *= (1 + strategy.adjustment_magnitude)
                adaptation_speed *= (1 + strategy.adjustment_magnitude)
            else:
                learning_rate *= (1 - strategy.adjustment_magnitude * 0.5)
                adaptation_speed *= (1 - strategy.adjustment_magnitude * 0.5)
            
            expert.learning_rate = max(0.01, min(0.5, learning_rate))
            expert.adaptation_speed = max(0.1, min(1.0, adaptation_speed))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply learning rate adjustment: {e}")
            return False
    
    def _apply_confidence_calibration(self, expert: Any, strategy: AdaptationStrategy) -> bool:
        """Apply confidence calibration adaptation"""
        try:
            # Adjust confidence-related parameters
            confidence_scaling = getattr(expert, 'confidence_scaling', 1.0)
            uncertainty_factor = getattr(expert, 'uncertainty_factor', 0.1)
            
            # Get calibration performance
            calibration_score = getattr(expert, 'confidence_calibration', 0.5)
            
            if calibration_score < 0.5:
                # Poor calibration - reduce confidence
                confidence_scaling *= (1 - strategy.adjustment_magnitude)
                uncertainty_factor *= (1 + strategy.adjustment_magnitude)
            else:
                # Good calibration - slight increase
                confidence_scaling *= (1 + strategy.adjustment_magnitude * 0.5)
                uncertainty_factor *= (1 - strategy.adjustment_magnitude * 0.5)
            
            expert.confidence_scaling = max(0.5, min(1.5, confidence_scaling))
            expert.uncertainty_factor = max(0.05, min(0.3, uncertainty_factor))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply confidence calibration: {e}")
            return False
    
    def _apply_specialization_focus(self, expert: Any, strategy: AdaptationStrategy) -> bool:
        """Apply specialization focus adaptation"""
        try:
            # Focus on best-performing categories
            if hasattr(expert, 'category_accuracies'):
                # Find best performing categories
                best_categories = sorted(
                    expert.category_accuracies.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                
                # Increase weights for best categories
                category_weights = getattr(expert, 'category_weights', {})
                
                for category, accuracy in best_categories:
                    current_weight = category_weights.get(category, 1.0)
                    category_weights[category] = min(2.0, current_weight * (1 + strategy.adjustment_magnitude))
                
                expert.category_weights = category_weights
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply specialization focus: {e}")
            return False
    
    def _backup_expert_parameters(self, expert: Any) -> Dict[str, Any]:
        """Backup expert's current parameters"""
        try:
            backup = {}
            
            # Backup personality traits
            if hasattr(expert, 'personality_traits'):
                backup['personality_traits'] = {}
                for trait, value in expert.personality_traits.items():
                    if hasattr(value, 'value'):
                        backup['personality_traits'][trait] = value.value
                    else:
                        backup['personality_traits'][trait] = value
            
            # Backup other parameters
            backup_attributes = [
                'learning_rate', 'adaptation_speed', 'confidence_scaling',
                'uncertainty_factor', 'category_weights'
            ]
            
            for attr in backup_attributes:
                if hasattr(expert, attr):
                    backup[attr] = getattr(expert, attr)
            
            return backup
            
        except Exception as e:
            logger.error(f"Failed to backup expert parameters: {e}")
            return {}
    
    async def _get_current_performance(self, expert_id: str) -> float:
        """Get current performance baseline"""
        try:
            if self.accuracy_tracker:
                profile = await self.accuracy_tracker.get_expert_accuracy_profile(expert_id)
                if profile:
                    return profile.overall_accuracy
            
            return 0.5  # Default baseline
            
        except Exception as e:
            logger.error(f"Failed to get current performance: {e}")
            return 0.5
    
    async def _schedule_performance_evaluation(self, expert_id: str, record: AdaptationRecord) -> None:
        """Schedule performance evaluation after adaptation"""
        try:
            # In a real system, this would schedule a background task
            # For now, we'll just log the scheduling
            eval_date = datetime.now() + timedelta(days=self.performance_evaluation_days)
            
            logger.info(f"Scheduled performance evaluation for {expert_id} at {eval_date}")
            
            # Move from active to history
            if expert_id in self.active_adaptations:
                self.adaptation_history.append(self.active_adaptations[expert_id])
                del self.active_adaptations[expert_id]
                
        except Exception as e:
            logger.error(f"Failed to schedule performance evaluation: {e}")
    
    async def evaluate_adaptation_success(self, expert_id: str) -> Optional[float]:
        """Evaluate if adaptation was successful"""
        try:
            # Get recent adaptation
            recent_adaptation = self._get_last_adaptation(expert_id)
            if not recent_adaptation:
                return None
            
            # Get current performance
            current_performance = await self._get_current_performance(expert_id)
            
            # Calculate improvement
            improvement = current_performance - recent_adaptation.performance_before
            
            # Update adaptation record
            recent_adaptation.performance_after = current_performance
            recent_adaptation.improvement_score = improvement
            
            # Check if rollback is needed
            if improvement < -recent_adaptation.performance_before * 0.1:  # 10% degradation
                await self._rollback_adaptation(expert_id, recent_adaptation)
            
            return improvement
            
        except Exception as e:
            logger.error(f"Failed to evaluate adaptation success: {e}")
            return None
    
    async def _rollback_adaptation(self, expert_id: str, record: AdaptationRecord) -> bool:
        """Rollback a failed adaptation"""
        try:
            # This would restore the expert to previous parameters
            logger.warning(f"Rolling back adaptation for {expert_id}")
            
            record.status = AdaptationStatus.ROLLED_BACK
            record.rollback_reason = "Performance degradation detected"
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback adaptation: {e}")
            return False
    
    async def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get adaptation system summary"""
        try:
            total_adaptations = len(self.adaptation_history)
            successful_adaptations = len([r for r in self.adaptation_history if r.status == AdaptationStatus.COMPLETED])
            
            # Group by type
            type_counts = {}
            for adaptation_type in AdaptationType:
                type_counts[adaptation_type.value] = len([
                    r for r in self.adaptation_history 
                    if r.adaptation_type == adaptation_type
                ])
            
            return {
                'total_adaptations': total_adaptations,
                'successful_adaptations': successful_adaptations,
                'success_rate': successful_adaptations / max(1, total_adaptations),
                'active_adaptations': len(self.active_adaptations),
                'adaptations_by_type': type_counts,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get adaptation summary: {e}")
            return {'error': str(e)}