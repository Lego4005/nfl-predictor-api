#!/usr/bin/env python3
"""
E2E Test Runner Script

This script provides various ways to run the E2E test suite with different
configurations and reporting options.
"""
import sys
import os
import argparse
import asyncio
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.config import (
    get_test_config,
    setup_test_logging,
    ensure_test_directories,
    cleanup_test_artifacts,
    test_environment
)
from tests.e2e.utils import ReportingHelpers

logger = logging.getLogger(__name__)


class TestRunner:
    """E2E Test Runner with various execution modes"""

    def __init__(self, args):
        self.args = args
        self.config = get_test_config(args.env)
        self.start_time = None
        self.end_time = None

    def setup_environment(self):
        """Setup test environment and directories"""
        setup_test_logging()
        ensure_test_directories()

        if self.args.clean:
            cleanup_test_artifacts()

        logger.info(f"Running tests in {self.args.env} environment")
        logger.info(f"Browser headless: {self.config.get('browser.headless')}")

    def build_pytest_command(self) -> List[str]:
        """Build pytest command with appropriate arguments"""
        cmd = ["python", "-m", "pytest"]

        # Test files/directories
        if self.args.tests:
            cmd.extend(self.args.tests)
        else:
            cmd.append("tests/e2e/")

        # Pytest options
        cmd.extend([
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            f"--maxfail={self.args.maxfail}",  # Stop after N failures
            "--capture=no" if self.args.no_capture else "--capture=sys",
            "--strict-markers",  # Strict marker checking
        ])

        # Parallel execution
        if self.args.workers > 1:
            cmd.extend(["-n", str(self.args.workers)])

        # Test markers
        if self.args.markers:
            cmd.extend(["-m", self.args.markers])

        # Test keywords
        if self.args.keyword:
            cmd.extend(["-k", self.args.keyword])

        # Reporting
        if self.args.html_report:
            cmd.extend([
                "--html=test-results/reports/report.html",
                "--self-contained-html"
            ])

        if self.args.junit_xml:
            cmd.extend([
                "--junit-xml=test-results/reports/junit.xml"
            ])

        if self.args.allure:
            cmd.extend([
                "--alluredir=test-results/allure-results"
            ])

        # Performance testing options
        if self.args.performance:
            cmd.extend([
                "-m", "performance",
                "--benchmark-sort=mean",
                "--benchmark-json=test-results/reports/benchmark.json"
            ])

        # Browser options
        if self.args.headed:
            os.environ["TEST_HEADLESS"] = "false"

        if self.args.slowmo:
            os.environ["TEST_SLOW_MO"] = str(self.args.slowmo)

        if self.args.video:
            os.environ["TEST_VIDEO"] = "true"

        # Environment variables
        os.environ.update({
            "TEST_ENV": self.args.env,
            "PYTHONPATH": str(project_root),
        })

        if self.args.debug:
            os.environ["DEBUG"] = "true"

        return cmd

    async def run_tests(self) -> int:
        """Run the E2E tests"""
        self.setup_environment()

        cmd = self.build_pytest_command()
        logger.info(f"Running command: {' '.join(cmd)}")

        self.start_time = datetime.now()

        if self.args.env in ["docker", "remote"]:
            # Use test environment context manager for complex setups
            async with test_environment(self.args.env) as config:
                return await self._execute_tests(cmd)
        else:
            return await self._execute_tests(cmd)

    async def _execute_tests(self, cmd: List[str]) -> int:
        """Execute the test command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=project_root
            )

            # Stream output in real-time
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                print(line.decode().rstrip())

            await process.wait()
            return_code = process.returncode

        except KeyboardInterrupt:
            logger.info("Test execution interrupted by user")
            return_code = 130
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return_code = 1

        self.end_time = datetime.now()

        # Generate reports
        if return_code == 0:
            await self.generate_reports()

        return return_code

    async def generate_reports(self):
        """Generate test reports and summaries"""
        logger.info("Generating test reports...")

        duration = self.end_time - self.start_time

        # Basic test summary
        summary = {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'environment': self.args.env,
            'configuration': {
                'headless': self.config.get('browser.headless'),
                'workers': self.args.workers,
                'markers': self.args.markers,
                'keyword': self.args.keyword,
            }
        }

        # Save test summary
        summary_file = Path("test-results/reports/test_summary.json")
        summary_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Test summary saved: {summary_file}")
        logger.info(f"Test execution completed in {duration}")

        # Generate performance summary if performance metrics exist
        metrics_dir = Path("test-results/metrics")
        if metrics_dir.exists():
            metrics_files = list(metrics_dir.glob("*.json"))
            if metrics_files:
                perf_summary = ReportingHelpers.generate_performance_summary(metrics_files)
                perf_file = Path("test-results/reports/performance_summary.json")

                with open(perf_file, 'w') as f:
                    json.dump(perf_summary, f, indent=2)

                logger.info(f"Performance summary saved: {perf_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NFL Predictor E2E Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests in local environment
  python tests/e2e/scripts/run_tests.py

  # Run smoke tests only
  python tests/e2e/scripts/run_tests.py -m smoke

  # Run with 4 parallel workers
  python tests/e2e/scripts/run_tests.py --workers 4

  # Run performance tests with reports
  python tests/e2e/scripts/run_tests.py --performance --html-report

  # Run specific test files
  python tests/e2e/scripts/run_tests.py tests/e2e/test_user_journey.py

  # Run in headed mode for debugging
  python tests/e2e/scripts/run_tests.py --headed --slowmo 1000 -k "login"

  # Run in Docker environment
  python tests/e2e/scripts/run_tests.py --env docker
        """
    )

    # Environment options
    parser.add_argument(
        "--env",
        choices=["local", "docker", "ci", "remote"],
        default="local",
        help="Test environment (default: local)"
    )

    # Test selection
    parser.add_argument(
        "tests",
        nargs="*",
        help="Specific test files or directories to run"
    )

    parser.add_argument(
        "-m", "--markers",
        help="Only run tests matching given mark expression"
    )

    parser.add_argument(
        "-k", "--keyword",
        help="Only run tests matching given keyword expression"
    )

    # Execution options
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1)"
    )

    parser.add_argument(
        "--maxfail",
        type=int,
        default=5,
        help="Stop after N failures (default: 5)"
    )

    parser.add_argument(
        "--no-capture",
        action="store_true",
        help="Don't capture stdout/stderr"
    )

    # Browser options
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode"
    )

    parser.add_argument(
        "--slowmo",
        type=int,
        help="Slow down operations by N milliseconds"
    )

    parser.add_argument(
        "--video",
        action="store_true",
        help="Record videos of test runs"
    )

    # Test types
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only"
    )

    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run smoke tests only"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )

    # Reporting options
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML report"
    )

    parser.add_argument(
        "--junit-xml",
        action="store_true",
        help="Generate JUnit XML report"
    )

    parser.add_argument(
        "--allure",
        action="store_true",
        help="Generate Allure report data"
    )

    # Utility options
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean old test artifacts before running"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Handle special test type flags
    if args.performance:
        args.markers = "performance"
    elif args.smoke:
        args.markers = "smoke"
    elif args.integration:
        args.markers = "integration"

    # Run tests
    runner = TestRunner(args)
    try:
        return_code = asyncio.run(runner.run_tests())
        sys.exit(return_code)
    except KeyboardInterrupt:
        logger.info("Test execution interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()