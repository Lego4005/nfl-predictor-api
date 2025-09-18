"""
Notification System for Betting Analytics

Handles various notification channels including:
- Email alerts
- SMS notifications
- Webhook notifications
- Push notifications
- Slack/Discord integration
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import os
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    SLACK = "slack"
    DISCORD = "discord"

class AlertPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict = None
    min_priority: AlertPriority = AlertPriority.LOW

@dataclass
class Alert:
    """Alert object for notifications"""
    id: str
    title: str
    message: str
    priority: AlertPriority
    alert_type: str
    game_id: Optional[str] = None
    data: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class NotificationSystem:
    """Main notification system for betting alerts"""

    def __init__(self, config: Dict[str, NotificationConfig]):
        self.config = config
        self.session = aiohttp.ClientSession()
        self.delivery_history = []

        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')

        # SMS configuration (Twilio)
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from = os.getenv('TWILIO_FROM_NUMBER')

        # Webhook configurations
        self.webhook_urls = os.getenv('WEBHOOK_URLS', '').split(',')

        # Slack configuration
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')

        # Discord configuration
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')

    async def send_alert(self, alert: Alert, channels: Optional[List[NotificationChannel]] = None) -> Dict[str, bool]:
        """
        Send alert through specified channels

        Args:
            alert: Alert object to send
            channels: Specific channels to use (if None, uses all enabled channels)

        Returns:
            Dict mapping channel names to success status
        """
        if channels is None:
            channels = [config.channel for config in self.config.values()
                       if config.enabled and alert.priority.value >= config.min_priority.value]

        results = {}
        tasks = []

        for channel in channels:
            if channel in self.config:
                task = self._send_to_channel(alert, channel, self.config[channel])
                tasks.append((channel, task))

        if tasks:
            task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

            for (channel, _), result in zip(tasks, task_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to send alert to {channel.value}: {result}")
                    results[channel.value] = False
                else:
                    results[channel.value] = result

        # Log delivery
        self._log_delivery(alert, results)

        return results

    async def _send_to_channel(self, alert: Alert, channel: NotificationChannel, config: NotificationConfig) -> bool:
        """Send alert to specific channel"""
        try:
            if channel == NotificationChannel.EMAIL:
                return await self._send_email(alert, config.config or {})
            elif channel == NotificationChannel.SMS:
                return await self._send_sms(alert, config.config or {})
            elif channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(alert, config.config or {})
            elif channel == NotificationChannel.PUSH:
                return await self._send_push(alert, config.config or {})
            elif channel == NotificationChannel.SLACK:
                return await self._send_slack(alert, config.config or {})
            elif channel == NotificationChannel.DISCORD:
                return await self._send_discord(alert, config.config or {})
            else:
                logger.warning(f"Unknown notification channel: {channel}")
                return False
        except Exception as e:
            logger.error(f"Error sending to {channel.value}: {e}")
            return False

    async def _send_email(self, alert: Alert, config: Dict) -> bool:
        """Send email notification"""
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("Email credentials not configured")
            return False

        try:
            recipients = config.get('recipients', [])
            if not recipients:
                logger.warning("No email recipients configured")
                return False

            # Create email
            msg = MimeMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{alert.priority.name}] {alert.title}"

            # Email body
            body = self._format_email_body(alert)
            msg.attach(MimeText(body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully for alert {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _format_email_body(self, alert: Alert) -> str:
        """Format email body with HTML"""
        priority_colors = {
            AlertPriority.LOW: "#28a745",
            AlertPriority.MEDIUM: "#ffc107",
            AlertPriority.HIGH: "#fd7e14",
            AlertPriority.CRITICAL: "#dc3545"
        }

        color = priority_colors.get(alert.priority, "#6c757d")

        html_body = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0; font-size: 24px;">{alert.title}</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Priority: {alert.priority.name}</p>
                </div>

                <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-radius: 0 0 5px 5px;">
                    <p style="font-size: 16px; line-height: 1.5; margin-bottom: 20px;">{alert.message}</p>

                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: #495057;">Alert Details</h4>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 5px; font-weight: bold; color: #495057;">Type:</td>
                                <td style="padding: 5px;">{alert.alert_type}</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px; font-weight: bold; color: #495057;">Time:</td>
                                <td style="padding: 5px;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                            </tr>
                            {"<tr><td style='padding: 5px; font-weight: bold; color: #495057;'>Game:</td><td style='padding: 5px;'>" + alert.game_id + "</td></tr>" if alert.game_id else ""}
                        </table>
                    </div>

                    {self._format_alert_data_html(alert.data) if alert.data else ""}

                    <div style="text-align: center; margin-top: 20px;">
                        <a href="#" style="background-color: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Dashboard</a>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px;">
                    <p>NFL Predictor Betting Analytics Engine</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_body

    def _format_alert_data_html(self, data: Dict) -> str:
        """Format alert data as HTML table"""
        if not data:
            return ""

        html = "<div style='background-color: white; padding: 15px; border-radius: 5px;'>"
        html += "<h4 style='margin: 0 0 10px 0; color: #495057;'>Additional Information</h4>"
        html += "<table style='width: 100%; border-collapse: collapse;'>"

        for key, value in data.items():
            if isinstance(value, dict):
                continue  # Skip nested objects for simplicity

            display_key = key.replace('_', ' ').title()
            display_value = str(value)

            if isinstance(value, float):
                if 'percentage' in key.lower() or 'rate' in key.lower():
                    display_value = f"{value:.2%}"
                elif 'probability' in key.lower():
                    display_value = f"{value:.3f}"
                else:
                    display_value = f"{value:.2f}"

            html += f"<tr><td style='padding: 5px; font-weight: bold; color: #495057;'>{display_key}:</td>"
            html += f"<td style='padding: 5px;'>{display_value}</td></tr>"

        html += "</table></div>"
        return html

    async def _send_sms(self, alert: Alert, config: Dict) -> bool:
        """Send SMS notification via Twilio"""
        if not all([self.twilio_sid, self.twilio_token, self.twilio_from]):
            logger.warning("Twilio credentials not configured")
            return False

        recipients = config.get('recipients', [])
        if not recipients:
            logger.warning("No SMS recipients configured")
            return False

        try:
            # Format SMS message (limited to 160 characters)
            sms_message = f"🚨 {alert.title[:50]}...\n{alert.message[:80]}\nPriority: {alert.priority.name}"

            # Twilio API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"

            auth = aiohttp.BasicAuth(self.twilio_sid, self.twilio_token)

            success_count = 0
            for recipient in recipients:
                data = {
                    'From': self.twilio_from,
                    'To': recipient,
                    'Body': sms_message
                }

                async with self.session.post(url, data=data, auth=auth) as response:
                    if response.status == 201:
                        success_count += 1
                    else:
                        logger.error(f"Failed to send SMS to {recipient}: {response.status}")

            logger.info(f"SMS sent to {success_count}/{len(recipients)} recipients")
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    async def _send_webhook(self, alert: Alert, config: Dict) -> bool:
        """Send webhook notification"""
        urls = config.get('urls', self.webhook_urls)
        if not urls:
            logger.warning("No webhook URLs configured")
            return False

        try:
            payload = {
                'alert_id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'priority': alert.priority.name,
                'alert_type': alert.alert_type,
                'game_id': alert.game_id,
                'timestamp': alert.timestamp.isoformat(),
                'data': alert.data
            }

            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NFL-Predictor-Analytics/1.0'
            }

            success_count = 0
            for url in urls:
                if not url.strip():
                    continue

                async with self.session.post(url.strip(), json=payload, headers=headers, timeout=10) as response:
                    if response.status < 400:
                        success_count += 1
                    else:
                        logger.error(f"Webhook failed for {url}: {response.status}")

            logger.info(f"Webhook sent to {success_count}/{len(urls)} URLs")
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    async def _send_push(self, alert: Alert, config: Dict) -> bool:
        """Send push notification (Firebase/OneSignal)"""
        # This would integrate with push notification services
        # Implementation depends on chosen service (Firebase, OneSignal, etc.)
        logger.info("Push notification not implemented yet")
        return False

    async def _send_slack(self, alert: Alert, config: Dict) -> bool:
        """Send Slack notification"""
        webhook_url = config.get('webhook_url', self.slack_webhook)
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            # Format Slack message
            priority_colors = {
                AlertPriority.LOW: "good",
                AlertPriority.MEDIUM: "warning",
                AlertPriority.HIGH: "danger",
                AlertPriority.CRITICAL: "danger"
            }

            color = priority_colors.get(alert.priority, "good")

            slack_payload = {
                "username": "NFL Predictor Bot",
                "icon_emoji": ":football:",
                "attachments": [{
                    "color": color,
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {"title": "Priority", "value": alert.priority.name, "short": True},
                        {"title": "Type", "value": alert.alert_type, "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'), "short": False}
                    ]
                }]
            }

            if alert.game_id:
                slack_payload["attachments"][0]["fields"].append({
                    "title": "Game", "value": alert.game_id, "short": True
                })

            async with self.session.post(webhook_url, json=slack_payload) as response:
                success = response.status == 200
                if success:
                    logger.info("Slack notification sent successfully")
                else:
                    logger.error(f"Slack notification failed: {response.status}")
                return success

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def _send_discord(self, alert: Alert, config: Dict) -> bool:
        """Send Discord notification"""
        webhook_url = config.get('webhook_url', self.discord_webhook)
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        try:
            # Format Discord message
            priority_colors = {
                AlertPriority.LOW: 0x28a745,    # Green
                AlertPriority.MEDIUM: 0xffc107,  # Yellow
                AlertPriority.HIGH: 0xfd7e14,    # Orange
                AlertPriority.CRITICAL: 0xdc3545 # Red
            }

            color = priority_colors.get(alert.priority, 0x6c757d)

            embed = {
                "title": alert.title,
                "description": alert.message,
                "color": color,
                "timestamp": alert.timestamp.isoformat(),
                "fields": [
                    {"name": "Priority", "value": alert.priority.name, "inline": True},
                    {"name": "Type", "value": alert.alert_type, "inline": True}
                ]
            }

            if alert.game_id:
                embed["fields"].append({"name": "Game", "value": alert.game_id, "inline": True})

            discord_payload = {
                "username": "NFL Predictor Bot",
                "avatar_url": "https://example.com/bot-avatar.png",
                "embeds": [embed]
            }

            async with self.session.post(webhook_url, json=discord_payload) as response:
                success = response.status == 204
                if success:
                    logger.info("Discord notification sent successfully")
                else:
                    logger.error(f"Discord notification failed: {response.status}")
                return success

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def _log_delivery(self, alert: Alert, results: Dict[str, bool]):
        """Log notification delivery results"""
        delivery_record = {
            'alert_id': alert.id,
            'timestamp': datetime.utcnow(),
            'channels_attempted': list(results.keys()),
            'successful_channels': [ch for ch, success in results.items() if success],
            'failed_channels': [ch for ch, success in results.items() if not success],
            'success_rate': sum(results.values()) / len(results) if results else 0
        }

        self.delivery_history.append(delivery_record)

        # Keep only recent delivery history (last 1000 records)
        if len(self.delivery_history) > 1000:
            self.delivery_history = self.delivery_history[-1000:]

    async def bulk_send_alerts(self, alerts: List[Alert]) -> Dict[str, int]:
        """
        Send multiple alerts efficiently

        Args:
            alerts: List of alerts to send

        Returns:
            Dict with summary statistics
        """
        if not alerts:
            return {'total': 0, 'successful': 0, 'failed': 0}

        # Group alerts by priority for batching
        priority_groups = {}
        for alert in alerts:
            priority = alert.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(alert)

        total_sent = 0
        successful = 0
        failed = 0

        # Send high priority alerts first
        for priority in [AlertPriority.CRITICAL, AlertPriority.HIGH, AlertPriority.MEDIUM, AlertPriority.LOW]:
            if priority in priority_groups:
                batch_alerts = priority_groups[priority]

                # Send alerts in parallel batches
                batch_size = 10  # Adjust based on rate limits
                for i in range(0, len(batch_alerts), batch_size):
                    batch = batch_alerts[i:i + batch_size]

                    tasks = [self.send_alert(alert) for alert in batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        total_sent += 1
                        if isinstance(result, dict) and any(result.values()):
                            successful += 1
                        else:
                            failed += 1

                    # Small delay between batches to respect rate limits
                    if i + batch_size < len(batch_alerts):
                        await asyncio.sleep(0.1)

        return {
            'total': total_sent,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_sent if total_sent > 0 else 0
        }

    async def get_delivery_stats(self, hours: int = 24) -> Dict:
        """Get delivery statistics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        recent_deliveries = [
            record for record in self.delivery_history
            if record['timestamp'] >= cutoff_time
        ]

        if not recent_deliveries:
            return {'period_hours': hours, 'total_alerts': 0}

        total_alerts = len(recent_deliveries)
        total_channels_attempted = sum(len(record['channels_attempted']) for record in recent_deliveries)
        total_successful_channels = sum(len(record['successful_channels']) for record in recent_deliveries)

        channel_stats = {}
        for record in recent_deliveries:
            for channel in record['channels_attempted']:
                if channel not in channel_stats:
                    channel_stats[channel] = {'attempted': 0, 'successful': 0}
                channel_stats[channel]['attempted'] += 1

                if channel in record['successful_channels']:
                    channel_stats[channel]['successful'] += 1

        # Calculate success rates by channel
        for channel, stats in channel_stats.items():
            stats['success_rate'] = stats['successful'] / stats['attempted'] if stats['attempted'] > 0 else 0

        return {
            'period_hours': hours,
            'total_alerts': total_alerts,
            'total_channels_attempted': total_channels_attempted,
            'total_successful_channels': total_successful_channels,
            'overall_success_rate': total_successful_channels / total_channels_attempted if total_channels_attempted > 0 else 0,
            'channel_stats': channel_stats,
            'average_success_rate': np.mean([record['success_rate'] for record in recent_deliveries])
        }

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()