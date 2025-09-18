"""
Live Data Service
Fetches real-time NFL data from premium APIs for expert predictions
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

class LiveDataService:
    """Fetches live NFL data from multiple premium sources"""

    def __init__(self):
        # API Keys from environment variables
        self.odds_api_key = os.getenv('VITE_ODDS_API_KEY', '')
        self.sportsdata_io_key = os.getenv('VITE_SPORTSDATA_IO_KEY', '')
        self.rapid_api_key = os.getenv('VITE_RAPID_API_KEY', '')

        # API Endpoints
        self.odds_api_base = "https://api.the-odds-api.com/v4"
        self.sportsdata_base = "https://api.sportsdata.io/v3/nfl"

        logger.info("🎯 Live Data Service initialized with premium APIs")

    def get_upcoming_games(self, week: int = None) -> List[Dict]:
        """Get upcoming NFL games with odds from The Odds API"""
        try:
            # The Odds API - NFL odds
            url = f"{self.odds_api_base}/sports/americanfootball_nfl/odds"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'spreads,totals,h2h',
                'oddsFormat': 'american',
                'bookmakers': 'draftkings,fanduel,betmgm,caesars'
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            games = response.json()
            logger.info(f"✅ Fetched {len(games)} upcoming NFL games from The Odds API")

            # Process games into our format
            processed_games = []
            for game in games:
                processed_game = self._process_odds_api_game(game)
                if processed_game:
                    processed_games.append(processed_game)

            return processed_games

        except Exception as e:
            logger.error(f"❌ Error fetching games from Odds API: {e}")
            return self._get_fallback_games(week)

    def _process_odds_api_game(self, game: Dict) -> Optional[Dict]:
        """Process game data from The Odds API"""
        try:
            # Extract team names
            teams = game.get('home_team', ''), game.get('away_team', '')

            # Get consensus odds from bookmakers
            spreads = []
            totals = []
            moneylines_home = []
            moneylines_away = []

            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['home_team']:
                                spreads.append(outcome['point'])
                    elif market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            if outcome['name'] == 'Over':
                                totals.append(outcome['point'])
                    elif market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['home_team']:
                                moneylines_home.append(outcome['price'])
                            else:
                                moneylines_away.append(outcome['price'])

            # Calculate consensus lines
            consensus_spread = sum(spreads) / len(spreads) if spreads else 0
            consensus_total = sum(totals) / len(totals) if totals else 45
            consensus_ml_home = sum(moneylines_home) / len(moneylines_home) if moneylines_home else -110
            consensus_ml_away = sum(moneylines_away) / len(moneylines_away) if moneylines_away else -110

            return {
                'game_id': game.get('id'),
                'home_team': self._normalize_team_name(game['home_team']),
                'away_team': self._normalize_team_name(game['away_team']),
                'commence_time': game.get('commence_time'),
                'spread': consensus_spread,
                'total': consensus_total,
                'home_moneyline': consensus_ml_home,
                'away_moneyline': consensus_ml_away,
                'bookmaker_count': len(game.get('bookmakers', [])),
                'has_live_odds': True
            }

        except Exception as e:
            logger.error(f"Error processing game: {e}")
            return None

    def get_team_stats(self, team: str, season: int = 2024) -> Dict:
        """Get team statistics from SportsData.io"""
        try:
            url = f"{self.sportsdata_base}/scores/json/TeamSeasonStats/{season}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_teams = response.json()

            # Find the specific team
            for team_stats in all_teams:
                if self._normalize_team_name(team_stats.get('Team', '')) == team:
                    return self._process_team_stats(team_stats)

            logger.warning(f"Team {team} not found in stats")
            return {}

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return {}

    def _process_team_stats(self, stats: Dict) -> Dict:
        """Process team statistics"""
        return {
            'offensive_rating': stats.get('OffensiveYardsPerPlay', 5.5) * 20,
            'defensive_rating': 110 - (stats.get('OpponentOffensiveYardsPerPlay', 5.5) * 20),
            'points_per_game': stats.get('PointsPerGame', 21),
            'points_allowed': stats.get('OpponentPointsPerGame', 21),
            'turnover_differential': stats.get('TurnoverDifferential', 0),
            'third_down_pct': stats.get('ThirdDownPercentage', 40),
            'red_zone_pct': stats.get('RedZonePercentage', 50),
            'time_of_possession': stats.get('TimeOfPossession', '30:00'),
            'games_played': stats.get('Games', 0)
        }

    def get_injuries(self, week: int = None) -> Dict[str, List]:
        """Get injury reports from SportsData.io"""
        try:
            url = f"{self.sportsdata_base}/injuries/json/Injuries/{2024}/{week or ''}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            injuries = response.json()

            # Group by team
            team_injuries = {}
            for injury in injuries:
                team = self._normalize_team_name(injury.get('Team', ''))
                if team not in team_injuries:
                    team_injuries[team] = []

                team_injuries[team].append({
                    'player': injury.get('Name'),
                    'position': injury.get('Position'),
                    'status': injury.get('Status'),
                    'injury': injury.get('Injury'),
                    'key_player': injury.get('Position') in ['QB', 'RB1', 'WR1']
                })

            return team_injuries

        except Exception as e:
            logger.error(f"Error fetching injuries: {e}")
            return {}

    def get_weather(self, stadium: str) -> Dict:
        """Get weather data for outdoor stadiums"""
        # For now, return mock weather data
        # In production, would use a weather API
        outdoor_stadiums = ['BUF', 'GB', 'CHI', 'DEN', 'NE', 'NYJ', 'PHI', 'PIT', 'CLE', 'CIN']

        if stadium in outdoor_stadiums:
            return {
                'temperature': 55,
                'wind_speed': 12,
                'precipitation': 0.1,
                'conditions': 'Partly Cloudy',
                'is_dome': False
            }
        else:
            return {
                'temperature': 72,
                'wind_speed': 0,
                'precipitation': 0,
                'conditions': 'Dome',
                'is_dome': True
            }

    def get_betting_percentages(self) -> Dict:
        """Get public betting percentages (mock for now)"""
        # In production, would fetch from Action Network or similar
        return {
            'public_money_percentage': 65,
            'public_bet_percentage': 72,
            'sharp_money_indicator': 'away',
            'line_movement': -1.5
        }

    def get_comprehensive_game_data(self, home_team: str, away_team: str) -> Dict:
        """Get all data needed for expert predictions"""

        # Fetch all data components
        home_stats = self.get_team_stats(home_team)
        away_stats = self.get_team_stats(away_team)
        injuries = self.get_injuries()
        weather = self.get_weather(home_team)
        betting = self.get_betting_percentages()

        # Get current odds from upcoming games
        upcoming = self.get_upcoming_games()
        game_odds = {}
        for game in upcoming:
            if game['home_team'] == home_team and game['away_team'] == away_team:
                game_odds = game
                break

        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_stats': home_stats,
            'away_stats': away_stats,
            'injuries': {
                'home': injuries.get(home_team, []),
                'away': injuries.get(away_team, [])
            },
            'weather': weather,
            'spread': game_odds.get('spread', -3),
            'total': game_odds.get('total', 45),
            'home_moneyline': game_odds.get('home_moneyline', -150),
            'away_moneyline': game_odds.get('away_moneyline', +130),
            'public_betting_percentage': betting['public_bet_percentage'],
            'line_movement': betting['line_movement'],
            'is_divisional': self._check_divisional(home_team, away_team),
            'is_primetime': datetime.now().hour >= 20,
            'home_advantage': 0.57,  # Historical home win percentage

            # Additional context for experts
            'home_offensive_rating': home_stats.get('offensive_rating', 100),
            'away_offensive_rating': away_stats.get('offensive_rating', 100),
            'home_defensive_rating': home_stats.get('defensive_rating', 100),
            'away_defensive_rating': away_stats.get('defensive_rating', 100),
            'home_streak': 2,  # Would fetch from recent games
            'away_streak': -1,
            'home_last5_record': [3, 2],
            'away_last5_record': [2, 3],
            'home_coach_rating': 7.5,
            'away_coach_rating': 6.5,
            'home_qb_rating': 95.5,
            'away_qb_rating': 88.2,
            'is_dome': weather['is_dome'],
            'travel_distance': 1200,  # Would calculate from city locations
            'time_zones': 1,
            'crowd_capacity_pct': 95
        }

    def _normalize_team_name(self, team: str) -> str:
        """Normalize team names to 2-3 letter codes"""
        team_map = {
            'Kansas City Chiefs': 'KC',
            'Buffalo Bills': 'BUF',
            'San Francisco 49ers': 'SF',
            'Dallas Cowboys': 'DAL',
            'Philadelphia Eagles': 'PHI',
            'Baltimore Ravens': 'BAL',
            'Detroit Lions': 'DET',
            'Green Bay Packers': 'GB',
            'Miami Dolphins': 'MIA',
            'New York Jets': 'NYJ',
            'Cincinnati Bengals': 'CIN',
            'Houston Texans': 'HOU',
            'Cleveland Browns': 'CLE',
            'Pittsburgh Steelers': 'PIT',
            'Los Angeles Rams': 'LAR',
            'Los Angeles Chargers': 'LAC',
            'Seattle Seahawks': 'SEA',
            'Minnesota Vikings': 'MIN',
            'Tampa Bay Buccaneers': 'TB',
            'Atlanta Falcons': 'ATL',
            'New Orleans Saints': 'NO',
            'Jacksonville Jaguars': 'JAX',
            'Indianapolis Colts': 'IND',
            'Tennessee Titans': 'TEN',
            'Denver Broncos': 'DEN',
            'Las Vegas Raiders': 'LV',
            'Arizona Cardinals': 'ARI',
            'Chicago Bears': 'CHI',
            'New England Patriots': 'NE',
            'New York Giants': 'NYG',
            'Washington Commanders': 'WAS',
            'Carolina Panthers': 'CAR'
        }

        # Try to find in map
        for full_name, code in team_map.items():
            if team in full_name or full_name in team:
                return code

        # Already a code
        if len(team) <= 3:
            return team.upper()

        return team

    def _check_divisional(self, home: str, away: str) -> bool:
        """Check if game is divisional"""
        divisions = {
            'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
            'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
            'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
            'AFC West': ['DEN', 'KC', 'LV', 'LAC'],
            'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
            'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
            'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
            'NFC West': ['ARI', 'LAR', 'SF', 'SEA']
        }

        for division, teams in divisions.items():
            if home in teams and away in teams:
                return True
        return False

    def _get_fallback_games(self, week: int) -> List[Dict]:
        """Fallback games if API fails"""
        return [
            {
                'game_id': 'fallback_1',
                'home_team': 'KC',
                'away_team': 'BAL',
                'commence_time': datetime.now().isoformat(),
                'spread': -3.5,
                'total': 48.5,
                'home_moneyline': -165,
                'away_moneyline': +145
            },
            {
                'game_id': 'fallback_2',
                'home_team': 'BUF',
                'away_team': 'MIA',
                'commence_time': datetime.now().isoformat(),
                'spread': -7,
                'total': 51.5,
                'home_moneyline': -280,
                'away_moneyline': +230
            }
        ]


# Create singleton instance
live_data_service = LiveDataService()