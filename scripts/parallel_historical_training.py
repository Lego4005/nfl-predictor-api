#!/usr/bin/env python3
"""
Parallel Historical Training System

Studies past year games with all 15 experts in parallel to build comprehensive memories.
Each expert analyzes games from their unique perspective and stores learnings.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from datetime import datetime, timedelta
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Dict, Any

from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parallel_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ParallelHistoricalTrainer:
    """Parallel training system for all 15 experts"""

    def __init__(self):
        self.supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
        self.openrouter = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))
        self.memory_service = SupabaseEpisodicMemoryManager(self.supabase)

        # 15 Expert configurations with tested models
        self.experts = {
            'claude-the-analyst': {
                'name': 'Claude "The Analyst" Thompson',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Methodical, data-driven, loves advanced metrics',
                'specialty': 'Deep statistical analysis and trend identification',
                'focus_areas': ['advanced_metrics', 'statistical_trends', 'efficiency_ratings']
            },
            'grok-the-maverick': {
                'name': 'Grok "The Maverick" Rodriguez',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Bold, contrarian, loves upset picks',
                'specialty': 'Finding value in underdog situations',
                'focus_areas': ['upset_potential', 'contrarian_value', 'market_inefficiencies']
            },
            'gemini-the-weatherman': {
                'name': 'Gemini "The Weatherman" Flash',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Environmental expert, considers all conditions',
                'specialty': 'Weather impact and outdoor game analysis',
                'focus_areas': ['weather_conditions', 'environmental_factors', 'dome_vs_outdoor']
            },
            'deepseek-the-intuitive': {
                'name': 'DeepSeek "The Intuitive" Chen',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Intuitive, considers intangibles and momentum',
                'specialty': 'Team chemistry and psychological factors',
                'focus_areas': ['team_momentum', 'psychological_factors', 'intangibles']
            },
            'gpt-the-historian': {
                'name': 'GPT "The Historian" Williams',
                'model': 'openai/gpt-5',
                'personality': 'Historical perspective, loves precedents',
                'specialty': 'Historical matchups and playoff implications',
                'focus_areas': ['historical_matchups', 'playoff_implications', 'precedents']
            },
            'gemini-pro-the-perfectionist': {
                'name': 'Gemini Pro "The Perfectionist" Singh',
                'model': 'google/gemini-2.5-pro',
                'personality': 'Perfectionist, wants all the data',
                'specialty': 'Comprehensive game breakdowns',
                'focus_areas': ['comprehensive_analysis', 'detailed_breakdowns', 'all_factors']
            },
            'qwen-the-calculator': {
                'name': 'Qwen "The Calculator" Liu',
                'model': 'z-ai/glm-4.6',
                'personality': 'Math genius, probability focused',
                'specialty': 'Advanced probability calculations',
                'focus_areas': ['probability_calculations', 'mathematical_models', 'statistical_analysis']
            },
            'sonoma-the-rookie': {
                'name': 'Sonoma "The Rookie" Sky',
                'model': 'google/gemini-2.5-flash',
                'personality': 'Fresh perspective, eager to prove itself',
                'specialty': 'Unbiased analysis without preconceptions',
                'focus_areas': ['fresh_perspective', 'unbiased_analysis', 'new_insights']
            },
            'deepseek-free-the-underdog': {
                'name': 'DeepSeek Free "The Underdog" Park',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Scrappy, hungry to prove free can beat premium',
                'specialty': 'Value finding and efficiency analysis',
                'focus_areas': ['value_finding', 'efficiency_analysis', 'underdog_value']
            },
            'flash-the-speedster': {
                'name': 'Flash "The Speedster" Johnson',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Quick decisions, trusts first instincts',
                'specialty': 'Rapid-fire analysis and gut calls',
                'focus_areas': ['quick_analysis', 'gut_instincts', 'rapid_decisions']
            },
            'claude-opus-the-veteran': {
                'name': 'Claude Opus "The Veteran" Davis',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Old school, seen it all before',
                'specialty': 'Veteran leadership and clutch situations',
                'focus_areas': ['veteran_leadership', 'clutch_situations', 'experience_factors']
            },
            'mixtral-the-philosopher': {
                'name': 'Mixtral "The Philosopher" Dubois',
                'model': 'z-ai/glm-4.6',
                'personality': 'Philosophical, considers deeper meanings',
                'specialty': 'Game narrative and storyline analysis',
                'focus_areas': ['game_narrative', 'storyline_analysis', 'deeper_meanings']
            },
            'llama-the-consistent': {
                'name': 'Llama "The Consistent" Martinez',
                'model': 'google/gemini-2.5-pro',
                'personality': 'Steady, reliable, never flashy',
                'specialty': 'Consistent baseline predictions',
                'focus_areas': ['consistent_analysis', 'baseline_predictions', 'reliable_factors']
            },
            'o1-the-thinker': {
                'name': 'O1 "The Thinker" Watson',
                'model': 'openai/gpt-5',
                'personality': 'Deep thinker, takes time to analyze',
                'specialty': 'Complex reasoning and edge cases',
                'focus_areas': ['complex_reasoning', 'edge_cases', 'deep_analysis']
            },
            'haiku-the-minimalist': {
                'name': 'Haiku "The Minimalist" Tanaka',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Minimalist, cuts to the essence',
                'specialty': 'Concise, essential insights only',
                'focus_areas': ['essential_insights', 'minimalist_analysis', 'core_factors']
            }
        }

        # Training statistics
        self.training_stats = {
            'games_processed': 0,
            'memories_created': 0,
            'experts_trained': 0,
            'start_time': None,
            'errors': []
        }

    async def fetch_historical_games(self, limit: int = 100) -> List[Dict]:
        """Fetch completed games from the past year"""

        logger.info(f"📊 Fetching {limit} historical games...")

        # Get games from 2024 season with results
        response = self.supabase.table('nfl_games').select('*').eq(
            'season', 2024
        ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
            'game_date', desc=False
        ).limit(limit).execute()

        games = response.data
        logger.info(f"✅ Loaded {len(games)} completed games")

        return games

    def build_expert_prompt(self, expert_id: str, game: Dict) -> tuple:
        """Build specialized prompt for each expert"""

        expert = self.experts[expert_id]

        system_message = f\"\"\"You are {expert['name']}, an NFL prediction expert.

PERSONALITY: {expert['personality']}
SPECIALTY: {expert['specialty']}
FOCUS AREAS: {', '.join(expert['focus_areas'])}

You are analyzing a COMPLETED game to learn from the outcome. Focus on your specialty areas and extract insights that will help you make better future predictions.

Analyze the game from YOUR unique perspective and identify:
1. Key factors that influenced the outcome
2. What you would have predicted and why
3. Lessons learned for future similar situations
4. Specific insights related to your specialty

Be authentic to your personality and focus on your areas of expertise.\"\"\"

        user_message = f\"\"\"GAME ANALYSIS REQUEST:

{game['away_team']} @ {game['home_team']}
Date: {game.get('game_date', 'Unknown')}
Final Score: {game['away_team']} {game.get('away_score', 0)} - {game['home_team']} {game.get('home_score', 0)}

GAME DETAILS:
- Season: {game.get('season', 2024)}
- Week: {game.get('week', 'Unknown')}
- Stadium: {game.get('stadium', 'Unknown')}
- Weather: {game.get('weather_description', 'Unknown')}
- Surface: {game.get('surface', 'Unknown')}

BETTING LINES:
- Spread: {game.get('spread_line', 'N/A')}
- Total: {game.get('total_line', 'N/A')}

Analyze this completed game from your expert perspective. What insights can you extract that will help you make better predictions in the future?\"\"\"

        return system_message, user_message

    async def train_expert_on_game(self, expert_id: str, game: Dict) -> Dict:
        """Train a single expert on a single game"""

        expert = self.experts[expert_id]

        try:
            # Build expert-specific prompt
            system_msg, user_msg = self.build_expert_prompt(expert_id, game)

            # Get expert analysis
            response = self.openrouter.generate_completion(
                system_message=system_msg,
                user_message=user_msg,
                temperature=0.7,
                max_tokens=500,
                model=expert['model']
            )

            # Extract insights and create memory
            memory_data = {
                'memory_type': 'historical_analysis',
                'expert_perspective': expert['specialty'],
                'game_outcome': {
                    'winner': game['home_team'] if game['home_score'] > game['away_score'] else game['away_team'],
                    'home_score': game['home_score'],
                    'away_score': game['away_score'],
                    'margin': abs(game['home_score'] - game['away_score'])
                },
                'analysis': response.content,
                'contextual_factors': [
                    {'factor': 'home_team', 'value': game['home_team']},
                    {'factor': 'away_team', 'value': game['away_team']},
                    {'factor': 'season', 'value': game['season']},
                    {'factor': 'week', 'value': game['week']},
                    {'factor': 'weather', 'value': game.get('weather_description', 'Unknown')},
                    {'factor': 'surface', 'value': game.get('surface', 'grass')}
                ],
                'lessons_learned': [
                    f"Historical analysis from {expert['name']} perspective",
                    f"Focus: {expert['specialty']}"
                ],
                'emotional_intensity': 0.6,
                'memory_vividness': 0.8
            }

            # Store memory
            game_id = f"historical_{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}"
            await self.memory_service.store_memory(expert_id, game_id, memory_data)

            return {
                'expert_id': expert_id,
                'game_id': game_id,
                'success': True,
                'tokens_used': response.tokens_used,
                'response_time': response.response_time
            }

        except Exception as e:
            logger.error(f"❌ {expert['name']} failed on {game['away_team']} @ {game['home_team']}: {e}")
            return {
                'expert_id': expert_id,
                'game_id': f"historical_{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}",
                'success': False,
                'error': str(e)
            }

    async def parallel_train_game(self, game: Dict) -> List[Dict]:
        """Train all 15 experts on a single game in parallel"""

        logger.info(f"🏈 Training all experts on: {game['away_team']} @ {game['home_team']}")

        # Create tasks for all experts
        tasks = []
        for expert_id in self.experts.keys():
            task = self.train_expert_on_game(expert_id, game)
            tasks.append(task)

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        failed = len(results) - successful

        logger.info(f"   ✅ {successful} experts trained successfully")
        if failed > 0:
            logger.warning(f"   ❌ {failed} experts failed")

        return results

    async def run_parallel_training(self, num_games: int = 50):
        """Run parallel training on historical games"""

        logger.info("🚀 STARTING PARALLEL HISTORICAL TRAINING")
        logger.info("=" * 60)

        self.training_stats['start_time'] = time.time()

        # Fetch historical games
        games = await self.fetch_historical_games(num_games)

        if not games:
            logger.error("❌ No historical games found")
            return

        logger.info(f"🎯 Training {len(self.experts)} experts on {len(games)} games")
        logger.info(f"📊 Total training sessions: {len(self.experts) * len(games)}")

        # Process games in batches to avoid overwhelming the API
        batch_size = 5
        total_memories = 0

        for i in range(0, len(games), batch_size):
            batch = games[i:i + batch_size]
            logger.info(f"\\n📦 Processing batch {i//batch_size + 1}/{(len(games) + batch_size - 1)//batch_size}")

            # Process batch games in parallel
            batch_tasks = []
            for game in batch:
                task = self.parallel_train_game(game)
                batch_tasks.append(task)

            batch_results = await asyncio.gather(*batch_tasks)

            # Update statistics
            for game_results in batch_results:
                self.training_stats['games_processed'] += 1
                for result in game_results:
                    if isinstance(result, dict):
                        if result.get('success', False):
                            total_memories += 1
                        else:
                            self.training_stats['errors'].append(result)

            # Brief pause between batches
            await asyncio.sleep(2)

        # Final statistics
        elapsed_time = time.time() - self.training_stats['start_time']

        logger.info(f"\\n🎉 PARALLEL TRAINING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"📊 TRAINING STATISTICS:")
        logger.info(f"   Games Processed: {self.training_stats['games_processed']}")
        logger.info(f"   Memories Created: {total_memories}")
        logger.info(f"   Experts Trained: {len(self.experts)}")
        logger.info(f"   Success Rate: {total_memories/(len(self.experts) * self.training_stats['games_processed'])*100:.1f}%")
        logger.info(f"   Total Time: {elapsed_time/60:.1f} minutes")
        logger.info(f"   Avg Time per Game: {elapsed_time/self.training_stats['games_processed']:.1f}s")

        if self.training_stats['errors']:
            logger.warning(f"   Errors: {len(self.training_stats['errors'])}")

        logger.info(f"\\n✅ All experts now have historical game memories!")
        logger.info(f"🧠 Ready for enhanced predictions with learned insights!")

async def main():
    """Main training execution"""

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    trainer = ParallelHistoricalTrainer()

    # Get user input for number of games
    try:
        num_games = int(input("How many historical games to train on? (default 50): ") or "50")
    except ValueError:
        num_games = 50

    logger.info(f"🎯 Training on {num_games} historical games")

    await trainer.run_parallel_training(num_games)

if __name__ == "__main__":
    asyncio.run(main())
