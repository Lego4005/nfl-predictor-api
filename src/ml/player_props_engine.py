"""
Player Props Prediction Engine

Advanced player feature engineering and prop-specific prediction models
for individual player performance predictions with edge calculations.

Target Accuracy: >57% for prop predictions
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import joblib
import os

from data_pipeline import DataPipeline
from enhanced_features import EnhancedFeatureEngine

logger = logging.getLogger(__name__)

@dataclass
class PlayerPropPrediction:
    """Player prop prediction with edge analysis"""
    player_name: str
    team: str
    opponent: str
    position: str
    week: int
    season: int
    
    # Prop predictions
    passing_yards: float
    rushing_yards: float
    receiving_yards: float
    passing_tds: float
    rushing_tds: float
    receiving_tds: float
    receptions: float
    
    # Confidence and edge analysis
    prop_confidences: Dict[str, float]  # Confidence for each prop
    market_lines: Dict[str, float]  # Market betting lines
    prop_edges: Dict[str, float]  # Edge over market lines
    
    # Key factors
    key_factors: List[str]
    matchup_analysis: Dict[str, Any]
    usage_metrics: Dict[str, float]
    
    # Model details
    model_predictions: Dict[str, Dict[str, float]]  # Model name -> prop -> value

@dataclass
class PlayerFeatures:
    """Enhanced player features for prop predictions"""
    player_name: str
    team: str
    position: str
    season: int
    
    # Season averages
    games_played: int
    passing_yards_avg: float = 0.0
    rushing_yards_avg: float = 0.0
    receiving_yards_avg: float = 0.0
    passing_tds_avg: float = 0.0
    rushing_tds_avg: float = 0.0
    receiving_tds_avg: float = 0.0
    receptions_avg: float = 0.0
    targets_avg: float = 0.0
    
    # Recent form (last 5 games)
    passing_yards_last_5: float = 0.0
    rushing_yards_last_5: float = 0.0
    receiving_yards_last_5: float = 0.0
    passing_tds_last_5: float = 0.0
    rushing_tds_last_5: float = 0.0
    receiving_tds_last_5: float = 0.0
    receptions_last_5: float = 0.0
    
    # Advanced metrics
    target_share: float = 0.0  # % of team targets
    air_yards_share: float = 0.0  # % of team air yards
    red_zone_targets: float = 0.0  # Red zone usage
    snap_percentage: float = 0.0  # % of snaps played
    
    # Matchup-specific
    vs_opponent_avg: float = 0.0  # Historical vs this opponent
    vs_position_rank: float = 0.0  # Opponent rank vs this position
    home_away_split: float = 0.0  # Home vs away performance
    
    # Situational
    weather_impact: float = 0.0  # Weather sensitivity
    primetime_boost: float = 0.0  # Primetime performance boost
    divisional_impact: float = 0.0  # Divisional game impact
    
    # Team context
    team_pace: float = 0.0  # Team plays per game
    team_pass_rate: float = 0.0  # Team pass play percentage
    projected_game_script: float = 0.0  # Expected game flow

class PlayerPropsEngine:
    """
    Advanced player props prediction engine with sophisticated feature engineering
    """
    
    def __init__(self, data_pipeline: DataPipeline, feature_engine: EnhancedFeatureEngine):
        self.data_pipeline = data_pipeline
        self.feature_engine = feature_engine
        self.player_features_cache: Dict[str, PlayerFeatures] = {}
        
        # Prop-specific models
        self.prop_models: Dict[str, Dict[str, Any]] = {}
        self.prop_scalers: Dict[str, StandardScaler] = {}
        self.prop_feature_columns: Dict[str, List[str]] = {}
        
        # Props we predict
        self.prop_types = [
            'passing_yards', 'rushing_yards', 'receiving_yards',
            'passing_tds', 'rushing_tds', 'receiving_tds', 'receptions'
        ]
        
        # Model configurations for each prop type
        self.model_configs = {
            'random_forest': {
                'n_estimators': 200,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 3,
                'random_state': 42
            },
            'xgboost': {
                'n_estimators': 150,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 150,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'random_state': 42
            },
            'neural_network': {
                'hidden_layer_sizes': (100, 50),
                'activation': 'relu',
                'solver': 'adam',
                'alpha': 0.001,
                'max_iter': 500,
                'random_state': 42
            }
        }
        
    def create_player_features(self, player_name: str, team: str, opponent: str, 
                             date: datetime, week: int) -> PlayerFeatures:
        """Create comprehensive player features for prop predictions"""
        
        # Get player's historical data
        if self.data_pipeline.players_df is None:
            logger.warning("No player data available")
            return self._create_default_player_features(player_name, team)
            
        player_data = self.data_pipeline.players_df[
            self.data_pipeline.players_df['player_name'] == player_name
        ]
        
        if len(player_data) == 0:
            logger.warning(f"No data found for player: {player_name}")
            return self._create_default_player_features(player_name, team)
            
        # Get season and recent performance
        season = date.year if date.month >= 9 else date.year - 1
        season_data = player_data[player_data['season'] == season]
        
        if len(season_data) == 0:
            logger.warning(f"No {season} data for player: {player_name}")
            return self._create_default_player_features(player_name, team)
            
        # Calculate features
        features = PlayerFeatures(
            player_name=player_name,
            team=team,
            position=season_data.iloc[0]['position'],
            season=season,
            games_played=len(season_data)
        )
        
        # Season averages
        features.passing_yards_avg = season_data['passing_yards'].mean()
        features.rushing_yards_avg = season_data['rushing_yards'].mean()
        features.receiving_yards_avg = season_data['receiving_yards'].mean()
        features.passing_tds_avg = season_data['passing_tds'].mean()
        features.rushing_tds_avg = season_data['rushing_tds'].mean()
        features.receiving_tds_avg = season_data['receiving_tds'].mean()
        features.receptions_avg = season_data['receptions'].mean()
        features.targets_avg = season_data['targets'].mean()
        
        # Recent form (last 5 games)
        recent_data = season_data.tail(5)
        features.passing_yards_last_5 = recent_data['passing_yards'].mean()
        features.rushing_yards_last_5 = recent_data['rushing_yards'].mean()
        features.receiving_yards_last_5 = recent_data['receiving_yards'].mean()
        features.passing_tds_last_5 = recent_data['passing_tds'].mean()
        features.rushing_tds_last_5 = recent_data['rushing_tds'].mean()
        features.receiving_tds_last_5 = recent_data['receiving_tds'].mean()
        features.receptions_last_5 = recent_data['receptions'].mean()
        
        # Advanced metrics (calculated/estimated)
        features = self._add_advanced_player_metrics(features, season_data, team, opponent)
        
        # Matchup analysis
        features = self._add_matchup_analysis(features, opponent, date)
        
        # Situational factors
        features = self._add_situational_factors(features, date, week)
        
        return features
        
    def _create_default_player_features(self, player_name: str, team: str) -> PlayerFeatures:
        """Create default features when no data is available"""
        return PlayerFeatures(
            player_name=player_name,
            team=team,
            position="UNKNOWN",
            season=2024,
            games_played=0
        )
        
    def _add_advanced_player_metrics(self, features: PlayerFeatures, season_data: pd.DataFrame,
                                   team: str, opponent: str) -> PlayerFeatures:
        """Add advanced player metrics"""
        
        # Target share (estimated based on receptions and team context)
        if features.position in ['WR', 'TE', 'RB']:
            team_games = len(season_data)
            if team_games > 0:
                # Estimate target share based on receptions
                features.target_share = min(0.35, features.targets_avg / 35.0)  # Assume ~35 team targets/game
                features.air_yards_share = features.target_share * 0.8  # Rough estimate
                
        # Red zone usage (estimated)
        if features.receiving_tds_avg > 0 or features.rushing_tds_avg > 0:
            features.red_zone_targets = (features.receiving_tds_avg + features.rushing_tds_avg) * 3
            
        # Snap percentage (estimated based on production)
        if features.position == 'QB':
            features.snap_percentage = 0.95  # QBs play most snaps
        elif features.position in ['WR', 'TE']:
            # Estimate based on targets
            features.snap_percentage = min(0.85, 0.4 + (features.targets_avg / 50))
        elif features.position == 'RB':
            # Estimate based on touches
            touches = features.rushing_yards_avg / 4.5 + features.receptions_avg  # ~4.5 yards per carry
            features.snap_percentage = min(0.75, 0.3 + (touches / 25))
        else:
            features.snap_percentage = 0.5
            
        return features
        
    def _add_matchup_analysis(self, features: PlayerFeatures, opponent: str, date: datetime) -> PlayerFeatures:
        """Add opponent-specific matchup analysis"""
        
        # Historical performance vs opponent (simplified)
        if self.data_pipeline.players_df is not None:
            player_vs_opp = self.data_pipeline.players_df[
                (self.data_pipeline.players_df['player_name'] == features.player_name) &
                (self.data_pipeline.players_df['opponent'] == opponent)
            ]
            
            if len(player_vs_opp) > 0:
                # Average performance vs this opponent
                if features.position == 'QB':
                    features.vs_opponent_avg = player_vs_opp['passing_yards'].mean()
                elif features.position == 'RB':
                    features.vs_opponent_avg = player_vs_opp['rushing_yards'].mean()
                else:  # WR, TE
                    features.vs_opponent_avg = player_vs_opp['receiving_yards'].mean()
            else:
                features.vs_opponent_avg = 0.0
                
        # Opponent defensive ranking vs position (estimated)
        if self.feature_engine and self.feature_engine.team_stats is not None:
            opp_stats = self.feature_engine.team_stats[
                (self.feature_engine.team_stats['team'] == opponent) &
                (self.feature_engine.team_stats['season'] == features.season)
            ]
            
            if len(opp_stats) > 0:
                opp_def_rank = opp_stats.iloc[0].get('points_allowed_per_game', 20)
                # Convert to position-specific ranking (simplified)
                features.vs_position_rank = min(32, max(1, opp_def_rank))
            else:
                features.vs_position_rank = 16  # Average
        else:
            features.vs_position_rank = 16
            
        return features
        
    def _add_situational_factors(self, features: PlayerFeatures, date: datetime, week: int) -> PlayerFeatures:
        """Add situational factors that affect performance"""
        
        # Home/away split (simplified - assume home games are better)
        features.home_away_split = 1.05  # 5% boost for home games (simplified)
        
        # Weather impact (position-dependent)
        if features.position in ['QB', 'WR', 'TE']:
            features.weather_impact = 0.95  # Passing affected by weather
        else:
            features.weather_impact = 1.0  # Running less affected
            
        # Primetime boost (some players perform better in primetime)
        if week % 4 == 0:  # Simplified primetime indicator
            features.primetime_boost = 1.03  # 3% boost
        else:
            features.primetime_boost = 1.0
            
        # Divisional game impact
        features.divisional_impact = 1.0  # Neutral for now
        
        # Team context (estimated)
        features.team_pace = 65.0  # Average plays per game
        features.team_pass_rate = 0.6  # 60% pass plays
        features.projected_game_script = 0.0  # Neutral game script
        
        return features
        
    def prepare_prop_training_data(self, prop_type: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data for a specific prop type"""
        logger.info(f"🏗️ Preparing {prop_type} training data...")
        
        if self.data_pipeline.players_df is None:
            raise ValueError("No player data available")
            
        training_features = []
        training_labels = []
        
        # Process player performances
        for _, player_game in self.data_pipeline.players_df.iterrows():
            try:
                # Skip if no data for this prop
                prop_value = player_game.get(prop_type, 0)
                if pd.isna(prop_value):
                    continue
                    
                # Create player features for this game
                game_date = pd.to_datetime(player_game['date'])
                features = self.create_player_features(
                    player_name=player_game['player_name'],
                    team=player_game['team'],
                    opponent=player_game['opponent'],
                    date=game_date,
                    week=player_game['week']
                )
                
                # Convert to feature dict
                feature_dict = self._player_features_to_dict(features)
                
                training_features.append(feature_dict)
                training_labels.append(prop_value)
                
            except Exception as e:
                logger.debug(f"Skipping player game: {e}")
                continue
                
        if not training_features:
            raise ValueError(f"No valid training data for {prop_type}")
            
        # Convert to DataFrame
        features_df = pd.DataFrame(training_features)
        labels_series = pd.Series(training_labels)
        
        # Keep only numeric features
        numeric_features = features_df.select_dtypes(include=[np.number])
        
        logger.info(f"✅ Prepared {len(numeric_features)} {prop_type} training samples with {len(numeric_features.columns)} features")
        
        return numeric_features, labels_series
        
    def _player_features_to_dict(self, features: PlayerFeatures) -> Dict:
        """Convert PlayerFeatures to dictionary for training"""
        return {
            'games_played': features.games_played,
            'passing_yards_avg': features.passing_yards_avg,
            'rushing_yards_avg': features.rushing_yards_avg,
            'receiving_yards_avg': features.receiving_yards_avg,
            'passing_tds_avg': features.passing_tds_avg,
            'rushing_tds_avg': features.rushing_tds_avg,
            'receiving_tds_avg': features.receiving_tds_avg,
            'receptions_avg': features.receptions_avg,
            'targets_avg': features.targets_avg,
            'passing_yards_last_5': features.passing_yards_last_5,
            'rushing_yards_last_5': features.rushing_yards_last_5,
            'receiving_yards_last_5': features.receiving_yards_last_5,
            'passing_tds_last_5': features.passing_tds_last_5,
            'rushing_tds_last_5': features.rushing_tds_last_5,
            'receiving_tds_last_5': features.receiving_tds_last_5,
            'receptions_last_5': features.receptions_last_5,
            'target_share': features.target_share,
            'air_yards_share': features.air_yards_share,
            'red_zone_targets': features.red_zone_targets,
            'snap_percentage': features.snap_percentage,
            'vs_opponent_avg': features.vs_opponent_avg,
            'vs_position_rank': features.vs_position_rank,
            'home_away_split': features.home_away_split,
            'weather_impact': features.weather_impact,
            'primetime_boost': features.primetime_boost,
            'divisional_impact': features.divisional_impact,
            'team_pace': features.team_pace,
            'team_pass_rate': features.team_pass_rate,
            'projected_game_script': features.projected_game_script,
        }
        
    def train_prop_models(self) -> Dict[str, Dict[str, float]]:
        """Train models for all prop types"""
        logger.info("🚀 Training player props models...")
        
        all_scores = {}
        
        for prop_type in self.prop_types:
            logger.info(f"🔧 Training models for {prop_type}...")
            
            try:
                # Prepare data for this prop
                X, y = self.prepare_prop_training_data(prop_type)
                
                # Handle missing values
                X = X.fillna(X.median())
                
                # Store feature columns
                self.prop_feature_columns[prop_type] = X.columns.tolist()
                
                # Initialize models for this prop
                models = {
                    'random_forest': RandomForestRegressor(**self.model_configs['random_forest']),
                    'xgboost': xgb.XGBRegressor(**self.model_configs['xgboost']),
                    'gradient_boosting': GradientBoostingRegressor(**self.model_configs['gradient_boosting']),
                    'neural_network': MLPRegressor(**self.model_configs['neural_network'])
                }
                
                # Train models
                prop_scores = {}
                prop_models = {}
                
                tscv = TimeSeriesSplit(n_splits=3)  # Fewer splits for smaller datasets
                
                for model_name, model in models.items():
                    try:
                        # Scale for neural network
                        if model_name == 'neural_network':
                            scaler = StandardScaler()
                            X_scaled = scaler.fit_transform(X)
                            self.prop_scalers[f"{prop_type}_{model_name}"] = scaler
                            
                            # Use negative MAE for scoring (higher is better)
                            scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='neg_mean_absolute_error')
                            model.fit(X_scaled, y)
                        else:
                            scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_absolute_error')
                            model.fit(X, y)
                            
                        prop_models[model_name] = model
                        prop_scores[model_name] = -scores.mean()  # Convert back to positive MAE
                        
                        logger.info(f"✅ {prop_type} {model_name}: MAE {prop_scores[model_name]:.2f}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to train {model_name} for {prop_type}: {e}")
                        continue
                        
                # Store models for this prop
                self.prop_models[prop_type] = prop_models
                all_scores[prop_type] = prop_scores
                
            except Exception as e:
                logger.error(f"❌ Failed to train models for {prop_type}: {e}")
                continue
                
        logger.info(f"🎯 Trained models for {len(all_scores)} prop types")
        return all_scores
        
    def predict_player_props(self, player_name: str, team: str, opponent: str, 
                           date: datetime, week: int) -> PlayerPropPrediction:
        """Generate comprehensive player prop predictions"""
        
        # Create player features
        features = self.create_player_features(player_name, team, opponent, date, week)
        
        # Convert to prediction format
        feature_dict = self._player_features_to_dict(features)
        
        # Generate predictions for each prop
        prop_predictions = {}
        prop_confidences = {}
        model_predictions = {}
        
        for prop_type in self.prop_types:
            if prop_type not in self.prop_models:
                continue
                
            # Get models for this prop
            models = self.prop_models[prop_type]
            feature_columns = self.prop_feature_columns.get(prop_type, [])
            
            if not models or not feature_columns:
                continue
                
            # Prepare features
            feature_df = pd.DataFrame([feature_dict])
            feature_df = feature_df.reindex(columns=feature_columns, fill_value=0)
            feature_df = feature_df.fillna(feature_df.median())
            
            # Get predictions from each model
            model_preds = {}
            for model_name, model in models.items():
                try:
                    if model_name == 'neural_network':
                        scaler_key = f"{prop_type}_{model_name}"
                        if scaler_key in self.prop_scalers:
                            X_scaled = self.prop_scalers[scaler_key].transform(feature_df)
                            pred = model.predict(X_scaled)[0]
                        else:
                            pred = model.predict(feature_df)[0]
                    else:
                        pred = model.predict(feature_df)[0]
                        
                    model_preds[model_name] = max(0, pred)  # Ensure non-negative
                    
                except Exception as e:
                    logger.warning(f"⚠️ Prediction failed for {model_name} {prop_type}: {e}")
                    continue
                    
            if model_preds:
                # Ensemble prediction (simple average)
                prop_predictions[prop_type] = np.mean(list(model_preds.values()))
                prop_confidences[prop_type] = 0.7  # Default confidence
                model_predictions[prop_type] = model_preds
                
        # Create prediction object
        prediction = PlayerPropPrediction(
            player_name=player_name,
            team=team,
            opponent=opponent,
            position=features.position,
            week=week,
            season=features.season,
            passing_yards=prop_predictions.get('passing_yards', 0),
            rushing_yards=prop_predictions.get('rushing_yards', 0),
            receiving_yards=prop_predictions.get('receiving_yards', 0),
            passing_tds=prop_predictions.get('passing_tds', 0),
            rushing_tds=prop_predictions.get('rushing_tds', 0),
            receiving_tds=prop_predictions.get('receiving_tds', 0),
            receptions=prop_predictions.get('receptions', 0),
            prop_confidences=prop_confidences,
            market_lines={},  # Would be populated with actual market data
            prop_edges={},    # Would be calculated vs market lines
            key_factors=self._get_player_key_factors(features),
            matchup_analysis=self._get_matchup_analysis(features, opponent),
            usage_metrics=self._get_usage_metrics(features),
            model_predictions=model_predictions
        )
        
        return prediction
        
    def _get_player_key_factors(self, features: PlayerFeatures) -> List[str]:
        """Get key factors affecting player performance"""
        factors = []
        
        if features.target_share > 0.2:
            factors.append(f"High target share ({features.target_share:.1%})")
            
        if features.snap_percentage > 0.7:
            factors.append(f"High snap count ({features.snap_percentage:.1%})")
            
        if features.vs_position_rank <= 10:
            factors.append("Favorable matchup (weak defense)")
        elif features.vs_position_rank >= 25:
            factors.append("Tough matchup (strong defense)")
            
        if features.red_zone_targets > 2:
            factors.append("Red zone target")
            
        if features.primetime_boost > 1.0:
            factors.append("Primetime game boost")
            
        return factors[:5]  # Top 5 factors
        
    def _get_matchup_analysis(self, features: PlayerFeatures, opponent: str) -> Dict[str, Any]:
        """Get detailed matchup analysis"""
        return {
            'opponent_def_rank': features.vs_position_rank,
            'historical_vs_opponent': features.vs_opponent_avg,
            'matchup_rating': 'favorable' if features.vs_position_rank > 20 else 'tough' if features.vs_position_rank < 10 else 'neutral'
        }
        
    def _get_usage_metrics(self, features: PlayerFeatures) -> Dict[str, float]:
        """Get player usage metrics"""
        return {
            'target_share': features.target_share,
            'snap_percentage': features.snap_percentage,
            'red_zone_usage': features.red_zone_targets,
            'air_yards_share': features.air_yards_share
        }

