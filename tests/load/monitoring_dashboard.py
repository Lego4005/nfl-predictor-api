#!/usr/bin/env python3
"""
Real-time Performance Monitoring Dashboard for Load Testing

This module provides a comprehensive real-time dashboard for monitoring
system performance during load tests. It integrates with all test types
and provides visual feedback on system health.

Features:
- Real-time metrics collection
- Interactive web dashboard
- Alerting system
- Performance trend analysis
- Resource utilization monitoring

Usage:
    python tests/load/monitoring_dashboard.py --host localhost --port 5000
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import logging

# Web framework and visualization
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.utils

# System monitoring
import psutil
import requests
import aiohttp

# Data processing
import pandas as pd
import numpy as np
from scipy import stats

# Configuration
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Single performance metric snapshot"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read: float
    disk_io_write: float
    network_bytes_sent: float
    network_bytes_recv: float
    active_connections: int
    response_time_avg: float
    response_time_p95: float
    requests_per_second: float
    error_rate: float
    cache_hit_rate: Optional[float] = None
    database_connections: Optional[int] = None
    queue_depth: Optional[int] = None


class SystemMonitor:
    """Comprehensive system performance monitor"""

    def __init__(self, sample_interval: int = 5, history_size: int = 1440):  # 2 hours at 5-second intervals
        self.sample_interval = sample_interval
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.is_monitoring = False
        self.monitor_thread = None

        # Initialize baseline measurements
        self._last_disk_io = psutil.disk_io_counters()
        self._last_network_io = psutil.net_io_counters()
        self._last_sample_time = time.time()

    def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("System monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                snapshot = self._collect_snapshot()
                self.metrics_history.append(snapshot)

                # Check for alerts
                self._check_alerts(snapshot)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            time.sleep(self.sample_interval)

    def _collect_snapshot(self) -> MetricSnapshot:
        """Collect current system metrics snapshot"""
        current_time = time.time()

        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Disk I/O
        current_disk_io = psutil.disk_io_counters()
        disk_read_rate = 0
        disk_write_rate = 0

        if self._last_disk_io:
            time_delta = current_time - self._last_sample_time
            if time_delta > 0:
                disk_read_rate = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta
                disk_write_rate = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta

        # Network I/O
        current_network_io = psutil.net_io_counters()
        network_sent_rate = 0
        network_recv_rate = 0

        if self._last_network_io:
            time_delta = current_time - self._last_sample_time
            if time_delta > 0:
                network_sent_rate = (current_network_io.bytes_sent - self._last_network_io.bytes_sent) / time_delta
                network_recv_rate = (current_network_io.bytes_recv - self._last_network_io.bytes_recv) / time_delta

        # Network connections
        active_connections = len(psutil.net_connections(kind='inet'))

        # Store current values for next iteration
        self._last_disk_io = current_disk_io
        self._last_network_io = current_network_io
        self._last_sample_time = current_time

        # Application metrics (would be populated by external sources)
        response_time_avg = self._get_app_metric('response_time_avg', 0)
        response_time_p95 = self._get_app_metric('response_time_p95', 0)
        requests_per_second = self._get_app_metric('requests_per_second', 0)
        error_rate = self._get_app_metric('error_rate', 0)
        cache_hit_rate = self._get_app_metric('cache_hit_rate')

        return MetricSnapshot(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_io_read=disk_read_rate / (1024 * 1024),  # MB/s
            disk_io_write=disk_write_rate / (1024 * 1024),  # MB/s
            network_bytes_sent=network_sent_rate / (1024 * 1024),  # MB/s
            network_bytes_recv=network_recv_rate / (1024 * 1024),  # MB/s
            active_connections=active_connections,
            response_time_avg=response_time_avg,
            response_time_p95=response_time_p95,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate
        )

    def _get_app_metric(self, metric_name: str, default_value: Any = None) -> Any:
        """Get application metric from external source (placeholder)"""
        # This would integrate with your application's metrics endpoint
        # For now, return default or simulate some data for demo
        return default_value

    def _check_alerts(self, snapshot: MetricSnapshot):
        """Check for alert conditions"""
        alerts = []

        # CPU alert
        if snapshot.cpu_percent > 85:
            alerts.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")

        # Memory alert
        if snapshot.memory_percent > 90:
            alerts.append(f"High memory usage: {snapshot.memory_percent:.1f}%")

        # Response time alert
        if snapshot.response_time_p95 > 2000:  # 2 seconds
            alerts.append(f"High P95 response time: {snapshot.response_time_p95:.0f}ms")

        # Error rate alert
        if snapshot.error_rate > 0.05:  # 5%
            alerts.append(f"High error rate: {snapshot.error_rate:.2%}")

        if alerts:
            logger.warning(f"Performance alerts: {'; '.join(alerts)}")

    def get_recent_metrics(self, minutes: int = 10) -> List[MetricSnapshot]:
        """Get metrics from the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_metric_statistics(self, metric_name: str, minutes: int = 60) -> Dict[str, float]:
        """Get statistics for a specific metric over time"""
        recent_metrics = self.get_recent_metrics(minutes)
        if not recent_metrics:
            return {}

        values = [getattr(m, metric_name) for m in recent_metrics if getattr(m, metric_name) is not None]
        if not values:
            return {}

        return {
            'min': min(values),
            'max': max(values),
            'mean': np.mean(values),
            'median': np.median(values),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99),
            'std': np.std(values),
            'count': len(values)
        }


