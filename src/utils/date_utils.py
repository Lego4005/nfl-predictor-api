"""
Date/Time Utilities for NFL Prediction Platform
Handles timezone conversions and game scheduling logic
"""

from datetime import datetime, timezone, timedelta
import pytz
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Constants
ET_TIMEZONE = pytz.timezone('US/Eastern')
UTC_TIMEZONE = timezone.utc

class DateUtils:
    """Centralized date/time handling for the platform"""

    @staticmethod
    def get_current_et() -> datetime:
        """Get current time in Eastern timezone"""
        return datetime.now(UTC_TIMEZONE).astimezone(ET_TIMEZONE)

    @staticmethod
    def get_current_utc() -> datetime:
        """Get current time in UTC"""
        return datetime.now(UTC_TIMEZONE)

    @staticmethod
    def parse_api_time(time_str: str) -> Optional[datetime]:
        """
        Parse time string from API (usually UTC) to timezone-aware datetime
        Handles various formats: ISO with Z, ISO with timezone, etc.
        """
        if not time_str or time_str == 'N/A':
            return None

        try:
            # Handle Z suffix (UTC)
            if time_str.endswith('Z'):
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

            # Handle already formatted ISO
            parsed = datetime.fromisoformat(time_str)

            # If no timezone info, assume UTC
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC_TIMEZONE)

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse time string '{time_str}': {e}")
            return None

    @staticmethod
    def convert_to_et(utc_dt: datetime) -> datetime:
        """Convert UTC datetime to Eastern time"""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=UTC_TIMEZONE)
        return utc_dt.astimezone(ET_TIMEZONE)

    @staticmethod
    def is_game_today(game_time_utc: datetime, reference_time: Optional[datetime] = None) -> bool:
        """
        Check if a game is happening "today" in ET timezone
        """
        if reference_time is None:
            reference_time = DateUtils.get_current_et()

        # Convert game time to ET
        game_et = DateUtils.convert_to_et(game_time_utc)

        # Compare dates in ET
        return game_et.date() == reference_time.date()

    @staticmethod
    def is_game_tonight(game_time_utc: datetime, reference_time: Optional[datetime] = None) -> bool:
        """
        Check if a game is happening "tonight" - same day in ET and within next 12 hours
        """
        if reference_time is None:
            reference_time = DateUtils.get_current_utc()

        # Must be today in ET
        if not DateUtils.is_game_today(game_time_utc, DateUtils.convert_to_et(reference_time)):
            return False

        # Must be within next 12 hours
        hours_until = (game_time_utc - reference_time).total_seconds() / 3600
        return -2 <= hours_until <= 12  # Allow 2 hours past start (for live games)

    @staticmethod
    def get_tonights_games(games: List[Dict]) -> List[Dict]:
        """
        Filter games list to only include tonight's games
        """
        current_time = DateUtils.get_current_utc()
        tonights_games = []

        for game in games:
            game_time_str = game.get('commence_time')
            if not game_time_str:
                continue

            game_time = DateUtils.parse_api_time(game_time_str)
            if not game_time:
                continue

            if DateUtils.is_game_tonight(game_time, current_time):
                # Add ET time to game data
                game_et = DateUtils.convert_to_et(game_time)
                game['game_time_et'] = game_et.strftime('%I:%M %p ET')
                game['game_date_et'] = game_et.strftime('%Y-%m-%d')

                # Calculate time until game
                hours_until = (game_time - current_time).total_seconds() / 3600
                game['hours_until'] = hours_until
                game['status'] = 'live' if -2 <= hours_until <= 0 else 'upcoming'

                tonights_games.append(game)

        # Sort by game time
        tonights_games.sort(key=lambda g: DateUtils.parse_api_time(g['commence_time']))

        return tonights_games

    @staticmethod
    def format_game_time(game_time_utc: datetime, include_date: bool = False) -> str:
        """
        Format game time for display in ET
        """
        game_et = DateUtils.convert_to_et(game_time_utc)

        if include_date:
            return game_et.strftime('%a %m/%d at %I:%M %p ET')
        else:
            return game_et.strftime('%I:%M %p ET')

    @staticmethod
    def get_game_status(game_time_utc: datetime) -> Dict[str, any]:
        """
        Get comprehensive status info for a game
        """
        current_time = DateUtils.get_current_utc()
        game_et = DateUtils.convert_to_et(game_time_utc)

        # Calculate time differences
        hours_until = (game_time_utc - current_time).total_seconds() / 3600

        # Determine status
        if hours_until < -3:
            status = 'completed'
        elif hours_until < 0:
            status = 'live'
        elif hours_until < 1:
            status = 'starting_soon'
        elif hours_until < 24:
            status = 'today'
        else:
            status = 'upcoming'

        return {
            'status': status,
            'hours_until': hours_until,
            'game_time_et': DateUtils.format_game_time(game_time_utc),
            'game_time_display': DateUtils.format_game_time(game_time_utc, include_date=True),
            'is_today': DateUtils.is_game_today(game_time_utc),
            'is_tonight': DateUtils.is_game_tonight(game_time_utc)
        }


def test_date_utils():
    """Test the date utilities with current games"""
    print("=== TESTING DATE UTILITIES ===")
    print()

    # Test current time functions
    current_et = DateUtils.get_current_et()
    current_utc = DateUtils.get_current_utc()

    print(f"Current ET:  {current_et}")
    print(f"Current UTC: {current_utc}")
    print()

    # Test with sample game times
    test_times = [
        "2025-09-15T23:06:00Z",  # TB @ HOU
        "2025-09-16T02:00:00Z",  # LAC @ LV
        "2025-09-19T00:15:00Z"   # Future game
    ]

    print("GAME TIME TESTING:")
    print("-" * 50)

    for i, time_str in enumerate(test_times, 1):
        print(f"Game {i}: {time_str}")

        # Parse time
        parsed = DateUtils.parse_api_time(time_str)
        if parsed:
            print(f"  Parsed UTC: {parsed}")
            print(f"  ET Format:  {DateUtils.format_game_time(parsed, True)}")

            status = DateUtils.get_game_status(parsed)
            print(f"  Status:     {status['status']}")
            print(f"  Is today:   {status['is_today']}")
            print(f"  Is tonight: {status['is_tonight']}")
            print(f"  Hours until: {status['hours_until']:.1f}")

        print()


if __name__ == "__main__":
    test_date_utils()