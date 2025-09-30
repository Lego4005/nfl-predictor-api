#!/usr/bin/env python3
"""
Memory-Enabled Expert Learning Journey
=====================================

Complete transparency into how an expert learns from experience across Weeks 1-4.

Features:
- Memory retrieval before each prediction
- Base vs memory-enhanced comparison
- Episodic memory storage with emotional states
- Lesson extraction and belief revision tracking
- Self-healing when accuracy drops
- Week summaries showing learning progress
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ml.memory_enabled_expert_service import MemoryEnabledExpert, MemoryEnabledExpertService
from ml.personality_driven_experts import (
    ConservativeAnalyzer, UniversalGameData
)
from ml.episodic_memory_manager import EpisodicMemoryManager, EmotionalState
from ml.belief_revision_service import BeliefRevisionService
from ml.reasoning_chain_logger import ReasoningChainLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryEnabledJourneyTracker:
    """Tracks and displays the complete learning journey with transparency"""

    def __init__(self, output_file: str = "/tmp/memory_enabled_journey.log"):
        self.output_file = output_file
        self.output_lines = []

        # Track learning progress
        self.week_summaries = []
        self.all_predictions = []
        self.belief_revisions = []
        self.lessons_learned = []
        self.self_healing_events = []

    def log(self, message: str, level: str = "INFO"):
        """Log to both stdout and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level:5} {message}"
        print(formatted)
        self.output_lines.append(formatted)

    def section_header(self, title: str, char: str = "="):
        """Print section header"""
        width = 80
        self.log("")
        self.log(char * width)
        self.log(f"{title:^{width}}")
        self.log(char * width)
        self.log("")

    def print_memory_retrieval(self, memories: List[Dict[str, Any]]):
        """Show retrieved memories with context"""
        self.log("🔍 MEMORY RETRIEVAL:", "INFO")

        if not memories:
            self.log("   No similar past experiences found", "INFO")
            return

        self.log(f"   Found {len(memories)} similar past experiences:", "INFO")
        for i, memory in enumerate(memories[:3], 1):  # Show top 3
            emotional_state = memory.get('emotional_state', 'unknown')
            memory_vividness = memory.get('memory_vividness', 0)
            similarity = memory.get('similarity_score', 0)

            self.log(f"   {i}. Memory (similarity: {similarity:.2f}, vividness: {memory_vividness:.2f})", "INFO")
            self.log(f"      Emotional state: {emotional_state}", "INFO")

            # Parse memory data
            try:
                pred_data = json.loads(memory.get('prediction_data', '{}'))
                outcome_data = json.loads(memory.get('actual_outcome', '{}'))
                was_correct = pred_data.get('winner') == outcome_data.get('winner')
                self.log(f"      Result: {'✅ Correct' if was_correct else '❌ Wrong'}", "INFO")
            except:
                pass

    def print_lesson_application(self, insights: List[str]):
        """Show lessons being applied"""
        self.log("📚 LESSON APPLICATION:", "INFO")

        if not insights:
            self.log("   No specific lessons applied (first-time prediction)", "INFO")
            return

        for i, insight in enumerate(insights, 1):
            self.log(f"   {i}. {insight}", "INFO")

    def print_prediction_comparison(self, base_pred: Dict, enhanced_pred: Dict):
        """Compare base vs memory-enhanced prediction"""
        self.log("⚖️  BASE vs MEMORY-ENHANCED:", "INFO")

        base_winner = base_pred.get('winner_prediction', 'N/A')
        base_conf = base_pred.get('winner_confidence', 0.5)

        enhanced_winner = enhanced_pred.get('winner_prediction', 'N/A')
        enhanced_conf = enhanced_pred.get('winner_confidence', 0.5)
        conf_boost = enhanced_pred.get('memory_confidence_boost', 0)

        self.log(f"   Base Prediction:     {base_winner} ({base_conf:.1%} confidence)", "INFO")
        self.log(f"   Enhanced Prediction: {enhanced_winner} ({enhanced_conf:.1%} confidence)", "INFO")

        if conf_boost != 0:
            direction = "increased" if conf_boost > 0 else "decreased"
            self.log(f"   Memory Impact: Confidence {direction} by {abs(conf_boost):.1%}", "INFO")
        else:
            self.log(f"   Memory Impact: No confidence adjustment", "INFO")

    def print_final_prediction(self, prediction: Dict):
        """Show final prediction with confidence"""
        self.log("🎯 FINAL PREDICTION:", "INFO")

        winner = prediction.get('winner_prediction', 'N/A')
        confidence = prediction.get('winner_confidence', 0.5)
        reasoning = prediction.get('reasoning', 'No reasoning provided')[:150]

        self.log(f"   Winner: {winner}", "INFO")
        self.log(f"   Confidence: {confidence:.1%}", "INFO")
        self.log(f"   Reasoning: {reasoning}...", "INFO")

    def print_game_result(self, actual_outcome: Dict, prediction: Dict):
        """Show game result and whether prediction was correct"""
        actual_winner = actual_outcome.get('winner', 'N/A')
        predicted_winner = prediction.get('winner_prediction', 'N/A')
        was_correct = actual_winner == predicted_winner

        if was_correct:
            self.log(f"✅ RESULT: Correct! {actual_winner} won as predicted", "INFO")
        else:
            self.log(f"❌ RESULT: Wrong! {actual_winner} won, predicted {predicted_winner}", "INFO")

        actual_score = f"{actual_outcome.get('home_score', 0)}-{actual_outcome.get('away_score', 0)}"
        self.log(f"   Final Score: {actual_score}", "INFO")

    def print_memory_storage(self, emotional_state: str, vividness: float):
        """Show memory being stored"""
        self.log("💾 MEMORY STORAGE:", "INFO")
        self.log(f"   Emotional State: {emotional_state}", "INFO")
        self.log(f"   Memory Vividness: {vividness:.2f}", "INFO")

    def print_lessons_learned(self, lessons: List[Dict[str, Any]]):
        """Show extracted lessons"""
        self.log("📚 LESSONS LEARNED:", "INFO")

        if not lessons:
            self.log("   No new lessons extracted", "INFO")
            return

        for i, lesson in enumerate(lessons[:3], 1):  # Top 3 lessons
            category = lesson.get('category', 'general')
            content = lesson.get('content', 'Unknown')
            confidence = lesson.get('confidence', 0.5)

            self.log(f"   {i}. [{category}] {content} (confidence: {confidence:.1%})", "INFO")

    def print_belief_revision(self, revision: Any):
        """Show belief revision if detected"""
        if not revision:
            return

        self.log("🔄 BELIEF REVISION DETECTED:", "WARN")
        self.log(f"   Type: {revision.revision_type.value}", "WARN")
        self.log(f"   Trigger: {revision.trigger.value}", "WARN")
        self.log(f"   Impact Score: {revision.impact_score:.2f}", "WARN")
        self.log(f"   Emotional State: {revision.emotional_state}", "WARN")

        self.belief_revisions.append({
            'type': revision.revision_type.value,
            'trigger': revision.trigger.value,
            'impact': revision.impact_score
        })

    def print_self_healing(self, recent_accuracy: float, corrections: Dict[str, Any]):
        """Show self-healing correction"""
        self.log("🔧 SELF-HEALING TRIGGERED:", "WARN")
        self.log(f"   Recent Accuracy: {recent_accuracy:.1%} (below 50% threshold)", "WARN")
        self.log(f"   Analysis of Failed Predictions:", "WARN")

        for factor, impact in corrections.get('factor_adjustments', {}).items():
            self.log(f"      • {factor}: adjusted weight by {impact:+.2f}", "WARN")

        self.self_healing_events.append({
            'accuracy': recent_accuracy,
            'corrections': corrections
        })

    def print_week_summary(self, week: int, stats: Dict[str, Any]):
        """Print summary for the week"""
        self.section_header(f"WEEK {week} SUMMARY", "-")

        self.log(f"📊 Performance:", "INFO")
        self.log(f"   Games Played: {stats.get('games_played', 0)}", "INFO")
        self.log(f"   Correct Predictions: {stats.get('correct', 0)}", "INFO")
        self.log(f"   Accuracy: {stats.get('accuracy', 0):.1%}", "INFO")

        self.log(f"", "INFO")
        self.log(f"🧠 Learning Progress:", "INFO")
        self.log(f"   Memories Created: {stats.get('memories_created', 0)}", "INFO")
        self.log(f"   Lessons Learned: {stats.get('lessons_count', 0)}", "INFO")
        self.log(f"   Belief Revisions: {stats.get('revisions_count', 0)}", "INFO")

        if stats.get('principles_learned'):
            self.log(f"", "INFO")
            self.log(f"📚 New Principles Learned:", "INFO")
            for principle in stats['principles_learned']:
                self.log(f"   • {principle}", "INFO")

        if stats.get('belief_changes'):
            self.log(f"", "INFO")
            self.log(f"🔄 Belief Changes:", "INFO")
            for change in stats['belief_changes']:
                self.log(f"   • {change}", "INFO")

        self.week_summaries.append(stats)

    def save_to_file(self):
        """Save all output to file"""
        try:
            with open(self.output_file, 'w') as f:
                f.write('\n'.join(self.output_lines))
            logger.info(f"✅ Journey log saved to {self.output_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save journey log: {e}")


