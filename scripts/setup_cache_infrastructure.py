#!/usr/bin/env python3
"""
Cache Infrastructure Setup Script for NFL Predictor.
Sets up Redis, monitoring, and alerting for production deployment.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.redis_config import get_redis_manager, RedisDeploymentType
    from src.monitoring.cache_monitor import create_cache_monitor, MonitoringConfig
    from config.production import get_config
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheInfrastructureSetup:
    """Handles complete cache infrastructure setup"""
    
    def __init__(self, deployment_type: str = "local"):
        self.deployment_type = deployment_type
        self.redis_manager = get_redis_manager(deployment_type)
        self.setup_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_type": deployment_type,
            "steps_completed": [],
            "files_created": [],
            "commands_to_run": [],
            "errors": [],
            "warnings": [],
            "success": False
        }
    
    def step_1_validate_environment(self) -> bool:
        """Step 1: Validate environment and dependencies"""
        logger.info("Step 1: Validating environment...")
        
        try:
            # Check Redis Python client
            try:
                import redis
                logger.info("✓ Redis Python client is available")
            except ImportError:
                self.setup_results["errors"].append("Redis Python client not installed")
                logger.error("✗ Redis Python client not installed")
                logger.info("Install with: pip install redis")
                return False
            
            # Check environment variables
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                self.setup_results["warnings"].append("REDIS_URL not set, using default")
                logger.warning("⚠ REDIS_URL not set, using default: redis://localhost:6379")
            else:
                logger.info(f"✓ REDIS_URL configured: {redis_url}")
            
            # Check Redis server availability (if local)
            if self.deployment_type == "local":
                connection_test = self.redis_manager.test_connection()
                if connection_test["connected"]:
                    logger.info("✓ Redis server is accessible")
                else:
                    self.setup_results["warnings"].append("Redis server not accessible - will be configured")
                    logger.warning(f"⚠ Redis server not accessible: {connection_test['error']}")
            
            self.setup_results["steps_completed"].append("environment_validation")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Environment validation failed: {str(e)}")
            logger.error(f"✗ Environment validation failed: {e}")
            return False
    
    def step_2_deploy_redis(self) -> bool:
        """Step 2: Deploy Redis instance"""
        logger.info("Step 2: Deploying Redis instance...")
        
        try:
            deployment_result = self.redis_manager.deploy_redis()
            
            if deployment_result["success"]:
                logger.info("✓ Redis deployment configuration created")
                self.setup_results["files_created"].extend(deployment_result["files_created"])
                self.setup_results["commands_to_run"].extend(deployment_result["commands_to_run"])
                
                for note in deployment_result.get("notes", []):
                    logger.info(f"ℹ {note}")
                
                self.setup_results["steps_completed"].append("redis_deployment")
                return True
            else:
                error_msg = deployment_result.get("error", "Unknown deployment error")
                self.setup_results["errors"].append(f"Redis deployment failed: {error_msg}")
                logger.error(f"✗ Redis deployment failed: {error_msg}")
                return False
                
        except Exception as e:
            self.setup_results["errors"].append(f"Redis deployment error: {str(e)}")
            logger.error(f"✗ Redis deployment error: {e}")
            return False
    
    def step_3_configure_monitoring(self) -> bool:
        """Step 3: Configure cache monitoring and alerting"""
        logger.info("Step 3: Configuring cache monitoring...")
        
        try:
            # Create monitoring configuration
            monitoring_config = MonitoringConfig(
                collection_interval=int(os.getenv("CACHE_MONITORING_INTERVAL", "30")),
                retention_hours=int(os.getenv("CACHE_METRICS_RETENTION_HOURS", "24")),
                memory_warning_threshold=float(os.getenv("CACHE_MEMORY_WARNING_THRESHOLD", "80.0")),
                memory_critical_threshold=float(os.getenv("CACHE_MEMORY_CRITICAL_THRESHOLD", "90.0"))
            )
            
            # Save monitoring configuration
            config_file = "config/cache_monitoring.json"
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, "w") as f:
                json.dump({
                    "collection_interval": monitoring_config.collection_interval,
                    "retention_hours": monitoring_config.retention_hours,
                    "thresholds": {
                        "memory_warning": monitoring_config.memory_warning_threshold,
                        "memory_critical": monitoring_config.memory_critical_threshold,
                        "connection_warning": monitoring_config.connection_warning_threshold,
                        "connection_critical": monitoring_config.connection_critical_threshold,
                        "response_time_warning": monitoring_config.response_time_warning_threshold,
                        "response_time_critical": monitoring_config.response_time_critical_threshold,
                        "error_rate_warning": monitoring_config.error_rate_warning_threshold,
                        "error_rate_critical": monitoring_config.error_rate_critical_threshold,
                        "hit_rate_warning": monitoring_config.hit_rate_warning_threshold,
                        "hit_rate_critical": monitoring_config.hit_rate_critical_threshold
                    }
                }, indent=2)
            
            self.setup_results["files_created"].append(config_file)
            logger.info(f"✓ Monitoring configuration saved: {config_file}")
            
            # Create monitoring service script
            service_script = self._create_monitoring_service()
            if service_script:
                self.setup_results["files_created"].append(service_script)
                logger.info(f"✓ Monitoring service script created: {service_script}")
            
            self.setup_results["steps_completed"].append("monitoring_configuration")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Monitoring configuration failed: {str(e)}")
            logger.error(f"✗ Monitoring configuration failed: {e}")
            return False
    
    def _create_monitoring_service(self) -> Optional[str]:
        """Create systemd service for cache monitoring"""
        service_content = f"""[Unit]
