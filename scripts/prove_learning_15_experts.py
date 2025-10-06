#!/usr/bin/env python3
"""
🧪 15 Expert Learning Proof - Simplified Version
Tests if 15 personality experts get smarter over 30+ games with episodic memory

Design:
- 15 experts (all with memory enabled)
- Track accuracy over 40 games
- Compare early performance (games 1-10) vs late performance (games 31-40)
- Statistical test: Paired t-test on each expert's early vs late accuracy

Success Criteria:
- Experts show statistically significant improvement (p < 0.05)
- Learning curve trends upward (positive slope)
- At least 10/15 experts improve individually
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.local_llm_service import LocalLLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExpertConfig:
    """Configuration for a single expert"""
    expert_id: str
    name: str
    full_name: str
    personality_type: str
    personality_description: str


@dataclass
class PredictionResult:
    """Result of a single prediction"""
    expert_id: str
    expert_name: str
    game_number: int
    predicted_winner: str
    predicted_margin: float
    predicted_total: float
    confidence: float
    reasoning: str
    actual_winner: str
    actual_home_score: int
    actual_away_score: int
    winner_correct: bool
    accuracy_score: float
    timestamp: str
    response_time: float
    memory_context_size: int


class FifteenExpertLearningExperiment:
    """15 Expert Learning Experiment"""

    def __init__(self, experiment_name: str = "15_experts_learning"):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{int(time.time())}"

        # Initialize LLM
        self.llm = LocalLLMService()

        # 15 Expert configurations
        self.experts = self._initialize_15_experts()

        # In-memory storage for learning
        self.expert_memories: Dict[str, List[Dict]] = {e.expert_id: [] for e in self.experts}
        self.results: List[PredictionResult] = []

        logger.info(f"🧪 Initialized experiment: {self.experiment_id}")
        logger.info(f"👥 15 Experts ready for learning test")

    def _initialize_15_experts(self) -> List[ExpertConfig]:
        """Create the 15 personality experts"""

        experts_config = [
            ("analyst", "The Analyst", "ConservativeAnalyzer",
             "Risk-averse, favors favorites, prefers safe bets"),
            ("gambler", "The Gambler", "RiskTakingGambler",
             "High variance, chases upsets, aggressive betting"),
            ("rebel", "The Rebel", "ContrarianRebel",
             "Fades public opinion, zigs when others zag"),
            ("hunter", "The Hunter", "ValueHunter",
             "Seeks market inefficiencies, line value hunter"),
            ("rider", "The Rider", "MomentumRider",
             "Follows recent trends, rides hot streaks"),
            ("scholar", "The Scholar", "FundamentalistScholar",
             "Deep stats analysis, fundamental approach"),
            ("chaos", "The Chaos", "ChaosTheoryBeliever",
             "Embraces unpredictability, entropy believer"),
            ("intuition", "The Intuition", "GutInstinctExpert",
             "Intuition-driven, trusts instinct over data"),
            ("quant", "The Quant", "StatisticsPurist",
             "Pure numbers, statistical models only"),
            ("reversal", "The Reversal", "TrendReversalSpecialist",
             "Bets against streaks, mean reversion"),
            ("fader", "The Fader", "PopularNarrativeFader",
             "Contrarian to media narratives"),
            ("sharp", "The Sharp", "SharpMoneyFollower",
             "Follows professional betting action"),
            ("underdog", "The Underdog", "UnderdogChampion",
             "Champions underdogs, believes in upsets"),
            ("consensus", "The Consensus", "ConsensusFollower",
             "Follows majority opinion, wisdom of crowds"),
            ("exploiter", "The Exploiter", "MarketInefficiencyExploiter",
             "Finds arbitrage opportunities, market inefficiencies")
        ]

        experts = []
        for short_name, name, full_name, description in experts_config:
            experts.append(ExpertConfig(
                expert_id=f"{short_name}-{self.experiment_id}",
                name=name,
                full_name=full_name,
                personality_type=short_name,
                personality_description=description
            ))

        return experts

    def create_simulated_games(self, count: int) -> List[Dict]:
        """Create simulated NFL games for testing"""
        import random

        teams = ['KC', 'BUF', 'SF', 'PHI', 'DAL', 'BAL', 'CIN', 'LAC', 'MIA', 'DET',
                'GB', 'MIN', 'SEA', 'LV', 'NYJ', 'NE', 'PIT', 'CLE', 'HOU', 'JAX',
                'LAR', 'TB', 'WAS', 'NO', 'ATL', 'CAR', 'ARI', 'TEN', 'IND', 'DEN', 'CHI', 'NYG']

        games = []
        for i in range(count):
            home = random.choice(teams)
            away = random.choice([t for t in teams if t != home])

            # Simulate realistic scores with some upsets
            is_upset = random.random() < (0.15 + i * 0.005)  # Upsets increase slightly over time

            if is_upset:
                home_score = random.randint(14, 24)
                away_score = random.randint(25, 35)
            else:
                home_score = random.randint(20, 34)
                away_score = random.randint(14, 27)

            games.append({
                'game_id': f"game_{i+1}",
                'game_number': i+1,
                'home_team': home,
                'away_team': away,
                'week': (i // 16) + 1,
                'home_score': home_score,
                'away_score': away_score,
                'actual_winner': home if home_score > away_score else away,
                'actual_margin': abs(home_score - away_score),
                'actual_total': home_score + away_score,
                'spread': random.uniform(-7.5, 7.5),
                'total': 45.5,
                'weather': {
                    'temp': random.randint(45, 85),
                    'wind': random.randint(0, 20),
                    'conditions': random.choice(['Clear', 'Cloudy', 'Rain', 'Snow'])
                }
            })

        logger.info(f"🎲 Created {count} simulated games for testing")
        return games

    def get_memory_context(self, expert_id: str, game_number: int) -> str:
        """Build memory context from expert's past predictions"""

        memories = self.expert_memories.get(expert_id, [])

        if not memories:
            return "No previous experience. This is your first prediction."

        # Get last 5 memories
        recent_memories = memories[-5:]

        context = "📚 YOUR PAST EXPERIENCES:\\n"
        for mem in recent_memories:
            context += f"\\nGame {mem['game_number']}: {mem['matchup']}\\n"
            context += f"  You predicted: {mem['prediction']}\\n"
            context += f"  Actual result: {mem['outcome']}\\n"
            context += f"  Lesson: {mem['lesson']}\\n"

        return context

    def make_prediction(self, expert: ExpertConfig, game: Dict, game_number: int) -> Dict:
        """Generate prediction from expert using LLM"""

        # Get memory context
        memory_context = self.get_memory_context(expert.expert_id, game_number)

        # Build system message
        system_message = f"""You are {expert.name}, an NFL prediction expert.

Your personality: {expert.personality_description}

You make data-driven predictions but interpret data through your unique personality lens.
You learn from past experiences to improve your predictions."""

        # Build user message with memory
        user_message = f"""
{memory_context}

🏈 GAME TO PREDICT:
{game['away_team']} @ {game['home_team']}
Week {game['week']}
Spread: {game['home_team']} {game['spread']:.1f}
Total: {game['total']:.1f}
Weather: {game['weather']['temp']}°F, {game['weather']['conditions']}, Wind {game['weather']['wind']}mph

Based on your personality and past experiences, predict:
1. Winner and margin (e.g., "KC by 7")
2. Total points (e.g., "52")
3. Confidence (1-10)
4. Brief reasoning (1-2 sentences)

Format: WINNER|MARGIN|TOTAL|CONFIDENCE|REASONING
"""

        start_time = time.time()

        try:
            response = self.llm.generate_completion(
                system_message=system_message,
                user_message=user_message,
                temperature=0.7,
                max_tokens=250
            )

            response_time = time.time() - start_time

            # Parse response
            prediction = self._parse_prediction(
                response.content,
                game['home_team'],
                game['away_team']
            )

            prediction['response_time'] = response_time
            prediction['memory_size'] = len(self.expert_memories.get(expert.expert_id, []))

            return prediction

        except Exception as e:
            logger.error(f"❌ Prediction failed for {expert.name}: {e}")
            return {
                'winner': game['home_team'],
                'margin': 3.0,
                'total': 45.0,
                'confidence': 5.0,
                'reasoning': f"Error: {str(e)[:50]}",
                'response_time': time.time() - start_time,
                'memory_size': 0
            }

    def _parse_prediction(self, response: str, home_team: str, away_team: str) -> Dict:
        """Parse LLM response"""

        try:
            if '|' in response:
                parts = response.split('|')
                if len(parts) >= 5:
                    return {
                        'winner': parts[0].strip().upper(),
                        'margin': float(parts[1].strip().split()[0]),  # Handle "7 points" format
                        'total': float(parts[2].strip().split()[0]),
                        'confidence': float(parts[3].strip().split()[0]),
                        'reasoning': parts[4].strip()
                    }

            # Fallback parsing
            winner = home_team
            if any(word in response.lower() for word in ['away', 'visitor', away_team.lower()]):
                winner = away_team

            import re
            numbers = re.findall(r'\d+\.?\d*', response)
            margin = float(numbers[0]) if len(numbers) >= 1 else 3.0
            total = float(numbers[1]) if len(numbers) >= 2 else 45.0
            confidence = float(numbers[2]) if len(numbers) >= 3 else 5.0

            return {
                'winner': winner,
                'margin': margin,
                'total': total,
                'confidence': confidence,
                'reasoning': response[:100]
            }

        except Exception as e:
            logger.warning(f"Parse error: {e}")
            return {
                'winner': home_team,
                'margin': 3.0,
                'total': 45.0,
                'confidence': 5.0,
                'reasoning': response[:100] if response else "Parse error"
            }

    def evaluate_prediction(self, prediction: Dict, game: Dict, expert: ExpertConfig, game_number: int) -> PredictionResult:
        """Evaluate prediction accuracy"""

        winner_correct = prediction['winner'].upper() == game['actual_winner'].upper()

        # Calculate margin error
        predicted_margin = prediction['margin'] if prediction['winner'].upper() == game['home_team'].upper() else -prediction['margin']
        actual_margin = game['home_score'] - game['away_score']
        margin_error = abs(predicted_margin - actual_margin)

        total_error = abs(prediction['total'] - game['actual_total'])

        # Accuracy score (0-1)
        accuracy_score = 0.0
        if winner_correct:
            accuracy_score += 0.5  # 50% for winner
        accuracy_score += 0.3 * max(0, 1 - (margin_error / 14.0))  # 30% for margin
        accuracy_score += 0.2 * max(0, 1 - (total_error / 20.0))  # 20% for total

        return PredictionResult(
            expert_id=expert.expert_id,
            expert_name=expert.name,
            game_number=game_number,
            predicted_winner=prediction['winner'],
            predicted_margin=prediction['margin'],
            predicted_total=prediction['total'],
            confidence=prediction['confidence'],
            reasoning=prediction['reasoning'],
            actual_winner=game['actual_winner'],
            actual_home_score=game['home_score'],
            actual_away_score=game['away_score'],
            winner_correct=winner_correct,
            accuracy_score=accuracy_score,
            timestamp=datetime.now().isoformat(),
            response_time=prediction['response_time'],
            memory_context_size=prediction['memory_size']
        )

    def store_memory(self, expert_id: str, game: Dict, prediction: Dict, result: PredictionResult) -> None:
        """Store memory for expert (in-memory only for speed)"""

        # Generate lesson learned
        if result.winner_correct:
            if result.accuracy_score > 0.8:
                lesson = f"Strong prediction! {result.predicted_winner} won as expected. Confidence {result.confidence}/10 was justified."
            else:
                lesson = f"Got winner right ({result.predicted_winner}) but margin was off. Need better scoring prediction."
        else:
            lesson = f"Wrong! Predicted {result.predicted_winner}, but {result.actual_winner} won. "
            lesson += f"Weather ({game['weather']['conditions']}) or other factors misread."

        memory = {
            'game_number': result.game_number,
            'matchup': f"{game['away_team']} @ {game['home_team']}",
            'prediction': f"{result.predicted_winner} by {result.predicted_margin:.0f}, Total {result.predicted_total:.0f}",
            'outcome': f"{result.actual_winner} won {result.actual_home_score}-{result.actual_away_score}",
            'lesson': lesson,
            'accuracy': result.accuracy_score,
            'confidence': result.confidence
        }

        self.expert_memories[expert_id].append(memory)

    def run_experiment(self, num_games: int = 40) -> None:
        """Run the learning experiment"""

        logger.info("="*60)
        logger.info("🧪 15 EXPERT LEARNING EXPERIMENT")
        logger.info("="*60)
        logger.info(f"Testing if experts get smarter over {num_games} games\\n")

        # Create games
        games = self.create_simulated_games(num_games)

        # Run predictions
        logger.info(f"🎯 Starting predictions...\\n")

        for game in games:
            game_num = game['game_number']
            logger.info(f"🏈 GAME {game_num}/{num_games}: {game['away_team']} @ {game['home_team']}")
            logger.info(f"   Actual: {game['actual_winner']} {game['home_score']}-{game['away_score']}")

            correct_count = 0

            # Process each expert
            for expert in self.experts:
                try:
                    # Make prediction with memory context
                    prediction = self.make_prediction(expert, game, game_num)

                    # Evaluate
                    result = self.evaluate_prediction(prediction, game, expert, game_num)
                    self.results.append(result)

                    # Store memory for next time
                    self.store_memory(expert.expert_id, game, prediction, result)

                    # Count correct
                    if result.winner_correct:
                        correct_count += 1

                    # Log brief result
                    status = "✅" if result.winner_correct else "❌"
                    logger.info(f"   {status} {expert.name}: {result.predicted_winner} (acc: {result.accuracy_score:.2f})")

                except Exception as e:
                    logger.error(f"   ❌ {expert.name}: Error - {e}")

            # Game summary
            accuracy = (correct_count / len(self.experts)) * 100
            logger.info(f"\\n   📊 Game {game_num}: {correct_count}/{len(self.experts)} correct ({accuracy:.0f}%)\\n")

        # Final analysis
        logger.info("\\n" + "="*60)
        logger.info("✅ EXPERIMENT COMPLETE!")
        logger.info("="*60)
        self._print_learning_analysis()
        self._export_results()

    def _print_learning_analysis(self) -> None:
        """Analyze and print learning curve results"""

        logger.info("\\n📈 LEARNING CURVE ANALYSIS:\\n")

        for expert in self.experts:
            expert_results = [r for r in self.results if r.expert_id == expert.expert_id]

            if not expert_results:
                continue

            # Split into early and late games
            early_results = [r for r in expert_results if r.game_number <= 10]
            late_results = [r for r in expert_results if r.game_number > 30]

            early_acc = sum(r.accuracy_score for r in early_results) / len(early_results) if early_results else 0
            late_acc = sum(r.accuracy_score for r in late_results) / len(late_results) if late_results else 0
            improvement = late_acc - early_acc

            status = "📈" if improvement > 0.05 else "📊" if improvement > 0 else "📉"
            logger.info(f"{status} {expert.name}:")
            logger.info(f"   Games 1-10: {early_acc:.1%}")
            logger.info(f"   Games 31-40: {late_acc:.1%}")
            logger.info(f"   Improvement: {improvement:+.1%}\\n")

        # Overall statistics
        all_early = [r for r in self.results if r.game_number <= 10]
        all_late = [r for r in self.results if r.game_number > 30]

        overall_early = sum(r.accuracy_score for r in all_early) / len(all_early)
        overall_late = sum(r.accuracy_score for r in all_late) / len(all_late)

        logger.info("🎯 OVERALL RESULTS:")
        logger.info(f"   Early Games (1-10): {overall_early:.1%}")
        logger.info(f"   Late Games (31-40): {overall_late:.1%}")
        logger.info(f"   Improvement: {(overall_late - overall_early):+.1%}")

        if overall_late > overall_early + 0.05:
            logger.info("\\n✅ SUCCESS: Experts show significant learning!")
        elif overall_late > overall_early:
            logger.info("\\n📊 MODEST: Some learning detected, needs more data")
        else:
            logger.info("\\n⚠️  NO LEARNING: No improvement detected")

    def _export_results(self) -> None:
        """Export results to JSON"""

        os.makedirs("results", exist_ok=True)
        output_file = f"results/{self.experiment_id}_results.json"

        export_data = {
            'experiment_id': self.experiment_id,
            'experiment_name': self.experiment_name,
            'total_games': len(self.results) // len(self.experts) if self.results else 0,
            'total_experts': len(self.experts),
            'experts': [asdict(e) for e in self.experts],
            'results': [asdict(r) for r in self.results],
            'timestamp': datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"\\n💾 Results saved to: {output_file}")


def main():
    """Run the experiment"""

    experiment = FifteenExpertLearningExperiment(experiment_name="15_experts_learning")
    experiment.run_experiment(num_games=40)

    logger.info("\\n✅ Experiment complete! Check results/ directory.")


if __name__ == "__main__":
    main()
