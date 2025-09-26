"""
Expert Ranking System
Multi-dimensional ranking algorithm for expert competition
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class RankingWeights:
    """Weights for different ranking components"""
    overall_accuracy: float = 0.35      # 35% - Overall prediction accuracy
    recent_performance: float = 0.25    # 25% - Last 4 weeks performance
    consistency: float = 0.20           # 20% - Consistency across categories
    confidence_calibration: float = 0.10 # 10% - How well confidence predicts success
    specialization_strength: float = 0.10 # 10% - Strength in specialized areas

class ExpertRankingSystem:
    """Advanced ranking system for expert competition"""
    
    def __init__(self, weights: RankingWeights = None):
        self.weights = weights or RankingWeights()
        self.ranking_history: List[Dict] = []
    
    async def calculate_rankings(self, experts: Dict[str, Any]) -> List[Any]:
        """Calculate comprehensive rankings for all experts"""
        try:
            expert_scores = {}
            
            for expert_id, expert in experts.items():
                score_components = await self._calculate_score_components(expert)
                total_score = self._calculate_weighted_score(score_components)
                
                expert_scores[expert_id] = {
                    'expert_id': expert_id,
                    'total_score': total_score,
                    'components': score_components,
                    'expert': expert
                }
            
            # Sort by total score (descending)
            ranked_experts = sorted(
                expert_scores.values(),
                key=lambda x: x['total_score'],
                reverse=True
            )
            
            # Assign ranks and create metrics objects
            rankings = []
            for rank, expert_data in enumerate(ranked_experts, 1):
                from .competition_framework import ExpertPerformanceMetrics
                
                metrics = ExpertPerformanceMetrics(
                    expert_id=expert_data['expert_id'],
                    overall_accuracy=expert_data['components']['overall_accuracy'],
                    category_accuracies=expert_data['components']['category_accuracies'],
                    confidence_calibration=expert_data['components']['confidence_calibration'],
                    recent_trend=expert_data['components']['trend'],
                    total_predictions=getattr(expert_data['expert'], 'total_predictions', 0),
                    correct_predictions=getattr(expert_data['expert'], 'correct_predictions', 0),
                    leaderboard_score=expert_data['total_score'],
                    current_rank=rank,
                    peak_rank=min(getattr(expert_data['expert'], 'peak_rank', rank), rank),
                    consistency_score=expert_data['components']['consistency'],
                    specialization_strength=expert_data['components']['specialization_strength'],
                    last_updated=datetime.now()
                )
                rankings.append(metrics)
            
            # Update peak ranks
            self._update_peak_ranks(rankings)
            
            # Store ranking history
            self._store_ranking_snapshot(rankings)
            
            logger.info(f"📊 Calculated rankings for {len(rankings)} experts")
            return rankings
            
        except Exception as e:
            logger.error(f"Failed to calculate rankings: {e}")
            return []
    
    async def _calculate_score_components(self, expert: Any) -> Dict[str, Any]:
        """Calculate individual scoring components for an expert"""
        components = {}
        
        # 1. Overall Accuracy Component
        components['overall_accuracy'] = self._calculate_overall_accuracy(expert)
        
        # 2. Recent Performance Component  
        components['recent_performance'] = await self._calculate_recent_performance(expert)
        
        # 3. Consistency Component
        components['consistency'] = self._calculate_consistency(expert)
        
        # 4. Confidence Calibration Component
        components['confidence_calibration'] = self._calculate_confidence_calibration(expert)
        
        # 5. Specialization Strength Component
        components['specialization_strength'] = self._calculate_specialization_strength(expert)
        
        # Additional metadata
        components['category_accuracies'] = self._get_category_accuracies(expert)
        components['trend'] = self._determine_trend(expert)
        
        return components
    
    def _calculate_overall_accuracy(self, expert: Any) -> float:
        """Calculate overall prediction accuracy"""
        total_predictions = getattr(expert, 'total_predictions', 0)
        correct_predictions = getattr(expert, 'correct_predictions', 0)
        
        if total_predictions == 0:
            return 0.5  # Neutral starting point
        
        return correct_predictions / total_predictions
    
    async def _calculate_recent_performance(self, expert: Any, weeks: int = 4) -> float:
        """Calculate performance over recent weeks"""
        # In real implementation, this would query database for recent predictions
        # For now, simulate based on overall performance with some variance
        base_accuracy = self._calculate_overall_accuracy(expert)
        
        # Add some variance to simulate recent performance trends
        variance = np.random.normal(0, 0.05)  # ±5% variance
        recent_performance = max(0, min(1, base_accuracy + variance))
        
        return recent_performance
    
    def _calculate_consistency(self, expert: Any) -> float:
        """Calculate consistency across different prediction categories"""
        category_accuracies = self._get_category_accuracies(expert)
        
        if not category_accuracies:
            return 0.5
        
        accuracies = list(category_accuracies.values())
        if len(accuracies) <= 1:
            return 1.0
        
        # Calculate standard deviation of category accuracies
        std_dev = np.std(accuracies)
        # Convert to consistency score (lower std_dev = higher consistency)
        consistency = max(0, 1 - (std_dev * 2))  # Normalize to 0-1 range
        
        return consistency
    
    def _calculate_confidence_calibration(self, expert: Any) -> float:
        """Calculate how well expert's confidence predicts actual success"""
        # In real implementation, this would analyze historical confidence vs accuracy
        # For now, simulate based on expert personality traits
        
        personality_traits = getattr(expert, 'personality_traits', {})
        confidence_trait = personality_traits.get('confidence_level', 0.5)
        
        # Better calibration for experts who are naturally confident but not overconfident
        if 0.6 <= confidence_trait <= 0.8:
            calibration = 0.8 + np.random.normal(0, 0.1)
        elif confidence_trait < 0.4:
            calibration = 0.6 + np.random.normal(0, 0.1)  # Under-confident
        else:
            calibration = 0.5 + np.random.normal(0, 0.1)  # Over-confident
        
        return max(0, min(1, calibration))
    
    def _calculate_specialization_strength(self, expert: Any) -> float:
        """Calculate strength in specialized areas"""
        # Get expert specializations
        if hasattr(expert, 'get_specializations'):
            specializations = expert.get_specializations()
        else:
            specializations = getattr(expert, 'specializations', [])
        
        if not specializations:
            return 0.5
        
        # Calculate average performance in specialized categories
        category_accuracies = self._get_category_accuracies(expert)
        
        specialized_accuracies = []
        for spec in specializations:
            # Map specializations to categories (simplified)
            related_categories = self._map_specialization_to_categories(spec)
            for category in related_categories:
                if category in category_accuracies:
                    specialized_accuracies.append(category_accuracies[category])
        
        if not specialized_accuracies:
            return 0.5
        
        # Return above-average performance in specializations
        avg_specialization_accuracy = np.mean(specialized_accuracies)
        overall_accuracy = self._calculate_overall_accuracy(expert)
        
        # Specialization strength = how much better than overall average
        specialization_boost = avg_specialization_accuracy - overall_accuracy
        return max(0, min(1, 0.5 + specialization_boost))
    
    def _get_category_accuracies(self, expert: Any) -> Dict[str, float]:
        """Get accuracy by prediction category"""
        # Check if expert has stored category accuracies
        if hasattr(expert, 'category_accuracies') and expert.category_accuracies:
            return expert.category_accuracies
        
        # In real implementation, this would query the database
        # For now, simulate based on expert characteristics
        categories = [
            'winner_prediction', 'spread_prediction', 'total_prediction',
            'player_props', 'weather_impact', 'injury_impact'
        ]
        
        base_accuracy = self._calculate_overall_accuracy(expert)
        accuracies = {}
        
        for category in categories:
            # Add category-specific variance based on expert specialization
            variance = np.random.normal(0, 0.1)  # ±10% variance
            category_accuracy = max(0, min(1, base_accuracy + variance))
            accuracies[category] = category_accuracy
        
        return accuracies
    
    def _map_specialization_to_categories(self, specialization: str) -> List[str]:
        """Map expert specialization to prediction categories"""
        mapping = {
            'weather_impact': ['weather_impact', 'outdoor_games'],
            'injury_analysis': ['injury_impact', 'player_availability'],
            'line_movement': ['spread_prediction', 'market_analysis'],
            'statistical_analysis': ['winner_prediction', 'total_prediction'],
            'upset_detection': ['underdog_picks', 'contrarian_plays'],
            'momentum_analysis': ['trend_analysis', 'streak_detection'],
            'player_props': ['player_props', 'individual_performance']
        }
        
        return mapping.get(specialization, ['general_prediction'])
    
    def _determine_trend(self, expert: Any) -> str:
        """Determine expert's performance trend"""
        # In real implementation, this would analyze recent performance history
        # For now, simulate based on current performance vs historical
        
        current_accuracy = self._calculate_overall_accuracy(expert)
        
        # Simple simulation
        if current_accuracy > 0.6:
            return np.random.choice(['improving', 'stable'], p=[0.7, 0.3])
        elif current_accuracy < 0.4:
            return np.random.choice(['declining', 'stable'], p=[0.7, 0.3])
        else:
            return np.random.choice(['improving', 'stable', 'declining'], p=[0.3, 0.4, 0.3])
    
    def _calculate_weighted_score(self, components: Dict[str, Any]) -> float:
        """Calculate weighted total score from components"""
        score = (
            components['overall_accuracy'] * self.weights.overall_accuracy +
            components['recent_performance'] * self.weights.recent_performance +
            components['consistency'] * self.weights.consistency +
            components['confidence_calibration'] * self.weights.confidence_calibration +
            components['specialization_strength'] * self.weights.specialization_strength
        )
        
        # Scale to 0-100 for leaderboard display
        return score * 100
    
    def _update_peak_ranks(self, rankings: List[Any]) -> None:
        """Update peak ranks for experts"""
        for metrics in rankings:
            # Peak rank is the best (lowest) rank ever achieved
            if hasattr(metrics, 'peak_rank') and metrics.current_rank < metrics.peak_rank:
                metrics.peak_rank = metrics.current_rank
    
    def _store_ranking_snapshot(self, rankings: List[Any]) -> None:
        """Store ranking snapshot for historical analysis"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'rankings': [
                {
                    'expert_id': r.expert_id,
                    'rank': r.current_rank,
                    'score': r.leaderboard_score,
                    'accuracy': r.overall_accuracy
                }
                for r in rankings
            ]
        }
        
        self.ranking_history.append(snapshot)
        
        # Keep only last 50 snapshots to prevent memory issues
        if len(self.ranking_history) > 50:
            self.ranking_history = self.ranking_history[-50:]
    
    def get_ranking_volatility(self) -> float:
        """Calculate ranking volatility (how much rankings change)"""
        if len(self.ranking_history) < 2:
            return 0.0
        
        # Calculate average rank change between snapshots
        total_changes = 0
        total_experts = 0
        
        for i in range(1, len(self.ranking_history)):
            prev_snapshot = self.ranking_history[i-1]
            curr_snapshot = self.ranking_history[i]
            
            # Create rank lookup for previous snapshot
            prev_ranks = {r['expert_id']: r['rank'] for r in prev_snapshot['rankings']}
            
            for curr_expert in curr_snapshot['rankings']:
                expert_id = curr_expert['expert_id']
                if expert_id in prev_ranks:
                    rank_change = abs(curr_expert['rank'] - prev_ranks[expert_id])
                    total_changes += rank_change
                    total_experts += 1
        
        if total_experts == 0:
            return 0.0
        
        average_rank_change = total_changes / total_experts
        return min(1.0, average_rank_change / 5.0)  # Normalize to 0-1 scale
    
    def get_top_movers(self, direction: str = 'up', limit: int = 3) -> List[Dict[str, Any]]:
        """Get experts with biggest rank movements"""
        if len(self.ranking_history) < 2:
            return []
        
        prev_snapshot = self.ranking_history[-2]
        curr_snapshot = self.ranking_history[-1]
        
        # Create rank lookup for previous snapshot
        prev_ranks = {r['expert_id']: r['rank'] for r in prev_snapshot['rankings']}
        
        movements = []
        for curr_expert in curr_snapshot['rankings']:
            expert_id = curr_expert['expert_id']
            if expert_id in prev_ranks:
                rank_change = prev_ranks[expert_id] - curr_expert['rank']  # Positive = moved up
                movements.append({
                    'expert_id': expert_id,
                    'current_rank': curr_expert['rank'],
                    'previous_rank': prev_ranks[expert_id],
                    'rank_change': rank_change
                })
        
        # Sort by rank change
        if direction == 'up':
            movements.sort(key=lambda x: x['rank_change'], reverse=True)
        else:
            movements.sort(key=lambda x: x['rank_change'])
        
        return movements[:limit]