"""
Trend Analyzer
Implements advanced performance trajectory detection and trend analysis for expert models
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np
from scipy import stats
import pandas as pd

logger = logging.getLogger(__name__)

class TrendDirection(Enum):
    """Trend direction classification"""
    STRONGLY_IMPROVING = "strongly_improving"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    STRONGLY_DECLINING = "strongly_declining"

class TrendConfidence(Enum):
    """Confidence level in trend detection"""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

@dataclass
class TrendPoint:
    """Single data point for trend analysis"""
    timestamp: datetime
    value: float
    weight: float = 1.0
    category: Optional[str] = None

@dataclass
class TrendAnalysis:
    """Complete trend analysis result"""
    expert_id: str
    category: Optional[str]
    direction: TrendDirection
    confidence: TrendConfidence
    slope: float
    r_squared: float
    p_value: float
    trend_strength: float  # 0.0 to 1.0
    data_points: int
    analysis_window_days: int
    momentum_score: float  # Recent acceleration/deceleration
    volatility: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/storage"""
        return {
            'expert_id': self.expert_id,
            'category': self.category,
            'direction': self.direction.value,
            'confidence': self.confidence.value,
            'slope': self.slope,
            'r_squared': self.r_squared,
            'p_value': self.p_value,
            'trend_strength': self.trend_strength,
            'data_points': self.data_points,
            'analysis_window_days': self.analysis_window_days,
            'momentum_score': self.momentum_score,
            'volatility': self.volatility,
            'last_updated': self.last_updated.isoformat()
        }

@dataclass
class PerformanceWindow:
    """Performance analysis for a specific time window"""
    start_date: datetime
    end_date: datetime
    accuracy: float
    predictions_count: int
    confidence_avg: float
    volatility: float

