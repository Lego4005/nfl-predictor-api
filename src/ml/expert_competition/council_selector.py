"""
AI Council Selector
Implements dynamic top-5 expert selection for the AI Council based on performance metrics
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SelectionCriteria:
    """Criteria for AI Council selection"""
    accuracy_weight: float = 0.35
    recent_performance_weight: float = 0.25
    consistency_weight: float = 0.20
    calibration_weight: float = 0.10
    specialization_weight: float = 0.10
    evaluation_window_weeks: int = 4
    minimum_predictions: int = 10
    
    def validate(self) -> bool:
        """Validate that weights sum to 1.0"""
        total_weight = (
            self.accuracy_weight + 
            self.recent_performance_weight + 
            self.consistency_weight + 
            self.calibration_weight + 
            self.specialization_weight
        )
        return abs(total_weight - 1.0) < 0.001

@dataclass
class ExpertSelectionScore:
    """Expert's selection score breakdown"""
    expert_id: str
    overall_score: float
    accuracy_score: float
    recent_performance_score: float
    consistency_score: float
    calibration_score: float
    specialization_score: float
    total_predictions: int
    eligible: bool
    selection_rank: int = 0

class AICouncilSelector:
    """Selects the top 5 performing experts for the AI Council"""
    
    def __init__(self, selection_criteria: Optional[SelectionCriteria] = None):
        self.criteria = selection_criteria or SelectionCriteria()
        
        if not self.criteria.validate():
            logger.warning("Selection criteria weights do not sum to 1.0, normalizing...")
            self._normalize_criteria_weights()
    
    def _normalize_criteria_weights(self) -> None:
        """Normalize criteria weights to sum to 1.0"""
        total_weight = (
            self.criteria.accuracy_weight + 
            self.criteria.recent_performance_weight + 
            self.criteria.consistency_weight + 
            self.criteria.calibration_weight + 
            self.criteria.specialization_weight
        )
        
        if total_weight > 0:
            self.criteria.accuracy_weight /= total_weight
            self.criteria.recent_performance_weight /= total_weight
            self.criteria.consistency_weight /= total_weight
            self.criteria.calibration_weight /= total_weight
            self.criteria.specialization_weight /= total_weight
    
    async def select_top_performers(
        self, 
        experts: Dict[str, Any], 
        evaluation_window_weeks: Optional[int] = None
    ) -> List[str]:
        """Select top 5 experts for AI Council based on performance metrics"""
        try:
            window_weeks = evaluation_window_weeks or self.criteria.evaluation_window_weeks
            
            # Calculate selection scores for all experts
            expert_scores = await self._calculate_selection_scores(experts, window_weeks)
            
            # Filter eligible experts
            eligible_experts = [score for score in expert_scores if score.eligible]
            
            if len(eligible_experts) < 5:
                logger.warning(f"Only {len(eligible_experts)} eligible experts found, need at least 5")
                # Include all eligible experts and fill with best available
                additional_needed = 5 - len(eligible_experts)
                ineligible_experts = [score for score in expert_scores if not score.eligible]
                ineligible_experts.sort(key=lambda x: x.overall_score, reverse=True)
                eligible_experts.extend(ineligible_experts[:additional_needed])
            
            # Sort by overall score and select top 5
            eligible_experts.sort(key=lambda x: x.overall_score, reverse=True)
            top_5_experts = eligible_experts[:5]
            
            # Update selection ranks
            for i, expert_score in enumerate(top_5_experts):
                expert_score.selection_rank = i + 1
            
            # Log selection details
            logger.info(f"Selected AI Council from {len(expert_scores)} experts:")
            for expert_score in top_5_experts:
                expert_name = experts[expert_score.expert_id].name if expert_score.expert_id in experts else expert_score.expert_id
                logger.info(f"  #{expert_score.selection_rank}: {expert_name} (Score: {expert_score.overall_score:.3f})")
            
            return [expert.expert_id for expert in top_5_experts]
            
        except Exception as e:
            logger.error(f"Failed to select AI Council: {e}")
            # Fallback: return first 5 experts
            return list(experts.keys())[:5]
    
    async def _calculate_selection_scores(
        self, 
        experts: Dict[str, Any], 
        window_weeks: int
    ) -> List[ExpertSelectionScore]:
        """Calculate selection scores for all experts"""
        expert_scores = []
        
        for expert_id, expert in experts.items():
            try:
                score = await self._calculate_expert_selection_score(expert, window_weeks)
                expert_scores.append(score)
            except Exception as e:
                logger.error(f"Failed to calculate score for expert {expert_id}: {e}")
                continue
        
        return expert_scores
    
    async def _calculate_expert_selection_score(
        self, 
        expert: Any, 
        window_weeks: int
    ) -> ExpertSelectionScore:
        """Calculate comprehensive selection score for a single expert"""
        
        # Get expert metrics
        total_predictions = getattr(expert, 'total_predictions', 0)
        overall_accuracy = getattr(expert, 'overall_accuracy', 0.5)
        
        # Check eligibility (minimum predictions in evaluation window)
        eligible = total_predictions >= self.criteria.minimum_predictions
        
        # Calculate component scores
        accuracy_score = self._calculate_accuracy_score(expert)
        recent_performance_score = await self._calculate_recent_performance_score(expert, window_weeks)
        consistency_score = self._calculate_consistency_score(expert)
        calibration_score = self._calculate_calibration_score(expert)
        specialization_score = self._calculate_specialization_score(expert)
        
        # Calculate weighted overall score
        overall_score = (
            accuracy_score * self.criteria.accuracy_weight +
            recent_performance_score * self.criteria.recent_performance_weight +
            consistency_score * self.criteria.consistency_weight +
            calibration_score * self.criteria.calibration_weight +
            specialization_score * self.criteria.specialization_weight
        )
        
        return ExpertSelectionScore(
            expert_id=expert.expert_id,
            overall_score=overall_score,
            accuracy_score=accuracy_score,
            recent_performance_score=recent_performance_score,
            consistency_score=consistency_score,
            calibration_score=calibration_score,
            specialization_score=specialization_score,
            total_predictions=total_predictions,
            eligible=eligible
        )
    
    def _calculate_accuracy_score(self, expert: Any) -> float:
        """Calculate accuracy-based score (0.0 to 1.0)"""
        try:
            accuracy = getattr(expert, 'overall_accuracy', 0.5)
            
            # Convert accuracy to score (50% accuracy = 0.0, 100% accuracy = 1.0)
            # This ensures that average performance gets neutral score
            accuracy_score = max(0.0, (accuracy - 0.5) * 2.0)
            
            return min(1.0, accuracy_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate accuracy score for {expert.expert_id}: {e}")
            return 0.0
    
    async def _calculate_recent_performance_score(self, expert: Any, window_weeks: int) -> float:
        """Calculate recent performance score based on trend"""
        try:
            # Get recent trend indicator
            recent_trend = getattr(expert, 'recent_trend', 'stable')
            
            # Convert trend to score
            trend_scores = {
                'improving': 1.0,
                'stable': 0.6,
                'declining': 0.2
            }
            
            base_score = trend_scores.get(recent_trend, 0.5)
            
            # Adjust based on recent accuracy if available
            recent_accuracy = getattr(expert, 'recent_accuracy', None)
            if recent_accuracy is not None:
                # Weight recent accuracy with trend
                accuracy_component = max(0.0, (recent_accuracy - 0.5) * 2.0)
                base_score = base_score * 0.7 + accuracy_component * 0.3
            
            return min(1.0, max(0.0, base_score))
            
        except Exception as e:
            logger.error(f"Failed to calculate recent performance score for {expert.expert_id}: {e}")
            return 0.5
    
    def _calculate_consistency_score(self, expert: Any) -> float:
        """Calculate consistency score based on prediction variance"""
        try:
            consistency = getattr(expert, 'consistency_score', 0.5)
            
            # Consistency score is already 0-1, use directly
            return max(0.0, min(1.0, consistency))
            
        except Exception as e:
            logger.error(f"Failed to calculate consistency score for {expert.expert_id}: {e}")
            return 0.5
    
    def _calculate_calibration_score(self, expert: Any) -> float:
        """Calculate confidence calibration score"""
        try:
            calibration = getattr(expert, 'confidence_calibration', 0.5)
            
            # Calibration score represents how well confidence matches actual accuracy
            # Higher calibration = better score
            return max(0.0, min(1.0, calibration))
            
        except Exception as e:
            logger.error(f"Failed to calculate calibration score for {expert.expert_id}: {e}")
            return 0.5
    
    def _calculate_specialization_score(self, expert: Any) -> float:
        """Calculate specialization strength score"""
        try:
            # Get specialization strengths
            specialization_strength = getattr(expert, 'specialization_strength', {})
            
            if not specialization_strength:
                return 0.5  # Neutral score for no specialization data
            
            # Calculate average specialization strength
            strengths = list(specialization_strength.values())
            if strengths:
                avg_strength = sum(strengths) / len(strengths)
                return max(0.0, min(1.0, avg_strength))
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Failed to calculate specialization score for {expert.expert_id}: {e}")
            return 0.5
    
    def get_selection_breakdown(
        self, 
        expert_scores: List[ExpertSelectionScore]
    ) -> Dict[str, Any]:
        """Get detailed breakdown of selection process"""
        try:
            if not expert_scores:
                return {'error': 'No expert scores provided'}
            
            # Sort by overall score
            sorted_scores = sorted(expert_scores, key=lambda x: x.overall_score, reverse=True)
            
            return {
                'selection_criteria': {
                    'accuracy_weight': self.criteria.accuracy_weight,
                    'recent_performance_weight': self.criteria.recent_performance_weight,
                    'consistency_weight': self.criteria.consistency_weight,
                    'calibration_weight': self.criteria.calibration_weight,
                    'specialization_weight': self.criteria.specialization_weight,
                    'evaluation_window_weeks': self.criteria.evaluation_window_weeks,
                    'minimum_predictions': self.criteria.minimum_predictions
                },
                'expert_rankings': [
                    {
                        'expert_id': score.expert_id,
                        'rank': i + 1,
                        'overall_score': score.overall_score,
                        'component_scores': {
                            'accuracy': score.accuracy_score,
                            'recent_performance': score.recent_performance_score,
                            'consistency': score.consistency_score,
                            'calibration': score.calibration_score,
                            'specialization': score.specialization_score
                        },
                        'total_predictions': score.total_predictions,
                        'eligible': score.eligible,
                        'selected_for_council': i < 5
                    }
                    for i, score in enumerate(sorted_scores)
                ],
                'selection_summary': {
                    'total_experts_evaluated': len(expert_scores),
                    'eligible_experts': len([s for s in expert_scores if s.eligible]),
                    'selected_experts': min(5, len(expert_scores)),
                    'average_score': sum(s.overall_score for s in expert_scores) / len(expert_scores),
                    'score_range': {
                        'min': min(s.overall_score for s in expert_scores),
                        'max': max(s.overall_score for s in expert_scores)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate selection breakdown: {e}")
            return {'error': str(e)}
    
    def update_selection_criteria(self, **kwargs) -> None:
        """Update selection criteria parameters"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.criteria, key):
                    setattr(self.criteria, key, value)
                    logger.info(f"Updated selection criteria: {key} = {value}")
                else:
                    logger.warning(f"Unknown selection criteria parameter: {key}")
            
            # Re-validate and normalize if needed
            if not self.criteria.validate():
                logger.info("Re-normalizing selection criteria weights...")
                self._normalize_criteria_weights()
                
        except Exception as e:
            logger.error(f"Failed to update selection criteria: {e}")
    
    def get_current_criteria(self) -> Dict[str, Any]:
        """Get current selection criteria"""
        return {
            'accuracy_weight': self.criteria.accuracy_weight,
            'recent_performance_weight': self.criteria.recent_performance_weight,
            'consistency_weight': self.criteria.consistency_weight,
            'calibration_weight': self.criteria.calibration_weight,
            'specialization_weight': self.criteria.specialization_weight,
            'evaluation_window_weeks': self.criteria.evaluation_window_weeks,
            'minimum_predictions': self.criteria.minimum_predictions,
            'weights_valid': self.criteria.validate()
        }

# Usage example
async def test_council_selector():
    """Test the AI Council Selector"""
    try:
        selector = AICouncilSelector()
        
        # Mock experts for testing
        mock_experts = {}
        for i in range(10):
            class MockExpert:
                def __init__(self, expert_id: str):
                    self.expert_id = expert_id
                    self.name = f"Expert {expert_id}"
                    self.total_predictions = np.random.randint(5, 50)
                    self.overall_accuracy = np.random.uniform(0.45, 0.75)
                    self.recent_trend = np.random.choice(['improving', 'stable', 'declining'])
                    self.consistency_score = np.random.uniform(0.3, 0.8)
                    self.confidence_calibration = np.random.uniform(0.4, 0.9)
                    self.specialization_strength = {'category_1': np.random.uniform(0.3, 0.9)}
            
            expert = MockExpert(f"expert_{i}")
            mock_experts[expert.expert_id] = expert
        
        # Select council
        council_members = await selector.select_top_performers(mock_experts)
        print(f"Selected council: {council_members}")
        
        # Get selection breakdown
        expert_scores = await selector._calculate_selection_scores(mock_experts, 4)
        breakdown = selector.get_selection_breakdown(expert_scores)
        print(f"Selection breakdown: {breakdown}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_council_selector())