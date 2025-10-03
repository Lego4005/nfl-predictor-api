"""
Data Validator for NFL Prediction System

This module provides comprehensive null checking and data validation
with fallback values for all critical data points. It implements
graceful degradation when data is miss

Requirements: 8.1, 8.4
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)

@dataclass
class LeagueAverages:
    """League average values for fallback data"""
    points_per_game: float = 22.5
    points_allowed_per_game: float = 22.5
    win_percentage: float = 0.5
    home_field_advantage: float = 3.0
    average_total_points: float = 45.0
    average_spread: float = 0.0
    default_temperature: float = 70.0
    default_wind_speed: float = 5.0
    default_humidity: float = 50.0

class DataValidator:
    """Comprehensive data validator with null checking and fallback values"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.league_averages = LeagueAverages()
        self.validation_stats = {
            'total_validations': 0,
            'fixes_applied': 0,
            'critical_errors': 0
        }

    def validate_universal_game_data(self, universal_data) -> ValidationResult:
        """Validate and fix UniversalGameData object"""
        self.validation_stats['total_validations'] += 1
        result = ValidationResult(is_valid=True)

        try:
            # Validate basic game info
            self._validate_basic_game_info(universal_data, result)

            # Validate weather data
            self._validate_weather_data(universal_data, result)

            # Validate team stats
            self._validate_team_stats(universal_data, result)

            # Validate betting lines
            self._validate_betting_lines(universal_data, result)

            # Validate head-to-head data
            self._validate_head_to_head_data(universal_data, result)

            # Validate coaching info
            self._validate_coaching_info(universal_data, result)

            # Update stats
            if result.fixes_applied:
                self.validation_stats['fixes_applied'] += len(result.fixes_applied)

            if result.errors:
                result.is_valid = False
                self.validation_stats['critical_errors'] += len(result.errors)

            self.logger.info(f"Validation complete: {len(result.fixes_applied)} fixes, {len(result.warnings)} warnings, {len(result.errors)} errors")

            return result

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            result.is_valid = False
            result.errors.append(f"Validation exception: {e}")
            return result

    def _validate_basic_game_info(self, universal_data, result: ValidationResult):
        """Validate basic game information"""
        # Check home team
        if not universal_data.home_team or universal_data.home_team.strip() == '':
            result.errors.append("Missing home team")

        # Check away team
        if not universal_data.away_team or universal_data.away_team.strip() == '':
            result.errors.append("Missing away team")

        # Check game time
        if not universal_data.game_time or universal_data.game_time.strip() == '':
            universal_data.game_time = "Unknown game time"
            result.fixes_applied.append("Set default game time")

        # Check location
        if not universal_data.location or universal_data.location.strip() == '':
            universal_data.location = "Unknown Stadium"
            result.fixes_applied.append("Set default stadium location")

    def _validate_weather_data(self, universal_data, result: ValidationResult):
        """Validate and fix weather data"""
        if not hasattr(universal_data, 'weather') or not universal_data.weather:
            universal_data.weather = {}

        weather = universal_data.weather

        # Temperature validation
        if weather.get('temperature') is None:
            # Check if it's a dome game
            if weather.get('is_dome', False):
                weather['temperature'] = 72.0  # Controlled environment
                result.fixes_applied.append("Set dome temperature to 72°F")
            else:
                weather['temperature'] = self.league_averages.default_temperature
                result.fixes_applied.append(f"Set default temperature to {self.league_averages.default_temperature}°F")
        elif not isinstance(weather['temperature'], (int, float)):
            try:
                weather['temperature'] = float(weather['temperature'])
                result.fixes_applied.append("Converted temperature to numeric")
            except (ValueError, TypeError):
                weather['temperature'] = self.league_averages.default_temperature
                result.fixes_applied.append("Fixed invalid temperature with default")

        # Wind speed validation
        if weather.get('wind_speed') is None:
            if weather.get('is_dome', False):
                weather['wind_speed'] = 0.0  # No wind in dome
                result.fixes_applied.append("Set dome wind speed to 0 mph")
            else:
                weather['wind_speed'] = self.league_averages.default_wind_speed
                result.fixes_applied.append(f"Set default wind speed to {self.league_averages.default_wind_speed} mph")
        elif not isinstance(weather['wind_speed'], (int, float)):
            try:
                weather['wind_speed'] = float(weather['wind_speed'])
                result.fixes_applied.append("Converted wind speed to numeric")
            except (ValueError, TypeError):
                weather['wind_speed'] = self.league_averages.default_wind_speed
                result.fixes_applied.append("Fixed invalid wind speed with default")

        # Humidity validation
        if weather.get('humidity') is None:
            weather['humidity'] = self.league_averages.default_humidity
            result.fixes_applied.append(f"Set default humidity to {self.league_averages.default_humidity}%")
        elif not isinstance(weather['humidity'], (int, float)):
            try:
                weather['humidity'] = float(weather['humidity'])
                result.fixes_applied.append("Converted humidity to numeric")
            except (ValueError, TypeError):
                weather['humidity'] = self.league_averages.default_humidity
                result.fixes_applied.append("Fixed invalid humidity with default")

        # Conditions validation
        if not weather.get('conditions') or weather['conditions'] in [None, '', 'null']:
            weather['conditions'] = 'Clear'
            result.fixes_applied.append("Set default weather conditions to 'Clear'")

        # Dome flag validation
        if weather.get('is_dome') is None:
            weather['is_dome'] = False
            result.fixes_applied.append("Set default dome flag to False")

    def _validate_team_stats(self, universal_data, result: ValidationResult):
        """Validate and fix team statistics"""
        if not hasattr(universal_data, 'team_stats') or not universal_data.team_stats:
            universal_data.team_stats = {'home': {}, 'away': {}}

        for team_type in ['home', 'away']:
            if team_type not in universal_data.team_stats:
                universal_data.team_stats[team_type] = {}

            team_stats = universal_data.team_stats[team_type]

            # Wins validation
            if team_stats.get('wins') is None:
                team_stats['wins'] = 0  # Week 1 default
                result.fixes_applied.append(f"Set default {team_type} wins to 0 (Week 1)")
            elif not isinstance(team_stats['wins'], (int, float)):
                try:
                    team_stats['wins'] = int(team_stats['wins'])
                    result.fixes_applied.append(f"Converted {team_type} wins to integer")
                except (ValueError, TypeError):
                    team_stats['wins'] = 0
                    result.fixes_applied.append(f"Fixed invalid {team_type} wins with 0")

            # Losses validation
            if team_stats.get('losses') is None:
                team_stats['losses'] = 0  # Week 1 default
                result.fixes_applied.append(f"Set default {team_type} losses to 0 (Week 1)")
            elif not isinstance(team_stats['losses'], (int, float)):
                try:
                    team_stats['losses'] = int(team_stats['losses'])
                    result.fixes_applied.append(f"Converted {team_type} losses to integer")
                except (ValueError, TypeError):
                    team_stats['losses'] = 0
                    result.fixes_applied.append(f"Fixed invalid {team_type} losses with 0")

            # Points per game validation
            if team_stats.get('points_per_game') is None:
                team_stats['points_per_game'] = self.league_averages.points_per_game
                result.fixes_applied.append(f"Set {team_type} points per game to league average ({self.league_averages.points_per_game})")
            elif not isinstance(team_stats['points_per_game'], (int, float)):
                try:
                    team_stats['points_per_game'] = float(team_stats['points_per_game'])
                    result.fixes_applied.append(f"Converted {team_type} points per game to float")
                except (ValueError, TypeError):
                    team_stats['points_per_game'] = self.league_averages.points_per_game
                    result.fixes_applied.append(f"Fixed invalid {team_type} points per game with league average")

            # Points allowed per game validation
            if team_stats.get('points_allowed_per_game') is None:
                team_stats['points_allowed_per_game'] = self.league_averages.points_allowed_per_game
                result.fixes_applied.append(f"Set {team_type} points allowed per game to league average ({self.league_averages.points_allowed_per_game})")
            elif not isinstance(team_stats['points_allowed_per_game'], (int, float)):
                try:
                    team_stats['points_allowed_per_game'] = float(team_stats['points_allowed_per_game'])
                    result.fixes_applied.append(f"Converted {team_type} points allowed per game to float")
                except (ValueError, TypeError):
                    team_stats['points_allowed_per_game'] = self.league_averages.points_allowed_per_game
                    result.fixes_applied.append(f"Fixed invalid {team_type} points allowed per game with league average")

            # Win percentage validation
            if team_stats.get('win_percentage') is None:
                team_stats['win_percentage'] = self.league_averages.win_percentage
                result.fixes_applied.append(f"Set {team_type} win percentage to league average ({self.league_averages.win_percentage})")
            elif not isinstance(team_stats['win_percentage'], (int, float)):
                try:
                    team_stats['win_percentage'] = float(team_stats['win_percentage'])
                    result.fixes_applied.append(f"Converted {team_type} win percentage to float")
                except (ValueError, TypeError):
                    team_stats['win_percentage'] = self.league_averages.win_percentage
                    result.fixes_applied.append(f"Fixed invalid {team_type} win percentage with league average")

            # Recent form validation
            if team_stats.get('recent_form') is None:
                team_stats['recent_form'] = ''
                result.fixes_applied.append(f"Set {team_type} recent form to empty string")
            elif not isinstance(team_stats['recent_form'], str):
                team_stats['recent_form'] = str(team_stats['recent_form'])
                result.fixes_applied.append(f"Converted {team_type} recent form to string")

            # Recent games count validation
            if team_stats.get('recent_games_count') is None:
                team_stats['recent_games_count'] = 0
                result.fixes_applied.append(f"Set {team_type} recent games count to 0")
            elif not isinstance(team_stats['recent_games_count'], int):
                try:
                    team_stats['recent_games_count'] = int(team_stats['recent_games_count'])
                    result.fixes_applied.append(f"Converted {team_type} recent games count to integer")
                except (ValueError, TypeError):
                    team_stats['recent_games_count'] = 0
                    result.fixes_applied.append(f"Fixed invalid {team_type} recent games count with 0")

    def _validate_betting_lines(self, universal_data, result: ValidationResult):
        """Validate and fix betting line data"""
        if not hasattr(universal_data, 'line_movement') or not universal_data.line_movement:
            universal_data.line_movement = {}

        line_movement = universal_data.line_movement

        # Opening line validation (spread)
        if line_movement.get('opening_line') is None:
            line_movement['opening_line'] = self.league_averages.average_spread
            result.fixes_applied.append(f"Set default opening line to {self.league_averages.average_spread}")
        elif isinstance(line_movement['opening_line'], str):
            try:
                line_movement['opening_line'] = float(line_movement['opening_line'])
                result.fixes_applied.append("Converted opening line from string to float")
            except (ValueError, TypeError):
                line_movement['opening_line'] = self.league_averages.average_spread
                result.fixes_applied.append("Fixed invalid opening line with default")

        # Current line validation
        if line_movement.get('current_line') is None:
            line_movement['current_line'] = line_movement.get('opening_line', self.league_averages.average_spread)
            result.fixes_applied.append("Set current line to opening line")
        elif isinstance(line_movement['current_line'], str):
            try:
                line_movement['current_line'] = float(line_movement['current_line'])
                result.fixes_applied.append("Converted current line from string to float")
            except (ValueError, TypeError):
                line_movement['current_line'] = line_movement.get('opening_line', self.league_averages.average_spread)
                result.fixes_applied.append("Fixed invalid current line with opening line")

        # Total line validation
        if line_movement.get('total_line') is None:
            line_movement['total_line'] = self.league_averages.average_total_points
            result.fixes_applied.append(f"Set default total line to {self.league_averages.average_total_points}")
        elif isinstance(line_movement['total_line'], str):
            try:
                line_movement['total_line'] = float(line_movement['total_line'])
                result.fixes_applied.append("Converted total line from string to float")
            except (ValueError, TypeError):
                line_movement['total_line'] = self.league_averages.average_total_points
                result.fixes_applied.append("Fixed invalid total line with default")

        # Moneyline validation
        for ml_type in ['home_moneyline', 'away_moneyline']:
            if line_movement.get(ml_type) is None:
                line_movement[ml_type] = -110 if ml_type == 'home_moneyline' else 110  # Default even odds
                result.fixes_applied.append(f"Set default {ml_type} to {line_movement[ml_type]}")
            elif not isinstance(line_movement[ml_type], (int, float)):
                try:
                    line_movement[ml_type] = int(line_movement[ml_type])
                    result.fixes_applied.append(f"Converted {ml_type} to integer")
                except (ValueError, TypeError):
                    line_movement[ml_type] = -110 if ml_type == 'home_moneyline' else 110
                    result.fixes_applied.append(f"Fixed invalid {ml_type} with default")

        # Public percentage validation
        if line_movement.get('public_percentage') is None:
            line_movement['public_percentage'] = 50.0  # Neutral
            result.fixes_applied.append("Set default public percentage to 50%")
        elif not isinstance(line_movement['public_percentage'], (int, float)):
            try:
                line_movement['public_percentage'] = float(line_movement['public_percentage'])
                result.fixes_applied.append("Converted public percentage to float")
            except (ValueError, TypeError):
                line_movement['public_percentage'] = 50.0
                result.fixes_applied.append("Fixed invalid public percentage with 50%")

    def _validate_head_to_head_data(self, universal_data, result: ValidationResult):
        """Validate and fix head-to-head data"""
        if not hasattr(universal_data, 'head_to_head') or not universal_data.head_to_head:
            universal_data.head_to_head = {}

        h2h = universal_data.head_to_head

        # Total games validation
        if h2h.get('total_games') is None:
            h2h['total_games'] = 0
            result.fixes_applied.append("Set default total H2H games to 0")
        elif not isinstance(h2h['total_games'], int):
            try:
                h2h['total_games'] = int(h2h['total_games'])
                result.fixes_applied.append("Converted total H2H games to integer")
            except (ValueError, TypeError):
                h2h['total_games'] = 0
                result.fixes_applied.append("Fixed invalid total H2H games with 0")

        # Recent games validation
        if h2h.get('recent_games') is None:
            h2h['recent_games'] = []
            result.fixes_applied.append("Set default recent H2H games to empty list")
        elif not isinstance(h2h['recent_games'], list):
            h2h['recent_games'] = []
            result.fixes_applied.append("Fixed invalid recent H2H games with empty list")

        # Win counts validation
        for team_type in ['home_team_wins', 'away_team_wins']:
            if h2h.get(team_type) is None:
                h2h[team_type] = 0
                result.fixes_applied.append(f"Set default {team_type} to 0")
            elif not isinstance(h2h[team_type], int):
                try:
                    h2h[team_type] = int(h2h[team_type])
                    result.fixes_applied.append(f"Converted {team_type} to integer")
                except (ValueError, TypeError):
                    h2h[team_type] = 0
                    result.fixes_applied.append(f"Fixed invalid {team_type} with 0")

        # Average total validation
        if h2h.get('average_total') is None:
            h2h['average_total'] = self.league_averages.average_total_points
            result.fixes_applied.append(f"Set default H2H average total to {self.league_averages.average_total_points}")
        elif not isinstance(h2h['average_total'], (int, float)):
            try:
                h2h['average_total'] = float(h2h['average_total'])
                result.fixes_applied.append("Converted H2H average total to float")
            except (ValueError, TypeError):
                h2h['average_total'] = self.league_averages.average_total_points
                result.fixes_applied.append("Fixed invalid H2H average total with league average")

        # Average margin validation
        if h2h.get('average_margin') is None:
            h2h['average_margin'] = 0.0
            result.fixes_applied.append("Set default H2H average margin to 0.0")
        elif not isinstance(h2h['average_margin'], (int, float)):
            try:
                h2h['average_margin'] = float(h2h['average_margin'])
                result.fixes_applied.append("Converted H2H average margin to float")
            except (ValueError, TypeError):
                h2h['average_margin'] = 0.0
                result.fixes_applied.append("Fixed invalid H2H average margin with 0.0")

    def _validate_coaching_info(self, universal_data, result: ValidationResult):
        """Validate and fix coaching information"""
        if not hasattr(universal_data, 'coaching_info') or not universal_data.coaching_info:
            universal_data.coaching_info = {}

        coaching = universal_data.coaching_info

        # Coach names validation
        for coach_type in ['home_coach', 'away_coach']:
            if coaching.get(coach_type) is None or coaching[coach_type] == '':
                coaching[coach_type] = 'Unknown Coach'
                result.fixes_applied.append(f"Set default {coach_type} to 'Unknown Coach'")
            elif not isinstance(coaching[coach_type], str):
                coaching[coach_type] = str(coaching[coach_type])
                result.fixes_applied.append(f"Converted {coach_type} to string")

    def validate_prediction_inputs(self, prediction_data: Dict[str, Any]) -> ValidationResult:
        """Validate prediction input data before processing"""
        result = ValidationResult(is_valid=True)

        # Check for required prediction fields
        required_fields = ['winner_prediction', 'winner_confidence', 'total_prediction', 'spread_prediction']

        for field in required_fields:
            if field not in prediction_data or prediction_data[field] is None:
                if field == 'winner_prediction':
                    prediction_data[field] = 'home'  # Default to home team
                    result.fixes_applied.append("Set default winner prediction to 'home'")
                elif field == 'winner_confidence':
                    prediction_data[field] = 0.5  # Neutral confidence
                    result.fixes_applied.append("Set default winner confidence to 0.5")
                elif field == 'total_prediction':
                    prediction_data[field] = self.league_averages.average_total_points
                    result.fixes_applied.append(f"Set default total prediction to {self.league_averages.average_total_points}")
                elif field == 'spread_prediction':
                    prediction_data[field] = self.league_averages.average_spread
                    result.fixes_applied.append(f"Set default spread prediction to {self.league_averages.average_spread}")

        return result

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'total_validations': self.validation_stats['total_validations'],
            'fixes_applied': self.validation_stats['fixes_applied'],
            'critical_errors': self.validation_stats['critical_errors'],
            'fix_rate': self.validation_stats['fixes_applied'] / max(1, self.validation_stats['total_validations']),
            'error_rate': self.validation_stats['critical_errors'] / max(1, self.validation_stats['total_validations'])
        }

    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {
            'total_validations': 0,
            'fixes_applied': 0,
            'critical_errors': 0
        }

# Global validator instance
_global_validator = None

def get_validator() -> DataValidator:
    """Get global validator instance"""
    global _global_validator
    if _global_validator is None:
        _global_validator = DataValidator()
    return _global_validator

def validate_and_fix_universal_data(universal_data) -> ValidationResult:
    """Convenience function to validate and fix UniversalGameData"""
    validator = get_validator()
    return validator.validate_universal_game_data(universal_data)

def validate_prediction_data(prediction_data: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate prediction data"""
    validator = get_validator()
    return validator.validate_prediction_inputs(prediction_data)
