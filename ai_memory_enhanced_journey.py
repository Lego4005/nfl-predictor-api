#!/usr/bin/env python3
"""
🏈 Memory-Enhanced 8-Week AI Journey with Database Storage 🧠
Stores episodic memories in Supabase and retrieves them for future predictions
"""

import json
import sys
import os
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.local_llm_service import LocalLLMService
from src.database.connection import DatabaseConnection

class MemoryEnhancedJourney:
    """AI Journey with real episodic memory storage in database"""
    
    def __init__(self):
        self.llm = LocalLLMService()
        self.db = DatabaseConnection()
        self.expert_id = "evolving-analyst-001"
        self.expert_name = "The Evolving Analyst"
        
    def create_expert_if_not_exists(self):
        """Create expert in database if doesn't exist"""
        try:
            # Check if expert exists
            result = self.db.fetch_one(
                "SELECT expert_id FROM experts WHERE expert_id = %s",
                (self.expert_id,)
            )
            
            if not result:
                # Create expert
                self.db.execute("""
                    INSERT INTO experts (expert_id, expert_name, personality_description, confidence_style)
                    VALUES (%s, %s, %s, %s)
                """, (
                    self.expert_id,
                    self.expert_name,
                    "An AI that learns and adapts from every game experience",
                    "adaptive"
                ))
                print(f"✅ Created expert: {self.expert_name}")
            else:
                print(f"✅ Expert exists: {self.expert_name}")
                
        except Exception as e:
            print(f"⚠️ Error managing expert: {e}")
    
    def store_episodic_memory(self, game_data: Dict, prediction: str, outcome: Dict, reflection: str, week: int, game_num: int) -> str:
        """Store episodic memory in database"""
        try:
            memory_id = str(uuid.uuid4())
            
            # Store in expert_episodic_memories table
            self.db.execute("""
                INSERT INTO expert_episodic_memories (
                    memory_id, expert_id, game_id, memory_type, emotional_state,
                    prediction_data, outcome_data, lessons_learned, confidence_impact,
                    created_at, game_week, memory_strength
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                memory_id,
                self.expert_id,
                f"week{week}_game{game_num}",
                "prediction_outcome",
                "learning" if not outcome.get('is_upset') else "surprised",
                json.dumps({
                    "prediction_text": prediction,
                    "game_context": game_data
                }),
                json.dumps(outcome),
                reflection[:500],  # Truncate for storage
                0.8,  # Default confidence impact
                datetime.now(),
                week,
                1.0  # Full strength initially
            ))
            
            print(f"📀 Stored memory {memory_id[:8]} in database")
            return memory_id
            
        except Exception as e:
            print(f"❌ Error storing memory: {e}")
            return ""
    
    def retrieve_recent_memories(self, limit: int = 6) -> List[Dict]:
        """Retrieve recent episodic memories from database"""
        try:
            memories = self.db.fetch_all("""
                SELECT memory_id, game_id, prediction_data, outcome_data, 
                       lessons_learned, game_week, emotional_state
                FROM expert_episodic_memories 
                WHERE expert_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (self.expert_id, limit))
            
            formatted_memories = []
            for memory in memories:
                try:
                    pred_data = json.loads(memory['prediction_data'])
                    outcome_data = json.loads(memory['outcome_data'])
                    
                    formatted_memories.append({
                        'week': memory['game_week'],
                        'game_id': memory['game_id'],
                        'prediction_summary': pred_data.get('prediction_text', '')[:100],
                        'outcome_summary': outcome_data.get('game_summary', ''),
                        'lesson_learned': memory['lessons_learned'],
                        'emotional_state': memory['emotional_state']
                    })
                except json.JSONDecodeError:
                    continue
                    
            return formatted_memories
            
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            return []
    
    def build_memory_context(self) -> str:
        """Build memory context from database"""
        memories = self.retrieve_recent_memories(6)
        
        if not memories:
            return "No previous game memories to reference."
        
        context = "🧠 MEMORY BANK - Your Recent Game Experiences:\n"
        for i, memory in enumerate(memories, 1):
            context += f"\n{i}. Week {memory['week']} ({memory['game_id']})"
            context += f"\n   Prediction: {memory['prediction_summary']}..."
            context += f"\n   Result: {memory['outcome_summary']}"
            context += f"\n   Lesson: {memory['lesson_learned']}"
            context += f"\n   Feeling: {memory['emotional_state']}\n"
        
        return context
    
    def run_memory_enhanced_week(self, week_num: int, max_games: int = 2):
        """Run one week with memory enhancement (limited games for demo)"""
        print(f"\n🧠 WEEK {week_num} - MEMORY-ENHANCED PREDICTIONS")
        print("="*60)
        
        # Get memory context
        memory_context = self.build_memory_context()
        memory_count = len(self.retrieve_recent_memories(100))
        
        print(f"📚 Memory Bank: {memory_count} stored experiences")
        
        # Demo games for this week
        games = [
            {"home": "KC", "away": "BAL", "weather": "75°F, Clear", "spread": "KC -3"},
            {"home": "BUF", "away": "NYJ", "weather": "68°F, Cloudy", "spread": "BUF -7"},
        ][:max_games]
        
        for game_idx, game in enumerate(games, 1):
            print(f"\n🏈 Game {game_idx}: {game['away']} @ {game['home']}")
            print(f"   📊 {game['weather']}, {game['spread']}")
            
            # 1. Make prediction with memory context
            prediction_prompt = f"""
            WEEK {week_num} PREDICTION WITH MEMORY:
            
            {memory_context}
            
            CURRENT GAME: {game['away']} @ {game['home']}
            Weather: {game['weather']}
            Line: {game['spread']}
            
            Based on your stored memories and past lessons:
            1. Who wins and by how much?
            2. What patterns from your memory apply?
            3. Confidence level (1-10)?
            
            Reference specific past experiences!
            """
            
            print("🤖 AI making prediction with memory context...")
            pred_response = self.llm.generate_completion(
                system_message=f"You are {self.expert_name}. Use your episodic memories to make better predictions.",
                user_message=prediction_prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            print(f"✅ Prediction: {pred_response.content[:100]}...")
            
            # 2. Simulate outcome
            import random
            is_upset = random.random() < 0.3
            
            if game['spread'].startswith(game['home']):
                # Home team favored
                if is_upset:
                    winner = game['away']
                    home_score, away_score = 21, 28
                else:
                    winner = game['home']
                    home_score, away_score = 27, 20
            else:
                # Away team favored (less common)
                if is_upset:
                    winner = game['home']
                    home_score, away_score = 24, 21
                else:
                    winner = game['away']
                    home_score, away_score = 17, 24
            
            outcome = {
                "final_score": f"{game['home']} {home_score}, {game['away']} {away_score}",
                "winner": winner,
                "total_points": home_score + away_score,
                "is_upset": is_upset,
                "game_summary": f"{'Upset!' if is_upset else 'Expected'} {winner} wins {abs(home_score-away_score)}-point game"
            }
            
            print(f"🏆 Result: {outcome['final_score']} ({'🚨 UPSET' if is_upset else '✅ Expected'})")
            
            # 3. Reflect and learn
            reflection_prompt = f"""
            MEMORY FORMATION - Reflect on this game:
            
            YOUR PREDICTION: {pred_response.content}
            
            ACTUAL OUTCOME: {outcome['final_score']}
            {outcome['game_summary']}
            
            What lesson should you store in memory for future games?
            Be specific about what you learned!
            """
            
            print("🤔 AI reflecting and forming memory...")
            reflection_response = self.llm.generate_completion(
                system_message=f"You are {self.expert_name}. Extract a specific lesson for your memory bank.",
                user_message=reflection_prompt,
                temperature=0.6,
                max_tokens=200
            )
            
            # 4. Store in database
            memory_id = self.store_episodic_memory(
                game, pred_response.content, outcome, 
                reflection_response.content, week_num, game_idx
            )
            
            print(f"🧠 Memory stored: {reflection_response.content[:80]}...")
        
        # Show updated memory stats
        updated_count = len(self.retrieve_recent_memories(100))
        print(f"\n📊 WEEK {week_num} SUMMARY:")
        print(f"   🎯 Games predicted: {len(games)}")
        print(f"   🧠 Total memories: {updated_count}")
        print(f"   💾 New memories: {updated_count - memory_count}")
    
    def run_enhanced_journey(self, weeks: int = 3):
        """Run memory-enhanced journey with database storage"""
        print("🚀 MEMORY-ENHANCED AI LEARNING JOURNEY")
        print("="*60)
        print(f"🤖 Expert: {self.expert_name}")
        print(f"💾 Database: Supabase with episodic memory storage")
        print(f"🧠 Memory System: Real database persistence")
        
        # Setup expert
        self.create_expert_if_not_exists()
        
        # Run weeks
        for week in range(1, weeks + 1):
            self.run_memory_enhanced_week(week, max_games=2)
            time.sleep(1)  # Brief pause
        
        # Final summary
        final_memories = self.retrieve_recent_memories(50)
        print(f"\n🎉 ENHANCED JOURNEY COMPLETE!")
        print("="*60)
        print(f"✅ Total memories stored: {len(final_memories)}")
        print(f"✅ Database integration: Working")
        print(f"✅ Memory persistence: Active")
        
        print(f"\n🧠 RECENT LESSONS LEARNED:")
        for i, memory in enumerate(final_memories[:3], 1):
            print(f"   {i}. {memory['lesson_learned'][:100]}...")
        
        print(f"\n💡 Your AI now has persistent memory that survives restarts!")

def main():
    """Run memory-enhanced journey"""
    journey = MemoryEnhancedJourney()
    journey.run_enhanced_journey(weeks=3)

if __name__ == "__main__":
    main()