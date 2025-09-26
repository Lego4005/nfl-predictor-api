"""
Vote Weight Calculator and Consensus Builder
Implements weighted voting mechanism for AI Council predictions
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class VoteWeight:
    """Individual expert's vote weight breakdown"""
    expert_id: str
    overall_weight: float
    accuracy_component: float
    recent_performance_component: float
    confidence_component: float
    council_tenure_component: float
    normalized_weight: float

@dataclass
class WeightedPrediction:
    """Prediction with associated weight"""
    expert_id: str
    prediction_value: Any
    confidence: float
    weight: float
    category: str

@dataclass
class ConsensusResult:
    """Result of consensus calculation"""
    category: str
    consensus_value: Any
    confidence_score: float
    agreement_level: float
    total_weight: float
    participating_experts: int
    method_used: str
    breakdown: Dict[str, Any]

class VoteWeightCalculator:
    """Calculates voting weights for AI Council members"""
    
    def __init__(
        self,
        accuracy_weight: float = 0.40,
        recent_performance_weight: float = 0.30,
        confidence_weight: float = 0.20,
        council_tenure_weight: float = 0.10
    ):
        self.accuracy_weight = accuracy_weight
        self.recent_performance_weight = recent_performance_weight
        self.confidence_weight = confidence_weight
        self.council_tenure_weight = council_tenure_weight
        
        # Validate weights sum to 1.0
        total = accuracy_weight + recent_performance_weight + confidence_weight + council_tenure_weight
        if abs(total - 1.0) > 0.001:
            logger.warning(f"Vote weights sum to {total}, normalizing...")
            self._normalize_weights()
    
    def _normalize_weights(self) -> None:
        """Normalize weights to sum to 1.0"""
        total = (self.accuracy_weight + self.recent_performance_weight + 
                self.confidence_weight + self.council_tenure_weight)
        
        if total > 0:
            self.accuracy_weight /= total
            self.recent_performance_weight /= total
            self.confidence_weight /= total
            self.council_tenure_weight /= total
    
    def calculate_vote_weights(
        self,
        council_experts: List[Any],
        prediction_confidence: Optional[Dict[str, float]] = None
    ) -> List[VoteWeight]:
        """Calculate voting weights for all council members"""
        try:
            vote_weights = []
            prediction_confidence = prediction_confidence or {}
            
            for expert in council_experts:
                weight = self._calculate_expert_vote_weight(expert, prediction_confidence)
                vote_weights.append(weight)
            
            # Normalize weights to sum to 1.0
            total_weight = sum(w.overall_weight for w in vote_weights)
            if total_weight > 0:
                for weight in vote_weights:
                    weight.normalized_weight = weight.overall_weight / total_weight
            else:
                # Equal weights fallback
                equal_weight = 1.0 / len(vote_weights) if vote_weights else 0.0
                for weight in vote_weights:
                    weight.normalized_weight = equal_weight
            
            logger.info(f"Calculated vote weights for {len(vote_weights)} council members")
            
            return vote_weights
            
        except Exception as e:
            logger.error(f"Failed to calculate vote weights: {e}")
            return []
    
    def _calculate_expert_vote_weight(
        self,
        expert: Any,
        prediction_confidence: Dict[str, float]
    ) -> VoteWeight:
        """Calculate vote weight for a single expert"""
        try:
            expert_id = expert.expert_id
            
            # Component 1: Accuracy (40% of weight)
            accuracy = getattr(expert, 'overall_accuracy', 0.5)
            accuracy_component = max(0.0, (accuracy - 0.5) * 2.0) * self.accuracy_weight
            
            # Component 2: Recent Performance (30% of weight)
            recent_trend = getattr(expert, 'recent_trend', 'stable')
            trend_scores = {'improving': 1.0, 'stable': 0.6, 'declining': 0.2}
            recent_performance_component = trend_scores.get(recent_trend, 0.5) * self.recent_performance_weight
            
            # Component 3: Prediction Confidence (20% of weight)
            expert_confidence = prediction_confidence.get(expert_id, 0.5)
            confidence_component = expert_confidence * self.confidence_weight
            
            # Component 4: Council Tenure/Experience (10% of weight)
            council_appearances = getattr(expert, 'council_appearances', 1)
            # Logarithmic scaling for tenure (diminishing returns)
            tenure_score = min(1.0, np.log(council_appearances + 1) / np.log(10))
            council_tenure_component = tenure_score * self.council_tenure_weight
            
            # Calculate overall weight
            overall_weight = (
                accuracy_component + 
                recent_performance_component + 
                confidence_component + 
                council_tenure_component
            )
            
            return VoteWeight(
                expert_id=expert_id,
                overall_weight=overall_weight,
                accuracy_component=accuracy_component,
                recent_performance_component=recent_performance_component,
                confidence_component=confidence_component,
                council_tenure_component=council_tenure_component,
                normalized_weight=0.0  # Will be set during normalization
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate vote weight for expert {expert.expert_id}: {e}")
            return VoteWeight(
                expert_id=expert.expert_id,
                overall_weight=0.2,  # Default equal weight
                accuracy_component=0.0,
                recent_performance_component=0.0,
                confidence_component=0.0,
                council_tenure_component=0.0,
                normalized_weight=0.2
            )

class ConsensusBuilder:
    """Builds consensus predictions from weighted AI Council votes"""
    
    def __init__(self, weight_calculator: Optional[VoteWeightCalculator] = None):
        self.weight_calculator = weight_calculator or VoteWeightCalculator()
    
    def build_consensus(
        self,
        council_predictions: Dict[str, Any],  # expert_id -> prediction
        council_experts: List[Any],
        prediction_category: str
    ) -> ConsensusResult:
        """Build consensus prediction for a specific category"""
        try:
            # Extract predictions and confidences
            weighted_predictions = self._extract_weighted_predictions(
                council_predictions, council_experts, prediction_category
            )
            
            if not weighted_predictions:
                return ConsensusResult(
                    category=prediction_category,
                    consensus_value=None,
                    confidence_score=0.0,
                    agreement_level=0.0,
                    total_weight=0.0,
                    participating_experts=0,
                    method_used="none",
                    breakdown={"error": "No valid predictions"}
                )
            
            # Determine consensus method based on prediction type
            sample_prediction = weighted_predictions[0].prediction_value
            
            if isinstance(sample_prediction, (int, float)):
                return self._build_numeric_consensus(weighted_predictions, prediction_category)
            elif isinstance(sample_prediction, str):
                return self._build_categorical_consensus(weighted_predictions, prediction_category)
            else:
                return self._build_generic_consensus(weighted_predictions, prediction_category)
                
        except Exception as e:
            logger.error(f"Failed to build consensus for {prediction_category}: {e}")
            return ConsensusResult(
                category=prediction_category,
                consensus_value=None,
                confidence_score=0.0,
                agreement_level=0.0,
                total_weight=0.0,
                participating_experts=0,
                method_used="error",
                breakdown={"error": str(e)}
            )
    
    def _extract_weighted_predictions(
        self,
        council_predictions: Dict[str, Any],
        council_experts: List[Any],
        category: str
    ) -> List[WeightedPrediction]:
        """Extract and weight predictions for a specific category"""
        try:
            # Calculate vote weights
            expert_confidences = {}
            for expert_id, prediction in council_predictions.items():
                if hasattr(prediction, 'confidence_overall'):
                    expert_confidences[expert_id] = prediction.confidence_overall
                elif hasattr(prediction, 'confidence_by_category'):
                    expert_confidences[expert_id] = prediction.confidence_by_category.get(category, 0.5)
                else:
                    expert_confidences[expert_id] = 0.5
            
            vote_weights = self.weight_calculator.calculate_vote_weights(
                council_experts, expert_confidences
            )
            
            # Create weight lookup
            weight_lookup = {vw.expert_id: vw.normalized_weight for vw in vote_weights}
            
            # Extract weighted predictions
            weighted_predictions = []
            for expert_id, prediction in council_predictions.items():
                try:
                    # Get prediction value for this category
                    prediction_value = self._get_prediction_value(prediction, category)
                    if prediction_value is not None:
                        confidence = expert_confidences.get(expert_id, 0.5)
                        weight = weight_lookup.get(expert_id, 0.2)  # Default equal weight
                        
                        weighted_predictions.append(WeightedPrediction(
                            expert_id=expert_id,
                            prediction_value=prediction_value,
                            confidence=confidence,
                            weight=weight,
                            category=category
                        ))
                        
                except Exception as e:
                    logger.warning(f"Failed to extract prediction for {expert_id}, category {category}: {e}")
                    continue
            
            return weighted_predictions
            
        except Exception as e:
            logger.error(f"Failed to extract weighted predictions: {e}")
            return []
    
    def _get_prediction_value(self, prediction: Any, category: str) -> Any:
        """Extract prediction value for a specific category"""
        try:
            # Map category names to prediction attributes
            category_mapping = {
                'winner_prediction': 'winner_prediction',
                'exact_score_home': 'exact_score_home',
                'exact_score_away': 'exact_score_away',
                'margin_of_victory': 'margin_of_victory',
                'against_the_spread': 'against_the_spread',
                'totals_over_under': 'totals_over_under',
                'first_half_winner': 'first_half_winner',
                'qb_passing_yards': 'qb_passing_yards',
                'qb_touchdowns': 'qb_touchdowns',
                'weather_impact_score': 'weather_impact_score',
                'home_field_advantage': 'home_field_advantage'
            }
            
            attribute_name = category_mapping.get(category, category)
            
            if hasattr(prediction, attribute_name):
                return getattr(prediction, attribute_name)
            elif isinstance(prediction, dict):
                return prediction.get(category)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get prediction value for category {category}: {e}")
            return None
    
    def _build_numeric_consensus(
        self,
        weighted_predictions: List[WeightedPrediction],
        category: str
    ) -> ConsensusResult:
        """Build consensus for numeric predictions using weighted average"""
        try:
            # Calculate weighted average
            total_weighted_value = 0.0
            total_weight = 0.0
            values = []
            
            for wp in weighted_predictions:
                if wp.prediction_value is not None:
                    total_weighted_value += float(wp.prediction_value) * wp.weight
                    total_weight += wp.weight
                    values.append(float(wp.prediction_value))
            
            if total_weight == 0:
                return ConsensusResult(
                    category=category,
                    consensus_value=None,
                    confidence_score=0.0,
                    agreement_level=0.0,
                    total_weight=0.0,
                    participating_experts=0,
                    method_used="numeric_weighted_average",
                    breakdown={"error": "No valid numeric predictions"}
                )
            
            consensus_value = total_weighted_value / total_weight
            
            # Calculate agreement level (inverse of coefficient of variation)
            if len(values) > 1:
                std_dev = np.std(values)
                mean_val = np.mean(values)
                agreement_level = 1.0 - (std_dev / mean_val if mean_val != 0 else 1.0)
                agreement_level = max(0.0, min(1.0, agreement_level))
            else:
                agreement_level = 1.0
            
            # Calculate confidence score (weighted average of individual confidences)
            total_confidence = sum(wp.confidence * wp.weight for wp in weighted_predictions)
            confidence_score = total_confidence / total_weight if total_weight > 0 else 0.0
            
            return ConsensusResult(
                category=category,
                consensus_value=consensus_value,
                confidence_score=confidence_score,
                agreement_level=agreement_level,
                total_weight=total_weight,
                participating_experts=len(weighted_predictions),
                method_used="numeric_weighted_average",
                breakdown={
                    "individual_predictions": [
                        {
                            "expert_id": wp.expert_id,
                            "value": wp.prediction_value,
                            "weight": wp.weight,
                            "confidence": wp.confidence
                        }
                        for wp in weighted_predictions
                    ],
                    "statistics": {
                        "mean": np.mean(values),
                        "std_dev": np.std(values),
                        "min": min(values),
                        "max": max(values)
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to build numeric consensus: {e}")
            return ConsensusResult(
                category=category,
                consensus_value=None,
                confidence_score=0.0,
                agreement_level=0.0,
                total_weight=0.0,
                participating_experts=0,
                method_used="numeric_weighted_average",
                breakdown={"error": str(e)}
            )
    
    def _build_categorical_consensus(
        self,
        weighted_predictions: List[WeightedPrediction],
        category: str
    ) -> ConsensusResult:
        """Build consensus for categorical predictions using weighted voting"""
        try:
            # Count weighted votes for each category
            vote_weights = {}
            confidence_by_category = {}
            
            for wp in weighted_predictions:
                value = wp.prediction_value
                if value is not None:
                    vote_weights[value] = vote_weights.get(value, 0.0) + wp.weight
                    if value not in confidence_by_category:
                        confidence_by_category[value] = []
                    confidence_by_category[value].append(wp.confidence * wp.weight)
            
            if not vote_weights:
                return ConsensusResult(
                    category=category,
                    consensus_value=None,
                    confidence_score=0.0,
                    agreement_level=0.0,
                    total_weight=0.0,
                    participating_experts=0,
                    method_used="categorical_weighted_voting",
                    breakdown={"error": "No valid categorical predictions"}
                )
            
            # Find consensus value (highest weighted vote)
            consensus_value = max(vote_weights.keys(), key=lambda k: vote_weights[k])
            consensus_weight = vote_weights[consensus_value]
            total_weight = sum(vote_weights.values())
            
            # Calculate agreement level (proportion of weight for consensus)
            agreement_level = consensus_weight / total_weight if total_weight > 0 else 0.0
            
            # Calculate confidence score for consensus value
            consensus_confidences = confidence_by_category.get(consensus_value, [])
            confidence_score = sum(consensus_confidences) / consensus_weight if consensus_weight > 0 else 0.0
            
            return ConsensusResult(
                category=category,
                consensus_value=consensus_value,
                confidence_score=confidence_score,
                agreement_level=agreement_level,
                total_weight=total_weight,
                participating_experts=len(weighted_predictions),
                method_used="categorical_weighted_voting",
                breakdown={
                    "vote_distribution": vote_weights,
                    "individual_votes": [
                        {
                            "expert_id": wp.expert_id,
                            "value": wp.prediction_value,
                            "weight": wp.weight,
                            "confidence": wp.confidence
                        }
                        for wp in weighted_predictions
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to build categorical consensus: {e}")
            return ConsensusResult(
                category=category,
                consensus_value=None,
                confidence_score=0.0,
                agreement_level=0.0,
                total_weight=0.0,
                participating_experts=0,
                method_used="categorical_weighted_voting",
                breakdown={"error": str(e)}
            )
    
    def _build_generic_consensus(
        self,
        weighted_predictions: List[WeightedPrediction],
        category: str
    ) -> ConsensusResult:
        """Build consensus for other prediction types"""
        try:
            # For generic types, use most confident prediction
            if not weighted_predictions:
                return ConsensusResult(
                    category=category,
                    consensus_value=None,
                    confidence_score=0.0,
                    agreement_level=0.0,
                    total_weight=0.0,
                    participating_experts=0,
                    method_used="highest_confidence",
                    breakdown={"error": "No predictions"}
                )
            
            # Find prediction with highest confidence * weight score
            best_prediction = max(
                weighted_predictions,
                key=lambda wp: wp.confidence * wp.weight
            )
            
            total_weight = sum(wp.weight for wp in weighted_predictions)
            avg_confidence = sum(wp.confidence * wp.weight for wp in weighted_predictions) / total_weight
            
            return ConsensusResult(
                category=category,
                consensus_value=best_prediction.prediction_value,
                confidence_score=best_prediction.confidence,
                agreement_level=0.5,  # Generic fallback
                total_weight=total_weight,
                participating_experts=len(weighted_predictions),
                method_used="highest_confidence",
                breakdown={
                    "selected_prediction": {
                        "expert_id": best_prediction.expert_id,
                        "value": best_prediction.prediction_value,
                        "confidence": best_prediction.confidence,
                        "weight": best_prediction.weight
                    },
                    "all_predictions": [
                        {
                            "expert_id": wp.expert_id,
                            "value": str(wp.prediction_value),
                            "confidence": wp.confidence,
                            "weight": wp.weight
                        }
                        for wp in weighted_predictions
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to build generic consensus: {e}")
            return ConsensusResult(
                category=category,
                consensus_value=None,
                confidence_score=0.0,
                agreement_level=0.0,
                total_weight=0.0,
                participating_experts=0,
                method_used="highest_confidence",
                breakdown={"error": str(e)}
            )