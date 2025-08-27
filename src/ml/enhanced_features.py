"""
Enhanced Feature Engineering for NFL Game Predictions

This module adds advanced features like power rankings, scoring offense/defense ranks,
and other sophisticated metrics to improve model accuracy.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class EnhancedFeatureEngine:
    """
    Creates advanced features from basic game and team data
    """
    
    def __init__(self, games_df: pd.DataFrame):
        self.games_df = games_df
        self.team_stats = self._calculate_team_season_stats()
        self.power_rankings = self._calculate_power_rankings()
        
    def _calculate_team_season_stats(self) -> pd.DataFrame:
        """Calculate comprehensive team statistics from game data"""
        logger.info("🧮 Calculating team season statistics...")
        
        team_stats = []
        
        # Get unique teams and seasons
        all_teams = set(self.games_df['home_team'].unique()) | set(self.games_df['away_team'].unique())
        seasons = self.games_df['season'].unique()
        
        for season in seasons:
            season_games = self.games_df[self.games_df['season'] == season]
            
            for team in all_teams:
                # Get team's games (home and away)
                home_games = season_games[season_games['home_team'] == team]
                away_games = season_games[season_games['away_team'] == team]
                
                if len(home_games) == 0 and len(away_games) == 0:
                    continue
                    
                # Calculate offensive stats
                home_points = home_games['home_score'].sum()
                away_points = away_games['away_score'].sum()
                total_points = home_points + away_points
                
                # Calculate defensive stats (points allowed)
                home_points_allowed = home_games['away_score'].sum()
                away_points_allowed = away_games['home_score'].sum()
                total_points_allowed = home_points_allowed + away_points_allowed
                
                # Calculate wins/losses
                home_wins = len(home_games[home_games['winner'] == team])
                away_wins = len(away_games[away_games['winner'] == team])
                total_wins = home_wins + away_wins
                
                total_games = len(home_games) + len(away_games)
                total_losses = total_games - total_wins
                
                # Advanced metrics (estimated from available data)
                points_per_game = total_points / max(total_games, 1)
                points_allowed_per_game = total_points_allowed / max(total_games, 1)
                
                # Estimate yards (rough approximation based on points)
                estimated_yards_per_game = points_per_game * 15  # ~15 yards per point
                estimated_yards_allowed_per_game = points_allowed_per_game * 15
                
                # Calculate differentials
                point_differential = points_per_game - points_allowed_per_game
                yard_differential = estimated_yards_per_game - estimated_yards_allowed_per_game
                
                # Estimate turnovers (rough approximation)
                estimated_turnovers_per_game = max(0, (25 - points_per_game) / 10)  # Better teams turn ball over less
                estimated_takeaways_per_game = max(0, (points_allowed_per_game - 15) / 8)  # Better defenses get more takeaways
                turnover_differential = estimated_takeaways_per_game - estimated_turnovers_per_game
                
                # Efficiency estimates
                third_down_percentage = min(0.5, max(0.2, points_per_game / 50))  # Rough estimate
                red_zone_percentage = min(0.8, max(0.4, points_per_game / 35))
                
                team_stat = {
                    'season': season,
                    'team': team,
                    'games': total_games,
                    'wins': total_wins,
                    'losses': total_losses,
                    'points_per_game': points_per_game,
                    'points_allowed_per_game': points_allowed_per_game,
                    'total_yards_per_game': estimated_yards_per_game,
                    'total_yards_allowed_per_game': estimated_yards_allowed_per_game,
                    'point_differential': point_differential,
                    'yard_differential': yard_differential,
                    'turnover_differential': turnover_differential,
                    'third_down_percentage': third_down_percentage,
                    'red_zone_percentage': red_zone_percentage,
                    'third_down_percentage_allowed': 1 - third_down_percentage,
                    'red_zone_percentage_allowed': 1 - red_zone_percentage,
                }
                
                team_stats.append(team_stat)
                
        team_stats_df = pd.DataFrame(team_stats)
        logger.info(f"✅ Calculated stats for {len(team_stats_df)} team-seasons")
        return team_stats_df
        
    def _calculate_power_rankings(self) -> pd.DataFrame:
        """Calculate power rankings based on team performance"""
        logger.info("⚡ Calculating power rankings...")
        
        power_rankings = []
        
        for season in self.team_stats['season'].unique():
            season_teams = self.team_stats[self.team_stats['season'] == season]
            
            for _, team_data in season_teams.iterrows():
                # Calculate power score
                win_pct = team_data['wins'] / max(team_data['games'], 1)
                point_diff = team_data['point_differential']
                yard_diff = team_data['yard_differential']
                turnover_diff = team_data['turnover_differential']
                
                # Weighted power score
                power_score = (
                    win_pct * 40 +  # 40% weight on wins
                    (point_diff / 10) * 30 +  # 30% weight on point differential
                    (yard_diff / 100) * 20 +  # 20% weight on yard differential
                    turnover_diff * 10  # 10% weight on turnover differential
                )
                
                power_ranking = {
                    'season': season,
                    'team': team_data['team'],
                    'power_score': power_score,
                    'win_percentage': win_pct,
                    'point_differential': point_diff,
                    'yard_differential': yard_diff,
                    'turnover_differential': turnover_diff,
                }
                
                power_rankings.append(power_ranking)
                
        power_rankings_df = pd.DataFrame(power_rankings)
        
        # Calculate rankings within each season
        for season in power_rankings_df['season'].unique():
            season_mask = power_rankings_df['season'] == season
            season_data = power_rankings_df[season_mask].copy()
            
            # Power rankings (1 = best)
            season_data = season_data.sort_values('power_score', ascending=False)
            power_rankings_df.loc[season_mask, 'power_rank'] = range(1, len(season_data) + 1)
            
            # Offensive rankings (points per game)
            season_teams = self.team_stats[self.team_stats['season'] == season]
            for idx, row in power_rankings_df[season_mask].iterrows():
                team_stats = season_teams[season_teams['team'] == row['team']].iloc[0]
                
                # Calculate offensive rank
                better_offense = (season_teams['points_per_game'] > team_stats['points_per_game']).sum()
                power_rankings_df.loc[idx, 'offensive_rank'] = better_offense + 1
                
                # Calculate defensive rank (lower points allowed = better)
                better_defense = (season_teams['points_allowed_per_game'] < team_stats['points_allowed_per_game']).sum()
                power_rankings_df.loc[idx, 'defensive_rank'] = better_defense + 1
                
        logger.info(f"✅ Calculated power rankings for {len(power_rankings_df)} team-seasons")
        return power_rankings_df
        
    def enhance_game_features(self, features: Dict) -> Dict:
        """Add advanced features to basic game features"""
        enhanced_features = features.copy()
        
        # Get team data
        home_team = features.get('home_team')
        away_team = features.get('away_team')
        season = features.get('season')
        
        if not all([home_team, away_team, season]):
            return enhanced_features
            
        # Get team stats
        home_stats = self.team_stats[
            (self.team_stats['team'] == home_team) & 
            (self.team_stats['season'] == season)
        ]
        away_stats = self.team_stats[
            (self.team_stats['team'] == away_team) & 
            (self.team_stats['season'] == season)
        ]
        
        # Get power rankings
        home_power = self.power_rankings[
            (self.power_rankings['team'] == home_team) & 
            (self.power_rankings['season'] == season)
        ]
        away_power = self.power_rankings[
            (self.power_rankings['team'] == away_team) & 
            (self.power_rankings['season'] == season)
        ]
        
        # Add advanced home team features
        if len(home_stats) > 0:
            home_stat = home_stats.iloc[0]
            enhanced_features.update({
                'home_scoring_offense_rank': home_power.iloc[0]['offensive_rank'] if len(home_power) > 0 else 16,
                'home_scoring_defense_rank': home_power.iloc[0]['defensive_rank'] if len(home_power) > 0 else 16,
                'home_total_offense_rank': home_power.iloc[0]['offensive_rank'] if len(home_power) > 0 else 16,
                'home_total_defense_rank': home_power.iloc[0]['defensive_rank'] if len(home_power) > 0 else 16,
                'home_power_ranking': home_power.iloc[0]['power_rank'] if len(home_power) > 0 else 16,
                'home_power_score': home_power.iloc[0]['power_score'] if len(home_power) > 0 else 50.0,
                'home_point_differential': home_stat['point_differential'],
                'home_turnover_differential': home_stat['turnover_differential'],
                'home_third_down_pct': home_stat['third_down_percentage'],
                'home_red_zone_pct': home_stat['red_zone_percentage'],
                'home_team_qbr': 85.0 + (home_stat['point_differential'] * 2),  # Estimated QBR
            })
            
        # Add advanced away team features
        if len(away_stats) > 0:
            away_stat = away_stats.iloc[0]
            enhanced_features.update({
                'away_scoring_offense_rank': away_power.iloc[0]['offensive_rank'] if len(away_power) > 0 else 16,
                'away_scoring_defense_rank': away_power.iloc[0]['defensive_rank'] if len(away_power) > 0 else 16,
                'away_total_offense_rank': away_power.iloc[0]['offensive_rank'] if len(away_power) > 0 else 16,
                'away_total_defense_rank': away_power.iloc[0]['defensive_rank'] if len(away_power) > 0 else 16,
                'away_power_ranking': away_power.iloc[0]['power_rank'] if len(away_power) > 0 else 16,
                'away_power_score': away_power.iloc[0]['power_score'] if len(away_power) > 0 else 50.0,
                'away_point_differential': away_stat['point_differential'],
                'away_turnover_differential': away_stat['turnover_differential'],
                'away_third_down_pct': away_stat['third_down_percentage'],
                'away_red_zone_pct': away_stat['red_zone_percentage'],
                'away_team_qbr': 85.0 + (away_stat['point_differential'] * 2),  # Estimated QBR
            })
            
        # Add advanced matchup features
        if len(home_power) > 0 and len(away_power) > 0:
            home_p = home_power.iloc[0]
            away_p = away_power.iloc[0]
            
            enhanced_features.update({
                'power_ranking_differential': home_p['power_rank'] - away_p['power_rank'],  # Negative = home better
                'power_score_differential': home_p['power_score'] - away_p['power_score'],
                'offensive_rank_matchup': home_p['offensive_rank'] - away_p['defensive_rank'],
                'defensive_rank_matchup': away_p['offensive_rank'] - home_p['defensive_rank'],
                'turnover_differential_gap': enhanced_features.get('home_turnover_differential', 0) - enhanced_features.get('away_turnover_differential', 0),
                'qbr_differential': enhanced_features.get('home_team_qbr', 85) - enhanced_features.get('away_team_qbr', 85),
            })
            
        # Add efficiency matchup features
        enhanced_features.update({
            'third_down_advantage': enhanced_features.get('home_third_down_pct', 0.4) - enhanced_features.get('away_third_down_pct', 0.4),
            'red_zone_advantage': enhanced_features.get('home_red_zone_pct', 0.6) - enhanced_features.get('away_red_zone_pct', 0.6),
        })
        
        return enhanced_features

def main():
    """Test the enhanced feature engine"""
    # Load games data
    games_df = pd.read_csv('data/historical/games/historical_games.csv')
    games_df['date'] = pd.to_datetime(games_df['date'])
    
    # Create enhanced feature engine
    feature_engine = EnhancedFeatureEngine(games_df)
    
    # Test with sample features
    sample_features = {
        'home_team': 'KC',
        'away_team': 'BUF',
        'season': 2024,
        'week': 13,
        'home_points_avg_last_5': 29.2,
        'away_points_avg_last_5': 28.8,
    }
    
    enhanced = feature_engine.enhance_game_features(sample_features)
    
    print("🚀 Enhanced Features Test:")
    print(f"Original features: {len(sample_features)}")
    print(f"Enhanced features: {len(enhanced)}")
    
    print("\n🔍 New Advanced Features:")
    for key, value in enhanced.items():
        if key not in sample_features:
            print(f"  {key}: {value}")
            
    print(f"\n📊 Team Stats Shape: {feature_engine.team_stats.shape}")
    print(f"⚡ Power Rankings Shape: {feature_engine.power_rankings.shape}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()