#!/usr/bin/env python3
"""
Monitoring and Health Check Setup Script for NFL Predictor.
Sets up comprehensive monitoring, alerting, and health check systems.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringSetup:
    """Handles comprehensive monitoring system setup"""
    
    def __init__(self):
        self.setup_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "steps_completed": [],
            "files_created": [],
            "services_created": [],
            "commands_to_run": [],
            "errors": [],
            "warnings": [],
            "success": False
        }
    
    def step_1_create_monitoring_config(self) -> bool:
        """Step 1: Create monitoring configuration files"""
        logger.info("Step 1: Creating monitoring configuration...")
        
        try:
            # Create monitoring configuration
            monitoring_config = {
                "health_checks": {
                    "enabled": True,
                    "interval_seconds": 30,
                    "timeout_seconds": 10,
                    "endpoints": {
                        "comprehensive": "/v1/health/comprehensive",
                        "api_sources": "/v1/health/api-sources",
                        "cache": "/v1/health/cache",
                        "system": "/v1/health/system"
                    }
                },
                "dashboard": {
                    "enabled": True,
                    "update_interval_seconds": 30,
                    "history_retention_hours": 24,
                    "auto_refresh": True
                },
                "alerting": {
                    "enabled": True,
                    "channels": {
                        "log": {
                            "enabled": True,
                            "path": "logs/monitoring.log",
                            "level": "warning"
                        },
                        "webhook": {
                            "enabled": False,
                            "url": "",
                            "level": "critical"
                        },
                        "email": {
                            "enabled": False,
                            "smtp_server": "",
                            "smtp_port": 587,
                            "username": "",
                            "password": "",
                            "to_addresses": [],
                            "level": "critical"
                        }
                    }
                },
                "metrics": {
                    "collection_enabled": True,
                    "retention_days": 7,
                    "export_format": "json",
                    "performance_tracking": True
                }
            }
            
            # Save monitoring configuration
            config_file = "config/monitoring.json"
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, "w") as f:
                json.dump(monitoring_config, f, indent=2)
            
            self.setup_results["files_created"].append(config_file)
            logger.info(f"✓ Monitoring configuration created: {config_file}")
            
            # Create log directory
            os.makedirs("logs", exist_ok=True)
            logger.info("✓ Log directory created")
            
            self.setup_results["steps_completed"].append("monitoring_config")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Monitoring config creation failed: {str(e)}")
            logger.error(f"✗ Monitoring config creation failed: {e}")
            return False
    
    def step_2_create_health_check_service(self) -> bool:
        """Step 2: Create health check service"""
        logger.info("Step 2: Creating health check service...")
        
        try:
            # Create health check service script
            service_script = f"""#!/usr/bin/env python3
\"\"\"
Health Check Service for NFL Predictor.
Continuously monitors system health and sends alerts.
\"\"\"

