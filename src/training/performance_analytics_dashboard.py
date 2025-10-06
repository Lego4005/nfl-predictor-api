#!/usr/bin/env python3
"""
Performance Analytics Dashboa
reates expert performance tracking visualization, builds memory usage and quality analytics,
implements learning curve analysis and reporting, and adds system performance monitoring.
"""

import sys
import logging
import json
import time
import psutil
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
sys.path.append('src')

from training.expert_learning_analyzer import ExpertLearningAnalyzer, LearningAnalysis
from training.training_loop_orchestrator import TrainingLoopOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceAnalyticsDashboard:
    """Comprehensive performance analytics and monitoring dashboard"""

    def __init__(self, results_dir: str = "2020_season_results", dashboard_dir: str = "dashboard_output"):
        """Initialize the performance analytics dashboard"""
        self.results_dir = Path(results_dir)
        self.dashboard_dir = Path(dashboard_dir)
        self.dashboard_dir.mkdir(exist_ok=True)

        # Initialize components
        self.learning_analyzer = ExpertLearningAnalyzer(results_dir)

        # Performance monitoring
        self.system_metrics = {
            'start_time': None,
            'memory_usage': [],
            'cpu_usage': [],
            'processing_speed': [],
            'timestamps': []
        }

        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        logger.info("✅ Performance Analytics Dashboard initialized")

    async def generate_complete_dashboard(self, season: int = 2020) -> Dict[str, str]:
        """Generate complete performance analytics dashboard"""
        logger.info(f"📊 Generating complete performance dashboard for season {season}...")

        dashboard_files = {}

        try:
            # Start system monitoring
            self._start_system_monitoring()

            # 1. Generate learning curve analysis
            logger.info("📈 Generating learning curve analysis...")
            learning_analysis = self.learning_analyzer.analyze_learning_curves(season)

            # 2. Create learning curve visualizations
            logger.info("📊 Creating learning curve visualizations...")
            learning_viz_file = await self._create_learning_curve_visualizations(learning_analysis)
            dashboard_files['learning_curves'] = learning_viz_file

            # 3. Create expert performance comparison
            logger.info("🏆 Creating expert performance comparison...")
            performance_viz_file = await self._create_performance_comparison(learning_analysis)
            dashboard_files['performance_comparison'] = performance_viz_file

            # 4. Create context analysis dashboard
            logger.info("🎯 Creating context analysis dashboard...")
            context_viz_file = await self._create_context_analysis(learning_analysis)
            dashboard_files['context_analysis'] = context_viz_file

            # 5. Generate system performance report
            logger.info("⚡ Generating system performance report...")
            system_report_file = await self._create_system_performance_report()
            dashboard_files['system_performance'] = system_report_file

            # 6. Create comprehensive HTML dashboard
            logger.info("🌐 Creating HTML dashboard...")
            html_dashboard_file = await self._create_html_dashboard(learning_analysis, dashboard_files)
            dashboard_files['html_dashboard'] = html_dashboard_file

            # 7. Generate executive summary
            logger.info("📋 Generating executive summary...")
            summary_file = await self._create_executive_summary(learning_analysis)
            dashboard_files['executive_summary'] = summary_file

            logger.info("✅ Complete dashboard generated successfully!")
            return dashboard_files

        except Exception as e:
            logger.error(f"❌ Dashboard generation failed: {e}")
            raise

    def _start_system_monitoring(self):
        """Start system performance monitoring"""
        self.system_metrics['start_time'] = time.time()
        self.system_metrics['memory_usage'] = []
        self.system_metrics['cpu_usage'] = []
        self.system_metrics['processing_speed'] = []
        self.system_metrics['timestamps'] = []

    def _record_system_metrics(self):
        """Record current system metrics"""
        current_time = time.time()

        # Memory usage in MB
        memory_mb = psutil.virtual_memory().used / (1024 * 1024)

        # CPU usage percentage
        cpu_percent = psutil.cpu_percent()

        # Processing speed (games per second - simplified)
        elapsed_time = current_time - self.system_metrics['start_time']
        processing_speed = 1.0 / max(elapsed_time, 0.1)  # Avoid division by zero

        self.system_metrics['memory_usage'].append(memory_mb)
        self.system_metrics['cpu_usage'].append(cpu_percent)
        self.system_metrics['processing_speed'].append(processing_speed)
        self.system_metrics['timestamps'].append(current_time)

    async def _create_learning_curve_visualizations(self, analysis: LearningAnalysis) -> str:
        """Create learning curve visualizations"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Expert Learning Curves - Season {analysis.season}', fontsize=16, fontweight='bold')

        # 1. Individual learning curves
        ax1 = axes[0, 0]
        for expert_id, curve in analysis.expert_curves.items():
            if len(curve.curve_points) > 5:  # Only plot experts with sufficient data
                game_numbers = [p.game_number for p in curve.curve_points]
                accuracies = [p.accuracy for p in curve.curve_points]
                ax1.plot(game_numbers, accuracies, label=expert_id[:15], alpha=0.7)

        ax1.set_title('Individual Expert Learning Curves')
        ax1.set_xlabel('Game Number')
        ax1.set_ylabel('Cumulative Accuracy')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)

        # 2. Accuracy improvement distribution
        ax2 = axes[0, 1]
        improvements = [curve.accuracy_improvement for curve in analysis.expert_curves.values()]
        expert_names = [expert_id[:15] for expert_id in analysis.expert_curves.keys()]

        colors = ['green' if imp > 0 else 'red' for imp in improvements]
        bars = ax2.barh(expert_names, improvements, color=colors, alpha=0.7)
        ax2.set_title('Accuracy Improvement by Expert')
        ax2.set_xlabel('Accuracy Change')
        ax2.axvline(x=0, color='black', linestyle='--', alpha=0.5)

        # Add value labels on bars
        for bar, improvement in zip(bars, improvements):
            width = bar.get_width()
            ax2.text(width + (0.001 if width >= 0 else -0.001), bar.get_y() + bar.get_height()/2,
                    f'{improvement:+.1%}', ha='left' if width >= 0 else 'right', va='center', fontsize=8)

        # 3. Confidence stability analysis
        ax3 = axes[1, 0]
        stability_scores = [curve.confidence_stability for curve in analysis.expert_curves.values()]
        expert_names = [expert_id[:15] for expert_id in analysis.expert_curves.keys()]

        bars = ax3.barh(expert_names, stability_scores, color='blue', alpha=0.7)
        ax3.set_title('Expert Confidence Stability')
        ax3.set_xlabel('Stability Score (0-1)')

        # Add value labels
        for bar, score in zip(bars, stability_scores):
            width = bar.get_width()
            ax3.text(width + 0.01, bar.get_y() + bar.get_height()/2,
                    f'{score:.3f}', ha='left', va='center', fontsize=8)

        # 4. Learning trend summary
        ax4 = axes[1, 1]
        trend_counts = {}
        for curve in analysis.expert_curves.values():
            trend = curve.learning_trend
            trend_counts[trend] = trend_counts.get(trend, 0) + 1

        colors = {'improving': 'green', 'declining': 'red', 'stable': 'orange', 'insufficient_data': 'gray'}
        trend_colors = [colors.get(trend, 'blue') for trend in trend_counts.keys()]

        wedges, texts, autotexts = ax4.pie(trend_counts.values(), labels=trend_counts.keys(),
                                          autopct='%1.1f%%', colors=trend_colors)
        ax4.set_title('Learning Trend Distribution')

        plt.tight_layout()

        # Save the plot
        output_file = self.dashboard_dir / "learning_curves_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Learning curve visualizations saved to {output_file}")
        return str(output_file)

    async def _create_performance_comparison(self, analysis: LearningAnalysis) -> str:
        """Create expert performance comparison dashboard"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Expert Performance Comparison - Season {analysis.season}', fontsize=16, fontweight='bold')

        # Prepare data
        expert_data = []
        for expert_id, curve in analysis.expert_curves.items():
            expert_data.append({
                'expert': expert_id[:15],
                'initial_accuracy': curve.initial_accuracy,
                'final_accuracy': curve.final_accuracy,
                'improvement': curve.accuracy_improvement,
                'stability': curve.confidence_stability,
                'drift': curve.personality_drift_score
            })

        df = pd.DataFrame(expert_data)

        # 1. Initial vs Final Accuracy Scatter
        ax1 = axes[0, 0]
        scatter = ax1.scatter(df['initial_accuracy'], df['final_accuracy'],
                             c=df['improvement'], cmap='RdYlGn', s=100, alpha=0.7)
        ax1.plot([0, 1], [0, 1], 'k--', alpha=0.5)  # Diagonal line
        ax1.set_xlabel('Initial Accuracy')
        ax1.set_ylabel('Final Accuracy')
        ax1.set_title('Initial vs Final Accuracy')
        plt.colorbar(scatter, ax=ax1, label='Improvement')

        # Add expert labels
        for _, row in df.iterrows():
            ax1.annotate(row['expert'], (row['initial_accuracy'], row['final_accuracy']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8, alpha=0.7)

        # 2. Performance vs Stability
        ax2 = axes[0, 1]
        scatter = ax2.scatter(df['stability'], df['final_accuracy'],
                             c=df['improvement'], cmap='RdYlGn', s=100, alpha=0.7)
        ax2.set_xlabel('Confidence Stability')
        ax2.set_ylabel('Final Accuracy')
        ax2.set_title('Performance vs Stability')
        plt.colorbar(scatter, ax=ax2, label='Improvement')

        # 3. Top and Bottom Performers
        ax3 = axes[1, 0]
        top_performers = df.nlargest(5, 'final_accuracy')
        bottom_performers = df.nsmallest(5, 'final_accuracy')

        y_pos = range(len(top_performers))
        ax3.barh(y_pos, top_performers['final_accuracy'], color='green', alpha=0.7, label='Top 5')
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(top_performers['expert'])
        ax3.set_xlabel('Final Accuracy')
        ax3.set_title('Top 5 Performers')

        # Add accuracy labels
        for i, accuracy in enumerate(top_performers['final_accuracy']):
            ax3.text(accuracy + 0.01, i, f'{accuracy:.1%}', va='center', fontsize=9)

        # 4. Improvement Leaders
        ax4 = axes[1, 1]
        improvement_leaders = df.nlargest(5, 'improvement')

        colors = ['green' if imp > 0 else 'red' for imp in improvement_leaders['improvement']]
        y_pos = range(len(improvement_leaders))
        bars = ax4.barh(y_pos, improvement_leaders['improvement'], color=colors, alpha=0.7)
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(improvement_leaders['expert'])
        ax4.set_xlabel('Accuracy Improvement')
        ax4.set_title('Top 5 Most Improved')
        ax4.axvline(x=0, color='black', linestyle='--', alpha=0.5)

        # Add improvement labels
        for i, improvement in enumerate(improvement_leaders['improvement']):
            ax4.text(improvement + (0.005 if improvement >= 0 else -0.005), i,
                    f'{improvement:+.1%}', va='center', ha='left' if improvement >= 0 else 'right', fontsize=9)

        plt.tight_layout()

        # Save the plot
        output_file = self.dashboard_dir / "performance_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"🏆 Performance comparison saved to {output_file}")
        return str(output_file)

    async def _create_context_analysis(self, analysis: LearningAnalysis) -> str:
        """Create context analysis dashboard"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Context Performance Analysis - Season {analysis.season}', fontsize=16, fontweight='bold')

        # Prepare context data
        context_data = []
        for expert_id, curve in analysis.expert_curves.items():
            for context, performance in curve.context_performance.items():
                context_data.append({
                    'expert': expert_id[:15],
                    'context': context,
                    'performance': performance
                })

        if context_data:
            df_context = pd.DataFrame(context_data)

            # 1. Context Performance Heatmap
            ax1 = axes[0, 0]
            pivot_data = df_context.pivot(index='expert', columns='context', values='performance')
            sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlGn', ax=ax1, cbar_kws={'label': 'Accuracy'})
            ax1.set_title('Expert Performance by Context')
            ax1.set_xlabel('Context')
            ax1.set_ylabel('Expert')

            # 2. Context Specialists
            ax2 = axes[0, 1]
            specialist_data = []
            for context, specialists in analysis.context_specialists.items():
                for specialist in specialists:
                    specialist_data.append({'context': context, 'specialist': specialist[:15]})

            if specialist_data:
                df_specialists = pd.DataFrame(specialist_data)
                specialist_counts = df_specialists['context'].value_counts()
                ax2.bar(specialist_counts.index, specialist_counts.values, color='skyblue', alpha=0.7)
                ax2.set_title('Number of Specialists by Context')
                ax2.set_xlabel('Context')
                ax2.set_ylabel('Number of Specialists')

                # Add count labels
                for i, count in enumerate(specialist_counts.values):
                    ax2.text(i, count + 0.1, str(count), ha='center', va='bottom')
            else:
                ax2.text(0.5, 0.5, 'No context specialists identified', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Context Specialists')

        # 3. Early vs Late Season Performance
        ax3 = axes[1, 0]
        early_late_data = []
        for expert_id, curve in analysis.expert_curves.items():
            early_perf = curve.context_performance.get('early_season', 0)
            late_perf = curve.context_performance.get('late_season', 0)
            if early_perf > 0 and late_perf > 0:
                early_late_data.append({
                    'expert': expert_id[:15],
                    'early_season': early_perf,
                    'late_season': late_perf,
                    'difference': late_perf - early_perf
                })

        if early_late_data:
            df_early_late = pd.DataFrame(early_late_data)

            scatter = ax3.scatter(df_early_late['early_season'], df_early_late['late_season'],
                                 c=df_early_late['difference'], cmap='RdYlGn', s=100, alpha=0.7)
            ax3.plot([0, 1], [0, 1], 'k--', alpha=0.5)  # Diagonal line
            ax3.set_xlabel('Early Season Accuracy')
            ax3.set_ylabel('Late Season Accuracy')
            ax3.set_title('Early vs Late Season Performance')
            plt.colorbar(scatter, ax=ax3, label='Late - Early Difference')

            # Add expert labels
            for _, row in df_early_late.iterrows():
                ax3.annotate(row['expert'], (row['early_season'], row['late_season']),
                            xytext=(5, 5), textcoords='offset points', fontsize=8, alpha=0.7)

        # 4. System Learning Effectiveness
        ax4 = axes[1, 1]
        effectiveness_metrics = {
            'Learning Effectiveness': analysis.learning_effectiveness_score,
            'Avg Improvement': np.mean([curve.accuracy_improvement for curve in analysis.expert_curves.values()]),
            'Avg Stability': np.mean([curve.confidence_stability for curve in analysis.expert_curves.values()]),
            'Improving %': len([c for c in analysis.expert_curves.values() if c.learning_trend == 'improving']) / len(analysis.expert_curves)
        }

        metrics_names = list(effectiveness_metrics.keys())
        metrics_values = list(effectiveness_metrics.values())

        bars = ax4.bar(metrics_names, metrics_values, color=['blue', 'green', 'orange', 'purple'], alpha=0.7)
        ax4.set_title('System Learning Effectiveness Metrics')
        ax4.set_ylabel('Score')
        ax4.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar, value in zip(bars, metrics_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()

        # Save the plot
        output_file = self.dashboard_dir / "context_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"🎯 Context analysis saved to {output_file}")
        return str(output_file)

    async def _create_system_performance_report(self) -> str:
        """Create system performance monitoring report"""
        # Record final metrics
        self._record_system_metrics()

        # Create performance report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'total_runtime_seconds': time.time() - self.system_metrics['start_time'],
                'peak_memory_mb': max(self.system_metrics['memory_usage']) if self.system_metrics['memory_usage'] else 0,
                'avg_memory_mb': np.mean(self.system_metrics['memory_usage']) if self.system_metrics['memory_usage'] else 0,
                'peak_cpu_percent': max(self.system_metrics['cpu_usage']) if self.system_metrics['cpu_usage'] else 0,
                'avg_cpu_percent': np.mean(self.system_metrics['cpu_usage']) if self.system_metrics['cpu_usage'] else 0,
                'avg_processing_speed': np.mean(self.system_metrics['processing_speed']) if self.system_metrics['processing_speed'] else 0
            },
            'performance_insights': self._generate_performance_insights()
        }

        # Save report
        output_file = self.dashboard_dir / "system_performance_report.json"
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"⚡ System performance report saved to {output_file}")
        return str(output_file)

    def _generate_performance_insights(self) -> List[str]:
        """Generate performance insights"""
        insights = []

        if self.system_metrics['memory_usage']:
            peak_memory = max(self.system_metrics['memory_usage'])
            if peak_memory > 2000:  # > 2GB
                insights.append(f"High memory usage detected: {peak_memory:.0f}MB peak")
            else:
                insights.append(f"Memory usage within normal range: {peak_memory:.0f}MB peak")

        if self.system_metrics['cpu_usage']:
            avg_cpu = np.mean(self.system_metrics['cpu_usage'])
            if avg_cpu > 80:
                insights.append(f"High CPU utilization: {avg_cpu:.1f}% average")
            else:
                insights.append(f"CPU utilization normal: {avg_cpu:.1f}% average")

        runtime = time.time() - self.system_metrics['start_time']
        if runtime > 3600:  # > 1 hour
            insights.append(f"Long processing time: {runtime/3600:.1f} hours")
        else:
            insights.append(f"Processing completed in {runtime/60:.1f} minutes")

        return insights

    async def _create_html_dashboard(self, analysis: LearningAnalysis, dashboard_files: Dict[str, str]) -> str:
        """Create comprehensive HTML dashboard"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFL Expert Performance Analytics Dashboard - Season {analysis.season}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .dashboard-section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .section-header {{
            background: #667eea;
            color: white;
            padding: 20px;
            font-size: 1.2em;
            font-weight: bold;
        }}
        .section-content {{
            padding: 20px;
        }}
        .visualization {{
            text-align: center;
            margin: 20px 0;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .expert-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }}
        .expert-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .trend-improving {{ border-left-color: #28a745; }}
        .trend-declining {{ border-left-color: #dc3545; }}
        .trend-stable {{ border-left-color: #ffc107; }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 50px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 NFL Expert Performance Analytics Dashboard</h1>
        <h2>Season {analysis.season} - Complete Analysis</h2>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{len(analysis.expert_curves)}</div>
            <div class="metric-label">Total Experts</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{analysis.total_games}</div>
            <div class="metric-label">Games Analyzed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{analysis.learning_effectiveness_score:.3f}</div>
            <div class="metric-label">Learning Effectiveness</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{analysis.overall_learning_trend.replace('_', ' ').title()}</div>
            <div class="metric-label">Overall Trend</div>
        </div>
    </div>

    <div class="dashboard-section">
        <div class="section-header">📈 Learning Curve Analysis</div>
        <div class="section-content">
            <p>Comprehensive analysis of how each expert's prediction accuracy evolved throughout the season.</p>
            <div class="visualization">
                <img src="{Path(dashboard_files.get('learning_curves', '')).name}" alt="Learning Curves Analysis">
            </div>
        </div>
    </div>

    <div class="dashboard-section">
        <div class="section-header">🏆 Performance Comparison</div>
        <div class="section-content">
            <p>Detailed comparison of expert performance metrics including accuracy, improvement, and stability.</p>
            <div class="visualization">
                <img src="{Path(dashboard_files.get('performance_comparison', '')).name}" alt="Performance Comparison">
            </div>
        </div>
    </div>

    <div class="dashboard-section">
        <div class="section-header">🎯 Context Analysis</div>
        <div class="section-content">
            <p>Analysis of expert performance in different contexts and identification of specialists.</p>
            <div class="visualization">
                <img src="{Path(dashboard_files.get('context_analysis', '')).name}" alt="Context Analysis">
            </div>
        </div>
    </div>

    <div class="dashboard-section">
        <div class="section-header">📊 Expert Performance Summary</div>
        <div class="section-content">
            <h3>🏆 Best Learners (Most Improved)</h3>
            <div class="expert-list">
"""

        # Add best learners
        for expert_id in analysis.best_learners:
            curve = analysis.expert_curves[expert_id]
            html_content += f"""
                <div class="expert-item trend-improving">
                    <strong>{expert_id}</strong><br>
                    Improvement: {curve.accuracy_improvement:+.1%}<br>
                    Final Accuracy: {curve.final_accuracy:.1%}
                </div>
"""

        html_content += """
            </div>

            <h3>📉 Needs Attention</h3>
            <div class="expert-list">
"""

        # Add worst learners
        for expert_id in analysis.worst_learners:
            curve = analysis.expert_curves[expert_id]
            html_content += f"""
                <div class="expert-item trend-declining">
                    <strong>{expert_id}</strong><br>
                    Change: {curve.accuracy_improvement:+.1%}<br>
                    Final Accuracy: {curve.final_accuracy:.1%}
                </div>
"""

        html_content += """
            </div>

            <h3>🎯 Most Stable Experts</h3>
            <div class="expert-list">
"""

        # Add most stable
        for expert_id in analysis.most_stable:
            curve = analysis.expert_curves[expert_id]
            html_content += f"""
                <div class="expert-item trend-stable">
                    <strong>{expert_id}</strong><br>
                    Stability: {curve.confidence_stability:.3f}<br>
                    Accuracy: {curve.final_accuracy:.1%}
                </div>
"""

        html_content += f"""
            </div>
        </div>
    </div>

    <div class="dashboard-section">
        <div class="section-header">🔍 Context Specialists</div>
        <div class="section-content">
"""

        # Add context specialists
        for context, specialists in analysis.context_specialists.items():
            if specialists:
                html_content += f"""
            <h3>{context.replace('_', ' ').title()} Specialists</h3>
            <div class="expert-list">
"""
                for specialist in specialists:
                    curve = analysis.expert_curves[specialist]
                    context_perf = curve.context_performance.get(context, 0)
                    html_content += f"""
                <div class="expert-item">
                    <strong>{specialist}</strong><br>
                    {context.replace('_', ' ').title()} Accuracy: {context_perf:.1%}
                </div>
"""
                html_content += "</div>"

        html_content += f"""
        </div>
    </div>

    <div class="footer">
        <p>Dashboard generated by NFL Expert Performance Analytics System</p>
        <p>For detailed data and analysis, check the accompanying JSON reports</p>
    </div>
</body>
</html>
"""

        # Save HTML dashboard
        output_file = self.dashboard_dir / "performance_dashboard.html"
        with open(output_file, 'w') as f:
            f.write(html_content)

        logger.info(f"🌐 HTML dashboard saved to {output_file}")
        return str(output_file)

    async def _create_executive_summary(self, analysis: LearningAnalysis) -> str:
        """Create executive summary report"""
        summary = {
            'executive_summary': {
                'season': analysis.season,
                'generated_at': datetime.now().isoformat(),
                'total_experts': len(analysis.expert_curves),
                'total_games': analysis.total_games,
                'overall_learning_trend': analysis.overall_learning_trend,
                'learning_effectiveness_score': analysis.learning_effectiveness_score
            },
            'key_findings': {
                'best_performing_experts': [
                    {
                        'expert_id': expert_id,
                        'final_accuracy': analysis.expert_curves[expert_id].final_accuracy,
                        'improvement': analysis.expert_curves[expert_id].accuracy_improvement
                    }
                    for expert_id in analysis.best_learners
                ],
                'most_improved_experts': [
                    {
                        'expert_id': expert_id,
                        'improvement': analysis.expert_curves[expert_id].accuracy_improvement,
                        'learning_trend': analysis.expert_curves[expert_id].learning_trend
                    }
                    for expert_id in analysis.best_learners
                ],
                'stability_leaders': [
                    {
                        'expert_id': expert_id,
                        'stability_score': analysis.expert_curves[expert_id].confidence_stability,
                        'personality_drift': analysis.expert_curves[expert_id].personality_drift_score
                    }
                    for expert_id in analysis.most_stable
                ]
            },
            'system_insights': {
                'learning_effectiveness': analysis.learning_effectiveness_score,
                'experts_improving': len([c for c in analysis.expert_curves.values() if c.learning_trend == 'improving']),
                'experts_declining': len([c for c in analysis.expert_curves.values() if c.learning_trend == 'declining']),
                'experts_stable': len([c for c in analysis.expert_curves.values() if c.learning_trend == 'stable']),
                'context_specialists_identified': sum(len(specialists) for specialists in analysis.context_specialists.values())
            },
            'recommendations': self._generate_recommendations(analysis)
        }

        # Save summary
        output_file = self.dashboard_dir / "executive_summary.json"
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📋 Executive summary saved to {output_file}")
        return str(output_file)

    def _generate_recommendations(self, analysis: LearningAnalysis) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # Learning effectiveness recommendations
        if analysis.learning_effectiveness_score < 0.3:
            recommendations.append("Low learning effectiveness detected - consider revising expert learning algorithms")
        elif analysis.learning_effectiveness_score > 0.7:
            recommendations.append("High learning effectiveness - system is performing well")

        # Expert-specific recommendations
        declining_experts = [expert_id for expert_id, curve in analysis.expert_curves.items()
                           if curve.learning_trend == 'declining']
        if len(declining_experts) > len(analysis.expert_curves) * 0.3:
            recommendations.append(f"High number of declining experts ({len(declining_experts)}) - investigate system-wide issues")

        # Stability recommendations
        unstable_experts = [expert_id for expert_id, curve in analysis.expert_curves.items()
                          if curve.confidence_stability < 0.3]
        if unstable_experts:
            recommendations.append(f"Unstable experts detected: {', '.join(unstable_experts[:3])} - consider confidence calibration")

        # Context specialist recommendations
        total_specialists = sum(len(specialists) for specialists in analysis.context_specialists.values())
        if total_specialists < len(analysis.expert_curves) * 0.2:
            recommendations.append("Few context specialists identified - consider enhancing context-aware learning")

        return recommendations


async def main():
    """Test the Performance Analytics Dashboard"""
    print("📊 Performance Analytics Dashboard Test")
    print("=" * 60)

    dashboard = PerformanceAnalyticsDashboard()

    try:
        # Generate complete dashboard
        dashboard_files = await dashboard.generate_complete_dashboard(2020)

        print(f"\n✅ Performance analytics dashboard generated successfully!")
        print(f"📁 Dashboard files created:")
        for component, file_path in dashboard_files.items():
            print(f"   • {component}: {file_path}")

        print(f"\n🌐 Open the HTML dashboard to view comprehensive results:")
        print(f"   {dashboard_files.get('html_dashboard', 'performance_dashboard.html')}")

    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}")
        logger.error(f"Dashboard generation failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
