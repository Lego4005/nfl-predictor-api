#!/usr/bin/env python3
"""
Diagnostic Script: Check Current State of Episodic Memory System

This script analyzes whether the learning system is actually working by checking:
1. Are episodic memories being stored?
2. Are learned principles being discovered?
3. Are belief revisions happening?
4. Is reasoning evolving over time?
5. Is self-healing working?

This determines if the 92.3% Week 4 accuracy was real learning or just luck.
"""

import asyncio
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def print_header(title):
    print(f"\n{'='*100}")
    print(f"  {title}")
    print(f"{'='*100}\n")

def print_section(title):
    print(f"\n{'─'*100}")
    print(f"  {title}")
    print(f"{'─'*100}\n")

async def diagnose_memory_system():
    """Comprehensive diagnosis of the episodic memory system"""

    print_header("🔍 EPISODIC MEMORY SYSTEM DIAGNOSTIC")

    expert_id = 'conservative_analyzer'

    # Test 1: Episodic Memories
    print_section("TEST 1: Episodic Memories (Game Experiences)")

    try:
        memories = supabase.table('expert_episodic_memories') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .execute()

        memory_count = len(memories.data) if memories.data else 0

        if memory_count == 0:
            print("❌ CRITICAL: No episodic memories found!")
            print("   This means the expert is NOT learning from past games.")
            print("   The 92.3% Week 4 accuracy is likely just lucky variance.\n")
        else:
            print(f"✅ Found {memory_count} episodic memories")

            if memory_count >= 3:
                print("\n📊 Sample memories:")
                for i, mem in enumerate(memories.data[:3], 1):
                    print(f"\n   Memory {i}:")
                    print(f"   • Game ID: {mem.get('game_id')}")
                    print(f"   • Memory Type: {mem.get('memory_type')}")
                    print(f"   • Emotional State: {mem.get('emotional_state')}")
                    print(f"   • Emotional Intensity: {mem.get('emotional_intensity')}")
                    print(f"   • Retrieval Count: {mem.get('retrieval_count', 0)}")
                    print(f"   • Created: {mem.get('created_at', 'N/A')[:10]}")

            # Check memory characteristics
            if memory_count > 0:
                avg_intensity = sum(m.get('emotional_intensity', 0) for m in memories.data) / memory_count
                avg_retrieval = sum(m.get('retrieval_count', 0) for m in memories.data) / memory_count
                print(f"\n📈 Memory Statistics:")
                print(f"   • Average Emotional Intensity: {avg_intensity:.2f}/1.0")
                print(f"   • Average Retrieval Count: {avg_retrieval:.1f}")

                if avg_retrieval < 1:
                    print("   ⚠️  Low retrieval count suggests memories aren't being used!")

    except Exception as e:
        print(f"❌ ERROR checking episodic memories: {e}\n")

    # Test 2: Learned Principles
    print_section("TEST 2: Learned Principles (Discovered Patterns)")

    try:
        principles = supabase.table('expert_learned_principles') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .eq('is_active', True) \
            .execute()

        principle_count = len(principles.data) if principles.data else 0

        if principle_count == 0:
            print("❌ CRITICAL: No learned principles found!")
            print("   This means the expert hasn't discovered any predictive patterns.")
            print("   No systematic learning has occurred.\n")
        else:
            print(f"✅ Found {principle_count} active learned principles")

            if principle_count >= 3:
                print("\n📚 Top principles:")
                # Sort by success rate
                sorted_principles = sorted(principles.data, key=lambda x: x.get('success_rate', 0), reverse=True)

                for i, principle in enumerate(sorted_principles[:3], 1):
                    print(f"\n   Principle {i}:")
                    print(f"   • Statement: {principle.get('principle_statement')}")
                    print(f"   • Category: {principle.get('principle_category')}")
                    print(f"   • Success Rate: {principle.get('success_rate', 0)*100:.1f}%")
                    print(f"   • Times Applied: {principle.get('times_applied', 0)}")
                    print(f"   • Supporting Games: {principle.get('supporting_games_count', 0)}")
                    print(f"   • Discovered: {principle.get('discovered_at', 'N/A')[:10]}")

                # Check if principles are actually helping
                high_success = [p for p in principles.data if p.get('success_rate', 0) > 0.7]
                if high_success:
                    print(f"\n✅ {len(high_success)} principles with >70% success rate")
                else:
                    print("\n⚠️  No principles with >70% success rate - learning may not be effective")

    except Exception as e:
        print(f"❌ ERROR checking learned principles: {e}\n")

    # Test 3: Belief Revisions
    print_section("TEST 3: Belief Revisions (Mind Changes)")

    try:
        revisions = supabase.table('expert_belief_revisions') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .order('revision_timestamp', desc=True) \
            .execute()

        revision_count = len(revisions.data) if revisions.data else 0

        if revision_count == 0:
            print("❌ CRITICAL: No belief revisions found!")
            print("   This means the expert never changed their approach.")
            print("   Static thinking = no adaptation to new evidence.\n")
        else:
            print(f"✅ Found {revision_count} belief revisions")

            if revision_count >= 2:
                print("\n🔄 Recent revisions:")

                for i, revision in enumerate(revisions.data[:2], 1):
                    print(f"\n   Revision {i}:")
                    print(f"   • Category: {revision.get('belief_category')}")
                    print(f"   • Key: {revision.get('belief_key')}")
                    print(f"   • Old → New: {revision.get('old_belief')} → {revision.get('new_belief')}")
                    print(f"   • Trigger: {revision.get('revision_trigger')}")
                    print(f"   • Impact Score: {revision.get('impact_score', 0):.2f}")
                    print(f"   • Reasoning: {revision.get('causal_reasoning', 'N/A')[:100]}...")
                    print(f"   • Date: {revision.get('revision_timestamp', 'N/A')[:10]}")

                # Check impact
                high_impact = [r for r in revisions.data if r.get('impact_score', 0) > 0.5]
                if high_impact:
                    print(f"\n✅ {len(high_impact)} high-impact revisions (>0.5 impact score)")
                else:
                    print("\n⚠️  No high-impact revisions - changes may not be meaningful")

    except Exception as e:
        print(f"❌ ERROR checking belief revisions: {e}\n")

    # Test 4: Reasoning Chain Evolution
    print_section("TEST 4: Reasoning Chain Evolution (Thought Process Changes)")

    try:
        # Get earliest reasoning chains (Week 1)
        early_chains = supabase.table('expert_reasoning_chains') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .order('prediction_timestamp', desc=False) \
            .limit(5) \
            .execute()

        # Get latest reasoning chains (Week 4)
        late_chains = supabase.table('expert_reasoning_chains') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .order('prediction_timestamp', desc=True) \
            .limit(5) \
            .execute()

        early_count = len(early_chains.data) if early_chains.data else 0
        late_count = len(late_chains.data) if late_chains.data else 0

        if early_count == 0 or late_count == 0:
            print("❌ CRITICAL: Insufficient reasoning chains to analyze evolution")
        else:
            print(f"✅ Found {early_count} early chains and {late_count} late chains")

            # Compare reasoning factors
            print("\n📊 Early Reasoning (Week 1):")
            if early_chains.data and early_chains.data[0].get('reasoning_factors'):
                factors = early_chains.data[0]['reasoning_factors']
                if isinstance(factors, list) and len(factors) > 0:
                    for factor in factors[:3]:
                        if isinstance(factor, dict):
                            print(f"   • {factor.get('factor', 'Unknown')}: weight {factor.get('weight', 0):.2f}")

            print("\n📊 Late Reasoning (Week 4):")
            if late_chains.data and late_chains.data[0].get('reasoning_factors'):
                factors = late_chains.data[0]['reasoning_factors']
                if isinstance(factors, list) and len(factors) > 0:
                    for factor in factors[:3]:
                        if isinstance(factor, dict):
                            print(f"   • {factor.get('factor', 'Unknown')}: weight {factor.get('weight', 0):.2f}")

            # Check for evolution
            print("\n🔍 Analysis:")
            if early_chains.data and late_chains.data:
                early_factors = early_chains.data[0].get('reasoning_factors', [])
                late_factors = late_chains.data[0].get('reasoning_factors', [])

                if str(early_factors) == str(late_factors):
                    print("   ⚠️  Reasoning appears IDENTICAL - no evolution detected!")
                else:
                    print("   ✅ Reasoning has EVOLVED - expert is adapting!")

    except Exception as e:
        print(f"❌ ERROR checking reasoning evolution: {e}\n")

    # Test 5: Discovered Factors
    print_section("TEST 5: Discovered Factors (New Predictive Variables)")

    try:
        factors = supabase.table('expert_discovered_factors') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .eq('is_active', True) \
            .execute()

        factor_count = len(factors.data) if factors.data else 0

        if factor_count == 0:
            print("⚠️  No discovered factors found")
            print("   Expert is using only pre-defined factors.\n")
        else:
            print(f"✅ Found {factor_count} discovered factors")

            for i, factor in enumerate(factors.data[:3], 1):
                print(f"\n   Factor {i}:")
                print(f"   • Name: {factor.get('factor_name')}")
                print(f"   • Description: {factor.get('factor_description', 'N/A')[:80]}")
                print(f"   • Correlation: {factor.get('correlation_strength', 0):.3f}")
                print(f"   • Times Used: {factor.get('times_used', 0)}")
                print(f"   • Success Rate: {factor.get('successful_applications', 0)}/{factor.get('times_used', 1)}")

    except Exception as e:
        print(f"❌ ERROR checking discovered factors: {e}\n")

    # Test 6: Confidence Calibration
    print_section("TEST 6: Confidence Calibration (Accuracy by Confidence Level)")

    try:
        calibration = supabase.table('expert_confidence_calibration') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .order('confidence_bucket') \
            .execute()

        cal_count = len(calibration.data) if calibration.data else 0

        if cal_count == 0:
            print("⚠️  No confidence calibration data")
            print("   Expert hasn't learned to adjust confidence levels.\n")
        else:
            print(f"✅ Found {cal_count} confidence calibration buckets")
            print("\n📊 Calibration by Confidence Level:")

            for bucket in calibration.data:
                conf = bucket.get('confidence_bucket', 0)
                predicted = bucket.get('predicted_count', 0)
                actual = bucket.get('actual_success_count', 0)
                actual_rate = (actual / predicted * 100) if predicted > 0 else 0
                calibration_score = bucket.get('calibration_score', 0)

                # Check if well-calibrated
                difference = abs(conf * 100 - actual_rate)
                status = "✅" if difference < 10 else "⚠️ " if difference < 20 else "❌"

                print(f"   {status} {conf*100:.0f}% confidence: {actual}/{predicted} = {actual_rate:.1f}% actual (calibration: {calibration_score:.2f})")

    except Exception as e:
        print(f"❌ ERROR checking confidence calibration: {e}\n")

    # Final Verdict
    print_header("🎯 DIAGNOSTIC VERDICT")

    # Collect results
    has_memories = memory_count > 0
    has_principles = principle_count > 0
    has_revisions = revision_count > 0
    has_chains = early_count > 0 and late_count > 0

    print(f"Memory System Status:")
    print(f"  {'✅' if has_memories else '❌'} Episodic Memories: {memory_count}")
    print(f"  {'✅' if has_principles else '❌'} Learned Principles: {principle_count}")
    print(f"  {'✅' if has_revisions else '❌'} Belief Revisions: {revision_count}")
    print(f"  {'✅' if has_chains else '❌'} Reasoning Chains: {early_count + late_count}")

    print(f"\n🏆 Overall Assessment:")

    if not has_memories and not has_principles and not has_revisions:
        print("  ❌ HYPOTHESIS 2: LUCKY VARIANCE")
        print("     The memory system is NOT being used at all.")
        print("     The 92.3% Week 4 accuracy is just random chance.")
        print("     No learning has occurred.")
        print("\n  📋 Recommendation: Build and test memory-enabled system from scratch")

    elif has_memories and has_principles and has_revisions:
        print("  ✅ HYPOTHESIS 1: GENUINE LEARNING")
        print("     The memory system is fully operational.")
        print("     Expert is storing experiences, learning principles, and revising beliefs.")
        print("     The 92.3% Week 4 accuracy likely reflects real learning.")
        print("\n  📋 Recommendation: Validate with Week 5 predictions to confirm persistence")

    else:
        print("  ⚠️  HYPOTHESIS 3: PARTIAL LEARNING")
        print("     Some memory components are working but not all.")
        print("     Learning is happening but may not be fully effective.")
        print("     Week 4 accuracy is a mix of learning and variance.")
        print("\n  📋 Recommendation: Complete the implementation and retest")

    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(diagnose_memory_system())