import asyncio
import json
import logging
import time
from datetime import datetime
import aiohttp
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_check_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HealthCheckService:
    \"\"\"Continuous health check service\"\"\"
    
    def __init__(self, config_file: str = "config/monitoring.json"):
        self.config = self.load_config(config_file)
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.running = False
    
    def load_config(self, config_file: str) -> dict:
        \"\"\"Load monitoring configuration\"\"\"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {{e}}")
            return {{"health_checks": {{"enabled": True, "interval_seconds": 60}}}}
    
    async def check_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> dict:
        \"\"\"Check a specific health endpoint\"\"\"
        url = f"{{self.api_base_url}}{{endpoint}}"
        
        try:
            start_time = time.time()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_time = (time.time() - start_time) * 1000
                data = await response.json()
                
                return {{
                    "endpoint": endpoint,
                    "status": "success",
                    "response_time_ms": response_time,
                    "http_status": response.status,
                    "data": data
                }}
                
        except Exception as e:
            return {{
                "endpoint": endpoint,
                "status": "error",
                "error": str(e),
                "response_time_ms": None
            }}
    
    async def run_health_checks(self):
        \"\"\"Run all configured health checks\"\"\"
        endpoints = self.config.get("health_checks", {{}}).get("endpoints", {{}})
        
        if not endpoints:
            logger.warning("No health check endpoints configured")
            return
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_endpoint(session, endpoint)
                for endpoint in endpoints.values()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Health check exception: {{result}}")
                    continue
                
                endpoint = result.get("endpoint", "unknown")
                status = result.get("status", "unknown")
                
                if status == "success":
                    response_time = result.get("response_time_ms", 0)
                    logger.info(f"✓ {{endpoint}} - {{response_time:.1f}}ms")
                    
                    # Check for unhealthy status in response
                    data = result.get("data", {{}})
                    if isinstance(data, dict):
                        overall_status = data.get("overall_status", data.get("status", "unknown"))
                        if overall_status in ["unhealthy", "critical"]:
                            logger.warning(f"⚠ {{endpoint}} reports unhealthy status: {{overall_status}}")
                        elif overall_status == "degraded":
                            logger.info(f"ℹ {{endpoint}} reports degraded status")
                else:
                    error = result.get("error", "unknown error")
                    logger.error(f"✗ {{endpoint}} - {{error}}")
    
    async def monitoring_loop(self):
        \"\"\"Main monitoring loop\"\"\"
        interval = self.config.get("health_checks", {{}}).get("interval_seconds", 60)
        logger.info(f"Starting health check service (interval: {{interval}}s)")
        
        while self.running:
            try:
                await self.run_health_checks()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {{e}}")
                await asyncio.sleep(interval)
    
    async def start(self):
        \"\"\"Start the health check service\"\"\"
        self.running = True
        await self.monitoring_loop()
    
    def stop(self):
        \"\"\"Stop the health check service\"\"\"
        self.running = False


async def main():
    \"\"\"Main function\"\"\"
    service = HealthCheckService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Health check service stopped by user")
        service.stop()
    except Exception as e:
        logger.error(f"Health check service error: {{e}}")


if __name__ == "__main__":
    asyncio.run(main())
"""
            
            script_file = "services/health_check_service.py"
            os.makedirs(os.path.dirname(script_file), exist_ok=True)
            
            with open(script_file, "w") as f:
                f.write(service_script)
            
            self.setup_results["files_created"].append(script_file)
            logger.info(f"✓ Health check service created: {script_file}")
            
            # Create systemd service file
            systemd_service = f"""[Unit]
Description=NFL Predictor Health Check Service
After=network.target
Wants=nfl-predictor.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
EnvironmentFile={os.getcwd()}/.env
ExecStart={os.getcwd()}/venv/bin/python services/health_check_service.py
Restart=always
RestartSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nfl-predictor-health-check

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={os.getcwd()}/logs

[Install]
WantedBy=multi-user.target
"""
            
            systemd_file = "/tmp/nfl-predictor-health-check.service"
            with open(systemd_file, "w") as f:
                f.write(systemd_service)
            
            self.setup_results["services_created"].append("health-check")
            self.setup_results["commands_to_run"].extend([
                f"sudo cp {systemd_file} /etc/systemd/system/",
                "sudo systemctl daemon-reload",
                "sudo systemctl enable nfl-predictor-health-check",
                "sudo systemctl start nfl-predictor-health-check"
            ])
            
            logger.info(f"✓ Systemd service file created: {systemd_file}")
            
            self.setup_results["steps_completed"].append("health_check_service")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Health check service creation failed: {str(e)}")
            logger.error(f"✗ Health check service creation failed: {e}")
            return False
    
    def step_3_create_monitoring_dashboard_service(self) -> bool:
        """Step 3: Create monitoring dashboard service"""
        logger.info("Step 3: Creating monitoring dashboard service...")
        
        try:
            # Create dashboard service script
            dashboard_script = f"""#!/usr/bin/env python3
\"\"\"
Monitoring Dashboard Service for NFL Predictor.
Provides real-time monitoring dashboard with metrics collection.
\"\"\"

