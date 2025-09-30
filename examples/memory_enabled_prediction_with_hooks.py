#!/usr/bin/env python3
"""
Memory-Enabled Prediction with Coordination Hooks

This example demonstrates the complete integration of memory retrieval
into the prediction process with proper coordination hooks as per CLAUDE.md.

Features:
- Pre-task coordination
- Session management
- Memory-enhanced predictions
- Post-operation notifications
- Proper cleanup
"""

import sys
import os
import subprocess
import json
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ml.personality_driven_experts import ConservativeAnalyzer, UniversalGameData
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager


def run_hook(hook_name: str, **kwargs) -> bool:
    """Run a coordination hook"""
    try:
        cmd = ["npx", "claude-flow@alpha", "hooks", hook_name]

        # Add arguments
        for key, value in kwargs.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print(f"✅ Hook {hook_name}: Success")
            return True
        else:
            print(f"⚠️ Hook {hook_name}: Failed (continuing anyway)")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ Hook {hook_name}: Timeout (continuing anyway)")
        return False
    except FileNotFoundError:
        print(f"⚠️ Hook {hook_name}: claude-flow not found (skipping hooks)")
        return False
    except Exception as e:
        print(f"⚠️ Hook {hook_name}: Error - {e} (continuing anyway)")
        return False


