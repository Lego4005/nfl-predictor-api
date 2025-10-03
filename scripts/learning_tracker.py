#!/usr/bin/env python3
"""
Learning Tracker - Comprehensive tracking and visualization of AI learning

Outputs:
1. CSV file for spreadsheet analysis
ML dashboard with charts
3. SQLite database for queries
4. Real-time console updates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import asyncio
from datetime import datetime
import json
import csv
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.prompts.natural_language_prompt import build_natural_language_prompt, parse_natural_language_response
from dotenv import load_dotenv

load_dotenv()


class LearningTracker:
    """Track and visualize AI learning progress"""

    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(f'logs/experiments/{self.experiment_name}_{self.timestamp}')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize tracking files
        self.csv_file = self.output_dir / 'predictions.csv'
        self.db_file = self.output_dir / 'tracking.db'
        self.html_file = self.output_dir / 'dashboard.html'

        self._init_csv()
        self._init_db()

        logger.info(f"📁 Tracking directory: {self.output_dir}")

    def _init_csv(self):
        """Initialize CSV file with headers"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Game_Num', 'Date', 'Away_Team', 'Home_Team', 'Week',
                'Memories_Available', 'Predicted_Winner', 'Actual_Winner',
                'Correct', 'Confidence', 'Away_Score', 'Home_Score',
                'Reasoning_Preview', 'Response_Time', 'Running_Accuracy'
            ])

    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # Predictions table
        c.execute('''CREATE TABLE predictions (
            id INTEGER PRIMARY KEY,
            game_num INTEGER,
            game_date TEXT,
            away_team TEXT,
            home_team TEXT,
            week INTEGER,
            memories_available INTEGER,
            predicted_winner TEXT,
            actual_winner TEXT,
            correct INTEGER,
            confidence REAL,
            away_score INTEGER,
            home_score INTEGER,
            reasoning TEXT,
            response_time REAL,
            timestamp TEXT
        )''')

        # Memories table
        c.execute('''CREATE TABLE memories_used (
            id INTEGER PRIMARY KEY,
            game_num INTEGER,
            memory_index INTEGER,
            memory_game TEXT,
            memory_prediction TEXT,
            memory_actual TEXT,
            memory_correct INTEGER,
            memory_lesson TEXT
        )''')

        # Accuracy tracking table
        c.execute('''CREATE TABLE accuracy_progression (
            id INTEGER PRIMARY KEY,
            game_num INTEGER,
            correct_count INTEGER,
            total_count INTEGER,
            accuracy REAL,
            avg_confidence REAL,
            avg_memories INTEGER
        )''')

        conn.commit()
        conn.close()

    def log_prediction(self, game_num, game_data, memories, prediction, actual, response_time, running_accuracy):
        """Log a single prediction to all tracking systems"""

        # CSV
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                game_num,
                game_data.get('game_date', 'N/A'),
                game_data.get('away_team', 'N/A'),
                game_data.get('home_team', 'N/A'),
                game_data.get('week', 'N/A'),
                len(memories),
                prediction['winner'],
                actual,
                1 if prediction['winner'] == actual else 0,
                f"{prediction['confidence']:.2f}",
                game_data.get('away_score', 0),
                game_data.get('home_score', 0),
                prediction['reasoning'][:100],
                f"{response_time:.2f}",
                f"{running_accuracy:.3f}"
            ])

        # Database
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        c.execute('''INSERT INTO predictions VALUES (
            NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )''', (
            game_num,
            game_data.get('game_date'),
            game_data.get('away_team'),
            game_data.get('home_team'),
            game_data.get('week'),
            len(memories),
            prediction['winner'],
            actual,
            1 if prediction['winner'] == actual else 0,
            prediction['confidence'],
            game_data.get('away_score'),
            game_data.get('home_score'),
            prediction['reasoning'],
            response_time,
            datetime.now().isoformat()
        ))

        # Log memories used
        for i, mem in enumerate(memories):
            pred_data = mem.get('prediction_data', {})
            actual_data = mem.get('actual_outcome', {})
            lessons = mem.get('lessons_learned', [])

            context = mem.get('contextual_factors', [])
            teams = {}
            for factor in context:
                if factor.get('factor') in ['home_team', 'away_team']:
                    teams[factor['factor']] = factor['value']

            c.execute('''INSERT INTO memories_used VALUES (
                NULL, ?, ?, ?, ?, ?, ?, ?
            )''', (
                game_num,
                i,
                f"{teams.get('away_team', '?')} @ {teams.get('home_team', '?')}",
                pred_data.get('winner'),
                actual_data.get('winner'),
                1 if pred_data.get('winner') == actual_data.get('winner') else 0,
                lessons[0].get('lesson', 'N/A') if lessons else 'N/A'
            ))

        conn.commit()
        conn.close()

    def log_accuracy_point(self, game_num, correct_count, total_count, avg_confidence, avg_memories):
        """Log accuracy progression point"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        c.execute('''INSERT INTO accuracy_progression VALUES (
            NULL, ?, ?, ?, ?, ?, ?
        )''', (
            game_num,
            correct_count,
            total_count,
            correct_count / total_count if total_count > 0 else 0,
            avg_confidence,
            avg_memories
        ))

        conn.commit()
        conn.close()

    def generate_html_dashboard(self):
        """Generate HTML dashboard with charts"""

        # Read data from database
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # Get predictions
        c.execute('SELECT * FROM predictions ORDER BY game_num')
        predictions = c.fetchall()

        # Get accuracy progression
        c.execute('SELECT * FROM accuracy_progression ORDER BY game_num')
        accuracy_data = c.fetchall()

        conn.close()

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Learning Analysis - {self.experiment_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #3498db; }}
        .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
        .correct {{ color: #27ae60; font-weight: bold; }}
        .wrong {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 AI Learning Analysis Dashboard</h1>
            <p>Experiment: {self.experiment_name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(predictions)}</div>
                <div class="stat-label">Total Games</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for p in predictions if p[9])}</div>
                <div class="stat-label">Correct Predictions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{(sum(1 for p in predictions if p[9]) / len(predictions) * 100):.1f}%</div>
                <div class="stat-label">Final Accuracy</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(p[6] for p in predictions) / len(predictions):.1f}</div>
                <div class="stat-label">Avg Memories Used</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>📈 Accuracy Over Time</h2>
            <canvas id="accuracyChart"></canvas>
        </div>

        <div class="chart-container">
            <h2>🧠 Memory Accumulation</h2>
            <canvas id="memoryChart"></canvas>
        </div>

        <div class="chart-container">
            <h2>📊 Prediction Details</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Game</th>
                    <th>Week</th>
                    <th>Memories</th>
                    <th>Predicted</th>
                    <th>Actual</th>
                    <th>Result</th>
                    <th>Confidence</th>
                </tr>
"""

        for p in predictions:
            result_class = 'correct' if p[9] else 'wrong'
            result_text = '✅ CORRECT' if p[9] else '❌ WRONG'
            html += f"""
                <tr>
                    <td>{p[1]}</td>
                    <td>{p[3]} @ {p[4]}</td>
                    <td>{p[5]}</td>
                    <td>{p[6]}</td>
                    <td>{p[7]}</td>
                    <td>{p[8]}</td>
                    <td class="{result_class}">{result_text}</td>
                    <td>{p[10]:.0%}</td>
                </tr>
"""

        html += """
            </table>
        </div>
    </div>

    <script>
        // Accuracy chart
        const accuracyCtx = document.getElementById('accuracyChart').getContext('2d');
        new Chart(accuracyCtx, {
            type: 'line',
            data: {
                labels: """ + str([p[1] for p in predictions]) + """,
                datasets: [{
                    label: 'Running Accuracy',
                    data: """ + str([sum(1 for x in predictions[:i+1] if x[9]) / (i+1) * 100 for i in range(len(predictions))]) + """,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: 'Accuracy (%)' }
                    },
                    x: {
                        title: { display: true, text: 'Game Number' }
                    }
                }
            }
        });

        // Memory chart
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        new Chart(memoryCtx, {
            type: 'bar',
            data: {
                labels: """ + str([p[1] for p in predictions]) + """,
                datasets: [{
                    label: 'Memories Available',
                    data: """ + str([p[6] for p in predictions]) + """,
                    backgroundColor: '#9b59b6'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Number of Memories' }
                    },
                    x: {
                        title: { display: true, text: 'Game Number' }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

        with open(self.html_file, 'w') as f:
            f.write(html)

        logger.info(f"\n📊 HTML Dashboard: {self.html_file}")
        logger.info(f"   Open in browser: file://{self.html_file.absolute()}")

    def generate_summary(self):
        """Generate text summary"""
        summary_file = self.output_dir / 'SUMMARY.txt'

        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        c.execute('SELECT COUNT(*), SUM(correct), AVG(confidence), AVG(memories_available) FROM predictions')
        total, correct, avg_conf, avg_mem = c.fetchone()

        c.execute('SELECT * FROM predictions ORDER BY game_num')
        predictions = c.fetchall()

        # Calculate first half vs second half
        mid = len(predictions) // 2
        first_half_acc = sum(1 for p in predictions[:mid] if p[9]) / mid if mid > 0 else 0
        second_half_acc = sum(1 for p in predictions[mid:] if p[9]) / (len(predictions) - mid) if len(predictions) > mid else 0

        conn.close()

        summary = f"""
{'='*80}
AI LEARNING EXPERIMENT SUMMARY
{'='*80}