import asyncio
import json
import logging
import signal
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DashboardService:
    \"\"\"Monitoring dashboard service\"\"\"
    
    def __init__(self):
        self.dashboard = None
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        \"\"\"Setup signal handlers for graceful shutdown\"\"\"
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        \"\"\"Handle shutdown signals\"\"\"
        logger.info(f"Received signal {{signum}}, shutting down...")
        self.running = False
    
    async def initialize_dashboard(self):
        \"\"\"Initialize monitoring dashboard\"\"\"
        try:
            from src.monitoring.dashboard import create_monitoring_dashboard
            from src.monitoring.health_checks import create_health_checker
            from src.monitoring.cache_monitor import create_cache_monitor
            
            # Get Redis client if available
            redis_client = None
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                redis_client = redis.from_url(redis_url, decode_responses=True)
                redis_client.ping()  # Test connection
                logger.info("✓ Redis client connected")
            except Exception as e:
                logger.warning(f"Redis client not available: {{e}}")
            
            # Get API keys
            api_keys = {{}}
            for key_name in ["ODDS_API_KEY", "SPORTSDATA_IO_KEY", "RAPID_API_KEY"]:
                key_value = os.getenv(key_name)
                if key_value:
                    service_name = key_name.lower().replace("_key", "").replace("_", "_")
                    api_keys[service_name] = key_value
            
            # Create components
            health_checker = create_health_checker(redis_client, api_keys)
            cache_monitor = create_cache_monitor(redis_client) if redis_client else None
            
            # Create dashboard
            self.dashboard = create_monitoring_dashboard(
                health_checker=health_checker,
                cache_monitor=cache_monitor,
                update_interval=30
            )
            
            logger.info("✓ Monitoring dashboard initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {{e}}")
            return False
    
    async def run(self):
        \"\"\"Run the dashboard service\"\"\"
        logger.info("Starting monitoring dashboard service...")
        
        # Initialize dashboard
        if not await self.initialize_dashboard():
            logger.error("Failed to initialize dashboard, exiting")
            return
        
        # Start dashboard
        self.running = True
        await self.dashboard.start_dashboard()
        
        try:
            # Keep service running
            while self.running:
                await asyncio.sleep(1)
        finally:
            # Cleanup
            if self.dashboard:
                await self.dashboard.stop_dashboard()
            logger.info("Monitoring dashboard service stopped")


async def main():
    \"\"\"Main function\"\"\"
    service = DashboardService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
"""
            
            dashboard_file = "services/dashboard_service.py"
            with open(dashboard_file, "w") as f:
                f.write(dashboard_script)
            
            self.setup_results["files_created"].append(dashboard_file)
            logger.info(f"✓ Dashboard service created: {dashboard_file}")
            
            # Create systemd service for dashboard
            dashboard_systemd = f"""[Unit]
Description=NFL Predictor Monitoring Dashboard
After=network.target redis.service
Wants=redis.service nfl-predictor.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
EnvironmentFile={os.getcwd()}/.env
ExecStart={os.getcwd()}/venv/bin/python services/dashboard_service.py
Restart=always
RestartSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nfl-predictor-dashboard

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={os.getcwd()}/logs

[Install]
WantedBy=multi-user.target
"""
            
            dashboard_systemd_file = "/tmp/nfl-predictor-dashboard.service"
            with open(dashboard_systemd_file, "w") as f:
                f.write(dashboard_systemd)
            
            self.setup_results["services_created"].append("dashboard")
            self.setup_results["commands_to_run"].extend([
                f"sudo cp {dashboard_systemd_file} /etc/systemd/system/",
                "sudo systemctl daemon-reload",
                "sudo systemctl enable nfl-predictor-dashboard",
                "sudo systemctl start nfl-predictor-dashboard"
            ])
            
            logger.info(f"✓ Dashboard systemd service created: {dashboard_systemd_file}")
            
            self.setup_results["steps_completed"].append("dashboard_service")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Dashboard service creation failed: {str(e)}")
            logger.error(f"✗ Dashboard service creation failed: {e}")
            return False
    
    def step_4_create_alerting_system(self) -> bool:
        """Step 4: Create alerting system"""
        logger.info("Step 4: Creating alerting system...")
        
        try:
            # Create alerting script
            alerting_script = f"""#!/usr/bin/env python3
\"\"\"
Alerting System for NFL Predictor.
Handles alert notifications via multiple channels.
\"\"\"

