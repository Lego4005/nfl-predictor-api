#!/usr/bin/env python3
"""
UPDATE LEARNING SYSTEM WITH REAL DATA
Process real game accuracy results and trigger proper learning/belief revision
"""

import asyncio
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

async def update_learning_with_real_data():
    """Update the learning system with real game accuracy results"""

    print("\n" + "🧠" * 30)
    print("UPDATING LEARNING SYSTEM WITH REAL DATA")
    print("🧠" * 30 + "\n")

    # Load real accuracy results
    try:
        with open("real_accuracy_results.json", "r") as f:
            accuracy_data = json.load(f)
        print("✅ Loaded real accuracy results")
    except FileNotFoundError:
        print("❌ No real_accuracy_results.json found. Run calculate_real_accuracy.py first!")
        return

    # Initialize services (using local storage for now due to schema issues)
    supabase_client = None
    print("🔧 Using local storage for learning system")

    reasoning_logger = ReasoningChainLogger(supabase_client)
    memory_manager = EpisodicMemoryManager(supabase_client)
    belief_service = BeliefRevisionService(supabase_client)

    real_outcome = accuracy_data["real_outcome"]
    expert_accuracies = accuracy_data["expert_accuracies"]

    print(f"📊 REAL GAME OUTCOME:")
    print(f"   {real_outcome['final_score']}")
    print(f"   Total: {real_outcome['total']} ({real_outcome['total_result']})")
    print(f"   Margin: {real_outcome['margin']} points")
    print(f"   Spread: {real_outcome['spread_result']}")
    print("=" * 60)

    # Process each expert's real performance
    high_performers = []
    poor_performers = []
    needs_revision = []

    for expert_data in expert_accuracies:
        expert_id = expert_data["expert"]
        accuracy = expert_data["accuracy"]
        overall_accuracy = accuracy["overall_accuracy"]

        # Categorize performance
        if overall_accuracy > 0.4:
            high_performers.append((expert_id, overall_accuracy))
        elif overall_accuracy < 0.2:
            poor_performers.append((expert_id, overall_accuracy))
            needs_revision.append(expert_data)

        # Create enhanced episodic memory with real accuracy
        lesson = generate_real_lesson(expert_id, accuracy, real_outcome)

        # Use simplified prediction format for episodic memory
        simplified_prediction = {
            "winner": accuracy["detailed_results"].get("winner", {}).get("predicted", "unknown"),
            "final_score": accuracy["detailed_results"].get("final_score", {}).get("predicted", "unknown"),
            "total_pick": accuracy["detailed_results"].get("total_pick", {}).get("predicted", "unknown"),
            "overall_accuracy": accuracy["overall_accuracy"]
        }

        memory_id = await memory_manager.store_episodic_memory(
            expert_id=expert_id,
            game_id="LAC_LV_20250916_REAL",
            prediction=simplified_prediction,
            outcome=real_outcome,
            lesson=lesson,
            expert_personality="analytical"  # Default for now
        )

        print(f"💾 Updated episodic memory for {expert_id}: {memory_id}")

    print(f"\n🏆 HIGH PERFORMERS ({len(high_performers)}):")
    for expert_id, acc in sorted(high_performers, key=lambda x: x[1], reverse=True):
        print(f"   {expert_id.replace('_', ' ').title()}: {acc:.1%}")

    print(f"\n❌ POOR PERFORMERS ({len(poor_performers)}):")
    for expert_id, acc in sorted(poor_performers, key=lambda x: x[1]):
        print(f"   {expert_id.replace('_', ' ').title()}: {acc:.1%}")

    # TRIGGER BELIEF REVISION for poor performers
    print(f"\n🔄 TRIGGERING BELIEF REVISION FOR {len(needs_revision)} EXPERTS...")

    for expert_data in needs_revision:
        expert_id = expert_data["expert"]
        accuracy = expert_data["accuracy"]

        # Create game results and prediction history for belief revision
        game_results = [{
            "game_id": "LAC_LV_20250916_REAL",
            "prediction": accuracy["detailed_results"],
            "actual_outcome": real_outcome,
            "accuracy": accuracy["overall_accuracy"],
            "major_failures": identify_major_failures(accuracy["detailed_results"])
        }]

        prediction_history = [{
            "game_id": "LAC_LV_20250916_REAL",
            "prediction": accuracy["detailed_results"],
            "confidence": 0.6  # Estimated average confidence
        }]

        try:
            revisions = await belief_service.trigger_belief_revision(
                expert_id=expert_id,
                game_results=game_results,
                prediction_history=prediction_history
            )

            print(f"🔄 {expert_id}: {len(revisions)} belief revisions triggered")

            # Show what needs to be revised
            failures = identify_major_failures(accuracy["detailed_results"])
            if failures:
                print(f"   Major failures: {', '.join(failures)}")

        except Exception as e:
            print(f"❌ Error triggering belief revision for {expert_id}: {e}")

    # LEARNING INSIGHTS
    print(f"\n🎓 KEY LEARNING INSIGHTS:")

    # 1. Total points prediction was universally wrong
    total_failures = sum(1 for expert in expert_accuracies
                        if expert["accuracy"]["detailed_results"].get("total_pick", {}).get("correct") == False)
    print(f"   • {total_failures}/15 experts failed total prediction (29 vs expected 40-50)")

    # 2. Score predictions were too high
    score_overestimates = sum(1 for expert in expert_accuracies
                             if "predicted_total" in expert["accuracy"]["detailed_results"]
                             and expert["accuracy"]["detailed_results"]["predicted_total"]["predicted"] > 35)
    print(f"   • {score_overestimates}/15 experts significantly overestimated scoring")

    # 3. Home field advantage was overvalued
    home_picks = sum(1 for expert in expert_accuracies
                    if expert["accuracy"]["detailed_results"].get("winner", {}).get("predicted") == "LV")
    print(f"   • {home_picks}/15 experts incorrectly favored home team")

    # 4. LAC momentum reading was correct
    lac_picks = sum(1 for expert in expert_accuracies
                   if expert["accuracy"]["detailed_results"].get("winner", {}).get("predicted") == "LAC")
    print(f"   • {lac_picks}/15 experts correctly read LAC momentum (80% success rate)")

    # Save updated learning data
    learning_update = {
        "real_outcome": real_outcome,
        "expert_performance": expert_accuracies,
        "learning_insights": {
            "total_prediction_failure_rate": total_failures / 15,
            "score_overestimation_rate": score_overestimates / 15,
            "home_field_bias": home_picks / 15,
            "momentum_reading_success": lac_picks / 15
        },
        "belief_revisions_triggered": len(needs_revision),
        "high_performers": high_performers,
        "poor_performers": poor_performers,
        "updated_at": datetime.now().isoformat()
    }

    with open("learning_system_update.json", "w") as f:
        json.dump(learning_update, f, indent=2)

    print(f"\n✅ LEARNING SYSTEM UPDATED WITH REAL DATA!")
    print(f"💾 Results saved to learning_system_update.json")
    print(f"\n🚀 SYSTEM IMPROVEMENTS:")
    print(f"   • Experts with <20% accuracy will revise core beliefs")
    print(f"   • Total scoring models need recalibration")
    print(f"   • Home field advantage weight should be reduced")
    print(f"   • Momentum reading strategies should be reinforced")

