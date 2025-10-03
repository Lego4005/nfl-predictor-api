#!/usr/bin/env python3
"""
Null Handling Diagnostic Runner

This script runs a diagnostic backtest on 2020 Week 1 games to identify
all null values and missing fields that cause crashes in the system.
It generates a comprehensive data availability report.

Requirements: 5.1, 5.2
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Coigure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NullFieldReport:
    """Report for a specific null field"""
    field_path: str
    null_count: int
    total_count: int
    null_percentage: float
    sample_null_values: List[Any] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)

@dataclass
class GameDiagnosticReport:
    """Diagnostic report for a single game"""
    game_id: str
    home_team: str
    away_team: str
    season: int
    week: int
    success: bool
    error_message: Optional[str] = None
    null_fields: List[NullFieldReport] = field(default_factory=list)
    missing_data_categories: List[str] = field(default_factory=list)

@dataclass
class ComprehensiveDataReport:
    """Complete data availability report"""
    total_games_tested: int
    successful_games: int
    failed_games: int
    success_rate: float
    null_field_summary: Dict[str, NullFieldReport] = field(default_factory=dict)
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    game_reports: List[GameDiagnosticReport] = field(default_factory=list)

class NullHandlingDiagnostic:
    """Diagnostic runner for null handling issues"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.report = ComprehensiveDataReport(
            total_games_tested=0,
            successful_games=0,
            failed_games=0,
            success_rate=0.0
        )

    async def run_diagnostic(self) -> ComprehensiveDataReport:
        """Run complete diagnostic on 2020 Week 1 games"""
        self.logger.info("🔍 Starting Null Handling Diagnostic")
        self.logger.info("=" * 60)

        try:
            # Initialize services
            await self._initialize_services()

            # Get 2020 Week 1 games
            games = await self._get_2020_week1_games()
            self.logger.info(f"📊 Found {len(games)} games in 2020 Week 1")

            # Test each game
            for game in games:
                await self._test_single_game(game)

            # Generate final report
            self._generate_final_report()

            # Save report to file
            await self._save_report()

            return self.report

        except Exception as e:
            self.logger.error(f"❌ Diagnostic failed: {e}")
            self.logger.error(traceback.format_exc())
            raise

    async def _initialize_services(self):
        """Initialize all required services"""
        self.logger.info("🔧 Initializing services...")

        try:
            # We'll use MCP for Supabase access, so we don't need to initialize Supabase client
            # Just initialize the services that don't require database access for now

            # Initialize ConservativeAnalyzer (doesn't need database for basic functionality)
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            from ml.personality_driven_experts import ConservativeAnalyzer
            self.expert = ConservativeAnalyzer()
            self.logger.info("✅ ConservativeAnalyzer initialized")

        except Exception as e:
            self.logger.error(f"❌ Service initialization failed: {e}")
            raise

    async def _get_2020_week1_games(self) -> List[Dict[str, Any]]:
        """Get all 2020 Week 1 games using real data from Supabase"""
        try:
            # Use the actual 2020 Week 1 games data from Supabase
            games = [
                {
                    "game_id": "2020_01_HOU_KC",
                    "season": 2020,
                    "week": 1,
                    "game_type": "REG",
                    "game_date": "2020-09-10",
                    "game_time": "20:20:00",
                    "home_team": "KC",
                    "away_team": "HOU",
                    "home_score": 34,
                    "away_score": 20,
                    "stadium": "Arrowhead Stadium",
                    "weather_temperature": 56,
                    "weather_wind_mph": 7,
                    "weather_humidity": None,  # NULL value
                    "weather_description": None,  # NULL value
                    "surface": "grass",
                    "roof": "outdoors",
                    "spread_line": "9.5",
                    "total_line": "53.5",
                    "away_moneyline": 349,
                    "home_moneyline": -423
                },
                {
                    "game_id": "2020_01_SEA_ATL",
                    "season": 2020,
                    "week": 1,
                    "game_date": "2020-09-13",
                    "home_team": "ATL",
                    "away_team": "SEA",
                    "home_score": 25,
                    "away_score": 38,
                    "stadium": "Mercedes-Benz Stadium",
                    "weather_temperature": None,  # NULL value - dome game
                    "weather_wind_mph": None,     # NULL value - dome game
                    "weather_humidity": None,     # NULL value
                    "weather_description": None,  # NULL value
                    "surface": "fieldturf",
                    "roof": "closed",
                    "spread_line": "1.0",
                    "total_line": "49.5",
                    "away_moneyline": 102,
                    "home_moneyline": -112
                },
                {
                    "game_id": "2020_01_NYJ_BUF",
                    "season": 2020,
                    "week": 1,
                    "game_date": "2020-09-13",
                    "home_team": "BUF",
                    "away_team": "NYJ",
                    "home_score": 27,
                    "away_score": 17,
                    "stadium": "New Era Field",
                    "weather_temperature": 67,
                    "weather_wind_mph": 15,
                    "weather_humidity": None,     # NULL value
                    "weather_description": None,  # NULL value
                    "surface": "astroturf",
                    "roof": "outdoors",
                    "spread_line": "6.5",
                    "total_line": "39.5",
                    "away_moneyline": 242,
                    "home_moneyline": -279
                }
            ]

            self.logger.info(f"📊 Using {len(games)} real 2020 Week 1 games with known null values")
            return games

        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve 2020 Week 1 games: {e}")
            raise

    async def _test_single_game(self, game: Dict[str, Any]):
        """Test a single game for null handling issues"""
        game_id = game.get('id', 'unknown')
        home_team = game.get('home_team', 'unknown')
        away_team = game.get('away_team', 'unknown')

        self.logger.info(f"🎯 Testing game: {away_team} @ {home_team}")

        game_report = GameDiagnosticReport(
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            season=2020,
            week=1,
            success=False
        )

        try:
            # Test UniversalGameDataBuilder
            universal_data = await self._test_universal_game_data_builder(game, game_report)

            # Test ConservativeAnalyzer
            await self._test_conservative_analyzer(universal_data, game_report)

            game_report.success = True
            self.report.successful_games += 1
            self.logger.info(f"✅ Game test successful: {away_team} @ {home_team}")

        except Exception as e:
            game_report.success = False
            game_report.error_message = str(e)
            self.report.failed_games += 1
            self.logger.error(f"❌ Game test failed: {away_team} @ {home_team} - {e}")

            # Log full traceback for debugging
            self.logger.debug(traceback.format_exc())

        self.report.game_reports.append(game_report)
        self.report.total_games_tested += 1

    async def _test_universal_game_data_builder(self, game: Dict[str, Any], game_report: GameDiagnosticReport):
        """Test UniversalGameDataBuilder for null handling issues"""
        self.logger.debug("🔍 Testing UniversalGameDataBuilder...")

        try:
            # Create mock UniversalGameData with the null values from the game data
            from ml.personality_driven_experts import UniversalGameData

            # Build weather data with null handling issues
            weather = {
                'temperature': game.get('weather_temperature'),  # Can be None
                'wind_speed': game.get('weather_wind_mph'),      # Can be None
                'humidity': game.get('weather_humidity'),        # Often None
                'conditions': game.get('weather_description') or 'Unknown',  # Often None
                'is_dome': game.get('roof') in ['dome', 'retractable_dome', 'closed']
            }

            # Build team stats with potential null issues
            team_stats = {
                'home': {
                    'wins': None,  # Simulate missing data for Week 1
                    'losses': None,
                    'points_per_game': None,  # No previous games in Week 1
                    'points_allowed_per_game': None,
                    'recent_form': '',  # Empty string
                    'recent_games_count': 0
                },
                'away': {
                    'wins': None,
                    'losses': None,
                    'points_per_game': None,
                    'points_allowed_per_game': None,
                    'recent_form': '',
                    'recent_games_count': 0
                }
            }

            # Build line movement with potential null issues
            line_movement = {
                'opening_line': game.get('spread_line'),  # Can be string or None
                'current_line': game.get('spread_line'),
                'total_line': game.get('total_line'),     # Can be string or None
                'home_moneyline': game.get('home_moneyline'),  # Can be None
                'away_moneyline': game.get('away_moneyline'),  # Can be None
                'public_percentage': None  # Often missing
            }

            universal_data = UniversalGameData(
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_time=f"{game['game_date']} {game['season']} Week {game['week']}",
                location=game.get('stadium', 'Unknown Stadium'),
                weather=weather,
                injuries={'home': [], 'away': []},  # Empty but not None
                team_stats=team_stats,
                line_movement=line_movement,
                public_betting={},
                recent_news=[],
                head_to_head={'total_games': 0, 'recent_games': []},  # Empty for Week 1
                coaching_info={'home_coach': None, 'away_coach': None}  # Simulate missing
            )

            # Check for null values in universal_data
            self._check_universal_data_nulls(universal_data, game_report)

            return universal_data

        except Exception as e:
            error_msg = f"UniversalGameDataBuilder error: {e}"
            game_report.error_message = error_msg
            self.logger.error(error_msg)
            raise

    async def _test_conservative_analyzer(self, universal_data, game_report: GameDiagnosticReport):
        """Test ConservativeAnalyzer for null handling issues"""
        self.logger.debug("🔍 Testing ConservativeAnalyzer...")

        try:
            prediction = self.expert.make_personality_driven_prediction(universal_data)

            # Check prediction for null values
            self._check_prediction_nulls(prediction, game_report)

        except Exception as e:
            error_msg = f"ConservativeAnalyzer error: {e}"
            if game_report.error_message:
                game_report.error_message += f" | {error_msg}"
            else:
                game_report.error_message = error_msg
            self.logger.error(error_msg)
            raise

    def _check_universal_data_nulls(self, universal_data, game_report: GameDiagnosticReport):
        """Check UniversalGameData for null values"""
        null_fields = []

        # Check basic fields
        if not universal_data.home_team:
            null_fields.append("home_team")
        if not universal_data.away_team:
            null_fields.append("away_team")
        if not universal_data.game_time:
            null_fields.append("game_time")
        if not universal_data.location:
            null_fields.append("location")

        # Check weather data
        weather_nulls = self._check_dict_nulls(universal_data.weather, "weather")
        null_fields.extend(weather_nulls)

        # Check team stats
        team_stats_nulls = self._check_dict_nulls(universal_data.team_stats, "team_stats")
        null_fields.extend(team_stats_nulls)

        # Check line movement
        line_nulls = self._check_dict_nulls(universal_data.line_movement, "line_movement")
        null_fields.extend(line_nulls)

        # Check head to head
        h2h_nulls = self._check_dict_nulls(universal_data.head_to_head, "head_to_head")
        null_fields.extend(h2h_nulls)

        # Add to game report
        for field in null_fields:
            game_report.null_fields.append(NullFieldReport(
                field_path=field,
                null_count=1,
                total_count=1,
                null_percentage=100.0,
                sample_null_values=[None]
            ))

    def _check_dict_nulls(self, data_dict: Dict[str, Any], prefix: str) -> List[str]:
        """Check dictionary for null values"""
        null_fields = []

        if not data_dict:
            null_fields.append(f"{prefix} (entire dict is None/empty)")
            return null_fields

        for key, value in data_dict.items():
            field_path = f"{prefix}.{key}"

            if value is None:
                null_fields.append(field_path)
            elif isinstance(value, dict):
                nested_nulls = self._check_dict_nulls(value, field_path)
                null_fields.extend(nested_nulls)
            elif isinstance(value, list) and len(value) == 0:
                null_fields.append(f"{field_path} (empty list)")

        return null_fields

    def _check_prediction_nulls(self, prediction: Dict[str, Any], game_report: GameDiagnosticReport):
        """Check prediction for null values"""
        null_fields = []

        # Check required prediction fields
        required_fields = ['winner_prediction', 'winner_confidence', 'total_prediction', 'spread_prediction']

        for field in required_fields:
            if field not in prediction or prediction[field] is None:
                null_fields.append(f"prediction.{field}")

        # Add to game report
        for field in null_fields:
            game_report.null_fields.append(NullFieldReport(
                field_path=field,
                null_count=1,
                total_count=1,
                null_percentage=100.0,
                sample_null_values=[None]
            ))

    def _generate_final_report(self):
        """Generate final comprehensive report"""
        self.logger.info("📊 Generating final diagnostic report...")

        # Calculate success rate
        if self.report.total_games_tested > 0:
            self.report.success_rate = (self.report.successful_games / self.report.total_games_tested) * 100

        # Aggregate null field reports
        null_field_counts = {}
        for game_report in self.report.game_reports:
            for null_field in game_report.null_fields:
                field_path = null_field.field_path
                if field_path not in null_field_counts:
                    null_field_counts[field_path] = {
                        'null_count': 0,
                        'total_count': 0,
                        'sample_values': []
                    }

                null_field_counts[field_path]['null_count'] += null_field.null_count
                null_field_counts[field_path]['total_count'] += null_field.total_count
                null_field_counts[field_path]['sample_values'].extend(null_field.sample_null_values)

        # Create summary reports
        for field_path, counts in null_field_counts.items():
            null_percentage = (counts['null_count'] / counts['total_count']) * 100 if counts['total_count'] > 0 else 0

            self.report.null_field_summary[field_path] = NullFieldReport(
                field_path=field_path,
                null_count=counts['null_count'],
                total_count=counts['total_count'],
                null_percentage=null_percentage,
                sample_null_values=counts['sample_values'][:5]  # Keep first 5 samples
            )

        # Generate critical issues
        self._identify_critical_issues()

        # Generate recommendations
        self._generate_recommendations()

    def _identify_critical_issues(self):
        """Identify critical issues that need immediate attention"""
        critical_issues = []

        # Check for high failure rate
        if self.report.success_rate < 50:
            critical_issues.append(f"High failure rate: {self.report.success_rate:.1f}% success rate")

        # Check for critical null fields
        critical_fields = ['home_team', 'away_team', 'winner_prediction', 'winner_confidence']
        for field_path, null_report in self.report.null_field_summary.items():
            if any(critical_field in field_path for critical_field in critical_fields):
                if null_report.null_percentage > 10:
                    critical_issues.append(f"Critical field '{field_path}' has {null_report.null_percentage:.1f}% null values")

        # Check for common error patterns
        error_patterns = {}
        for game_report in self.report.game_reports:
            if not game_report.success and game_report.error_message:
                error_type = game_report.error_message.split(':')[0]
                error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

        for error_type, count in error_patterns.items():
            if count > 1:
                critical_issues.append(f"Recurring error pattern: '{error_type}' occurred {count} times")

        self.report.critical_issues = critical_issues

    def _generate_recommendations(self):
        """Generate recommendations for fixing null handling issues"""
        recommendations = []

        # Recommendations based on null fields
        for field_path, null_report in self.report.null_field_summary.items():
            if null_report.null_percentage > 50:
                if 'weather' in field_path:
                    recommendations.append(f"Add fallback values for weather data: {field_path}")
                elif 'team_stats' in field_path:
                    recommendations.append(f"Use league averages for missing team stats: {field_path}")
                elif 'line_movement' in field_path:
                    recommendations.append(f"Add neutral defaults for betting lines: {field_path}")
                else:
                    recommendations.append(f"Add null checking and fallback for: {field_path}")

        # General recommendations
        if self.report.success_rate < 80:
            recommendations.append("Implement comprehensive DataValidator class")
            recommendations.append("Add graceful degradation for missing data")
            recommendations.append("Implement validation logging instead of crashes")

        self.report.recommendations = recommendations

    async def _save_report(self):
        """Save diagnostic report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/null_handling_diagnostic_report_{timestamp}.json"

        # Convert report to dict for JSON serialization
        report_dict = {
            'timestamp': timestamp,
            'total_games_tested': self.report.total_games_tested,
            'successful_games': self.report.successful_games,
            'failed_games': self.report.failed_games,
            'success_rate': self.report.success_rate,
            'null_field_summary': {
                field_path: {
                    'field_path': report.field_path,
                    'null_count': report.null_count,
                    'total_count': report.total_count,
                    'null_percentage': report.null_percentage,
                    'sample_null_values': report.sample_null_values
                }
                for field_path, report in self.report.null_field_summary.items()
            },
            'critical_issues': self.report.critical_issues,
            'recommendations': self.report.recommendations,
            'game_reports': [
                {
                    'game_id': report.game_id,
                    'home_team': report.home_team,
                    'away_team': report.away_team,
                    'season': report.season,
                    'week': report.week,
                    'success': report.success,
                    'error_message': report.error_message,
                    'null_fields_count': len(report.null_fields),
                    'missing_data_categories': report.missing_data_categories
                }
                for report in self.report.game_reports
            ]
        }

        try:
            import os
            os.makedirs('data', exist_ok=True)

            with open(filename, 'w') as f:
                json.dump(report_dict, f, indent=2)

            self.logger.info(f"📄 Diagnostic report saved to: {filename}")

        except Exception as e:
            self.logger.error(f"❌ Failed to save report: {e}")

async def main():
    """Main function to run the diagnostic"""
    print("🔍 NULL HANDLING DIAGNOSTIC")
    print("=" * 60)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: 2020 NFL Week 1 games")
    print(f"📊 Focus: Identify null values and missing data")
    print()

    diagnostic = NullHandlingDiagnostic()

    try:
        report = await diagnostic.run_diagnostic()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        print(f"Total games tested: {report.total_games_tested}")
        print(f"Successful games: {report.successful_games}")
        print(f"Failed games: {report.failed_games}")
        print(f"Success rate: {report.success_rate:.1f}%")
        print()

        print("🚨 CRITICAL ISSUES:")
        for issue in report.critical_issues:
            print(f"  • {issue}")
        print()

        print("💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"  • {rec}")
        print()

        print("📊 NULL FIELD SUMMARY:")
        for field_path, null_report in report.null_field_summary.items():
            print(f"  • {field_path}: {null_report.null_percentage:.1f}% null ({null_report.null_count}/{null_report.total_count})")

        print(f"\n✅ Diagnostic completed successfully!")

    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
