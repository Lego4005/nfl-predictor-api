"""
Historical Performance Tracking and Analysis System
Implements comprehensive tracking, trend analysis, and performance validation
as specified in the comprehensive system testing plan design document.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import numpy as np
import json
from enum import Enum

logger = logging.getLogger(__name__)

class PerformanceTrend(Enum):
    """Performance trend categories"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"

@dataclass
class HistoricalDataPoint:
    """Single historical performance data point"""
    timestamp: datetime
    expert_id: str
    accuracy: float
    confidence_calibration: float
    consistency_score: float
    category_accuracies: Dict[str, float]
    game_context: Dict[str, Any]  # Weather, primetime, divisional, etc.
    prediction_count: int
    correct_predictions: int

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    trend_direction: PerformanceTrend
    trend_strength: float  # 0-1, higher = stronger trend
    slope: float  # Linear regression slope
    r_squared: float  # Correlation coefficient
    volatility: float  # Standard deviation of changes
    recent_performance: float  # Last 4 weeks average
    seasonal_patterns: Dict[str, float]  # Performance by conditions

@dataclass
class PerformanceWindow:
    """Performance analysis window"""
    start_date: datetime
    end_date: datetime
    data_points: List[HistoricalDataPoint]
    accuracy_trend: TrendAnalysis
    calibration_trend: TrendAnalysis
    consistency_trend: TrendAnalysis
    
