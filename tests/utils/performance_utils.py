"""
Performance testing utilities and benchmarking tools.
"""
import time
import asyncio
import statistics
import threading
from contextlib import contextmanager, asynccontextmanager
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator, Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil
import json
import csv
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    memory_peak_mb: float
    cpu_percent: float
    response_times: List[float] = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0
    additional_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_requests(self) -> int:
        """Total number of requests made."""
        return self.success_count + self.error_count

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100

    @property
    def memory_delta_mb(self) -> float:
        """Memory delta in MB."""
        return self.memory_after_mb - self.memory_before_mb

    @property
    def avg_response_time_ms(self) -> float:
        """Average response time in milliseconds."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times) * 1000

    @property
    def p95_response_time_ms(self) -> float:
        """95th percentile response time in milliseconds."""
        if not self.response_times:
            return 0.0
        return np.percentile(self.response_times, 95) * 1000

    @property
    def p99_response_time_ms(self) -> float:
        """99th percentile response time in milliseconds."""
        if not self.response_times:
            return 0.0
        return np.percentile(self.response_times, 99) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'test_name': self.test_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_ms': self.duration_ms,
            'memory_before_mb': self.memory_before_mb,
            'memory_after_mb': self.memory_after_mb,
            'memory_peak_mb': self.memory_peak_mb,
            'memory_delta_mb': self.memory_delta_mb,
            'cpu_percent': self.cpu_percent,
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'avg_response_time_ms': self.avg_response_time_ms,
            'p95_response_time_ms': self.p95_response_time_ms,
            'p99_response_time_ms': self.p99_response_time_ms,
            **self.additional_metrics
        }


class PerformanceMonitor:
    """Monitor system performance during tests."""

    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.monitoring = False
        self.metrics_thread = None
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.peak_memory = 0.0

    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.cpu_samples.clear()
        self.memory_samples.clear()
        self.peak_memory = 0.0

        self.metrics_thread = threading.Thread(target=self._monitor_loop)
        self.metrics_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.metrics_thread:
            self.metrics_thread.join()

    def _monitor_loop(self):
        """Monitor system resources in background thread."""
        process = psutil.Process()

        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = process.cpu_percent()
                self.cpu_samples.append(cpu_percent)

                # Memory usage
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_samples.append(memory_mb)

                # Track peak memory
                if memory_mb > self.peak_memory:
                    self.peak_memory = memory_mb

                time.sleep(self.sample_interval)

            except Exception:
                # Process might have ended
                break

    def get_average_cpu(self) -> float:
        """Get average CPU usage."""
        return statistics.mean(self.cpu_samples) if self.cpu_samples else 0.0

    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0


class PerformanceProfiler:
    """Profile performance of test functions."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.monitor = PerformanceMonitor()
        self.start_time = None
        self.end_time = None
        self.initial_memory = None
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.additional_metrics: Dict[str, Any] = {}

    def start(self):
        """Start performance profiling."""
        self.start_time = datetime.now()
        self.initial_memory = self.monitor.get_current_memory_mb()
        self.monitor.start_monitoring()

    def stop(self) -> PerformanceMetrics:
        """Stop profiling and return metrics."""
        self.end_time = datetime.now()
        self.monitor.stop_monitoring()

        duration = (self.end_time - self.start_time).total_seconds() * 1000  # ms
        final_memory = self.monitor.get_current_memory_mb()

        return PerformanceMetrics(
            test_name=self.test_name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_ms=duration,
            memory_before_mb=self.initial_memory,
            memory_after_mb=final_memory,
            memory_peak_mb=self.monitor.peak_memory,
            cpu_percent=self.monitor.get_average_cpu(),
            response_times=self.response_times.copy(),
            success_count=self.success_count,
            error_count=self.error_count,
            additional_metrics=self.additional_metrics.copy()
        )

    def record_response_time(self, response_time_seconds: float):
        """Record a response time."""
        self.response_times.append(response_time_seconds)

    def record_success(self):
        """Record a successful operation."""
        self.success_count += 1

    def record_error(self):
        """Record an error."""
        self.error_count += 1

    def add_metric(self, key: str, value: Any):
        """Add additional metric."""
        self.additional_metrics[key] = value


