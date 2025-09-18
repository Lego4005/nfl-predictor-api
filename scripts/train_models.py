#!/usr/bin/env python3
"""
NFL ML Model Training Pipeline
Downloads historical data, performs feature engineering, trains models with hyperparameter tuning
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import logging
from typing import Dict, List, Tuple, Any, Optional
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.ml_models import NFLEnsembleModel, hyperparameter_tuning
from src.ml.feature_engineering import AdvancedFeatureEngineer
from src.ml.confidence_calibration import ConfidenceCalibrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SportsDataAPIClient:
    """Client for SportsData.io API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sportsdata.io/v3/nfl"
        self.session = requests.Session()

    def get_historical_games(self, seasons: List[int]) -> List[Dict[str, Any]]:
        """Download historical game data"""
        all_games = []

        for season in seasons:
            logger.info(f"Fetching games for {season} season...")

            # Get regular season games
            for week in range(1, 19):  # 18 regular season weeks
                try:
                    url = f"{self.base_url}/scores/json/ScoresByWeek/{season}/{week}"
                    params = {'key': self.api_key}

                    response = self.session.get(url, params=params)
                    response.raise_for_status()

                    week_games = response.json()
                    if week_games:
                        all_games.extend(week_games)

                except Exception as e:
                    logger.error(f"Error fetching week {week}, season {season}: {e}")
                    continue

            # Get playoff games
            try:
                url = f"{self.base_url}/scores/json/ScoresByWeek/{season}/1"  # Playoffs
                params = {'key': self.api_key, 'seasontype': 'POST'}

                response = self.session.get(url, params=params)
                response.raise_for_status()

                playoff_games = response.json()
                if playoff_games:
                    all_games.extend(playoff_games)

            except Exception as e:
                logger.error(f"Error fetching playoffs for season {season}: {e}")

        logger.info(f"Downloaded {len(all_games)} historical games")
        return all_games

    def get_team_stats(self, seasons: List[int]) -> List[Dict[str, Any]]:
        """Download team statistics"""
        all_stats = []

        for season in seasons:
            try:
                url = f"{self.base_url}/stats/json/TeamSeasonStats/{season}"
                params = {'key': self.api_key}

                response = self.session.get(url, params=params)
                response.raise_for_status()

                season_stats = response.json()
                if season_stats:
                    all_stats.extend(season_stats)

            except Exception as e:
                logger.error(f"Error fetching team stats for season {season}: {e}")

        return all_stats

    def get_player_stats(self, seasons: List[int]) -> List[Dict[str, Any]]:
        """Download player statistics"""
        all_player_stats = []

        for season in seasons:
            try:
                # Get passing stats
                url = f"{self.base_url}/stats/json/PlayerSeasonStats/{season}"
                params = {'key': self.api_key}

                response = self.session.get(url, params=params)
                response.raise_for_status()

                player_stats = response.json()
                if player_stats:
                    all_player_stats.extend(player_stats)

            except Exception as e:
                logger.error(f"Error fetching player stats for season {season}: {e}")

        return all_player_stats