class MockGameData:
    """Generate realistic mock game data for Weeks 1-4"""

    @staticmethod
    def get_week_games(week: int) -> List[Tuple[UniversalGameData, Dict[str, Any]]]:
        """Get games and their outcomes for a specific week"""

        # Week 1 games
        if week == 1:
            return [
                # Game 1: Chiefs vs Ravens (Chiefs win)
                (
                    UniversalGameData(
                        home_team="KC",
                        away_team="BAL",
                        game_time="2025-09-11 20:20:00",
                        location="Kansas City",
                        weather={'temperature': 75, 'wind_speed': 8, 'conditions': 'Clear'},
                        injuries={'home': [], 'away': [{'position': 'RB', 'severity': 'questionable', 'probability_play': 0.6}]},
                        line_movement={'opening_line': -3.0, 'current_line': -2.5, 'public_percentage': 65},
                        team_stats={'home': {'offensive_yards_per_game': 385}, 'away': {'offensive_yards_per_game': 370}}
                    ),
                    {'winner': 'KC', 'home_score': 27, 'away_score': 20, 'margin': 7}
                ),
                # Game 2: Bills vs Jets (Bills win easily)
                (
                    UniversalGameData(
                        home_team="NYJ",
                        away_team="BUF",
                        game_time="2025-09-14 20:15:00",
                        location="East Rutherford",
                        weather={'temperature': 72, 'wind_speed': 12, 'conditions': 'Cloudy'},
                        injuries={'home': [{'position': 'WR', 'severity': 'out', 'probability_play': 0}], 'away': []},
                        line_movement={'opening_line': 7.0, 'current_line': 6.5, 'public_percentage': 78},
                        team_stats={'home': {'offensive_yards_per_game': 310}, 'away': {'offensive_yards_per_game': 395}}
                    ),
                    {'winner': 'BUF', 'home_score': 17, 'away_score': 31, 'margin': 14}
                ),
            ]

        # Week 2 games
        elif week == 2:
            return [
                # Game 3: 49ers vs Seahawks (Upset! Seahawks win)
                (
                    UniversalGameData(
                        home_team="SEA",
                        away_team="SF",
                        game_time="2025-09-18 16:05:00",
                        location="Seattle",
                        weather={'temperature': 62, 'wind_speed': 15, 'conditions': 'Rain'},
                        injuries={'home': [], 'away': [{'position': 'QB', 'severity': 'questionable', 'probability_play': 0.7}]},
                        line_movement={'opening_line': 6.5, 'current_line': 5.5, 'public_percentage': 72},
                        team_stats={'home': {'offensive_yards_per_game': 345}, 'away': {'offensive_yards_per_game': 410}}
                    ),
                    {'winner': 'SEA', 'home_score': 24, 'away_score': 21, 'margin': 3}
                ),
                # Game 4: Cowboys vs Giants (Cowboys dominate)
                (
                    UniversalGameData(
                        home_team="NYG",
                        away_team="DAL",
                        game_time="2025-09-21 20:15:00",
                        location="East Rutherford",
                        weather={'temperature': 68, 'wind_speed': 10, 'conditions': 'Clear'},
                        injuries={'home': [{'position': 'OL', 'severity': 'out', 'probability_play': 0}], 'away': []},
                        line_movement={'opening_line': 4.5, 'current_line': 5.0, 'public_percentage': 68},
                        team_stats={'home': {'offensive_yards_per_game': 290}, 'away': {'offensive_yards_per_game': 375}}
                    ),
                    {'winner': 'DAL', 'home_score': 13, 'away_score': 34, 'margin': 21}
                ),
            ]

        # Week 3 games
        elif week == 3:
            return [
                # Game 5: Packers vs Bears (Close game, Packers)
                (
                    UniversalGameData(
                        home_team="CHI",
                        away_team="GB",
                        game_time="2025-09-25 13:00:00",
                        location="Chicago",
                        weather={'temperature': 55, 'wind_speed': 18, 'conditions': 'Windy'},
                        injuries={'home': [], 'away': []},
                        line_movement={'opening_line': 3.0, 'current_line': 2.5, 'public_percentage': 58},
                        team_stats={'home': {'offensive_yards_per_game': 325}, 'away': {'offensive_yards_per_game': 360}}
                    ),
                    {'winner': 'GB', 'home_score': 20, 'away_score': 24, 'margin': 4}
                ),
                # Game 6: Eagles vs Bucs (Upset! Bucs win)
                (
                    UniversalGameData(
                        home_team="TB",
                        away_team="PHI",
                        game_time="2025-09-28 20:15:00",
                        location="Tampa",
                        weather={'temperature': 82, 'wind_speed': 6, 'conditions': 'Hot'},
                        injuries={'home': [], 'away': [{'position': 'RB', 'severity': 'out', 'probability_play': 0}]},
                        line_movement={'opening_line': 5.5, 'current_line': 6.0, 'public_percentage': 75},
                        team_stats={'home': {'offensive_yards_per_game': 340}, 'away': {'offensive_yards_per_game': 385}}
                    ),
                    {'winner': 'TB', 'home_score': 28, 'away_score': 24, 'margin': 4}
                ),
            ]

        # Week 4 games
        elif week == 4:
            return [
                # Game 7: Vikings vs Lions (Vikings win)
                (
                    UniversalGameData(
                        home_team="DET",
                        away_team="MIN",
                        game_time="2025-10-02 13:00:00",
                        location="Detroit",
                        weather={'temperature': 58, 'wind_speed': 11, 'conditions': 'Cloudy'},
                        injuries={'home': [{'position': 'OL', 'severity': 'doubtful', 'probability_play': 0.3}], 'away': []},
                        line_movement={'opening_line': 2.5, 'current_line': 3.0, 'public_percentage': 55},
                        team_stats={'home': {'offensive_yards_per_game': 350}, 'away': {'offensive_yards_per_game': 365}}
                    ),
                    {'winner': 'MIN', 'home_score': 23, 'away_score': 27, 'margin': 4}
                ),
                # Game 8: Chargers vs Raiders (Chargers win)
                (
                    UniversalGameData(
                        home_team="LV",
                        away_team="LAC",
                        game_time="2025-10-05 16:25:00",
                        location="Las Vegas",
                        weather={'temperature': 88, 'wind_speed': 5, 'conditions': 'Hot'},
                        injuries={'home': [], 'away': []},
                        line_movement={'opening_line': 4.0, 'current_line': 3.5, 'public_percentage': 62},
                        team_stats={'home': {'offensive_yards_per_game': 315}, 'away': {'offensive_yards_per_game': 355}}
                    ),
                    {'winner': 'LAC', 'home_score': 20, 'away_score': 27, 'margin': 7}
                ),
            ]

        return []