@contextmanager
def performance_test(test_name: str) -> Generator[PerformanceProfiler, None, None]:
    """Context manager for performance testing."""
    profiler = PerformanceProfiler(test_name)
    profiler.start()
    try:
        yield profiler
    finally:
        metrics = profiler.stop()
        # Could log or store metrics here
        print(f"Performance Test '{test_name}' completed:")
        print(f"  Duration: {metrics.duration_ms:.1f}ms")
        print(f"  Memory Delta: {metrics.memory_delta_mb:+.1f}MB")
        print(f"  Average CPU: {metrics.cpu_percent:.1f}%")
        if metrics.response_times:
            print(f"  Avg Response Time: {metrics.avg_response_time_ms:.1f}ms")
            print(f"  P95 Response Time: {metrics.p95_response_time_ms:.1f}ms")


class LoadTestRunner:
    """Advanced load testing utility."""

    def __init__(self, name: str = "Load Test"):
        self.name = name
        self.results: List[Dict[str, Any]] = []

    async def run_concurrent_requests(self,
                                    request_func: Callable,
                                    concurrent_users: int = 10,
                                    requests_per_user: int = 10,
                                    ramp_up_time: float = 0.0) -> Dict[str, Any]:
        """Run concurrent requests with configurable load pattern."""

        async def user_session(user_id: int):
            """Simulate a user session."""
            session_results = {
                'user_id': user_id,
                'requests': [],
                'total_time': 0.0,
                'errors': 0
            }

            # Ramp up delay
            if ramp_up_time > 0:
                delay = (user_id / concurrent_users) * ramp_up_time
                await asyncio.sleep(delay)

            session_start = time.perf_counter()

            for request_id in range(requests_per_user):
                request_start = time.perf_counter()
                try:
                    await request_func()
                    success = True
                except Exception as e:
                    success = False
                    session_results['errors'] += 1

                request_end = time.perf_counter()
                request_time = request_end - request_start

                session_results['requests'].append({
                    'request_id': request_id,
                    'response_time': request_time,
                    'success': success,
                    'timestamp': request_start
                })

            session_end = time.perf_counter()
            session_results['total_time'] = session_end - session_start
            return session_results

        # Run all user sessions concurrently
        test_start = time.perf_counter()
        tasks = [user_session(user_id) for user_id in range(concurrent_users)]
        session_results = await asyncio.gather(*tasks)
        test_end = time.perf_counter()

        # Aggregate results
        total_requests = concurrent_users * requests_per_user
        successful_requests = 0
        failed_requests = 0
        all_response_times = []

        for session in session_results:
            for request in session['requests']:
                if request['success']:
                    successful_requests += 1
                    all_response_times.append(request['response_time'])
                else:
                    failed_requests += 1

        # Calculate metrics
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0

        results = {
            'test_name': self.name,
            'concurrent_users': concurrent_users,
            'requests_per_user': requests_per_user,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': success_rate,
            'total_test_time': test_end - test_start,
            'requests_per_second': total_requests / (test_end - test_start),
        }

        if all_response_times:
            results.update({
                'avg_response_time': statistics.mean(all_response_times),
                'min_response_time': min(all_response_times),
                'max_response_time': max(all_response_times),
                'median_response_time': statistics.median(all_response_times),
                'p95_response_time': np.percentile(all_response_times, 95),
                'p99_response_time': np.percentile(all_response_times, 99),
                'response_time_std': statistics.stdev(all_response_times) if len(all_response_times) > 1 else 0
            })

        self.results.append(results)
        return results


