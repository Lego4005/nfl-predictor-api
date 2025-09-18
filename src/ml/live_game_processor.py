#!/usr/bin/env python3
"""
Live Game Data Processor for AI Game Narrator
Integrates ESPN API data and processes real-time game events
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pandas as pd
from collections import defaultdict, deque

from .ai_game_narrator import AIGameNarrator, GameState, NarratorInsight

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LiveGameEvent:
    """Live game event from ESPN API"""
    event_id: str
    game_id: str
    timestamp: datetime
    quarter: int
    time_remaining: str
    play_type: str
    description: str
    team: str
    yards_gained: int
    down: int
    yards_to_go: int
    yard_line: int
    score_home: int
    score_away: int
    drive_info: Dict[str, Any]
    situational_data: Dict[str, Any]


@dataclass
class GameStateUpdate:
    """Game state update notification"""
    game_id: str
    timestamp: datetime
    previous_state: GameState
    current_state: GameState
    triggering_event: LiveGameEvent
    narrator_insight: NarratorInsight
    significance_score: float  # 0-1, how significant this update is


class ESPNAPIClient:
    """ESPN API client for real-time game data"""

    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.session = None
        self.rate_limit_delay = 1.0  # Seconds between requests

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'NFL-Predictor-API/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_live_games(self) -> List[Dict[str, Any]]:
        """Get list of live/current games"""

        try:
            url = f"{self.base_url}/scoreboard"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('events', [])

                    live_games = []
                    for event in events:
                        status = event.get('status', {})
                        state = status.get('type', {}).get('state', '')

                        # Only include live or recently completed games
                        if state in ['in', 'post'] and status.get('period', 0) > 0:
                            live_games.append({
                                'game_id': event.get('id'),
                                'status': state,
                                'period': status.get('period', 1),
                                'clock': status.get('displayClock', '15:00'),
                                'home_team': event.get('competitions', [{}])[0].get('competitors', [{}])[0].get('team', {}).get('abbreviation', 'HOME'),
                                'away_team': event.get('competitions', [{}])[0].get('competitors', [{}])[1].get('team', {}).get('abbreviation', 'AWAY'),
                                'home_score': int(event.get('competitions', [{}])[0].get('competitors', [{}])[0].get('score', 0)),
                                'away_score': int(event.get('competitions', [{}])[0].get('competitors', [{}])[1].get('score', 0)),
                                'last_update': datetime.now()
                            })

                    return live_games
                else:
                    logger.error(f"ESPN API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching live games: {e}")
            return []

    async def get_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed game information"""

        try:
            url = f"{self.base_url}/summary"
            params = {'event': game_id}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"ESPN API error for game {game_id}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching game details for {game_id}: {e}")
            return None

    async def get_game_plays(self, game_id: str) -> List[Dict[str, Any]]:
        """Get play-by-play data for a game"""

        try:
            url = f"{self.base_url}/playbyplay"
            params = {'event': game_id}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    drives = data.get('drives', {}).get('previous', [])

                    all_plays = []
                    for drive in drives:
                        plays = drive.get('plays', [])
                        for play in plays:
                            all_plays.append(play)

                    return all_plays
                else:
                    logger.error(f"ESPN API error for plays {game_id}: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching plays for {game_id}: {e}")
            return []

    async def get_team_stats(self, game_id: str) -> Dict[str, Any]:
        """Get team statistics for the game"""

        try:
            url = f"{self.base_url}/summary"
            params = {'event': game_id}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract team statistics
                    stats = {}
                    boxscore = data.get('boxscore', {})
                    teams = boxscore.get('teams', [])

                    for team in teams:
                        team_id = team.get('team', {}).get('id')
                        team_stats = {}

                        for stat_category in team.get('statistics', []):
                            category_name = stat_category.get('name', '')
                            category_stats = {}

                            for stat in stat_category.get('stats', []):
                                stat_name = stat.get('name', '')
                                stat_value = stat.get('displayValue', '0')
                                category_stats[stat_name] = stat_value

                            team_stats[category_name] = category_stats

                        stats[team_id] = team_stats

                    return stats
                else:
                    logger.error(f"ESPN API error for stats {game_id}: {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error fetching team stats for {game_id}: {e}")
            return {}


