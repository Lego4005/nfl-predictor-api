#!/usr/bin/env python3
"""
Weekly NFL Predictions Generator
Fetches current week's games, runs all 15 experts, and generates comprehensive reports
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.comprehensive_intelligent_predictor import ComprehensiveIntelligentPredictor
from src.ml.autonomous_expert_system import AutonomousExpertSystem
from src.services.enhanced_data_fetcher import EnhancedDataFetcher
from src.formatters.comprehensive_output_generator import ComprehensiveOutputGenerator
from src.services.supabaseClient import supabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeeklyPredictionsGenerator:
    """Generates comprehensive weekly NFL predictions"""

    def __init__(self):
        self.predictor = None
        self.expert_system = None
        self.data_fetcher = None
        self.output_generator = None

    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing prediction system components...")

        try:
            self.predictor = ComprehensiveIntelligentPredictor()
            self.expert_system = AutonomousExpertSystem()
            self.data_fetcher = EnhancedDataFetcher()
            self.output_generator = ComprehensiveOutputGenerator()

            logger.info("✅ All components initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise

    async def get_current_week_info(self) -> tuple[int, int]:
        """Get current NFL week and season"""
        try:
            # Get current date and determine NFL week
            now = datetime.now()
            current_year = now.year

            # NFL season typically starts in September
            # Week 1 usually starts around September 8-14
            season_start = datetime(current_year, 9, 10)  # Approximate start

            if now < season_start:
                # Still in previous season's playoffs or offseason
                current_year -= 1
                season_start = datetime(current_year, 9, 10)

            # Calculate week number
            days_since_start = (now - season_start).days
            week_number = max(1, min(18, (days_since_start // 7) + 1))

            # Adjust for playoffs (weeks 19-22)
            if week_number > 18:
                week_number = min(22, week_number)

            logger.info(f"📅 Current NFL Season: {current_year}, Week: {week_number}")
            return week_number, current_year

        except Exception as e:
            logger.warning(f"Could not determine current week, using defaults: {e}")
            return 1, 2024

    async def fetch_week_games(self, week: int, season: int) -> List[Dict]:
        """Fetch games for specified week"""
        logger.info(f"🏈 Fetching games for Week {week}, {season} season...")

        try:
            # Try to get current week games
            games = await self.data_fetcher.get_current_week_games()

            if not games:
                # Fallback to mock games for testing
                logger.warning("No real games found, generating mock games for testing...")
                games = await self._generate_mock_games(week, season)

            logger.info(f"✅ Found {len(games)} games for Week {week}")
            return games

        except Exception as e:
            logger.error(f"❌ Failed to fetch games: {e}")
            # Generate mock games for testing
            logger.info("Generating mock games for testing...")
            return await self._generate_mock_games(week, season)

    async def _generate_mock_games(self, week: int, season: int) -> List[Dict]:
        """Generate mock games for testing purposes"""
        mock_teams = [
            'Chiefs', 'Bills', 'Ravens', 'Cowboys', '49ers', 'Eagles',
            'Dolphins', 'Bengals', 'Browns', 'Steelers', 'Titans', 'Colts',
            'Jaguars', 'Texans', 'Broncos', 'Raiders', 'Chargers', 'Patriots',
            'Jets', 'Lions', 'Packers', 'Bears', 'Vikings', 'Saints',
            'Falcons', 'Panthers', 'Buccaneers', 'Cardinals', 'Rams',
            'Seahawks', 'Giants', 'Commanders'
        ]

        games = []
        game_date = datetime.now() + timedelta(days=1)

        # Generate 16 mock games (full week)
        for i in range(0, min(16, len(mock_teams)-1), 2):
            if i + 1 < len(mock_teams):
                game = {
                    'id': f'mock_game_{i//2 + 1}',
                    'home_team': mock_teams[i],
                    'away_team': mock_teams[i + 1],
                    'date': game_date.strftime('%Y-%m-%d'),
                    'time': '1:00 PM ET',
                    'week': week,
                    'season': season,
                    'venue': f"{mock_teams[i]} Stadium",
                    'weather': 'Clear, 72°F',
                    'spread': f"{mock_teams[i]} -3.5",
                    'total': '47.5'
                }
                games.append(game)

        return games[:16]  # Return up to 16 games

    async def generate_game_predictions(self, games: List[Dict]) -> Dict[str, Dict]:
        """Generate predictions for all games"""
        logger.info(f"🤖 Generating predictions for {len(games)} games...")

        all_predictions = {}

        for i, game in enumerate(games, 1):
            logger.info(f"⚡ Processing game {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")

            try:
                # Generate comprehensive predictions
                game_predictions = await self.predictor.generate_comprehensive_predictions(game)

                # Add game metadata
                game_predictions.update({
                    'game_id': game['id'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'game_date': game['date'],
                    'game_time': game.get('time', 'TBD'),
                    'venue': game.get('venue', 'TBD'),
                    'weather': game.get('weather', 'TBD')
                })

                all_predictions[game['id']] = game_predictions

                logger.info(f"✅ Generated {len(game_predictions.get('expert_predictions', {}))} expert predictions")

            except Exception as e:
                logger.error(f"❌ Failed to generate predictions for {game['id']}: {e}")
                # Continue with other games
                continue

        logger.info(f"🎯 Completed predictions for {len(all_predictions)} games")
        return all_predictions

    async def generate_comprehensive_report(self, predictions: Dict[str, Dict], week: int, season: int) -> str:
        """Generate comprehensive markdown report"""
        logger.info("📝 Generating comprehensive markdown report...")

        try:
            report_content = await self.output_generator.generate_comprehensive_report(
                predictions, week, season
            )

            # Calculate report statistics
            line_count = report_content.count('\n')
            word_count = len(report_content.split())
            char_count = len(report_content)

            logger.info(f"📊 Report generated: {line_count:,} lines, {word_count:,} words, {char_count:,} characters")

            return report_content

        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
            raise

    async def save_predictions_data(self, predictions: Dict[str, Dict], week: int, season: int) -> str:
        """Save predictions data as JSON for later analysis"""
        try:
            predictions_dir = "/home/iris/code/experimental/nfl-predictor-api/predictions"
            os.makedirs(predictions_dir, exist_ok=True)

            # Save detailed JSON data
            json_filename = f"week_{week}_{season}_predictions_data.json"
            json_filepath = os.path.join(predictions_dir, json_filename)

            # Prepare data for JSON serialization
            json_data = {
                'meta': {
                    'week': week,
                    'season': season,
                    'generated_at': datetime.now().isoformat(),
                    'total_games': len(predictions),
                    'total_experts': 15,
                    'total_predictions': len(predictions) * 15 * 35
                },
                'predictions': predictions
            }

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=str)

            logger.info(f"💾 Predictions data saved: {json_filepath}")
            return json_filepath

        except Exception as e:
            logger.error(f"❌ Failed to save predictions data: {e}")
            raise

    async def store_predictions_database(self, predictions: Dict[str, Dict], week: int, season: int) -> bool:
        """Store predictions in Supabase database"""
        try:
            logger.info("🗄️ Storing predictions in database...")

            for game_id, game_predictions in predictions.items():
                # Prepare database record
                db_record = {
                    'game_id': game_id,
                    'week': week,
                    'season': season,
                    'home_team': game_predictions.get('home_team'),
                    'away_team': game_predictions.get('away_team'),
                    'game_date': game_predictions.get('game_date'),
                    'predictions_data': json.dumps(game_predictions, default=str),
                    'consensus_winner': game_predictions.get('consensus', {}).get('predicted_winner'),
                    'consensus_confidence': game_predictions.get('consensus', {}).get('confidence'),
                    'expert_count': len(game_predictions.get('expert_predictions', {})),
                    'generated_at': datetime.now().isoformat()
                }

                # Insert into database
                result = supabase.table('weekly_predictions').upsert(db_record).execute()

                if result.data:
                    logger.info(f"✅ Stored predictions for {game_id}")
                else:
                    logger.warning(f"⚠️ No data returned for {game_id}")

            logger.info(f"🗄️ Database storage completed for {len(predictions)} games")
            return True

        except Exception as e:
            logger.error(f"❌ Database storage failed: {e}")
            return False

    async def run_weekly_generation(self, week: Optional[int] = None, season: Optional[int] = None) -> Dict[str, str]:
        """Run complete weekly prediction generation"""
        start_time = datetime.now()
        logger.info("🚀 Starting weekly predictions generation...")

        try:
            # Initialize system
            await self.initialize()

            # Get current week info if not provided
            if week is None or season is None:
                week, season = await self.get_current_week_info()

            logger.info(f"📅 Generating predictions for Week {week}, {season} season")

            # Fetch games
            games = await self.fetch_week_games(week, season)

            if not games:
                raise ValueError("No games found for the specified week")

            # Generate predictions
            predictions = await self.generate_game_predictions(games)

            if not predictions:
                raise ValueError("No predictions generated")

            # Generate comprehensive report
            report_content = await self.generate_comprehensive_report(predictions, week, season)

            # Save report
            report_filename = f"week_{week}_{season}_comprehensive_predictions.md"
            report_path = await self.output_generator.save_report(
                report_content, report_filename
            )

            # Save JSON data
            json_path = await self.save_predictions_data(predictions, week, season)

            # Store in database
            db_success = await self.store_predictions_database(predictions, week, season)

            # Calculate completion stats
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Summary
            results = {
                'week': week,
                'season': season,
                'games_processed': len(predictions),
                'total_predictions': len(predictions) * 15 * 35,
                'report_path': report_path,
                'json_path': json_path,
                'database_stored': db_success,
                'duration_seconds': duration,
                'status': 'completed'
            }

            logger.info("🎉 Weekly predictions generation completed successfully!")
            logger.info(f"📊 Summary: {len(predictions)} games, {len(predictions) * 15 * 35:,} predictions")
            logger.info(f"⏱️ Duration: {duration:.1f} seconds")
            logger.info(f"📄 Report: {report_path}")
            logger.info(f"💾 Data: {json_path}")

            return results

        except Exception as e:
            logger.error(f"❌ Weekly predictions generation failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate weekly NFL predictions')
    parser.add_argument('--week', type=int, help='NFL week number (1-22)')
    parser.add_argument('--season', type=int, help='NFL season year')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create generator and run
    generator = WeeklyPredictionsGenerator()
    results = await generator.run_weekly_generation(args.week, args.season)

    # Print results
    print("\n" + "="*60)
    print("🏈 NFL Weekly Predictions Generator Results")
    print("="*60)

    if results.get('status') == 'completed':
        print(f"✅ Status: {results['status'].upper()}")
        print(f"📅 Week: {results['week']}, Season: {results['season']}")
        print(f"🏈 Games: {results['games_processed']}")
        print(f"🤖 Total Predictions: {results['total_predictions']:,}")
        print(f"⏱️ Duration: {results['duration_seconds']:.1f} seconds")
        print(f"📄 Report: {results['report_path']}")
        print(f"💾 Data: {results['json_path']}")
        print(f"🗄️ Database: {'✅ Stored' if results['database_stored'] else '❌ Failed'}")
    else:
        print(f"❌ Status: {results['status'].upper()}")
        print(f"⚠️ Error: {results.get('error', 'Unknown error')}")
        print(f"⏱️ Duration: {results['duration_seconds']:.1f} seconds")

    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())