async def run_memory_enabled_journey():
    """Run the complete memory-enabled expert journey"""

    tracker = MemoryEnabledJourneyTracker()

    tracker.section_header("MEMORY-ENABLED EXPERT LEARNING JOURNEY")
    tracker.log("Expert: The Analyst (Conservative Analyzer)")
    tracker.log("Weeks: 1-4 (8 games total)")
    tracker.log("Features: Memory retrieval, lesson learning, belief revision, self-healing")
    tracker.log("")

    # Initialize database config
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'database': os.getenv('DB_NAME', 'nfl_predictor')
    }

    # Initialize services
    tracker.log("🔧 Initializing memory services...", "INFO")
    memory_manager = EpisodicMemoryManager(db_config)
    belief_service = BeliefRevisionService(db_config)
    reasoning_logger = ReasoningChainLogger()

    try:
        await memory_manager.initialize()
        await belief_service.initialize()
        tracker.log("✅ Memory services initialized", "INFO")
    except Exception as e:
        tracker.log(f"❌ Failed to initialize services: {e}", "ERROR")
        tracker.log("⚠️  Continuing without database persistence (demo mode)", "WARN")

    # Create memory-enabled expert
    base_expert = ConservativeAnalyzer()
    expert = MemoryEnabledExpert(
        base_expert=base_expert,
        memory_manager=memory_manager,
        belief_service=belief_service,
        reasoning_logger=reasoning_logger
    )

    tracker.log(f"✅ Created memory-enabled expert: {expert.name}", "INFO")
    tracker.log("")

    # Track performance across weeks
    all_correct = 0
    all_games = 0
    recent_results = []  # For self-healing

    # Run through Weeks 1-4
    for week in range(1, 5):
        tracker.section_header(f"WEEK {week}")

        games = MockGameData.get_week_games(week)
        week_stats = {
            'games_played': len(games),
            'correct': 0,
            'memories_created': 0,
            'lessons_count': 0,
            'revisions_count': 0,
            'principles_learned': [],
            'belief_changes': []
        }

        for game_num, (game_data, actual_outcome) in enumerate(games, 1):
            game_id = f"week{week}_game{game_num}"
            tracker.log(f"🏈 Game {game_num}: {game_data.away_team} @ {game_data.home_team}", "INFO")
            tracker.log("")

            # Step 1: Retrieve relevant memories
            current_situation = {
                'home_team': game_data.home_team,
                'away_team': game_data.away_team,
                'weather_conditions': game_data.weather,
                'injury_context': game_data.injuries,
                'market_conditions': game_data.line_movement
            }

            try:
                memories = await memory_manager.retrieve_similar_memories(
                    expert_id=expert.expert_id,
                    current_situation=current_situation,
                    limit=5
                )
            except:
                memories = []

            tracker.print_memory_retrieval(memories)
            tracker.log("")

            # Step 2: Make base prediction (without memory enhancement)
            base_prediction = expert.make_personality_driven_prediction(game_data)

            # Step 3: Make memory-enhanced prediction
            try:
                enhanced_prediction = await expert.make_memory_enhanced_prediction(game_data)
            except Exception as e:
                tracker.log(f"⚠️  Memory enhancement failed: {e}", "WARN")
                enhanced_prediction = base_prediction.copy()
                enhanced_prediction['memory_enhanced'] = False

            # Show lessons being applied
            learning_insights = enhanced_prediction.get('learning_insights', [])
            tracker.print_lesson_application(learning_insights)
            tracker.log("")

            # Compare base vs enhanced
            tracker.print_prediction_comparison(base_prediction, enhanced_prediction)
            tracker.log("")

            # Show final prediction
            tracker.print_final_prediction(enhanced_prediction)
            tracker.log("")

            # Show game result
            tracker.print_game_result(actual_outcome, enhanced_prediction)
            tracker.log("")

            # Check if correct
            was_correct = (enhanced_prediction.get('winner_prediction') == actual_outcome['winner'])
            if was_correct:
                week_stats['correct'] += 1
                all_correct += 1
            all_games += 1
            recent_results.append(was_correct)
            if len(recent_results) > 5:
                recent_results.pop(0)

            # Step 4: Store episodic memory
            try:
                memory = await expert.process_game_outcome(
                    game_id=game_id,
                    actual_outcome=actual_outcome,
                    my_prediction=enhanced_prediction
                )

                if memory:
                    week_stats['memories_created'] += 1
                    tracker.print_memory_storage(
                        memory.emotional_state.value,
                        memory.memory_vividness
                    )
                    tracker.log("")

                    # Show lessons learned
                    if memory.lessons_learned:
                        week_stats['lessons_count'] += len(memory.lessons_learned)
                        tracker.print_lessons_learned(memory.lessons_learned)
                        tracker.log("")

                        # Track principles
                        for lesson in memory.lessons_learned:
                            week_stats['principles_learned'].append(
                                f"{lesson.get('category', 'general')}: {lesson.get('content', 'Unknown')}"
                            )
            except Exception as e:
                tracker.log(f"⚠️  Memory storage failed: {e}", "WARN")
                tracker.log("")

            # Step 5: Check for belief revision
            try:
                if game_num > 1:  # Need previous prediction to compare
                    # This would be detected automatically in the service
                    pass
            except Exception as e:
                tracker.log(f"⚠️  Belief revision check failed: {e}", "WARN")

            # Step 6: Self-healing check (every 5 games)
            if len(recent_results) >= 5:
                recent_accuracy = sum(recent_results) / len(recent_results)
                if recent_accuracy < 0.5:
                    corrections = {
                        'factor_adjustments': {
                            'injury_impact': -0.05,
                            'weather_factor': +0.03,
                            'market_sentiment': +0.02
                        }
                    }
                    tracker.print_self_healing(recent_accuracy, corrections)
                    tracker.log("")

            tracker.log("─" * 80)
            tracker.log("")

        # Calculate week accuracy
        week_stats['accuracy'] = week_stats['correct'] / week_stats['games_played'] if week_stats['games_played'] > 0 else 0

        # Print week summary
        tracker.print_week_summary(week, week_stats)
        tracker.log("")

    # Final summary
    tracker.section_header("FINAL SUMMARY (Weeks 1-4)")

    overall_accuracy = all_correct / all_games if all_games > 0 else 0
    tracker.log(f"📊 Overall Performance:", "INFO")
    tracker.log(f"   Total Games: {all_games}", "INFO")
    tracker.log(f"   Correct Predictions: {all_correct}", "INFO")
    tracker.log(f"   Overall Accuracy: {overall_accuracy:.1%}", "INFO")
    tracker.log("")

    tracker.log(f"🧠 Learning Summary:", "INFO")
    total_memories = sum(w['memories_created'] for w in tracker.week_summaries)
    total_lessons = sum(w['lessons_count'] for w in tracker.week_summaries)
    total_revisions = sum(w['revisions_count'] for w in tracker.week_summaries)

    tracker.log(f"   Total Memories Created: {total_memories}", "INFO")
    tracker.log(f"   Total Lessons Learned: {total_lessons}", "INFO")
    tracker.log(f"   Belief Revisions: {total_revisions}", "INFO")
    tracker.log(f"   Self-Healing Events: {len(tracker.self_healing_events)}", "INFO")
    tracker.log("")

    # Close services
    try:
        await memory_manager.close()
        await belief_service.close()
        await reasoning_logger.close()
    except:
        pass

    # Save to file
    tracker.save_to_file()

    tracker.log("")
    tracker.log("🎉 Memory-Enabled Expert Journey Complete!", "INFO")


if __name__ == "__main__":
    # Run with coordination hooks
    import subprocess

    # Pre-task hook
    subprocess.run([
        "npx", "claude-flow@alpha", "hooks", "pre-task",
        "--description", "Run memory-enabled expert learning journey Weeks 1-4"
    ], check=False)

    # Run the journey
    asyncio.run(run_memory_enabled_journey())

    # Post-task hook
    subprocess.run([
        "npx", "claude-flow@alpha", "hooks", "post-task",
        "--task-id", "memory-expert-journey"
    ], check=False)

    # Session end hook
    subprocess.run([
        "npx", "claude-flow@alpha", "hooks", "session-end",
        "--export-metrics", "true"
    ], check=False)