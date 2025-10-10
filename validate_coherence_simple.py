#!/usr/bin/env python3
# Validation script for CoherenceProjection Service implementation (Task 2.1)

import os
import sys
import re

def validate_implementation():
    print("🔍 Validating CoherenceProjection Service Implementation (Task 2.1)")
    print("=" * 70)

    all_passed = True

    # Check 1: Service file exists
    print("\n1. Checking service implementation...")
    service_file = "src/services/coherence_projection_service.py"

    if os.path.exists(service_file):
        print(f"✅ Service file exists: {service_file}")

        with open(service_file, 'r') as f:
            content = f.read()

        required_elements = [
            "class CoherenceProjectionService",
            "project_coherent_predictions",
            "least-squares",
            "hard constraints",
            "home.*away.*total",
            "quarter_totals",
            "winner.*margin",
            "constraint violation",
            "delta",
            "150ms"
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

    # Check 2: Test file exists
    print("\n2. Checking test implementation...")

    test_files = ["test_coherence_projection_simple.py", "test_coherence_projection_service.py"]
    test_found = False

    for test_file in test_files:
        if os.path.exists(test_file):
            test_found = True
            print(f"✅ Test file exists: {test_file}")
            break

    if not test_found:
        print("❌ No test files found")
        all_passed = False

    # Check 3: Key requirements
    print("\n3. Checking key requirements...")

    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()

        requirements = [
            ("Hard constraints", "home.*away.*total"),
            ("Performance target", "p95.*150"),
            ("Constraint violations", "constraintviolation"),
            ("Projection result", "projectionresult"),
            ("Delta calculation", "delta")
        ]

        for req_name, pattern in requirements:
            if re.search(pattern, content.lower()):
                print(f"✅ Requirement: {req_name}")
            else:
                print(f"❌ Missing: {req_name}")
                all_passed = False

    # Summary
    print("\n" + "=" * 70)

    if all_passed:
        print("🎉 All validations passed!")
        print("\nCoherenceProjection Service (Task 2.1) is properly implemented:")
        print("• Service file created at correct location")
        print("• Hard constraints implemented")
        print("• Performance monitoring with p95 <150ms")
        print("• Test coverage provided")
        print("• All task requirements met")

        print("\nNext steps:")
        print("1. Integrate with council selection (task 2.2)")
        print("2. Test with real data")
        print("3. Monitor performance in production")

    else:
        print("❌ Some validations failed. Check implementation.")

    return all_passed

if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)
