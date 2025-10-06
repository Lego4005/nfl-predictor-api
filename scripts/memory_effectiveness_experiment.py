#!/usr/bin/env python3
"""
Controlled Memory Effectiveness Experiment

Tests whether episodic memory actually improves prediction accuracy.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client, Client
from src.services.local_llm_service import LocalLLMService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.prompts.natural_language_prompt import build_natural_language_prompt, parse_natural_language_response
import os
from dotenv import load_dotenv

load_dotenv()


class SimpleGameData:
    """Game data using REAL database fields"""
    def __init__(self, game_dict):
        self.away_team = game_dict['away_team']
        self.home_team = game_dict['home_team']
        self.season = game_dict['season']
        self.week = game_dict['week']
        self.game_date = game_dict.get('game_date', 'Unknown')

        # REAL team data from database
        self.home_team_stats = type('obj', (object,), {
            'wins': 0, 'losses': 0,
            'points_per_game': 'N/A',
            'points_allowed_per_game': 'N/A',
            'recent_form': 'N/A',
            'coach': game_dict.get('home_coach', 'Unknown'),
            'qb': game_dict.get('home_qb_name', 'Unknown'),
            'rest_days': game_dict.get('home_rest', 7)
        })()

        self.away_team_stats = type('obj', (object,), {
            'wins': 0, 'losses': 0,
            'points_per_game': 'N/A',
            'points_allowed_per_game': 'N/A',
            'recent_form': 'N/A',
            'coach': game_dict.get('away_coach', 'Unknown'),
            'qb': game_dict.get('away_qb_name', 'Unknown'),
            'rest_days': game_dict.get('away_rest', 7)
        })()

        # REAL venue data
        self.venue_info = type('obj', (object,), {
            'stadium_name': game_dict.get('stadium', 'Unknown'),
            'surface': game_dict.get('surface', 'grass'),
            'roof': game_dict.get('roof', 'outdoor'),
            'is_division_game': game_dict.get('div_game', False)
        })()

        # REAL weather data
        self.weather_conditions = type('obj', (object,), {
            'temperature': game_dict.get('weather_temperature', 'N/A'),
            'wind_speed': game_dict.get('weather_wind_mph', 'N/A'),
            'conditions': game_dict.get('weather_description', 'N/A')
        })()

        # REAL betting lines
        self.public_betting = type('obj', (object,), {
            'spread': game_dict.get('spread_line', 'N/A'),
            'total': game_dict.get('total_line', 'N/A'),
            'public_percentage': 'N/A'
        })()


class MemoryExperiment:
    """Controlled experiment to test memory effectiveness"""

    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase = create_client(supabase_url, supabase_key)

        self.llm_service = LocalLLMService()
        self.memory_service = SupabaseEpisodicMemoryManager(self.supabase)

    async def fetch_test_games(self, num_games: int = 20, team: str = "KC", season: int = 2024):
        """Fetch sequential games"""
        logger.info(f"📊 Fetching {num_games} games for {team} in {season}...")

        response = self.supabase.table('nfl_games').select('*').eq(
            'season', season
        ).or_(
            f'home_team.eq.{team},away_team.eq.{team}'
        ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
            'game_date', desc=False
        ).limit(num_games).execute()

        games = response.data
        logger.info(f"✅ Fetched {len(games)} games")
        return games

    async def make_prediction(self, game: Dict, memories: List = None) -> Dict:
        """Make a single prediction using LLM"""
        game_data = SimpleGameData(game)

        # Build prompt
        system_msg, user_msg = build_natural_language_prompt(
            expert_personality="You are The Conservative Analyzer, a risk-averse NFL prediction expert.",
            game_data=game_data,
            episodic_memories=memories or []
        )

        # Get LLM prediction
        response = self.llm_service.generate_completion(
            system_message=system_msg,
            user_message=user_msg,
            temperature=0.6,
            max_tokens=300,
            model="openai/gpt-oss-20b"
        )

        # Parse response
        parsed = parse_natural_language_response(response.content)

        return {
            'predicted_winner': parsed['winner'],
            'confidence': parsed['confidence'],
            'spread': parsed['spread'],
            'total': parsed['total'],
            'reasoning': parsed['reasoning']
        }

    async def store_memory(self, game: Dict, prediction: Dict, actual_winner: str):
        """Store prediction as memory for future use"""
        try:
            memory_data = {
                'expert_id': 'conservative_analyzer',
                'game_context': {
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'season': game['season'],
                    'week': game['week']
                },
                'prediction_data': {
                    'winner': prediction['predicted_winner'],
                    'confidence': prediction['confidence']
                },
                'actual_outcome': {
                    'winner': actual_winner
                },
                'was_correct': prediction['predicted_winner'] == actual_winner
            }

            await self.memory_service.store_memory(**memory_data)
        except Exception as e:
            logger.warning(f"Failed to store memory: {e}")

    async def run_with_memory(self, games: List[Dict]) -> Dict:
        """Run WITH memory"""
        logger.info("\n" + "=" * 80)
        logger.info("🧠 EXPERIMENT 1: WITH MEMORY")
        logger.info("=" * 80)

        correct = 0
        predictions = []

        for i, game in enumerate(games, 1):
            logger.info(f"\n🏈 Game {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")

            # Retrieve memories
            game_context = {
                'home_team': game['home_team'],
                'away_team': game['away_team']
            }
            memories = await self.memory_service.retrieve_memories(
                'conservative_analyzer', game_context, limit=3
            )
            logger.info(f"   🧠 Retrieved {len(memories)} memories")

            # Make prediction
            pred = await self.make_prediction(game, memories)
            actual = 'home' if game['home_score'] > game['away_score'] else 'away'
            correct_pred = pred['predicted_winner'] == actual

            if correct_pred:
                correct += 1

            predictions.append({
                'game': f"{game['away_team']} @ {game['home_team']}",
                'predicted': pred['predicted_winner'],
                'actual': actual,
                'correct': correct_pred,
                'memories_used': len(memories)
            })

            logger.info(f"   Predicted: {pred['predicted_winner']} ({pred['confidence']:.0%})")
            logger.info(f"   Actual: {actual}")
            logger.info(f"   {'✅ CORRECT' if correct_pred else '❌ WRONG'}")
            logger.info(f"   Accuracy: {correct}/{i} ({correct/i*100:.1f}%)")

            # Store as memory
            await self.store_memory(game, pred, actual)

        return {
            'accuracy': correct / len(games),
            'correct': correct,
            'total': len(games),
            'predictions': predictions
        }

    async def run_without_memory(self, games: List[Dict]) -> Dict:
        """Run WITHOUT memory (baseline)"""
        logger.info("\n" + "=" * 80)
        logger.info("🚫 EXPERIMENT 2: WITHOUT MEMORY (BASELINE)")
        logger.info("=" * 80)

        correct = 0
        predictions = []

        for i, game in enumerate(games, 1):
            logger.info(f"\n🏈 Game {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")

            # Make prediction WITHOUT memories
            pred = await self.make_prediction(game, memories=None)
            actual = 'home' if game['home_score'] > game['away_score'] else 'away'
            correct_pred = pred['predicted_winner'] == actual

            if correct_pred:
                correct += 1

            predictions.append({
                'game': f"{game['away_team']} @ {game['home_team']}",
                'predicted': pred['predicted_winner'],
                'actual': actual,
                'correct': correct_pred
            })

            logger.info(f"   Predicted: {pred['predicted_winner']} ({pred['confidence']:.0%})")
            logger.info(f"   Actual: {actual}")
            logger.info(f"   {'✅ CORRECT' if correct_pred else '❌ WRONG'}")
            logger.info(f"   Accuracy: {correct}/{i} ({correct/i*100:.1f}%)")

        return {
            'accuracy': correct / len(games),
            'correct': correct,
            'total': len(games),
            'predictions': predictions
        }

    def generate_report(self, with_mem: Dict, without_mem: Dict):
        """Generate comparison report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 MEMORY EFFECTIVENESS REPORT")
        logger.info("=" * 80)

        logger.info(f"\n🧠 WITH MEMORY:")
        logger.info(f"   Accuracy: {with_mem['accuracy']:.1%}")
        logger.info(f"   Correct: {with_mem['correct']}/{with_mem['total']}")

        logger.info(f"\n🚫 WITHOUT MEMORY:")
        logger.info(f"   Accuracy: {without_mem['accuracy']:.1%}")
        logger.info(f"   Correct: {without_mem['correct']}/{without_mem['total']}")

        improvement = with_mem['accuracy'] - without_mem['accuracy']
        logger.info(f"\n📈 IMPROVEMENT: {improvement:+.1%}")

        if improvement > 0.05:
            logger.info(f"✅ Memory shows meaningful improvement!")
        elif improvement > 0:
            logger.info(f"⚠️  Memory shows slight improvement")
        else:
            logger.info(f"❌ Memory does not improve accuracy")


async def main():
    logger.info("🧪 MEMORY EFFECTIVENESS EXPERIMENT\n")

    exp = MemoryExperiment()
    games = await exp.fetch_test_games(num_games=20, team="KC", season=2024)

    if len(games) < 10:
        logger.error(f"Not enough games: {len(games)}")
        return

    with_mem = await exp.run_with_memory(games)
    without_mem = await exp.run_without_memory(games)

    exp.generate_report(with_mem, without_mem)

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'with_memory': with_mem,
        'without_memory': without_mem,
        'improvement': with_mem['accuracy'] - without_mem['accuracy']
    }

    os.makedirs('logs', exist_ok=True)
    output = f"logs/memory_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n💾 Results saved: {output}")


if __name__ == "__main__":
    asyncio.run(main())
