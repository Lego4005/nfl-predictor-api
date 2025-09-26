"""
Performance Evaluator
Evaluates expert performance for competition rounds and overall tracking
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceEvaluator:
    """Evaluates expert performance across different metrics and time periods"""
    
    def __init__(self):
        self.evaluation_history: List[Dict[str, Any]] = []
        self.scoring_weights = {
            'accuracy': 0.4,        # 40% - Raw prediction accuracy
            'confidence': 0.25,     # 25% - Confidence calibration
            'difficulty': 0.2,      # 20% - Performance on difficult predictions
            'consistency': 0.15     # 15% - Consistency across categories
        }
    
    async def evaluate_round_performance(
        self,
        experts: Dict[str, Any],
        game_ids: List[str],
        game_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate expert performance for a specific competition round"""
        try:
            round_performances = {}
            
            for expert_id, expert in experts.items():
                try:
                    performance = await self._evaluate_expert_round(
                        expert, game_ids, game_results
                    )
                    round_performances[expert_id] = performance
                    
                except Exception as e:
                    logger.warning(f"Failed to evaluate round performance for expert {expert_id}: {e}")
                    # Create default performance
                    round_performances[expert_id] = self._create_default_performance(expert_id)
            
            # Store round evaluation
            self._store_round_evaluation(round_performances, game_ids)
            
            logger.info(f"📊 Evaluated round performance for {len(round_performances)} experts")
            return round_performances
            
        except Exception as e:
            logger.error(f"Failed to evaluate round performance: {e}")
            return {}
    
    async def _evaluate_expert_round(
        self,
        expert: Any,
        game_ids: List[str],
        game_results: Dict[str, Any]
    ) -> Any:
        """Evaluate single expert's performance for the round"""
        from .competition_framework import ExpertPerformanceMetrics
        
        # Get expert predictions for these games (mock for now)
        expert_predictions = await self._get_expert_predictions(expert, game_ids)
        
        # Calculate performance metrics
        accuracy_metrics = self._calculate_accuracy_metrics(expert_predictions, game_results)
        confidence_metrics = self._calculate_confidence_metrics(expert_predictions, game_results)
        difficulty_metrics = self._calculate_difficulty_performance(expert_predictions, game_results)
        consistency_metrics = self._calculate_round_consistency(expert_predictions)
        
        # Calculate weighted round score
        round_score = (
            accuracy_metrics['overall_accuracy'] * self.scoring_weights['accuracy'] +
            confidence_metrics['calibration_score'] * self.scoring_weights['confidence'] +
            difficulty_metrics['difficulty_score'] * self.scoring_weights['difficulty'] +
            consistency_metrics['consistency_score'] * self.scoring_weights['consistency']
        )
        
        # Update expert's cumulative performance
        await self._update_expert_cumulative_performance(expert, accuracy_metrics, confidence_metrics)
        
        # Create performance metrics object
        performance_metrics = ExpertPerformanceMetrics(
            expert_id=expert.expert_id,
            overall_accuracy=accuracy_metrics['overall_accuracy'],
            category_accuracies=accuracy_metrics['category_accuracies'],
            confidence_calibration=confidence_metrics['calibration_score'],
            recent_trend=self._determine_recent_trend(expert, round_score),
            total_predictions=getattr(expert, 'total_predictions', 0) + len(game_ids),
            correct_predictions=getattr(expert, 'correct_predictions', 0) + accuracy_metrics['correct_count'],
            leaderboard_score=round_score * 100,  # Scale to 0-100
            current_rank=getattr(expert, 'current_rank', 999),
            peak_rank=getattr(expert, 'peak_rank', 999),
            consistency_score=consistency_metrics['consistency_score'],
            specialization_strength=self._calculate_specialization_performance(expert, accuracy_metrics),
            last_updated=datetime.now()
        )
        
        return performance_metrics
    
    async def _get_expert_predictions(self, expert: Any, game_ids: List[str]) -> List[Dict[str, Any]]:
        """Get expert's predictions for specified games"""
        # In real implementation, this would query the database
        # For now, generate mock predictions
        
        predictions = []
        for game_id in game_ids:
            # Generate mock prediction using expert's make_prediction method
            try:
                if hasattr(expert, 'make_prediction'):
                    mock_game_data = {'game_id': game_id, 'spread': -3.5, 'total': 45.5}
                    prediction = expert.make_prediction(mock_game_data)
                    prediction['game_id'] = game_id
                    predictions.append(prediction)
                else:
                    # Create basic mock prediction
                    predictions.append({
                        'game_id': game_id,
                        'expert_id': expert.expert_id,
                        'prediction': {
                            'winner_prediction': np.random.choice(['home', 'away']),
                            'confidence_overall': np.random.uniform(0.5, 0.9),
                            'spread_prediction': np.random.uniform(-10, 10),
                            'total_prediction': np.random.uniform(35, 55)
                        }
                    })
            except Exception as e:
                logger.warning(f"Failed to generate prediction for expert {expert.expert_id}: {e}")
                # Create fallback prediction
                predictions.append({
                    'game_id': game_id,
                    'expert_id': expert.expert_id,
                    'prediction': {
                        'winner_prediction': 'home',
                        'confidence_overall': 0.5,
                        'spread_prediction': 0,
                        'total_prediction': 45
                    }
                })
        
        return predictions
    
    def _calculate_accuracy_metrics(
        self, 
        predictions: List[Dict[str, Any]], 
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate accuracy metrics for predictions"""
        if not predictions:
            return {
                'overall_accuracy': 0.5,
                'correct_count': 0,
                'total_count': 0,
                'category_accuracies': {}
            }
        
        correct_predictions = 0
        category_correct = {}
        category_total = {}
        
        for prediction in predictions:
            game_id = prediction['game_id']
            pred_data = prediction['prediction']
            
            # Get actual result (mock if not available)
            actual_result = results.get(game_id, self._generate_mock_result())
            
            # Evaluate winner prediction
            if 'winner_prediction' in pred_data:
                is_correct = pred_data['winner_prediction'] == actual_result.get('winner', 'home')
                if is_correct:
                    correct_predictions += 1
                    category_correct['winner'] = category_correct.get('winner', 0) + 1
                category_total['winner'] = category_total.get('winner', 0) + 1
            
            # Evaluate spread prediction
            if 'spread_prediction' in pred_data and 'actual_spread' in actual_result:
                spread_error = abs(pred_data['spread_prediction'] - actual_result['actual_spread'])
                is_correct = spread_error <= 3.0  # Within 3 points
                if is_correct:
                    category_correct['spread'] = category_correct.get('spread', 0) + 1
                category_total['spread'] = category_total.get('spread', 0) + 1
            
            # Evaluate total prediction
            if 'total_prediction' in pred_data and 'actual_total' in actual_result:
                total_error = abs(pred_data['total_prediction'] - actual_result['actual_total'])
                is_correct = total_error <= 6.0  # Within 6 points
                if is_correct:
                    category_correct['total'] = category_correct.get('total', 0) + 1
                category_total['total'] = category_total.get('total', 0) + 1
        
        # Calculate category accuracies
        category_accuracies = {}
        for category in category_total:
            if category_total[category] > 0:
                category_accuracies[category] = category_correct.get(category, 0) / category_total[category]
        
        overall_accuracy = correct_predictions / len(predictions) if predictions else 0.5
        
        return {
            'overall_accuracy': overall_accuracy,
            'correct_count': correct_predictions,
            'total_count': len(predictions),
            'category_accuracies': category_accuracies
        }
    
    def _calculate_confidence_metrics(
        self, 
        predictions: List[Dict[str, Any]], 
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate confidence calibration metrics"""
        if not predictions:
            return {
                'calibration_score': 0.5,
                'overconfidence': 0.0,
                'underconfidence': 0.0
            }
        
        confidence_accuracy_pairs = []
        
        for prediction in predictions:
            game_id = prediction['game_id']
            pred_data = prediction['prediction']
            
            confidence = pred_data.get('confidence_overall', 0.5)
            
            # Get actual result
            actual_result = results.get(game_id, self._generate_mock_result())
            
            # Check if prediction was correct
            was_correct = False
            if 'winner_prediction' in pred_data:
                was_correct = pred_data['winner_prediction'] == actual_result.get('winner', 'home')
            
            confidence_accuracy_pairs.append((confidence, 1.0 if was_correct else 0.0))
        
        if not confidence_accuracy_pairs:
            return {
                'calibration_score': 0.5,
                'overconfidence': 0.0,
                'underconfidence': 0.0
            }
        
        # Calculate calibration score (simplified)
        total_calibration_error = 0
        for confidence, accuracy in confidence_accuracy_pairs:
            calibration_error = abs(confidence - accuracy)
            total_calibration_error += calibration_error
        
        avg_calibration_error = total_calibration_error / len(confidence_accuracy_pairs)
        calibration_score = max(0.0, 1.0 - avg_calibration_error)
        
        # Calculate over/under confidence (simplified)
        avg_confidence = np.mean([pair[0] for pair in confidence_accuracy_pairs])
        avg_accuracy = np.mean([pair[1] for pair in confidence_accuracy_pairs])
        
        overconfidence = max(0.0, avg_confidence - avg_accuracy)
        underconfidence = max(0.0, avg_accuracy - avg_confidence)
        
        return {
            'calibration_score': calibration_score,
            'overconfidence': overconfidence,
            'underconfidence': underconfidence
        }
    
    def _calculate_difficulty_performance(
        self, 
        predictions: List[Dict[str, Any]], 
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance on difficult predictions"""
        # In real implementation, this would assess game difficulty
        # For now, simulate based on confidence levels
        
        if not predictions:
            return {'difficulty_score': 0.5}
        
        # Consider low-confidence predictions as "difficult"
        difficult_predictions = [p for p in predictions if p['prediction'].get('confidence_overall', 0.5) < 0.6]
        
        if not difficult_predictions:
            return {'difficulty_score': 0.6}  # Neutral score if no difficult predictions
        
        # Calculate accuracy on difficult predictions
        correct_difficult = 0
        for prediction in difficult_predictions:
            game_id = prediction['game_id']
            actual_result = results.get(game_id, self._generate_mock_result())
            
            if prediction['prediction'].get('winner_prediction') == actual_result.get('winner', 'home'):
                correct_difficult += 1
        
        difficulty_accuracy = correct_difficult / len(difficult_predictions)
        
        return {'difficulty_score': difficulty_accuracy}
    
    def _calculate_round_consistency(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consistency within the round"""
        if not predictions:
            return {'consistency_score': 0.5}
        
        # Calculate standard deviation of confidence levels
        confidences = [p['prediction'].get('confidence_overall', 0.5) for p in predictions]
        confidence_std = np.std(confidences) if len(confidences) > 1 else 0
        
        # Lower standard deviation = higher consistency
        consistency_score = max(0.0, 1.0 - confidence_std * 2)
        
        return {'consistency_score': consistency_score}
    
    def _calculate_specialization_performance(
        self, 
        expert: Any, 
        accuracy_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate performance in expert's specialization areas"""
        # Get expert specializations
        if hasattr(expert, 'get_specializations'):
            specializations = expert.get_specializations()
        else:
            specializations = getattr(expert, 'specializations', [])
        
        if not specializations:
            return {}
        
        # Map specializations to performance metrics
        specialization_performance = {}
        category_accuracies = accuracy_metrics.get('category_accuracies', {})
        
        for specialization in specializations:
            # Simple mapping for demo
            if 'weather' in specialization.lower():
                specialization_performance[specialization] = category_accuracies.get('weather', 0.5)
            elif 'spread' in specialization.lower():
                specialization_performance[specialization] = category_accuracies.get('spread', 0.5)
            elif 'total' in specialization.lower():
                specialization_performance[specialization] = category_accuracies.get('total', 0.5)
            else:
                specialization_performance[specialization] = accuracy_metrics.get('overall_accuracy', 0.5)
        
        return specialization_performance
    
    def _determine_recent_trend(self, expert: Any, round_score: float) -> str:
        """Determine expert's recent performance trend"""
        # Compare current round score to historical performance
        historical_avg = getattr(expert, 'leaderboard_score', 50) / 100  # Convert to 0-1 scale
        
        if round_score > historical_avg + 0.1:
            return 'improving'
        elif round_score < historical_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    async def _update_expert_cumulative_performance(
        self, 
        expert: Any, 
        accuracy_metrics: Dict[str, Any], 
        confidence_metrics: Dict[str, Any]
    ) -> None:
        """Update expert's cumulative performance metrics"""
        try:
            # Update total predictions and correct predictions
            if hasattr(expert, 'total_predictions'):
                expert.total_predictions += accuracy_metrics['total_count']
            else:
                expert.total_predictions = accuracy_metrics['total_count']
            
            if hasattr(expert, 'correct_predictions'):
                expert.correct_predictions += accuracy_metrics['correct_count']
            else:
                expert.correct_predictions = accuracy_metrics['correct_count']
            
            # Update overall accuracy
            if expert.total_predictions > 0:
                expert.overall_accuracy = expert.correct_predictions / expert.total_predictions
            
            # Update confidence calibration (exponential moving average)
            if hasattr(expert, 'confidence_calibration'):
                expert.confidence_calibration = (
                    0.8 * expert.confidence_calibration + 
                    0.2 * confidence_metrics['calibration_score']
                )
            else:
                expert.confidence_calibration = confidence_metrics['calibration_score']
            
            # Update category accuracies
            if not hasattr(expert, 'category_accuracies'):
                expert.category_accuracies = {}
            
            for category, accuracy in accuracy_metrics['category_accuracies'].items():
                if category in expert.category_accuracies:
                    # Exponential moving average
                    expert.category_accuracies[category] = (
                        0.7 * expert.category_accuracies[category] + 0.3 * accuracy
                    )
                else:
                    expert.category_accuracies[category] = accuracy
            
        except Exception as e:
            logger.warning(f"Failed to update cumulative performance for expert {expert.expert_id}: {e}")
    
    def _generate_mock_result(self) -> Dict[str, Any]:
        """Generate mock game result for testing"""
        home_score = np.random.randint(10, 35)
        away_score = np.random.randint(10, 35)
        
        return {
            'winner': 'home' if home_score > away_score else 'away',
            'home_score': home_score,
            'away_score': away_score,
            'actual_total': home_score + away_score,
            'actual_spread': home_score - away_score
        }
    
    def _create_default_performance(self, expert_id: str) -> Any:
        """Create default performance metrics for failed evaluations"""
        from .competition_framework import ExpertPerformanceMetrics
        
        return ExpertPerformanceMetrics(
            expert_id=expert_id,
            overall_accuracy=0.5,
            category_accuracies={},
            confidence_calibration=0.5,
            recent_trend='stable',
            total_predictions=0,
            correct_predictions=0,
            leaderboard_score=50.0,
            current_rank=999,
            peak_rank=999,
            consistency_score=0.5,
            specialization_strength={},
            last_updated=datetime.now()
        )
    
    def _store_round_evaluation(
        self, 
        round_performances: Dict[str, Any], 
        game_ids: List[str]
    ) -> None:
        """Store round evaluation in history"""
        evaluation_record = {
            'timestamp': datetime.now().isoformat(),
            'game_ids': game_ids,
            'expert_performances': {
                expert_id: {
                    'overall_accuracy': perf.overall_accuracy,
                    'leaderboard_score': perf.leaderboard_score,
                    'recent_trend': perf.recent_trend
                }
                for expert_id, perf in round_performances.items()
            },
            'round_statistics': self._calculate_round_statistics(round_performances)
        }
        
        self.evaluation_history.append(evaluation_record)
        
        # Keep only last 30 evaluations
        if len(self.evaluation_history) > 30:
            self.evaluation_history = self.evaluation_history[-30:]
    
    def _calculate_round_statistics(self, round_performances: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics for the round"""
        if not round_performances:
            return {}
        
        accuracies = [perf.overall_accuracy for perf in round_performances.values()]
        scores = [perf.leaderboard_score for perf in round_performances.values()]
        
        return {
            'average_accuracy': np.mean(accuracies),
            'accuracy_std': np.std(accuracies),
            'average_score': np.mean(scores),
            'score_std': np.std(scores),
            'best_performer': max(round_performances.items(), key=lambda x: x[1].leaderboard_score)[0],
            'worst_performer': min(round_performances.items(), key=lambda x: x[1].leaderboard_score)[0]
        }
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of evaluation history"""
        if not self.evaluation_history:
            return {'total_evaluations': 0}
        
        recent_evaluations = self.evaluation_history[-10:]  # Last 10 evaluations
        
        avg_accuracy_trend = []
        for eval_record in recent_evaluations:
            stats = eval_record.get('round_statistics', {})
            if 'average_accuracy' in stats:
                avg_accuracy_trend.append(stats['average_accuracy'])
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'recent_average_accuracy': np.mean(avg_accuracy_trend) if avg_accuracy_trend else 0.5,
            'accuracy_trend': 'improving' if len(avg_accuracy_trend) > 1 and avg_accuracy_trend[-1] > avg_accuracy_trend[0] else 'stable',
            'last_evaluation': self.evaluation_history[-1]['timestamp'] if self.evaluation_history else None
        }