import json
import logging
import smtplib
import requests
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertManager:
    \"\"\"Manages alert notifications\"\"\"
    
    def __init__(self, config_file: str = "config/monitoring.json"):
        self.config = self.load_config(config_file)
    
    def load_config(self, config_file: str) -> dict:
        \"\"\"Load alerting configuration\"\"\"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {{e}}")
            return {{"alerting": {{"enabled": False}}}}
    
    def send_log_alert(self, alert_data: Dict[str, Any]):
        \"\"\"Send alert to log file\"\"\"
        log_config = self.config.get("alerting", {{}}).get("channels", {{}}).get("log", {{}})
        
        if not log_config.get("enabled", False):
            return
        
        log_file = log_config.get("path", "logs/alerts.log")
        alert_level = alert_data.get("level", "info")
        required_level = log_config.get("level", "warning")
        
        # Check if alert level meets threshold
        level_priority = {{"info": 1, "warning": 2, "critical": 3}}
        if level_priority.get(alert_level, 1) < level_priority.get(required_level, 2):
            return
        
        # Format alert message
        timestamp = alert_data.get("timestamp", datetime.utcnow().isoformat())
        message = alert_data.get("message", "Unknown alert")
        component = alert_data.get("component", "unknown")
        
        log_message = f"[{{timestamp}}] {{alert_level.upper()}} - {{component}}: {{message}}"
        
        try:
            with open(log_file, "a") as f:
                f.write(log_message + "\\n")
            logger.info(f"Alert logged: {{component}} - {{alert_level}}")
        except Exception as e:
            logger.error(f"Failed to write alert to log: {{e}}")
    
    def send_webhook_alert(self, alert_data: Dict[str, Any]):
        \"\"\"Send alert via webhook\"\"\"
        webhook_config = self.config.get("alerting", {{}}).get("channels", {{}}).get("webhook", {{}})
        
        if not webhook_config.get("enabled", False):
            return
        
        webhook_url = webhook_config.get("url")
        if not webhook_url:
            return
        
        alert_level = alert_data.get("level", "info")
        required_level = webhook_config.get("level", "critical")
        
        # Check if alert level meets threshold
        level_priority = {{"info": 1, "warning": 2, "critical": 3}}
        if level_priority.get(alert_level, 1) < level_priority.get(required_level, 3):
            return
        
        try:
            payload = {{
                "timestamp": datetime.utcnow().isoformat(),
                "service": "nfl-predictor",
                "alert": alert_data
            }}
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Webhook alert sent: {{alert_data.get('component', 'unknown')}}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {{e}}")
    
    def send_email_alert(self, alert_data: Dict[str, Any]):
        \"\"\"Send alert via email\"\"\"
        email_config = self.config.get("alerting", {{}}).get("channels", {{}}).get("email", {{}})
        
        if not email_config.get("enabled", False):
            return
        
        alert_level = alert_data.get("level", "info")
        required_level = email_config.get("level", "critical")
        
        # Check if alert level meets threshold
        level_priority = {{"info": 1, "warning": 2, "critical": 3}}
        if level_priority.get(alert_level, 1) < level_priority.get(required_level, 3):
            return
        
        try:
            msg = MimeMultipart()
            msg["From"] = email_config.get("username", "")
            msg["To"] = ", ".join(email_config.get("to_addresses", []))
            msg["Subject"] = f"NFL Predictor Alert - {{alert_level.upper()}}"
            
            body = f\"\"\"
NFL Predictor System Alert

Level: {{alert_level.upper()}}
Component: {{alert_data.get('component', 'Unknown')}}
Message: {{alert_data.get('message', 'No message')}}
Timestamp: {{alert_data.get('timestamp', 'Unknown')}}

{{alert_data.get('details', '')}}

Please check the system status and take appropriate action.
\"\"\"
            
            msg.attach(MimeText(body, "plain"))
            
            server = smtplib.SMTP(email_config.get("smtp_server", ""), email_config.get("smtp_port", 587))
            server.starttls()
            server.login(email_config.get("username", ""), email_config.get("password", ""))
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {{alert_data.get('component', 'unknown')}}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {{e}}")
    
    def process_alert(self, alert_data: Dict[str, Any]):
        \"\"\"Process alert through all configured channels\"\"\"
        if not self.config.get("alerting", {{}}).get("enabled", False):
            return
        
        logger.info(f"Processing alert: {{alert_data.get('component', 'unknown')}} - {{alert_data.get('level', 'info')}}")
        
        # Send through all channels
        self.send_log_alert(alert_data)
        self.send_webhook_alert(alert_data)
        self.send_email_alert(alert_data)


