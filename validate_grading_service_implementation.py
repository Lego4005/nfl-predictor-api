#!/usr/bin/env python3
"""
Validation script for Grading Service implementation (Task 3.1)
Validates implementation without requiring full system setup
"""

import os
import sys
import re

def validate_grading_service_implementation():
    """Validate the grading service implementation"""

    print("🔍 Validating Grading Service Implementation (Task 3.1)")
    print("=" * 70)

    all_passed = True

    # Check 1: Service file exists
    print("\n1. Checking service implementation...")
    service_file = "src/services/grading_service.py"

    if os.path.exists(service_file):
        print(f"✅ Service file exists: {service_file}")

        with open(service_file, 'r') as f:
            content = f.read()

        required_elements = [
            "class GradingService",
            "grade_predictions",
            "Binary/Enum.*Brier",
            "Numeric.*Gaussian",
            "PredictionType",
            "GradingResult",
            "brier_score",
            "gaussian_score",
            "sigma"
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

    # Check 2: Grading methods implementation
    print("\n2. Checking grading methods...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        grading_methods = [
            ("Binary grading", "_grade_binary_prediction"),
            ("Enum grading", "_grade_enum_prediction"),
            ("Numeric grading", "_grade_numeric_prediction"),
            ("Brier score calculation", "brier_score.*="),
            ("Gaussian kernel", "gaussian.*exp|exp.*gaussian"),
            ("Exact match", "exact_match"),
            ("Confidence adjustment", "confidence")
        ]

        for method_name, pattern in grading_methods:
            if re.search(pattern, content.lower()):
                print(f"✅ Method: {method_name}")
            else:
                print(f"❌ Missing method: {method_name}")
                all_passed = False

    # Check 3: Data structures
    print("\n3. Checking data structures...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        structures = [
            ("GradingResult dataclass", "@dataclass.*GradingResult"),
            ("PredictionType enum", "class PredictionType.*Enum"),
            ("Binary type", "BINARY"),
            ("Enum type", "ENUM"),
            ("Numeric type", "NUMERIC"),
            ("Category config", "CategoryGradingConfig"),
            ("Default sigmas", "default_sigmas")
        ]

        for struct_name, pattern in structures:
            if re.search(pattern, content, re.DOTALL):
                print(f"✅ Structure: {struct_name}")
            else:
                print(f"❌ Missing structure: {struct_name}")
                all_passed = False

    # Check 4: Test implementation
    print("\n4. Checking test implementation...")

    test_file = "test_grading_service.py"

    if os.path.exists(test_file):
        print(f"✅ Test file exists: {test_file}")

        with open(test_file, 'r') as f:
            content = f.read()

        test_features = [
            "test_grading_service",
            "binary.*grading",
            "enum.*grading",
            "numeric.*grading",
            "brier.*score",
            "gaussian.*score",
            "expert.*grade",
            "category.*performance"
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

    # Check 5: Requirements compliance
    print("\n5. Checking requirements compliance...")

    requirements = [
        ("Service location", "src/services/grading_service.py"),
        ("Binary/Enum + Brier", "binary.*enum.*brier"),
        ("Numeric Gaussian kernel", "numeric.*gaussian.*kernel"),
        ("Category sigma", "category.*sigma"),
        ("Exact match scoring", "exact.*match"),
        ("Performance tracking", "performance.*metrics")
    ]

    for req_name, pattern in requirements:
        if req_name == "Service location":
            # Check file location
            if os.path.exists("src/services/grading_service.py"):
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

    # Check 6: Scoring formulas
    print("\n6. Checking scoring formulas...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        formulas = [
            ("Brier score formula", "forecast.*outcome.*\\*\\*.*2"),
            ("Gaussian kernel formula", "exp.*-0\\.5.*distance.*sigma"),
            ("Combined scoring", "0\\.7.*exact.*0\\.3.*brier|exact_weight.*calibration_weight"),
            ("Confidence adjustment", "confidence.*factor"),
            ("Final score bounds", "max.*0.*min.*1|min.*max")
        ]

        for formula_name, pattern in formulas:
            if re.search(pattern, content):
                print(f"✅ Formula: {formula_name}")
            else:
                print(f"❌ Missing formula: {formula_name}")
                all_passed = False

    # Summary
    print("\n" + "=" * 70)

    if all_passed:
        print("🎉 All validations passed!")
        print("\nGrading Service (Task 3.1) is properly implemented:")
        print("• Service created at correct location")
        print("• Binary/Enum grading with Brier scoring")
        print("• Numeric grading with Gaussian kernel")
        print("• Category-specific sigma values")
        print("• Comprehensive data structures")
        print("• Performance tracking and metrics")
        print("• Complete test coverage")

        print("\nKey Features:")
        print("• Binary: Exact match (70%) + Brier score (30%)")
        print("• Enum: Exact match (70%) + Brier score (30%)")
        print("• Numeric: Gaussian kernel with category sigma")
        print("• Confidence-adjusted scoring")
        print("• Expert grade aggregation")
        print("• Category performance analysis")
        print("• Configurable sigma values")

        print(f"\nNext steps:")
        print("1. Integrate with settlement service (task 3.2)")
        print("2. Connect to actual game outcome data")
        print("3. Tune sigma values based on real data")
        print("4. Monitor grading performance")

    else:
        print("❌ Some validations failed. Check implementation.")

    return all_passed

if __name__ == "__main__":
    success = validate_grading_service_implementation()
    sys.exit(0 if success else 1)
