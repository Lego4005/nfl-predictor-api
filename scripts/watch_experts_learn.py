#!/usr/bin/env python3
"""
Watch Experts Learn - Deep Dive into Expert Reasoning

Shows EXACTLY what each expert sees and how they make decisions:
- 3 experts: conservative_analyzer, risk_taking_gambler, contrarian_rebel
- One game at a time with full transparency
- Shows: input data, reasoning process, prediction, actual result
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.expert_data_access_layer import ExpertDataAccessLayer
from src.ml.expert_models import get_expert_model
from src.ml.reasoning_chain_logger import ReasoningChainLogger

load_dotenv()

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def print_section(title, symbol="="):
    """Print a nice section header"""
    print(f"\n{symbol * 100}")
    print(f"{symbol * 2} {title}")
    print(f"{symbol * 100}\n")


def print_data_details(data, indent="   "):
    """Print data in a readable format"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{indent}{key}:")
                print_data_details(value, indent + "   ")
            else:
                # Format numbers nicely
                if isinstance(value, float):
                    print(f"{indent}{key}: {value:.2f}")
                else:
                    print(f"{indent}{key}: {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                print(f"{indent}[{i}]:")
                print_data_details(item, indent + "   ")
            else:
                print(f"{indent}[{i}]: {item}")


async def watch_experts_learn():
    """Watch 3 experts make predictions step-by-step"""

    print_section("🔬 EXPERT LEARNING LAB - DEEP DIVE", "=")

    print("📊 Test Setup:")
    print("   • Experts: conservative_analyzer, risk_taking_gambler, contrarian_rebel")
    print("   • Games: First 5 games from Week 1")
    print("   • Detail Level: MAXIMUM - see everything they see")
    print("   • Weather: Disabled (rate limited)\n")

    # Initialize
    dal = ExpertDataAccessLayer()
    reasoning_logger = ReasoningChainLogger(supabase)

    expert_ids = ['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel']

    print(f"✅ Initialized data access layer")
    print(f"✅ Initialized reasoning chain logger")
    print(f"✅ Selected 3 experts with different personalities\n")

    # Get games
    games = supabase.table('games') \
        .select('*') \
        .eq('season', 2025) \
        .eq('week', 1) \
        .order('game_time') \
        .limit(5) \
        .execute()

    games = games.data
    print(f"✅ Fetched {len(games)} games from Week 1\n")

    # Track accuracy
    expert_stats = {eid: {'correct': 0, 'total': 0} for eid in expert_ids}

    # Process each game
    for game_idx, game in enumerate(games, 1):
        game_id = game['id']
        week = game['week']
        home_team = game['home_team']
        away_team = game['away_team']
        game_time = game['game_time'][:16]

        # Actual result
        actual_winner = None
        if game.get('home_score') is not None and game.get('away_score') is not None:
            if game['home_score'] > game['away_score']:
                actual_winner = home_team
            elif game['away_score'] > game['home_score']:
                actual_winner = away_team

        print_section(f"🏈 GAME {game_idx}/5: {away_team} @ {home_team}", "=")

        print(f"📅 Game Time: {game_time}")
        print(f"📍 Location: {home_team} stadium")
        if actual_winner:
            print(f"🏆 Actual Result: {away_team} {game['away_score']} - {home_team} {game['home_score']}")
            print(f"   Winner: {actual_winner}")
        print()

        # Batch fetch data for all experts
        print_section("📊 STEP 1: GATHERING DATA FOR EXPERTS", "-")

        game_metadata = {
            game_id: {
                'season': game['season'],
                'week': game['week'],
                'home_team': home_team,
                'away_team': away_team
            }
        }

        print(f"🔄 Fetching data from APIs...")
        print(f"   • SportsData.io: Team stats, standings, trends")
        print(f"   • The Odds API: Betting lines, public sentiment")
        print(f"   • Weather: Skipped (rate limited)\n")

        expert_data = await dal.batch_get_expert_data(expert_ids, [game_id], game_metadata=game_metadata)

        print(f"✅ Data fetched! Now showing what EACH expert sees:\n")

        # Process each expert ONE BY ONE
        for expert_idx, expert_id in enumerate(expert_ids, 1):
            expert_name = expert_id.replace('_', ' ').title()

            print_section(f"🤖 EXPERT {expert_idx}/3: {expert_name}", "━")

            # Show expert personality
            personalities = {
                'conservative_analyzer': "📊 Data-driven, risk-averse, values consistency",
                'risk_taking_gambler': "🎲 Bold picks, loves underdogs, high risk/reward",
                'contrarian_rebel': "🔄 Fades public opinion, zigs when others zag"
            }
            print(f"💭 Personality: {personalities.get(expert_id, 'Unknown')}\n")

            try:
                # Get expert's model and data
                model = get_expert_model(expert_id)
                game_data = expert_data[expert_id].get(game_id)

                if not game_data:
                    print(f"❌ No data available for this expert!\n")
                    continue

                # SHOW INPUT DATA
                print_section("📥 INPUT DATA - What the expert sees", "·")

                # Show team stats (nested in team_stats dict)
                if hasattr(game_data, 'team_stats') and game_data.team_stats:
                    team_stats = game_data.team_stats

                    if 'home' in team_stats:
                        print("🏠 HOME TEAM STATS:")
                        home_stats = team_stats['home']
                        print(f"   Team: {home_team}")
                        if isinstance(home_stats, dict):
                            print(f"   Wins-Losses: {home_stats.get('wins', 0)}-{home_stats.get('losses', 0)}")
                            print(f"   Points Per Game: {home_stats.get('points_per_game', 0):.1f}")
                            print(f"   Points Allowed: {home_stats.get('points_allowed_per_game', 0):.1f}")
                            print(f"   Offensive Efficiency: {home_stats.get('offensive_efficiency', 0):.2f}")
                            print(f"   Defensive Efficiency: {home_stats.get('defensive_efficiency', 0):.2f}")
                        print()

                    if 'away' in team_stats:
                        print("✈️  AWAY TEAM STATS:")
                        away_stats = team_stats['away']
                        print(f"   Team: {away_team}")
                        if isinstance(away_stats, dict):
                            print(f"   Wins-Losses: {away_stats.get('wins', 0)}-{away_stats.get('losses', 0)}")
                            print(f"   Points Per Game: {away_stats.get('points_per_game', 0):.1f}")
                            print(f"   Points Allowed: {away_stats.get('points_allowed_per_game', 0):.1f}")
                            print(f"   Offensive Efficiency: {away_stats.get('offensive_efficiency', 0):.2f}")
                            print(f"   Defensive Efficiency: {away_stats.get('defensive_efficiency', 0):.2f}")
                        print()

                if hasattr(game_data, 'odds') and game_data.odds:
                    print("💰 BETTING ODDS:")
                    odds = game_data.odds
                    print(f"   Spread: {odds.get('spread', 'N/A')}")
                    print(f"   Over/Under: {odds.get('total', 'N/A')}")
                    print(f"   Home ML: {odds.get('home_ml', 'N/A')}")
                    print(f"   Away ML: {odds.get('away_ml', 'N/A')}")
                    print()

                if hasattr(game_data, 'weather') and game_data.weather:
                    print("☁️  WEATHER:")
                    weather = game_data.weather
                    print(f"   Temperature: {weather.get('temperature', 'N/A')}")
                    print(f"   Wind: {weather.get('wind_speed', 'N/A')} mph")
                    print(f"   Conditions: {weather.get('conditions', 'N/A')}")
                    print()
                else:
                    print("☁️  WEATHER: Not available\n")

                # EXPERT THINKS
                print_section("🧠 EXPERT REASONING - How they analyze the data", "·")

                print("⚙️  Running expert's prediction algorithm...")
                prediction = await model.predict(game_data)

                # Show the reasoning
                print(f"\n💭 Expert's Internal Monologue:")
                print(f"   \"{prediction.reasoning}\"\n")

                print("🔍 Key Factors Identified:")
                if prediction.key_factors:
                    for i, factor in enumerate(prediction.key_factors[:5], 1):
                        print(f"   {i}. {factor}")
                else:
                    print("   (No specific factors listed)")
                print()

                # PREDICTION
                print_section("📤 PREDICTION - Final decision", "·")

                print(f"🎯 Predicted Winner: {prediction.winner}")
                print(f"📊 Confidence: {prediction.winner_confidence * 100:.1f}%")

                if hasattr(prediction, 'spread_prediction'):
                    print(f"📈 Predicted Spread: {prediction.spread_prediction}")
                if hasattr(prediction, 'total_prediction'):
                    print(f"📊 Predicted Total: {prediction.total_prediction}")
                print()

                # Log reasoning to database
                complete_factors = []
                for f in (prediction.key_factors or []):
                    complete_factors.append({
                        'factor': f,
                        'value': f,
                        'weight': 1.0,
                        'confidence': prediction.winner_confidence,
                        'source': 'model_prediction'
                    })

                await reasoning_logger.log_reasoning_chain(
                    expert_id=expert_id,
                    game_id=game_id,
                    prediction={
                        'winner': prediction.winner,
                        'confidence': prediction.winner_confidence,
                        'home_team': home_team,
                        'away_team': away_team
                    },
                    factors=complete_factors,
                    monologue=prediction.reasoning
                )

                print("💾 Reasoning chain saved to database for learning\n")

                # RESULT
                if actual_winner and actual_winner != "TIE":
                    print_section("🎓 LEARNING - Did they get it right?", "·")

                    if prediction.winner == actual_winner:
                        print(f"✅ CORRECT! Expert predicted {prediction.winner}, actual winner was {actual_winner}")
                        expert_stats[expert_id]['correct'] += 1
                        print(f"   This expert is now {expert_stats[expert_id]['correct']}/{expert_stats[expert_id]['total'] + 1}")
                    else:
                        print(f"❌ WRONG! Expert predicted {prediction.winner}, actual winner was {actual_winner}")
                        print(f"   This expert is now {expert_stats[expert_id]['correct']}/{expert_stats[expert_id]['total'] + 1}")

                    expert_stats[expert_id]['total'] += 1
                    print()

            except Exception as e:
                print(f"❌ ERROR: {e}\n")
                import traceback
                traceback.print_exc()

        # Summary after each game
        print_section(f"📊 GAME {game_idx} SUMMARY", "═")
        print(f"Game: {away_team} @ {home_team}")
        if actual_winner:
            print(f"Winner: {actual_winner}\n")

        print("Expert Performance:")
        for expert_id in expert_ids:
            stats = expert_stats[expert_id]
            if stats['total'] > 0:
                acc = stats['correct'] / stats['total'] * 100
                print(f"   {expert_id.replace('_', ' ').title():<30}: {stats['correct']}/{stats['total']} ({acc:.0f}%)")
        print()

        # Pause between games (skip if non-interactive)
        import sys
        if sys.stdin.isatty():
            input("Press ENTER to continue to next game...")
        else:
            print("(Auto-continuing to next game...)\n")

    # Final summary
    print_section("🏆 FINAL RESULTS", "═")

    for expert_id in expert_ids:
        stats = expert_stats[expert_id]
        if stats['total'] > 0:
            acc = stats['correct'] / stats['total'] * 100
            expert_name = expert_id.replace('_', ' ').title()
            print(f"{expert_name:<30}: {stats['correct']}/{stats['total']} = {acc:.1f}% accuracy")

    print("\n✅ Deep dive complete! You've seen exactly how each expert thinks.\n")


if __name__ == "__main__":
    asyncio.run(watch_experts_learn())