class LoadTestIntegrator:
    """Integrates with running load tests to collect test-specific metrics"""

    def __init__(self, locust_host: str = "http://localhost:8089"):
        self.locust_host = locust_host
        self.last_stats = {}

    async def get_locust_stats(self) -> Dict[str, Any]:
        """Get current stats from Locust web interface"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.locust_host}/stats/requests") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
        except Exception as e:
            logger.debug(f"Could not fetch Locust stats: {e}")

        return {}

    async def get_aggregated_metrics(self) -> Dict[str, float]:
        """Get aggregated metrics from load test"""
        stats = await self.get_locust_stats()

        if not stats or 'stats' not in stats:
            return {}

        total_stats = None
        for stat in stats['stats']:
            if stat['name'] == 'Aggregated':
                total_stats = stat
                break

        if not total_stats:
            return {}

        return {
            'requests_per_second': total_stats.get('current_rps', 0),
            'response_time_avg': total_stats.get('avg_response_time', 0),
            'response_time_p95': total_stats.get('95%', 0),
            'error_rate': total_stats.get('num_failures', 0) / max(total_stats.get('num_requests', 1), 1),
            'total_requests': total_stats.get('num_requests', 0),
            'total_failures': total_stats.get('num_failures', 0)
        }


class PerformanceDashboard:
    """Web-based performance monitoring dashboard"""

    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Initialize monitoring components
        self.system_monitor = SystemMonitor()
        self.load_test_integrator = LoadTestIntegrator()

        # Setup routes
        self._setup_routes()
        self._setup_websocket_handlers()

        # Background task for real-time updates
        self.update_thread = None
        self.is_updating = False

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            return render_template('dashboard.html')

        @self.app.route('/api/metrics/current')
        def current_metrics():
            if self.system_monitor.metrics_history:
                latest = self.system_monitor.metrics_history[-1]
                return jsonify(asdict(latest))
            return jsonify({})

        @self.app.route('/api/metrics/history')
        def metrics_history():
            minutes = request.args.get('minutes', 30, type=int)
            recent = self.system_monitor.get_recent_metrics(minutes)
            return jsonify([asdict(m) for m in recent])

        @self.app.route('/api/metrics/statistics')
        def metrics_statistics():
            minutes = request.args.get('minutes', 60, type=int)
            metric = request.args.get('metric', 'cpu_percent')

            stats = self.system_monitor.get_metric_statistics(metric, minutes)
            return jsonify(stats)

        @self.app.route('/api/charts/cpu')
        def cpu_chart():
            recent = self.system_monitor.get_recent_metrics(30)

            timestamps = [datetime.fromtimestamp(m.timestamp) for m in recent]
            cpu_values = [m.cpu_percent for m in recent]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=cpu_values,
                mode='lines+markers',
                name='CPU Usage (%)',
                line=dict(color='#ff6b6b', width=2)
            ))

            fig.update_layout(
                title='CPU Usage Over Time',
                xaxis_title='Time',
                yaxis_title='CPU Usage (%)',
                template='plotly_dark',
                height=300
            )

            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        @self.app.route('/api/charts/memory')
        def memory_chart():
            recent = self.system_monitor.get_recent_metrics(30)

            timestamps = [datetime.fromtimestamp(m.timestamp) for m in recent]
            memory_values = [m.memory_percent for m in recent]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=memory_values,
                mode='lines+markers',
                name='Memory Usage (%)',
                line=dict(color='#4ecdc4', width=2)
            ))

            fig.update_layout(
                title='Memory Usage Over Time',
                xaxis_title='Time',
                yaxis_title='Memory Usage (%)',
                template='plotly_dark',
                height=300
            )

            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        @self.app.route('/api/charts/response_times')
        def response_times_chart():
            recent = self.system_monitor.get_recent_metrics(30)

            timestamps = [datetime.fromtimestamp(m.timestamp) for m in recent]
            avg_times = [m.response_time_avg for m in recent]
            p95_times = [m.response_time_p95 for m in recent]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=avg_times,
                mode='lines+markers',
                name='Average Response Time (ms)',
                line=dict(color='#45b7d1', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=timestamps,
                y=p95_times,
                mode='lines+markers',
                name='P95 Response Time (ms)',
                line=dict(color='#f7dc6f', width=2)
            ))

            fig.update_layout(
                title='Response Times Over Time',
                xaxis_title='Time',
                yaxis_title='Response Time (ms)',
                template='plotly_dark',
                height=300
            )

            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            emit('status', {'message': 'Connected to monitoring dashboard'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on('request_update')
        def handle_update_request():
            if self.system_monitor.metrics_history:
                latest = self.system_monitor.metrics_history[-1]
                emit('metrics_update', asdict(latest))

    def _real_time_update_loop(self):
        """Background loop for real-time dashboard updates"""
        while self.is_updating:
            try:
                if self.system_monitor.metrics_history:
                    latest = self.system_monitor.metrics_history[-1]
                    self.socketio.emit('metrics_update', asdict(latest))

                time.sleep(2)  # Update every 2 seconds

            except Exception as e:
                logger.error(f"Error in update loop: {e}")

    def start(self):
        """Start the monitoring dashboard"""
        # Start system monitoring
        self.system_monitor.start_monitoring()

        # Start real-time updates
        self.is_updating = True
        self.update_thread = threading.Thread(target=self._real_time_update_loop, daemon=True)
        self.update_thread.start()

        logger.info(f"Starting performance dashboard on http://{self.host}:{self.port}")

        # Create template directory if it doesn't exist
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self._create_dashboard_template(template_dir)

        # Start Flask app
        self.socketio.run(self.app, host=self.host, port=self.port, debug=False)

    def stop(self):
        """Stop the monitoring dashboard"""
        self.is_updating = False
        self.system_monitor.stop_monitoring()

        if self.update_thread:
            self.update_thread.join(timeout=5)

        logger.info("Performance dashboard stopped")

    def _create_dashboard_template(self, template_dir: Path):
        """Create the HTML template for the dashboard"""
        template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFL Predictor Performance Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: #ffffff;
        }

        .header {
            background-color: #2d2d2d;
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #4ecdc4;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            padding: 20px;
        }

        .metric-card {
            background-color: #2d2d2d;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #444;
        }

        .metric-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #4ecdc4;
        }

        .metric-value {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .metric-unit {
            font-size: 14px;
            color: #888;
        }

        .chart-container {
            height: 300px;
            margin-top: 15px;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-good { background-color: #27ae60; }
        .status-warning { background-color: #f39c12; }
        .status-critical { background-color: #e74c3c; }

        .alert-panel {
            background-color: #3d2d2d;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 20px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>NFL Predictor Performance Dashboard</h1>
        <p>Real-time system monitoring and load testing metrics</p>
        <div id="connection-status">
            <span id="status-indicator" class="status-indicator status-good"></span>
            <span id="status-text">Connected</span>
        </div>
    </div>

    <div class="dashboard-grid">
        <div class="metric-card">
            <div class="metric-title">CPU Usage</div>
            <div class="metric-value" id="cpu-value">0</div>
            <div class="metric-unit">%</div>
            <div id="cpu-chart" class="chart-container"></div>
        </div>

        <div class="metric-card">
            <div class="metric-title">Memory Usage</div>
            <div class="metric-value" id="memory-value">0</div>
            <div class="metric-unit">%</div>
            <div id="memory-chart" class="chart-container"></div>
        </div>

        <div class="metric-card">
            <div class="metric-title">Response Times</div>
            <div class="metric-value" id="response-time-value">0</div>
            <div class="metric-unit">ms (avg)</div>
            <div id="response-times-chart" class="chart-container"></div>
        </div>

        <div class="metric-card">
            <div class="metric-title">Requests per Second</div>
            <div class="metric-value" id="rps-value">0</div>
            <div class="metric-unit">req/s</div>
        </div>

        <div class="metric-card">
            <div class="metric-title">Error Rate</div>
            <div class="metric-value" id="error-rate-value">0.0</div>
            <div class="metric-unit">%</div>
        </div>

        <div class="metric-card">
            <div class="metric-title">Active Connections</div>
            <div class="metric-value" id="connections-value">0</div>
            <div class="metric-unit">connections</div>
        </div>
    </div>

    <div id="alerts-panel" class="alert-panel" style="display: none;">
        <h3>Performance Alerts</h3>
        <ul id="alerts-list"></ul>
    </div>

    <script>
        const socket = io();

        // Connection status handling
        socket.on('connect', function() {
            document.getElementById('status-indicator').className = 'status-indicator status-good';
            document.getElementById('status-text').textContent = 'Connected';
        });

        socket.on('disconnect', function() {
            document.getElementById('status-indicator').className = 'status-indicator status-critical';
            document.getElementById('status-text').textContent = 'Disconnected';
        });

        // Metrics update handling
        socket.on('metrics_update', function(data) {
            updateMetrics(data);
        });

        function updateMetrics(data) {
            // Update metric values
            document.getElementById('cpu-value').textContent = data.cpu_percent.toFixed(1);
            document.getElementById('memory-value').textContent = data.memory_percent.toFixed(1);
            document.getElementById('response-time-value').textContent = data.response_time_avg.toFixed(0);
            document.getElementById('rps-value').textContent = data.requests_per_second.toFixed(1);
            document.getElementById('error-rate-value').textContent = (data.error_rate * 100).toFixed(2);
            document.getElementById('connections-value').textContent = data.active_connections;

            // Color coding for critical values
            const cpuElement = document.getElementById('cpu-value');
            cpuElement.style.color = data.cpu_percent > 80 ? '#e74c3c' : data.cpu_percent > 60 ? '#f39c12' : '#27ae60';

            const memoryElement = document.getElementById('memory-value');
            memoryElement.style.color = data.memory_percent > 85 ? '#e74c3c' : data.memory_percent > 70 ? '#f39c12' : '#27ae60';
        }

        // Load charts
        function loadCharts() {
            fetch('/api/charts/cpu')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('cpu-chart', data.data, data.layout, {responsive: true});
                });

            fetch('/api/charts/memory')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('memory-chart', data.data, data.layout, {responsive: true});
                });

            fetch('/api/charts/response_times')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('response-times-chart', data.data, data.layout, {responsive: true});
                });
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadCharts();

            // Refresh charts every 30 seconds
            setInterval(loadCharts, 30000);

            // Request initial update
            socket.emit('request_update');
        });
    </script>
</body>
</html>
        '''

        with open(template_dir / "dashboard.html", "w") as f:
            f.write(template_content.strip())


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Monitoring Dashboard")
    parser.add_argument("--host", default="localhost", help="Dashboard host")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port")
    parser.add_argument("--locust-host", default="http://localhost:8089", help="Locust web interface URL")

    args = parser.parse_args()

    dashboard = PerformanceDashboard(host=args.host, port=args.port)
    dashboard.load_test_integrator = LoadTestIntegrator(locust_host=args.locust_host)

    try:
        dashboard.start()
    except KeyboardInterrupt:
        logger.info("Shutting down dashboard...")
        dashboard.stop()


if __name__ == "__main__":
    main()