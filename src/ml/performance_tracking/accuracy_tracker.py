"""
Accuracy Tracker
Implements category-specific accuracy tracking and performance metrics for expert models
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class CategoryAccuracy:
    """Accuracy metrics for a specific prediction category"""
    category: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    confidence_weighted_accuracy: float
    recent_accuracy: float  # Last N predictions
    trend: str  # 'improving', 'stable', 'declining'
    calibration_score: float  # How well confidence matches accuracy
    last_updated: datetime

@dataclass
class PredictionOutcome:
    """Individual prediction outcome record"""
    prediction_id: str
    expert_id: str
    category: str
    predicted_value: Any
    actual_value: Any
    confidence: float
    is_correct: bool
    prediction_timestamp: datetime
    evaluation_timestamp: datetime
    game_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'prediction_id': self.prediction_id,
            'expert_id': self.expert_id,
            'category': self.category,
            'predicted_value': str(self.predicted_value),
            'actual_value': str(self.actual_value),
            'confidence': self.confidence,
            'is_correct': self.is_correct,
            'prediction_timestamp': self.prediction_timestamp.isoformat(),
            'evaluation_timestamp': self.evaluation_timestamp.isoformat(),
            'game_id': self.game_id
        }

@dataclass
class ExpertAccuracyProfile:
    """Complete accuracy profile for an expert"""
    expert_id: str
    overall_accuracy: float
    total_predictions: int
    correct_predictions: int
    category_accuracies: Dict[str, CategoryAccuracy] = field(default_factory=dict)
    confidence_calibration: float = 0.5
    recent_performance: Dict[str, float] = field(default_factory=dict)  # Category -> recent accuracy
    performance_trend: str = 'stable'
    specialization_scores: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

class AccuracyTracker:
    """Tracks and calculates category-specific accuracy metrics for experts"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.prediction_outcomes: Dict[str, List[PredictionOutcome]] = defaultdict(list)
        self.expert_profiles: Dict[str, ExpertAccuracyProfile] = {}
        
        # Configuration
        self.recent_window_size = 20  # Number of recent predictions for trend analysis
        self.calibration_bins = 10  # Number of confidence bins for calibration
        self.min_predictions_for_trend = 5  # Minimum predictions to calculate trend
    
    async def record_prediction_outcome(
        self,
        prediction_id: str,
        expert_id: str,
        category: str,
        predicted_value: Any,
        actual_value: Any,
        confidence: float,
        game_id: str,
        prediction_timestamp: datetime
    ) -> PredictionOutcome:
        """Record the outcome of a prediction for accuracy tracking"""
        try:
            # Determine if prediction is correct
            is_correct = self._evaluate_prediction_correctness(
                category, predicted_value, actual_value
            )
            
            # Create outcome record
            outcome = PredictionOutcome(
                prediction_id=prediction_id,
                expert_id=expert_id,
                category=category,
                predicted_value=predicted_value,
                actual_value=actual_value,
                confidence=confidence,
                is_correct=is_correct,
                prediction_timestamp=prediction_timestamp,
                evaluation_timestamp=datetime.now(),
                game_id=game_id
            )
            
            # Store outcome
            self.prediction_outcomes[expert_id].append(outcome)
            
            # Update expert accuracy profile
            await self._update_expert_accuracy_profile(expert_id, outcome)
            
            # Store in database if available
            if self.supabase:
                await self._store_prediction_outcome(outcome)
            
            logger.info(f\"Recorded prediction outcome for {expert_id}, category {category}: {'✓' if is_correct else '✗'}\")
            
            return outcome
            
        except Exception as e:
            logger.error(f\"Failed to record prediction outcome: {e}\")
            raise
    
    def _evaluate_prediction_correctness(
        self, 
        category: str, 
        predicted_value: Any, 
        actual_value: Any
    ) -> bool:
        \"\"\"Evaluate whether a prediction is correct based on category type\"\"\"
        try:
            if category in ['winner_prediction', 'against_the_spread', 'totals_over_under', 
                          'first_half_winner', 'highest_scoring_quarter', 'coaching_advantage']:
                # Exact match for categorical predictions
                return str(predicted_value).lower() == str(actual_value).lower()
            
            elif category in ['exact_score_home', 'exact_score_away']:
                # Exact score: correct if within 3 points
                try:
                    pred_score = float(predicted_value)
                    actual_score = float(actual_value)
                    return abs(pred_score - actual_score) <= 3
                except (ValueError, TypeError):
                    return False
            
            elif category == 'margin_of_victory':
                # Margin: correct if within 7 points
                try:
                    pred_margin = float(predicted_value)
                    actual_margin = float(actual_value)
                    return abs(pred_margin - actual_margin) <= 7
                except (ValueError, TypeError):
                    return False
            
            elif category in ['qb_passing_yards', 'rb_rushing_yards', 'wr_receiving_yards']:
                # Yardage: correct if within 20% or 25 yards
                try:
                    pred_yards = float(predicted_value)
                    actual_yards = float(actual_value)
                    
                    percentage_error = abs(pred_yards - actual_yards) / max(actual_yards, 1)
                    absolute_error = abs(pred_yards - actual_yards)
                    
                    return percentage_error <= 0.20 or absolute_error <= 25
                except (ValueError, TypeError):
                    return False
            
            elif category in ['qb_touchdowns', 'qb_interceptions', 'rb_touchdowns', 'wr_receptions']:
                # Count stats: exact match or within 1
                try:
                    pred_count = int(float(predicted_value))
                    actual_count = int(float(actual_value))
                    return abs(pred_count - actual_count) <= 1
                except (ValueError, TypeError):
                    return False
            
            elif category in ['weather_impact_score', 'injury_impact_score', 
                            'divisional_rivalry_factor', 'home_field_advantage']:
                # Score/factor predictions: within 20% of range
                try:
                    pred_score = float(predicted_value)
                    actual_score = float(actual_value)
                    
                    # For 0-1 scale factors
                    if category in ['weather_impact_score', 'injury_impact_score', 'divisional_rivalry_factor']:
                        return abs(pred_score - actual_score) <= 0.2
                    else:  # home_field_advantage (points)
                        return abs(pred_score - actual_score) <= 2.0
                except (ValueError, TypeError):
                    return False
            
            else:
                # Generic comparison for unknown categories
                return str(predicted_value) == str(actual_value)
                
        except Exception as e:
            logger.error(f\"Failed to evaluate prediction correctness for {category}: {e}\")
            return False
    
    async def _update_expert_accuracy_profile(
        self, 
        expert_id: str, 
        outcome: PredictionOutcome
    ) -> None:
        \"\"\"Update expert's accuracy profile with new outcome\"\"\"
        try:
            # Get or create expert profile
            if expert_id not in self.expert_profiles:
                self.expert_profiles[expert_id] = ExpertAccuracyProfile(
                    expert_id=expert_id,
                    overall_accuracy=0.0,
                    total_predictions=0,
                    correct_predictions=0
                )
            
            profile = self.expert_profiles[expert_id]
            
            # Update overall statistics
            profile.total_predictions += 1
            if outcome.is_correct:
                profile.correct_predictions += 1
            
            profile.overall_accuracy = profile.correct_predictions / profile.total_predictions
            
            # Update category-specific accuracy
            await self._update_category_accuracy(profile, outcome)
            
            # Recalculate derived metrics
            await self._recalculate_derived_metrics(profile)
            
            profile.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f\"Failed to update expert accuracy profile: {e}\")
    
    async def _update_category_accuracy(
        self, 
        profile: ExpertAccuracyProfile, 
        outcome: PredictionOutcome
    ) -> None:
        \"\"\"Update category-specific accuracy metrics\"\"\"
        try:
            category = outcome.category
            
            # Get or create category accuracy
            if category not in profile.category_accuracies:
                profile.category_accuracies[category] = CategoryAccuracy(
                    category=category,
                    total_predictions=0,
                    correct_predictions=0,
                    accuracy=0.0,
                    confidence_weighted_accuracy=0.0,
                    recent_accuracy=0.0,
                    trend='stable',
                    calibration_score=0.5,
                    last_updated=datetime.now()
                )
            
            cat_acc = profile.category_accuracies[category]
            
            # Update basic counts
            cat_acc.total_predictions += 1
            if outcome.is_correct:
                cat_acc.correct_predictions += 1
            
            # Calculate accuracy
            cat_acc.accuracy = cat_acc.correct_predictions / cat_acc.total_predictions
            
            # Calculate confidence-weighted accuracy
            cat_acc.confidence_weighted_accuracy = self._calculate_confidence_weighted_accuracy(
                profile.expert_id, category
            )
            
            # Calculate recent accuracy (last N predictions)
            cat_acc.recent_accuracy = self._calculate_recent_category_accuracy(
                profile.expert_id, category
            )
            
            # Calculate trend
            cat_acc.trend = self._calculate_category_trend(
                profile.expert_id, category
            )
            
            # Calculate calibration score
            cat_acc.calibration_score = self._calculate_category_calibration(
                profile.expert_id, category
            )
            
            cat_acc.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f\"Failed to update category accuracy: {e}\")
    
    def _calculate_confidence_weighted_accuracy(
        self, 
        expert_id: str, 
        category: str
    ) -> float:
        \"\"\"Calculate confidence-weighted accuracy for a category\"\"\"
        try:
            outcomes = [
                o for o in self.prediction_outcomes[expert_id] 
                if o.category == category
            ]
            
            if not outcomes:
                return 0.0
            
            total_weighted_score = 0.0
            total_confidence = 0.0
            
            for outcome in outcomes:
                weight = outcome.confidence
                score = 1.0 if outcome.is_correct else 0.0
                
                total_weighted_score += score * weight
                total_confidence += weight
            
            return total_weighted_score / total_confidence if total_confidence > 0 else 0.0
            
        except Exception as e:
            logger.error(f\"Failed to calculate confidence-weighted accuracy: {e}\")
            return 0.0
    
    def _calculate_recent_category_accuracy(
        self, 
        expert_id: str, 
        category: str
    ) -> float:
        \"\"\"Calculate accuracy for recent predictions in a category\"\"\"
        try:
            outcomes = [
                o for o in self.prediction_outcomes[expert_id] 
                if o.category == category
            ]
            
            # Sort by timestamp and take recent ones
            outcomes.sort(key=lambda x: x.prediction_timestamp, reverse=True)
            recent_outcomes = outcomes[:self.recent_window_size]
            
            if not recent_outcomes:
                return 0.0
            
            correct_count = sum(1 for o in recent_outcomes if o.is_correct)
            return correct_count / len(recent_outcomes)
            
        except Exception as e:
            logger.error(f\"Failed to calculate recent category accuracy: {e}\")
            return 0.0
    
    def _calculate_category_trend(
        self, 
        expert_id: str, 
        category: str
    ) -> str:
        \"\"\"Calculate performance trend for a category\"\"\"
        try:
            outcomes = [
                o for o in self.prediction_outcomes[expert_id] 
                if o.category == category
            ]
            
            if len(outcomes) < self.min_predictions_for_trend:
                return 'stable'
            
            # Sort by timestamp
            outcomes.sort(key=lambda x: x.prediction_timestamp)
            
            # Split into two halves
            mid_point = len(outcomes) // 2
            earlier_half = outcomes[:mid_point]
            later_half = outcomes[mid_point:]
            
            # Calculate accuracy for each half
            earlier_accuracy = sum(1 for o in earlier_half if o.is_correct) / len(earlier_half)
            later_accuracy = sum(1 for o in later_half if o.is_correct) / len(later_half)
            
            # Determine trend
            diff = later_accuracy - earlier_accuracy
            if diff > 0.1:
                return 'improving'
            elif diff < -0.1:
                return 'declining'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f\"Failed to calculate category trend: {e}\")
            return 'stable'
    
    def _calculate_category_calibration(
        self, 
        expert_id: str, 
        category: str
    ) -> float:
        \"\"\"Calculate confidence calibration for a category\"\"\"
        try:
            outcomes = [
                o for o in self.prediction_outcomes[expert_id] 
                if o.category == category
            ]
            
            if len(outcomes) < 5:  # Need minimum predictions for calibration
                return 0.5
            
            # Create confidence bins
            bins = np.linspace(0, 1, self.calibration_bins + 1)
            bin_accuracies = []
            bin_confidences = []
            
            for i in range(self.calibration_bins):
                bin_min = bins[i]
                bin_max = bins[i + 1]
                
                bin_outcomes = [
                    o for o in outcomes 
                    if bin_min <= o.confidence < bin_max
                ]
                
                if bin_outcomes:
                    bin_accuracy = sum(1 for o in bin_outcomes if o.is_correct) / len(bin_outcomes)
                    bin_confidence = sum(o.confidence for o in bin_outcomes) / len(bin_outcomes)
                    
                    bin_accuracies.append(bin_accuracy)
                    bin_confidences.append(bin_confidence)
            
            if not bin_accuracies:
                return 0.5
            
            # Calculate calibration error (lower is better)
            calibration_error = np.mean([
                abs(acc - conf) 
                for acc, conf in zip(bin_accuracies, bin_confidences)
            ])
            
            # Convert to calibration score (higher is better)
            calibration_score = 1.0 - calibration_error
            return max(0.0, min(1.0, calibration_score))
            
        except Exception as e:
            logger.error(f\"Failed to calculate category calibration: {e}\")
            return 0.5
    
    async def _recalculate_derived_metrics(self, profile: ExpertAccuracyProfile) -> None:
        \"\"\"Recalculate derived metrics for expert profile\"\"\"
        try:
            # Update recent performance
            profile.recent_performance = {
                category: cat_acc.recent_accuracy
                for category, cat_acc in profile.category_accuracies.items()
            }
            
            # Calculate overall performance trend
            trends = [cat_acc.trend for cat_acc in profile.category_accuracies.values()]
            if trends:
                improving_count = trends.count('improving')
                declining_count = trends.count('declining')
                
                if improving_count > declining_count:
                    profile.performance_trend = 'improving'
                elif declining_count > improving_count:
                    profile.performance_trend = 'declining'
                else:
                    profile.performance_trend = 'stable'
            
            # Calculate overall confidence calibration
            calibrations = [
                cat_acc.calibration_score 
                for cat_acc in profile.category_accuracies.values()
            ]
            
            if calibrations:
                profile.confidence_calibration = sum(calibrations) / len(calibrations)
            
            # Calculate specialization scores
            profile.specialization_scores = {
                category: cat_acc.accuracy
                for category, cat_acc in profile.category_accuracies.items()
                if cat_acc.total_predictions >= 5  # Minimum predictions for reliable score
            }
            
        except Exception as e:
            logger.error(f\"Failed to recalculate derived metrics: {e}\")
    
    async def get_expert_accuracy_profile(self, expert_id: str) -> Optional[ExpertAccuracyProfile]:
        \"\"\"Get comprehensive accuracy profile for an expert\"\"\"
        try:
            if expert_id in self.expert_profiles:
                return self.expert_profiles[expert_id]
            
            # Try to load from database
            if self.supabase:
                profile = await self._load_expert_profile_from_db(expert_id)
                if profile:
                    self.expert_profiles[expert_id] = profile
                    return profile
            
            return None
            
        except Exception as e:
            logger.error(f\"Failed to get expert accuracy profile: {e}\")
            return None
    
    async def get_category_leaderboard(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        \"\"\"Get leaderboard for a specific category\"\"\"
        try:
            category_performances = []
            
            for expert_id, profile in self.expert_profiles.items():
                if category in profile.category_accuracies:
                    cat_acc = profile.category_accuracies[category]
                    
                    if cat_acc.total_predictions >= 5:  # Minimum for inclusion
                        category_performances.append({
                            'expert_id': expert_id,
                            'accuracy': cat_acc.accuracy,
                            'total_predictions': cat_acc.total_predictions,
                            'recent_accuracy': cat_acc.recent_accuracy,
                            'trend': cat_acc.trend,
                            'calibration_score': cat_acc.calibration_score,
                            'confidence_weighted_accuracy': cat_acc.confidence_weighted_accuracy
                        })
            
            # Sort by accuracy (descending)
            category_performances.sort(key=lambda x: x['accuracy'], reverse=True)
            
            return category_performances[:limit]
            
        except Exception as e:
            logger.error(f\"Failed to get category leaderboard: {e}\")
            return []
    
    async def get_accuracy_summary(self) -> Dict[str, Any]:
        \"\"\"Get overall accuracy tracking summary\"\"\"
        try:
            total_experts = len(self.expert_profiles)
            total_predictions = sum(p.total_predictions for p in self.expert_profiles.values())
            total_correct = sum(p.correct_predictions for p in self.expert_profiles.values())
            
            overall_accuracy = total_correct / total_predictions if total_predictions > 0 else 0
            
            # Category statistics
            category_stats = {}
            all_categories = set()
            for profile in self.expert_profiles.values():
                all_categories.update(profile.category_accuracies.keys())
            
            for category in all_categories:
                category_predictions = 0
                category_correct = 0
                experts_in_category = 0
                
                for profile in self.expert_profiles.values():
                    if category in profile.category_accuracies:
                        cat_acc = profile.category_accuracies[category]
                        category_predictions += cat_acc.total_predictions
                        category_correct += cat_acc.correct_predictions
                        experts_in_category += 1
                
                category_accuracy = category_correct / category_predictions if category_predictions > 0 else 0
                
                category_stats[category] = {
                    'total_predictions': category_predictions,
                    'accuracy': category_accuracy,
                    'experts_participating': experts_in_category
                }
            
            return {
                'total_experts_tracked': total_experts,
                'total_predictions_evaluated': total_predictions,
                'overall_accuracy': overall_accuracy,
                'categories_tracked': len(all_categories),
                'category_statistics': category_stats,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f\"Failed to get accuracy summary: {e}\")
            return {'error': str(e)}
    
    # Database operations (placeholders)
    async def _store_prediction_outcome(self, outcome: PredictionOutcome) -> None:
        \"\"\"Store prediction outcome in database\"\"\"
        try:
            if not self.supabase:
                return
            
            self.supabase.table('prediction_outcomes').insert(outcome.to_dict()).execute()
            
        except Exception as e:
            logger.error(f\"Failed to store prediction outcome: {e}\")
    
    async def _load_expert_profile_from_db(self, expert_id: str) -> Optional[ExpertAccuracyProfile]:
        \"\"\"Load expert profile from database\"\"\"
        try:
            if not self.supabase:
                return None
            
            # This would load profile from database
            # Implementation depends on specific database schema
            return None
            
        except Exception as e:
            logger.error(f\"Failed to load expert profile from database: {e}\")
            return None