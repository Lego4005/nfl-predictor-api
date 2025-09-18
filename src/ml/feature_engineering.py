"""
Advanced Feature Engineering for NFL Predictions
Calculates EPA, success rate, DVOA-style metrics, and situational statistics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GameContext:
    """Context information for a game"""
    week: int
    season: int
    is_playoff: bool
    is_division_game: bool
    is_conference_game: bool
    is_primetime: bool
    dome_game: bool
    weather_conditions: Dict[str, Any]

class AdvancedFeatureEngineer:
    """Advanced feature engineering for NFL predictions"""

    def __init__(self):
        self.epa_values = self._initialize_epa_values()
        self.success_rate_thresholds = self._initialize_success_thresholds()

    def _initialize_epa_values(self) -> Dict[str, Dict[str, float]]:
        """Initialize Expected Points Added values by field position and down"""
        # Simplified EPA values based on historical NFL data
        epa_values = {}
        for down in range(1, 5):
            epa_values[down] = {}
            for yard_line in range(1, 101):
                if yard_line <= 20:  # Red zone
                    base_epa = 3.5 - (down - 1) * 0.8
                elif yard_line <= 50:  # Midfield
                    base_epa = 2.0 - (down - 1) * 0.6
                else:  # Own territory
                    base_epa = 0.5 - (down - 1) * 0.4

                # Adjust based on field position
                position_factor = (100 - yard_line) / 100
                epa_values[down][yard_line] = base_epa * (0.5 + position_factor)

        return epa_values

    def _initialize_success_thresholds(self) -> Dict[int, float]:
        """Initialize success rate thresholds by down"""
        return {
            1: 0.5,   # 50% of yards needed on 1st down
            2: 0.7,   # 70% of yards needed on 2nd down
            3: 1.0,   # 100% of yards needed on 3rd down
            4: 1.0    # 100% of yards needed on 4th down
        }

    def calculate_epa(self, plays_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Expected Points Added for each play"""
        plays_df = plays_df.copy()

        # Calculate EPA for each play
        epa_values = []
        for _, play in plays_df.iterrows():
            down = play.get('down', 1)
            yard_line = play.get('yard_line', 50)

            # Get base EPA
            base_epa = self.epa_values.get(down, {}).get(yard_line, 0)

            # Adjust for play outcome
            yards_gained = play.get('yards_gained', 0)
            is_touchdown = play.get('touchdown', False)
            is_turnover = play.get('turnover', False)
            is_safety = play.get('safety', False)

            if is_touchdown:
                epa = 7.0 - base_epa  # Touchdown worth 7 points
            elif is_safety:
                epa = -2.0 - base_epa  # Safety worth -2 points
            elif is_turnover:
                epa = -base_epa - 1.0  # Turnover penalty
            else:
                # Regular play - calculate based on yards gained and new field position
                new_yard_line = min(99, yard_line + yards_gained)
                new_down = min(4, down + 1) if yards_gained < play.get('yards_to_go', 10) else 1

                new_epa = self.epa_values.get(new_down, {}).get(new_yard_line, 0)
                epa = new_epa - base_epa

            epa_values.append(epa)

        plays_df['epa'] = epa_values
        return plays_df

    def calculate_success_rate(self, plays_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate success rate for plays"""
        plays_df = plays_df.copy()

        success_indicators = []
        for _, play in plays_df.iterrows():
            down = play.get('down', 1)
            yards_gained = play.get('yards_gained', 0)
            yards_to_go = play.get('yards_to_go', 10)

            threshold = self.success_rate_thresholds.get(down, 1.0)
            required_yards = yards_to_go * threshold

            # Success criteria
            is_success = (
                yards_gained >= required_yards or
                play.get('touchdown', False) or
                play.get('first_down', False)
            )

            success_indicators.append(1 if is_success else 0)

        plays_df['success'] = success_indicators
        return plays_df

    def calculate_dvoa_style_metrics(self, team_plays: pd.DataFrame, opponent_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate DVOA-style efficiency metrics"""
        metrics = {}

        # Offensive DVOA-style calculation
        if len(team_plays) > 0:
            team_epa_per_play = team_plays['epa'].mean()
            team_success_rate = team_plays['success'].mean()

            # Weight EPA and success rate
            offensive_dvoa = (team_epa_per_play * 0.6) + (team_success_rate * 0.4)
            metrics['offensive_dvoa'] = offensive_dvoa

            # Situational metrics
            red_zone_plays = team_plays[team_plays['yard_line'] <= 20]
            if len(red_zone_plays) > 0:
                metrics['red_zone_efficiency'] = red_zone_plays['success'].mean()
            else:
                metrics['red_zone_efficiency'] = 0.5

            third_down_plays = team_plays[team_plays['down'] == 3]
            if len(third_down_plays) > 0:
                metrics['third_down_rate'] = third_down_plays['success'].mean()
            else:
                metrics['third_down_rate'] = 0.3

        # Defensive DVOA-style calculation
        if len(opponent_plays) > 0:
            opp_epa_per_play = opponent_plays['epa'].mean()
            opp_success_rate = opponent_plays['success'].mean()

            # Defensive rating is inverse of opponent's offensive performance
            defensive_dvoa = -((opp_epa_per_play * 0.6) + (opp_success_rate * 0.4))
            metrics['defensive_dvoa'] = defensive_dvoa

        return metrics

    def calculate_rolling_averages(self, team_stats: pd.DataFrame, windows: List[int] = [3, 5, 10]) -> pd.DataFrame:
        """Calculate rolling averages for various metrics"""
        team_stats = team_stats.copy().sort_values(['team', 'date'])

        rolling_columns = []
        base_columns = ['points_scored', 'points_allowed', 'yards_gained', 'yards_allowed',
                       'turnovers', 'penalties', 'time_of_possession']

        for window in windows:
            for col in base_columns:
                if col in team_stats.columns:
                    new_col = f'{col}_avg_{window}'
                    team_stats[new_col] = team_stats.groupby('team')[col].transform(
                        lambda x: x.rolling(window=window, min_periods=1).mean()
                    )
                    rolling_columns.append(new_col)

        return team_stats

    def calculate_situational_stats(self, plays_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate situational statistics"""
        situational_stats = {}

        # Group by team
        for team in plays_df['team'].unique():
            team_plays = plays_df[plays_df['team'] == team]
            team_stats = {}

            # Red zone efficiency
            red_zone_plays = team_plays[team_plays['yard_line'] <= 20]
            if len(red_zone_plays) > 0:
                team_stats['red_zone_efficiency'] = red_zone_plays['success'].mean()
                team_stats['red_zone_td_rate'] = red_zone_plays['touchdown'].mean()
            else:
                team_stats['red_zone_efficiency'] = 0.5
                team_stats['red_zone_td_rate'] = 0.3

            # Third down efficiency
            third_down_plays = team_plays[team_plays['down'] == 3]
            if len(third_down_plays) > 0:
                team_stats['third_down_rate'] = third_down_plays['success'].mean()
            else:
                team_stats['third_down_rate'] = 0.35

            # Goal line efficiency (within 5 yards)
            goal_line_plays = team_plays[team_plays['yard_line'] <= 5]
            if len(goal_line_plays) > 0:
                team_stats['goal_line_efficiency'] = goal_line_plays['touchdown'].mean()
            else:
                team_stats['goal_line_efficiency'] = 0.6

            # Explosive play rate (20+ yards)
            explosive_plays = team_plays[team_plays['yards_gained'] >= 20]
            team_stats['explosive_play_rate'] = len(explosive_plays) / len(team_plays) if len(team_plays) > 0 else 0

            # Turnover differential
            turnovers_lost = team_plays['turnover'].sum()
            turnovers_gained = 0  # This would need opponent data
            team_stats['turnover_differential'] = turnovers_gained - turnovers_lost

            situational_stats[team] = team_stats

        return situational_stats

    def calculate_weather_impact(self, weather_data: Dict[str, Any]) -> float:
        """Calculate weather impact score"""
        impact_score = 0.0

        # Temperature impact
        temp = weather_data.get('temperature', 70)
        if temp < 32:
            impact_score += 0.3  # Freezing conditions
        elif temp < 50:
            impact_score += 0.2  # Cold conditions
        elif temp > 85:
            impact_score += 0.1  # Hot conditions

        # Wind impact
        wind_speed = weather_data.get('wind_speed', 0)
        if wind_speed > 20:
            impact_score += 0.4  # High winds
        elif wind_speed > 15:
            impact_score += 0.2  # Moderate winds
        elif wind_speed > 10:
            impact_score += 0.1  # Light winds

        # Precipitation impact
        precipitation = weather_data.get('precipitation_type', 'none')
        if precipitation in ['snow', 'sleet']:
            impact_score += 0.3
        elif precipitation == 'rain':
            precip_intensity = weather_data.get('precipitation_intensity', 'light')
            if precip_intensity == 'heavy':
                impact_score += 0.3
            elif precip_intensity == 'moderate':
                impact_score += 0.2
            else:
                impact_score += 0.1

        # Dome game reduces weather impact to zero
        if weather_data.get('dome_game', False):
            impact_score = 0.0

        return min(1.0, impact_score)

    def calculate_rest_and_travel_features(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate rest days and travel distance features"""
        games_df = games_df.copy()

        # Sort by team and date
        games_df = games_df.sort_values(['team', 'date'])

        # Calculate rest days
        games_df['prev_game_date'] = games_df.groupby('team')['date'].shift(1)
        games_df['rest_days'] = (games_df['date'] - games_df['prev_game_date']).dt.days
        games_df['rest_days'] = games_df['rest_days'].fillna(7)  # Default to 7 days for first game

        # Calculate travel distance (simplified - would need actual coordinates)
        games_df['travel_distance'] = 0  # Default for home games

        # For away games, estimate travel distance based on divisions/regions
        away_games = games_df[games_df['is_home'] == False]
        for idx, game in away_games.iterrows():
            # Simplified travel calculation - would need actual team locations
            home_team = game['opponent']
            away_team = game['team']

            # Estimate based on division/region (simplified)
            if self._different_divisions(home_team, away_team):
                if self._different_conferences(home_team, away_team):
                    games_df.loc[idx, 'travel_distance'] = 1500  # Cross-country
                else:
                    games_df.loc[idx, 'travel_distance'] = 800   # Cross-division
            else:
                games_df.loc[idx, 'travel_distance'] = 300      # Same division

        return games_df

    def _different_divisions(self, team1: str, team2: str) -> bool:
        """Check if teams are in different divisions (simplified)"""
        # This would need actual division mappings
        afc_east = ['BUF', 'MIA', 'NE', 'NYJ']
        afc_north = ['BAL', 'CIN', 'CLE', 'PIT']
        afc_south = ['HOU', 'IND', 'JAX', 'TEN']
        afc_west = ['DEN', 'KC', 'LV', 'LAC']

        nfc_east = ['DAL', 'NYG', 'PHI', 'WAS']
        nfc_north = ['CHI', 'DET', 'GB', 'MIN']
        nfc_south = ['ATL', 'CAR', 'NO', 'TB']
        nfc_west = ['ARI', 'LAR', 'SF', 'SEA']

        divisions = [afc_east, afc_north, afc_south, afc_west,
                    nfc_east, nfc_north, nfc_south, nfc_west]

        for division in divisions:
            if team1 in division and team2 in division:
                return False
        return True

    def _different_conferences(self, team1: str, team2: str) -> bool:
        """Check if teams are in different conferences"""
        afc_teams = ['BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT',
                    'HOU', 'IND', 'JAX', 'TEN', 'DEN', 'KC', 'LV', 'LAC']
        nfc_teams = ['DAL', 'NYG', 'PHI', 'WAS', 'CHI', 'DET', 'GB', 'MIN',
                    'ATL', 'CAR', 'NO', 'TB', 'ARI', 'LAR', 'SF', 'SEA']

        team1_afc = team1 in afc_teams
        team2_afc = team2 in afc_teams

        return team1_afc != team2_afc

    def engineer_advanced_features(self,
                                 games_df: pd.DataFrame,
                                 plays_df: Optional[pd.DataFrame] = None,
                                 weather_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Engineer all advanced features for model training"""

        logger.info("Engineering advanced features...")

        # Start with base game data
        features_df = games_df.copy()

        # Add play-by-play derived features
        if plays_df is not None:
            # Calculate EPA and success rate
            plays_df = self.calculate_epa(plays_df)
            plays_df = self.calculate_success_rate(plays_df)

            # Aggregate play-by-play stats to game level
            game_features = self._aggregate_plays_to_games(plays_df)
            features_df = features_df.merge(game_features, on=['game_id'], how='left')

        # Add rolling averages
        features_df = self.calculate_rolling_averages(features_df)

        # Add rest and travel features
        features_df = self.calculate_rest_and_travel_features(features_df)

        # Add weather features
        if weather_df is not None:
            weather_features = self._process_weather_features(weather_df)
            features_df = features_df.merge(weather_features, on=['game_id'], how='left')

        # Add derived features
        features_df = self._add_derived_features(features_df)

        # Fill missing values
        features_df = self._fill_missing_values(features_df)

        logger.info(f"Feature engineering completed. Shape: {features_df.shape}")

        return features_df

    def _aggregate_plays_to_games(self, plays_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate play-by-play statistics to game level"""

        game_stats = plays_df.groupby(['game_id', 'team']).agg({
            'epa': ['mean', 'sum', 'std'],
            'success': 'mean',
            'yards_gained': ['mean', 'sum'],
            'yards_to_go': 'mean',
            'down': lambda x: (x == 3).mean(),  # Third down percentage
            'turnover': 'sum',
            'touchdown': 'sum',
            'penalty': 'sum'
        }).reset_index()

        # Flatten column names
        game_stats.columns = [
            'game_id', 'team', 'epa_mean', 'epa_total', 'epa_std',
            'success_rate', 'yards_per_play', 'total_yards',
            'avg_yards_to_go', 'third_down_pct', 'turnovers',
            'touchdowns', 'penalties'
        ]

        return game_stats

    def _process_weather_features(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """Process weather data into features"""

        weather_features = weather_df.copy()

        # Calculate weather impact score
        weather_impact_scores = []
        for _, weather in weather_df.iterrows():
            impact_score = self.calculate_weather_impact(weather.to_dict())
            weather_impact_scores.append(impact_score)

        weather_features['weather_impact_score'] = weather_impact_scores

        # Add categorical weather features
        weather_features['is_cold'] = (weather_features['temperature'] < 40).astype(int)
        weather_features['is_windy'] = (weather_features['wind_speed'] > 15).astype(int)
        weather_features['has_precipitation'] = (weather_features['precipitation_type'] != 'none').astype(int)

        return weather_features[['game_id', 'weather_impact_score', 'is_cold', 'is_windy', 'has_precipitation']]

    def _add_derived_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features from existing data"""

        features_df = features_df.copy()

        # Team strength features
        if 'points_scored_avg_5' in features_df.columns and 'points_allowed_avg_5' in features_df.columns:
            features_df['point_differential_avg_5'] = features_df['points_scored_avg_5'] - features_df['points_allowed_avg_5']

        # Momentum features
        if 'points_scored_avg_3' in features_df.columns:
            features_df['recent_momentum'] = features_df['points_scored_avg_3'] - features_df.groupby('team')['points_scored_avg_3'].shift(1)

        # Home field advantage
        features_df['home_field_strength'] = np.where(
            features_df['is_home'],
            features_df.get('home_win_rate', 0.5) * 3,  # 3 point home field advantage
            0
        )

        # Fatigue indicator
        features_df['fatigue_factor'] = np.where(
            features_df['rest_days'] < 6,
            (6 - features_df['rest_days']) * 0.1,
            0
        )

        # Playoff implications
        features_df['playoff_race'] = np.where(
            features_df['week'] >= 14,
            1,  # Late season games have playoff implications
            0
        )

        return features_df

    def _fill_missing_values(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values with appropriate defaults"""

        features_df = features_df.copy()

        # Numeric columns - fill with median
        numeric_columns = features_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if features_df[col].isnull().any():
                median_value = features_df[col].median()
                features_df[col] = features_df[col].fillna(median_value)

        # Categorical columns - fill with mode
        categorical_columns = features_df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_columns:
            if features_df[col].isnull().any():
                mode_value = features_df[col].mode().iloc[0] if len(features_df[col].mode()) > 0 else 'Unknown'
                features_df[col] = features_df[col].fillna(mode_value)

        return features_df

    def create_model_ready_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Create final feature set ready for model training"""

        # Select key features for modeling
        model_features = [
            # Team strength metrics
            'points_scored_avg_3', 'points_scored_avg_5', 'points_scored_avg_10',
            'points_allowed_avg_3', 'points_allowed_avg_5', 'points_allowed_avg_10',
            'point_differential_avg_5',

            # Advanced metrics (if available)
            'epa_mean', 'success_rate', 'yards_per_play',
            'third_down_pct', 'red_zone_efficiency',

            # Situational factors
            'is_home', 'rest_days', 'travel_distance',
            'weather_impact_score', 'is_cold', 'is_windy',

            # Game context
            'is_division_game', 'is_conference_game', 'playoff_race',
            'week', 'fatigue_factor', 'recent_momentum',

            # Injuries and other factors
            'home_field_strength'
        ]

        # Filter to available features
        available_features = [col for col in model_features if col in features_df.columns]

        model_df = features_df[available_features + ['game_id', 'team', 'opponent']].copy()

        return model_df