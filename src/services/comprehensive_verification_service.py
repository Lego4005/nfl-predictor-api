"""
Comprehensive Expert Prediction Verification Service

Uses enhanced NFL game data to verify all dimensions of expert predictions:
- Winner predictions
- Score predictions (exact, margin, total)
- Spread and total predictions
- Coaching advantage analysis
- Special teams edge verification
- Live game predictions
- Drive outcome predictions
- Situational performance verification

Integrates with reasoning chain logger, belief revision service, and episodic memory
to provide comprehensive learning feedback for the expert system.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from .enhanced_data_storage import EnhancedDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """Result of expert prediction verification"""
    expert_id: str
    game_id: str
    category: str
    predicted_value: Any
    actual_value: Any
    is_correct: bool
    accuracy_score: float
    confidence_score: float
    verification_method: str
    supporting_data: Dict[str, Any]

@dataclass
class ComprehensiveAccuracy:
    """Comprehensive accuracy across all prediction dimensions"""
    expert_id: str
    game_id: str
    total_predictions: int
    correct_predictions: int
    overall_accuracy: float
    category_accuracies: Dict[str, float]
    weighted_accuracy: float
    confidence_calibration: float
    prediction_distribution: Dict[str, int]

class ComprehensiveVerificationService:
    """Verifies expert predictions across all dimensions using enhanced data"""

    def __init__(self, storage: EnhancedDataStorage):
        self.storage = storage

        # Verification weights for different prediction categories
        self.category_weights = {
            "winner": 1.0,
            "final_score": 0.8,
            "home_score": 0.6,
            "away_score": 0.6,
            "margin": 0.7,
            "predicted_total": 0.7,
            "spread_pick": 0.9,
            "total_pick": 0.8,
            "moneyline_pick": 1.0,
            "coaching_advantage": 0.6,
            "special_teams_edge": 0.5,
            "home_field_impact": 0.4,
            "drive_outcome": 0.3,
            "next_score_prob": 0.4
        }

    async def verify_all_expert_predictions(self, game_id: str, expert_predictions: Dict[str, Dict[str, Any]]) -> Dict[str, ComprehensiveAccuracy]:
        """Verify predictions for all experts for a game"""
        logger.info(f"Verifying predictions for {len(expert_predictions)} experts for game {game_id}")

        verification_results = {}

        try:
            # Get comprehensive game data
            game_data = await self.storage.get_game_verification_data(game_id)

            if not game_data or not game_data.get("game_data"):
                logger.error(f"No game data found for {game_id}")
                return {}

            # Extract actual outcomes
            actual_outcomes = await self._extract_comprehensive_outcomes(game_id, game_data)

            # Verify each expert
            for expert_id, predictions in expert_predictions.items():
                try:
                    accuracy = await self._verify_expert_comprehensive(
                        expert_id, game_id, predictions, actual_outcomes, game_data
                    )
                    verification_results[expert_id] = accuracy

                except Exception as e:
                    logger.error(f"Error verifying expert {expert_id}: {e}")

            logger.info(f"Completed verification for {len(verification_results)} experts")

        except Exception as e:
            logger.error(f"Error in comprehensive verification: {e}")

        return verification_results

    async def _verify_expert_comprehensive(self, expert_id: str, game_id: str,
                                        predictions: Dict[str, Any], actual_outcomes: Dict[str, Any],
                                        game_data: Dict[str, Any]) -> ComprehensiveAccuracy:
        """Verify all predictions for a single expert"""

        verification_results = []
        category_accuracies = {}

        # Verify each prediction category
        for category, predicted_value in predictions.items():
            if category.endswith('_confidence'):
                continue  # Skip confidence scores

            if category in actual_outcomes:
                actual_value = actual_outcomes[category]

                # Calculate accuracy for this category
                is_correct, accuracy_score = self._calculate_category_accuracy(
                    category, predicted_value, actual_value
                )

                # Get confidence score
                confidence_key = f"{category}_confidence"
                confidence_score = predictions.get(confidence_key, 0.5)

                # Get verification method
                verification_method = self._get_verification_method(category)

                # Create verification result
                result = VerificationResult(
                    expert_id=expert_id,
                    game_id=game_id,
                    category=category,
                    predicted_value=predicted_value,
                    actual_value=actual_value,
                    is_correct=is_correct,
                    accuracy_score=accuracy_score,
                    confidence_score=confidence_score,
                    verification_method=verification_method,
                    supporting_data=self._get_supporting_data(category, game_data)
                )

                verification_results.append(result)
                category_accuracies[category] = accuracy_score

        # Calculate comprehensive accuracy metrics
        total_predictions = len(verification_results)
        correct_predictions = sum(1 for r in verification_results if r.is_correct)
        overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0

        # Calculate weighted accuracy
        weighted_accuracy = self._calculate_weighted_accuracy(verification_results)

        # Calculate confidence calibration
        confidence_calibration = self._calculate_confidence_calibration(verification_results)

        # Calculate prediction distribution
        prediction_distribution = self._calculate_prediction_distribution(verification_results)

        # Store verification results in database
        await self._store_verification_results(verification_results)

        return ComprehensiveAccuracy(
            expert_id=expert_id,
            game_id=game_id,
            total_predictions=total_predictions,
            correct_predictions=correct_predictions,
            overall_accuracy=overall_accuracy,
            category_accuracies=category_accuracies,
            weighted_accuracy=weighted_accuracy,
            confidence_calibration=confidence_calibration,
            prediction_distribution=prediction_distribution
        )

    async def _extract_comprehensive_outcomes(self, game_id: str, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all possible actual outcomes from enhanced game data"""

        enhanced_game = game_data.get("game_data", {})
        coaching_decisions = game_data.get("coaching_decisions", [])
        special_teams = game_data.get("special_teams", [])
        situational = game_data.get("situational", [])

        outcomes = {}

        # Basic game outcomes
        if enhanced_game.get("final_score_home") is not None and enhanced_game.get("final_score_away") is not None:
            home_score = enhanced_game["final_score_home"]
            away_score = enhanced_game["final_score_away"]
            home_team = enhanced_game.get("home_team", "HOME")
            away_team = enhanced_game.get("away_team", "AWAY")

            outcomes.update({
                "home_score": home_score,
                "away_score": away_score,
                "final_score": f"{away_team} {away_score} - {home_team} {home_score}",
                "winner": home_team if home_score > away_score else away_team,
                "margin": abs(home_score - away_score),
                "predicted_total": home_score + away_score
            })

            # Moneyline pick (same as winner)
            outcomes["moneyline_pick"] = outcomes["winner"]

            # Home field impact calculation
            expected_home_advantage = 2.5  # Average home field advantage
            actual_margin = home_score - away_score
            outcomes["home_field_impact"] = actual_margin - expected_home_advantage

        # Spread and total outcomes (would need betting lines for full verification)
        # For now, use winner and score-based approximations
        if "winner" in outcomes:
            outcomes["spread_pick"] = outcomes["winner"]

        if "predicted_total" in outcomes:
            # Approximate total pick based on actual total vs average
            avg_total = 45  # NFL average
            outcomes["total_pick"] = "over" if outcomes["predicted_total"] > avg_total else "under"

        # Coaching advantage analysis
        coaching_advantage = await self._analyze_coaching_advantage(coaching_decisions, enhanced_game)
        if coaching_advantage:
            outcomes["coaching_advantage"] = coaching_advantage

        # Special teams edge analysis
        special_teams_edge = await self._analyze_special_teams_edge(special_teams)
        if special_teams_edge:
            outcomes["special_teams_edge"] = special_teams_edge

        # Drive outcome analysis (from play-by-play if available)
        drive_outcomes = await self._analyze_drive_outcomes(game_id)
        if drive_outcomes:
            outcomes.update(drive_outcomes)

        # Live game predictions (if available)
        live_outcomes = await self._analyze_live_game_outcomes(game_id)
        if live_outcomes:
            outcomes.update(live_outcomes)

        return outcomes

    async def _analyze_coaching_advantage(self, coaching_decisions: List[Dict], game_data: Dict) -> Optional[str]:
        """Analyze which team had the coaching advantage"""
        if not coaching_decisions:
            return None

        home_team = game_data.get("home_team")
        away_team = game_data.get("away_team")

        if not home_team or not away_team:
            return None

        # Calculate coaching decision quality scores
        home_quality_scores = []
        away_quality_scores = []

        for decision in coaching_decisions:
            team = decision.get("team")
            quality_score = decision.get("decision_quality_score")

            if quality_score is not None:
                if team == home_team:
                    home_quality_scores.append(float(quality_score))
                elif team == away_team:
                    away_quality_scores.append(float(quality_score))

        # Determine advantage based on average quality scores
        if home_quality_scores and away_quality_scores:
            home_avg = statistics.mean(home_quality_scores)
            away_avg = statistics.mean(away_quality_scores)

            if home_avg > away_avg:
                return home_team
            else:
                return away_team

        return None

    async def _analyze_special_teams_edge(self, special_teams: List[Dict]) -> Optional[str]:
        """Analyze which team had the special teams edge"""
        if not special_teams:
            return None

        best_team = None
        best_score = 0

        for st_data in special_teams:
            team = st_data.get("team")
            st_score = st_data.get("special_teams_score", 0) or 0

            if isinstance(st_score, (int, float, Decimal)) and st_score > best_score:
                best_score = float(st_score)
                best_team = team

        return best_team

    async def _analyze_drive_outcomes(self, game_id: str) -> Dict[str, Any]:
        """Analyze drive outcomes from enhanced data"""
        outcomes = {}

        try:
            async with self.storage.pool.acquire() as conn:
                # Get drive data
                drives = await conn.fetch(
                    "SELECT * FROM game_drives WHERE game_id = $1",
                    game_id
                )

                if drives:
                    # Calculate drive outcome probabilities
                    total_drives = len(drives)
                    touchdown_drives = sum(1 for d in drives if d["drive_result"] == "touchdown")
                    field_goal_drives = sum(1 for d in drives if d["drive_result"] == "field_goal")
                    punt_drives = sum(1 for d in drives if d["drive_result"] == "punt")
                    turnover_drives = sum(1 for d in drives if d["drive_result"] == "turnover")

                    outcomes["drive_outcome"] = {
                        "TD": touchdown_drives / total_drives if total_drives > 0 else 0,
                        "FG": field_goal_drives / total_drives if total_drives > 0 else 0,
                        "punt": punt_drives / total_drives if total_drives > 0 else 0,
                        "turnover": turnover_drives / total_drives if total_drives > 0 else 0
                    }

        except Exception as e:
            logger.error(f"Error analyzing drive outcomes: {e}")

        return outcomes

    async def _analyze_live_game_outcomes(self, game_id: str) -> Dict[str, Any]:
        """Analyze live game outcomes for real-time verification"""
        outcomes = {}

        try:
            async with self.storage.pool.acquire() as conn:
                # Get play-by-play for scoring analysis
                plays = await conn.fetch(
                    "SELECT * FROM game_play_by_play WHERE game_id = $1 AND (is_touchdown = true OR is_field_goal = true)",
                    game_id
                )

                if plays:
                    # Analyze scoring patterns for next score probability
                    teams = set()
                    for play in plays:
                        if play["possession_team"]:
                            teams.add(play["possession_team"])

                    if len(teams) == 2:
                        teams_list = list(teams)
                        team1_scores = sum(1 for p in plays if p["possession_team"] == teams_list[0])
                        team2_scores = sum(1 for p in plays if p["possession_team"] == teams_list[1])
                        total_scores = team1_scores + team2_scores

                        if total_scores > 0:
                            outcomes["next_score_prob"] = {
                                teams_list[0]: team1_scores / total_scores,
                                teams_list[1]: team2_scores / total_scores
                            }

        except Exception as e:
            logger.error(f"Error analyzing live game outcomes: {e}")

        return outcomes

    def _calculate_category_accuracy(self, category: str, predicted: Any, actual: Any) -> Tuple[bool, float]:
        """Calculate accuracy for a specific prediction category"""

        try:
            if category == "winner":
                is_correct = predicted == actual
                return is_correct, 1.0 if is_correct else 0.0

            elif category in ["final_score"]:
                # For final score strings, check if predicted winner is correct
                if isinstance(predicted, str) and isinstance(actual, str):
                    pred_parts = predicted.split(" - ")
                    actual_parts = actual.split(" - ")

                    if len(pred_parts) == 2 and len(actual_parts) == 2:
                        # Extract scores and compare winners
                        try:
                            pred_away = int(pred_parts[0].split()[-1])
                            pred_home = int(pred_parts[1].split()[-1])
                            actual_away = int(actual_parts[0].split()[-1])
                            actual_home = int(actual_parts[1].split()[-1])

                            pred_winner = "home" if pred_home > pred_away else "away"
                            actual_winner = "home" if actual_home > actual_away else "away"

                            is_correct = pred_winner == actual_winner

                            # Calculate accuracy based on score difference
                            pred_margin = abs(pred_home - pred_away)
                            actual_margin = abs(actual_home - actual_away)
                            margin_diff = abs(pred_margin - actual_margin)

                            accuracy = max(0.0, 1.0 - (margin_diff / 21.0))  # 21 point max difference
                            return is_correct, accuracy

                        except (ValueError, IndexError):
                            pass

                return predicted == actual, 1.0 if predicted == actual else 0.0

            elif category in ["home_score", "away_score", "margin", "predicted_total"]:
                if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                    diff = abs(predicted - actual)
                    max_diff = 21.0 if category in ["home_score", "away_score"] else 14.0
                    accuracy = max(0.0, 1.0 - (diff / max_diff))
                    is_correct = diff <= 3  # Within 3 points considered "correct"
                    return is_correct, accuracy
                else:
                    return predicted == actual, 1.0 if predicted == actual else 0.0

            elif category in ["spread_pick", "total_pick", "moneyline_pick", "coaching_advantage", "special_teams_edge"]:
                is_correct = predicted == actual
                return is_correct, 1.0 if is_correct else 0.0

            elif category == "home_field_impact":
                if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                    diff = abs(predicted - actual)
                    accuracy = max(0.0, 1.0 - (diff / 10.0))  # 10 point max difference
                    is_correct = diff <= 2
                    return is_correct, accuracy

            elif category == "drive_outcome":
                # Compare probability distributions
                if isinstance(predicted, dict) and isinstance(actual, dict):
                    total_diff = 0
                    for outcome in ["TD", "FG", "punt", "turnover"]:
                        pred_prob = predicted.get(outcome, 0)
                        actual_prob = actual.get(outcome, 0)
                        total_diff += abs(pred_prob - actual_prob)

                    accuracy = max(0.0, 1.0 - (total_diff / 2.0))  # Max diff is 2.0
                    is_correct = total_diff <= 0.4
                    return is_correct, accuracy

            elif category == "next_score_prob":
                # Compare team scoring probabilities
                if isinstance(predicted, dict) and isinstance(actual, dict):
                    total_diff = 0
                    for team in predicted.keys():
                        if team in actual:
                            pred_prob = predicted[team]
                            actual_prob = actual[team]
                            total_diff += abs(pred_prob - actual_prob)

                    accuracy = max(0.0, 1.0 - (total_diff / 2.0))
                    is_correct = total_diff <= 0.3
                    return is_correct, accuracy

            else:
                # Default exact match
                is_correct = predicted == actual
                return is_correct, 1.0 if is_correct else 0.0

        except Exception as e:
            logger.error(f"Error calculating accuracy for {category}: {e}")
            return False, 0.0

    def _get_verification_method(self, category: str) -> str:
        """Get verification method for a category"""
        if category in ["winner", "spread_pick", "total_pick", "moneyline_pick"]:
            return "exact_match"
        elif category in ["home_score", "away_score", "margin", "predicted_total"]:
            return "numerical_tolerance"
        elif category in ["drive_outcome", "next_score_prob"]:
            return "probability_distribution"
        else:
            return "statistical_analysis"

    def _get_supporting_data(self, category: str, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get supporting data for verification"""
        supporting_data = {"category": category}

        if category in ["winner", "home_score", "away_score"]:
            supporting_data.update({
                "final_score_home": game_data.get("game_data", {}).get("final_score_home"),
                "final_score_away": game_data.get("game_data", {}).get("final_score_away"),
                "home_team": game_data.get("game_data", {}).get("home_team"),
                "away_team": game_data.get("game_data", {}).get("away_team")
            })

        elif category == "coaching_advantage":
            supporting_data["coaching_decisions"] = game_data.get("coaching_decisions", [])

        elif category == "special_teams_edge":
            supporting_data["special_teams"] = game_data.get("special_teams", [])

        return supporting_data

    def _calculate_weighted_accuracy(self, verification_results: List[VerificationResult]) -> float:
        """Calculate weighted accuracy based on category importance"""
        if not verification_results:
            return 0.0

        total_weight = 0
        weighted_sum = 0

        for result in verification_results:
            weight = self.category_weights.get(result.category, 0.5)
            total_weight += weight
            weighted_sum += result.accuracy_score * weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_confidence_calibration(self, verification_results: List[VerificationResult]) -> float:
        """Calculate confidence calibration (how well confidence matches accuracy)"""
        if not verification_results:
            return 0.0

        calibration_errors = []

        for result in verification_results:
            confidence = result.confidence_score
            accuracy = result.accuracy_score
            calibration_error = abs(confidence - accuracy)
            calibration_errors.append(calibration_error)

        return 1.0 - (statistics.mean(calibration_errors) if calibration_errors else 0.0)

    def _calculate_prediction_distribution(self, verification_results: List[VerificationResult]) -> Dict[str, int]:
        """Calculate distribution of prediction categories"""
        distribution = {}

        for result in verification_results:
            category = result.category
            distribution[category] = distribution.get(category, 0) + 1

        return distribution

    async def _store_verification_results(self, verification_results: List[VerificationResult]):
        """Store verification results in database"""
        try:
            async with self.storage.pool.acquire() as conn:
                for result in verification_results:
                    # Get reasoning chain ID
                    reasoning_chain_id = await conn.fetchval(
                        "SELECT id FROM expert_reasoning_chains WHERE expert_id = $1 AND game_id = $2 ORDER BY created_at DESC LIMIT 1",
                        result.expert_id, result.game_id
                    )

                    if reasoning_chain_id:
                        await conn.execute("""
                            INSERT INTO expert_prediction_verification (
                                expert_reasoning_chain_id, game_id, expert_id, prediction_category,
                                predicted_value, actual_value, is_correct, accuracy_score,
                                confidence_score, verification_method, supporting_data
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT (expert_reasoning_chain_id, prediction_category) DO UPDATE SET
                                predicted_value = EXCLUDED.predicted_value,
                                actual_value = EXCLUDED.actual_value,
                                is_correct = EXCLUDED.is_correct,
                                accuracy_score = EXCLUDED.accuracy_score,
                                confidence_score = EXCLUDED.confidence_score,
                                verification_method = EXCLUDED.verification_method,
                                supporting_data = EXCLUDED.supporting_data,
                                verified_at = NOW()
                        """, reasoning_chain_id, result.game_id, result.expert_id, result.category,
                            str(result.predicted_value), str(result.actual_value), result.is_correct,
                            result.accuracy_score, result.confidence_score, result.verification_method,
                            json.dumps(result.supporting_data))

        except Exception as e:
            logger.error(f"Error storing verification results: {e}")

    async def generate_verification_report(self, game_id: str, expert_accuracies: Dict[str, ComprehensiveAccuracy]) -> Dict[str, Any]:
        """Generate comprehensive verification report"""

        report = {
            "game_id": game_id,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_experts": len(expert_accuracies),
            "overall_metrics": {},
            "expert_rankings": [],
            "category_analysis": {},
            "insights": []
        }

        if not expert_accuracies:
            return report

        # Overall metrics
        all_accuracies = [acc.overall_accuracy for acc in expert_accuracies.values()]
        weighted_accuracies = [acc.weighted_accuracy for acc in expert_accuracies.values()]
        calibrations = [acc.confidence_calibration for acc in expert_accuracies.values()]

        report["overall_metrics"] = {
            "mean_accuracy": statistics.mean(all_accuracies),
            "median_accuracy": statistics.median(all_accuracies),
            "std_accuracy": statistics.stdev(all_accuracies) if len(all_accuracies) > 1 else 0,
            "mean_weighted_accuracy": statistics.mean(weighted_accuracies),
            "mean_calibration": statistics.mean(calibrations),
            "best_accuracy": max(all_accuracies),
            "worst_accuracy": min(all_accuracies)
        }

        # Expert rankings
        expert_rankings = sorted(
            expert_accuracies.items(),
            key=lambda x: x[1].weighted_accuracy,
            reverse=True
        )

        report["expert_rankings"] = [
            {
                "rank": i + 1,
                "expert_id": expert_id,
                "accuracy": acc.overall_accuracy,
                "weighted_accuracy": acc.weighted_accuracy,
                "calibration": acc.confidence_calibration,
                "total_predictions": acc.total_predictions,
                "correct_predictions": acc.correct_predictions
            }
            for i, (expert_id, acc) in enumerate(expert_rankings)
        ]

        # Category analysis
        all_categories = set()
        for acc in expert_accuracies.values():
            all_categories.update(acc.category_accuracies.keys())

        category_analysis = {}
        for category in all_categories:
            category_accuracies = [
                acc.category_accuracies[category]
                for acc in expert_accuracies.values()
                if category in acc.category_accuracies
            ]

            if category_accuracies:
                category_analysis[category] = {
                    "mean_accuracy": statistics.mean(category_accuracies),
                    "median_accuracy": statistics.median(category_accuracies),
                    "best_accuracy": max(category_accuracies),
                    "worst_accuracy": min(category_accuracies),
                    "expert_count": len(category_accuracies)
                }

        report["category_analysis"] = category_analysis

        # Generate insights
        insights = []

        # Best performing expert
        best_expert = expert_rankings[0] if expert_rankings else None
        if best_expert:
            insights.append(f"Best performer: {best_expert['expert_id']} with {best_expert['weighted_accuracy']:.1%} weighted accuracy")

        # Best category performance
        if category_analysis:
            best_category = max(category_analysis.items(), key=lambda x: x[1]["mean_accuracy"])
            insights.append(f"Best category performance: {best_category[0]} with {best_category[1]['mean_accuracy']:.1%} average accuracy")

        # Worst category performance
        if category_analysis:
            worst_category = min(category_analysis.items(), key=lambda x: x[1]["mean_accuracy"])
            insights.append(f"Most challenging category: {worst_category[0]} with {worst_category[1]['mean_accuracy']:.1%} average accuracy")

        # Calibration insight
        well_calibrated = [expert_id for expert_id, acc in expert_accuracies.items() if acc.confidence_calibration > 0.8]
        if well_calibrated:
            insights.append(f"{len(well_calibrated)} experts are well-calibrated (calibration > 80%)")

        report["insights"] = insights

        return report

# Example usage
async def main():
    """Test comprehensive verification service"""
    from .enhanced_data_storage import EnhancedDataStorage

    # Initialize storage
    storage = EnhancedDataStorage("postgresql://localhost/nfl_predictor")
    await storage.initialize()

    # Initialize verification service
    verification_service = ComprehensiveVerificationService(storage)

    # Test game ID and sample predictions
    game_id = "test_game_id"
    expert_predictions = {
        "expert_1": {
            "winner": "LAC",
            "home_score": 23,
            "away_score": 27,
            "margin": 4,
            "coaching_advantage": "LAC"
        }
    }

    # Verify predictions
    accuracies = await verification_service.verify_all_expert_predictions(game_id, expert_predictions)

    # Generate report
    report = await verification_service.generate_verification_report(game_id, accuracies)

    logger.info(f"Verification complete: {report}")

    await storage.close()

if __name__ == "__main__":
    asyncio.run(main())