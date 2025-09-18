"""
Advanced ML Models for NFL Predictions
Implements XGBoost, RandomForest, Neural Network, and Ensemble models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import pickle
import os
import warnings
from sklearn.ensemble import RandomForestRegressor, VotingRegressor, VotingClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, mean_squared_error, log_loss
import xgboost as xgb
import logging

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class NFLGameWinnerModel:
    """XGBoost model for predicting game winners and spread coverage"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False

    def _get_model_params(self) -> Dict[str, Any]:
        """Get optimized XGBoost parameters for game winner prediction"""
        return {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'early_stopping_rounds': 20,
            'verbose': False
        }

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for training/prediction"""
        # Key features for game winner prediction
        feature_cols = [
            'home_team_rating', 'away_team_rating',
            'home_offensive_rating', 'away_offensive_rating',
            'home_defensive_rating', 'away_defensive_rating',
            'home_recent_form_3', 'away_recent_form_3',
            'home_recent_form_5', 'away_recent_form_5',
            'home_rest_days', 'away_rest_days',
            'weather_impact_score',
            'home_red_zone_efficiency', 'away_red_zone_efficiency',
            'home_third_down_rate', 'away_third_down_rate',
            'home_turnover_differential', 'away_turnover_differential',
            'home_epa_per_play', 'away_epa_per_play',
            'home_success_rate', 'away_success_rate',
            'home_dvoa', 'away_dvoa',
            'travel_distance',
            'is_division_game', 'is_conference_game',
            'home_injuries_impact', 'away_injuries_impact'
        ]

        # Store feature columns for later use
        if self.feature_columns is None:
            self.feature_columns = [col for col in feature_cols if col in df.columns]

        # Fill missing values
        features_df = df[self.feature_columns].fillna(0)

        return features_df.values

    def train(self, X: pd.DataFrame, y: np.ndarray, validation_split: float = 0.2) -> Dict[str, float]:
        """Train the XGBoost model"""
        logger.info("Training XGBoost game winner model...")

        # Prepare features
        X_prepared = self.prepare_features(X)

        # Scale features
        X_scaled = self.scaler.fit_transform(X_prepared)

        # Split for validation
        split_idx = int(len(X_scaled) * (1 - validation_split))
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Initialize and train model
        self.model = xgb.XGBClassifier(**self._get_model_params())

        eval_set = [(X_train, y_train), (X_val, y_val)]
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )

        self.is_trained = True

        # Calculate metrics
        train_pred = self.model.predict_proba(X_train)[:, 1]
        val_pred = self.model.predict_proba(X_val)[:, 1]

        train_acc = accuracy_score(y_train, (train_pred > 0.5).astype(int))
        val_acc = accuracy_score(y_val, (val_pred > 0.5).astype(int))

        train_logloss = log_loss(y_train, train_pred)
        val_logloss = log_loss(y_val, val_pred)

        metrics = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'train_logloss': train_logloss,
            'val_logloss': val_logloss
        }

        logger.info(f"Game Winner Model - Val Accuracy: {val_acc:.4f}, Val LogLoss: {val_logloss:.4f}")
        return metrics

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.transform(X_prepared)

        return self.model.predict_proba(X_scaled)[:, 1]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict winners"""
        probabilities = self.predict_proba(X)
        return (probabilities > 0.5).astype(int)

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance_df


class NFLTotalPointsModel:
    """RandomForest model for predicting total points"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False

    def _get_model_params(self) -> Dict[str, Any]:
        """Get optimized RandomForest parameters"""
        return {
            'n_estimators': 300,
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1
        }

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for total points prediction"""
        feature_cols = [
            'home_offensive_rating', 'away_offensive_rating',
            'home_defensive_rating', 'away_defensive_rating',
            'home_pace_of_play', 'away_pace_of_play',
            'home_avg_points_scored', 'away_avg_points_scored',
            'home_avg_points_allowed', 'away_avg_points_allowed',
            'home_red_zone_efficiency', 'away_red_zone_efficiency',
            'weather_impact_score',
            'dome_game', 'is_primetime',
            'home_epa_per_play', 'away_epa_per_play',
            'home_explosive_play_rate', 'away_explosive_play_rate',
            'home_time_of_possession', 'away_time_of_possession',
            'season_week',
            'home_injuries_offensive', 'away_injuries_offensive',
            'total_line_movement'
        ]

        if self.feature_columns is None:
            self.feature_columns = [col for col in feature_cols if col in df.columns]

        features_df = df[self.feature_columns].fillna(0)
        return features_df.values

    def train(self, X: pd.DataFrame, y: np.ndarray, validation_split: float = 0.2) -> Dict[str, float]:
        """Train the RandomForest model"""
        logger.info("Training RandomForest total points model...")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.fit_transform(X_prepared)

        split_idx = int(len(X_scaled) * (1 - validation_split))
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        self.model = RandomForestRegressor(**self._get_model_params())
        self.model.fit(X_train, y_train)

        self.is_trained = True

        # Calculate metrics
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))

        train_mae = np.mean(np.abs(y_train - train_pred))
        val_mae = np.mean(np.abs(y_val - val_pred))

        metrics = {
            'train_rmse': train_rmse,
            'val_rmse': val_rmse,
            'train_mae': train_mae,
            'val_mae': val_mae
        }

        logger.info(f"Total Points Model - Val RMSE: {val_rmse:.4f}, Val MAE: {val_mae:.4f}")
        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict total points"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.transform(X_prepared)

        return self.model.predict(X_scaled)

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance_df


