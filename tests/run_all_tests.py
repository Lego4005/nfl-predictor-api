#!/usr/bin/env python3
"""
Test Runner for NFL Expert Prediction System

Runs all unit tests and generates a comprehensive test report.
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_all_tests():
    """Run all unit tests with comprehensive reporting"""
    print("🧪 Running All Unit Tests for NFL Expert Prediction System")
    print("=" * 70)

    # Get test directory
    test_dir = Path(__file__).parent

    # Test files to run
    test_files = [
        "test_ai_expert_orchestrator.py",
        "test_performance_monitor.py",
        "test_error_handler.py",
        "test_graceful_degradation.py",
        "test_memory_cache.py"
    ]

    # Run tests with detailed output
    args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--durations=10",  # Show 10 slowest tests
        "--color=yes",  # Colored output
        "-x",  # Stop on first failure
    ]

    # Add test files
    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            args.append(str(test_path))
        else:
            print(f"⚠️ Warning: Test file {test_file} not found")

    print(f"Running {len([f for f in test_files if (test_dir / f).exists()])} test files...")
    print()

    # Run pytest
    exit_code = pytest.main(args)

    print()
    print("=" * 70)

    if exit_code == 0:
        print("🎉 ALL UNIT TESTS PASSED!")
        print("   All components are working correctly and ready for integration.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Review failed tests and fix issues before proceeding.")

    print("=" * 70)

    return exit_code == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
