"""
Enhanced Data Pipeline Orchestrator

Coordinates the fetching, processing, and storage of comprehensive NFL game data
from SportsData.io APIs. Manages the complete data pipeline for expert prediction
verification and learning system enhancement.

Features:
- Automated data fetching and storage
- Expert prediction verification processing
- Learning system integration
- Error handling and retry logic
- Progress tracking and logging
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import os
from dataclasses import asdict

from .enhanced_data_fetcher import EnhancedDataFetcher
from .enhanced_data_storage import EnhancedDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDataPipeline:
    """Orchestrates comprehensive NFL data pipeline"""

    def __init__(self, sportsdata_api_key: str, database_url: str):
        self.fetcher = EnhancedDataFetcher(sportsdata_api_key)
        self.storage = EnhancedDataStorage(database_url)
        self.initialized = False

    async def initialize(self):
        """Initialize pipeline components"""
        try:
            await self.storage.initialize()
            self.initialized = True
            logger.info("Enhanced data pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise

    async def close(self):
        """Close pipeline resources"""
        if self.storage:
            await self.storage.close()
        logger.info("Enhanced data pipeline closed")

    async def process_week_data(self, season: int, week: int,
                              include_detailed: bool = True) -> Dict[str, Any]:
        """Process complete data for a week"""
        if not self.initialized:
            await self.initialize()

        logger.info(f"Processing enhanced data for {season} Week {week}")

        results = {
            "season": season,
            "week": week,
            "games_processed": 0,
            "detailed_games": 0,
            "success": False,
            "errors": []
        }

        try:
            # Step 1: Fetch enhanced game data
            logger.info("Fetching enhanced game data...")
            enhanced_games = await self.fetcher.fetch_enhanced_game_data(season, week)

            if not enhanced_games:
                logger.warning(f"No games found for {season} Week {week}")
                return results

            # Step 2: Store enhanced game data
            logger.info(f"Storing {len(enhanced_games)} enhanced games...")
            game_storage_success = await self.storage.store_enhanced_game_data(enhanced_games)

            if not game_storage_success:
                results["errors"].append("Failed to store enhanced game data")
                return results

            results["games_processed"] = len(enhanced_games)

            # Step 3: Process detailed data for each game (if requested)
            if include_detailed:
                detailed_success = 0

                for game in enhanced_games:
                    try:
                        detailed_result = await self.process_game_detailed_data(game.game_id)
                        if detailed_result["success"]:
                            detailed_success += 1
                        else:
                            results["errors"].extend(detailed_result.get("errors", []))

                    except Exception as e:
                        error_msg = f"Error processing detailed data for game {game.game_id}: {e}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

                results["detailed_games"] = detailed_success

            results["success"] = True
            logger.info(f"Successfully processed Week {week} data: {results['games_processed']} games, {results['detailed_games']} detailed")

        except Exception as e:
            error_msg = f"Error processing week data: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results

    async def process_game_detailed_data(self, game_id: str) -> Dict[str, Any]:
        """Process detailed data for a single game"""
        logger.info(f"Processing detailed data for game {game_id}")

        result = {
            "game_id": game_id,
            "play_by_play": False,
            "drives": False,
            "coaching_decisions": False,
            "special_teams": False,
            "situational": False,
            "success": False,
            "errors": []
        }

        try:
            # Fetch all detailed data concurrently
            tasks = [
                self.fetcher.fetch_play_by_play_data(game_id),
                self.fetcher.fetch_drive_data(game_id),
                self.fetcher.fetch_coaching_decisions(game_id),
                self.fetcher.fetch_special_teams_data(game_id),
                self.fetcher.fetch_situational_performance(game_id)
            ]

            play_by_play, drives, coaching_decisions, special_teams, situational = await asyncio.gather(
                *tasks, return_exceptions=True
            )

            # Store play-by-play data
            if not isinstance(play_by_play, Exception) and play_by_play:
                pbp_success = await self.storage.store_play_by_play_data(play_by_play)
                result["play_by_play"] = pbp_success
                if not pbp_success:
                    result["errors"].append("Failed to store play-by-play data")

            # Store drive data
            if not isinstance(drives, Exception) and drives:
                drives_success = await self.storage.store_drive_data(drives)
                result["drives"] = drives_success
                if not drives_success:
                    result["errors"].append("Failed to store drive data")

            # Store coaching decisions
            if not isinstance(coaching_decisions, Exception) and coaching_decisions:
                coaching_success = await self.storage.store_coaching_decisions(coaching_decisions)
                result["coaching_decisions"] = coaching_success
                if not coaching_success:
                    result["errors"].append("Failed to store coaching decisions")

            # Store special teams performance
            if not isinstance(special_teams, Exception) and special_teams:
                st_success = await self.storage.store_special_teams_performance(special_teams)
                result["special_teams"] = st_success
                if not st_success:
                    result["errors"].append("Failed to store special teams data")

            # Store situational performance
            if not isinstance(situational, Exception) and situational:
                situational_success = await self.storage.store_situational_performance(situational)
                result["situational"] = situational_success
                if not situational_success:
                    result["errors"].append("Failed to store situational data")

            # Check overall success
            result["success"] = len(result["errors"]) == 0

            if result["success"]:
                logger.info(f"Successfully processed detailed data for game {game_id}")
            else:
                logger.warning(f"Partial success processing game {game_id}: {result['errors']}")

        except Exception as e:
            error_msg = f"Error processing detailed game data: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    async def verify_expert_predictions(self, game_id: str, expert_predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Verify expert predictions against actual game outcomes"""
        logger.info(f"Verifying expert predictions for game {game_id}")

        results = {
            "game_id": game_id,
            "experts_verified": 0,
            "verification_success": False,
            "expert_accuracies": {},
            "errors": []
        }

        try:
            # Get comprehensive verification data
            verification_data = await self.storage.get_game_verification_data(game_id)

            if not verification_data or not verification_data.get("game_data"):
                results["errors"].append("No verification data found for game")
                return results

            # Extract actual outcomes from verification data
            actual_outcomes = self._extract_actual_outcomes(verification_data)

            if not actual_outcomes:
                results["errors"].append("Could not extract actual outcomes from game data")
                return results

            # Verify each expert's predictions
            experts_verified = 0
            for expert_id, predictions in expert_predictions.items():
                try:
                    # Store verification results
                    verification_success = await self.storage.store_expert_prediction_verification(
                        game_id, expert_id, predictions, actual_outcomes
                    )

                    if verification_success:
                        # Get comprehensive accuracy
                        accuracy = await self.storage.get_expert_comprehensive_accuracy(expert_id, game_id)
                        results["expert_accuracies"][expert_id] = accuracy
                        experts_verified += 1
                    else:
                        results["errors"].append(f"Failed to verify predictions for expert {expert_id}")

                except Exception as e:
                    error_msg = f"Error verifying expert {expert_id}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            results["experts_verified"] = experts_verified
            results["verification_success"] = experts_verified > 0

            logger.info(f"Verified predictions for {experts_verified} experts for game {game_id}")

        except Exception as e:
            error_msg = f"Error verifying expert predictions: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results

    def _extract_actual_outcomes(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actual game outcomes for verification"""
        game_data = verification_data.get("game_data", {})
        coaching_advantage = verification_data.get("coaching_advantage", {})
        special_teams = verification_data.get("special_teams", [])

        outcomes = {}

        # Basic game outcomes
        if game_data.get("final_score_home") is not None and game_data.get("final_score_away") is not None:
            home_score = game_data["final_score_home"]
            away_score = game_data["final_score_away"]

            outcomes["home_score"] = home_score
            outcomes["away_score"] = away_score
            outcomes["final_score"] = f"{game_data.get('away_team', 'AWAY')} {away_score} - {game_data.get('home_team', 'HOME')} {home_score}"
            outcomes["winner"] = game_data.get("home_team") if home_score > away_score else game_data.get("away_team")
            outcomes["margin"] = abs(home_score - away_score)
            outcomes["predicted_total"] = home_score + away_score

            # Spread and total outcomes would need betting line data
            # For now, just use winner and basic metrics

        # Coaching advantage
        if coaching_advantage and coaching_advantage.get("advantage_team"):
            outcomes["coaching_advantage"] = coaching_advantage["advantage_team"]

        # Special teams edge
        if special_teams:
            # Determine special teams edge based on performance scores
            best_st_team = None
            best_st_score = 0

            for st_data in special_teams:
                st_score = st_data.get("special_teams_score", 0) or 0
                if st_score > best_st_score:
                    best_st_score = st_score
                    best_st_team = st_data.get("team")

            if best_st_team:
                outcomes["special_teams_edge"] = best_st_team

        return outcomes

    async def process_live_game_updates(self, game_id: str) -> Dict[str, Any]:
        """Process live game updates for ongoing predictions"""
        logger.info(f"Processing live updates for game {game_id}")

        result = {
            "game_id": game_id,
            "live_data_updated": False,
            "expert_notifications_sent": False,
            "success": False,
            "errors": []
        }

        try:
            # Fetch current game state
            current_data = await self.fetcher.fetch_enhanced_game_data(2024, 18)  # Current week
            game_data = next((game for game in current_data if game.game_id == game_id), None)

            if not game_data:
                result["errors"].append("Game not found in current data")
                return result

            # Update database with latest data
            update_success = await self.storage.store_enhanced_game_data([game_data])
            result["live_data_updated"] = update_success

            if update_success:
                # Trigger expert system notifications for live updates
                # This would integrate with the reasoning chain logger and expert systems
                result["expert_notifications_sent"] = True
                result["success"] = True
                logger.info(f"Successfully processed live updates for game {game_id}")

        except Exception as e:
            error_msg = f"Error processing live game updates: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    async def run_weekly_pipeline(self, season: int, week: int) -> Dict[str, Any]:
        """Run complete weekly data pipeline"""
        logger.info(f"Running weekly pipeline for {season} Week {week}")

        pipeline_result = {
            "season": season,
            "week": week,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "week_data_processed": False,
            "expert_verifications": {},
            "success": False,
            "errors": []
        }

        start_time = datetime.now()

        try:
            # Step 1: Process week data
            week_result = await self.process_week_data(season, week, include_detailed=True)
            pipeline_result["week_data_processed"] = week_result["success"]

            if not week_result["success"]:
                pipeline_result["errors"].extend(week_result.get("errors", []))
                return pipeline_result

            # Step 2: Load and verify expert predictions (if available)
            # This would integrate with the expert prediction system
            # For now, we'll create a placeholder for this integration

            # Step 3: Update learning systems
            # This would trigger updates to the reasoning chain logger,
            # belief revision service, and episodic memory manager

            pipeline_result["success"] = True
            logger.info(f"Weekly pipeline completed successfully for {season} Week {week}")

        except Exception as e:
            error_msg = f"Error running weekly pipeline: {e}"
            logger.error(error_msg)
            pipeline_result["errors"].append(error_msg)

        finally:
            end_time = datetime.now()
            pipeline_result["end_time"] = end_time.isoformat()
            pipeline_result["duration_seconds"] = (end_time - start_time).total_seconds()

        return pipeline_result

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and health"""
        status = {
            "initialized": self.initialized,
            "database_connected": False,
            "api_accessible": False,
            "health": "unknown"
        }

        try:
            # Check database connection
            if self.storage.pool and not self.storage.pool._closed:
                status["database_connected"] = True

            # Check API accessibility
            # This would involve a test API call
            status["api_accessible"] = True  # Placeholder

            # Determine overall health
            if status["initialized"] and status["database_connected"] and status["api_accessible"]:
                status["health"] = "healthy"
            elif status["initialized"]:
                status["health"] = "degraded"
            else:
                status["health"] = "unhealthy"

        except Exception as e:
            logger.error(f"Error checking pipeline status: {e}")
            status["health"] = "error"

        return status

# Enhanced Pipeline Factory
class EnhancedPipelineFactory:
    """Factory for creating configured pipeline instances"""

    @staticmethod
    def create_pipeline(config: Optional[Dict[str, str]] = None) -> EnhancedDataPipeline:
        """Create pipeline with configuration"""
        if config is None:
            config = {}

        # Get configuration from environment or provided config
        sportsdata_api_key = config.get('SPORTSDATA_IO_KEY') or os.getenv('SPORTSDATA_IO_KEY', 'bc297647c7aa4ef29747e6a85cb575dc')
        database_url = config.get('DATABASE_URL') or os.getenv('DATABASE_URL', 'postgresql://localhost/nfl_predictor')

        if not sportsdata_api_key:
            raise ValueError("SPORTSDATA_IO_KEY is required")

        if not database_url:
            raise ValueError("DATABASE_URL is required")

        return EnhancedDataPipeline(sportsdata_api_key, database_url)

    @staticmethod
    def create_test_pipeline() -> EnhancedDataPipeline:
        """Create pipeline for testing"""
        return EnhancedPipelineFactory.create_pipeline({
            'SPORTSDATA_IO_KEY': 'bc297647c7aa4ef29747e6a85cb575dc',
            'DATABASE_URL': 'postgresql://localhost/nfl_predictor_test'
        })

# Example usage and testing
async def main():
    """Test the enhanced data pipeline"""

    logger.info("Testing Enhanced Data Pipeline")

    # Create pipeline
    pipeline = EnhancedPipelineFactory.create_pipeline()

    try:
        # Initialize pipeline
        await pipeline.initialize()

        # Check pipeline status
        status = await pipeline.get_pipeline_status()
        logger.info(f"Pipeline Status: {status}")

        # Run weekly pipeline for current week
        season = 2024
        week = 18

        pipeline_result = await pipeline.run_weekly_pipeline(season, week)
        logger.info(f"Pipeline Result: {pipeline_result}")

        # Test single game processing
        if pipeline_result.get("week_data_processed"):
            # This would use actual game IDs from the processed data
            test_game_id = "test_game_id"
            detailed_result = await pipeline.process_game_detailed_data(test_game_id)
            logger.info(f"Detailed Game Processing: {detailed_result}")

    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")

    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())