class PerformanceBaseline:
    """Manage performance baselines and regression detection."""

    def __init__(self, baseline_file: Path = None):
        self.baseline_file = baseline_file or Path("performance_baseline.json")
        self.baselines = self._load_baselines()

    def _load_baselines(self) -> Dict[str, Dict[str, float]]:
        """Load performance baselines from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_baselines(self):
        """Save baselines to file."""
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baselines, f, indent=2)

    def set_baseline(self, test_name: str, metrics: PerformanceMetrics):
        """Set performance baseline for a test."""
        self.baselines[test_name] = {
            'duration_ms': metrics.duration_ms,
            'memory_delta_mb': metrics.memory_delta_mb,
            'avg_response_time_ms': metrics.avg_response_time_ms,
            'p95_response_time_ms': metrics.p95_response_time_ms,
            'cpu_percent': metrics.cpu_percent,
            'timestamp': metrics.start_time.isoformat()
        }
        self.save_baselines()

    def check_regression(self, test_name: str, metrics: PerformanceMetrics,
                        tolerance: float = 0.2) -> Dict[str, Any]:
        """Check for performance regression."""
        if test_name not in self.baselines:
            return {'has_regression': False, 'reason': 'No baseline found'}

        baseline = self.baselines[test_name]
        regressions = []

        # Check duration
        duration_ratio = metrics.duration_ms / baseline['duration_ms']
        if duration_ratio > (1 + tolerance):
            regressions.append(f"Duration increased by {(duration_ratio - 1) * 100:.1f}%")

        # Check memory usage
        if metrics.memory_delta_mb > baseline['memory_delta_mb'] * (1 + tolerance):
            regressions.append("Memory usage increased significantly")

        # Check response times
        if metrics.avg_response_time_ms > baseline['avg_response_time_ms'] * (1 + tolerance):
            regressions.append("Average response time increased significantly")

        if metrics.p95_response_time_ms > baseline['p95_response_time_ms'] * (1 + tolerance):
            regressions.append("P95 response time increased significantly")

        return {
            'has_regression': len(regressions) > 0,
            'regressions': regressions,
            'baseline': baseline,
            'current': metrics.to_dict()
        }


class PerformanceReporter:
    """Generate performance test reports."""

    @staticmethod
    def generate_csv_report(metrics_list: List[PerformanceMetrics],
                          output_file: Path):
        """Generate CSV performance report."""
        if not metrics_list:
            return

        fieldnames = list(metrics_list[0].to_dict().keys())

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for metrics in metrics_list:
                writer.writerow(metrics.to_dict())

    @staticmethod
    def generate_html_report(metrics_list: List[PerformanceMetrics],
                           output_file: Path):
        """Generate HTML performance report."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .regression { background-color: #ffebee; }
                .improvement { background-color: #e8f5e8; }
                .summary { background-color: #f5f5f5; padding: 15px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <h1>Performance Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {total_tests}</p>
                <p>Generated: {timestamp}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Duration (ms)</th>
                        <th>Memory Delta (MB)</th>
                        <th>Avg Response Time (ms)</th>
                        <th>P95 Response Time (ms)</th>
                        <th>Success Rate (%)</th>
                        <th>CPU Usage (%)</th>
                    </tr>
                </thead>
                <tbody>
        """.format(
            total_tests=len(metrics_list),
            timestamp=datetime.now().isoformat()
        )

        for metrics in metrics_list:
            html_content += f"""
                    <tr>
                        <td>{metrics.test_name}</td>
                        <td>{metrics.duration_ms:.1f}</td>
                        <td>{metrics.memory_delta_mb:+.1f}</td>
                        <td>{metrics.avg_response_time_ms:.1f}</td>
                        <td>{metrics.p95_response_time_ms:.1f}</td>
                        <td>{metrics.success_rate:.1f}</td>
                        <td>{metrics.cpu_percent:.1f}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """

        with open(output_file, 'w') as f:
            f.write(html_content)


# Utility functions for common performance tests
async def benchmark_api_endpoint(client, endpoint: str,
                               concurrent_requests: int = 10,
                               total_requests: int = 100) -> Dict[str, Any]:
    """Benchmark an API endpoint."""
    load_tester = LoadTestRunner(f"Benchmark {endpoint}")

    async def make_request():
        response = await client.get(endpoint)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

    return await load_tester.run_concurrent_requests(
        request_func=make_request,
        concurrent_users=concurrent_requests,
        requests_per_user=total_requests // concurrent_requests
    )


def assert_performance_regression(metrics: PerformanceMetrics,
                                baseline: PerformanceBaseline,
                                tolerance: float = 0.2):
    """Assert no performance regression occurred."""
    regression_check = baseline.check_regression(
        metrics.test_name,
        metrics,
        tolerance
    )

    if regression_check['has_regression']:
        raise AssertionError(
            f"Performance regression detected in {metrics.test_name}: "
            f"{', '.join(regression_check['regressions'])}"
        )


# Export utilities
__all__ = [
    'PerformanceMetrics',
    'PerformanceMonitor',
    'PerformanceProfiler',
    'performance_test',
    'LoadTestRunner',
    'PerformanceBaseline',
    'PerformanceReporter',
    'benchmark_api_endpoint',
    'assert_performance_regression'
]