#!/usr/bin/env python3
"""
Verify Pilot Expert State Seeding (Phase 1.4)
Checks database for proper initialization of 4 pilot experts.
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def verify_pilot_expert_seeding():
    """Verify Phase 1.4 pilot expert seeding"""

    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing Supabase credentials")
        print("   Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        return False

    supabase = create_client(supabase_url, supabase_key)

    # Expected configuration
    RUN_ID = "run_2025_pilot4"
    EXPECTED_EXPERTS = [
        "conservative_analyzer",
        "momentum_rider",
        "contrarian_rebel",
        "value_hunter"
    ]
    EXPECTED_CATEGORIES_COUNT = 83
    EXPECTED_CALIBRATIONS_PER_EXPERT = 83
    EXPECTED_TOTAL_CALIBRATIONS = 4 * 83  # 332

    print("=" * 80)
    print("PILOT EXPERT STATE SEEDING VERIFICATION (Phase 1.4)")
    print("=" * 80)
    print(f"Run ID: {RUN_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    results = {
        "run_id": RUN_ID,
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "all_passed": True
    }

    # ========================================
    # 1. Check Expert Bankroll Initialization
    # ========================================
    print("1. EXPERT BANKROLL INITIALIZATION")
    print("-" * 80)

    try:
        response = supabase.table("expert_bankroll").select("*").eq("run_id", RUN_ID).execute()
        bankrolls = response.data

        print(f"   Found {len(bankrolls)} expert bankroll records")

        bankroll_check = {
            "expected_count": 4,
            "actual_count": len(bankrolls),
            "passed": len(bankrolls) == 4,
            "details": []
        }

        if len(bankrolls) == 0:
            print("   ❌ FAIL: No bankroll records found")
            print(f"   Expected: 4 experts with {RUN_ID}")
            bankroll_check["passed"] = False
            results["all_passed"] = False
        else:
            for bankroll in bankrolls:
                expert_id = bankroll["expert_id"]
                current_units = bankroll["current_units"]
                starting_units = bankroll["starting_units"]

                is_expected = expert_id in EXPECTED_EXPERTS
                correct_units = (current_units == 100.0 and starting_units == 100.0)

                status = "✅" if (is_expected and correct_units) else "❌"
                print(f"   {status} {expert_id}: {current_units} units (start: {starting_units})")

                bankroll_check["details"].append({
                    "expert_id": expert_id,
                    "current_units": float(current_units),
                    "starting_units": float(starting_units),
                    "is_expected": is_expected,
                    "correct_units": correct_units
                })

                if not is_expected:
                    print(f"      ⚠️  WARNING: Unexpected expert '{expert_id}'")
                    print(f"      Expected one of: {', '.join(EXPECTED_EXPERTS)}")

                if not correct_units:
                    print(f"      ❌ FAIL: Incorrect starting bankroll")
                    print(f"      Expected: 100.0 units, Got: {current_units}")
                    bankroll_check["passed"] = False
                    results["all_passed"] = False

            # Check for missing experts
            found_experts = {b["expert_id"] for b in bankrolls}
            missing_experts = set(EXPECTED_EXPERTS) - found_experts
            if missing_experts:
                print(f"   ❌ FAIL: Missing experts: {', '.join(missing_experts)}")
                bankroll_check["passed"] = False
                bankroll_check["missing_experts"] = list(missing_experts)
                results["all_passed"] = False

        results["checks"]["bankroll"] = bankroll_check
        print()

    except Exception as e:
        print(f"   ❌ ERROR querying expert_bankroll: {e}")
        results["checks"]["bankroll"] = {"passed": False, "error": str(e)}
        results["all_passed"] = False
        print()

    # ========================================
    # 2. Check Category Calibration Initialization
    # ========================================
    print("2. CATEGORY CALIBRATION INITIALIZATION")
    print("-" * 80)

    try:
        response = supabase.table("expert_category_calibration").select("*").eq("run_id", RUN_ID).execute()
        calibrations = response.data

        print(f"   Found {len(calibrations)} calibration records")

        calibration_check = {
            "expected_count": EXPECTED_TOTAL_CALIBRATIONS,
            "actual_count": len(calibrations),
            "passed": len(calibrations) == EXPECTED_TOTAL_CALIBRATIONS,
            "by_expert": {},
            "beta_priors_correct": True,
            "ema_priors_present": True
        }

        if len(calibrations) == 0:
            print("   ❌ FAIL: No calibration records found")
            print(f"   Expected: {EXPECTED_TOTAL_CALIBRATIONS} records (4 experts × 83 categories)")
            calibration_check["passed"] = False
            results["all_passed"] = False
        else:
            # Group by expert
            by_expert = {}
            for cal in calibrations:
                expert_id = cal["expert_id"]
                if expert_id not in by_expert:
                    by_expert[expert_id] = []
                by_expert[expert_id].append(cal)

            # Verify each expert
            for expert_id in EXPECTED_EXPERTS:
                if expert_id not in by_expert:
                    print(f"   ❌ {expert_id}: NO CALIBRATIONS FOUND")
                    calibration_check["passed"] = False
                    results["all_passed"] = False
                    continue

                expert_cals = by_expert[expert_id]
                count = len(expert_cals)
                status = "✅" if count == EXPECTED_CALIBRATIONS_PER_EXPERT else "❌"
                print(f"   {status} {expert_id}: {count} categories")

                calibration_check["by_expert"][expert_id] = {
                    "count": count,
                    "expected": EXPECTED_CALIBRATIONS_PER_EXPERT,
                    "passed": count == EXPECTED_CALIBRATIONS_PER_EXPERT
                }

                if count != EXPECTED_CALIBRATIONS_PER_EXPERT:
                    calibration_check["passed"] = False
                    results["all_passed"] = False

                # Check Beta priors (sample first 3)
                beta_sample = [c for c in expert_cals if c["category"] in ["game_winner", "spread_full_game", "will_overtime"]]
                for cal in beta_sample[:3]:
                    beta_alpha = cal.get("beta_alpha")
                    beta_beta = cal.get("beta_beta")
                    if beta_alpha != 1.0 or beta_beta != 1.0:
                        print(f"      ⚠️  {cal['category']}: Beta({beta_alpha}, {beta_beta}) - expected Beta(1.0, 1.0)")
                        calibration_check["beta_priors_correct"] = False

                # Check EMA priors (sample first 3)
                ema_sample = [c for c in expert_cals if c["category"] in ["home_score_exact", "qb_passing_yards", "total_full_game"]]
                for cal in ema_sample[:3]:
                    ema_mu = cal.get("ema_mu")
                    ema_sigma = cal.get("ema_sigma")
                    if ema_mu is None or ema_sigma is None:
                        print(f"      ⚠️  {cal['category']}: Missing EMA parameters")
                        calibration_check["ema_priors_present"] = False

            # Check unique categories
            all_categories = set(c["category"] for c in calibrations)
            print(f"   📊 Unique categories: {len(all_categories)}")
            calibration_check["unique_categories_count"] = len(all_categories)

            if len(all_categories) != EXPECTED_CATEGORIES_COUNT:
                print(f"      ⚠️  Expected {EXPECTED_CATEGORIES_COUNT} unique categories")

        results["checks"]["calibration"] = calibration_check
        print()

    except Exception as e:
        print(f"   ❌ ERROR querying expert_category_calibration: {e}")
        results["checks"]["calibration"] = {"passed": False, "error": str(e)}
        results["all_passed"] = False
        print()

    # ========================================
    # 3. Check Expert Eligibility Gates
    # ========================================
    print("3. EXPERT ELIGIBILITY GATES")
    print("-" * 80)

    try:
        response = supabase.table("expert_eligibility_gates").select("*").eq("run_id", RUN_ID).execute()
        gates = response.data

        print(f"   Found {len(gates)} eligibility gate records")

        gates_check = {
            "expected_count": 4,
            "actual_count": len(gates),
            "passed": len(gates) == 4,
            "details": []
        }

        if len(gates) == 0:
            print("   ❌ FAIL: No eligibility gate records found")
            print(f"   Expected: 4 experts with eligibility gates")
            gates_check["passed"] = False
            results["all_passed"] = False
        else:
            for gate in gates:
                expert_id = gate["expert_id"]
                eligible = gate["eligible"]
                validity_rate = gate["schema_validity_rate"]
                latency_slo = gate["latency_slo_ms"]
                validity_slo = gate["validity_slo_rate"]

                correct_slos = (latency_slo == 6000 and validity_slo == 0.985)

                status = "✅" if eligible and correct_slos else "❌"
                print(f"   {status} {expert_id}: eligible={eligible}, validity_slo={validity_slo}, latency_slo={latency_slo}ms")

                gates_check["details"].append({
                    "expert_id": expert_id,
                    "eligible": eligible,
                    "schema_validity_rate": float(validity_rate),
                    "latency_slo_ms": latency_slo,
                    "validity_slo_rate": float(validity_slo),
                    "correct_slos": correct_slos
                })

                if not correct_slos:
                    print(f"      ⚠️  WARNING: Incorrect SLO configuration")
                    print(f"      Expected: validity_slo=0.985, latency_slo=6000ms")
                    gates_check["passed"] = False
                    results["all_passed"] = False

        results["checks"]["eligibility_gates"] = gates_check
        print()

    except Exception as e:
        print(f"   ❌ ERROR querying expert_eligibility_gates: {e}")
        results["checks"]["eligibility_gates"] = {"passed": False, "error": str(e)}
        results["all_passed"] = False
        print()

    # ========================================
    # 4. Summary
    # ========================================
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    print(f"Run ID: {RUN_ID}")
    print()

    print("Requirements from tasks.md Phase 1.4:")
    print("  1. Insert expert_bankroll rows (100 units) for 4 pilot experts")
    print("  2. Initialize expert_category_calibration priors (Beta α=1,β=1; EMA μ=0,σ from registry)")
    print("  3. Set up expert eligibility gates (validity ≥98.5%, latency SLO 6000ms)")
    print("  4. Pilot experts: conservative_analyzer, momentum_rider, contrarian_rebel, value_hunter")
    print()

    bankroll_status = "✅ PASS" if results["checks"].get("bankroll", {}).get("passed") else "❌ FAIL"
    calibration_status = "✅ PASS" if results["checks"].get("calibration", {}).get("passed") else "❌ FAIL"
    gates_status = "✅ PASS" if results["checks"].get("eligibility_gates", {}).get("passed") else "❌ FAIL"

    print(f"Bankroll Initialization:      {bankroll_status}")
    print(f"Category Calibration:         {calibration_status}")
    print(f"Eligibility Gates:            {gates_status}")
    print()

    if results["all_passed"]:
        print("🎉 ALL CHECKS PASSED - Pilot Expert Seeding Complete!")
    else:
        print("⚠️  SOME CHECKS FAILED - Review output above for details")

    print()
    print("=" * 80)

    # Save results to file
    output_file = f"pilot_expert_seeding_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=decimal_default)

    print(f"📄 Full results saved to: {output_file}")
    print()

    return results["all_passed"]

if __name__ == "__main__":
    success = verify_pilot_expert_seeding()
    sys.exit(0 if success else 1)
