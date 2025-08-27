"""
Enhanced Feature Engineering for NFL Game Predictions

This module adds advanced features like power rankings, scoring offense/defense ranks,
and other sophisticated metrics to improve model accuracy.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedFeatureEngine:
    """
    Creates advanced features from basic game and team data
    """
    
    def __init__(self, games_df: Optional[pd.DataFrame] = None):
        self.games_df = games_df
        self.team_stats_cache = {}
        self.weather_cache = {}
        
        if games_df is not None:
            self.team_stats = self._calculate_team_season_stats()
            self.power_rankings = self._calculate_power_rankings()
        else:
            self.team_stats = None
            self.power_rankings = None
    
    def calculate_advanced_team_metrics(self, team_stats: Dict, opponent_stats: Dict) -> Dict:
        """Calculate advanced team performance metrics with enhanced analytics"""
        try:
            metrics = {}
            
            # Offensive efficiency metrics
            total_plays = max(team_stats.get('plays', 1), 1)
            metrics['offensive_efficiency'] = team_stats.get('total_yards', 0) / total_plays
            metrics['yards_per_play'] = team_stats.get('total_yards', 0) / total_plays
            metrics['points_per_play'] = team_stats.get('points', 0) / total_plays
            
            # Advanced passing metrics
            pass_attempts = max(team_stats.get('pass_attempts', 1), 1)
            metrics['completion_percentage'] = team_stats.get('completions', 0) / pass_attempts
            metrics['yards_per_attempt'] = team_stats.get('pass_yards', 0) / pass_attempts
            metrics['passer_rating'] = self._calculate_passer_rating(team_stats)
            metrics['air_yards_per_attempt'] = team_stats.get('air_yards', 0) / pass_attempts
            
            # Advanced rushing metrics
            rush_attempts = max(team_stats.get('rush_attempts', 1), 1)
            metrics['yards_per_carry'] = team_stats.get('rush_yards', 0) / rush_attempts
            metrics['rush_success_rate'] = team_stats.get('successful_rushes', 0) / rush_attempts
            metrics['explosive_rush_rate'] = team_stats.get('rushes_10plus', 0) / rush_attempts
            
            # Defensive efficiency metrics
            opp_plays = max(opponent_stats.get('plays', 1), 1)
            metrics['defensive_efficiency'] = opponent_stats.get('total_yards', 0) / opp_plays
            metrics['points_allowed_per_play'] = opponent_stats.get('points', 0) / opp_plays
            metrics['sack_rate'] = team_stats.get('sacks', 0) / max(opponent_stats.get('pass_attempts', 1), 1)
            
            # Turnover and penalty metrics
            metrics['turnover_differential'] = (
                team_stats.get('takeaways', 0) - team_stats.get('turnovers', 0)
            )
            metrics['penalty_yards_per_game'] = team_stats.get('penalty_yards', 0)
            metrics['time_of_possession'] = team_stats.get('time_of_possession', 30.0)
            
            # Situational efficiency
            metrics['red_zone_efficiency'] = (
                team_stats.get('red_zone_tds', 0) / max(team_stats.get('red_zone_attempts', 1), 1)
            )
            metrics['third_down_rate'] = (
                team_stats.get('third_down_conversions', 0) / max(team_stats.get('third_down_attempts', 1), 1)
            )
            metrics['fourth_down_rate'] = (
                team_stats.get('fourth_down_conversions', 0) / max(team_stats.get('fourth_down_attempts', 1), 1)
            )
            
            # Advanced situational metrics
            metrics['goal_to_go_efficiency'] = (
                team_stats.get('goal_to_go_tds', 0) / max(team_stats.get('goal_to_go_attempts', 1), 1)
            )
            metrics['two_minute_efficiency'] = team_stats.get('two_minute_drives_success', 0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating advanced team metrics: {e}")
            return {}
    
    def _calculate_passer_rating(self, stats: Dict) -> float:
        """Calculate NFL passer rating"""
        try:
            attempts = max(stats.get('pass_attempts', 1), 1)
            completions = stats.get('completions', 0)
            yards = stats.get('pass_yards', 0)
            tds = stats.get('pass_tds', 0)
            ints = stats.get('interceptions', 0)
            
            # NFL passer rating formula
            a = max(0, min(2.375, (completions / attempts - 0.3) * 5))
            b = max(0, min(2.375, (yards / attempts - 3) * 0.25))
            c = max(0, min(2.375, (tds / attempts) * 20))
            d = max(0, min(2.375, 2.375 - (ints / attempts * 25)))
            
            return ((a + b + c + d) / 6) * 100
            
        except Exception:
            return 0.0

    def calculate_momentum_indicators(self, recent_games: List[Dict], season_stats: Dict) -> Dict:
        """Calculate team momentum and trend indicators"""
        try:
            if not recent_games:
                return {}
            
            momentum = {}
            
            # Recent performance trends (last 5 games)
            recent_5 = recent_games[-5:] if len(recent_games) >= 5 else recent_games
            
            # Win/loss momentum
            recent_wins = sum(1 for game in recent_5 if game.get('result') == 'W')
            momentum['recent_win_rate'] = recent_wins / len(recent_5)
            
            # Scoring trends
            recent_scores = [game.get('points_scored', 0) for game in recent_5]
            momentum['scoring_trend'] = self._calculate_trend(recent_scores)
            momentum['avg_recent_scoring'] = sum(recent_scores) / len(recent_scores)
            
            # Defensive trends
            recent_allowed = [game.get('points_allowed', 0) for game in recent_5]
            momentum['defensive_trend'] = self._calculate_trend(recent_allowed, inverse=True)
            momentum['avg_recent_allowed'] = sum(recent_allowed) / len(recent_allowed)
            
            # Margin trends
            recent_margins = [game.get('point_margin', 0) for game in recent_5]
            momentum['margin_trend'] = self._calculate_trend(recent_margins)
            momentum['avg_recent_margin'] = sum(recent_margins) / len(recent_margins)
            
            # Streak analysis
            momentum['current_streak'] = self._calculate_current_streak(recent_games)
            momentum['ats_streak'] = self._calculate_ats_streak(recent_games)
            
            # Performance vs expectations
            momentum['recent_ats_record'] = self._calculate_recent_ats_record(recent_5)
            momentum['recent_total_record'] = self._calculate_recent_total_record(recent_5)
            
            # Injury/roster stability
            momentum['roster_stability'] = self._calculate_roster_stability(recent_games)
            
            # Home/away momentum
            home_games = [g for g in recent_5 if g.get('location') == 'home']
            away_games = [g for g in recent_5 if g.get('location') == 'away']
            
            if home_games:
                momentum['home_momentum'] = sum(1 for g in home_games if g.get('result') == 'W') / len(home_games)
            if away_games:
                momentum['away_momentum'] = sum(1 for g in away_games if g.get('result') == 'W') / len(away_games)
            
            return momentum
            
        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float], inverse: bool = False) -> float:
        """Calculate trend direction (-1 to 1, where 1 is improving)"""
        if len(values) < 2:
            return 0.0
        
        try:
            # Simple linear regression slope
            n = len(values)
            x_sum = sum(range(n))
            y_sum = sum(values)
            xy_sum = sum(i * values[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            # Normalize slope to -1 to 1 range
            max_change = max(values) - min(values)
            if max_change > 0:
                normalized_slope = slope / max_change
                return -normalized_slope if inverse else normalized_slope
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_current_streak(self, games: List[Dict]) -> int:
        """Calculate current win/loss streak"""
        if not games:
            return 0
        
        streak = 0
        last_result = games[-1].get('result')
        
        for game in reversed(games):
            if game.get('result') == last_result:
                streak += 1 if last_result == 'W' else -1
            else:
                break
        
        return streak
    
    def _calculate_ats_streak(self, games: List[Dict]) -> int:
        """Calculate current ATS streak"""
        if not games:
            return 0
        
        streak = 0
        last_ats = games[-1].get('ats_result')
        
        for game in reversed(games):
            if game.get('ats_result') == last_ats and last_ats in ['cover', 'no_cover']:
                streak += 1 if last_ats == 'cover' else -1
            else:
                break
        
        return streak
    
    def _calculate_recent_ats_record(self, games: List[Dict]) -> Dict:
        """Calculate recent ATS record"""
        covers = sum(1 for g in games if g.get('ats_result') == 'cover')
        total = len([g for g in games if g.get('ats_result') in ['cover', 'no_cover']])
        
        return {
            'covers': covers,
            'total': total,
            'percentage': covers / max(total, 1)
        }
    
    def _calculate_recent_total_record(self, games: List[Dict]) -> Dict:
        """Calculate recent over/under record"""
        overs = sum(1 for g in games if g.get('total_result') == 'over')
        total = len([g for g in games if g.get('total_result') in ['over', 'under']])
        
        return {
            'overs': overs,
            'total': total,
            'percentage': overs / max(total, 1)
        }
    
    def _calculate_roster_stability(self, games: List[Dict]) -> float:
        """Calculate roster stability based on key player availability"""
        # Simplified calculation - in production would track actual injuries
        try:
            stability_scores = []
            for game in games:
                # Mock calculation based on game performance consistency
                expected_score = game.get('expected_points', 20)
                actual_score = game.get('points_scored', 20)
                consistency = 1 - abs(expected_score - actual_score) / max(expected_score, 1)
                stability_scores.append(max(0, min(1, consistency)))
            
            return sum(stability_scores) / len(stability_scores) if stability_scores else 0.5
            
        except Exception:
            return 0.5

    def calculate_environmental_factors(self, game_info: Dict, team_stats: Dict, opponent_stats: Dict) -> Dict:
        """Calculate environmental impact factors"""
        try:
            factors = {}
            
            # Weather impact
            weather = game_info.get('weather', {})
            factors.update(self._calculate_weather_impact(weather, team_stats, opponent_stats))
            
            # Stadium factors
            stadium = game_info.get('stadium', {})
            factors.update(self._calculate_stadium_impact(stadium, team_stats))
            
            # Travel and rest factors
            factors.update(self._calculate_travel_rest_impact(game_info, team_stats))
            
            # Prime time and crowd factors
            factors.update(self._calculate_game_situation_impact(game_info))
            
            # Divisional and rivalry factors
            factors.update(self._calculate_rivalry_impact(game_info, team_stats, opponent_stats))
            
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating environmental factors: {e}")
            return {}
    
    def _calculate_weather_impact(self, weather: Dict, team_stats: Dict, opponent_stats: Dict) -> Dict:
        """Calculate weather impact on game performance"""
        impact = {}
        
        try:
            # Temperature impact
            temp = weather.get('temperature', 70)
            impact['temperature_factor'] = self._get_temperature_factor(temp)
            
            # Wind impact
            wind_speed = weather.get('wind_speed', 0)
            impact['wind_factor'] = self._get_wind_factor(wind_speed)
            
            # Precipitation impact
            precipitation = weather.get('precipitation', 0)
            impact['precipitation_factor'] = self._get_precipitation_factor(precipitation)
            
            # Dome/outdoor adjustment
            is_dome = weather.get('is_dome', False)
            impact['dome_factor'] = 1.0 if is_dome else 0.95
            
            # Team-specific weather performance
            home_team = team_stats.get('team_name', '')
            impact['weather_advantage'] = self._get_weather_advantage(home_team, weather)
            
            # Combined weather impact
            impact['overall_weather_impact'] = (
                impact['temperature_factor'] * 
                impact['wind_factor'] * 
                impact['precipitation_factor'] * 
                impact['dome_factor']
            )
            
        except Exception as e:
            logger.error(f"Error calculating weather impact: {e}")
        
        return impact
    
    def _get_temperature_factor(self, temp: float) -> float:
        """Get temperature impact factor (1.0 = neutral)"""
        if temp < 20:  # Very cold
            return 0.85
        elif temp < 40:  # Cold
            return 0.92
        elif temp > 90:  # Very hot
            return 0.90
        elif temp > 80:  # Hot
            return 0.95
        else:  # Ideal conditions
            return 1.0
    
    def _get_wind_factor(self, wind_speed: float) -> float:
        """Get wind impact factor"""
        if wind_speed > 20:  # Very windy
            return 0.80
        elif wind_speed > 15:  # Windy
            return 0.88
        elif wind_speed > 10:  # Breezy
            return 0.95
        else:  # Calm
            return 1.0
    
    def _get_precipitation_factor(self, precipitation: float) -> float:
        """Get precipitation impact factor"""
        if precipitation > 0.5:  # Heavy rain/snow
            return 0.75
        elif precipitation > 0.1:  # Light rain/snow
            return 0.88
        else:  # No precipitation
            return 1.0
    
    def _get_weather_advantage(self, team: str, weather: Dict) -> float:
        """Get team-specific weather advantage"""
        # Cold weather teams
        cold_weather_teams = ['GB', 'BUF', 'NE', 'CHI', 'MIN', 'DET', 'CLE', 'PIT']
        # Warm weather/dome teams
        warm_weather_teams = ['MIA', 'TB', 'JAX', 'HOU', 'NO', 'ATL', 'ARI', 'LAC', 'LV']
        
        temp = weather.get('temperature', 70)
        
        if temp < 40 and team in cold_weather_teams:
            return 1.1  # 10% advantage in cold
        elif temp > 80 and team in warm_weather_teams:
            return 1.05  # 5% advantage in heat
        elif temp < 40 and team in warm_weather_teams:
            return 0.9  # 10% disadvantage in cold
        else:
            return 1.0  # Neutral
    
    def _calculate_stadium_impact(self, stadium: Dict, team_stats: Dict) -> Dict:
        """Calculate stadium-specific factors"""
        impact = {}
        
        try:
            # Altitude impact
            altitude = stadium.get('altitude', 0)
            impact['altitude_factor'] = 1.0 + (altitude / 10000) * 0.05  # 5% boost per 10k feet
            
            # Field surface impact
            surface = stadium.get('surface', 'grass')
            impact['surface_factor'] = 1.02 if surface == 'turf' else 1.0
            
            # Stadium noise/crowd impact
            capacity = stadium.get('capacity', 65000)
            noise_level = stadium.get('noise_level', 'average')  # quiet, average, loud
            
            noise_multiplier = {'quiet': 0.98, 'average': 1.0, 'loud': 1.03}[noise_level]
            impact['crowd_factor'] = noise_multiplier * (capacity / 70000)
            
            # Home field advantage
            impact['home_field_advantage'] = team_stats.get('home_win_rate', 0.5) * 0.1 + 1.0
            
        except Exception as e:
            logger.error(f"Error calculating stadium impact: {e}")
        
        return impact
    
    def _calculate_travel_rest_impact(self, game_info: Dict, team_stats: Dict) -> Dict:
        """Calculate travel and rest impact"""
        impact = {}
        
        try:
            # Days of rest
            days_rest = game_info.get('days_rest', 7)
            if days_rest < 4:  # Short rest
                impact['rest_factor'] = 0.92
            elif days_rest > 10:  # Long rest
                impact['rest_factor'] = 1.03
            else:  # Normal rest
                impact['rest_factor'] = 1.0
            
            # Travel distance
            travel_distance = game_info.get('travel_distance', 0)
            if travel_distance > 2000:  # Cross-country
                impact['travel_factor'] = 0.95
            elif travel_distance > 1000:  # Long distance
                impact['travel_factor'] = 0.98
            else:  # Short/no travel
                impact['travel_factor'] = 1.0
            
            # Time zone changes
            timezone_change = game_info.get('timezone_change', 0)
            impact['timezone_factor'] = 1.0 - abs(timezone_change) * 0.02
            
            # Back-to-back away games
            consecutive_away = game_info.get('consecutive_away_games', 0)
            impact['consecutive_away_factor'] = 1.0 - (consecutive_away * 0.01)
            
        except Exception as e:
            logger.error(f"Error calculating travel/rest impact: {e}")
        
        return impact
    
    def _calculate_game_situation_impact(self, game_info: Dict) -> Dict:
        """Calculate game situation factors"""
        impact = {}
        
        try:
            # Prime time games
            is_primetime = game_info.get('is_primetime', False)
            impact['primetime_factor'] = 1.02 if is_primetime else 1.0
            
            # Playoff implications
            playoff_implications = game_info.get('playoff_implications', 'none')
            playoff_multipliers = {
                'none': 1.0,
                'low': 1.01,
                'medium': 1.03,
                'high': 1.05,
                'elimination': 1.08
            }
            impact['playoff_factor'] = playoff_multipliers.get(playoff_implications, 1.0)
            
            # Revenge game
            is_revenge = game_info.get('is_revenge_game', False)
            impact['revenge_factor'] = 1.02 if is_revenge else 1.0
            
            # Nationally televised
            is_national_tv = game_info.get('is_national_tv', False)
            impact['national_tv_factor'] = 1.01 if is_national_tv else 1.0
            
        except Exception as e:
            logger.error(f"Error calculating game situation impact: {e}")
        
        return impact
    
    def _calculate_rivalry_impact(self, game_info: Dict, team_stats: Dict, opponent_stats: Dict) -> Dict:
        """Calculate rivalry and divisional factors"""
        impact = {}
        
        try:
            # Divisional game
            is_divisional = game_info.get('is_divisional', False)
            impact['divisional_factor'] = 0.98 if is_divisional else 1.0  # Divisional games often closer
            
            # Historical rivalry
            rivalry_level = game_info.get('rivalry_level', 'none')
            rivalry_multipliers = {
                'none': 1.0,
                'mild': 1.01,
                'moderate': 1.02,
                'intense': 1.04
            }
            impact['rivalry_factor'] = rivalry_multipliers.get(rivalry_level, 1.0)
            
            # Head-to-head history
            h2h_record = game_info.get('head_to_head_record', {'wins': 0, 'losses': 0})
            total_games = h2h_record['wins'] + h2h_record['losses']
            if total_games > 0:
                h2h_advantage = (h2h_record['wins'] - h2h_record['losses']) / total_games
                impact['h2h_factor'] = 1.0 + (h2h_advantage * 0.02)  # Small historical advantage
            else:
                impact['h2h_factor'] = 1.0
            
        except Exception as e:
            logger.error(f"Error calculating rivalry impact: {e}")
        
        return impact

    # Placeholder methods for compatibility with existing code
    def _calculate_team_season_stats(self) -> pd.DataFrame:
        """Calculate comprehensive team statistics from game data"""
        if self.games_df is None:
            return pd.DataFrame()
        
        logger.info("🧮 Calculating team season statistics...")
        # Implementation would go here for full historical analysis
        return pd.DataFrame()
    
    def _calculate_power_rankings(self) -> Dict:
        """Calculate power rankings for teams"""
        if self.games_df is None:
            return {}
        
        logger.info("📊 Calculating power rankings...")
        # Implementation would go here for power rankings
        return {}