"""
Universal Game Data Builder with Temporal Safety

This module creates complete UniversalGameData objects using only historically
available information, ensuring no future data leakage in backtesting scenarios.

The builder integrates with HistoricalDataService to construct comprehensive
game context that personality-driven experts can use for predictions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Import the HistoricalDataService
try:
    from .historical_data_service import HistoricalDataService, GameContext, TeamSeasonStats
except ImportError:
    from src.services.historical_data_service import HistoricalDataService, GameContext, TeamSeasonStats

# Import UniversalGameData from personality experts
try:
    from ..ml.personality_driven_experts import UniversalGameData
except ImportError:
    try:
        from src.ml.personality_driven_experts import UniversalGameData
    except ImportError:
        # Define UniversalGameData if import fails
        @dataclass
        class UniversalGameData:
            """All available data that every expert can access equally"""
            # Team and game basics
            home_team: str = ""
            away_team: str = ""
            game_time: str = ""
            location: str = ""

            # Weather conditions
            weather: Dict[str, Any] = field(default_factory=dict)

            # Injury reports
            injuries: Dict[str, List[Dict]] = field(default_factory=dict)

            # Team statistics
            team_stats: Dict[str, Dict] = field(default_factory=dict)

            # Market data
            line_movement: Dict[str, Any] = field(default_factory=dict)
            public_betting: Dict[str, Any] = field(default_factory=dict)

            # News and updates
            recent_news: List[Dict] = field(default_factory=list)

            # Historical matchups
            head_to_head: Dict[str, Any] = field(default_factory=dict)

            # Coaching data
            coaching_info: Dict[str, Any] = field(default_factory=dict)

logger = logging.getLogger(__name__)


class UniversalGameDataBuilder:
    """
    Builds complete UniversalGameData objects using only historically available information
    
    This builder ensures temporal safety by:
    1. Only accessing data that would have been available at prediction time
    2. Using HistoricalDataService for time-aware queries
    3. Preventing future data leakage in backtesting scenarios
    """
    
    def __init__(self, historical_service: HistoricalDataService):
        self.historical_service = historical_service
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Cache for frequently accessed data during backtesting
        self._team_stats_cache: Dict[str, TeamSeasonStats] = {}
        self._game_context_cache: Dict[str, GameContext] = {}
        
        self.logger.info("🏗️ Universal Game Data Builder initialized with temporal safety")
    
    def build_universal_game_data(
        self,
        season: int,
        week: int,
        home_team: str,
        away_team: str,
        include_current_week_stats: bool = False
    ) -> UniversalGameData:
        """
        Build complete UniversalGameData using only historically available information
        
        Args:
            season: Season year
            week: Week number
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            include_current_week_stats: Whether to include current week in team stats
            
        Returns:
            UniversalGameData object with all available historical context
        """
        try:
            self.logger.debug(f"🏗️ Building UniversalGameData for {away_team} @ {home_team}, {season} Week {week}")
            
            # Get complete game context with temporal cutoff
            game_context = self.historical_service.get_game_context(
                home_team=home_team,
                away_team=away_team,
                season=season,
                week=week
            )
            
            # Build team statistics (through previous week by default)
            stats_week = week if include_current_week_stats else week
            home_stats = self.historical_service.get_team_season_stats_through_week(
                team=home_team,
                season=season,
                through_week=stats_week,
                include_current_week=include_current_week_stats
            )
            
            away_stats = self.historical_service.get_team_season_stats_through_week(
                team=away_team,
                season=season,
                through_week=stats_week,
                include_current_week=include_current_week_stats
            )
            
            # Get recent games for momentum analysis
            cutoff_date = game_context.game_date
            home_recent = self.historical_service.get_recent_games(
                team=home_team,
                cutoff_date=cutoff_date,
                limit=3
            )
            
            away_recent = self.historical_service.get_recent_games(
                team=away_team,
                cutoff_date=cutoff_date,
                limit=3
            )
            
            # Get head-to-head history
            h2h_history = self.historical_service.get_head_to_head_history(
                team1=home_team,
                team2=away_team,
                cutoff_date=cutoff_date,
                limit=5
            )
            
            # Build comprehensive team statistics
            team_stats = {
                'home': self._build_team_stats_dict(home_stats, home_recent),
                'away': self._build_team_stats_dict(away_stats, away_recent)
            }
            
            # Build weather information
            weather = {
                'temperature': game_context.weather.get('temperature'),
                'wind_speed': game_context.weather.get('wind_mph'),
                'humidity': game_context.weather.get('humidity'),
                'conditions': game_context.weather.get('description') or 'Unknown',
                'is_dome': game_context.venue_info.get('roof') in ['dome', 'retractable_dome']
            }
            
            # Build betting/market data
            line_movement = {
                'opening_line': game_context.betting_lines.get('spread_line'),
                'current_line': game_context.betting_lines.get('spread_line'),  # Same as opening for historical
                'total_line': game_context.betting_lines.get('total_line'),
                'home_moneyline': game_context.betting_lines.get('home_moneyline'),
                'away_moneyline': game_context.betting_lines.get('away_moneyline'),
                'public_percentage': 50  # Default neutral if not available
            }
            
            # Build injury reports (placeholder - would need additional data source)
            injuries = {
                'home': [],
                'away': []
            }
            
            # Build head-to-head information
            head_to_head = {
                'total_games': len(h2h_history),
                'home_team_wins': len([g for g in h2h_history if self._get_winner(g, home_team) == home_team]),
                'away_team_wins': len([g for g in h2h_history if self._get_winner(g, home_team) == away_team]),
                'recent_games': h2h_history[:3],
                'average_total': self._calculate_average_total(h2h_history),
                'average_margin': self._calculate_average_margin(h2h_history, home_team)
            }
            
            # Build coaching information
            coaching_info = {
                'home_coach': game_context.coaching_staff.get('home_coach'),
                'away_coach': game_context.coaching_staff.get('away_coach')
            }
            
            # Create UniversalGameData object
            universal_data = UniversalGameData(
                home_team=home_team,
                away_team=away_team,
                game_time=f"{game_context.game_date} {game_context.season} Week {game_context.week}",
                location=game_context.venue_info.get('stadium', 'Unknown Stadium'),
                weather=weather,
                injuries=injuries,
                team_stats=team_stats,
                line_movement=line_movement,
                public_betting={},  # Placeholder
                recent_news=[],     # Placeholder
                head_to_head=head_to_head,
                coaching_info=coaching_info
            )
            
            self.logger.debug(f"✅ Built UniversalGameData with {len(team_stats)} team stat sets")
            return universal_data
            
        except Exception as e:
            self.logger.error(f"❌ Error building UniversalGameData: {e}")
            raise
    
    def _build_team_stats_dict(self, stats: TeamSeasonStats, recent_games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert TeamSeasonStats and recent games into the expected format"""
        
        # Calculate recent form
        recent_results = []
        recent_points_for = []
        recent_points_against = []
        
        for game in recent_games[:5]:  # Last 5 games
            if 'team_perspective' in game:
                perspective = game['team_perspective']
                recent_results.append(perspective['result'])
                recent_points_for.append(perspective['team_score'])
                recent_points_against.append(perspective['opponent_score'])
        
        return {
            # Basic record
            'wins': stats.wins,
            'losses': stats.losses,
            'win_percentage': stats.win_percentage,
            'games_played': stats.games_played,
            
            # Scoring
            'points_per_game': stats.points_per_game,
            'points_allowed_per_game': stats.points_allowed_per_game,
            'point_differential': stats.point_differential,
            'average_margin': stats.average_margin,
            
            # Home/Away splits
            'home_record': f"{stats.home_record[0]}-{stats.home_record[1]}",
            'away_record': f"{stats.away_record[0]}-{stats.away_record[1]}",
            
            # Division performance
            'division_record': f"{stats.division_record[0]}-{stats.division_record[1]}",
            
            # Recent form
            'recent_form': ''.join(recent_results),
            'recent_points_for': sum(recent_points_for) / len(recent_points_for) if recent_points_for else 0,
            'recent_points_against': sum(recent_points_against) / len(recent_points_against) if recent_points_against else 0,
            'recent_games_count': len(recent_games),
            
            # Close game performance
            'close_game_record': f"{stats.close_game_record[0]}-{stats.close_game_record[1]}",
            
            # Momentum indicators
            'last_game_result': recent_results[0] if recent_results else None,
            'last_game_margin': recent_games[0]['team_perspective']['margin'] if recent_games and 'team_perspective' in recent_games[0] else 0,
            'winning_streak': self._calculate_streak(recent_results, 'W'),
            'losing_streak': self._calculate_streak(recent_results, 'L')
        }
    
    def _calculate_streak(self, results: List[str], result_type: str) -> int:
        """Calculate current winning or losing streak"""
        if not results:
            return 0
        
        streak = 0
        for result in results:
            if result == result_type:
                streak += 1
            else:
                break
        return streak
    
    def _get_winner(self, game: Dict[str, Any], perspective_team: str) -> str:
        """Determine winner of a game from perspective team's view"""
        if game['home_team'] == perspective_team:
            return game['home_team'] if game['home_score'] > game['away_score'] else game['away_team']
        else:
            return game['away_team'] if game['away_score'] > game['home_score'] else game['home_team']
    
    def _calculate_average_total(self, games: List[Dict[str, Any]]) -> float:
        """Calculate average total points in head-to-head games"""
        if not games:
            return 0.0
        
        totals = []
        for game in games:
            if game.get('home_score') is not None and game.get('away_score') is not None:
                totals.append(game['home_score'] + game['away_score'])
        
        return sum(totals) / len(totals) if totals else 0.0
    
    def _calculate_average_margin(self, games: List[Dict[str, Any]], home_team: str) -> float:
        """Calculate average margin from home team's perspective"""
        if not games:
            return 0.0
        
        margins = []
        for game in games:
            if game.get('home_score') is not None and game.get('away_score') is not None:
                if game['home_team'] == home_team:
                    margin = game['home_score'] - game['away_score']
                else:
                    margin = game['away_score'] - game['home_score']
                margins.append(margin)
        
        return sum(margins) / len(margins) if margins else 0.0
    
    def clear_cache(self):
        """Clear all cached data"""
        self._team_stats_cache.clear()
        self._game_context_cache.clear()
        self.logger.info("🗑️ Cleared UniversalGameDataBuilder cache")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'team_stats_cached': len(self._team_stats_cache),
            'game_context_cached': len(self._game_context_cache)
        }