#!/usr/bin/env python3
"""
Memory Leak Detection and CPU Usage Monitoring for Load Tests

This module provides comprehensive memory leak detection and system resource
monitoring during load testing operations.

Features:
- Real-time memory usage tracking
- Memory leak detection algorithms
- CPU usage profiling
- Object reference tracking
- Resource utilization alerts
- Performance trend analysis

Usage:
    python tests/load/memory_leak_detector.py --target-process nfl-predictor --duration 300
"""

import psutil
import gc
import sys
import os
import time
import threading
import logging
import argparse
import json
import tracemalloc
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import statistics
import weakref
import pickle
from pathlib import Path

# Memory profiling imports
try:
    import tracemalloc
    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False

try:
    import objgraph
    OBJGRAPH_AVAILABLE = True
except ImportError:
    OBJGRAPH_AVAILABLE = False

try:
    from memory_profiler import profile
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time"""
    timestamp: float
    rss_mb: float          # Resident Set Size
    vms_mb: float          # Virtual Memory Size
    percent: float         # Memory percentage
    available_mb: float    # Available system memory
    buffers_mb: float      # Buffer memory
    cached_mb: float       # Cache memory
    swap_used_mb: float    # Swap usage
    swap_percent: float    # Swap percentage


@dataclass
class CPUSnapshot:
    """CPU usage snapshot"""
    timestamp: float
    cpu_percent: float           # Overall CPU usage
    cpu_count: int               # Number of CPUs
    load_average: Tuple[float, float, float]  # 1min, 5min, 15min load
    context_switches: int        # Context switches
    interrupts: int              # Interrupts
    per_cpu_percent: List[float] # Per-CPU usage


@dataclass
class ProcessSnapshot:
    """Process-specific resource snapshot"""
    timestamp: float
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    memory_vms_mb: float
    num_threads: int
    num_fds: int                 # File descriptors (Unix only)
    io_counters: Optional[Dict]  # I/O statistics
    connections: int             # Network connections


class MemoryLeakDetector:
    """Advanced memory leak detection system"""

    def __init__(self, sample_interval: int = 5, history_size: int = 2880):  # 4 hours at 5s intervals
        self.sample_interval = sample_interval
        self.history_size = history_size
        self.memory_history = deque(maxlen=history_size)
        self.cpu_history = deque(maxlen=history_size)
        self.process_history = defaultdict(lambda: deque(maxlen=history_size))

        self.monitoring = False
        self.monitor_thread = None

        # Leak detection parameters
        self.leak_threshold_mb = 50  # 50MB growth threshold
        self.leak_duration_minutes = 10  # Sustained growth duration
        self.leak_confidence_threshold = 0.7  # Confidence in leak detection

        # Object tracking
        self.tracked_objects = weakref.WeakSet()
        self.object_counts = defaultdict(int)
        self.object_history = deque(maxlen=history_size)

        # Alerts
        self.alerts = []
        self.alert_callbacks = []

    def start_monitoring(self, target_processes: List[str] = None):
        """Start continuous monitoring"""
        if self.monitoring:
            return

        self.monitoring = True

        # Start tracemalloc if available
        if TRACEMALLOC_AVAILABLE:
            tracemalloc.start()
            logger.info("Tracemalloc started for detailed memory tracking")

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(target_processes,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Memory leak detection started")

    def stop_monitoring(self):
        """Stop monitoring and generate final report"""
        self.monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)

        if TRACEMALLOC_AVAILABLE:
            tracemalloc.stop()

        logger.info("Memory leak detection stopped")

    def _monitoring_loop(self, target_processes: List[str]):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system memory snapshot
                memory_snapshot = self._collect_memory_snapshot()
                self.memory_history.append(memory_snapshot)

                # Collect CPU snapshot
                cpu_snapshot = self._collect_cpu_snapshot()
                self.cpu_history.append(cpu_snapshot)

                # Collect process-specific snapshots
                if target_processes:
                    for process_name in target_processes:
                        process_snapshot = self._collect_process_snapshot(process_name)
                        if process_snapshot:
                            self.process_history[process_name].append(process_snapshot)

                # Collect object tracking data
                self._collect_object_data()

                # Check for memory leaks
                self._analyze_for_leaks()

                # Check for alerts
                self._check_alerts(memory_snapshot, cpu_snapshot)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            time.sleep(self.sample_interval)

    def _collect_memory_snapshot(self) -> MemorySnapshot:
        """Collect current system memory snapshot"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return MemorySnapshot(
            timestamp=time.time(),
            rss_mb=memory.used / (1024 * 1024),
            vms_mb=memory.total / (1024 * 1024),
            percent=memory.percent,
            available_mb=memory.available / (1024 * 1024),
            buffers_mb=getattr(memory, 'buffers', 0) / (1024 * 1024),
            cached_mb=getattr(memory, 'cached', 0) / (1024 * 1024),
            swap_used_mb=swap.used / (1024 * 1024),
            swap_percent=swap.percent
        )

    def _collect_cpu_snapshot(self) -> CPUSnapshot:
        """Collect current CPU snapshot"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        try:
            load_avg = os.getloadavg()
        except OSError:
            load_avg = (0.0, 0.0, 0.0)  # Not available on Windows

        try:
            cpu_stats = psutil.cpu_stats()
            context_switches = cpu_stats.ctx_switches
            interrupts = cpu_stats.interrupts
        except:
            context_switches = 0
            interrupts = 0

        per_cpu = psutil.cpu_percent(percpu=True)

        return CPUSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            load_average=load_avg,
            context_switches=context_switches,
            interrupts=interrupts,
            per_cpu_percent=per_cpu
        )

    def _collect_process_snapshot(self, process_name: str) -> Optional[ProcessSnapshot]:
        """Collect snapshot for a specific process"""
        try:
            # Find process by name
            processes = [p for p in psutil.process_iter(['pid', 'name'])
                        if process_name.lower() in p.info['name'].lower()]

            if not processes:
                return None

            # Use the first matching process
            process = psutil.Process(processes[0].info['pid'])

            # Get memory info
            memory_info = process.memory_info()

            # Get I/O counters if available
            try:
                io_counters = process.io_counters()._asdict()
            except (AttributeError, psutil.AccessDenied):
                io_counters = None

            # Get file descriptors count (Unix only)
            try:
                num_fds = process.num_fds()
            except (AttributeError, psutil.AccessDenied):
                num_fds = 0

            # Get network connections count
            try:
                connections = len(process.connections())
            except (AttributeError, psutil.AccessDenied):
                connections = 0

            return ProcessSnapshot(
                timestamp=time.time(),
                pid=process.pid,
                name=process.name(),
                cpu_percent=process.cpu_percent(),
                memory_percent=process.memory_percent(),
                memory_rss_mb=memory_info.rss / (1024 * 1024),
                memory_vms_mb=memory_info.vms / (1024 * 1024),
                num_threads=process.num_threads(),
                num_fds=num_fds,
                io_counters=io_counters,
                connections=connections
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.warning(f"Could not collect data for process {process_name}: {e}")
            return None

    def _collect_object_data(self):
        """Collect Python object tracking data"""
        if not OBJGRAPH_AVAILABLE:
            return

        try:
            # Get object counts by type
            obj_counts = {}
            for obj_type in ['dict', 'list', 'tuple', 'set', 'function', 'type', 'module']:
                obj_counts[obj_type] = len(objgraph.by_type(obj_type))

            # Track total object count
            total_objects = sum(obj_counts.values())
            obj_counts['total'] = total_objects

            # Store in history
            self.object_history.append({
                'timestamp': time.time(),
                'counts': obj_counts
            })

            # Update object counts tracking
            for obj_type, count in obj_counts.items():
                self.object_counts[obj_type] = count

        except Exception as e:
            logger.error(f"Error collecting object data: {e}")

    def _analyze_for_leaks(self):
        """Analyze collected data for memory leaks"""
        if len(self.memory_history) < 10:  # Need sufficient data
            return

        # Get recent memory usage trend
        recent_samples = list(self.memory_history)[-60:]  # Last 5 minutes
        memory_values = [s.rss_mb for s in recent_samples]

        if len(memory_values) < 5:
            return

        # Calculate linear regression to detect trend
        x_values = list(range(len(memory_values)))
        slope = self._calculate_slope(x_values, memory_values)

        # Check for sustained memory growth
        growth_rate_mb_per_minute = slope * (60 / self.sample_interval)

        # Detect potential leak
        if growth_rate_mb_per_minute > 5:  # Growing by > 5MB per minute
            confidence = min(abs(slope) / 10, 1.0)  # Confidence based on slope

            if confidence >= self.leak_confidence_threshold:
                alert = {
                    'type': 'memory_leak_detected',
                    'timestamp': time.time(),
                    'growth_rate_mb_per_minute': growth_rate_mb_per_minute,
                    'confidence': confidence,
                    'current_memory_mb': memory_values[-1],
                    'samples_analyzed': len(memory_values)
                }

                self.alerts.append(alert)
                self._trigger_alert_callbacks(alert)

                logger.warning(f"Potential memory leak detected: "
                             f"{growth_rate_mb_per_minute:.2f} MB/min growth "
                             f"(confidence: {confidence:.2f})")

    def _calculate_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate slope of linear regression"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _check_alerts(self, memory_snapshot: MemorySnapshot, cpu_snapshot: CPUSnapshot):
        """Check for various alert conditions"""
        alerts_to_add = []

        # High memory usage alert
        if memory_snapshot.percent > 90:
            alerts_to_add.append({
                'type': 'high_memory_usage',
                'timestamp': time.time(),
                'memory_percent': memory_snapshot.percent,
                'memory_used_mb': memory_snapshot.rss_mb,
                'severity': 'critical'
            })
        elif memory_snapshot.percent > 80:
            alerts_to_add.append({
                'type': 'high_memory_usage',
                'timestamp': time.time(),
                'memory_percent': memory_snapshot.percent,
                'memory_used_mb': memory_snapshot.rss_mb,
                'severity': 'warning'
            })

        # High CPU usage alert
        if cpu_snapshot.cpu_percent > 90:
            alerts_to_add.append({
                'type': 'high_cpu_usage',
                'timestamp': time.time(),
                'cpu_percent': cpu_snapshot.cpu_percent,
                'load_average': cpu_snapshot.load_average,
                'severity': 'critical'
            })
        elif cpu_snapshot.cpu_percent > 80:
            alerts_to_add.append({
                'type': 'high_cpu_usage',
                'timestamp': time.time(),
                'cpu_percent': cpu_snapshot.cpu_percent,
                'load_average': cpu_snapshot.load_average,
                'severity': 'warning'
            })

        # High swap usage alert
        if memory_snapshot.swap_percent > 50:
            alerts_to_add.append({
                'type': 'high_swap_usage',
                'timestamp': time.time(),
                'swap_percent': memory_snapshot.swap_percent,
                'swap_used_mb': memory_snapshot.swap_used_mb,
                'severity': 'warning' if memory_snapshot.swap_percent < 80 else 'critical'
            })

        # Add alerts and trigger callbacks
        for alert in alerts_to_add:
            self.alerts.append(alert)
            self._trigger_alert_callbacks(alert)

    def _trigger_alert_callbacks(self, alert: Dict[str, Any]):
        """Trigger registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def add_alert_callback(self, callback):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)

    def get_memory_analysis(self, minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive memory usage analysis"""
        cutoff_time = time.time() - (minutes * 60)
        recent_memory = [m for m in self.memory_history if m.timestamp >= cutoff_time]

        if not recent_memory:
            return {"error": "No recent data available"}

        memory_values = [m.rss_mb for m in recent_memory]
        timestamps = [m.timestamp for m in recent_memory]

        # Calculate statistics
        analysis = {
            "time_range_minutes": minutes,
            "samples_count": len(recent_memory),
            "memory_statistics": {
                "current_mb": memory_values[-1] if memory_values else 0,
                "min_mb": min(memory_values) if memory_values else 0,
                "max_mb": max(memory_values) if memory_values else 0,
                "avg_mb": statistics.mean(memory_values) if memory_values else 0,
                "median_mb": statistics.median(memory_values) if memory_values else 0,
                "std_dev_mb": statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            },
            "trend_analysis": {
                "growth_rate_mb_per_minute": self._calculate_slope(
                    list(range(len(memory_values))),
                    memory_values
                ) * (60 / self.sample_interval) if len(memory_values) > 1 else 0
            }
        }

        # Leak detection analysis
        if len(memory_values) >= 10:
            # Check for sustained growth patterns
            growth_periods = self._detect_growth_periods(timestamps, memory_values)
            analysis["leak_analysis"] = {
                "growth_periods_detected": len(growth_periods),
                "longest_growth_period_minutes": max([g["duration_minutes"] for g in growth_periods]) if growth_periods else 0,
                "total_growth_mb": memory_values[-1] - memory_values[0] if memory_values else 0,
                "leak_probability": self._calculate_leak_probability(memory_values)
            }

        return analysis

    def get_cpu_analysis(self, minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive CPU usage analysis"""
        cutoff_time = time.time() - (minutes * 60)
        recent_cpu = [c for c in self.cpu_history if c.timestamp >= cutoff_time]

        if not recent_cpu:
            return {"error": "No recent data available"}

        cpu_values = [c.cpu_percent for c in recent_cpu]

        analysis = {
            "time_range_minutes": minutes,
            "samples_count": len(recent_cpu),
            "cpu_statistics": {
                "current_percent": cpu_values[-1] if cpu_values else 0,
                "min_percent": min(cpu_values) if cpu_values else 0,
                "max_percent": max(cpu_values) if cpu_values else 0,
                "avg_percent": statistics.mean(cpu_values) if cpu_values else 0,
                "median_percent": statistics.median(cpu_values) if cpu_values else 0,
                "p95_percent": statistics.quantiles(cpu_values, n=20)[18] if len(cpu_values) > 20 else max(cpu_values) if cpu_values else 0
            },
            "load_average": {
                "current": recent_cpu[-1].load_average if recent_cpu else (0, 0, 0),
                "cpu_count": recent_cpu[-1].cpu_count if recent_cpu else 0
            }
        }

        return analysis

    def get_process_analysis(self, process_name: str, minutes: int = 60) -> Dict[str, Any]:
        """Get analysis for a specific process"""
        if process_name not in self.process_history:
            return {"error": f"No data available for process: {process_name}"}

        cutoff_time = time.time() - (minutes * 60)
        recent_process = [p for p in self.process_history[process_name] if p.timestamp >= cutoff_time]

        if not recent_process:
            return {"error": "No recent data available for process"}

        memory_values = [p.memory_rss_mb for p in recent_process]
        cpu_values = [p.cpu_percent for p in recent_process]

        analysis = {
            "process_name": process_name,
            "time_range_minutes": minutes,
            "samples_count": len(recent_process),
            "current_pid": recent_process[-1].pid if recent_process else None,
            "memory_analysis": {
                "current_mb": memory_values[-1] if memory_values else 0,
                "min_mb": min(memory_values) if memory_values else 0,
                "max_mb": max(memory_values) if memory_values else 0,
                "avg_mb": statistics.mean(memory_values) if memory_values else 0,
                "growth_rate_mb_per_minute": self._calculate_slope(
                    list(range(len(memory_values))),
                    memory_values
                ) * (60 / self.sample_interval) if len(memory_values) > 1 else 0
            },
            "cpu_analysis": {
                "current_percent": cpu_values[-1] if cpu_values else 0,
                "avg_percent": statistics.mean(cpu_values) if cpu_values else 0,
                "max_percent": max(cpu_values) if cpu_values else 0
            },
            "resource_analysis": {
                "current_threads": recent_process[-1].num_threads if recent_process else 0,
                "current_connections": recent_process[-1].connections if recent_process else 0,
                "current_file_descriptors": recent_process[-1].num_fds if recent_process else 0
            }
        }

        return analysis

    def _detect_growth_periods(self, timestamps: List[float], values: List[float]) -> List[Dict]:
        """Detect periods of sustained memory growth"""
        growth_periods = []
        current_period = None

        for i in range(1, len(values)):
            growth = values[i] - values[i-1]

            if growth > 1:  # Growing by more than 1MB
                if current_period is None:
                    current_period = {
                        "start_time": timestamps[i-1],
                        "start_value": values[i-1],
                        "peak_growth_rate": growth
                    }
                else:
                    current_period["peak_growth_rate"] = max(current_period["peak_growth_rate"], growth)
            else:
                if current_period is not None:
                    current_period["end_time"] = timestamps[i]
                    current_period["end_value"] = values[i]
                    current_period["total_growth"] = current_period["end_value"] - current_period["start_value"]
                    current_period["duration_minutes"] = (current_period["end_time"] - current_period["start_time"]) / 60

                    if current_period["duration_minutes"] >= 2:  # At least 2 minutes of growth
                        growth_periods.append(current_period)

                    current_period = None

        return growth_periods

    def _calculate_leak_probability(self, memory_values: List[float]) -> float:
        """Calculate probability of memory leak based on patterns"""
        if len(memory_values) < 10:
            return 0.0

        # Calculate overall trend
        slope = self._calculate_slope(list(range(len(memory_values))), memory_values)

        # Calculate volatility
        volatility = statistics.stdev(memory_values) / statistics.mean(memory_values) if memory_values else 0

        # High slope with low volatility suggests leak
        if slope > 0.1 and volatility < 0.1:
            return min(slope * 10, 1.0)

        return max(slope * 5, 0.0)

    def generate_report(self, output_file: str = None) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_duration_hours": (time.time() - (self.memory_history[0].timestamp if self.memory_history else time.time())) / 3600,
            "system_analysis": {
                "memory": self.get_memory_analysis(60),
                "cpu": self.get_cpu_analysis(60)
            },
            "process_analyses": {},
            "alerts_summary": {
                "total_alerts": len(self.alerts),
                "alert_types": {},
                "recent_alerts": []
            },
            "recommendations": []
        }

        # Process analyses
        for process_name in self.process_history:
            report["process_analyses"][process_name] = self.get_process_analysis(process_name, 60)

        # Alert summary
        alert_types = defaultdict(int)
        for alert in self.alerts:
            alert_types[alert['type']] += 1

        report["alerts_summary"]["alert_types"] = dict(alert_types)
        report["alerts_summary"]["recent_alerts"] = [
            alert for alert in self.alerts if alert['timestamp'] > time.time() - 3600
        ]

        # Recommendations based on analysis
        recommendations = []

        memory_analysis = report["system_analysis"]["memory"]
        if not memory_analysis.get("error") and "leak_analysis" in memory_analysis:
            leak_prob = memory_analysis["leak_analysis"]["leak_probability"]
            if leak_prob > 0.7:
                recommendations.append("High probability memory leak detected - investigate object lifecycle and garbage collection")
            elif leak_prob > 0.4:
                recommendations.append("Possible memory leak - monitor for longer period and check for unreleased resources")

        cpu_analysis = report["system_analysis"]["cpu"]
        if not cpu_analysis.get("error"):
            avg_cpu = cpu_analysis["cpu_statistics"]["avg_percent"]
            if avg_cpu > 80:
                recommendations.append("High CPU usage detected - consider performance optimization or scaling")
            elif avg_cpu > 60:
                recommendations.append("Elevated CPU usage - monitor for performance bottlenecks")

        report["recommendations"] = recommendations

        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")

        return report


