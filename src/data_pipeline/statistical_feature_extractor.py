"""
Statistical Feature Extractor
Advanced analytics and feature engineering for NFL prediction models
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import mutual_info_regression
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class FeatureSet:
    """Container for extracted features"""
    basic_features: Dict[str, float] = field(default_factory=dict)
    advanced_features: Dict[str, float] = field(default_factory=dict)
    situational_features: Dict[str, float] = field(default_factory=dict)
    momentum_features: Dict[str, float] = field(default_factory=dict)
    meta_features: Dict[str, Any] = field(default_factory=dict)
    
    def get_all_features(self) -> Dict[str, float]:
        """Get all numeric features as a single dictionary"""
        all_features = {}
        all_features.update(self.basic_features)
        all_features.update(self.advanced_features)
        all_features.update(self.situational_features)
        all_features.update(self.momentum_features)
        
        # Add numeric meta features
        for key, value in self.meta_features.items():
            if isinstance(value, (int, float)):
                all_features[f"meta_{key}"] = float(value)
        
        return all_features

class StatisticalFeatureExtractor:
    """Extracts and engineers advanced statistical features for prediction models"""
    
    def __init__(self):
        self.scalers = {}
        self.feature_importance_cache = {}
        
        # Configuration
        self.lookback_games = 5  # Games to look back for momentum
        self.season_weight_decay = 0.95  # Weight decay for older games
        
    def extract_game_features(
        self, 
        game_data: Dict[str, Any], 
        team_history: Optional[Dict[str, List[Dict]]] = None,
        opponent_history: Optional[Dict[str, List[Dict]]] = None
    ) -> FeatureSet:
        """Extract comprehensive features for a game"""
        try:
            features = FeatureSet()
            
            # Basic game features
            features.basic_features = self._extract_basic_features(game_data)
            
            # Advanced statistical features
            features.advanced_features = self._extract_advanced_features(
                game_data, team_history, opponent_history
            )
            
            # Situational features
            features.situational_features = self._extract_situational_features(game_data)
            
            # Momentum features
            if team_history and opponent_history:
                features.momentum_features = self._extract_momentum_features(
                    team_history, opponent_history
                )
            
            # Meta features
            features.meta_features = self._extract_meta_features(game_data)
            
            logger.debug(f"Extracted {len(features.get_all_features())} features for game")
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return FeatureSet()
    
    def _extract_basic_features(self, game_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract basic game features"""
        features = {}
        
        try:
            # Spread and total features
            spread = game_data.get('spread', 0)
            total = game_data.get('total', 45)
            
            features['spread'] = spread
            features['total'] = total
            features['spread_abs'] = abs(spread)
            features['total_normalized'] = (total - 45) / 10  # Normalize around average
            
            # Home field advantage
            features['is_home'] = 1.0
            features['is_away'] = 0.0
            
            # Week and season context
            week = game_data.get('week', 1)
            season = game_data.get('season', 2024)
            
            features['week'] = week
            features['week_normalized'] = week / 18.0
            features['is_early_season'] = 1.0 if week <= 4 else 0.0
            features['is_mid_season'] = 1.0 if 5 <= week <= 13 else 0.0
            features['is_late_season'] = 1.0 if week >= 14 else 0.0
            
            # Divisional game indicator
            features['is_divisional'] = 1.0 if game_data.get('is_divisional', False) else 0.0
            
            return features
            
        except Exception as e:
            logger.error(f"Basic features extraction error: {e}")
            return {}
    
    def _extract_advanced_features(
        self, 
        game_data: Dict[str, Any],
        team_history: Optional[Dict[str, List[Dict]]],
        opponent_history: Optional[Dict[str, List[Dict]]]
    ) -> Dict[str, float]:
        """Extract advanced statistical features"""
        features = {}
        
        try:
            if not team_history or not opponent_history:
                return features
            
            home_team = game_data.get('home_team', '')
            away_team = game_data.get('away_team', '')
            
            home_history = team_history.get(home_team, [])
            away_history = opponent_history.get(away_team, [])
            
            # Team performance metrics
            features.update(self._calculate_team_metrics(home_history, 'home'))
            features.update(self._calculate_team_metrics(away_history, 'away'))
            
            # Head-to-head features
            features.update(self._calculate_h2h_features(home_history, away_history))
            
            # Strength of schedule
            features.update(self._calculate_sos_features(home_history, away_history))
            
            # Advanced efficiency metrics
            features.update(self._calculate_efficiency_metrics(home_history, away_history))
            
            return features
            
        except Exception as e:
            logger.error(f"Advanced features extraction error: {e}")
            return {}
    
    def _calculate_team_metrics(self, team_history: List[Dict], prefix: str) -> Dict[str, float]:
        """Calculate team performance metrics"""
        metrics = {}
        
        try:
            if not team_history:
                return metrics
            
            recent_games = team_history[-self.lookback_games:]
            
            # Basic averages
            scores_for = [g.get('points_for', 0) for g in recent_games]
            scores_against = [g.get('points_against', 0) for g in recent_games]
            
            if scores_for:
                metrics[f'{prefix}_avg_points_for'] = np.mean(scores_for)
                metrics[f'{prefix}_avg_points_against'] = np.mean(scores_against)
                metrics[f'{prefix}_point_differential'] = np.mean(scores_for) - np.mean(scores_against)
                
                # Variability metrics
                metrics[f'{prefix}_points_for_std'] = np.std(scores_for)
                metrics[f'{prefix}_points_against_std'] = np.std(scores_against)
                
                # Trend metrics
                if len(scores_for) > 2:
                    # Linear trend
                    x = np.arange(len(scores_for))
                    for_trend = np.polyfit(x, scores_for, 1)[0]
                    against_trend = np.polyfit(x, scores_against, 1)[0]
                    
                    metrics[f'{prefix}_scoring_trend'] = for_trend
                    metrics[f'{prefix}_defense_trend'] = -against_trend  # Negative because lower is better
            
            # Win rate and recent form
            wins = sum(1 for g in recent_games if g.get('result') == 'W')
            metrics[f'{prefix}_win_rate'] = wins / len(recent_games) if recent_games else 0.0
            
            # Home/away splits
            home_games = [g for g in recent_games if g.get('location') == 'home']
            away_games = [g for g in recent_games if g.get('location') == 'away']
            
            if home_games:
                home_scores = [g.get('points_for', 0) for g in home_games]
                metrics[f'{prefix}_home_avg_points'] = np.mean(home_scores)
            
            if away_games:
                away_scores = [g.get('points_for', 0) for g in away_games]
                metrics[f'{prefix}_away_avg_points'] = np.mean(away_scores)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Team metrics calculation error: {e}")
            return {}
    
    def _calculate_h2h_features(self, home_history: List[Dict], away_history: List[Dict]) -> Dict[str, float]:
        """Calculate head-to-head features"""
        features = {}
        
        try:
            # Recent meetings (simplified - would need actual H2H data)
            features['h2h_games_played'] = 0  # Placeholder
            features['home_team_h2h_wins'] = 0  # Placeholder
            features['away_team_h2h_wins'] = 0  # Placeholder
            features['h2h_avg_total'] = 45.0  # Placeholder
            
            # Style matchup indicators
            home_offense_avg = np.mean([g.get('points_for', 0) for g in home_history[-5:]])
            away_defense_avg = np.mean([g.get('points_against', 0) for g in away_history[-5:]])
            
            away_offense_avg = np.mean([g.get('points_for', 0) for g in away_history[-5:]])
            home_defense_avg = np.mean([g.get('points_against', 0) for g in home_history[-5:]])
            
            features['home_offense_vs_away_defense'] = home_offense_avg - away_defense_avg
            features['away_offense_vs_home_defense'] = away_offense_avg - home_defense_avg
            
            return features
            
        except Exception as e:
            logger.error(f"H2H features calculation error: {e}")
            return {}
    
    def _calculate_sos_features(self, home_history: List[Dict], away_history: List[Dict]) -> Dict[str, float]:
        """Calculate strength of schedule features"""
        features = {}
        
        try:
            # Opponent strength metrics (simplified)
            home_opp_strength = []
            away_opp_strength = []
            
            for game in home_history[-self.lookback_games:]:
                # Would calculate actual opponent strength
                opp_strength = game.get('opponent_strength', 0.5)
                home_opp_strength.append(opp_strength)
            
            for game in away_history[-self.lookback_games:]:
                opp_strength = game.get('opponent_strength', 0.5)
                away_opp_strength.append(opp_strength)
            
            if home_opp_strength:
                features['home_sos'] = np.mean(home_opp_strength)
                features['home_sos_variance'] = np.var(home_opp_strength)
            
            if away_opp_strength:
                features['away_sos'] = np.mean(away_opp_strength)
                features['away_sos_variance'] = np.var(away_opp_strength)
            
            # Relative strength of schedule
            if home_opp_strength and away_opp_strength:
                features['sos_differential'] = np.mean(home_opp_strength) - np.mean(away_opp_strength)
            
            return features
            
        except Exception as e:
            logger.error(f"SOS features calculation error: {e}")
            return {}
    
    def _calculate_efficiency_metrics(self, home_history: List[Dict], away_history: List[Dict]) -> Dict[str, float]:
        """Calculate advanced efficiency metrics"""
        features = {}
        
        try:
            # Yards per play, red zone efficiency, etc.
            for team, history, prefix in [('home', home_history, 'home'), ('away', away_history, 'away')]:
                recent_games = history[-self.lookback_games:]
                
                if recent_games:
                    # Offensive efficiency
                    yards_per_play = [g.get('yards_per_play', 5.0) for g in recent_games]
                    red_zone_pct = [g.get('red_zone_pct', 0.5) for g in recent_games]
                    third_down_pct = [g.get('third_down_pct', 0.4) for g in recent_games]
                    
                    features[f'{prefix}_yards_per_play'] = np.mean(yards_per_play)
                    features[f'{prefix}_red_zone_efficiency'] = np.mean(red_zone_pct)
                    features[f'{prefix}_third_down_efficiency'] = np.mean(third_down_pct)
                    
                    # Defensive efficiency
                    opp_yards_per_play = [g.get('opp_yards_per_play', 5.0) for g in recent_games]
                    opp_red_zone_pct = [g.get('opp_red_zone_pct', 0.5) for g in recent_games]
                    
                    features[f'{prefix}_def_yards_per_play'] = np.mean(opp_yards_per_play)
                    features[f'{prefix}_def_red_zone_pct'] = np.mean(opp_red_zone_pct)
                    
                    # Turnover metrics
                    turnovers_forced = [g.get('turnovers_forced', 1) for g in recent_games]
                    turnovers_committed = [g.get('turnovers_committed', 1) for g in recent_games]
                    
                    features[f'{prefix}_turnovers_forced'] = np.mean(turnovers_forced)
                    features[f'{prefix}_turnovers_committed'] = np.mean(turnovers_committed)
                    features[f'{prefix}_turnover_differential'] = np.mean(turnovers_forced) - np.mean(turnovers_committed)
            
            return features
            
        except Exception as e:
            logger.error(f"Efficiency metrics calculation error: {e}")
            return {}
    
    def _extract_situational_features(self, game_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract situational features"""
        features = {}
        
        try:
            # Weather features
            weather = game_data.get('weather', {})
            
            features['temperature'] = weather.get('temperature', 70)
            features['wind_speed'] = weather.get('wind_speed', 5)
            features['precipitation'] = weather.get('precipitation', 0)
            features['humidity'] = weather.get('humidity', 50)
            
            # Weather impact indicators
            features['cold_weather'] = 1.0 if weather.get('temperature', 70) < 35 else 0.0
            features['hot_weather'] = 1.0 if weather.get('temperature', 70) > 85 else 0.0
            features['high_wind'] = 1.0 if weather.get('wind_speed', 5) > 15 else 0.0
            features['precipitation_present'] = 1.0 if weather.get('precipitation', 0) > 0.1 else 0.0
            
            # Dome/outdoor indicator
            features['is_dome'] = 0.0  # Would need venue data
            
            # Injury impact
            injuries = game_data.get('injuries', {})
            home_injuries = injuries.get('home', [])
            away_injuries = injuries.get('away', [])
            
            features['home_key_injuries'] = sum(
                1 for inj in home_injuries 
                if inj.get('is_starter', False) and inj.get('severity') in ['out', 'doubtful']
            )
            features['away_key_injuries'] = sum(
                1 for inj in away_injuries 
                if inj.get('is_starter', False) and inj.get('severity') in ['out', 'doubtful']
            )
            
            # Rest and travel
            travel_data = game_data.get('travel', {})
            features['home_rest_days'] = travel_data.get('home_rest_days', 7)
            features['away_rest_days'] = travel_data.get('away_rest_days', 7)
            features['travel_distance'] = travel_data.get('travel_distance', 500)
            features['rest_advantage'] = travel_data.get('home_rest_days', 7) - travel_data.get('away_rest_days', 7)
            
            # Game timing
            game_date = game_data.get('game_date')
            if isinstance(game_date, datetime):
                features['hour_of_day'] = game_date.hour
                features['day_of_week'] = game_date.weekday()
                features['is_prime_time'] = 1.0 if game_date.hour >= 20 else 0.0
                features['is_early_game'] = 1.0 if game_date.hour <= 13 else 0.0
            
            return features
            
        except Exception as e:
            logger.error(f"Situational features extraction error: {e}")
            return {}
    
    def _extract_momentum_features(
        self,
        team_history: Dict[str, List[Dict]],
        opponent_history: Dict[str, List[Dict]]
    ) -> Dict[str, float]:
        """Extract momentum and trend features"""
        features = {}
        
        try:
            # For each team, calculate momentum metrics
            for team_type, history in [('home', team_history), ('away', opponent_history)]:
                team_key = list(history.keys())[0] if history else None
                if not team_key:
                    continue
                
                team_games = history[team_key][-self.lookback_games:]
                
                if len(team_games) >= 3:
                    # Scoring momentum
                    recent_scores = [g.get('points_for', 0) for g in team_games]
                    features[f'{team_type}_scoring_momentum'] = self._calculate_momentum(recent_scores)
                    
                    # Defensive momentum
                    recent_defense = [g.get('points_against', 0) for g in team_games]
                    features[f'{team_type}_defensive_momentum'] = -self._calculate_momentum(recent_defense)
                    
                    # Win/loss momentum
                    recent_results = [1 if g.get('result') == 'W' else 0 for g in team_games]
                    features[f'{team_type}_win_momentum'] = self._calculate_momentum(recent_results)
                    
                    # Cover momentum (ATS)
                    ats_results = [g.get('ats_result', 0) for g in team_games]
                    if any(r != 0 for r in ats_results):
                        features[f'{team_type}_ats_momentum'] = self._calculate_momentum(ats_results)
            
            return features
            
        except Exception as e:
            logger.error(f"Momentum features extraction error: {e}")
            return {}
    
    def _calculate_momentum(self, values: List[float]) -> float:
        """Calculate momentum score using weighted trend"""
        try:
            if len(values) < 2:
                return 0.0
            
            # Weight recent games more heavily
            weights = [self.season_weight_decay ** (len(values) - i - 1) for i in range(len(values))]
            
            # Calculate weighted linear trend
            x = np.arange(len(values))
            weighted_slope = np.polyfit(x, values, 1, w=weights)[0]
            
            # Normalize momentum score
            return np.tanh(weighted_slope)  # Returns value between -1 and 1
            
        except Exception as e:
            logger.error(f"Momentum calculation error: {e}")
            return 0.0
    
    def _extract_meta_features(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meta features for tracking and analysis"""
        meta = {}
        
        try:
            meta['game_id'] = game_data.get('game_id', '')
            meta['week'] = game_data.get('week', 0)
            meta['season'] = game_data.get('season', 0)
            meta['home_team'] = game_data.get('home_team', '')
            meta['away_team'] = game_data.get('away_team', '')
            meta['extraction_timestamp'] = datetime.now().isoformat()
            
            # Data quality indicators
            meta['has_weather_data'] = bool(game_data.get('weather'))
            meta['has_injury_data'] = bool(game_data.get('injuries'))
            meta['has_betting_data'] = bool(game_data.get('betting_data'))
            meta['data_completeness_score'] = (
                int(meta['has_weather_data']) +
                int(meta['has_injury_data']) +
                int(meta['has_betting_data'])
            ) / 3.0
            
            return meta
            
        except Exception as e:
            logger.error(f"Meta features extraction error: {e}")
            return {}
    
    def calculate_feature_importance(
        self,
        features_list: List[FeatureSet],
        target_values: List[float],
        method: str = 'mutual_info'
    ) -> Dict[str, float]:
        """Calculate feature importance scores"""
        try:
            if not features_list or not target_values:
                return {}
            
            # Convert features to matrix
            feature_names = list(features_list[0].get_all_features().keys())
            feature_matrix = []
            
            for feature_set in features_list:
                feature_vector = [feature_set.get_all_features().get(name, 0.0) for name in feature_names]
                feature_matrix.append(feature_vector)
            
            feature_matrix = np.array(feature_matrix)
            target_array = np.array(target_values)
            
            # Calculate importance based on method
            if method == 'mutual_info':
                importance_scores = mutual_info_regression(feature_matrix, target_array)
            else:
                # Correlation-based importance
                importance_scores = [
                    abs(np.corrcoef(feature_matrix[:, i], target_array)[0, 1])
                    for i in range(feature_matrix.shape[1])
                ]
            
            # Create importance dictionary
            importance_dict = dict(zip(feature_names, importance_scores))
            
            # Cache for future use
            self.feature_importance_cache[method] = importance_dict
            
            return importance_dict
            
        except Exception as e:
            logger.error(f"Feature importance calculation error: {e}")
            return {}
    
    def get_feature_summary(self, feature_set: FeatureSet) -> Dict[str, Any]:
        """Get summary statistics of extracted features"""
        try:
            all_features = feature_set.get_all_features()
            
            return {
                'total_features': len(all_features),
                'basic_features': len(feature_set.basic_features),
                'advanced_features': len(feature_set.advanced_features),
                'situational_features': len(feature_set.situational_features),
                'momentum_features': len(feature_set.momentum_features),
                'feature_ranges': {
                    'min_value': min(all_features.values()) if all_features else 0,
                    'max_value': max(all_features.values()) if all_features else 0,
                    'mean_value': np.mean(list(all_features.values())) if all_features else 0
                },
                'meta_info': feature_set.meta_features
            }
            
        except Exception as e:
            logger.error(f"Feature summary error: {e}")
            return {}

# Usage example
def test_feature_extractor():
    """Test the statistical feature extractor"""
    try:
        extractor = StatisticalFeatureExtractor()
        
        # Mock game data
        game_data = {
            'game_id': 'test_game',
            'home_team': 'KC',
            'away_team': 'BUF',
            'week': 1,
            'season': 2024,
            'spread': -3.5,
            'total': 52.5,
            'weather': {
                'temperature': 72,
                'wind_speed': 8,
                'precipitation': 0
            },
            'injuries': {
                'home': [],
                'away': [{'is_starter': True, 'severity': 'questionable'}]
            }
        }
        
        # Extract features
        features = extractor.extract_game_features(game_data)
        
        print(f"Extracted features:")
        print(f"  Basic: {len(features.basic_features)}")
        print(f"  Advanced: {len(features.advanced_features)}")
        print(f"  Situational: {len(features.situational_features)}")
        print(f"  Total numeric: {len(features.get_all_features())}")
        
        # Feature summary
        summary = extractor.get_feature_summary(features)
        print(f"  Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"Feature extractor test failed: {e}")
        return False

if __name__ == "__main__":
    test_feature_extractor()