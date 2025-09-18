#!/usr/bin/env python3
"""
NFL Prediction Storage System
Handles storage of predictions and results to local files and Supabase
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PredictionRecord:
    """Single prediction record"""
    game_id: str
    home_team: str
    away_team: str
    predicted_home_score: float
    predicted_away_score: float
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None
    expert_name: str = "system"
    confidence: float = 0.75
    prediction_time: str = ""
    game_time: Optional[str] = None

class NFLPredictionStorage:
    """Handles all prediction storage operations"""

    def __init__(self, db_path: str = "data/predictions.db"):
        self.db_path = db_path
        self.ensure_directory()
        self.init_database()

    def ensure_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def init_database(self):
        """Initialize SQLite database for predictions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    expert_name TEXT NOT NULL,
                    predicted_home_score REAL NOT NULL,
                    predicted_away_score REAL NOT NULL,
                    actual_home_score INTEGER,
                    actual_away_score INTEGER,
                    confidence REAL DEFAULT 0.75,
                    prediction_time TEXT NOT NULL,
                    game_time TEXT,
                    season INTEGER DEFAULT 2024,
                    week INTEGER DEFAULT 2,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT UNIQUE NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    home_score INTEGER NOT NULL,
                    away_score INTEGER NOT NULL,
                    game_status TEXT DEFAULT 'Final',
                    game_date TEXT,
                    season INTEGER DEFAULT 2024,
                    week INTEGER DEFAULT 2,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def store_predictions(self, predictions: List[Dict], season: int = 2024, week: int = 2):
        """Store predictions to database"""
        with sqlite3.connect(self.db_path) as conn:
            for pred in predictions:
                game_data = pred.get('game_data', {})
                expert_predictions = pred.get('predictions', [])

                for expert_pred in expert_predictions:
                    conn.execute("""
                        INSERT INTO predictions (
                            game_id, home_team, away_team, expert_name,
                            predicted_home_score, predicted_away_score,
                            confidence, prediction_time, season, week
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        expert_pred.get('game_id', ''),
                        game_data.get('HomeTeam', ''),
                        game_data.get('AwayTeam', ''),
                        expert_pred.get('expert_name', 'unknown'),
                        expert_pred.get('predictions', {}).get('exact_score', {}).get('home', 0),
                        expert_pred.get('predictions', {}).get('exact_score', {}).get('away', 0),
                        expert_pred.get('confidence', 0.75),
                        expert_pred.get('timestamp', datetime.now().isoformat()),
                        season,
                        week
                    ))
            conn.commit()
        logger.info(f"Stored {len(predictions)} prediction sets to database")

    def store_game_result(self, game_id: str, home_team: str, away_team: str,
                         home_score: int, away_score: int, game_date: str = None,
                         season: int = 2024, week: int = 2):
        """Store actual game result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO game_results (
                    game_id, home_team, away_team, home_score, away_score,
                    game_date, season, week
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_id, home_team, away_team, home_score, away_score,
                  game_date or datetime.now().isoformat(), season, week))

            # Update predictions with actual results
            conn.execute("""
                UPDATE predictions
                SET actual_home_score = ?, actual_away_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE game_id = ?
            """, (home_score, away_score, game_id))

            conn.commit()
        logger.info(f"Stored result for {game_id}: {home_team} {home_score} - {away_team} {away_score}")

    def get_prediction_accuracy(self, expert_name: str = None) -> Dict:
        """Calculate prediction accuracy"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT
                    expert_name,
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN
                        (predicted_home_score > predicted_away_score AND actual_home_score > actual_away_score) OR
                        (predicted_away_score > predicted_home_score AND actual_away_score > actual_home_score)
                        THEN 1 ELSE 0 END) as correct_winners,
                    AVG(ABS(predicted_home_score - actual_home_score)) as avg_home_error,
                    AVG(ABS(predicted_away_score - actual_away_score)) as avg_away_error,
                    AVG(ABS((predicted_home_score + predicted_away_score) - (actual_home_score + actual_away_score))) as avg_total_error
                FROM predictions
                WHERE actual_home_score IS NOT NULL AND actual_away_score IS NOT NULL
            """

            if expert_name:
                query += " AND expert_name = ?"
                cursor = conn.execute(query, (expert_name,))
            else:
                query += " GROUP BY expert_name"
                cursor = conn.execute(query)

            results = []
            for row in cursor:
                total = row[1]
                accuracy = (row[2] / total * 100) if total > 0 else 0
                results.append({
                    'expert_name': row[0],
                    'total_predictions': total,
                    'correct_winners': row[2],
                    'winner_accuracy': accuracy,
                    'avg_home_error': row[3] or 0,
                    'avg_away_error': row[4] or 0,
                    'avg_total_error': row[5] or 0
                })

            return results

    def export_to_json(self, output_file: str):
        """Export all data to JSON file"""
        with sqlite3.connect(self.db_path) as conn:
            # Get predictions
            predictions = []
            for row in conn.execute("SELECT * FROM predictions"):
                predictions.append({
                    'id': row[0], 'game_id': row[1], 'home_team': row[2], 'away_team': row[3],
                    'expert_name': row[4], 'predicted_home_score': row[5], 'predicted_away_score': row[6],
                    'actual_home_score': row[7], 'actual_away_score': row[8], 'confidence': row[9],
                    'prediction_time': row[10], 'game_time': row[11], 'season': row[12], 'week': row[13]
                })

            # Get results
            results = []
            for row in conn.execute("SELECT * FROM game_results"):
                results.append({
                    'id': row[0], 'game_id': row[1], 'home_team': row[2], 'away_team': row[3],
                    'home_score': row[4], 'away_score': row[5], 'game_status': row[6],
                    'game_date': row[7], 'season': row[8], 'week': row[9]
                })

        export_data = {
            'export_time': datetime.now().isoformat(),
            'predictions': predictions,
            'results': results,
            'accuracy': self.get_prediction_accuracy()
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(predictions)} predictions and {len(results)} results to {output_file}")
        return export_data

# Global storage instance
storage = NFLPredictionStorage()

if __name__ == "__main__":
    # Test the storage system
    print("🗄️ Testing NFL Prediction Storage System")

    # Test prediction storage
    sample_predictions = [{
        'game_data': {'HomeTeam': 'KC', 'AwayTeam': 'BUF'},
        'predictions': [{
            'game_id': 'BUF@KC',
            'expert_name': 'Test Expert',
            'predictions': {'exact_score': {'home': 28, 'away': 24}},
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        }]
    }]

    storage.store_predictions(sample_predictions)
    storage.store_game_result('BUF@KC', 'KC', 'BUF', 31, 17)

    accuracy = storage.get_prediction_accuracy()
    print(f"📊 Accuracy results: {accuracy}")

    export_file = f"data/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    storage.export_to_json(export_file)
    print(f"✅ Storage system test complete - exported to {export_file}")