class TrendAnalyzer:
    """Advanced trend analysis for expert performance trajectories"""
    
    def __init__(self, accuracy_tracker=None):
        self.accuracy_tracker = accuracy_tracker
        
        # Configuration parameters
        self.min_data_points = 10  # Minimum predictions for reliable trend
        self.default_window_days = 30  # Default analysis window
        self.momentum_window_days = 7  # Window for momentum calculation
        self.significance_threshold = 0.05  # P-value threshold for statistical significance
        
        # Trend strength thresholds
        self.strong_trend_threshold = 0.15  # Absolute slope for strong trends
        self.weak_trend_threshold = 0.05   # Absolute slope for weak trends
        
        # Cached trend analyses
        self.trend_cache: Dict[str, Dict[str, TrendAnalysis]] = {}
        self.cache_expiry_hours = 6
    
    async def analyze_expert_trend(
        self,
        expert_id: str,
        category: Optional[str] = None,
        window_days: Optional[int] = None,
        force_refresh: bool = False
    ) -> Optional[TrendAnalysis]:
        """Analyze performance trend for an expert (overall or category-specific)"""
        try:
            window_days = window_days or self.default_window_days
            cache_key = f"{expert_id}_{category or 'overall'}_{window_days}"
            
            # Check cache unless force refresh
            if not force_refresh and self._is_cache_valid(cache_key):
                return self.trend_cache.get(expert_id, {}).get(cache_key)
            
            # Get performance data
            performance_data = await self._get_performance_data(expert_id, category, window_days)
            
            if len(performance_data) < self.min_data_points:
                logger.warning(f"Insufficient data for trend analysis: {len(performance_data)} points")
                return None
            
            # Perform trend analysis
            trend_analysis = self._calculate_trend_analysis(
                expert_id, category, performance_data, window_days
            )
            
            # Cache result
            if expert_id not in self.trend_cache:
                self.trend_cache[expert_id] = {}
            self.trend_cache[expert_id][cache_key] = trend_analysis
            
            logger.info(f"Analyzed trend for {expert_id}, category {category}: {trend_analysis.direction.value}")
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze expert trend: {e}")
            return None
    
    async def _get_performance_data(
        self,
        expert_id: str,
        category: Optional[str],
        window_days: int
    ) -> List[TrendPoint]:
        """Get performance data points for trend analysis"""
        try:
            performance_data = []
            
            if not self.accuracy_tracker:
                logger.warning("No accuracy tracker available, using mock data")
                return self._generate_mock_performance_data(window_days)
            
            # Get prediction outcomes from accuracy tracker
            outcomes = self.accuracy_tracker.prediction_outcomes.get(expert_id, [])
            
            # Filter by category if specified
            if category:
                outcomes = [o for o in outcomes if o.category == category]
            
            # Filter by time window
            cutoff_date = datetime.now() - timedelta(days=window_days)
            outcomes = [o for o in outcomes if o.prediction_timestamp >= cutoff_date]
            
            if not outcomes:
                return []
            
            # Sort by timestamp
            outcomes.sort(key=lambda x: x.prediction_timestamp)
            
            # Convert to trend points with rolling accuracy
            window_size = max(5, len(outcomes) // 10)  # Adaptive window size
            
            for i in range(window_size, len(outcomes)):
                window_outcomes = outcomes[i-window_size:i]
                accuracy = sum(1 for o in window_outcomes if o.is_correct) / len(window_outcomes)
                
                # Weight recent outcomes more heavily
                age_days = (datetime.now() - outcomes[i].prediction_timestamp).days
                weight = max(0.1, 1.0 - (age_days / window_days))
                
                performance_data.append(TrendPoint(
                    timestamp=outcomes[i].prediction_timestamp,
                    value=accuracy,
                    weight=weight,
                    category=category
                ))
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to get performance data: {e}")
            return []
    
    def _generate_mock_performance_data(self, window_days: int) -> List[TrendPoint]:
        """Generate mock performance data for testing"""
        try:
            import random
            
            data_points = []
            start_date = datetime.now() - timedelta(days=window_days)
            
            # Generate realistic performance trajectory
            base_accuracy = 0.55
            trend_slope = random.uniform(-0.001, 0.001)  # Small daily change
            noise_level = 0.05
            
            for i in range(window_days):
                date = start_date + timedelta(days=i)
                
                # Add trend and noise
                accuracy = base_accuracy + (trend_slope * i) + random.uniform(-noise_level, noise_level)
                accuracy = max(0.0, min(1.0, accuracy))  # Clamp to valid range
                
                weight = max(0.1, 1.0 - (i / window_days))  # Recent data weighted more
                
                data_points.append(TrendPoint(
                    timestamp=date,
                    value=accuracy,
                    weight=weight
                ))
            
            return data_points
            
        except Exception as e:
            logger.error(f"Failed to generate mock performance data: {e}")
            return []
    
    def _calculate_trend_analysis(
        self,
        expert_id: str,
        category: Optional[str],
        performance_data: List[TrendPoint],
        window_days: int
    ) -> TrendAnalysis:
        """Calculate comprehensive trend analysis"""
        try:
            # Convert to numpy arrays for analysis
            timestamps = np.array([p.timestamp.timestamp() for p in performance_data])
            values = np.array([p.value for p in performance_data])
            weights = np.array([p.weight for p in performance_data])
            
            # Normalize timestamps to days from start
            time_days = (timestamps - timestamps[0]) / (24 * 3600)
            
            # Weighted linear regression
            slope, r_squared, p_value = self._weighted_linear_regression(
                time_days, values, weights
            )
            
            # Determine trend direction and strength
            direction = self._classify_trend_direction(slope, r_squared)
            confidence = self._assess_trend_confidence(r_squared, p_value, len(performance_data))
            trend_strength = self._calculate_trend_strength(slope, r_squared)
            
            # Calculate momentum (recent acceleration/deceleration)
            momentum_score = self._calculate_momentum_score(performance_data)
            
            # Calculate volatility
            volatility = self._calculate_volatility(values, weights)
            
            return TrendAnalysis(
                expert_id=expert_id,
                category=category,
                direction=direction,
                confidence=confidence,
                slope=slope,
                r_squared=r_squared,
                p_value=p_value,
                trend_strength=trend_strength,
                data_points=len(performance_data),
                analysis_window_days=window_days,
                momentum_score=momentum_score,
                volatility=volatility,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate trend analysis: {e}")
            # Return default analysis
            return TrendAnalysis(
                expert_id=expert_id,
                category=category,
                direction=TrendDirection.STABLE,
                confidence=TrendConfidence.LOW,
                slope=0.0,
                r_squared=0.0,
                p_value=1.0,
                trend_strength=0.0,
                data_points=len(performance_data),
                analysis_window_days=window_days,
                momentum_score=0.0,
                volatility=0.0,
                last_updated=datetime.now()
            )
    
    def _weighted_linear_regression(
        self,
        x: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray
    ) -> Tuple[float, float, float]:
        """Perform weighted linear regression"""
        try:
            # Weighted least squares
            W = np.diag(weights)
            X = np.column_stack([np.ones(len(x)), x])
            
            # Calculate coefficients: β = (X^T W X)^(-1) X^T W y
            XTW = X.T @ W
            beta = np.linalg.inv(XTW @ X) @ XTW @ y
            
            slope = beta[1]
            
            # Calculate R-squared
            y_pred = X @ beta
            ss_res = np.sum(weights * (y - y_pred) ** 2)
            ss_tot = np.sum(weights * (y - np.average(y, weights=weights)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Calculate p-value (simplified approximation)
            n = len(x)
            if n > 2:
                t_stat = slope / (np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum(weights * (x - np.average(x, weights=weights)) ** 2)))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                p_value = 1.0
            
            return slope, max(0, r_squared), max(0, min(1, p_value))
            
        except Exception as e:
            logger.error(f"Failed to perform weighted linear regression: {e}")
            return 0.0, 0.0, 1.0
    
    def _classify_trend_direction(self, slope: float, r_squared: float) -> TrendDirection:
        """Classify trend direction based on slope and R-squared"""
        try:
            # Consider both slope magnitude and fit quality
            abs_slope = abs(slope)
            
            if r_squared < 0.1:  # Poor fit, likely stable
                return TrendDirection.STABLE
            
            if slope > 0:
                if abs_slope >= self.strong_trend_threshold:
                    return TrendDirection.STRONGLY_IMPROVING
                elif abs_slope >= self.weak_trend_threshold:
                    return TrendDirection.IMPROVING
                else:
                    return TrendDirection.STABLE
            elif slope < 0:
                if abs_slope >= self.strong_trend_threshold:
                    return TrendDirection.STRONGLY_DECLINING
                elif abs_slope >= self.weak_trend_threshold:
                    return TrendDirection.DECLINING
                else:
                    return TrendDirection.STABLE
            else:
                return TrendDirection.STABLE
                
        except Exception as e:
            logger.error(f"Failed to classify trend direction: {e}")
            return TrendDirection.STABLE
    
    def _assess_trend_confidence(self, r_squared: float, p_value: float, data_points: int) -> TrendConfidence:
        """Assess confidence in trend analysis"""
        try:
            # Consider fit quality, statistical significance, and sample size
            confidence_score = 0.0
            
            # R-squared contribution (0-0.4)
            confidence_score += min(0.4, r_squared * 0.4)
            
            # Statistical significance contribution (0-0.3)
            if p_value <= self.significance_threshold:
                confidence_score += 0.3 * (1 - p_value / self.significance_threshold)
            
            # Sample size contribution (0-0.3)
            sample_score = min(1.0, (data_points - self.min_data_points) / 20)
            confidence_score += 0.3 * sample_score
            
            if confidence_score >= 0.7:
                return TrendConfidence.HIGH
            elif confidence_score >= 0.4:
                return TrendConfidence.MODERATE
            else:
                return TrendConfidence.LOW
                
        except Exception as e:
            logger.error(f"Failed to assess trend confidence: {e}")
            return TrendConfidence.LOW
    
    def _calculate_trend_strength(self, slope: float, r_squared: float) -> float:
        """Calculate overall trend strength (0.0 to 1.0)"""
        try:
            # Combine slope magnitude and fit quality
            slope_strength = min(1.0, abs(slope) / self.strong_trend_threshold)
            fit_strength = r_squared
            
            # Weighted combination
            trend_strength = (slope_strength * 0.6) + (fit_strength * 0.4)
            
            return max(0.0, min(1.0, trend_strength))
            
        except Exception as e:
            logger.error(f"Failed to calculate trend strength: {e}")
            return 0.0
    
    def _calculate_momentum_score(self, performance_data: List[TrendPoint]) -> float:
        """Calculate momentum score (recent acceleration/deceleration)"""
        try:
            if len(performance_data) < 10:
                return 0.0
            
            # Split data into recent and earlier periods
            split_point = len(performance_data) // 2
            earlier_data = performance_data[:split_point]
            recent_data = performance_data[split_point:]
            
            # Calculate slopes for each period
            earlier_slope = self._calculate_period_slope(earlier_data)
            recent_slope = self._calculate_period_slope(recent_data)
            
            # Momentum is the difference in slopes
            momentum = recent_slope - earlier_slope
            
            # Normalize to -1 to 1 range
            return max(-1.0, min(1.0, momentum * 10))
            
        except Exception as e:
            logger.error(f"Failed to calculate momentum score: {e}")
            return 0.0
    
    def _calculate_period_slope(self, data: List[TrendPoint]) -> float:
        """Calculate slope for a specific period"""
        try:
            if len(data) < 2:
                return 0.0
            
            timestamps = np.array([p.timestamp.timestamp() for p in data])
            values = np.array([p.value for p in data])
            
            # Normalize timestamps
            time_days = (timestamps - timestamps[0]) / (24 * 3600)
            
            # Simple linear regression
            if len(set(time_days)) > 1:  # Avoid division by zero
                slope = np.polyfit(time_days, values, 1)[0]
                return slope
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate period slope: {e}")
            return 0.0
    
    def _calculate_volatility(self, values: np.ndarray, weights: np.ndarray) -> float:
        """Calculate weighted volatility of performance"""
        try:
            if len(values) < 2:
                return 0.0
            
            # Weighted standard deviation
            weighted_mean = np.average(values, weights=weights)
            weighted_variance = np.average((values - weighted_mean) ** 2, weights=weights)
            volatility = np.sqrt(weighted_variance)
            
            return min(1.0, volatility)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Failed to calculate volatility: {e}")
            return 0.0
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached trend analysis is still valid"""
        try:
            for expert_trends in self.trend_cache.values():
                if cache_key in expert_trends:
                    analysis = expert_trends[cache_key]
                    age_hours = (datetime.now() - analysis.last_updated).total_seconds() / 3600
                    return age_hours < self.cache_expiry_hours
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check cache validity: {e}")
            return False
    
    async def analyze_multiple_experts(
        self,
        expert_ids: List[str],
        category: Optional[str] = None,
        window_days: Optional[int] = None
    ) -> Dict[str, TrendAnalysis]:
        """Analyze trends for multiple experts"""
        try:
            results = {}
            
            for expert_id in expert_ids:
                trend_analysis = await self.analyze_expert_trend(expert_id, category, window_days)
                if trend_analysis:
                    results[expert_id] = trend_analysis
            
            logger.info(f"Analyzed trends for {len(results)} experts")
            return results
            
        except Exception as e:
            logger.error(f"Failed to analyze multiple expert trends: {e}")
            return {}
    
    async def get_trending_experts(
        self,
        direction: TrendDirection,
        confidence: Optional[TrendConfidence] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[TrendAnalysis]:
        """Get experts with specific trend characteristics"""
        try:
            trending_experts = []
            
            # Search through cached analyses
            for expert_id, expert_trends in self.trend_cache.items():
                for analysis in expert_trends.values():
                    if analysis.direction == direction:
                        if confidence is None or analysis.confidence == confidence:
                            if category is None or analysis.category == category:
                                trending_experts.append(analysis)
            
            # Sort by trend strength (descending)
            trending_experts.sort(key=lambda x: x.trend_strength, reverse=True)
            
            return trending_experts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get trending experts: {e}")
            return []
    
    async def get_trend_summary(self) -> Dict[str, Any]:
        """Get overall trend analysis summary"""
        try:
            all_analyses = []
            
            for expert_trends in self.trend_cache.values():
                all_analyses.extend(expert_trends.values())
            
            if not all_analyses:
                return {'error': 'No trend analyses available'}
            
            # Count by direction
            direction_counts = {}
            for direction in TrendDirection:
                direction_counts[direction.value] = sum(
                    1 for a in all_analyses if a.direction == direction
                )
            
            # Count by confidence
            confidence_counts = {}
            for confidence in TrendConfidence:
                confidence_counts[confidence.value] = sum(
                    1 for a in all_analyses if a.confidence == confidence
                )
            
            # Calculate averages
            avg_trend_strength = sum(a.trend_strength for a in all_analyses) / len(all_analyses)
            avg_r_squared = sum(a.r_squared for a in all_analyses) / len(all_analyses)
            avg_volatility = sum(a.volatility for a in all_analyses) / len(all_analyses)
            
            return {
                'total_analyses': len(all_analyses),
                'direction_distribution': direction_counts,
                'confidence_distribution': confidence_counts,
                'average_trend_strength': avg_trend_strength,
                'average_r_squared': avg_r_squared,
                'average_volatility': avg_volatility,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get trend summary: {e}")
            return {'error': str(e)}

# Usage example and testing
async def test_trend_analyzer():
    """Test the trend analyzer with mock data"""
    try:
        analyzer = TrendAnalyzer()
        
        # Test with mock expert
        expert_id = "test_expert"
        
        print("Testing Trend Analyzer...")
        
        # Analyze overall trend
        trend_analysis = await analyzer.analyze_expert_trend(expert_id)
        
        if trend_analysis:
            print(f"✅ Trend Analysis for {expert_id}:")
            print(f"  Direction: {trend_analysis.direction.value}")
            print(f"  Confidence: {trend_analysis.confidence.value}")
            print(f"  Slope: {trend_analysis.slope:.6f}")
            print(f"  R-squared: {trend_analysis.r_squared:.3f}")
            print(f"  Trend Strength: {trend_analysis.trend_strength:.3f}")
            print(f"  Momentum Score: {trend_analysis.momentum_score:.3f}")
            print(f"  Volatility: {trend_analysis.volatility:.3f}")
        else:
            print("❌ Failed to analyze trend")
        
        # Test trend summary
        summary = await analyzer.get_trend_summary()
        print(f"\nTrend Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Trend analyzer test failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_trend_analyzer())