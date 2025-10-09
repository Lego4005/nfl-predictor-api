#!/usr/bin/env python3
"""
Integration Test Runner for NFL Expert Prediction System
Runs comprehensive integration tests for complete system flows.

Usage:
    python tests/run_integration_tests.py
    python tests/run_integration_tests.py --verbose
    python tests/run_integration_tests.py --test-class TestEndToEndPredictionGeneration
"""

import sys
import os
import subprocess
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_integration_tests(test_class=None, verbose=False, markers=None):
    """
    Run integration tests for the NFL Expert Prediction System

    Args:
        test_class: Specific test class to run (optional)
        verbose: Enable verbose output
        markers: Pytest markers to filter tests
    """
    setup_logging(verbose)

    # Base pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_nfl_expert_prediction_system_flows.py",
        "-v" if verbose else "-q",
        "--tb=short",
        "--disable-warnings"
    ]

    # Add specific test class if provided
    if test_class:
        cmd.append(f"-k {test_class}")

    # Add markers if provided
    if markers:
        cmd.extend(["-m", markers])

    # Add coverage if available
    try:
        import coverage
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
        logger.info("Coverage reporting enabled")
    except ImportError:
        logger.info("Coverage not available, running without coverage")

    logger.info(f"Running integration tests with command: {' '.join(cmd)}")

    try:
        # Run the tests
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to run integration tests: {e}")
        return 1

def run_specific_test_suites():
    """Run specific test suites individually for detailed analysis"""
    test_suites = [
        "TestEndToEndPredictionGeneration",
        "TestTrainingLoopValidation",
        "TestExpertPersonalityConsistency",
        "TestMemoryStorageAndRetrievalAccuracy",
        "TestSystemPerformanceAndScalability"
    ]

    results = {}

    for suite in test_suites:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running test suite: {suite}")
        logger.info(f"{'='*60}")

        result_code = run_integration_tests(test_class=suite, verbose=True)
        results[suite] = result_code

        if result_code == 0:
            logger.info(f"✅ {suite} - PASSED")
        else:
            logger.error(f"❌ {suite} - FAILED")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info(f"{'='*60}")

    passed = sum(1 for code in results.values() if code == 0)
    total = len(results)

    for suite, code in results.items():
        status = "PASSED" if code == 0 else "FAILED"
        logger.info(f"{suite}: {status}")

    logger.info(f"\nOverall: {passed}/{total} test suites passed")

    return 0 if passed == total else 1

def validate_test_environment():
    """Validate that the test environment is properly set up"""
    logger.info("Validating test environment...")

    # Check for required test dependencies
    required_packages = ['pytest', 'asyncio']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.error("Install with: pip install pytest pytest-asyncio")
        return False

    # Check for test files
    test_file = project_root / "tests" / "integration" / "test_nfl_expert_prediction_system_flows.py"
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return False

    logger.info("✅ Test environment validation passed")
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run NFL Expert Prediction System Integration Tests"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--test-class", "-k",
        help="Run specific test class"
    )
    parser.add_argument(
        "--markers", "-m",
        help="Run tests with specific markers (e.g., 'integration')"
    )
    parser.add_argument(
        "--suites",
        action="store_true",
        help="Run each test suite individually"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate test environment"
    )

    args = parser.parse_args()

    # Validate environment first
    if not validate_test_environment():
        return 1

    if args.validate_only:
        logger.info("Environment validation complete")
        return 0

    # Run tests
    if args.suites:
        return run_specific_test_suites()
    else:
        return run_integration_tests(
            test_class=args.test_class,
            verbose=args.verbose,
            markers=args.markers or "integration"
        )

if __name__ == "__main__":
    sys.exit(main())
