"""
Mock Expert for Testing
Simple mock implementation of an expert for testing the competition framework
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import numpy as np

class MockExpert:
    """Mock expert implementation for testing"""
    
    def __init__(self, expert_id: str, name: str, personality: str):
        self.expert_id = expert_id
        self.name = name
        self.personality = personality
        
        # Performance metrics
        self.total_predictions = 0
        self.correct_predictions = 0
        self.overall_accuracy = 0.5 + random.uniform(-0.1, 0.1)  # Random baseline accuracy
        self.current_rank = 999
        self.peak_rank = 999
        self.leaderboard_score = 0.0
        
        # Advanced metrics
        self.category_accuracies = {}
        self.confidence_calibration = 0.5 + random.uniform(-0.1, 0.1)
        self.consistency_score = 0.5 + random.uniform(-0.1, 0.1)
        self.specialization_strength = {}
        
        # Council participation
        self.council_appearances = 0
        self.council_performance = 0.5
        
        # Personality traits (mock)
        self.personality_traits = self._generate_mock_personality_traits()
        self.algorithm_parameters = self._generate_mock_algorithm_parameters()
        
        # Status
        self.status = 'active'
        self.last_updated = datetime.now()
    
    def _generate_mock_personality_traits(self) -> Dict[str, float]:
        """Generate mock personality traits based on personality type"""
        base_traits = {
            'risk_tolerance': 0.5,
            'contrarian_tendency': 0.5,
            'data_reliance': 0.5,
            'intuition_weight': 0.5,
            'confidence_level': 0.5
        }
        
        # Adjust traits based on personality
        if self.personality == 'analytical':
            base_traits.update({
                'data_reliance': 0.9,
                'risk_tolerance': 0.3,
                'confidence_level': 0.7
            })
        elif self.personality == 'aggressive':
            base_traits.update({
                'risk_tolerance': 0.9,
                'contrarian_tendency': 0.7,
                'confidence_level': 0.8
            })
        elif self.personality == 'contrarian':
            base_traits.update({
                'contrarian_tendency': 0.9,
                'risk_tolerance': 0.7,
                'intuition_weight': 0.6
            })
        elif self.personality == 'intuitive':
            base_traits.update({
                'intuition_weight': 0.9,
                'data_reliance': 0.3,
                'confidence_level': 0.6
            })
        
        # Add some randomness
        for trait, value in base_traits.items():
            base_traits[trait] = max(0.0, min(1.0, value + random.uniform(-0.1, 0.1)))
        
        return base_traits
    
    def _generate_mock_algorithm_parameters(self) -> Dict[str, Any]:
        """Generate mock algorithm parameters"""
        return {
            'learning_rate': random.uniform(0.01, 0.1),
            'confidence_threshold': random.uniform(0.4, 0.8),
            'weight_decay': random.uniform(0.01, 0.05),
            'momentum': random.uniform(0.1, 0.3),
            'regularization': random.uniform(0.01, 0.1)
        }
    
    def make_prediction(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock prediction"""
        # Simulate prediction generation based on personality
        confidence = self.personality_traits.get('confidence_level', 0.5)
        risk_tolerance = self.personality_traits.get('risk_tolerance', 0.5)
        
        # Mock prediction logic
        home_win_prob = 0.5 + random.uniform(-0.3, 0.3)
        home_win_prob = max(0.1, min(0.9, home_win_prob))
        
        # Adjust confidence based on personality
        prediction_confidence = confidence * (0.7 + random.uniform(0, 0.3))
        
        prediction = {
            'expert_id': self.expert_id,
            'expert_name': self.name,
            'prediction': {
                'winner_prediction': 'home' if home_win_prob > 0.5 else 'away',
                'home_win_probability': home_win_prob,
                'away_win_probability': 1 - home_win_prob,
                'spread_prediction': (home_win_prob - 0.5) * 20,  # Convert to point spread
                'total_prediction': 45 + random.uniform(-10, 10),
                'confidence_overall': prediction_confidence
            },
            'reasoning': f"Mock prediction from {self.name} based on {self.personality} personality",
            'prediction_timestamp': datetime.now().isoformat()
        }
        
        return prediction
    
    def update_performance(self, was_correct: bool, confidence: float = None) -> None:
        """Update expert performance metrics"""
        self.total_predictions += 1
        if was_correct:
            self.correct_predictions += 1
        
        # Recalculate accuracy
        if self.total_predictions > 0:
            self.overall_accuracy = self.correct_predictions / self.total_predictions
        
        # Update other metrics (simplified)
        if confidence:
            # Simple confidence calibration update
            calibration_error = abs(confidence - (1.0 if was_correct else 0.0))
            self.confidence_calibration = 0.9 * self.confidence_calibration + 0.1 * (1.0 - calibration_error)
        
        self.last_updated = datetime.now()
    
    def get_specializations(self) -> List[str]:
        """Get expert specializations based on personality"""
        specialization_map = {
            'analytical': ['statistical_analysis', 'trend_analysis', 'data_modeling'],
            'aggressive': ['upset_detection', 'high_risk_picks', 'contrarian_plays'],
            'contrarian': ['contrarian_analysis', 'public_fading', 'market_inefficiency'],
            'intuitive': ['gut_instinct', 'momentum_reading', 'situational_awareness'],
            'mathematical': ['statistical_modeling', 'regression_analysis', 'probability_theory'],
            'trend_following': ['momentum_analysis', 'streak_detection', 'trend_identification'],
            'market_focused': ['line_movement', 'sharp_money', 'market_sentiment'],
            'research_driven': ['deep_analysis', 'fundamental_research', 'contextual_factors']
        }
        
        return specialization_map.get(self.personality, ['general_analysis'])
    
    def adapt_parameters(self, adaptation_type: str, changes: Dict[str, Any]) -> bool:
        """Adapt expert parameters (mock implementation)"""
        try:
            if adaptation_type == 'personality_adjustment':
                for trait, change in changes.items():
                    if trait in self.personality_traits:
                        old_value = self.personality_traits[trait]
                        new_value = max(0.0, min(1.0, old_value + change))
                        self.personality_traits[trait] = new_value
            
            elif adaptation_type == 'algorithm_tuning':
                for param, change in changes.items():
                    if param in self.algorithm_parameters:
                        old_value = self.algorithm_parameters[param]
                        new_value = max(0.0, old_value + change)
                        self.algorithm_parameters[param] = new_value
            
            self.last_updated = datetime.now()
            return True
            
        except Exception as e:
            return False
    
    def __repr__(self) -> str:
        return f"MockExpert(id='{self.expert_id}', name='{self.name}', personality='{self.personality}', accuracy={self.overall_accuracy:.3f})"