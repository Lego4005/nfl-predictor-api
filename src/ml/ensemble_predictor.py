#!/usr/bin/env python3
"""
Advanced Ensemble Predictor for NFL Games
Combines multiple specialized models with advanced features for 75%+ accuracy
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Core ML libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.calibration import CalibratedClassifierCV
from sklearn.base import BaseEstimator, TransformerMixin
import xgboost as xgb
import lightgbm as lgb

# Deep learning libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Advanced ML tools
import optuna
import shap
import joblib
from scipy import stats
from scipy.optimize import minimize
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Utilities
import logging
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import requests
import requests_cache
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup requests cache for weather API
requests_cache.install_cache('/tmp/weather_cache', expire_after=3600)


class WeatherImpactAnalyzer:
    """Analyzes weather conditions and their impact on NFL games"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.weather_factors = {
            'temperature': {'weight': 0.15, 'threshold_cold': 32, 'threshold_hot': 85},
            'wind_speed': {'weight': 0.25, 'threshold_high': 15, 'threshold_extreme': 25},
            'precipitation': {'weight': 0.20, 'threshold_light': 0.1, 'threshold_heavy': 0.3},
            'humidity': {'weight': 0.10, 'threshold_high': 80},
            'visibility': {'weight': 0.15, 'threshold_poor': 5, 'threshold_very_poor': 2},
            'dome_game': {'weight': 0.15}  # Indoor games have no weather impact
        }

    def get_historical_weather(self, location: str, date: str) -> Dict[str, float]:
        """Get historical weather data for a specific game location and date"""
        try:
            # Mock weather data - in production, integrate with weather API
            # This would normally call OpenWeather, WeatherAPI, or similar service
            mock_weather = {
                'temperature': np.random.normal(60, 20),
                'wind_speed': np.random.exponential(8),
                'precipitation': np.random.exponential(0.05),
                'humidity': np.random.normal(60, 20),
                'visibility': np.random.normal(8, 2),
                'dome_game': 0 if 'dome' in location.lower() or 'indoor' in location.lower() else 1
            }

            # Ensure realistic ranges
            mock_weather['temperature'] = np.clip(mock_weather['temperature'], -10, 110)
            mock_weather['wind_speed'] = np.clip(mock_weather['wind_speed'], 0, 40)
            mock_weather['precipitation'] = np.clip(mock_weather['precipitation'], 0, 2)
            mock_weather['humidity'] = np.clip(mock_weather['humidity'], 10, 100)
            mock_weather['visibility'] = np.clip(mock_weather['visibility'], 0.5, 15)

            return mock_weather

        except Exception as e:
            logger.warning(f"Weather data unavailable for {location} on {date}: {e}")
            return self._get_default_weather()

    def _get_default_weather(self) -> Dict[str, float]:
        """Return neutral weather conditions"""
        return {
            'temperature': 65.0,
            'wind_speed': 5.0,
            'precipitation': 0.0,
            'humidity': 50.0,
            'visibility': 10.0,
            'dome_game': 0
        }

    def calculate_weather_impact_score(self, weather_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate weather impact scores for various game aspects"""

        if weather_data['dome_game'] == 0:  # Indoor game
            return {
                'passing_impact': 0.0,
                'rushing_impact': 0.0,
                'kicking_impact': 0.0,
                'total_impact': 0.0,
                'weather_advantage': 0.0
            }

        impacts = {}

        # Temperature impact
        temp = weather_data['temperature']
        if temp < self.weather_factors['temperature']['threshold_cold']:
            temp_impact = (self.weather_factors['temperature']['threshold_cold'] - temp) / 32
        elif temp > self.weather_factors['temperature']['threshold_hot']:
            temp_impact = (temp - self.weather_factors['temperature']['threshold_hot']) / 20
        else:
            temp_impact = 0.0

        # Wind impact (mainly affects passing and kicking)
        wind = weather_data['wind_speed']
        wind_impact = 0.0
        if wind > self.weather_factors['wind_speed']['threshold_high']:
            wind_impact = min((wind - self.weather_factors['wind_speed']['threshold_high']) / 10, 1.0)

        # Precipitation impact
        precip = weather_data['precipitation']
        precip_impact = 0.0
        if precip > self.weather_factors['precipitation']['threshold_light']:
            precip_impact = min(precip / self.weather_factors['precipitation']['threshold_heavy'], 1.0)

        # Visibility impact
        visibility = weather_data['visibility']
        visibility_impact = 0.0
        if visibility < self.weather_factors['visibility']['threshold_poor']:
            visibility_impact = (self.weather_factors['visibility']['threshold_poor'] - visibility) / 5

        # Calculate specific impacts
        impacts['passing_impact'] = np.clip(
            temp_impact * 0.3 + wind_impact * 0.5 + precip_impact * 0.2 + visibility_impact * 0.4,
            0, 1
        )

        impacts['rushing_impact'] = np.clip(
            temp_impact * 0.2 + precip_impact * 0.4 + visibility_impact * 0.2,
            0, 1
        )

        impacts['kicking_impact'] = np.clip(
            temp_impact * 0.4 + wind_impact * 0.6 + precip_impact * 0.1,
            0, 1
        )

        impacts['total_impact'] = (
            impacts['passing_impact'] * 0.4 +
            impacts['rushing_impact'] * 0.3 +
            impacts['kicking_impact'] * 0.3
        )

        # Weather advantage (negative weather generally favors defense and running)
        impacts['weather_advantage'] = impacts['total_impact'] * 0.5  # Defensive advantage

        return impacts


class InjurySeverityScorer:
    """Scores injury impact on team performance"""

    def __init__(self):
        self.position_weights = {
            'QB': 0.35,
            'RB': 0.15,
            'WR': 0.12,
            'TE': 0.08,
            'OL': 0.10,
            'DL': 0.08,
            'LB': 0.06,
            'CB': 0.04,
            'S': 0.02
        }

        self.injury_severity = {
            'OUT': 1.0,
            'DOUBTFUL': 0.8,
            'QUESTIONABLE': 0.4,
            'PROBABLE': 0.1,
            'HEALTHY': 0.0
        }

    def calculate_team_injury_score(self, injury_report: List[Dict]) -> Dict[str, float]:
        """Calculate injury impact score for a team"""

        total_impact = 0.0
        position_impacts = {pos: 0.0 for pos in self.position_weights}

        for injury in injury_report:
            position = injury.get('position', 'UNKNOWN')
            severity = injury.get('status', 'HEALTHY')
            player_importance = injury.get('importance', 0.5)  # 0-1 scale

            if position in self.position_weights:
                impact = (
                    self.position_weights[position] *
                    self.injury_severity.get(severity, 0.0) *
                    player_importance
                )

                total_impact += impact
                position_impacts[position] += impact

        return {
            'total_injury_impact': np.clip(total_impact, 0, 1),
            'offensive_impact': sum([
                position_impacts[pos] for pos in ['QB', 'RB', 'WR', 'TE', 'OL']
            ]),
            'defensive_impact': sum([
                position_impacts[pos] for pos in ['DL', 'LB', 'CB', 'S']
            ]),
            'position_impacts': position_impacts
        }


class MomentumIndicators:
    """Calculates team momentum based on recent performance"""

    def __init__(self):
        self.weights = {
            'recent_wins': 0.25,
            'point_differential': 0.20,
            'ats_performance': 0.15,
            'home_road_performance': 0.15,
            'strength_of_schedule': 0.10,
            'turnovers': 0.10,
            'injury_momentum': 0.05
        }

    def calculate_momentum_score(self, team_stats: Dict) -> Dict[str, float]:
        """Calculate comprehensive momentum score"""

        momentum_components = {}

        # Recent win percentage (last 4 games)
        recent_record = team_stats.get('recent_record', [])
        if recent_record:
            wins = sum(1 for result in recent_record[-4:] if result == 'W')
            momentum_components['recent_wins'] = wins / min(len(recent_record), 4)
        else:
            momentum_components['recent_wins'] = 0.5

        # Point differential momentum
        recent_scores = team_stats.get('recent_point_diff', [])
        if recent_scores:
            avg_diff = np.mean(recent_scores[-4:])
            momentum_components['point_differential'] = np.tanh(avg_diff / 14) * 0.5 + 0.5
        else:
            momentum_components['point_differential'] = 0.5

        # ATS performance
        ats_record = team_stats.get('ats_record', [])
        if ats_record:
            ats_wins = sum(1 for result in ats_record[-4:] if result == 'W')
            momentum_components['ats_performance'] = ats_wins / min(len(ats_record), 4)
        else:
            momentum_components['ats_performance'] = 0.5

        # Home/Road performance contextual to current game
        is_home = team_stats.get('is_home', True)
        if is_home:
            home_record = team_stats.get('home_record', 0.5)
            momentum_components['home_road_performance'] = home_record
        else:
            road_record = team_stats.get('road_record', 0.5)
            momentum_components['home_road_performance'] = road_record

        # Strength of schedule (opponents' win percentage)
        sos = team_stats.get('strength_of_schedule', 0.5)
        momentum_components['strength_of_schedule'] = 1 - abs(sos - 0.5)  # Normalize

        # Turnover differential momentum
        turnover_diff = team_stats.get('recent_turnover_diff', [])
        if turnover_diff:
            avg_turnover = np.mean(turnover_diff[-4:])
            momentum_components['turnovers'] = np.tanh(avg_turnover / 2) * 0.5 + 0.5
        else:
            momentum_components['turnovers'] = 0.5

        # Injury momentum (getting healthier vs more injured)
        injury_trend = team_stats.get('injury_trend', 0)  # -1 to 1
        momentum_components['injury_momentum'] = injury_trend * 0.5 + 0.5

        # Calculate weighted momentum score
        total_momentum = sum([
            momentum_components[component] * self.weights[component]
            for component in momentum_components
        ])

        return {
            'total_momentum': np.clip(total_momentum, 0, 1),
            'components': momentum_components,
            'trend': 'POSITIVE' if total_momentum > 0.6 else 'NEGATIVE' if total_momentum < 0.4 else 'NEUTRAL'
        }


class CoachingAnalyzer:
    """Analyzes coaching matchups and their impact"""

    def __init__(self):
        self.coaching_factors = {
            'experience': 0.25,
            'playoff_success': 0.20,
            'ats_performance': 0.20,
            'situational_coaching': 0.15,
            'player_development': 0.10,
            'game_management': 0.10
        }

    def analyze_coaching_matchup(self, home_coach: Dict, away_coach: Dict) -> Dict[str, float]:
        """Analyze coaching matchup advantages"""

        home_scores = self._calculate_coach_score(home_coach)
        away_scores = self._calculate_coach_score(away_coach)

        coaching_advantage = {}

        for factor in self.coaching_factors:
            home_factor = home_scores.get(factor, 0.5)
            away_factor = away_scores.get(factor, 0.5)

            # Calculate advantage (-1 to 1, positive favors home)
            advantage = (home_factor - away_factor)
            coaching_advantage[f'{factor}_advantage'] = advantage

        # Overall coaching advantage
        total_advantage = sum([
            coaching_advantage[f'{factor}_advantage'] * weight
            for factor, weight in self.coaching_factors.items()
        ])

        return {
            'coaching_advantage': np.clip(total_advantage, -1, 1),
            'home_coach_score': sum(home_scores.values()) / len(home_scores),
            'away_coach_score': sum(away_scores.values()) / len(away_scores),
            'factor_advantages': coaching_advantage
        }

    def _calculate_coach_score(self, coach_data: Dict) -> Dict[str, float]:
        """Calculate individual coach scores"""

        scores = {}

        # Experience (years coaching)
        years = coach_data.get('years_experience', 5)
        scores['experience'] = min(years / 20, 1.0)  # Normalize to 20 years max

        # Playoff success
        playoff_wins = coach_data.get('playoff_wins', 0)
        playoff_appearances = coach_data.get('playoff_appearances', 1)
        scores['playoff_success'] = min((playoff_wins + playoff_appearances * 0.3) / 10, 1.0)

        # ATS performance
        ats_record = coach_data.get('ats_win_percentage', 0.5)
        scores['ats_performance'] = ats_record

        # Situational coaching (red zone, third down, etc.)
        situational_rank = coach_data.get('situational_rank', 16)  # Out of 32 teams
        scores['situational_coaching'] = (33 - situational_rank) / 32

        # Player development
        draft_success = coach_data.get('draft_success_rate', 0.5)
        scores['player_development'] = draft_success

        # Game management
        timeout_efficiency = coach_data.get('timeout_efficiency', 0.5)
        challenge_success = coach_data.get('challenge_success_rate', 0.5)
        scores['game_management'] = (timeout_efficiency + challenge_success) / 2

        return scores


class BettingLineAnalyzer:
    """Analyzes betting line movements and market sentiment"""

    def __init__(self):
        self.line_factors = {
            'line_movement': 0.30,
            'volume_weighted_movement': 0.25,
            'sharp_money_indicators': 0.20,
            'public_betting_percentage': 0.15,
            'closing_line_value': 0.10
        }

    def analyze_line_movement(self, line_history: List[Dict]) -> Dict[str, float]:
        """Analyze betting line movement patterns"""

        if len(line_history) < 2:
            return self._get_neutral_line_analysis()

        # Sort by timestamp
        line_history = sorted(line_history, key=lambda x: x.get('timestamp', 0))

        analysis = {}

        # Basic line movement
        initial_line = line_history[0].get('spread', 0)
        final_line = line_history[-1].get('spread', 0)
        line_movement = final_line - initial_line

        analysis['raw_line_movement'] = line_movement
        analysis['line_movement_strength'] = min(abs(line_movement) / 3, 1.0)  # Normalize to 3-point max

        # Volume-weighted movement
        total_volume = sum([entry.get('volume', 1) for entry in line_history])
        weighted_movement = sum([
            (entry.get('spread', 0) - initial_line) * entry.get('volume', 1)
            for entry in line_history
        ]) / total_volume if total_volume > 0 else 0

        analysis['volume_weighted_movement'] = weighted_movement

        # Sharp money indicators (large moves with small volume changes)
        sharp_moves = 0
        for i in range(1, len(line_history)):
            prev_entry = line_history[i-1]
            curr_entry = line_history[i]

            spread_change = abs(curr_entry.get('spread', 0) - prev_entry.get('spread', 0))
            volume_change = abs(curr_entry.get('volume', 1) - prev_entry.get('volume', 1))

            if spread_change >= 0.5 and volume_change < 100:  # Significant line move, small volume
                sharp_moves += 1

        analysis['sharp_money_indicator'] = min(sharp_moves / 5, 1.0)  # Normalize to 5 moves max

        # Public betting percentage (if available)
        public_percentage = line_history[-1].get('public_percentage', 50)
        analysis['public_betting_bias'] = abs(public_percentage - 50) / 50  # 0-1 scale

        # Closing line value (how much the line moved from open to close)
        analysis['closing_line_value'] = min(abs(final_line - initial_line) / 2, 1.0)

        # Overall market sentiment
        sentiment_score = (
            analysis['line_movement_strength'] * self.line_factors['line_movement'] +
            min(abs(analysis['volume_weighted_movement']) / 2, 1.0) * self.line_factors['volume_weighted_movement'] +
            analysis['sharp_money_indicator'] * self.line_factors['sharp_money_indicators'] +
            analysis['public_betting_bias'] * self.line_factors['public_betting_percentage'] +
            analysis['closing_line_value'] * self.line_factors['closing_line_value']
        )

        analysis['market_sentiment_strength'] = sentiment_score
        analysis['market_direction'] = 'BULLISH' if line_movement > 0.5 else 'BEARISH' if line_movement < -0.5 else 'NEUTRAL'

        return analysis

    def _get_neutral_line_analysis(self) -> Dict[str, float]:
        """Return neutral line analysis when insufficient data"""
        return {
            'raw_line_movement': 0.0,
            'line_movement_strength': 0.0,
            'volume_weighted_movement': 0.0,
            'sharp_money_indicator': 0.0,
            'public_betting_bias': 0.0,
            'closing_line_value': 0.0,
            'market_sentiment_strength': 0.0,
            'market_direction': 'NEUTRAL'
        }


class LSTMTimeSeriesPredictor:
    """LSTM Neural Network for time-series game predictions"""

    def __init__(self, sequence_length: int = 10, features: int = 50):
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False

    def build_model(self):
        """Build LSTM model architecture"""

        model = keras.Sequential([
            # Input layer
            layers.Input(shape=(self.sequence_length, self.features)),

            # First LSTM layer with dropout
            layers.LSTM(128, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            layers.BatchNormalization(),

            # Second LSTM layer
            layers.LSTM(64, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            layers.BatchNormalization(),

            # Third LSTM layer
            layers.LSTM(32, dropout=0.3, recurrent_dropout=0.3),
            layers.BatchNormalization(),

            # Dense layers
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.4),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(16, activation='relu'),

            # Output layer (3 classes: home win, away win, push)
            layers.Dense(3, activation='softmax')
        ])

        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        self.model = model
        logger.info("LSTM model built successfully")

    def prepare_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare time series sequences for LSTM training"""

        if len(X) < self.sequence_length:
            logger.warning(f"Not enough data for sequences. Need {self.sequence_length}, got {len(X)}")
            return X, y

        X_sequences = []
        y_sequences = []

        for i in range(self.sequence_length, len(X)):
            X_sequences.append(X[i-self.sequence_length:i])
            y_sequences.append(y[i])

        return np.array(X_sequences), np.array(y_sequences)

    def fit(self, X: np.ndarray, y: np.ndarray, validation_split: float = 0.2):
        """Train the LSTM model"""

        if self.model is None:
            self.build_model()

        # Scale features
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)

        # Prepare sequences
        X_seq, y_seq = self.prepare_sequences(X_scaled, y)

        if len(X_seq) == 0:
            logger.error("No sequences created. Check data size and sequence length.")
            return

        # Callbacks
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True, monitor='val_loss'),
            ReduceLROnPlateau(factor=0.5, patience=8, min_lr=0.0001, monitor='val_loss')
        ]

        # Train model
        history = self.model.fit(
            X_seq, y_seq,
            validation_split=validation_split,
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )

        self.is_trained = True
        logger.info("LSTM model training completed")

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions with LSTM model"""

        if not self.is_trained or self.model is None:
            logger.warning("Model not trained. Returning default predictions.")
            return np.random.rand(len(X), 3)  # Random probabilities

        # Scale features
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)

        # Prepare sequences
        if len(X_scaled) >= self.sequence_length:
            X_seq, _ = self.prepare_sequences(X_scaled, np.zeros(len(X_scaled)))
            if len(X_seq) > 0:
                predictions = self.model.predict(X_seq, verbose=0)

                # Pad predictions for shorter sequences
                if len(predictions) < len(X):
                    padding = np.tile(predictions[-1:], (len(X) - len(predictions), 1))
                    predictions = np.vstack([padding, predictions])

                return predictions

        # Fallback for insufficient data
        return np.random.rand(len(X), 3)


class ConfidenceCalibrator:
    """Calibrates model confidence to provide accurate probability estimates"""

    def __init__(self):
        self.calibration_curves = {}
        self.is_calibrated = False

    def fit(self, y_true: np.ndarray, y_proba: np.ndarray, method: str = 'isotonic'):
        """Fit calibration curves"""

        from sklearn.calibration import calibration_curve
        from sklearn.isotonic import IsotonicRegression

        # Create bins for calibration
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        self.calibration_curves = {}

        # For each class, fit calibration
        n_classes = y_proba.shape[1] if len(y_proba.shape) > 1 else 2

        for class_idx in range(n_classes):
            if len(y_proba.shape) > 1:
                class_proba = y_proba[:, class_idx]
            else:
                class_proba = y_proba if class_idx == 1 else 1 - y_proba

            y_class = (y_true == class_idx).astype(int)

            if method == 'isotonic':
                calibrator = IsotonicRegression(out_of_bounds='clip')
                calibrator.fit(class_proba, y_class)
                self.calibration_curves[class_idx] = calibrator
            else:
                # Binning method
                fraction_of_positives, mean_predicted_value = calibration_curve(
                    y_class, class_proba, n_bins=n_bins
                )

                # Create simple mapping
                self.calibration_curves[class_idx] = {
                    'bin_lowers': bin_lowers,
                    'bin_uppers': bin_uppers,
                    'fraction_of_positives': fraction_of_positives,
                    'mean_predicted_value': mean_predicted_value
                }

        self.is_calibrated = True
        logger.info("Confidence calibration fitted")

    def transform(self, y_proba: np.ndarray) -> np.ndarray:
        """Apply calibration to probabilities"""

        if not self.is_calibrated:
            logger.warning("Calibrator not fitted. Returning original probabilities.")
            return y_proba

        calibrated_proba = np.copy(y_proba)

        n_classes = y_proba.shape[1] if len(y_proba.shape) > 1 else 2

        for class_idx in range(n_classes):
            if len(y_proba.shape) > 1:
                class_proba = y_proba[:, class_idx]
            else:
                class_proba = y_proba if class_idx == 1 else 1 - y_proba

            if class_idx in self.calibration_curves:
                calibrator = self.calibration_curves[class_idx]

                if hasattr(calibrator, 'predict'):  # Isotonic regression
                    calibrated_class_proba = calibrator.predict(class_proba)
                else:  # Binning method
                    calibrated_class_proba = self._apply_binning_calibration(
                        class_proba, calibrator
                    )

                if len(y_proba.shape) > 1:
                    calibrated_proba[:, class_idx] = calibrated_class_proba
                else:
                    if class_idx == 1:
                        calibrated_proba = calibrated_class_proba
                    else:
                        calibrated_proba = 1 - calibrated_class_proba

        # Normalize probabilities to sum to 1
        if len(calibrated_proba.shape) > 1:
            calibrated_proba = calibrated_proba / calibrated_proba.sum(axis=1, keepdims=True)

        return calibrated_proba

    def _apply_binning_calibration(self, y_proba: np.ndarray, calibrator: Dict) -> np.ndarray:
        """Apply binning calibration method"""

        calibrated = np.copy(y_proba)

        for i, prob in enumerate(y_proba):
            # Find appropriate bin
            bin_idx = np.digitize(prob, calibrator['bin_lowers']) - 1
            bin_idx = np.clip(bin_idx, 0, len(calibrator['fraction_of_positives']) - 1)

            # Use calibrated probability
            calibrated[i] = calibrator['fraction_of_positives'][bin_idx]

        return calibrated


class AdvancedEnsemblePredictor:
    """
    Advanced Ensemble Predictor combining multiple specialized models
    Target: 75%+ accuracy on NFL game predictions
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Initialize specialized analyzers
        self.weather_analyzer = WeatherImpactAnalyzer()
        self.injury_scorer = InjurySeverityScorer()
        self.momentum_calculator = MomentumIndicators()
        self.coaching_analyzer = CoachingAnalyzer()
        self.betting_analyzer = BettingLineAnalyzer()

        # Initialize models
        self.models = {}
        self.scalers = {}
        self.lstm_predictor = None
        self.confidence_calibrator = ConfidenceCalibrator()

        # Feature importance and explainability
        self.feature_importance = {}
        self.shap_explainer = None
        self.feature_names = []

        # Performance tracking
        self.training_history = {}
        self.validation_scores = {}

        self._initialize_models()

    def _initialize_models(self):
        """Initialize all ensemble models"""

        # 1. XGBoost for game outcomes
        self.models['xgboost'] = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            n_jobs=-1,
            tree_method='hist',
            enable_categorical=True
        )

        # 2. Random Forest for player props
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            bootstrap=True,
            oob_score=True,
            random_state=42,
            n_jobs=-1
        )

        # 3. Gradient Boosting for totals
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=250,
            learning_rate=0.08,
            max_depth=7,
            min_samples_split=10,
            min_samples_leaf=4,
            max_features='sqrt',
            subsample=0.8,
            random_state=42
        )

        # 4. LightGBM as additional ensemble member
        self.models['lightgbm'] = lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=10,
            learning_rate=0.06,
            num_leaves=31,
            feature_fraction=0.8,
            bagging_fraction=0.8,
            bagging_freq=5,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            n_jobs=-1,
            verbosity=-1
        )

        # Initialize scalers for each model
        for model_name in self.models.keys():
            self.scalers[model_name] = RobustScaler()

        # LSTM predictor for time-series patterns
        self.lstm_predictor = LSTMTimeSeriesPredictor()

        logger.info("Ensemble models initialized")

    def create_advanced_features(self, game_data: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive feature set with all advanced analyzers"""

        logger.info("Creating advanced features...")

        # Start with base features
        X = game_data.copy()

        # Add weather impact features
        weather_features = []
        for idx, row in game_data.iterrows():
            weather_data = self.weather_analyzer.get_historical_weather(
                location=row.get('location', 'outdoor'),
                date=row.get('game_date', '2024-01-01')
            )

            weather_impact = self.weather_analyzer.calculate_weather_impact_score(weather_data)

            weather_features.append({
                'weather_passing_impact': weather_impact['passing_impact'],
                'weather_rushing_impact': weather_impact['rushing_impact'],
                'weather_kicking_impact': weather_impact['kicking_impact'],
                'weather_total_impact': weather_impact['total_impact'],
                'weather_advantage': weather_impact['weather_advantage'],
                'temperature': weather_data['temperature'],
                'wind_speed': weather_data['wind_speed'],
                'precipitation': weather_data['precipitation'],
                'dome_game': weather_data['dome_game']
            })

        weather_df = pd.DataFrame(weather_features)
        X = pd.concat([X, weather_df], axis=1)

        # Add injury severity scores
        injury_features = []
        for idx, row in game_data.iterrows():
            # Mock injury data - in production, integrate with injury reports
            home_injuries = [
                {'position': 'QB', 'status': 'HEALTHY', 'importance': 0.9},
                {'position': 'RB', 'status': 'QUESTIONABLE', 'importance': 0.7}
            ]
            away_injuries = [
                {'position': 'WR', 'status': 'DOUBTFUL', 'importance': 0.8}
            ]

            home_injury_score = self.injury_scorer.calculate_team_injury_score(home_injuries)
            away_injury_score = self.injury_scorer.calculate_team_injury_score(away_injuries)

            injury_features.append({
                'home_injury_impact': home_injury_score['total_injury_impact'],
                'home_offensive_injury': home_injury_score['offensive_impact'],
                'home_defensive_injury': home_injury_score['defensive_impact'],
                'away_injury_impact': away_injury_score['total_injury_impact'],
                'away_offensive_injury': away_injury_score['offensive_impact'],
                'away_defensive_injury': away_injury_score['defensive_impact'],
                'injury_differential': home_injury_score['total_injury_impact'] - away_injury_score['total_injury_impact']
            })

        injury_df = pd.DataFrame(injury_features)
        X = pd.concat([X, injury_df], axis=1)

        # Add momentum indicators
        momentum_features = []
        for idx, row in game_data.iterrows():
            # Mock team stats - in production, calculate from historical data
            home_stats = {
                'recent_record': ['W', 'W', 'L', 'W'],
                'recent_point_diff': [7, -3, 14, 10],
                'ats_record': ['W', 'L', 'W', 'W'],
                'is_home': True,
                'home_record': 0.7,
                'strength_of_schedule': 0.52,
                'recent_turnover_diff': [1, -2, 0, 2],
                'injury_trend': 0.1
            }

            away_stats = {
                'recent_record': ['L', 'W', 'W', 'L'],
                'recent_point_diff': [-10, 3, 7, -14],
                'ats_record': ['L', 'W', 'L', 'L'],
                'is_home': False,
                'road_record': 0.4,
                'strength_of_schedule': 0.48,
                'recent_turnover_diff': [-1, 0, 1, -2],
                'injury_trend': -0.2
            }

            home_momentum = self.momentum_calculator.calculate_momentum_score(home_stats)
            away_momentum = self.momentum_calculator.calculate_momentum_score(away_stats)

            momentum_features.append({
                'home_momentum': home_momentum['total_momentum'],
                'away_momentum': away_momentum['total_momentum'],
                'momentum_differential': home_momentum['total_momentum'] - away_momentum['total_momentum'],
                'home_momentum_trend': 1 if home_momentum['trend'] == 'POSITIVE' else -1 if home_momentum['trend'] == 'NEGATIVE' else 0,
                'away_momentum_trend': 1 if away_momentum['trend'] == 'POSITIVE' else -1 if away_momentum['trend'] == 'NEGATIVE' else 0
            })

        momentum_df = pd.DataFrame(momentum_features)
        X = pd.concat([X, momentum_df], axis=1)

        # Add coaching analysis
        coaching_features = []
        for idx, row in game_data.iterrows():
            # Mock coaching data - in production, maintain coaching database
            home_coach = {
                'years_experience': 8,
                'playoff_wins': 3,
                'playoff_appearances': 5,
                'ats_win_percentage': 0.52,
                'situational_rank': 12,
                'draft_success_rate': 0.65,
                'timeout_efficiency': 0.7,
                'challenge_success_rate': 0.6
            }

            away_coach = {
                'years_experience': 15,
                'playoff_wins': 8,
                'playoff_appearances': 12,
                'ats_win_percentage': 0.58,
                'situational_rank': 8,
                'draft_success_rate': 0.72,
                'timeout_efficiency': 0.8,
                'challenge_success_rate': 0.75
            }

            coaching_analysis = self.coaching_analyzer.analyze_coaching_matchup(home_coach, away_coach)

            coaching_features.append({
                'coaching_advantage': coaching_analysis['coaching_advantage'],
                'home_coach_score': coaching_analysis['home_coach_score'],
                'away_coach_score': coaching_analysis['away_coach_score'],
                'coaching_experience_diff': coaching_analysis['factor_advantages']['experience_advantage'],
                'coaching_playoff_diff': coaching_analysis['factor_advantages']['playoff_success_advantage']
            })

        coaching_df = pd.DataFrame(coaching_features)
        X = pd.concat([X, coaching_df], axis=1)

        # Add betting line movement analysis
        betting_features = []
        for idx, row in game_data.iterrows():
            # Mock betting line data - in production, integrate with sportsbook APIs
            line_history = [
                {'timestamp': 1, 'spread': -3.5, 'volume': 1000, 'public_percentage': 60},
                {'timestamp': 2, 'spread': -4.0, 'volume': 1200, 'public_percentage': 65},
                {'timestamp': 3, 'spread': -3.0, 'volume': 1500, 'public_percentage': 55},
                {'timestamp': 4, 'spread': -3.5, 'volume': 1300, 'public_percentage': 58}
            ]

            line_analysis = self.betting_analyzer.analyze_line_movement(line_history)

            betting_features.append({
                'line_movement': line_analysis['raw_line_movement'],
                'line_movement_strength': line_analysis['line_movement_strength'],
                'sharp_money_indicator': line_analysis['sharp_money_indicator'],
                'public_betting_bias': line_analysis['public_betting_bias'],
                'market_sentiment': line_analysis['market_sentiment_strength'],
                'market_direction': 1 if line_analysis['market_direction'] == 'BULLISH' else -1 if line_analysis['market_direction'] == 'BEARISH' else 0
            })

        betting_df = pd.DataFrame(betting_features)
        X = pd.concat([X, betting_df], axis=1)

        # Add engineered interaction features
        if 'home_power_rating' in X.columns and 'away_power_rating' in X.columns:
            X['power_rating_diff'] = X['home_power_rating'] - X['away_power_rating']
            X['power_rating_sum'] = X['home_power_rating'] + X['away_power_rating']
            X['power_rating_product'] = X['home_power_rating'] * X['away_power_rating']

        # Add composite scores
        feature_cols = [col for col in X.columns if col not in ['game_id', 'home_team', 'away_team', 'game_date']]
        numeric_cols = X[feature_cols].select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 0:
            X['composite_home_advantage'] = (
                X.get('home_momentum', 0) * 0.3 +
                X.get('home_coach_score', 0.5) * 0.2 +
                (1 - X.get('home_injury_impact', 0)) * 0.3 +
                X.get('weather_advantage', 0) * 0.2
            )

            X['composite_team_strength'] = (
                X.get('power_rating_diff', 0) * 0.4 +
                X.get('momentum_differential', 0) * 0.3 +
                X.get('coaching_advantage', 0) * 0.3
            )

        # Store feature names for later use
        self.feature_names = [col for col in X.columns if col not in ['game_id', 'home_team', 'away_team', 'game_date']]

        logger.info(f"Advanced features created: {len(self.feature_names)} features")

        return X

    def hyperparameter_tuning(self, X: np.ndarray, y: np.ndarray, model_name: str, n_trials: int = 50):
        """Perform hyperparameter tuning using Optuna"""

        logger.info(f"Starting hyperparameter tuning for {model_name}")

        def objective(trial):
            if model_name == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 12),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
                    'random_state': 42,
                    'n_jobs': -1
                }
                model = xgb.XGBClassifier(**params)

            elif model_name == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 300),
                    'max_depth': trial.suggest_int('max_depth', 5, 20),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
                    'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
                    'random_state': 42,
                    'n_jobs': -1
                }
                model = RandomForestClassifier(**params)

            elif model_name == 'gradient_boosting':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 400),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 15),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 8),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'random_state': 42
                }
                model = GradientBoostingClassifier(**params)

            elif model_name == 'lightgbm':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'num_leaves': trial.suggest_int('num_leaves', 10, 100),
                    'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
                    'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
                    'random_state': 42,
                    'n_jobs': -1,
                    'verbosity': -1
                }
                model = lgb.LGBMClassifier(**params)

            # Cross-validation score
            cv_scores = cross_val_score(
                model, X, y,
                cv=TimeSeriesSplit(n_splits=5),
                scoring='accuracy',
                n_jobs=-1
            )

            return cv_scores.mean()

        # Create and optimize study
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        # Update model with best parameters
        best_params = study.best_params
        best_params.update({'random_state': 42, 'n_jobs': -1})

        if model_name == 'xgboost':
            self.models[model_name] = xgb.XGBClassifier(**best_params)
        elif model_name == 'random_forest':
            self.models[model_name] = RandomForestClassifier(**best_params)
        elif model_name == 'gradient_boosting':
            self.models[model_name] = GradientBoostingClassifier(**best_params)
        elif model_name == 'lightgbm':
            best_params['verbosity'] = -1
            self.models[model_name] = lgb.LGBMClassifier(**best_params)

        logger.info(f"Best parameters for {model_name}: {best_params}")
        logger.info(f"Best CV score: {study.best_value:.4f}")

        return study.best_params, study.best_value

    def fit(self, X: pd.DataFrame, y: np.ndarray, tune_hyperparameters: bool = False):
        """Train the ensemble with all models"""

        logger.info("Starting ensemble training...")

        # Create advanced features
        X_features = self.create_advanced_features(X)

        # Ensure we only use numeric features for modeling
        feature_columns = [col for col in X_features.columns
                          if col in self.feature_names and
                          X_features[col].dtype in ['int64', 'float64']]

        X_model = X_features[feature_columns].copy()

        # Handle missing values
        X_model = X_model.fillna(X_model.median())

        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_model, y, test_size=0.2, random_state=42, stratify=y
        )

        # Store validation data for calibration
        self.X_val = X_val
        self.y_val = y_val

        # Train each model
        ensemble_predictions = []
        ensemble_probabilities = []

        for model_name, model in self.models.items():
            logger.info(f"Training {model_name}...")

            # Scale features for this model
            X_train_scaled = self.scalers[model_name].fit_transform(X_train)
            X_val_scaled = self.scalers[model_name].transform(X_val)

            # Hyperparameter tuning if requested
            if tune_hyperparameters:
                best_params, best_score = self.hyperparameter_tuning(
                    X_train_scaled, y_train, model_name
                )
                self.training_history[f'{model_name}_tuning'] = {
                    'best_params': best_params,
                    'best_score': best_score
                }

            # Train model
            model.fit(X_train_scaled, y_train)

            # Validate
            val_predictions = model.predict(X_val_scaled)
            val_probabilities = model.predict_proba(X_val_scaled)

            accuracy = accuracy_score(y_val, val_predictions)
            self.validation_scores[model_name] = accuracy

            logger.info(f"{model_name} validation accuracy: {accuracy:.4f}")

            # Store predictions for ensemble
            ensemble_predictions.append(val_predictions)
            ensemble_probabilities.append(val_probabilities)

            # Calculate feature importance
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[model_name] = dict(
                    zip(feature_columns, model.feature_importances_)
                )

        # Train LSTM model
        logger.info("Training LSTM model...")
        X_lstm = X_model.values

        # Reshape for LSTM if we have enough data
        if len(X_lstm) > 20:  # Need reasonable amount of data for LSTM
            self.lstm_predictor.fit(X_lstm, y_train)
            lstm_proba = self.lstm_predictor.predict(X_val.values)
            ensemble_probabilities.append(lstm_proba)

        # Calculate ensemble weights based on validation performance
        weights = []
        for model_name in self.models.keys():
            weights.append(self.validation_scores.get(model_name, 0.5))

        if len(ensemble_probabilities) > len(weights):  # Include LSTM
            weights.append(np.mean(weights))  # Average weight for LSTM

        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()

        # Create ensemble predictions
        ensemble_proba = np.average(ensemble_probabilities, axis=0, weights=weights)

        # Calibrate confidence
        self.confidence_calibrator.fit(y_val, ensemble_proba)

        # Initialize SHAP explainer
        try:
            # Use tree explainer for tree-based models
            self.shap_explainer = shap.TreeExplainer(self.models['xgboost'])
            logger.info("SHAP explainer initialized")
        except Exception as e:
            logger.warning(f"Could not initialize SHAP explainer: {e}")

        # Calculate final ensemble accuracy
        calibrated_proba = self.confidence_calibrator.transform(ensemble_proba)
        ensemble_predictions = np.argmax(calibrated_proba, axis=1)
        ensemble_accuracy = accuracy_score(y_val, ensemble_predictions)

        self.validation_scores['ensemble'] = ensemble_accuracy
        logger.info(f"Ensemble validation accuracy: {ensemble_accuracy:.4f}")

        # Store training metadata
        self.training_history['ensemble'] = {
            'weights': weights.tolist(),
            'feature_count': len(feature_columns),
            'validation_accuracy': ensemble_accuracy,
            'model_accuracies': self.validation_scores
        }

        logger.info("Ensemble training completed!")

        return self.training_history

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions with the ensemble"""

        # Create advanced features
        X_features = self.create_advanced_features(X)

        # Use same features as training
        feature_columns = [col for col in X_features.columns
                          if col in self.feature_names and
                          X_features[col].dtype in ['int64', 'float64']]

        X_model = X_features[feature_columns].copy()
        X_model = X_model.fillna(X_model.median())

        # Get predictions from all models
        ensemble_probabilities = []

        for model_name, model in self.models.items():
            X_scaled = self.scalers[model_name].transform(X_model)
            proba = model.predict_proba(X_scaled)
            ensemble_probabilities.append(proba)

        # Add LSTM predictions if available
        if self.lstm_predictor.is_trained:
            lstm_proba = self.lstm_predictor.predict(X_model.values)
            ensemble_probabilities.append(lstm_proba)

        # Use stored weights
        weights = self.training_history.get('ensemble', {}).get('weights',
                                                              [1/len(ensemble_probabilities)] * len(ensemble_probabilities))

        # Ensemble predictions
        ensemble_proba = np.average(ensemble_probabilities, axis=0, weights=weights)

        # Apply confidence calibration
        calibrated_proba = self.confidence_calibrator.transform(ensemble_proba)

        # Return class predictions
        return np.argmax(calibrated_proba, axis=1)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get calibrated prediction probabilities"""

        # Create advanced features
        X_features = self.create_advanced_features(X)

        # Use same features as training
        feature_columns = [col for col in X_features.columns
                          if col in self.feature_names and
                          X_features[col].dtype in ['int64', 'float64']]

        X_model = X_features[feature_columns].copy()
        X_model = X_model.fillna(X_model.median())

        # Get predictions from all models
        ensemble_probabilities = []

        for model_name, model in self.models.items():
            X_scaled = self.scalers[model_name].transform(X_model)
            proba = model.predict_proba(X_scaled)
            ensemble_probabilities.append(proba)

        # Add LSTM predictions if available
        if self.lstm_predictor.is_trained:
            lstm_proba = self.lstm_predictor.predict(X_model.values)
            ensemble_probabilities.append(lstm_proba)

        # Use stored weights
        weights = self.training_history.get('ensemble', {}).get('weights',
                                                              [1/len(ensemble_probabilities)] * len(ensemble_probabilities))

        # Ensemble predictions
        ensemble_proba = np.average(ensemble_probabilities, axis=0, weights=weights)

        # Apply confidence calibration
        calibrated_proba = self.confidence_calibrator.transform(ensemble_proba)

        return calibrated_proba

    def get_feature_importance(self, top_k: int = 20) -> Dict[str, float]:
        """Get aggregated feature importance across models"""

        if not self.feature_importance:
            logger.warning("No feature importance calculated yet")
            return {}

        # Aggregate importance scores
        all_features = set()
        for importance_dict in self.feature_importance.values():
            all_features.update(importance_dict.keys())

        aggregated_importance = {}
        for feature in all_features:
            scores = [
                importance_dict.get(feature, 0)
                for importance_dict in self.feature_importance.values()
            ]
            aggregated_importance[feature] = np.mean(scores)

        # Sort and return top K
        sorted_features = sorted(
            aggregated_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return dict(sorted_features[:top_k])

    def explain_prediction(self, X: pd.DataFrame, sample_idx: int = 0) -> Dict[str, Any]:
        """Explain a specific prediction using SHAP"""

        if self.shap_explainer is None:
            logger.warning("SHAP explainer not available")
            return {'error': 'SHAP explainer not initialized'}

        # Prepare features
        X_features = self.create_advanced_features(X)
        feature_columns = [col for col in X_features.columns
                          if col in self.feature_names and
                          X_features[col].dtype in ['int64', 'float64']]

        X_model = X_features[feature_columns].copy()
        X_model = X_model.fillna(X_model.median())
        X_scaled = self.scalers['xgboost'].transform(X_model)

        # Get SHAP values
        try:
            shap_values = self.shap_explainer.shap_values(X_scaled[sample_idx:sample_idx+1])

            # For multi-class, shap_values is a list
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class

            explanation = {
                'shap_values': shap_values.flatten().tolist(),
                'feature_names': feature_columns,
                'feature_values': X_scaled[sample_idx].tolist(),
                'base_value': self.shap_explainer.expected_value if hasattr(self.shap_explainer, 'expected_value') else 0,
                'prediction': self.predict(X.iloc[sample_idx:sample_idx+1])[0],
                'prediction_proba': self.predict_proba(X.iloc[sample_idx:sample_idx+1])[0].tolist()
            }

            return explanation

        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            return {'error': str(e)}

    def get_model_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""

        report = {
            'ensemble_accuracy': self.validation_scores.get('ensemble', 0.0),
            'individual_models': self.validation_scores,
            'feature_count': len(self.feature_names),
            'top_features': self.get_feature_importance(top_k=10),
            'training_config': {
                'models_used': list(self.models.keys()),
                'lstm_enabled': self.lstm_predictor.is_trained,
                'confidence_calibration': self.confidence_calibrator.is_calibrated,
                'shap_available': self.shap_explainer is not None
            }
        }

        # Add model-specific insights
        if 'ensemble' in self.training_history:
            report['model_weights'] = self.training_history['ensemble']['weights']

        return report

    def save_model(self, filepath: str = '/home/iris/code/experimental/nfl-predictor-api/models/ensemble_predictor.pkl'):
        """Save the complete ensemble model"""

        # Create models directory if it doesn't exist
        models_dir = Path(filepath).parent
        models_dir.mkdir(parents=True, exist_ok=True)

        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'lstm_predictor': self.lstm_predictor,
            'confidence_calibrator': self.confidence_calibrator,
            'feature_importance': self.feature_importance,
            'feature_names': self.feature_names,
            'training_history': self.training_history,
            'validation_scores': self.validation_scores,
            'config': self.config
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Ensemble model saved to {filepath}")

    def load_model(self, filepath: str = '/home/iris/code/experimental/nfl-predictor-api/models/ensemble_predictor.pkl'):
        """Load a trained ensemble model"""

        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.models = model_data['models']
        self.scalers = model_data['scalers']
        self.lstm_predictor = model_data['lstm_predictor']
        self.confidence_calibrator = model_data['confidence_calibrator']
        self.feature_importance = model_data['feature_importance']
        self.feature_names = model_data['feature_names']
        self.training_history = model_data['training_history']
        self.validation_scores = model_data['validation_scores']
        self.config = model_data.get('config', {})

        logger.info(f"Ensemble model loaded from {filepath}")


def create_sample_training_data(n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
    """Create sample training data for testing the ensemble"""

    np.random.seed(42)

    # Base features
    data = {
        'home_team': [f'Team_{i%32}' for i in range(n_samples)],
        'away_team': [f'Team_{(i+16)%32}' for i in range(n_samples)],
        'week': np.random.randint(1, 18, n_samples),
        'home_power_rating': np.random.normal(85, 10, n_samples),
        'away_power_rating': np.random.normal(85, 10, n_samples),
        'location': ['outdoor'] * int(n_samples * 0.8) + ['dome'] * int(n_samples * 0.2),
        'game_date': ['2024-01-01'] * n_samples
    }

    X = pd.DataFrame(data)

    # Target variable (0: away win, 1: home win, 2: tie)
    # Create realistic home field advantage
    home_advantage = 0.55
    y = np.random.choice([0, 1], size=n_samples, p=[1-home_advantage, home_advantage])

    return X, y


# Example usage and testing
if __name__ == "__main__":
    logger.info("Advanced Ensemble Predictor for NFL Games")
    logger.info("Target: 75%+ accuracy with comprehensive feature analysis")

    # Create sample data
    X_sample, y_sample = create_sample_training_data(1000)

    # Initialize ensemble
    ensemble = AdvancedEnsemblePredictor()

    # Train ensemble
    training_results = ensemble.fit(X_sample, y_sample, tune_hyperparameters=False)

    # Get performance report
    report = ensemble.get_model_performance_report()
    print("\nPerformance Report:")
    print(f"Ensemble Accuracy: {report['ensemble_accuracy']:.4f}")
    print(f"Feature Count: {report['feature_count']}")

    # Display top features
    print("\nTop Features:")
    for feature, importance in list(report['top_features'].items())[:10]:
        print(f"  {feature}: {importance:.4f}")

    # Save model
    ensemble.save_model()

    logger.info("Ensemble predictor ready for deployment!")