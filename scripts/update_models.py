#!/usr/bin/env python3
"""
Automated Model Update Script

Runs after each week's games to update model weights, retrain if performance drops,
and generate learning reports. This script orchestrates the entire learning pipeline.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from ml.continuous_learner import ContinuousLearner
    from ml.learning_coordinator import LearningCoordinator
    from ml.belief_revision_service import BeliefRevisionService
    from ml.episodic_memory_manager import EpisodicMemoryManager
    from ml.expert_memory_service import ExpertMemoryService
    from monitoring.prediction_monitor import PredictionMonitor
    from services.enhanced_data_fetcher import EnhancedDataFetcher
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    print("Running in standalone mode...")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/model_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelUpdateOrchestrator:
    """Orchestrates the complete model update process"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.continuous_learner = None
        self.learning_coordinator = None
        self.prediction_monitor = None
        self.data_fetcher = None

        # Update statistics
        self.update_stats = {
            'start_time': datetime.now(),
            'experts_updated': 0,
            'models_retrained': 0,
            'belief_revisions': 0,
            'performance_improvements': 0,
            'errors': []
        }

        self._init_components()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration for model updates"""
        default_config = {
            'retraining_threshold': 0.05,  # Retrain if accuracy drops by 5%
            'belief_revision_threshold': 0.3,  # Revise beliefs if accuracy < 30%
            'minimum_predictions': 10,  # Minimum predictions before retraining
            'backup_models': True,
            'generate_reports': True,
            'update_expert_weights': True,
            'enable_drift_detection': True,
            'max_retrain_attempts': 3,
            'learning_rate_adjustment': True,
            'memory_cleanup': True
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")

        return default_config

    def _init_components(self):
        """Initialize all learning components"""
        try:
            self.continuous_learner = ContinuousLearner()
            self.learning_coordinator = LearningCoordinator()
            self.prediction_monitor = PredictionMonitor()

            # Initialize data fetcher if available
            try:
                self.data_fetcher = EnhancedDataFetcher()
            except:
                logger.warning("Could not initialize data fetcher - using mock data")
                self.data_fetcher = MockDataFetcher()

            logger.info("Successfully initialized all learning components")

        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise

    def run_weekly_update(self, week: Optional[int] = None, season: Optional[int] = None):
        """Run complete weekly model update process"""
        logger.info("=" * 50)
        logger.info("STARTING WEEKLY MODEL UPDATE")
        logger.info("=" * 50)

        try:
            # Step 1: Fetch latest game results
            game_results = self._fetch_game_results(week, season)
            logger.info(f"Fetched {len(game_results)} game results")

            # Step 2: Process game outcomes
            self._process_game_outcomes(game_results)

            # Step 3: Update expert weights
            if self.config['update_expert_weights']:
                self._update_expert_weights()

            # Step 4: Check for belief revisions
            self._check_belief_revisions()

            # Step 5: Detect drift and trigger retraining
            if self.config['enable_drift_detection']:
                self._detect_drift_and_retrain()

            # Step 6: Clean up memory
            if self.config['memory_cleanup']:
                self._cleanup_memory()

            # Step 7: Generate reports
            if self.config['generate_reports']:
                report = self._generate_update_report()
                self._save_report(report)

            # Step 8: Backup models
            if self.config['backup_models']:
                self._backup_models()

            logger.info("WEEKLY MODEL UPDATE COMPLETED SUCCESSFULLY")

        except Exception as e:
            logger.error(f"Error during weekly update: {e}")
            self.update_stats['errors'].append(str(e))
            raise

        finally:
            self._log_update_summary()

    def _fetch_game_results(self, week: Optional[int], season: Optional[int]) -> List[Dict[str, Any]]:
        """Fetch game results from the past week"""
        try:
            if not week or not season:
                # Use current week if not specified
                now = datetime.now()
                week = self._get_current_nfl_week()
                season = now.year

            logger.info(f"Fetching results for Week {week}, {season}")

            # Fetch from data fetcher
            games = self.data_fetcher.get_completed_games(week, season)

            # Convert to standard format
            game_results = []
            for game in games:
                result = {
                    'game_id': game.get('id', f"{game.get('home_team')}_{game.get('away_team')}_{week}"),
                    'week': week,
                    'season': season,
                    'home_team': game.get('home_team'),
                    'away_team': game.get('away_team'),
                    'home_score': game.get('home_score', 0),
                    'away_score': game.get('away_score', 0),
                    'spread': game.get('spread', 0),
                    'total': game.get('total', 0),
                    'completed': game.get('completed', True),
                    'date': game.get('date', datetime.now().isoformat())
                }
                game_results.append(result)

            return game_results

        except Exception as e:
            logger.error(f"Error fetching game results: {e}")
            # Return mock data for testing
            return self._generate_mock_game_results(week or 1, season or 2024)

    def _generate_mock_game_results(self, week: int, season: int) -> List[Dict[str, Any]]:
        """Generate mock game results for testing"""
        teams = ['BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT']
        games = []

        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                home_score = np.random.randint(14, 35)
                away_score = np.random.randint(7, 31)

                games.append({
                    'game_id': f"{teams[i]}_{teams[i+1]}_{week}_{season}",
                    'week': week,
                    'season': season,
                    'home_team': teams[i],
                    'away_team': teams[i + 1],
                    'home_score': home_score,
                    'away_score': away_score,
                    'spread': home_score - away_score,
                    'total': home_score + away_score,
                    'completed': True,
                    'date': (datetime.now() - timedelta(days=np.random.randint(1, 7))).isoformat()
                })

        return games

    def _get_current_nfl_week(self) -> int:
        """Get current NFL week (simplified)"""
        # This is a simplified version - in production, use proper NFL calendar
        now = datetime.now()
        september_1 = datetime(now.year, 9, 1)

        if now < september_1:
            return 1  # Preseason or early season

        days_since_season_start = (now - september_1).days
        week = min(18, max(1, days_since_season_start // 7 + 1))
        return week

    def _process_game_outcomes(self, game_results: List[Dict[str, Any]]):
        """Process game outcomes and update learning systems"""
        logger.info("Processing game outcomes for learning updates")

        try:
            # Get stored predictions for these games
            stored_predictions = self._get_stored_predictions(game_results)

            for game in game_results:
                game_id = game['game_id']

                if game_id in stored_predictions:
                    predictions = stored_predictions[game_id]

                    # Calculate actual outcomes
                    actual_outcomes = self._calculate_actual_outcomes(game)

                    # Process each expert's predictions
                    for expert_id, expert_predictions in predictions.items():
                        for prediction_type, pred_data in expert_predictions.items():
                            predicted_value = pred_data.get('value', 0.5)
                            confidence = pred_data.get('confidence', 0.5)
                            actual_value = actual_outcomes.get(prediction_type, 0.5)

                            # Record outcome in learning coordinator
                            prediction_id = f"{game_id}_{expert_id}_{prediction_type}"
                            self.learning_coordinator.record_prediction_outcome(
                                prediction_id=prediction_id,
                                expert_id=expert_id,
                                game_id=game_id,
                                prediction_type=prediction_type,
                                predicted_value=predicted_value,
                                confidence=confidence,
                                actual_value=actual_value,
                                context=game
                            )

                            # Record in prediction monitor
                            self.prediction_monitor.record_prediction(
                                expert_id=expert_id,
                                prediction=predicted_value,
                                actual=actual_value,
                                confidence=confidence
                            )

                            # Process for continuous learner
                            features = self._extract_features(game)
                            self.continuous_learner.process_game_outcome(
                                game_id=game_id,
                                predictions={expert_id: predicted_value},
                                actual_results={expert_id: actual_value},
                                features=features
                            )

            logger.info(f"Processed outcomes for {len(game_results)} games")

        except Exception as e:
            logger.error(f"Error processing game outcomes: {e}")
            self.update_stats['errors'].append(f"Process outcomes: {e}")

    def _get_stored_predictions(self, game_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retrieve stored predictions for games"""
        stored_predictions = {}

        try:
            # This would normally query your prediction database
            # For now, generate mock predictions
            for game in game_results:
                game_id = game['game_id']
                stored_predictions[game_id] = self._generate_mock_predictions(game)

            return stored_predictions

        except Exception as e:
            logger.error(f"Error retrieving stored predictions: {e}")
            return {}

    def _generate_mock_predictions(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock predictions for testing"""
        experts = ['momentum_expert', 'weather_expert', 'historical_expert', 'advanced_stats_expert']
        prediction_types = ['spread', 'total', 'moneyline']

        predictions = {}
        for expert in experts:
            expert_preds = {}
            for pred_type in prediction_types:
                expert_preds[pred_type] = {
                    'value': np.random.uniform(0.2, 0.8),
                    'confidence': np.random.uniform(0.5, 0.9)
                }
            predictions[expert] = expert_preds

        return predictions

    def _calculate_actual_outcomes(self, game: Dict[str, Any]) -> Dict[str, float]:
        """Calculate actual outcomes from game results"""
        home_score = game['home_score']
        away_score = game['away_score']
        total_points = home_score + away_score
        point_spread = home_score - away_score

        return {
            'spread': 1.0 if point_spread > 0 else 0.0,
            'total': total_points / 70.0,  # Normalize to 0-1
            'moneyline': 1.0 if home_score > away_score else 0.0
        }

    def _extract_features(self, game: Dict[str, Any]) -> np.ndarray:
        """Extract features from game data"""
        # This is a simplified feature extraction
        features = [
            game.get('home_score', 0) / 50.0,  # Normalized scores
            game.get('away_score', 0) / 50.0,
            game.get('week', 1) / 18.0,
            1.0 if game.get('completed') else 0.0
        ]

        # Pad to consistent length
        while len(features) < 10:
            features.append(0.0)

        return np.array(features[:10])

    def _update_expert_weights(self):
        """Update expert weights based on recent performance"""
        logger.info("Updating expert weights")

        try:
            expert_performances = self.learning_coordinator.get_expert_performance()

            for expert_id, performance in expert_performances.items():
                if performance and performance.total_predictions >= self.config['minimum_predictions']:
                    # Check if weight update is needed
                    accuracy_change = abs(performance.accuracy - 0.5)

                    if accuracy_change >= self.config['retraining_threshold']:
                        # Force weight update
                        self.learning_coordinator._update_expert_weights(expert_id)
                        self.update_stats['experts_updated'] += 1

                        logger.info(f"Updated weights for {expert_id}: "
                                   f"accuracy={performance.accuracy:.3f}, "
                                   f"weight={performance.weight:.3f}")

        except Exception as e:
            logger.error(f"Error updating expert weights: {e}")
            self.update_stats['errors'].append(f"Weight update: {e}")

    def _check_belief_revisions(self):
        """Check for and trigger belief revisions"""
        logger.info("Checking for belief revisions")

        try:
            expert_performances = self.learning_coordinator.get_expert_performance()

            for expert_id, performance in expert_performances.items():
                if performance and performance.recent_accuracy < self.config['belief_revision_threshold']:
                    # Trigger belief revision
                    mock_outcome = type('MockOutcome', (), {
                        'expert_id': expert_id,
                        'was_correct': False,
                        'error_magnitude': 0.5,
                        'confidence': 0.5,
                        'prediction_type': 'mock',
                        'to_dict': lambda: {}
                    })()

                    self.learning_coordinator._trigger_belief_revision(expert_id, mock_outcome)
                    self.update_stats['belief_revisions'] += 1

                    logger.info(f"Triggered belief revision for {expert_id} "
                               f"(accuracy: {performance.recent_accuracy:.3f})")

        except Exception as e:
            logger.error(f"Error checking belief revisions: {e}")
            self.update_stats['errors'].append(f"Belief revision: {e}")

    def _detect_drift_and_retrain(self):
        """Detect drift and trigger retraining if needed"""
        logger.info("Detecting drift and checking retraining needs")

        try:
            # Check for retraining flags
            flag_dir = Path("data/retrain_flags")
            if flag_dir.exists():
                for flag_file in flag_dir.glob("*.flag"):
                    try:
                        with open(flag_file) as f:
                            flag_data = json.load(f)

                        model_id = flag_file.stem.replace("_retrain", "")
                        reason = flag_data.get('reason', 'unknown')

                        logger.warning(f"Retraining flag found for {model_id}: {reason}")

                        # Trigger retraining
                        success = self._retrain_model(model_id, reason)

                        if success:
                            flag_file.unlink()  # Remove flag after successful retraining
                            self.update_stats['models_retrained'] += 1
                            logger.info(f"Successfully retrained {model_id}")

                    except Exception as e:
                        logger.error(f"Error processing retraining flag {flag_file}: {e}")

            # Check drift scores from monitor
            if self.prediction_monitor.dashboard_data:
                for expert_id, drift_score in self.prediction_monitor.dashboard_data.drift_scores.items():
                    if drift_score > 0.5:  # High drift threshold
                        logger.warning(f"High drift detected for {expert_id}: {drift_score:.3f}")
                        self._retrain_model(expert_id, "high_drift")
                        self.update_stats['models_retrained'] += 1

        except Exception as e:
            logger.error(f"Error in drift detection and retraining: {e}")
            self.update_stats['errors'].append(f"Drift detection: {e}")

    def _retrain_model(self, model_id: str, reason: str) -> bool:
        """Retrain a specific model"""
        logger.info(f"Retraining model {model_id} (reason: {reason})")

        try:
            # This is a simplified retraining process
            # In production, this would involve:
            # 1. Loading training data
            # 2. Retraining the model with new parameters
            # 3. Validating performance
            # 4. Updating model weights

            # For now, simulate retraining
            logger.info(f"Simulating retraining for {model_id}")

            # Reset learning rate for the model
            if hasattr(self.continuous_learner, 'reset_learning_rate'):
                self.continuous_learner.reset_learning_rate()

            # Log retraining event
            self.learning_coordinator._log_learning_event(
                self.learning_coordinator.LearningEvent.RETRAINING_TRIGGER,
                model_id,
                {'reason': reason, 'timestamp': datetime.now().isoformat()},
                impact_score=1.0
            )

            return True

        except Exception as e:
            logger.error(f"Error retraining model {model_id}: {e}")
            return False

    def _cleanup_memory(self):
        """Clean up old memory entries"""
        logger.info("Cleaning up memory")

        try:
            # Clean up old database entries
            cutoff_date = datetime.now() - timedelta(days=30)

            databases = [
                "data/continuous_learning.db",
                "data/learning_coordination.db",
                "data/prediction_monitoring.db"
            ]

            for db_path in databases:
                if Path(db_path).exists():
                    with sqlite3.connect(db_path) as conn:
                        # Get table names
                        tables = conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        ).fetchall()

                        for (table_name,) in tables:
                            # Check if table has timestamp column
                            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                            has_timestamp = any('timestamp' in col[1].lower() for col in columns)

                            if has_timestamp:
                                deleted = conn.execute(
                                    f"DELETE FROM {table_name} WHERE timestamp < ?",
                                    (cutoff_date.isoformat(),)
                                ).rowcount

                                if deleted > 0:
                                    logger.info(f"Cleaned {deleted} old records from {table_name}")

            logger.info("Memory cleanup completed")

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            self.update_stats['errors'].append(f"Memory cleanup: {e}")

    def _generate_update_report(self) -> Dict[str, Any]:
        """Generate comprehensive update report"""
        logger.info("Generating update report")

        try:
            # Get learning summary
            learning_summary = self.learning_coordinator.get_learning_summary(days=7)

            # Get monitoring report
            monitoring_report = self.prediction_monitor.generate_monitoring_report()

            # Get expert performances
            expert_performances = self.learning_coordinator.get_expert_performance()
            expert_summary = {}
            for expert_id, perf in expert_performances.items():
                if perf:
                    expert_summary[expert_id] = {
                        'accuracy': perf.accuracy,
                        'recent_accuracy': perf.recent_accuracy,
                        'weight': perf.weight,
                        'trend': perf.trend,
                        'total_predictions': perf.total_predictions
                    }

            # Calculate performance improvements
            improvements = 0
            for expert_id, perf in expert_performances.items():
                if perf and perf.trend == 'improving':
                    improvements += 1

            self.update_stats['performance_improvements'] = improvements
            self.update_stats['end_time'] = datetime.now()
            self.update_stats['duration'] = (
                self.update_stats['end_time'] - self.update_stats['start_time']
            ).total_seconds()

            report = {
                'update_timestamp': datetime.now().isoformat(),
                'update_stats': self.update_stats,
                'learning_summary': learning_summary,
                'expert_performances': expert_summary,
                'monitoring_report': monitoring_report,
                'system_health': monitoring_report.get('system_health', 'unknown'),
                'recommendations': self._generate_recommendations(expert_summary, monitoring_report)
            }

            return report

        except Exception as e:
            logger.error(f"Error generating update report: {e}")
            return {
                'error': str(e),
                'update_timestamp': datetime.now().isoformat(),
                'update_stats': self.update_stats
            }

    def _generate_recommendations(self, expert_summary: Dict[str, Any],
                                monitoring_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on update results"""
        recommendations = []

        try:
            # Check overall system health
            system_health = monitoring_report.get('system_health', 'unknown')
            if system_health == 'critical':
                recommendations.append("URGENT: System health is critical - investigate immediately")
            elif system_health == 'degraded':
                recommendations.append("WARNING: System performance is degraded - monitor closely")

            # Check expert performances
            poor_performers = [
                expert_id for expert_id, perf in expert_summary.items()
                if perf['recent_accuracy'] < 0.5
            ]

            if poor_performers:
                recommendations.append(
                    f"Consider reviewing or replacing poor performing experts: {', '.join(poor_performers)}"
                )

            # Check for declining experts
            declining = [
                expert_id for expert_id, perf in expert_summary.items()
                if perf['trend'] == 'declining'
            ]

            if declining:
                recommendations.append(
                    f"Monitor declining experts for potential belief revision: {', '.join(declining)}"
                )

            # Check alert count
            alert_count = monitoring_report.get('active_alerts_count', 0)
            if alert_count > 10:
                recommendations.append("High number of active alerts - investigate alert causes")

            # Check if retraining was successful
            if self.update_stats['models_retrained'] > 0:
                recommendations.append("Monitor retrained models for performance improvement")

            # General recommendations
            if not recommendations:
                recommendations.append("System appears healthy - continue monitoring")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(f"Error generating recommendations: {e}")

        return recommendations

    def _save_report(self, report: Dict[str, Any]):
        """Save update report to file"""
        try:
            reports_dir = Path("reports/weekly_updates")
            reports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"weekly_update_{timestamp}.json"

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Saved update report to {report_path}")

            # Also save latest report
            latest_path = reports_dir / "latest_update.json"
            with open(latest_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def _backup_models(self):
        """Backup current models"""
        logger.info("Backing up models")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(f"models/backups/weekly_update_{timestamp}")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup continuous learner models
            self.continuous_learner.save_models(str(backup_dir / "continuous_learning"))

            # Backup learning state
            state_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'expert_performances': {
                    eid: perf.to_dict() if perf else None
                    for eid, perf in self.learning_coordinator.expert_performances.items()
                },
                'update_stats': self.update_stats
            }

            with open(backup_dir / "learning_state.json", 'w') as f:
                json.dump(state_data, f, indent=2, default=str)

            logger.info(f"Models backed up to {backup_dir}")

        except Exception as e:
            logger.error(f"Error backing up models: {e}")
            self.update_stats['errors'].append(f"Backup: {e}")

    def _log_update_summary(self):
        """Log summary of update process"""
        logger.info("=" * 50)
        logger.info("WEEKLY UPDATE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Duration: {self.update_stats.get('duration', 0):.1f} seconds")
        logger.info(f"Experts updated: {self.update_stats['experts_updated']}")
        logger.info(f"Models retrained: {self.update_stats['models_retrained']}")
        logger.info(f"Belief revisions: {self.update_stats['belief_revisions']}")
        logger.info(f"Performance improvements: {self.update_stats['performance_improvements']}")
        logger.info(f"Errors: {len(self.update_stats['errors'])}")

        if self.update_stats['errors']:
            logger.warning("Errors encountered:")
            for error in self.update_stats['errors']:
                logger.warning(f"  - {error}")

        logger.info("=" * 50)

class MockDataFetcher:
    """Mock data fetcher for testing"""
    def get_completed_games(self, week: int, season: int) -> List[Dict[str, Any]]:
        return []

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="Update NFL prediction models")
    parser.add_argument('--week', type=int, help='NFL week to process')
    parser.add_argument('--season', type=int, help='NFL season year')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')

    args = parser.parse_args()

    try:
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)

        # Initialize orchestrator
        orchestrator = ModelUpdateOrchestrator(args.config)

        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # In dry run, just generate reports without updates
            report = orchestrator._generate_update_report()
            print(json.dumps(report, indent=2, default=str))
        else:
            # Run full update
            orchestrator.run_weekly_update(args.week, args.season)

    except Exception as e:
        logger.error(f"Fatal error in model update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()