"""
Accuracy Calculation Engine
Handles real-time accuracy calculations, ROI analysis, and performance metrics
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .models import (
    PredictionResult, PredictionMatch, PerformanceHistory, 
    AccuracySnapshot, AccuracyAlert
)
from ..database.models import Prediction
from ..database.connection import get_db

logger = logging.getLogger(__name__)

class AccuracyCalculationEngine:
    """Main engine for calculating prediction accuracy and performance metrics"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'high': Decimal('0.70'),
            'medium': Decimal('0.50'),
            'low': Decimal('0.30')
        }
        
        # Standard betting odds for ROI calculation
        self.standard_odds = {
            'game': Decimal('-110'),  # Standard -110 odds
            'ats': Decimal('-110'),
            'total': Decimal('-110'),
            'prop': Decimal('-120')   # Props typically have worse odds
        }
    
    def calculate_prediction_accuracy(self, prediction_id: str, result_id: str) -> Dict:
        """Calculate accuracy for a single prediction-result match"""
        with get_db() as db:
            try:
                # Get prediction and result
                prediction = db.query(Prediction).filter_by(id=prediction_id).first()
                result = db.query(PredictionResult).filter_by(id=result_id).first()
                
                if not prediction or not result:
                    raise ValueError("Prediction or result not found")
                
                # Calculate accuracy based on prediction type
                is_correct, prediction_value, actual_value = self._evaluate_prediction(
                    prediction, result
                )
                
                # Calculate ROI
                roi_data = self._calculate_roi(prediction, result, is_correct)
                
                # Create or update prediction match
                match = db.query(PredictionMatch).filter_by(
                    prediction_id=prediction_id,
                    result_id=result_id
                ).first()
                
                if not match:
                    match = PredictionMatch(
                        prediction_id=prediction_id,
                        result_id=result_id
                    )
                    db.add(match)
                
                # Update match data
                match.is_correct = is_correct
                match.confidence_score = prediction.confidence
                match.prediction_value = prediction_value
                match.actual_value = actual_value
                match.theoretical_payout = roi_data['payout']
                match.roi_percentage = roi_data['roi_percentage']
                match.accuracy_calculated_at = datetime.utcnow()
                
                db.commit()
                
                return {
                    'success': True,
                    'is_correct': is_correct,
                    'confidence': float(prediction.confidence) if prediction.confidence else 0,
                    'roi_percentage': float(roi_data['roi_percentage']),
                    'prediction_value': prediction_value,
                    'actual_value': actual_value
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error calculating prediction accuracy: {e}")
                return {'success': False, 'error': str(e)}
    
    def _evaluate_prediction(self, prediction: Prediction, result: PredictionResult) -> Tuple[bool, str, str]:
        """Evaluate if a prediction was correct based on type"""
        prediction_data = prediction.prediction_data
        prediction_type = prediction.prediction_type
        
        if prediction_type == 'game':
            # Straight up winner prediction
            predicted_winner = prediction_data.get('predicted_winner')
            actual_winner = result.winner
            return predicted_winner == actual_winner, predicted_winner, actual_winner
            
        elif prediction_type == 'ats':
            # Against the spread prediction
            predicted_ats = prediction_data.get('ats_prediction')  # 'home', 'away'
            actual_ats = result.ats_winner
            return predicted_ats == actual_ats, predicted_ats, actual_ats
            
        elif prediction_type == 'total':
            # Over/under prediction
            predicted_total = prediction_data.get('total_prediction')  # 'over', 'under'
            actual_total = result.total_result
            return predicted_total == actual_total, predicted_total, actual_total
            
        elif prediction_type == 'prop':
            # Player prop prediction
            predicted_outcome = prediction_data.get('predicted_outcome')
            # For props, we'd need to match against specific prop results
            # This would require more complex matching logic
            return False, str(predicted_outcome), "N/A"
        
        return False, "Unknown", "Unknown"
    
    def _calculate_roi(self, prediction: Prediction, result: PredictionResult, is_correct: bool) -> Dict:
        """Calculate theoretical ROI for a prediction"""
        bet_amount = Decimal('100.00')  # Standard $100 bet
        odds = self.standard_odds.get(prediction.prediction_type, Decimal('-110'))
        
        if is_correct:
            if odds > 0:
                # Positive odds (underdog)
                payout = bet_amount + (bet_amount * odds / 100)
            else:
                # Negative odds (favorite)
                payout = bet_amount + (bet_amount * 100 / abs(odds))
        else:
            payout = Decimal('0.00')
        
        roi_percentage = ((payout - bet_amount) / bet_amount) * 100
        
        return {
            'payout': payout,
            'roi_percentage': roi_percentage,
            'bet_amount': bet_amount
        }
    
    def calculate_period_accuracy(self, period_type: str, start_date: datetime, 
                                end_date: datetime, prediction_type: str = None) -> Dict:
        """Calculate accuracy metrics for a specific time period"""
        with get_db() as db:
            try:
                # Build query for predictions in period
                query = db.query(PredictionMatch).join(Prediction).filter(
                    and_(
                        Prediction.created_at >= start_date,
                        Prediction.created_at <= end_date,
                        PredictionMatch.is_correct.isnot(None)
                    )
                )
                
                if prediction_type:
                    query = query.filter(Prediction.prediction_type == prediction_type)
                
                matches = query.all()
                
                if not matches:
                    return {
                        'total_predictions': 0,
                        'correct_predictions': 0,
                        'accuracy_percentage': 0.0,
                        'confidence_weighted_accuracy': 0.0,
                        'roi_percentage': 0.0
                    }
                
                # Calculate basic metrics
                total_predictions = len(matches)
                correct_predictions = sum(1 for m in matches if m.is_correct)
                accuracy_percentage = (correct_predictions / total_predictions) * 100
                
                # Calculate confidence-weighted accuracy
                total_confidence = sum(float(m.confidence_score or 0) for m in matches)
                weighted_correct = sum(
                    float(m.confidence_score or 0) for m in matches if m.is_correct
                )
                confidence_weighted_accuracy = (
                    (weighted_correct / total_confidence) * 100 if total_confidence > 0 else 0
                )
                
                # Calculate ROI
                total_roi = sum(float(m.roi_percentage or 0) for m in matches)
                avg_roi = total_roi / total_predictions if total_predictions > 0 else 0
                
                # Calculate confidence breakdowns
                confidence_breakdown = self._calculate_confidence_breakdown(matches)
                
                # Calculate streaks
                streak_data = self._calculate_streaks(matches)
                
                return {
                    'total_predictions': total_predictions,
                    'correct_predictions': correct_predictions,
                    'accuracy_percentage': round(accuracy_percentage, 2),
                    'confidence_weighted_accuracy': round(confidence_weighted_accuracy, 2),
                    'roi_percentage': round(avg_roi, 3),
                    'confidence_breakdown': confidence_breakdown,
                    'streak_data': streak_data,
                    'period_type': period_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error calculating period accuracy: {e}")
                return {'error': str(e)}
    
    def _calculate_confidence_breakdown(self, matches: List[PredictionMatch]) -> Dict:
        """Calculate accuracy breakdown by confidence levels"""
        breakdown = {
            'high_confidence': {'total': 0, 'correct': 0, 'accuracy': 0.0},
            'medium_confidence': {'total': 0, 'correct': 0, 'accuracy': 0.0},
            'low_confidence': {'total': 0, 'correct': 0, 'accuracy': 0.0}
        }
        
        for match in matches:
            confidence = match.confidence_score or Decimal('0')
            
            if confidence >= self.confidence_thresholds['high']:
                category = 'high_confidence'
            elif confidence >= self.confidence_thresholds['medium']:
                category = 'medium_confidence'
            else:
                category = 'low_confidence'
            
            breakdown[category]['total'] += 1
            if match.is_correct:
                breakdown[category]['correct'] += 1
        
        # Calculate accuracy percentages
        for category in breakdown:
            total = breakdown[category]['total']
            if total > 0:
                accuracy = (breakdown[category]['correct'] / total) * 100
                breakdown[category]['accuracy'] = round(accuracy, 2)
        
        return breakdown
    
    def _calculate_streaks(self, matches: List[PredictionMatch]) -> Dict:
        """Calculate win/loss streaks"""
        if not matches:
            return {
                'current_streak': 0,
                'longest_win_streak': 0,
                'longest_loss_streak': 0
            }
        
        # Sort matches by date (most recent first)
        sorted_matches = sorted(matches, key=lambda m: m.matched_at, reverse=True)
        
        current_streak = 0
        longest_win_streak = 0
        longest_loss_streak = 0
        
        # Calculate current streak
        for match in sorted_matches:
            if match.is_correct:
                if current_streak >= 0:
                    current_streak += 1
                else:
                    break
            else:
                if current_streak <= 0:
                    current_streak -= 1
                else:
                    break
        
        # Calculate longest streaks
        win_streak = 0
        loss_streak = 0
        
        for match in reversed(sorted_matches):  # Chronological order
            if match.is_correct:
                win_streak += 1
                loss_streak = 0
                longest_win_streak = max(longest_win_streak, win_streak)
            else:
                loss_streak += 1
                win_streak = 0
                longest_loss_streak = max(longest_loss_streak, loss_streak)
        
        return {
            'current_streak': current_streak,
            'longest_win_streak': longest_win_streak,
            'longest_loss_streak': longest_loss_streak
        } 
   def update_performance_history(self, period_type: str, season: int, week: int = None) -> Dict:
        """Update performance history for a specific period"""
        with get_db() as db:
            try:
                # Calculate period dates
                if period_type == 'weekly':
                    start_date, end_date = self._get_week_dates(season, week)
                elif period_type == 'monthly':
                    start_date, end_date = self._get_month_dates(season, week)
                elif period_type == 'season':
                    start_date, end_date = self._get_season_dates(season)
                else:
                    raise ValueError(f"Invalid period type: {period_type}")
                
                # Calculate accuracy for each prediction type
                prediction_types = ['game', 'ats', 'total', 'prop']
                
                for pred_type in prediction_types:
                    accuracy_data = self.calculate_period_accuracy(
                        period_type, start_date, end_date, pred_type
                    )
                    
                    if 'error' in accuracy_data:
                        continue
                    
                    # Create or update performance history record
                    history = db.query(PerformanceHistory).filter_by(
                        period_type=period_type,
                        period_start=start_date,
                        prediction_type=pred_type
                    ).first()
                    
                    if not history:
                        history = PerformanceHistory(
                            period_type=period_type,
                            period_start=start_date,
                            period_end=end_date,
                            week=week,
                            season=season,
                            prediction_type=pred_type
                        )
                        db.add(history)
                    
                    # Update metrics
                    history.total_predictions = accuracy_data['total_predictions']
                    history.correct_predictions = accuracy_data['correct_predictions']
                    history.accuracy_percentage = Decimal(str(accuracy_data['accuracy_percentage']))
                    history.confidence_weighted_accuracy = Decimal(str(accuracy_data['confidence_weighted_accuracy']))
                    history.roi_percentage = Decimal(str(accuracy_data['roi_percentage']))
                    
                    # Update confidence breakdowns
                    breakdown = accuracy_data['confidence_breakdown']
                    history.high_confidence_accuracy = Decimal(str(breakdown['high_confidence']['accuracy']))
                    history.medium_confidence_accuracy = Decimal(str(breakdown['medium_confidence']['accuracy']))
                    history.low_confidence_accuracy = Decimal(str(breakdown['low_confidence']['accuracy']))
                    
                    # Update streak data
                    streak_data = accuracy_data['streak_data']
                    history.current_streak = streak_data['current_streak']
                    history.longest_win_streak = streak_data['longest_win_streak']
                    history.longest_loss_streak = streak_data['longest_loss_streak']
                    
                    # Calculate trend
                    trend_data = self._calculate_trend(db, pred_type, period_type, season, week)
                    history.trend_direction = trend_data['direction']
                    history.momentum_score = Decimal(str(trend_data['momentum']))
                
                db.commit()
                
                return {
                    'success': True,
                    'period_type': period_type,
                    'season': season,
                    'week': week,
                    'updated_types': prediction_types
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating performance history: {e}")
                return {'success': False, 'error': str(e)}
    
    def create_accuracy_snapshot(self, snapshot_type: str = 'live') -> Dict:
        """Create a real-time accuracy snapshot for dashboard display"""
        with get_db() as db:
            try:
                current_time = datetime.utcnow()
                
                # Calculate overall accuracy (last 30 days)
                thirty_days_ago = current_time - timedelta(days=30)
                overall_data = self.calculate_period_accuracy(
                    'monthly', thirty_days_ago, current_time
                )
                
                # Calculate accuracy by prediction type
                type_accuracies = {}
                for pred_type in ['game', 'ats', 'total', 'prop']:
                    type_data = self.calculate_period_accuracy(
                        'monthly', thirty_days_ago, current_time, pred_type
                    )
                    type_accuracies[pred_type] = type_data.get('accuracy_percentage', 0)
                
                # Calculate recent performance (last 10 predictions)
                recent_data = self._get_recent_performance(db, 10)
                
                # Create snapshot
                snapshot = AccuracySnapshot(
                    snapshot_type=snapshot_type,
                    snapshot_date=current_time,
                    overall_accuracy=Decimal(str(overall_data.get('accuracy_percentage', 0))),
                    total_predictions=overall_data.get('total_predictions', 0),
                    correct_predictions=overall_data.get('correct_predictions', 0),
                    game_accuracy=Decimal(str(type_accuracies['game'])),
                    ats_accuracy=Decimal(str(type_accuracies['ats'])),
                    total_accuracy=Decimal(str(type_accuracies['total'])),
                    prop_accuracy=Decimal(str(type_accuracies['prop'])),
                    confidence_weighted_overall=Decimal(str(overall_data.get('confidence_weighted_accuracy', 0))),
                    theoretical_roi=Decimal(str(overall_data.get('roi_percentage', 0))),
                    recent_accuracy=Decimal(str(recent_data.get('accuracy', 0))),
                    recent_streak=recent_data.get('streak', 0)
                )
                
                db.add(snapshot)
                db.commit()
                
                return {
                    'success': True,
                    'snapshot_id': str(snapshot.id),
                    'snapshot_data': {
                        'overall_accuracy': float(snapshot.overall_accuracy),
                        'total_predictions': snapshot.total_predictions,
                        'type_breakdown': type_accuracies,
                        'recent_performance': recent_data,
                        'roi': float(snapshot.theoretical_roi)
                    }
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error creating accuracy snapshot: {e}")
                return {'success': False, 'error': str(e)}
    
    def _get_recent_performance(self, db: Session, limit: int = 10) -> Dict:
        """Get performance for most recent predictions"""
        recent_matches = db.query(PredictionMatch).join(Prediction).order_by(
            desc(Prediction.created_at)
        ).limit(limit).all()
        
        if not recent_matches:
            return {'accuracy': 0, 'streak': 0, 'total': 0}
        
        correct = sum(1 for m in recent_matches if m.is_correct)
        total = len(recent_matches)
        accuracy = (correct / total) * 100 if total > 0 else 0
        
        # Calculate current streak from recent matches
        streak = 0
        for match in recent_matches:
            if match.is_correct:
                if streak >= 0:
                    streak += 1
                else:
                    break
            else:
                if streak <= 0:
                    streak -= 1
                else:
                    break
        
        return {
            'accuracy': round(accuracy, 2),
            'streak': streak,
            'total': total,
            'correct': correct
        }
    
    def _calculate_trend(self, db: Session, prediction_type: str, period_type: str, 
                        season: int, week: int = None) -> Dict:
        """Calculate trend direction and momentum"""
        try:
            # Get last 5 periods of the same type
            query = db.query(PerformanceHistory).filter_by(
                prediction_type=prediction_type,
                period_type=period_type,
                season=season
            ).order_by(desc(PerformanceHistory.period_start)).limit(5)
            
            if week:
                query = query.filter(PerformanceHistory.week <= week)
            
            recent_periods = query.all()
            
            if len(recent_periods) < 2:
                return {'direction': 'stable', 'momentum': 0.0}
            
            # Calculate trend based on accuracy changes
            accuracies = [float(p.accuracy_percentage) for p in reversed(recent_periods)]
            
            # Simple linear trend calculation
            n = len(accuracies)
            x_sum = sum(range(n))
            y_sum = sum(accuracies)
            xy_sum = sum(i * accuracies[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            # Determine direction and momentum
            if slope > 1:
                direction = 'improving'
                momentum = min(100, slope * 10)
            elif slope < -1:
                direction = 'declining'
                momentum = max(-100, slope * 10)
            else:
                direction = 'stable'
                momentum = slope * 10
            
            return {
                'direction': direction,
                'momentum': round(momentum, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {'direction': 'stable', 'momentum': 0.0}
    
    def _get_week_dates(self, season: int, week: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a specific week"""
        # NFL season typically starts first Thursday in September
        # This is a simplified calculation - in production you'd use actual NFL schedule
        season_start = datetime(season, 9, 1)
        week_start = season_start + timedelta(weeks=week-1)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    def _get_month_dates(self, season: int, month: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a specific month"""
        start_date = datetime(season, month, 1)
        if month == 12:
            end_date = datetime(season + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(season, month + 1, 1) - timedelta(days=1)
        return start_date, end_date
    
    def _get_season_dates(self, season: int) -> Tuple[datetime, datetime]:
        """Get start and end dates for a season"""
        start_date = datetime(season, 9, 1)
        end_date = datetime(season + 1, 2, 28)  # End of Super Bowl
        return start_date, end_date

# Global accuracy calculation engine instance
accuracy_engine = AccuracyCalculationEngine()