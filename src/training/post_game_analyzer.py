#!/usr/bin/env python3
"""
Post-Game Analyzer

Compares expert predictions against actual game outcomes and creates memories
for future learning. Core component for expert improvement over time.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
sys.path.append('src')

from training.nfl_data_loader import GameContext
from training.prediction_generator import GamePrediction
from training.expert_configuration import ExpertType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionAccuracy(Enum):
    """Prediction accuracy levels"""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PUSH = "push"  # For spread/total predictions

@dataclass
class PredictionAnalysis:
    """Analysis of a single expert's prediction vs actual outcome"""
    expert_id: str
    expert_type: ExpertType
    game_id: str
    prediction: GamePrediction
    actual_outcome: Dict[str, Any]

    # Accuracy metrics
    winner_correct: bool
    margin_error: Optional[float] = None
    confidence_calibration: Optional[float] = None

    # Learning insights
    key_factors_validated: List[str] = None
    key_factors_contradicted: List[str] = None
    reasoning_quality_score: float = 0.0

    # Memory creation
    memory_strength: float = 0.0  # How memorable this game should be
    memory_tags: List[str] = None

    def __post_init__(self):
        if self.key_factors_validated is None:
            self.key_factors_validated = []
        if self.key_factors_contradicted is None:
            self.key_factors_contradicted = []
        if self.memory_tags is None:
            self.memory_tags = []

@dataclass
class GameAnalysis:
    """Complete analysis of all expert predictions for a game"""
    game_id: str
    game_context: GameContext
    actual_outcome: Dict[str, Any]
    expert_analyses: Dict[str, PredictionAnalysis]

    # Game-level insights
    consensus_accuracy: float = 0.0
    prediction_spread: float = 0.0  # How much experts disagreed
    surprise_factor: float = 0.0    # How unexpected the outcome was

    # Learning opportunities
    key_lessons: List[str] = None

    def __post_init__(self):
        if self.key_lessons is None:
            self.key_lessons = []

