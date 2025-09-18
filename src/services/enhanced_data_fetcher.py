"""
Enhanced NFL Data Fetcher Service

Fetches comprehensive NFL game data from SportsData.io APIs to populate
the enhanced database schema for detailed expert prediction verification.

Supports:
- Game scores and basic stats
- Play-by-play data
- Advanced team metrics
- Coaching decisions analysis
- Special teams performance
- Situational performance metrics
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import os
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedGameData:
    """Enhanced game data structure matching database schema"""
    game_id: str
    season: int
    week: int
    home_team: str
    away_team: str
    game_date: Optional[datetime] = None
    final_score_home: Optional[int] = None
    final_score_away: Optional[int] = None
    status: Optional[str] = None

    # Weather and conditions
    weather_temperature: Optional[int] = None
    weather_humidity: Optional[int] = None
    weather_wind_speed: Optional[int] = None
    weather_wind_direction: Optional[str] = None
    weather_condition: Optional[str] = None
    stadium_name: Optional[str] = None
    attendance: Optional[int] = None

    # Game flow
    total_plays: Optional[int] = None
    game_duration_minutes: Optional[int] = None
    overtime_periods: Optional[int] = None

    # Team stats
    home_time_of_possession: Optional[str] = None
    away_time_of_possession: Optional[str] = None
    home_first_downs: Optional[int] = None
    away_first_downs: Optional[int] = None
    home_total_yards: Optional[int] = None
    away_total_yards: Optional[int] = None
    home_passing_yards: Optional[int] = None
    away_passing_yards: Optional[int] = None
    home_rushing_yards: Optional[int] = None
    away_rushing_yards: Optional[int] = None

    # Efficiency metrics
    home_third_down_attempts: Optional[int] = None
    home_third_down_conversions: Optional[int] = None
    away_third_down_attempts: Optional[int] = None
    away_third_down_conversions: Optional[int] = None
    home_red_zone_attempts: Optional[int] = None
    home_red_zone_scores: Optional[int] = None
    away_red_zone_attempts: Optional[int] = None
    away_red_zone_scores: Optional[int] = None

    # Turnovers and penalties
    home_turnovers: Optional[int] = None
    away_turnovers: Optional[int] = None
    home_penalties: Optional[int] = None
    home_penalty_yards: Optional[int] = None
    away_penalties: Optional[int] = None
    away_penalty_yards: Optional[int] = None

    # Special teams
    home_punt_return_yards: Optional[int] = None
    away_punt_return_yards: Optional[int] = None
    home_kick_return_yards: Optional[int] = None
    away_kick_return_yards: Optional[int] = None

    # Raw data storage
    raw_score_data: Optional[Dict] = None
    raw_stats_data: Optional[Dict] = None
    raw_advanced_metrics: Optional[Dict] = None

@dataclass
class GamePlayByPlay:
    """Play-by-play data structure"""
    game_id: str
    play_id: str
    quarter: Optional[int] = None
    time_remaining: Optional[str] = None
    down: Optional[int] = None
    yards_to_go: Optional[int] = None
    yard_line: Optional[int] = None
    possession_team: Optional[str] = None
    play_type: Optional[str] = None
    play_description: Optional[str] = None
    yards_gained: Optional[int] = None
    is_touchdown: bool = False
    is_field_goal: bool = False
    is_safety: bool = False
    is_turnover: bool = False
    is_penalty: bool = False
    primary_player: Optional[str] = None
    secondary_players: Optional[Dict] = None
    is_red_zone: bool = False
    is_goal_to_go: bool = False
    is_fourth_down: bool = False
    is_two_minute_warning: bool = False
    raw_play_data: Optional[Dict] = None

@dataclass
class GameDrive:
    """Drive data structure"""
    game_id: str
    drive_id: str
    quarter: Optional[int] = None
    possession_team: Optional[str] = None
    starting_field_position: Optional[int] = None
    drive_result: Optional[str] = None
    ending_field_position: Optional[int] = None
    total_plays: Optional[int] = None
    total_yards: Optional[int] = None
    time_consumed: Optional[str] = None
    plays_per_yard: Optional[Decimal] = None
    yards_per_play: Optional[Decimal] = None
    is_scoring_drive: bool = False
    is_three_and_out: bool = False
    is_two_minute_drill: bool = False
    is_goal_line_stand: bool = False

@dataclass
class CoachingDecision:
    """Coaching decision data structure"""
    game_id: str
    team: str
    quarter: Optional[int] = None
    situation: Optional[str] = None
    decision_type: Optional[str] = None
    decision_description: Optional[str] = None
    outcome: Optional[str] = None
    expected_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    decision_quality_score: Optional[Decimal] = None
    game_state: Optional[Dict] = None
    alternative_decisions: Optional[Dict] = None

@dataclass
class SpecialTeamsPerformance:
    """Special teams performance data structure"""
    game_id: str
    team: str
    field_goal_attempts: int = 0
    field_goals_made: int = 0
    longest_field_goal: Optional[int] = None
    extra_point_attempts: int = 0
    extra_points_made: int = 0
    punts: int = 0
    punt_yards: int = 0
    punts_inside_20: int = 0
    punt_return_yards_allowed: int = 0
    kickoff_returns: int = 0
    kickoff_return_yards: int = 0
    punt_returns: int = 0
    punt_return_yards: int = 0
    return_touchdowns: int = 0
    tackles_on_coverage: int = 0
    coverage_efficiency_score: Optional[Decimal] = None
    field_position_advantage: Optional[Decimal] = None
    special_teams_score: Optional[Decimal] = None

@dataclass
class SituationalPerformance:
    """Situational performance data structure"""
    game_id: str
    team: str
    points_final_2_minutes: int = 0
    drives_final_2_minutes: int = 0
    scoring_drives_final_2_minutes: int = 0
    fourth_down_attempts: int = 0
    fourth_down_conversions: int = 0
    red_zone_trips: int = 0
    red_zone_touchdowns: int = 0
    crowd_noise_impact_score: Optional[Decimal] = None
    home_field_advantage_score: Optional[Decimal] = None
    referee_calls_differential: Optional[int] = None
    momentum_shifts: int = 0
    largest_lead: int = 0
    time_with_lead: Optional[int] = None
    comeback_ability_score: Optional[Decimal] = None

class EnhancedDataFetcher:
    """Fetches comprehensive NFL data from SportsData.io APIs"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sportsdata.io/v3/nfl"
        self.headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "User-Agent": "NFL-Predictor-Enhanced/1.0"
        }

    async def fetch_enhanced_game_data(self, season: int, week: int) -> List[EnhancedGameData]:
        """Fetch enhanced game data for a specific week"""
        logger.info(f"Fetching enhanced game data for {season} Week {week}")

        try:
            # Fetch multiple data sources concurrently
            async with aiohttp.ClientSession() as session:
                # Core endpoints for comprehensive data
                tasks = [
                    self._fetch_scores(session, season, week),
                    self._fetch_team_stats(session, season, week),
                    self._fetch_advanced_metrics(session, season, week)
                ]

                scores_data, stats_data, metrics_data = await asyncio.gather(*tasks, return_exceptions=True)

                # Process and combine data
                enhanced_games = []
                if not isinstance(scores_data, Exception):
                    for game in scores_data:
                        enhanced_game = self._build_enhanced_game_data(game, stats_data, metrics_data)
                        enhanced_games.append(enhanced_game)

                logger.info(f"Successfully fetched {len(enhanced_games)} enhanced games")
                return enhanced_games

        except Exception as e:
            logger.error(f"Error fetching enhanced game data: {e}")
            return []

    async def fetch_play_by_play_data(self, game_id: str) -> List[GamePlayByPlay]:
        """Fetch detailed play-by-play data for a game"""
        logger.info(f"Fetching play-by-play data for game {game_id}")

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/pbp/{game_id}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_play_by_play_data(data, game_id)
                    else:
                        logger.error(f"Failed to fetch play-by-play: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching play-by-play data: {e}")
            return []

    async def fetch_drive_data(self, game_id: str) -> List[GameDrive]:
        """Fetch drive-level data for a game"""
        logger.info(f"Fetching drive data for game {game_id}")

        try:
            # Drive data is typically extracted from play-by-play
            plays = await self.fetch_play_by_play_data(game_id)
            return self._extract_drive_data(plays, game_id)

        except Exception as e:
            logger.error(f"Error fetching drive data: {e}")
            return []

    async def fetch_coaching_decisions(self, game_id: str) -> List[CoachingDecision]:
        """Analyze and extract coaching decisions from play-by-play"""
        logger.info(f"Analyzing coaching decisions for game {game_id}")

        try:
            plays = await self.fetch_play_by_play_data(game_id)
            return self._analyze_coaching_decisions(plays, game_id)

        except Exception as e:
            logger.error(f"Error analyzing coaching decisions: {e}")
            return []

    async def fetch_special_teams_data(self, game_id: str) -> List[SpecialTeamsPerformance]:
        """Extract special teams performance from game data"""
        logger.info(f"Extracting special teams data for game {game_id}")

        try:
            # Get team stats and play-by-play for special teams analysis
            async with aiohttp.ClientSession() as session:
                tasks = [
                    self._fetch_team_game_stats(session, game_id),
                    self.fetch_play_by_play_data(game_id)
                ]

                team_stats, plays = await asyncio.gather(*tasks, return_exceptions=True)

                if not isinstance(team_stats, Exception) and not isinstance(plays, Exception):
                    return self._extract_special_teams_performance(team_stats, plays, game_id)
                else:
                    logger.error("Failed to fetch data for special teams analysis")
                    return []

        except Exception as e:
            logger.error(f"Error extracting special teams data: {e}")
            return []

    async def fetch_situational_performance(self, game_id: str) -> List[SituationalPerformance]:
        """Extract situational performance metrics"""
        logger.info(f"Extracting situational performance for game {game_id}")

        try:
            plays = await self.fetch_play_by_play_data(game_id)
            return self._extract_situational_performance(plays, game_id)

        except Exception as e:
            logger.error(f"Error extracting situational performance: {e}")
            return []

    # Internal methods for API calls
    async def _fetch_scores(self, session: aiohttp.ClientSession, season: int, week: int) -> List[Dict]:
        """Fetch basic score data"""
        url = f"{self.base_url}/scores/{season}/{week}"
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to fetch scores: {response.status}")
                return []

    async def _fetch_team_stats(self, session: aiohttp.ClientSession, season: int, week: int) -> List[Dict]:
        """Fetch team statistics"""
        url = f"{self.base_url}/teamgamestats/{season}/{week}"
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to fetch team stats: {response.status}")
                return []

    async def _fetch_advanced_metrics(self, session: aiohttp.ClientSession, season: int, week: int) -> List[Dict]:
        """Fetch advanced team metrics"""
        url = f"{self.base_url}/advancedteamstats/{season}"
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to fetch advanced metrics: {response.status}")
                return []

    async def _fetch_team_game_stats(self, session: aiohttp.ClientSession, game_id: str) -> List[Dict]:
        """Fetch team stats for specific game"""
        # Note: This would need the actual game ID format for SportsData.io
        # For now, return empty list as placeholder
        return []

    def _build_enhanced_game_data(self, game: Dict, stats_data: Any, metrics_data: Any) -> EnhancedGameData:
        """Build enhanced game data object from API responses"""

        # Extract basic game info
        game_id = str(game.get('GameID', game.get('GameKey', '')))
        season = game.get('Season', 2024)
        week = game.get('Week', 1)
        home_team = game.get('HomeTeam', '')
        away_team = game.get('AwayTeam', '')

        # Parse game date
        game_date = None
        if game.get('DateTime'):
            try:
                game_date = datetime.fromisoformat(game['DateTime'].replace('Z', '+00:00'))
            except:
                pass

        # Extract scores and status
        final_score_home = game.get('HomeScore')
        final_score_away = game.get('AwayScore')
        status = game.get('Status', '')

        # Extract stadium and weather info
        stadium_name = game.get('StadiumDetails', {}).get('Name') if game.get('StadiumDetails') else None
        attendance = game.get('Attendance')

        # Weather data (if available)
        weather_data = game.get('Weather', {})
        weather_temperature = weather_data.get('Temperature')
        weather_humidity = weather_data.get('Humidity')
        weather_wind_speed = weather_data.get('WindSpeed')
        weather_wind_direction = weather_data.get('WindDirection')
        weather_condition = weather_data.get('Description')

        # Find team stats for this game
        home_stats = {}
        away_stats = {}

        if stats_data and not isinstance(stats_data, Exception):
            for stat in stats_data:
                if stat.get('GameID') == game.get('GameID'):
                    if stat.get('Team') == home_team:
                        home_stats = stat
                    elif stat.get('Team') == away_team:
                        away_stats = stat

        # Extract team statistics
        home_first_downs = home_stats.get('FirstDowns')
        away_first_downs = away_stats.get('FirstDowns')
        home_total_yards = home_stats.get('TotalYards')
        away_total_yards = away_stats.get('TotalYards')
        home_passing_yards = home_stats.get('PassingYards')
        away_passing_yards = away_stats.get('PassingYards')
        home_rushing_yards = home_stats.get('RushingYards')
        away_rushing_yards = away_stats.get('RushingYards')

        # Efficiency metrics
        home_third_down_attempts = home_stats.get('ThirdDownAttempts')
        home_third_down_conversions = home_stats.get('ThirdDownConversions')
        away_third_down_attempts = away_stats.get('ThirdDownAttempts')
        away_third_down_conversions = away_stats.get('ThirdDownConversions')
        home_red_zone_attempts = home_stats.get('RedZoneAttempts')
        home_red_zone_scores = home_stats.get('RedZoneConversions')
        away_red_zone_attempts = away_stats.get('RedZoneAttempts')
        away_red_zone_scores = away_stats.get('RedZoneConversions')

        # Turnovers and penalties
        home_turnovers = home_stats.get('Turnovers')
        away_turnovers = away_stats.get('Turnovers')
        home_penalties = home_stats.get('Penalties')
        home_penalty_yards = home_stats.get('PenaltyYards')
        away_penalties = away_stats.get('Penalties')
        away_penalty_yards = away_stats.get('PenaltyYards')

        # Special teams
        home_punt_return_yards = home_stats.get('PuntReturnYards')
        away_punt_return_yards = away_stats.get('PuntReturnYards')
        home_kick_return_yards = home_stats.get('KickReturnYards')
        away_kick_return_yards = away_stats.get('KickReturnYards')

        # Time of possession
        home_time_of_possession = home_stats.get('TimeOfPossession')
        away_time_of_possession = away_stats.get('TimeOfPossession')

        # Game flow metrics
        total_plays = (home_stats.get('Plays', 0) + away_stats.get('Plays', 0)) or None
        overtime_periods = game.get('OverTime', 0) if game.get('OverTime') else None

        return EnhancedGameData(
            game_id=game_id,
            season=season,
            week=week,
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            final_score_home=final_score_home,
            final_score_away=final_score_away,
            status=status,
            weather_temperature=weather_temperature,
            weather_humidity=weather_humidity,
            weather_wind_speed=weather_wind_speed,
            weather_wind_direction=weather_wind_direction,
            weather_condition=weather_condition,
            stadium_name=stadium_name,
            attendance=attendance,
            total_plays=total_plays,
            overtime_periods=overtime_periods,
            home_time_of_possession=home_time_of_possession,
            away_time_of_possession=away_time_of_possession,
            home_first_downs=home_first_downs,
            away_first_downs=away_first_downs,
            home_total_yards=home_total_yards,
            away_total_yards=away_total_yards,
            home_passing_yards=home_passing_yards,
            away_passing_yards=away_passing_yards,
            home_rushing_yards=home_rushing_yards,
            away_rushing_yards=away_rushing_yards,
            home_third_down_attempts=home_third_down_attempts,
            home_third_down_conversions=home_third_down_conversions,
            away_third_down_attempts=away_third_down_attempts,
            away_third_down_conversions=away_third_down_conversions,
            home_red_zone_attempts=home_red_zone_attempts,
            home_red_zone_scores=home_red_zone_scores,
            away_red_zone_attempts=away_red_zone_attempts,
            away_red_zone_scores=away_red_zone_scores,
            home_turnovers=home_turnovers,
            away_turnovers=away_turnovers,
            home_penalties=home_penalties,
            home_penalty_yards=home_penalty_yards,
            away_penalties=away_penalties,
            away_penalty_yards=away_penalty_yards,
            home_punt_return_yards=home_punt_return_yards,
            away_punt_return_yards=away_punt_return_yards,
            home_kick_return_yards=home_kick_return_yards,
            away_kick_return_yards=away_kick_return_yards,
            raw_score_data=game,
            raw_stats_data={"home": home_stats, "away": away_stats},
            raw_advanced_metrics=metrics_data if not isinstance(metrics_data, Exception) else None
        )

    def _process_play_by_play_data(self, data: Dict, game_id: str) -> List[GamePlayByPlay]:
        """Process play-by-play API response into structured data"""
        plays = []

        if not data or 'Plays' not in data:
            return plays

        for play_data in data['Plays']:
            play = GamePlayByPlay(
                game_id=game_id,
                play_id=str(play_data.get('PlayID', '')),
                quarter=play_data.get('Quarter'),
                time_remaining=play_data.get('TimeRemaining'),
                down=play_data.get('Down'),
                yards_to_go=play_data.get('YardsToGo'),
                yard_line=play_data.get('YardLine'),
                possession_team=play_data.get('Team'),
                play_type=play_data.get('Type'),
                play_description=play_data.get('Description'),
                yards_gained=play_data.get('Yards'),
                is_touchdown=play_data.get('IsTouchdown', False),
                is_field_goal=play_data.get('IsFieldGoal', False),
                is_safety=play_data.get('IsSafety', False),
                is_turnover=play_data.get('IsTurnover', False),
                is_penalty=play_data.get('IsPenalty', False),
                primary_player=play_data.get('Player'),
                is_red_zone=play_data.get('YardLine', 100) <= 20 if play_data.get('YardLine') else False,
                is_goal_to_go=play_data.get('YardsToGo', 0) >= play_data.get('YardLine', 100) if play_data.get('YardsToGo') and play_data.get('YardLine') else False,
                is_fourth_down=play_data.get('Down') == 4,
                is_two_minute_warning=self._is_two_minute_warning(play_data.get('TimeRemaining'), play_data.get('Quarter')),
                raw_play_data=play_data
            )
            plays.append(play)

        return plays

    def _extract_drive_data(self, plays: List[GamePlayByPlay], game_id: str) -> List[GameDrive]:
        """Extract drive data from play-by-play"""
        drives = []
        current_drive = None
        drive_id_counter = 1

        for play in plays:
            # Start new drive on possession change or game start
            if (current_drive is None or
                current_drive.possession_team != play.possession_team or
                play.is_turnover or
                play.is_touchdown or
                play.is_field_goal or
                play.is_safety):

                # Finalize previous drive
                if current_drive:
                    self._finalize_drive(current_drive)
                    drives.append(current_drive)

                # Start new drive
                current_drive = GameDrive(
                    game_id=game_id,
                    drive_id=f"{game_id}_drive_{drive_id_counter}",
                    quarter=play.quarter,
                    possession_team=play.possession_team,
                    starting_field_position=play.yard_line,
                    total_plays=0,
                    total_yards=0
                )
                drive_id_counter += 1

            # Update current drive
            if current_drive and play.possession_team == current_drive.possession_team:
                current_drive.total_plays = (current_drive.total_plays or 0) + 1
                current_drive.total_yards = (current_drive.total_yards or 0) + (play.yards_gained or 0)
                current_drive.ending_field_position = play.yard_line

                # Determine drive result
                if play.is_touchdown:
                    current_drive.drive_result = "touchdown"
                    current_drive.is_scoring_drive = True
                elif play.is_field_goal:
                    current_drive.drive_result = "field_goal"
                    current_drive.is_scoring_drive = True
                elif play.is_turnover:
                    current_drive.drive_result = "turnover"
                elif play.is_safety:
                    current_drive.drive_result = "safety"

        # Finalize last drive
        if current_drive:
            self._finalize_drive(current_drive)
            drives.append(current_drive)

        return drives

    def _finalize_drive(self, drive: GameDrive):
        """Finalize drive calculations"""
        if drive.total_plays and drive.total_yards:
            drive.yards_per_play = Decimal(str(drive.total_yards / drive.total_plays)).quantize(Decimal('0.01'))
            if drive.total_yards > 0:
                drive.plays_per_yard = Decimal(str(drive.total_plays / drive.total_yards)).quantize(Decimal('0.01'))

        # Check for three and out
        if drive.total_plays == 3 and not drive.is_scoring_drive:
            drive.is_three_and_out = True

        # Default drive result if not set
        if not drive.drive_result:
            drive.drive_result = "punt"

    def _analyze_coaching_decisions(self, plays: List[GamePlayByPlay], game_id: str) -> List[CoachingDecision]:
        """Analyze coaching decisions from play-by-play data"""
        decisions = []

        for play in plays:
            # Fourth down decisions
            if play.is_fourth_down and play.down == 4:
                decision = CoachingDecision(
                    game_id=game_id,
                    team=play.possession_team,
                    quarter=play.quarter,
                    situation="fourth_down",
                    decision_type=self._classify_fourth_down_decision(play),
                    decision_description=play.play_description,
                    outcome="successful" if (play.yards_gained or 0) >= (play.yards_to_go or 0) else "failed",
                    game_state={
                        "quarter": play.quarter,
                        "time_remaining": play.time_remaining,
                        "yard_line": play.yard_line,
                        "yards_to_go": play.yards_to_go
                    }
                )
                decisions.append(decision)

            # Two-point conversion attempts
            if "two point" in (play.play_description or "").lower():
                decision = CoachingDecision(
                    game_id=game_id,
                    team=play.possession_team,
                    quarter=play.quarter,
                    situation="two_point_conversion",
                    decision_type="attempt_two_point",
                    decision_description=play.play_description,
                    outcome="successful" if play.is_touchdown else "failed"
                )
                decisions.append(decision)

        return decisions

    def _classify_fourth_down_decision(self, play: GamePlayByPlay) -> str:
        """Classify type of fourth down decision"""
        if play.is_field_goal:
            return "field_goal_attempt"
        elif "punt" in (play.play_description or "").lower():
            return "punt"
        else:
            return "go_for_it"

    def _extract_special_teams_performance(self, team_stats: List[Dict], plays: List[GamePlayByPlay], game_id: str) -> List[SpecialTeamsPerformance]:
        """Extract special teams performance from stats and plays"""
        teams = set()
        for play in plays:
            if play.possession_team:
                teams.add(play.possession_team)

        st_performance = []

        for team in teams:
            # Count special teams plays
            field_goal_attempts = sum(1 for play in plays if play.possession_team == team and play.is_field_goal)
            field_goals_made = sum(1 for play in plays if play.possession_team == team and play.is_field_goal and "good" in (play.play_description or "").lower())

            # Extract other ST metrics from team stats if available
            team_stat = next((stat for stat in team_stats if stat.get('Team') == team), {})

            performance = SpecialTeamsPerformance(
                game_id=game_id,
                team=team,
                field_goal_attempts=field_goal_attempts,
                field_goals_made=field_goals_made,
                extra_point_attempts=team_stat.get('ExtraPointAttempts', 0),
                extra_points_made=team_stat.get('ExtraPointsMade', 0),
                punts=team_stat.get('Punts', 0),
                punt_yards=team_stat.get('PuntYards', 0),
                kickoff_returns=team_stat.get('KickoffReturns', 0),
                kickoff_return_yards=team_stat.get('KickoffReturnYards', 0),
                punt_returns=team_stat.get('PuntReturns', 0),
                punt_return_yards=team_stat.get('PuntReturnYards', 0)
            )

            # Calculate efficiency scores
            if performance.field_goal_attempts > 0:
                fg_pct = performance.field_goals_made / performance.field_goal_attempts
                performance.special_teams_score = Decimal(str(fg_pct * 100)).quantize(Decimal('0.01'))

            st_performance.append(performance)

        return st_performance

    def _extract_situational_performance(self, plays: List[GamePlayByPlay], game_id: str) -> List[SituationalPerformance]:
        """Extract situational performance metrics"""
        teams = set()
        for play in plays:
            if play.possession_team:
                teams.add(play.possession_team)

        situational_performance = []

        for team in teams:
            team_plays = [play for play in plays if play.possession_team == team]

            # Final 2 minutes performance
            final_2_min_plays = [play for play in team_plays if self._is_final_2_minutes(play.time_remaining, play.quarter)]
            points_final_2_minutes = sum(6 if play.is_touchdown else 3 if play.is_field_goal else 0 for play in final_2_min_plays)

            # Fourth down performance
            fourth_down_plays = [play for play in team_plays if play.is_fourth_down]
            fourth_down_attempts = len(fourth_down_plays)
            fourth_down_conversions = sum(1 for play in fourth_down_plays if (play.yards_gained or 0) >= (play.yards_to_go or 0))

            # Red zone performance
            red_zone_plays = [play for play in team_plays if play.is_red_zone]
            red_zone_trips = len(set(f"{play.quarter}_{play.time_remaining}" for play in red_zone_plays))
            red_zone_touchdowns = sum(1 for play in red_zone_plays if play.is_touchdown)

            performance = SituationalPerformance(
                game_id=game_id,
                team=team,
                points_final_2_minutes=points_final_2_minutes,
                fourth_down_attempts=fourth_down_attempts,
                fourth_down_conversions=fourth_down_conversions,
                red_zone_trips=red_zone_trips,
                red_zone_touchdowns=red_zone_touchdowns
            )

            situational_performance.append(performance)

        return situational_performance

    def _is_two_minute_warning(self, time_remaining: str, quarter: int) -> bool:
        """Check if play is at two minute warning"""
        if not time_remaining or quarter not in [2, 4]:
            return False

        try:
            # Parse time format MM:SS
            parts = time_remaining.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
                return total_seconds <= 120  # 2 minutes = 120 seconds
        except:
            pass

        return False

    def _is_final_2_minutes(self, time_remaining: str, quarter: int) -> bool:
        """Check if play is in final 2 minutes of either half"""
        if not time_remaining or quarter not in [2, 4]:
            return False

        try:
            parts = time_remaining.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                return minutes <= 2
        except:
            pass

        return False

