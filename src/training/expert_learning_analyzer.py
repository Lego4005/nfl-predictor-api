#!/usr/bin/env python3
"""
Expert Learning Curve Analyzer

Measures prediction acacy improvement over time, tracks expert personality
stability vs drift, analyzes which experts perform best in different contexts,
and identifies experts that improve vs degrade with experience.
"""

import sys
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
sys.path.append('src')

from training.expert_configuration import ExpertType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LearningCurvePoint:
    """Single point on an expert's learning curve"""
    game_number: int
    week: int
    accuracy: float
    confidence: float
    correct_predictions: int
    total_predictions: int
    game_date: date

@dataclass
class ExpertLearningCurve:
    """Complete learning curve for an expert"""
    expert_id: str
    expert_type: ExpertType
    curve_points: List[LearningCurvePoint]

    # Learning metrics
    initial_accuracy: float
    final_accuracy: float
    accuracy_improvement: float
    learning_trend: str  # 'improving', 'declining', 'stable'

    # Stability metrics
    confidence_stability: float
    personality_drift_score: float

    # Context performance
    context_performance: Dict[str, float]  # Performance in different contexts

@dataclass
class LearningAnalysis:
    """Complete learning analysis for all experts"""
    season: int
    total_games: int
    expert_curves: Dict[str, ExpertLearningCurve]

    # Comparative analysis
    best_learners: List[str]
    worst_learners: List[str]
    most_stable: List[str]
    most_volatile: List[str]

    # Context insights
    context_specialists: Dict[str, List[str]]  # Context -> List of expert IDs

    # System insights
    overall_learning_trend: str
    learning_effectiveness_score: float