class PostGameAnalyzer:
    """Analyzes expert predictions against actual game outcomes"""

    def __init__(self):
        """Initialize the post-game analyzer"""
        logger.info("✅ Post-Game Analyzer initialized")

    def analyze_game(self, game: GameContext, predictions: Dict[str, GamePrediction]) -> GameAnalysis:
        """Analyze all expert predictions for a completed game"""
        try:
            # Extract actual outcome
            actual_outcome = self._extract_actual_outcome(game)

            # Analyze each expert's prediction
            expert_analyses = {}
            for expert_id, prediction in predictions.items():
                try:
                    expert_type = ExpertType(expert_id)
                    analysis = self._analyze_expert_prediction(
                        expert_id, expert_type, game, prediction, actual_outcome
                    )
                    expert_analyses[expert_id] = analysis
                except Exception as e:
                    logger.warning(f"⚠️ Failed to analyze {expert_id} prediction: {e}")
                    continue

            # Calculate game-level metrics
            game_analysis = GameAnalysis(
                game_id=game.game_id,
                game_context=game,
                actual_outcome=actual_outcome,
                expert_analyses=expert_analyses
            )

            self._calculate_game_metrics(game_analysis)
            self._identify_key_lessons(game_analysis)

            logger.debug(f"📊 Analyzed {len(expert_analyses)} predictions for {game.game_id}")
            return game_analysis

        except Exception as e:
            logger.error(f"❌ Failed to analyze game {game.game_id}: {e}")
            raise

    def _extract_actual_outcome(self, game: GameContext) -> Dict[str, Any]:
        """Extract actual game outcome from GameContext"""
        if game.home_score is None or game.away_score is None:
            raise ValueError(f"Game {game.game_id} is not completed - missing scores")

        home_score = game.home_score
        away_score = game.away_score

        # Determine winner
        if home_score > away_score:
            winner = 'home'
            winning_team = game.home_team
            losing_team = game.away_team
        elif away_score > home_score:
            winner = 'away'
            winning_team = game.away_team
            losing_team = game.home_team
        else:
            winner = 'tie'
            winning_team = None
            losing_team = None

        # Calculate margin
        margin = abs(home_score - away_score)

        # Calculate total points
        total_points = home_score + away_score

        return {
            'home_score': home_score,
            'away_score': away_score,
            'winner': winner,
            'winning_team': winning_team,
            'losing_team': losing_team,
            'margin': margin,
            'total_points': total_points,
            'overtime': game.overtime
        }

    def _analyze_expert_prediction(self, expert_id: str, expert_type: ExpertType,
                                 game: GameContext, prediction: GamePrediction,
                                 actual_outcome: Dict[str, Any]) -> PredictionAnalysis:
        """Analyze a single expert's prediction against actual outcome"""

        # Determine if winner prediction was correct
        predicted_winner = 'home' if prediction.win_probability > 0.5 else 'away'
        actual_winner = actual_outcome['winner']

        winner_correct = (predicted_winner == actual_winner) if actual_winner != 'tie' else False

        # Calculate confidence calibration
        confidence_calibration = self._calculate_confidence_calibration(
            prediction.confidence_level, winner_correct
        )

        # Analyze reasoning factors
        validated_factors, contradicted_factors = self._analyze_reasoning_factors(
            prediction.reasoning_chain, game, actual_outcome
        )

        # Calculate reasoning quality
        reasoning_quality = self._calculate_reasoning_quality(
            prediction.reasoning_chain, validated_factors, contradicted_factors
        )

        # Determine memory strength (how memorable this game should be)
        memory_strength = self._calculate_memory_strength(
            prediction, actual_outcome, winner_correct, confidence_calibration
        )

        # Generate memory tags
        memory_tags = self._generate_memory_tags(
            expert_type, game, prediction, actual_outcome, winner_correct
        )

        return PredictionAnalysis(
            expert_id=expert_id,
            expert_type=expert_type,
            game_id=game.game_id,
            prediction=prediction,
            actual_outcome=actual_outcome,
            winner_correct=winner_correct,
            confidence_calibration=confidence_calibration,
            key_factors_validated=validated_factors,
            key_factors_contradicted=contradicted_factors,
            reasoning_quality_score=reasoning_quality,
            memory_strength=memory_strength,
            memory_tags=memory_tags
        )

    def _calculate_confidence_calibration(self, confidence: float, was_correct: bool) -> float:
        """Calculate how well calibrated the expert's confidence was"""
        # Simple calibration: if high confidence and correct, or low confidence and incorrect, good calibration
        if was_correct:
            return confidence  # Higher confidence for correct predictions is good
        else:
            return 1.0 - confidence  # Lower confidence for incorrect predictions is good

    def _analyze_reasoning_factors(self, reasoning_chain: List[str], game: GameContext,
                                 actual_outcome: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Analyze which reasoning factors were validated or contradicted"""
        validated = []
        contradicted = []

        reasoning_text = ' '.join(reasoning_chain).lower()

        # Check weather-related reasoning
        if 'weather' in reasoning_text or 'temperature' in reasoning_text or 'wind' in reasoning_text:
            if game.weather:
                # Simple heuristic: cold/windy weather mentioned and low-scoring game
                if (game.weather.get('temperature', 70) < 40 or game.weather.get('wind_speed', 0) > 15):
                    if actual_outcome['total_points'] < 45:
                        validated.append('weather_impact')
                    else:
                        contradicted.append('weather_impact')

        # Check momentum-related reasoning
        if 'momentum' in reasoning_text or 'hot' in reasoning_text or 'streak' in reasoning_text:
            # This would need more sophisticated momentum tracking
            # For now, just tag it as a momentum-based prediction
            validated.append('momentum_based')

        # Check contrarian reasoning
        if 'fade' in reasoning_text or 'contrarian' in reasoning_text or 'public' in reasoning_text:
            validated.append('contrarian_approach')

        # Check statistical reasoning
        if 'statistics' in reasoning_text or 'data' in reasoning_text or 'model' in reasoning_text:
            validated.append('statistical_analysis')

        return validated, contradicted

    def _calculate_reasoning_quality(self, reasoning_chain: List[str],
                                   validated: List[str], contradicted: List[str]) -> float:
        """Calculate quality score for reasoning chain"""
        if not reasoning_chain:
            return 0.0

        # Base score for having reasoning
        base_score = 0.3

        # Bonus for detailed reasoning
        detail_bonus = min(len(reasoning_chain) * 0.1, 0.4)

        # Bonus for validated factors
        validation_bonus = len(validated) * 0.1

        # Penalty for contradicted factors
        contradiction_penalty = len(contradicted) * 0.1

        return min(base_score + detail_bonus + validation_bonus - contradiction_penalty, 1.0)

    def _calculate_memory_strength(self, prediction: GamePrediction, actual_outcome: Dict[str, Any],
                                 was_correct: bool, confidence_calibration: float) -> float:
        """Calculate how memorable this game should be for the expert"""

        # Base memory strength
        base_strength = 0.5

        # Boost for surprising outcomes (high confidence but wrong, or low confidence but right)
        if was_correct and prediction.confidence_level < 0.3:
            base_strength += 0.3  # Unexpected success
        elif not was_correct and prediction.confidence_level > 0.7:
            base_strength += 0.4  # Overconfident failure

        # Boost for extreme games (blowouts, overtime, etc.)
        if actual_outcome['margin'] > 21:  # Blowout
            base_strength += 0.2
        elif actual_outcome.get('overtime', False):  # Overtime
            base_strength += 0.3

        # Boost for poor confidence calibration (learning opportunity)
        if confidence_calibration < 0.3:
            base_strength += 0.2

        return min(base_strength, 1.0)

    def _generate_memory_tags(self, expert_type: ExpertType, game: GameContext,
                            prediction: GamePrediction, actual_outcome: Dict[str, Any],
                            was_correct: bool) -> List[str]:
        """Generate tags for memory categorization"""
        tags = []

        # Basic tags
        tags.append(f"week_{game.week}")
        tags.append(f"season_{game.season}")
        tags.append("correct" if was_correct else "incorrect")

        # Game characteristics
        if game.division_game:
            tags.append("division_game")

        if game.weather:
            if game.weather.get('temperature', 70) < 40:
                tags.append("cold_weather")
            if game.weather.get('wind_speed', 0) > 15:
                tags.append("windy_conditions")

        # Outcome characteristics
        if actual_outcome['margin'] > 14:
            tags.append("blowout")
        elif actual_outcome['margin'] <= 3:
            tags.append("close_game")

        if actual_outcome.get('overtime', False):
            tags.append("overtime")

        # Confidence-based tags
        if prediction.confidence_level > 0.7:
            tags.append("high_confidence")
        elif prediction.confidence_level < 0.3:
            tags.append("low_confidence")

        # Expert-specific tags
        if expert_type == ExpertType.CONTRARIAN_REBEL:
            tags.append("contrarian_pick")
        elif expert_type == ExpertType.MOMENTUM_RIDER:
            tags.append("momentum_play")
        elif expert_type == ExpertType.UNDERDOG_CHAMPION:
            tags.append("underdog_focus")

        return tags

    def _calculate_game_metrics(self, game_analysis: GameAnalysis):
        """Calculate game-level metrics"""
        if not game_analysis.expert_analyses:
            return

        # Consensus accuracy
        correct_predictions = sum(1 for analysis in game_analysis.expert_analyses.values()
                                if analysis.winner_correct)
        total_predictions = len(game_analysis.expert_analyses)
        game_analysis.consensus_accuracy = correct_predictions / total_predictions

        # Prediction spread (how much experts disagreed)
        probabilities = [analysis.prediction.win_probability for analysis in game_analysis.expert_analyses.values()]
        if probabilities:
            game_analysis.prediction_spread = max(probabilities) - min(probabilities)

        # Surprise factor (how unexpected the outcome was based on average confidence)
        avg_confidence = sum(analysis.prediction.confidence_level for analysis in game_analysis.expert_analyses.values()) / total_predictions
        game_analysis.surprise_factor = 1.0 - avg_confidence if game_analysis.consensus_accuracy < 0.5 else avg_confidence

    def _identify_key_lessons(self, game_analysis: GameAnalysis):
        """Identify key lessons from the game"""
        lessons = []

        # Low consensus accuracy suggests unpredictable game
        if game_analysis.consensus_accuracy < 0.4:
            lessons.append("Highly unpredictable game - chaos factors dominated")

        # High prediction spread suggests expert disagreement
        if game_analysis.prediction_spread > 0.3:
            lessons.append("Experts strongly disagreed - conflicting signals present")

        # High surprise factor
        if game_analysis.surprise_factor > 0.7:
            lessons.append("Outcome was surprising relative to expert confidence")

        # Weather impact
        weather = game_analysis.game_context.weather
        if weather and (weather.get('temperature', 70) < 35 or weather.get('wind_speed', 0) > 20):
            if game_analysis.actual_outcome['total_points'] < 40:
                lessons.append("Extreme weather significantly impacted scoring")

        game_analysis.key_lessons = lessons

    def create_learning_memories(self, game_analysis: GameAnalysis) -> Dict[str, Dict[str, Any]]:
        """Create memory objects for each expert based on game analysis"""
        memories = {}

        for expert_id, analysis in game_analysis.expert_analyses.items():
            memory = {
                'game_id': game_analysis.game_id,
                'game_date': game_analysis.game_context.game_date.isoformat(),
                'teams': f"{game_analysis.game_context.away_team}@{game_analysis.game_context.home_team}",
                'week': game_analysis.game_context.week,
                'season': game_analysis.game_context.season,

                # Prediction details
                'prediction': {
                    'winner': analysis.prediction.predicted_winner,
                    'probability': analysis.prediction.win_probability,
                    'confidence': analysis.prediction.confidence_level,
                    'reasoning': analysis.prediction.reasoning_chain
                },

                # Outcome details
                'outcome': analysis.actual_outcome,
                'was_correct': analysis.winner_correct,

                # Learning insights
                'confidence_calibration': analysis.confidence_calibration,
                'validated_factors': analysis.key_factors_validated,
                'contradicted_factors': analysis.key_factors_contradicted,
                'reasoning_quality': analysis.reasoning_quality_score,

                # Memory metadata
                'memory_strength': analysis.memory_strength,
                'tags': analysis.memory_tags,
                'created_at': datetime.now().isoformat()
            }

            memories[expert_id] = memory

        return memories

    def generate_analysis_summary(self, game_analysis: GameAnalysis) -> Dict[str, Any]:
        """Generate a summary of the game analysis"""
        return {
            'game_id': game_analysis.game_id,
            'teams': f"{game_analysis.game_context.away_team}@{game_analysis.game_context.home_team}",
            'final_score': f"{game_analysis.actual_outcome['away_score']}-{game_analysis.actual_outcome['home_score']}",
            'winner': game_analysis.actual_outcome['winning_team'],
            'margin': game_analysis.actual_outcome['margin'],

            'expert_performance': {
                'total_experts': len(game_analysis.expert_analyses),
                'correct_predictions': sum(1 for a in game_analysis.expert_analyses.values() if a.winner_correct),
                'consensus_accuracy': game_analysis.consensus_accuracy,
                'prediction_spread': game_analysis.prediction_spread,
                'surprise_factor': game_analysis.surprise_factor
            },

            'top_performers': [
                {
                    'expert': analysis.expert_id,
                    'correct': analysis.winner_correct,
                    'confidence': analysis.prediction.confidence_level,
                    'calibration': analysis.confidence_calibration
                }
                for analysis in sorted(game_analysis.expert_analyses.values(),
                                     key=lambda x: x.confidence_calibration, reverse=True)[:3]
            ],

            'key_lessons': game_analysis.key_lessons
        }


async def main():
    """Test the Post-Game Analyzer"""

    print("📊 Post-Game Analyzer Test")
    print("=" * 50)

    # Initialize analyzer
    analyzer = PostGameAnalyzer()

    # Create a mock completed game
    from training.nfl_data_loader import NFLDataLoader
    from training.prediction_generator import GamePrediction

    # Load a real completed game
    loader = NFLDataLoader()
    season_2020 = loader.load_season_games(2020, completed_only=True)

    if not season_2020.games:
        print("❌ No completed games found for testing")
        return

    test_game = season_2020.games[0]  # First game of 2020 season

    # Create mock predictions (simplified)
    from training.prediction_generator import PredictionType
    from training.expert_configuration import ExpertType

    mock_predictions = {
        'conservative_analyzer': GamePrediction(
            expert_type=ExpertType.CONSERVATIVE_ANALYZER,
            prediction_type=PredictionType.WINNER,
            predicted_winner=test_game.home_team,
            win_probability=0.55,
            confidence_level=0.65,
            reasoning_chain=["Conservative analysis suggests home team advantage", "Statistical models favor the home team"]
        ),
        'contrarian_rebel': GamePrediction(
            expert_type=ExpertType.CONTRARIAN_REBEL,
            prediction_type=PredictionType.WINNER,
            predicted_winner=test_game.away_team,
            win_probability=0.45,
            confidence_level=0.75,
            reasoning_chain=["Fading the public consensus", "Contrarian value on the road team"]
        ),
        'chaos_theory_believer': GamePrediction(
            expert_type=ExpertType.CHAOS_THEORY_BELIEVER,
            prediction_type=PredictionType.WINNER,
            predicted_winner=test_game.away_team,
            win_probability=0.52,
            confidence_level=0.15,
            reasoning_chain=["Chaos theory suggests unpredictable outcome", "Random events dominate"]
        )
    }

    print(f"\n🏈 Analyzing: {test_game.away_team} @ {test_game.home_team}")
    print(f"Final Score: {test_game.away_score} - {test_game.home_score}")
    print(f"Date: {test_game.game_date}")

    # Analyze the game
    game_analysis = analyzer.analyze_game(test_game, mock_predictions)

    # Generate summary
    summary = analyzer.generate_analysis_summary(game_analysis)

    print(f"\n📈 Analysis Results:")
    print(f"Consensus Accuracy: {summary['expert_performance']['consensus_accuracy']:.1%}")
    print(f"Prediction Spread: {summary['expert_performance']['prediction_spread']:.3f}")
    print(f"Surprise Factor: {summary['expert_performance']['surprise_factor']:.3f}")

    print(f"\n🏆 Top Performers:")
    for performer in summary['top_performers']:
        status = "✅" if performer['correct'] else "❌"
        print(f"  {status} {performer['expert']}: {performer['confidence']:.1%} confidence, {performer['calibration']:.3f} calibration")

    if summary['key_lessons']:
        print(f"\n📚 Key Lessons:")
        for lesson in summary['key_lessons']:
            print(f"  • {lesson}")

    # Create learning memories
    memories = analyzer.create_learning_memories(game_analysis)
    print(f"\n🧠 Created {len(memories)} learning memories for experts")

    print(f"\n✅ Post-Game Analyzer test complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