Experiment: {self.experiment_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL RESULTS:
  Total Games: {total}
  Correct Predictions: {correct}
  Final Accuracy: {correct/total*100:.1f}%
  Average Confidence: {avg_conf:.1%}
  Average Memories Used: {avg_mem:.1f}

LEARNING PROGRESSION:
  First Half Accuracy (Games 1-{mid}): {first_half_acc*100:.1f}%
  Second Half Accuracy (Games {mid+1}-{total}): {second_half_acc*100:.1f}%
  Improvement: {(second_half_acc - first_half_acc)*100:+.1f}%

  {'✅ LEARNING CONFIRMED' if second_half_acc > first_half_acc else '⚠️  NO CLEAR LEARNING TREND'}

FILES GENERATED:
  📊 Dashboard: {self.html_file.name}
  📁 CSV Data: {self.csv_file.name}
  🗄️  Database: {self.db_file.name}
  📄 Summary: {summary_file.name}

NEXT STEPS:
  1. Open dashboard.html in your browser for visualizations
  2. Open predictions.csv in Excel/Sheets for analysis
  3. Query tracking.db with SQL for custom analysis

{'='*80}
"""

        with open(summary_file, 'w') as f:
            f.write(summary)

        logger.info(summary)
        logger.info(f"\n📄 Summary saved: {summary_file}")


# Export for use in other scripts
__all__ = ['LearningTracker']
