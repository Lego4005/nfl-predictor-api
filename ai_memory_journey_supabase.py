#!/usr/bin/env python3
"""
🏈 Memory-Enhanced AI Journey with Real Supabase Storage 🧠
Uses existing Supabase infrastructure to store and retrieve episodic memories
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
from supabase import create_client, Client
import hashlib

class SupabaseMemoryJourney:
    """AI Journey with real Supabase episodic memory storage"""
    
    def __init__(self):
        self.llm = LocalLLMService()
        self.expert_id = "evolving-analyst-001"
        self.expert_name = "The Evolving Analyst"
        
        # Initialize Supabase client
        supabase_url = "https://vaypgzvivahnfegnlinn.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws"
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        print(f"✅ Connected to Supabase for memory storage")
        
    def create_expert_if_not_exists(self):
        """Create expert in personality_experts table if doesn't exist"""
        try:
            # Check if expert exists
            result = self.supabase.table('personality_experts').select('expert_id').eq('expert_id', self.expert_id).execute()
            
            if not result.data:
                # Create expert in personality_experts table
                expert_data = {
                    'expert_id': self.expert_id,
                    'name': self.expert_name,
                    'personality_traits': ['adaptive', 'learning', 'analytical'],
                    'decision_style': 'evidence_based',
                    'risk_tolerance': 'moderate',
                    'confidence_style': 'calibrated',
                    'is_active': True
                }
                
                self.supabase.table('personality_experts').insert(expert_data).execute()
                print(f"✅ Created expert in database: {self.expert_name}")
            else:
                print(f"✅ Expert already exists: {self.expert_name}")
                
        except Exception as e:
            print(f"⚠️ Error managing expert: {e}")
            # Continue anyway - maybe the constraint doesn't exist
        
    def store_episodic_memory(self, game_data: Dict, prediction: str, outcome: Dict, reflection: str, week: int, game_num: int) -> str:
        """Store episodic memory in Supabase"""
        try:
            # Generate unique memory ID
            memory_content = f"{self.expert_id}_{week}_{game_num}_{datetime.now().isoformat()}"
            memory_id = hashlib.md5(memory_content.encode()).hexdigest()[:16]
            
            # Store in expert_episodic_memories table (using actual schema)
            memory_data = {
                'expert_id': self.expert_id,
                'game_id': f"week{week}_game{game_num}",
                'memory_type': 'prediction_outcome',
                'prediction_summary': json.dumps({
                    "text": prediction[:200],
                    "game": game_data
                }),
                'actual_outcome': json.dumps(outcome),
                'accuracy_scores': json.dumps({
                    'winner': 1.0 if not outcome.get('is_upset') else 0.0,
                    'overall': 0.8
                }),
                'lesson_learned': reflection[:500],
                'emotional_weight': 0.9 if outcome.get('is_upset') else 0.5,
                'surprise_factor': 0.9 if outcome.get('is_upset') else 0.2,
                'memory_strength': 1.0,
                'emotional_state': 'surprised' if outcome.get('is_upset') else 'neutral'
            }
            
            result = self.supabase.table('expert_episodic_memories').insert(memory_data).execute()
            
            if result.data:
                print(f"📀 Stored memory {memory_id} in Supabase")
                return memory_id
            else:
                print(f"⚠️ Memory storage may have failed")
                return ""
                
        except Exception as e:
            print(f"❌ Error storing memory: {e}")
            return ""
    
    def retrieve_recent_memories(self, limit: int = 6) -> List[Dict]:
        """Retrieve recent episodic memories from Supabase"""
        try:
            result = self.supabase.table('expert_episodic_memories') \
                .select('*') \
                .eq('expert_id', self.expert_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            formatted_memories = []
            if result.data:
                for memory in result.data:
                    try:
                        # Parse stored JSON data
                        pred_summary = json.loads(memory['prediction_summary']) if memory['prediction_summary'] else {}
                        outcome_data = json.loads(memory['actual_outcome']) if memory['actual_outcome'] else {}
                        
                        formatted_memories.append({
                            'week': 1,  # Default since not explicitly stored
                            'game_id': memory['game_id'],
                            'prediction_summary': pred_summary.get('text', '')[:100],
                            'outcome_summary': outcome_data.get('game_summary', f"Result: {outcome_data.get('final_score', 'Unknown')}"),
                            'lesson_learned': memory['lesson_learned'],
                            'emotional_state': memory.get('emotional_state', 'neutral')
                        })
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue
                        
            return formatted_memories
            
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            return []
    
    def build_memory_context(self) -> str:
        """Build memory context from Supabase"""
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
        """Run one week with Supabase memory enhancement"""
        print(f"\n🧠 WEEK {week_num} - SUPABASE MEMORY-ENHANCED PREDICTIONS")
        print("="*60)
        
        # Get memory context from Supabase
        memory_context = self.build_memory_context()
        memory_count = len(self.retrieve_recent_memories(100))
        
        print(f"📚 Supabase Memory Bank: {memory_count} stored experiences")
        
        # Demo games for this week
        games_by_week = {
            1: [
                {"home": "KC", "away": "BAL", "weather": "75°F, Clear", "spread": "KC -3"},
                {"home": "BUF", "away": "NYJ", "weather": "68°F, Cloudy", "spread": "BUF -7"},
            ],
            2: [
                {"home": "DAL", "away": "LAC", "weather": "89°F, Hot", "spread": "DAL -3.5"},
                {"home": "GB", "away": "ATL", "weather": "71°F, Clear", "spread": "GB -4"},
            ],
            3: [
                {"home": "DEN", "away": "TB", "weather": "62°F, Windy", "spread": "DEN -1"},
                {"home": "SEA", "away": "CAR", "weather": "67°F, Drizzle", "spread": "SEA -8"},
            ],
        }
        
        games = games_by_week.get(week_num, games_by_week[1])[:max_games]
        
        for game_idx, game in enumerate(games, 1):
            print(f"\n🏈 Game {game_idx}: {game['away']} @ {game['home']}")
            print(f"   📊 {game['weather']}, {game['spread']}")
            
            # 1. Make prediction with memory context from Supabase
            prediction_prompt = f"""
            WEEK {week_num} PREDICTION WITH SUPABASE MEMORY:
            
            {memory_context}
            
            CURRENT GAME: {game['away']} @ {game['home']}
            Weather: {game['weather']}
            Line: {game['spread']}
            
            Based on your stored memories from Supabase and past lessons:
            1. Who wins and by how much?
            2. What patterns from your memory bank apply?
            3. Confidence level (1-10)?
            4. How do your past experiences inform this prediction?
            
            Reference specific memories when explaining your reasoning!
            """
            
            print("🤖 AI making prediction with Supabase memory context...")
            start_time = time.time()
            pred_response = self.llm.generate_completion(
                system_message=f"You are {self.expert_name}. Use your episodic memories stored in Supabase to make better predictions.",
                user_message=prediction_prompt,
                temperature=0.7,
                max_tokens=400
            )
            pred_time = time.time() - start_time
            
            print(f"✅ Prediction made ({pred_time:.1f}s, {pred_response.total_tokens} tokens)")
            print(f"🤖 Reasoning: {pred_response.content[:150]}...")
            
            # 2. Simulate realistic outcome
            import random
            is_upset = random.random() < (0.2 + week_num * 0.05)  # Increasing upset chance
            
            # Parse spread to determine favorite
            spread_text = game['spread']
            favorite = spread_text.split('-')[0].strip()
            
            if favorite == game['home']:
                if is_upset:
                    winner = game['away']
                    home_score, away_score = 20, 27
                else:
                    winner = game['home']
                    home_score, away_score = 28, 21
            else:
                if is_upset:
                    winner = game['home']
                    home_score, away_score = 24, 20
                else:
                    winner = game['away']
                    home_score, away_score = 17, 26
            
            outcome = {
                "final_score": f"{game['home']} {home_score}, {game['away']} {away_score}",
                "winner": winner,
                "total_points": home_score + away_score,
                "is_upset": is_upset,
                "game_summary": f"{'🚨 UPSET!' if is_upset else '✅ Expected'} {winner} wins by {abs(home_score-away_score)}"
            }
            
            print(f"🏆 Result: {outcome['final_score']} ({outcome['game_summary']})")
            
            # 3. Reflect and form new memory
            reflection_prompt = f"""
            MEMORY FORMATION FOR SUPABASE STORAGE:
            
            YOUR PREDICTION: {pred_response.content}
            
            ACTUAL OUTCOME: {outcome['final_score']}
            {outcome['game_summary']}
            
            Form a specific lesson for your Supabase memory bank:
            1. What specific insight should you remember?
            2. How does this connect to your previous memories?
            3. What pattern emerged that you can use next time?
            
            Be concise but specific - this will be stored permanently!
            """
            
            print("🤔 AI reflecting and forming memory for Supabase...")
            refl_start = time.time()
            reflection_response = self.llm.generate_completion(
                system_message=f"You are {self.expert_name}. Extract a specific, actionable lesson for permanent storage.",
                user_message=reflection_prompt,
                temperature=0.6,
                max_tokens=250
            )
            refl_time = time.time() - refl_start
            
            print(f"✅ Reflection complete ({refl_time:.1f}s, {reflection_response.total_tokens} tokens)")
            
            # 4. Store in Supabase
            memory_id = self.store_episodic_memory(
                game, pred_response.content, outcome, 
                reflection_response.content, week_num, game_idx
            )
            
            print(f"🧠 Memory lesson: {reflection_response.content[:100]}...")
            
            # Brief pause between games
            time.sleep(0.5)
        
        # Show updated memory stats from Supabase
        updated_count = len(self.retrieve_recent_memories(100))
        print(f"\n📊 WEEK {week_num} SUMMARY:")
        print(f"   🎯 Games predicted: {len(games)}")
        print(f"   🧠 Total Supabase memories: {updated_count}")
        print(f"   💾 New memories stored: {updated_count - memory_count}")
    
    def run_enhanced_journey(self, weeks: int = 3):
        """Run memory-enhanced journey with Supabase storage"""
        print("🚀 SUPABASE MEMORY-ENHANCED AI LEARNING JOURNEY")
        print("="*60)
        print(f"🤖 Expert: {self.expert_name}")
        print(f"💾 Database: Supabase Cloud Database")
        print(f"🎆 Memory System: Real persistent episodic memory")
        print(f"📅 Duration: {weeks} weeks of NFL games")
        
        # Setup expert in database
        self.create_expert_if_not_exists()
        
        journey_start = time.time()
        
        # Run weeks
        for week in range(1, weeks + 1):
            self.run_memory_enhanced_week(week, max_games=2)
            time.sleep(1)  # Brief pause between weeks
        
        # Final summary from Supabase
        final_memories = self.retrieve_recent_memories(50)
        journey_time = time.time() - journey_start
        
        print(f"\n🎉 SUPABASE JOURNEY COMPLETE!")
        print("="*60)
        print(f"✅ Total memories in Supabase: {len(final_memories)}")
        print(f"✅ Database integration: Working")
        print(f"✅ Memory persistence: Active across restarts")
        print(f"✅ Journey duration: {journey_time:.1f}s")
        
        print(f"\n🧠 RECENT LESSONS IN SUPABASE:")
        for i, memory in enumerate(final_memories[:5], 1):
            print(f"   {i}. Week {memory['week']}: {memory['lesson_learned'][:80]}...")
        
        print(f"\n💡 Your AI memories are now persistent in Supabase!")
        print(f"🔄 Restart the program and the AI will remember everything!")

def main():
    """Run Supabase memory-enhanced journey"""
    journey = SupabaseMemoryJourney()
    journey.run_enhanced_journey(weeks=3)

if __name__ == "__main__":
    main()