#!/usr/bin/env python3
"""
System Alerting and Notification System for NFL Expert Prediction System.
Monitors system health and sends alerts for critical issues.
"""

import asynci
gging
import sys
import os
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.production_deployment import get_deployment_manager
from src.admin.system_administration import get_health_monitor


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    component: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """Manages system alerts and notifications"""

    def __init__(self):
        self.logger = logging.getLogger("alert_manager")
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels = []

        # Load configuration
        self._load_configuration()

    def _load_configuration(self):
        """Load alerting configuration"""
        # Email configuration
        self.email_config = {
            "smtp_server": os.getenv("ALERT_SMTP_SERVER", "localhost"),
            "smtp_port": int(os.getenv("ALERT_SMTP_PORT", "587")),
            "username": os.getenv("ALERT_EMAIL_USERNAME"),
            "password": os.getenv("ALERT_EMAIL_PASSWORD"),
            "from_email": os.getenv("ALERT_FROM_EMAIL", "nfl-system@localhost"),
            "to_emails": os.getenv("ALERT_TO_EMAILS", "").split(",")
        }

        # Slack configuration
        self.slack_config = {
            "webhook_url": os.getenv("ALERT_SLACK_WEBHOOK"),
            "channel": os.getenv("ALERT_SLACK_CHANNEL", "#alerts")
        }

        # Webhook configuration
        self.webhook_config = {
            "url": os.getenv("ALERT_WEBHOOK_URL"),
            "headers": json.loads(os.getenv("ALERT_WEBHOOK_HEADERS", "{}"))
        }

        # Alert thresholds
        self.thresholds = {
            "database_connection_usage": float(os.getenv("ALERT_DB_CONNECTION_THRESHOLD", "0.85")),
            "memory_usage": float(os.getenv("ALERT_MEMORY_THRESHOLD", "0.90")),
            "error_rate": float(os.getenv("ALERT_ERROR_RATE_THRESHOLD", "0.05")),
            "expert_failure_rate": float(os.getenv("ALERT_EXPERT_FAILURE_THRESHOLD", "0.10")),
            "response_time": float(os.getenv("ALERT_RESPONSE_TIME_THRESHOLD", "2.0"))
        }

    async def check_system_health(self):
        """Check system health and generate alerts"""
        try:
            health_monitor = await get_health_monitor()
            health_status = await health_monitor.get_comprehensive_health_status()

            # Process health alerts
            for alert_data in health_status.alerts:
                await self._process_health_alert(alert_data)

            # Check custom thresholds
            await self._check_custom_thresholds(health_status)

            # Resolve alerts that are no longer active
            await self._resolve_inactive_alerts(health_status)

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            await self._create_alert(
                "system_health_check",
                AlertSeverity.CRITICAL,
                "system",
                f"Health check system failure: {str(e)}",
                {"error": str(e)}
            )

    async def _process_health_alert(self, alert_data: Dict[str, Any]):
        """Process a health alert"""
        alert_id = f"{alert_data['component']}_{alert_data['severity']}"
        severity = AlertSeverity(alert_data["severity"])

        # Check if this is a new alert
        if alert_id not in self.active_alerts:
            await self._create_alert(
                alert_id,
                severity,
                alert_data["component"],
                alert_data["message"],
                alert_data
            )

    async def _check_custom_thresholds(self, health_status):
        """Check custom alert thresholds"""
        # Database connection usage
        if hasattr(health_status, 'database_health'):
            db_health = health_status.database_health
            if "connection_usage" in db_health:
                usage = db_health["connection_usage"]
                if usage > self.thresholds["database_connection_usage"]:
                    await self._create_alert(
                        "database_connection_high",
                        AlertSeverity.WARNING,
                        "database",
                        f"High database connection usage: {usage:.1%}",
                        {"usage": usage, "threshold": self.thresholds["database_connection_usage"]}
                    )

        # Expert system performance
        if hasattr(health_status, 'expert_system_health'):
            expert_health = health_status.expert_system_health
            if "active_experts" in expert_health:
                active_experts = expert_health["active_experts"]
                if active_experts < 10:  # Minimum expected experts
                    await self._create_alert(
                        "expert_system_low_activity",
                        AlertSeverity.WARNING,
                        "expert_system",
                        f"Low expert activity: {active_experts} active experts",
                        {"active_experts": active_experts, "minimum_expected": 10}
                    )

    async def _resolve_inactive_alerts(self, health_status):
        """Resolve alerts that are no longer active"""
        current_alert_ids = set()

        # Collect current alert IDs from health status
        for alert_data in health_status.alerts:
            alert_id = f"{alert_data['component']}_{alert_data['severity']}"
            current_alert_ids.add(alert_id)

        # Resolve alerts that are no longer present
        for alert_id in list(self.active_alerts.keys()):
            if alert_id not in current_alert_ids:
                await self._resolve_alert(alert_id)

    async def _create_alert(self, alert_id: str, severity: AlertSeverity,
                          component: str, message: str, details: Dict[str, Any]):
        """Create a new alert"""
        # Check if alert already exists
        if alert_id in self.active_alerts:
            return

        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            severity=severity,
            component=component,
            message=message,
            details=details
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Send notifications
        await self._send_notifications(alert)

        self.logger.warning(f"ALERT CREATED: {severity.value.upper()} - {component} - {message}")

    async def _resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()

            del self.active_alerts[alert_id]

            # Send resolution notification
            await self._send_resolution_notification(alert)

            self.logger.info(f"ALERT RESOLVED: {alert.component} - {alert.message}")

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        # Email notification
        if self.email_config["username"] and self.email_config["to_emails"]:
            await self._send_email_notification(alert)

        # Slack notification
        if self.slack_config["webhook_url"]:
            await self._send_slack_notification(alert)

        # Webhook notification
        if self.webhook_config["url"]:
            await self._send_webhook_notification(alert)

        # Log notification (always enabled)
        await self._send_log_notification(alert)

    async def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["from_email"]
            msg["To"] = ", ".join(self.email_config["to_emails"])
            msg["Subject"] = f"NFL System Alert: {alert.severity.value.upper()} - {alert.component}"

            body = f"""
NFL Expert Prediction System Alert

Severity: {alert.severity.value.upper()}
Component: {alert.component}
Message: {alert.message}
Timestamp: {alert.timestamp.isoformat()}

Details:
{json.dumps(alert.details, indent=2)}

Please investigate this issue promptly.
            """

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Email notification sent for alert {alert.id}")

        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")

    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        try:
            import aiohttp

            color = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.CRITICAL: "danger"
            }[alert.severity]

            payload = {
                "channel": self.slack_config["channel"],
                "username": "NFL System Monitor",
                "icon_emoji": ":warning:",
                "attachments": [{
                    "color": color,
                    "title": f"{alert.severity.value.upper()} Alert: {alert.component}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.isoformat(),
                            "short": True
                        },
                        {
                            "title": "Component",
                            "value": alert.component,
                            "short": True
                        }
                    ],
                    "footer": "NFL Expert Prediction System",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_config["webhook_url"], json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack notification sent for alert {alert.id}")
                    else:
                        self.logger.error(f"Slack notification failed: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")

    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        try:
            import aiohttp

            payload = alert.to_dict()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_config["url"],
                    json=payload,
                    headers=self.webhook_config["headers"]
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook notification sent for alert {alert.id}")
                    else:
                        self.logger.error(f"Webhook notification failed: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")

    async def _send_log_notification(self, alert: Alert):
        """Send log notification"""
        log_entry = {
            "type": "alert",
            "alert": alert.to_dict()
        }

        # Save to alerts log file
        os.makedirs("./logs/alerts", exist_ok=True)
        log_file = f"./logs/alerts/alerts_{datetime.now().strftime('%Y%m%d')}.json"

        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry, default=str) + "\n")

    async def _send_resolution_notification(self, alert: Alert):
        """Send alert resolution notification"""
        self.logger.info(f"Alert resolved: {alert.component} - {alert.message}")

        # Could send resolution notifications through same channels
        # For now, just log it

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert.to_dict()
            for alert in self.alert_history
            if alert.timestamp > cutoff
        ]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        recent_alerts = [a for a in self.alert_history if a.timestamp > last_24h]
        weekly_alerts = [a for a in self.alert_history if a.timestamp > last_7d]

        return {
            "active_alerts": len(self.active_alerts),
            "alerts_last_24h": len(recent_alerts),
            "alerts_last_7d": len(weekly_alerts),
            "critical_alerts_24h": len([a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]),
            "warning_alerts_24h": len([a for a in recent_alerts if a.severity == AlertSeverity.WARNING]),
            "most_common_components": self._get_most_common_components(weekly_alerts),
            "timestamp": now.isoformat()
        }

    def _get_most_common_components(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Get most common alert components"""
        component_counts = {}
        for alert in alerts:
            component_counts[alert.component] = component_counts.get(alert.component, 0) + 1

        return [
            {"component": component, "count": count}
            for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True)
        ]


class AlertMonitor:
    """Continuous alert monitoring service"""

    def __init__(self, check_interval: int = 300):  # 5 minutes
        self.logger = logging.getLogger("alert_monitor")
        self.check_interval = check_interval
        self.alert_manager = AlertManager()
        self.running = False

    async def start_monitoring(self):
        """Start continuous alert monitoring"""
        self.logger.info("Starting alert monitoring...")
        self.running = True

        while self.running:
            try:
                await self.alert_manager.check_system_health()
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Alert monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.running = False
        self.logger.info("Alert monitoring stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get monitoring status"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "alert_summary": self.alert_manager.get_alert_summary()
        }


async def main():
    """Main function for alert system"""
    import argparse

    parser = argparse.ArgumentParser(description="NFL Expert System Alert Manager")
    parser.add_argument("command", choices=[
        "monitor", "status", "history", "test"
    ], help="Alert command to run")
    parser.add_argument("--interval", type=int, default=300, help="Monitoring interval in seconds")
    parser.add_argument("--hours", type=int, default=24, help="Hours for history command")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if args.command == "monitor":
        # Start alert monitoring
        monitor = AlertMonitor(args.interval)
        await monitor.start_monitoring()

    elif args.command == "status":
        # Show alert status
        alert_manager = AlertManager()
        summary = alert_manager.get_alert_summary()
        active_alerts = alert_manager.get_active_alerts()

        print("Alert System Status:")
        print(json.dumps(summary, indent=2))
        print("\nActive Alerts:")
        print(json.dumps(active_alerts, indent=2))

    elif args.command == "history":
        # Show alert history
        alert_manager = AlertManager()
        history = alert_manager.get_alert_history(args.hours)

        print(f"Alert History (last {args.hours} hours):")
        print(json.dumps(history, indent=2))

    elif args.command == "test":
        # Test alert system
        alert_manager = AlertManager()
        await alert_manager._create_alert(
            "test_alert",
            AlertSeverity.WARNING,
            "test_system",
            "This is a test alert",
            {"test": True, "timestamp": datetime.now().isoformat()}
        )
        print("Test alert created")


if __name__ == "__main__":
    asyncio.run(main())
