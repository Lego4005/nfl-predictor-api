"""
Performance Decline Detector
Detects performance degradation in expert models with configurable thresholds
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)

class DeclineType(Enum):
    """Types of performance decline"""
    ACCURACY_DROP = "accuracy_drop"
    CONSISTENCY_LOSS = "consistency_loss"
    CONFIDENCE_MISCALIBRATION = "confidence_miscalibration"
    TREND_REVERSAL = "trend_reversal"
    CATEGORY_DEGRADATION = "category_degradation"

class DeclineSeverity(Enum):
    """Severity levels of decline"""
    CRITICAL = "critical"
    SEVERE = "severe"
    MODERATE = "moderate"
    MILD = "mild"

@dataclass
class DeclineThresholds:
    """Configurable thresholds for decline detection"""
    # Accuracy thresholds
    accuracy_drop_critical: float = 0.15  # 15% drop triggers critical
    accuracy_drop_severe: float = 0.10    # 10% drop triggers severe
    accuracy_drop_moderate: float = 0.05  # 5% drop triggers moderate
    
    # Consistency thresholds
    consistency_loss_critical: float = 0.20
    consistency_loss_severe: float = 0.15
    consistency_loss_moderate: float = 0.10
    
    # Calibration thresholds
    calibration_loss_critical: float = 0.25
    calibration_loss_severe: float = 0.15
    calibration_loss_moderate: float = 0.10
    
    # Time windows
    short_term_window_days: int = 7
    medium_term_window_days: int = 21
    long_term_window_days: int = 60
    
    # Minimum predictions for analysis
    min_predictions_short: int = 5
    min_predictions_medium: int = 15
    min_predictions_long: int = 30

@dataclass
class DeclineAlert:
    """Performance decline alert"""
    expert_id: str
    decline_type: DeclineType
    severity: DeclineSeverity
    current_value: float
    baseline_value: float
    change_magnitude: float
    confidence_score: float
    time_window: str
    category: Optional[str]
    detected_at: datetime
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expert_id': self.expert_id,
            'decline_type': self.decline_type.value,
            'severity': self.severity.value,
            'current_value': self.current_value,
            'baseline_value': self.baseline_value,
            'change_magnitude': self.change_magnitude,
            'confidence_score': self.confidence_score,
            'time_window': self.time_window,
            'category': self.category,
            'detected_at': self.detected_at.isoformat(),
            'recommendations': self.recommendations
        }

class PerformanceDeclineDetector:
    """Detects and classifies performance decline in expert models"""
    
    def __init__(self, accuracy_tracker=None, trend_analyzer=None):
        self.accuracy_tracker = accuracy_tracker
        self.trend_analyzer = trend_analyzer
        self.thresholds = DeclineThresholds()
        
        # Active alerts
        self.active_alerts: Dict[str, List[DeclineAlert]] = {}
        
        # Detection history
        self.detection_history: List[DeclineAlert] = []
    
    async def check_expert_performance(self, expert_id: str) -> List[DeclineAlert]:
        """Comprehensive performance decline check for an expert"""
        try:
            alerts = []
            
            # Check accuracy decline
            accuracy_alerts = await self._check_accuracy_decline(expert_id)
            alerts.extend(accuracy_alerts)
            
            # Check consistency loss
            consistency_alerts = await self._check_consistency_decline(expert_id)
            alerts.extend(consistency_alerts)
            
            # Check calibration issues
            calibration_alerts = await self._check_calibration_decline(expert_id)
            alerts.extend(calibration_alerts)
            
            # Check trend reversals
            trend_alerts = await self._check_trend_reversals(expert_id)
            alerts.extend(trend_alerts)
            
            # Check category-specific decline
            category_alerts = await self._check_category_decline(expert_id)
            alerts.extend(category_alerts)
            
            # Update active alerts
            self.active_alerts[expert_id] = alerts
            self.detection_history.extend(alerts)
            
            if alerts:
                logger.warning(f"Detected {len(alerts)} performance issues for {expert_id}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check expert performance: {e}")
            return []
    
    async def _check_accuracy_decline(self, expert_id: str) -> List[DeclineAlert]:
        """Check for accuracy decline across time windows"""
        alerts = []
        
        try:
            if not self.accuracy_tracker:
                return alerts
            
            profile = await self.accuracy_tracker.get_expert_accuracy_profile(expert_id)
            if not profile:
                return alerts
            
            # Check different time windows
            for window_name, window_days, min_preds in [
                ("short_term", self.thresholds.short_term_window_days, self.thresholds.min_predictions_short),
                ("medium_term", self.thresholds.medium_term_window_days, self.thresholds.min_predictions_medium),
                ("long_term", self.thresholds.long_term_window_days, self.thresholds.min_predictions_long)
            ]:
                recent_accuracy = self._calculate_recent_accuracy(expert_id, window_days)
                baseline_accuracy = profile.overall_accuracy
                
                if recent_accuracy is not None and baseline_accuracy > 0:
                    accuracy_drop = baseline_accuracy - recent_accuracy
                    
                    severity = self._classify_accuracy_severity(accuracy_drop)
                    if severity:
                        alert = DeclineAlert(
                            expert_id=expert_id,
                            decline_type=DeclineType.ACCURACY_DROP,
                            severity=severity,
                            current_value=recent_accuracy,
                            baseline_value=baseline_accuracy,
                            change_magnitude=accuracy_drop,
                            confidence_score=self._calculate_confidence(window_days, min_preds),
                            time_window=window_name,
                            category=None,
                            detected_at=datetime.now(),
                            recommendations=self._generate_accuracy_recommendations(accuracy_drop, severity)
                        )
                        alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check accuracy decline: {e}")
            return []
    
    def _calculate_recent_accuracy(self, expert_id: str, window_days: int) -> Optional[float]:
        """Calculate accuracy for recent time window"""
        try:
            if not self.accuracy_tracker:
                return None
            
            outcomes = self.accuracy_tracker.prediction_outcomes.get(expert_id, [])
            cutoff_date = datetime.now() - timedelta(days=window_days)
            
            recent_outcomes = [o for o in outcomes if o.prediction_timestamp >= cutoff_date]
            
            if len(recent_outcomes) < self.thresholds.min_predictions_short:
                return None
            
            correct_count = sum(1 for o in recent_outcomes if o.is_correct)
            return correct_count / len(recent_outcomes)
            
        except Exception as e:
            logger.error(f"Failed to calculate recent accuracy: {e}")
            return None
    
    def _classify_accuracy_severity(self, accuracy_drop: float) -> Optional[DeclineSeverity]:
        """Classify severity of accuracy decline"""
        if accuracy_drop >= self.thresholds.accuracy_drop_critical:
            return DeclineSeverity.CRITICAL
        elif accuracy_drop >= self.thresholds.accuracy_drop_severe:
            return DeclineSeverity.SEVERE
        elif accuracy_drop >= self.thresholds.accuracy_drop_moderate:
            return DeclineSeverity.MODERATE
        else:
            return None
    
    async def _check_consistency_decline(self, expert_id: str) -> List[DeclineAlert]:
        """Check for consistency decline"""
        # Implementation for consistency checking
        return []
    
    async def _check_calibration_decline(self, expert_id: str) -> List[DeclineAlert]:
        """Check for confidence calibration decline"""
        # Implementation for calibration checking
        return []
    
    async def _check_trend_reversals(self, expert_id: str) -> List[DeclineAlert]:
        """Check for trend reversals"""
        # Implementation for trend reversal detection
        return []
    
    async def _check_category_decline(self, expert_id: str) -> List[DeclineAlert]:
        """Check for category-specific decline"""
        # Implementation for category-specific decline
        return []
    
    def _calculate_confidence(self, window_days: int, min_predictions: int) -> float:
        """Calculate confidence in decline detection"""
        # Simple confidence calculation based on data availability
        base_confidence = min(1.0, window_days / 30.0)
        return max(0.1, base_confidence)
    
    def _generate_accuracy_recommendations(self, drop: float, severity: DeclineSeverity) -> List[str]:
        """Generate recommendations for accuracy decline"""
        recommendations = []
        
        if severity == DeclineSeverity.CRITICAL:
            recommendations.extend([
                "Immediate algorithm review required",
                "Consider temporary exclusion from AI Council",
                "Implement emergency parameter reset"
            ])
        elif severity == DeclineSeverity.SEVERE:
            recommendations.extend([
                "Algorithm parameter tuning needed",
                "Review recent prediction patterns",
                "Consider training data refresh"
            ])
        else:
            recommendations.extend([
                "Monitor performance closely",
                "Minor parameter adjustments may help"
            ])
        
        return recommendations
    
    async def get_system_health_report(self) -> Dict[str, Any]:
        """Get overall system health report"""
        try:
            total_experts = len(self.active_alerts)
            experts_with_issues = len([a for a in self.active_alerts.values() if a])
            
            # Count by severity
            severity_counts = {}
            for severity in DeclineSeverity:
                severity_counts[severity.value] = sum(
                    1 for alerts in self.active_alerts.values()
                    for alert in alerts
                    if alert.severity == severity
                )
            
            return {
                'total_experts_monitored': total_experts,
                'experts_with_performance_issues': experts_with_issues,
                'system_health_percentage': ((total_experts - experts_with_issues) / max(1, total_experts)) * 100,
                'alerts_by_severity': severity_counts,
                'total_active_alerts': sum(len(alerts) for alerts in self.active_alerts.values()),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return {'error': str(e)}