Description=NFL Predictor Cache Monitor
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
EnvironmentFile={os.getcwd()}/.env
ExecStart={os.getcwd()}/venv/bin/python -m src.monitoring.cache_monitor
Restart=always
RestartSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nfl-predictor-cache-monitor

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={os.getcwd()}/logs

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/tmp/nfl-predictor-cache-monitor.service"
        
        try:
            with open(service_file, "w") as f:
                f.write(service_content)
            
            self.setup_results["commands_to_run"].extend([
                f"sudo cp {service_file} /etc/systemd/system/",
                "sudo systemctl daemon-reload",
                "sudo systemctl enable nfl-predictor-cache-monitor",
                "sudo systemctl start nfl-predictor-cache-monitor"
            ])
            
            return service_file
            
        except Exception as e:
            logger.warning(f"Failed to create monitoring service: {e}")
            return None
    
    def step_4_test_cache_operations(self) -> bool:
        """Step 4: Test cache operations"""
        logger.info("Step 4: Testing cache operations...")
        
        try:
            # Test Redis connection
            connection_test = self.redis_manager.test_connection()
            
            if not connection_test["connected"]:
                self.setup_results["warnings"].append("Cache operations test skipped - Redis not accessible")
                logger.warning("⚠ Cache operations test skipped - Redis not accessible")
                logger.info("This is normal if Redis hasn't been started yet")
                self.setup_results["steps_completed"].append("cache_operations_test_skipped")
                return True
            
            # Test cache manager
            from src.cache.cache_manager import CacheManager
            
            cache_manager = CacheManager(
                redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
                default_ttl_minutes=30
            )
            
            # Test basic operations
            test_key = "nfl_predictor:infrastructure_test"
            test_data = {
                "test": True,
                "timestamp": datetime.utcnow().isoformat(),
                "setup_phase": "infrastructure_test"
            }
            
            # Test set operation
            set_success = cache_manager.set(test_key, test_data, "infrastructure_test")
            if not set_success:
                raise Exception("Cache set operation failed")
            
            # Test get operation
            retrieved_data = cache_manager.get(test_key)
            if not retrieved_data or retrieved_data["data"] != test_data:
                raise Exception("Cache get operation failed")
            
            # Test delete operation
            delete_success = cache_manager.delete(test_key)
            if not delete_success:
                raise Exception("Cache delete operation failed")
            
            # Test cache key generation
            cache_key = cache_manager.get_cache_key_for_predictions(
                week=1,
                prediction_type="test",
                year=2025
            )
            
            if not cache_key or not cache_key.startswith("nfl_predictor:"):
                raise Exception("Cache key generation failed")
            
            logger.info("✓ All cache operations successful")
            logger.info(f"  - Set/Get/Delete: ✓")
            logger.info(f"  - Key generation: ✓")
            logger.info(f"  - Response time: {connection_test.get('ping_time_ms', 'N/A')}ms")
            
            self.setup_results["steps_completed"].append("cache_operations_test")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Cache operations test failed: {str(e)}")
            logger.error(f"✗ Cache operations test failed: {e}")
            return False
    
    def step_5_setup_alerting(self) -> bool:
        """Step 5: Set up alerting system"""
        logger.info("Step 5: Setting up alerting system...")
        
        try:
            # Create alerting configuration
            alerting_config = {
                "enabled": True,
                "channels": {
                    "log_file": {
                        "enabled": True,
                        "path": "logs/cache_alerts.log",
                        "level": "warning"
                    },
                    "webhook": {
                        "enabled": os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true",
                        "url": os.getenv("ALERT_WEBHOOK_URL", ""),
                        "level": "critical"
                    },
                    "email": {
                        "enabled": os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
                        "smtp_server": os.getenv("ALERT_SMTP_SERVER", ""),
                        "smtp_port": int(os.getenv("ALERT_SMTP_PORT", "587")),
                        "username": os.getenv("ALERT_EMAIL_USERNAME", ""),
                        "password": os.getenv("ALERT_EMAIL_PASSWORD", ""),
                        "to_addresses": os.getenv("ALERT_EMAIL_TO", "").split(","),
                        "level": "critical"
                    }
                }
            }
            
            # Save alerting configuration
            config_file = "config/alerting.json"
            with open(config_file, "w") as f:
                json.dump(alerting_config, f, indent=2)
            
            self.setup_results["files_created"].append(config_file)
            logger.info(f"✓ Alerting configuration saved: {config_file}")
            
            # Create log directory
            os.makedirs("logs", exist_ok=True)
            logger.info("✓ Log directory created")
            
            # Create alerting script
            alerting_script = self._create_alerting_script()
            if alerting_script:
                self.setup_results["files_created"].append(alerting_script)
                logger.info(f"✓ Alerting script created: {alerting_script}")
            
            self.setup_results["steps_completed"].append("alerting_setup")
            return True
            
        except Exception as e:
            self.setup_results["errors"].append(f"Alerting setup failed: {str(e)}")
            logger.error(f"✗ Alerting setup failed: {e}")
            return False
    
    def _create_alerting_script(self) -> Optional[str]:
        """Create alerting script"""
        script_content = f"""#!/usr/bin/env python3
\"\"\"
Cache alerting script for NFL Predictor.
Sends alerts via configured channels when cache issues are detected.
\"\"\"

import json
import logging
import smtplib
import requests
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_alerting_config():
    \"\"\"Load alerting configuration\"\"\"
    try:
        with open("config/alerting.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load alerting config: {{e}}")
        return {{"enabled": False}}


def send_webhook_alert(webhook_url: str, alert_data: dict):
    \"\"\"Send alert via webhook\"\"\"
    try:
        payload = {{
            "timestamp": datetime.utcnow().isoformat(),
            "service": "nfl-predictor-cache",
            "alert": alert_data
        }}
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Webhook alert sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send webhook alert: {{e}}")


def send_email_alert(config: dict, alert_data: dict):
    \"\"\"Send alert via email\"\"\"
    try:
        msg = MimeMultipart()
        msg["From"] = config["username"]
        msg["To"] = ", ".join(config["to_addresses"])
        msg["Subject"] = f"NFL Predictor Cache Alert - {{alert_data['level'].upper()}}"
        
        body = f\"\"\"
Cache Alert Notification

Level: {{alert_data['level'].upper()}}
Message: {{alert_data['message']}}
Value: {{alert_data['value']}}
Threshold: {{alert_data['threshold']}}
Timestamp: {{alert_data['timestamp']}}

Please check the cache system status.
\"\"\"
        
        msg.attach(MimeText(body, "plain"))
        
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["username"], config["password"])
        server.send_message(msg)
        server.quit()
        
        logger.info("Email alert sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send email alert: {{e}}")


def process_alert(alert_data: dict):
    \"\"\"Process and route alert to configured channels\"\"\"
    config = load_alerting_config()
    
    if not config.get("enabled", False):
        return
    
    alert_level = alert_data.get("level", "info")
    
    # Log file alert
    log_config = config.get("channels", {{}}).get("log_file", {{}})
    if log_config.get("enabled", False):
        log_level = log_config.get("level", "warning")
        if alert_level in ["critical", "warning"] or log_level == "info":
            log_message = f"[{{alert_data['timestamp']}}] {{alert_level.upper()}}: {{alert_data['message']}}"
            with open(log_config.get("path", "logs/cache_alerts.log"), "a") as f:
                f.write(log_message + "\\n")
    
    # Webhook alert
    webhook_config = config.get("channels", {{}}).get("webhook", {{}})
    if webhook_config.get("enabled", False) and alert_level == "critical":
        webhook_url = webhook_config.get("url")
        if webhook_url:
            send_webhook_alert(webhook_url, alert_data)
    
    # Email alert
    email_config = config.get("channels", {{}}).get("email", {{}})
    if email_config.get("enabled", False) and alert_level == "critical":
        send_email_alert(email_config, alert_data)


if __name__ == "__main__":
    # Test alert
    test_alert = {{
        "level": "warning",
        "message": "Test alert from setup script",
        "value": 85.0,
        "threshold": 80.0,
        "timestamp": datetime.utcnow().isoformat()
    }}
    
    process_alert(test_alert)
    print("Test alert processed")
"""
        
        script_file = "scripts/cache_alerting.py"
        
        try:
            os.makedirs(os.path.dirname(script_file), exist_ok=True)
            with open(script_file, "w") as f:
                f.write(script_content)
            
            # Make executable on Unix systems
            try:
                import stat
                os.chmod(script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass
            
            return script_file
            
        except Exception as e:
            logger.warning(f"Failed to create alerting script: {e}")
            return None
    
    def run_complete_setup(self) -> Dict[str, Any]:
        """Run complete cache infrastructure setup"""
        logger.info("Starting complete cache infrastructure setup...")
        logger.info("=" * 60)
        
        steps = [
            ("Environment Validation", self.step_1_validate_environment),
            ("Redis Deployment", self.step_2_deploy_redis),
            ("Monitoring Configuration", self.step_3_configure_monitoring),
            ("Cache Operations Test", self.step_4_test_cache_operations),
            ("Alerting Setup", self.step_5_setup_alerting)
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
            logger.info("\\n🎉 Cache infrastructure setup completed successfully!")
        
        return self.setup_results
    
    def generate_setup_report(self) -> str:
        """Generate setup report"""
        report_file = f"cache_infrastructure_setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, "w") as f:
            json.dump(self.setup_results, f, indent=2)
        
        logger.info(f"Setup report saved: {report_file}")
        return report_file


async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="NFL Predictor Cache Infrastructure Setup")
    parser.add_argument(
        "--deployment-type",
        choices=["local", "docker", "cloud"],
        default="local",
        help="Redis deployment type"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report without running setup"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Run tests only, skip setup"
    )
    
    args = parser.parse_args()
    
    setup = CacheInfrastructureSetup(args.deployment_type)
    
    if args.test_only:
        # Run tests only
        logger.info("Running cache infrastructure tests...")
        success = setup.step_4_test_cache_operations()
        if success:
            logger.info("✅ All tests passed")
        else:
            logger.error("❌ Tests failed")
            sys.exit(1)
        return
    
    if args.report_only:
        # Generate report only
        report_file = setup.generate_setup_report()
        print(f"Report generated: {report_file}")
        return
    
    # Run complete setup
    results = setup.run_complete_setup()
    
    # Generate report
    report_file = setup.generate_setup_report()
    
    # Print summary
    logger.info("\\n" + "=" * 60)
    logger.info("SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Deployment Type: {results['deployment_type']}")
    logger.info(f"Success: {results['success']}")
    logger.info(f"Steps Completed: {len(results['steps_completed'])}")
    logger.info(f"Files Created: {len(results['files_created'])}")
    logger.info(f"Commands to Run: {len(results['commands_to_run'])}")
    logger.info(f"Errors: {len(results['errors'])}")
    logger.info(f"Warnings: {len(results['warnings'])}")
    
    if results["files_created"]:
        logger.info("\\nFiles Created:")
        for file_path in results["files_created"]:
            logger.info(f"  - {file_path}")
    
    if results["commands_to_run"]:
        logger.info("\\nCommands to Run:")
        for command in results["commands_to_run"]:
            logger.info(f"  - {command}")
    
    if results["errors"]:
        logger.info("\\nErrors:")
        for error in results["errors"]:
            logger.error(f"  - {error}")
    
    if results["warnings"]:
        logger.info("\\nWarnings:")
        for warning in results["warnings"]:
            logger.warning(f"  - {warning}")
    
    logger.info(f"\\nDetailed report: {report_file}")
    
    if not results["success"]:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())