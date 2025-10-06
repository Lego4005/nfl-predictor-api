#!/usr/bin/env python3
"""
Deep Learning Analysis - Verify the AI is actually learning from memories

Analyzes:
1. Memory accumulation over time
2. Accuracy improvement as memories grow
3. How memories influence predictions
4. Reasoning quality and evolution
5. Confidence calibration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import asyncio
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.prompts.natural_language_prompt import build_natural_language_prompt, parse_natural_language_response
from dotenv import load_dotenv
from learning_tracker import LearningTracker

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


async def analyze_learning_progression(games, llm_service, memory_service):
    """Analyze how the AI learns over time"""

    logger.info("="*80)
    logger.info("🔬 DEEP LEARNING ANALYSIS")
    logger.info("="*80)
    logger.info("")

    results = []
    memory_counts = []
    accuracy_by_batch = []

    # Clear existing memories for clean test
    logger.info("🧹 Clearing existing memories for clean test...")
    try:
        # Delete all memories for this expert to start fresh
        result = memory_service.supabase.table('expert_episodic_memories').delete().eq(
            'expert_id', 'conservative_analyzer'
        ).execute()
        logger.info(f"✅ Cleared old memories\n")
    except Exception as e:
        logger.warning(f"⚠️  Could not clear memories: {e}\n")

    for i, game in enumerate(games, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"🏈 GAME {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")
        logger.info(f"   Week {game['week']}, {game['game_date']}")
        logger.info(f"{'='*80}")

        game_data = SimpleGameData(game)

        # 1. Check how many memories exist BEFORE this prediction
        game_context = {
            'home_team': game['home_team'],
            'away_team': game['away_team']
        }
        memories = await memory_service.retrieve_memories(
            'conservative_analyzer',
            game_context,
            limit=5
        )

        memory_count = len(memories)
        memory_counts.append(memory_count)

        logger.info(f"\n📊 MEMORY STATE:")
        logger.info(f"   Memories available: {memory_count}")

        # 2. Show what memories are being used
        if memories:
            logger.info(f"\n🧠 RETRIEVED MEMORIES:")
            for j, mem in enumerate(memories, 1):
                pred_data = mem.get('prediction_data', {})
                actual = mem.get('actual_outcome', {})
                lessons = mem.get('lessons_learned', [])

                was_correct = pred_data.get('winner') == actual.get('winner')
                logger.info(f"\n   Memory {j}:")
                logger.info(f"      Prediction: {pred_data.get('winner')} (conf: {pred_data.get('confidence', 0):.0%})")
                logger.info(f"      Actual: {actual.get('winner')}")
                logger.info(f"      Result: {'✅ CORRECT' if was_correct else '❌ WRONG'}")
                if lessons:
                    logger.info(f"      Lesson: {lessons[0].get('lesson', 'N/A')}")

        # 3. Make prediction
        system_msg, user_msg = build_natural_language_prompt(
            "You are The Conservative Analyzer. Learn from your past experiences.",
            game_data,
            memories
        )

        logger.info(f"\n🤖 MAKING PREDICTION...")
        response = llm_service.generate_completion(
            system_message=system_msg,
            user_message=user_msg,
            temperature=0.6,
            max_tokens=500,
            model="deepseek/deepseek-chat-v3.1:free"
        )

        parsed = parse_natural_language_response(response.content)
        actual_winner = 'home' if game['home_score'] > game['away_score'] else 'away'
        is_correct = parsed['winner'] == actual_winner

        # 4. Show reasoning
        logger.info(f"\n💭 REASONING:")
        reasoning_preview = parsed['reasoning'][:200] + "..." if len(parsed['reasoning']) > 200 else parsed['reasoning']
        logger.info(f"   {reasoning_preview}")

        # 5. Show prediction
        logger.info(f"\n🎯 PREDICTION:")
        logger.info(f"   Predicted: {parsed['winner']} (confidence: {parsed['confidence']:.0%})")
        logger.info(f"   Actual: {actual_winner} ({game['away_score']}-{game['home_score']})")
        logger.info(f"   Result: {'✅ CORRECT' if is_correct else '❌ WRONG'}")

        # 6. Store this prediction as a memory for future games
        try:
            game_id = f"{game['season']}_W{game['week']}_{game['away_team']}_{game['home_team']}"

            memory_data = {
                'memory_type': 'prediction_outcome',
                'emotional_state': 'satisfied' if is_correct else 'disappointed',
                'prediction_data': {
                    'winner': parsed['winner'],
                    'confidence': parsed['confidence'],
                    'reasoning': parsed['reasoning'][:200]
                },
                'actual_outcome': {
                    'winner': actual_winner,
                    'home_score': game['home_score'],
                    'away_score': game['away_score']
                },
                'contextual_factors': [
                    {'factor': 'home_team', 'value': game['home_team']},
                    {'factor': 'away_team', 'value': game['away_team']},
                    {'factor': 'season', 'value': str(game['season'])},
                    {'factor': 'week', 'value': str(game['week'])}
                ],
                'lessons_learned': [
                    {
                        'lesson': f"{'Correctly' if is_correct else 'Incorrectly'} predicted {parsed['winner']} for {game['away_team']} @ {game['home_team']}",
                        'category': 'prediction_accuracy',
                        'confidence': 0.8 if is_correct else 0.6
                    }
                ],
                'emotional_intensity': 0.7 if is_correct else 0.6,
                'memory_vividness': 0.8
            }

            success = await memory_service.store_memory('conservative_analyzer', game_id, memory_data)
            if success:
                logger.info(f"\n💾 Memory stored successfully!")
            else:
                logger.warning(f"\n⚠️  Memory storage returned False")
        except Exception as e:
            logger.warning(f"\n⚠️  Failed to store memory: {e}")

        # 7. Track results
        results.append({
            'game_num': i,
            'game': f"{game['away_team']} @ {game['home_team']}",
            'memories_available': memory_count,
            'predicted': parsed['winner'],
            'actual': actual_winner,
            'correct': is_correct,
            'confidence': parsed['confidence'],
            'reasoning': parsed['reasoning'][:100]
        })

        # 8. Calculate running accuracy
        correct_so_far = sum(1 for r in results if r['correct'])
        accuracy = correct_so_far / len(results)

        logger.info(f"\n📈 RUNNING STATS:")
        logger.info(f"   Accuracy: {correct_so_far}/{len(results)} ({accuracy:.1%})")
        logger.info(f"   Memories accumulated: {memory_count} → {memory_count + 1}")

        # Track accuracy by batch
        if i % 5 == 0:
            batch_results = results[-5:]
            batch_correct = sum(1 for r in batch_results if r['correct'])
            batch_accuracy = batch_correct / len(batch_results)
            accuracy_by_batch.append({
                'games': f"{i-4}-{i}",
                'accuracy': batch_accuracy,
                'avg_memories': sum(memory_counts[-5:]) / 5
            })
            logger.info(f"\n📊 BATCH {len(accuracy_by_batch)} (Games {i-4}-{i}):")
            logger.info(f"   Accuracy: {batch_correct}/5 ({batch_accuracy:.1%})")
            logger.info(f"   Avg memories: {sum(memory_counts[-5:]) / 5:.1f}")

    # Final analysis
    logger.info(f"\n\n{'='*80}")
    logger.info("📊 LEARNING PROGRESSION ANALYSIS")
    logger.info(f"{'='*80}\n")

    logger.info("🎯 ACCURACY BY BATCH (5 games each):")
    for batch in accuracy_by_batch:
        logger.info(f"   Games {batch['games']}: {batch['accuracy']:.1%} (avg {batch['avg_memories']:.1f} memories)")

    # Check if accuracy improves
    if len(accuracy_by_batch) >= 2:
        first_half_acc = sum(b['accuracy'] for b in accuracy_by_batch[:len(accuracy_by_batch)//2]) / (len(accuracy_by_batch)//2)
        second_half_acc = sum(b['accuracy'] for b in accuracy_by_batch[len(accuracy_by_batch)//2:]) / (len(accuracy_by_batch) - len(accuracy_by_batch)//2)

        logger.info(f"\n📈 LEARNING TREND:")
        logger.info(f"   First half accuracy: {first_half_acc:.1%}")
        logger.info(f"   Second half accuracy: {second_half_acc:.1%}")
        logger.info(f"   Improvement: {(second_half_acc - first_half_acc):+.1%}")

        if second_half_acc > first_half_acc:
            logger.info(f"\n✅ LEARNING CONFIRMED: Accuracy improved as memories accumulated!")
        else:
            logger.info(f"\n⚠️  NO CLEAR LEARNING: Accuracy did not improve with more memories")

    # Save detailed results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_games': len(games),
        'results': results,
        'accuracy_by_batch': accuracy_by_batch,
        'final_accuracy': sum(1 for r in results if r['correct']) / len(results)
    }

    os.makedirs('logs', exist_ok=True)
    filename = f"logs/learning_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"\n💾 Detailed results saved: {filename}")

    return output


async def main():
    logger.info("🔬 DEEP LEARNING ANALYSIS\n")

    # Initialize services
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    memory_service = SupabaseEpisodicMemoryManager(supabase)
    llm_service = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))

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

    # Run analysis
    await analyze_learning_progression(games, llm_service, memory_service)


if __name__ == "__main__":
    asyncio.run(main())
