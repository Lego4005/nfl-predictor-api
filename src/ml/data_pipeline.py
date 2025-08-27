"""
Data Pipeline for NFL ML Engine
Processes historical and live data into ML features for training and prediction.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TeamFeatures:
    """Team-level features for ML models"""
    team: str
    date: datetime
    week: int
    season: int
    
    # Offensive stats (last 5 games)
    points_avg_last_5: float = 0.0
    yards_avg_last_5: float = 0.0
    pass_yards_avg_last_5: float = 0.0
    rush_yards_avg_last_5: float = 0.0
    turnovers_avg_last_5: float = 0.0
    
    # Defensive stats (last 5 games)
    points_allowed_avg_last_5: float = 0.0
    yards_allowed_avg_last_5: float = 0.0
    pass_yards_allowed_avg_last_5: float = 0.0
    rush_yards_allowed_avg_last_5: float = 0.0
    turnovers_forced_avg_last_5: float = 0.0
    
    # Season performance
    wins: int = 0
    losses: int = 0
    win_percentage: float = 0.0
    
    # Recent form
    wins_last_5: int = 0
    losses_last_5: int = 0
    
    # Home/Away performance
    home_wins: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0

@dataclass
class PlayerFeatures:
    """Player-level features for ML models"""
    player_id: str
    player_name: str
    team: str
    position: str
    date: datetime
    week: int
    season: int
    
    # Season averages
    games_played: int = 0
    passing_yards_avg: float = 0.0
    rushing_yards_avg: float = 0.0
    receiving_yards_avg: float = 0.0
    receptions_avg: float = 0.0
    targets_avg: float = 0.0
    
    # Recent form (last 5 games)
    passing_yards_last_5: List[float] = None
    rushing_yards_last_5: List[float] = None
    receiving_yards_last_5: List[float] = None
    receptions_last_5: List[float] = None
    
    # Trend analysis
    passing_yards_trend: float = 0.0  # Slope of last 5 games
    receiving_yards_trend: float = 0.0
    target_share_trend: float = 0.0
    
    def __post_init__(self):
        if self.passing_yards_last_5 is None:
            self.passing_yards_last_5 = []
        if self.rushing_yards_last_5 is None:
            self.rushing_yards_last_5 = []
        if self.receiving_yards_last_5 is None:
            self.receiving_yards_last_5 = []
        if self.receptions_last_5 is None:
            self.receptions_last_5 = []

class DataPipeline:
    """
    Advanced data pipeline for processing historical and live NFL data into ML features.
    Handles feature engineering, temporal patterns, and data validation.
    """
    
    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = data_dir
        self.games_df: Optional[pd.DataFrame] = None
        self.players_df: Optional[pd.DataFrame] = None
        self.team_features_cache: Dict[str, TeamFeatures] = {}
        self.player_features_cache: Dict[str, PlayerFeatures] = {}
        
        # Load historical data
        self.load_historical_data()
        
    def load_historical_data(self):
        """Load historical data from CSV files"""
        try:
            games_path = os.path.join(self.data_dir, "games", "historical_games.csv")
            players_path = os.path.join(self.data_dir, "players", "historical_player_stats.csv")
            
            if os.path.exists(games_path):
                self.games_df = pd.read_csv(games_path)
                self.games_df['date'] = pd.to_datetime(self.games_df['date'])
                logger.info(f"✅ Loaded {len(self.games_df)} historical games")
            else:
                logger.warning(f"⚠️ Games file not found: {games_path}")
                
            if os.path.exists(players_path):
                self.players_df = pd.read_csv(players_path)
                self.players_df['date'] = pd.to_datetime(self.players_df['date'])
                logger.info(f"✅ Loaded {len(self.players_df)} historical player performances")
            else:
                logger.warning(f"⚠️ Players file not found: {players_path}")
                
        except Exception as e:
            logger.error(f"❌ Error loading historical data: {e}")
            
    def create_team_features(self, team: str, date: datetime, opponent: str = None) -> TeamFeatures:
        """Create comprehensive team features for ML models"""
        if self.games_df is None:
            logger.warning("⚠️ No games data available for team features")
            return TeamFeatures(team=team, date=date, week=1, season=2024)
            
        # Get team's historical games up to the given date
        team_games = self.games_df[
            ((self.games_df['home_team'] == team) | (self.games_df['away_team'] == team)) &
            (self.games_df['date'] < date)
        ].sort_values('date')
        
        if len(team_games) == 0:
            logger.warning(f"⚠️ No historical games found for {team}")
            return TeamFeatures(team=team, date=date, week=1, season=2024)
        
        # Calculate features
        features = TeamFeatures(
            team=team,
            date=date,
            week=self._get_week_from_date(date),
            season=self._get_season_from_date(date)
        )
        
        # Calculate offensive and defensive stats
        self._calculate_team_offensive_stats(features, team_games, team)
        self._calculate_team_defensive_stats(features, team_games, team)
        self._calculate_team_record(features, team_games, team)
        self._calculate_recent_form(features, team_games, team)
        
        # Head-to-head analysis if opponent provided
        if opponent:
            self._calculate_head_to_head_stats(features, team, opponent, date)
            
        return features
        
    def _calculate_team_offensive_stats(self, features: TeamFeatures, team_games: pd.DataFrame, team: str):
        """Calculate team offensive statistics"""
        # Get last 5 games
        recent_games = team_games.tail(5)
        
        offensive_stats = []
        for _, game in recent_games.iterrows():
            if game['home_team'] == team:
                # Team was home
                points = game['home_score']
                # For now, we'll estimate yards based on points (in real implementation, you'd have actual yards data)
                yards = points * 15  # Rough estimation
                pass_yards = yards * 0.6
                rush_yards = yards * 0.4
            else:
                # Team was away
                points = game['away_score']
                yards = points * 15
                pass_yards = yards * 0.6
                rush_yards = yards * 0.4
                
            offensive_stats.append({
                'points': points,
                'yards': yards,
                'pass_yards': pass_yards,
                'rush_yards': rush_yards
            })
        
        if offensive_stats:
            features.points_avg_last_5 = np.mean([s['points'] for s in offensive_stats])
            features.yards_avg_last_5 = np.mean([s['yards'] for s in offensive_stats])
            features.pass_yards_avg_last_5 = np.mean([s['pass_yards'] for s in offensive_stats])
            features.rush_yards_avg_last_5 = np.mean([s['rush_yards'] for s in offensive_stats])
            features.turnovers_avg_last_5 = np.random.uniform(1.0, 2.5)  # Placeholder
            
    def _calculate_team_defensive_stats(self, features: TeamFeatures, team_games: pd.DataFrame, team: str):
        """Calculate team defensive statistics"""
        recent_games = team_games.tail(5)
        
        defensive_stats = []
        for _, game in recent_games.iterrows():
            if game['home_team'] == team:
                # Team was home, opponent was away
                points_allowed = game['away_score']
            else:
                # Team was away, opponent was home
                points_allowed = game['home_score']
                
            # Estimate defensive yards allowed
            yards_allowed = points_allowed * 15
            pass_yards_allowed = yards_allowed * 0.6
            rush_yards_allowed = yards_allowed * 0.4
            
            defensive_stats.append({
                'points_allowed': points_allowed,
                'yards_allowed': yards_allowed,
                'pass_yards_allowed': pass_yards_allowed,
                'rush_yards_allowed': rush_yards_allowed
            })
        
        if defensive_stats:
            features.points_allowed_avg_last_5 = np.mean([s['points_allowed'] for s in defensive_stats])
            features.yards_allowed_avg_last_5 = np.mean([s['yards_allowed'] for s in defensive_stats])
            features.pass_yards_allowed_avg_last_5 = np.mean([s['pass_yards_allowed'] for s in defensive_stats])
            features.rush_yards_allowed_avg_last_5 = np.mean([s['rush_yards_allowed'] for s in defensive_stats])
            features.turnovers_forced_avg_last_5 = np.random.uniform(1.0, 2.5)  # Placeholder
            
    def _calculate_team_record(self, features: TeamFeatures, team_games: pd.DataFrame, team: str):
        """Calculate team win/loss record"""
        wins = 0
        losses = 0
        home_wins = 0
        home_losses = 0
        away_wins = 0
        away_losses = 0
        
        for _, game in team_games.iterrows():
            if game['winner'] == team:
                wins += 1
                if game['home_team'] == team:
                    home_wins += 1
                else:
                    away_wins += 1
            else:
                losses += 1
                if game['home_team'] == team:
                    home_losses += 1
                else:
                    away_losses += 1
        
        features.wins = wins
        features.losses = losses
        features.win_percentage = wins / (wins + losses) if (wins + losses) > 0 else 0.0
        features.home_wins = home_wins
        features.home_losses = home_losses
        features.away_wins = away_wins
        features.away_losses = away_losses
        
    def _calculate_recent_form(self, features: TeamFeatures, team_games: pd.DataFrame, team: str):
        """Calculate recent form (last 5 games)"""
        recent_games = team_games.tail(5)
        
        wins_last_5 = 0
        losses_last_5 = 0
        
        for _, game in recent_games.iterrows():
            if game['winner'] == team:
                wins_last_5 += 1
            else:
                losses_last_5 += 1
                
        features.wins_last_5 = wins_last_5
        features.losses_last_5 = losses_last_5
        
    def _calculate_head_to_head_stats(self, features: TeamFeatures, team: str, opponent: str, date: datetime):
        """Calculate head-to-head statistics between teams"""
        if self.games_df is None:
            return
            
        # Get head-to-head games
        h2h_games = self.games_df[
            (((self.games_df['home_team'] == team) & (self.games_df['away_team'] == opponent)) |
             ((self.games_df['home_team'] == opponent) & (self.games_df['away_team'] == team))) &
            (self.games_df['date'] < date)
        ].sort_values('date')
        
        # Add head-to-head features (could be expanded)
        h2h_wins = len(h2h_games[h2h_games['winner'] == team])
        h2h_total = len(h2h_games)
        
        # Store as additional attributes (could be added to TeamFeatures dataclass)
        features.h2h_wins = h2h_wins
        features.h2h_total = h2h_total
        features.h2h_win_rate = h2h_wins / h2h_total if h2h_total > 0 else 0.5
        
    def create_player_features(self, player_id: str, player_name: str, team: str, date: datetime) -> PlayerFeatures:
        """Create comprehensive player features for ML models"""
        if self.players_df is None:
            logger.warning("⚠️ No player data available for player features")
            return PlayerFeatures(
                player_id=player_id,
                player_name=player_name,
                team=team,
                position="UNKNOWN",
                date=date,
                week=1,
                season=2024
            )
            
        # Get player's historical performances up to the given date
        player_games = self.players_df[
            (self.players_df['player_id'] == player_id) &
            (self.players_df['date'] < date)
        ].sort_values('date')
        
        if len(player_games) == 0:
            logger.warning(f"⚠️ No historical games found for player {player_name}")
            return PlayerFeatures(
                player_id=player_id,
                player_name=player_name,
                team=team,
                position="UNKNOWN",
                date=date,
                week=1,
                season=2024
            )
        
        # Get position from most recent game
        position = player_games.iloc[-1]['position'] if len(player_games) > 0 else "UNKNOWN"
        
        features = PlayerFeatures(
            player_id=player_id,
            player_name=player_name,
            team=team,
            position=position,
            date=date,
            week=self._get_week_from_date(date),
            season=self._get_season_from_date(date),
            games_played=len(player_games)
        )
        
        # Calculate season averages
        self._calculate_player_season_averages(features, player_games)
        
        # Calculate recent form
        self._calculate_player_recent_form(features, player_games)
        
        # Calculate trends
        self._calculate_player_trends(features, player_games)
        
        return features
        
    def _calculate_player_season_averages(self, features: PlayerFeatures, player_games: pd.DataFrame):
        """Calculate player season averages"""
        if len(player_games) == 0:
            return
            
        features.passing_yards_avg = player_games['passing_yards'].mean()
        features.rushing_yards_avg = player_games['rushing_yards'].mean()
        features.receiving_yards_avg = player_games['receiving_yards'].mean()
        features.receptions_avg = player_games['receptions'].mean()
        features.targets_avg = player_games['targets'].mean()
        
    def _calculate_player_recent_form(self, features: PlayerFeatures, player_games: pd.DataFrame):
        """Calculate player recent form (last 5 games)"""
        recent_games = player_games.tail(5)
        
        if len(recent_games) == 0:
            return
            
        features.passing_yards_last_5 = recent_games['passing_yards'].tolist()
        features.rushing_yards_last_5 = recent_games['rushing_yards'].tolist()
        features.receiving_yards_last_5 = recent_games['receiving_yards'].tolist()
        features.receptions_last_5 = recent_games['receptions'].tolist()
        
    def _calculate_player_trends(self, features: PlayerFeatures, player_games: pd.DataFrame):
        """Calculate player performance trends"""
        recent_games = player_games.tail(5)
        
        if len(recent_games) < 3:  # Need at least 3 games for trend
            return
            
        # Calculate trend slopes using simple linear regression
        x = np.arange(len(recent_games))
        
        if len(recent_games['passing_yards']) > 0:
            features.passing_yards_trend = np.polyfit(x, recent_games['passing_yards'], 1)[0]
            
        if len(recent_games['receiving_yards']) > 0:
            features.receiving_yards_trend = np.polyfit(x, recent_games['receiving_yards'], 1)[0]
            
        # Target share trend (simplified)
        if len(recent_games['targets']) > 0 and recent_games['targets'].sum() > 0:
            features.target_share_trend = np.polyfit(x, recent_games['targets'], 1)[0]
            
    def create_game_features(self, home_team: str, away_team: str, date: datetime, week: int) -> Dict[str, Any]:
        """Create comprehensive game-level features for ML models"""
        logger.info(f"🏈 Creating game features for {away_team} @ {home_team} (Week {week})")
        
        # Get team features
        home_features = self.create_team_features(home_team, date, away_team)
        away_features = self.create_team_features(away_team, date, home_team)
        
        # Combine into game features
        game_features = {
            # Basic game info
            'home_team': home_team,
            'away_team': away_team,
            'week': week,
            'season': self._get_season_from_date(date),
            
            # Home team features
            'home_points_avg_last_5': home_features.points_avg_last_5,
            'home_yards_avg_last_5': home_features.yards_avg_last_5,
            'home_points_allowed_avg_last_5': home_features.points_allowed_avg_last_5,
            'home_win_percentage': home_features.win_percentage,
            'home_wins_last_5': home_features.wins_last_5,
            'home_home_win_percentage': home_features.home_wins / (home_features.home_wins + home_features.home_losses) if (home_features.home_wins + home_features.home_losses) > 0 else 0.5,
            
            # Away team features
            'away_points_avg_last_5': away_features.points_avg_last_5,
            'away_yards_avg_last_5': away_features.yards_avg_last_5,
            'away_points_allowed_avg_last_5': away_features.points_allowed_avg_last_5,
            'away_win_percentage': away_features.win_percentage,
            'away_wins_last_5': away_features.wins_last_5,
            'away_away_win_percentage': away_features.away_wins / (away_features.away_wins + away_features.away_losses) if (away_features.away_wins + away_features.away_losses) > 0 else 0.5,
            
            # Matchup features
            'home_offensive_advantage': home_features.points_avg_last_5 - away_features.points_allowed_avg_last_5,
            'away_offensive_advantage': away_features.points_avg_last_5 - home_features.points_allowed_avg_last_5,
            'total_points_trend': home_features.points_avg_last_5 + away_features.points_avg_last_5,
            
            # Head-to-head features (if available)
            'h2h_home_advantage': getattr(home_features, 'h2h_win_rate', 0.5) - 0.5,
            
            # Environmental features (placeholders)
            'is_dome': self._is_dome_game(home_team),
            'rest_days_home': 7,  # Placeholder
            'rest_days_away': 7,  # Placeholder
        }
        
        return game_features
        
    def create_prop_features(self, player_id: str, player_name: str, team: str, opponent: str, 
                           prop_type: str, date: datetime) -> Dict[str, Any]:
        """Create features for player prop predictions"""
        logger.info(f"🎯 Creating prop features for {player_name} ({prop_type})")
        
        # Get player features
        player_features = self.create_player_features(player_id, player_name, team, date)
        
        # Get opponent defensive features
        opponent_features = self.create_team_features(opponent, date, team)
        
        # Create prop-specific features
        prop_features = {
            # Player info
            'player_id': player_id,
            'player_name': player_name,
            'team': team,
            'opponent': opponent,
            'position': player_features.position,
            'prop_type': prop_type,
            
            # Player performance features
            'games_played': player_features.games_played,
            'season_avg': self._get_season_avg_for_prop_type(player_features, prop_type),
            'last_5_avg': self._get_last_5_avg_for_prop_type(player_features, prop_type),
            'trend': self._get_trend_for_prop_type(player_features, prop_type),
            
            # Matchup features
            'opponent_defense_rank': self._estimate_defense_rank(opponent_features, prop_type),
            'opponent_yards_allowed': self._get_opponent_yards_allowed(opponent_features, prop_type),
            
            # Game context
            'week': player_features.week,
            'season': player_features.season,
            'is_home': team == self._get_home_team_for_game(team, opponent, date),
        }
        
        return prop_features
        
    def _get_season_avg_for_prop_type(self, player_features: PlayerFeatures, prop_type: str) -> float:
        """Get season average for specific prop type"""
        if prop_type == "Passing Yards":
            return player_features.passing_yards_avg
        elif prop_type == "Rushing Yards":
            return player_features.rushing_yards_avg
        elif prop_type == "Receiving Yards":
            return player_features.receiving_yards_avg
        elif prop_type == "Receptions":
            return player_features.receptions_avg
        else:
            return 0.0
            
    def _get_last_5_avg_for_prop_type(self, player_features: PlayerFeatures, prop_type: str) -> float:
        """Get last 5 games average for specific prop type"""
        if prop_type == "Passing Yards" and player_features.passing_yards_last_5:
            return np.mean(player_features.passing_yards_last_5)
        elif prop_type == "Rushing Yards" and player_features.rushing_yards_last_5:
            return np.mean(player_features.rushing_yards_last_5)
        elif prop_type == "Receiving Yards" and player_features.receiving_yards_last_5:
            return np.mean(player_features.receiving_yards_last_5)
        elif prop_type == "Receptions" and player_features.receptions_last_5:
            return np.mean(player_features.receptions_last_5)
        else:
            return 0.0
            
    def _get_trend_for_prop_type(self, player_features: PlayerFeatures, prop_type: str) -> float:
        """Get trend for specific prop type"""
        if prop_type == "Passing Yards":
            return player_features.passing_yards_trend
        elif prop_type == "Receiving Yards":
            return player_features.receiving_yards_trend
        else:
            return 0.0
            
    def _estimate_defense_rank(self, opponent_features: TeamFeatures, prop_type: str) -> int:
        """Estimate opponent defense ranking for prop type"""
        # Simplified ranking based on yards allowed
        if prop_type in ["Passing Yards", "Receiving Yards"]:
            yards_allowed = opponent_features.pass_yards_allowed_avg_last_5
        else:
            yards_allowed = opponent_features.rush_yards_allowed_avg_last_5
            
        # Convert to ranking (1-32, lower is better defense)
        if yards_allowed < 200:
            return np.random.randint(1, 8)  # Top defense
        elif yards_allowed < 250:
            return np.random.randint(8, 16)  # Average defense
        else:
            return np.random.randint(16, 33)  # Poor defense
            
    def _get_opponent_yards_allowed(self, opponent_features: TeamFeatures, prop_type: str) -> float:
        """Get opponent yards allowed for prop type"""
        if prop_type in ["Passing Yards", "Receiving Yards"]:
            return opponent_features.pass_yards_allowed_avg_last_5
        else:
            return opponent_features.rush_yards_allowed_avg_last_5
            
    def _get_home_team_for_game(self, team: str, opponent: str, date: datetime) -> str:
        """Determine home team for a game (simplified)"""
        # In a real implementation, this would look up the actual game
        return team  # Placeholder
        
    def _get_week_from_date(self, date: datetime) -> int:
        """Estimate NFL week from date"""
        # Simplified week calculation
        if date.month == 9:
            return min(4, max(1, date.day // 7))
        elif date.month == 10:
            return min(8, 5 + (date.day // 7))
        elif date.month == 11:
            return min(12, 9 + (date.day // 7))
        elif date.month == 12:
            return min(16, 13 + (date.day // 7))
        elif date.month == 1:
            return min(18, 17 + (date.day // 7))
        else:
            return 1
            
    def _get_season_from_date(self, date: datetime) -> int:
        """Get NFL season from date"""
        if date.month >= 9:
            return date.year
        else:
            return date.year - 1
            
    def _is_dome_game(self, home_team: str) -> bool:
        """Check if game is played in a dome"""
        dome_teams = ['ATL', 'DET', 'HOU', 'IND', 'LV', 'LAR', 'MIN', 'NO', 'ARI']
        return home_team in dome_teams
        
    def validate_features(self, features: Dict[str, Any]) -> bool:
        """Validate feature data quality"""
        try:
            # Check for required fields
            required_fields = ['home_team', 'away_team', 'week', 'season']
            for field in required_fields:
                if field not in features:
                    logger.error(f"❌ Missing required field: {field}")
                    return False
                    
            # Check for reasonable values
            if features.get('week', 0) < 1 or features.get('week', 0) > 18:
                logger.error(f"❌ Invalid week: {features.get('week')}")
                return False
                
            # Check for NaN values
            for key, value in features.items():
                if isinstance(value, (int, float)) and np.isnan(value):
                    logger.warning(f"⚠️ NaN value found for {key}, replacing with 0")
                    features[key] = 0.0
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Feature validation error: {e}")
            return False
            
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data"""
        summary = {
            'historical_games': len(self.games_df) if self.games_df is not None else 0,
            'historical_players': len(self.players_df) if self.players_df is not None else 0,
            'data_loaded': self.games_df is not None and self.players_df is not None
        }
        
        if self.games_df is not None:
            summary['date_range'] = {
                'start': self.games_df['date'].min().isoformat(),
                'end': self.games_df['date'].max().isoformat()
            }
            summary['teams'] = sorted(list(set(self.games_df['home_team'].unique()) | set(self.games_df['away_team'].unique())))
            
        if self.players_df is not None:
            summary['unique_players'] = self.players_df['player_id'].nunique()
            summary['positions'] = sorted(self.players_df['position'].unique().tolist())
            
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = DataPipeline()
    
    # Get data summary
    summary = pipeline.get_data_summary()
    print("📊 Data Pipeline Summary:")
    print(f"Historical Games: {summary['historical_games']}")
    print(f"Historical Players: {summary['historical_players']}")
    print(f"Unique Players: {summary.get('unique_players', 0)}")
    print(f"Teams: {len(summary.get('teams', []))}")
    
    if summary['data_loaded']:
        # Test game features
        test_date = datetime(2024, 12, 1)
        game_features = pipeline.create_game_features("KC", "BUF", test_date, 13)
        print(f"\n🏈 Sample Game Features (BUF @ KC):")
        for key, value in list(game_features.items())[:10]:
            print(f"  {key}: {value}")
            
        # Test player features
        if len(pipeline.players_df) > 0:
            sample_player = pipeline.players_df.iloc[0]
            player_features = pipeline.create_player_features(
                sample_player['player_id'],
                sample_player['player_name'],
                sample_player['team'],
                test_date
            )
            print(f"\n👤 Sample Player Features ({sample_player['player_name']}):")
            print(f"  Position: {player_features.position}")
            print(f"  Games Played: {player_features.games_played}")
            print(f"  Passing Yards Avg: {player_features.passing_yards_avg:.1f}")
            print(f"  Receiving Yards Avg: {player_features.receiving_yards_avg:.1f}")
    else:
        print("⚠️ No historical data loaded - pipeline ready for live data only")