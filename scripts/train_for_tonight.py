#!/usr/bin/env python3
"""
Quick Training for TonGame: SF @ LA

Build memories for 49ers and Rams from 2023-2024 seasons
Then predict tonight's game with those memories
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.prompts.natural_language_prompt import build_natural_language_prompt, parse_natural_language_response
from dotenv import load_dotenv

load_dotenv()


class RealGameData:
    """Game data with CALCULATED team stats"""
    def __init__(self, game_dict, team_stats):
        self.away_team = game_dict['away_team']
        self.home_team = game_dict['home_team']
        self.season = game_dict['season']
        self.week = game_dict['week']
        self.game_date = game_dict.get('game_date', 'Unknown')

        home_stats = team_stats.get(self.home_team, {})
        away_stats = team_stats.get(self.away_team, {})

        self.home_team_stats = type('obj', (object,), {
            'wins': home_stats.get('wins', 0),
            'losses': home_stats.get('losses', 0),
            'points_per_game': f"{home_stats.get('ppg', 0):.1f}",
            'points_allowed_per_game': f"{home_stats.get('papg', 0):.1f}",
            'recent_form': home_stats.get('form', 'N/A'),
            'coach': game_dict.get('home_coach', 'Unknown'),
            'qb': game_dict.get('home_qb_name', 'Unknown'),
            'rest_days': game_dict.get('home_rest', 7)
        })()

        self.away_team_stats = type('obj', (object,), {
            'wins': away_stats.get('wins', 0),
            'losses': away_stats.get('losses', 0),
            'points_per_game': f"{away_stats.get('ppg', 0):.1f}",
            'points_allowed_per_game': f"{away_stats.get('papg', 0):.1f}",
            'recent_form': away_stats.get('form', 'N/A'),
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


def calculate_team_stats(all_games, current_game_date):
    """Calculate team stats UP TO current game"""
    team_stats = defaultdict(lambda: {
        'wins': 0, 'losses': 0,
        'points_scored': [], 'points_allowed': [],
        'recent_games': []
    })

    for game in all_games:
        if game['game_date'] >= current_game_date:
            continue

        home_team = game['home_team']
        away_team = game['away_team']
        home_score = game.get('home_score')
        away_score = game.get('away_score')

        if home_score is None or away_score is None:
            continue

        # Update home team
        team_stats[home_team]['points_scored'].append(home_score)
        team_stats[home_team]['points_allowed'].append(away_score)
        team_stats[home_team]['recent_games'].append('W' if home_score > away_score else 'L')
        if home_score > away_score:
            team_stats[home_team]['wins'] += 1
        else:
            team_stats[home_team]['losses'] += 1

        # Update away team
        team_stats[away_team]['points_scored'].append(away_score)
        team_stats[away_team]['points_allowed'].append(home_score)
        team_stats[away_team]['recent_games'].append('W' if away_score > home_score else 'L')
        if away_score > home_score:
            team_stats[away_team]['wins'] += 1
        else:
            team_stats[away_team]['losses'] += 1

    # Calculate averages
    final_stats = {}
    for team, stats in team_stats.items():
        ppg = sum(stats['points_scored']) / len(stats['points_scored']) if stats['points_scored'] else 0
        papg = sum(stats['points_allowed']) / len(stats['points_allowed']) if stats['points_allowed'] else 0
        recent = ''.join(stats['recent_games'][-5:])

        final_stats[team] = {
            'wins': stats['wins'],
            'losses': stats['losses'],
            'ppg': ppg,
            'papg': papg,
            'form': recent if recent else 'N/A'
        }

    return final_stats


async def train_team(team_code, team_games, all_games, llm_service, memory_service):
    """Train on a team's historical games"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🏈 TRAINING: {team_code}")
    logger.info(f"{'='*80}")
    logger.info(f"Games: {len(team_games)}\n")

    trained = 0

    for i, game in enumerate(team_games, 1):
        team_stats = calculate_team_stats(all_games, game['game_date'])

        # Retrieve existing memories
        memories = await memory_service.retrieve_memories(
            'conservative_analyzer',
            {'home_team': game['home_team'], 'away_team': game['away_team']},
            limit=40
        )

        # Make prediction
        game_data = RealGameData(game, team_stats)
        system_msg, user_msg = build_natural_language_prompt(
            "You are The Conservative Analyzer. Learn from your past experiences.",
            game_data,
            memories
        )

        try:
            response = llm_service.generate_completion(
                system_message=system_msg,
                user_message=user_msg,
                temperature=0.6,
                max_tokens=300,
                model="deepseek/deepseek-chat-v3.1:free"
            )

            parsed = parse_natural_language_response(response.content)
            actual = 'home' if game['home_score'] > game['away_score'] else 'away'
            correct = parsed['winner'] == actual

            # Store memory
            game_id = f"train_{team_code}_{game['season']}_W{game['week']}_{game['away_team']}_{game['home_team']}"
            memory_data = {
                'memory_type': 'prediction_outcome',
                'prediction_data': {
                    'winner': parsed['winner'],
                    'confidence': parsed['confidence'],
                    'reasoning': parsed['reasoning'][:150]
                },
                'actual_outcome': {
                    'winner': actual,
                    'home_score': game['home_score'],
                    'away_score': game['away_score']
                },
                'contextual_factors': [
                    {'factor': 'home_team', 'value': game['home_team']},
                    {'factor': 'away_team', 'value': game['away_team']},
                    {'factor': 'season', 'value': str(game['season'])},
                    {'factor': 'week', 'value': str(game['week'])}
                ],
                'lessons_learned': [{
                    'lesson': f"{'Correct' if correct else 'Wrong'} on {game['away_team']} @ {game['home_team']}",
                    'category': 'team_performance',
                    'confidence': 0.8 if correct else 0.6
                }],
                'emotional_state': 'satisfied' if correct else 'disappointed',
                'emotional_intensity': 0.7,
                'memory_vividness': 0.8
            }

            await memory_service.store_memory('conservative_analyzer', game_id, memory_data)
            trained += 1

            if i % 5 == 0:
                logger.info(f"   Progress: {i}/{len(team_games)} games trained")

            await asyncio.sleep(3)  # Rate limit protection

        except Exception as e:
            if '429' in str(e):
                logger.warning(f"   ⚠️  Rate limit at game {i}, waiting 30s...")
                await asyncio.sleep(30)
                continue
            else:
                logger.error(f"   Error on game {i}: {e}")
                continue

    logger.info(f"✅ Trained on {trained}/{len(team_games)} games\n")
    return trained


