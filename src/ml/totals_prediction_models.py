"""
Totals (Over/Under) Prediction Models

This module implements machine learning models specifically for predicting
NFL game totals (over/under) with advanced feature engineering.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
import logging
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class TotalsPredictor:
    """Advanced totals prediction using ensemble methods"""
    
    def __init__(self, data_pipeline, feature_engine):
        self.data_pipeline = data_pipeline
        self.feature_engine = feature_engine
        self.models = {}
        self.scalers = {}
        self.model_weights = {}
        self.feature_names = []
        
        # Model configurations
        self.model_configs = {
            'totals_random_forest': {
                'model': RandomForestRegressor(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'needs_scaling': False
            },
            'totals_xgboost': {
                'model': xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                ),
                'needs_scaling': False
            },
            'totals_gradient_boosting': {
                'model': GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42
                ),
                'needs_scaling': False
            },
            'totals_neural_network': {
                'model': MLPRegressor(
                    hidden_layer_sizes=(100, 50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    learning_rate='adaptive',
                    max_iter=500,
                    random_state=42
                ),
                'needs_scaling': True
            }
        }
    
    def create_totals_features(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """Create totals-specific features"""
        logger.info("🏗️ Preparing totals training data with scoring analysis...")
        
        features_list = []
        
        for _, game in games_df.iterrows():
            try:
                # Convert to proper types
                week = int(game['week']) if 'week' in game else 1
                season = int(game['season']) if 'season' in game else 2024
                
                # Get base game features
                game_features = self.data_pipeline.create_game_features(
                    game['home_team'], game['away_team'], week, season
                )
                
                # Add totals-specific features
                totals_features = self._create_totals_specific_features(
                    game['home_team'], game['away_team'], week, season
                )
                
                # Combine features
                combined_features = {**game_features, **totals_features}
                combined_features['actual_total'] = game['home_score'] + game['away_score']
                combined_features['game_id'] = f"{game['away_team']}@{game['home_team']}_W{week}"
                
                features_list.append(combined_features)
                
            except Exception as e:
                logger.warning(f"⚠️ Error creating features for {game['away_team']} @ {game['home_team']}: {e}")
                continue
        
        if not features_list:
            logger.error("❌ No valid features created for totals training")
            return pd.DataFrame()
        
        features_df = pd.DataFrame(features_list)
        
        # Remove rows with missing actual totals
        features_df = features_df.dropna(subset=['actual_total'])
        
        logger.info(f"✅ Prepared {len(features_df)} totals training samples with {len(features_df.columns)-2} features")
        
        return features_df
    
    def _create_totals_specific_features(self, home_team: str, away_team: str, 
                                       week: int, season: int) -> Dict[str, float]:
        """Create features specific to totals prediction"""
        features = {}
        
        try:
            # Get team season stats
            home_stats = self.feature_engine.get_team_season_stats(home_team, season)
            away_stats = self.feature_engine.get_team_season_stats(away_team, season)
            
            # Offensive pace and efficiency
            features['home_points_per_game'] = home_stats.get('points_per_game', 20.0)
            features['away_points_per_game'] = away_stats.get('points_per_game', 20.0)
            features['combined_ppg'] = features['home_points_per_game'] + features['away_points_per_game']
            
            # Defensive efficiency
            features['home_points_allowed_per_game'] = home_stats.get('points_allowed_per_game', 22.0)
            features['away_points_allowed_per_game'] = away_stats.get('points_allowed_per_game', 22.0)
            features['combined_papg'] = features['home_points_allowed_per_game'] + features['away_points_allowed_per_game']
            
            # Pace of play indicators
            features['home_plays_per_game'] = home_stats.get('plays_per_game', 65.0)
            features['away_plays_per_game'] = away_stats.get('plays_per_game', 65.0)
            features['combined_pace'] = features['home_plays_per_game'] + features['away_plays_per_game']
            
            # Yards per play (efficiency)
            features['home_yards_per_play'] = home_stats.get('yards_per_play', 5.5)
            features['away_yards_per_play'] = away_stats.get('yards_per_play', 5.5)
            features['combined_ypp'] = features['home_yards_per_play'] + features['away_yards_per_play']
            
            # Red zone efficiency
            features['home_red_zone_pct'] = home_stats.get('red_zone_pct', 0.55)
            features['away_red_zone_pct'] = away_stats.get('red_zone_pct', 0.55)
            features['combined_rz_eff'] = features['home_red_zone_pct'] + features['away_red_zone_pct']
            
            # Turnover differential impact
            features['home_turnover_diff'] = home_stats.get('turnover_differential', 0.0)
            features['away_turnover_diff'] = away_stats.get('turnover_differential', 0.0)
            features['combined_to_diff'] = features['home_turnover_diff'] + features['away_turnover_diff']
            
            # Time of possession (affects pace)
            features['home_time_of_possession'] = home_stats.get('time_of_possession', 30.0)
            features['away_time_of_possession'] = away_stats.get('time_of_possession', 30.0)
            
            # Weather factors (dome vs outdoor)
            features['is_dome_game'] = 1.0 if home_team in ['NO', 'ATL', 'DET', 'MIN', 'LV', 'LAR', 'ARI'] else 0.0
            
            # Week-based adjustments
            features['week_factor'] = min(week / 18.0, 1.0)  # Season progression
            features['is_late_season'] = 1.0 if week >= 15 else 0.0
            
            # Matchup-specific factors
            features['offense_vs_defense'] = (
                features['home_points_per_game'] - features['away_points_allowed_per_game'] +
                features['away_points_per_game'] - features['home_points_allowed_per_game']
            ) / 2.0
            
            # Historical totals tendency
            features['home_over_tendency'] = home_stats.get('games_over_total', 0.5)
            features['away_over_tendency'] = away_stats.get('games_over_total', 0.5)
            features['combined_over_tendency'] = (features['home_over_tendency'] + features['away_over_tendency']) / 2.0
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating totals features: {e}")
            # Return default features
            features = {
                'home_points_per_game': 21.0, 'away_points_per_game': 21.0, 'combined_ppg': 42.0,
                'home_points_allowed_per_game': 21.0, 'away_points_allowed_per_game': 21.0, 'combined_papg': 42.0,
                'home_plays_per_game': 65.0, 'away_plays_per_game': 65.0, 'combined_pace': 130.0,
                'home_yards_per_play': 5.5, 'away_yards_per_play': 5.5, 'combined_ypp': 11.0,
                'home_red_zone_pct': 0.55, 'away_red_zone_pct': 0.55, 'combined_rz_eff': 1.1,
                'home_turnover_diff': 0.0, 'away_turnover_diff': 0.0, 'combined_to_diff': 0.0,
                'home_time_of_possession': 30.0, 'away_time_of_possession': 30.0,
                'is_dome_game': 0.0, 'week_factor': 0.5, 'is_late_season': 0.0,
                'offense_vs_defense': 0.0, 'home_over_tendency': 0.5, 'away_over_tendency': 0.5,
                'combined_over_tendency': 0.5
            }
        
        return features
    
    def train_totals_models(self) -> Dict[str, float]:
        """Train all totals prediction models"""
        logger.info("🚀 Training totals prediction models...")
        
        # Get historical games
        games_df = self.data_pipeline.games_df
        if games_df is None or games_df.empty:
            logger.error("❌ No historical games available for totals training")
            return {}
        
        # Create features
        features_df = self.create_totals_features(games_df)
        if features_df.empty:
            logger.error("❌ No features created for totals training")
            return {}
        
        # Prepare training data
        feature_cols = [col for col in features_df.columns 
                       if col not in ['actual_total', 'game_id']]
        X = features_df[feature_cols].fillna(0)
        y = features_df['actual_total']
        
        self.feature_names = feature_cols
        
        # Count feature categories
        scoring_features = len([f for f in feature_cols if any(x in f for x in ['points', 'total', 'score'])])
        pace_features = len([f for f in feature_cols if any(x in f for x in ['pace', 'plays', 'time'])])
        efficiency_features = len([f for f in feature_cols if any(x in f for x in ['yards', 'red_zone', 'efficiency'])])
        
        logger.info(f"📊 Totals Feature categories: {scoring_features} scoring features, {pace_features} pace features, {efficiency_features} efficiency features")
        
        # Train models with time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        model_scores = {}
        
        for model_name, config in self.model_configs.items():
            logger.info(f"🔧 Training {model_name}...")
            
            model = config['model']
            
            # Scale features if needed
            if config['needs_scaling']:
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                self.scalers[model_name] = scaler
            else:
                X_scaled = X
                self.scalers[model_name] = None
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=tscv, 
                                      scoring='neg_mean_absolute_error', n_jobs=-1)
            mae_scores = -cv_scores
            avg_mae = mae_scores.mean()
            std_mae = mae_scores.std()
            
            # Train final model
            model.fit(X_scaled, y)
            self.models[model_name] = model
            
            model_scores[model_name] = avg_mae
            logger.info(f"✅ {model_name}: {avg_mae:.2f} ± {std_mae:.2f} MAE")
        
        # Calculate ensemble weights (inverse of MAE)
        total_inverse_mae = sum(1/mae for mae in model_scores.values())
        self.model_weights = {
            name: (1/mae) / total_inverse_mae 
            for name, mae in model_scores.items()
        }
        
        # Calculate ensemble performance
        ensemble_mae = sum(mae * weight for mae, weight in zip(model_scores.values(), self.model_weights.values()))
        
        logger.info(f"🎯 Totals Ensemble Performance: {ensemble_mae:.2f} MAE")
        logger.info(f"📊 Totals Model Weights: {self.model_weights}")
        
        return model_scores
    
    def predict_total(self, home_team: str, away_team: str, 
                     week: int, season: int = 2024) -> Dict[str, Any]:
        """Predict game total with confidence"""
        try:
            # Create features
            game_features = self.data_pipeline.create_game_features(
                home_team, away_team, week, season
            )
            totals_features = self._create_totals_specific_features(
                home_team, away_team, week, season
            )
            
            # Combine features
            combined_features = {**game_features, **totals_features}
            
            # Convert to DataFrame
            feature_df = pd.DataFrame([combined_features])
            feature_df = feature_df[self.feature_names].fillna(0)
            
            # Get predictions from all models
            predictions = {}
            for model_name, model in self.models.items():
                if self.scalers[model_name] is not None:
                    X_scaled = self.scalers[model_name].transform(feature_df)
                else:
                    X_scaled = feature_df
                
                pred = model.predict(X_scaled)[0]
                predictions[model_name] = max(pred, 30.0)  # Minimum reasonable total
            
            # Ensemble prediction
            ensemble_total = sum(
                pred * self.model_weights[name] 
                for name, pred in predictions.items()
            )
            
            # Round to nearest 0.5
            ensemble_total = round(ensemble_total * 2) / 2
            
            # Determine over/under recommendation
            market_total = 47.5  # Default market total
            recommendation = "OVER" if ensemble_total > market_total else "UNDER"
            
            # Calculate confidence based on prediction spread
            pred_values = list(predictions.values())
            prediction_std = np.std(pred_values)
            confidence = max(0.55, min(0.85, 0.7 - (prediction_std / 10)))
            
            # Key factors
            key_factors = self._get_totals_key_factors(combined_features)
            
            return {
                'predicted_total': ensemble_total,
                'market_total': market_total,
                'recommendation': recommendation,
                'confidence': confidence,
                'edge': abs(ensemble_total - market_total),
                'key_factors': key_factors,
                'model_predictions': predictions
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting total for {away_team} @ {home_team}: {e}")
            return {
                'predicted_total': 47.5,
                'market_total': 47.5,
                'recommendation': 'UNDER',
                'confidence': 0.60,
                'edge': 0.0,
                'key_factors': ['Default prediction'],
                'model_predictions': {}
            }
    
    def _get_totals_key_factors(self, features: Dict[str, float]) -> List[str]:
        """Identify key factors influencing the total"""
        factors = []
        
        try:
            # High scoring offenses
            if features.get('combined_ppg', 42) > 50:
                factors.append("High-scoring offenses")
            elif features.get('combined_ppg', 42) < 38:
                factors.append("Low-scoring offenses")
            
            # Defensive strength
            if features.get('combined_papg', 42) < 38:
                factors.append("Strong defenses")
            elif features.get('combined_papg', 42) > 50:
                factors.append("Weak defenses")
            
            # Pace of play
            if features.get('combined_pace', 130) > 140:
                factors.append("Fast-paced game")
            elif features.get('combined_pace', 130) < 120:
                factors.append("Slow-paced game")
            
            # Weather/dome
            if features.get('is_dome_game', 0) == 1:
                factors.append("Dome game (favorable conditions)")
            
            # Red zone efficiency
            if features.get('combined_rz_eff', 1.1) > 1.2:
                factors.append("High red zone efficiency")
            
            # Over/under tendency
            if features.get('combined_over_tendency', 0.5) > 0.6:
                factors.append("Teams tend to go OVER")
            elif features.get('combined_over_tendency', 0.5) < 0.4:
                factors.append("Teams tend to go UNDER")
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting key factors: {e}")
            factors = ["Standard analysis"]
        
        return factors[:3] if factors else ["Standard analysis"]