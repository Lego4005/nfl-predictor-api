#!/usr/bin/env python3
"""
🏈 8-Week AI NFL Prediction Journey with Episodic Memory 🧠
Runs AI through 8 weeks of games, building episodic memory and improving over time
"""

import json
import sys
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.local_llm_service import LocalLLMService

class AILearningJourney:
    """Manages 8-week AI learning journey with episodic memory"""
    
    def __init__(self):
        self.llm = LocalLLMService()
        self.episodic_memories = []  # Will store in DB later
        self.week_results = []
        self.expert_personality = "The Evolving Analyst - An AI that learns and adapts from every game"
        
    def create_week_games(self, week_num: int) -> List[Dict]:
        """Create realistic games for each week"""
        week_games = {
            1: [
                {"home": "KC", "away": "BAL", "weather": "75°F, Clear", "spread": "KC -3"},
                {"home": "BUF", "away": "NYJ", "weather": "68°F, Cloudy", "spread": "BUF -7"},
                {"home": "SF", "away": "PIT", "weather": "82°F, Sunny", "spread": "SF -6"},
            ],
            2: [
                {"home": "DAL", "away": "LAC", "weather": "89°F, Hot", "spread": "DAL -3.5"},
                {"home": "GB", "away": "ATL", "weather": "71°F, Clear", "spread": "GB -4"},
                {"home": "MIA", "away": "NE", "weather": "85°F, Humid", "spread": "MIA -6"},
            ],
            3: [
                {"home": "DEN", "away": "TB", "weather": "62°F, Windy", "spread": "DEN -1"},
                {"home": "SEA", "away": "CAR", "weather": "67°F, Drizzle", "spread": "SEA -8"},
                {"home": "MIN", "away": "HOU", "weather": "58°F, Cool", "spread": "MIN -2.5"},
            ],
            4: [
                {"home": "PHI", "away": "WAS", "weather": "76°F, Perfect", "spread": "PHI -9"},
                {"home": "LV", "away": "CLE", "weather": "94°F, Desert", "spread": "LV -3"},
                {"home": "ARI", "away": "LAR", "weather": "101°F, Blazing", "spread": "ARI -1"},
            ],
            5: [
                {"home": "TEN", "away": "IND", "weather": "69°F, Mild", "spread": "TEN -2"},
                {"home": "CIN", "away": "JAX", "weather": "73°F, Pleasant", "spread": "CIN -7"},
                {"home": "DET", "away": "CHI", "weather": "45°F, Crisp", "spread": "DET -5.5"},
            ],
            6: [
                {"home": "NO", "away": "NYG", "weather": "81°F, Humid", "spread": "NO -4"},
                {"home": "KC", "away": "DEN", "weather": "38°F, Cold", "spread": "KC -8"},
                {"home": "BUF", "away": "MIA", "weather": "42°F, Blustery", "spread": "BUF -4.5"},
            ],
            7: [
                {"home": "SF", "away": "LAR", "weather": "78°F, Clear", "spread": "SF -3"},
                {"home": "DAL", "away": "WAS", "weather": "84°F, Warm", "spread": "DAL -10"},
                {"home": "BAL", "away": "CLE", "weather": "51°F, Overcast", "spread": "BAL -6.5"},
            ],
            8: [
                {"home": "GB", "away": "MIN", "weather": "34°F, Snow", "spread": "GB -2.5"},
                {"home": "PIT", "away": "NYJ", "weather": "46°F, Windy", "spread": "PIT -7"},
                {"home": "LAC", "away": "CHI", "weather": "77°F, Nice", "spread": "LAC -8.5"},
            ]
        }
        return week_games.get(week_num, [])
    
    def create_realistic_outcomes(self, game: Dict, week_num: int) -> Dict:
        """Create realistic game outcomes with some upsets"""
        
        # Extract spread to determine favorite
        spread_text = game["spread"]
        if "-" in spread_text:
            favorite = spread_text.split("-")[0].strip()
            spread_value = float(spread_text.split("-")[1].strip())
        else:
            favorite = game["home"]  # Default
            spread_value = 3.0
        
        # Simulate upsets based on week (AI should learn upset patterns)
        upset_probability = 0.15 + (week_num * 0.02)  # Increases over time
        is_upset = random.random() < upset_probability
        
        if favorite == game["home"]:
            if is_upset:
                winner = game["away"]
                margin = random.randint(3, 14)
                home_score = random.randint(17, 24)
                away_score = home_score + margin
            else:
                winner = game["home"]
                margin = random.randint(1, int(spread_value + 7))
                away_score = random.randint(14, 21)
                home_score = away_score + margin
        else:
            if is_upset:
                winner = game["home"]
                margin = random.randint(3, 10)
                away_score = random.randint(17, 24)
                home_score = away_score + margin
            else:
                winner = game["away"]
                margin = random.randint(1, int(spread_value + 5))
                home_score = random.randint(14, 21)
                away_score = home_score + margin
        
        return {
            "final_score": f"{game['home']} {home_score}, {game['away']} {away_score}",
            "winner": winner,
            "total_points": home_score + away_score,
            "winning_margin": margin,
            "is_upset": is_upset,
            "game_summary": self.generate_game_summary(game, winner, is_upset, margin)
        }
    
    def generate_game_summary(self, game: Dict, winner: str, is_upset: bool, margin: int) -> str:
        """Generate realistic game summary"""
        summaries = {
            True: [  # Upsets
                f"{winner} shocked everyone with dominant {margin}-point victory",
                f"Stunning upset as {winner} outplayed favorites by {margin}",
                f"{winner} pulled off major surprise win by {margin} points",
            ],
            False: [  # Expected results
                f"{winner} controlled the game winning by {margin}",
                f"{winner} lived up to expectations with {margin}-point win",
                f"{winner} handled business at home with {margin}-point victory",
            ]
        }
        return random.choice(summaries[is_upset])
    
    def get_memory_context(self, week_num: int) -> str:
        """Build memory context from previous weeks"""
        if not self.episodic_memories:
            return "No previous game memories to reference."
        
        recent_memories = self.episodic_memories[-6:]  # Last 6 games
        memory_context = "MEMORY BANK - Recent Game Experiences:\n"
        
        for i, memory in enumerate(recent_memories, 1):
            memory_context += f"\n{i}. Week {memory['week']}: {memory['game_summary']}"
            memory_context += f"\n   My Prediction: {memory['prediction_summary']}"
            memory_context += f"\n   Result: {memory['outcome_summary']}"
            memory_context += f"\n   Lesson: {memory['lesson_learned']}\n"
        
        return memory_context
    
    def make_week_predictions(self, week_num: int, games: List[Dict]) -> List[Dict]:
        """Make predictions for all games in a week"""
        print(f"\n🎯 WEEK {week_num} PREDICTIONS")
        print("=" * 50)
        
        week_predictions = []
        memory_context = self.get_memory_context(week_num)
        
        for game_idx, game in enumerate(games, 1):
            print(f"\n🏈 Game {game_idx}: {game['away']} @ {game['home']}")
            print(f"   Weather: {game['weather']}, Spread: {game['spread']}")
            
            # Build prediction prompt with memory
            prompt = f"""
            WEEK {week_num} PREDICTION TASK:
            
            {memory_context}
            
            CURRENT GAME: {game['away']} @ {game['home']}
            Weather: {game['weather']}
            Betting Line: {game['spread']}
            
            Based on your memory of previous games and lessons learned:
            1. Who wins and by how much?
            2. Total points over/under 45?
            3. Key factors influencing this game?
            4. What patterns from your memory apply here?
            5. Confidence level (1-10)?
            
            Be specific and reference your past experiences!
            """
            
            start_time = time.time()
            response = self.llm.generate_completion(
                system_message=f"You are {self.expert_personality}. You learn from every game and apply those lessons.",
                user_message=prompt,
                temperature=0.7,
                max_tokens=400
            )
            
            prediction_time = time.time() - start_time
            
            # Parse prediction
            prediction_data = {
                "game": game,
                "prediction_text": response.content,
                "timestamp": datetime.now().isoformat(),
                "response_time": prediction_time,
                "tokens_used": response.total_tokens,
                "week": week_num,
                "game_number": game_idx
            }
            
            week_predictions.append(prediction_data)
            
            print(f"   ✅ Prediction made ({prediction_time:.1f}s, {response.total_tokens} tokens)")
            print(f"   🤖: {response.content[:150]}...")
        
        return week_predictions
    
    def simulate_week_outcomes(self, week_num: int, games: List[Dict]) -> List[Dict]:
        """Simulate outcomes for all games in a week"""
        print(f"\n🏆 WEEK {week_num} RESULTS")
        print("=" * 50)
        
        outcomes = []
        for game_idx, game in enumerate(games, 1):
            outcome = self.create_realistic_outcomes(game, week_num)
            outcomes.append(outcome)
            
            print(f"\n🏈 Game {game_idx}: {outcome['final_score']}")
            print(f"   📊 Total: {outcome['total_points']} points")
            print(f"   {'🚨 UPSET!' if outcome['is_upset'] else '✅ Expected'}")
            print(f"   📝 {outcome['game_summary']}")
        
        return outcomes
    
    def reflect_and_learn(self, week_num: int, predictions: List[Dict], outcomes: List[Dict]) -> List[Dict]:
        """AI reflects on week performance and learns"""
        print(f"\n🧠 WEEK {week_num} LEARNING & REFLECTION")
        print("=" * 50)
        
        week_memories = []
        
        for i, (pred, outcome) in enumerate(zip(predictions, outcomes)):
            print(f"\n🤔 Reflecting on Game {i+1}...")
            
            reflection_prompt = f"""
            REFLECTION TASK - Week {week_num}, Game {i+1}:
            
            YOUR PREDICTION:
            {pred['prediction_text']}
            
            ACTUAL OUTCOME:
            {outcome['final_score']}
            Total Points: {outcome['total_points']}
            {outcome['game_summary']}
            {'🚨 This was an UPSET!' if outcome['is_upset'] else ''}
            
            REFLECTION QUESTIONS:
            1. What did you get right/wrong?
            2. What surprised you about this outcome?
            3. What pattern or lesson should you remember?
            4. How will this influence future predictions?
            5. Rate your performance (1-10)?
            
            Be honest and specific about lessons learned!
            """
            
            start_time = time.time()
            reflection_response = self.llm.generate_completion(
                system_message=f"You are {self.expert_personality}. Honestly reflect on your prediction and extract valuable lessons.",
                user_message=reflection_prompt,
                temperature=0.6,
                max_tokens=300
            )
            
            reflection_time = time.time() - start_time
            
            # Store episodic memory
            memory = {
                "week": week_num,
                "game_number": i+1,
                "game_summary": f"{pred['game']['away']} @ {pred['game']['home']}",
                "prediction_summary": pred['prediction_text'][:100] + "...",
                "outcome_summary": outcome['game_summary'],
                "lesson_learned": reflection_response.content[:200] + "...",
                "is_upset": outcome['is_upset'],
                "reflection_full": reflection_response.content,
                "timestamp": datetime.now().isoformat(),
                "reflection_time": reflection_time
            }
            
            self.episodic_memories.append(memory)
            week_memories.append(memory)
            
            print(f"   ✅ Reflection complete ({reflection_time:.1f}s)")
            print(f"   📚 Lesson: {memory['lesson_learned']}")
        
        return week_memories
    
    def run_8_week_journey(self):
        """Run complete 8-week AI learning journey"""
        print("🚀 STARTING 8-WEEK AI NFL LEARNING JOURNEY")
        print("=" * 60)
        print(f"🤖 Expert: {self.expert_personality}")
        print(f"🧠 Memory System: Active")
        print(f"📅 Duration: 8 weeks of NFL games")
        
        journey_start = time.time()
        total_predictions = 0
        total_reflections = 0
        
        for week_num in range(1, 9):
            week_start = time.time()
            print(f"\n" + "="*60)
            print(f"📅 WEEK {week_num} - AI Learning Journey")
            print(f"🧠 Current Memory Bank: {len(self.episodic_memories)} experiences")
            print("="*60)
            
            # Get games for this week
            games = self.create_week_games(week_num)
            
            # AI makes predictions
            predictions = self.make_week_predictions(week_num, games)
            total_predictions += len(predictions)
            
            # Simulate outcomes  
            outcomes = self.simulate_week_outcomes(week_num, games)
            
            # AI reflects and learns
            memories = self.reflect_and_learn(week_num, predictions, outcomes)
            total_reflections += len(memories)
            
            # Week summary
            week_time = time.time() - week_start
            upset_count = sum(1 for outcome in outcomes if outcome['is_upset'])
            
            print(f"\n📊 WEEK {week_num} SUMMARY:")
            print(f"   🎯 Predictions Made: {len(predictions)}")
            print(f"   🏆 Games Completed: {len(outcomes)}")
            print(f"   🚨 Upsets: {upset_count}/{len(outcomes)}")
            print(f"   🧠 New Memories: {len(memories)}")
            print(f"   ⏱️ Week Duration: {week_time:.1f}s")
            
            # Store week results
            self.week_results.append({
                "week": week_num,
                "predictions": len(predictions),
                "outcomes": len(outcomes),
                "upsets": upset_count,
                "memories_added": len(memories),
                "week_duration": week_time
            })
            
            # Brief pause between weeks
            time.sleep(1)
        
        # Journey complete!
        journey_time = time.time() - journey_start
        
        print(f"\n" + "="*60)
        print("🎉 8-WEEK AI LEARNING JOURNEY COMPLETE!")
        print("="*60)
        print(f"✅ Total Predictions: {total_predictions}")
        print(f"✅ Total Reflections: {total_reflections}")
        print(f"✅ Total Memories Stored: {len(self.episodic_memories)}")
        print(f"✅ Journey Duration: {journey_time:.1f}s ({journey_time/60:.1f} minutes)")
        
        # Show memory evolution
        print(f"\n🧠 MEMORY EVOLUTION:")
        for week_result in self.week_results:
            print(f"   Week {week_result['week']}: {week_result['memories_added']} new memories")
        
        # Show lessons learned summary
        print(f"\n📚 KEY LESSONS LEARNED:")
        for i, memory in enumerate(self.episodic_memories[-5:], 1):  # Last 5 lessons
            print(f"   {i}. {memory['lesson_learned']}")
        
        print(f"\n🚀 The AI has evolved from 0 to {len(self.episodic_memories)} experiences!")
        print(f"💡 Ready for smarter predictions with rich memory context!")

def main():
    """Run the 8-week journey"""
    journey = AILearningJourney()
    journey.run_8_week_journey()

if __name__ == "__main__":
    main()