class GameStateTracker:
    """Tracks game state changes and significant events"""

    def __init__(self):
        self.game_states: Dict[str, GameState] = {}
        self.game_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.significance_thresholds = {
            'score_change': 0.8,
            'turnover': 0.9,
            'fourth_down': 0.7,
            'red_zone_entry': 0.6,
            'two_minute_warning': 0.8,
            'quarterback_change': 0.7
        }

    def update_game_state(self, game_id: str, espn_data: Dict[str, Any], plays: List[Dict[str, Any]]) -> Optional[GameStateUpdate]:
        """Update game state from ESPN data and return significant changes"""

        try:
            # Extract current game state from ESPN data
            current_state = self._extract_game_state(game_id, espn_data, plays)

            if not current_state:
                return None

            # Get previous state
            previous_state = self.game_states.get(game_id)

            # Store current state
            self.game_states[game_id] = current_state
            self.game_histories[game_id].append(current_state)

            # If no previous state, this is initial load
            if not previous_state:
                logger.info(f"Initial game state loaded for {game_id}")
                return None

            # Analyze significance of change
            significance_score = self._calculate_significance(previous_state, current_state, plays)

            # Create update if significant enough
            if significance_score >= 0.5:
                # Find the triggering event
                triggering_event = self._identify_triggering_event(previous_state, current_state, plays)

                return GameStateUpdate(
                    game_id=game_id,
                    timestamp=datetime.now(),
                    previous_state=previous_state,
                    current_state=current_state,
                    triggering_event=triggering_event,
                    narrator_insight=None,  # Will be populated later
                    significance_score=significance_score
                )

            return None

        except Exception as e:
            logger.error(f"Error updating game state for {game_id}: {e}")
            return None

    def _extract_game_state(self, game_id: str, espn_data: Dict[str, Any], plays: List[Dict[str, Any]]) -> Optional[GameState]:
        """Extract GameState from ESPN API data"""

        try:
            header = espn_data.get('header', {})
            competitions = header.get('competitions', [{}])[0]
            status = competitions.get('status', {})

            # Basic game info
            quarter = status.get('period', 1)
            time_remaining = status.get('displayClock', '15:00')

            # Score
            competitors = competitions.get('competitors', [])
            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})

            home_score = int(home_team.get('score', 0))
            away_score = int(away_team.get('score', 0))

            # Current drive/possession info
            drives = espn_data.get('drives', {})
            current_drive = drives.get('current', {})

            # Get last play for current situation
            last_play = {}
            down = 1
            yards_to_go = 10
            yard_line = 50
            possession = 'home'
            drive_info = {}

            if plays:
                last_play_data = plays[-1]

                # Extract play details
                last_play = {
                    'type': last_play_data.get('type', {}).get('text', 'unknown'),
                    'description': last_play_data.get('text', ''),
                    'yards': last_play_data.get('statYardage', 0),
                    'result': last_play_data.get('end', {}).get('shortDownDistanceText', '')
                }

                # Extract current situation
                end_situation = last_play_data.get('end', {})
                down = end_situation.get('down', 1)
                distance = end_situation.get('distance', 10)
                yards_to_go = distance if distance and distance > 0 else 10

                # Yard line (convert to standardized format)
                yard_line_data = end_situation.get('yardLine', 50)
                yard_line = yard_line_data if isinstance(yard_line_data, int) else 50

                # Possession
                possession_team = last_play_data.get('start', {}).get('team', {}).get('id')
                home_team_id = home_team.get('team', {}).get('id')
                possession = 'home' if possession_team == home_team_id else 'away'

            # Drive info
            if current_drive:
                drive_info = {
                    'plays': current_drive.get('plays', 0),
                    'yards': current_drive.get('yards', 0),
                    'time_consumed': current_drive.get('timeElapsed', {}).get('displayValue', '0:00')
                }

            return GameState(
                quarter=quarter,
                time_remaining=time_remaining,
                down=down,
                yards_to_go=yards_to_go,
                yard_line=yard_line,
                home_score=home_score,
                away_score=away_score,
                possession=possession,
                last_play=last_play,
                drive_info=drive_info,
                game_id=game_id,
                week=1,  # Would need to be extracted from schedule
                season=2024
            )

        except Exception as e:
            logger.error(f"Error extracting game state: {e}")
            return None

    def _calculate_significance(self, previous: GameState, current: GameState, plays: List[Dict[str, Any]]) -> float:
        """Calculate how significant the state change is"""

        significance = 0.0

        # Score changes
        if current.home_score != previous.home_score or current.away_score != previous.away_score:
            significance += self.significance_thresholds['score_change']

        # Quarter changes
        if current.quarter != previous.quarter:
            significance += 0.6

        # Down changes (especially to 4th down)
        if current.down == 4 and previous.down != 4:
            significance += self.significance_thresholds['fourth_down']

        # Red zone entry
        if current.yard_line <= 20 and previous.yard_line > 20:
            significance += self.significance_thresholds['red_zone_entry']

        # Two minute warning
        if current.quarter >= 2 and self._time_to_seconds(current.time_remaining) <= 120:
            if previous.quarter < 2 or self._time_to_seconds(previous.time_remaining) > 120:
                significance += self.significance_thresholds['two_minute_warning']

        # Big plays (analyze from play data)
        if plays:
            last_play = plays[-1]
            yards_gained = last_play.get('statYardage', 0)
            play_type = last_play.get('type', {}).get('text', '').lower()

            if yards_gained >= 20:  # Big play
                significance += 0.6
            elif 'turnover' in play_type or 'interception' in play_type or 'fumble' in play_type:
                significance += self.significance_thresholds['turnover']
            elif 'touchdown' in play_type:
                significance += 1.0
            elif 'sack' in play_type:
                significance += 0.4

        return min(1.0, significance)

    def _identify_triggering_event(self, previous: GameState, current: GameState, plays: List[Dict[str, Any]]) -> Optional[LiveGameEvent]:
        """Identify the event that triggered the state change"""

        if not plays:
            return None

        try:
            last_play = plays[-1]

            return LiveGameEvent(
                event_id=last_play.get('id', 'unknown'),
                game_id=current.game_id,
                timestamp=datetime.now(),
                quarter=current.quarter,
                time_remaining=current.time_remaining,
                play_type=last_play.get('type', {}).get('text', 'unknown'),
                description=last_play.get('text', ''),
                team=last_play.get('start', {}).get('team', {}).get('abbreviation', 'UNK'),
                yards_gained=last_play.get('statYardage', 0),
                down=current.down,
                yards_to_go=current.yards_to_go,
                yard_line=current.yard_line,
                score_home=current.home_score,
                score_away=current.away_score,
                drive_info=current.drive_info,
                situational_data={}
            )

        except Exception as e:
            logger.error(f"Error identifying triggering event: {e}")
            return None

    def _time_to_seconds(self, time_str: str) -> int:
        """Convert time string to seconds"""
        try:
            parts = time_str.split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0


