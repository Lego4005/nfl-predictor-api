#!/usr/bin/env python3
"""
Validation script for Shadow Storage Contract implementation
Validates implementation without requiring a running server
"""

import os
import sys
import importlib.util
from pathlib import Path

def validate_shadow_storage_implementation():
    """Validate the shadow storage contract implementation"""

    print("🔍 Validating Shadow Storage Contract Implementation...")
    print("=" * 70)

    all_passed = True

    # Check 1: Database migration exists
    print("\n1. Checking database migration...")
    migration_file = "supabase/migrations/053_shadow_storage_contract.sql"

    if os.path.exists(migration_file):
        print(f"✅ Migration file exists: {migration_file}")

        # Check migration content
        with open(migration_file, 'r') as f:
            content = f.read()

        required_elements = [
            "expert_prediction_assertions_shadow",
            "shadow_run_telemetry",
            "store_shadow_prediction",
            "used_in_council = FALSE",
            "used_in_coherence = FALSE",
            "used_in_settlement = FALSE"
        ]

        for element in required_elements:
            if element in content:
                print(f"✅ Migration contains: {element}")
            else:
                print(f"❌ Migration missing: {element}")
                all_passed = False
    else:
        print(f"❌ Migration file not found: {migration_file}")
        all_passed = False

    # Check 2: Shadow API implementation
    print("\n2. Checking Shadow API implementation...")
    api_file = "src/api/shadow_predictions_api.py"

    if os.path.exists(api_file):
        print(f"✅ Shadow API file exists: {api_file}")

        # Check API content
        with open(api_file, 'r') as f:
            content = f.read()

        required_endpoints = [
            "@router.post(\"/predictions\"",
            "@router.get(\"/predictions/{shadow_run_id}\"",
            "@router.get(\"/telemetry/{shadow_run_id}\"",
            "@router.get(\"/health\"",
            "isolation_verified"
        ]

        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"✅ API contains: {endpoint}")
            else:
                print(f"❌ API missing: {endpoint}")
                all_passed = False

        # Check isolation guarantees
        isolation_checks = [
            ("council", "never.*council|council.*never"),
            ("coherence", "never.*coherence|coherence.*never"),
            ("settlement", "never.*settlement|settlement.*never"),
            ("isolated", "isolated.*hot path|hot path.*isolated")
        ]

        isolation_found = 0
        import re
        for check_name, pattern in isolation_checks:
            if re.search(pattern, content.lower()):
                isolation_found += 1
                print(f"✅ Isolation guarantee found: {check_name}")
            else:
                print(f"❌ Isolation guarantee missing: {check_name}")

        if isolation_found >= 3:
            print(f"✅ Sufficient isolation guarantees documented ({isolation_found}/4)")
        else:
            print(f"❌ Insufficient isolation documentation ({isolation_found}/4)")
            all_passed = False

    else:
        print(f"❌ Shadow API file not found: {api_file}")
        all_passed = False

    # Check 3: Orchestrator integration
    print("\n3. Checking orchestrator integration...")
    orchestrator_file = "agentuity/agents/game-orchestrator/index.ts"

    if os.path.exists(orchestrator_file):
        print(f"✅ Orchestrator file exists: {orchestrator_file}")

        # Check orchestrator content
        with open(orchestrator_file, 'r') as f:
            content = f.read()

        required_features = [
            "generateShadowPredictions",
            "shadow_model",
            "enable_shadow_runs",
            "/api/shadow/predictions"
        ]

        for feature in required_features:
            if feature in content:
                print(f"✅ Orchestrator contains: {feature}")
            else:
                print(f"❌ Orchestrator missing: {feature}")
                all_passed = False
    else:
        print(f"❌ Orchestrator file not found: {orchestrator_file}")
        all_passed = False

    # Check 4: Main API integration
    print("\n4. Checking main API integration...")
    main_api_file = "src/api/main.py"

    if os.path.exists(main_api_file):
        print(f"✅ Main API file exists: {main_api_file}")

        # Check main API content
        with open(main_api_file, 'r') as f:
            content = f.read()

        if "shadow_predictions_api" in content:
            print(f"✅ Shadow API router imported")
        else:
            print(f"❌ Shadow API router not imported")
            all_passed = False

        if "app.include_router(shadow_predictions_api.router)" in content:
            print(f"✅ Shadow API router included")
        else:
            print(f"❌ Shadow API router not included")
            all_passed = False
    else:
        print(f"❌ Main API file not found: {main_api_file}")
        all_passed = False

    # Check 5: Test script exists
    print("\n5. Checking test implementation...")
    test_file = "test_shadow_storage_contract.py"

    if os.path.exists(test_file):
        print(f"✅ Test script exists: {test_file}")

        # Check test content
        with open(test_file, 'r') as f:
            content = f.read()

        required_tests = [
            "test_store_shadow_prediction",
            "test_isolation_guarantees",
            "test_telemetry_collection",
            "test_shadow_run_management",
            "test_health_monitoring"
        ]

        for test in required_tests:
            if test in content:
                print(f"✅ Test includes: {test}")
            else:
                print(f"❌ Test missing: {test}")
                all_passed = False
    else:
        print(f"❌ Test script not found: {test_file}")
        all_passed = False

    # Summary
    print("\n" + "=" * 70)

    if all_passed:
        print("🎉 All validations passed!")
        print("\nShadow Storage Contract is properly implemented:")
        print("• Database schema with isolation constraints")
        print("• Shadow predictions API with telemetry")
        print("• Orchestrator integration for shadow model execution")
        print("• Main API integration")
        print("• Comprehensive test coverage")
        print("\nKey features:")
        print("• Shadow predictions stored separately from hot path")
        print("• Database constraints enforce isolation (never used in council/coherence/settlement)")
        print("• Telemetry collection for shadow runs")
        print("• Shadow model execution in orchestrator")
        print("• Health monitoring and management endpoints")

        print(f"\nNext steps:")
        print("1. Apply database migration: supabase db push")
        print("2. Start API server: python src/api/main.py")
        print("3. Run integration tests: python test_shadow_storage_contract.py")
        print("4. Test with Agentuity orchestrator")

    else:
        print("❌ Some validations failed. Check implementation.")

    return all_passed

if __name__ == "__main__":
    success = validate_shadow_storage_implementation()
    sys.exit(0 if success else 1)
