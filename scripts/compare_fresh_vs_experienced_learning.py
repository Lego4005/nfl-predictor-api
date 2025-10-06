#!/usr/bin/env python3
"""
Hybrid Learning Comparison: Fresh vs Experienced Expert

Runs TWO parallel tracks:
Track A: Fresh expert (clean slate, 0 games learned)
Track B: Experienced expert (keeps existing learning history)

Shows:
- Real-time streaming progress
- Side-by-side accuracy comparison
- Learning trajectory differences
- Confidence adjustment patterns
- What factors matter most

Saves detailed logs for analysis.
"""

import asyncio
import sys
import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ml.enhanced_llm_expert import EnhancedLLMExpertAgent
from src.ml.adaptive_learning_engine import AdaptiveLearningEngine

load_dotenv()


def determine_winner(game):
    """Determine who won the game"""
    if game['home_score'] > game['away_score']:
        return game['home_team']
    elif game['away_score'] > game['home_score']:
        return game['away_team']
    else:
        return "TIE"


def print_header(text, char="="):
    """Print formatted header"""
    print()
    print(char * 100)
    print(f"  {text}")
    print(char * 100)
    print()


def print_progress(track, game_num, total, game_info, prediction, actual, is_correct, ml_adj=None):
    """Print streaming progress for a game"""
    status = "✅ CORRECT" if is_correct else "❌ WRONG"
    ml_text = f", ML Adj: {ml_adj*100:+.1f}%" if ml_adj else ""

    print(f"[{track}] Game {game_num:2d}/{total} | {game_info:20s} | "
          f"Pred: {prediction['winner']:3s} ({prediction['confidence']*100:4.1f}%{ml_text}) | "
          f"Actual: {actual:3s} | {status}")


async def run_learning_track(
    track_name: str,
    expert_id: str,
    expert_config: dict,
    games: list,
    supabase,
    clear_history: bool = False,
    log_file: str = None
):
    """
    Run a complete learning track for N games.

    Args:
        track_name: "Track A" or "Track B"
        expert_id: Expert identifier (will be modified for Track A)
        expert_config: Expert configuration
        games: List of games to predict
        supabase: Supabase client
        clear_history: If True, start with empty learning history
        log_file: Path to save detailed logs

    Returns:
        Dict with results and analytics
    """

    # Initialize agent and learning engine
    llm_agent = EnhancedLLMExpertAgent(supabase, expert_config, current_bankroll=1000.0)
    learning_engine = AdaptiveLearningEngine(supabase, learning_rate=0.01)

    # Initialize learning engine
    standard_factors = [
        'defensive_strength', 'offensive_efficiency', 'red_zone_efficiency',
        'third_down_conversion', 'turnover_differential', 'home_advantage',
        'recent_momentum', 'special_teams'
    ]
    await learning_engine.initialize_expert(expert_id, standard_factors)

    # Clear history if requested (for fresh track)
    if clear_history:
        # Force reset to clean slate
        learning_engine.expert_weights[expert_id].accuracy_history = []
        learning_engine.expert_weights[expert_id].weights = {
            f: 1.0/len(standard_factors) for f in standard_factors
        }
        # Save cleaned weights to database
        await learning_engine._save_weights(expert_id)

    # Track results
    results = {
        'track': track_name,
        'expert_id': expert_id,
        'games': [],
        'accuracy_by_week': {},
        'ml_adjustments': [],
        'factor_importance_evolution': []
    }

    log_lines = []
    log_lines.append(f"{'='*100}")
    log_lines.append(f"{track_name}: {expert_config['name']} ({'Clean Slate' if clear_history else 'With History'})")
    log_lines.append(f"{'='*100}\n")

    total_games = len(games)
    correct_count = 0

    for idx, game in enumerate(games, 1):
        game_info = f"{game['away_team']}@{game['home_team']}"

        # Predict
        pred = await llm_agent.predict(
            game['id'],
            game_data={
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'week': game['week'],
                'season': game['season']
            }
        )

        if not pred:
            log_lines.append(f"Game {idx}: FAILED to generate prediction\n")
            continue

        actual_winner = determine_winner(game)
        is_correct = (pred['winner'] == actual_winner)
        if is_correct:
            correct_count += 1

        # Get ML adjustment (before learning from this game)
        base_confidence = pred['confidence']
        factors = pred.get('key_factors', [])

        if factors and isinstance(factors[0], dict):
            adjusted_confidence = learning_engine.get_adjusted_confidence(
                expert_id=expert_id,
                base_confidence=base_confidence,
                factors=factors
            )
            ml_adjustment = adjusted_confidence - base_confidence
        else:
            adjusted_confidence = base_confidence
            ml_adjustment = 0.0

        # Print progress
        print_progress(
            track_name, idx, total_games, game_info,
            pred, actual_winner, is_correct, ml_adjustment
        )

        # Log detailed info
        log_lines.append(f"\nGame {idx}/{total_games}: {game_info} (Week {game['week']})")
        log_lines.append(f"  Predicted: {pred['winner']} @ {base_confidence*100:.1f}% confidence")
        log_lines.append(f"  ML Adjustment: {ml_adjustment*100:+.1f}% → Final: {adjusted_confidence*100:.1f}%")
        log_lines.append(f"  Actual: {actual_winner} | {'✅ CORRECT' if is_correct else '❌ WRONG'}")
        log_lines.append(f"  Factors:")
        for f in factors[:3]:  # Top 3 factors
            if isinstance(f, dict):
                log_lines.append(f"    - {f['factor']}: {f['value']:.2f} - {f.get('description', 'N/A')}")

        # Store result
        results['games'].append({
            'game_num': idx,
            'week': game['week'],
            'matchup': game_info,
            'predicted': pred['winner'],
            'actual': actual_winner,
            'correct': is_correct,
            'base_confidence': base_confidence,
            'ml_adjustment': ml_adjustment,
            'final_confidence': adjusted_confidence,
            'factors': factors
        })

        results['ml_adjustments'].append(ml_adjustment)

        # Track accuracy by week
        week = game['week']
        if week not in results['accuracy_by_week']:
            results['accuracy_by_week'][week] = {'correct': 0, 'total': 0}
        results['accuracy_by_week'][week]['total'] += 1
        if is_correct:
            results['accuracy_by_week'][week]['correct'] += 1

        # Learn from this game
        if factors and isinstance(factors[0], dict):
            await learning_engine.update_from_prediction(
                expert_id=expert_id,
                predicted_winner=pred['winner'],
                predicted_confidence=adjusted_confidence,  # Use adjusted confidence
                actual_winner=actual_winner,
                factors_used=factors
            )

        # Track factor importance evolution every 4 games
        if idx % 4 == 0:
            stats = learning_engine.get_learning_stats(expert_id)
            results['factor_importance_evolution'].append({
                'game_num': idx,
                'top_factors': stats['top_factors'][:5]
            })

    # Final statistics
    final_accuracy = correct_count / total_games if total_games > 0 else 0
    results['final_accuracy'] = final_accuracy
    results['total_games'] = total_games
    results['correct_count'] = correct_count

    log_lines.append(f"\n{'='*100}")
    log_lines.append(f"FINAL RESULTS: {correct_count}/{total_games} = {final_accuracy*100:.1f}% accuracy")
    log_lines.append(f"{'='*100}\n")

    # Save log file
    if log_file:
        with open(log_file, 'w') as f:
            f.write('\n'.join(log_lines))

    return results


