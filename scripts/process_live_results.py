#!/usr/bin/env python3
"""
LIVE RESULTS PROCESSOR - Learn from actual game outcome!
Processes real game results to test episodic memory and belief revision.
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.reasoning_chain_logger import ReasoningChainLogger
from src.ml.episodic_memory_manager import EpisodicMemoryManager
from src.ml.belief_revision_service import BeliefRevisionService

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_live_results():
    """Process actual game outcome and test learning systems"""

    print("\n" + "🎯" * 30)
    print("🏁 PROCESSING ACTUAL GAME RESULTS!")
    print("🎯" * 30 + "\n")

    # Initialize services with database
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')

    # Temporarily disable database for episodic memory due to schema mismatch
    # if supabase_url and supabase_key:
    #     supabase_client = create_client(supabase_url, supabase_key)
    #     print("🔧 Connected to Supabase database")
    # else:
    supabase_client = None
    print("🔧 Using local storage for episodic memory testing")

    reasoning_logger = ReasoningChainLogger(supabase_client)
    memory_manager = EpisodicMemoryManager(supabase_client)
    belief_service = BeliefRevisionService(supabase_client)

    # Load the predictions we made
    try:
        with open("live_reasoning_predictions.json", "r") as f:
            test_data = json.load(f)
        print("📁 Loaded predictions from live_reasoning_predictions.json")
    except FileNotFoundError:
        print("❌ No live_reasoning_predictions.json found. Run live_reasoning_test.py first!")
        return

    game = test_data["game"]
    predictions = test_data["predictions"]

    print(f"🏈 Original Game: {game['current_score']} with {game['time_left']} left")
    print(f"📊 Found {len(predictions)} expert predictions to analyze")
    print("=" * 70)

    # SIMULATE ACTUAL GAME OUTCOME (In real usage, this would be fetched from ESPN API)
    print("⚠️  SIMULATING ACTUAL GAME OUTCOME:")
    print("    (In production, this would fetch from ESPN/sports API)")

    # Let's say LAC actually won 27-24 (they had the momentum and were leading)
    actual_outcome = {
        "final_score": "LAC 27 - LV 24",
        "winner": "LAC",
        "home_score": 24,
        "away_score": 27,
        "final_margin": 3,
        "spread_result": "LAC",  # LAC was +1, won by 3, so they covered
        "total_result": "over",  # 51 points vs 43.5 line
        "final_total": 51,
        "game_narrative": "LAC controlled final drive, scored TD with 1:12 left. LV failed to answer.",
        "key_moments": [
            "LAC 8-play TD drive (3:00-1:12)",
            "LV incomplete pass on 4th down with 0:23 left",
            "LAC kneeled to end game"
        ],
        "surprise_factor": 0.2  # Not too surprising given LAC was leading
    }

    print(f"🏁 ACTUAL RESULT: {actual_outcome['final_score']}")
    print(f"📈 Total: {actual_outcome['final_total']} ({actual_outcome['total_result']})")
    print(f"📊 Spread: {actual_outcome['spread_result']} covered")
    print(f"🎬 Key: {actual_outcome['game_narrative']}")
    print()

    # Process each expert's prediction accuracy
    expert_results = []
    correct_winners = 0
    correct_spreads = 0
    correct_totals = 0

    for prediction_data in predictions:
        expert_id = prediction_data["expert"]
        prediction = prediction_data["prediction"]
        confidence = prediction_data["confidence"]

        # Calculate accuracy for each prediction type
        accuracy = {
            "winner": 1.0 if prediction.get("winner") == actual_outcome["winner"] else 0.0,
            "spread": 1.0 if prediction.get("spread_pick") == actual_outcome["spread_result"] else 0.0,
            "total": 1.0 if prediction.get("total_pick") == actual_outcome["total_result"] else 0.0
        }

        # Calculate overall accuracy score
        overall_accuracy = (accuracy["winner"] + accuracy["spread"] + accuracy["total"]) / 3

        expert_results.append({
            "expert_id": expert_id,
            "prediction": prediction,
            "confidence": confidence,
            "accuracy": accuracy,
            "overall_accuracy": overall_accuracy
        })

        # Track aggregates
        if accuracy["winner"] == 1.0:
            correct_winners += 1
        if accuracy["spread"] == 1.0:
            correct_spreads += 1
        if accuracy["total"] == 1.0:
            correct_totals += 1

        # Display expert results
        status = "✅" if overall_accuracy > 0.6 else "⚠️" if overall_accuracy > 0.3 else "❌"
        print(f"{status} {expert_id.replace('_', ' ').title()}")
        print(f"   Predicted: {prediction.get('winner', 'N/A')} | Actual: {actual_outcome['winner']} {'✓' if accuracy['winner'] else '✗'}")
        print(f"   Spread: {prediction.get('spread_pick', 'N/A')} {'✓' if accuracy['spread'] else '✗'} | Total: {prediction.get('total_pick', 'N/A')} {'✓' if accuracy['total'] else '✗'}")
        print(f"   Overall Accuracy: {overall_accuracy:.0%} | Confidence: {confidence['overall']:.0%}")
        print()

    print("📊 PANEL PERFORMANCE SUMMARY:")
    print(f"   Winners: {correct_winners}/15 ({correct_winners/15:.0%})")
    print(f"   Spreads: {correct_spreads}/15 ({correct_spreads/15:.0%})")
    print(f"   Totals: {correct_totals}/15 ({correct_totals/15:.0%})")
    print()

    # CREATE EPISODIC MEMORIES
    print("🧠 CREATING EPISODIC MEMORIES...")

    for i, result in enumerate(expert_results):
        expert_id = result["expert_id"]
        prediction = result["prediction"]
        accuracy = result["accuracy"]
        confidence = result["confidence"]
        original_prediction_data = predictions[i]  # Get original data for personality

        # Generate lesson learned from this game
        if result["overall_accuracy"] > 0.7:
            lesson = f"Successfully predicted LAC victory. Key factors: {prediction.get('confidence_reasoning', 'Strong analysis')}"
        elif result["overall_accuracy"] > 0.5:
            lesson = f"Partially correct on LAC win but missed {['spread' if accuracy['spread'] == 0 else 'total'][0]} prediction"
        else:
            lesson = f"Failed prediction - expected {prediction.get('winner', 'N/A')} but LAC won. Need to revise approach."

        # Store episodic memory with correct signature
        memory_id = await memory_manager.store_episodic_memory(
            expert_id=expert_id,
            game_id=game["game_id"],
            prediction=prediction,
            outcome=actual_outcome,
            lesson=lesson,
            expert_personality="analytical"  # Default personality for now
        )

        print(f"💾 Created episodic memory for {expert_id}: {memory_id}")

    # TRIGGER BELIEF REVISION
    print("\n🔄 TRIGGERING BELIEF REVISION...")

    for result in expert_results:
        expert_id = result["expert_id"]
        accuracy = result["accuracy"]

        # Trigger belief revision if performance was poor
        if result["overall_accuracy"] < 0.5:
            # Create game result and prediction history for belief revision
            game_results = [{
                "game_id": game["game_id"],
                "prediction": result["prediction"],
                "actual_outcome": actual_outcome,
                "accuracy": accuracy
            }]

            prediction_history = [{
                "game_id": game["game_id"],
                "prediction": result["prediction"],
                "confidence": result["confidence"]
            }]

            revisions = await belief_service.trigger_belief_revision(
                expert_id=expert_id,
                game_results=game_results,
                prediction_history=prediction_history
            )

            print(f"🔄 Triggered belief revision for {expert_id}: {len(revisions)} revisions")
        else:
            print(f"✅ {expert_id} performed well - no revision needed")

    # ANALYZE LEARNING PATTERNS
    print("\n🎓 ANALYZING LEARNING PATTERNS...")

    # Find top and bottom performers
    expert_results.sort(key=lambda x: x["overall_accuracy"], reverse=True)
    top_performer = expert_results[0]
    bottom_performer = expert_results[-1]

    print(f"🏆 TOP PERFORMER: {top_performer['expert_id'].replace('_', ' ').title()}")
    print(f"   Accuracy: {top_performer['overall_accuracy']:.0%}")
    print(f"   Confidence: {top_performer['confidence']['overall']:.0%}")

    print(f"📉 NEEDS IMPROVEMENT: {bottom_performer['expert_id'].replace('_', ' ').title()}")
    print(f"   Accuracy: {bottom_performer['overall_accuracy']:.0%}")
    print(f"   Confidence: {bottom_performer['confidence']['overall']:.0%}")

    # Update test data with results
    test_data["actual_outcome"] = actual_outcome
    test_data["expert_results"] = expert_results
    test_data["status"] = "processed"
    test_data["processed_at"] = datetime.now().isoformat()

    # Save results
    with open("live_reasoning_results.json", "w") as f:
        json.dump(test_data, f, indent=2)

    print(f"\n✅ LEARNING CYCLE COMPLETE!")
    print(f"💾 Results saved to live_reasoning_results.json")
    print("\n🎯 NEXT STEPS:")
    print("   • Experts with poor accuracy will revise beliefs")
    print("   • Episodic memories will inform future predictions")
    print("   • Learning rates will be adjusted based on performance")
    print("   • Top performers' strategies will be analyzed")

    return test_data

if __name__ == "__main__":
    asyncio.run(process_live_results())