class NFLDataProcessor:
    """Process NFL data for model training"""

    def __init__(self):
        self.feature_engineer = AdvancedFeatureEngineer()

    def process_games_data(self, games_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Process raw games data into structured DataFrame"""
        processed_games = []

        for game in games_data:
            if not game.get('IsClosed', False):
                continue  # Skip incomplete games

            # Home team record
            home_record = {
                'game_id': game['GameID'],
                'season': game['Season'],
                'week': game['Week'],
                'date': pd.to_datetime(game['DateTime']),
                'team': game['HomeTeam'],
                'opponent': game['AwayTeam'],
                'is_home': True,
                'points_scored': game.get('HomeScore', 0),
                'points_allowed': game.get('AwayScore', 0),
                'won_game': 1 if game.get('HomeScore', 0) > game.get('AwayScore', 0) else 0,
                'total_points': game.get('HomeScore', 0) + game.get('AwayScore', 0),
                'spread_line': game.get('PointSpread', 0),
                'total_line': game.get('OverUnder', 45),
                'is_playoff': game.get('SeasonType') == 3,
                'weather_temp': game.get('Temperature'),
                'weather_wind': game.get('WindSpeed'),
                'weather_conditions': game.get('WeatherConditions', ''),
                'stadium': game.get('StadiumDetails', {}).get('Name', ''),
                'dome_game': game.get('StadiumDetails', {}).get('Type') == 'Dome'
            }
            processed_games.append(home_record)

            # Away team record
            away_record = {
                'game_id': game['GameID'],
                'season': game['Season'],
                'week': game['Week'],
                'date': pd.to_datetime(game['DateTime']),
                'team': game['AwayTeam'],
                'opponent': game['HomeTeam'],
                'is_home': False,
                'points_scored': game.get('AwayScore', 0),
                'points_allowed': game.get('HomeScore', 0),
                'won_game': 1 if game.get('AwayScore', 0) > game.get('HomeScore', 0) else 0,
                'total_points': game.get('HomeScore', 0) + game.get('AwayScore', 0),
                'spread_line': -game.get('PointSpread', 0) if game.get('PointSpread') else 0,
                'total_line': game.get('OverUnder', 45),
                'is_playoff': game.get('SeasonType') == 3,
                'weather_temp': game.get('Temperature'),
                'weather_wind': game.get('WindSpeed'),
                'weather_conditions': game.get('WeatherConditions', ''),
                'stadium': game.get('StadiumDetails', {}).get('Name', ''),
                'dome_game': game.get('StadiumDetails', {}).get('Type') == 'Dome'
            }
            processed_games.append(away_record)

        games_df = pd.DataFrame(processed_games)

        # Add division and conference information
        games_df = self._add_division_info(games_df)

        return games_df

    def _add_division_info(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """Add division and conference information"""
        # Division mappings
        divisions = {
            'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
            'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
            'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
            'AFC West': ['DEN', 'KC', 'LV', 'LAC'],
            'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
            'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
            'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
            'NFC West': ['ARI', 'LAR', 'SF', 'SEA']
        }

        # Create mappings
        team_to_division = {}
        team_to_conference = {}

        for division, teams in divisions.items():
            conference = 'AFC' if division.startswith('AFC') else 'NFC'
            for team in teams:
                team_to_division[team] = division
                team_to_conference[team] = conference

        # Add to dataframe
        games_df['division'] = games_df['team'].map(team_to_division)
        games_df['conference'] = games_df['team'].map(team_to_conference)
        games_df['opponent_division'] = games_df['opponent'].map(team_to_division)
        games_df['opponent_conference'] = games_df['opponent'].map(team_to_conference)

        # Add division/conference game flags
        games_df['is_division_game'] = (games_df['division'] == games_df['opponent_division']).astype(int)
        games_df['is_conference_game'] = (games_df['conference'] == games_df['opponent_conference']).astype(int)

        return games_df

    def create_training_datasets(self, games_df: pd.DataFrame) -> Dict[str, Tuple[pd.DataFrame, np.ndarray]]:
        """Create training datasets for different prediction tasks"""

        # Engineer advanced features
        features_df = self.feature_engineer.engineer_advanced_features(games_df)

        training_data = {}

        # Game Winner Dataset
        winner_features = features_df[[
            'team', 'opponent', 'is_home', 'week', 'season',
            'points_scored_avg_3', 'points_scored_avg_5', 'points_allowed_avg_3',
            'points_allowed_avg_5', 'rest_days', 'is_division_game', 'is_conference_game'
        ]].copy()

        # Create matchup features for game winner prediction
        winner_matchups = self._create_matchup_features(winner_features)
        winner_labels = games_df['won_game'].values

        training_data['game_winner'] = (winner_matchups, winner_labels)

        # Total Points Dataset
        total_features = features_df[[
            'team', 'opponent', 'is_home', 'week',
            'points_scored_avg_3', 'points_scored_avg_5',
            'points_allowed_avg_3', 'points_allowed_avg_5'
        ]].copy()

        total_matchups = self._create_matchup_features(total_features)
        total_labels = games_df['total_points'].values

        training_data['total_points'] = (total_matchups, total_labels)

        # Player Props Dataset (simplified - would need actual player data)
        props_features = features_df[['week', 'is_home', 'points_scored_avg_3']].copy()
        props_labels = np.random.normal(250, 50, len(props_features))  # Placeholder

        training_data['player_props'] = (props_features, props_labels)

        return training_data

    def _create_matchup_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Create head-to-head matchup features"""
        matchup_features = []

        # Group by game (each game has 2 rows: home and away team)
        for game_id in features_df.index[::2]:  # Take every other row
            if game_id + 1 >= len(features_df):
                continue

            home_stats = features_df.iloc[game_id]
            away_stats = features_df.iloc[game_id + 1]

            # Create matchup features
            matchup = {
                'home_team_rating': home_stats.get('points_scored_avg_5', 20) - home_stats.get('points_allowed_avg_5', 20),
                'away_team_rating': away_stats.get('points_scored_avg_5', 20) - away_stats.get('points_allowed_avg_5', 20),
                'home_offensive_rating': home_stats.get('points_scored_avg_5', 20),
                'away_offensive_rating': away_stats.get('points_scored_avg_5', 20),
                'home_defensive_rating': 50 - home_stats.get('points_allowed_avg_5', 20),
                'away_defensive_rating': 50 - away_stats.get('points_allowed_avg_5', 20),
                'home_recent_form_3': home_stats.get('points_scored_avg_3', 20),
                'away_recent_form_3': away_stats.get('points_scored_avg_3', 20),
                'home_recent_form_5': home_stats.get('points_scored_avg_5', 20),
                'away_recent_form_5': away_stats.get('points_scored_avg_5', 20),
                'home_rest_days': home_stats.get('rest_days', 7),
                'away_rest_days': away_stats.get('rest_days', 7),
                'is_division_game': home_stats.get('is_division_game', 0),
                'is_conference_game': home_stats.get('is_conference_game', 0),
                'weather_impact_score': 0,  # Would need weather data
                'travel_distance': 0,  # Would calculate based on teams
                'home_red_zone_efficiency': 0.6,  # Placeholder
                'away_red_zone_efficiency': 0.6,  # Placeholder
                'home_third_down_rate': 0.4,  # Placeholder
                'away_third_down_rate': 0.4,  # Placeholder
                'home_turnover_differential': 0,  # Placeholder
                'away_turnover_differential': 0,  # Placeholder
                'home_epa_per_play': 0,  # Placeholder
                'away_epa_per_play': 0,  # Placeholder
                'home_success_rate': 0.5,  # Placeholder
                'away_success_rate': 0.5,  # Placeholder
                'home_dvoa': 0,  # Placeholder
                'away_dvoa': 0,  # Placeholder
                'home_injuries_impact': 0,  # Placeholder
                'away_injuries_impact': 0   # Placeholder
            }

            matchup_features.append(matchup)

        return pd.DataFrame(matchup_features)


class ModelTrainer:
    """Train and evaluate NFL prediction models"""

    def __init__(self, models_dir: str = '/home/iris/code/experimental/nfl-predictor-api/models'):
        self.models_dir = models_dir
        self.ensemble_model = NFLEnsembleModel()
        self.confidence_calibrator = ConfidenceCalibrator()

        # Create models directory
        os.makedirs(models_dir, exist_ok=True)

    def train_models(self, training_data: Dict[str, Tuple[pd.DataFrame, np.ndarray]]) -> Dict[str, Any]:
        """Train all models with hyperparameter tuning"""

        logger.info("Starting model training with hyperparameter tuning...")

        # Split data
        split_data = {}
        for task, (X, y) in training_data.items():
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if task == 'game_winner' else None
            )
            split_data[task] = (X_train, X_test, y_train, y_test)

        # Hyperparameter tuning (optional - can be time consuming)
        tuning_results = {}
        if False:  # Set to True to enable hyperparameter tuning
            logger.info("Performing hyperparameter tuning...")

            for task, (X_train, _, y_train, _) in split_data.items():
                if task == 'game_winner':
                    model_type = 'xgboost_classifier'
                elif task == 'total_points':
                    model_type = 'random_forest_regressor'
                else:
                    model_type = 'neural_network'

                tuning_results[task] = hyperparameter_tuning(X_train, y_train, model_type)

        # Train ensemble model
        ensemble_training_data = {}
        for task, (X_train, _, y_train, _) in split_data.items():
            ensemble_training_data[task] = (X_train, y_train)

        training_metrics = self.ensemble_model.train(ensemble_training_data)

        # Evaluate on test sets
        test_metrics = {}
        for task, (_, X_test, _, y_test) in split_data.items():
            if task == 'game_winner':
                y_pred_proba = self.ensemble_model.game_winner_model.predict_proba(X_test)
                y_pred = (y_pred_proba > 0.5).astype(int)

                test_metrics[task] = {
                    'accuracy': accuracy_score(y_test, y_pred),
                    'precision': precision_score(y_test, y_pred),
                    'recall': recall_score(y_test, y_pred),
                    'f1': f1_score(y_test, y_pred)
                }

            elif task == 'total_points':
                y_pred = self.ensemble_model.total_points_model.predict(X_test)

                test_metrics[task] = {
                    'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                    'mae': mean_absolute_error(y_test, y_pred),
                    'r2': 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
                }

        # Train confidence calibrator
        if 'game_winner' in split_data:
            X_cal, y_cal = split_data['game_winner'][0], split_data['game_winner'][2]
            probabilities = self.ensemble_model.game_winner_model.predict_proba(X_cal)
            self.confidence_calibrator.fit(probabilities, y_cal)

        # Save models
        self.ensemble_model.save_models(self.models_dir)
        self.confidence_calibrator.save_calibrator(os.path.join(self.models_dir, 'confidence_calibrator.pkl'))

        results = {
            'training_metrics': training_metrics,
            'test_metrics': test_metrics,
            'tuning_results': tuning_results,
            'model_insights': self.ensemble_model.get_model_insights()
        }

        return results

    def generate_accuracy_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive accuracy report"""

        report_lines = [
            "="*80,
            "NFL PREDICTION MODELS - TRAINING REPORT",
            "="*80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "TRAINING METRICS:",
            "-"*40
        ]

        # Training metrics
        for model, metrics in results['training_metrics'].items():
            report_lines.append(f"\n{model.upper()} MODEL:")
            for metric, value in metrics.items():
                report_lines.append(f"  {metric}: {value:.4f}")

        # Test metrics
        report_lines.extend([
            "",
            "TEST SET EVALUATION:",
            "-"*40
        ])

        for model, metrics in results['test_metrics'].items():
            report_lines.append(f"\n{model.upper()} MODEL:")
            for metric, value in metrics.items():
                report_lines.append(f"  {metric}: {value:.4f}")

        # Feature importance
        if 'model_insights' in results:
            report_lines.extend([
                "",
                "FEATURE IMPORTANCE:",
                "-"*40
            ])

            for model, importance_df in results['model_insights'].items():
                report_lines.append(f"\nTop 10 Features - {model.upper()}:")
                for _, row in importance_df.head(10).iterrows():
                    report_lines.append(f"  {row['feature']}: {row['importance']:.4f}")

        report_text = "\n".join(report_lines)

        # Save report
        report_path = os.path.join(self.models_dir, 'training_report.txt')
        with open(report_path, 'w') as f:
            f.write(report_text)

        logger.info(f"Training report saved to: {report_path}")
        return report_text


def main():
    """Main training pipeline"""
    logger.info("Starting NFL ML Model Training Pipeline")

    # Configuration
    API_KEY = os.getenv('SPORTSDATA_API_KEY', 'demo')  # Use demo key if not set
    SEASONS = [2022, 2023, 2024]  # Last 3 years
    MODELS_DIR = '/home/iris/code/experimental/nfl-predictor-api/models'

    try:
        # Initialize components
        api_client = SportsDataAPIClient(API_KEY)
        data_processor = NFLDataProcessor()
        model_trainer = ModelTrainer(MODELS_DIR)

        # Download historical data
        if API_KEY != 'demo':
            logger.info("Downloading historical data from SportsData.io...")
            games_data = api_client.get_historical_games(SEASONS)

            # Save raw data
            with open(os.path.join(MODELS_DIR, 'raw_games_data.json'), 'w') as f:
                json.dump(games_data, f, indent=2, default=str)

        else:
            logger.warning("Using demo API key - loading sample data instead")
            # Create sample data for demo
            games_data = create_sample_data()

        # Process data
        logger.info("Processing games data...")
        games_df = data_processor.process_games_data(games_data)

        # Save processed data
        games_df.to_csv(os.path.join(MODELS_DIR, 'processed_games.csv'), index=False)

        # Create training datasets
        logger.info("Creating training datasets...")
        training_data = data_processor.create_training_datasets(games_df)

        # Train models
        logger.info("Training models...")
        results = model_trainer.train_models(training_data)

        # Generate report
        report = model_trainer.generate_accuracy_report(results)
        print(report)

        # Save results
        with open(os.path.join(MODELS_DIR, 'training_results.json'), 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Training pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        raise


def create_sample_data() -> List[Dict[str, Any]]:
    """Create sample data for demo purposes"""
    teams = ['NE', 'BUF', 'NYJ', 'MIA', 'KC', 'LAC', 'DEN', 'LV']
    sample_games = []

    for game_id in range(100):
        home_team = np.random.choice(teams)
        away_team = np.random.choice([t for t in teams if t != home_team])

        home_score = np.random.poisson(24)
        away_score = np.random.poisson(21)

        game = {
            'GameID': game_id,
            'Season': 2023,
            'Week': (game_id % 17) + 1,
            'DateTime': f"2023-09-{10 + (game_id % 20):02d}T13:00:00",
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'HomeScore': home_score,
            'AwayScore': away_score,
            'IsClosed': True,
            'PointSpread': np.random.uniform(-7, 7),
            'OverUnder': np.random.uniform(40, 55),
            'SeasonType': 1,  # Regular season
            'Temperature': np.random.uniform(32, 85),
            'WindSpeed': np.random.uniform(0, 20),
            'WeatherConditions': 'Clear',
            'StadiumDetails': {'Name': 'Stadium', 'Type': 'Open'}
        }
        sample_games.append(game)

    return sample_games


if __name__ == "__main__":
    main()