def main():
    \"\"\"Main function for testing\"\"\"
    alert_manager = AlertManager()
    
    # Test alert
    test_alert = {{
        "level": "warning",
        "component": "test_system",
        "message": "Test alert from monitoring setup",
        "timestamp": datetime.utcnow().isoformat(),
        "details": "This is a test alert to verify the alerting system is working."
    }}
    
    alert_manager.process_alert(test_alert)
    print("Test alert processed")


if __name__ == "__main__":
    main()
"""
            
            alerting_file = "services/alerting.py"
            with open(alerting_file, "w") as f:
                f.write(alerting_script)
            
            self.setup_results["files_created"].append(alerting_file)
            logger.info(f"✓ Alerting system created: {alerting_file}")
            
            self.setup_results["steps_completed"].append("alerting_system")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Alerting system creation failed: {str(e)}")
            logger.error(f"✗ Alerting system creation failed: {e}")
            return False
    
    def step_5_create_monitoring_scripts(self) -> bool:
        """Step 5: Create monitoring utility scripts"""
        logger.info("Step 5: Creating monitoring utility scripts...")
        
        try:
            # Create monitoring status script
            status_script = f"""#!/bin/bash
# Monitoring Status Script for NFL Predictor
# Shows status of all monitoring components

echo "NFL Predictor Monitoring Status"
echo "==============================="
echo "Timestamp: $(date)"
echo ""

# Check API health
echo "API Health Check:"
curl -s http://localhost:8000/v1/health/api-sources | jq '.overall_status' 2>/dev/null || echo "API not responding"
echo ""

# Check cache health
echo "Cache Health Check:"
curl -s http://localhost:8000/v1/health/cache | jq '.status' 2>/dev/null || echo "Cache check failed"
echo ""

# Check system health
echo "System Health Check:"
curl -s http://localhost:8000/v1/health/system | jq '.status' 2>/dev/null || echo "System check failed"
echo ""

# Check services
echo "Service Status:"
systemctl is-active nfl-predictor 2>/dev/null || echo "Main API: not running"
systemctl is-active nfl-predictor-health-check 2>/dev/null || echo "Health Check: not running"
systemctl is-active nfl-predictor-dashboard 2>/dev/null || echo "Dashboard: not running"
systemctl is-active redis 2>/dev/null || echo "Redis: not running"
echo ""

