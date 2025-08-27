"""
Advanced ML Model Trainer
Trains sophisticated models using enhanced features for improved prediction accuracy
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, 
    RandomForestRegressor, GradientBoostingRegressor
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

from .enhanced_features import EnhancedFeatureEngine
from .data_pipeline import DataPipeline

logger = logging.getLogger(__name__)

class AdvancedModelTrainer:
    """Advanced ML model trainer with ensemble methods and feature engineering"""
    
    def __init__(self):
        self.feature_engine = EnhancedFeatureEngine()
        self.data_pipeline = DataPipeline()
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        
        # Model configurations
        self.model_configs = {
            'game_winner': {
                'type': 'classification',
                'models': {
                    'random_forest': RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42),
                    'gradient_boost': GradientBoostingClassifier(n_estimators=150, max_depth=8, random_state=42),
                    'neural_network': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42),
                    'svm': SVC(kernel='rbf', probability=True, random_state=42)
                }
            },
            'ats_prediction': {
                'type': 'classification',
                'models': {
                    'random_forest': RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42),
                    'gradient_boost': GradientBoostingClassifier(n_estimators=150, max_depth=6, random_state=42),
                    'logistic': LogisticRegression(max_iter=1000, random_state=42)
                }
            },
            'total_prediction': {
                'type': 'regression',
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42),
                    'gradient_boost': GradientBoostingRegressor(n_estimators=150, max_depth=8, random_state=42),
                    'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
                }
            },
            'score_prediction': {
                'type': 'regression',
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=250, max_depth=20, random_state=42),
                    'gradient_boost': GradientBoostingRegressor(n_estimators=200, max_depth=10, random_state=42),
                    'ridge': Ridge(alpha=1.0, random_state=42)
                }
            }
        }
    
    def prepare_training_data(self, seasons: List[int], weeks: Optional[List[int]] = None) -> Dict:
        """Prepare comprehensive training data with enhanced features"""
        try:
            logger.info(f"Preparing training data for seasons: {seasons}")
            
            # Collect raw game data
            raw_data = self.data_pipeline.collect_historical_data(seasons, weeks)
            
            # Generate enhanced features for each game
            enhanced_data = []
            for game in raw_data:
                try:
                    features = self._generate_game_features(game)
                    if features:
                        enhanced_data.append(features)
                except Exception as e:
                    logger.warning(f"Failed to generate features for game {game.get('game_id', 'unknown')}: {e}")
                    continue
            
            if not enhanced_data:
                raise ValueError("No valid training data generated")
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(enhanced_data)
            
            # Prepare target variables
            targets = self._prepare_target_variables(df)
            
            # Prepare feature matrices
            feature_matrices = self._prepare_feature_matrices(df)
            
            logger.info(f"Training data prepared: {len(df)} games, {len(feature_matrices['base_features'].columns)} features")
            
            return {
                'dataframe': df,
                'targets': targets,
                'features': feature_matrices,
                'game_count': len(df)
            }
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            raise    

    def _generate_game_features(self, game: Dict) -> Optional[Dict]:
        """Generate comprehensive features for a single game"""
        try:
            features = {
                'game_id': game.get('game_id'),
                'season': game.get('season'),
                'week': game.get('week'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team')
            }
            
            # Basic game information
            features.update({
                'home_score': game.get('home_score', 0),
                'away_score': game.get('away_score', 0),
                'total_score': game.get('home_score', 0) + game.get('away_score', 0),
                'point_spread': game.get('point_spread', 0),
                'total_line': game.get('total_line', 0)
            })
            
            # Team statistics (would be fetched from database)
            home_stats = self._get_team_stats(game['home_team'], game['season'], game['week'])
            away_stats = self._get_team_stats(game['away_team'], game['season'], game['week'])
            
            # Enhanced team metrics
            home_metrics = self.feature_engine.calculate_advanced_team_metrics(home_stats, away_stats)
            away_metrics = self.feature_engine.calculate_advanced_team_metrics(away_stats, home_stats)
            
            # Add prefixed team metrics
            for key, value in home_metrics.items():
                features[f'home_{key}'] = value
            for key, value in away_metrics.items():
                features[f'away_{key}'] = value
            
            # Momentum indicators
            home_recent = self._get_recent_games(game['home_team'], game['season'], game['week'])
            away_recent = self._get_recent_games(game['away_team'], game['season'], game['week'])
            
            home_momentum = self.feature_engine.calculate_momentum_indicators(home_recent, home_stats)
            away_momentum = self.feature_engine.calculate_momentum_indicators(away_recent, away_stats)
            
            for key, value in home_momentum.items():
                features[f'home_{key}'] = value
            for key, value in away_momentum.items():
                features[f'away_{key}'] = value
            
            # Environmental factors
            env_factors = self.feature_engine.calculate_environmental_factors(game, home_stats, away_stats)
            features.update(env_factors)
            
            # Matchup-specific features
            matchup_features = self._calculate_matchup_features(home_stats, away_stats, game)
            features.update(matchup_features)
            
            # Historical head-to-head
            h2h_features = self._calculate_h2h_features(game['home_team'], game['away_team'], game['season'])
            features.update(h2h_features)
            
            return features
            
        except Exception as e:
            logger.error(f"Error generating game features: {e}")
            return None
    
    def _calculate_matchup_features(self, home_stats: Dict, away_stats: Dict, game: Dict) -> Dict:
        """Calculate matchup-specific features"""
        features = {}
        
        try:
            # Offensive vs Defensive matchups
            features['home_off_vs_away_def'] = (
                home_stats.get('offensive_efficiency', 0) - away_stats.get('defensive_efficiency', 0)
            )
            features['away_off_vs_home_def'] = (
                away_stats.get('offensive_efficiency', 0) - home_stats.get('defensive_efficiency', 0)
            )
            
            # Pace matchup
            home_pace = home_stats.get('plays_per_game', 65)
            away_pace = away_stats.get('plays_per_game', 65)
            features['pace_differential'] = abs(home_pace - away_pace)
            features['combined_pace'] = (home_pace + away_pace) / 2
            
            # Turnover battle
            features['turnover_differential_matchup'] = (
                home_stats.get('turnover_differential', 0) - away_stats.get('turnover_differential', 0)
            )
            
            # Red zone matchup
            features['red_zone_matchup'] = (
                home_stats.get('red_zone_efficiency', 0.5) - away_stats.get('red_zone_defense', 0.5)
            )
            
            # Third down matchup
            features['third_down_matchup'] = (
                home_stats.get('third_down_rate', 0.4) - away_stats.get('third_down_defense', 0.4)
            )
            
            # Strength vs weakness analysis
            features['home_strength_score'] = self._calculate_team_strength(home_stats)
            features['away_strength_score'] = self._calculate_team_strength(away_stats)
            features['strength_differential'] = features['home_strength_score'] - features['away_strength_score']
            
        except Exception as e:
            logger.error(f"Error calculating matchup features: {e}")
        
        return features
    
    def _calculate_team_strength(self, stats: Dict) -> float:
        """Calculate overall team strength score"""
        try:
            # Weighted combination of key metrics
            offensive_score = (
                stats.get('offensive_efficiency', 0) * 0.3 +
                stats.get('red_zone_efficiency', 0) * 0.2 +
                stats.get('third_down_rate', 0) * 0.2 +
                stats.get('turnover_differential', 0) * 0.1 +
                stats.get('yards_per_play', 0) * 0.2
            )
            
            defensive_score = (
                (1 - stats.get('defensive_efficiency', 0)) * 0.3 +
                stats.get('sack_rate', 0) * 0.2 +
                (1 - stats.get('third_down_defense', 0)) * 0.2 +
                stats.get('takeaway_rate', 0) * 0.3
            )
            
            return (offensive_score + defensive_score) / 2
            
        except Exception:
            return 0.5
    
    def _calculate_h2h_features(self, home_team: str, away_team: str, season: int) -> Dict:
        """Calculate head-to-head historical features"""
        features = {}
        
        try:
            # Get historical matchups (last 5 years)
            h2h_games = self._get_h2h_history(home_team, away_team, season, years=5)
            
            if h2h_games:
                # Overall record
                home_wins = sum(1 for g in h2h_games if g.get('winner') == home_team)
                features['h2h_home_win_rate'] = home_wins / len(h2h_games)
                
                # ATS record
                home_ats_wins = sum(1 for g in h2h_games if g.get('ats_winner') == home_team)
                features['h2h_home_ats_rate'] = home_ats_wins / len(h2h_games)
                
                # Total trends
                overs = sum(1 for g in h2h_games if g.get('total_result') == 'over')
                features['h2h_over_rate'] = overs / len(h2h_games)
                
                # Average scores
                home_scores = [g.get('home_score', 0) for g in h2h_games if g.get('home_team') == home_team]
                away_scores = [g.get('away_score', 0) for g in h2h_games if g.get('away_team') == away_team]
                
                features['h2h_avg_home_score'] = sum(home_scores) / len(home_scores) if home_scores else 20
                features['h2h_avg_away_score'] = sum(away_scores) / len(away_scores) if away_scores else 20
                
                # Recent trend (last 3 games)
                recent_h2h = h2h_games[-3:] if len(h2h_games) >= 3 else h2h_games
                recent_home_wins = sum(1 for g in recent_h2h if g.get('winner') == home_team)
                features['h2h_recent_home_win_rate'] = recent_home_wins / len(recent_h2h)
            else:
                # No historical data
                features.update({
                    'h2h_home_win_rate': 0.5,
                    'h2h_home_ats_rate': 0.5,
                    'h2h_over_rate': 0.5,
                    'h2h_avg_home_score': 20,
                    'h2h_avg_away_score': 20,
                    'h2h_recent_home_win_rate': 0.5
                })
            
        except Exception as e:
            logger.error(f"Error calculating H2H features: {e}")
        
        return features
    
    def _prepare_target_variables(self, df: pd.DataFrame) -> Dict:
        """Prepare target variables for training"""
        targets = {}
        
        # Game winner (1 for home win, 0 for away win)
        targets['game_winner'] = (df['home_score'] > df['away_score']).astype(int)
        
        # ATS prediction (1 for home cover, 0 for away cover)
        home_ats_margin = df['home_score'] - df['away_score'] + df['point_spread']
        targets['ats_prediction'] = (home_ats_margin > 0).astype(int)
        
        # Total prediction (actual total score)
        targets['total_prediction'] = df['total_score']
        
        # Score predictions
        targets['home_score_prediction'] = df['home_score']
        targets['away_score_prediction'] = df['away_score']
        
        return targets
    
    def _prepare_feature_matrices(self, df: pd.DataFrame) -> Dict:
        """Prepare feature matrices for training"""
        # Select numeric features only
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        # Exclude target variables and identifiers
        exclude_columns = [
            'game_id', 'home_score', 'away_score', 'total_score',
            'season', 'week'  # Keep these as potential features but handle separately
        ]
        
        feature_columns = [col for col in numeric_columns if col not in exclude_columns]
        
        # Base feature matrix
        base_features = df[feature_columns].fillna(0)
        
        return {
            'base_features': base_features,
            'feature_names': feature_columns
        }
    
    # Helper methods for data retrieval (would connect to actual database)
    def _get_team_stats(self, team: str, season: int, week: int) -> Dict:
        """Get team statistics up to a specific week"""
        # Mock implementation - would query actual database
        return {
            'team_name': team,
            'offensive_efficiency': 5.5,
            'defensive_efficiency': 5.2,
            'plays_per_game': 65,
            'total_yards': 350,
            'plays': 65,
            'pass_attempts': 35,
            'completions': 22,
            'pass_yards': 250,
            'pass_tds': 1.5,
            'interceptions': 0.8,
            'rush_attempts': 25,
            'rush_yards': 120,
            'successful_rushes': 15,
            'rushes_10plus': 3,
            'sacks': 2.5,
            'takeaways': 1.2,
            'turnovers': 1.0,
            'penalty_yards': 65,
            'time_of_possession': 30.0,
            'red_zone_attempts': 3,
            'red_zone_tds': 2,
            'third_down_attempts': 12,
            'third_down_conversions': 5,
            'fourth_down_attempts': 1,
            'fourth_down_conversions': 0.5,
            'goal_to_go_attempts': 2,
            'goal_to_go_tds': 1.5,
            'two_minute_drives_success': 0.6,
            'home_win_rate': 0.6,
            'air_yards': 180,
            'points': 24
        }
    
    def _get_recent_games(self, team: str, season: int, week: int, num_games: int = 5) -> List[Dict]:
        """Get recent games for a team"""
        # Mock implementation - would query actual database
        return [
            {
                'result': 'W',
                'points_scored': 28,
                'points_allowed': 21,
                'point_margin': 7,
                'ats_result': 'cover',
                'total_result': 'over',
                'location': 'home',
                'expected_points': 24
            },
            {
                'result': 'L',
                'points_scored': 17,
                'points_allowed': 24,
                'point_margin': -7,
                'ats_result': 'no_cover',
                'total_result': 'under',
                'location': 'away',
                'expected_points': 21
            }
        ]
    
    def _get_h2h_history(self, team1: str, team2: str, season: int, years: int = 5) -> List[Dict]:
        """Get head-to-head history between two teams"""
        # Mock implementation - would query actual database
        return [
            {
                'home_team': team1,
                'away_team': team2,
                'home_score': 24,
                'away_score': 17,
                'winner': team1,
                'ats_winner': team1,
                'total_result': 'over'
            }
        ]

# Example usage and testing
if __name__ == "__main__":
    # Initialize trainer
    trainer = AdvancedModelTrainer()
    
    # Prepare training data (mock example)
    try:
        training_data = trainer.prepare_training_data([2022, 2023, 2024])
        print(f"Training data prepared: {training_data['game_count']} games")
        
        # Train models
        results = trainer.train_models(training_data)
        print("Training completed successfully!")
        
        for prediction_type, result in results.items():
            print(f"{prediction_type}: Best model = {result['best_model']}")
            print(f"  Metrics: {result['best_metrics']}")
        
    except Exception as e:
        print(f"Training failed: {e}")