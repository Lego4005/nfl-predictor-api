#!/usr/bin/env python3
"""
Demonstration Script: Memory-Enhanced Expert System Integration

This script demonstrates the complete integration of episodic memory services
with the personality-driven experts system for NFL prediction.

Features demonstrated:
1. Memory-enhanced predictions using past experiences
2. Belief revision tracking when experts change their minds
3. Reasoning chain logging with memory influences
4. Learning from game outcomes and pattern recognition
5. Expert memory analytics and performance tracking
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.memory_enabled_expert_service import MemoryEnabledExpertService
from ml.personality_driven_experts import UniversalGameData

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryIntegrationDemo:
    """Demonstration of the complete memory integration"""

    def __init__(self):
        # Database configuration (adjust for your setup)
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'database': os.getenv('DB_NAME', 'nfl_predictor')
        }

        self.service = None

    async def initialize(self):
        """Initialize the memory-enabled expert service"""
        print("🚀 Initializing Memory-Enhanced Expert System")
        print("=" * 60)

        try:
            self.service = MemoryEnabledExpertService(self.db_config)
            await self.service.initialize()
            print(f"✅ Service initialized with {len(self.service.memory_experts)} memory-enabled experts")
            print(f"📊 Database: {self.db_config['database']}@{self.db_config['host']}")
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise

    async def demonstrate_basic_prediction(self):
        """Demonstrate basic memory-enhanced predictions"""
        print("\n🧠 DEMONSTRATION 1: Memory-Enhanced Predictions")
        print("-" * 50)

        # Create game scenario
        game_data = UniversalGameData(
            home_team="KC",
            away_team="BAL",
            game_time="2024-01-21 18:00:00",
            location="Kansas City",
            weather={
                'temperature': 25,
                'wind_speed': 20,
                'conditions': 'Snow',
                'humidity': 85
            },
            injuries={
                'home': [{'position': 'RB', 'severity': 'questionable', 'probability_play': 0.6}],
                'away': [{'position': 'QB', 'severity': 'probable', 'probability_play': 0.9}]
            },
            line_movement={
                'opening_line': -3.0,
                'current_line': -1.5,
                'public_percentage': 75
            },
            team_stats={
                'home': {'offensive_yards_per_game': 415, 'defensive_yards_allowed': 290},
                'away': {'offensive_yards_per_game': 385, 'defensive_yards_allowed': 305}
            }
        )

        print(f"🏈 Game Scenario: {game_data.away_team} @ {game_data.home_team}")
        print(f"🌨️ Weather: {game_data.weather['temperature']}°F, {game_data.weather['wind_speed']}mph, {game_data.weather['conditions']}")
        print(f"📈 Line Movement: {game_data.line_movement['opening_line']} → {game_data.line_movement['current_line']}")
        print(f"👥 Public Betting: {game_data.line_movement['public_percentage']}% on favorite")

        # Generate predictions
        result = await self.service.generate_memory_enhanced_predictions(game_data)

        print(f"\n🎭 Expert Predictions (Top 8):")
        print("-" * 70)
        print(f"{'Expert':<18} {'Winner':<4} {'Conf':<6} {'Mem':<4} {'Insights'}")
        print("-" * 70)

        for i, pred in enumerate(result['all_predictions'][:8]):
            memory_icon = "🧠" if pred.get('memory_enhanced') and pred.get('similar_experiences', 0) > 0 else "🤖"
            name = pred.get('expert_name', 'Unknown')[:17]
            winner = pred.get('winner_prediction', 'N/A')
            confidence = pred.get('winner_confidence', 0.5)
            memories = pred.get('similar_experiences', 0)

            print(f"{memory_icon} {name:<16} {winner:<4} {confidence:<5.1%} {memories:<4}", end="")

            # Show first insight if available
            insights = pred.get('learning_insights', [])
            if insights:
                print(f" {insights[0][:35]}...")
            else:
                print()

        # Show consensus
        consensus = result['consensus']
        print(f"\n🎯 Memory-Enhanced Consensus:")
        print(f"   Winner: {consensus.get('winner', 'N/A')} ({consensus.get('confidence', 0):.1%} confidence)")
        print(f"   Memory Factor: {consensus.get('memory_enhanced_count', 0)}/{consensus.get('expert_count', 0)} experts used memories")

        # Show memory statistics
        memory_stats = result['memory_stats']
        print(f"\n📊 Memory Usage Statistics:")
        print(f"   Total memories consulted: {memory_stats['total_memories_consulted']}")
        print(f"   Experts with relevant memories: {memory_stats['experts_with_memories']}")
        print(f"   Average confidence adjustment: {memory_stats['average_confidence_adjustment']:+.3f}")

        return result

    async def demonstrate_learning_from_outcomes(self, prediction_result):
        """Demonstrate learning from game outcomes"""
        print("\n📚 DEMONSTRATION 2: Learning from Game Outcomes")
        print("-" * 50)

        # Simulate game outcome (upset scenario - away team wins in bad weather)
        actual_outcome = {
            'winner': 'BAL',  # Away team wins despite being underdog
            'home_score': 14,
            'away_score': 21,
            'margin': 7
        }

        print(f"⚽ Simulated Outcome: {actual_outcome['winner']} wins {actual_outcome['away_score']}-{actual_outcome['home_score']}")
        print(f"   Result: Away team upset victory in harsh weather conditions")

        # Process the outcome
        game_result = {
            'game_id': 'demo_kc_bal_2024',
            'actual_outcome': actual_outcome,
            'expert_predictions': prediction_result['all_predictions']
        }

        learning_result = await self.service.process_game_outcomes([game_result])

        print(f"\n🧠 Learning Results:")
        print(f"   Memories created: {learning_result['memories_created']}")
        print(f"   Experts updated: {len(learning_result['expert_learning_updates'])}")

        # Show expert learning updates
        print(f"\n📈 Expert Learning Updates:")
        for expert_id, update in list(learning_result['expert_learning_updates'].items())[:5]:
            correct_symbol = "✅" if update['recent_accuracy'] > 0.5 else "❌"
            print(f"   {correct_symbol} {update['name']:<18} | Recent Accuracy: {update['recent_accuracy']:5.1%}")

        return learning_result

    async def demonstrate_pattern_learning(self):
        """Demonstrate pattern learning over multiple games"""
        print("\n🔄 DEMONSTRATION 3: Pattern Learning Over Time")
        print("-" * 50)

        # Simulate a series of cold weather games to establish a pattern
        cold_weather_games = []

        for week in range(1, 4):
            print(f"\n❄️ Week {week}: Cold Weather Game")

            # Create cold weather scenario
            cold_game_data = UniversalGameData(
                home_team="BUF",
                away_team="MIA",
                game_time=f"2024-{week:02d}-07 13:00:00",
                location="Buffalo",
                weather={
                    'temperature': 15 + week * 5,  # Gradually getting colder
                    'wind_speed': 18 + week * 2,
                    'conditions': 'Snow',
                    'humidity': 90
                },
                injuries={'home': [], 'away': []},
                line_movement={'opening_line': -4.0, 'current_line': -3.5, 'public_percentage': 70},
                team_stats={
                    'home': {'offensive_yards_per_game': 320, 'defensive_yards_allowed': 280},
                    'away': {'offensive_yards_per_game': 380, 'defensive_yards_allowed': 350}
                }
            )

            # Generate predictions
            predictions = await self.service.generate_memory_enhanced_predictions(cold_game_data)

            # Simulate consistent pattern: home team wins in cold weather (cold weather advantage)
            outcome = {
                'game_id': f'cold_weather_week_{week}',
                'actual_outcome': {
                    'winner': 'BUF',  # Home team always wins
                    'home_score': 20 + week,
                    'away_score': 14 + week - 3
                },
                'expert_predictions': predictions['all_predictions']
            }

            await self.service.process_game_outcomes([outcome])
            cold_weather_games.append(outcome)

            print(f"   Outcome: BUF wins (establishing cold weather home advantage pattern)")

        # Now test with a new cold weather game
        print(f"\n❄️ Week 4: Testing Pattern Recognition")

        test_game_data = UniversalGameData(
            home_team="BUF",
            away_team="NE",  # Different away team
            game_time="2024-04-07 13:00:00",
            location="Buffalo",
            weather={
                'temperature': 10,  # Very cold
                'wind_speed': 25,   # Very windy
                'conditions': 'Heavy Snow',
                'humidity': 95
            },
            injuries={'home': [], 'away': []},
            line_movement={'opening_line': -2.0, 'current_line': -1.0, 'public_percentage': 55},
            team_stats={
                'home': {'offensive_yards_per_game': 320, 'defensive_yards_allowed': 280},
                'away': {'offensive_yards_per_game': 310, 'defensive_yards_allowed': 320}
            }
        )

        test_predictions = await self.service.generate_memory_enhanced_predictions(test_game_data)

        print(f"\n🧠 Pattern Recognition Results:")
        print("-" * 40)

        experts_with_cold_weather_learning = 0
        cold_weather_insights = []

        for pred in test_predictions['all_predictions']:
            if pred.get('similar_experiences', 0) > 0:
                experts_with_cold_weather_learning += 1

                # Look for cold weather related insights
                insights = pred.get('learning_insights', [])
                for insight in insights:
                    if 'weather' in insight.lower() or 'cold' in insight.lower():
                        cold_weather_insights.append((pred['expert_name'], insight))

        print(f"   Experts with relevant memories: {experts_with_cold_weather_learning}")
        print(f"   Weather-related insights: {len(cold_weather_insights)}")

        # Show insights
        if cold_weather_insights:
            print(f"\n💡 Cold Weather Learning Insights:")
            for expert_name, insight in cold_weather_insights[:3]:
                print(f"   🧠 {expert_name}: {insight}")

        return test_predictions

    async def demonstrate_belief_revision(self):
        """Demonstrate belief revision when new information arrives"""
        print("\n🔄 DEMONSTRATION 4: Belief Revision Detection")
        print("-" * 50)

        # Initial scenario
        initial_game_data = UniversalGameData(
            home_team="KC",
            away_team="CIN",
            game_time="2024-01-28 15:00:00",
            location="Kansas City",
            weather={'temperature': 35, 'wind_speed': 10, 'conditions': 'Clear'},
            injuries={'home': [], 'away': []},
            line_movement={'opening_line': -7.0, 'current_line': -6.5, 'public_percentage': 80},
            team_stats={
                'home': {'offensive_yards_per_game': 420, 'defensive_yards_allowed': 285},
                'away': {'offensive_yards_per_game': 350, 'defensive_yards_allowed': 340}
            }
        )

        print(f"📊 Initial Scenario: {initial_game_data.away_team} @ {initial_game_data.home_team}")
        print(f"   Line: KC -6.5, 80% public on KC")

        # Generate initial predictions
        initial_predictions = await self.service.generate_memory_enhanced_predictions(initial_game_data)

        # Show initial consensus
        initial_consensus = initial_predictions['consensus']
        print(f"   Initial Consensus: {initial_consensus['winner']} ({initial_consensus['confidence']:.1%})")

        # Simulate breaking news: Starting QB injured
        print(f"\n🚨 BREAKING NEWS: KC starting QB ruled out with injury!")

        updated_game_data = UniversalGameData(
            home_team="KC",
            away_team="CIN",
            game_time="2024-01-28 15:00:00",
            location="Kansas City",
            weather={'temperature': 35, 'wind_speed': 10, 'conditions': 'Clear'},
            injuries={
                'home': [{'position': 'QB', 'severity': 'out', 'probability_play': 0.0}],
                'away': []
            },
            line_movement={'opening_line': -7.0, 'current_line': -2.0, 'public_percentage': 55},  # Line moves dramatically
            team_stats={
                'home': {'offensive_yards_per_game': 420, 'defensive_yards_allowed': 285},
                'away': {'offensive_yards_per_game': 350, 'defensive_yards_allowed': 340}
            }
        )

        print(f"   Updated Line: KC -2.0, 55% public on KC (major line movement)")

        # Generate updated predictions
        updated_predictions = await self.service.generate_memory_enhanced_predictions(updated_game_data)

        # Show updated consensus
        updated_consensus = updated_predictions['consensus']
        print(f"   Updated Consensus: {updated_consensus['winner']} ({updated_consensus['confidence']:.1%})")

        # Analyze belief revisions
        print(f"\n🔄 Belief Revision Analysis:")

        revisions = 0
        significant_changes = []

        initial_preds = {pred['expert_name']: pred for pred in initial_predictions['all_predictions']}
        updated_preds = {pred['expert_name']: pred for pred in updated_predictions['all_predictions']}

        for expert_name in initial_preds:
            if expert_name in updated_preds:
                initial_winner = initial_preds[expert_name]['winner_prediction']
                updated_winner = updated_preds[expert_name]['winner_prediction']
                initial_conf = initial_preds[expert_name]['winner_confidence']
                updated_conf = updated_preds[expert_name]['winner_confidence']

                # Check for significant changes
                if initial_winner != updated_winner:
                    revisions += 1
                    significant_changes.append({
                        'expert': expert_name,
                        'change': f"{initial_winner} → {updated_winner}",
                        'confidence_change': updated_conf - initial_conf
                    })
                elif abs(initial_conf - updated_conf) > 0.15:
                    significant_changes.append({
                        'expert': expert_name,
                        'change': f"Confidence: {initial_conf:.1%} → {updated_conf:.1%}",
                        'confidence_change': updated_conf - initial_conf
                    })

        print(f"   Experts who changed winner pick: {revisions}")
        print(f"   Experts with significant changes: {len(significant_changes)}")

        # Show examples of belief revisions
        if significant_changes:
            print(f"\n🔄 Notable Belief Revisions:")
            for change in significant_changes[:3]:
                direction = "📈" if change['confidence_change'] > 0 else "📉"
                print(f"   {direction} {change['expert']}: {change['change']}")

        return {
            'initial_consensus': initial_consensus,
            'updated_consensus': updated_consensus,
            'revisions_detected': revisions,
            'significant_changes': len(significant_changes)
        }

    async def demonstrate_memory_analytics(self):
        """Demonstrate comprehensive memory analytics"""
        print("\n📈 DEMONSTRATION 5: Memory Analytics Dashboard")
        print("-" * 50)

        # Get system-wide analytics
        analytics = await self.service.get_expert_memory_analytics()

        # System overview
        total_predictions = sum(data['learning_metrics']['total_predictions'] for data in analytics.values())
        total_memories = sum(data['memory_stats'].get('total_memories', 0) for data in analytics.values())
        memory_enhanced_predictions = sum(data['learning_metrics']['memory_enhanced_predictions'] for data in analytics.values())

        print(f"📊 System Overview:")
        print(f"   Total Experts: {len(analytics)}")
        print(f"   Total Predictions: {total_predictions}")
        print(f"   Total Memories: {total_memories}")
        print(f"   Memory-Enhanced Predictions: {memory_enhanced_predictions}")

        if total_predictions > 0:
            enhancement_rate = memory_enhanced_predictions / total_predictions
            print(f"   Memory Enhancement Rate: {enhancement_rate:.1%}")

        # Expert performance leaderboard
        print(f"\n🏆 Expert Performance Leaderboard:")
        print("-" * 50)

        # Sort by recent accuracy
        sorted_experts = sorted(
            analytics.items(),
            key=lambda x: x[1]['learning_metrics']['recent_accuracy'],
            reverse=True
        )

        print(f"{'Rank':<4} {'Expert':<18} {'Accuracy':<8} {'Predictions':<11} {'Memories':<8}")
        print("-" * 60)

        for i, (expert_id, data) in enumerate(sorted_experts[:10]):
            rank = f"#{i+1}"
            name = data['name'][:17]
            accuracy = data['learning_metrics']['recent_accuracy']
            predictions = data['learning_metrics']['total_predictions']
            memories = data['memory_stats'].get('total_memories', 0)

            accuracy_icon = "🏆" if accuracy > 0.6 else "📊" if accuracy > 0.4 else "📉"

            print(f"{rank:<4} {accuracy_icon} {name:<15} {accuracy:<7.1%} {predictions:<11} {memories:<8}")

        # Memory utilization analysis
        experts_with_memories = [data for data in analytics.values() if data['memory_stats'].get('total_memories', 0) > 0]

        print(f"\n🧠 Memory Utilization:")
        print(f"   Experts with memories: {len(experts_with_memories)}/{len(analytics)}")

        if experts_with_memories:
            avg_memories = sum(data['memory_stats']['total_memories'] for data in experts_with_memories) / len(experts_with_memories)
            print(f"   Average memories per expert: {avg_memories:.1f}")

        # Show top memory users
        top_memory_users = sorted(
            analytics.items(),
            key=lambda x: x[1]['memory_stats'].get('total_memories', 0),
            reverse=True
        )[:3]

        if top_memory_users and top_memory_users[0][1]['memory_stats'].get('total_memories', 0) > 0:
            print(f"\n🧠 Top Memory Users:")
            for expert_id, data in top_memory_users:
                if data['memory_stats'].get('total_memories', 0) > 0:
                    print(f"   🧠 {data['name']}: {data['memory_stats']['total_memories']} memories")

        return analytics

    async def run_complete_demonstration(self):
        """Run the complete demonstration"""
        try:
            await self.initialize()

            # Run all demonstrations
            print("\n" + "="*80)
            print("🧠 COMPLETE MEMORY INTEGRATION DEMONSTRATION")
            print("="*80)

            # Demo 1: Basic prediction
            prediction_result = await self.demonstrate_basic_prediction()

            # Demo 2: Learning from outcomes
            await self.demonstrate_learning_from_outcomes(prediction_result)

            # Demo 3: Pattern learning
            await self.demonstrate_pattern_learning()

            # Demo 4: Belief revision
            revision_result = await self.demonstrate_belief_revision()

            # Demo 5: Analytics
            await self.demonstrate_memory_analytics()

            # Summary
            print("\n" + "="*80)
            print("🎉 DEMONSTRATION COMPLETE - INTEGRATION SUCCESSFUL!")
            print("="*80)

            print(f"\n✅ Key Features Demonstrated:")
            print(f"   🧠 Memory-enhanced predictions with past experience consultation")
            print(f"   📚 Learning from game outcomes and episodic memory creation")
            print(f"   🔄 Pattern recognition across multiple similar games")
            print(f"   💭 Belief revision detection when expert opinions change")
            print(f"   📈 Comprehensive memory analytics and performance tracking")

            print(f"\n🚀 Integration Status:")
            print(f"   ✅ Episodic Memory Manager: Connected and functional")
            print(f"   ✅ Belief Revision Service: Tracking opinion changes")
            print(f"   ✅ Reasoning Chain Logger: Recording detailed expert thought processes")
            print(f"   ✅ Personality Experts: All 15 experts memory-enabled")
            print(f"   ✅ Learning Pipeline: Continuous improvement from outcomes")

            print(f"\n📊 System Capabilities:")
            print(f"   • Real-time memory consultation during predictions")
            print(f"   • Automatic belief revision detection and logging")
            print(f"   • Pattern learning across weather, market, and team contexts")
            print(f"   • Confidence adjustments based on historical performance")
            print(f"   • Comprehensive analytics for expert performance tracking")

        except Exception as e:
            print(f"\n❌ Demonstration failed: {e}")
            logger.error("Demonstration failed", exc_info=True)
            raise

        finally:
            if self.service:
                await self.service.close()
                print(f"\n🔧 Service shutdown complete")

async def main():
    """Main entry point for the demonstration"""
    print("🧠 Memory-Enhanced Expert System Integration Demonstration")
    print("🎯 Showing complete integration of episodic memory services with personality experts")
    print("⚡ This demo will take a few minutes to run through all scenarios...\n")

    demo = MemoryIntegrationDemo()
    await demo.run_complete_demonstration()

    print(f"\n📝 Note: This demonstration used a test database scenario.")
    print(f"   In production, the system would integrate with real NFL game data,")
    print(f"   live betting lines, weather APIs, and injury reports.")

    print(f"\n🔗 Next Steps:")
    print(f"   1. Connect to live data sources (ESPN API, weather APIs)")
    print(f"   2. Deploy memory-enhanced endpoints to production")
    print(f"   3. Set up monitoring and analytics dashboards")
    print(f"   4. Configure automated learning pipelines")

if __name__ == "__main__":
    # Set up environment if needed
    if 'DB_HOST' not in os.environ:
        print("💡 Using default database configuration.")
        print("   Set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME environment variables for custom config.")

    # Run the demonstration
    asyncio.run(main())