class HistoricalPerformanceTracker:
    """Comprehensive historical performance tracking system"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.performance_history: Dict[str, List[HistoricalDataPoint]] = defaultdict(list)
        self.trend_cache: Dict[str, TrendAnalysis] = {}
        self.context_patterns: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Analysis windows
        self.analysis_windows = {
            'recent': timedelta(weeks=4),
            'medium_term': timedelta(weeks=8),
            'season_long': timedelta(weeks=17),
            'yearly': timedelta(days=365)
        }
        
    async def record_performance_datapoint(
        self,
        expert_id: str,
        accuracy: float,
        confidence_calibration: float,
        consistency_score: float,
        category_accuracies: Dict[str, float],
        game_context: Dict[str, Any],
        prediction_count: int,
        correct_predictions: int,
        timestamp: Optional[datetime] = None
    ) -> HistoricalDataPoint:
        """Record a new performance data point"""
        try:
            datapoint = HistoricalDataPoint(
                timestamp=timestamp or datetime.now(),
                expert_id=expert_id,
                accuracy=accuracy,
                confidence_calibration=confidence_calibration,
                consistency_score=consistency_score,
                category_accuracies=category_accuracies.copy(),
                game_context=game_context.copy(),
                prediction_count=prediction_count,
                correct_predictions=correct_predictions
            )
            
            # Store in memory
            self.performance_history[expert_id].append(datapoint)
            
            # Keep only last 100 data points per expert
            if len(self.performance_history[expert_id]) > 100:
                self.performance_history[expert_id] = self.performance_history[expert_id][-100:]
            
            # Store in database if available
            if self.supabase:
                await self._store_datapoint_to_db(datapoint)
            
            # Update context patterns
            self._update_context_patterns(expert_id, datapoint)
            
            # Invalidate trend cache for this expert
            if expert_id in self.trend_cache:
                del self.trend_cache[expert_id]
            
            logger.info(f"Recorded performance datapoint for {expert_id}: {accuracy:.3f} accuracy")
            
            return datapoint
            
        except Exception as e:
            logger.error(f"Failed to record performance datapoint for {expert_id}: {e}")
            raise
    
    async def analyze_performance_trends(
        self,
        expert_id: str,
        window_name: str = 'recent'
    ) -> TrendAnalysis:
        """Analyze performance trends for specified expert and window"""
        try:
            # Check cache first
            cache_key = f"{expert_id}_{window_name}"
            if cache_key in self.trend_cache:
                cached_trend = self.trend_cache[cache_key]
                # Return cached if less than 1 hour old
                if (datetime.now() - cached_trend.seasonal_patterns.get('last_updated', datetime.min)).total_seconds() < 3600:
                    return cached_trend
            
            # Get data for analysis window
            window_data = await self._get_window_data(expert_id, window_name)
            
            if len(window_data) < 3:
                # Insufficient data for trend analysis
                return TrendAnalysis(
                    trend_direction=PerformanceTrend.STABLE,
                    trend_strength=0.0,
                    slope=0.0,
                    r_squared=0.0,
                    volatility=0.0,
                    recent_performance=window_data[0].accuracy if window_data else 0.5,
                    seasonal_patterns={}
                )
            
            # Perform trend analysis
            trend_analysis = self._calculate_trend_analysis(window_data)
            
            # Cache the result
            trend_analysis.seasonal_patterns['last_updated'] = datetime.now()
            self.trend_cache[cache_key] = trend_analysis
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze trends for {expert_id}: {e}")
            raise
    
    async def generate_performance_report(
        self,
        expert_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            end_date = end_date or datetime.now()
            start_date = start_date or (end_date - timedelta(weeks=8))
            
            # Get performance data for period
            period_data = [
                dp for dp in self.performance_history[expert_id]
                if start_date <= dp.timestamp <= end_date
            ]
            
            if not period_data:
                return {
                    'error': 'No performance data available for specified period',
                    'expert_id': expert_id,
                    'period': f"{start_date} to {end_date}"
                }
            
            # Calculate summary statistics
            accuracies = [dp.accuracy for dp in period_data]
            calibrations = [dp.confidence_calibration for dp in period_data]
            consistencies = [dp.consistency_score for dp in period_data]
            
            summary_stats = {
                'accuracy': {
                    'mean': np.mean(accuracies),
                    'std': np.std(accuracies),
                    'min': np.min(accuracies),
                    'max': np.max(accuracies),
                    'trend': self._calculate_simple_trend(accuracies)
                },
                'calibration': {
                    'mean': np.mean(calibrations),
                    'std': np.std(calibrations),
                    'trend': self._calculate_simple_trend(calibrations)
                },
                'consistency': {
                    'mean': np.mean(consistencies),
                    'std': np.std(consistencies),
                    'trend': self._calculate_simple_trend(consistencies)
                }
            }
            
            # Analyze context performance
            context_analysis = self._analyze_context_performance(period_data)
            
            # Generate trend analysis for multiple windows
            trend_analyses = {}
            for window_name in self.analysis_windows.keys():
                trend_analyses[window_name] = await self.analyze_performance_trends(
                    expert_id, window_name
                )
            
            # Identify improvement opportunities
            improvement_opportunities = self._identify_improvement_opportunities(
                period_data, context_analysis, trend_analyses
            )
            
            # Calculate ranking stability
            ranking_stability = self._calculate_ranking_stability(expert_id, period_data)
            
            report = {
                'expert_id': expert_id,
                'report_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'data_points': len(period_data)
                },
                'summary_statistics': summary_stats,
                'trend_analyses': {
                    window: {
                        'direction': analysis.trend_direction.value,
                        'strength': analysis.trend_strength,
                        'recent_performance': analysis.recent_performance,
                        'volatility': analysis.volatility
                    }
                    for window, analysis in trend_analyses.items()
                },
                'context_performance': context_analysis,
                'ranking_stability': ranking_stability,
                'improvement_opportunities': improvement_opportunities,
                'generated_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report for {expert_id}: {e}")
            return {
                'error': str(e),
                'expert_id': expert_id,
                'generated_at': datetime.now().isoformat()
            }
    
    async def compare_expert_performance(
        self,
        expert_ids: List[str],
        window_name: str = 'recent'
    ) -> Dict[str, Any]:
        """Compare performance across multiple experts"""
        try:
            comparison_results = {}
            
            for expert_id in expert_ids:
                trend_analysis = await self.analyze_performance_trends(expert_id, window_name)
                window_data = await self._get_window_data(expert_id, window_name)
                
                if window_data:
                    comparison_results[expert_id] = {
                        'accuracy_mean': np.mean([dp.accuracy for dp in window_data]),
                        'accuracy_std': np.std([dp.accuracy for dp in window_data]),
                        'trend_direction': trend_analysis.trend_direction.value,
                        'trend_strength': trend_analysis.trend_strength,
                        'consistency': np.mean([dp.consistency_score for dp in window_data]),
                        'calibration': np.mean([dp.confidence_calibration for dp in window_data]),
                        'data_points': len(window_data)
                    }
            
            # Calculate relative rankings
            if comparison_results:
                sorted_by_accuracy = sorted(
                    comparison_results.items(),
                    key=lambda x: x[1]['accuracy_mean'],
                    reverse=True
                )
                
                for rank, (expert_id, data) in enumerate(sorted_by_accuracy, 1):
                    comparison_results[expert_id]['accuracy_rank'] = rank
                
                # Calculate statistical significance of differences
                significance_tests = self._calculate_significance_tests(comparison_results)
                
                return {
                    'window': window_name,
                    'expert_comparisons': comparison_results,
                    'rankings': {
                        'by_accuracy': [expert_id for expert_id, _ in sorted_by_accuracy],
                        'statistical_significance': significance_tests
                    },
                    'summary': {
                        'best_performer': sorted_by_accuracy[0][0] if sorted_by_accuracy else None,
                        'most_consistent': min(
                            comparison_results.items(),
                            key=lambda x: x[1]['accuracy_std']
                        )[0] if comparison_results else None,
                        'most_improving': max(
                            comparison_results.items(),
                            key=lambda x: x[1]['trend_strength'] if x[1]['trend_direction'] == 'improving' else 0
                        )[0] if comparison_results else None
                    },
                    'generated_at': datetime.now().isoformat()
                }
            
            return {'error': 'No performance data available for any expert'}
            
        except Exception as e:
            logger.error(f"Failed to compare expert performance: {e}")
            return {'error': str(e)}
    
    async def _get_window_data(
        self,
        expert_id: str,
        window_name: str
    ) -> List[HistoricalDataPoint]:
        """Get performance data for specified window"""
        if window_name not in self.analysis_windows:
            raise ValueError(f"Unknown analysis window: {window_name}")
        
        window_duration = self.analysis_windows[window_name]
        cutoff_date = datetime.now() - window_duration
        
        return [
            dp for dp in self.performance_history[expert_id]
            if dp.timestamp >= cutoff_date
        ]
    
    def _calculate_trend_analysis(self, data_points: List[HistoricalDataPoint]) -> TrendAnalysis:
        """Calculate comprehensive trend analysis"""
        if len(data_points) < 2:
            return TrendAnalysis(
                trend_direction=PerformanceTrend.STABLE,
                trend_strength=0.0,
                slope=0.0,
                r_squared=0.0,
                volatility=0.0,
                recent_performance=data_points[0].accuracy if data_points else 0.5,
                seasonal_patterns={}
            )
        
        # Sort by timestamp
        sorted_data = sorted(data_points, key=lambda x: x.timestamp)
        
        # Extract time series data
        timestamps = [(dp.timestamp - sorted_data[0].timestamp).total_seconds() for dp in sorted_data]
        accuracies = [dp.accuracy for dp in sorted_data]
        
        # Calculate linear regression
        slope, r_squared = self._linear_regression(timestamps, accuracies)
        
        # Calculate volatility
        accuracy_changes = [accuracies[i] - accuracies[i-1] for i in range(1, len(accuracies))]
        volatility = np.std(accuracy_changes) if accuracy_changes else 0.0
        
        # Determine trend direction and strength
        trend_direction = PerformanceTrend.IMPROVING if slope > 0.001 else \
                         PerformanceTrend.DECLINING if slope < -0.001 else \
                         PerformanceTrend.VOLATILE if volatility > 0.05 else \
                         PerformanceTrend.STABLE
        
        trend_strength = min(abs(slope) * 1000, 1.0)  # Scale slope to 0-1
        
        # Calculate recent performance
        recent_count = min(len(sorted_data), max(1, len(sorted_data) // 4))
        recent_performance = np.mean([dp.accuracy for dp in sorted_data[-recent_count:]])
        
        # Analyze seasonal patterns
        seasonal_patterns = self._analyze_seasonal_patterns(sorted_data)
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            slope=slope,
            r_squared=r_squared,
            volatility=volatility,
            recent_performance=recent_performance,
            seasonal_patterns=seasonal_patterns
        )
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        """Calculate linear regression slope and R-squared"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0, 0.0
        
        n = len(x)
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0.0
        
        # Calculate R-squared
        y_pred = [slope * (x[i] - x_mean) + y_mean for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return slope, max(0.0, r_squared)
    
    def _analyze_seasonal_patterns(self, data_points: List[HistoricalDataPoint]) -> Dict[str, float]:
        """Analyze performance patterns by context"""
        patterns = {}
        
        # Group by context conditions
        context_groups = defaultdict(list)
        
        for dp in data_points:
            # Weather conditions
            if 'weather' in dp.game_context:
                weather = dp.game_context['weather']
                context_groups[f"weather_{weather}"].append(dp.accuracy)
            
            # Game type
            if 'game_type' in dp.game_context:
                game_type = dp.game_context['game_type']
                context_groups[f"game_type_{game_type}"].append(dp.accuracy)
            
            # Day of week
            day_of_week = dp.timestamp.strftime('%A')
            context_groups[f"day_{day_of_week}"].append(dp.accuracy)
            
            # Time of year (month)
            month = dp.timestamp.strftime('%B')
            context_groups[f"month_{month}"].append(dp.accuracy)
        
        # Calculate average performance for each context
        for context, accuracies in context_groups.items():
            if len(accuracies) >= 2:  # Need at least 2 data points
                patterns[context] = np.mean(accuracies)
        
        return patterns
    
    def _analyze_context_performance(self, data_points: List[HistoricalDataPoint]) -> Dict[str, Any]:
        """Analyze performance by game context"""
        context_analysis = {
            'weather_performance': defaultdict(list),
            'game_type_performance': defaultdict(list),
            'divisional_performance': defaultdict(list),
            'primetime_performance': defaultdict(list)
        }
        
        for dp in data_points:
            context = dp.game_context
            
            # Weather analysis
            if 'weather' in context:
                context_analysis['weather_performance'][context['weather']].append(dp.accuracy)
            
            # Game type analysis
            if 'game_type' in context:
                context_analysis['game_type_performance'][context['game_type']].append(dp.accuracy)
            
            # Divisional games
            is_divisional = context.get('divisional_game', False)
            context_analysis['divisional_performance']['divisional' if is_divisional else 'non_divisional'].append(dp.accuracy)
            
            # Primetime games
            is_primetime = context.get('primetime', False)
            context_analysis['primetime_performance']['primetime' if is_primetime else 'regular'].append(dp.accuracy)
        
        # Calculate averages and identify strengths/weaknesses
        analysis_results = {}
        
        for category, performance_data in context_analysis.items():
            category_results = {}
            best_context = None
            worst_context = None
            best_performance = 0.0
            worst_performance = 1.0
            
            for context_type, accuracies in performance_data.items():
                if accuracies:
                    avg_accuracy = np.mean(accuracies)
                    category_results[context_type] = {
                        'average_accuracy': avg_accuracy,
                        'sample_size': len(accuracies),
                        'std_deviation': np.std(accuracies)
                    }
                    
                    if avg_accuracy > best_performance:
                        best_performance = avg_accuracy
                        best_context = context_type
                    
                    if avg_accuracy < worst_performance:
                        worst_performance = avg_accuracy
                        worst_context = context_type
            
            analysis_results[category] = {
                'by_context': category_results,
                'best_context': best_context,
                'worst_context': worst_context,
                'performance_spread': best_performance - worst_performance if best_context and worst_context else 0.0
            }
        
        return analysis_results
    
    def _identify_improvement_opportunities(
        self,
        data_points: List[HistoricalDataPoint],
        context_analysis: Dict[str, Any],
        trend_analyses: Dict[str, TrendAnalysis]
    ) -> List[str]:
        """Identify specific improvement opportunities"""
        opportunities = []
        
        # Analyze context weaknesses
        for category, analysis in context_analysis.items():
            if analysis.get('performance_spread', 0) > 0.1:  # Significant variation
                worst_context = analysis.get('worst_context')
                if worst_context:
                    opportunities.append(
                        f"Improve performance in {worst_context} conditions "
                        f"(current weakness in {category.replace('_performance', '')})"
                    )
        
        # Analyze trend concerns
        recent_trend = trend_analyses.get('recent')
        if recent_trend and recent_trend.trend_direction == PerformanceTrend.DECLINING:
            opportunities.append(
                f"Address declining recent performance trend "
                f"(slope: {recent_trend.slope:.4f})"
            )
        
        # Analyze consistency issues
        if recent_trend and recent_trend.volatility > 0.05:
            opportunities.append(
                "Improve prediction consistency - high volatility detected"
            )
        
        # Analyze calibration issues
        recent_calibrations = [dp.confidence_calibration for dp in data_points[-10:]] if data_points else []
        if recent_calibrations and np.mean(recent_calibrations) < 0.6:
            opportunities.append(
                "Improve confidence calibration - predictions overconfident or underconfident"
            )
        
        # Category-specific analysis
        if data_points:
            category_accuracy_avgs = defaultdict(list)
            for dp in data_points[-20:]:  # Last 20 data points
                for category, accuracy in dp.category_accuracies.items():
                    category_accuracy_avgs[category].append(accuracy)
            
            weak_categories = []
            for category, accuracies in category_accuracy_avgs.items():
                if accuracies and np.mean(accuracies) < 0.5:
                    weak_categories.append(category)
            
            if weak_categories:
                opportunities.append(
                    f"Focus on improving performance in: {', '.join(weak_categories)}"
                )
        
        return opportunities[:5]  # Return top 5 opportunities
    
    def _calculate_ranking_stability(
        self,
        expert_id: str,
        data_points: List[HistoricalDataPoint]
    ) -> Dict[str, float]:
        """Calculate ranking stability metrics"""
        # This would need access to other experts' data for true ranking
        # For now, provide stability based on performance consistency
        
        if len(data_points) < 5:
            return {'stability_score': 0.5, 'rank_changes': 0}
        
        # Use accuracy as proxy for ranking
        accuracies = [dp.accuracy for dp in data_points[-10:]]  # Last 10 points
        
        # Calculate stability as inverse of standard deviation
        stability_score = max(0.0, 1.0 - np.std(accuracies) * 2)
        
        # Estimate rank changes based on performance swings
        accuracy_ranges = [max(accuracies[max(0, i-2):i+3]) - min(accuracies[max(0, i-2):i+3]) 
                          for i in range(2, len(accuracies)-2)]
        avg_range = np.mean(accuracy_ranges) if accuracy_ranges else 0.0
        estimated_rank_changes = int(avg_range * 10)  # Rough estimate
        
        return {
            'stability_score': stability_score,
            'estimated_rank_changes': estimated_rank_changes,
            'performance_variance': np.var(accuracies)
        }
    
    def _calculate_significance_tests(self, comparison_results: Dict[str, Any]) -> Dict[str, bool]:
        """Calculate statistical significance of performance differences"""
        # Simplified significance testing
        significance_tests = {}
        
        expert_ids = list(comparison_results.keys())
        for i, expert1 in enumerate(expert_ids):
            for expert2 in expert_ids[i+1:]:
                acc1 = comparison_results[expert1]['accuracy_mean']
                std1 = comparison_results[expert1]['accuracy_std']
                n1 = comparison_results[expert1]['data_points']
                
                acc2 = comparison_results[expert2]['accuracy_mean']
                std2 = comparison_results[expert2]['accuracy_std']
                n2 = comparison_results[expert2]['data_points']
                
                # Simple t-test approximation
                if n1 > 1 and n2 > 1 and (std1 > 0 or std2 > 0):
                    pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
                    t_stat = abs(acc1 - acc2) / (pooled_std * np.sqrt(1/n1 + 1/n2)) if pooled_std > 0 else 0
                    
                    # Rough significance threshold (t > 2.0 for p < 0.05 approximation)
                    is_significant = t_stat > 2.0
                    
                    significance_tests[f"{expert1}_vs_{expert2}"] = is_significant
        
        return significance_tests
    
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction"""
        if len(values) < 2:
            return "stable"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)
        
        diff = second_avg - first_avg
        
        if diff > 0.02:
            return "improving"
        elif diff < -0.02:
            return "declining"
        else:
            return "stable"
    
    def _update_context_patterns(self, expert_id: str, datapoint: HistoricalDataPoint):
        """Update context performance patterns"""
        for context_key, context_value in datapoint.game_context.items():
            pattern_key = f"{context_key}_{context_value}"
            
            if pattern_key not in self.context_patterns[expert_id]:
                self.context_patterns[expert_id][pattern_key] = datapoint.accuracy
            else:
                # Exponential moving average
                current = self.context_patterns[expert_id][pattern_key]
                self.context_patterns[expert_id][pattern_key] = 0.8 * current + 0.2 * datapoint.accuracy
    
    async def _store_datapoint_to_db(self, datapoint: HistoricalDataPoint):
        """Store datapoint to database"""
        if not self.supabase:
            return
        
        try:
            # Convert to database format
            db_record = {
                'expert_id': datapoint.expert_id,
                'timestamp': datapoint.timestamp.isoformat(),
                'accuracy': datapoint.accuracy,
                'confidence_calibration': datapoint.confidence_calibration,
                'consistency_score': datapoint.consistency_score,
                'category_accuracies': json.dumps(datapoint.category_accuracies),
                'game_context': json.dumps(datapoint.game_context),
                'prediction_count': datapoint.prediction_count,
                'correct_predictions': datapoint.correct_predictions
            }
            
            # Insert into database
            result = self.supabase.table('expert_performance_history').insert(db_record).execute()
            
            if result.data:
                logger.debug(f"Stored performance datapoint to database for {datapoint.expert_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store datapoint to database: {e}")
    
    async def load_historical_data_from_db(self, expert_id: str, days: int = 30) -> List[HistoricalDataPoint]:
        """Load historical data from database"""
        if not self.supabase:
            return []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = self.supabase.table('expert_performance_history').select('*').eq(
                'expert_id', expert_id
            ).gte('timestamp', cutoff_date.isoformat()).execute()
            
            datapoints = []
            for record in result.data:
                datapoint = HistoricalDataPoint(
                    timestamp=datetime.fromisoformat(record['timestamp']),
                    expert_id=record['expert_id'],
                    accuracy=record['accuracy'],
                    confidence_calibration=record['confidence_calibration'],
                    consistency_score=record['consistency_score'],
                    category_accuracies=json.loads(record['category_accuracies']),
                    game_context=json.loads(record['game_context']),
                    prediction_count=record['prediction_count'],
                    correct_predictions=record['correct_predictions']
                )
                datapoints.append(datapoint)
            
            # Store in memory
            self.performance_history[expert_id] = datapoints
            
            logger.info(f"Loaded {len(datapoints)} historical datapoints for {expert_id}")
            return datapoints
            
        except Exception as e:
            logger.error(f"Failed to load historical data for {expert_id}: {e}")
            return []