class ExpertLearningAnalyzer:
    """Analyzes expert learning curves and performance evolution"""

    def __init__(self, results_dir: str = "2020_season_results"):
        """Initialize the learning analyzer"""
        self.results_dir = Path(results_dir)
        self.predictions_data = []
        self.outcomes_data = []

        logger.info("✅ Expert Learning Analyzer initialized")

    def load_season_data(self, season: int = 2020) -> bool:
        """Load season prediction and outcome data"""
        try:
            # Load from checkpoint files
            predictions_file = Path("training_checkpoints") / f"predictions_{season}.jsonl"
            outcomes_file = Path("training_checkpoints") / f"outcomes_{season}.jsonl"

            if not predictions_file.exists() or not outcomes_file.exists():
                logger.error(f"❌ Season {season} data files not found")
                return False

            # Load predictions
            self.predictions_data = []
            with open(predictions_file, 'r') as f:
                for line in f:
                    self.predictions_data.append(json.loads(line))

            # Load outcomes
            self.outcomes_data = []
            with open(outcomes_file, 'r') as f:
                for line in f:
                    self.outcomes_data.append(json.loads(line))

            logger.info(f"✅ Loaded {len(self.predictions_data)} predictions and {len(self.outcomes_data)} outcomes")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load season data: {e}")
            return False

    def analyze_learning_curves(self, season: int = 2020) -> LearningAnalysis:
        """Analyze learning curves for all experts"""
        logger.info(f"📊 Analyzing learning curves for {season} season...")

        if not self.load_season_data(season):
            raise ValueError(f"Could not load data for season {season}")

        # Build expert learning curves
        expert_curves = {}

        # Get all expert IDs from the data
        all_expert_ids = set()
        for pred_record in self.predictions_data:
            all_expert_ids.update(pred_record.get('predictions', {}).keys())

        logger.info(f"📈 Analyzing {len(all_expert_ids)} experts across {len(self.predictions_data)} games")

        # Build learning curve for each expert
        for expert_id in all_expert_ids:
            try:
                expert_type = ExpertType(expert_id)
                curve = self._build_expert_learning_curve(expert_id, expert_type)
                expert_curves[expert_id] = curve
            except Exception as e:
                logger.warning(f"⚠️ Failed to analyze {expert_id}: {e}")
                continue

        # Perform comparative analysis
        analysis = self._perform_comparative_analysis(season, expert_curves)

        # Save analysis results
        self._save_learning_analysis(analysis)

        logger.info("✅ Learning curve analysis completed")
        return analysis

    def _build_expert_learning_curve(self, expert_id: str, expert_type: ExpertType) -> ExpertLearningCurve:
        """Build learning curve for a single expert"""
        curve_points = []
        running_correct = 0
        running_total = 0

        # Process games chronologically
        for i, (pred_record, outcome_record) in enumerate(zip(self.predictions_data, self.outcomes_data)):
            if expert_id not in pred_record.get('predictions', {}):
                continue

            expert_pred = pred_record['predictions'][expert_id]

            # Determine if prediction was correct
            home_score = outcome_record['actual_result']['home_score']
            away_score = outcome_record['actual_result']['away_score']

            actual_winner = 'home' if home_score > away_score else 'away'
            predicted_winner = 'home' if expert_pred['win_probability'] > 0.5 else 'away'

            was_correct = (actual_winner == predicted_winner)

            # Update running totals
            running_total += 1
            if was_correct:
                running_correct += 1

            # Calculate current accuracy
            current_accuracy = running_correct / running_total

            # Parse game date
            game_date = datetime.fromisoformat(pred_record['game_date']).date()

            # Create curve point
            point = LearningCurvePoint(
                game_number=i + 1,
                week=pred_record['week'],
                accuracy=current_accuracy,
                confidence=expert_pred['confidence_level'],
                correct_predictions=running_correct,
                total_predictions=running_total,
                game_date=game_date
            )

            curve_points.append(point)

        if not curve_points:
            raise ValueError(f"No valid predictions found for {expert_id}")

        # Calculate learning metrics
        initial_accuracy = curve_points[0].accuracy if curve_points else 0.0
        final_accuracy = curve_points[-1].accuracy if curve_points else 0.0
        accuracy_improvement = final_accuracy - initial_accuracy

        # Determine learning trend
        learning_trend = self._determine_learning_trend(curve_points)

        # Calculate stability metrics
        confidence_stability = self._calculate_confidence_stability(curve_points)
        personality_drift_score = self._calculate_personality_drift(expert_id, curve_points)

        # Analyze context performance
        context_performance = self._analyze_context_performance(expert_id)

        return ExpertLearningCurve(
            expert_id=expert_id,
            expert_type=expert_type,
            curve_points=curve_points,
            initial_accuracy=initial_accuracy,
            final_accuracy=final_accuracy,
            accuracy_improvement=accuracy_improvement,
            learning_trend=learning_trend,
            confidence_stability=confidence_stability,
            personality_drift_score=personality_drift_score,
            context_performance=context_performance
        )

    def _determine_learning_trend(self, curve_points: List[LearningCurvePoint]) -> str:
        """Determine if expert is improving, declining, or stable"""
        if len(curve_points) < 10:
            return 'insufficient_data'

        # Use linear regression on accuracy over time
        x = np.array([p.game_number for p in curve_points])
        y = np.array([p.accuracy for p in curve_points])

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.001:  # Improving by more than 0.1% per game
            return 'improving'
        elif slope < -0.001:  # Declining by more than 0.1% per game
            return 'declining'
        else:
            return 'stable'

    def _calculate_confidence_stability(self, curve_points: List[LearningCurvePoint]) -> float:
        """Calculate how stable the expert's confidence levels are"""
        if len(curve_points) < 5:
            return 0.0

        confidences = [p.confidence for p in curve_points]

        # Calculate coefficient of variation (std dev / mean)
        mean_confidence = np.mean(confidences)
        std_confidence = np.std(confidences)

        if mean_confidence == 0:
            return 0.0

        # Return stability score (1 - coefficient of variation)
        cv = std_confidence / mean_confidence
        return max(0.0, 1.0 - cv)

    def _calculate_personality_drift(self, expert_id: str, curve_points: List[LearningCurvePoint]) -> float:
        """Calculate how much the expert's personality has drifted"""
        # This is a simplified implementation
        # In a full system, we'd analyze reasoning patterns, confidence patterns, etc.

        if len(curve_points) < 20:
            return 0.0

        # Split into early and late periods
        mid_point = len(curve_points) // 2
        early_points = curve_points[:mid_point]
        late_points = curve_points[mid_point:]

        # Compare confidence patterns
        early_avg_confidence = np.mean([p.confidence for p in early_points])
        late_avg_confidence = np.mean([p.confidence for p in late_points])

        confidence_drift = abs(late_avg_confidence - early_avg_confidence)

        # For now, use confidence drift as a proxy for personality drift
        return min(confidence_drift, 1.0)

    def _analyze_context_performance(self, expert_id: str) -> Dict[str, float]:
        """Analyze expert performance in different contexts"""
        context_performance = {}

        # Analyze performance by week (early vs late season)
        early_season_correct = 0
        early_season_total = 0
        late_season_correct = 0
        late_season_total = 0

        # Analyze performance by game type
        division_correct = 0
        division_total = 0
        non_division_correct = 0
        non_division_total = 0

        for pred_record, outcome_record in zip(self.predictions_data, self.outcomes_data):
            if expert_id not in pred_record.get('predictions', {}):
                continue

            expert_pred = pred_record['predictions'][expert_id]

            # Determine if prediction was correct
            home_score = outcome_record['actual_result']['home_score']
            away_score = outcome_record['actual_result']['away_score']

            actual_winner = 'home' if home_score > away_score else 'away'
            predicted_winner = 'home' if expert_pred['win_probability'] > 0.5 else 'away'

            was_correct = (actual_winner == predicted_winner)

            # Categorize by week
            week = pred_record['week']
            if week <= 8:  # Early season
                early_season_total += 1
                if was_correct:
                    early_season_correct += 1
            else:  # Late season
                late_season_total += 1
                if was_correct:
                    late_season_correct += 1

        # Calculate context accuracies
        if early_season_total > 0:
            context_performance['early_season'] = early_season_correct / early_season_total

        if late_season_total > 0:
            context_performance['late_season'] = late_season_correct / late_season_total

        return context_performance

    def _perform_comparative_analysis(self, season: int, expert_curves: Dict[str, ExpertLearningCurve]) -> LearningAnalysis:
        """Perform comparative analysis across all experts"""

        # Find best and worst learners
        learners_by_improvement = sorted(
            expert_curves.items(),
            key=lambda x: x[1].accuracy_improvement,
            reverse=True
        )

        best_learners = [expert_id for expert_id, _ in learners_by_improvement[:3]]
        worst_learners = [expert_id for expert_id, _ in learners_by_improvement[-3:]]

        # Find most stable and volatile experts
        experts_by_stability = sorted(
            expert_curves.items(),
            key=lambda x: x[1].confidence_stability,
            reverse=True
        )

        most_stable = [expert_id for expert_id, _ in experts_by_stability[:3]]
        most_volatile = [expert_id for expert_id, _ in experts_by_stability[-3:]]

        # Analyze context specialists
        context_specialists = self._identify_context_specialists(expert_curves)

        # Calculate overall system metrics
        overall_trend = self._calculate_overall_learning_trend(expert_curves)
        effectiveness_score = self._calculate_learning_effectiveness(expert_curves)

        return LearningAnalysis(
            season=season,
            total_games=len(self.predictions_data),
            expert_curves=expert_curves,
            best_learners=best_learners,
            worst_learners=worst_learners,
            most_stable=most_stable,
            most_volatile=most_volatile,
            context_specialists=context_specialists,
            overall_learning_trend=overall_trend,
            learning_effectiveness_score=effectiveness_score
        )

    def _identify_context_specialists(self, expert_curves: Dict[str, ExpertLearningCurve]) -> Dict[str, List[str]]:
        """Identify experts who specialize in different contexts"""
        context_specialists = {
            'early_season': [],
            'late_season': []
        }

        for expert_id, curve in expert_curves.items():
            context_perf = curve.context_performance

            # Check for early season specialists
            if (context_perf.get('early_season', 0) > 0.55 and
                context_perf.get('early_season', 0) > context_perf.get('late_season', 0) + 0.05):
                context_specialists['early_season'].append(expert_id)

            # Check for late season specialists
            if (context_perf.get('late_season', 0) > 0.55 and
                context_perf.get('late_season', 0) > context_perf.get('early_season', 0) + 0.05):
                context_specialists['late_season'].append(expert_id)

        return context_specialists

    def _calculate_overall_learning_trend(self, expert_curves: Dict[str, ExpertLearningCurve]) -> str:
        """Calculate overall system learning trend"""
        improving_count = sum(1 for curve in expert_curves.values() if curve.learning_trend == 'improving')
        declining_count = sum(1 for curve in expert_curves.values() if curve.learning_trend == 'declining')

        if improving_count > declining_count * 1.5:
            return 'system_improving'
        elif declining_count > improving_count * 1.5:
            return 'system_declining'
        else:
            return 'system_stable'

    def _calculate_learning_effectiveness(self, expert_curves: Dict[str, ExpertLearningCurve]) -> float:
        """Calculate overall learning effectiveness score"""
        if not expert_curves:
            return 0.0

        # Average improvement across all experts
        avg_improvement = np.mean([curve.accuracy_improvement for curve in expert_curves.values()])

        # Percentage of experts showing improvement
        improving_pct = sum(1 for curve in expert_curves.values() if curve.accuracy_improvement > 0) / len(expert_curves)

        # Average stability
        avg_stability = np.mean([curve.confidence_stability for curve in expert_curves.values()])

        # Combine metrics (weighted average)
        effectiveness = (avg_improvement * 0.4 + improving_pct * 0.4 + avg_stability * 0.2)

        return max(0.0, min(1.0, effectiveness))

    def _save_learning_analysis(self, analysis: LearningAnalysis):
        """Save learning analysis results"""
        output_file = self.results_dir / "expert_learning_analysis.json"

        # Convert to serializable format
        analysis_data = {
            'season': analysis.season,
            'total_games': analysis.total_games,
            'analysis_timestamp': datetime.now().isoformat(),

            'expert_curves': {
                expert_id: {
                    'expert_type': curve.expert_type.value,
                    'initial_accuracy': curve.initial_accuracy,
                    'final_accuracy': curve.final_accuracy,
                    'accuracy_improvement': curve.accuracy_improvement,
                    'learning_trend': curve.learning_trend,
                    'confidence_stability': curve.confidence_stability,
                    'personality_drift_score': curve.personality_drift_score,
                    'context_performance': curve.context_performance,
                    'total_predictions': len(curve.curve_points)
                }
                for expert_id, curve in analysis.expert_curves.items()
            },

            'comparative_analysis': {
                'best_learners': analysis.best_learners,
                'worst_learners': analysis.worst_learners,
                'most_stable': analysis.most_stable,
                'most_volatile': analysis.most_volatile,
                'context_specialists': analysis.context_specialists
            },

            'system_metrics': {
                'overall_learning_trend': analysis.overall_learning_trend,
                'learning_effectiveness_score': analysis.learning_effectiveness_score
            }
        }

        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)

        logger.info(f"💾 Learning analysis saved to {output_file}")

    def generate_learning_report(self, analysis: LearningAnalysis) -> str:
        """Generate human-readable learning analysis report"""
        report_lines = [
            f"Expert Learning Analysis Report - Season {analysis.season}",
            "=" * 60,
            "",
            f"📊 Overview:",
            f"   Total Games Analyzed: {analysis.total_games}",
            f"   Total Experts: {len(analysis.expert_curves)}",
            f"   Overall Learning Trend: {analysis.overall_learning_trend}",
            f"   Learning Effectiveness Score: {analysis.learning_effectiveness_score:.3f}",
            "",
            f"🏆 Best Learners (Most Improved):",
        ]

        for expert_id in analysis.best_learners:
            curve = analysis.expert_curves[expert_id]
            report_lines.append(f"   • {expert_id}: {curve.accuracy_improvement:+.1%} improvement ({curve.initial_accuracy:.1%} → {curve.final_accuracy:.1%})")

        report_lines.extend([
            "",
            f"📉 Worst Learners (Most Declined):",
        ])

        for expert_id in analysis.worst_learners:
            curve = analysis.expert_curves[expert_id]
            report_lines.append(f"   • {expert_id}: {curve.accuracy_improvement:+.1%} change ({curve.initial_accuracy:.1%} → {curve.final_accuracy:.1%})")

        report_lines.extend([
            "",
            f"🎯 Most Stable Experts:",
        ])

        for expert_id in analysis.most_stable:
            curve = analysis.expert_curves[expert_id]
            report_lines.append(f"   • {expert_id}: {curve.confidence_stability:.3f} stability score")

        report_lines.extend([
            "",
            f"📈 Context Specialists:",
        ])

        for context, specialists in analysis.context_specialists.items():
            if specialists:
                report_lines.append(f"   {context.replace('_', ' ').title()}: {', '.join(specialists)}")

        # Add detailed expert analysis
        report_lines.extend([
            "",
            f"📋 Detailed Expert Analysis:",
            ""
        ])

        for expert_id, curve in sorted(analysis.expert_curves.items()):
            report_lines.extend([
                f"Expert: {expert_id}",
                f"   Learning Trend: {curve.learning_trend}",
                f"   Accuracy Change: {curve.initial_accuracy:.1%} → {curve.final_accuracy:.1%} ({curve.accuracy_improvement:+.1%})",
                f"   Confidence Stability: {curve.confidence_stability:.3f}",
                f"   Personality Drift: {curve.personality_drift_score:.3f}",
                f"   Context Performance: {curve.context_performance}",
                ""
            ])

        return "\n".join(report_lines)


async def main():
    """Test the Expert Learning Analyzer"""
    print("📈 Expert Learning Curve Analyzer Test")
    print("=" * 60)

    analyzer = ExpertLearningAnalyzer()

    try:
        # Analyze learning curves for 2020 season
        analysis = analyzer.analyze_learning_curves(2020)

        # Generate and display report
        report = analyzer.generate_learning_report(analysis)
        print(report)

        print(f"\n✅ Learning analysis completed!")
        print(f"📁 Detailed results saved to: 2020_season_results/expert_learning_analysis.json")

    except Exception as e:
        print(f"❌ Learning analysis failed: {e}")
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
