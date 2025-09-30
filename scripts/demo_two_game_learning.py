#!/usr/bin/env python3
"""
Two-Game Learning Demo

Shows:
1. Game 1: Predict with no learning history
2. Learn from Game 1 result
3. Game 2: Predict with self-reflection from Game 1 learning

This demonstrates the learning loop in action!
"""

import asyncio
import sys
import os
from supabase import create_client
from dotenv import load_dotenv

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


async def main():
    print("="*80)
    print("🎓 TWO-GAME LEARNING DEMO")
    print("="*80)
    print()
    print("This demo shows:")
    print("  1. Game 1: Predict with no learning history")
    print("  2. Learn from Game 1 result using gradient descent")
    print("  3. Game 2: Predict with self-reflection from Game 1")
    print()
    print("="*80)
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
    print(f"   Traits: Analytics Trust={expert_config['personality_traits']['analytics_trust']:.1f}, Risk Tolerance={expert_config['personality_traits']['risk_tolerance']:.1f}")
    print()

    # Get first 2 completed Week 1 games
    games = supabase.table('games') \
        .select('*') \
        .eq('season', 2025) \
        .eq('week', 1) \
        .not_.is_('home_score', 'null') \
        .order('game_time') \
        .limit(2) \
        .execute()

    if len(games.data) < 2:
        print("❌ Need at least 2 completed games")
        return

    game1 = games.data[0]
    game2 = games.data[1]

    # Initialize agents
    llm_agent = EnhancedLLMExpertAgent(supabase, expert_config, current_bankroll=1000.0)
    learning_engine = AdaptiveLearningEngine(supabase, learning_rate=0.01)

    # Initialize learning for this expert
    await learning_engine.initialize_expert(expert_config['expert_id'], [
        'defensive_strength', 'offensive_output', 'red_zone_efficiency',
        'third_down_conversion', 'home_advantage', 'turnover_differential'
    ])

    print("="*80)
    print("🏈 GAME 1: Prediction WITHOUT Learning History")
    print("="*80)
    print()

    # Game 1: Predict without learning
    print(f"Game: {game1['away_team']} @ {game1['home_team']}")
    print(f"Actual Score: {game1['away_score']} - {game1['home_score']}")
    print(f"Actual Winner: {determine_winner(game1)}")
    print()

    pred1 = await llm_agent.predict(
        game1['id'],
        game_data={
            'home_team': game1['home_team'],
            'away_team': game1['away_team'],
            'week': game1['week'],
            'season': game1['season']
        }
    )

    if not pred1:
        print("❌ Failed to generate prediction for Game 1")
        return

    actual_winner1 = determine_winner(game1)
    is_correct1 = (pred1['winner'] == actual_winner1)

    print(f"\n📊 Game 1 Results:")
    print(f"   Predicted: {pred1['winner']} ({pred1['confidence']*100:.1f}% confidence)")
    print(f"   Actual: {actual_winner1}")
    print(f"   Result: {'✅ CORRECT' if is_correct1 else '❌ WRONG'}")
    print(f"   Base Confidence: {pred1['confidence']*100:.1f}% (no ML adjustment)")
    print()

    # Use structured factors from LLM (no keyword matching needed!)
    factors_used = pred1.get('key_factors', [])

    # Ensure factors have proper format for learning engine
    if factors_used and isinstance(factors_used[0], dict):
        # Already in correct format: [{"factor": "...", "value": 0.9, "description": "..."}]
        print(f"   Factors identified by LLM:")
        for f in factors_used:
            print(f"     - {f['factor']}: {f['value']:.2f} ({f.get('description', 'N/A')})")
    else:
        # Fallback if old format (shouldn't happen with new prompt)
        print(f"   Warning: Using fallback factor extraction")
        factors_used = [{'factor': str(f), 'value': pred1['confidence']} for f in factors_used]

    print("="*80)
    print("🧠 LEARNING FROM GAME 1")
    print("="*80)
    print()

    # Learn from Game 1
    await learning_engine.update_from_prediction(
        expert_id=expert_config['expert_id'],
        predicted_winner=pred1['winner'],
        predicted_confidence=pred1['confidence'],
        actual_winner=actual_winner1,
        factors_used=factors_used
    )

    # Show learning stats
    stats = learning_engine.get_learning_stats(expert_config['expert_id'])
    print(f"📈 Learning Update Complete:")
    print(f"   Games Learned From: {stats['games_learned_from']}")
    print(f"   Recent Accuracy: {stats['recent_accuracy']*100:.1f}%")
    print(f"   Top Factors: {[f['factor'] for f in stats['top_factors'][:3]]}")
    print()

    print("="*80)
    print("🏈 GAME 2: Prediction WITH Self-Reflection")
    print("="*80)
    print()

    # Game 2: Predict with learning
    print(f"Game: {game2['away_team']} @ {game2['home_team']}")
    print(f"Actual Score: {game2['away_score']} - {game2['home_score']}")
    print(f"Actual Winner: {determine_winner(game2)}")
    print()

    pred2 = await llm_agent.predict(
        game2['id'],
        game_data={
            'home_team': game2['home_team'],
            'away_team': game2['away_team'],
            'week': game2['week'],
            'season': game2['season']
        }
    )

    if not pred2:
        print("❌ Failed to generate prediction for Game 2")
        return

    # Apply ML adjustment based on learning
    base_confidence2 = pred2['confidence']

    # Use structured factors from LLM for Game 2
    factors_used2 = pred2.get('key_factors', [])

    if factors_used2 and isinstance(factors_used2[0], dict):
        print(f"   Factors identified by LLM:")
        for f in factors_used2:
            print(f"     - {f['factor']}: {f['value']:.2f} ({f.get('description', 'N/A')})")
    else:
        factors_used2 = [{'factor': str(f), 'value': pred2['confidence']} for f in factors_used2]

    # Get adjusted confidence from learning engine
    adjusted_confidence2 = learning_engine.get_adjusted_confidence(
        expert_id=expert_config['expert_id'],
        base_confidence=base_confidence2,
        factors=factors_used2
    )

    ml_adjustment = adjusted_confidence2 - base_confidence2

    actual_winner2 = determine_winner(game2)
    is_correct2 = (pred2['winner'] == actual_winner2)

    print(f"\n📊 Game 2 Results (WITH LEARNING):")
    print(f"   Predicted: {pred2['winner']}")
    print(f"   Base Confidence: {base_confidence2*100:.1f}%")
    print(f"   ML Adjustment: {ml_adjustment*100:+.1f}% (based on Game 1 learning)")
    print(f"   Final Confidence: {adjusted_confidence2*100:.1f}%")
    print(f"   Actual: {actual_winner2}")
    print(f"   Result: {'✅ CORRECT' if is_correct2 else '❌ WRONG'}")
    print()

    print("="*80)
    print("📈 LEARNING COMPARISON")
    print("="*80)
    print()
    print(f"Game 1 (no learning):")
    print(f"  Confidence: {pred1['confidence']*100:.1f}% → {'✅ CORRECT' if is_correct1 else '❌ WRONG'}")
    print()
    print(f"Game 2 (with learning from Game 1):")
    print(f"  Base: {base_confidence2*100:.1f}% → Adjusted: {adjusted_confidence2*100:.1f}% ({ml_adjustment*100:+.1f}%)")
    print(f"  Result: {'✅ CORRECT' if is_correct2 else '❌ WRONG'}")
    print()
    print(f"💡 Key Insight:")
    if ml_adjustment > 0:
        print(f"   Learning engine INCREASED confidence by {ml_adjustment*100:.1f}%")
        print(f"   The AI learned that these factors predict success!")
    elif ml_adjustment < 0:
        print(f"   Learning engine DECREASED confidence by {abs(ml_adjustment)*100:.1f}%")
        print(f"   The AI learned to be more cautious with these factors")
    else:
        print(f"   No adjustment - need more data to learn patterns")
    print()
    print("✅ This demonstrates self-reflection: the AI adjusts future predictions based on past performance!")


if __name__ == "__main__":
    asyncio.run(main())