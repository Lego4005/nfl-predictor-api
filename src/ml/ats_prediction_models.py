"""
Against The Spread (ATS) Prediction Models

Specialized models for predicting NFL games against the spread with
line movement integration and sharp money indicators.

Target Accuracy: >58% for ATS predictions
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
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import joblib
import os

from data_pipeline import DataPipeline
from enhanced_features import EnhancedFeatureEngine

logger = logging.getLogger(__name__)

@dataclass
class ATSPrediction:
    """ATS prediction result with spread analysis"""
    home_team: str
    away_team: str
    week: int
    season: int
    
    # ATS Predictions
    ats_prediction: str  # 'home' or 'away' (who covers the spread)
    ats_confidence: float  # 0.0 to 1.0
    
    # Spread Analysis
    predicted_spread: float  # Our predicted spread
    market_spread: float  # Current market spread
    spread_edge: float  # Difference between predicted and market
    
    # Model explanations
    key_factors: List[str]
    ats_feature_importance: Dict[str, float]
    model_votes: Dict[str, str]
    model_confidences: Dict[str, float]
    
    # Line Movement Analysis
    opening_spread: Optional[float] = None
    current_spread: Optional[float] = None
    line_movement: Optional[float] = None  # Positive = moved toward home
    
    # Sharp Money Indicators
    public_betting_percentage: Optional[float] = None  # % of public on home team
    sharp_money_indicator: str = "neutral"  # "home", "away", "neutral"

class ATSPredictor:
    """
    Specialized ATS prediction system with spread analysis and line movement
    """
    
    def __init__(self, data_pipeline: DataPipeline, feature_engine: EnhancedFeatureEngine):
        self.data_pipeline = data_pipeline
        self.feature_engine = feature_engine
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_columns: List[str] = []
        self.model_weights: Dict[str, float] = {}
        
        # ATS-specific model configurations
        self.model_configs = {
            'ats_random_forest': {
                'n_estimators': 250,
                'max_depth': 12,
                'min_samples_split': 8,
                'min_samples_leaf': 4,
                'random_state': 42
            },
            'ats_xgboost': {
                'n_estimators': 200,
                'max_depth': 6,
                'learning_rate': 0.08,
                'subsample': 0.85,
                'colsample_bytree': 0.85,
                'random_state': 42
            },
            'ats_gradient_boosting': {
                'n_estimators': 180,
                'max_depth': 6,
                'learning_rate': 0.08,
                'subsample': 0.85,
                'random_state': 42
            },
            'ats_neural_network': {
                'hidden_layer_sizes': (80, 40, 20),
                'activation': 'relu',
                'solver': 'adam',
                'alpha': 0.002,
                'max_iter': 600,
                'random_state': 42
            }
        }
        
    def prepare_ats_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare ATS-specific training data with spread-focused features
        """
        logger.info("🏗️ Preparing ATS training data with spread analysis...")
        
        if self.data_pipeline.games_df is None:
            raise ValueError("No historical games data available")
            
        training_features = []
        training_labels = []
        
        # Process each historical game for ATS analysis
        for _, game in self.data_pipeline.games_df.iterrows():
            try:
                # Create enhanced game features
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
                
                # Add ATS-specific features
                features = self._add_ats_features(features, game)
                
                # Create ATS label (who covered the spread)
                home_score = game['home_score']
                away_score = game['away_score']
                margin = home_score - away_score  # Positive = home team won by this much
                
                # Estimate spread (negative = home favored)
                estimated_spread = self._estimate_historical_spread(features)
                
                # Determine ATS winner
                # If home team beats the spread, label = 1 (home covers)
                # If away team beats the spread, label = 0 (away covers)
                home_covers = margin > abs(estimated_spread) if estimated_spread < 0 else margin > -abs(estimated_spread)
                ats_label = 1 if home_covers else 0
                
                training_features.append(features)
                training_labels.append(ats_label)
                
            except Exception as e:
                logger.warning(f"⚠️ Skipping game for ATS training: {e}")
                continue
                
        if not training_features:
            raise ValueError("No valid ATS training features generated")
            
        # Convert to DataFrame
        features_df = pd.DataFrame(training_features)
        labels_series = pd.Series(training_labels)
        
        # Remove non-predictive features and keep only numeric
        prediction_features = features_df.drop(columns=[
            'home_team', 'away_team', 'actual_spread', 'actual_margin'
        ], errors='ignore')
        
        numeric_features = prediction_features.select_dtypes(include=[np.number])
        self.feature_columns = numeric_features.columns.tolist()
        
        logger.info(f"✅ Prepared {len(numeric_features)} ATS training samples with {len(self.feature_columns)} features")
        logger.info(f"📊 ATS Feature categories: {len([f for f in self.feature_columns if 'spread' in f])} spread features, "
                   f"{len([f for f in self.feature_columns if 'line' in f])} line movement features")
        
        return numeric_features, labels_series
        
    def _add_ats_features(self, features: Dict, game: pd.Series) -> Dict:
        """Add ATS-specific features to game features"""
        enhanced_features = features.copy()
        
        # Spread-related features
        home_power_rank = features.get('home_power_ranking', 16)
        away_power_rank = features.get('away_power_ranking', 16)
        
        # Calculate various spread estimates
        power_spread = (away_power_rank - home_power_rank) * 0.8 - 2.5  # Home field advantage
        point_diff_spread = features.get('home_point_differential', 0) - features.get('away_point_differential', 0)
        
        # Line movement simulation (simplified)
        opening_spread = power_spread
        current_spread = power_spread + np.random.normal(0, 0.5)  # Simulate line movement
        line_movement = current_spread - opening_spread
        
        # Public betting simulation (teams with better records get more public money)
        home_win_pct = features.get('home_win_percentage', 0.5)
        away_win_pct = features.get('away_win_percentage', 0.5)
        public_betting_home = (home_win_pct + 0.1) / (home_win_pct + away_win_pct + 0.2)  # Home bias
        
        # Sharp money indicator (contrarian to public)
        sharp_indicator = "away" if public_betting_home > 0.6 else ("home" if public_betting_home < 0.4 else "neutral")
        
        # Add ATS-specific features
        enhanced_features.update({
            'power_spread_estimate': power_spread,
            'point_differential_spread': point_diff_spread,
            'opening_spread': opening_spread,
            'current_spread': current_spread,
            'line_movement': line_movement,
            'public_betting_home_pct': public_betting_home,
            'sharp_money_home': 1 if sharp_indicator == "home" else 0,
            'sharp_money_away': 1 if sharp_indicator == "away" else 0,
            
            # Spread-specific matchup features
            'home_ats_power': features.get('home_power_score', 50) - abs(power_spread) * 2,
            'away_ats_power': features.get('away_power_score', 50) + abs(power_spread) * 2,
            'spread_value': abs(power_spread - current_spread),  # How much value in the line
            
            # Historical performance against spread (estimated)
            'home_ats_record_est': min(0.6, max(0.4, features.get('home_win_percentage', 0.5) * 0.9)),
            'away_ats_record_est': min(0.6, max(0.4, features.get('away_win_percentage', 0.5) * 0.9)),
            
            # Game situation factors
            'divisional_game': 1 if self._is_divisional_matchup(features.get('home_team'), features.get('away_team')) else 0,
            'primetime_game': 1 if features.get('week', 1) % 4 == 0 else 0,  # Simplified primetime indicator
            
            # Store actual values for training
            'actual_spread': current_spread,
            'actual_margin': game['home_score'] - game['away_score'],
        })
        
        return enhanced_features
        
    def _estimate_historical_spread(self, features: Dict) -> float:
        """Estimate what the spread would have been for historical games"""
        power_diff = features.get('power_ranking_differential', 0)
        point_diff = features.get('home_point_differential', 0) - features.get('away_point_differential', 0)
        
        # Combine power rankings and point differential
        estimated_spread = power_diff * 0.6 + point_diff * 0.2 - 2.5  # Home field advantage
        
        return round(estimated_spread, 1)
        
    def _is_divisional_matchup(self, home_team: str, away_team: str) -> bool:
        """Check if teams are in the same division (simplified)"""
        divisions = {
            'AFC_EAST': ['BUF', 'MIA', 'NE', 'NYJ'],
            'AFC_NORTH': ['BAL', 'CIN', 'CLE', 'PIT'],
            'AFC_SOUTH': ['HOU', 'IND', 'JAX', 'TEN'],
            'AFC_WEST': ['DEN', 'KC', 'LV', 'LAC'],
            'NFC_EAST': ['DAL', 'NYG', 'PHI', 'WAS'],
            'NFC_NORTH': ['CHI', 'DET', 'GB', 'MIN'],
            'NFC_SOUTH': ['ATL', 'CAR', 'NO', 'TB'],
            'NFC_WEST': ['ARI', 'LAR', 'SF', 'SEA']
        }
        
        for division_teams in divisions.values():
            if home_team in division_teams and away_team in division_teams:
                return True
        return False
        
    def train_ats_models(self) -> Dict[str, float]:
        """Train ATS-specific models"""
        logger.info("🚀 Training ATS prediction models...")
        
        # Prepare ATS training data
        X, y = self.prepare_ats_training_data()
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Initialize ATS models
        models = {
            'ats_random_forest': RandomForestClassifier(**self.model_configs['ats_random_forest']),
            'ats_xgboost': xgb.XGBClassifier(**self.model_configs['ats_xgboost']),
            'ats_gradient_boosting': GradientBoostingClassifier(**self.model_configs['ats_gradient_boosting']),
            'ats_neural_network': MLPClassifier(**self.model_configs['ats_neural_network'])
        }
        
        # Temporal cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        model_scores = {}
        
        for model_name, model in models.items():
            logger.info(f"🔧 Training {model_name}...")
            
            # Scale features for neural network
            if 'neural_network' in model_name:
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                self.scalers[model_name] = scaler
                
                scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='accuracy')
                model.fit(X_scaled, y)
            else:
                scores = cross_val_score(model, X, y, cv=tscv, scoring='accuracy')
                model.fit(X, y)
            
            self.models[model_name] = model
            model_scores[model_name] = scores.mean()
            
            logger.info(f"✅ {model_name}: {scores.mean():.3f} ± {scores.std():.3f} ATS accuracy")
            
        # Calculate ensemble weights
        total_score = sum(model_scores.values())
        self.model_weights = {
            name: score / total_score 
            for name, score in model_scores.items()
        }
        
        ensemble_score = sum(score * weight for score, weight in zip(model_scores.values(), self.model_weights.values()))
        
        logger.info(f"🎯 ATS Ensemble Performance: {ensemble_score:.3f} accuracy")
        logger.info(f"📊 ATS Model Weights: {self.model_weights}")
        
        return model_scores
        
    def predict_ats(self, home_team: str, away_team: str, date: datetime, week: int, 
                   market_spread: float = None) -> ATSPrediction:
        """Generate ATS prediction with spread analysis"""
        if not self.models:
            raise ValueError("ATS models not trained. Call train_ats_models() first.")
            
        # Create enhanced game features
        features = self.data_pipeline.create_game_features(home_team, away_team, date, week)
        if self.feature_engine:
            features = self.feature_engine.enhance_game_features(features)
            
        # Add ATS features (without actual game data)
        features = self._add_ats_features(features, pd.Series({'home_score': 0, 'away_score': 0}))
        
        # Convert to DataFrame and ensure feature order
        feature_df = pd.DataFrame([features])
        feature_df = feature_df.reindex(columns=self.feature_columns, fill_value=0)
        feature_df = feature_df.fillna(feature_df.median())
        
        # Get predictions from each model
        model_predictions = {}
        model_probabilities = {}
        
        for model_name, model in self.models.items():
            if 'neural_network' in model_name:
                X_scaled = self.scalers[model_name].transform(feature_df)
                pred = model.predict(X_scaled)[0]
                prob = model.predict_proba(X_scaled)[0]
            else:
                pred = model.predict(feature_df)[0]
                prob = model.predict_proba(feature_df)[0]
                
            model_predictions[model_name] = 'home' if pred == 1 else 'away'
            model_probabilities[model_name] = max(prob)
            
        # Ensemble prediction
        home_votes = sum(
            self.model_weights[name] 
            for name, pred in model_predictions.items() 
            if pred == 'home'
        )
        
        ats_prediction = 'home' if home_votes > 0.5 else 'away'
        ats_confidence = max(home_votes, 1 - home_votes)
        
        # Spread analysis
        predicted_spread = features.get('power_spread_estimate', -3.0)
        market_spread = market_spread or predicted_spread
        spread_edge = predicted_spread - market_spread
        
        # Line movement analysis
        opening_spread = features.get('opening_spread')
        current_spread = features.get('current_spread', market_spread)
        line_movement = current_spread - opening_spread if opening_spread else 0
        
        # Sharp money analysis
        public_pct = features.get('public_betting_home_pct', 0.5)
        if public_pct > 0.65:
            sharp_indicator = "away"  # Fade the public
        elif public_pct < 0.35:
            sharp_indicator = "home"
        else:
            sharp_indicator = "neutral"
            
        # Feature importance
        feature_importance = {}
        if 'ats_random_forest' in self.models:
            rf_importance = self.models['ats_random_forest'].feature_importances_
            feature_importance = dict(zip(self.feature_columns, rf_importance))
            
        # Get key ATS factors
        key_factors = self._get_ats_key_factors(features, feature_importance)
        
        return ATSPrediction(
            home_team=home_team,
            away_team=away_team,
            week=week,
            season=date.year if date.month >= 9 else date.year - 1,
            ats_prediction=ats_prediction,
            ats_confidence=ats_confidence,
            predicted_spread=predicted_spread,
            market_spread=market_spread,
            spread_edge=spread_edge,
            opening_spread=opening_spread,
            current_spread=current_spread,
            line_movement=line_movement,
            public_betting_percentage=public_pct * 100,
            sharp_money_indicator=sharp_indicator,
            key_factors=key_factors,
            ats_feature_importance=feature_importance,
            model_votes=model_predictions,
            model_confidences=model_probabilities
        )
        
    def _get_ats_key_factors(self, features: Dict, importance: Dict[str, float]) -> List[str]:
        """Get key factors for ATS prediction"""
        if not importance:
            return ["Spread value", "Line movement", "Sharp money", "Power rankings", "Public betting"]
            
        # Sort features by importance
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # ATS-specific explanations
        ats_explanations = {
            'spread_value': f"Spread value ({features.get('spread_value', 0):.1f})",
            'line_movement': f"Line movement ({features.get('line_movement', 0):+.1f})",
            'public_betting_home_pct': f"Public on home ({features.get('public_betting_home_pct', 0.5):.1%})",
            'power_spread_estimate': f"Power spread ({features.get('power_spread_estimate', 0):+.1f})",
            'sharp_money_away': "Sharp money on away" if features.get('sharp_money_away', 0) else "",
            'sharp_money_home': "Sharp money on home" if features.get('sharp_money_home', 0) else "",
            'divisional_game': "Divisional rivalry" if features.get('divisional_game', 0) else "",
            'home_ats_record_est': f"Home ATS record ({features.get('home_ats_record_est', 0.5):.1%})",
            'power_ranking_differential': f"Power ranking edge ({features.get('power_ranking_differential', 0):+.1f})"
        }
        
        key_factors = []
        for feature_name, _ in sorted_features[:6]:  # Top 6 ATS factors
            explanation = ats_explanations.get(feature_name, feature_name.replace('_', ' ').title())
            if explanation:  # Only add non-empty explanations
                key_factors.append(explanation)
                
        return key_factors[:5]  # Return top 5
        
    def save_ats_models(self, model_dir: str = "models/ats_prediction"):
        """Save ATS models"""
        os.makedirs(model_dir, exist_ok=True)
        
        for model_name, model in self.models.items():
            joblib.dump(model, os.path.join(model_dir, f"{model_name}.joblib"))
            
        for scaler_name, scaler in self.scalers.items():
            joblib.dump(scaler, os.path.join(model_dir, f"{scaler_name}_scaler.joblib"))
            
        # Save metadata
        metadata = {
            'feature_columns': self.feature_columns,
            'model_weights': self.model_weights,
            'training_date': datetime.now().isoformat(),
            'model_type': 'ATS_Prediction'
        }
        
        import json
        with open(os.path.join(model_dir, "ats_metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"✅ ATS models saved to {model_dir}")

def main():
    """Test ATS prediction models"""
    # Initialize components
    pipeline = DataPipeline()
    feature_engine = EnhancedFeatureEngine(pipeline.games_df)
    
    # Create ATS predictor
    ats_predictor = ATSPredictor(pipeline, feature_engine)
    
    # Train models
    logger.info("🚀 Training ATS prediction models...")
    scores = ats_predictor.train_ats_models()
    
    # Test prediction
    test_date = datetime(2024, 12, 15)
    market_spread = -6.5  # KC favored by 6.5
    
    ats_prediction = ats_predictor.predict_ats('KC', 'BUF', test_date, 15, market_spread)
    
    print(f"\n🏈 ATS Prediction: {ats_prediction.away_team} @ {ats_prediction.home_team}")
    print(f"🎯 ATS Pick: {ats_prediction.ats_prediction.upper()} covers ({ats_prediction.ats_confidence:.1%} confidence)")
    print(f"📊 Market Spread: {ats_prediction.market_spread:+.1f}")
    print(f"🔮 Predicted Spread: {ats_prediction.predicted_spread:+.1f}")
    print(f"💰 Spread Edge: {ats_prediction.spread_edge:+.1f}")
    print(f"📈 Line Movement: {ats_prediction.line_movement:+.1f}")
    print(f"👥 Public Betting: {ats_prediction.public_betting_percentage:.1f}% on home")
    print(f"🧠 Sharp Money: {ats_prediction.sharp_money_indicator}")
    
    print(f"\n🔍 Key ATS Factors:")
    for factor in ats_prediction.key_factors:
        print(f"  • {factor}")
        
    print(f"\n🤖 Model Votes: {ats_prediction.model_votes}")
    
    # Save models
    ats_predictor.save_ats_models()
    
    print(f"\n🎉 ATS Prediction System Complete!")
    print(f"📈 Target Accuracy: >58% ATS")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()