async def predict_tonights_game(llm_service, memory_service, all_games):
    """Predict tonight's SF @ LA game with accumulated memories"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🎯 PREDICTING TONIGHT'S GAME: SF @ LA")
    logger.info(f"{'='*80}\n")

    # Get current stats (up to today)
    today = datetime.now().strftime('%Y-%m-%d')
    team_stats = calculate_team_stats(all_games, today)

    # Create game data for tonight
    tonight_game = {
        'away_team': 'SF',
        'home_team': 'LA',
        'season': 2025,
        'week': 5,  # Approximate
        'game_date': today,
        'home_coach': 'Sean McVay',
        'away_coach': 'Kyle Shanahan',
        'home_qb_name': 'Matthew Stafford',
        'away_qb_name': 'Brock Purdy',
        'home_rest': 7,
        'away_rest': 7,
        'stadium': 'SoFi Stadium',
        'surface': 'turf',
        'roof': 'retractable',
        'div_game': True,
        'weather_temperature': 72,
        'weather_wind_mph': 5,
        'weather_description': 'Clear',
        'spread_line': -3.5,  # Rams favored
        'total_line': 47.5
    }

    # Retrieve memories for BOTH teams
    sf_memories = await memory_service.retrieve_memories(
        'conservative_analyzer',
        {'home_team': 'SF', 'away_team': 'SF'},  # Get all SF memories
        limit=20
    )

    la_memories = await memory_service.retrieve_memories(
        'conservative_analyzer',
        {'home_team': 'LA', 'away_team': 'LA'},  # Get all LA memories
        limit=20
    )

    # Combine memories (prioritize exact matchup if exists)
    all_memories = sf_memories + la_memories
    all_memories.sort(key=lambda x: (x.get('similarity_score', 0), x.get('created_at', '')), reverse=True)
    combined_memories = all_memories[:30]  # Top 30 most relevant

    logger.info(f"📊 Retrieved {len(sf_memories)} SF memories, {len(la_memories)} LA memories")
    logger.info(f"   Using top {len(combined_memories)} combined memories\n")

    # Make prediction
    game_data = RealGameData(tonight_game, team_stats)
    system_msg, user_msg = build_natural_language_prompt(
        "You are The Conservative Analyzer. Use all your accumulated knowledge about both teams.",
        game_data,
        combined_memories
    )

    logger.info("🤖 Making prediction...\n")

    response = llm_service.generate_completion(
        system_message=system_msg,
        user_message=user_msg,
        temperature=0.6,
        max_tokens=500,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    parsed = parse_natural_language_response(response.content)

    # Display prediction
    logger.info(f"{'='*80}")
    logger.info(f"🎯 PREDICTION FOR TONIGHT")
    logger.info(f"{'='*80}")
    logger.info(f"\nGame: San Francisco 49ers @ Los Angeles Rams")
    logger.info(f"Time: 8:15 PM ET")
    logger.info(f"Spread: LA -3.5")
    logger.info(f"Total: 47.5")
    logger.info(f"\n💭 ANALYSIS:")
    logger.info(f"{parsed['reasoning']}")
    logger.info(f"\n🎯 PREDICTION:")
    logger.info(f"   Winner: {parsed['winner'].upper()}")
    logger.info(f"   Confidence: {parsed['confidence']:.0%}")
    logger.info(f"   Predicted Spread: {parsed.get('spread', 'N/A')}")
    logger.info(f"   Predicted Total: {parsed.get('total', 'N/A')}")
    logger.info(f"\n📊 Based on {len(combined_memories)} historical memories")
    logger.info(f"{'='*80}\n")

    return parsed


async def main():
    logger.info("="*80)
    logger.info("🏈 TRAINING FOR TONIGHT'S GAME: SF @ LA")
    logger.info("="*80)
    logger.info("Step 1: Train on 49ers games (2023-2024)")
    logger.info("Step 2: Train on Rams games (2023-2024)")
    logger.info("Step 3: Predict tonight's game with combined memories")
    logger.info("="*80)
    logger.info("")

    # Initialize
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    memory_service = SupabaseEpisodicMemoryManager(supabase)
    llm_service = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))

    # Get all games
    logger.info("📊 Fetching 2023-2024 season data...")
    all_games_response = supabase.table('nfl_games').select('*').in_(
        'season', [2023, 2024]
    ).not_.is_('home_score', 'null').not_.is_('away_score', 'null').order(
        'game_date', desc=False
    ).execute()

    all_games = all_games_response.data
    logger.info(f"✅ Loaded {len(all_games)} total games\n")

    # Clear old memories
    logger.info("🧹 Clearing old memories...")
    try:
        memory_service.supabase.table('expert_episodic_memories').delete().eq(
            'expert_id', 'conservative_analyzer'
        ).execute()
        logger.info("✅ Cleared\n")
    except Exception as e:
        logger.warning(f"⚠️  {e}\n")

    # Get team games
    sf_games = [g for g in all_games if g['home_team'] == 'SF' or g['away_team'] == 'SF'][:30]
    la_games = [g for g in all_games if g['home_team'] == 'LA' or g['away_team'] == 'LA'][:30]

    logger.info(f"Found {len(sf_games)} 49ers games, {len(la_games)} Rams games")
    logger.info(f"Training on 30 games per team for speed\n")

    # Train on both teams
    await train_team('SF', sf_games, all_games, llm_service, memory_service)
    await train_team('LA', la_games, all_games, llm_service, memory_service)

    # Predict tonight's game
    await predict_tonights_game(llm_service, memory_service, all_games)


if __name__ == "__main__":
    asyncio.run(main())