async def memory_enabled_prediction_with_hooks():
    """
    Complete workflow: Memory-enhanced prediction with coordination hooks
    """

    print("=" * 80)
    print("🧠 MEMORY-ENABLED PREDICTION WITH COORDINATION HOOKS")
    print("=" * 80)

    # Generate session ID
    session_id = f"swarm-conservative-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    game_id = "KC_BAL_2024-01-15"

    # =========================================================================
    # STEP 1: PRE-TASK COORDINATION HOOK
    # =========================================================================
    print("\n📋 Step 1: Pre-Task Coordination")
    print("-" * 80)

    run_hook(
        "pre-task",
        description=f"Memory-enhanced prediction for {game_id}",
        task_id=f"predict-{game_id}"
    )

    # =========================================================================
    # STEP 2: SESSION RESTORE HOOK
    # =========================================================================
    print("\n🔄 Step 2: Session Restore")
    print("-" * 80)

    run_hook(
        "session-restore",
        session_id=session_id
    )

    # =========================================================================
    # STEP 3: INITIALIZE MEMORY SERVICE
    # =========================================================================
    print("\n🗄️ Step 3: Initialize Memory Service")
    print("-" * 80)

    # For this example, we'll use a mock since real Supabase needs credentials
    # In production, use: supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("⚠️ Using mock memory service for demonstration")
    print("   In production, initialize with real Supabase client")

    # Create mock memory service
    class MockMemoryService:
        async def retrieve_memories(self, expert_id, game_context, limit=5):
            """Mock memory retrieval"""
            return [
                {
                    'memory_id': 'mem_001',
                    'expert_id': expert_id,
                    'prediction_data': json.dumps({
                        'winner': 'home',
                        'confidence': 0.75
                    }),
                    'actual_outcome': json.dumps({
                        'winner': 'home',
                        'home_score': 27,
                        'away_score': 20
                    })
                },
                {
                    'memory_id': 'mem_002',
                    'expert_id': expert_id,
                    'prediction_data': json.dumps({
                        'winner': 'home',
                        'confidence': 0.70
                    }),
                    'actual_outcome': json.dumps({
                        'winner': 'home',
                        'home_score': 24,
                        'away_score': 21
                    })
                }
            ]

    memory_service = MockMemoryService()
    print("✅ Memory service initialized")

    # =========================================================================
    # STEP 4: CREATE MEMORY-ENABLED ANALYZER
    # =========================================================================
    print("\n🤖 Step 4: Create Memory-Enabled Analyzer")
    print("-" * 80)

    analyzer = ConservativeAnalyzer(memory_service=memory_service)
    print(f"✅ Analyzer created: {analyzer.name}")
    print(f"   Expert ID: {analyzer.expert_id}")
    print(f"   Memory Service: {'Enabled' if analyzer.memory_service else 'Disabled'}")

    # =========================================================================
    # STEP 5: CREATE GAME DATA
    # =========================================================================
    print("\n🏈 Step 5: Prepare Game Data")
    print("-" * 80)

    game_data = UniversalGameData(
        home_team="KC",
        away_team="BAL",
        game_time="2024-01-15 21:00:00",
        location="Kansas City",
        weather={
            'temperature': 28,
            'wind_speed': 22,
            'conditions': 'Snow',
            'humidity': 85
        },
        injuries={
            'home': [
                {'position': 'WR', 'severity': 'questionable', 'probability_play': 0.6}
            ],
            'away': [
                {'position': 'RB', 'severity': 'doubtful', 'probability_play': 0.3}
            ]
        },
        line_movement={
            'opening_line': -2.5,
            'current_line': -1.0,
            'public_percentage': 78
        },
        team_stats={
            'home': {
                'offensive_yards_per_game': 415,
                'defensive_yards_allowed': 298
            },
            'away': {
                'offensive_yards_per_game': 389,
                'defensive_yards_allowed': 312
            }
        }
    )

    print(f"📊 Game: {game_data.away_team} @ {game_data.home_team}")
    print(f"🌨️ Weather: {game_data.weather['temperature']}°F, "
          f"{game_data.weather['wind_speed']}mph wind, "
          f"{game_data.weather['conditions']}")
    print(f"📈 Line: {game_data.line_movement['opening_line']} → "
          f"{game_data.line_movement['current_line']}")
    print(f"👥 Public: {game_data.line_movement['public_percentage']}%")

    # =========================================================================
    # STEP 6: MAKE MEMORY-ENHANCED PREDICTION
    # =========================================================================
    print("\n🧠 Step 6: Make Memory-Enhanced Prediction")
    print("-" * 80)

    print("Retrieving relevant memories...")
    print("Processing through personality lens...")
    print("Applying learned principles...")

    prediction = analyzer.make_personality_driven_prediction(game_data)

    print(f"\n✅ Prediction Complete!")

    # =========================================================================
    # STEP 7: DISPLAY PREDICTION RESULTS
    # =========================================================================
    print("\n📊 Step 7: Prediction Results")
    print("-" * 80)

    print(f"\n🎯 Winner Prediction:")
    print(f"   Pick: {prediction.get('winner_prediction', 'N/A')}")
    print(f"   Confidence: {prediction.get('winner_confidence', 0):.1%}")

    print(f"\n📈 Spread Prediction:")
    print(f"   Pick: {prediction.get('spread_prediction', 0):+.1f}")
    print(f"   Confidence: {prediction.get('winner_confidence', 0) * 0.9:.1%}")

    print(f"\n🔢 Total Prediction:")
    print(f"   Total: {prediction.get('total_prediction', 0):.1f}")

    print(f"\n🧠 Memory Enhancement:")
    print(f"   Memory Enhanced: {prediction.get('memory_enhanced', False)}")
    print(f"   Memories Consulted: {prediction.get('memories_consulted', 0)}")

    if prediction.get('memory_enhanced'):
        print(f"   Success Rate: {prediction.get('memory_success_rate', 0):.1%}")
        print(f"   Confidence Adjustment: {prediction.get('confidence_adjustment', 0):+.3f}")

        if prediction.get('learned_principles'):
            print(f"\n   📚 Learned Principles:")
            for principle in prediction['learned_principles']:
                print(f"      • {principle}")

    print(f"\n💭 Reasoning:")
    print(f"   {prediction.get('reasoning', 'N/A')}")

    # =========================================================================
    # STEP 8: POST-EDIT HOOK (Store Prediction)
    # =========================================================================
    print("\n💾 Step 8: Store Prediction")
    print("-" * 80)

    # Save prediction to file
    prediction_file = f"predictions/{game_id}_prediction.json"
    os.makedirs("predictions", exist_ok=True)

    with open(prediction_file, 'w') as f:
        json.dump({
            'game_id': game_id,
            'expert': analyzer.name,
            'expert_id': analyzer.expert_id,
            'timestamp': datetime.now().isoformat(),
            'prediction': prediction
        }, f, indent=2)

    print(f"✅ Prediction saved to: {prediction_file}")

    # Post-edit hook
    run_hook(
        "post-edit",
        file=prediction_file,
        memory_key=f"swarm/{analyzer.expert_id}/prediction_{datetime.now().isoformat()}"
    )

    # =========================================================================
    # STEP 9: NOTIFICATION HOOK
    # =========================================================================
    print("\n📢 Step 9: Notify Completion")
    print("-" * 80)

    notification_message = (
        f"Prediction complete: {prediction['winner_prediction']} "
        f"({prediction['winner_confidence']:.1%}) - "
        f"Memory enhanced with {prediction.get('memories_consulted', 0)} experiences"
    )

    run_hook(
        "notify",
        message=notification_message
    )

    # =========================================================================
    # STEP 10: POST-TASK HOOK
    # =========================================================================
    print("\n✅ Step 10: Post-Task Cleanup")
    print("-" * 80)

    run_hook(
        "post-task",
        task_id=f"predict-{game_id}"
    )

    # =========================================================================
    # STEP 11: SESSION END HOOK
    # =========================================================================
    print("\n🏁 Step 11: Session End")
    print("-" * 80)

    run_hook(
        "session-end",
        session_id=session_id,
        export_metrics="true"
    )

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("🎉 MEMORY-ENHANCED PREDICTION WORKFLOW COMPLETE")
    print("=" * 80)

    print(f"\n📋 Workflow Summary:")
    print(f"   ✅ Pre-task coordination executed")
    print(f"   ✅ Session management configured")
    print(f"   ✅ Memory service initialized")
    print(f"   ✅ {prediction.get('memories_consulted', 0)} relevant memories retrieved")
    print(f"   ✅ Prediction enhanced with learned principles")
    print(f"   ✅ Results stored with proper coordination")
    print(f"   ✅ Post-task cleanup completed")

    print(f"\n🧠 Memory Enhancement Impact:")
    if prediction.get('memory_enhanced'):
        print(f"   • Confidence adjusted by {prediction.get('confidence_adjustment', 0):+.1%}")
        print(f"   • Based on {prediction.get('memory_success_rate', 0):.0%} historical success rate")
        print(f"   • Applied {len(prediction.get('learned_principles', []))} learned principles")
    else:
        print(f"   • No memory enhancement applied (no relevant memories found)")

    print(f"\n🎯 Final Prediction:")
    print(f"   {game_data.away_team} @ {game_data.home_team}")
    print(f"   Winner: {prediction['winner_prediction']}")
    print(f"   Confidence: {prediction['winner_confidence']:.1%}")
    print(f"   Spread: {prediction.get('spread_prediction', 0):+.1f}")


def main():
    """Run the complete example"""
    try:
        asyncio.run(memory_enabled_prediction_with_hooks())
        print("\n✅ Example completed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ Example interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())