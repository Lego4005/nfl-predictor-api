"""
Enhanced Game Prediction Models with Historical Training

This module implements sophisticated ML models for NFL game predictions using
2+ years of historical data with advanced metrics like power rankings, 
scoring offense/defense ranks, QBR, and turnover differentials.

Target Accuracy: >62% for game predictions using historical patterns
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import joblib
import os

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_pipeline import DataPipeline
from enhanced_features import EnhancedFeatureEngine

logger = logging.getLogger(__name__)

@dataclass
class GamePrediction:
    """Game prediction result with confidence and explanation"""
    home_team: str
    away_team: str
    week: int
    season: int
    
    # Predictions
    winner_prediction: str  # 'home' or 'away'
    winner_confidence: float  # 0.0 to 1.0
    
    # Spread predictions
    spread_prediction: float  # Predicted point spread (negative = home favored)
    spread_confidence: float
    
    # Total predictions
    total_prediction: float  # Predicted total points
    total_confidence: float
    
    # Model explanations
    key_factors: List[str]  # Top factors influencing prediction
    feature_importance: Dict[str, float]  # Feature importance scores
    
    # Ensemble details
    model_votes: Dict[str, str]  # Individual model predictions
    model_confidences: Dict[str, float]  # Individual model confidences

class EnhancedGamePredictor:
    """
    Enhanced game prediction system using ensemble of ML models
    trained on 2+ years of historical data with advanced metrics
    """
    
    def __init__(self, data_pipeline: DataPipeline):
        self.data_pipeline = data_pipeline
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_columns: List[str] = []
        self.model_weights: Dict[str, float] = {}
        
        # Initialize enhanced feature engine
        if self.data_pipeline.games_df is not None:
            self.feature_engine = EnhancedFeatureEngine(self.data_pipeline.games_df)
        else:
            self.feature_engine = None
        
        # Model configurations
        self.model_configs = {
            'random_forest': {
                'n_estimators': 200,
                'max_depth': 15,
                'min_samples_split': 10,
                'min_samples_leaf': 5,
                'random_state': 42
            },
            'xgboost': {
                'n_estimators': 150,
                'max_depth': 8,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 150,
                'max_depth': 8,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'random_state': 42
            },
            'neural_network': {
                'hidden_layer_sizes': (100, 50, 25),
                'activation': 'relu',
                'solver': 'adam',
                'alpha': 0.001,
                'max_iter': 500,
                'random_state': 42
            }
        }
        
    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from historical games with advanced features
        """
        logger.info("🏗️ Preparing training data with advanced features...")
        
        if self.data_pipeline.games_df is None:
            raise ValueError("No historical games data available")
            
        training_features = []
        training_labels = []
        
        # Process each historical game
        for _, game in self.data_pipeline.games_df.iterrows():
            try:
                # Create game features using our enhanced pipeline
                game_date = pd.to_datetime(game['date'])
                features = self.data_pipeline.create_game_features(
                    home_team=game['home_team'],
                    away_team=game['away_team'],
                    date=game_date,
                    week=game['week']
                )
                
                # Enhance with advanced features
                if self.feature_engine:
                    features = self.feature_engine.enhance_game_features(features)
                
                # Add actual game outcome features
                features['actual_home_score'] = game['home_score']
                features['actual_away_score'] = game['away_score']
                features['actual_total'] = game['total_points']
                features['actual_margin'] = game['margin']
                
                # Create labels
                winner_label = 1 if game['winner'] == game['home_team'] else 0  # 1 = home wins
                
                training_features.append(features)
                training_labels.append(winner_label)
                
            except Exception as e:
                logger.warning(f"⚠️ Skipping game {game.get('game_id', 'unknown')}: {e}")
                continue
                
        if not training_features:
            raise ValueError("No valid training features generated")
            
        # Convert to DataFrame
        features_df = pd.DataFrame(training_features)
        labels_series = pd.Series(training_labels)
        
        # Remove non-predictive features (actual outcomes) and non-numeric features
        prediction_features = features_df.drop(columns=[
            'actual_home_score', 'actual_away_score', 
            'actual_total', 'actual_margin',
            'home_team', 'away_team'  # Remove team names (strings)
        ], errors='ignore')
        
        # Keep only numeric columns
        numeric_features = prediction_features.select_dtypes(include=[np.number])
        
        # Store feature columns for later use
        self.feature_columns = numeric_features.columns.tolist()
        
        logger.info(f"✅ Prepared {len(numeric_features)} training samples with {len(self.feature_columns)} features")
        logger.info(f"📊 Feature categories: {len([f for f in self.feature_columns if 'rank' in f])} ranking features, "
                   f"{len([f for f in self.feature_columns if 'power' in f])} power features, "
                   f"{len([f for f in self.feature_columns if 'differential' in f])} differential features")
        
        return numeric_features, labels_series
        
    def train_models(self) -> Dict[str, float]:
        """
        Train ensemble of ML models with temporal cross-validation
        """
        logger.info("🚀 Training enhanced game prediction models...")
        
        # Prepare training data
        X, y = self.prepare_training_data()
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Initialize models
        models = {
            'random_forest': RandomForestClassifier(**self.model_configs['random_forest']),
            'xgboost': xgb.XGBClassifier(**self.model_configs['xgboost']),
            'gradient_boosting': GradientBoostingClassifier(**self.model_configs['gradient_boosting']),
            'neural_network': MLPClassifier(**self.model_configs['neural_network'])
        }
        
        # Temporal cross-validation (important for time series data)
        tscv = TimeSeriesSplit(n_splits=5)
        model_scores = {}
        
        for model_name, model in models.items():
            logger.info(f"🔧 Training {model_name}...")
            
            # Scale features for neural network
            if model_name == 'neural_network':
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                self.scalers[model_name] = scaler
                
                # Cross-validation with scaled features
                scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='accuracy')
                
                # Train final model
                model.fit(X_scaled, y)
            else:
                # Cross-validation
                scores = cross_val_score(model, X, y, cv=tscv, scoring='accuracy')
                
                # Train final model
                model.fit(X, y)
            
            # Store model and scores
            self.models[model_name] = model
            model_scores[model_name] = scores.mean()
            
            logger.info(f"✅ {model_name}: {scores.mean():.3f} ± {scores.std():.3f} accuracy")
            
        # Calculate ensemble weights based on performance
        total_score = sum(model_scores.values())
        self.model_weights = {
            name: score / total_score 
            for name, score in model_scores.items()
        }
        
        # Overall ensemble performance estimate
        ensemble_score = sum(score * weight for score, weight in zip(model_scores.values(), self.model_weights.values()))
        
        logger.info(f"🎯 Ensemble Model Performance: {ensemble_score:.3f} accuracy")
        logger.info(f"📊 Model Weights: {self.model_weights}")
        
        return model_scores
        
    def predict_game(self, home_team: str, away_team: str, date: datetime, week: int) -> GamePrediction:
        """
        Generate comprehensive game prediction using ensemble models
        """
        if not self.models:
            raise ValueError("Models not trained. Call train_models() first.")
            
        # Create game features
        features = self.data_pipeline.create_game_features(home_team, away_team, date, week)
        
        # Enhance with advanced features
        if self.feature_engine:
            features = self.feature_engine.enhance_game_features(features)
        
        # Convert to DataFrame and ensure feature order
        feature_df = pd.DataFrame([features])
        feature_df = feature_df.reindex(columns=self.feature_columns, fill_value=0)
        
        # Handle missing values
        feature_df = feature_df.fillna(feature_df.median())
        
        # Get predictions from each model
        model_predictions = {}
        model_probabilities = {}
        
        for model_name, model in self.models.items():
            if model_name == 'neural_network':
                # Use scaled features for neural network
                X_scaled = self.scalers[model_name].transform(feature_df)
                pred = model.predict(X_scaled)[0]
                prob = model.predict_proba(X_scaled)[0]
            else:
                pred = model.predict(feature_df)[0]
                prob = model.predict_proba(feature_df)[0]
                
            model_predictions[model_name] = 'home' if pred == 1 else 'away'
            model_probabilities[model_name] = max(prob)  # Confidence in prediction
            
        # Ensemble prediction (weighted voting)
        home_votes = sum(
            self.model_weights[name] 
            for name, pred in model_predictions.items() 
            if pred == 'home'
        )
        
        winner_prediction = 'home' if home_votes > 0.5 else 'away'
        winner_confidence = max(home_votes, 1 - home_votes)
        
        # Feature importance (from Random Forest)
        feature_importance = {}
        if 'random_forest' in self.models:
            rf_importance = self.models['random_forest'].feature_importances_
            feature_importance = dict(zip(self.feature_columns, rf_importance))
            
        # Get top factors
        top_factors = self._get_key_factors(features, feature_importance)
        
        # Create prediction object
        prediction = GamePrediction(
            home_team=home_team,
            away_team=away_team,
            week=week,
            season=date.year if date.month >= 9 else date.year - 1,
            winner_prediction=winner_prediction,
            winner_confidence=winner_confidence,
            spread_prediction=self._predict_spread(features),
            spread_confidence=0.75,  # Placeholder
            total_prediction=self._predict_total(features),
            total_confidence=0.70,  # Placeholder
            key_factors=top_factors,
            feature_importance=feature_importance,
            model_votes=model_predictions,
            model_confidences=model_probabilities
        )
        
        return prediction
        
    def _predict_spread(self, features: Dict) -> float:
        """Predict point spread (negative = home favored)"""
        # Use power ranking differential and other factors
        power_diff = features.get('power_ranking_differential', 0)
        home_advantage = 2.5  # Standard home field advantage
        
        # Adjust based on power rankings (lower rank = better team)
        spread = power_diff * 0.5 - home_advantage
        
        return round(spread, 1)
        
    def _predict_total(self, features: Dict) -> float:
        """Predict total points"""
        # Use offensive/defensive rankings and recent trends
        home_off_rank = features.get('home_scoring_offense_rank', 16)
        away_off_rank = features.get('away_scoring_offense_rank', 16)
        home_def_rank = features.get('home_scoring_defense_rank', 16)
        away_def_rank = features.get('away_scoring_defense_rank', 16)
        
        # Base total around league average
        base_total = 44.0
        
        # Adjust based on offensive and defensive strength
        offensive_adjustment = (32 - home_off_rank + 32 - away_off_rank) * 0.3
        defensive_adjustment = (home_def_rank + away_def_rank - 32) * 0.2
        
        total = base_total + offensive_adjustment + defensive_adjustment
        
        return round(total, 1)
        
    def _get_key_factors(self, features: Dict, importance: Dict[str, float]) -> List[str]:
        """Get key factors influencing the prediction"""
        if not importance:
            return ["Power rankings", "Recent form", "Home field advantage"]
            
        # Sort features by importance
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # Convert technical feature names to readable explanations
        factor_explanations = {
            'power_ranking_differential': f"Power ranking advantage ({features.get('power_ranking_differential', 0):+.1f})",
            'home_power_score': f"Home team power score ({features.get('home_power_score', 0):.1f})",
            'away_power_score': f"Away team power score ({features.get('away_power_score', 0):.1f})",
            'home_scoring_offense_rank': f"Home offense rank (#{features.get('home_scoring_offense_rank', 16)})",
            'away_scoring_defense_rank': f"Away defense rank (#{features.get('away_scoring_defense_rank', 16)})",
            'home_win_percentage': f"Home team win rate ({features.get('home_win_percentage', 0.5):.1%})",
            'turnover_differential_gap': f"Turnover differential gap ({features.get('turnover_differential_gap', 0):+.1f})",
            'qbr_differential': f"QBR advantage ({features.get('qbr_differential', 0):+.1f})"
        }
        
        key_factors = []
        for feature_name, _ in sorted_features[:5]:  # Top 5 factors
            explanation = factor_explanations.get(feature_name, feature_name.replace('_', ' ').title())
            key_factors.append(explanation)
            
        return key_factors
        
    def save_models(self, model_dir: str = "models/game_prediction"):
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        # Save each model
        for model_name, model in self.models.items():
            model_path = os.path.join(model_dir, f"{model_name}.joblib")
            joblib.dump(model, model_path)
            
        # Save scalers
        for scaler_name, scaler in self.scalers.items():
            scaler_path = os.path.join(model_dir, f"{scaler_name}_scaler.joblib")
            joblib.dump(scaler, scaler_path)
            
        # Save metadata
        metadata = {
            'feature_columns': self.feature_columns,
            'model_weights': self.model_weights,
            'training_date': datetime.now().isoformat()
        }
        
        import json
        with open(os.path.join(model_dir, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"✅ Models saved to {model_dir}")
        
    def load_models(self, model_dir: str = "models/game_prediction"):
        """Load trained models from disk"""
        import json
        
        # Load metadata
        with open(os.path.join(model_dir, "metadata.json"), 'r') as f:
            metadata = json.load(f)
            
        self.feature_columns = metadata['feature_columns']
        self.model_weights = metadata['model_weights']
        
        # Load models
        for model_name in self.model_weights.keys():
            model_path = os.path.join(model_dir, f"{model_name}.joblib")
            if os.path.exists(model_path):
                self.models[model_name] = joblib.load(model_path)
                
        # Load scalers
        for model_name in self.models.keys():
            scaler_path = os.path.join(model_dir, f"{model_name}_scaler.joblib")
            if os.path.exists(scaler_path):
                self.scalers[model_name] = joblib.load(scaler_path)
                
        logger.info(f"✅ Models loaded from {model_dir}")

def main():
    """Test the enhanced game prediction models"""
    # Initialize data pipeline
    pipeline = DataPipeline()
    
    # Create predictor
    predictor = EnhancedGamePredictor(pipeline)
    
    # Train models
    logger.info("🚀 Training enhanced game prediction models...")
    scores = predictor.train_models()
    
    # Test prediction
    test_date = datetime(2024, 12, 15)  # Week 15
    prediction = predictor.predict_game('KC', 'BUF', test_date, 15)
    
    print(f"\n🏈 Game Prediction: {prediction.away_team} @ {prediction.home_team}")
    print(f"🎯 Winner: {prediction.winner_prediction.upper()} ({prediction.winner_confidence:.1%} confidence)")
    print(f"📊 Spread: {prediction.spread_prediction:+.1f} (Home perspective)")
    print(f"🔢 Total: {prediction.total_prediction:.1f}")
    print(f"\n🔍 Key Factors:")
    for factor in prediction.key_factors:
        print(f"  • {factor}")
    print(f"\n🤖 Model Votes: {prediction.model_votes}")
    
    # Save models
    predictor.save_models()
    
    print(f"\n🎉 Enhanced Game Prediction Models Complete!")
    print(f"📈 Target Accuracy: >62% (Enhanced with 2+ years of data)")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()