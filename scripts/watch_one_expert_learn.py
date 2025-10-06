#!/usr/bin/env python3
"""
Watch ONE Expert Learn Over Time

Follows a single expert through multiple weeks to see how they learn:
- ONE expert: conservative_analyzer (the only one working without odds)
- ALL games from Weeks 1-4 (64 games)
- Shows their reasoning, prediction, result for each game
- Track improvement over time
"""

import asyncio
import sys
import os
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


def print_header(title):
    """Print a header"""
    print(f"\n{'='*100}")
    print(f"  {title}")
    print(f"{'='*100}\n")


async def watch_one_expert_learn():
    """Watch ONE expert learn game by game"""

    print_header("🎓 EXPERT LEARNING JOURNEY - Conservative Analyzer")

    print("📊 Following ONE expert through their learning journey:")
    print("   • Expert: Conservative Analyzer (data-driven, risk-averse)")
    print("   • Games: 64 games across Weeks 1-4")
    print("   • Watching: Every prediction, reasoning, and result")
    print("   • Goal: See how accuracy improves with experience\n")

    # Initialize
    dal = ExpertDataAccessLayer()
    reasoning_logger = ReasoningChainLogger(supabase)
    expert_id = 'conservative_analyzer'

    print(f"✅ Initialized services for {expert_id}\n")

    # Get all games
    games = supabase.table('games') \
        .select('*') \
        .eq('season', 2025) \
        .in_('week', [1, 2, 3, 4]) \
        .order('game_time') \
        .execute()

    games = games.data
    print(f"✅ Loaded {len(games)} games\n")

    # Track stats
    stats = {
        'correct': 0,
        'total': 0,
        'by_week': {1: [], 2: [], 3: [], 4: []}
    }

    model = get_expert_model(expert_id)

    # Process each game
    for game_idx, game in enumerate(games, 1):
        game_id = game['id']
        week = game['week']
        home_team = game['home_team']
        away_team = game['away_team']
        game_time = game['game_time'][:10]

        # Actual result
        actual_winner = None
        if game.get('home_score') is not None and game.get('away_score') is not None:
            if game['home_score'] > game['away_score']:
                actual_winner = home_team
            elif game['away_score'] > game['home_score']:
                actual_winner = away_team

        print(f"\n{'─'*100}")
        print(f"🏈 Game {game_idx}/{len(games)} | Week {week} | {away_team} @ {home_team} ({game_time})")
        print(f"{'─'*100}")

        # Show actual result
        if actual_winner:
            print(f"📊 Final Score: {away_team} {game['away_score']} - {home_team} {game['home_score']} | Winner: {actual_winner}")
        else:
            print(f"📊 Game status: Not yet played or tied")

        try:
            # Get expert data
            game_metadata = {
                game_id: {
                    'season': game['season'],
                    'week': game['week'],
                    'home_team': home_team,
                    'away_team': away_team
                }
            }

            expert_data = await dal.batch_get_expert_data([expert_id], [game_id], game_metadata=game_metadata)
            game_data = expert_data[expert_id].get(game_id)

            if not game_data:
                print(f"⚠️  No data available")
                continue

            # Make prediction
            prediction = await model.predict(game_data)

            # Show prediction
            print(f"\n💭 Expert's Thinking:")
            print(f"   \"{prediction.reasoning}\"")

            print(f"\n🎯 Prediction: {prediction.winner} ({prediction.winner_confidence*100:.1f}% confidence)")

            if prediction.key_factors:
                print(f"📌 Key Factors:")
                for factor in prediction.key_factors[:3]:
                    print(f"   • {factor}")

            # Log reasoning
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

            # Check result
            if actual_winner and actual_winner != "TIE":
                stats['total'] += 1

                if prediction.winner == actual_winner:
                    stats['correct'] += 1
                    stats['by_week'][week].append(1)
                    print(f"\n✅ CORRECT! Running accuracy: {stats['correct']}/{stats['total']} = {stats['correct']/stats['total']*100:.1f}%")
                else:
                    stats['by_week'][week].append(0)
                    print(f"\n❌ WRONG (predicted {prediction.winner}, actual {actual_winner})")
                    print(f"   Running accuracy: {stats['correct']}/{stats['total']} = {stats['correct']/stats['total']*100:.1f}%")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

        # Show week summary after each week
        if game_idx < len(games) and games[game_idx]['week'] != week:
            print(f"\n\n{'━'*100}")
            print(f"📈 WEEK {week} COMPLETE")
            print(f"{'━'*100}")

            week_correct = sum(stats['by_week'][week])
            week_total = len(stats['by_week'][week])

            if week_total > 0:
                week_acc = week_correct / week_total * 100
                print(f"   Week {week} Accuracy: {week_correct}/{week_total} = {week_acc:.1f}%")
                print(f"   Overall Accuracy: {stats['correct']}/{stats['total']} = {stats['correct']/stats['total']*100:.1f}%")

                # Show trend
                if week > 1:
                    prev_weeks_correct = sum(sum(stats['by_week'][w]) for w in range(1, week))
                    prev_weeks_total = sum(len(stats['by_week'][w]) for w in range(1, week))
                    if prev_weeks_total > 0:
                        prev_acc = prev_weeks_correct / prev_weeks_total * 100
                        trend = week_acc - prev_acc
                        if trend > 0:
                            print(f"   📈 Improving! (+{trend:.1f}% from previous weeks)")
                        elif trend < 0:
                            print(f"   📉 Declining ({trend:.1f}% from previous weeks)")
                        else:
                            print(f"   ➡️  Stable (same as previous weeks)")

            print(f"{'━'*100}\n")

    # Final summary
    print_header("🏆 FINAL LEARNING SUMMARY")

    print(f"Expert: {expert_id.replace('_', ' ').title()}")
    print(f"Total Games: {stats['total']}")
    print(f"Correct Predictions: {stats['correct']}")
    print(f"Overall Accuracy: {stats['correct']/stats['total']*100:.1f}%\n")

    print("📊 Week-by-Week Breakdown:\n")
    for week in [1, 2, 3, 4]:
        if stats['by_week'][week]:
            week_correct = sum(stats['by_week'][week])
            week_total = len(stats['by_week'][week])
            week_acc = week_correct / week_total * 100
            print(f"   Week {week}: {week_correct:>2}/{week_total:>2} = {week_acc:>5.1f}%")

    # Learning trend
    print("\n📈 Learning Trend:")
    week_accs = []
    for week in [1, 2, 3, 4]:
        if stats['by_week'][week]:
            week_correct = sum(stats['by_week'][week])
            week_total = len(stats['by_week'][week])
            week_acc = week_correct / week_total
            week_accs.append(week_acc)

    if len(week_accs) >= 2:
        first_half_acc = sum(week_accs[:2]) / 2 if len(week_accs) >= 2 else week_accs[0]
        second_half_acc = sum(week_accs[2:]) / len(week_accs[2:]) if len(week_accs) > 2 else (week_accs[1] if len(week_accs) > 1 else 0)

        if second_half_acc > first_half_acc:
            improvement = (second_half_acc - first_half_acc) * 100
            print(f"   ✅ Expert IMPROVED over time! (+{improvement:.1f}% from first half to second half)")
        elif second_half_acc < first_half_acc:
            decline = (first_half_acc - second_half_acc) * 100
            print(f"   ⚠️  Expert accuracy declined (-{decline:.1f}% from first half to second half)")
        else:
            print(f"   ➡️  Expert remained consistent")

    print("\n✅ Learning journey complete!\n")


if __name__ == "__main__":
    asyncio.run(watch_one_expert_learn())