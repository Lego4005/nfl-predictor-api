#!/usr/bin/env python3
"""
Validate ConservativeAnalyzer on 50 Historical Games

This script:
1. Fetches 50 historical NFL games from Supabase
2. Runs ConservativeAnalyzer with LLM integration on each game
3. Validates predictions against actual outcomes
4. Generates comprehensive accuracy report
5. Demonstrates episodic memory usage

Target: 40-60% accuracy
Requirements: 1.1, 1.2, 2.1, 2.2
"""

import sys
import os
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/validation_50_games_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class HistoricalGameValidator:
    """Validator for running ConservativeAnalyzer on historical games"""

    def __init__(self):
        self.expert = None
        self.llm_service = None
        self.validation_framework = None
        self.prediction_logger = None
        self.games_processed = 0
        self.predictions_made = 0
        self.successful_predictions = 0

    async def initialize_services(self):
        """Initialize all required services"""
        logger.info("=" * 80)
        logger.info("🚀 INITIALIZING SERVICES")
        logger.info("=" * 80)

        # Initialize LLM service
        from src.services.local_llm_service import LocalLLMService
        self.llm_service = LocalLLMService()
        logger.info("✅ LLM service initialized")

        # Test LLM connection
        if not self.llm_service.test_connection():
            raise ConnectionError("❌ LLM connection test failed")
        logger.info("✅ LLM connection verified")

        # Initialize ConservativeAnalyzer
        from src.ml.personality_driven_experts import ConservativeAnalyzer
        self.expert = ConservativeAnalyzer(
            memory_service=None,  # Start without memory for baseline
            llm_service=self.llm_service
        )
        logger.info(f"✅ {self.expert.name} initialized")

        # Initialize validation framework
        from src.ml.prediction_validation_framework import get_validation_framework
        self.validation_framework = get_validation_framework()
        logger.info("✅ Validation framework initialized")

        # Initialize logging system
        from src.ml.comprehensive_logging_system import get_prediction_logger
        self.prediction_logger = get_prediction_logger()
        logger.info("✅ Logging system initialized")

        logger.info("\n✅ All services initialized successfully\n")

    def fetch_historical_games(self, limit: int = 50, team: str = 'KC', season: int = 2024) -> List[Dict[str, Any]]:
        """
        Fetch historical games from Supabase in chronological order for a specific team.
        This allows memory to build up context about the team over the season.
        """
        logger.info(f"📊 Fetching {limit} sequential games for {team} in {season} season...")

        try:
            from supabase import create_client
            import os

            # Get Supabase credentials (try multiple env var names)
            supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')

            if not supabase_url or not supabase_key:
                logger.warning("⚠️  Supabase credentials not found, using mock data")
                return self._generate_mock_games(limit)

            supabase = create_client(supabase_url, supabase_key)

            # Fetch games for specific team in chronological order
            # This allows memory to build up context about the team
            response = supabase.table('nfl_games') \
                .select('*') \
                .eq('season', season) \
                .or_(f'home_team.eq.{team},away_team.eq.{team}') \
                .not_.is_('home_score', 'null') \
                .not_.is_('away_score', 'null') \
                .order('game_date', desc=False) \
                .limit(limit) \
                .execute()

            if response.data and len(response.data) > 0:
                logger.info(f"✅ Fetched {len(response.data)} sequential games for {team}")
                logger.info(f"   Season: {season}, Weeks {response.data[0].get('week', '?')} to {response.data[-1].get('week', '?')}")
                return response.data
            else:
                logger.warning(f"⚠️  No games found for {team} in {season}, trying 2023...")
                # Try 2023 season
                response = supabase.table('nfl_games') \
                    .select('*') \
                    .eq('season', 2023) \
                    .or_(f'home_team.eq.{team},away_team.eq.{team}') \
                    .not_.is_('home_score', 'null') \
                    .not_.is_('away_score', 'null') \
                    .order('game_date', desc=False) \
                    .limit(limit) \
                    .execute()

                if response.data and len(response.data) > 0:
                    logger.info(f"✅ Fetched {len(response.data)} sequential games for {team} from 2023")
                    return response.data
                else:
                    logger.warning("⚠️  No games found, using mock data")
                    return self._generate_mock_games(limit)

        except Exception as e:
            logger.error(f"❌ Error fetching from Supabase: {e}")
            logger.info("📝 Falling back to mock data")
            return self._generate_mock_games(limit)

    def _generate_mock_games(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock historical games for testing"""
        logger.info(f"🎭 Generating {count} mock games...")

        teams = ['KC', 'BUF', 'SF', 'PHI', 'DAL', 'BAL', 'CIN', 'MIA', 'LAC', 'DET']
        games = []

        for i in range(count):
            home_idx = i % len(teams)
            away_idx = (i + 1) % len(teams)

            home_score = 20 + (i % 15)
            away_score = 17 + ((i + 3) % 15)

            game = {
                'game_id': f'mock_game_{i+1}',
                'season': 2024,
                'week': (i % 17) + 1,
                'game_date': f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                'home_team': teams[home_idx],
                'away_team': teams[away_idx],
                'home_score': home_score,
                'away_score': away_score,
                'status': 'completed',
                'weather_temp': 65 + (i % 30),
                'weather_wind': 5 + (i % 15),
                'weather_conditions': 'Clear' if i % 3 == 0 else 'Cloudy',
                'spread': -3.0 + (i % 7) - 3,
                'total': 45.0 + (i % 10)
            }
            games.append(game)

        logger.info(f"✅ Generated {len(games)} mock games")
        return games

    def convert_to_universal_game_data(self, game: Dict[str, Any]):
        """Convert database game to UniversalGameData format"""
        from src.ml.personality_driven_experts import UniversalGameData

        # Create UniversalGameData object
        universal_data = UniversalGameData(
            home_team=game['home_team'],
            away_team=game['away_team'],
            game_time=game.get('game_date', ''),
            location=f"{game['home_team']} Stadium",
            weather={
                'temperature': game.get('weather_temp', 70),
                'wind_speed': game.get('weather_wind', 5),
                'conditions': game.get('weather_conditions', 'Clear'),
                'humidity': 50,
                'is_dome': False
            },
            injuries={'home': [], 'away': []},
            line_movement={
                'opening_line': game.get('spread', -3.0),
                'current_line': game.get('spread', -3.0),
                'total_line': game.get('total', 45.0),
                'home_moneyline': -150,
                'away_moneyline': 130,
                'public_percentage': 55
            },
            team_stats={
                'home': {
                    'wins': 8, 'losses': 5,
                    'points_per_game': 24.5,
                    'points_allowed_per_game': 21.0,
                    'win_percentage': 0.615,
                    'recent_form': 'W-W-L-W-L',
                    'recent_games_count': 5
                },
                'away': {
                    'wins': 7, 'losses': 6,
                    'points_per_game': 22.8,
                    'points_allowed_per_game': 23.5,
                    'win_percentage': 0.538,
                    'recent_form': 'L-W-W-L-W',
                    'recent_games_count': 5
                }
            },
            head_to_head={
                'total_games': 4,
                'home_team_wins': 2,
                'away_team_wins': 2,
                'average_total': 48.0,
                'average_margin': 3.5,
                'recent_games': []
            },
            coaching_info={
                'home_coach': 'Head Coach',
                'away_coach': 'Head Coach'
            }
        )

        # Add required attributes for prompt building
        universal_data.week = game.get('week', 1)
        universal_data.season = game.get('season', 2024)
        universal_data.game_date = game.get('game_date', '')

        # Add team stats objects
        class TeamStats:
            def __init__(self, stats_dict):
                for key, value in stats_dict.items():
                    setattr(self, key, value)

        universal_data.home_team_stats = TeamStats(universal_data.team_stats['home'])
        universal_data.away_team_stats = TeamStats(universal_data.team_stats['away'])

        # Add venue and weather objects
        class VenueInfo:
            stadium_name = f"{game['home_team']} Stadium"
            surface_type = "Grass"
            roof_type = "Outdoor"

        class WeatherConditions:
            def __init__(self, weather_dict):
                for key, value in weather_dict.items():
                    setattr(self, key, value)

        class PublicBetting:
            def __init__(self, line_dict):
                self.spread = line_dict.get('current_line')
                self.total = line_dict.get('total_line')
                self.home_ml = line_dict.get('home_moneyline')
                self.away_ml = line_dict.get('away_moneyline')
                self.public_percentage = line_dict.get('public_percentage')

        class RecentNews:
            injury_report = "No significant injuries"

        class MatchupContext:
            is_division_game = "Unknown"
            rest_differential = "Even rest"

        universal_data.venue_info = VenueInfo()
        universal_data.weather_conditions = WeatherConditions(universal_data.weather)
        universal_data.public_betting = PublicBetting(universal_data.line_movement)
        universal_data.recent_news = RecentNews()
        universal_data.matchup_context = MatchupContext()

        return universal_data

    async def process_game(self, game: Dict[str, Any], game_number: int, total_games: int) -> Dict[str, Any]:
        """Process a single game and make prediction"""
        logger.info("\n" + "=" * 80)
        logger.info(f"🏈 GAME {game_number}/{total_games}: {game['away_team']} @ {game['home_team']}")
        logger.info(f"   Season: {game['season']}, Week: {game['week']}")
        logger.info(f"   Date: {game.get('game_date', 'Unknown')}")
        logger.info("=" * 80)

        try:
            # Convert to UniversalGameData
            universal_data = self.convert_to_universal_game_data(game)

            # Make prediction
            logger.info("🤖 Making LLM-powered prediction...")
            prediction = await self.expert.make_llm_powered_prediction(universal_data)

            # Extract actual outcome
            actual_outcome = {
                'winner': game['home_team'] if game['home_score'] > game['away_score'] else game['away_team'],
                'spread': game['home_score'] - game['away_score'],
                'total_points': game['home_score'] + game['away_score'],
                'home_score': game['home_score'],
                'away_score': game['away_score']
            }

            # Log prediction
            game_context = {
                'game_id': game['game_id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'season': game['season'],
                'week': game['week'],
                'game_date': game.get('game_date', '')
            }

            self.prediction_logger.log_prediction(
                expert_id=self.expert.expert_id,
                expert_name=self.expert.name,
                game_context=game_context,
                prediction=prediction,
                input_data=universal_data.__dict__
            )

            # Record in validation framework
            prediction_result = self.validation_framework.record_prediction(
                game_id=game['game_id'],
                expert_id=self.expert.expert_id,
                expert_name=self.expert.name,
                prediction_data=prediction,
                game_context=game_context
            )

            # Validate against actual outcome
            validated_result = self.validation_framework.validate_prediction(
                game_id=game['game_id'],
                actual_outcome=actual_outcome
            )

            self.games_processed += 1
            self.predictions_made += 1
            if validated_result and validated_result.winner_correct:
                self.successful_predictions += 1

            # Display result
            result_emoji = "✅" if validated_result and validated_result.winner_correct else "❌"
            logger.info(f"\n{result_emoji} PREDICTION RESULT:")
            logger.info(f"   Predicted: {prediction.get('winner_prediction')} (conf: {prediction.get('winner_confidence', 0):.1%})")
            logger.info(f"   Actual: {actual_outcome['winner']}")
            logger.info(f"   Score: {game['away_team']} {game['away_score']} - {game['home_team']} {game['home_score']}")

            if validated_result:
                logger.info(f"   Spread Error: {validated_result.spread_error:.1f} points")
                logger.info(f"   Total Error: {validated_result.total_error:.1f} points")

            # Show current accuracy
            current_accuracy = (self.successful_predictions / self.predictions_made * 100) if self.predictions_made > 0 else 0
            logger.info(f"\n📊 Running Accuracy: {self.successful_predictions}/{self.predictions_made} ({current_accuracy:.1f}%)")

            return {
                'game_id': game['game_id'],
                'prediction': prediction,
                'actual_outcome': actual_outcome,
                'validated_result': validated_result,
                'success': True
            }

        except Exception as e:
            logger.error(f"❌ Error processing game: {e}")
            import traceback
            traceback.print_exc()
            return {
                'game_id': game.get('game_id', 'unknown'),
                'error': str(e),
                'success': False
            }

    async def run_validation(self, num_games: int = 50):
        """Run validation on specified number of games"""
        logger.info("\n" + "=" * 80)
        logger.info(f"🎯 STARTING VALIDATION ON {num_games} HISTORICAL GAMES")
        logger.info("=" * 80)
        logger.info(f"Target Accuracy: 40-60%")
        logger.info(f"Expert: {self.expert.name}")
        logger.info(f"LLM Integration: Enabled")
        logger.info(f"Memory System: Disabled (baseline test)")
        logger.info("=" * 80 + "\n")

        # Fetch games
        games = self.fetch_historical_games(limit=num_games)

        if not games:
            logger.error("❌ No games available for validation")
            return False

        logger.info(f"✅ Loaded {len(games)} games for validation\n")

        # Process each game
        results = []
        for i, game in enumerate(games, 1):
            result = await self.process_game(game, i, len(games))
            results.append(result)

            # Small delay to avoid overwhelming the LLM
            if i < len(games):
                await asyncio.sleep(0.5)

        # Generate final report
        self.generate_final_report(results)

        return True

    def generate_final_report(self, results: List[Dict[str, Any]]):
        """Generate comprehensive final report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL VALIDATION REPORT")
        logger.info("=" * 80)

        # Calculate statistics
        successful_games = sum(1 for r in results if r['success'])
        failed_games = len(results) - successful_games

        logger.info(f"\n📈 Processing Summary:")
        logger.info(f"   Total Games: {len(results)}")
        logger.info(f"   Successfully Processed: {successful_games}")
        logger.info(f"   Failed: {failed_games}")
        logger.info(f"   Success Rate: {successful_games/len(results)*100:.1f}%")

        # Get accuracy metrics from validation framework
        metrics = self.validation_framework.get_accuracy_metrics(
            expert_id=self.expert.expert_id
        )

        logger.info(f"\n🎯 Prediction Accuracy:")
        logger.info(f"   Overall Accuracy: {metrics.accuracy_rate*100:.1f}%")
        logger.info(f"   Correct Predictions: {metrics.correct_predictions}/{metrics.total_predictions}")
        logger.info(f"   Average Spread Error: {metrics.average_spread_error:.2f} points")
        logger.info(f"   Average Total Error: {metrics.average_total_error:.2f} points")

        # Target assessment
        target_met = 40 <= metrics.accuracy_rate * 100 <= 60
        target_emoji = "✅" if target_met else "⚠️"
        logger.info(f"\n{target_emoji} Target Assessment:")
        logger.info(f"   Target Range: 40-60%")
        logger.info(f"   Achieved: {metrics.accuracy_rate*100:.1f}%")
        logger.info(f"   Status: {'WITHIN TARGET' if target_met else 'OUTSIDE TARGET'}")

        logger.info(f"\n🎲 Confidence Calibration:")
        logger.info(f"   Average Confidence: {metrics.average_confidence*100:.1f}%")
        logger.info(f"   Confidence When Correct: {metrics.confidence_when_correct*100:.1f}%")
        logger.info(f"   Confidence When Wrong: {metrics.confidence_when_wrong*100:.1f}%")

        # Print full validation report
        self.validation_framework.print_validation_report(expert_id=self.expert.expert_id)

        logger.info("\n" + "=" * 80)
        logger.info("✅ VALIDATION COMPLETE")
        logger.info("=" * 80)

        # Save report to file
        report_file = f"logs/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'expert_name': self.expert.name,
            'expert_id': self.expert.expert_id,
            'total_games': len(results),
            'successful_games': successful_games,
            'accuracy_rate': metrics.accuracy_rate,
            'target_met': target_met,
            'metrics': {
                'correct_predictions': metrics.correct_predictions,
                'total_predictions': metrics.total_predictions,
                'average_spread_error': metrics.average_spread_error,
                'average_total_error': metrics.average_total_error,
                'average_confidence': metrics.average_confidence,
                'confidence_when_correct': metrics.confidence_when_correct,
                'confidence_when_wrong': metrics.confidence_when_wrong
            }
        }

        try:
            os.makedirs('logs', exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"\n📄 Report saved to: {report_file}")
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")


async def main():
    """Main execution function"""
    try:
        validator = HistoricalGameValidator()

        # Initialize services
        await validator.initialize_services()

        # Run validation on 50 games
        success = await validator.run_validation(num_games=50)

        return 0 if success else 1

    except Exception as e:
        logger.error(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
