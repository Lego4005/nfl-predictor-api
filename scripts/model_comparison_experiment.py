#!/usr/bin/env python3
"""
Model Comparison Experiment

Tests multiple models (local + cloud) to see which performs best for NFL predictions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import asyncio
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client
from src.services.local_llm_service import LocalLLMService
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.prompts.natural_language_prompt import build_natural_language_prompt, parse_natural_language_response
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

        self.venue_info = type('obj', (object,), {
            'stadium_name': game_dict.get('stadium', 'Unknown'),
            'surface': game_dict.get('surface', 'grass'),
            'roof': game_dict.get('roof', 'outdoor'),
            'is_division_game': game_dict.get('div_game', False)
        })()

        self.weather_conditions = type('obj', (object,), {
            'temperature': game_dict.get('weather_temperature', 'N/A'),
            'wind_speed': game_dict.get('weather_wind_mph', 'N/A'),
            'conditions': game_dict.get('weather_description', 'N/A')
        })()

        self.public_betting = type('obj', (object,), {
            'spread': game_dict.get('spread_line', 'N/A'),
            'total': game_dict.get('total_line', 'N/A'),
            'public_percentage': 'N/A'
        })()


async def test_model(model_name: str, llm_service, games, memory_service):
    """Test a single model"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🤖 TESTING: {model_name}")
    logger.info(f"{'='*80}")

    correct = 0
    predictions = []
    total_time = 0

    for i, game in enumerate(games, 1):
        logger.info(f"\n🏈 Game {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")

        game_data = SimpleGameData(game)

        # Get memories
        memories = await memory_service.retrieve_memories(
            'conservative_analyzer',
            {'home_team': game['home_team'], 'away_team': game['away_team']},
            limit=3
        )

        # Build prompt
        system_msg, user_msg = build_natural_language_prompt(
            "You are The Conservative Analyzer, a risk-averse NFL prediction expert.",
            game_data,
            memories
        )

        # Get prediction
        start = asyncio.get_event_loop().time()
        response = llm_service.generate_completion(
            system_message=system_msg,
            user_message=user_msg,
            temperature=0.6,
            max_tokens=300,
            model=model_name
        )
        elapsed = asyncio.get_event_loop().time() - start
        total_time += elapsed

        # Parse
        parsed = parse_natural_language_response(response.content)
        actual = 'home' if game['home_score'] > game['away_score'] else 'away'
        correct_pred = parsed['winner'] == actual

        if correct_pred:
            correct += 1

        predictions.append({
            'game': f"{game['away_team']} @ {game['home_team']}",
            'predicted': parsed['winner'],
            'actual': actual,
            'correct': correct_pred,
            'time': elapsed
        })

        logger.info(f"   Predicted: {parsed['winner']} ({parsed['confidence']:.0%})")
        logger.info(f"   Actual: {actual}")
        logger.info(f"   {'✅ CORRECT' if correct_pred else '❌ WRONG'}")
        logger.info(f"   Time: {elapsed:.2f}s")
        logger.info(f"   Accuracy: {correct}/{i} ({correct/i*100:.1f}%)")

    accuracy = correct / len(games)
    avg_time = total_time / len(games)

    logger.info(f"\n📊 {model_name} RESULTS:")
    logger.info(f"   Accuracy: {accuracy:.1%} ({correct}/{len(games)})")
    logger.info(f"   Avg Time: {avg_time:.2f}s per game")
    logger.info(f"   Total Time: {total_time:.1f}s")

    return {
        'model': model_name,
        'accuracy': accuracy,
        'correct': correct,
        'total': len(games),
        'avg_time': avg_time,
        'total_time': total_time,
        'predictions': predictions
    }


async def main():
    logger.info("🧪 MODEL COMPARISON EXPERIMENT\n")

    # Initialize services
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    memory_service = SupabaseEpisodicMemoryManager(supabase)

    # Fetch test games
    logger.info("📊 Fetching test games...")
    response = supabase.table('nfl_games').select('*').eq(
        'season', 2024
    ).or_(
        'home_team.eq.KC,away_team.eq.KC'
    ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
        'game_date', desc=False
    ).limit(20).execute()

    games = response.data
    logger.info(f"✅ Loaded {len(games)} games\n")

    # Models to test
    models_to_test = [
        ('local', 'openai/gpt-oss-20b', LocalLLMService()),
        ('openrouter', 'anthropic/claude-sonnet-4.5', OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))),
        ('openrouter', 'deepseek/deepseek-chat-v3.1:free', OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))),
        ('openrouter', 'x-ai/grok-4-fast:free', OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY')))
    ]

    results = []

    for service_type, model_name, service in models_to_test:
        try:
            result = await test_model(model_name, service, games, memory_service)
            results.append(result)
        except Exception as e:
            logger.error(f"❌ {model_name} failed: {e}")
            results.append({
                'model': model_name,
                'accuracy': 0,
                'error': str(e)
            })

    # Generate comparison report
    logger.info(f"\n{'='*80}")
    logger.info("📊 MODEL COMPARISON REPORT")
    logger.info(f"{'='*80}\n")

    # Sort by accuracy
    results.sort(key=lambda x: x.get('accuracy', 0), reverse=True)

    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result['model']}")
        logger.info(f"   Accuracy: {result.get('accuracy', 0):.1%}")
        if 'avg_time' in result:
            logger.info(f"   Avg Time: {result['avg_time']:.2f}s")
        if 'error' in result:
            logger.info(f"   Error: {result['error']}")
        logger.info("")

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'num_games': len(games),
        'results': results
    }

    os.makedirs('logs', exist_ok=True)
    filename = f"logs/model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"💾 Results saved: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
