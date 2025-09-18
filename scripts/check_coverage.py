#!/usr/bin/env python3
"""
Coverage checking script for pre-commit hooks and CI/CD.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import xml.etree.ElementTree as ET


class CoverageChecker:
    """Check test coverage and enforce thresholds."""

    def __init__(self, threshold: float = 80.0, config_file: Optional[Path] = None):
        self.threshold = threshold
        self.config_file = config_file or Path("pytest.ini")
        self.coverage_file = Path("coverage.xml")
        self.html_dir = Path("htmlcov")

    def run_coverage_check(self) -> Dict[str, Any]:
        """Run coverage analysis and return results."""
        results = {
            "overall_coverage": 0.0,
            "file_coverage": {},
            "missing_files": [],
            "below_threshold": [],
            "passed": False,
            "errors": []
        }

        try:
            # Run pytest with coverage
            cmd = [
                "pytest",
                "tests/unit/",
                "--cov=src",
                "--cov-report=xml:coverage.xml",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
                f"--cov-fail-under={self.threshold}",
                "--tb=no",
                "-q"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )

            if result.returncode == 0:
                results["passed"] = True

            # Parse coverage XML
            if self.coverage_file.exists():
                coverage_data = self._parse_coverage_xml()
                results.update(coverage_data)
            else:
                results["errors"].append("Coverage XML file not found")

        except subprocess.TimeoutExpired:
            results["errors"].append("Coverage check timed out")
        except Exception as e:
            results["errors"].append(f"Coverage check failed: {e}")

        return results

    def _parse_coverage_xml(self) -> Dict[str, Any]:
        """Parse coverage XML file and extract metrics."""
        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()

            # Overall coverage
            overall_coverage = float(root.attrib.get("line-rate", 0)) * 100

            # File-level coverage
            file_coverage = {}
            below_threshold = []

            for package in root.findall(".//package"):
                for class_elem in package.findall(".//class"):
                    filename = class_elem.attrib.get("filename", "")
                    if filename:
                        line_rate = float(class_elem.attrib.get("line-rate", 0)) * 100
                        file_coverage[filename] = line_rate

                        if line_rate < self.threshold:
                            below_threshold.append({
                                "file": filename,
                                "coverage": line_rate,
                                "threshold": self.threshold
                            })

            return {
                "overall_coverage": overall_coverage,
                "file_coverage": file_coverage,
                "below_threshold": below_threshold
            }

        except Exception as e:
            return {"errors": [f"Failed to parse coverage XML: {e}"]}

    def check_critical_files(self) -> List[str]:
        """Check coverage for critical files that must have high coverage."""
        critical_files = [
            "src/api/predictions.py",
            "src/ml/models.py",
            "src/database/operations.py",
            "src/services/websocket.py"
        ]

        missing_coverage = []
        for file_path in critical_files:
            if Path(file_path).exists():
                # Check if file is covered in tests
                coverage = self._get_file_coverage(file_path)
                if coverage < 90:  # Critical files need 90%+ coverage
                    missing_coverage.append(f"{file_path}: {coverage:.1f}%")

        return missing_coverage

    def _get_file_coverage(self, file_path: str) -> float:
        """Get coverage percentage for a specific file."""
        try:
            cmd = ["coverage", "report", "--show-missing", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Parse coverage output
            lines = result.stdout.split('\n')
            for line in lines:
                if file_path in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[3].replace('%', '')
                        return float(coverage_str)

        except Exception:
            pass

        return 0.0

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable coverage report."""
        report = []
        report.append("=" * 60)
        report.append("COVERAGE REPORT")
        report.append("=" * 60)

        # Overall status
        status = "✅ PASSED" if results["passed"] else "❌ FAILED"
        report.append(f"Status: {status}")
        report.append(f"Overall Coverage: {results['overall_coverage']:.1f}%")
        report.append(f"Threshold: {self.threshold}%")
        report.append("")

        # Files below threshold
        if results["below_threshold"]:
            report.append("Files Below Threshold:")
            report.append("-" * 30)
            for item in results["below_threshold"]:
                report.append(f"  {item['file']}: {item['coverage']:.1f}%")
            report.append("")

        # Critical file coverage
        critical_issues = self.check_critical_files()
        if critical_issues:
            report.append("Critical Files with Low Coverage:")
            report.append("-" * 40)
            for issue in critical_issues:
                report.append(f"  {issue}")
            report.append("")

        # Errors
        if results["errors"]:
            report.append("Errors:")
            report.append("-" * 10)
            for error in results["errors"]:
                report.append(f"  {error}")
            report.append("")

        # Recommendations
        if not results["passed"]:
            report.append("Recommendations:")
            report.append("-" * 15)
            report.append("  1. Add more unit tests for uncovered code")
            report.append("  2. Focus on critical business logic")
            report.append("  3. Review test quality and effectiveness")
            report.append("  4. Consider integration tests for complex flows")

        return "\n".join(report)

    def save_results(self, results: Dict[str, Any], output_file: Path):
        """Save coverage results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)


def main():
    """Main entry point for coverage checking."""
    parser = argparse.ArgumentParser(
        description="Check test coverage and enforce thresholds"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Coverage threshold percentage (default: 80.0)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for JSON results"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if coverage below threshold"
    )

    args = parser.parse_args()

    # Initialize coverage checker
    checker = CoverageChecker(threshold=args.threshold)

    # Run coverage check
    print("Running coverage analysis...")
    results = checker.run_coverage_check()

    # Generate report
    if args.report:
        report = checker.generate_report(results)
        print(report)

    # Save results
    if args.output:
        checker.save_results(results, args.output)
        print(f"Results saved to {args.output}")

    # Summary output
    if results["passed"]:
        print(f"✅ Coverage check passed: {results['overall_coverage']:.1f}%")
    else:
        print(f"❌ Coverage check failed: {results['overall_coverage']:.1f}%")
        if results["below_threshold"]:
            print(f"   {len(results['below_threshold'])} files below threshold")

    # Exit with appropriate code
    if args.strict and not results["passed"]:
        sys.exit(1)
    elif results["errors"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()