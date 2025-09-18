#!/usr/bin/env python3
"""
Performance baseline management for NFL Predictor API.
Creates and validates performance baselines for regression testing.
"""
import json
import argparse
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import sys

import psutil


class PerformanceBaseline:
    """Manage performance baselines for regression testing."""

    def __init__(self, baseline_file: Path = Path("performance-baseline.json")):
        self.baseline_file = baseline_file
        self.current_baselines = self.load_baselines()

    def load_baselines(self) -> Dict[str, Any]:
        """Load existing performance baselines."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load baselines: {e}")
        return {}

    def save_baselines(self):
        """Save baselines to file."""
        with open(self.baseline_file, 'w') as f:
            json.dump(self.current_baselines, f, indent=2, sort_keys=True)

    def create_baseline(self, test_category: str = "all") -> Dict[str, Any]:
        """Create new performance baseline by running tests."""
        print(f"Creating baseline for category: {test_category}")

        baseline_data = {
            "created_at": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "test_results": {}
        }

        # Run different test categories
        if test_category in ["all", "api"]:
            print("Running API performance tests...")
            api_results = self._run_api_benchmarks()
            baseline_data["test_results"]["api"] = api_results

        if test_category in ["all", "ml"]:
            print("Running ML performance tests...")
            ml_results = self._run_ml_benchmarks()
            baseline_data["test_results"]["ml"] = ml_results

        if test_category in ["all", "database"]:
            print("Running database performance tests...")
            db_results = self._run_database_benchmarks()
            baseline_data["test_results"]["database"] = db_results

        if test_category in ["all", "load"]:
            print("Running load test baseline...")
            load_results = self._run_load_test_baseline()
            baseline_data["test_results"]["load"] = load_results

        # Update current baselines
        self.current_baselines[test_category] = baseline_data
        self.save_baselines()

        return baseline_data

    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "memory_total": psutil.virtual_memory().total,
            "disk_usage": psutil.disk_usage('/').total,
            "python_version": sys.version,
            "platform": sys.platform
        }

    def _run_api_benchmarks(self) -> Dict[str, Any]:
        """Run API performance benchmarks."""
        cmd = [
            "pytest",
            "tests/performance/test_api_performance.py",
            "--benchmark-only",
            "--benchmark-json=temp-api-benchmark.json",
            "--benchmark-sort=mean",
            "-v"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Load benchmark results
            benchmark_file = Path("temp-api-benchmark.json")
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)

                # Extract key metrics
                api_metrics = {}
                for benchmark in benchmark_data.get("benchmarks", []):
                    test_name = benchmark["name"].replace("test_", "")
                    api_metrics[test_name] = {
                        "mean_time": benchmark["stats"]["mean"],
                        "median_time": benchmark["stats"]["median"],
                        "min_time": benchmark["stats"]["min"],
                        "max_time": benchmark["stats"]["max"],
                        "stddev": benchmark["stats"]["stddev"],
                        "iterations": benchmark["stats"]["iterations"]
                    }

                # Cleanup
                benchmark_file.unlink()
                return api_metrics

        except subprocess.TimeoutExpired:
            print("API benchmarks timed out")
        except Exception as e:
            print(f"API benchmark error: {e}")

        return {}

    def _run_ml_benchmarks(self) -> Dict[str, Any]:
        """Run ML model performance benchmarks."""
        cmd = [
            "pytest",
            "tests/performance/test_ml_performance.py",
            "--benchmark-only",
            "--benchmark-json=temp-ml-benchmark.json",
            "-v"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            # Load benchmark results
            benchmark_file = Path("temp-ml-benchmark.json")
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)

                ml_metrics = {}
                for benchmark in benchmark_data.get("benchmarks", []):
                    test_name = benchmark["name"].replace("test_", "")
                    ml_metrics[test_name] = {
                        "mean_time": benchmark["stats"]["mean"],
                        "median_time": benchmark["stats"]["median"],
                        "memory_peak": benchmark.get("memory_peak", 0),
                        "iterations": benchmark["stats"]["iterations"]
                    }

                # Cleanup
                benchmark_file.unlink()
                return ml_metrics

        except Exception as e:
            print(f"ML benchmark error: {e}")

        return {}

    def _run_database_benchmarks(self) -> Dict[str, Any]:
        """Run database performance benchmarks."""
        cmd = [
            "pytest",
            "tests/performance/test_database_performance.py",
            "--benchmark-only",
            "--benchmark-json=temp-db-benchmark.json",
            "-v"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

            # Load benchmark results
            benchmark_file = Path("temp-db-benchmark.json")
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)

                db_metrics = {}
                for benchmark in benchmark_data.get("benchmarks", []):
                    test_name = benchmark["name"].replace("test_", "")
                    db_metrics[test_name] = {
                        "mean_time": benchmark["stats"]["mean"],
                        "median_time": benchmark["stats"]["median"],
                        "query_count": benchmark.get("query_count", 1),
                        "iterations": benchmark["stats"]["iterations"]
                    }

                # Cleanup
                benchmark_file.unlink()
                return db_metrics

        except Exception as e:
            print(f"Database benchmark error: {e}")

        return {}

    def _run_load_test_baseline(self) -> Dict[str, Any]:
        """Run load test to establish baseline."""
        cmd = [
            "locust",
            "-f", "tests/load/locustfile.py",
            "--headless",
            "--users", "10",
            "--spawn-rate", "2",
            "--run-time", "60s",
            "--host", "http://localhost:8000",
            "--csv", "baseline-load-test"
        ]

        try:
            # Start the test server
            server_cmd = ["python", "main.py"]
            server_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            import time
            time.sleep(10)

            # Run load test
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Parse results
            load_metrics = {}
            csv_files = [
                "baseline-load-test_stats.csv",
                "baseline-load-test_failures.csv"
            ]

            for csv_file in csv_files:
                if Path(csv_file).exists():
                    # Parse CSV and extract metrics
                    # This is a simplified version - you'd want more robust CSV parsing
                    load_metrics[csv_file.replace("baseline-load-test_", "").replace(".csv", "")] = {
                        "file": csv_file,
                        "timestamp": datetime.now().isoformat()
                    }

            # Cleanup
            server_process.terminate()
            for csv_file in csv_files:
                csv_path = Path(csv_file)
                if csv_path.exists():
                    csv_path.unlink()

            return load_metrics

        except Exception as e:
            print(f"Load test baseline error: {e}")
            return {}

    def validate_performance(self, current_results: Dict[str, Any],
                           tolerance: float = 0.20) -> Dict[str, Any]:
        """Validate current performance against baseline."""
        validation_results = {
            "passed": True,
            "regressions": [],
            "improvements": [],
            "summary": {}
        }

        for category, baseline_data in self.current_baselines.items():
            if category not in current_results:
                continue

            category_regressions = self._compare_category_performance(
                baseline_data["test_results"],
                current_results[category],
                tolerance
            )

            if category_regressions["regressions"]:
                validation_results["passed"] = False
                validation_results["regressions"].extend(category_regressions["regressions"])

            validation_results["improvements"].extend(category_regressions["improvements"])

        return validation_results

    def _compare_category_performance(self, baseline: Dict[str, Any],
                                    current: Dict[str, Any],
                                    tolerance: float) -> Dict[str, Any]:
        """Compare performance for a specific category."""
        result = {
            "regressions": [],
            "improvements": []
        }

        for test_name, baseline_metrics in baseline.items():
            if test_name not in current:
                continue

            current_metrics = current[test_name]

            # Compare mean execution time
            if "mean_time" in baseline_metrics and "mean_time" in current_metrics:
                baseline_time = baseline_metrics["mean_time"]
                current_time = current_metrics["mean_time"]
                change_ratio = (current_time - baseline_time) / baseline_time

                if change_ratio > tolerance:
                    result["regressions"].append({
                        "test": test_name,
                        "metric": "mean_time",
                        "baseline": baseline_time,
                        "current": current_time,
                        "change_percent": change_ratio * 100
                    })
                elif change_ratio < -tolerance:
                    result["improvements"].append({
                        "test": test_name,
                        "metric": "mean_time",
                        "baseline": baseline_time,
                        "current": current_time,
                        "improvement_percent": abs(change_ratio) * 100
                    })

        return result

    def generate_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate performance validation report."""
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE VALIDATION REPORT")
        report.append("=" * 60)

        status = "✅ PASSED" if validation_results["passed"] else "❌ FAILED"
        report.append(f"Overall Status: {status}")
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append("")

        # Regressions
        if validation_results["regressions"]:
            report.append("Performance Regressions:")
            report.append("-" * 30)
            for regression in validation_results["regressions"]:
                report.append(
                    f"  {regression['test']}: {regression['change_percent']:+.1f}% "
                    f"({regression['baseline']:.3f}s → {regression['current']:.3f}s)"
                )
            report.append("")

        # Improvements
        if validation_results["improvements"]:
            report.append("Performance Improvements:")
            report.append("-" * 32)
            for improvement in validation_results["improvements"]:
                report.append(
                    f"  {improvement['test']}: -{improvement['improvement_percent']:.1f}% "
                    f"({improvement['baseline']:.3f}s → {improvement['current']:.3f}s)"
                )
            report.append("")

        # Summary
        regression_count = len(validation_results["regressions"])
        improvement_count = len(validation_results["improvements"])

        report.append(f"Summary: {regression_count} regressions, {improvement_count} improvements")

        return "\n".join(report)


