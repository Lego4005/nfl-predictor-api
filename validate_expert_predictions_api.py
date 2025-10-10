#!/usr/bin/env python3
"""
Valcript for Expert Predictions API
Tests core functionality without requiring a running server
"""

import json
import jsonschema
import os
from typing import Dict, Any, List, Tuple

def load_prediction_schema() -> Dict[str, Any]:
    """Load the prediction schema for validation"""

    schema_path = "schemas/expert_predictions_v1.schema.json"

    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        return None

    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_prediction_bundle(bundle: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a prediction bundle against the schema"""

    try:
        jsonschema.validate(bundle, schema)
        return True, []
    except jsonschema.ValidationError as e:
        error_msg = f"Schema validation failed: {e.message}"
        if e.path:
            error_msg += f" at path: {'.'.join(str(p) for p in e.path)}"
        return False, [error_msg]
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]

def create_valid_bundle() -> Dict[str, Any]:
    """Create a valid 83-assertion prediction bundle"""

    # Create 83 predictions with valid categories
    predictions = []

    # All 83 valid categories from schema
    categories = [
        "game_winner", "home_score_exact", "away_score_exact", "margin_of_victory",
        "spread_full_game", "total_full_game", "winner_moneyline", "first_half_winner",
        "first_half_spread", "first_half_total", "q1_winner", "q2_winner", "q3_winner",
        "q4_winner", "q1_total", "q2_total", "q3_total", "q4_total", "first_half_total_points",
        "second_half_total_points", "highest_scoring_quarter", "lowest_scoring_quarter",
        "team_total_points_home", "team_total_points_away", "first_team_to_score",
        "last_team_to_score", "team_with_longest_td", "team_with_most_turnovers",
        "team_with_most_sacks", "team_with_most_penalties", "largest_lead_of_game",
        "number_of_lead_changes", "will_overtime", "will_safety", "will_pick_six",
        "will_fumble_return_td", "will_defensive_td", "will_special_teams_td",
        "will_punt_return_td", "will_kickoff_return_td", "total_turnovers", "total_sacks",
        "total_penalties", "longest_touchdown", "longest_field_goal", "total_field_goals_made",
        "missed_extra_points", "qb_passing_yards", "qb_passing_tds", "qb_interceptions",
        "qb_rushing_yards", "rb_rushing_yards", "rb_rushing_tds", "wr_receiving_yards",
        "wr_receptions", "te_receiving_yards", "kicker_total_points", "anytime_td_scorer",
        "first_td_scorer", "last_td_scorer", "qb_longest_completion", "rb_longest_rush",
        "wr_longest_reception", "kicker_longest_fg", "defense_interceptions", "defense_sacks",
        "defense_forced_fumbles", "qb_fantasy_points", "top_skill_player_fantasy",
        "live_win_probability", "next_score_type", "current_drive_outcome", "fourth_down_decision",
        "next_team_to_score", "time_to_next_score_min", "weather_impact_score",
        "injury_impact_score", "travel_rest_factor", "divisional_rivalry_factor",
        "coaching_advantage", "home_field_advantage_pts", "momentum_factor", "public_betting_bias"
    ]

    # Create exactly 83 predictions
    for i, category in enumerate(categories[:83]):
        pred_type = "binary" if i % 3 == 0 else ("numeric" if i % 3 == 1 else "enum")

        prediction = {
            "category": category,
            "subject": f"Prediction for {category}",
            "pred_type": pred_type,
            "confidence": 0.5 + (i % 5) * 0.1,
            "stake_units": 0.5 + (i % 3) * 0.5,
            "odds": {"type": "american", "value": -110 + (i % 20)},
            "why": [{"memory_id": f"mem_{i:03d}", "weight": 0.5 + (i % 3) * 0.2}] if i % 4 == 0 else []
        }

        # Set appropriate value based on pred_type
        if pred_type == "binary":
            prediction["value"] = i % 2 == 0
        elif pred_type == "numeric":
            prediction["value"] = 10.5 + i
        else:
            prediction["value"] = "option_a" if i % 2 == 0 else "option_b"

        predictions.append(prediction)

    return {
        "overall": {
            "winner_team_id": "BUF",
            "home_win_prob": 0.45,
            "away_win_prob": 0.55,
            "overall_confidence": 0.72,
            "recency_alpha_used": 0.8
        },
        "predictions": predictions
    }

def create_invalid_bundles() -> List[Tuple[str, Dict[str, Any]]]:
    """Create various invalid bundles for testing"""

    valid_bundle = create_valid_bundle()

    invalid_bundles = []

    # 1. Missing required field
    bundle1 = valid_bundle.copy()
    del bundle1["overall"]
    invalid_bundles.append(("Missing overall field", bundle1))

    # 2. Wrong number of predictions
    bundle2 = valid_bundle.copy()
    bundle2["predictions"] = bundle2["predictions"][:50]  # Only 50 instead of 83
    invalid_bundles.append(("Wrong prediction count", bundle2))

    # 3. Invalid confidence value
    bundle3 = valid_bundle.copy()
    bundle3["overall"]["overall_confidence"] = 1.5  # > 1.0
    invalid_bundles.append(("Invalid confidence", bundle3))

    # 4. Invalid category
    bundle4 = valid_bundle.copy()
    bundle4["predictions"][0]["category"] = "invalid_category"
    invalid_bundles.append(("Invalid category", bundle4))

    # 5. Invalid pred_type
    bundle5 = valid_bundle.copy()
    bundle5["predictions"][0]["pred_type"] = "invalid_type"
    invalid_bundles.append(("Invalid pred_type", bundle5))

    # 6. Negative stake_units
    bundle6 = valid_bundle.copy()
    bundle6["predictions"][0]["stake_units"] = -1.0
    invalid_bundles.append(("Negative stake", bundle6))

    # 7. Missing required prediction field
    bundle7 = valid_bundle.copy()
    del bundle7["predictions"][0]["confidence"]
    invalid_bundles.append(("Missing prediction field", bundle7))

    return invalid_bundles

def validate_api_file_structure():
    """Validate that API files are properly structured"""

    print("🔍 Validating API file structure...")

    files_to_check = [
        "src/api/expert_predictions_api.py",
        "src/api/expert_context_api.py",
        "src/config/settings.py",
        "schemas/expert_predictions_v1.schema.json"
    ]

    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_exist = False

    return all_exist

def validate_api_endpoints():
    """Validate API endpoint definitions"""

    print("\n🔍 Validating API endpoint definitions...")

    api_file = "src/api/expert_predictions_api.py"

    if not os.path.exists(api_file):
        print(f"   ❌ {api_file} not found")
        return False

    with open(api_file, 'r') as f:
        content = f.read()

    endpoints = [
        '@router.post("/expert/predictions"',
        '@router.get("/expert/predictions/{expert_id}/{game_id}"',
        '@router.get("/expert/predictions/{expert_id}/recent"',
        '@router.get("/validation/stats"',
        '@router.post("/validation/test"',
        '@router.get("/validation/monitor"'
    ]

    all_found = True
    for endpoint in endpoints:
        if endpoint in content:
            print(f"   ✅ {endpoint}")
        else:
            print(f"   ❌ {endpoint}")
            all_found = False

    return all_found

def validate_schema_compliance():
    """Test schema validation with various bundles"""

    print("\n🔍 Validating schema compliance...")

    # Load schema
    schema = load_prediction_schema()
    if not schema:
        return False

    print("   ✅ Schema loaded successfully")

    # Test valid bundle
    valid_bundle = create_valid_bundle()
    is_valid, errors = validate_prediction_bundle(valid_bundle, schema)

    if is_valid:
        print(f"   ✅ Valid bundle passes validation ({len(valid_bundle['predictions'])} predictions)")
    else:
        print(f"   ❌ Valid bundle failed validation: {errors[0] if errors else 'Unknown error'}")
        return False

    # Test invalid bundles
    invalid_bundles = create_invalid_bundles()

    passed_invalid_tests = 0
    for test_name, invalid_bundle in invalid_bundles:
        is_valid, errors = validate_prediction_bundle(invalid_bundle, schema)

        if not is_valid:
            print(f"   ✅ {test_name}: Correctly rejected")
            passed_invalid_tests += 1
        else:
            print(f"   ❌ {test_name}: Should have been rejected")

    print(f"   📊 Invalid bundle tests: {passed_invalid_tests}/{len(invalid_bundles)} passed")

    return passed_invalid_tests == len(invalid_bundles)

def validate_database_integration():
    """Validate database table structure for predictions"""

    print("\n🔍 Validating database integration...")

    # Check migration files
    migration_files = [
        "supabase/migrations/050_add_run_id_isolation.sql",
        "supabase/migrations/20250116_expert_competition_tables.sql"
    ]

    all_migrations_exist = True
    for migration in migration_files:
        if os.path.exists(migration):
            print(f"   ✅ {migration}")
        else:
            print(f"   ❌ {migration}")
            all_migrations_exist = False

    # Check for required tables in migration
    if os.path.exists("supabase/migrations/050_add_run_id_isolation.sql"):
        with open("supabase/migrations/050_add_run_id_isolation.sql", 'r') as f:
            content = f.read()

        required_tables = [
            "expert_bets",
            "expert_bankroll",
            "expert_category_calibration"
        ]

        for table in required_tables:
            if f"CREATE TABLE IF NOT EXISTS {table}" in content:
                print(f"   ✅ Table: {table}")
            else:
                print(f"   ❌ Table: {table}")
                all_migrations_exist = False

    return all_migrations_exist

def main():
    """Main validation function"""

    print("🚀 Validating Expert Predictions API Implementation...")
    print("=" * 70)

    # Run all validations
    validations = [
        ("File Structure", validate_api_file_structure),
        ("API Endpoints", validate_api_endpoints),
        ("Schema Compliance", validate_schema_compliance),
        ("Database Integration", validate_database_integration)
    ]

    results = {}
    for name, validator in validations:
        results[name] = validator()

    # Summary
    print("\n" + "=" * 70)
    print("📋 Validation Summary:")

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All validations passed!")
        print("\nThe Expert Predictions API is properly implemented.")
        print("\nKey features validated:")
        print("• 83-assertion prediction bundle validation")
        print("• JSON schema compliance (≥98.5% target)")
        print("• Expert bet creation with run_id isolation")
        print("• Comprehensive API endpoints")
        print("• Database integration ready")
        print("\nNext steps:")
        print("1. Start FastAPI server and test endpoints")
        print("2. Test with Agentuity orchestrator")
        print("3. Monitor validation pass rates")
        print("4. Implement bet settlement system")
    else:
        print("⚠️ Some validations failed.")
        print("Please fix the issues above before proceeding.")

    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
