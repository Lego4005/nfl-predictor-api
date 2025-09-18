"""
Enhanced Data Storage Service

Stores comprehensive NFL game data from SportsData.io APIs into the enhanced
database schema for detailed expert prediction verification.

Handles:
- Enhanced game data storage
- Play-by-play data persistence
- Drive analysis storage
- Coaching decisions tracking
- Special teams performance
- Situational performance metrics
- Expert prediction verification links
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import os

from .enhanced_data_fetcher import (
    EnhancedGameData, GamePlayByPlay, GameDrive, CoachingDecision,
    SpecialTeamsPerformance, SituationalPerformance
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDataStorage:
    """Stores enhanced NFL data into PostgreSQL database"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Enhanced data storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    async def store_enhanced_game_data(self, games: List[EnhancedGameData]) -> bool:
        """Store enhanced game data in database"""
        if not games:
            return True

        try:
            async with self.pool.acquire() as conn:
                # Prepare insert query
                insert_query = """
                INSERT INTO enhanced_game_data (
                    game_id, season, week, home_team, away_team, game_date,
                    final_score_home, final_score_away, status,
                    weather_temperature, weather_humidity, weather_wind_speed,
                    weather_wind_direction, weather_condition, stadium_name, attendance,
                    total_plays, game_duration_minutes, overtime_periods,
                    home_time_of_possession, away_time_of_possession,
                    home_first_downs, away_first_downs, home_total_yards, away_total_yards,
                    home_passing_yards, away_passing_yards, home_rushing_yards, away_rushing_yards,
                    home_third_down_attempts, home_third_down_conversions,
                    away_third_down_attempts, away_third_down_conversions,
                    home_red_zone_attempts, home_red_zone_scores,
                    away_red_zone_attempts, away_red_zone_scores,
                    home_turnovers, away_turnovers, home_penalties, home_penalty_yards,
                    away_penalties, away_penalty_yards, home_punt_return_yards,
                    away_punt_return_yards, home_kick_return_yards, away_kick_return_yards,
                    raw_score_data, raw_stats_data, raw_advanced_metrics
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                         $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
                         $31, $32, $33, $34, $35, $36, $37, $38, $39, $40, $41, $42, $43, $44,
                         $45, $46, $47, $48, $49, $50, $51, $52)
                ON CONFLICT (game_id) DO UPDATE SET
                    final_score_home = EXCLUDED.final_score_home,
                    final_score_away = EXCLUDED.final_score_away,
                    status = EXCLUDED.status,
                    raw_score_data = EXCLUDED.raw_score_data,
                    raw_stats_data = EXCLUDED.raw_stats_data,
                    raw_advanced_metrics = EXCLUDED.raw_advanced_metrics,
                    updated_at = NOW()
                """

                # Prepare data for batch insert
                game_records = []
                for game in games:
                    record = (
                        game.game_id, game.season, game.week, game.home_team, game.away_team,
                        game.game_date, game.final_score_home, game.final_score_away, game.status,
                        game.weather_temperature, game.weather_humidity, game.weather_wind_speed,
                        game.weather_wind_direction, game.weather_condition, game.stadium_name,
                        game.attendance, game.total_plays, game.game_duration_minutes,
                        game.overtime_periods, game.home_time_of_possession, game.away_time_of_possession,
                        game.home_first_downs, game.away_first_downs, game.home_total_yards,
                        game.away_total_yards, game.home_passing_yards, game.away_passing_yards,
                        game.home_rushing_yards, game.away_rushing_yards, game.home_third_down_attempts,
                        game.home_third_down_conversions, game.away_third_down_attempts,
                        game.away_third_down_conversions, game.home_red_zone_attempts,
                        game.home_red_zone_scores, game.away_red_zone_attempts, game.away_red_zone_scores,
                        game.home_turnovers, game.away_turnovers, game.home_penalties,
                        game.home_penalty_yards, game.away_penalties, game.away_penalty_yards,
                        game.home_punt_return_yards, game.away_punt_return_yards,
                        game.home_kick_return_yards, game.away_kick_return_yards,
                        json.dumps(game.raw_score_data) if game.raw_score_data else None,
                        json.dumps(game.raw_stats_data) if game.raw_stats_data else None,
                        json.dumps(game.raw_advanced_metrics) if game.raw_advanced_metrics else None
                    )
                    game_records.append(record)

                # Execute batch insert
                await conn.executemany(insert_query, game_records)
                logger.info(f"Stored {len(games)} enhanced game records")
                return True

        except Exception as e:
            logger.error(f"Error storing enhanced game data: {e}")
            return False

    async def store_play_by_play_data(self, plays: List[GamePlayByPlay]) -> bool:
        """Store play-by-play data in database"""
        if not plays:
            return True

        try:
            async with self.pool.acquire() as conn:
                # Clear existing plays for this game to avoid duplicates
                if plays:
                    await conn.execute(
                        "DELETE FROM game_play_by_play WHERE game_id = $1",
                        plays[0].game_id
                    )

                insert_query = """
                INSERT INTO game_play_by_play (
                    game_id, play_id, quarter, time_remaining, down, yards_to_go,
                    yard_line, possession_team, play_type, play_description, yards_gained,
                    is_touchdown, is_field_goal, is_safety, is_turnover, is_penalty,
                    primary_player, secondary_players, is_red_zone, is_goal_to_go,
                    is_fourth_down, is_two_minute_warning, raw_play_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                         $15, $16, $17, $18, $19, $20, $21, $22, $23)
                """

                play_records = []
                for play in plays:
                    record = (
                        play.game_id, play.play_id, play.quarter, play.time_remaining,
                        play.down, play.yards_to_go, play.yard_line, play.possession_team,
                        play.play_type, play.play_description, play.yards_gained,
                        play.is_touchdown, play.is_field_goal, play.is_safety,
                        play.is_turnover, play.is_penalty, play.primary_player,
                        json.dumps(play.secondary_players) if play.secondary_players else None,
                        play.is_red_zone, play.is_goal_to_go, play.is_fourth_down,
                        play.is_two_minute_warning,
                        json.dumps(play.raw_play_data) if play.raw_play_data else None
                    )
                    play_records.append(record)

                await conn.executemany(insert_query, play_records)
                logger.info(f"Stored {len(plays)} play-by-play records")
                return True

        except Exception as e:
            logger.error(f"Error storing play-by-play data: {e}")
            return False

    async def store_drive_data(self, drives: List[GameDrive]) -> bool:
        """Store drive data in database"""
        if not drives:
            return True

        try:
            async with self.pool.acquire() as conn:
                # Clear existing drives for this game
                if drives:
                    await conn.execute(
                        "DELETE FROM game_drives WHERE game_id = $1",
                        drives[0].game_id
                    )

                insert_query = """
                INSERT INTO game_drives (
                    game_id, drive_id, quarter, possession_team, starting_field_position,
                    drive_result, ending_field_position, total_plays, total_yards,
                    time_consumed, plays_per_yard, yards_per_play, is_scoring_drive,
                    is_three_and_out, is_two_minute_drill, is_goal_line_stand
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """

                drive_records = []
                for drive in drives:
                    record = (
                        drive.game_id, drive.drive_id, drive.quarter, drive.possession_team,
                        drive.starting_field_position, drive.drive_result, drive.ending_field_position,
                        drive.total_plays, drive.total_yards, drive.time_consumed,
                        drive.plays_per_yard, drive.yards_per_play, drive.is_scoring_drive,
                        drive.is_three_and_out, drive.is_two_minute_drill, drive.is_goal_line_stand
                    )
                    drive_records.append(record)

                await conn.executemany(insert_query, drive_records)
                logger.info(f"Stored {len(drives)} drive records")
                return True

        except Exception as e:
            logger.error(f"Error storing drive data: {e}")
            return False

    async def store_coaching_decisions(self, decisions: List[CoachingDecision]) -> bool:
        """Store coaching decisions in database"""
        if not decisions:
            return True

        try:
            async with self.pool.acquire() as conn:
                insert_query = """
                INSERT INTO coaching_decisions (
                    game_id, team, quarter, situation, decision_type, decision_description,
                    outcome, expected_value, actual_value, decision_quality_score,
                    game_state, alternative_decisions
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT DO NOTHING
                """

                decision_records = []
                for decision in decisions:
                    record = (
                        decision.game_id, decision.team, decision.quarter, decision.situation,
                        decision.decision_type, decision.decision_description, decision.outcome,
                        decision.expected_value, decision.actual_value, decision.decision_quality_score,
                        json.dumps(decision.game_state) if decision.game_state else None,
                        json.dumps(decision.alternative_decisions) if decision.alternative_decisions else None
                    )
                    decision_records.append(record)

                await conn.executemany(insert_query, decision_records)
                logger.info(f"Stored {len(decisions)} coaching decision records")
                return True

        except Exception as e:
            logger.error(f"Error storing coaching decisions: {e}")
            return False

    async def store_special_teams_performance(self, performances: List[SpecialTeamsPerformance]) -> bool:
        """Store special teams performance in database"""
        if not performances:
            return True

        try:
            async with self.pool.acquire() as conn:
                # Clear existing ST data for this game
                if performances:
                    await conn.execute(
                        "DELETE FROM special_teams_performance WHERE game_id = $1",
                        performances[0].game_id
                    )

                insert_query = """
                INSERT INTO special_teams_performance (
                    game_id, team, field_goal_attempts, field_goals_made, longest_field_goal,
                    extra_point_attempts, extra_points_made, punts, punt_yards, punts_inside_20,
                    punt_return_yards_allowed, kickoff_returns, kickoff_return_yards,
                    punt_returns, punt_return_yards, return_touchdowns, tackles_on_coverage,
                    coverage_efficiency_score, field_position_advantage, special_teams_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                         $16, $17, $18, $19, $20)
                """

                st_records = []
                for performance in performances:
                    record = (
                        performance.game_id, performance.team, performance.field_goal_attempts,
                        performance.field_goals_made, performance.longest_field_goal,
                        performance.extra_point_attempts, performance.extra_points_made,
                        performance.punts, performance.punt_yards, performance.punts_inside_20,
                        performance.punt_return_yards_allowed, performance.kickoff_returns,
                        performance.kickoff_return_yards, performance.punt_returns,
                        performance.punt_return_yards, performance.return_touchdowns,
                        performance.tackles_on_coverage, performance.coverage_efficiency_score,
                        performance.field_position_advantage, performance.special_teams_score
                    )
                    st_records.append(record)

                await conn.executemany(insert_query, st_records)
                logger.info(f"Stored {len(performances)} special teams performance records")
                return True

        except Exception as e:
            logger.error(f"Error storing special teams performance: {e}")
            return False

    async def store_situational_performance(self, performances: List[SituationalPerformance]) -> bool:
        """Store situational performance in database"""
        if not performances:
            return True

        try:
            async with self.pool.acquire() as conn:
                # Clear existing situational data for this game
                if performances:
                    await conn.execute(
                        "DELETE FROM situational_performance WHERE game_id = $1",
                        performances[0].game_id
                    )

                insert_query = """
                INSERT INTO situational_performance (
                    game_id, team, points_final_2_minutes, drives_final_2_minutes,
                    scoring_drives_final_2_minutes, fourth_down_attempts, fourth_down_conversions,
                    red_zone_trips, red_zone_touchdowns, crowd_noise_impact_score,
                    home_field_advantage_score, referee_calls_differential, momentum_shifts,
                    largest_lead, time_with_lead, comeback_ability_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """

                situational_records = []
                for performance in performances:
                    record = (
                        performance.game_id, performance.team, performance.points_final_2_minutes,
                        performance.drives_final_2_minutes, performance.scoring_drives_final_2_minutes,
                        performance.fourth_down_attempts, performance.fourth_down_conversions,
                        performance.red_zone_trips, performance.red_zone_touchdowns,
                        performance.crowd_noise_impact_score, performance.home_field_advantage_score,
                        performance.referee_calls_differential, performance.momentum_shifts,
                        performance.largest_lead, performance.time_with_lead,
                        performance.comeback_ability_score
                    )
                    situational_records.append(record)

                await conn.executemany(insert_query, situational_records)
                logger.info(f"Stored {len(performances)} situational performance records")
                return True

        except Exception as e:
            logger.error(f"Error storing situational performance: {e}")
            return False

    async def store_expert_prediction_verification(self, game_id: str, expert_id: str,
                                                 predictions: Dict[str, Any], actual_outcomes: Dict[str, Any]) -> bool:
        """Store expert prediction verification results"""
        try:
            async with self.pool.acquire() as conn:
                # Get expert reasoning chain ID (if exists)
                reasoning_chain_id = await conn.fetchval(
                    "SELECT id FROM expert_reasoning_chains WHERE expert_id = $1 AND game_id = $2 ORDER BY created_at DESC LIMIT 1",
                    expert_id, game_id
                )

                if not reasoning_chain_id:
                    logger.warning(f"No reasoning chain found for expert {expert_id} and game {game_id}")
                    return False

                insert_query = """
                INSERT INTO expert_prediction_verification (
                    expert_reasoning_chain_id, game_id, expert_id, prediction_category,
                    predicted_value, actual_value, is_correct, accuracy_score,
                    confidence_score, verification_method, supporting_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """

                verification_records = []

                # Verify each prediction category
                for category, predicted_value in predictions.items():
                    if category in actual_outcomes:
                        actual_value = actual_outcomes[category]
                        is_correct, accuracy_score = self._calculate_accuracy(category, predicted_value, actual_value)

                        verification_record = (
                            reasoning_chain_id, game_id, expert_id, category,
                            str(predicted_value), str(actual_value), is_correct, accuracy_score,
                            predictions.get(f"{category}_confidence", 0.5),  # Default confidence
                            "exact_match" if is_correct else "statistical_analysis",
                            json.dumps({"predicted": predicted_value, "actual": actual_value})
                        )
                        verification_records.append(verification_record)

                if verification_records:
                    await conn.executemany(insert_query, verification_records)
                    logger.info(f"Stored {len(verification_records)} verification records for expert {expert_id}")

                return True

        except Exception as e:
            logger.error(f"Error storing expert prediction verification: {e}")
            return False

    def _calculate_accuracy(self, category: str, predicted: Any, actual: Any) -> tuple[bool, float]:
        """Calculate accuracy score for a prediction category"""
        try:
            if category == "winner":
                return predicted == actual, 1.0 if predicted == actual else 0.0

            elif category in ["final_score", "home_score", "away_score"]:
                if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                    diff = abs(predicted - actual)
                    # Accuracy decreases with point difference
                    accuracy = max(0.0, 1.0 - (diff / 20.0))  # 20 point max difference
                    return diff == 0, accuracy
                else:
                    return predicted == actual, 1.0 if predicted == actual else 0.0

            elif category == "spread_pick":
                return predicted == actual, 1.0 if predicted == actual else 0.0

            elif category == "total_pick":
                return predicted == actual, 1.0 if predicted == actual else 0.0

            elif category in ["predicted_total", "margin"]:
                if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                    diff = abs(predicted - actual)
                    accuracy = max(0.0, 1.0 - (diff / 10.0))  # 10 point max difference
                    return diff == 0, accuracy

            elif category in ["coaching_advantage", "special_teams_edge"]:
                return predicted == actual, 1.0 if predicted == actual else 0.0

            else:
                # Default exact match
                return predicted == actual, 1.0 if predicted == actual else 0.0

        except Exception as e:
            logger.error(f"Error calculating accuracy for {category}: {e}")
            return False, 0.0

    async def get_game_verification_data(self, game_id: str) -> Dict[str, Any]:
        """Get comprehensive verification data for a game"""
        try:
            async with self.pool.acquire() as conn:
                # Get enhanced game data
                game_data = await conn.fetchrow(
                    "SELECT * FROM enhanced_game_data WHERE game_id = $1",
                    game_id
                )

                if not game_data:
                    return {}

                # Get coaching decisions
                coaching_decisions = await conn.fetch(
                    "SELECT * FROM coaching_decisions WHERE game_id = $1",
                    game_id
                )

                # Get special teams performance
                special_teams = await conn.fetch(
                    "SELECT * FROM special_teams_performance WHERE game_id = $1",
                    game_id
                )

                # Get situational performance
                situational = await conn.fetch(
                    "SELECT * FROM situational_performance WHERE game_id = $1",
                    game_id
                )

                # Get coaching advantage
                coaching_advantage = await conn.fetchrow(
                    "SELECT get_game_coaching_advantage($1) as advantage",
                    game_id
                )

                return {
                    "game_data": dict(game_data) if game_data else {},
                    "coaching_decisions": [dict(row) for row in coaching_decisions],
                    "special_teams": [dict(row) for row in special_teams],
                    "situational": [dict(row) for row in situational],
                    "coaching_advantage": coaching_advantage["advantage"] if coaching_advantage else {}
                }

        except Exception as e:
            logger.error(f"Error getting verification data for game {game_id}: {e}")
            return {}

    async def get_expert_comprehensive_accuracy(self, expert_id: str, game_id: str) -> Dict[str, Any]:
        """Get comprehensive accuracy for an expert"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT calculate_expert_comprehensive_accuracy($1, $2) as accuracy",
                    expert_id, game_id
                )

                return result["accuracy"] if result and result["accuracy"] else {}

        except Exception as e:
            logger.error(f"Error getting expert accuracy: {e}")
            return {}

# Example usage
async def main():
    """Test the enhanced data storage"""

    # Database URL (use environment variable in production)
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/nfl_predictor')

    storage = EnhancedDataStorage(database_url)

    try:
        await storage.initialize()
        logger.info("Enhanced data storage test completed successfully")
    except Exception as e:
        logger.error(f"Enhanced data storage test failed: {e}")
    finally:
        await storage.close()

if __name__ == "__main__":
    asyncio.run(main())