class NFLPlayerPropsModel:
    """Neural Network model for player prop predictions"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False

    def _get_model_params(self) -> Dict[str, Any]:
        """Get optimized Neural Network parameters"""
        return {
            'hidden_layer_sizes': (100, 50, 25),
            'activation': 'relu',
            'solver': 'adam',
            'alpha': 0.001,
            'learning_rate': 'adaptive',
            'max_iter': 500,
            'random_state': 42,
            'early_stopping': True,
            'validation_fraction': 0.1
        }

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for player props prediction"""
        feature_cols = [
            'player_avg_yards', 'player_avg_attempts',
            'player_recent_form_3', 'player_recent_form_5',
            'opponent_defense_rank', 'opponent_yards_allowed',
            'weather_impact_score', 'is_home_game',
            'game_pace_projection', 'game_script_factor',
            'player_snap_percentage', 'player_target_share',
            'red_zone_opportunities', 'goal_line_carries',
            'injury_probability', 'rest_days',
            'divisional_matchup', 'playoff_implications',
            'player_epa_per_play', 'opponent_epa_allowed'
        ]

        if self.feature_columns is None:
            self.feature_columns = [col for col in feature_cols if col in df.columns]

        features_df = df[self.feature_columns].fillna(0)
        return features_df.values

    def train(self, X: pd.DataFrame, y: np.ndarray, validation_split: float = 0.2) -> Dict[str, float]:
        """Train the Neural Network model"""
        logger.info("Training Neural Network player props model...")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.fit_transform(X_prepared)

        split_idx = int(len(X_scaled) * (1 - validation_split))
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        self.model = MLPRegressor(**self._get_model_params())
        self.model.fit(X_train, y_train)

        self.is_trained = True

        # Calculate metrics
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))

        train_mae = np.mean(np.abs(y_train - train_pred))
        val_mae = np.mean(np.abs(y_val - val_pred))

        metrics = {
            'train_rmse': train_rmse,
            'val_rmse': val_rmse,
            'train_mae': train_mae,
            'val_mae': val_mae
        }

        logger.info(f"Player Props Model - Val RMSE: {val_rmse:.4f}, Val MAE: {val_mae:.4f}")
        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict player props"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.transform(X_prepared)

        return self.model.predict(X_scaled)


