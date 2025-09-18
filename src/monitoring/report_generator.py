"""
Automated Performance Report Generator
Generates comprehensive performance reports with charts, insights, and recommendations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
import jinja2
import redis
from sqlalchemy import create_engine, text
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import base64
import io


class ReportGenerator:
    """Automated report generation for performance monitoring"""

    def __init__(self, redis_client: redis.Redis, db_engine, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.db_engine = db_engine
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Setup Jinja2 template environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

        # Report configuration
        self.sla_targets = config.get('sla_targets', {
            'api_response_time': 200,
            'prediction_accuracy': 0.75,
            'uptime': 0.999,
            'cache_hit_rate': 0.8
        })

    async def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive daily performance report"""
        if not date:
            date = datetime.utcnow().date()

        try:
            # Collect data for the day
            start_time = datetime.combine(date, datetime.min.time())
            end_time = start_time + timedelta(days=1)

            data = await self._collect_report_data(start_time, end_time)

            if not data['metrics']:
                return {'error': 'No data available for the specified date'}

            # Generate report components
            report = {
                'report_type': 'daily',
                'date': date.isoformat(),
                'period': f"{start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}",
                'generated_at': datetime.utcnow().isoformat(),
                'summary': await self._generate_summary(data),
                'sla_compliance': await self._calculate_sla_compliance(data),
                'performance_trends': await self._analyze_trends(data),
                'bottleneck_analysis': await self._analyze_bottlenecks(data),
                'recommendations': await self._generate_recommendations(data),
                'charts': await self._generate_charts(data),
                'detailed_metrics': await self._generate_detailed_metrics(data),
                'alerts': await self._get_alerts_for_period(start_time, end_time)
            }

            # Store report in Redis
            report_key = f"daily_report:{date.strftime('%Y-%m-%d')}"
            self.redis_client.setex(
                report_key,
                86400 * 7,  # Keep for 7 days
                json.dumps(report, default=str, cls=PlotlyJSONEncoder)
            )

            return report

        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return {'error': str(e)}

    async def generate_weekly_report(self, week_start: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive weekly performance report"""
        if not week_start:
            today = datetime.utcnow().date()
            week_start = today - timedelta(days=today.weekday())  # Start of current week

        try:
            start_time = datetime.combine(week_start, datetime.min.time())
            end_time = start_time + timedelta(days=7)

            data = await self._collect_report_data(start_time, end_time)

            if not data['metrics']:
                return {'error': 'No data available for the specified week'}

            report = {
                'report_type': 'weekly',
                'week_start': week_start.isoformat(),
                'period': f"{start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}",
                'generated_at': datetime.utcnow().isoformat(),
                'executive_summary': await self._generate_executive_summary(data),
                'sla_compliance': await self._calculate_sla_compliance(data),
                'performance_trends': await self._analyze_weekly_trends(data),
                'capacity_analysis': await self._analyze_capacity(data),
                'bottleneck_analysis': await self._analyze_bottlenecks(data),
                'cost_analysis': await self._analyze_costs(data),
                'recommendations': await self._generate_strategic_recommendations(data),
                'charts': await self._generate_weekly_charts(data),
                'detailed_analysis': await self._generate_detailed_analysis(data),
                'alerts_summary': await self._get_alerts_summary(start_time, end_time)
            }

            # Store report in Redis
            report_key = f"weekly_report:{week_start.strftime('%Y-W%U')}"
            self.redis_client.setex(
                report_key,
                86400 * 30,  # Keep for 30 days
                json.dumps(report, default=str, cls=PlotlyJSONEncoder)
            )

            return report

        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
            return {'error': str(e)}

    async def _collect_report_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Collect all data needed for report generation"""
        data = {
            'metrics': [],
            'alerts': [],
            'bottlenecks': [],
            'predictions': [],
            'api_logs': []
        }

        try:
            # Get metrics from Redis
            metrics_data = []
            for i in range(self.redis_client.llen('metrics_history')):
                metric_json = self.redis_client.lindex('metrics_history', i)
                if metric_json:
                    try:
                        metric = json.loads(metric_json)
                        metric_time = datetime.fromisoformat(metric['timestamp'])
                        if start_time <= metric_time < end_time:
                            metrics_data.append(metric)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

            data['metrics'] = sorted(metrics_data, key=lambda x: x['timestamp'])

            # Get prediction data from database
            with self.db_engine.connect() as conn:
                predictions_query = text("""
                    SELECT created_at, model_name, confidence_score, actual_result, predicted_result
                    FROM predictions
                    WHERE created_at >= :start_time AND created_at < :end_time
                    ORDER BY created_at
                """)
                predictions_result = conn.execute(predictions_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                data['predictions'] = [dict(row) for row in predictions_result]

                # Get API logs
                api_logs_query = text("""
                    SELECT timestamp, method, endpoint, status_code, response_time
                    FROM api_logs
                    WHERE timestamp >= :start_time AND timestamp < :end_time
                    ORDER BY timestamp
                """)
                api_logs_result = conn.execute(api_logs_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                data['api_logs'] = [dict(row) for row in api_logs_result]

            # Get bottleneck detections
            bottleneck_data = []
            for i in range(self.redis_client.llen('bottleneck_history')):
                bottleneck_json = self.redis_client.lindex('bottleneck_history', i)
                if bottleneck_json:
                    try:
                        bottleneck = json.loads(bottleneck_json)
                        bottleneck_time = datetime.fromisoformat(bottleneck['timestamp'])
                        if start_time <= bottleneck_time < end_time:
                            bottleneck_data.append(bottleneck)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

            data['bottlenecks'] = sorted(bottleneck_data, key=lambda x: x['timestamp'])

        except Exception as e:
            self.logger.error(f"Error collecting report data: {e}")

        return data

    async def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the report period"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        summary = {
            'total_api_requests': len(data['api_logs']),
            'total_predictions': len(data['predictions']),
            'average_response_time': metrics_df['api_response_time'].mean(),
            'peak_response_time': metrics_df['api_response_time'].max(),
            'average_prediction_accuracy': metrics_df['prediction_accuracy'].mean(),
            'average_cache_hit_rate': metrics_df['cache_hit_rate'].mean(),
            'peak_cpu_usage': metrics_df['system_cpu'].max(),
            'peak_memory_usage': metrics_df['system_memory'].max(),
            'total_alerts': len(data.get('alerts', [])),
            'total_bottlenecks': len(data.get('bottlenecks', [])),
            'uptime_percentage': self._calculate_uptime(data),
            'error_rate': self._calculate_error_rate(data)
        }

        return summary

    async def _generate_executive_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary for weekly reports"""
        summary = await self._generate_summary(data)

        # Add executive-level insights
        executive_summary = {
            **summary,
            'key_achievements': self._identify_achievements(data, summary),
            'major_issues': self._identify_major_issues(data, summary),
            'business_impact': self._assess_business_impact(data, summary),
            'resource_utilization': self._assess_resource_utilization(data, summary),
            'growth_metrics': self._calculate_growth_metrics(data)
        }

        return executive_summary

    async def _calculate_sla_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SLA compliance metrics"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        compliance = {}

        for metric, target in self.sla_targets.items():
            if metric not in metrics_df.columns:
                continue

            values = metrics_df[metric].dropna()
            if len(values) == 0:
                continue

            if metric in ['prediction_accuracy', 'cache_hit_rate', 'uptime']:
                # Higher is better
                compliance_rate = (values >= target).mean()
            else:
                # Lower is better (response time, error rate)
                compliance_rate = (values <= target).mean()

            compliance[metric] = {
                'target': target,
                'compliance_rate': compliance_rate,
                'average_value': values.mean(),
                'worst_value': values.min() if metric in ['prediction_accuracy', 'cache_hit_rate'] else values.max(),
                'trend': self._calculate_trend(values)
            }

        return compliance

    async def _analyze_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        trends = {}

        for column in metrics_df.select_dtypes(include=[np.number]).columns:
            if column == 'timestamp':
                continue

            values = metrics_df[column].dropna()
            if len(values) < 2:
                continue

            # Calculate trend using linear regression slope
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)

            # Calculate trend strength (R-squared)
            predicted = slope * x + intercept
            ss_res = np.sum((values - predicted) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            trends[column] = {
                'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                'slope': float(slope),
                'strength': float(r_squared),
                'significance': 'strong' if abs(r_squared) > 0.7 else 'moderate' if abs(r_squared) > 0.3 else 'weak'
            }

        return trends

    async def _analyze_weekly_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends with weekly context"""
        trends = await self._analyze_trends(data)

        # Add weekly-specific analysis
        weekly_analysis = {}
        for metric, trend in trends.items():
            weekly_analysis[metric] = {
                **trend,
                'weekly_impact': self._assess_weekly_impact(metric, trend),
                'forecast': self._generate_forecast(metric, trend)
            }

        return weekly_analysis

    async def _analyze_bottlenecks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bottleneck patterns and impacts"""
        bottlenecks = data.get('bottlenecks', [])

        if not bottlenecks:
            return {'total_bottlenecks': 0}

        # Count by type and severity
        type_counts = {}
        severity_counts = {}
        component_impacts = {}

        for bottleneck in bottlenecks:
            btype = bottleneck.get('type', 'unknown')
            severity = bottleneck.get('severity', 'unknown')
            component = bottleneck.get('affected_component', 'unknown')

            type_counts[btype] = type_counts.get(btype, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            if component not in component_impacts:
                component_impacts[component] = []
            component_impacts[component].append(bottleneck.get('impact_score', 0))

        # Calculate component impact scores
        for component in component_impacts:
            scores = component_impacts[component]
            component_impacts[component] = {
                'incident_count': len(scores),
                'average_impact': sum(scores) / len(scores),
                'max_impact': max(scores)
            }

        return {
            'total_bottlenecks': len(bottlenecks),
            'type_distribution': type_counts,
            'severity_distribution': severity_counts,
            'component_impacts': component_impacts,
            'most_problematic_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            'highest_impact_component': max(component_impacts.items(),
                                          key=lambda x: x[1]['average_impact'])[0] if component_impacts else None
        }

    async def _analyze_capacity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system capacity and utilization"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        capacity_metrics = {
            'cpu_utilization': {
                'current_average': metrics_df['system_cpu'].mean(),
                'peak_usage': metrics_df['system_cpu'].max(),
                'capacity_remaining': 100 - metrics_df['system_cpu'].max(),
                'utilization_trend': self._calculate_trend(metrics_df['system_cpu'])
            },
            'memory_utilization': {
                'current_average': metrics_df['system_memory'].mean(),
                'peak_usage': metrics_df['system_memory'].max(),
                'capacity_remaining': 100 - metrics_df['system_memory'].max(),
                'utilization_trend': self._calculate_trend(metrics_df['system_memory'])
            },
            'database_capacity': {
                'average_connections': metrics_df['database_connections'].mean(),
                'peak_connections': metrics_df['database_connections'].max(),
                'connection_trend': self._calculate_trend(metrics_df['database_connections'])
            },
            'websocket_capacity': {
                'average_connections': metrics_df['websocket_connections'].mean(),
                'peak_connections': metrics_df['websocket_connections'].max(),
                'connection_trend': self._calculate_trend(metrics_df['websocket_connections'])
            }
        }

        # Calculate capacity warnings
        warnings = []
        if capacity_metrics['cpu_utilization']['peak_usage'] > 80:
            warnings.append("CPU utilization approaching capacity limits")
        if capacity_metrics['memory_utilization']['peak_usage'] > 85:
            warnings.append("Memory utilization approaching capacity limits")

        capacity_metrics['warnings'] = warnings
        capacity_metrics['overall_capacity_health'] = self._assess_capacity_health(capacity_metrics)

        return capacity_metrics

    async def _analyze_costs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost implications of performance metrics"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        # Estimate costs based on resource usage
        # These are example calculations - adjust based on your infrastructure
        cost_analysis = {
            'compute_costs': {
                'cpu_hours': metrics_df['system_cpu'].mean() / 100 * len(metrics_df) / 24,
                'estimated_cost': metrics_df['system_cpu'].mean() / 100 * len(metrics_df) / 24 * 0.10  # $0.10/hour
            },
            'storage_costs': {
                'cache_usage_gb': 10,  # Placeholder - would come from actual cache size
                'estimated_cost': 10 * 0.023  # $0.023/GB/month
            },
            'network_costs': {
                'api_requests': len(data.get('api_logs', [])),
                'estimated_cost': len(data.get('api_logs', [])) * 0.0001  # $0.0001/request
            }
        }

        total_estimated_cost = (
            cost_analysis['compute_costs']['estimated_cost'] +
            cost_analysis['storage_costs']['estimated_cost'] +
            cost_analysis['network_costs']['estimated_cost']
        )

        cost_analysis['total_estimated_cost'] = total_estimated_cost
        cost_analysis['cost_optimization_opportunities'] = self._identify_cost_optimizations(data)

        return cost_analysis

    async def _generate_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # Analyze metrics for recommendations
        metrics_df = pd.DataFrame(data['metrics'])
        if not metrics_df.empty:
            # Performance recommendations
            if metrics_df['api_response_time'].mean() > 500:
                recommendations.append({
                    'priority': 'high',
                    'category': 'performance',
                    'title': 'Optimize API Response Time',
                    'description': 'Average API response time exceeds 500ms',
                    'suggested_actions': [
                        'Review slow database queries',
                        'Implement API response caching',
                        'Optimize algorithm efficiency',
                        'Consider load balancing'
                    ],
                    'expected_impact': 'Reduce response time by 20-40%'
                })

            if metrics_df['cache_hit_rate'].mean() < 0.7:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'optimization',
                    'title': 'Improve Cache Strategy',
                    'description': 'Cache hit rate is below optimal threshold',
                    'suggested_actions': [
                        'Analyze cache key patterns',
                        'Implement cache warming',
                        'Increase cache size',
                        'Review cache TTL settings'
                    ],
                    'expected_impact': 'Improve response time and reduce database load'
                })

            if metrics_df['prediction_accuracy'].mean() < 0.75:
                recommendations.append({
                    'priority': 'high',
                    'category': 'ml_models',
                    'title': 'Improve Model Accuracy',
                    'description': 'Prediction accuracy is below SLA target',
                    'suggested_actions': [
                        'Retrain models with recent data',
                        'Feature engineering review',
                        'Hyperparameter optimization',
                        'Consider ensemble methods'
                    ],
                    'expected_impact': 'Increase prediction accuracy by 5-10%'
                })

        # Bottleneck-based recommendations
        bottlenecks = data.get('bottlenecks', [])
        if bottlenecks:
            bottleneck_types = [b.get('type') for b in bottlenecks]
            most_common = max(set(bottleneck_types), key=bottleneck_types.count) if bottleneck_types else None

            if most_common:
                recommendations.append({
                    'priority': 'high',
                    'category': 'bottlenecks',
                    'title': f'Address {most_common.replace("_", " ").title()} Bottlenecks',
                    'description': f'Multiple {most_common} bottlenecks detected',
                    'suggested_actions': self._get_bottleneck_actions(most_common),
                    'expected_impact': 'Reduce bottleneck occurrences by 50%'
                })

        return recommendations[:5]  # Limit to top 5 recommendations

    async def _generate_strategic_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations for weekly reports"""
        recommendations = await self._generate_recommendations(data)

        # Add strategic-level recommendations
        strategic_recs = []

        # Capacity planning recommendations
        capacity = await self._analyze_capacity(data)
        if capacity.get('warnings'):
            strategic_recs.append({
                'priority': 'high',
                'category': 'capacity_planning',
                'title': 'Scale Infrastructure',
                'description': 'System approaching capacity limits',
                'suggested_actions': [
                    'Plan infrastructure scaling',
                    'Implement auto-scaling',
                    'Optimize resource allocation',
                    'Consider cloud migration'
                ],
                'expected_impact': 'Prevent performance degradation',
                'timeline': '2-4 weeks'
            })

        # Cost optimization recommendations
        cost_analysis = await self._analyze_costs(data)
        if cost_analysis.get('cost_optimization_opportunities'):
            strategic_recs.append({
                'priority': 'medium',
                'category': 'cost_optimization',
                'title': 'Optimize Infrastructure Costs',
                'description': 'Opportunities identified for cost reduction',
                'suggested_actions': cost_analysis['cost_optimization_opportunities'],
                'expected_impact': f"Reduce costs by 15-25%",
                'timeline': '1-2 weeks'
            })

        return recommendations + strategic_recs

    async def _generate_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate performance charts for the report"""
        charts = {}
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return charts

        metrics_df['timestamp'] = pd.to_datetime(metrics_df['timestamp'])

        # API Response Time Chart
        fig = px.line(metrics_df, x='timestamp', y='api_response_time',
                     title='API Response Time Over Time')
        fig.add_hline(y=self.sla_targets.get('api_response_time', 200),
                     line_dash="dash", annotation_text="SLA Target")
        charts['api_response_time'] = fig.to_json()

        # Prediction Accuracy Chart
        fig = px.line(metrics_df, x='timestamp', y='prediction_accuracy',
                     title='Prediction Accuracy Over Time')
        fig.add_hline(y=self.sla_targets.get('prediction_accuracy', 0.75),
                     line_dash="dash", annotation_text="SLA Target")
        charts['prediction_accuracy'] = fig.to_json()

        # System Resources Chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=metrics_df['timestamp'], y=metrics_df['system_cpu'],
                      mode='lines', name='CPU %'),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=metrics_df['timestamp'], y=metrics_df['system_memory'],
                      mode='lines', name='Memory %'),
            secondary_y=False
        )
        fig.update_layout(title='System Resource Usage')
        fig.update_yaxes(title_text="Usage %", secondary_y=False)
        charts['system_resources'] = fig.to_json()

        # Cache Performance Chart
        fig = px.line(metrics_df, x='timestamp', y='cache_hit_rate',
                     title='Cache Hit Rate Over Time')
        fig.add_hline(y=self.sla_targets.get('cache_hit_rate', 0.8),
                     line_dash="dash", annotation_text="SLA Target")
        charts['cache_performance'] = fig.to_json()

        return charts

    async def _generate_weekly_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts specific to weekly reports"""
        charts = await self._generate_charts(data)

        # Add weekly-specific charts
        metrics_df = pd.DataFrame(data['metrics'])
        if not metrics_df.empty:
            metrics_df['timestamp'] = pd.to_datetime(metrics_df['timestamp'])
            metrics_df['hour'] = metrics_df['timestamp'].dt.hour
            metrics_df['day'] = metrics_df['timestamp'].dt.day_name()

            # Hourly performance heatmap
            hourly_perf = metrics_df.groupby('hour')['api_response_time'].mean().reset_index()
            fig = px.bar(hourly_perf, x='hour', y='api_response_time',
                        title='Average Response Time by Hour')
            charts['hourly_performance'] = fig.to_json()

            # Daily performance comparison
            daily_perf = metrics_df.groupby('day')['api_response_time'].mean().reset_index()
            fig = px.bar(daily_perf, x='day', y='api_response_time',
                        title='Average Response Time by Day of Week')
            charts['daily_performance'] = fig.to_json()

        return charts

    async def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML report from report data"""
        try:
            template = self.jinja_env.get_template('performance_report.html')
            html_content = template.render(**report_data)
            return html_content
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return f"<html><body><h1>Error generating report: {e}</h1></body></html>"

    async def send_report_email(self, report_data: Dict[str, Any], recipients: List[str]):
        """Send report via email"""
        try:
            smtp_config = self.config.get('smtp', {})
            if not smtp_config or not recipients:
                return

            # Generate HTML report
            html_content = await self.generate_html_report(report_data)

            # Create email
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"NFL Predictor {report_data['report_type'].title()} Performance Report"
            msg['From'] = smtp_config['from_email']
            msg['To'] = ', '.join(recipients)

            # Attach HTML content
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            if smtp_config.get('use_tls'):
                server.starttls()
            if smtp_config.get('username'):
                server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Report sent to {len(recipients)} recipients")

        except Exception as e:
            self.logger.error(f"Error sending report email: {e}")

    # Helper methods
    def _calculate_trend(self, values: pd.Series) -> str:
        """Calculate trend direction for a series of values"""
        if len(values) < 2:
            return 'stable'

        slope, _ = np.polyfit(range(len(values)), values, 1)
        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_uptime(self, data: Dict[str, Any]) -> float:
        """Calculate system uptime percentage"""
        # This is a simplified calculation - in reality, you'd track actual downtime
        api_logs = data.get('api_logs', [])
        if not api_logs:
            return 100.0

        error_requests = sum(1 for log in api_logs if log.get('status_code', 200) >= 500)
        total_requests = len(api_logs)

        return ((total_requests - error_requests) / total_requests * 100) if total_requests > 0 else 100.0

    def _calculate_error_rate(self, data: Dict[str, Any]) -> float:
        """Calculate error rate from API logs"""
        api_logs = data.get('api_logs', [])
        if not api_logs:
            return 0.0

        error_requests = sum(1 for log in api_logs if log.get('status_code', 200) >= 400)
        return error_requests / len(api_logs) if api_logs else 0.0

    def _identify_achievements(self, data: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """Identify key achievements for the period"""
        achievements = []

        if summary.get('average_prediction_accuracy', 0) > 0.8:
            achievements.append(f"Achieved {summary['average_prediction_accuracy']:.1%} prediction accuracy")

        if summary.get('average_cache_hit_rate', 0) > 0.85:
            achievements.append(f"Maintained {summary['average_cache_hit_rate']:.1%} cache hit rate")

        if summary.get('uptime_percentage', 0) > 99.9:
            achievements.append(f"Achieved {summary['uptime_percentage']:.2f}% uptime")

        return achievements

    def _identify_major_issues(self, data: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
        """Identify major issues for the period"""
        issues = []

        if summary.get('average_response_time', 0) > 1000:
            issues.append(f"High average response time: {summary['average_response_time']:.0f}ms")

        if summary.get('error_rate', 0) > 0.05:
            issues.append(f"High error rate: {summary['error_rate']:.1%}")

        if summary.get('total_bottlenecks', 0) > 10:
            issues.append(f"Multiple bottlenecks detected: {summary['total_bottlenecks']}")

        return issues

    def _assess_business_impact(self, data: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business impact of performance metrics"""
        return {
            'user_experience_score': min(10, 10 - (summary.get('average_response_time', 0) / 100)),
            'reliability_score': summary.get('uptime_percentage', 0) / 10,
            'accuracy_score': summary.get('average_prediction_accuracy', 0) * 10,
            'overall_impact': 'positive' if summary.get('uptime_percentage', 0) > 99 else 'negative'
        }

    def _assess_resource_utilization(self, data: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Assess resource utilization efficiency"""
        return {
            'cpu_efficiency': 'high' if summary.get('peak_cpu_usage', 0) < 70 else 'moderate' if summary.get('peak_cpu_usage', 0) < 85 else 'low',
            'memory_efficiency': 'high' if summary.get('peak_memory_usage', 0) < 70 else 'moderate' if summary.get('peak_memory_usage', 0) < 85 else 'low',
            'cache_efficiency': 'high' if summary.get('average_cache_hit_rate', 0) > 0.8 else 'moderate' if summary.get('average_cache_hit_rate', 0) > 0.6 else 'low'
        }

    def _calculate_growth_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate growth metrics"""
        # This would compare with previous periods - simplified for example
        return {
            'request_volume_growth': '15%',  # Would be calculated from historical data
            'user_engagement_growth': '8%',
            'prediction_volume_growth': '12%'
        }

    def _assess_weekly_impact(self, metric: str, trend: Dict[str, Any]) -> str:
        """Assess the weekly impact of a trend"""
        if trend['strength'] < 0.3:
            return 'minimal'
        elif trend['direction'] == 'increasing' and metric in ['api_response_time', 'error_rate']:
            return 'negative'
        elif trend['direction'] == 'increasing' and metric in ['prediction_accuracy', 'cache_hit_rate']:
            return 'positive'
        elif trend['direction'] == 'decreasing' and metric in ['api_response_time', 'error_rate']:
            return 'positive'
        else:
            return 'neutral'

    def _generate_forecast(self, metric: str, trend: Dict[str, Any]) -> str:
        """Generate a simple forecast based on trend"""
        if trend['strength'] > 0.7:
            return f"Strong {trend['direction']} trend expected to continue"
        elif trend['strength'] > 0.3:
            return f"Moderate {trend['direction']} trend may continue"
        else:
            return "Stable performance expected"

    def _assess_capacity_health(self, capacity_metrics: Dict[str, Any]) -> str:
        """Assess overall capacity health"""
        cpu_health = capacity_metrics['cpu_utilization']['peak_usage'] < 80
        memory_health = capacity_metrics['memory_utilization']['peak_usage'] < 85

        if cpu_health and memory_health:
            return 'healthy'
        elif cpu_health or memory_health:
            return 'moderate'
        else:
            return 'at_risk'

    def _identify_cost_optimizations(self, data: Dict[str, Any]) -> List[str]:
        """Identify cost optimization opportunities"""
        optimizations = []

        metrics_df = pd.DataFrame(data['metrics'])
        if not metrics_df.empty:
            if metrics_df['system_cpu'].mean() < 30:
                optimizations.append("Consider downsizing compute instances")

            if metrics_df['cache_hit_rate'].mean() > 0.9:
                optimizations.append("Evaluate cache size optimization")

            if len(data.get('api_logs', [])) < 1000:
                optimizations.append("Consider usage-based pricing models")

        return optimizations

    def _get_bottleneck_actions(self, bottleneck_type: str) -> List[str]:
        """Get specific actions for bottleneck type"""
        actions = {
            'cpu_bound': ['Scale CPU resources', 'Optimize algorithms', 'Implement caching'],
            'memory_bound': ['Increase memory', 'Optimize memory usage', 'Implement pagination'],
            'database_bound': ['Optimize queries', 'Add indexes', 'Scale database'],
            'cache_inefficiency': ['Increase cache size', 'Optimize cache strategy'],
            'network_bound': ['Optimize network calls', 'Implement CDN', 'Use connection pooling']
        }
        return actions.get(bottleneck_type, ['Monitor and analyze'])

    async def _get_alerts_for_period(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get alerts for a specific time period"""
        # This would query your alert storage system
        # For now, return empty list as placeholder
        return []

    async def _get_alerts_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get summary of alerts for a period"""
        alerts = await self._get_alerts_for_period(start_time, end_time)

        return {
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a.get('severity') == 'critical']),
            'resolved_alerts': len([a for a in alerts if a.get('resolved', False)]),
            'average_resolution_time': 15  # Would be calculated from actual data
        }

    async def _generate_detailed_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed metrics breakdown"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        detailed = {}

        for column in metrics_df.select_dtypes(include=[np.number]).columns:
            if column == 'timestamp':
                continue

            values = metrics_df[column].dropna()
            if len(values) == 0:
                continue

            detailed[column] = {
                'mean': float(values.mean()),
                'median': float(values.median()),
                'min': float(values.min()),
                'max': float(values.max()),
                'std': float(values.std()),
                'p95': float(values.quantile(0.95)),
                'p99': float(values.quantile(0.99))
            }

        return detailed

    async def _generate_detailed_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed analysis for weekly reports"""
        detailed_metrics = await self._generate_detailed_metrics(data)

        # Add additional analysis
        return {
            'metrics_breakdown': detailed_metrics,
            'performance_patterns': self._analyze_performance_patterns(data),
            'correlation_analysis': self._analyze_metric_correlations(data),
            'anomaly_summary': self._summarize_anomalies(data)
        }

    def _analyze_performance_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance patterns"""
        # Placeholder for performance pattern analysis
        return {
            'peak_hours': [9, 10, 11, 14, 15, 16],
            'low_activity_hours': [2, 3, 4, 5, 6],
            'weekend_vs_weekday': 'weekdays show 40% higher activity'
        }

    def _analyze_metric_correlations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations between metrics"""
        metrics_df = pd.DataFrame(data['metrics'])

        if metrics_df.empty:
            return {}

        numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns
        correlations = {}

        if len(numeric_cols) > 1:
            corr_matrix = metrics_df[numeric_cols].corr()

            # Find strong correlations
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j and abs(corr_matrix.loc[col1, col2]) > 0.7:
                        correlations[f"{col1}_vs_{col2}"] = float(corr_matrix.loc[col1, col2])

        return correlations

    def _summarize_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize anomalies found in the data"""
        # This would integrate with the bottleneck detector
        bottlenecks = data.get('bottlenecks', [])

        return {
            'total_anomalies': len(bottlenecks),
            'anomaly_types': list(set(b.get('type') for b in bottlenecks)),
            'most_common_anomaly': max([b.get('type') for b in bottlenecks], key=[b.get('type') for b in bottlenecks].count) if bottlenecks else None
        }