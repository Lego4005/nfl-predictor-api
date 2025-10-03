#!/usr/bin/env python3
"""
Run experiment with comprehensive tracking

Generates:
- CSV file for spreadsheet analysis
- HTML dashboard with charts
- SQLite database for queries
- Text summary
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import time
from learning_tracker import LearningTracker
from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.prompts.natural_language_prompt import build_natural_language_prompt, parse_natural_language_response
from dotenv import load_dotenv

load_dotenv()


class SimpleGameData:
    def __init__(self, game_dict):
        self.away_team = game_dict['away_team']
        self.home_team = game_dict['home_team']
        self.season = game_dict['season']
        self.week = game_dict['week']
        self.game_date = game_dict.get('game_date', 'Unknown')

        self.home_team_stats = type('obj', (object,), {
            'coach': game_dict.get('home_coach', 'Unknown'),
            'qb': game_dict.get('home_qb_name', 'Unknown'),
            'rest_days': game_dict.get('home_rest', 7),
            'wins': 0, 'losses': 0, 'points_per_game': 'N/A',
            'points_allowed_per_game': 'N/A', 'recent_form': 'N/A'
        })()

        self.away_team_stats = type('obj', (object,), {
            'coach': game_dict.get('away_coach', 'Unknown'),
            'qb': game_dict.get('away_qb_name', 'Unknown'),
            'rest_days': game_dict.get('away_rest', 7),
            'wins': 0, 'losses': 0, 'points_per_game': 'N/A',
            'points_allowed_per_game': 'N/A', 'recent_form': 'N/A'
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


async def main():
    print("🔬 TRACKED LEARNING EXPERIMENT\n")

    # Initialize
    tracker = LearningTracker("DeepSeek_v3.1_Learning")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    memory_service = SupabaseEpisodicMemoryManager(supabase)
    llm_service = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))

    # Fetch games
    print("📊 Fetching games...")
    response = supabase.table('nfl_games').select('*').eq('season', 2024).or_(
        'home_team.eq.KC,away_team.eq.KC'
    ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
        'game_date', desc=False
    ).limit(20).execute()

    games = response.data
    print(f"✅ Loaded {len(games)} games\n")

    correct_count = 0

    for i, game in enumerate(games, 1):
        print(f"\n{'='*80}")
        print(f"🏈 GAME {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")
        print(f"{'='*80}")

        # Get memories
        memories = await memory_service.retrieve_memories(
            'tracked_experiment',
            {'home_team': game['home_team'], 'away_team': game['away_team']},
            limit=5
        )

        print(f"🧠 Memories available: {len(memories)}")

        # Make prediction
        game_data = SimpleGameData(game)
        system_msg, user_msg = build_natural_language_prompt(
            "You are an NFL expert. Learn from past experiences.",
            game_data,
            memories
        )

        start = time.time()
        response = llm_service.generate_completion(
            system_message=system_msg,
            user_message=user_msg,
            temperature=0.6,
            max_tokens=500,
            model="deepseek/deepseek-chat-v3.1:free"
        )
        response_time = time.time() - start

        parsed = parse_natural_language_response(response.content)
        actual = 'home' if game['home_score'] > game['away_score'] else 'away'
        is_correct = parsed['winner'] == actual

        if is_correct:
            correct_count += 1

        running_accuracy = correct_count / i

        print(f"🎯 Predicted: {parsed['winner']} ({parsed['confidence']:.0%})")
        print(f"   Actual: {actual} ({game['away_score']}-{game['home_score']})")
        print(f"   {'✅ CORRECT' if is_correct else '❌ WRONG'}")
        print(f"📊 Running: {correct_count}/{i} ({running_accuracy:.1%})")

        # Track
        tracker.log_prediction(
            i, game, memories, parsed, actual, response_time, running_accuracy
        )

        if i % 5 == 0:
            tracker.log_accuracy_point(
                i, correct_count, i,
                parsed['confidence'],
                len(memories)
            )

        # Store memory with correct API
        try:
            memory_data = {
                'memory_type': 'prediction_outcome',
                'prediction_data': {
                    'winner': parsed['winner'],
                    'confidence': parsed['confidence'],
                    'reasoning': parsed['reasoning'][:200]
                },
                'actual_outcome': {
                    'winner': actual,
                    'home_score': game['home_score'],
                    'away_score': game['away_score']
                },
                'contextual_factors': [
                    {'factor': 'home_team', 'value': game['home_team']},
                    {'factor': 'away_team', 'value': game['away_team']},
                    {'factor': 'week', 'value': str(game['week'])},
                    {'factor': 'season', 'value': str(game['season'])}
                ],
                'lessons_learned': [
                    {
                        'lesson': f"{'Successfully' if is_correct else 'Incorrectly'} predicted {parsed['winner']} would win in {game['away_team']} @ {game['home_team']}",
                        'category': 'prediction_accuracy',
                        'confidence': 0.8 if is_correct else 0.6
                    }
                ],
                'emotional_state': 'confident' if is_correct else 'disappointed',
                'emotional_intensity': 0.7 if is_correct else 0.5
            }

            await memory_service.store_memory(
                expert_id='tracked_experiment',
                game_id=game.get('game_id', f"{game['season']}_W{game['week']}_{game['away_team']}_{game['home_team']}"),
                memory_data=memory_data
            )
            print(f"💾 Memory stored successfully")
        except Exception as e:
            print(f"⚠️  Memory storage failed: {e}")

    # Generate outputs
    print(f"\n\n{'='*80}")
    print("📊 GENERATING REPORTS...")
    print(f"{'='*80}\n")

    tracker.generate_html_dashboard()
    tracker.generate_summary()

    print(f"\n✅ Experiment complete!")
    print(f"📁 All files saved to: {tracker.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