class NFLEnsembleModel:
    """Ensemble voting system combining all models"""

    def __init__(self):
        self.game_winner_model = NFLGameWinnerModel()
        self.total_points_model = NFLTotalPointsModel()
        self.player_props_model = NFLPlayerPropsModel()
        self.ensemble_weights = {
            'game_winner': 0.4,
            'total_points': 0.3,
            'player_props': 0.3
        }
        self.is_trained = False

    def train(self, data: Dict[str, Tuple[pd.DataFrame, np.ndarray]]) -> Dict[str, Dict[str, float]]:
        """Train all models in the ensemble"""
        logger.info("Training NFL Ensemble Model...")

        all_metrics = {}

        # Train game winner model
        if 'game_winner' in data:
            X_winner, y_winner = data['game_winner']
            winner_metrics = self.game_winner_model.train(X_winner, y_winner)
            all_metrics['game_winner'] = winner_metrics

        # Train total points model
        if 'total_points' in data:
            X_points, y_points = data['total_points']
            points_metrics = self.total_points_model.train(X_points, y_points)
            all_metrics['total_points'] = points_metrics

        # Train player props model
        if 'player_props' in data:
            X_props, y_props = data['player_props']
            props_metrics = self.player_props_model.train(X_props, y_props)
            all_metrics['player_props'] = props_metrics

        self.is_trained = True
        logger.info("Ensemble model training completed!")

        return all_metrics

    def predict_game_outcome(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive game prediction"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before prediction")

        predictions = {}

        # Game winner prediction
        winner_prob = self.game_winner_model.predict_proba(X)
        predictions['home_win_probability'] = float(winner_prob[0])
        predictions['away_win_probability'] = float(1 - winner_prob[0])
        predictions['predicted_winner'] = 'home' if winner_prob[0] > 0.5 else 'away'

        # Total points prediction
        total_points = self.total_points_model.predict(X)
        predictions['predicted_total'] = float(total_points[0])

        # Confidence based on model agreement
        confidence_factors = [
            abs(winner_prob[0] - 0.5) * 2,  # Winner confidence
            min(1.0, total_points[0] / 60.0)  # Points confidence (normalized)
        ]
        predictions['confidence'] = float(np.mean(confidence_factors))

        return predictions

    def predict_player_props(self, X: pd.DataFrame) -> np.ndarray:
        """Predict player props"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before prediction")

        return self.player_props_model.predict(X)

    def get_model_insights(self) -> Dict[str, pd.DataFrame]:
        """Get feature importance from all models"""
        insights = {}

        if self.game_winner_model.is_trained:
            insights['game_winner_features'] = self.game_winner_model.get_feature_importance()

        if self.total_points_model.is_trained:
            insights['total_points_features'] = self.total_points_model.get_feature_importance()

        return insights

    def save_models(self, model_dir: str) -> None:
        """Save all trained models"""
        os.makedirs(model_dir, exist_ok=True)

        # Save individual models
        with open(os.path.join(model_dir, 'game_winner_model.pkl'), 'wb') as f:
            pickle.dump(self.game_winner_model, f)

        with open(os.path.join(model_dir, 'total_points_model.pkl'), 'wb') as f:
            pickle.dump(self.total_points_model, f)

        with open(os.path.join(model_dir, 'player_props_model.pkl'), 'wb') as f:
            pickle.dump(self.player_props_model, f)

        # Save ensemble metadata
        ensemble_metadata = {
            'weights': self.ensemble_weights,
            'is_trained': self.is_trained
        }
        with open(os.path.join(model_dir, 'ensemble_metadata.pkl'), 'wb') as f:
            pickle.dump(ensemble_metadata, f)

        logger.info(f"Models saved to {model_dir}")

    def load_models(self, model_dir: str) -> None:
        """Load trained models"""
        try:
            # Load individual models
            with open(os.path.join(model_dir, 'game_winner_model.pkl'), 'rb') as f:
                self.game_winner_model = pickle.load(f)

            with open(os.path.join(model_dir, 'total_points_model.pkl'), 'rb') as f:
                self.total_points_model = pickle.load(f)

            with open(os.path.join(model_dir, 'player_props_model.pkl'), 'rb') as f:
                self.player_props_model = pickle.load(f)

            # Load ensemble metadata
            with open(os.path.join(model_dir, 'ensemble_metadata.pkl'), 'rb') as f:
                metadata = pickle.load(f)
                self.ensemble_weights = metadata['weights']
                self.is_trained = metadata['is_trained']

            logger.info(f"Models loaded from {model_dir}")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise


def hyperparameter_tuning(X: pd.DataFrame, y: np.ndarray, model_type: str) -> Dict[str, Any]:
    """Perform hyperparameter tuning for different model types"""

    if model_type == 'xgboost_classifier':
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [4, 6, 8],
            'learning_rate': [0.05, 0.1, 0.2],
            'subsample': [0.8, 0.9, 1.0]
        }
        model = xgb.XGBClassifier(random_state=42, objective='binary:logistic')
        scoring = 'accuracy'

    elif model_type == 'random_forest_regressor':
        param_grid = {
            'n_estimators': [200, 300, 400],
            'max_depth': [10, 15, 20],
            'min_samples_split': [2, 5, 10],
            'max_features': ['sqrt', 'log2']
        }
        model = RandomForestRegressor(random_state=42)
        scoring = 'neg_mean_squared_error'

    elif model_type == 'neural_network':
        param_grid = {
            'hidden_layer_sizes': [(50,), (100,), (100, 50), (100, 50, 25)],
            'activation': ['relu', 'tanh'],
            'alpha': [0.0001, 0.001, 0.01],
            'learning_rate': ['constant', 'adaptive']
        }
        model = MLPRegressor(max_iter=500, random_state=42)
        scoring = 'neg_mean_squared_error'

    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Perform grid search
    grid_search = GridSearchCV(
        model, param_grid, cv=5, scoring=scoring, n_jobs=-1, verbose=1
    )

    # Prepare features if needed (assuming this function gets called appropriately)
    if isinstance(X, pd.DataFrame):
        X = X.fillna(0).values

    grid_search.fit(X, y)

    return {
        'best_params': grid_search.best_params_,
        'best_score': grid_search.best_score_,
        'cv_results': grid_search.cv_results_
    }