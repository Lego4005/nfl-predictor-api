"""
Learning Mode Comparator for NFL Personality-Driven Experts

This module compares expert performance across different learning configurations:
1. Baseline: No learning, static behavior
2. Memory-only: Episodic memory without belief revision 
3. Full learning: Memory + belief revision + weight adaptation

The comparator runs the same expert through identical seasons
with different learning modes to determine if memory and belief
revision actually improve predictions compared to baseline.
"""

import logging
import asyncio
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
from scipy import stats

# Import necessary services and data structures
try:
    from .backtest_runner import BacktestRunner, BacktestResults, LearningMode
    from .historical_data_service import HistoricalDataService
    from .universal_game_data_builder import UniversalGameDataBuilder
except ImportError:
    from src.services.backtest_runner import BacktestRunner, BacktestResults, LearningMode
    from src.services.historical_data_service import HistoricalDataService
    from src.services.universal_game_data_builder import UniversalGameDataBuilder

# Import personality expert classes
try:
    from ..ml.personality_driven_experts import PersonalityDrivenExpert
except ImportError:
    try:
        from src.ml.personality_driven_experts import PersonalityDrivenExpert
    except ImportError:
        # Create a placeholder if the personality experts module isn't available
        class PersonalityDrivenExpert:
            def __init__(self):
                self.expert_id = "placeholder"
                self.name = "Placeholder Expert"

logger = logging.getLogger(__name__)


@dataclass
class LearningComparison:
    """Results comparing learning modes for a single expert"""
    expert_id: str
    season: int
    comparison_timestamp: str
    
    # Individual mode results
    baseline_results: BacktestResults
    memory_only_results: BacktestResults
    full_learning_results: BacktestResults
    
    # Comparative analysis
    baseline_accuracy: float = 0.0
    memory_only_accuracy: float = 0.0
    full_learning_accuracy: float = 0.0
    
    # Improvement metrics
    memory_improvement: float = 0.0  # Memory vs Baseline
    full_improvement: float = 0.0    # Full vs Baseline
    memory_vs_full: float = 0.0      # Memory vs Full
    
    # Statistical significance
    memory_p_value: Optional[float] = None
    full_p_value: Optional[float] = None
    memory_vs_full_p_value: Optional[float] = None
    
    # Learning effectiveness
    is_memory_significant: bool = False
    is_full_significant: bool = False
    best_learning_mode: LearningMode = LearningMode.BASELINE
    
    # Performance evolution
    baseline_consistency: float = 0.0
    memory_consistency: float = 0.0
    full_consistency: float = 0.0
    
    # Learning metrics
    total_learning_events: int = 0
    total_belief_revisions: int = 0
    total_memories_stored: int = 0


@dataclass
class SeasonComparison:
    """Multi-season learning comparison results"""
    expert_id: str
    seasons: List[int]
    comparisons: List[LearningComparison] = field(default_factory=list)
    
    # Aggregate statistics
    avg_baseline_accuracy: float = 0.0
    avg_memory_accuracy: float = 0.0
    avg_full_accuracy: float = 0.0
    
    # Consistency across seasons
    baseline_variance: float = 0.0
    memory_variance: float = 0.0
    full_variance: float = 0.0
    
    # Overall learning effectiveness
    consistent_memory_improvement: bool = False
    consistent_full_improvement: bool = False
    learning_reliability_score: float = 0.0