def main():
    """Main monitoring application"""
    parser = argparse.ArgumentParser(description="Memory Leak Detection and System Monitoring")
    parser.add_argument("--target-process", action="append", help="Process name to monitor (can specify multiple)")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds")
    parser.add_argument("--sample-interval", type=int, default=5, help="Sampling interval in seconds")
    parser.add_argument("--output-file", help="Output file for final report")
    parser.add_argument("--alert-file", help="File to log alerts")
    parser.add_argument("--memory-threshold", type=float, default=80.0, help="Memory usage alert threshold (%)")
    parser.add_argument("--cpu-threshold", type=float, default=80.0, help="CPU usage alert threshold (%)")

    args = parser.parse_args()

    # Initialize detector
    detector = MemoryLeakDetector(
        sample_interval=args.sample_interval,
        history_size=max(args.duration // args.sample_interval, 100)
    )

    # Setup alert logging if requested
    if args.alert_file:
        def log_alert(alert):
            with open(args.alert_file, 'a') as f:
                f.write(json.dumps(alert) + '\n')

        detector.add_alert_callback(log_alert)

    # Setup console alert callback
    def console_alert(alert):
        severity = alert.get('severity', 'info')
        alert_type = alert.get('type', 'unknown')
        timestamp = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')

        if severity == 'critical':
            logger.error(f"[{timestamp}] CRITICAL {alert_type}: {alert}")
        elif severity == 'warning':
            logger.warning(f"[{timestamp}] WARNING {alert_type}: {alert}")
        else:
            logger.info(f"[{timestamp}] {alert_type}: {alert}")

    detector.add_alert_callback(console_alert)

    logger.info("Starting memory leak detection and system monitoring")
    logger.info(f"Duration: {args.duration} seconds")
    logger.info(f"Sample interval: {args.sample_interval} seconds")

    if args.target_process:
        logger.info(f"Target processes: {args.target_process}")

    try:
        # Start monitoring
        detector.start_monitoring(args.target_process)

        # Run for specified duration
        time.sleep(args.duration)

        # Stop monitoring
        detector.stop_monitoring()

        # Generate final report
        report = detector.generate_report(args.output_file)

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("MEMORY LEAK DETECTION SUMMARY")
        logger.info("="*60)

        memory_analysis = report["system_analysis"]["memory"]
        if not memory_analysis.get("error"):
            logger.info(f"Memory Usage: {memory_analysis['memory_statistics']['current_mb']:.1f} MB")
            logger.info(f"Memory Growth Rate: {memory_analysis['trend_analysis']['growth_rate_mb_per_minute']:.2f} MB/min")

            if "leak_analysis" in memory_analysis:
                leak_prob = memory_analysis["leak_analysis"]["leak_probability"]
                logger.info(f"Leak Probability: {leak_prob:.2%}")

        cpu_analysis = report["system_analysis"]["cpu"]
        if not cpu_analysis.get("error"):
            logger.info(f"Average CPU Usage: {cpu_analysis['cpu_statistics']['avg_percent']:.1f}%")

        logger.info(f"Total Alerts: {report['alerts_summary']['total_alerts']}")

        if report["recommendations"]:
            logger.info("\nRecommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                logger.info(f"  {i}. {rec}")

        logger.info("="*60)

    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        detector.stop_monitoring()

    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())