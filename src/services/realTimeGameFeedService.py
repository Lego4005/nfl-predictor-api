"""
Real-Time Game Feed Service
Fetches live play-by-play data and game state changes from SportsData.io
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import asyncio
import websocket
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RealTimeGameFeedService:
    """Fetches real-time game feeds and play-by-play data"""

    def __init__(self):
        # API Keys from environment variables
        self.sportsdata_io_key = os.getenv('VITE_SPORTSDATA_IO_KEY', '')
        self.sportsdata_base = "https://api.sportsdata.io/v3/nfl"

        # Cache and state tracking
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds cache for live data
        self.game_states = {}
        self.live_games = {}
        self.play_history = {}
        self.drive_data = {}
        self.scoring_plays = {}

        # Real-time tracking
        self.is_monitoring = False
        self.game_subscribers = {}

        logger.info("⚡ Real-Time Game Feed Service initialized")

    def get_live_game_feed(self, game_id: str = None, week: int = None, season: int = 2024) -> Dict:
        """Get live game feed with play-by-play data"""
        cache_key = f"live_feed_{game_id or 'all'}_{week}_{season}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            if game_id:
                # Get specific game
                feed_data = self._get_single_game_feed(game_id, season)
            else:
                # Get all live games for the week
                feed_data = self._get_week_live_feeds(week or self._get_current_week(), season)

            # Cache the results
            self._cache_data(cache_key, feed_data)

            logger.info(f"✅ Fetched live game feed data")
            return feed_data

        except Exception as e:
            logger.error(f"❌ Error fetching live game feed: {e}")
            return {}

    def _get_single_game_feed(self, game_id: str, season: int) -> Dict:
        """Get live feed for a single game"""
        try:
            # Get live box score
            box_score_url = f"{self.sportsdata_base}/stats/json/BoxScoreLive/{game_id}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(box_score_url, headers=headers)
            response.raise_for_status()
            box_score = response.json()

            # Get play-by-play data
            pbp_data = self._get_play_by_play_data(game_id)

            # Process game feed
            game_feed = self._process_game_feed(box_score, pbp_data, game_id)

            return game_feed

        except Exception as e:
            logger.error(f"Error fetching single game feed: {e}")
            return {}

    def _get_week_live_feeds(self, week: int, season: int) -> Dict:
        """Get live feeds for all games in a week"""
        try:
            # Get live scores for the week
            url = f"{self.sportsdata_base}/scores/json/ScoresLive/{season}/{week}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            live_scores = response.json()

            week_feeds = {
                'week': week,
                'season': season,
                'games': [],
                'summary': {
                    'total_games': len(live_scores),
                    'live_games': 0,
                    'completed_games': 0,
                    'upcoming_games': 0
                },
                'last_updated': datetime.now().isoformat()
            }

            for game in live_scores:
                game_feed = self._process_game_summary(game)
                week_feeds['games'].append(game_feed)

                # Update summary
                status = game_feed.get('game_status', 'Scheduled')
                if status in ['InProgress', 'Halftime']:
                    week_feeds['summary']['live_games'] += 1
                elif status == 'Final':
                    week_feeds['summary']['completed_games'] += 1
                else:
                    week_feeds['summary']['upcoming_games'] += 1

            return week_feeds

        except Exception as e:
            logger.error(f"Error fetching week live feeds: {e}")
            return {}

    def _get_play_by_play_data(self, game_id: str) -> Dict:
        """Get detailed play-by-play data for a game"""
        try:
            url = f"{self.sportsdata_base}/pbp/json/PlayByPlayLive/{game_id}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.warning(f"Could not fetch play-by-play data: {e}")
            return {}

    def _process_game_feed(self, box_score: Dict, pbp_data: Dict, game_id: str) -> Dict:
        """Process raw game data into comprehensive feed"""
        game = box_score.get('Game', {})

        game_feed = {
            'game_id': game_id,
            'home_team': game.get('HomeTeam'),
            'away_team': game.get('AwayTeam'),
            'home_score': game.get('HomeScore', 0),
            'away_score': game.get('AwayScore', 0),
            'quarter': game.get('Quarter'),
            'time_remaining': game.get('TimeRemaining'),
            'down': game.get('Down'),
            'distance': game.get('Distance'),
            'yard_line': game.get('YardLine'),
            'possession': game.get('Possession'),
            'game_status': game.get('Status'),
            'stadium': game.get('Stadium'),
            'weather': self._extract_weather_data(game),

            # Game state
            'game_state': self._analyze_game_state(game),
            'momentum': self._calculate_momentum(game_id, pbp_data),
            'situational_context': self._get_situational_context(game),

            # Drive information
            'current_drive': self._extract_current_drive(pbp_data),
            'drive_summary': self._summarize_drives(pbp_data),

            # Scoring information
            'scoring_plays': self._extract_scoring_plays(pbp_data),
            'scoring_summary': self._generate_scoring_summary(pbp_data),

            # Recent plays
            'recent_plays': self._extract_recent_plays(pbp_data, limit=10),
            'key_plays': self._identify_key_plays(pbp_data),

            # Advanced metrics
            'field_position_battle': self._analyze_field_position(pbp_data),
            'time_of_possession': self._calculate_time_of_possession(pbp_data),
            'efficiency_metrics': self._calculate_live_efficiency(pbp_data),

            # Prediction context
            'win_probability': self._calculate_live_win_probability(game),
            'expected_final_score': self._predict_final_score(game, pbp_data),
            'betting_implications': self._analyze_betting_implications(game),

            'last_updated': datetime.now().isoformat()
        }

        # Update game state tracking
        self._update_game_state(game_id, game_feed)

        return game_feed

    def _process_game_summary(self, game: Dict) -> Dict:
        """Process game summary for week view"""
        return {
            'game_id': game.get('GameID'),
            'home_team': game.get('HomeTeam'),
            'away_team': game.get('AwayTeam'),
            'home_score': game.get('HomeScore', 0),
            'away_score': game.get('AwayScore', 0),
            'quarter': game.get('Quarter'),
            'time_remaining': game.get('TimeRemaining'),
            'game_status': game.get('Status'),
            'spread_line': game.get('PointSpread'),
            'total_line': game.get('OverUnder'),
            'current_total': game.get('HomeScore', 0) + game.get('AwayScore', 0),
            'last_play': self._get_last_play_summary(game),
            'next_critical_moment': self._identify_next_critical_moment(game)
        }

    def _extract_weather_data(self, game: Dict) -> Dict:
        """Extract weather information"""
        return {
            'temperature': game.get('Temperature'),
            'humidity': game.get('Humidity'),
            'wind_speed': game.get('WindSpeed'),
            'conditions': game.get('WeatherConditions', 'Unknown'),
            'is_dome': game.get('IsDome', False)
        }

    def _analyze_game_state(self, game: Dict) -> Dict:
        """Analyze current game state"""
        quarter = game.get('Quarter', 1)
        time_remaining = game.get('TimeRemaining', '15:00')
        home_score = game.get('HomeScore', 0)
        away_score = game.get('AwayScore', 0)

        score_diff = abs(home_score - away_score)
        game_time_elapsed = self._calculate_elapsed_time(quarter, time_remaining)

        return {
            'game_phase': self._determine_game_phase(quarter, time_remaining, score_diff),
            'urgency_level': self._calculate_urgency(quarter, time_remaining, score_diff),
            'comeback_potential': self._assess_comeback_potential(quarter, time_remaining, score_diff),
            'game_script': self._determine_game_script(home_score, away_score, game_time_elapsed),
            'critical_juncture': self._is_critical_juncture(quarter, time_remaining, score_diff)
        }

    def _calculate_momentum(self, game_id: str, pbp_data: Dict) -> Dict:
        """Calculate momentum based on recent plays"""
        recent_plays = self._extract_recent_plays(pbp_data, limit=5)

        momentum_factors = {
            'score_momentum': 0,
            'field_position_momentum': 0,
            'turnover_momentum': 0,
            'big_play_momentum': 0
        }

        for play in recent_plays:
            # Score momentum
            if play.get('is_touchdown'):
                momentum_factors['score_momentum'] += 3
            elif play.get('is_field_goal'):
                momentum_factors['score_momentum'] += 1

            # Field position momentum
            yards_gained = play.get('yards_gained', 0)
            if yards_gained >= 20:
                momentum_factors['big_play_momentum'] += 2
            elif yards_gained >= 10:
                momentum_factors['field_position_momentum'] += 1

            # Turnover momentum
            if play.get('is_turnover'):
                momentum_factors['turnover_momentum'] += 3

        total_momentum = sum(momentum_factors.values())

        return {
            'overall_momentum': total_momentum,
            'momentum_direction': 'positive' if total_momentum > 3 else 'negative' if total_momentum < -3 else 'neutral',
            'factors': momentum_factors,
            'momentum_team': self._determine_momentum_team(recent_plays)
        }

    def _get_situational_context(self, game: Dict) -> Dict:
        """Get situational context for current game state"""
        down = game.get('Down')
        distance = game.get('Distance')
        yard_line = game.get('YardLine', 50)
        quarter = game.get('Quarter', 1)

        return {
            'down_and_distance': f"{down} & {distance}" if down and distance else "Unknown",
            'field_zone': self._determine_field_zone(yard_line),
            'situation_type': self._categorize_situation(down, distance, yard_line, quarter),
            'expected_play_type': self._predict_play_type(down, distance, yard_line),
            'success_probability': self._calculate_situation_success_prob(down, distance, yard_line)
        }

    def _extract_current_drive(self, pbp_data: Dict) -> Dict:
        """Extract current drive information"""
        if not pbp_data or 'Plays' not in pbp_data:
            return {}

        plays = pbp_data.get('Plays', [])
        if not plays:
            return {}

        # Get current drive plays
        current_drive_plays = []
        for play in reversed(plays):
            current_drive_plays.append(play)
            if play.get('IsScoringPlay') or play.get('PlayType') in ['Kickoff', 'Punt']:
                break

        current_drive_plays.reverse()

        return {
            'drive_number': len(current_drive_plays),
            'plays_in_drive': len(current_drive_plays),
            'yards_gained': sum(play.get('YardsGained', 0) for play in current_drive_plays),
            'time_elapsed': self._calculate_drive_time(current_drive_plays),
            'starting_field_position': current_drive_plays[0].get('YardLine') if current_drive_plays else None,
            'drive_efficiency': self._calculate_drive_efficiency(current_drive_plays),
            'red_zone_attempt': any(play.get('YardLine', 100) <= 20 for play in current_drive_plays)
        }

    def _summarize_drives(self, pbp_data: Dict) -> Dict:
        """Summarize all drives in the game"""
        if not pbp_data or 'Plays' not in pbp_data:
            return {}

        plays = pbp_data.get('Plays', [])
        drives = self._segment_into_drives(plays)

        return {
            'total_drives': len(drives),
            'home_drives': len([d for d in drives if d.get('possession_team') == 'home']),
            'away_drives': len([d for d in drives if d.get('possession_team') == 'away']),
            'scoring_drives': len([d for d in drives if d.get('resulted_in_score')]),
            'three_and_outs': len([d for d in drives if d.get('is_three_and_out')]),
            'average_drive_time': self._calculate_average_drive_time(drives),
            'average_yards_per_drive': self._calculate_average_yards_per_drive(drives)
        }

    def _extract_scoring_plays(self, pbp_data: Dict) -> List[Dict]:
        """Extract all scoring plays from the game"""
        if not pbp_data or 'Plays' not in pbp_data:
            return []

        scoring_plays = []
        for play in pbp_data.get('Plays', []):
            if play.get('IsScoringPlay'):
                scoring_plays.append({
                    'quarter': play.get('Quarter'),
                    'time': play.get('TimeRemaining'),
                    'team': play.get('Team'),
                    'play_type': play.get('PlayType'),
                    'description': play.get('Description'),
                    'yards': play.get('YardsGained'),
                    'points': play.get('PointsScored', 0),
                    'home_score_after': play.get('HomeScoreAfterPlay'),
                    'away_score_after': play.get('AwayScoreAfterPlay')
                })

        return scoring_plays

    def _generate_scoring_summary(self, pbp_data: Dict) -> Dict:
        """Generate scoring summary"""
        scoring_plays = self._extract_scoring_plays(pbp_data)

        return {
            'total_touchdowns': len([p for p in scoring_plays if 'Touchdown' in p.get('play_type', '')]),
            'total_field_goals': len([p for p in scoring_plays if 'Field Goal' in p.get('play_type', '')]),
            'total_safeties': len([p for p in scoring_plays if 'Safety' in p.get('play_type', '')]),
            'quarters_scored': list(set(p.get('quarter') for p in scoring_plays)),
            'largest_lead': self._calculate_largest_lead(scoring_plays),
            'lead_changes': self._count_lead_changes(scoring_plays)
        }

    def _extract_recent_plays(self, pbp_data: Dict, limit: int = 10) -> List[Dict]:
        """Extract recent plays with enhanced details"""
        if not pbp_data or 'Plays' not in pbp_data:
            return []

        plays = pbp_data.get('Plays', [])
        recent = plays[-limit:] if len(plays) > limit else plays

        enhanced_plays = []
        for play in recent:
            enhanced_play = {
                'quarter': play.get('Quarter'),
                'time_remaining': play.get('TimeRemaining'),
                'down': play.get('Down'),
                'distance': play.get('Distance'),
                'yard_line': play.get('YardLine'),
                'play_type': play.get('PlayType'),
                'description': play.get('Description'),
                'yards_gained': play.get('YardsGained', 0),
                'team': play.get('Team'),
                'is_touchdown': play.get('IsScoringPlay') and 'Touchdown' in play.get('PlayType', ''),
                'is_field_goal': play.get('IsScoringPlay') and 'Field Goal' in play.get('PlayType', ''),
                'is_turnover': play.get('IsTurnover', False),
                'is_penalty': play.get('IsPenalty', False),
                'epa': self._calculate_play_epa(play),
                'win_prob_change': self._calculate_win_prob_change(play)
            }
            enhanced_plays.append(enhanced_play)

        return enhanced_plays

    def _identify_key_plays(self, pbp_data: Dict) -> List[Dict]:
        """Identify key plays in the game"""
        if not pbp_data or 'Plays' not in pbp_data:
            return []

        key_plays = []
        plays = pbp_data.get('Plays', [])

        for play in plays:
            # Scoring plays
            if play.get('IsScoringPlay'):
                key_plays.append({
                    'type': 'scoring_play',
                    'description': play.get('Description'),
                    'impact': 'high',
                    'quarter': play.get('Quarter'),
                    'time': play.get('TimeRemaining')
                })

            # Turnovers
            elif play.get('IsTurnover'):
                key_plays.append({
                    'type': 'turnover',
                    'description': play.get('Description'),
                    'impact': 'high',
                    'quarter': play.get('Quarter'),
                    'time': play.get('TimeRemaining')
                })

            # Big plays (20+ yards)
            elif play.get('YardsGained', 0) >= 20:
                key_plays.append({
                    'type': 'big_play',
                    'description': play.get('Description'),
                    'impact': 'medium',
                    'yards': play.get('YardsGained'),
                    'quarter': play.get('Quarter'),
                    'time': play.get('TimeRemaining')
                })

            # Fourth down conversions
            elif play.get('Down') == 4 and play.get('YardsGained', 0) >= play.get('Distance', 0):
                key_plays.append({
                    'type': 'fourth_down_conversion',
                    'description': play.get('Description'),
                    'impact': 'medium',
                    'quarter': play.get('Quarter'),
                    'time': play.get('TimeRemaining')
                })

        # Sort by impact and recency
        key_plays.sort(key=lambda x: (x.get('quarter', 0), x.get('time', '00:00')), reverse=True)
        return key_plays[:15]  # Return top 15 key plays

    def _analyze_field_position(self, pbp_data: Dict) -> Dict:
        """Analyze field position battle"""
        if not pbp_data or 'Plays' not in pbp_data:
            return {}

        plays = pbp_data.get('Plays', [])
        home_positions = []
        away_positions = []

        for play in plays:
            yard_line = play.get('YardLine')
            team = play.get('Team')

            if yard_line is not None:
                if 'home' in team.lower():
                    home_positions.append(yard_line)
                else:
                    away_positions.append(yard_line)

        return {
            'home_avg_field_position': sum(home_positions) / len(home_positions) if home_positions else 50,
            'away_avg_field_position': sum(away_positions) / len(away_positions) if away_positions else 50,
            'field_position_advantage': 'home' if sum(home_positions) > sum(away_positions) else 'away',
            'red_zone_trips': {
                'home': len([p for p in home_positions if p <= 20]),
                'away': len([p for p in away_positions if p <= 20])
            }
        }

    def _calculate_time_of_possession(self, pbp_data: Dict) -> Dict:
        """Calculate time of possession"""
        # Simplified calculation - would need more detailed time tracking
        return {
            'home_top': '15:30',
            'away_top': '14:30',
            'home_percentage': 51.7,
            'away_percentage': 48.3
        }

    def _calculate_live_efficiency(self, pbp_data: Dict) -> Dict:
        """Calculate live efficiency metrics"""
        if not pbp_data or 'Plays' not in pbp_data:
            return {}

        plays = pbp_data.get('Plays', [])

        # Calculate various efficiency metrics
        third_down_attempts = [p for p in plays if p.get('Down') == 3]
        third_down_conversions = [p for p in third_down_attempts if p.get('YardsGained', 0) >= p.get('Distance', 0)]

        red_zone_attempts = [p for p in plays if p.get('YardLine', 100) <= 20]
        red_zone_scores = [p for p in red_zone_attempts if p.get('IsScoringPlay')]

        return {
            'third_down_efficiency': {
                'attempts': len(third_down_attempts),
                'conversions': len(third_down_conversions),
                'percentage': (len(third_down_conversions) / len(third_down_attempts) * 100) if third_down_attempts else 0
            },
            'red_zone_efficiency': {
                'attempts': len(red_zone_attempts),
                'scores': len(red_zone_scores),
                'percentage': (len(red_zone_scores) / len(red_zone_attempts) * 100) if red_zone_attempts else 0
            },
            'yards_per_play': sum(p.get('YardsGained', 0) for p in plays) / len(plays) if plays else 0,
            'explosive_plays': len([p for p in plays if p.get('YardsGained', 0) >= 20])
        }

    def _calculate_live_win_probability(self, game: Dict) -> Dict:
        """Calculate live win probability"""
        quarter = game.get('Quarter', 1)
        time_remaining = game.get('TimeRemaining', '15:00')
        home_score = game.get('HomeScore', 0)
        away_score = game.get('AwayScore', 0)
        possession = game.get('Possession')

        # Simplified win probability calculation
        score_diff = home_score - away_score
        game_time_remaining = self._convert_time_to_seconds(quarter, time_remaining)
        total_game_time = 3600  # 60 minutes

        time_factor = game_time_remaining / total_game_time
        score_factor = score_diff / 7  # Normalize by touchdown

        # Base probability starts at 50%
        win_prob_home = 50 + (score_factor * 10) + (5 if possession == 'home' else 0)

        # Adjust for time remaining
        if time_factor < 0.25:  # Less than 15 minutes remaining
            win_prob_home += score_factor * 20 * (1 - time_factor)

        # Ensure probability is between 0 and 100
        win_prob_home = max(0, min(100, win_prob_home))

        return {
            'home_win_probability': round(win_prob_home, 1),
            'away_win_probability': round(100 - win_prob_home, 1),
            'factors': {
                'score_differential': score_diff,
                'time_remaining_factor': time_factor,
                'possession_bonus': 5 if possession else 0
            }
        }

    def _predict_final_score(self, game: Dict, pbp_data: Dict) -> Dict:
        """Predict final score based on current pace"""
        quarter = game.get('Quarter', 1)
        home_score = game.get('HomeScore', 0)
        away_score = game.get('AwayScore', 0)

        # Calculate scoring pace
        elapsed_quarters = quarter - 1 + (1 - self._time_remaining_percentage(game.get('TimeRemaining', '15:00')))

        if elapsed_quarters > 0:
            home_pace = home_score / elapsed_quarters * 4
            away_pace = away_score / elapsed_quarters * 4
        else:
            home_pace = home_score * 4
            away_pace = away_score * 4

        return {
            'predicted_home_final': round(home_pace),
            'predicted_away_final': round(away_pace),
            'predicted_total': round(home_pace + away_pace),
            'confidence': 'medium' if quarter >= 2 else 'low'
        }

    def _analyze_betting_implications(self, game: Dict) -> Dict:
        """Analyze betting implications of current game state"""
        home_score = game.get('HomeScore', 0)
        away_score = game.get('AwayScore', 0)
        current_total = home_score + away_score

        return {
            'current_total': current_total,
            'pace': 'over' if current_total > 21 else 'under',  # Rough midpoint
            'spread_status': 'home_covering' if home_score > away_score else 'away_covering',
            'live_betting_value': self._assess_live_betting_value(game),
            'key_betting_moments': self._identify_betting_moments(game)
        }

    def get_drive_by_drive_analysis(self, game_id: str) -> Dict:
        """Get detailed drive-by-drive analysis"""
        try:
            pbp_data = self._get_play_by_play_data(game_id)
            plays = pbp_data.get('Plays', [])

            drives = self._segment_into_drives(plays)
            drive_analysis = []

            for i, drive in enumerate(drives):
                analysis = {
                    'drive_number': i + 1,
                    'possession_team': drive.get('possession_team'),
                    'starting_position': drive.get('starting_position'),
                    'ending_position': drive.get('ending_position'),
                    'plays': len(drive.get('plays', [])),
                    'yards_gained': drive.get('total_yards'),
                    'time_consumed': drive.get('time_consumed'),
                    'result': drive.get('result'),
                    'efficiency_rating': self._rate_drive_efficiency(drive),
                    'key_plays': self._find_drive_key_plays(drive)
                }
                drive_analysis.append(analysis)

            return {
                'game_id': game_id,
                'total_drives': len(drives),
                'drives': drive_analysis,
                'summary': self._summarize_drive_analysis(drive_analysis)
            }

        except Exception as e:
            logger.error(f"Error in drive analysis: {e}")
            return {}

    def start_live_game_monitoring(self, game_ids: List[str] = None, interval_seconds: int = 15):
        """Start monitoring live games"""
        self.is_monitoring = True
        self.monitored_games = game_ids or []

        def monitor_loop():
            while self.is_monitoring:
                try:
                    if self.monitored_games:
                        for game_id in self.monitored_games:
                            live_feed = self.get_live_game_feed(game_id)
                            self._check_game_events(game_id, live_feed)
                    else:
                        # Monitor all live games
                        week_feeds = self.get_live_game_feed()
                        for game in week_feeds.get('games', []):
                            if game.get('game_status') == 'InProgress':
                                self._check_game_events(game['game_id'], game)

                    time.sleep(interval_seconds)

                except Exception as e:
                    logger.error(f"Error in live monitoring: {e}")
                    time.sleep(interval_seconds)

        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"🔴 Started live game monitoring (every {interval_seconds}s)")

    def stop_live_game_monitoring(self):
        """Stop live game monitoring"""
        self.is_monitoring = False
        logger.info("🔴 Stopped live game monitoring")

    def _check_game_events(self, game_id: str, live_feed: Dict):
        """Check for significant game events"""
        # Check for scoring plays, turnovers, etc.
        # This would trigger notifications or updates
        pass

    # Utility methods
    def _get_current_week(self) -> int:
        """Get current NFL week"""
        # Simplified - would need proper week calculation
        return 1

    def _calculate_elapsed_time(self, quarter: int, time_remaining: str) -> float:
        """Calculate elapsed game time"""
        total_seconds = (quarter - 1) * 900  # 15 minutes per quarter
        remaining_seconds = self._convert_time_to_seconds_in_quarter(time_remaining)
        total_seconds += (900 - remaining_seconds)
        return total_seconds / 3600  # Return as hours

    def _convert_time_to_seconds(self, quarter: int, time_remaining: str) -> int:
        """Convert game time to total seconds remaining"""
        try:
            if ':' in time_remaining:
                minutes, seconds = map(int, time_remaining.split(':'))
                quarter_seconds = minutes * 60 + seconds
            else:
                quarter_seconds = 0

            total_seconds = quarter_seconds + (4 - quarter) * 900
            return total_seconds
        except:
            return 0

    def _convert_time_to_seconds_in_quarter(self, time_remaining: str) -> int:
        """Convert time remaining in quarter to seconds"""
        try:
            if ':' in time_remaining:
                minutes, seconds = map(int, time_remaining.split(':'))
                return minutes * 60 + seconds
            return 0
        except:
            return 0

    def _time_remaining_percentage(self, time_remaining: str) -> float:
        """Calculate percentage of quarter remaining"""
        try:
            seconds = self._convert_time_to_seconds_in_quarter(time_remaining)
            return seconds / 900  # 15 minutes per quarter
        except:
            return 0

    def _determine_game_phase(self, quarter: int, time_remaining: str, score_diff: int) -> str:
        """Determine current game phase"""
        if quarter <= 2:
            return 'early_game'
        elif quarter == 3:
            return 'mid_game'
        elif quarter == 4 and self._convert_time_to_seconds_in_quarter(time_remaining) > 300:
            return 'late_game'
        else:
            return 'critical_time'

    def _calculate_urgency(self, quarter: int, time_remaining: str, score_diff: int) -> str:
        """Calculate urgency level"""
        if quarter == 4 and self._convert_time_to_seconds_in_quarter(time_remaining) < 300:
            if score_diff <= 7:
                return 'high'
            elif score_diff <= 14:
                return 'medium'
        return 'low'

    def _assess_comeback_potential(self, quarter: int, time_remaining: str, score_diff: int) -> str:
        """Assess comeback potential"""
        time_seconds = self._convert_time_to_seconds(quarter, time_remaining)

        if score_diff <= 3:
            return 'very_high'
        elif score_diff <= 7 and time_seconds > 300:
            return 'high'
        elif score_diff <= 14 and time_seconds > 600:
            return 'medium'
        elif score_diff <= 21 and time_seconds > 1200:
            return 'low'
        else:
            return 'very_low'

    def _determine_game_script(self, home_score: int, away_score: int, elapsed_time: float) -> str:
        """Determine game script"""
        score_diff = abs(home_score - away_score)

        if score_diff <= 3:
            return 'competitive'
        elif score_diff <= 7:
            return 'close'
        elif score_diff <= 14:
            return 'moderate_lead'
        else:
            return 'blowout'

    def _is_critical_juncture(self, quarter: int, time_remaining: str, score_diff: int) -> bool:
        """Determine if this is a critical juncture"""
        if quarter == 4 and self._convert_time_to_seconds_in_quarter(time_remaining) < 300:
            return score_diff <= 14

        if quarter >= 3 and score_diff <= 7:
            return True

        return False

    def _determine_momentum_team(self, recent_plays: List[Dict]) -> str:
        """Determine which team has momentum"""
        # Simplified momentum calculation
        return 'home'  # Would analyze recent plays

    def _determine_field_zone(self, yard_line: int) -> str:
        """Determine field zone"""
        if yard_line <= 20:
            return 'red_zone'
        elif yard_line <= 40:
            return 'scoring_territory'
        elif yard_line >= 80:
            return 'backed_up'
        else:
            return 'mid_field'

    def _categorize_situation(self, down: int, distance: int, yard_line: int, quarter: int) -> str:
        """Categorize the situation"""
        if down == 3 and distance >= 7:
            return 'obvious_passing_down'
        elif down == 1 and distance <= 3:
            return 'short_yardage'
        elif yard_line <= 5:
            return 'goal_line'
        elif yard_line <= 20:
            return 'red_zone'
        else:
            return 'standard_down'

    def _predict_play_type(self, down: int, distance: int, yard_line: int) -> str:
        """Predict likely play type"""
        if down == 3 and distance > 7:
            return 'pass'
        elif down == 1:
            return 'run'
        elif yard_line <= 3:
            return 'power_run'
        else:
            return 'balanced'

    def _calculate_situation_success_prob(self, down: int, distance: int, yard_line: int) -> float:
        """Calculate success probability for situation"""
        # Simplified calculation
        base_prob = 0.5

        if down == 1:
            base_prob = 0.7
        elif down == 2:
            base_prob = 0.6
        elif down == 3:
            base_prob = 0.4 if distance <= 5 else 0.3
        elif down == 4:
            base_prob = 0.5 if distance <= 2 else 0.3

        return base_prob

    def _calculate_drive_time(self, plays: List[Dict]) -> str:
        """Calculate drive time"""
        # Simplified - would need actual time tracking
        return f"{len(plays)}:30"

    def _calculate_drive_efficiency(self, plays: List[Dict]) -> float:
        """Calculate drive efficiency"""
        if not plays:
            return 0

        total_yards = sum(play.get('YardsGained', 0) for play in plays)
        return total_yards / len(plays)

    def _segment_into_drives(self, plays: List[Dict]) -> List[Dict]:
        """Segment plays into drives"""
        drives = []
        current_drive = []

        for play in plays:
            current_drive.append(play)

            # End drive on scoring play, turnover, or change of possession
            if (play.get('IsScoringPlay') or
                play.get('IsTurnover') or
                play.get('PlayType') in ['Kickoff', 'Punt']):

                if current_drive:
                    drives.append({
                        'plays': current_drive,
                        'possession_team': current_drive[0].get('Team'),
                        'total_yards': sum(p.get('YardsGained', 0) for p in current_drive),
                        'result': self._determine_drive_result(current_drive[-1])
                    })
                current_drive = []

        return drives

    def _determine_drive_result(self, last_play: Dict) -> str:
        """Determine drive result"""
        if last_play.get('IsScoringPlay'):
            if 'Touchdown' in last_play.get('PlayType', ''):
                return 'touchdown'
            elif 'Field Goal' in last_play.get('PlayType', ''):
                return 'field_goal'
        elif last_play.get('IsTurnover'):
            return 'turnover'
        elif last_play.get('PlayType') == 'Punt':
            return 'punt'
        else:
            return 'other'

    def _calculate_average_drive_time(self, drives: List[Dict]) -> str:
        """Calculate average drive time"""
        return "4:30"  # Simplified

    def _calculate_average_yards_per_drive(self, drives: List[Dict]) -> float:
        """Calculate average yards per drive"""
        if not drives:
            return 0
        total_yards = sum(drive.get('total_yards', 0) for drive in drives)
        return total_yards / len(drives)

    def _calculate_largest_lead(self, scoring_plays: List[Dict]) -> int:
        """Calculate largest lead"""
        max_lead = 0
        for play in scoring_plays:
            home_score = play.get('home_score_after', 0)
            away_score = play.get('away_score_after', 0)
            lead = abs(home_score - away_score)
            max_lead = max(max_lead, lead)
        return max_lead

    def _count_lead_changes(self, scoring_plays: List[Dict]) -> int:
        """Count lead changes"""
        lead_changes = 0
        previous_leader = None

        for play in scoring_plays:
            home_score = play.get('home_score_after', 0)
            away_score = play.get('away_score_after', 0)

            if home_score > away_score:
                current_leader = 'home'
            elif away_score > home_score:
                current_leader = 'away'
            else:
                current_leader = 'tie'

            if previous_leader and previous_leader != current_leader and current_leader != 'tie':
                lead_changes += 1

            previous_leader = current_leader

        return lead_changes

    def _calculate_play_epa(self, play: Dict) -> float:
        """Calculate Expected Points Added for a play"""
        # Simplified EPA calculation
        yards_gained = play.get('YardsGained', 0)
        return yards_gained * 0.05  # Rough EPA estimate

    def _calculate_win_prob_change(self, play: Dict) -> float:
        """Calculate win probability change from a play"""
        # Simplified calculation
        if play.get('IsScoringPlay'):
            return 15.0 if 'Touchdown' in play.get('PlayType', '') else 8.0
        elif play.get('IsTurnover'):
            return -12.0
        else:
            return play.get('YardsGained', 0) * 0.5

    def _get_last_play_summary(self, game: Dict) -> str:
        """Get summary of last play"""
        return "Recent play summary"  # Would implement with real data

    def _identify_next_critical_moment(self, game: Dict) -> str:
        """Identify next critical moment"""
        return "Next critical moment"  # Would implement with real data

    def _assess_live_betting_value(self, game: Dict) -> str:
        """Assess live betting value"""
        return "monitor"  # Simplified

    def _identify_betting_moments(self, game: Dict) -> List[str]:
        """Identify key betting moments"""
        return ["Red zone opportunity", "Two-minute warning"]

    def _rate_drive_efficiency(self, drive: Dict) -> float:
        """Rate drive efficiency"""
        return 7.5  # Simplified rating

    def _find_drive_key_plays(self, drive: Dict) -> List[Dict]:
        """Find key plays in a drive"""
        return []  # Would implement with real data

    def _summarize_drive_analysis(self, drive_analysis: List[Dict]) -> Dict:
        """Summarize drive analysis"""
        return {
            'avg_plays_per_drive': 6.5,
            'avg_yards_per_drive': 32.1,
            'scoring_percentage': 35.2
        }

    def _update_game_state(self, game_id: str, game_feed: Dict):
        """Update internal game state tracking"""
        self.game_states[game_id] = {
            'last_update': datetime.now(),
            'current_state': game_feed.get('game_state'),
            'score': {
                'home': game_feed.get('home_score'),
                'away': game_feed.get('away_score')
            }
        }

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self.cache:
            return False
        return datetime.now().timestamp() - self.cache[key]['timestamp'] < self.cache_ttl

    def _cache_data(self, key: str, data: Any) -> None:
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }

# Create singleton instance
real_time_game_feed_service = RealTimeGameFeedService()