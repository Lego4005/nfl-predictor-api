"""
Player Props Service
Fetches player prop data and projections from SportsData.io for comprehensive NFL predictions
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PlayerPropsService:
    """Fetches player props and projections from SportsData.io"""

    def __init__(self):
        # API Keys from environment variables
        self.sportsdata_io_key = os.getenv('VITE_SPORTSDATA_IO_KEY', '')
        self.sportsdata_base = "https://api.sportsdata.io/v3/nfl"

        # Cache for expensive API calls
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache

        logger.info("🏈 Player Props Service initialized with SportsData.io")

    def get_qb_projections(self, week: int, season: int = 2024) -> List[Dict]:
        """Get QB projections: passing yards, touchdowns, completions, attempts"""
        cache_key = f"qb_projections_{season}_{week}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.sportsdata_base}/projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_projections = response.json()

            # Filter for QBs and extract relevant stats
            qb_projections = []
            for player in all_projections:
                if player.get('Position') == 'QB' and player.get('PassingYards', 0) > 0:
                    projection = {
                        'player_id': player.get('PlayerID'),
                        'player_name': player.get('Name'),
                        'team': player.get('Team'),
                        'position': 'QB',
                        'game_week': week,
                        'season': season,

                        # Passing projections
                        'passing_yards': player.get('PassingYards', 0),
                        'passing_yards_prop': self._convert_to_prop_line(player.get('PassingYards', 0)),
                        'passing_touchdowns': player.get('PassingTouchdowns', 0),
                        'passing_td_prop': self._convert_to_prop_line(player.get('PassingTouchdowns', 0), 'td'),
                        'passing_completions': player.get('PassingCompletions', 0),
                        'completions_prop': self._convert_to_prop_line(player.get('PassingCompletions', 0)),
                        'passing_attempts': player.get('PassingAttempts', 0),
                        'attempts_prop': self._convert_to_prop_line(player.get('PassingAttempts', 0)),
                        'passing_interceptions': player.get('PassingInterceptions', 0),
                        'interceptions_prop': self._convert_to_prop_line(player.get('PassingInterceptions', 0), 'int'),

                        # Additional QB rushing props
                        'rushing_yards': player.get('RushingYards', 0),
                        'qb_rushing_yards_prop': self._convert_to_prop_line(player.get('RushingYards', 0), 'qb_rush'),
                        'rushing_touchdowns': player.get('RushingTouchdowns', 0),
                        'qb_rushing_td_prop': self._convert_to_prop_line(player.get('RushingTouchdowns', 0), 'qb_rush_td'),

                        # Fantasy and advanced metrics
                        'fantasy_points': player.get('FantasyPoints', 0),
                        'fantasy_points_prop': self._convert_to_prop_line(player.get('FantasyPoints', 0), 'fantasy'),
                        'qbr_projection': self._calculate_qbr_projection(player),
                        'confidence_level': self._calculate_confidence(player),
                        'weather_impact': self._get_weather_impact(player.get('Team')),
                        'opponent_defense_rating': self._get_opponent_defense_rating(player.get('Team'), week)
                    }
                    qb_projections.append(projection)

            # Cache the results
            self._cache_data(cache_key, qb_projections)

            logger.info(f"✅ Fetched {len(qb_projections)} QB projections for Week {week}")
            return qb_projections

        except Exception as e:
            logger.error(f"❌ Error fetching QB projections: {e}")
            return []

    def get_rb_projections(self, week: int, season: int = 2024) -> List[Dict]:
        """Get RB projections: rushing yards, attempts, touchdowns, receptions"""
        cache_key = f"rb_projections_{season}_{week}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.sportsdata_base}/projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_projections = response.json()

            # Filter for RBs and extract relevant stats
            rb_projections = []
            for player in all_projections:
                if player.get('Position') == 'RB' and (player.get('RushingYards', 0) > 0 or player.get('ReceivingYards', 0) > 0):
                    projection = {
                        'player_id': player.get('PlayerID'),
                        'player_name': player.get('Name'),
                        'team': player.get('Team'),
                        'position': 'RB',
                        'game_week': week,
                        'season': season,

                        # Rushing projections
                        'rushing_yards': player.get('RushingYards', 0),
                        'rushing_yards_prop': self._convert_to_prop_line(player.get('RushingYards', 0)),
                        'rushing_attempts': player.get('RushingAttempts', 0),
                        'rushing_attempts_prop': self._convert_to_prop_line(player.get('RushingAttempts', 0)),
                        'rushing_touchdowns': player.get('RushingTouchdowns', 0),
                        'rushing_td_prop': self._convert_to_prop_line(player.get('RushingTouchdowns', 0), 'td'),
                        'rushing_long': player.get('RushingLong', 0),
                        'longest_rush_prop': self._convert_to_prop_line(player.get('RushingLong', 0), 'long'),

                        # Receiving projections
                        'receiving_yards': player.get('ReceivingYards', 0),
                        'receiving_yards_prop': self._convert_to_prop_line(player.get('ReceivingYards', 0)),
                        'receptions': player.get('Receptions', 0),
                        'receptions_prop': self._convert_to_prop_line(player.get('Receptions', 0)),
                        'receiving_touchdowns': player.get('ReceivingTouchdowns', 0),
                        'receiving_td_prop': self._convert_to_prop_line(player.get('ReceivingTouchdowns', 0), 'td'),
                        'targets': player.get('Targets', 0),
                        'targets_prop': self._convert_to_prop_line(player.get('Targets', 0)),

                        # Combined metrics
                        'scrimmage_yards': player.get('RushingYards', 0) + player.get('ReceivingYards', 0),
                        'scrimmage_yards_prop': self._convert_to_prop_line(
                            player.get('RushingYards', 0) + player.get('ReceivingYards', 0)
                        ),
                        'total_touchdowns': player.get('RushingTouchdowns', 0) + player.get('ReceivingTouchdowns', 0),
                        'total_td_prop': self._convert_to_prop_line(
                            player.get('RushingTouchdowns', 0) + player.get('ReceivingTouchdowns', 0), 'td'
                        ),

                        # Fantasy and advanced metrics
                        'fantasy_points': player.get('FantasyPoints', 0),
                        'fantasy_points_prop': self._convert_to_prop_line(player.get('FantasyPoints', 0), 'fantasy'),
                        'snap_count_projection': self._calculate_snap_count_projection(player),
                        'goal_line_carries_proj': self._calculate_goal_line_projection(player),
                        'confidence_level': self._calculate_confidence(player),
                        'injury_risk': self._get_injury_risk(player.get('PlayerID')),
                        'matchup_rating': self._get_matchup_rating(player.get('Team'), week, 'RB')
                    }
                    rb_projections.append(projection)

            # Cache the results
            self._cache_data(cache_key, rb_projections)

            logger.info(f"✅ Fetched {len(rb_projections)} RB projections for Week {week}")
            return rb_projections

        except Exception as e:
            logger.error(f"❌ Error fetching RB projections: {e}")
            return []

    def get_wr_projections(self, week: int, season: int = 2024) -> List[Dict]:
        """Get WR projections: receiving yards, receptions, targets, touchdowns"""
        cache_key = f"wr_projections_{season}_{week}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.sportsdata_base}/projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_projections = response.json()

            # Filter for WRs and TEs
            wr_projections = []
            for player in all_projections:
                if player.get('Position') in ['WR', 'TE'] and player.get('ReceivingYards', 0) > 0:
                    projection = {
                        'player_id': player.get('PlayerID'),
                        'player_name': player.get('Name'),
                        'team': player.get('Team'),
                        'position': player.get('Position'),
                        'game_week': week,
                        'season': season,

                        # Receiving projections
                        'receiving_yards': player.get('ReceivingYards', 0),
                        'receiving_yards_prop': self._convert_to_prop_line(player.get('ReceivingYards', 0)),
                        'receptions': player.get('Receptions', 0),
                        'receptions_prop': self._convert_to_prop_line(player.get('Receptions', 0)),
                        'targets': player.get('Targets', 0),
                        'targets_prop': self._convert_to_prop_line(player.get('Targets', 0)),
                        'receiving_touchdowns': player.get('ReceivingTouchdowns', 0),
                        'receiving_td_prop': self._convert_to_prop_line(player.get('ReceivingTouchdowns', 0), 'td'),
                        'receiving_long': player.get('ReceivingLong', 0),
                        'longest_reception_prop': self._convert_to_prop_line(player.get('ReceivingLong', 0), 'long'),

                        # Advanced receiving metrics
                        'yards_after_catch': self._calculate_yac_projection(player),
                        'yac_prop': self._convert_to_prop_line(self._calculate_yac_projection(player)),
                        'red_zone_targets': self._calculate_rz_targets_projection(player),
                        'rz_targets_prop': self._convert_to_prop_line(self._calculate_rz_targets_projection(player)),
                        'first_down_catches': self._calculate_first_down_projection(player),
                        'first_down_prop': self._convert_to_prop_line(self._calculate_first_down_projection(player)),

                        # Special categories
                        '1st_catch_of_game': self._calculate_first_catch_odds(player),
                        'anytime_td_odds': self._calculate_anytime_td_odds(player),
                        '2_plus_td_odds': self._calculate_multiple_td_odds(player),
                        '100_plus_yards_odds': self._calculate_100_yard_odds(player),

                        # Fantasy and advanced metrics
                        'fantasy_points': player.get('FantasyPoints', 0),
                        'fantasy_points_prop': self._convert_to_prop_line(player.get('FantasyPoints', 0), 'fantasy'),
                        'target_share_projection': self._calculate_target_share(player),
                        'air_yards_projection': self._calculate_air_yards(player),
                        'snap_count_projection': self._calculate_snap_count_projection(player),
                        'confidence_level': self._calculate_confidence(player),
                        'matchup_rating': self._get_matchup_rating(player.get('Team'), week, player.get('Position')),
                        'coverage_difficulty': self._get_coverage_difficulty(player.get('Team'), week)
                    }
                    wr_projections.append(projection)

            # Cache the results
            self._cache_data(cache_key, wr_projections)

            logger.info(f"✅ Fetched {len(wr_projections)} WR/TE projections for Week {week}")
            return wr_projections

        except Exception as e:
            logger.error(f"❌ Error fetching WR projections: {e}")
            return []

    def get_team_player_props_summary(self, team: str, week: int, season: int = 2024) -> Dict:
        """Get comprehensive team player props summary"""
        try:
            qb_props = [p for p in self.get_qb_projections(week, season) if p['team'] == team]
            rb_props = [p for p in self.get_rb_projections(week, season) if p['team'] == team]
            wr_props = [p for p in self.get_wr_projections(week, season) if p['team'] == team]

            return {
                'team': team,
                'week': week,
                'season': season,
                'quarterbacks': qb_props,
                'running_backs': rb_props,
                'receivers': wr_props,

                # Team totals
                'team_passing_yards_total': sum(p['passing_yards'] for p in qb_props),
                'team_rushing_yards_total': sum(p['rushing_yards'] for p in rb_props),
                'team_receiving_yards_total': sum(p['receiving_yards'] for p in wr_props),
                'team_total_touchdowns': (
                    sum(p['passing_touchdowns'] + p['rushing_touchdowns'] for p in qb_props) +
                    sum(p['rushing_touchdowns'] + p['receiving_touchdowns'] for p in rb_props) +
                    sum(p['receiving_touchdowns'] for p in wr_props)
                ),

                # Key player props
                'key_players': self._identify_key_players(qb_props + rb_props + wr_props),
                'prop_betting_opportunities': self._identify_prop_opportunities(qb_props + rb_props + wr_props),
                'lineup_analysis': self._analyze_lineup_impact(qb_props + rb_props + wr_props),

                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error getting team props summary: {e}")
            return {}

    def _convert_to_prop_line(self, projection_value: float, prop_type: str = 'yards') -> Dict:
        """Convert projection to betting prop line with over/under"""
        if not projection_value:
            return {'line': 0, 'over_odds': 100, 'under_odds': -120}

        # Add variance based on prop type
        variance_map = {
            'yards': 0.15,  # ±15% variance
            'td': 0.25,     # ±25% variance for TDs
            'int': 0.30,    # ±30% variance for INTs
            'fantasy': 0.12, # ±12% variance for fantasy
            'long': 0.20,   # ±20% variance for long plays
            'qb_rush': 0.25, # ±25% variance for QB rushing
            'qb_rush_td': 0.35 # ±35% variance for QB rushing TDs
        }

        variance = variance_map.get(prop_type, 0.15)
        line = round(projection_value * (1 - variance), 1)

        # Calculate odds based on confidence
        over_odds = -110 if projection_value > line * 1.1 else -105
        under_odds = -110 if projection_value < line * 0.9 else -115

        return {
            'line': line,
            'over_odds': over_odds,
            'under_odds': under_odds,
            'projection': projection_value,
            'confidence': min(100, max(50, 100 - (variance * 100)))
        }

    def _calculate_qbr_projection(self, player: Dict) -> float:
        """Calculate projected QBR based on stats"""
        try:
            comp_pct = player.get('PassingCompletions', 0) / max(player.get('PassingAttempts', 1), 1)
            td_int_ratio = player.get('PassingTouchdowns', 0) / max(player.get('PassingInterceptions', 1), 1)
            yards_per_attempt = player.get('PassingYards', 0) / max(player.get('PassingAttempts', 1), 1)

            qbr = (comp_pct * 40) + (td_int_ratio * 20) + (yards_per_attempt * 5) + 30
            return min(158.3, max(0, qbr))
        except:
            return 85.0

    def _calculate_snap_count_projection(self, player: Dict) -> int:
        """Calculate projected snap count"""
        position = player.get('Position', '')
        fantasy_points = player.get('FantasyPoints', 0)

        if position == 'QB':
            return 65 if fantasy_points > 15 else 45
        elif position == 'RB':
            return int(fantasy_points * 3) if fantasy_points > 8 else 25
        elif position in ['WR', 'TE']:
            return int(fantasy_points * 2.5) if fantasy_points > 6 else 20

        return 30

    def _calculate_goal_line_projection(self, player: Dict) -> float:
        """Calculate goal line carry projection for RBs"""
        rushing_tds = player.get('RushingTouchdowns', 0)
        rushing_attempts = player.get('RushingAttempts', 0)

        if rushing_attempts > 15:
            return max(2.0, rushing_tds * 1.5)
        return 1.0

    def _calculate_yac_projection(self, player: Dict) -> float:
        """Calculate yards after catch projection"""
        receiving_yards = player.get('ReceivingYards', 0)
        receptions = player.get('Receptions', 0)

        if receptions > 0:
            avg_per_catch = receiving_yards / receptions
            return avg_per_catch * 0.6  # ~60% typically YAC
        return 0

    def _calculate_rz_targets_projection(self, player: Dict) -> float:
        """Calculate red zone targets projection"""
        receiving_tds = player.get('ReceivingTouchdowns', 0)
        targets = player.get('Targets', 0)

        # RZ targets typically 2-3x TD projection
        return max(1.0, receiving_tds * 2.5)

    def _calculate_first_down_projection(self, player: Dict) -> float:
        """Calculate first down catches projection"""
        receptions = player.get('Receptions', 0)
        # ~40% of catches typically result in first downs
        return receptions * 0.4

    def _calculate_first_catch_odds(self, player: Dict) -> int:
        """Calculate odds for first catch of game"""
        receptions = player.get('Receptions', 0)
        if receptions >= 6:
            return -150
        elif receptions >= 4:
            return -110
        elif receptions >= 2:
            return +120
        else:
            return +250

    def _calculate_anytime_td_odds(self, player: Dict) -> int:
        """Calculate anytime touchdown odds"""
        td_prob = player.get('ReceivingTouchdowns', 0) + player.get('RushingTouchdowns', 0)

        if td_prob >= 0.8:
            return -200
        elif td_prob >= 0.6:
            return -150
        elif td_prob >= 0.4:
            return +100
        elif td_prob >= 0.2:
            return +200
        else:
            return +400

    def _calculate_multiple_td_odds(self, player: Dict) -> int:
        """Calculate 2+ touchdown odds"""
        td_proj = player.get('ReceivingTouchdowns', 0) + player.get('RushingTouchdowns', 0)

        if td_proj >= 1.5:
            return +200
        elif td_proj >= 1.0:
            return +400
        elif td_proj >= 0.8:
            return +600
        else:
            return +1000

    def _calculate_100_yard_odds(self, player: Dict) -> int:
        """Calculate 100+ receiving yards odds"""
        receiving_yards = player.get('ReceivingYards', 0)

        if receiving_yards >= 100:
            return -150
        elif receiving_yards >= 85:
            return +100
        elif receiving_yards >= 70:
            return +200
        elif receiving_yards >= 50:
            return +400
        else:
            return +800

    def _calculate_target_share(self, player: Dict) -> float:
        """Calculate projected target share"""
        targets = player.get('Targets', 0)
        # Estimate team total targets (typically 30-40 per game)
        team_targets = 35
        return (targets / team_targets) * 100

    def _calculate_air_yards(self, player: Dict) -> float:
        """Calculate projected air yards"""
        receiving_yards = player.get('ReceivingYards', 0)
        # Air yards typically ~40% of total receiving yards
        return receiving_yards * 0.4

    def _calculate_confidence(self, player: Dict) -> int:
        """Calculate confidence level for projections"""
        fantasy_points = player.get('FantasyPoints', 0)

        if fantasy_points > 15:
            return 90
        elif fantasy_points > 10:
            return 80
        elif fantasy_points > 5:
            return 70
        else:
            return 60

    def _get_weather_impact(self, team: str) -> str:
        """Get weather impact for outdoor teams"""
        outdoor_teams = ['BUF', 'GB', 'CHI', 'DEN', 'NE', 'NYJ', 'PHI', 'PIT', 'CLE', 'CIN']
        return 'High' if team in outdoor_teams else 'Low'

    def _get_opponent_defense_rating(self, team: str, week: int) -> int:
        """Get opponent defense rating (mock for now)"""
        # Would fetch actual opponent defensive rankings
        return 15  # Average ranking

    def _get_injury_risk(self, player_id: str) -> str:
        """Get injury risk assessment"""
        # Would fetch from injury reports
        return 'Low'

    def _get_matchup_rating(self, team: str, week: int, position: str) -> str:
        """Get matchup rating vs opponent"""
        # Would analyze opponent's defense vs position
        return 'Average'

    def _get_coverage_difficulty(self, team: str, week: int) -> str:
        """Get opponent coverage difficulty"""
        # Would analyze opponent's pass defense
        return 'Medium'

    def _identify_key_players(self, all_props: List[Dict]) -> List[Dict]:
        """Identify key players for prop betting"""
        key_players = []
        for player in all_props:
            if player.get('fantasy_points', 0) > 12 or player.get('confidence_level', 0) > 85:
                key_players.append({
                    'name': player['player_name'],
                    'position': player['position'],
                    'team': player['team'],
                    'top_props': self._get_top_props(player),
                    'confidence': player.get('confidence_level', 0)
                })
        return sorted(key_players, key=lambda x: x['confidence'], reverse=True)[:10]

    def _get_top_props(self, player: Dict) -> List[str]:
        """Get top prop recommendations for player"""
        props = []
        position = player.get('position', '')

        if position == 'QB':
            if player.get('passing_yards', 0) > 250:
                props.append('Passing Yards Over')
            if player.get('passing_touchdowns', 0) > 1.5:
                props.append('Passing TDs Over')
        elif position == 'RB':
            if player.get('rushing_yards', 0) > 80:
                props.append('Rushing Yards Over')
            if player.get('scrimmage_yards', 0) > 100:
                props.append('Scrimmage Yards Over')
        elif position in ['WR', 'TE']:
            if player.get('receiving_yards', 0) > 60:
                props.append('Receiving Yards Over')
            if player.get('receptions', 0) > 5:
                props.append('Receptions Over')

        return props

    def _identify_prop_opportunities(self, all_props: List[Dict]) -> List[Dict]:
        """Identify best prop betting opportunities"""
        opportunities = []

        for player in all_props:
            confidence = player.get('confidence_level', 0)

            if confidence > 80:
                # High confidence plays
                opportunities.append({
                    'player': player['player_name'],
                    'prop_type': 'High Confidence',
                    'recommendation': self._get_top_props(player),
                    'confidence': confidence,
                    'reasoning': f"High projection confidence with {confidence}% certainty"
                })

        return sorted(opportunities, key=lambda x: x['confidence'], reverse=True)[:5]

    def _analyze_lineup_impact(self, all_props: List[Dict]) -> Dict:
        """Analyze how lineup changes affect props"""
        return {
            'injury_impacts': [],  # Would track injury impacts
            'weather_adjustments': [],  # Would track weather impacts
            'lineup_changes': [],  # Would track lineup changes
            'recommendation': 'Monitor injury reports for final lineup decisions'
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
player_props_service = PlayerPropsService()