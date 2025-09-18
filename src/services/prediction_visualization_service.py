"""
Prediction Visualization Service

Transforms comprehensive expert prediction verification data into chart-ready formats
for visual dashboards. Provides data for:

- Expert performance leaderboards
- Prediction vs reality comparisons
- Accuracy heatmaps across categories
- Confidence calibration analysis
- Historical trends and insights
- Game-by-game breakdowns

Integrates with enhanced_data_storage and comprehensive_verification_service
to provide rich visualizations of the expert prediction system.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics
from decimal import Decimal
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

from .enhanced_data_storage import EnhancedDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExpertPerformanceData:
    """Expert performance data for visualizations"""
    expert_id: str
    expert_name: str
    overall_accuracy: float
    weighted_accuracy: float
    confidence_calibration: float
    total_predictions: int
    correct_predictions: int
    games_analyzed: int
    category_accuracies: Dict[str, float]
    recent_trend: str  # "improving", "declining", "stable"
    strengths: List[str]
    weaknesses: List[str]
    last_updated: str

@dataclass
class GameAnalysisData:
    """Game analysis data for visualization"""
    game_id: str
    game_title: str
    game_date: str
    home_team: str
    away_team: str
    final_score: str
    expert_predictions: Dict[str, Dict[str, Any]]
    actual_outcomes: Dict[str, Any]
    verification_results: Dict[str, Dict[str, Any]]
    prediction_accuracy_summary: Dict[str, float]
    surprise_factor: float
    game_context: Dict[str, Any]

@dataclass
class CategoryPerformanceData:
    """Category performance across all experts"""
    category: str
    category_display_name: str
    overall_accuracy: float
    expert_accuracies: Dict[str, float]
    difficulty_score: float
    prediction_count: int
    best_expert: str
    worst_expert: str
    accuracy_variance: float

class PredictionVisualizationService:
    """Transforms prediction data into visualization-ready formats"""

    def __init__(self, storage: EnhancedDataStorage):
        self.storage = storage

        # Display names for prediction categories
        self.category_display_names = {
            "winner": "Game Winner",
            "final_score": "Final Score",
            "home_score": "Home Score",
            "away_score": "Away Score",
            "margin": "Victory Margin",
            "predicted_total": "Total Points",
            "spread_pick": "Spread Pick",
            "total_pick": "Over/Under",
            "moneyline_pick": "Moneyline",
            "coaching_advantage": "Coaching Edge",
            "special_teams_edge": "Special Teams",
            "home_field_impact": "Home Field Advantage",
            "drive_outcome": "Drive Outcomes",
            "next_score_prob": "Next Score Probability"
        }

        # Expert display names
        self.expert_display_names = {
            "the_analyst": "The Analyst",
            "pattern_hunter": "Pattern Hunter",
            "contrarian_voice": "Contrarian Voice",
            "momentum_tracker": "Momentum Tracker",
            "clutch_specialist": "Clutch Specialist",
            "weather_guru": "Weather Guru",
            "coaching_scout": "Coaching Scout",
            "injury_tracker": "Injury Tracker",
            "value_finder": "Value Finder",
            "home_field_expert": "Home Field Expert",
            "divisional_specialist": "Divisional Specialist",
            "primetime_predictor": "Primetime Predictor",
            "upset_detector": "Upset Detector",
            "line_movement_tracker": "Line Movement Tracker",
            "chaos_theorist": "Chaos Theorist"
        }

    async def get_expert_performance_dashboard_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive expert performance data for dashboard"""
        logger.info(f"Generating expert performance dashboard data for last {days_back} days")

        try:
            # Get expert performance data
            expert_performances = await self._get_expert_performance_data(days_back)

            # Get category performance data
            category_performances = await self._get_category_performance_data(days_back)

            # Get recent games summary
            recent_games = await self._get_recent_games_summary(days_back)

            # Generate expert leaderboard
            expert_leaderboard = self._generate_expert_leaderboard(expert_performances)

            # Generate accuracy heatmap data
            accuracy_heatmap = self._generate_accuracy_heatmap(expert_performances)

            # Generate confidence calibration data
            confidence_calibration = await self._generate_confidence_calibration_data(days_back)

            # Generate performance trends
            performance_trends = await self._generate_performance_trends(days_back)

            dashboard_data = {
                "summary": {
                    "total_experts": len(expert_performances),
                    "total_games": len(recent_games),
                    "average_accuracy": statistics.mean([ep.overall_accuracy for ep in expert_performances]) if expert_performances else 0,
                    "best_expert": expert_leaderboard[0]["expert_name"] if expert_leaderboard else "None",
                    "most_accurate_category": max(category_performances, key=lambda x: x.overall_accuracy).category_display_name if category_performances else "None",
                    "last_updated": datetime.now(timezone.utc).isoformat()
                },
                "expert_leaderboard": expert_leaderboard,
                "accuracy_heatmap": accuracy_heatmap,
                "category_performance": [asdict(cp) for cp in category_performances],
                "confidence_calibration": confidence_calibration,
                "performance_trends": performance_trends,
                "recent_games": recent_games
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {}

    async def get_game_analysis_data(self, game_id: str) -> Dict[str, Any]:
        """Get detailed game analysis data for visualization"""
        logger.info(f"Generating game analysis data for {game_id}")

        try:
            # Get game verification data
            game_data = await self.storage.get_game_verification_data(game_id)

            if not game_data or not game_data.get("game_data"):
                return {}

            # Get expert predictions and verification results
            expert_predictions = await self._get_expert_predictions_for_game(game_id)
            verification_results = await self._get_verification_results_for_game(game_id)

            # Process game analysis
            game_analysis = await self._process_game_analysis(
                game_id, game_data, expert_predictions, verification_results
            )

            return asdict(game_analysis) if game_analysis else {}

        except Exception as e:
            logger.error(f"Error generating game analysis data: {e}")
            return {}

    async def get_prediction_comparison_data(self, game_ids: List[str]) -> Dict[str, Any]:
        """Get prediction vs reality comparison data for multiple games"""
        logger.info(f"Generating prediction comparison data for {len(game_ids)} games")

        comparison_data = {
            "games": [],
            "expert_summary": {},
            "category_summary": {},
            "accuracy_distribution": {}
        }

        try:
            for game_id in game_ids:
                game_analysis = await self.get_game_analysis_data(game_id)
                if game_analysis:
                    comparison_data["games"].append(game_analysis)

            # Generate summary statistics
            if comparison_data["games"]:
                comparison_data["expert_summary"] = self._generate_expert_summary(comparison_data["games"])
                comparison_data["category_summary"] = self._generate_category_summary(comparison_data["games"])
                comparison_data["accuracy_distribution"] = self._generate_accuracy_distribution(comparison_data["games"])

            return comparison_data

        except Exception as e:
            logger.error(f"Error generating comparison data: {e}")
            return comparison_data

    async def _get_expert_performance_data(self, days_back: int) -> List[ExpertPerformanceData]:
        """Get expert performance data from database"""
        expert_performances = []

        try:
            async with self.storage.pool.acquire() as conn:
                # Get expert performance from verification results
                query = """
                SELECT
                    epv.expert_id,
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN epv.is_correct THEN 1 ELSE 0 END) as correct_predictions,
                    AVG(epv.accuracy_score) as avg_accuracy,
                    AVG(epv.confidence_score) as avg_confidence,
                    COUNT(DISTINCT epv.game_id) as games_analyzed,
                    json_object_agg(epv.prediction_category, AVG(epv.accuracy_score)) as category_accuracies
                FROM expert_prediction_verification epv
                JOIN enhanced_game_data egd ON epv.game_id = egd.game_id
                WHERE egd.game_date >= NOW() - INTERVAL '%s days'
                GROUP BY epv.expert_id
                """ % days_back

                results = await conn.fetch(query)

                for row in results:
                    expert_id = row["expert_id"]

                    # Calculate metrics
                    overall_accuracy = float(row["avg_accuracy"]) if row["avg_accuracy"] else 0.0
                    confidence_calibration = self._calculate_confidence_calibration(
                        float(row["avg_confidence"]) if row["avg_confidence"] else 0.5,
                        overall_accuracy
                    )

                    # Parse category accuracies
                    category_accuracies = {}
                    if row["category_accuracies"]:
                        for category, accuracy in row["category_accuracies"].items():
                            if accuracy is not None:
                                category_accuracies[category] = float(accuracy)

                    # Determine strengths and weaknesses
                    strengths, weaknesses = self._analyze_expert_strengths_weaknesses(category_accuracies)

                    # Calculate recent trend (placeholder - would need historical data)
                    recent_trend = "stable"

                    expert_performance = ExpertPerformanceData(
                        expert_id=expert_id,
                        expert_name=self.expert_display_names.get(expert_id, expert_id.replace("_", " ").title()),
                        overall_accuracy=overall_accuracy,
                        weighted_accuracy=overall_accuracy,  # Would calculate weighted based on category importance
                        confidence_calibration=confidence_calibration,
                        total_predictions=row["total_predictions"],
                        correct_predictions=row["correct_predictions"],
                        games_analyzed=row["games_analyzed"],
                        category_accuracies=category_accuracies,
                        recent_trend=recent_trend,
                        strengths=strengths,
                        weaknesses=weaknesses,
                        last_updated=datetime.now(timezone.utc).isoformat()
                    )

                    expert_performances.append(expert_performance)

        except Exception as e:
            logger.error(f"Error getting expert performance data: {e}")

        return expert_performances

    async def _get_category_performance_data(self, days_back: int) -> List[CategoryPerformanceData]:
        """Get category performance data across all experts"""
        category_performances = []

        try:
            async with self.storage.pool.acquire() as conn:
                query = """
                SELECT
                    epv.prediction_category,
                    COUNT(*) as prediction_count,
                    AVG(epv.accuracy_score) as avg_accuracy,
                    STDDEV(epv.accuracy_score) as accuracy_variance,
                    json_object_agg(epv.expert_id, AVG(epv.accuracy_score)) as expert_accuracies
                FROM expert_prediction_verification epv
                JOIN enhanced_game_data egd ON epv.game_id = egd.game_id
                WHERE egd.game_date >= NOW() - INTERVAL '%s days'
                GROUP BY epv.prediction_category
                """ % days_back

                results = await conn.fetch(query)

                for row in results:
                    category = row["prediction_category"]

                    # Parse expert accuracies
                    expert_accuracies = {}
                    if row["expert_accuracies"]:
                        for expert_id, accuracy in row["expert_accuracies"].items():
                            if accuracy is not None:
                                expert_accuracies[expert_id] = float(accuracy)

                    # Find best and worst experts
                    best_expert = max(expert_accuracies.items(), key=lambda x: x[1])[0] if expert_accuracies else "None"
                    worst_expert = min(expert_accuracies.items(), key=lambda x: x[1])[0] if expert_accuracies else "None"

                    # Calculate difficulty score (inverse of average accuracy)
                    avg_accuracy = float(row["avg_accuracy"]) if row["avg_accuracy"] else 0.0
                    difficulty_score = 1.0 - avg_accuracy

                    category_performance = CategoryPerformanceData(
                        category=category,
                        category_display_name=self.category_display_names.get(category, category.replace("_", " ").title()),
                        overall_accuracy=avg_accuracy,
                        expert_accuracies=expert_accuracies,
                        difficulty_score=difficulty_score,
                        prediction_count=row["prediction_count"],
                        best_expert=self.expert_display_names.get(best_expert, best_expert),
                        worst_expert=self.expert_display_names.get(worst_expert, worst_expert),
                        accuracy_variance=float(row["accuracy_variance"]) if row["accuracy_variance"] else 0.0
                    )

                    category_performances.append(category_performance)

        except Exception as e:
            logger.error(f"Error getting category performance data: {e}")

        return category_performances

    async def _get_recent_games_summary(self, days_back: int) -> List[Dict[str, Any]]:
        """Get summary of recent games"""
        games_summary = []

        try:
            async with self.storage.pool.acquire() as conn:
                query = """
                SELECT
                    egd.game_id,
                    egd.home_team,
                    egd.away_team,
                    egd.final_score_home,
                    egd.final_score_away,
                    egd.game_date,
                    COUNT(epv.id) as predictions_count,
                    AVG(epv.accuracy_score) as avg_accuracy
                FROM enhanced_game_data egd
                LEFT JOIN expert_prediction_verification epv ON egd.game_id = epv.game_id
                WHERE egd.game_date >= NOW() - INTERVAL '%s days'
                AND egd.final_score_home IS NOT NULL
                GROUP BY egd.game_id, egd.home_team, egd.away_team, egd.final_score_home, egd.final_score_away, egd.game_date
                ORDER BY egd.game_date DESC
                """ % days_back

                results = await conn.fetch(query)

                for row in results:
                    game_summary = {
                        "game_id": row["game_id"],
                        "title": f"{row['away_team']} @ {row['home_team']}",
                        "final_score": f"{row['away_team']} {row['final_score_away']} - {row['home_team']} {row['final_score_home']}",
                        "game_date": row["game_date"].isoformat() if row["game_date"] else None,
                        "predictions_count": row["predictions_count"] or 0,
                        "avg_accuracy": float(row["avg_accuracy"]) if row["avg_accuracy"] else 0.0
                    }
                    games_summary.append(game_summary)

        except Exception as e:
            logger.error(f"Error getting recent games summary: {e}")

        return games_summary

    def _generate_expert_leaderboard(self, expert_performances: List[ExpertPerformanceData]) -> List[Dict[str, Any]]:
        """Generate expert leaderboard for visualization"""
        # Sort experts by weighted accuracy
        sorted_experts = sorted(expert_performances, key=lambda x: x.weighted_accuracy, reverse=True)

        leaderboard = []
        for rank, expert in enumerate(sorted_experts, 1):
            leaderboard_entry = {
                "rank": rank,
                "expert_id": expert.expert_id,
                "expert_name": expert.expert_name,
                "overall_accuracy": round(expert.overall_accuracy * 100, 1),
                "weighted_accuracy": round(expert.weighted_accuracy * 100, 1),
                "confidence_calibration": round(expert.confidence_calibration * 100, 1),
                "total_predictions": expert.total_predictions,
                "correct_predictions": expert.correct_predictions,
                "games_analyzed": expert.games_analyzed,
                "recent_trend": expert.recent_trend,
                "strengths": expert.strengths[:3],  # Top 3 strengths
                "weaknesses": expert.weaknesses[:3],  # Top 3 weaknesses
                "trend_icon": self._get_trend_icon(expert.recent_trend)
            }
            leaderboard.append(leaderboard_entry)

        return leaderboard

    def _generate_accuracy_heatmap(self, expert_performances: List[ExpertPerformanceData]) -> Dict[str, Any]:
        """Generate accuracy heatmap data"""
        # Get all categories
        all_categories = set()
        for expert in expert_performances:
            all_categories.update(expert.category_accuracies.keys())

        # Create heatmap matrix
        heatmap_data = {
            "experts": [expert.expert_name for expert in expert_performances],
            "categories": [self.category_display_names.get(cat, cat.replace("_", " ").title()) for cat in sorted(all_categories)],
            "accuracy_matrix": [],
            "colorscale": [
                [0, '#ff4444'],      # Red for poor accuracy
                [0.3, '#ffaa44'],    # Orange for below average
                [0.5, '#ffff44'],    # Yellow for average
                [0.7, '#aaff44'],    # Light green for good
                [1.0, '#44ff44']     # Green for excellent
            ]
        }

        # Fill accuracy matrix
        for expert in expert_performances:
            expert_row = []
            for category in sorted(all_categories):
                accuracy = expert.category_accuracies.get(category, 0.0)
                expert_row.append(round(accuracy * 100, 1))
            heatmap_data["accuracy_matrix"].append(expert_row)

        return heatmap_data

    async def _generate_confidence_calibration_data(self, days_back: int) -> Dict[str, Any]:
        """Generate confidence calibration visualization data"""
        calibration_data = {
            "scatter_data": [],
            "calibration_line": {"x": [0, 100], "y": [0, 100]},
            "expert_colors": {}
        }

        try:
            async with self.storage.pool.acquire() as conn:
                query = """
                SELECT
                    epv.expert_id,
                    epv.confidence_score,
                    epv.accuracy_score
                FROM expert_prediction_verification epv
                JOIN enhanced_game_data egd ON epv.game_id = egd.game_id
                WHERE egd.game_date >= NOW() - INTERVAL '%s days'
                AND epv.confidence_score IS NOT NULL
                """ % days_back

                results = await conn.fetch(query)

                # Group by expert
                expert_data = {}
                for row in results:
                    expert_id = row["expert_id"]
                    if expert_id not in expert_data:
                        expert_data[expert_id] = {"confidence": [], "accuracy": []}

                    expert_data[expert_id]["confidence"].append(float(row["confidence_score"]) * 100)
                    expert_data[expert_id]["accuracy"].append(float(row["accuracy_score"]) * 100)

                # Create scatter plot data
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                for i, (expert_id, data) in enumerate(expert_data.items()):
                    expert_name = self.expert_display_names.get(expert_id, expert_id.replace("_", " ").title())
                    color = colors[i % len(colors)]

                    calibration_data["scatter_data"].append({
                        "x": data["confidence"],
                        "y": data["accuracy"],
                        "name": expert_name,
                        "mode": "markers",
                        "marker": {"color": color, "size": 8, "opacity": 0.7}
                    })

                    calibration_data["expert_colors"][expert_name] = color

        except Exception as e:
            logger.error(f"Error generating confidence calibration data: {e}")

        return calibration_data

    async def _generate_performance_trends(self, days_back: int) -> Dict[str, Any]:
        """Generate performance trends over time"""
        trends_data = {
            "time_series": [],
            "trend_summary": {}
        }

        try:
            # For now, return placeholder data
            # In production, this would query historical performance data
            trends_data["trend_summary"] = {
                "improving_experts": ["The Analyst", "Pattern Hunter"],
                "declining_experts": ["Chaos Theorist"],
                "stable_experts": ["Momentum Tracker", "Weather Guru"]
            }

        except Exception as e:
            logger.error(f"Error generating performance trends: {e}")

        return trends_data

    async def _get_expert_predictions_for_game(self, game_id: str) -> Dict[str, Dict[str, Any]]:
        """Get expert predictions for a specific game"""
        # This would query the expert predictions database
        # For now, return empty dict as placeholder
        return {}

    async def _get_verification_results_for_game(self, game_id: str) -> Dict[str, Dict[str, Any]]:
        """Get verification results for a specific game"""
        try:
            async with self.storage.pool.acquire() as conn:
                query = """
                SELECT
                    expert_id,
                    prediction_category,
                    predicted_value,
                    actual_value,
                    is_correct,
                    accuracy_score,
                    confidence_score
                FROM expert_prediction_verification
                WHERE game_id = $1
                """

                results = await conn.fetch(query, game_id)

                verification_data = {}
                for row in results:
                    expert_id = row["expert_id"]
                    if expert_id not in verification_data:
                        verification_data[expert_id] = {}

                    verification_data[expert_id][row["prediction_category"]] = {
                        "predicted": row["predicted_value"],
                        "actual": row["actual_value"],
                        "correct": row["is_correct"],
                        "accuracy": float(row["accuracy_score"]),
                        "confidence": float(row["confidence_score"]) if row["confidence_score"] else None
                    }

                return verification_data

        except Exception as e:
            logger.error(f"Error getting verification results: {e}")
            return {}

    async def _process_game_analysis(self, game_id: str, game_data: Dict[str, Any],
                                   expert_predictions: Dict[str, Dict[str, Any]],
                                   verification_results: Dict[str, Dict[str, Any]]) -> Optional[GameAnalysisData]:
        """Process game data into analysis format"""
        try:
            enhanced_game = game_data.get("game_data", {})

            # Create game analysis object
            game_analysis = GameAnalysisData(
                game_id=game_id,
                game_title=f"{enhanced_game.get('away_team', 'AWAY')} @ {enhanced_game.get('home_team', 'HOME')}",
                game_date=enhanced_game.get("game_date", "").isoformat() if enhanced_game.get("game_date") else "",
                home_team=enhanced_game.get("home_team", ""),
                away_team=enhanced_game.get("away_team", ""),
                final_score=f"{enhanced_game.get('away_team', 'AWAY')} {enhanced_game.get('final_score_away', 0)} - {enhanced_game.get('home_team', 'HOME')} {enhanced_game.get('final_score_home', 0)}",
                expert_predictions=expert_predictions,
                actual_outcomes=self._extract_actual_outcomes(game_data),
                verification_results=verification_results,
                prediction_accuracy_summary=self._calculate_prediction_accuracy_summary(verification_results),
                surprise_factor=self._calculate_surprise_factor(expert_predictions, game_data),
                game_context=self._extract_game_context(enhanced_game)
            )

            return game_analysis

        except Exception as e:
            logger.error(f"Error processing game analysis: {e}")
            return None

    def _calculate_confidence_calibration(self, avg_confidence: float, avg_accuracy: float) -> float:
        """Calculate confidence calibration score"""
        return 1.0 - abs(avg_confidence - avg_accuracy)

    def _analyze_expert_strengths_weaknesses(self, category_accuracies: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """Analyze expert strengths and weaknesses"""
        if not category_accuracies:
            return [], []

        # Sort categories by accuracy
        sorted_categories = sorted(category_accuracies.items(), key=lambda x: x[1], reverse=True)

        # Top categories are strengths, bottom are weaknesses
        strengths = [self.category_display_names.get(cat, cat.replace("_", " ").title())
                    for cat, acc in sorted_categories[:3] if acc > 0.6]
        weaknesses = [self.category_display_names.get(cat, cat.replace("_", " ").title())
                     for cat, acc in sorted_categories[-3:] if acc < 0.4]

        return strengths, weaknesses

    def _get_trend_icon(self, trend: str) -> str:
        """Get trend icon for visualization"""
        trend_icons = {
            "improving": "📈",
            "declining": "📉",
            "stable": "➡️"
        }
        return trend_icons.get(trend, "➡️")

    def _extract_actual_outcomes(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actual outcomes from game data"""
        enhanced_game = game_data.get("game_data", {})
        return {
            "winner": enhanced_game.get("home_team") if enhanced_game.get("final_score_home", 0) > enhanced_game.get("final_score_away", 0) else enhanced_game.get("away_team"),
            "home_score": enhanced_game.get("final_score_home", 0),
            "away_score": enhanced_game.get("final_score_away", 0),
            "total_points": enhanced_game.get("final_score_home", 0) + enhanced_game.get("final_score_away", 0)
        }

    def _calculate_prediction_accuracy_summary(self, verification_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate summary accuracy statistics"""
        if not verification_results:
            return {}

        all_accuracies = []
        for expert_results in verification_results.values():
            for category_result in expert_results.values():
                all_accuracies.append(category_result.get("accuracy", 0.0))

        return {
            "mean_accuracy": statistics.mean(all_accuracies) if all_accuracies else 0.0,
            "median_accuracy": statistics.median(all_accuracies) if all_accuracies else 0.0,
            "accuracy_range": max(all_accuracies) - min(all_accuracies) if all_accuracies else 0.0
        }

    def _calculate_surprise_factor(self, expert_predictions: Dict[str, Dict[str, Any]], game_data: Dict[str, Any]) -> float:
        """Calculate how surprising the game outcome was"""
        # Placeholder implementation
        return 0.3

    def _extract_game_context(self, enhanced_game: Dict[str, Any]) -> Dict[str, Any]:
        """Extract game context for visualization"""
        return {
            "weather": enhanced_game.get("weather_condition"),
            "temperature": enhanced_game.get("weather_temperature"),
            "stadium": enhanced_game.get("stadium_name"),
            "attendance": enhanced_game.get("attendance"),
            "overtime": enhanced_game.get("overtime_periods", 0) > 0
        }

    def _generate_expert_summary(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate expert summary across multiple games"""
        return {"placeholder": "expert_summary"}

    def _generate_category_summary(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate category summary across multiple games"""
        return {"placeholder": "category_summary"}

    def _generate_accuracy_distribution(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate accuracy distribution data"""
        return {"placeholder": "accuracy_distribution"}

# Example usage and testing
async def main():
    """Test the visualization service"""
    from .enhanced_data_storage import EnhancedDataStorage

    # Initialize storage
    database_url = "postgresql://localhost/nfl_predictor"
    storage = EnhancedDataStorage(database_url)
    await storage.initialize()

    # Initialize visualization service
    viz_service = PredictionVisualizationService(storage)

    # Test dashboard data generation
    dashboard_data = await viz_service.get_expert_performance_dashboard_data(days_back=30)
    print(f"Generated dashboard data with {len(dashboard_data.get('expert_leaderboard', []))} experts")

    # Test game analysis
    test_game_id = "test_game_123"
    game_analysis = await viz_service.get_game_analysis_data(test_game_id)
    if game_analysis:
        print(f"Generated game analysis for {game_analysis.get('game_title', 'Unknown Game')}")

    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())