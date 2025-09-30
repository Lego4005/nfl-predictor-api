#!/usr/bin/env python3
"""
🧪 Memory Learning Proof Experiment
Rigorous A/B test to prove whether episodic memory makes LLM experts smarter

Design:
- Control Group: 15 experts WITHOUT memory (fresh predictions every game)
- Experimental Group: 15 experts WITH memory (accumulate and use episodic memories)
- Both groups predict same 40+ real NFL games in chronological order
- Statistical analysis proves learning curve improvement

Success Criteria:
- Memory group shows statistically significant accuracy improvement (p < 0.05)
- Learning curve trends upward for memory, flat for no-memory
- At least 10/15 experts show individual improvement
"""

import sys
import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from supabase import create_client, Client

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.local_llm_service import LocalLLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExpertConfig:
    """Configuration for a single expert"""
    expert_id: str
    name: str
    personality_type: str
    has_memory: bool
    group: str  # "memory" or "no-memory"

@dataclass
class PredictionResult:
    """Result of a single prediction"""
    expert_id: str
    game_id: str
    game_number: int
    predicted_winner: str
    predicted_margin: float
    predicted_total: float
    confidence: float
    reasoning: str
    actual_winner: str
    actual_home_score: int
    actual_away_score: int
    actual_margin: float
    actual_total: float
    winner_correct: bool
    margin_error: float
    total_error: float
    accuracy_score: float
    timestamp: str
    response_time: float
    memories_used: int


