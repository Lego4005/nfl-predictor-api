#!/usr/bin/env python3
"""
🏈 AI NFL Prediction Demo - Go Buck Wild! 🤖
Shows AI making predictions, reflecting, and learning
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.local_llm_service import LocalLLMService
from src.prompts.nfl_prediction_prompts import build_prediction_prompt, build_belief_revision_prompt

def create_mock_game():
    """Create a playoff game scenario"""
    class Game:
        home_team, away_team = 'KC', 'BUF'
        game_date, week, season = '2024-01-21', 19, 2024
        
        class Stats:
            wins, losses = 14, 3
            points_per_game = 29.2
            points_allowed_per_game = 19.8
            passing_yards_per_game = 275
            rushing_yards_per_game = 128
            turnover_differential = 12
            recent_results = 'W-W-W-L-W'
        
        class Weather:
            temperature, conditions, wind_speed = 28, 'Snow', 15
        
        class Venue:
            stadium_name, surface_type = 'Arrowhead Stadium', 'Grass'
        
        class Betting:
            spread, total = -6.5, 42.5
            home_ml, away_ml = -275, +225
        
        class News:
            injury_report = 'KC WR2 questionable, BUF LB1 probable'
        
        # Add missing attributes for compatibility
        class Context:
            is_division_game = 'No'
            primetime_game = 'Yes'
            playoff_implications = 'Championship Game'
        
        home_team_stats = away_team_stats = Stats()
        weather_conditions = Weather()
        venue_info = Venue()
        public_betting = Betting()
        recent_news = News()
        matchup_context = Context()
    
    return Game()

def run_ai_prediction_demo():
    """Run complete AI prediction demo"""
    
    print("🚀 Starting AI NFL Prediction Demo")
    print("="*60)
    
    # Initialize
    llm = LocalLLMService()
    personality = """You are The Conservative Analyzer, a risk-averse NFL expert who values proven patterns over speculation. You prefer historical data and conservative projections."""
    
    # Create game
    game = create_mock_game()
    print(f"🏈 Game: {game.away_team} @ {game.home_team}")
    print(f"🌨️ Weather: {game.weather_conditions.temperature}°F, {game.weather_conditions.conditions}")
    print(f"📊 Spread: {game.home_team} {game.public_betting.spread}")
    
    # Step 1: AI makes predictions
    print(f"\n🎯 STEP 1: AI MAKING PREDICTIONS")
    print("-" * 40)
    
    system_msg, user_msg = build_prediction_prompt(personality, game, [])
    
    print(f"💭 Calling LLM for predictions...")
    print(f"📝 System prompt: {len(system_msg)} chars, User prompt: {len(user_msg)} chars")
    
    import time
    start_time = time.time()
    pred_response = llm.generate_completion(system_msg, user_msg, temperature=0.7, max_tokens=2000)  # Limited tokens
    elapsed = time.time() - start_time
    
    print(f"✅ Response received: {pred_response.total_tokens} tokens in {pred_response.response_time:.2f}s")
    
    try:
        prediction_data = json.loads(pred_response.content)
        print(f"📊 Successfully parsed {len(prediction_data.get('predictions', []))} predictions")
    except:
        print(f"⚠️ JSON parsing failed, using raw content")
        prediction_data = {'reasoning_discussion': pred_response.content, 'predictions': []}
    
    # Show AI reasoning (first 800 chars)
    reasoning = prediction_data.get('reasoning_discussion', 'No reasoning available')
    print(f"\n🤖 AI REASONING (excerpt):")
    print(reasoning[:800] + "..." if len(reasoning) > 800 else reasoning)
    
    # Show predictions
    predictions = prediction_data.get('predictions', [])
    print(f"\n📋 PREDICTIONS MADE ({len(predictions)}):")
    for i, pred in enumerate(predictions[:5], 1):  # Show first 5
        ptype = pred.get('prediction_type', 'unknown')
        pvalue = pred.get('predicted_value', 'N/A')
        conf = pred.get('confidence', 0)
        print(f"  {i}. {ptype}: {pvalue} ({conf}% confidence)")
    if len(predictions) > 5:
        print(f"  ... and {len(predictions)-5} more predictions")
    
    # Step 2: Simulate game outcome
    print(f"\n🏆 STEP 2: GAME OUTCOME")
    print("-" * 40)
    
    # Simulate an outcome different from prediction
    actual_outcome = {
        'final_score': 'BUF 24, KC 21',
        'winner': 'away',
        'total_points': 45,
        'winning_margin': 3,
        'total_turnovers': 4,
        'home_passing_yards': 245,
        'away_passing_yards': 312,
        'game_flow_summary': 'Bills upset Chiefs in snow with strong running game'
    }
    
    print(f"Final Score: {actual_outcome['final_score']}")
    print(f"Total Points: {actual_outcome['total_points']}")
    print(f"Game Flow: {actual_outcome['game_flow_summary']}")
    
    # Step 3: AI reflects and learns
    print(f"\n🪞 STEP 3: AI SELF-REFLECTION")
    print("-" * 40)
    
    system_msg, user_msg = build_belief_revision_prompt(prediction_data, actual_outcome, personality)
    
    print(f"🤔 AI reflecting on its performance...")
    refl_response = llm.generate_completion(system_msg, user_msg, temperature=0.6, max_tokens=1200)
    
    print(f"✅ Reflection completed: {refl_response.total_tokens} tokens in {refl_response.response_time:.2f}s")
    
    try:
        reflection_data = json.loads(refl_response.content)
        print(f"📚 Successfully parsed reflection analysis")
    except:
        print(f"⚠️ Reflection JSON parsing failed")
        reflection_data = {'reflection_discussion': refl_response.content}
    
    # Show AI self-reflection
    reflection = reflection_data.get('reflection_discussion', 'No reflection available')
    print(f"\n🤔 AI SELF-REFLECTION (excerpt):")
    print(reflection[:800] + "..." if len(reflection) > 800 else reflection)
    
    # Show lessons learned
    lessons = reflection_data.get('lessons_learned', [])
    if lessons:
        print(f"\n📚 LESSONS LEARNED ({len(lessons)}):")
        for i, lesson in enumerate(lessons, 1):
            lesson_text = lesson.get('lesson', 'Unknown lesson')
            print(f"  {i}. {lesson_text}")
    
    # Summary
    print(f"\n🎉 DEMO COMPLETE!")
    print("="*60)
    print(f"✅ AI made {len(predictions)} predictions")
    print(f"✅ AI reflected on performance and learned {len(lessons)} lessons")
    print(f"✅ Total tokens used: {pred_response.total_tokens + refl_response.total_tokens:,}")
    print(f"✅ Total time: {pred_response.response_time + refl_response.response_time:.2f}s")
    
    print(f"\n🚀 The AI is ready to make smarter predictions next time!")

if __name__ == "__main__":
    run_ai_prediction_demo()