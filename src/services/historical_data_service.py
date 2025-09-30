"""
Historical Data Service with Temporal Cutoff Enforcement

This service provides time-aware access to historical NFL game data,
ensuring that backtesting and prediction systems only use data that
would have been available at the time of prediction.

Key Features:
- Temporal cutoff enforcement (no future data leakage)
- Chronological data querying
- Team performance metrics through specific weeks
- Context-aware game data retrieval
- Memory integration for personality-driven experts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class GameContext:
    """Context data for a specific game at prediction time"""
    game_id: str
    season: int
    week: int
    game_date: str
    home_team: str
    away_team: str
    
    # Available context (no outcomes)
    weather: Dict[str, Any]
    betting_lines: Dict[str, Any]
    rest_days: Dict[str, int]
    coaching_staff: Dict[str, str]
    venue_info: Dict[str, Any]
    
    # Historical context through cutoff
    team_stats: Dict[str, Dict[str, Any]]
    recent_form: Dict[str, List[Dict[str, Any]]]
    head_to_head: List[Dict[str, Any]]


@dataclass 
class TeamSeasonStats:
    """Team statistics through a specific week"""
    team: str
    season: int
    through_week: int
    
    # Offensive stats
    games_played: int
    points_per_game: float
    yards_per_game: float
    passing_yards_per_game: float
    rushing_yards_per_game: float
    
    # Defensive stats
    points_allowed_per_game: float
    yards_allowed_per_game: float
    
    # Record and performance
    wins: int
    losses: int
    win_percentage: float
    
    # Situational stats
    home_record: Tuple[int, int]
    away_record: Tuple[int, int]
    division_record: Tuple[int, int]
    
    # Advanced metrics
    point_differential: float
    average_margin: float
    close_game_record: Tuple[int, int]  # Games decided by 7 or less


class HistoricalDataService:
    """
    Time-aware historical data service with temporal cutoff enforcement
    
    Ensures that all data queries respect the temporal boundary, preventing
    future data leakage in backtesting and prediction scenarios.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Cache for frequently accessed data
        self._team_stats_cache: Dict[str, TeamSeasonStats] = {}
        self._game_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        self.logger.info("🏈 Historical Data Service initialized with temporal cutoff enforcement")
    
    def get_team_season_stats_through_week(
        self, 
        team: str, 
        season: int, 
        through_week: int,
        include_current_week: bool = False
    ) -> TeamSeasonStats:
        """
        Get team statistics through a specific week with temporal cutoff
        
        Args:
            team: Team abbreviation (e.g., 'KC', 'BAL')
            season: Season year
            through_week: Calculate stats through this week
            include_current_week: Whether to include the current week's games
            
        Returns:
            TeamSeasonStats with data only through the specified week
        """
        cache_key = f"{team}_{season}_{through_week}_{include_current_week}"
        
        if cache_key in self._team_stats_cache:
            return self._team_stats_cache[cache_key]
        
        try:
            # Determine week cutoff
            self.logger.debug(f"📊 Calculating {team} stats through {season} Week {through_week}")
            
            # Query games with temporal cutoff
            if include_current_week:
                home_games_query = self.supabase.table('nfl_games') \
                    .select('*') \
                    .eq('home_team', team) \
                    .eq('season', season) \
                    .lte('week', through_week) \
                    .not_.is_('home_score', 'null') \
                    .order('week')
                
                away_games_query = self.supabase.table('nfl_games') \
                    .select('*') \
                    .eq('away_team', team) \
                    .eq('season', season) \
                    .lte('week', through_week) \
                    .not_.is_('away_score', 'null') \
                    .order('week')
            else:
                home_games_query = self.supabase.table('nfl_games') \
                    .select('*') \
                    .eq('home_team', team) \
                    .eq('season', season) \
                    .lt('week', through_week) \
                    .not_.is_('home_score', 'null') \
                    .order('week')
                
                away_games_query = self.supabase.table('nfl_games') \
                    .select('*') \
                    .eq('away_team', team) \
                    .eq('season', season) \
                    .lt('week', through_week) \
                    .not_.is_('away_score', 'null') \
                    .order('week')
            
            home_games = home_games_query.execute().data or []
            away_games = away_games_query.execute().data or []
            
            all_games = home_games + away_games
            all_games.sort(key=lambda x: x['week'])
            
            if not all_games:
                self.logger.warning(f"⚠️ No games found for {team} in {season} through week {through_week}")
                return self._create_empty_team_stats(team, season, through_week)
            
            # Calculate comprehensive statistics
            stats = self._calculate_team_statistics(team, all_games, season, through_week)
            
            # Cache the result
            self._team_stats_cache[cache_key] = stats
            
            self.logger.debug(f"✅ Calculated stats for {team}: {stats.wins}-{stats.losses} record")
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating team stats for {team}: {e}")
            return self._create_empty_team_stats(team, season, through_week)
    
    def get_recent_games(
        self, 
        team: str, 
        cutoff_date: str, 
        limit: int = 5,
        include_playoffs: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get recent games for a team before the cutoff date
        
        Args:
            team: Team abbreviation
            cutoff_date: ISO date string for temporal cutoff
            limit: Maximum number of games to return
            include_playoffs: Whether to include playoff games
            
        Returns:
            List of recent games with outcomes and context
        """
        cache_key = f"recent_{team}_{cutoff_date}_{limit}_{include_playoffs}"
        
        if cache_key in self._game_cache:
            return self._game_cache[cache_key]
        
        try:
            self.logger.debug(f"🔍 Getting recent {limit} games for {team} before {cutoff_date}")
            
            # Build query with temporal cutoff
            base_query = self.supabase.table('nfl_games') \
                .select('*') \
                .lt('game_date', cutoff_date) \
                .not_.is_('home_score', 'null') \
                .order('game_date', desc=True) \
                .limit(limit)
            
            # Filter by game type if needed
            if not include_playoffs:
                base_query = base_query.eq('game_type', 'REG')
            
            # Get home and away games
            home_games = base_query.eq('home_team', team).execute().data or []
            away_games = base_query.eq('away_team', team).execute().data or []
            
            # Combine and sort by date (most recent first)
            all_games = home_games + away_games
            all_games.sort(key=lambda x: x['game_date'], reverse=True)
            
            # Take only the requested number
            recent_games = all_games[:limit]
            
            # Enrich with team perspective
            enriched_games = []
            for game in recent_games:
                enriched_game = self._enrich_game_with_team_perspective(game, team)
                enriched_games.append(enriched_game)
            
            # Cache the result
            self._game_cache[cache_key] = enriched_games
            
            self.logger.debug(f"✅ Found {len(enriched_games)} recent games for {team}")
            return enriched_games
            
        except Exception as e:
            self.logger.error(f"❌ Error getting recent games for {team}: {e}")
            return []
    
    def get_game_context(
        self, 
        home_team: str, 
        away_team: str, 
        season: int, 
        week: int
    ) -> GameContext:
        """
        Get complete game context with temporal cutoff enforcement
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation  
            season: Season year
            week: Week number
            
        Returns:
            GameContext with all available historical data through the cutoff
        """
        try:
            self.logger.debug(f"📋 Building context for {away_team} @ {home_team}, {season} Week {week}")
            
            # Get the specific game (without outcome data)
            game_query = self.supabase.table('nfl_games') \
                .select('*') \
                .eq('home_team', home_team) \
                .eq('away_team', away_team) \
                .eq('season', season) \
                .eq('week', week) \
                .single()
            
            game_data = game_query.execute().data
            
            if not game_data:
                raise ValueError(f"Game not found: {away_team} @ {home_team}, {season} Week {week}")
            
            # Build context with temporal cutoff (exclude current week by default)
            home_stats = self.get_team_season_stats_through_week(home_team, season, week, include_current_week=False)
            away_stats = self.get_team_season_stats_through_week(away_team, season, week, include_current_week=False)
            
            # Get recent form for both teams
            cutoff_date = game_data['game_date']
            home_recent = self.get_recent_games(home_team, cutoff_date, limit=3)
            away_recent = self.get_recent_games(away_team, cutoff_date, limit=3)
            
            # Get head-to-head history
            h2h_history = self._get_head_to_head_history(
                home_team, away_team, cutoff_date, limit=5
            )
            
            # Extract contextual information (available at prediction time)
            weather = {
                'temperature': game_data.get('weather_temperature'),
                'wind_mph': game_data.get('weather_wind_mph'),
                'humidity': game_data.get('weather_humidity'),
                'description': game_data.get('weather_description')
            }
            
            betting_lines = {
                'spread_line': game_data.get('spread_line'),
                'total_line': game_data.get('total_line'),
                'home_moneyline': game_data.get('home_moneyline'),
                'away_moneyline': game_data.get('away_moneyline')
            }
            
            rest_days = {
                'home': game_data.get('home_rest'),
                'away': game_data.get('away_rest')
            }
            
            coaching_staff = {
                'home_coach': game_data.get('home_coach'),
                'away_coach': game_data.get('away_coach')
            }
            
            venue_info = {
                'stadium': game_data.get('stadium'),
                'surface': game_data.get('surface'),
                'roof': game_data.get('roof'),
                'location': game_data.get('location')
            }
            
            context = GameContext(
                game_id=game_data['game_id'],
                season=season,
                week=week,
                game_date=game_data['game_date'],
                home_team=home_team,
                away_team=away_team,
                weather=weather,
                betting_lines=betting_lines,
                rest_days=rest_days,
                coaching_staff=coaching_staff,
                venue_info=venue_info,
                team_stats={
                    'home': home_stats.__dict__,
                    'away': away_stats.__dict__
                },
                recent_form={
                    'home': home_recent,
                    'away': away_recent
                },
                head_to_head=h2h_history
            )
            
            self.logger.debug(f"✅ Built complete context for {away_team} @ {home_team}")
            return context
            
        except Exception as e:
            self.logger.error(f"❌ Error building game context: {e}")
            raise
    
    def get_head_to_head_history(
        self, 
        team1: str, 
        team2: str, 
        cutoff_date: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get head-to-head history between two teams before cutoff date"""
        return self._get_head_to_head_history(team1, team2, cutoff_date, limit)
    
    def _get_head_to_head_history(
        self, 
        team1: str, 
        team2: str, 
        cutoff_date: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Internal method to get head-to-head history"""
        try:
            # Query both directions (team1 home vs team2, team2 home vs team1)
            query1 = self.supabase.table('nfl_games') \
                .select('*') \
                .eq('home_team', team1) \
                .eq('away_team', team2) \
                .lt('game_date', cutoff_date) \
                .not_.is_('home_score', 'null')
            
            query2 = self.supabase.table('nfl_games') \
                .select('*') \
                .eq('home_team', team2) \
                .eq('away_team', team1) \
                .lt('game_date', cutoff_date) \
                .not_.is_('away_score', 'null')
            
            games1 = query1.execute().data or []
            games2 = query2.execute().data or []
            
            all_games = games1 + games2
            all_games.sort(key=lambda x: x['game_date'], reverse=True)
            
            return all_games[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting H2H history: {e}")
            return []
    
    def _calculate_team_statistics(
        self, 
        team: str, 
        games: List[Dict[str, Any]], 
        season: int, 
        through_week: int
    ) -> TeamSeasonStats:
        """Calculate comprehensive team statistics from game list"""
        
        if not games:
            return self._create_empty_team_stats(team, season, through_week)
        
        # Initialize counters
        total_points = 0
        total_points_allowed = 0
        
        wins = 0
        losses = 0
        home_wins = home_losses = 0
        away_wins = away_losses = 0
        div_wins = div_losses = 0
        close_wins = close_losses = 0
        
        margins = []
        
        for game in games:
            is_home = game['home_team'] == team
            
            if is_home:
                team_score = game['home_score']
                opp_score = game['away_score']
            else:
                team_score = game['away_score']
                opp_score = game['home_score']
            
            # Basic stats
            total_points += team_score
            total_points_allowed += opp_score
            
            # Determine win/loss
            margin = team_score - opp_score
            margins.append(margin)
            
            if margin > 0:
                wins += 1
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1
                    
                if game.get('div_game'):
                    div_wins += 1
                    
                if abs(margin) <= 7:
                    close_wins += 1
            else:
                losses += 1
                if is_home:
                    home_losses += 1
                else:
                    away_losses += 1
                    
                if game.get('div_game'):
                    div_losses += 1
                    
                if abs(margin) <= 7:
                    close_losses += 1
        
        games_played = len(games)
        
        return TeamSeasonStats(
            team=team,
            season=season,
            through_week=through_week,
            games_played=games_played,
            points_per_game=total_points / games_played if games_played > 0 else 0,
            yards_per_game=0,  # Would need additional data
            passing_yards_per_game=0,  # Would need additional data
            rushing_yards_per_game=0,  # Would need additional data
            points_allowed_per_game=total_points_allowed / games_played if games_played > 0 else 0,
            yards_allowed_per_game=0,  # Would need additional data
            wins=wins,
            losses=losses,
            win_percentage=wins / games_played if games_played > 0 else 0,
            home_record=(home_wins, home_losses),
            away_record=(away_wins, away_losses), 
            division_record=(div_wins, div_losses),
            point_differential=sum(margins),
            average_margin=sum(margins) / len(margins) if margins else 0,
            close_game_record=(close_wins, close_losses)
        )
    
    def _enrich_game_with_team_perspective(
        self, 
        game: Dict[str, Any], 
        team: str
    ) -> Dict[str, Any]:
        """Add team-specific perspective to game data"""
        is_home = game['home_team'] == team
        
        enriched = game.copy()
        enriched.update({
            'team_perspective': {
                'is_home': is_home,
                'opponent': game['away_team'] if is_home else game['home_team'],
                'team_score': game['home_score'] if is_home else game['away_score'],
                'opponent_score': game['away_score'] if is_home else game['home_score'],
                'result': 'W' if (
                    (is_home and game['home_score'] > game['away_score']) or
                    (not is_home and game['away_score'] > game['home_score'])
                ) else 'L',
                'margin': (
                    game['home_score'] - game['away_score'] if is_home 
                    else game['away_score'] - game['home_score']
                )
            }
        })
        
        return enriched
    
    def _create_empty_team_stats(
        self, 
        team: str, 
        season: int, 
        through_week: int
    ) -> TeamSeasonStats:
        """Create empty team statistics object"""
        return TeamSeasonStats(
            team=team,
            season=season,
            through_week=through_week,
            games_played=0,
            points_per_game=0,
            yards_per_game=0,
            passing_yards_per_game=0,
            rushing_yards_per_game=0,
            points_allowed_per_game=0,
            yards_allowed_per_game=0,
            wins=0,
            losses=0,
            win_percentage=0,
            home_record=(0, 0),
            away_record=(0, 0),
            division_record=(0, 0),
            point_differential=0,
            average_margin=0,
            close_game_record=(0, 0)
        )
    
    def clear_cache(self):
        """Clear all cached data"""
        self._team_stats_cache.clear()
        self._game_cache.clear()
        self.logger.info("🗑️ Cleared all cached data")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'team_stats_cached': len(self._team_stats_cache),
            'games_cached': len(self._game_cache)
        }
    
    # LLM Integration Methods
    
    async def store_reasoning_chain(self, reasoning_data: Dict[str, Any]):
        """Store complete LLM reasoning chain in database"""
        try:
            result = self.supabase.table('expert_reasoning_chains').insert({
                'expert_id': reasoning_data['expert_id'],
                'game_context': reasoning_data['game_context'],
                'llm_request_metadata': reasoning_data['llm_request'],
                'raw_llm_response': reasoning_data['raw_llm_response'],
                'parsed_predictions': reasoning_data['parsed_predictions'],
                'structured_prediction': reasoning_data['structured_prediction'],
                'memories_used_count': reasoning_data['memories_used'],
                'reasoning_discussion': reasoning_data['reasoning_discussion'],
                'prediction_relationships': reasoning_data['prediction_relationships'],
                'created_at': reasoning_data['timestamp']
            }).execute()
            
            self.logger.info(f"✅ Stored reasoning chain for {reasoning_data['expert_id']}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"❌ Error storing reasoning chain: {e}")
            raise
    
    async def store_belief_revision(self, revision_data: Dict[str, Any]):
        """Store belief revision analysis in database"""
        try:
            result = self.supabase.table('expert_belief_revisions').insert({
                'expert_id': revision_data['expert_id'],
                'original_prediction': revision_data['original_prediction'],
                'actual_outcome': revision_data['actual_outcome'],
                'belief_revision_analysis': revision_data['belief_revision_analysis'],
                'reflection_discussion': revision_data['reflection_discussion'],
                'correct_predictions_analysis': revision_data['correct_predictions_analysis'],
                'incorrect_predictions_analysis': revision_data['incorrect_predictions_analysis'],
                'causal_reasoning_evaluation': revision_data['causal_reasoning_evaluation'],
                'pattern_recognition': revision_data['pattern_recognition'],
                'lessons_learned': revision_data['lessons_learned'],
                'memory_updates': revision_data['memory_updates'],
                'llm_response_metadata': revision_data['llm_response_metadata'],
                'created_at': revision_data['timestamp']
            }).execute()
            
            self.logger.info(f"✅ Stored belief revision for {revision_data['expert_id']}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"❌ Error storing belief revision: {e}")
            raise
    
    async def store_learned_weight(self, weight_data: Dict[str, Any]):
        """Store learned weight adjustment in database"""
        try:
            result = self.supabase.table('expert_learned_weights').insert({
                'expert_id': weight_data['expert_id'],
                'lesson_description': weight_data['lesson_description'],
                'application_method': weight_data['application_method'],
                'confidence_impact': weight_data['confidence_impact'],
                'created_at': weight_data['timestamp']
            }).execute()
            
            self.logger.debug(f"✅ Stored learned weight for {weight_data['expert_id']}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"❌ Error storing learned weight: {e}")
            raise
    
    async def store_episodic_memory(self, memory_data: Dict[str, Any]):
        """Store enriched episodic memory in database"""
        try:
            result = self.supabase.table('expert_episodic_memories').insert({
                'expert_id': memory_data['expert_id'],
                'game_context': memory_data['game_context'],
                'prediction_summary': memory_data['prediction_summary'],
                'actual_outcome': memory_data['actual_outcome'],
                'was_correct': memory_data['was_correct'],
                'reasoning_chain': memory_data['reasoning_chain'],
                'post_game_insights': memory_data['post_game_insights'],
                'lessons_extracted': memory_data['lessons_extracted'],
                'causal_analysis': memory_data['causal_analysis'],
                'pattern_insights': memory_data['pattern_insights'],
                'memory_type': memory_data['memory_type'],
                'created_at': memory_data['timestamp']
            }).execute()
            
            self.logger.info(f"✅ Stored episodic memory for {memory_data['expert_id']}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"❌ Error storing episodic memory: {e}")
            raise
    
    async def get_recent_reasoning_chains(self, expert_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reasoning chains for an expert"""
        try:
            result = self.supabase.table('expert_reasoning_chains') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving reasoning chains: {e}")
            return []
    
    async def get_recent_belief_revisions(self, expert_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent belief revisions for an expert"""
        try:
            result = self.supabase.table('expert_belief_revisions') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving belief revisions: {e}")
            return []
    
    async def retrieve_memories(self, expert_id: str, game_context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant episodic memories for an expert"""
        try:
            # Simple retrieval based on teams (can be enhanced with vector similarity)
            home_team = game_context.get('home_team')
            away_team = game_context.get('away_team')
            
            query = self.supabase.table('expert_episodic_memories') \
                .select('*') \
                .eq('expert_id', expert_id) \
                .order('created_at', desc=True) \
                .limit(limit * 2)  # Get more to filter
            
            result = query.execute()
            memories = result.data or []
            
            # Filter for relevant memories (teams involved)
            relevant_memories = []
            for memory in memories:
                memory_context = memory.get('game_context', {})
                memory_home = memory_context.get('home_team')
                memory_away = memory_context.get('away_team')
                
                # Include if involves same teams
                if home_team in [memory_home, memory_away] or away_team in [memory_home, memory_away]:
                    relevant_memories.append({
                        'matchup_description': f"{memory_away} @ {memory_home}",
                        'prediction_summary': memory.get('prediction_summary', ''),
                        'reasoning': memory.get('reasoning_chain', ''),
                        'actual_outcome': memory.get('actual_outcome', {}),
                        'lesson_learned': memory.get('post_game_insights', ''),
                        'relevance_to_current': 'Similar teams involved'
                    })
                
                if len(relevant_memories) >= limit:
                    break
            
            self.logger.info(f"🧠 Retrieved {len(relevant_memories)} relevant memories for {expert_id}")
            return relevant_memories
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving memories: {e}")
            return []
    
    async def get_games_for_week(self, season: int, week: int) -> List[Dict[str, Any]]:
        """Get all games for a specific week and season"""
        try:
            result = self.supabase.table('nfl_games') \
                .select('*') \
                .eq('season', season) \
                .eq('week', week) \
                .order('game_date') \
                .execute()
            
            games = result.data or []
            self.logger.info(f"📅 Retrieved {len(games)} games for {season} Week {week}")
            return games
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving games for {season} Week {week}: {e}")
            return []