async def main():
    print_header("🔬 HYBRID LEARNING EXPERIMENT: FRESH VS EXPERIENCED", "=")

    print("📊 Experiment Design:")
    print("   Track A: Fresh Expert (0 games learned, clean slate)")
    print("   Track B: Experienced Expert (keeps existing 23-game history)")
    print()
    print("   Running 20 games from Weeks 1-2 for each track...")
    print("   Real-time streaming output below...")
    print()

    # Initialize Supabase
    supabase = create_client(
        os.getenv('VITE_SUPABASE_URL'),
        os.getenv('VITE_SUPABASE_ANON_KEY')
    )

    # Get The Analyst expert
    expert_result = supabase.table('personality_experts') \
        .select('*') \
        .eq('expert_id', 'conservative_analyzer') \
        .execute()

    expert_config = expert_result.data[0]
    print(f"👤 Expert: {expert_config['name']}")
    print(f"   Personality: Analytics Trust={expert_config['personality_traits']['analytics_trust']:.1f}, "
          f"Risk Tolerance={expert_config['personality_traits']['risk_tolerance']:.1f}")
    print()

    # Get 20 completed games from Weeks 1-2
    games = supabase.table('games') \
        .select('*') \
        .eq('season', 2025) \
        .in_('week', [1, 2]) \
        .not_.is_('home_score', 'null') \
        .order('week, game_time') \
        .limit(20) \
        .execute()

    if len(games.data) < 20:
        print(f"⚠️  Only {len(games.data)} games available")

    print(f"🎮 Running {len(games.data)} games for each track...")
    print()
    print_header("STREAMING RESULTS", "-")

    # Run Track A (Fresh)
    print("\n🆕 Track A: Fresh Expert (Starting from 0 games)")
    results_a = await run_learning_track(
        "Track A",
        "conservative_analyzer",
        expert_config,
        games.data,
        supabase,
        clear_history=True,
        log_file="/tmp/track_a_fresh.log"
    )

    print("\n" + "="*100)
    print(f"Track A Complete: {results_a['correct_count']}/{results_a['total_games']} = {results_a['final_accuracy']*100:.1f}%")
    print("="*100 + "\n")

    # Run Track B (Experienced)
    print("\n🎓 Track B: Experienced Expert (With 23-game history)")
    results_b = await run_learning_track(
        "Track B",
        "conservative_analyzer",
        expert_config,
        games.data,
        supabase,
        clear_history=False,
        log_file="/tmp/track_b_experienced.log"
    )

    print("\n" + "="*100)
    print(f"Track B Complete: {results_b['correct_count']}/{results_b['total_games']} = {results_b['final_accuracy']*100:.1f}%")
    print("="*100 + "\n")

    # Generate comparison analysis
    print_header("📊 COMPARATIVE ANALYSIS", "=")

    # Overall accuracy
    print(f"Final Accuracy:")
    print(f"  Track A (Fresh):       {results_a['final_accuracy']*100:5.1f}%  ({results_a['correct_count']}/{results_a['total_games']} games)")
    print(f"  Track B (Experienced): {results_b['final_accuracy']*100:5.1f}%  ({results_b['correct_count']}/{results_b['total_games']} games)")
    print(f"  Difference:            {(results_b['final_accuracy'] - results_a['final_accuracy'])*100:+5.1f}%")
    print()

    # Accuracy by week
    print(f"Accuracy by Week:")
    for week in sorted(results_a['accuracy_by_week'].keys()):
        acc_a = results_a['accuracy_by_week'][week]['correct'] / results_a['accuracy_by_week'][week]['total']
        acc_b = results_b['accuracy_by_week'][week]['correct'] / results_b['accuracy_by_week'][week]['total']
        print(f"  Week {week}:  Fresh={acc_a*100:5.1f}%  |  Experienced={acc_b*100:5.1f}%  |  Δ={((acc_b-acc_a)*100):+5.1f}%")
    print()

    # ML Adjustments
    avg_adj_a = sum(results_a['ml_adjustments']) / len(results_a['ml_adjustments']) if results_a['ml_adjustments'] else 0
    avg_adj_b = sum(results_b['ml_adjustments']) / len(results_b['ml_adjustments']) if results_b['ml_adjustments'] else 0

    print(f"ML Confidence Adjustments:")
    print(f"  Track A Avg: {avg_adj_a*100:+5.2f}%  (Range: {min(results_a['ml_adjustments'])*100:+.1f}% to {max(results_a['ml_adjustments'])*100:+.1f}%)")
    print(f"  Track B Avg: {avg_adj_b*100:+5.2f}%  (Range: {min(results_b['ml_adjustments'])*100:+.1f}% to {max(results_b['ml_adjustments'])*100:+.1f}%)")
    print()

    # Save detailed results
    results_file = f"/tmp/learning_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'track_a_fresh': results_a,
            'track_b_experienced': results_b,
            'comparison': {
                'accuracy_difference': results_b['final_accuracy'] - results_a['final_accuracy'],
                'ml_adjustment_difference': avg_adj_b - avg_adj_a
            }
        }, f, indent=2)

    print(f"📁 Detailed logs saved:")
    print(f"   Track A: /tmp/track_a_fresh.log")
    print(f"   Track B: /tmp/track_b_experienced.log")
    print(f"   JSON:    {results_file}")
    print()

    print_header("💡 KEY INSIGHTS", "=")

    # Analyze and provide insights
    if results_b['final_accuracy'] > results_a['final_accuracy']:
        diff = (results_b['final_accuracy'] - results_a['final_accuracy']) * 100
        print(f"✅ EXPERIENCED expert performed BETTER by {diff:.1f}%")
        print(f"   Learning history from 23 previous games provided an advantage!")
    elif results_a['final_accuracy'] > results_b['final_accuracy']:
        diff = (results_a['final_accuracy'] - results_b['final_accuracy']) * 100
        print(f"⚠️  FRESH expert performed BETTER by {diff:.1f}%")
        print(f"   This suggests previous learning may have overfit or needs more data.")
    else:
        print(f"➖ Both tracks performed EQUALLY ({results_a['final_accuracy']*100:.1f}%)")
        print(f"   20 games may not be enough to show learning advantage.")

    print()
    print("🔍 Observations:")
    print(f"   1. ML adjustments ranged from {min(results_a['ml_adjustments'] + results_b['ml_adjustments'])*100:+.1f}% "
          f"to {max(results_a['ml_adjustments'] + results_b['ml_adjustments'])*100:+.1f}%")
    print(f"   2. Average ML adjustment: Fresh={avg_adj_a*100:+.2f}%, Experienced={avg_adj_b*100:+.2f}%")
    print(f"   3. Learning is {'active' if abs(avg_adj_b) > 0.01 else 'minimal'} (adjustments {'> 1%' if abs(avg_adj_b) > 0.01 else '< 1%'})")
    print()

    print("📈 Next Steps:")
    if results_b['final_accuracy'] - results_a['final_accuracy'] > 0.05:
        print("   ✓ Learning is working! Consider running 64 games to see full trajectory.")
    elif abs(results_b['final_accuracy'] - results_a['final_accuracy']) < 0.05:
        print("   → Need more games (40-64) to see clear learning signal.")
    else:
        print("   ⚠  Fresh expert outperformed - investigate factor extraction or learning rate.")

    print()
    print(f"🎯 Recommendation: {'Run full 64-game analysis' if abs(avg_adj_b) > 0.01 else 'Tune learning parameters first'}")
    print()


if __name__ == "__main__":
    asyncio.run(main())