def main():
    """Main entry point for performance baseline management."""
    parser = argparse.ArgumentParser(
        description="Manage performance baselines for regression testing"
    )
    parser.add_argument(
        "action",
        choices=["create", "validate", "report"],
        help="Action to perform"
    )
    parser.add_argument(
        "--category",
        default="all",
        choices=["all", "api", "ml", "database", "load"],
        help="Test category to process"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.20,
        help="Performance tolerance (default: 20%)"
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=Path("performance-baseline.json"),
        help="Baseline file path"
    )
    parser.add_argument(
        "--current-results",
        type=Path,
        help="Current test results file (for validation)"
    )

    args = parser.parse_args()

    # Initialize baseline manager
    baseline_manager = PerformanceBaseline(args.baseline_file)

    if args.action == "create":
        print(f"Creating performance baseline for {args.category}...")
        baseline_data = baseline_manager.create_baseline(args.category)
        print(f"✅ Baseline created with {len(baseline_data.get('test_results', {}))} test categories")

    elif args.action == "validate":
        if not args.current_results:
            print("❌ Current results file required for validation")
            sys.exit(1)

        if not args.current_results.exists():
            print(f"❌ Current results file not found: {args.current_results}")
            sys.exit(1)

        # Load current results
        with open(args.current_results, 'r') as f:
            current_results = json.load(f)

        # Validate performance
        validation_results = baseline_manager.validate_performance(
            current_results,
            args.tolerance
        )

        # Generate report
        report = baseline_manager.generate_report(validation_results)
        print(report)

        # Exit with appropriate code
        if not validation_results["passed"]:
            sys.exit(1)

    elif args.action == "report":
        # Generate baseline report
        if baseline_manager.current_baselines:
            print("Current Performance Baselines:")
            print("-" * 40)
            for category, data in baseline_manager.current_baselines.items():
                created_at = data.get("created_at", "Unknown")
                test_count = len(data.get("test_results", {}))
                print(f"  {category}: {test_count} tests (created: {created_at})")
        else:
            print("No performance baselines found. Run 'create' action first.")


if __name__ == "__main__":
    main()