# Example usage and testing
async def main():
    """Test the enhanced data fetcher"""

    # Get API key from environment
    api_key = os.getenv('SPORTSDATA_IO_KEY', 'bc297647c7aa4ef29747e6a85cb575dc')

    if not api_key:
        logger.error("SPORTSDATA_IO_KEY environment variable not set")
        return

    fetcher = EnhancedDataFetcher(api_key)

    # Test fetching enhanced game data for current week
    season = 2024
    week = 18

    logger.info(f"Testing enhanced data fetcher for {season} Week {week}")

    # Fetch enhanced game data
    enhanced_games = await fetcher.fetch_enhanced_game_data(season, week)
    logger.info(f"Fetched {len(enhanced_games)} enhanced games")

    # Test detailed data for first game
    if enhanced_games:
        game = enhanced_games[0]
        logger.info(f"Testing detailed data for game: {game.game_id}")

        # Fetch play-by-play
        plays = await fetcher.fetch_play_by_play_data(game.game_id)
        logger.info(f"Fetched {len(plays)} plays")

        # Extract drives
        drives = await fetcher.fetch_drive_data(game.game_id)
        logger.info(f"Extracted {len(drives)} drives")

        # Analyze coaching decisions
        decisions = await fetcher.fetch_coaching_decisions(game.game_id)
        logger.info(f"Analyzed {len(decisions)} coaching decisions")

        # Extract special teams
        st_performance = await fetcher.fetch_special_teams_data(game.game_id)
        logger.info(f"Extracted special teams data for {len(st_performance)} teams")

        # Extract situational performance
        situational = await fetcher.fetch_situational_performance(game.game_id)
        logger.info(f"Extracted situational data for {len(situational)} teams")

        # Print sample data
        print(f"\nSample Enhanced Game Data:")
        print(f"Game: {game.home_team} vs {game.away_team}")
        print(f"Score: {game.final_score_home} - {game.final_score_away}")
        print(f"Stadium: {game.stadium_name}")
        print(f"Weather: {game.weather_condition}, {game.weather_temperature}°F")

        if plays:
            print(f"\nSample Play: {plays[0].play_description}")

        if drives:
            print(f"\nSample Drive: {drives[0].possession_team} - {drives[0].total_plays} plays, {drives[0].total_yards} yards, {drives[0].drive_result}")

if __name__ == "__main__":
    asyncio.run(main())