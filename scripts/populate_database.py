"""
Database population script for historical NFL data.
Processes raw API data, calculates derived metrics, and stores in database.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Import our models
from database.models.historical_games import (
    Base, HistoricalGame, TeamStats, PlayerStats, BettingData, Injury,
    create_all_tables, get_performance_indexes
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePopulator:
    """Processes raw historical data and populates database"""

    def __init__(self, db_type: str = None):
        self.db_type = db_type or os.getenv('DB_TYPE', 'sqlite')
        self.engine = None
        self.Session = None
        self.setup_database()

        # EPA calculation parameters
        self.epa_model_params = {
            'field_position_weight': 0.1,
            'down_distance_weight': 0.3,
            'time_weight': 0.2,
            'score_weight': 0.4
        }

    def setup_database(self):
        """Initialize database connection and create tables"""
        if self.db_type.lower() == 'postgresql':
            db_url = (
                f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
                f"{os.getenv('DB_PASSWORD', '')}@"
                f"{os.getenv('DB_HOST', 'localhost')}:"
                f"{os.getenv('DB_PORT', 5432)}/"
                f"{os.getenv('DB_NAME', 'nfl_predictor')}"
            )
        else:
            # SQLite for development
            db_path = os.getenv('DB_PATH', 'data/nfl_historical.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

        # Create tables
        create_all_tables(self.engine)
        logger.info("Database tables created successfully")

    def load_raw_data_files(self, data_dir: str = "data/raw") -> List[Dict]:
        """Load all raw JSON data files"""
        raw_data = []
        data_path = Path(data_dir)

        if not data_path.exists():
            logger.error(f"Raw data directory {data_dir} does not exist")
            return raw_data

        json_files = list(data_path.glob("*_raw.json"))
        logger.info(f"Found {len(json_files)} raw data files")

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    raw_data.append(data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
                continue

        logger.info(f"Loaded {len(raw_data)} raw data records")
        return raw_data

    def calculate_epa(self, play_data: Dict) -> float:
        """
        Calculate Expected Points Added (EPA) for a play.
        Simplified implementation - in production, use more sophisticated model.
        """
        try:
            # Basic EPA calculation based on field position, down, distance
            field_position = play_data.get('yard_line', 50)
            down = play_data.get('down', 1)
            distance = play_data.get('yards_to_go', 10)

            # Normalize field position (0-100, where 100 is opponent's goal line)
            if field_position <= 50:
                norm_field_pos = 50 + (50 - field_position)
            else:
                norm_field_pos = field_position

            # Base EPA from field position (closer to goal = higher EPA)
            base_epa = (norm_field_pos / 100) * 7  # Max 7 points (touchdown)

            # Down and distance penalties
            down_penalty = (down - 1) * 0.5  # Each down reduces expected value
            distance_penalty = min(distance / 10, 1.0) * 1.0  # Long distance penalty

            epa = base_epa - down_penalty - distance_penalty
            return round(epa, 2)

        except Exception as e:
            logger.debug(f"EPA calculation error: {e}")
            return 0.0

    def calculate_success_rate_metrics(self, team_stats: Dict, play_by_play: List = None) -> Dict[str, float]:
        """Calculate success rate and other advanced metrics"""
        metrics = {
            'success_rate': 0.0,
            'passing_success_rate': 0.0,
            'rushing_success_rate': 0.0,
            'explosive_plays': 0,
            'three_and_outs': 0,
            'yards_per_play': 0.0,
            'epa_per_play': 0.0
        }

        try:
            # Basic calculations from team stats
            total_plays = (team_stats.get('passing_attempts', 0) +
                          team_stats.get('rushing_attempts', 0))

            if total_plays > 0:
                total_yards = team_stats.get('total_yards', 0)
                metrics['yards_per_play'] = round(total_yards / total_plays, 2)

            # Success rate approximation (in absence of play-by-play)
            # Based on efficiency metrics
            third_down_rate = team_stats.get('third_down_efficiency', 0) / 100.0
            red_zone_rate = team_stats.get('red_zone_efficiency', 0) / 100.0

            # Weighted average of efficiency metrics as success rate proxy
            metrics['success_rate'] = round((third_down_rate * 0.4 + red_zone_rate * 0.6), 3)

            # Estimate passing/rushing success rates
            completion_rate = 0
            if team_stats.get('passing_attempts', 0) > 0:
                completion_rate = team_stats.get('completions', 0) / team_stats.get('passing_attempts', 0)

            metrics['passing_success_rate'] = round(completion_rate * 1.2, 3)  # Adjust for successful vs completion

            # Rushing success rate approximation
            rushing_attempts = team_stats.get('rushing_attempts', 0)
            if rushing_attempts > 0:
                rushing_ypa = team_stats.get('rushing_yards', 0) / rushing_attempts
                metrics['rushing_success_rate'] = round(min(rushing_ypa / 4.0, 1.0), 3)  # 4+ yards = success

            # Estimate explosive plays (20+ yard plays)
            # Rough approximation based on total yards and attempts
            avg_yards_per_play = metrics['yards_per_play']
            if avg_yards_per_play > 6.0:  # Above average indicates explosive plays
                metrics['explosive_plays'] = max(1, int(total_plays * 0.15))  # 15% estimate

            return metrics

        except Exception as e:
            logger.debug(f"Success rate calculation error: {e}")
            return metrics

    def process_game_data(self, raw_game: Dict) -> Optional[HistoricalGame]:
        """Process raw game data into HistoricalGame model"""
        try:
            game_info = raw_game.get('game_info', {})
            weather = raw_game.get('weather')
            betting = raw_game.get('betting_data')

            # Parse game date
            game_date_str = game_info.get('DateTime') or game_info.get('Date')
            game_date = None
            if game_date_str:
                try:
                    game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                except:
                    try:
                        game_date = datetime.strptime(game_date_str[:19], '%Y-%m-%dT%H:%M:%S')
                    except:
                        logger.warning(f"Could not parse date: {game_date_str}")

            # Calculate derived metrics
            home_score = game_info.get('HomeScore', 0) or 0
            away_score = game_info.get('AwayScore', 0) or 0
            total_points = home_score + away_score
            point_differential = home_score - away_score

            # Determine if it's an upset (simplified - would need betting data)
            is_upset = None
            if betting and betting.get('point_spread_home'):
                spread = betting['point_spread_home']
                is_upset = (spread < 0 and point_differential < 0) or (spread > 0 and point_differential > 0)

            game = HistoricalGame(
                game_key=game_info.get('GameKey'),
                season=game_info.get('Season'),
                season_type=game_info.get('SeasonType', 'Regular'),
                week=game_info.get('Week'),
                game_date=game_date,
                home_team=game_info.get('HomeTeam'),
                away_team=game_info.get('AwayTeam'),
                home_score=home_score,
                away_score=away_score,
                home_score_quarter1=game_info.get('HomeScoreQuarter1'),
                home_score_quarter2=game_info.get('HomeScoreQuarter2'),
                home_score_quarter3=game_info.get('HomeScoreQuarter3'),
                home_score_quarter4=game_info.get('HomeScoreQuarter4'),
                home_score_overtime=game_info.get('HomeScoreOvertime'),
                away_score_quarter1=game_info.get('AwayScoreQuarter1'),
                away_score_quarter2=game_info.get('AwayScoreQuarter2'),
                away_score_quarter3=game_info.get('AwayScoreQuarter3'),
                away_score_quarter4=game_info.get('AwayScoreQuarter4'),
                away_score_overtime=game_info.get('AwayScoreOvertime'),
                is_final=game_info.get('IsFinal', False),
                is_overtime=game_info.get('IsOvertime', False),
                stadium_name=game_info.get('StadiumDetails', {}).get('Name'),
                stadium_city=game_info.get('StadiumDetails', {}).get('City'),
                stadium_state=game_info.get('StadiumDetails', {}).get('State'),
                playing_surface=game_info.get('StadiumDetails', {}).get('PlayingSurface'),
                is_dome=game_info.get('StadiumDetails', {}).get('Type') == 'Dome',
                # Weather data
                temperature=weather.get('Temperature') if weather else None,
                humidity=weather.get('Humidity') if weather else None,
                wind_speed=weather.get('WindSpeed') if weather else None,
                wind_direction=weather.get('WindDirection') if weather else None,
                weather_conditions=weather.get('Conditions') if weather else None,
                # Betting data
                point_spread=betting.get('PointSpread') if betting else None,
                over_under=betting.get('OverUnder') if betting else None,
                home_moneyline=betting.get('HomeMoneyLine') if betting else None,
                away_moneyline=betting.get('AwayMoneyLine') if betting else None,
                # Derived metrics
                total_points=total_points,
                point_differential=point_differential,
                is_upset=is_upset,
                is_high_scoring=total_points > 45,  # Above average threshold
            )

            return game

        except Exception as e:
            logger.error(f"Error processing game data: {e}")
            return None

    def process_team_stats(self, raw_game: Dict, game_id: int) -> List[TeamStats]:
        """Process team statistics for a game"""
        team_stats_list = []

        try:
            game_info = raw_game.get('game_info', {})
            team_stats_data = raw_game.get('team_stats', [])
            game_key = game_info.get('GameKey')
            home_team = game_info.get('HomeTeam')
            away_team = game_info.get('AwayTeam')

            # If no team stats in data, create basic records
            if not team_stats_data:
                team_stats_data = [
                    {'Team': home_team, 'IsHome': True},
                    {'Team': away_team, 'IsHome': False}
                ]

            for team_data in team_stats_data:
                team = team_data.get('Team')
                is_home = team_data.get('IsHome', team == home_team)
                opponent = away_team if is_home else home_team

                # Calculate advanced metrics
                advanced_metrics = self.calculate_success_rate_metrics(team_data)

                # Calculate turnover margin (simplified)
                turnovers = team_data.get('Turnovers', 0)
                interceptions_forced = team_data.get('InterceptionsDefense', 0)
                fumbles_forced = team_data.get('FumblesForced', 0)
                turnover_margin = (interceptions_forced + fumbles_forced) - turnovers

                team_stats = TeamStats(
                    game_id=game_id,
                    game_key=game_key,
                    team=team,
                    is_home=is_home,
                    opponent=opponent,
                    points=team_data.get('Points', 0),
                    first_downs=team_data.get('FirstDowns'),
                    total_yards=team_data.get('TotalYards'),
                    passing_yards=team_data.get('PassingYards'),
                    rushing_yards=team_data.get('RushingYards'),
                    penalties=team_data.get('Penalties'),
                    penalty_yards=team_data.get('PenaltyYards'),
                    turnovers=turnovers,
                    fumbles_lost=team_data.get('FumblesLost'),
                    interceptions_thrown=team_data.get('InterceptionsThrown'),
                    completions=team_data.get('PassingCompletions'),
                    passing_attempts=team_data.get('PassingAttempts'),
                    passing_touchdowns=team_data.get('PassingTouchdowns'),
                    qb_rating=team_data.get('QuarterbackRating'),
                    sacks_allowed=team_data.get('SacksAllowed'),
                    sack_yards_lost=team_data.get('SackYards'),
                    rushing_attempts=team_data.get('RushingAttempts'),
                    rushing_touchdowns=team_data.get('RushingTouchdowns'),
                    red_zone_attempts=team_data.get('RedZoneAttempts'),
                    red_zone_scores=team_data.get('RedZoneScores'),
                    third_down_attempts=team_data.get('ThirdDownAttempts'),
                    third_down_conversions=team_data.get('ThirdDownConversions'),
                    time_of_possession_seconds=team_data.get('TimeOfPossessionSeconds'),
                    # Calculated fields
                    yards_per_play=advanced_metrics['yards_per_play'],
                    turnover_margin=turnover_margin,
                    explosive_plays=advanced_metrics['explosive_plays'],
                    three_and_outs=advanced_metrics['three_and_outs'],
                    success_rate=advanced_metrics['success_rate'],
                    passing_success_rate=advanced_metrics['passing_success_rate'],
                    rushing_success_rate=advanced_metrics['rushing_success_rate'],
                    epa_per_play=advanced_metrics['epa_per_play'],
                    # Calculate efficiency percentages
                    red_zone_efficiency=(
                        (team_data.get('RedZoneScores', 0) / max(team_data.get('RedZoneAttempts', 1), 1)) * 100
                        if team_data.get('RedZoneAttempts', 0) > 0 else None
                    ),
                    third_down_efficiency=(
                        (team_data.get('ThirdDownConversions', 0) / max(team_data.get('ThirdDownAttempts', 1), 1)) * 100
                        if team_data.get('ThirdDownAttempts', 0) > 0 else None
                    ),
                    rushing_yards_per_attempt=(
                        team_data.get('RushingYards', 0) / max(team_data.get('RushingAttempts', 1), 1)
                        if team_data.get('RushingAttempts', 0) > 0 else None
                    ),
                    time_of_possession_percentage=(
                        team_data.get('TimeOfPossessionSeconds', 0) / (60 * 60) * 100  # Convert to percentage of 60 minutes
                        if team_data.get('TimeOfPossessionSeconds', 0) > 0 else None
                    )
                )

                team_stats_list.append(team_stats)

        except Exception as e:
            logger.error(f"Error processing team stats: {e}")

        return team_stats_list

    def process_player_stats(self, raw_game: Dict, game_id: int) -> List[PlayerStats]:
        """Process player statistics for a game"""
        player_stats_list = []

        try:
            game_info = raw_game.get('game_info', {})
            player_stats_data = raw_game.get('player_stats', [])
            game_key = game_info.get('GameKey')

            for player_data in player_stats_data:
                # Calculate fantasy points (standard scoring)
                fantasy_points = 0
                fantasy_points += (player_data.get('PassingYards', 0) * 0.04)  # 1 pt per 25 yards
                fantasy_points += (player_data.get('PassingTouchdowns', 0) * 4)  # 4 pts per TD
                fantasy_points += (player_data.get('RushingYards', 0) * 0.1)  # 1 pt per 10 yards
                fantasy_points += (player_data.get('RushingTouchdowns', 0) * 6)  # 6 pts per TD
                fantasy_points += (player_data.get('ReceivingYards', 0) * 0.1)  # 1 pt per 10 yards
                fantasy_points += (player_data.get('ReceivingTouchdowns', 0) * 6)  # 6 pts per TD
                fantasy_points += (player_data.get('Receptions', 0))  # 1 pt per reception (PPR)
                fantasy_points -= (player_data.get('Interceptions', 0) * 2)  # -2 pts per INT
                fantasy_points -= (player_data.get('FumblesLost', 0) * 2)  # -2 pts per fumble lost

                fantasy_points_ppr = fantasy_points  # Already included receptions above

                player_stats = PlayerStats(
                    game_id=game_id,
                    game_key=game_key,
                    player_id=str(player_data.get('PlayerID', '')),
                    player_name=player_data.get('Name', ''),
                    team=player_data.get('Team', ''),
                    position=player_data.get('Position', ''),
                    jersey_number=player_data.get('Number'),
                    # Passing
                    passing_attempts=player_data.get('PassingAttempts'),
                    passing_completions=player_data.get('PassingCompletions'),
                    passing_yards=player_data.get('PassingYards'),
                    passing_touchdowns=player_data.get('PassingTouchdowns'),
                    interceptions=player_data.get('PassingInterceptions'),
                    qb_rating=player_data.get('PassingRating'),
                    longest_pass=player_data.get('PassingLong'),
                    times_sacked=player_data.get('PassingSacked'),
                    sack_yards=player_data.get('PassingSackYards'),
                    # Rushing
                    rushing_attempts=player_data.get('RushingAttempts'),
                    rushing_yards=player_data.get('RushingYards'),
                    rushing_touchdowns=player_data.get('RushingTouchdowns'),
                    longest_rush=player_data.get('RushingLong'),
                    fumbles=player_data.get('Fumbles'),
                    fumbles_lost=player_data.get('FumblesLost'),
                    # Receiving
                    receptions=player_data.get('Receptions'),
                    receiving_yards=player_data.get('ReceivingYards'),
                    receiving_touchdowns=player_data.get('ReceivingTouchdowns'),
                    targets=player_data.get('ReceivingTargets'),
                    longest_reception=player_data.get('ReceivingLong'),
                    # Kicking
                    field_goals_made=player_data.get('FieldGoalsMade'),
                    field_goals_attempted=player_data.get('FieldGoalsAttempted'),
                    field_goal_percentage=player_data.get('FieldGoalPercentage'),
                    longest_field_goal=player_data.get('FieldGoalsLongestMade'),
                    extra_points_made=player_data.get('ExtraPointsMade'),
                    extra_points_attempted=player_data.get('ExtraPointsAttempted'),
                    # Defense
                    tackles=player_data.get('Tackles'),
                    solo_tackles=player_data.get('TacklesSolo'),
                    assisted_tackles=player_data.get('TacklesAssisted'),
                    sacks=player_data.get('Sacks'),
                    quarterback_hits=player_data.get('QuarterbackHits'),
                    tackles_for_loss=player_data.get('TacklesForLoss'),
                    interceptions_defense=player_data.get('Interceptions'),
                    passes_defended=player_data.get('PassesDefended'),
                    fumbles_forced=player_data.get('FumblesForced'),
                    fumbles_recovered=player_data.get('FumblesRecovered'),
                    defensive_touchdowns=player_data.get('DefensiveTouchdowns'),
                    # Special teams
                    punt_returns=player_data.get('PuntReturns'),
                    punt_return_yards=player_data.get('PuntReturnYards'),
                    punt_return_touchdowns=player_data.get('PuntReturnTouchdowns'),
                    kick_returns=player_data.get('KickReturns'),
                    kick_return_yards=player_data.get('KickReturnYards'),
                    kick_return_touchdowns=player_data.get('KickReturnTouchdowns'),
                    # Fantasy
                    fantasy_points=round(fantasy_points, 2),
                    fantasy_points_ppr=round(fantasy_points_ppr, 2),
                )

                player_stats_list.append(player_stats)

        except Exception as e:
            logger.error(f"Error processing player stats: {e}")

        return player_stats_list

    def process_betting_data(self, raw_game: Dict, game_id: int) -> List[BettingData]:
        """Process betting data for a game"""
        betting_data_list = []

        try:
            betting = raw_game.get('betting_data')
            if not betting:
                return betting_data_list

            game_info = raw_game.get('game_info', {})
            game_key = game_info.get('GameKey')

            # Determine outcomes
            home_score = game_info.get('HomeScore', 0) or 0
            away_score = game_info.get('AwayScore', 0) or 0
            total_score = home_score + away_score
            point_diff = home_score - away_score

            # Calculate outcomes
            spread_result = None
            total_result = None
            moneyline_result = None

            if betting.get('PointSpread') is not None:
                spread = betting['PointSpread']
                spread_adjusted_home = point_diff + spread
                if spread_adjusted_home > 0:
                    spread_result = "Home_Cover"
                elif spread_adjusted_home < 0:
                    spread_result = "Away_Cover"
                else:
                    spread_result = "Push"

            if betting.get('OverUnder') is not None:
                over_under = betting['OverUnder']
                if total_score > over_under:
                    total_result = "Over"
                elif total_score < over_under:
                    total_result = "Under"
                else:
                    total_result = "Push"

            if point_diff > 0:
                moneyline_result = "Home_Win"
            elif point_diff < 0:
                moneyline_result = "Away_Win"
            else:
                moneyline_result = "Tie"

            betting_record = BettingData(
                game_id=game_id,
                game_key=game_key,
                sportsbook="Unknown",  # Would need to be provided in data
                line_type="Closing",   # Assume closing lines
                point_spread_home=betting.get('PointSpread'),
                point_spread_away=-betting.get('PointSpread') if betting.get('PointSpread') else None,
                over_under=betting.get('OverUnder'),
                moneyline_home=betting.get('HomeMoneyLine'),
                moneyline_away=betting.get('AwayMoneyLine'),
                spread_result=spread_result,
                total_result=total_result,
                moneyline_result=moneyline_result,
            )

            betting_data_list.append(betting_record)

        except Exception as e:
            logger.error(f"Error processing betting data: {e}")

        return betting_data_list

    def process_injuries(self, raw_game: Dict, game_id: int) -> List[Injury]:
        """Process injury data for a game"""
        injury_list = []

        try:
            injuries = raw_game.get('injuries', [])
            game_info = raw_game.get('game_info', {})
            game_key = game_info.get('GameKey')

            for injury_data in injuries:
                # Determine if player is key (simplified - based on position)
                position = injury_data.get('Position', '')
                is_key_player = position in ['QB', 'RB', 'WR', 'TE', 'LT', 'RT', 'C']

                injury = Injury(
                    game_id=game_id,
                    game_key=game_key,
                    player_id=str(injury_data.get('PlayerID', '')),
                    player_name=injury_data.get('Name', ''),
                    team=injury_data.get('Team', ''),
                    position=position,
                    jersey_number=injury_data.get('Number'),
                    injury_status=injury_data.get('Status', ''),
                    injury_type=injury_data.get('InjuryType'),
                    injury_body_part=injury_data.get('BodyPart'),
                    injury_description=injury_data.get('Description'),
                    report_date=datetime.now(),  # Would be better to get actual report date
                    is_key_player=is_key_player,
                )

                injury_list.append(injury)

        except Exception as e:
            logger.error(f"Error processing injury data: {e}")

        return injury_list

    def create_performance_indexes(self):
        """Create additional database indexes for performance"""
        try:
            indexes = get_performance_indexes()
            with self.engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                    except Exception as e:
                        logger.debug(f"Index creation skipped (may already exist): {e}")
                conn.commit()

            logger.info("Performance indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating performance indexes: {e}")

    def validate_data_integrity(self, session: Session):
        """Validate data integrity and log statistics"""
        try:
            # Count records
            game_count = session.query(HistoricalGame).count()
            team_stats_count = session.query(TeamStats).count()
            player_stats_count = session.query(PlayerStats).count()
            betting_count = session.query(BettingData).count()
            injury_count = session.query(Injury).count()

            logger.info(f"Data integrity check:")
            logger.info(f"  Games: {game_count}")
            logger.info(f"  Team Stats: {team_stats_count}")
            logger.info(f"  Player Stats: {player_stats_count}")
            logger.info(f"  Betting Records: {betting_count}")
            logger.info(f"  Injury Records: {injury_count}")

            # Check for orphaned records
            orphaned_team_stats = session.execute(text("""
                SELECT COUNT(*) FROM team_stats ts
                LEFT JOIN historical_games hg ON ts.game_id = hg.id
                WHERE hg.id IS NULL
            """)).scalar()

            if orphaned_team_stats > 0:
                logger.warning(f"Found {orphaned_team_stats} orphaned team stats records")

            # Check for games with missing stats
            games_without_stats = session.execute(text("""
                SELECT COUNT(*) FROM historical_games hg
                LEFT JOIN team_stats ts ON hg.id = ts.game_id
                WHERE ts.game_id IS NULL
            """)).scalar()

            if games_without_stats > 0:
                logger.warning(f"Found {games_without_stats} games without team stats")

            # Season distribution
            season_counts = session.execute(text("""
                SELECT season, COUNT(*) as game_count
                FROM historical_games
                GROUP BY season
                ORDER BY season DESC
            """)).fetchall()

            logger.info("Games by season:")
            for season, count in season_counts:
                logger.info(f"  {season}: {count} games")

        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")

    def populate_database(self, raw_data: List[Dict] = None):
        """Main method to populate database from raw data"""
        if raw_data is None:
            raw_data = self.load_raw_data_files()

        if not raw_data:
            logger.error("No raw data found to process")
            return

        session = self.Session()
        processed_count = 0
        error_count = 0

        try:
            for raw_game in raw_data:
                try:
                    # Check if game already exists
                    game_key = raw_game.get('game_info', {}).get('GameKey')
                    if not game_key:
                        logger.warning("Skipping game with no GameKey")
                        continue

                    existing_game = session.query(HistoricalGame).filter_by(game_key=game_key).first()
                    if existing_game:
                        logger.debug(f"Game {game_key} already exists, skipping")
                        continue

                    # Process main game record
                    game = self.process_game_data(raw_game)
                    if not game:
                        error_count += 1
                        continue

                    session.add(game)
                    session.flush()  # Get the game ID

                    # Process related data
                    team_stats = self.process_team_stats(raw_game, game.id)
                    for ts in team_stats:
                        session.add(ts)

                    player_stats = self.process_player_stats(raw_game, game.id)
                    for ps in player_stats:
                        session.add(ps)

                    betting_data = self.process_betting_data(raw_game, game.id)
                    for bd in betting_data:
                        session.add(bd)

                    injuries = self.process_injuries(raw_game, game.id)
                    for injury in injuries:
                        session.add(injury)

                    processed_count += 1

                    if processed_count % 50 == 0:
                        session.commit()
                        logger.info(f"Processed {processed_count} games...")

                except IntegrityError as e:
                    session.rollback()
                    logger.warning(f"Integrity error for game {game_key}: {e}")
                    error_count += 1
                    continue

                except Exception as e:
                    session.rollback()
                    logger.error(f"Error processing game {game_key}: {e}")
                    error_count += 1
                    continue

            # Final commit
            session.commit()

            logger.info(f"Database population completed:")
            logger.info(f"  Successfully processed: {processed_count} games")
            logger.info(f"  Errors encountered: {error_count} games")

            # Create performance indexes
            self.create_performance_indexes()

            # Validate data integrity
            self.validate_data_integrity(session)

        except Exception as e:
            session.rollback()
            logger.error(f"Database population failed: {e}")
            raise

        finally:
            session.close()

def main():
    """Main execution function"""
    try:
        logger.info("Starting database population...")

        # Initialize populator
        populator = DatabasePopulator()

        # Populate database
        populator.populate_database()

        logger.info("Database population completed successfully!")

    except Exception as e:
        logger.error(f"Database population failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()