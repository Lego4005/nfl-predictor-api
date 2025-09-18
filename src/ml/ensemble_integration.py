#!/usr/bin/env python3
"""
Integration layer for Advanced Ensemble Predictor
Connects the ensemble predictor with existing NFL prediction system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import asyncio
from pathlib import Path

# Import ensemble predictor and validator
from .ensemble_predictor import AdvancedEnsemblePredictor
from .model_validator import ModelValidator

# Import existing system components
try:
    from .data_pipeline import NFLDataPipeline
    from .enhanced_features import EnhancedFeatureEngine
    from .prediction_service import PredictionService
    from .game_prediction_models import GamePredictionModels
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import existing components: {e}")
    logger.info("Running in standalone mode")

logger = logging.getLogger(__name__)


class EnsembleIntegration:
    """Integration layer for advanced ensemble predictor"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.ensemble_predictor = None
        self.validator = ModelValidator(save_results=True)
        self.data_pipeline = None
        self.feature_engine = None

        # Model paths
        self.models_dir = Path('/home/iris/code/experimental/nfl-predictor-api/models')
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Performance tracking
        self.prediction_history = []
        self.performance_metrics = {}

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize ensemble predictor and supporting components"""

        try:
            # Initialize ensemble predictor
            self.ensemble_predictor = AdvancedEnsemblePredictor(self.config)

            # Initialize data pipeline if available
            try:
                self.data_pipeline = NFLDataPipeline()
                self.feature_engine = EnhancedFeatureEngine()
                logger.info("Integrated with existing NFL data pipeline")
            except NameError:
                logger.info("Running without existing data pipeline")

            logger.info("Ensemble integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ensemble integration: {e}")
            raise

    def prepare_training_data(self, start_date: str = '2020-01-01',
                            end_date: str = '2024-01-01') -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare training data from existing system or mock data"""

        if self.data_pipeline:
            # Use existing data pipeline
            try:
                raw_data = self.data_pipeline.get_historical_data(start_date, end_date)

                if self.feature_engine:
                    processed_data = self.feature_engine.create_features(raw_data)
                else:
                    processed_data = raw_data

                # Create target variable (home team win = 1, away team win = 0, tie = 2)
                target = self._create_target_variable(processed_data)

                logger.info(f"Prepared training data: {processed_data.shape}")
                return processed_data, target

            except Exception as e:
                logger.warning(f"Failed to use existing data pipeline: {e}")
                logger.info("Falling back to mock data")

        # Create mock training data
        return self._create_mock_training_data()

    def _create_target_variable(self, data: pd.DataFrame) -> np.ndarray:
        """Create target variable from game results"""

        if 'home_score' in data.columns and 'away_score' in data.columns:
            home_scores = data['home_score']
            away_scores = data['away_score']

            target = np.where(home_scores > away_scores, 1,  # Home win
                            np.where(home_scores < away_scores, 0, 2))  # Away win, Tie

        elif 'result' in data.columns:
            # If result column exists (W/L/T)
            target = data['result'].map({'W': 1, 'L': 0, 'T': 2}).fillna(1).astype(int)

        else:
            # Create synthetic target with home field advantage
            np.random.seed(42)
            target = np.random.choice([0, 1], size=len(data), p=[0.45, 0.55])

        return target

    def _create_mock_training_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Create comprehensive mock training data for testing"""

        logger.info("Creating mock training data...")

        n_samples = 2000
        np.random.seed(42)

        # NFL team names
        nfl_teams = [
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN',
            'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LAS', 'LAC', 'LAR', 'MIA',
            'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
        ]

        # Create base game data
        data = {
            'game_id': [f'game_{i}' for i in range(n_samples)],
            'home_team': np.random.choice(nfl_teams, n_samples),
            'away_team': np.random.choice(nfl_teams, n_samples),
            'week': np.random.randint(1, 18, n_samples),
            'season': np.random.choice([2020, 2021, 2022, 2023], n_samples),
            'game_date': [f'2023-{np.random.randint(9, 13):02d}-{np.random.randint(1, 29):02d}' for _ in range(n_samples)],

            # Team performance metrics
            'home_power_rating': np.random.normal(85, 12, n_samples),
            'away_power_rating': np.random.normal(85, 12, n_samples),
            'home_offensive_rating': np.random.normal(75, 15, n_samples),
            'away_offensive_rating': np.random.normal(75, 15, n_samples),
            'home_defensive_rating': np.random.normal(75, 15, n_samples),
            'away_defensive_rating': np.random.normal(75, 15, n_samples),

            # Recent performance
            'home_wins_last_4': np.random.randint(0, 5, n_samples),
            'away_wins_last_4': np.random.randint(0, 5, n_samples),
            'home_point_diff_last_4': np.random.normal(0, 20, n_samples),
            'away_point_diff_last_4': np.random.normal(0, 20, n_samples),

            # Game context
            'is_divisional': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'is_primetime': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
            'is_playoff': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
            'location': np.random.choice(['outdoor', 'dome'], n_samples, p=[0.75, 0.25]),

            # Betting data
            'opening_spread': np.random.normal(0, 6, n_samples),
            'closing_spread': np.random.normal(0, 6, n_samples),
            'total_line': np.random.normal(45, 5, n_samples),
            'public_bet_percentage': np.random.uniform(30, 80, n_samples),

            # Advanced metrics
            'home_yards_per_play': np.random.normal(5.5, 1.0, n_samples),
            'away_yards_per_play': np.random.normal(5.5, 1.0, n_samples),
            'home_turnover_diff': np.random.normal(0, 2, n_samples),
            'away_turnover_diff': np.random.normal(0, 2, n_samples),
            'home_red_zone_pct': np.random.uniform(40, 80, n_samples),
            'away_red_zone_pct': np.random.uniform(40, 80, n_samples),
            'home_third_down_pct': np.random.uniform(30, 50, n_samples),
            'away_third_down_pct': np.random.uniform(30, 50, n_samples),

            # Injury and coaching
            'home_injury_score': np.random.exponential(0.2, n_samples),
            'away_injury_score': np.random.exponential(0.2, n_samples),
            'home_coach_experience': np.random.randint(1, 20, n_samples),
            'away_coach_experience': np.random.randint(1, 20, n_samples),

            # Weather will be added by ensemble predictor
            'temperature_expected': np.random.normal(60, 20, n_samples),
            'wind_speed_expected': np.random.exponential(8, n_samples),
        }

        # Create DataFrame
        df = pd.DataFrame(data)

        # Ensure home and away teams are different
        mask = df['home_team'] == df['away_team']
        df.loc[mask, 'away_team'] = np.random.choice(
            [team for team in nfl_teams if team != df.loc[mask, 'home_team'].iloc[0]],
            mask.sum()
        )

        # Create realistic target variable with correlations
        home_advantage = (
            df['home_power_rating'] - df['away_power_rating'] +
            (df['home_wins_last_4'] - df['away_wins_last_4']) * 2 +
            np.random.normal(3, 2, n_samples)  # Home field advantage
        )

        # Convert to probabilities
        home_win_prob = 1 / (1 + np.exp(-home_advantage / 10))

        # Generate target
        target = np.random.binomial(1, home_win_prob)

        # Add some ties (rare)
        tie_indices = np.random.choice(len(target), size=int(len(target) * 0.02), replace=False)
        target[tie_indices] = 2

        logger.info(f"Created mock training data: {df.shape}")
        return df, target

    async def train_ensemble(self, tune_hyperparameters: bool = True,
                           validation_type: str = 'time_series') -> Dict[str, Any]:
        """Train the ensemble predictor with validation"""

        logger.info("Starting ensemble training process...")

        # Prepare training data
        X, y = self.prepare_training_data()

        # Train ensemble
        training_results = self.ensemble_predictor.fit(X, y, tune_hyperparameters)

        # Validate model
        validation_results = self.validator.validate_model(
            self.ensemble_predictor, X, y, validation_type
        )

        # Combine results
        complete_results = {
            'training': training_results,
            'validation': validation_results,
            'timestamp': datetime.now().isoformat(),
            'data_shape': X.shape,
            'target_distribution': dict(zip(*np.unique(y, return_counts=True)))
        }

        # Save model
        model_path = self.models_dir / 'ensemble_predictor_integrated.pkl'
        self.ensemble_predictor.save_model(str(model_path))

        logger.info(f"Ensemble training completed. Model saved to {model_path}")
        return complete_results

    def predict_games(self, games_data: pd.DataFrame,
                     include_explanation: bool = False) -> List[Dict[str, Any]]:
        """Make predictions for upcoming games"""

        if self.ensemble_predictor is None:
            raise ValueError("Ensemble predictor not initialized")

        logger.info(f"Making predictions for {len(games_data)} games")

        # Get predictions and probabilities
        predictions = self.ensemble_predictor.predict(games_data)
        probabilities = self.ensemble_predictor.predict_proba(games_data)

        results = []

        for i, (_, game) in enumerate(games_data.iterrows()):
            prediction_result = {
                'game_id': game.get('game_id', f'game_{i}'),
                'home_team': game.get('home_team', 'HOME'),
                'away_team': game.get('away_team', 'AWAY'),
                'prediction': int(predictions[i]),
                'prediction_label': self._get_prediction_label(predictions[i]),
                'probabilities': {
                    'away_win': float(probabilities[i][0]),
                    'home_win': float(probabilities[i][1]),
                    'tie': float(probabilities[i][2]) if probabilities.shape[1] > 2 else 0.0
                },
                'confidence': float(np.max(probabilities[i])),
                'timestamp': datetime.now().isoformat()
            }

            # Add explanation if requested
            if include_explanation:
                try:
                    explanation = self.ensemble_predictor.explain_prediction(games_data, i)
                    prediction_result['explanation'] = explanation
                except Exception as e:
                    logger.warning(f"Could not generate explanation for game {i}: {e}")
                    prediction_result['explanation'] = {'error': str(e)}

            results.append(prediction_result)

        # Store predictions in history
        self.prediction_history.extend(results)

        return results

    def _get_prediction_label(self, prediction: int) -> str:
        """Convert prediction integer to readable label"""
        labels = {0: 'AWAY_WIN', 1: 'HOME_WIN', 2: 'TIE'}
        return labels.get(prediction, 'UNKNOWN')

    def batch_predict_season(self, season_year: int = 2024) -> Dict[str, Any]:
        """Make predictions for entire season (mock implementation)"""

        logger.info(f"Generating season predictions for {season_year}")

        # Create mock season schedule
        season_data = self._create_mock_season_schedule(season_year)

        # Make predictions
        predictions = self.predict_games(season_data, include_explanation=False)

        # Aggregate results
        season_summary = {
            'season': season_year,
            'total_games': len(predictions),
            'predictions_by_week': {},
            'team_win_predictions': {},
            'high_confidence_games': [],
            'upset_predictions': []
        }

        # Organize by week
        for pred in predictions:
            week = season_data[season_data['game_id'] == pred['game_id']]['week'].iloc[0]

            if week not in season_summary['predictions_by_week']:
                season_summary['predictions_by_week'][week] = []

            season_summary['predictions_by_week'][week].append(pred)

            # Track team predictions
            home_team = pred['home_team']
            away_team = pred['away_team']

            if home_team not in season_summary['team_win_predictions']:
                season_summary['team_win_predictions'][home_team] = 0
            if away_team not in season_summary['team_win_predictions']:
                season_summary['team_win_predictions'][away_team] = 0

            if pred['prediction'] == 1:  # Home win
                season_summary['team_win_predictions'][home_team] += 1
            elif pred['prediction'] == 0:  # Away win
                season_summary['team_win_predictions'][away_team] += 1

            # High confidence games
            if pred['confidence'] > 0.8:
                season_summary['high_confidence_games'].append(pred)

            # Potential upsets (high confidence underdog wins)
            home_favored = season_data[season_data['game_id'] == pred['game_id']]['opening_spread'].iloc[0] < 0
            if pred['confidence'] > 0.7:
                if (home_favored and pred['prediction'] == 0) or (not home_favored and pred['prediction'] == 1):
                    season_summary['upset_predictions'].append(pred)

        return {
            'season_summary': season_summary,
            'detailed_predictions': predictions
        }

    def _create_mock_season_schedule(self, season_year: int, weeks: int = 17) -> pd.DataFrame:
        """Create mock NFL season schedule"""

        games = []
        nfl_teams = [
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN',
            'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LAS', 'LAC', 'LAR', 'MIA',
            'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
        ]

        game_id_counter = 1

        for week in range(1, weeks + 1):
            # Each week, create ~16 games (32 teams / 2)
            week_teams = nfl_teams.copy()
            np.random.shuffle(week_teams)

            for i in range(0, len(week_teams) - 1, 2):
                home_team = week_teams[i]
                away_team = week_teams[i + 1]

                game = {
                    'game_id': f'{season_year}_week_{week}_game_{game_id_counter}',
                    'home_team': home_team,
                    'away_team': away_team,
                    'week': week,
                    'season': season_year,
                    'game_date': f'{season_year}-{9 + (week - 1) // 4:02d}-{((week - 1) % 4) * 7 + 1:02d}',

                    # Mock attributes for prediction
                    'home_power_rating': np.random.normal(85, 10),
                    'away_power_rating': np.random.normal(85, 10),
                    'opening_spread': np.random.normal(0, 5),
                    'total_line': np.random.normal(45, 4),
                    'is_divisional': np.random.choice([0, 1], p=[0.75, 0.25]),
                    'location': np.random.choice(['outdoor', 'dome'], p=[0.7, 0.3])
                }

                games.append(game)
                game_id_counter += 1

        return pd.DataFrame(games)

    def evaluate_predictions(self, actual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate prediction accuracy against actual results"""

        if not self.prediction_history:
            return {'error': 'No predictions to evaluate'}

        # Match predictions with actual results
        evaluation_data = []

        for actual in actual_results:
            # Find corresponding prediction
            pred = next((p for p in self.prediction_history
                        if p['game_id'] == actual['game_id']), None)

            if pred:
                evaluation_data.append({
                    'game_id': actual['game_id'],
                    'predicted': pred['prediction'],
                    'actual': actual['result'],
                    'confidence': pred['confidence'],
                    'correct': pred['prediction'] == actual['result']
                })

        if not evaluation_data:
            return {'error': 'No matching predictions and results found'}

        # Calculate metrics
        df_eval = pd.DataFrame(evaluation_data)

        overall_accuracy = df_eval['correct'].mean()
        high_conf_accuracy = df_eval[df_eval['confidence'] > 0.7]['correct'].mean() if len(df_eval[df_eval['confidence'] > 0.7]) > 0 else 0
        low_conf_accuracy = df_eval[df_eval['confidence'] <= 0.5]['correct'].mean() if len(df_eval[df_eval['confidence'] <= 0.5]) > 0 else 0

        evaluation_results = {
            'overall_accuracy': overall_accuracy,
            'high_confidence_accuracy': high_conf_accuracy,
            'low_confidence_accuracy': low_conf_accuracy,
            'total_evaluated': len(evaluation_data),
            'confidence_distribution': {
                'mean': df_eval['confidence'].mean(),
                'std': df_eval['confidence'].std(),
                'min': df_eval['confidence'].min(),
                'max': df_eval['confidence'].max()
            },
            'detailed_results': evaluation_data
        }

        # Update performance metrics
        self.performance_metrics['latest_evaluation'] = evaluation_results

        return evaluation_results

    def generate_performance_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive performance dashboard data"""

        if not self.ensemble_predictor:
            return {'error': 'Ensemble predictor not available'}

        # Get model performance report
        model_report = self.ensemble_predictor.get_model_performance_report()

        # Get validation report
        validation_report = self.validator.generate_validation_report()

        # Create dashboard data
        dashboard_data = {
            'model_performance': model_report,
            'validation_summary': validation_report,
            'prediction_history': {
                'total_predictions': len(self.prediction_history),
                'latest_predictions': self.prediction_history[-10:] if self.prediction_history else []
            },
            'performance_metrics': self.performance_metrics,
            'system_status': {
                'ensemble_trained': self.ensemble_predictor is not None,
                'data_pipeline_available': self.data_pipeline is not None,
                'feature_engine_available': self.feature_engine is not None,
                'last_updated': datetime.now().isoformat()
            }
        }

        return dashboard_data

    def load_trained_model(self, model_path: Optional[str] = None) -> bool:
        """Load a previously trained ensemble model"""

        if model_path is None:
            model_path = self.models_dir / 'ensemble_predictor_integrated.pkl'

        try:
            if not Path(model_path).exists():
                logger.error(f"Model file not found: {model_path}")
                return False

            self.ensemble_predictor = AdvancedEnsemblePredictor()
            self.ensemble_predictor.load_model(str(model_path))

            logger.info(f"Ensemble model loaded from {model_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False


# Async wrapper for integration
class AsyncEnsembleIntegration:
    """Async wrapper for ensemble integration"""

    def __init__(self, config: Optional[Dict] = None):
        self.integration = EnsembleIntegration(config)

    async def train_ensemble_async(self, tune_hyperparameters: bool = True) -> Dict[str, Any]:
        """Async wrapper for ensemble training"""
        return await self.integration.train_ensemble(tune_hyperparameters)

    async def predict_games_async(self, games_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Async wrapper for game predictions"""
        return self.integration.predict_games(games_data)

    async def evaluate_predictions_async(self, actual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Async wrapper for prediction evaluation"""
        return self.integration.evaluate_predictions(actual_results)


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        logger.info("NFL Ensemble Predictor Integration Test")

        # Initialize integration
        integration = EnsembleIntegration()

        # Train ensemble
        logger.info("Training ensemble...")
        training_results = await integration.train_ensemble(tune_hyperparameters=False)

        print(f"Training Results:")
        print(f"Ensemble Accuracy: {training_results['validation']['overall_metrics']['accuracy']:.4f}")

        # Make sample predictions
        logger.info("Making sample predictions...")
        sample_games = integration._create_mock_season_schedule(2024, weeks=1)
        predictions = integration.predict_games(sample_games.head(5), include_explanation=True)

        print(f"\nSample Predictions:")
        for pred in predictions[:3]:
            print(f"{pred['away_team']} @ {pred['home_team']}: {pred['prediction_label']} "
                  f"(Confidence: {pred['confidence']:.3f})")

        # Generate dashboard
        dashboard = integration.generate_performance_dashboard()
        print(f"\nDashboard Summary:")
        print(f"Model Status: {'Ready' if dashboard['system_status']['ensemble_trained'] else 'Not Ready'}")
        print(f"Total Features: {dashboard['model_performance']['feature_count']}")

        logger.info("Integration test completed successfully")

    asyncio.run(main())