def generate_real_lesson(expert_id, accuracy, real_outcome):
    """Generate specific lessons based on real accuracy results"""

    overall_acc = accuracy["overall_accuracy"]
    details = accuracy["detailed_results"]

    if overall_acc > 0.4:
        # High performer - reinforce successful strategies
        successes = [k for k, v in details.items() if v.get("correct") == True]
        return f"Strong performance ({overall_acc:.1%}). Successful on: {', '.join(successes[:3])}. Continue current approach."

    elif overall_acc < 0.2:
        # Poor performer - major revision needed
        failures = [k for k, v in details.items() if v.get("correct") == False]
        return f"Poor performance ({overall_acc:.1%}). Failed on: {', '.join(failures[:3])}. Major strategy revision required."

    else:
        # Mixed performance - selective improvements
        winner_correct = details.get("winner", {}).get("correct")
        total_correct = details.get("total_pick", {}).get("correct")

        if winner_correct and not total_correct:
            return f"Good directional read but scoring model needs work. Actual total was {real_outcome['total']}, much lower than expected."
        elif not winner_correct:
            return f"Missed the winner ({real_outcome['winner']}). Need to better evaluate team strengths and momentum."
        else:
            return f"Mixed results ({overall_acc:.1%}). Some predictions accurate, others need refinement."

def identify_major_failures(detailed_results):
    """Identify the major prediction failures for belief revision"""

    failures = []

    if detailed_results.get("winner", {}).get("correct") == False:
        failures.append("winner_prediction")

    if detailed_results.get("total_pick", {}).get("correct") == False:
        failures.append("total_scoring")

    if detailed_results.get("predicted_total", {}).get("difference", 0) > 15:
        failures.append("score_overestimation")

    if detailed_results.get("final_score", {}).get("correct") == False:
        failures.append("exact_score")

    return failures

if __name__ == "__main__":
    asyncio.run(update_learning_with_real_data())