def main():
    """Test player props engine"""
    # Initialize components
    pipeline = DataPipeline()
    feature_engine = EnhancedFeatureEngine(pipeline.games_df)
    
    # Create props engine
    props_engine = PlayerPropsEngine(pipeline, feature_engine)
    
    # Train models
    logger.info("🚀 Training player props models...")
    scores = props_engine.train_prop_models()
    
    # Test prediction
    test_date = datetime(2024, 12, 15)
    
    # Test with a few players
    test_players = [
        ("Josh Allen", "BUF"),
        ("Patrick Mahomes", "KC"),
        ("Tyreek Hill", "MIA")
    ]
    
    for player_name, team in test_players:
        try:
            prediction = props_engine.predict_player_props(
                player_name, team, "KC" if team != "KC" else "BUF", test_date, 15
            )
            
            print(f"\n🏈 {prediction.player_name} ({prediction.position}) - {prediction.team} vs {prediction.opponent}")
            print(f"📊 Passing Yards: {prediction.passing_yards:.1f}")
            print(f"🏃 Rushing Yards: {prediction.rushing_yards:.1f}")
            print(f"🎯 Receiving Yards: {prediction.receiving_yards:.1f}")
            print(f"🏈 Passing TDs: {prediction.passing_tds:.1f}")
            print(f"🏃 Rushing TDs: {prediction.rushing_tds:.1f}")
            print(f"🎯 Receiving TDs: {prediction.receiving_tds:.1f}")
            print(f"👐 Receptions: {prediction.receptions:.1f}")
            
            print(f"\n🔍 Key Factors:")
            for factor in prediction.key_factors:
                print(f"  • {factor}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to predict for {player_name}: {e}")
            
    print(f"\n🎉 Player Props Engine Complete!")
    print(f"📈 Target Accuracy: >57% for props")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()