"""
Simple Enhanced Game Models
Working version without complex dependencies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class SimpleEnhancedModels:
    """Simple enhanced game prediction models"""
    
    def __init__(self):
        # Model configurations
        self.model_configs = {
            'game_winner': {
                'type': 'classification',
                'target_accuracy': 0.62,
                'model': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            },
            'ats_prediction': {
                'type': 'classification', 
                'target_accuracy': 0.58,
                'model': LogisticRegression(max_iter=1000, random_state=42)
            }
        }
        
        self.trained_models = {}
        self.scalers = {}
        
    def create_mock_training_data(self, num_games: int = 200) -> Dict:
        """Create mock training data for testing"""
        np.random.seed(42)
        
        # Generate mock features
        features = {}
        feature_names = [
            'home_points_avg', 'away_points_avg', 'home_win_pct', 'away_win_pct',
            'point_spread', 'total_line', 'home_offensive_eff', 'away_offensive_eff',
            'home_defensive_eff', 'away_defensive_eff', 'weather_factor', 'rest_factor'
        ]
        
        for feature in feature_names:
            if 'pct' in feature or 'eff' in feature:
                features[feature] = np.random.uniform(0.3, 0.7, num_games)
            elif 'points' in feature:
                features[feature] = np.random.uniform(15, 35, num_games)
            elif 'spread' in feature:
                features[feature] = np.random.uniform(-14, 14, num_games)
            elif 'total' in feature:
                features[feature] = np.random.uniform(38, 55, num_games)
            else:
                features[feature] = np.random.uniform(0.8, 1.2, num_games)
        
        # Create DataFrame
        df = pd.DataFrame(features)
        
        # Generate targets
        # Game winner (home team wins if they have advantage)
        home_advantage = (df['home_points_avg'] - df['away_points_avg'] + 
                         df['home_win_pct'] - df['away_win_pct'] + 
                         df['home_offensive_eff'] - df['away_offensive_eff'])
        game_winner = (home_advantage > 0).astype(int)
        
        # ATS prediction (home covers if they beat spread)
        ats_margin = home_advantage * 10 + df['point_spread']
        ats_prediction = (ats_margin > 0).astype(int)
        
        return {
            'features': df,
            'targets': {
                'game_winner': game_winner,
                'ats_prediction': ats_prediction
            },
            'feature_names': feature_names,
            'game_count': num_games
        }
    
    def train_models(self, training_data: Optional[Dict] = None) -> Dict:
        """Train the enhanced models"""
        try:
            logger.info("🚀 Training enhanced models...")
            
            # Use mock data if none provided
            if training_data is None:
                training_data = self.create_mock_training_data()
            
            # Split data
            split_point = int(len(training_data['features']) * 0.8)
            
            X_train = training_data['features'].iloc[:split_point]
            X_val = training_data['features'].iloc[split_point:]
            
            results = {}
            
            for prediction_type, config in self.model_configs.items():
                logger.info(f"🎯 Training {prediction_type}...")
                
                y_train = training_data['targets'][prediction_type].iloc[:split_point]
                y_val = training_data['targets'][prediction_type].iloc[split_point:]
                
                # Scale features
                scaler = RobustScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_val_scaled = scaler.transform(X_val)
                
                # Train model
                model = config['model']
                model.fit(X_train_scaled, y_train)
                
                # Make predictions
                predictions = model.predict(X_val_scaled)
                
                # Calculate performance
                if config['type'] == 'classification':
                    accuracy = accuracy_score(y_val, predictions)
                    performance = {'accuracy': accuracy}
                    target_met = accuracy >= config['target_accuracy']
                else:
                    mae = mean_absolute_error(y_val, predictions)
                    performance = {'mae': mae}
                    target_met = mae <= config.get('target_mae', float('inf'))
                
                # Store results
                self.trained_models[prediction_type] = model
                self.scalers[prediction_type] = scaler
                
                results[prediction_type] = {
                    'performance': performance,
                    'target_met': target_met
                }
                
                main_metric = performance.get('accuracy', performance.get('mae', 'N/A'))
                status = "✅" if target_met else "❌"
                logger.info(f"  {prediction_type}: {main_metric:.3f} {status}")
            
            # Generate report
            report = {
                'training_summary': {
                    'total_games': training_data['game_count'],
                    'features_count': len(training_data['feature_names']),
                    'models_trained': len(results),
                    'timestamp': datetime.utcnow().isoformat()
                },
                'model_performance': {k: v['performance'] for k, v in results.items()},
                'targets_met': {k: v['target_met'] for k, v in results.items()}
            }
            
            logger.info("🎉 Training completed!")
            return report
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            raise
    
    def predict_game(self, game_features: Dict) -> Dict:
        """Make predictions for a single game"""
        try:
            # Convert features to DataFrame
            feature_df = pd.DataFrame([game_features])
            
            predictions = {}
            
            for prediction_type, model in self.trained_models.items():
                if prediction_type not in self.scalers:
                    continue
                
                # Scale features
                scaler = self.scalers[prediction_type]
                X_scaled = scaler.transform(feature_df)
                
                # Make prediction
                prediction = model.predict(X_scaled)[0]
                
                # Get confidence if available
                confidence = None
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(X_scaled)[0]
                    confidence = max(probabilities)
                
                predictions[prediction_type] = {
                    'prediction': prediction,
                    'confidence': confidence
                }
            
            return {
                'success': True,
                'predictions': predictions,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_models(self, path: str = 'models/simple_enhanced'):
        """Save trained models"""
        try:
            import os
            os.makedirs(path, exist_ok=True)
            
            for prediction_type, model in self.trained_models.items():
                model_path = f'{path}/{prediction_type}_model.joblib'
                scaler_path = f'{path}/{prediction_type}_scaler.joblib'
                
                joblib.dump(model, model_path)
                joblib.dump(self.scalers[prediction_type], scaler_path)
                
                logger.info(f"💾 Saved {prediction_type} model")
            
        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")

# Example usage
if __name__ == "__main__":
    models = SimpleEnhancedModels()
    
    # Train models
    results = models.train_models()
    
    print("🎉 Training Results:")
    for model_type, performance in results['model_performance'].items():
        main_metric = performance.get('accuracy', performance.get('mae', 'N/A'))
        target_met = "✅" if results['targets_met'][model_type] else "❌"
        print(f"{model_type}: {main_metric:.3f} {target_met}")
    
    # Test prediction
    test_features = {
        'home_points_avg': 28.5,
        'away_points_avg': 24.2,
        'home_win_pct': 0.65,
        'away_win_pct': 0.55,
        'point_spread': -3.5,
        'total_line': 47.5,
        'home_offensive_eff': 0.62,
        'away_offensive_eff': 0.58,
        'home_defensive_eff': 0.45,
        'away_defensive_eff': 0.52,
        'weather_factor': 0.95,
        'rest_factor': 1.0
    }
    
    prediction = models.predict_game(test_features)
    
    if prediction['success']:
        print("\\n🎮 Test Prediction:")
        for pred_type, pred_data in prediction['predictions'].items():
            print(f"{pred_type}: {pred_data['prediction']} (confidence: {pred_data.get('confidence', 'N/A')})")
    else:
        print(f"❌ Prediction failed: {prediction['error']}")