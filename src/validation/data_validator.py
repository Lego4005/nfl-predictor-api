"""
Data Validation and Sanitization Layer

Comprehensive validation and sanitization for real-time NFL data pipeline.
Ensures data integrity, consistency, and security across all data sources.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from pydantic import BaseModel, Field, validator, ValidationError

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"  # Must pass or reject data
    WARNING = "warning"    # Log warning but allow data
    INFO = "info"         # Informational validation


class ValidationResult(Enum):
    """Validation result status"""
    VALID = "valid"
    INVALID = "invalid"
    SANITIZED = "sanitized"  # Data was modified to make it valid


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    field: str
    level: ValidationLevel
    message: str
    original_value: Any = None
    sanitized_value: Any = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    is_valid: bool
    result: ValidationResult
    issues: List[ValidationIssue]
    sanitized_data: Optional[Dict[str, Any]] = None

    def has_critical_issues(self) -> bool:
        """Check if there are any critical validation issues"""
        return any(issue.level == ValidationLevel.CRITICAL for issue in self.issues)

    def get_issues_by_level(self, level: ValidationLevel) -> List[ValidationIssue]:
        """Get validation issues by severity level"""
        return [issue for issue in self.issues if issue.level == level]


# Pydantic models for data validation

class NFLTeamModel(BaseModel):
    """NFL team validation model"""
    abbreviation: str = Field(..., min_length=2, max_length=4)
    city: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=50)

    @validator('abbreviation')
    def validate_team_abbreviation(cls, v):
        """Validate NFL team abbreviation"""
        valid_teams = {
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
        }

        if v.upper() not in valid_teams:
            raise ValueError(f'Invalid NFL team abbreviation: {v}')

        return v.upper()


class GameStateModel(BaseModel):
    """Game state validation model"""
    game_id: str = Field(..., min_length=1, max_length=50)
    home_team: str = Field(..., min_length=2, max_length=4)
    away_team: str = Field(..., min_length=2, max_length=4)
    home_score: int = Field(..., ge=0, le=100)
    away_score: int = Field(..., ge=0, le=100)
    quarter: Union[str, int] = Field(..., description="Quarter (1-4, OT, etc.)")
    time_remaining: str = Field(..., pattern=r'^\d{1,2}:\d{2}$')
    possession: Optional[str] = Field(None, min_length=2, max_length=4)
    down: Optional[int] = Field(None, ge=1, le=4)
    distance: Optional[int] = Field(None, ge=0, le=99)
    field_position: Optional[str] = None
    status: str = Field(..., max_length=20)
    week: Optional[int] = Field(None, ge=1, le=22)

    @validator('quarter')
    def validate_quarter(cls, v):
        """Validate quarter format"""
        if isinstance(v, int):
            if 1 <= v <= 4:
                return str(v)
            else:
                raise ValueError('Quarter must be between 1-4')

        if isinstance(v, str):
            if v.upper() in ['1', '2', '3', '4', 'OT', 'OT1', 'OT2', 'FINAL']:
                return v.upper()
            else:
                raise ValueError(f'Invalid quarter format: {v}')

        raise ValueError('Quarter must be string or integer')

    @validator('time_remaining')
    def validate_time_format(cls, v):
        """Validate time remaining format (MM:SS)"""
        if not re.match(r'^\d{1,2}:\d{2}$', v):
            raise ValueError('Time must be in MM:SS format')

        minutes, seconds = map(int, v.split(':'))
        if seconds >= 60:
            raise ValueError('Seconds must be less than 60')
        if minutes > 15:
            raise ValueError('Minutes cannot exceed 15 in a quarter')

        return v

    @validator('possession')
    def validate_possession(cls, v, values):
        """Validate possession team"""
        if v is None:
            return v

        home_team = values.get('home_team', '').upper()
        away_team = values.get('away_team', '').upper()

        if v.upper() not in [home_team, away_team]:
            raise ValueError(f'Possession team {v} must be either home ({home_team}) or away ({away_team})')

        return v.upper()


class PlayerStatsModel(BaseModel):
    """Player statistics validation model"""
    player_id: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    team: str = Field(..., min_length=2, max_length=4)
    position: str = Field(..., min_length=1, max_length=5)
    passing_yards: Optional[int] = Field(None, ge=0, le=1000)
    rushing_yards: Optional[int] = Field(None, ge=-50, le=500)
    receiving_yards: Optional[int] = Field(None, ge=0, le=500)
    receptions: Optional[int] = Field(None, ge=0, le=50)
    touchdowns: Optional[int] = Field(None, ge=0, le=10)

    @validator('position')
    def validate_position(cls, v):
        """Validate player position"""
        valid_positions = {
            'QB', 'RB', 'FB', 'WR', 'TE', 'OL', 'C', 'G', 'T',
            'DL', 'DE', 'DT', 'NT', 'LB', 'MLB', 'OLB', 'CB', 'S',
            'FS', 'SS', 'K', 'P', 'LS', 'KR', 'PR'
        }

        if v.upper() not in valid_positions:
            logger.warning(f'Unusual position: {v}')

        return v.upper()


class OddsDataModel(BaseModel):
    """Betting odds validation model"""
    game_id: str = Field(..., min_length=1, max_length=50)
    home_team: str = Field(..., min_length=2, max_length=4)
    away_team: str = Field(..., min_length=2, max_length=4)
    spread: Optional[float] = Field(None, ge=-50, le=50)
    total: Optional[float] = Field(None, ge=20, le=100)
    home_moneyline: Optional[int] = Field(None, ge=-2000, le=2000)
    away_moneyline: Optional[int] = Field(None, ge=-2000, le=2000)
    timestamp: datetime

    @validator('spread')
    def validate_spread(cls, v):
        """Validate point spread"""
        if v is not None and abs(v) > 30:
            logger.warning(f'Unusual point spread: {v}')
        return v

    @validator('total')
    def validate_total(cls, v):
        """Validate game total"""
        if v is not None and (v < 30 or v > 80):
            logger.warning(f'Unusual game total: {v}')
        return v


class DataValidator:
    """
    Main data validation and sanitization class

    Provides comprehensive validation for all NFL data types including:
    - Game states and scores
    - Player statistics
    - Betting odds
    - Team information
    - Real-time updates
    """

    def __init__(self):
        """Initialize data validator"""
        self.nfl_teams = {
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
        }

        self.valid_game_statuses = {
            'SCHEDULED', 'PRE', 'IN_PROGRESS', 'IN', 'HALFTIME',
            'FINAL', 'POSTPONED', 'CANCELLED', 'SUSPENDED'
        }

    def validate_game_data(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Validate game data

        Args:
            data: Raw game data dictionary

        Returns:
            ValidationReport with validation results
        """
        issues = []
        sanitized_data = data.copy()

        try:
            # Use Pydantic model for basic validation
            validated_data = GameStateModel(**sanitized_data)
            sanitized_data = validated_data.dict()

        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                issues.append(ValidationIssue(
                    field=field,
                    level=ValidationLevel.CRITICAL,
                    message=error['msg'],
                    original_value=data.get(field)
                ))

        # Additional custom validations
        issues.extend(self._validate_game_logic(sanitized_data))

        # Determine overall result
        has_critical = any(issue.level == ValidationLevel.CRITICAL for issue in issues)

        if has_critical:
            return ValidationReport(
                is_valid=False,
                result=ValidationResult.INVALID,
                issues=issues
            )
        elif issues:
            return ValidationReport(
                is_valid=True,
                result=ValidationResult.SANITIZED,
                issues=issues,
                sanitized_data=sanitized_data
            )
        else:
            return ValidationReport(
                is_valid=True,
                result=ValidationResult.VALID,
                issues=issues,
                sanitized_data=sanitized_data
            )

    def validate_player_stats(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Validate player statistics data

        Args:
            data: Raw player stats dictionary

        Returns:
            ValidationReport with validation results
        """
        issues = []
        sanitized_data = data.copy()

        try:
            # Use Pydantic model for validation
            validated_data = PlayerStatsModel(**sanitized_data)
            sanitized_data = validated_data.dict()

        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                issues.append(ValidationIssue(
                    field=field,
                    level=ValidationLevel.CRITICAL,
                    message=error['msg'],
                    original_value=data.get(field)
                ))

        # Additional validations
        issues.extend(self._validate_player_logic(sanitized_data))

        return self._create_validation_report(issues, sanitized_data)

    def validate_odds_data(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Validate betting odds data

        Args:
            data: Raw odds data dictionary

        Returns:
            ValidationReport with validation results
        """
        issues = []
        sanitized_data = data.copy()

        try:
            # Ensure timestamp is present
            if 'timestamp' not in sanitized_data:
                sanitized_data['timestamp'] = datetime.utcnow()

            # Use Pydantic model for validation
            validated_data = OddsDataModel(**sanitized_data)
            sanitized_data = validated_data.dict()

        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                issues.append(ValidationIssue(
                    field=field,
                    level=ValidationLevel.CRITICAL,
                    message=error['msg'],
                    original_value=data.get(field)
                ))

        # Additional validations
        issues.extend(self._validate_odds_logic(sanitized_data))

        return self._create_validation_report(issues, sanitized_data)

    def sanitize_text_input(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input to prevent injection attacks

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)[:max_length]

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)

        # Remove extra whitespace
        sanitized = ' '.join(sanitized.split())

        # Truncate to max length
        return sanitized[:max_length]

    def validate_api_response(self, response_data: Any, expected_structure: Dict) -> ValidationReport:
        """
        Validate API response structure

        Args:
            response_data: Raw API response
            expected_structure: Expected data structure

        Returns:
            ValidationReport with validation results
        """
        issues = []

        if not isinstance(response_data, dict):
            issues.append(ValidationIssue(
                field='root',
                level=ValidationLevel.CRITICAL,
                message='Response must be a dictionary',
                original_value=type(response_data).__name__
            ))
            return ValidationReport(is_valid=False, result=ValidationResult.INVALID, issues=issues)

        # Check required fields
        for field, field_type in expected_structure.items():
            if field not in response_data:
                issues.append(ValidationIssue(
                    field=field,
                    level=ValidationLevel.CRITICAL,
                    message=f'Required field {field} is missing'
                ))
            elif not isinstance(response_data[field], field_type):
                issues.append(ValidationIssue(
                    field=field,
                    level=ValidationLevel.WARNING,
                    message=f'Field {field} has incorrect type. Expected {field_type.__name__}, got {type(response_data[field]).__name__}',
                    original_value=response_data[field]
                ))

        return self._create_validation_report(issues, response_data)

    def _validate_game_logic(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate game-specific business logic"""
        issues = []

        # Check score consistency
        if 'status' in data and data['status'] == 'SCHEDULED':
            if data.get('home_score', 0) > 0 or data.get('away_score', 0) > 0:
                issues.append(ValidationIssue(
                    field='scores',
                    level=ValidationLevel.WARNING,
                    message='Scheduled game should not have scores'
                ))

        # Check possession logic
        if data.get('possession') and not data.get('down'):
            if data.get('status') == 'IN_PROGRESS':
                issues.append(ValidationIssue(
                    field='down',
                    level=ValidationLevel.WARNING,
                    message='Team has possession but no down information'
                ))

        # Check time remaining logic
        if data.get('quarter') == 'FINAL' and data.get('time_remaining') != '0:00':
            issues.append(ValidationIssue(
                field='time_remaining',
                level=ValidationLevel.WARNING,
                message='Final game should have 0:00 time remaining'
            ))

        return issues

    def _validate_player_logic(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate player statistics business logic"""
        issues = []

        # Check position-specific stats
        position = data.get('position', '')

        if position == 'QB':
            if data.get('receiving_yards', 0) > 0:
                issues.append(ValidationIssue(
                    field='receiving_yards',
                    level=ValidationLevel.WARNING,
                    message='QB should not have receiving yards'
                ))

        elif position in ['RB', 'FB']:
            if data.get('passing_yards', 0) > 0:
                issues.append(ValidationIssue(
                    field='passing_yards',
                    level=ValidationLevel.WARNING,
                    message='RB/FB should not have passing yards'
                ))

        # Check stat consistency
        receptions = data.get('receptions', 0)
        receiving_yards = data.get('receiving_yards', 0)

        if receptions > 0 and receiving_yards == 0:
            issues.append(ValidationIssue(
                field='receiving_yards',
                level=ValidationLevel.INFO,
                message='Player has receptions but no receiving yards'
            ))

        return issues

    def _validate_odds_logic(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate betting odds business logic"""
        issues = []

        # Check moneyline consistency
        home_ml = data.get('home_moneyline')
        away_ml = data.get('away_moneyline')

        if home_ml and away_ml:
            if home_ml > 0 and away_ml > 0:
                issues.append(ValidationIssue(
                    field='moneylines',
                    level=ValidationLevel.WARNING,
                    message='Both teams cannot be underdogs (positive moneylines)'
                ))

        # Check spread consistency with moneylines
        spread = data.get('spread')
        if spread and home_ml and away_ml:
            # Home team favored (negative spread) should have negative moneyline
            if spread < 0 and home_ml > 0:
                issues.append(ValidationIssue(
                    field='home_moneyline',
                    level=ValidationLevel.WARNING,
                    message='Home team is favored by spread but has underdog moneyline'
                ))

        return issues

    def _create_validation_report(self, issues: List[ValidationIssue], sanitized_data: Dict[str, Any]) -> ValidationReport:
        """Create validation report from issues and data"""
        has_critical = any(issue.level == ValidationLevel.CRITICAL for issue in issues)

        if has_critical:
            return ValidationReport(
                is_valid=False,
                result=ValidationResult.INVALID,
                issues=issues
            )
        elif issues:
            return ValidationReport(
                is_valid=True,
                result=ValidationResult.SANITIZED,
                issues=issues,
                sanitized_data=sanitized_data
            )
        else:
            return ValidationReport(
                is_valid=True,
                result=ValidationResult.VALID,
                issues=issues,
                sanitized_data=sanitized_data
            )

    def get_validation_summary(self, reports: List[ValidationReport]) -> Dict[str, Any]:
        """
        Generate summary statistics from multiple validation reports

        Args:
            reports: List of validation reports

        Returns:
            Summary statistics dictionary
        """
        total_reports = len(reports)
        valid_reports = sum(1 for r in reports if r.is_valid)
        critical_issues = sum(len(r.get_issues_by_level(ValidationLevel.CRITICAL)) for r in reports)
        warning_issues = sum(len(r.get_issues_by_level(ValidationLevel.WARNING)) for r in reports)

        return {
            'total_validations': total_reports,
            'valid_count': valid_reports,
            'invalid_count': total_reports - valid_reports,
            'success_rate': (valid_reports / total_reports * 100) if total_reports > 0 else 0,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'most_common_issues': self._get_most_common_issues(reports)
        }

    def _get_most_common_issues(self, reports: List[ValidationReport]) -> List[Dict[str, Any]]:
        """Get most common validation issues across reports"""
        issue_counts = {}

        for report in reports:
            for issue in report.issues:
                key = f"{issue.field}: {issue.message}"
                issue_counts[key] = issue_counts.get(key, 0) + 1

        # Sort by frequency and return top 5
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return [
            {'issue': issue, 'count': count}
            for issue, count in sorted_issues
        ]


# Global validator instance
data_validator = DataValidator()