class LearningModeComparator:
    """
    Compares expert performance across different learning configurations
    
    Runs the same expert through identical seasons with different learning modes
    to determine if memory and belief revision improve predictions.
    """
    
    def __init__(
        self,
        backtest_runner: BacktestRunner,
        historical_service: HistoricalDataService
    ):
        self.backtest_runner = backtest_runner
        self.historical_service = historical_service
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Comparison tracking
        self._comparisons: List[LearningComparison] = []
        self._season_comparisons: List[SeasonComparison] = []
        
        self.logger.info("🧠 Learning Mode Comparator initialized for expert analysis")
    
    async def compare_learning_modes(
        self,
        expert: PersonalityDrivenExpert,
        season: int,
        start_week: int = 1,
        end_week: int = 18,
        game_filter: Optional[Dict[str, Any]] = None
    ) -> LearningComparison:
        """
        Compare expert performance across three learning configurations
        
        Args:
            expert: Personality-driven expert to test
            season: Season year to analyze
            start_week: Starting week (default: 1)
            end_week: Ending week (default: 18)
            game_filter: Optional filter for specific games
            
        Returns:
            LearningComparison with detailed analysis
        """
        try:
            self.logger.info(f"🧠 Starting learning mode comparison for {expert.name} - {season} season")
            
            # Run three backtests with different learning modes
            baseline_results = await self._run_controlled_backtest(
                expert, season, LearningMode.BASELINE, start_week, end_week, game_filter
            )
            
            memory_only_results = await self._run_controlled_backtest(
                expert, season, LearningMode.MEMORY_ONLY, start_week, end_week, game_filter
            )
            
            full_learning_results = await self._run_controlled_backtest(
                expert, season, LearningMode.FULL_LEARNING, start_week, end_week, game_filter
            )
            
            # Create comparison analysis
            comparison = LearningComparison(
                expert_id=expert.expert_id,
                season=season,
                comparison_timestamp=datetime.now().isoformat(),
                baseline_results=baseline_results,
                memory_only_results=memory_only_results,
                full_learning_results=full_learning_results
            )
            
            # Analyze the results
            self._analyze_learning_effectiveness(comparison)
            
            # Store for future analysis
            self._comparisons.append(comparison)
            
            self.logger.info(f"✅ Learning comparison complete for {expert.name}: "
                           f"Baseline: {comparison.baseline_accuracy:.1%}, "
                           f"Memory: {comparison.memory_only_accuracy:.1%}, "
                           f"Full: {comparison.full_learning_accuracy:.1%}")
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"❌ Error in learning mode comparison: {e}")
            raise
    
    async def compare_multiple_seasons(
        self,
        expert: PersonalityDrivenExpert,
        seasons: List[int],
        start_week: int = 1,
        end_week: int = 18,
        game_filter: Optional[Dict[str, Any]] = None
    ) -> SeasonComparison:
        """
        Compare learning modes across multiple seasons
        
        Args:
            expert: Personality-driven expert to test
            seasons: List of season years to analyze
            start_week: Starting week (default: 1)
            end_week: Ending week (default: 18)
            game_filter: Optional filter for specific games
            
        Returns:
            SeasonComparison with multi-season analysis
        """
        try:
            self.logger.info(f"🏈 Starting multi-season learning comparison for {expert.name}")
            self.logger.info(f"📅 Analyzing {len(seasons)} seasons: {seasons}")
            
            season_comparison = SeasonComparison(
                expert_id=expert.expert_id,
                seasons=seasons
            )
            
            # Run comparison for each season
            for season in seasons:
                self.logger.info(f"🔍 Analyzing {season} season...")
                
                comparison = await self.compare_learning_modes(
                    expert, season, start_week, end_week, game_filter
                )
                
                season_comparison.comparisons.append(comparison)
            
            # Analyze multi-season patterns
            self._analyze_season_patterns(season_comparison)
            
            # Store for future reference
            self._season_comparisons.append(season_comparison)
            
            self.logger.info(f"✅ Multi-season analysis complete for {expert.name}")
            self.logger.info(f"📊 Average accuracies - Baseline: {season_comparison.avg_baseline_accuracy:.1%}, "
                           f"Memory: {season_comparison.avg_memory_accuracy:.1%}, "
                           f"Full: {season_comparison.avg_full_accuracy:.1%}")
            
            return season_comparison
            
        except Exception as e:
            self.logger.error(f"❌ Error in multi-season comparison: {e}")
            raise
    
    async def _run_controlled_backtest(
        self,
        expert: PersonalityDrivenExpert,
        season: int,
        learning_mode: LearningMode,
        start_week: int,
        end_week: int,
        game_filter: Optional[Dict[str, Any]]
    ) -> BacktestResults:
        """Run a controlled backtest ensuring clean expert state"""
        try:
            # Reset expert state to ensure clean comparison
            await self._reset_expert_state(expert)
            
            # Run backtest with specific learning mode
            results = await self.backtest_runner.run_season_backtest(
                expert=expert,
                season=season,
                learning_mode=learning_mode,
                start_week=start_week,
                end_week=end_week,
                game_filter=game_filter
            )
            
            self.logger.debug(f"🎯 {learning_mode.value} backtest complete: {results.overall_accuracy:.1%} accuracy")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in controlled backtest ({learning_mode.value}): {e}")
            raise
    
    async def _reset_expert_state(self, expert: PersonalityDrivenExpert):
        """Reset expert to clean state for fair comparison"""
        try:
            # Reset memory if expert has memory service
            if hasattr(expert, 'memory_service') and expert.memory_service:
                if hasattr(expert.memory_service, 'clear_memories'):
                    await expert.memory_service.clear_memories()
            
            # Reset beliefs if expert has belief system
            if hasattr(expert, 'reset_beliefs'):
                expert.reset_beliefs()
            
            # Reset any learning state
            if hasattr(expert, 'reset_learning_state'):
                expert.reset_learning_state()
            
            self.logger.debug(f"🔄 Expert {expert.expert_id} state reset for clean comparison")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not fully reset expert state: {e}")
    
    def _analyze_learning_effectiveness(self, comparison: LearningComparison):
        """Analyze the effectiveness of different learning modes"""
        try:
            # Extract accuracy metrics
            comparison.baseline_accuracy = comparison.baseline_results.overall_accuracy
            comparison.memory_only_accuracy = comparison.memory_only_results.overall_accuracy
            comparison.full_learning_accuracy = comparison.full_learning_results.overall_accuracy
            
            # Calculate improvement percentages
            if comparison.baseline_accuracy > 0:
                comparison.memory_improvement = (
                    (comparison.memory_only_accuracy - comparison.baseline_accuracy) 
                    / comparison.baseline_accuracy
                ) * 100
                
                comparison.full_improvement = (
                    (comparison.full_learning_accuracy - comparison.baseline_accuracy) 
                    / comparison.baseline_accuracy
                ) * 100
            
            if comparison.memory_only_accuracy > 0:
                comparison.memory_vs_full = (
                    (comparison.full_learning_accuracy - comparison.memory_only_accuracy) 
                    / comparison.memory_only_accuracy
                ) * 100
            
            # Statistical significance testing
            self._calculate_statistical_significance(comparison)
            
            # Determine best learning mode
            accuracies = {
                LearningMode.BASELINE: comparison.baseline_accuracy,
                LearningMode.MEMORY_ONLY: comparison.memory_only_accuracy,
                LearningMode.FULL_LEARNING: comparison.full_learning_accuracy
            }
            comparison.best_learning_mode = max(accuracies, key=accuracies.get)
            
            # Calculate consistency metrics
            self._calculate_consistency_metrics(comparison)
            
            # Aggregate learning statistics
            comparison.total_learning_events = (
                comparison.memory_only_results.learning_events + 
                comparison.full_learning_results.learning_events
            )
            comparison.total_belief_revisions = (
                comparison.memory_only_results.belief_revisions + 
                comparison.full_learning_results.belief_revisions
            )
            comparison.total_memories_stored = (
                comparison.memory_only_results.memories_created + 
                comparison.full_learning_results.memories_created
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing learning effectiveness: {e}")
    
    def _calculate_statistical_significance(self, comparison: LearningComparison):
        """Calculate statistical significance of learning improvements"""
        try:
            # Extract prediction accuracies for statistical testing
            baseline_accuracies = [
                p.overall_accuracy for p in comparison.baseline_results.predictions 
                if p.overall_accuracy is not None
            ]
            memory_accuracies = [
                p.overall_accuracy for p in comparison.memory_only_results.predictions 
                if p.overall_accuracy is not None
            ]
            full_accuracies = [
                p.overall_accuracy for p in comparison.full_learning_results.predictions 
                if p.overall_accuracy is not None
            ]
            
            # Paired t-tests for significance
            if len(baseline_accuracies) >= 10 and len(memory_accuracies) >= 10:
                # Memory vs Baseline
                try:
                    _, comparison.memory_p_value = stats.ttest_rel(memory_accuracies, baseline_accuracies)
                    comparison.is_memory_significant = comparison.memory_p_value < 0.05
                except Exception:
                    comparison.memory_p_value = None
            
            if len(baseline_accuracies) >= 10 and len(full_accuracies) >= 10:
                # Full learning vs Baseline
                try:
                    _, comparison.full_p_value = stats.ttest_rel(full_accuracies, baseline_accuracies)
                    comparison.is_full_significant = comparison.full_p_value < 0.05
                except Exception:
                    comparison.full_p_value = None
            
            if len(memory_accuracies) >= 10 and len(full_accuracies) >= 10:
                # Memory vs Full learning
                try:
                    _, comparison.memory_vs_full_p_value = stats.ttest_rel(full_accuracies, memory_accuracies)
                except Exception:
                    comparison.memory_vs_full_p_value = None
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not calculate statistical significance: {e}")
    
    def _calculate_consistency_metrics(self, comparison: LearningComparison):
        """Calculate consistency metrics for each learning mode"""
        try:
            # Calculate standard deviation of rolling accuracies as consistency measure
            if comparison.baseline_results.rolling_accuracy:
                comparison.baseline_consistency = 1.0 - statistics.stdev(
                    comparison.baseline_results.rolling_accuracy
                )
            
            if comparison.memory_only_results.rolling_accuracy:
                comparison.memory_consistency = 1.0 - statistics.stdev(
                    comparison.memory_only_results.rolling_accuracy
                )
            
            if comparison.full_learning_results.rolling_accuracy:
                comparison.full_consistency = 1.0 - statistics.stdev(
                    comparison.full_learning_results.rolling_accuracy
                )
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not calculate consistency metrics: {e}")
    
    def _analyze_season_patterns(self, season_comparison: SeasonComparison):
        """Analyze patterns across multiple seasons"""
        try:
            if not season_comparison.comparisons:
                return
            
            # Calculate average accuracies
            baseline_accuracies = [c.baseline_accuracy for c in season_comparison.comparisons]
            memory_accuracies = [c.memory_only_accuracy for c in season_comparison.comparisons]
            full_accuracies = [c.full_learning_accuracy for c in season_comparison.comparisons]
            
            season_comparison.avg_baseline_accuracy = statistics.mean(baseline_accuracies)
            season_comparison.avg_memory_accuracy = statistics.mean(memory_accuracies)
            season_comparison.avg_full_accuracy = statistics.mean(full_accuracies)
            
            # Calculate variance (consistency across seasons)
            if len(baseline_accuracies) > 1:
                season_comparison.baseline_variance = statistics.variance(baseline_accuracies)
                season_comparison.memory_variance = statistics.variance(memory_accuracies)
                season_comparison.full_variance = statistics.variance(full_accuracies)
            
            # Check for consistent improvement
            memory_improvements = [c.memory_improvement for c in season_comparison.comparisons]
            full_improvements = [c.full_improvement for c in season_comparison.comparisons]
            
            season_comparison.consistent_memory_improvement = all(imp > 0 for imp in memory_improvements)
            season_comparison.consistent_full_improvement = all(imp > 0 for imp in full_improvements)
            
            # Calculate learning reliability score
            positive_memory = sum(1 for imp in memory_improvements if imp > 0)
            positive_full = sum(1 for imp in full_improvements if imp > 0)
            total_seasons = len(season_comparison.comparisons)
            
            season_comparison.learning_reliability_score = (
                (positive_memory + positive_full) / (2 * total_seasons)
            ) if total_seasons > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing season patterns: {e}")
    
    def get_comparison_summary(self, expert_id: str) -> Dict[str, Any]:
        """Get summary of all comparisons for an expert"""
        expert_comparisons = [c for c in self._comparisons if c.expert_id == expert_id]
        expert_season_comparisons = [c for c in self._season_comparisons if c.expert_id == expert_id]
        
        if not expert_comparisons:
            return {"error": f"No comparisons found for expert {expert_id}"}
        
        # Aggregate statistics
        avg_baseline = statistics.mean([c.baseline_accuracy for c in expert_comparisons])
        avg_memory = statistics.mean([c.memory_only_accuracy for c in expert_comparisons])
        avg_full = statistics.mean([c.full_learning_accuracy for c in expert_comparisons])
        
        significant_memory = sum(1 for c in expert_comparisons if c.is_memory_significant)
        significant_full = sum(1 for c in expert_comparisons if c.is_full_significant)
        
        return {
            "expert_id": expert_id,
            "total_comparisons": len(expert_comparisons),
            "total_season_comparisons": len(expert_season_comparisons),
            "average_accuracies": {
                "baseline": avg_baseline,
                "memory_only": avg_memory,
                "full_learning": avg_full
            },
            "significant_improvements": {
                "memory_count": significant_memory,
                "full_count": significant_full,
                "memory_rate": significant_memory / len(expert_comparisons),
                "full_rate": significant_full / len(expert_comparisons)
            },
            "learning_effectiveness": {
                "memory_helpful": avg_memory > avg_baseline,
                "full_learning_helpful": avg_full > avg_baseline,
                "best_mode": "full_learning" if avg_full > max(avg_baseline, avg_memory) 
                           else "memory_only" if avg_memory > avg_baseline else "baseline"
            }
        }