# Check logs for recent errors
echo "Recent Errors (last 10):"
tail -n 10 logs/*.log 2>/dev/null | grep -i error | tail -n 5 || echo "No recent errors found"
"""
            
            status_script_file = "scripts/monitoring_status.sh"
            with open(status_script_file, "w") as f:
                f.write(status_script)
            
            # Create log rotation script
            logrotate_script = f"""#!/bin/bash
# Log rotation script for NFL Predictor monitoring logs

LOG_DIR="logs"
MAX_SIZE="10M"
KEEP_DAYS=7

echo "Rotating NFL Predictor logs..."

# Rotate large log files
find $LOG_DIR -name "*.log" -size +$MAX_SIZE -exec {{
    echo "Rotating large log file: {{}}"
    mv {{}} {{}}.$(date +%Y%m%d_%H%M%S)
    touch {{}}
}} \\;

# Remove old log files
find $LOG_DIR -name "*.log.*" -mtime +$KEEP_DAYS -delete

# Compress old logs
find $LOG_DIR -name "*.log.*" -not -name "*.gz" -exec gzip {{}} \\;

echo "Log rotation completed"
"""
            
            logrotate_file = "scripts/rotate_logs.sh"
            with open(logrotate_file, "w") as f:
                f.write(logrotate_script)
            
            # Make scripts executable
            try:
                import stat
                os.chmod(status_script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
                os.chmod(logrotate_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except:
                self.setup_results["commands_to_run"].extend([
                    f"chmod +x {status_script_file}",
                    f"chmod +x {logrotate_file}"
                ])
            
            self.setup_results["files_created"].extend([status_script_file, logrotate_file])
            logger.info(f"✓ Monitoring scripts created")
            
            # Create cron job for log rotation
            cron_entry = f"0 2 * * * {os.getcwd()}/{logrotate_file}"
            self.setup_results["commands_to_run"].append(f"echo '{cron_entry}' | crontab -")
            
            self.setup_results["steps_completed"].append("monitoring_scripts")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Monitoring scripts creation failed: {str(e)}")
            logger.error(f"✗ Monitoring scripts creation failed: {e}")
            return False
    
    def run_complete_setup(self) -> Dict[str, Any]:
        """Run complete monitoring setup"""
        logger.info("Starting complete monitoring system setup...")
        logger.info("=" * 60)
        
        steps = [
            ("Monitoring Configuration", self.step_1_create_monitoring_config),
            ("Health Check Service", self.step_2_create_health_check_service),
            ("Dashboard Service", self.step_3_create_monitoring_dashboard_service),
            ("Alerting System", self.step_4_create_alerting_system),
            ("Monitoring Scripts", self.step_5_create_monitoring_scripts)
        ]
        
        for step_name, step_function in steps:
            logger.info(f"\\n--- {step_name} ---")
            
            try:
                success = step_function()
                if success:
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.error(f"❌ {step_name} failed")
                    self.setup_results["success"] = False
                    break
            except Exception as e:
                logger.error(f"❌ {step_name} failed with exception: {e}")
                self.setup_results["errors"].append(f"{step_name} exception: {str(e)}")
                self.setup_results["success"] = False
                break
        else:
            # All steps completed successfully
            self.setup_results["success"] = True
            logger.info("\\n🎉 Monitoring system setup completed successfully!")
        
        return self.setup_results
    
    def generate_setup_report(self) -> str:
        """Generate setup report"""
        report_file = f"monitoring_setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, "w") as f:
            json.dump(self.setup_results, f, indent=2)
        
        logger.info(f"Setup report saved: {report_file}")
        return report_file


async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="NFL Predictor Monitoring Setup")
    parser.add_argument(
        "--test-alerts",
        action="store_true",
        help="Test alerting system after setup"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report without running setup"
    )
    
    args = parser.parse_args()
    
    setup = MonitoringSetup()
    
    if args.report_only:
        # Generate report only
        report_file = setup.generate_setup_report()
        print(f"Report generated: {report_file}")
        return
    
    # Run complete setup
    results = setup.run_complete_setup()
    
    # Test alerts if requested
    if args.test_alerts and results["success"]:
        logger.info("\\nTesting alerting system...")
        try:
            import subprocess
            subprocess.run([sys.executable, "services/alerting.py"], check=True)
            logger.info("✓ Alerting system test completed")
        except Exception as e:
            logger.warning(f"Alerting system test failed: {e}")
    
    # Generate report
    report_file = setup.generate_setup_report()
    
    # Print summary
    logger.info("\\n" + "=" * 60)
    logger.info("MONITORING SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Success: {results['success']}")
    logger.info(f"Steps Completed: {len(results['steps_completed'])}")
    logger.info(f"Files Created: {len(results['files_created'])}")
    logger.info(f"Services Created: {len(results['services_created'])}")
    logger.info(f"Commands to Run: {len(results['commands_to_run'])}")
    logger.info(f"Errors: {len(results['errors'])}")
    
    if results["files_created"]:
        logger.info("\\nFiles Created:")
        for file_path in results["files_created"]:
            logger.info(f"  - {file_path}")
    
    if results["services_created"]:
        logger.info("\\nServices Created:")
        for service in results["services_created"]:
            logger.info(f"  - {service}")
    
    if results["commands_to_run"]:
        logger.info("\\nCommands to Run:")
        for command in results["commands_to_run"]:
            logger.info(f"  - {command}")
    
    if results["errors"]:
        logger.info("\\nErrors:")
        for error in results["errors"]:
            logger.error(f"  - {error}")
    
    logger.info(f"\\nDetailed report: {report_file}")
    
    if not results["success"]:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())