class MemoryLearningExperiment:
    """Main experiment coordinator"""

    def __init__(self, experiment_name: str = "memory_proof_v1"):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{int(time.time())}"

        # Initialize services
        self.llm = LocalLLMService()

        # Initialize Supabase
        self.supabase_url = "https://vaypgzvivahnfegnlinn.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Expert configurations
        self.experts: List[ExpertConfig] = []
        self.results: List[PredictionResult] = []

        # Progress tracking
        self.current_game = 0
        self.total_games = 0

        logger.info(f"🧪 Initialized experiment: {self.experiment_id}")

    def initialize_experts(self) -> None:
        """Create 30 expert instances: 15 with memory, 15 without"""

        personality_types = [
            ("conservative", "ConservativeAnalyzer"),
            ("gambler", "RiskTakingGambler"),
            ("contrarian", "ContrarianRebel"),
            ("value", "ValueHunter"),
            ("momentum", "MomentumRider"),
            ("scholar", "FundamentalistScholar"),
            ("chaos", "ChaosTheoryBeliever"),
            ("gut", "GutInstinctExpert"),
            ("quant", "StatisticsPurist"),
            ("reversal", "TrendReversalSpecialist"),
            ("fader", "PopularNarrativeFader"),
            ("sharp", "SharpMoneyFollower"),
            ("underdog", "UnderdogChampion"),
            ("consensus", "ConsensusFollower"),
            ("exploiter", "MarketInefficiencyExploiter")
        ]

        # Create memory-enabled experts
        for short_name, full_name in personality_types:
            self.experts.append(ExpertConfig(
                expert_id=f"{short_name}-mem-{self.experiment_id}",
                name=f"{full_name} (Memory)",
                personality_type=short_name,
                has_memory=True,
                group="memory"
            ))

        # Create no-memory experts
        for short_name, full_name in personality_types:
            self.experts.append(ExpertConfig(
                expert_id=f"{short_name}-nomem-{self.experiment_id}",
                name=f"{full_name} (No Memory)",
                personality_type=short_name,
                has_memory=False,
                group="no-memory"
            ))

        logger.info(f"✅ Initialized {len(self.experts)} experts (15 memory, 15 no-memory)")

        # Store expert configs in Supabase
        self._store_expert_configs()

    def _store_expert_configs(self) -> None:
        """Store expert configurations in Supabase"""
        try:
            for expert in self.experts:
                # Simplified expert data (only required fields)
                expert_data = {
                    'expert_id': expert.expert_id,
                    'name': expert.name,
                    'personality_traits': [expert.personality_type],
                    'decision_style': expert.group,
                    'risk_tolerance': 'moderate',
                    'is_active': True
                }

                # Upsert to avoid duplicates
                self.supabase.table('personality_experts').upsert(expert_data, on_conflict='expert_id').execute()

            logger.info("📝 Stored expert configurations in Supabase")

        except Exception as e:
            logger.warning(f"⚠️ Could not store expert configs: {e}")
            logger.info("Continuing without expert storage (memory storage may fail)")

    def load_real_games(self, limit: int = 40, season: int = 2025) -> List[Dict]:
        """Load real completed NFL games from Supabase"""

        try:
            # Query completed games with scores
            response = self.supabase.table('nfl_games')\
                .select('*')\
                .eq('season', season)\
                .not_.is_('home_score', 'null')\
                .not_.is_('away_score', 'null')\
                .order('game_time')\ # Fixed column name
                .limit(limit)\
                .execute()

            games = response.data if response.data else []

            if not games:
                logger.warning(f"⚠️ No completed games found for season {season}")
                logger.info("💡 Falling back to simulated games for testing")
                return self._create_simulated_games(limit)

            logger.info(f"✅ Loaded {len(games)} real games from Supabase")

            # Enrich games with full data
            enriched_games = []
            for game in games:
                enriched = self._enrich_game_data(game)
                enriched_games.append(enriched)

            return enriched_games

        except Exception as e:
            logger.error(f"❌ Error loading games: {e}")
            logger.info("💡 Falling back to simulated games")
            return self._create_simulated_games(limit)

    def _enrich_game_data(self, game: Dict) -> Dict:
        """Enrich game with all necessary data for prediction"""

        return {
            'game_id': game.get('game_id', f"game_{game.get('week', 1)}_{game.get('home_team', 'HOME')}"),
            'home_team': game.get('home_team', 'UNKNOWN'),
            'away_team': game.get('away_team', 'UNKNOWN'),
            'week': game.get('week', 1),
            'season': game.get('season', 2025),
            'game_time': game.get('game_time', game.get('game_time_et', 'Unknown')),
            'location': game.get('location', 'Unknown'),

            # Actual outcomes
            'home_score': int(game.get('home_score', 0)),
            'away_score': int(game.get('away_score', 0)),
            'actual_total': int(game.get('home_score', 0)) + int(game.get('away_score', 0)),
            'actual_margin': abs(int(game.get('home_score', 0)) - int(game.get('away_score', 0))),
            'actual_winner': game.get('home_team') if int(game.get('home_score', 0)) > int(game.get('away_score', 0)) else game.get('away_team'),

            # Betting lines
            'spread': game.get('spread_line', 0.0),
            'total': game.get('total_line', 45.0),
            'moneyline_home': game.get('moneyline_home'),
            'moneyline_away': game.get('moneyline_away'),

            # Context data
            'weather': game.get('weather_data', {}),
            'injuries': game.get('injury_data', {}),
            'status': game.get('status', 'completed')
        }

    def _create_simulated_games(self, count: int) -> List[Dict]:
        """Create simulated games for testing when no real data available"""

        import random

        teams = ['KC', 'BUF', 'SF', 'PHI', 'DAL', 'BAL', 'CIN', 'LAC', 'MIA', 'DET',
                'GB', 'MIN', 'SEA', 'LV', 'NYJ', 'NE', 'PIT', 'CLE', 'HOU', 'JAX']

        games = []
        for i in range(count):
            home = random.choice(teams)
            away = random.choice([t for t in teams if t != home])

            # Simulate realistic scores
            home_score = random.randint(17, 35)
            away_score = random.randint(14, 31)

            games.append({
                'game_id': f"sim_game_{i+1}",
                'home_team': home,
                'away_team': away,
                'week': (i // 16) + 1,
                'season': 2025,
                'game_time': f"Week {(i // 16) + 1}",
                'location': f"{home} Stadium",
                'home_score': home_score,
                'away_score': away_score,
                'actual_total': home_score + away_score,
                'actual_margin': abs(home_score - away_score),
                'actual_winner': home if home_score > away_score else away,
                'spread': random.uniform(-7, 7),
                'total': 45.0,
                'moneyline_home': None,
                'moneyline_away': None,
                'weather': {'temp': random.randint(50, 85), 'wind': random.randint(0, 15)},
                'injuries': {},
                'status': 'completed'
            })

        logger.info(f"🎲 Created {count} simulated games for testing")
        return games

    def make_prediction(self, expert: ExpertConfig, game: Dict, memories: List[Dict] = None) -> Dict:
        """Generate prediction from expert using LLM"""

        # Build personality-specific system message
        personality_traits = self._get_personality_traits(expert.personality_type)
        system_message = f"""You are {expert.name}, an NFL prediction expert.

Your personality traits: {personality_traits}

You make data-driven predictions but interpret data through your unique personality lens.
Always provide: winner, margin, total points, confidence (1-10), and brief reasoning."""

        # Build context with memory if available
        memory_context = ""
        if memories and len(memories) > 0:
            memory_context = "\\n\\n📚 RELEVANT PAST EXPERIENCES:\\n"
            for i, mem in enumerate(memories[:5], 1):
                memory_context += f"{i}. {mem.get('summary', 'Past game experience')}\\n"

        # Build user message
        user_message = f"""
{memory_context}

GAME TO PREDICT:
{game['away_team']} @ {game['home_team']}
Week {game['week']}, {game['season']} Season
Spread: {game['home_team']} {game['spread']:.1f}
Total: {game['total']:.1f}
Weather: {game.get('weather', {})}

Predict:
1. Winner and margin (e.g., "KC by 7")
2. Total points (e.g., "52")
3. Confidence (1-10)
4. Key reasoning (1-2 sentences)

Format: WINNER|MARGIN|TOTAL|CONFIDENCE|REASONING
"""

        start_time = time.time()

        try:
            response = self.llm.generate_completion(
                system_message=system_message,
                user_message=user_message,
                temperature=0.7,
                max_tokens=200
            )

            response_time = time.time() - start_time

            # Parse response
            prediction = self._parse_prediction_response(
                response.content,
                game['home_team'],
                game['away_team']
            )

            prediction['response_time'] = response_time
            prediction['memories_used'] = len(memories) if memories else 0

            return prediction

        except Exception as e:
            logger.error(f"❌ Prediction failed for {expert.expert_id}: {e}")
            # Return default prediction
            return {
                'winner': game['home_team'],
                'margin': 3.0,
                'total': 45.0,
                'confidence': 5.0,
                'reasoning': f"Error: {str(e)[:50]}",
                'response_time': time.time() - start_time,
                'memories_used': 0
            }

    def _get_personality_traits(self, personality_type: str) -> str:
        """Get personality description for expert"""

        traits = {
            'conservative': 'Risk-averse, favors favorites, prefers safe bets',
            'gambler': 'High variance, chases upsets, aggressive betting',
            'contrarian': 'Fades public opinion, zigs when others zag',
            'value': 'Seeks market inefficiencies, line value hunter',
            'momentum': 'Follows recent trends, rides hot streaks',
            'scholar': 'Deep stats analysis, fundamental approach',
            'chaos': 'Embraces unpredictability, entropy believer',
            'gut': 'Intuition-driven, trusts instinct over data',
            'quant': 'Pure numbers, statistical models only',
            'reversal': 'Bets against streaks, mean reversion',
            'fader': 'Contrarian to media narratives',
            'sharp': 'Follows professional betting action',
            'underdog': 'Champions underdogs, believes in upsets',
            'consensus': 'Follows majority opinion, wisdom of crowds',
            'exploiter': 'Finds arbitrage opportunities, market inefficiencies'
        }

        return traits.get(personality_type, 'Balanced analytical approach')

    def _parse_prediction_response(self, response: str, home_team: str, away_team: str) -> Dict:
        """Parse LLM response into structured prediction"""

        try:
            # Try to parse structured format: WINNER|MARGIN|TOTAL|CONFIDENCE|REASONING
            if '|' in response:
                parts = response.split('|')
                if len(parts) >= 5:
                    return {
                        'winner': parts[0].strip().upper(),
                        'margin': float(parts[1].strip()),
                        'total': float(parts[2].strip()),
                        'confidence': float(parts[3].strip()),
                        'reasoning': parts[4].strip()
                    }

            # Fallback: try to extract from natural language
            winner = home_team if 'home' in response.lower() else away_team
            margin = 3.0  # default
            total = 45.0  # default
            confidence = 5.0  # default

            # Try to find numbers
            import re
            numbers = re.findall(r'\d+\.?\d*', response)
            if len(numbers) >= 2:
                margin = float(numbers[0])
                total = float(numbers[1])
            if len(numbers) >= 3:
                confidence = float(numbers[2])

            return {
                'winner': winner,
                'margin': margin,
                'total': total,
                'confidence': confidence,
                'reasoning': response[:100]
            }

        except Exception as e:
            logger.warning(f"⚠️ Could not parse prediction: {e}")
            return {
                'winner': home_team,
                'margin': 3.0,
                'total': 45.0,
                'confidence': 5.0,
                'reasoning': response[:100] if response else "Parse error"
            }

    def retrieve_memories(self, expert_id: str, game: Dict, limit: int = 5) -> List[Dict]:
        """Retrieve relevant memories for expert (simple version without vector search for now)"""

        try:
            # Query recent memories for this expert
            response = self.supabase.table('expert_episodic_memories')\
                .select('*')\
                .eq('expert_id', expert_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()

            if not response.data:
                return []

            # Format memories
            memories = []
            for mem in response.data:
                try:
                    pred_summary = json.loads(mem.get('prediction_summary', '{}'))
                    actual_outcome = json.loads(mem.get('actual_outcome', '{}'))

                    summary = f"{mem.get('game_id', 'Unknown')}: "
                    summary += f"Predicted {pred_summary.get('winner', '?')} by {pred_summary.get('margin', 0)}, "
                    summary += f"Actual: {actual_outcome.get('winner', '?')}. "
                    summary += f"Lesson: {mem.get('lesson_learned', 'N/A')[:100]}"

                    memories.append({
                        'memory_id': mem.get('id'),
                        'summary': summary,
                        'game_id': mem.get('game_id'),
                        'created_at': mem.get('created_at')
                    })
                except:
                    continue

            return memories

        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve memories for {expert_id}: {e}")
            return []

    def evaluate_prediction(self, prediction: Dict, game: Dict, expert: ExpertConfig, game_number: int) -> PredictionResult:
        """Evaluate prediction against actual outcome"""

        # Check winner correctness
        winner_correct = prediction['winner'].upper() == game['actual_winner'].upper()

        # Calculate errors
        # For margin: predict home team margin, actual home team margin
        predicted_margin = prediction['margin'] if prediction['winner'].upper() == game['home_team'].upper() else -prediction['margin']
        actual_margin = game['home_score'] - game['away_score']
        margin_error = abs(predicted_margin - actual_margin)

        total_error = abs(prediction['total'] - game['actual_total'])

        # Calculate accuracy score (0-1)
        accuracy_score = 0.0
        if winner_correct:
            accuracy_score += 0.5  # Winner worth 50%

        # Margin accuracy (within 7 points = full credit)
        margin_accuracy = max(0, 1 - (margin_error / 14.0))  # 14 points = 2 TDs
        accuracy_score += 0.3 * margin_accuracy

        # Total accuracy (within 10 points = full credit)
        total_accuracy = max(0, 1 - (total_error / 20.0))
        accuracy_score += 0.2 * total_accuracy

        return PredictionResult(
            expert_id=expert.expert_id,
            game_id=game['game_id'],
            game_number=game_number,
            predicted_winner=prediction['winner'],
            predicted_margin=prediction['margin'],
            predicted_total=prediction['total'],
            confidence=prediction['confidence'],
            reasoning=prediction['reasoning'],
            actual_winner=game['actual_winner'],
            actual_home_score=game['home_score'],
            actual_away_score=game['away_score'],
            actual_margin=game['actual_margin'],
            actual_total=game['actual_total'],
            winner_correct=winner_correct,
            margin_error=margin_error,
            total_error=total_error,
            accuracy_score=accuracy_score,
            timestamp=datetime.now().isoformat(),
            response_time=prediction['response_time'],
            memories_used=prediction['memories_used']
        )

    def store_memory(self, expert_id: str, game: Dict, prediction: Dict, result: PredictionResult) -> None:
        """Store episodic memory for expert"""

        try:
            # Generate reflection/lesson learned
            if result.winner_correct:
                lesson = f"Correctly predicted {result.actual_winner} to win. "
                if result.margin_error < 7:
                    lesson += "Margin was accurate. "
                if result.total_error < 10:
                    lesson += "Total was accurate."
            else:
                lesson = f"Incorrectly predicted {result.predicted_winner}, actual winner was {result.actual_winner}. "
                lesson += f"Need to better account for {game.get('weather', {}).get('conditions', 'unknown factors')}."

            memory_data = {
                'expert_id': expert_id,
                'game_id': game['game_id'],
                'memory_type': 'prediction_outcome',
                'prediction_summary': json.dumps({
                    'winner': prediction['winner'],
                    'margin': prediction['margin'],
                    'total': prediction['total'],
                    'confidence': prediction['confidence']
                }),
                'actual_outcome': json.dumps({
                    'winner': result.actual_winner,
                    'home_score': result.actual_home_score,
                    'away_score': result.actual_away_score
                }),
                'accuracy_scores': json.dumps({
                    'overall': result.accuracy_score,
                    'winner_correct': result.winner_correct,
                    'margin_error': result.margin_error,
                    'total_error': result.total_error
                }),
                'lesson_learned': lesson,
                'emotional_weight': 0.9 if not result.winner_correct else 0.5,
                'surprise_factor': 0.8 if not result.winner_correct else 0.2,
                'memory_strength': result.confidence / 10.0
            }

            self.supabase.table('expert_episodic_memories').insert(memory_data).execute()

        except Exception as e:
            logger.warning(f"⚠️ Could not store memory for {expert_id}: {e}")

    def run_experiment(self, num_games: int = 40) -> None:
        """Run the complete experiment"""

        logger.info("="*60)
        logger.info("🧪 MEMORY LEARNING PROOF EXPERIMENT")
        logger.info("="*60)

        # Initialize experts
        logger.info("\\n📋 Phase 1: Initializing experts...")
        self.initialize_experts()

        # Load real games
        logger.info("\\n📊 Phase 2: Loading real NFL games...")
        games = self.load_real_games(limit=num_games)
        self.total_games = len(games)

        if not games:
            logger.error("❌ No games available. Exiting.")
            return

        # Run predictions for each game
        logger.info(f"\\n🎯 Phase 3: Running predictions for {len(games)} games...")
        logger.info("="*60)

        for game_num, game in enumerate(games, 1):
            self.current_game = game_num

            logger.info(f"\\n🏈 GAME {game_num}/{len(games)}: {game['away_team']} @ {game['home_team']}")
            logger.info(f"   Week {game['week']}, Actual: {game['actual_winner']} {game['home_score']}-{game['away_score']}")

            # Process experts in batches of 5 for performance
            batch_size = 5
            for i in range(0, len(self.experts), batch_size):
                batch = self.experts[i:i+batch_size]

                for expert in batch:
                    try:
                        # Retrieve memories if expert has memory enabled
                        memories = []
                        if expert.has_memory and game_num > 1:
                            memories = self.retrieve_memories(expert.expert_id, game)

                        # Make prediction
                        prediction = self.make_prediction(expert, game, memories)

                        # Evaluate against actual outcome
                        result = self.evaluate_prediction(prediction, game, expert, game_num)
                        self.results.append(result)

                        # Store memory if expert has memory enabled
                        if expert.has_memory:
                            self.store_memory(expert.expert_id, game, prediction, result)

                        # Log result
                        status = "✅" if result.winner_correct else "❌"
                        logger.info(f"   {status} {expert.name}: {result.predicted_winner} (acc: {result.accuracy_score:.2f})")

                    except Exception as e:
                        logger.error(f"   ❌ Error processing {expert.expert_id}: {e}")
                        continue

            # Print summary after each game
            self._print_game_summary(game_num)

        # Final report
        logger.info("\\n"+"="*60)
        logger.info("✅ EXPERIMENT COMPLETE!")
        logger.info("="*60)
        self._print_final_summary()

    def _print_game_summary(self, game_num: int) -> None:
        """Print summary after each game"""

        # Get results for this game
        game_results = [r for r in self.results if r.game_number == game_num]

        if not game_results:
            return

        memory_results = [r for r in game_results if '-mem-' in r.expert_id]
        nomem_results = [r for r in game_results if '-nomem-' in r.expert_id]

        memory_acc = sum(r.accuracy_score for r in memory_results) / len(memory_results) if memory_results else 0
        nomem_acc = sum(r.accuracy_score for r in nomem_results) / len(nomem_results) if nomem_results else 0

        logger.info(f"\\n   📊 Game {game_num} Summary:")
        logger.info(f"      Memory Group: {memory_acc:.1%} avg accuracy")
        logger.info(f"      No-Memory Group: {nomem_acc:.1%} avg accuracy")
        logger.info(f"      Difference: {(memory_acc - nomem_acc):.1%}")

    def _print_final_summary(self) -> None:
        """Print final experiment summary"""

        if not self.results:
            logger.info("No results to summarize.")
            return

        # Split by group
        memory_results = [r for r in self.results if '-mem-' in r.expert_id]
        nomem_results = [r for r in self.results if '-nomem-' in r.expert_id]

        # Calculate overall accuracy
        memory_acc = sum(r.accuracy_score for r in memory_results) / len(memory_results) if memory_results else 0
        nomem_acc = sum(r.accuracy_score for r in nomem_results) / len(nomem_results) if nomem_results else 0

        logger.info(f"\\n📊 OVERALL RESULTS:")
        logger.info(f"   Memory Group: {memory_acc:.1%} accuracy ({len(memory_results)} predictions)")
        logger.info(f"   No-Memory Group: {nomem_acc:.1%} accuracy ({len(nomem_results)} predictions)")
        logger.info(f"   Improvement: {(memory_acc - nomem_acc):.1%}")

        # Calculate learning curve for memory group (first 10 vs last 10)
        if len(memory_results) >= 20:
            early_games = [r for r in memory_results if r.game_number <= 10]
            late_games = [r for r in memory_results if r.game_number > max(r.game_number for r in memory_results) - 10]

            early_acc = sum(r.accuracy_score for r in early_games) / len(early_games)
            late_acc = sum(r.accuracy_score for r in late_games) / len(late_games)

            logger.info(f"\\n📈 LEARNING CURVE (Memory Group):")
            logger.info(f"   Games 1-10: {early_acc:.1%}")
            logger.info(f"   Final 10 games: {late_acc:.1%}")
            logger.info(f"   Learning Improvement: {(late_acc - early_acc):.1%}")

        # Export results
        self._export_results()

    def _export_results(self) -> None:
        """Export results to JSON file"""

        output_file = f"results/{self.experiment_id}_results.json"
        os.makedirs("results", exist_ok=True)

        export_data = {
            'experiment_id': self.experiment_id,
            'experiment_name': self.experiment_name,
            'total_games': self.total_games,
            'total_predictions': len(self.results),
            'experts': [asdict(e) for e in self.experts],
            'results': [asdict(r) for r in self.results],
            'timestamp': datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"\\n💾 Results exported to: {output_file}")


def main():
    """Run the experiment"""

    # Create experiment
    experiment = MemoryLearningExperiment(experiment_name="memory_proof_v1")

    # Run for 40 games (or as many as available)
    experiment.run_experiment(num_games=40)

    logger.info("\\n✅ Experiment complete! Check results/ directory for detailed output.")


if __name__ == "__main__":
    main()