class LiveGameProcessor:
    """Main processor for live game data and AI narrator integration"""

    def __init__(self, update_callback: Optional[Callable] = None):
        self.narrator = AIGameNarrator()
        self.state_tracker = GameStateTracker()
        self.espn_client = ESPNAPIClient()
        self.update_callback = update_callback
        self.active_games: Dict[str, Dict[str, Any]] = {}
        self.polling_interval = 5.0  # Seconds between updates
        self.is_running = False

    async def start_live_processing(self):
        """Start processing live games"""

        logger.info("Starting live game processing...")
        self.is_running = True

        async with self.espn_client:
            while self.is_running:
                try:
                    await self._process_live_games()
                    await asyncio.sleep(self.polling_interval)
                except Exception as e:
                    logger.error(f"Error in live processing: {e}")
                    await asyncio.sleep(self.polling_interval)

    async def stop_live_processing(self):
        """Stop processing live games"""

        logger.info("Stopping live game processing...")
        self.is_running = False

    async def _process_live_games(self):
        """Process all live games"""

        # Get list of live games
        live_games = await self.espn_client.get_live_games()

        for game_info in live_games:
            game_id = game_info['game_id']

            try:
                # Get detailed game data
                game_details = await self.espn_client.get_game_details(game_id)
                if not game_details:
                    continue

                # Get play-by-play data
                plays = await self.espn_client.get_game_plays(game_id)

                # Update game state
                state_update = self.state_tracker.update_game_state(game_id, game_details, plays)

                if state_update:
                    # Generate narrator insight
                    insight = await self._generate_insight_for_update(state_update, game_details)
                    state_update.narrator_insight = insight

                    # Store active game info
                    self.active_games[game_id] = {
                        'last_update': datetime.now(),
                        'current_state': state_update.current_state,
                        'latest_insight': insight,
                        'game_info': game_info
                    }

                    # Notify callback if provided
                    if self.update_callback:
                        await self.update_callback(state_update)

                    logger.info(f"Updated game {game_id}: {state_update.significance_score:.2f} significance")

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing game {game_id}: {e}")

    async def _generate_insight_for_update(self, state_update: GameStateUpdate, game_details: Dict[str, Any]) -> NarratorInsight:
        """Generate narrator insight for a game state update"""

        try:
            # Get team stats
            team_stats = await self.espn_client.get_team_stats(state_update.game_id)

            # Build context for narrator
            context = {
                'team_stats': team_stats,
                'recent_scoring': self._extract_recent_scoring(game_details),
                'weather_data': self._extract_weather_data(game_details),
                'momentum_history': self._get_momentum_history(state_update.game_id)
            }

            # Generate comprehensive insight
            insight = self.narrator.generate_comprehensive_insight(
                state_update.current_state,
                context
            )

            return insight

        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            # Return minimal insight on error
            return self._create_minimal_insight(state_update.current_state)

    def _extract_recent_scoring(self, game_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract recent scoring events"""

        # Mock implementation - would parse actual scoring plays
        return [
            {'team': 'home', 'points': 7, 'time': '8:45', 'type': 'touchdown'},
            {'team': 'away', 'points': 3, 'time': '3:22', 'type': 'field_goal'}
        ]

    def _extract_weather_data(self, game_details: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weather data if available"""

        # Mock implementation - ESPN API sometimes has weather data
        return {
            'temperature': 65,
            'wind_speed': 8,
            'precipitation': 0.0,
            'dome_game': False,
            'visibility': 10
        }

    def _get_momentum_history(self, game_id: str) -> List[float]:
        """Get momentum history for the game"""

        # Return recent momentum scores
        history = self.state_tracker.game_histories.get(game_id, deque())
        return [0.5] * min(5, len(history))  # Mock momentum values

    def _create_minimal_insight(self, game_state: GameState) -> NarratorInsight:
        """Create minimal insight when full generation fails"""

        from .ai_game_narrator import (
            ScoringProbability, GameOutcomeLikelihood, ContextualInsight,
            MomentumAnalysis, PredictionConfidence, MomentumShift
        )

        confidence = PredictionConfidence(
            probability=0.5,
            confidence_interval=(0.3, 0.7),
            confidence_level="medium",
            factors=["limited_data"]
        )

        return NarratorInsight(
            timestamp=datetime.now(),
            game_state=game_state,
            scoring_probability=ScoringProbability(
                team=game_state.possession,
                score_type="unknown",
                probability=0.5,
                expected_points=3.0,
                confidence=confidence
            ),
            game_outcome=GameOutcomeLikelihood(
                home_win_prob=0.5,
                away_win_prob=0.5,
                tie_prob=0.0,
                expected_home_score=float(game_state.home_score + 10),
                expected_away_score=float(game_state.away_score + 10),
                confidence=confidence
            ),
            contextual_insights=[
                ContextualInsight(
                    insight_type="basic",
                    message="Game in progress",
                    historical_comparison=None,
                    statistical_backing={},
                    relevance_score=0.5
                )
            ],
            momentum_analysis=MomentumAnalysis(
                current_momentum=MomentumShift.NEUTRAL,
                shift_magnitude=0.0,
                shift_reason="Insufficient data",
                key_factors=[],
                trend_direction="stable"
            ),
            decision_recommendation=None,
            weather_impact=None,
            key_matchup_analysis={}
        )

    async def get_active_games(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active games"""
        return self.active_games.copy()

    async def get_game_insight(self, game_id: str) -> Optional[NarratorInsight]:
        """Get latest insight for a specific game"""

        game_info = self.active_games.get(game_id)
        if game_info:
            return game_info.get('latest_insight')
        return None

    async def force_update_game(self, game_id: str) -> Optional[GameStateUpdate]:
        """Force an update for a specific game"""

        try:
            async with self.espn_client:
                game_details = await self.espn_client.get_game_details(game_id)
                plays = await self.espn_client.get_game_plays(game_id)

                if game_details:
                    state_update = self.state_tracker.update_game_state(game_id, game_details, plays)

                    if state_update:
                        insight = await self._generate_insight_for_update(state_update, game_details)
                        state_update.narrator_insight = insight

                        return state_update

        except Exception as e:
            logger.error(f"Error forcing update for game {game_id}: {e}")

        return None


# Example callback function for handling updates
async def example_update_callback(state_update: GameStateUpdate):
    """Example callback for handling game state updates"""

    print(f"\n=== GAME UPDATE: {state_update.game_id} ===")
    print(f"Significance: {state_update.significance_score:.2f}")
    print(f"Quarter {state_update.current_state.quarter} - {state_update.current_state.time_remaining}")
    print(f"Score: {state_update.current_state.home_score} - {state_update.current_state.away_score}")

    if state_update.triggering_event:
        print(f"Event: {state_update.triggering_event.description}")

    if state_update.narrator_insight:
        summary = AIGameNarrator().get_insight_summary(state_update.narrator_insight)
        print(f"Next Score Probability: {summary['predictions']['next_score']}")
        print(f"Win Probability: Home {summary['predictions']['game_outcome']['home_win_probability']:.1%}")


# Example usage
async def main():
    """Example usage of LiveGameProcessor"""

    processor = LiveGameProcessor(update_callback=example_update_callback)

    try:
        # Start processing (this would run continuously in production)
        await processor.start_live_processing()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await processor.stop_live_processing()


if __name__ == "__main__":
    logger.info("Live Game Processor for AI Game Narrator")
    asyncio.run(main())