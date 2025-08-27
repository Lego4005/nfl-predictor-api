"""
Player Props Prediction Engine
Advanced ML models for individual player performance predictions with edge calculations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PlayerPropsEngine:
    """
    Advanced player props prediction engine with edge calculations
    Target accuracy: 57% for prop predictions, 68% for fantasy
    """
    
    def __init__(self):
        # Prop type configurations
        self.prop_configs = {
            'passing_yards': {
                'type': 'regression',
                'target_mae': 25.0,
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42),
                    'gradient_boost': GradientBoostingRegressor(n_estimators=100, max_depth=8, random_state=42),
                    'ridge': Ridge(alpha=1.0, random_state=42)
                }
            },
            'rushing_yards': {
                'type': 'regression',
                'target_mae': 20.0,
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42),
                    'gradient_boost': GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42)
                }
            },
            'receiving_yards': {
                'type': 'regression',
                'target_mae': 18.0,
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42),
                    'gradient_boost': GradientBoostingRegressor(n_estimators=100, max_depth=8, random_state=42)
                }
            },
            'receptions': {
                'type': 'regression',
                'target_mae': 1.5,
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
                    'ridge': Ridge(alpha=0.5, random_state=42)
                }
            },
            'touchdowns': {
                'type': 'regression',
                'target_mae': 0.8,
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42),
                    'gradient_boost': GradientBoostingRegressor(n_estimators=80, max_depth=4, random_state=42)
                }
            }
        }
        
        self.trained_models = {}
        self.scalers = {}
        self.feature_importance = {}
        
    def create_player_features(self, player_data: Dict, matchup_data: Dict, 
                              historical_data: List[Dict]) -> Dict:
        """Create comprehensive player features for ML models"""
        try:
            features = {}
            
            # Basic player info
            features.update({
                'position_qb': 1 if player_data.get('position') == 'QB' else 0,
                'position_rb': 1 if player_data.get('position') == 'RB' else 0,
                'position_wr': 1 if player_data.get('position') == 'WR' else 0,
                'position_te': 1 if player_data.get('position') == 'TE' else 0,
                'games_played': player_data.get('games_played', 0),
                'is_home': 1 if matchup_data.get('is_home', False) else 0
            })
            
            # Season averages
            features.update({
                'season_passing_yards_avg': player_data.get('season_passing_yards_avg', 0),
                'season_rushing_yards_avg': player_data.get('season_rushing_yards_avg', 0),
                'season_receiving_yards_avg': player_data.get('season_receiving_yards_avg', 0),
                'season_receptions_avg': player_data.get('season_receptions_avg', 0),
                'season_targets_avg': player_data.get('season_targets_avg', 0),
                'season_touchdowns_avg': player_data.get('season_touchdowns_avg', 0)
            })
            
            # Recent form (last 5 games)
            if historical_data and len(historical_data) >= 5:
                recent_games = historical_data[-5:]
                
                features.update({
                    'recent_passing_yards_avg': np.mean([g.get('passing_yards', 0) for g in recent_games]),
                    'recent_rushing_yards_avg': np.mean([g.get('rushing_yards', 0) for g in recent_games]),
                    'recent_receiving_yards_avg': np.mean([g.get('receiving_yards', 0) for g in recent_games]),
                    'recent_receptions_avg': np.mean([g.get('receptions', 0) for g in recent_games]),
                    'recent_targets_avg': np.mean([g.get('targets', 0) for g in recent_games]),
                    'recent_touchdowns_avg': np.mean([g.get('touchdowns', 0) for g in recent_games])
                })
                
                # Trend analysis (slope of last 5 games)
                if len(recent_games) >= 3:
                    x = np.arange(len(recent_games))
                    
                    # Calculate trends
                    passing_trend = np.polyfit(x, [g.get('passing_yards', 0) for g in recent_games], 1)[0]
                    receiving_trend = np.polyfit(x, [g.get('receiving_yards', 0) for g in recent_games], 1)[0]
                    
                    features.update({
                        'passing_yards_trend': passing_trend,
                        'receiving_yards_trend': receiving_trend,
                        'targets_trend': np.polyfit(x, [g.get('targets', 0) for g in recent_games], 1)[0]
                    })
                else:
                    features.update({
                        'passing_yards_trend': 0,
                        'receiving_yards_trend': 0,
                        'targets_trend': 0
                    })
            else:
                # No recent data available
                features.update({
                    'recent_passing_yards_avg': features['season_passing_yards_avg'],
                    'recent_rushing_yards_avg': features['season_rushing_yards_avg'],
                    'recent_receiving_yards_avg': features['season_receiving_yards_avg'],
                    'recent_receptions_avg': features['season_receptions_avg'],
                    'recent_targets_avg': features['season_targets_avg'],
                    'recent_touchdowns_avg': features['season_touchdowns_avg'],
                    'passing_yards_trend': 0,
                    'receiving_yards_trend': 0,
                    'targets_trend': 0
                })
            
            # Matchup features
            features.update({
                'opponent_pass_defense_rank': matchup_data.get('opponent_pass_defense_rank', 16),
                'opponent_rush_defense_rank': matchup_data.get('opponent_rush_defense_rank', 16),
                'opponent_pass_yards_allowed_avg': matchup_data.get('opponent_pass_yards_allowed_avg', 250),
                'opponent_rush_yards_allowed_avg': matchup_data.get('opponent_rush_yards_allowed_avg', 120),
                'opponent_points_allowed_avg': matchup_data.get('opponent_points_allowed_avg', 22),
                'game_total_line': matchup_data.get('game_total_line', 45),
                'team_implied_total': matchup_data.get('team_implied_total', 22.5)
            })
            
            # Advanced matchup metrics
            features.update({
                'target_share': features['season_targets_avg'] / max(matchup_data.get('team_targets_avg', 35), 1),
                'red_zone_target_share': player_data.get('red_zone_target_share', 0.1),
                'snap_percentage': player_data.get('snap_percentage', 0.8),
                'air_yards_share': player_data.get('air_yards_share', 0.15)
            })
            
            # Environmental factors
            features.update({
                'weather_factor': matchup_data.get('weather_factor', 1.0),
                'dome_game': 1 if matchup_data.get('is_dome', False) else 0,
                'primetime_game': 1 if matchup_data.get('is_primetime', False) else 0,
                'divisional_game': 1 if matchup_data.get('is_divisional', False) else 0
            })
            
            # Usage and opportunity metrics
            features.update({
                'carries_per_game': player_data.get('carries_per_game', 0),
                'pass_attempts_per_game': player_data.get('pass_attempts_per_game', 0),
                'target_percentage': features['season_targets_avg'] / max(features['games_played'], 1),
                'goal_line_carries_avg': player_data.get('goal_line_carries_avg', 0),
                'red_zone_targets_avg': player_data.get('red_zone_targets_avg', 0)
            })
            
            return features
            
        except Exception as e:
            logger.error(f"Error creating player features: {e}")
            return {}
    
    def create_mock_player_data(self, num_players: int = 500) -> Dict:
        """Create mock player data for training"""
        np.random.seed(42)
        
        positions = ['QB', 'RB', 'WR', 'TE']
        
        players_data = []
        
        for i in range(num_players):
            position = np.random.choice(positions)
            
            # Generate position-specific stats
            if position == 'QB':
                player_data = {
                    'position': position,
                    'games_played': np.random.randint(8, 17),
                    'season_passing_yards_avg': np.random.uniform(180, 320),
                    'season_rushing_yards_avg': np.random.uniform(0, 40),
                    'season_receiving_yards_avg': 0,
                    'season_receptions_avg': 0,
                    'season_targets_avg': 0,
                    'season_touchdowns_avg': np.random.uniform(1.2, 3.5),
                    'pass_attempts_per_game': np.random.uniform(25, 45),
                    'carries_per_game': np.random.uniform(0, 8)
                }
            elif position == 'RB':
                player_data = {
                    'position': position,
                    'games_played': np.random.randint(6, 17),
                    'season_passing_yards_avg': 0,
                    'season_rushing_yards_avg': np.random.uniform(30, 120),
                    'season_receiving_yards_avg': np.random.uniform(5, 50),
                    'season_receptions_avg': np.random.uniform(1, 6),
                    'season_targets_avg': np.random.uniform(2, 8),
                    'season_touchdowns_avg': np.random.uniform(0.3, 1.8),
                    'carries_per_game': np.random.uniform(8, 25),
                    'pass_attempts_per_game': 0
                }
            elif position == 'WR':
                player_data = {
                    'position': position,
                    'games_played': np.random.randint(8, 17),
                    'season_passing_yards_avg': 0,
                    'season_rushing_yards_avg': np.random.uniform(0, 15),
                    'season_receiving_yards_avg': np.random.uniform(20, 100),
                    'season_receptions_avg': np.random.uniform(2, 8),
                    'season_targets_avg': np.random.uniform(4, 12),
                    'season_touchdowns_avg': np.random.uniform(0.2, 1.2),
                    'carries_per_game': np.random.uniform(0, 2),
                    'pass_attempts_per_game': 0
                }
            else:  # TE
                player_data = {
                    'position': position,
                    'games_played': np.random.randint(10, 17),
                    'season_passing_yards_avg': 0,
                    'season_rushing_yards_avg': np.random.uniform(0, 8),
                    'season_receiving_yards_avg': np.random.uniform(15, 70),
                    'season_receptions_avg': np.random.uniform(2, 6),
                    'season_targets_avg': np.random.uniform(3, 9),
                    'season_touchdowns_avg': np.random.uniform(0.3, 1.0),
                    'carries_per_game': np.random.uniform(0, 1),
                    'pass_attempts_per_game': 0
                }
            
            # Add common fields
            player_data.update({
                'snap_percentage': np.random.uniform(0.4, 1.0),
                'red_zone_target_share': np.random.uniform(0.05, 0.25),
                'air_yards_share': np.random.uniform(0.05, 0.3),
                'goal_line_carries_avg': np.random.uniform(0, 3),
                'red_zone_targets_avg': np.random.uniform(0, 4)
            })
            
            # Matchup data
            matchup_data = {
                'is_home': np.random.choice([True, False]),
                'opponent_pass_defense_rank': np.random.randint(1, 33),
                'opponent_rush_defense_rank': np.random.randint(1, 33),
                'opponent_pass_yards_allowed_avg': np.random.uniform(180, 280),
                'opponent_rush_yards_allowed_avg': np.random.uniform(80, 160),
                'opponent_points_allowed_avg': np.random.uniform(16, 30),
                'game_total_line': np.random.uniform(38, 55),
                'team_implied_total': np.random.uniform(18, 32),
                'team_targets_avg': np.random.uniform(30, 40),
                'weather_factor': np.random.uniform(0.85, 1.1),
                'is_dome': np.random.choice([True, False]),
                'is_primetime': np.random.choice([True, False]),
                'is_divisional': np.random.choice([True, False])
            }
            
            # Historical data (mock recent games)
            historical_data = []
            for j in range(5):
                if position == 'QB':
                    game = {
                        'passing_yards': max(0, player_data['season_passing_yards_avg'] + np.random.normal(0, 50)),
                        'rushing_yards': max(0, player_data['season_rushing_yards_avg'] + np.random.normal(0, 15)),
                        'receiving_yards': 0,
                        'receptions': 0,
                        'targets': 0,
                        'touchdowns': max(0, np.random.poisson(player_data['season_touchdowns_avg']))
                    }
                elif position == 'RB':
                    game = {
                        'passing_yards': 0,
                        'rushing_yards': max(0, player_data['season_rushing_yards_avg'] + np.random.normal(0, 30)),
                        'receiving_yards': max(0, player_data['season_receiving_yards_avg'] + np.random.normal(0, 20)),
                        'receptions': max(0, np.random.poisson(player_data['season_receptions_avg'])),
                        'targets': max(0, np.random.poisson(player_data['season_targets_avg'])),
                        'touchdowns': max(0, np.random.poisson(player_data['season_touchdowns_avg']))
                    }
                else:  # WR/TE
                    game = {
                        'passing_yards': 0,
                        'rushing_yards': max(0, player_data['season_rushing_yards_avg'] + np.random.normal(0, 10)),
                        'receiving_yards': max(0, player_data['season_receiving_yards_avg'] + np.random.normal(0, 25)),
                        'receptions': max(0, np.random.poisson(player_data['season_receptions_avg'])),
                        'targets': max(0, np.random.poisson(player_data['season_targets_avg'])),
                        'touchdowns': max(0, np.random.poisson(player_data['season_touchdowns_avg']))
                    }
                historical_data.append(game)
            
            # Create features
            features = self.create_player_features(player_data, matchup_data, historical_data)
            
            # Generate actual performance (targets)
            if position == 'QB':
                actual_performance = {
                    'passing_yards': max(0, features['recent_passing_yards_avg'] + np.random.normal(0, 40)),
                    'rushing_yards': max(0, features['recent_rushing_yards_avg'] + np.random.normal(0, 15)),
                    'receiving_yards': 0,
                    'receptions': 0,
                    'touchdowns': max(0, np.random.poisson(features['season_touchdowns_avg']))
                }
            elif position == 'RB':
                actual_performance = {
                    'passing_yards': 0,
                    'rushing_yards': max(0, features['recent_rushing_yards_avg'] + np.random.normal(0, 25)),
                    'receiving_yards': max(0, features['recent_receiving_yards_avg'] + np.random.normal(0, 15)),
                    'receptions': max(0, np.random.poisson(features['recent_receptions_avg'])),
                    'touchdowns': max(0, np.random.poisson(features['season_touchdowns_avg']))
                }
            else:  # WR/TE
                actual_performance = {
                    'passing_yards': 0,
                    'rushing_yards': max(0, features['recent_rushing_yards_avg'] + np.random.normal(0, 8)),
                    'receiving_yards': max(0, features['recent_receiving_yards_avg'] + np.random.normal(0, 20)),
                    'receptions': max(0, np.random.poisson(features['recent_receptions_avg'])),
                    'touchdowns': max(0, np.random.poisson(features['season_touchdowns_avg']))
                }
            
            players_data.append({
                'features': features,
                'targets': actual_performance,
                'position': position
            })
        
        return {
            'players': players_data,
            'feature_names': list(features.keys()) if features else [],
            'player_count': len(players_data)
        }
    
    def train_prop_models(self, training_data: Optional[Dict] = None) -> Dict:
        """Train player prop prediction models"""
        try:
            logger.info("🚀 Training player prop models...")
            
            # Use mock data if none provided
            if training_data is None:
                training_data = self.create_mock_player_data()
            
            # Convert to DataFrame format
            features_list = []
            targets_dict = {prop_type: [] for prop_type in self.prop_configs.keys()}
            
            for player in training_data['players']:
                features_list.append(player['features'])
                
                # Map targets to prop types
                targets_dict['passing_yards'].append(player['targets']['passing_yards'])
                targets_dict['rushing_yards'].append(player['targets']['rushing_yards'])
                targets_dict['receiving_yards'].append(player['targets']['receiving_yards'])
                targets_dict['receptions'].append(player['targets']['receptions'])
                targets_dict['touchdowns'].append(player['targets']['touchdowns'])
            
            features_df = pd.DataFrame(features_list)
            
            # Split data
            split_point = int(len(features_df) * 0.8)
            
            X_train = features_df.iloc[:split_point]
            X_val = features_df.iloc[split_point:]
            
            results = {}
            
            for prop_type, config in self.prop_configs.items():
                logger.info(f"🎯 Training {prop_type} models...")
                
                y_train = pd.Series(targets_dict[prop_type][:split_point])
                y_val = pd.Series(targets_dict[prop_type][split_point:])
                
                # Train models for this prop type
                prop_results = self._train_prop_type_models(
                    prop_type, config, X_train, X_val, y_train, y_val
                )
                
                # Select best model
                best_model = self._select_best_prop_model(prop_results, config)
                
                # Store results
                self.trained_models[prop_type] = best_model
                
                results[prop_type] = {
                    'best_model': best_model['name'],
                    'performance': best_model['performance'],
                    'target_met': self._check_prop_target(config, best_model['performance']),
                    'all_models': {name: result['performance'] for name, result in prop_results.items()}
                }
                
                mae = best_model['performance']['mae']
                status = "✅" if results[prop_type]['target_met'] else "❌"
                logger.info(f"  {prop_type}: MAE {mae:.2f} {status}")
            
            # Save models
            self._save_prop_models()
            
            # Generate report
            report = {
                'training_summary': {
                    'total_players': training_data['player_count'],
                    'features_count': len(training_data['feature_names']),
                    'prop_types_trained': len(results),
                    'timestamp': datetime.utcnow().isoformat()
                },
                'model_performance': {k: v['performance'] for k, v in results.items()},
                'targets_met': {k: v['target_met'] for k, v in results.items()},
                'recommendations': self._generate_prop_recommendations(results)
            }
            
            logger.info("🎉 Player prop model training completed!")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error training prop models: {e}")
            raise
    
    def _train_prop_type_models(self, prop_type: str, config: Dict, 
                               X_train: pd.DataFrame, X_val: pd.DataFrame,
                               y_train: pd.Series, y_val: pd.Series) -> Dict:
        """Train models for a specific prop type"""
        results = {}
        
        # Scale features
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        for model_name, model in config['models'].items():
            try:
                # Train model
                if 'neural' in model_name:
                    model.fit(X_train_scaled, y_train)
                    predictions = model.predict(X_val_scaled)
                else:
                    model.fit(X_train, y_train)
                    predictions = model.predict(X_val)
                
                # Calculate performance
                mae = mean_absolute_error(y_val, predictions)
                r2 = r2_score(y_val, predictions)
                
                performance = {
                    'mae': mae,
                    'r2': r2,
                    'samples': len(y_val)
                }
                
                results[model_name] = {
                    'model': model,
                    'scaler': scaler if 'neural' in model_name else None,
                    'performance': performance,
                    'predictions': predictions
                }
                
            except Exception as e:
                logger.error(f"    ❌ {model_name} training failed: {e}")
                continue
        
        return results
    
    def _select_best_prop_model(self, model_results: Dict, config: Dict) -> Dict:
        """Select the best performing model for a prop type"""
        if not model_results:
            return {'name': 'none', 'model': None, 'performance': {'error': 'No models trained'}}
        
        # Select based on MAE (lower is better)
        best_name = min(model_results.keys(), 
                       key=lambda x: model_results[x]['performance'].get('mae', float('inf')))
        
        best_result = model_results[best_name]
        
        return {
            'name': best_name,
            'model': best_result['model'],
            'scaler': best_result.get('scaler'),
            'performance': best_result['performance']
        }
    
    def _check_prop_target(self, config: Dict, performance: Dict) -> bool:
        """Check if model meets target performance"""
        if 'error' in performance:
            return False
        
        target_mae = config.get('target_mae', float('inf'))
        actual_mae = performance.get('mae', float('inf'))
        return actual_mae <= target_mae
    
    def _save_prop_models(self):
        """Save trained prop models"""
        try:
            import os
            os.makedirs('models/props', exist_ok=True)
            
            for prop_type, model_info in self.trained_models.items():
                if model_info['model'] is not None:
                    model_path = f'models/props/{prop_type}_model.joblib'
                    joblib.dump(model_info, model_path)
                    logger.info(f"💾 Saved {prop_type} model")
            
        except Exception as e:
            logger.error(f"❌ Error saving prop models: {e}")
    
    def _generate_prop_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for prop models"""
        recommendations = []
        
        targets_met = sum(1 for v in results.values() if v['target_met'])
        total_targets = len(results)
        
        if targets_met == total_targets:
            recommendations.append("🎉 All prop models meet target performance!")
        elif targets_met > 0:
            recommendations.append(f"✅ {targets_met}/{total_targets} prop models meet targets.")
            failed_props = [k for k, v in results.items() if not v['target_met']]
            recommendations.append(f"⚠️ Improve: {', '.join(failed_props)}")
        else:
            recommendations.append("❌ No prop models meet target performance.")
            recommendations.append("💡 Consider: More player data, position-specific features")
        
        return recommendations
    
    def predict_player_props(self, player_data: Dict, matchup_data: Dict, 
                           historical_data: List[Dict]) -> Dict:
        """Predict player props with edge calculations"""
        try:
            # Generate features
            features = self.create_player_features(player_data, matchup_data, historical_data)
            if not features:
                raise ValueError("Could not generate player features")
            
            # Convert to DataFrame
            feature_df = pd.DataFrame([features])
            
            predictions = {}
            
            for prop_type, model_info in self.trained_models.items():
                if model_info['model'] is None:
                    continue
                
                try:
                    # Prepare features
                    X = feature_df
                    
                    # Handle scaling
                    if model_info.get('scaler') is not None:
                        X = model_info['scaler'].transform(X)
                    
                    # Make prediction
                    model = model_info['model']
                    prediction = model.predict(X)[0]
                    
                    predictions[prop_type] = {
                        'prediction': max(0, prediction),  # Ensure non-negative
                        'model_name': model_info['name']
                    }
                    
                except Exception as e:
                    logger.error(f"Error predicting {prop_type}: {e}")
                    continue
            
            return {
                'success': True,
                'predictions': predictions,
                'player_name': player_data.get('name', 'Unknown'),
                'position': player_data.get('position', 'Unknown'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making player prop predictions: {e}")
            return {
                'success': False,
                'error': str(e),
                'player_name': player_data.get('name', 'Unknown')
            }
    
    def calculate_prop_edges(self, predictions: Dict, betting_lines: Dict) -> Dict:
        """Calculate edges over betting lines"""
        try:
            edges = {}
            
            for prop_type, prediction_data in predictions.items():
                if prop_type not in betting_lines:
                    continue
                
                prediction = prediction_data['prediction']
                line = betting_lines[prop_type]['line']
                over_odds = betting_lines[prop_type].get('over_odds', -110)
                under_odds = betting_lines[prop_type].get('under_odds', -110)
                
                # Calculate implied probabilities
                over_prob_implied = self._odds_to_probability(over_odds)
                under_prob_implied = self._odds_to_probability(under_odds)
                
                # Estimate our probability (simplified)
                # In reality, you'd want a more sophisticated approach
                std_dev = prediction * 0.25  # Assume 25% standard deviation
                our_over_prob = 1 - self._normal_cdf(line, prediction, std_dev)
                our_under_prob = self._normal_cdf(line, prediction, std_dev)
                
                # Calculate edges
                over_edge = our_over_prob - over_prob_implied
                under_edge = our_under_prob - under_prob_implied
                
                # Expected value
                over_ev = (our_over_prob * self._odds_to_payout(over_odds)) - (1 - our_over_prob)
                under_ev = (our_under_prob * self._odds_to_payout(under_odds)) - (1 - our_under_prob)
                
                edges[prop_type] = {
                    'prediction': prediction,
                    'line': line,
                    'over_edge': over_edge,
                    'under_edge': under_edge,
                    'over_ev': over_ev,
                    'under_ev': under_ev,
                    'best_bet': 'over' if over_edge > under_edge and over_edge > 0.05 else 'under' if under_edge > 0.05 else 'no_bet',
                    'confidence': max(abs(over_edge), abs(under_edge))
                }
            
            return edges
            
        except Exception as e:
            logger.error(f"Error calculating prop edges: {e}")
            return {}
    
    def _odds_to_probability(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    def _odds_to_payout(self, odds: int) -> float:
        """Convert American odds to payout multiplier"""
        if odds > 0:
            return odds / 100
        else:
            return 100 / abs(odds)
    
    def _normal_cdf(self, x: float, mean: float, std: float) -> float:
        """Approximate normal CDF"""
        from math import erf, sqrt
        return 0.5 * (1 + erf((x - mean) / (std * sqrt(2))))

# Example usage
if __name__ == "__main__":
    props_engine = PlayerPropsEngine()
    
    # Train models
    results = props_engine.train_prop_models()
    
    print("🎉 Player Props Training Results:")
    for prop_type, performance in results['model_performance'].items():
        mae = performance['mae']
        target_met = "✅" if results['targets_met'][prop_type] else "❌"
        print(f"{prop_type}: MAE {mae:.2f} {target_met}")
    
    # Test prediction
    test_player = {
        'name': 'Test Player',
        'position': 'WR',
        'games_played': 12,
        'season_receiving_yards_avg': 75.5,
        'season_receptions_avg': 5.2,
        'season_targets_avg': 8.1,
        'season_touchdowns_avg': 0.6,
        'snap_percentage': 0.85,
        'red_zone_target_share': 0.15
    }
    
    test_matchup = {
        'is_home': True,
        'opponent_pass_defense_rank': 22,
        'opponent_pass_yards_allowed_avg': 245,
        'game_total_line': 48.5,
        'team_implied_total': 25.5,
        'team_targets_avg': 35,
        'weather_factor': 1.0,
        'is_dome': True
    }
    
    test_historical = [
        {'receiving_yards': 82, 'receptions': 6, 'targets': 9, 'touchdowns': 1},
        {'receiving_yards': 65, 'receptions': 4, 'targets': 7, 'touchdowns': 0},
        {'receiving_yards': 91, 'receptions': 7, 'targets': 10, 'touchdowns': 1},
        {'receiving_yards': 58, 'receptions': 3, 'targets': 6, 'touchdowns': 0},
        {'receiving_yards': 77, 'receptions': 5, 'targets': 8, 'touchdowns': 1}
    ]
    
    prediction = props_engine.predict_player_props(test_player, test_matchup, test_historical)
    
    if prediction['success']:
        print(f"\\n🎮 Test Prediction for {prediction['player_name']} ({prediction['position']}):")
        for prop_type, pred_data in prediction['predictions'].items():
            print(f"{prop_type}: {pred_data['prediction']:.1f}")
        
        # Test edge calculation
        test_lines = {
            'receiving_yards': {'line': 72.5, 'over_odds': -110, 'under_odds': -110},
            'receptions': {'line': 4.5, 'over_odds': -115, 'under_odds': -105}
        }
        
        edges = props_engine.calculate_prop_edges(prediction['predictions'], test_lines)
        
        print("\\n💰 Edge Analysis:")
        for prop_type, edge_data in edges.items():
            print(f"{prop_type}: {edge_data['best_bet']} (confidence: {edge_data['confidence']:.3f})")
    else:
        print(f"❌ Prediction failed: {prediction['error']}")