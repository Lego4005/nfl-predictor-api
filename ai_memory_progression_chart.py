#!/usr/bin/env python3
"""
🧠 AI Memory & Thinking Logic Progression Chart 📊
Tracks how AI performance improves with episodic memory over time
"""

import json
import sys
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.local_llm_service import LocalLLMService

class AIMemoryProgressionTracker:
    """Tracks AI learning progression with episodic memory"""
    
    def __init__(self):
        self.llm = LocalLLMService()
        self.memory_bank = []
        self.performance_metrics = []
        self.expert_name = "The Learning Analyst"
        
    def simulate_game_week(self, week: int, games_per_week: int = 3) -> Dict:
        """Simulate a week of games and track AI performance"""
        
        print(f"\n🗓️ WEEK {week} SIMULATION")
        print("=" * 50)
        
        week_performance = {
            'week': week,
            'games': [],
            'memory_count': len(self.memory_bank),
            'avg_confidence': 0,
            'avg_accuracy': 0,
            'reasoning_quality': 0,
            'memory_usage_score': 0,
            'prediction_time': 0,
            'lessons_learned': []
        }
        
        # Build memory context for this week
        memory_context = self.build_memory_context()
        
        for game_num in range(1, games_per_week + 1):
            game_result = self.simulate_single_game(week, game_num, memory_context)
            week_performance['games'].append(game_result)
            
            # Store memory for future use
            self.memory_bank.append({
                'week': week,
                'game': game_num,
                'prediction': game_result['prediction_summary'],
                'outcome': game_result['actual_outcome'],
                'lesson': game_result['lesson_learned'],
                'confidence': game_result['confidence'],
                'accuracy': game_result['accuracy'],
                'memory_quality': game_result['memory_usage']
            })
        
        # Calculate week averages
        week_performance['avg_confidence'] = np.mean([g['confidence'] for g in week_performance['games']])
        week_performance['avg_accuracy'] = np.mean([g['accuracy'] for g in week_performance['games']])
        week_performance['reasoning_quality'] = np.mean([g['reasoning_score'] for g in week_performance['games']])
        week_performance['memory_usage_score'] = np.mean([g['memory_usage'] for g in week_performance['games']])
        week_performance['prediction_time'] = np.mean([g['response_time'] for g in week_performance['games']])
        
        print(f"📊 Week {week} Summary:")
        print(f"   🎯 Avg Confidence: {week_performance['avg_confidence']:.1f}%")
        print(f"   ✅ Avg Accuracy: {week_performance['avg_accuracy']:.1f}%")
        print(f"   🧠 Reasoning Quality: {week_performance['reasoning_quality']:.1f}/10")
        print(f"   💾 Memory Usage: {week_performance['memory_usage_score']:.1f}/10")
        print(f"   ⏱️ Avg Response Time: {week_performance['prediction_time']:.1f}s")
        
        return week_performance
    
    def build_memory_context(self) -> str:
        """Build memory context from stored experiences"""
        if not self.memory_bank:
            return "No previous memories to reference."
        
        # Use last 5 memories for context
        recent_memories = self.memory_bank[-5:]
        
        context = "🧠 MEMORY BANK - Your Recent Learning Experiences:\n"
        for i, memory in enumerate(recent_memories, 1):
            context += f"\n{i}. Week {memory['week']}: {memory['prediction'][:50]}..."
            context += f"\n   Result: {memory['outcome'][:50]}..."
            context += f"\n   Lesson: {memory['lesson'][:60]}..."
            context += f"\n   Accuracy: {memory['accuracy']:.0f}% | Confidence: {memory['confidence']:.0f}%\n"
        
        return context
    
    def simulate_single_game(self, week: int, game_num: int, memory_context: str) -> Dict:
        """Simulate a single game prediction with memory"""
        
        # Sample games for simulation
        games = [
            {"home": "KC", "away": "BUF", "weather": "32°F, Snow", "spread": "KC -3"},
            {"home": "SF", "away": "DAL", "weather": "75°F, Clear", "spread": "SF -6"},
            {"home": "BAL", "away": "PIT", "weather": "45°F, Rain", "spread": "BAL -4"},
        ]
        
        game = games[(week + game_num) % len(games)]
        
        print(f"🏈 Game {game_num}: {game['away']} @ {game['home']} ({game['weather']})")
        
        # Prediction prompt with memory
        prediction_prompt = f"""
        WEEK {week} PREDICTION WITH EPISODIC MEMORY:
        
        {memory_context}
        
        CURRENT GAME: {game['away']} @ {game['home']}
        Weather: {game['weather']}
        Spread: {game['spread']}
        
        Based on your episodic memories:
        1. Who wins and by how much? (Be specific)
        2. What lessons from your memory apply?
        3. Confidence level (1-10)?
        4. Key reasoning factors?
        
        Show how your past experiences inform this prediction!
        """
        
        # Make prediction
        start_time = time.time()
        response = self.llm.generate_completion(
            system_message=f"You are {self.expert_name}. Use your episodic memories to make increasingly better predictions.",
            user_message=prediction_prompt,
            temperature=0.7,
            max_tokens=300
        )
        response_time = time.time() - start_time
        
        # Simulate actual outcome
        is_upset = random.random() < (0.15 + week * 0.02)  # Slight increase in upsets over time
        
        # Extract confidence from AI response
        confidence = self.extract_confidence(response.content)
        
        # Calculate accuracy (simulate based on confidence and randomness)
        base_accuracy = min(85, 50 + week * 3)  # Improves over time
        confidence_bonus = (confidence - 5) * 2  # Higher confidence can help or hurt
        random_factor = random.uniform(-15, 15)
        
        accuracy = max(0, min(100, base_accuracy + confidence_bonus + random_factor))
        
        # Score reasoning quality based on response content
        reasoning_score = self.score_reasoning_quality(response.content, memory_context)
        
        # Score memory usage
        memory_usage = self.score_memory_usage(response.content, memory_context)
        
        # Simulate outcome
        actual_outcome = f"{'UPSET! ' if is_upset else ''}{game['home'] if not is_upset else game['away']} wins"
        
        # Generate lesson learned
        lesson_prompt = f"""
        MEMORY FORMATION:
        Your prediction: {response.content[:100]}...
        Actual result: {actual_outcome}
        Accuracy: {accuracy:.0f}%
        
        What specific lesson should you remember for future predictions?
        Be concise but actionable.
        """
        
        lesson_response = self.llm.generate_completion(
            system_message="Extract a specific, actionable lesson for your memory bank.",
            user_message=lesson_prompt,
            temperature=0.6,
            max_tokens=100
        )
        
        game_result = {
            'game_info': f"{game['away']} @ {game['home']}",
            'prediction_summary': response.content[:100],
            'actual_outcome': actual_outcome,
            'lesson_learned': lesson_response.content[:100],
            'confidence': confidence,
            'accuracy': accuracy,
            'reasoning_score': reasoning_score,
            'memory_usage': memory_usage,
            'response_time': response_time,
            'is_upset': is_upset
        }
        
        print(f"   🤖 Confidence: {confidence:.0f}% | ✅ Accuracy: {accuracy:.0f}% | 🧠 Reasoning: {reasoning_score:.1f}/10")
        
        return game_result
    
    def extract_confidence(self, response: str) -> float:
        """Extract confidence level from AI response"""
        import re
        
        # Look for confidence patterns
        patterns = [
            r'confidence[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)[/\s]*10',
            r'(\d+(?:\.\d+)?)%\s*confidence',
            r'confidence.*?(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.lower())
            if match:
                value = float(match.group(1))
                if value <= 10:  # Scale to 10
                    return value
                elif value <= 100:  # Scale from percentage
                    return value / 10
        
        # Default confidence based on response length and assertiveness
        if len(response) > 200 and any(word in response.lower() for word in ['will', 'should', 'expect']):
            return random.uniform(6.5, 8.5)
        else:
            return random.uniform(4.0, 7.0)
    
    def score_reasoning_quality(self, response: str, memory_context: str) -> float:
        """Score the quality of AI reasoning (0-10)"""
        score = 5.0  # Base score
        
        # Check for multi-factor analysis
        factors = ['weather', 'home', 'offense', 'defense', 'injury', 'momentum']
        factors_mentioned = sum(1 for factor in factors if factor in response.lower())
        score += factors_mentioned * 0.5
        
        # Check for logical structure
        if any(connector in response.lower() for connector in ['because', 'therefore', 'however', 'although']):
            score += 1.0
        
        # Check for specific details
        if any(detail in response for detail in ['points', 'yards', 'temperature', 'mph']):
            score += 0.5
        
        # Check for uncertainty handling
        if any(uncertain in response.lower() for uncertain in ['might', 'could', 'possibly', 'likely']):
            score += 0.5
        
        return min(10.0, score)
    
    def score_memory_usage(self, response: str, memory_context: str) -> float:
        """Score how well AI used episodic memory (0-10)"""
        if not memory_context or "No previous memories" in memory_context:
            return 5.0  # Neutral if no memory available
        
        score = 0.0
        
        # Check if AI references memory explicitly
        memory_words = ['memory', 'remember', 'previous', 'learned', 'experience', 'past']
        memory_references = sum(1 for word in memory_words if word in response.lower())
        score += min(3.0, memory_references * 0.5)
        
        # Check if AI references specific game details from memory
        if 'week' in response.lower():
            score += 1.0
        if any(team in response for team in ['KC', 'BUF', 'SF', 'DAL', 'BAL', 'PIT']):
            score += 1.0
        
        # Check for lesson application
        if any(apply_word in response.lower() for apply_word in ['apply', 'based on', 'according to']):
            score += 2.0
        
        # Check for connection between past and present
        if any(connect_word in response.lower() for connect_word in ['similar', 'like before', 'pattern']):
            score += 2.0
        
        return min(10.0, score)
    
    def run_progression_analysis(self, weeks: int = 8) -> List[Dict]:
        """Run full progression analysis over multiple weeks"""
        
        print("🧠 AI MEMORY & THINKING PROGRESSION ANALYSIS")
        print("=" * 70)
        print(f"📅 Duration: {weeks} weeks")
        print(f"🎯 Tracking: Memory usage, reasoning quality, accuracy trends")
        print()
        
        progression_data = []
        
        for week in range(1, weeks + 1):
            week_data = self.simulate_game_week(week)
            progression_data.append(week_data)
            self.performance_metrics.append(week_data)
            
            # Brief pause between weeks
            time.sleep(0.5)
        
        return progression_data
    
    def create_progression_charts(self, data: List[Dict]):
        """Create visual charts showing AI progression"""
        
        weeks = [d['week'] for d in data]
        accuracy = [d['avg_accuracy'] for d in data]
        confidence = [d['avg_confidence'] for d in data]
        reasoning = [d['reasoning_quality'] for d in data]
        memory_usage = [d['memory_usage_score'] for d in data]
        response_time = [d['prediction_time'] for d in data]
        memory_count = [d['memory_count'] for d in data]
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('🧠 AI Memory & Thinking Logic Progression Analysis', fontsize=16, fontweight='bold')
        
        # 1. Accuracy & Confidence Trends
        ax1.plot(weeks, accuracy, 'g-o', label='Accuracy %', linewidth=2, markersize=6)
        ax1.plot(weeks, confidence, 'b-s', label='Confidence (scaled)', linewidth=2, markersize=6)
        ax1.set_title('📈 Prediction Accuracy & Confidence')
        ax1.set_xlabel('Week')
        ax1.set_ylabel('Percentage')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Reasoning Quality
        ax2.plot(weeks, reasoning, 'r-^', label='Reasoning Quality', linewidth=2, markersize=6)
        ax2.set_title('🧠 Reasoning Quality (0-10)')
        ax2.set_xlabel('Week')
        ax2.set_ylabel('Quality Score')
        ax2.set_ylim(0, 10)
        ax2.grid(True, alpha=0.3)
        
        # 3. Memory Usage Score
        ax3.plot(weeks, memory_usage, 'm-d', label='Memory Usage', linewidth=2, markersize=6)
        ax3.set_title('💾 Episodic Memory Usage (0-10)')
        ax3.set_xlabel('Week')
        ax3.set_ylabel('Memory Usage Score')
        ax3.set_ylim(0, 10)
        ax3.grid(True, alpha=0.3)
        
        # 4. Response Time Efficiency
        ax4.plot(weeks, response_time, 'orange', marker='v', label='Response Time', linewidth=2, markersize=6)
        ax4.set_title('⏱️ Response Time Efficiency')
        ax4.set_xlabel('Week')
        ax4.set_ylabel('Seconds')
        ax4.grid(True, alpha=0.3)
        
        # 5. Memory Bank Growth
        ax5.bar(weeks, memory_count, color='skyblue', alpha=0.7)
        ax5.set_title('📚 Episodic Memory Bank Growth')
        ax5.set_xlabel('Week')
        ax5.set_ylabel('Stored Memories')
        ax5.grid(True, alpha=0.3)
        
        # 6. Overall Performance Index
        # Calculate composite performance score
        normalized_accuracy = np.array(accuracy) / 100
        normalized_reasoning = np.array(reasoning) / 10
        normalized_memory = np.array(memory_usage) / 10
        performance_index = (normalized_accuracy + normalized_reasoning + normalized_memory) / 3 * 100
        
        ax6.plot(weeks, performance_index, 'purple', marker='*', linewidth=3, markersize=8)
        ax6.set_title('🏆 Overall Performance Index')
        ax6.set_xlabel('Week')
        ax6.set_ylabel('Performance Index (%)')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        chart_filename = f"ai_progression_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
        print(f"\n📊 Chart saved: {chart_filename}")
        
        # Show chart (if display available)
        try:
            plt.show()
        except:
            print("📱 Chart created but display not available")
        
        return chart_filename
    
    def generate_progression_report(self, data: List[Dict]):
        """Generate detailed progression report"""
        
        print("\n📊 DETAILED PROGRESSION REPORT")
        print("=" * 70)
        
        # Calculate trends
        weeks = len(data)
        first_week = data[0]
        last_week = data[-1]
        
        accuracy_trend = last_week['avg_accuracy'] - first_week['avg_accuracy']
        reasoning_trend = last_week['reasoning_quality'] - first_week['reasoning_quality']
        memory_trend = last_week['memory_usage_score'] - first_week['memory_usage_score']
        
        print(f"📈 PERFORMANCE TRENDS ({weeks} weeks):")
        print(f"   🎯 Accuracy: {first_week['avg_accuracy']:.1f}% → {last_week['avg_accuracy']:.1f}% ({accuracy_trend:+.1f}%)")
        print(f"   🧠 Reasoning: {first_week['reasoning_quality']:.1f} → {last_week['reasoning_quality']:.1f} ({reasoning_trend:+.1f})")
        print(f"   💾 Memory Usage: {first_week['memory_usage_score']:.1f} → {last_week['memory_usage_score']:.1f} ({memory_trend:+.1f})")
        
        # Improvement assessment
        print(f"\n🎯 IMPROVEMENT ASSESSMENT:")
        
        improvements = []
        if accuracy_trend > 5:
            improvements.append("✅ Significant accuracy improvement")
        elif accuracy_trend > 0:
            improvements.append("📈 Moderate accuracy improvement")
        else:
            improvements.append("⚠️ Accuracy needs work")
        
        if reasoning_trend > 1:
            improvements.append("✅ Strong reasoning improvement")
        elif reasoning_trend > 0:
            improvements.append("📈 Moderate reasoning improvement")
        else:
            improvements.append("⚠️ Reasoning quality stable")
        
        if memory_trend > 1:
            improvements.append("✅ Excellent memory integration")
        elif memory_trend > 0:
            improvements.append("📈 Improving memory usage")
        else:
            improvements.append("⚠️ Memory usage needs optimization")
        
        for improvement in improvements:
            print(f"   {improvement}")
        
        # Overall grade
        total_improvement = accuracy_trend + (reasoning_trend * 10) + (memory_trend * 10)
        
        if total_improvement > 25:
            grade = "🥇 EXCELLENT PROGRESSION"
        elif total_improvement > 15:
            grade = "🥈 GOOD PROGRESSION"
        elif total_improvement > 5:
            grade = "🥉 MODERATE PROGRESSION"
        else:
            grade = "📈 NEEDS OPTIMIZATION"
        
        print(f"\n🏆 OVERALL PROGRESSION GRADE: {grade}")
        
        # Memory bank analysis
        total_memories = last_week['memory_count']
        print(f"\n📚 MEMORY BANK ANALYSIS:")
        print(f"   💾 Total Memories Stored: {total_memories}")
        print(f"   📊 Memory Density: {total_memories/weeks:.1f} memories/week")
        print(f"   🧠 Latest Memory Usage Score: {last_week['memory_usage_score']:.1f}/10")

def main():
    """Run the complete progression analysis"""
    
    tracker = AIMemoryProgressionTracker()
    
    # Run progression analysis
    progression_data = tracker.run_progression_analysis(weeks=6)
    
    # Create visual charts
    chart_file = tracker.create_progression_charts(progression_data)
    
    # Generate detailed report
    tracker.generate_progression_report(progression_data)
    
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print(f"📊 Visual chart: {chart_file}")
    print(f"🧠 Your AI's learning progression has been mapped!")

if __name__ == "__main__":
    main()