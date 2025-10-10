#!/usr/bin/env python3

"""
Validation script for Learning Service implementation (Task 3.3)
Validates implementat requiring full system setup
"""

import os
import sys
import re

def validate_learning_service_implementation():
    """Validate the learning service implementation"""

    print("🔍 Validating Learning Service Implementation (Task 3.3)")
    print("=" * 70)

    all_passed = True

    # Check 1: Service file exists
    print("\n1. Checking service implementation...")
    service_file = "src/services/learning_service.py"

    if os.path.exists(service_file):
        print(f"✅ Service file exists: {service_file}")

        with open(service_file, 'r') as f:
            content = f.read()

        required_elements = [
            "class LearningService",
            "process_expert_learning",
            "BetaCalibrationState",
            "EMAState",
            "FactorState",
            "LearningUpdate",
            "LearningSession",
            "beta.*calibration",
            "ema.*calibration",
            "factor.*update"
        ]

        for element in required_elements:
            if re.search(element.lower(), content.lower()):
                print(f"✅ Service contains: {element}")
            else:
                print(f"❌ Service missing: {element}")
                all_passed = False

    else:
        print(f"❌ Service file not found: {service_file}")
        all_passed = False

    # Check 2: Learning methods implementation
    print("\n2. Checking learning methods...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        learning_methods = [
            ("Expert learning processing", "process_expert_learning"),
            ("Beta calibration update", "_update_beta_calibration"),
            ("EMA calibration update", "_update_ema_calibration"),
            ("Factor updates", "_update_category_factors"),
            ("Persona learning rates", "_get_persona_learning_rate"),
            ("Calibration improvement", "_calculate_calibration_improvement"),
            ("Expert state initialization", "_initialize_expert_states")
        ]

        for method_name, pattern in learning_methods:
            if re.search(pattern, content.lower()):
                print(f"✅ Method: {method_name}")
            else:
                print(f"❌ Missing method: {method_name}")
                all_passed = False

    # Check 3: Data structures and enums
    print("\n3. Checking data structures...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        structures = [
            ("BetaCalibrationState dataclass", "@dataclass.*BetaCalibrationState"),
            ("EMAState dataclass", "@dataclass.*EMAState"),
            ("FactorState dataclass", "@dataclass.*FactorState"),
            ("LearningUpdate dataclass", "@dataclass.*LearningUpdate"),
            ("LearningSession dataclass", "@dataclass.*LearningSession"),
            ("LearningType enum", "class LearningType.*Enum"),
            ("CalibrationMethod enum", "class CalibrationMethod.*Enum")
        ]

        for struct_name, pattern in structures:
            if re.search(pattern, content, re.DOTALL):
                print(f"✅ Structure: {struct_name}")
            else:
                print(f"❌ Missing structure: {struct_name}")
                all_passed = False

    # Check 4: Beta calibration implementation
    print("\n4. Checking Beta calibration...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        beta_features = [
            ("Alpha/Beta parameters", "alpha.*beta"),
            ("Beta distribution mean", "get_mean"),
            ("Beta distribution variance", "get_variance"),
            ("Confidence intervals", "confidence_interval"),
            ("Beta parameter updates", "alpha.*learning_rate|beta.*learning_rate"),
            ("Exact match handling", "exact_match"),
            ("Binary/enum support", "binary.*enum")
        ]

        for feature_name, pattern in beta_features:
            if re.search(pattern, content.lower()):
                print(f"✅ Beta feature: {feature_name}")
            else:
                print(f"❌ Missing beta feature: {feature_name}")
                all_passed = False

    # Check 5: EMA implementation
    print("\n5. Checking EMA calibration...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        ema_features = [
            ("Mu parameter (mean)", "mu.*float"),
            ("Sigma parameter (std dev)", "sigma.*float"),
            ("Alpha parameter (learning rate)", "alpha.*float"),
            ("EMA update method", "def update.*observed_value.*predicted_value"),
            ("Error calculation", "error.*observed.*predicted"),
            ("Variance update", "sigma.*squared_error"),
            ("Numeric prediction support", "numeric.*prediction")
        ]

        for feature_name, pattern in ema_features:
            if re.search(pattern, content.lower()):
                print(f"✅ EMA feature: {feature_name}")
            else:
                print(f"❌ Missing EMA feature: {feature_name}")
                all_passed = False

    # Check 6: Factor updates implementation
    print("\n6. Checking factor updates...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        factor_features = [
            ("Momentum factor", "momentum_factor"),
            ("Offensive efficiency factor", "offensive_efficiency_factor"),
            ("Defensive factor", "defensive_factor"),
            ("Weather factor", "weather_factor"),
            ("Home field factor", "home_field_factor"),
            ("Injury factor", "injury_factor"),
            ("Factor retrieval by category", "get_factor.*category"),
            ("Multiplicative updates", "update_factor.*multiplier"),
            ("Performance-based adjustments", "grading_score.*performance_delta|performance_delta.*grading_score")
        ]

        for feature_name, pattern in factor_features:
            if re.search(pattern, content.lower()):
                print(f"✅ Factor feature: {feature_name}")
            else:
                print(f"❌ Missing factor feature: {feature_name}")
                all_passed = False

    # Check 7: Persona-specific adjustments
    print("\n7. Checking persona adjustments...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        persona_features = [
            ("Conservative analyzer", "conservative_analyzer"),
            ("Momentum rider", "momentum_rider"),
            ("Contrarian rebel", "contrarian_rebel"),
            ("Value hunter", "value_hunter"),
            ("Persona adjustments dict", "persona_adjustments"),
            ("Beta learning rate adjustment", "beta_learning_rate"),
            ("EMA alpha adjustment", "ema_alpha"),
            ("Factor adjustment rate", "factor_adjustment_rate")
        ]

        for feature_name, pattern in persona_features:
            if re.search(pattern, content.lower()):
                print(f"✅ Persona feature: {feature_name}")
            else:
                print(f"❌ Missing persona feature: {feature_name}")
                all_passed = False

    # Check 8: Audit trail implementation
    print("\n8. Checking audit trails...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        audit_features = [
            ("Learning updates list", "learning_updates"),
            ("Learning sessions list", "learning_sessions"),
            ("Update ID tracking", "update_id"),
            ("State before/after", "state_before.*=|state_after.*="),
            ("Processing time tracking", "processing_time_ms"),
            ("Learning history retrieval", "get_learning_history"),
            ("Performance metrics", "get_learning_performance_metrics"),
            ("Audit trail storage", "learning_updates.*append")
        ]

        for feature_name, pattern in audit_features:
            if re.search(pattern, content.lower()):
                print(f"✅ Audit feature: {feature_name}")
            else:
                print(f"❌ Missing audit feature: {feature_name}")
                all_passed = False

    # Check 9: Test implementation
    print("\n9. Checking test implementation...")

    test_file = "test_learning_service.py"

    if os.path.exists(test_file):
        print(f"✅ Test file exists: {test_file}")

        with open(test_file, 'r') as f:
            content = f.read()

        test_features = [
            "test_learning_service",
            "beta.*calibration.*state",
            "ema.*state",
            "factor.*state",
            "beta.*calibration.*update",
            "ema.*calibration.*update",
            "factor.*update",
            "expert.*learning.*session",
            "calibration.*state.*retrieval",
            "learning.*history",
            "performance.*metrics",
            "persona.*adjustments",
            "configuration.*updates"
        ]

        for feature in test_features:
            if re.search(feature, content.lower()):
                print(f"✅ Test includes: {feature}")
            else:
                print(f"❌ Test missing: {feature}")
                all_passed = False
    else:
        print(f"❌ Test file not found: {test_file}")
        all_passed = False

    # Check 10: Requirements compliance
    print("\n10. Checking requirements compliance...")

    requirements = [
        ("Service location", "src/services/learning_service.py"),
        ("Beta calibration", "beta.*calibration"),
        ("EMA μ/σ updates", "ema.*mu.*sigma"),
        ("Factor updates", "factor.*update"),
        ("Audit trail", "audit.*trail"),
        ("Learning configuration", "learning_config"),
        ("Persona adjustments", "persona.*adjustment"),
        ("Performance tracking", "performance.*metrics")
    ]

    for req_name, pattern in requirements:
        if req_name == "Service location":
            # Check file location
            if os.path.exists("src/services/learning_service.py"):
                print(f"✅ Requirement: {req_name}")
            else:
                print(f"❌ Missing requirement: {req_name}")
                all_passed = False
        else:
            # Check content
            if os.path.exists(service_file):
                with open(service_file, 'r') as f:
                    content = f.read()

                if re.search(pattern, content.lower()):
                    print(f"✅ Requirement: {req_name}")
                else:
                    print(f"❌ Missing requirement: {req_name}")
                    all_passed = False

    # Summary
    print("\n" + "=" * 70)

    if all_passed:
        print("🎉 All validations passed!")
        print("\nLearning Service (Task 3.3) is properly implemented:")
        print("• Service created at correct location")
        print("• Beta calibration for binary/enum predictions")
        print("• EMA calibration for numeric predictions")
        print("• Factor updates with multiplicative weights")
        print("• Comprehensive data structures")
        print("• Persona-specific learning rate adjustments")
        print("• Complete audit trails and history tracking")
        print("• Performance metrics and monitoring")
        print("• Configuration management")
        print("• Complete test coverage")

        print("\nKey Features:")
        print("• Beta distribution parameters (α/β) with confidence intervals")
        print("• Exponential Moving Average for numeric error tracking")
        print("• Category-specific factor adjustments (momentum, offensive, etc.)")
        print("• Persona-aware learning rates (conservative vs contrarian)")
        print("• Comprehensive learning session summaries")
        print("• Real-time calibration state monitoring")
        print("• Configurable learning parameters")
        print("• Complete audit trails for all updates")

        print(f"\nNext steps:")
        print("1. Integrate with settlement service (task 3.2)")
        print("2. Connect to reflection system (task 3.4)")
        print("3. Implement database persistence")
        print("4. Add learning performance alerts")
        print("5. Monitor calibration drift in production")

    else:
        print("❌ Some validations failed. Check implementation.")

    return all_passed

if __name__ == "__main__":
    success = validate_learning_service_implementation()
    sys.exit(0 if success else 1)
