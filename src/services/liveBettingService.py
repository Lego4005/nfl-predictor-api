"""
Live Betting Service
Fetches real-time betting data and market movements from The Odds API
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

class LiveBettingService:
    """Fetches live betting data and tracks market movements"""

    def __init__(self):
        # API Keys from environment variables
        self.odds_api_key = os.getenv('VITE_ODDS_API_KEY', '')
        self.odds_api_base = "https://api.the-odds-api.com/v4"

        # Cache and tracking
        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache for live data
        self.market_history = {}
        self.live_games = {}
        self.market_alerts = []

        # WebSocket connection (if available)
        self.ws_connection = None
        self.is_monitoring = False

        logger.info("📈 Live Betting Service initialized")

    def get_live_odds_movements(self, game_id: str = None) -> Dict:
        """Get real-time odds movements for all or specific games"""
        cache_key = f"live_odds_{game_id or 'all'}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Get current odds
            url = f"{self.odds_api_base}/sports/americanfootball_nfl/odds/live"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american',
                'bookmakers': 'draftkings,fanduel,betmgm,caesars,pointsbet,barstool'
            }

            if game_id:
                params['eventIds'] = game_id

            response = requests.get(url, params=params)
            response.raise_for_status()

            current_odds = response.json()

            # Process and track movements
            movements_data = self._process_odds_movements(current_odds)

            # Cache the results
            self._cache_data(cache_key, movements_data)

            logger.info(f"✅ Fetched live odds movements for {len(current_odds)} games")
            return movements_data

        except Exception as e:
            logger.error(f"❌ Error fetching live odds movements: {e}")
            return {}

    def _process_odds_movements(self, current_odds: List[Dict]) -> Dict:
        """Process current odds and detect movements"""
        movements = {
            'games': [],
            'significant_movements': [],
            'market_inefficiencies': [],
            'sharp_action_indicators': [],
            'public_vs_sharp_divergence': [],
            'last_updated': datetime.now().isoformat()
        }

        for game in current_odds:
            game_id = game.get('id')
            game_movements = self._analyze_game_movements(game, game_id)

            movements['games'].append(game_movements)

            # Detect significant movements
            if game_movements.get('significant_movements'):
                movements['significant_movements'].extend(game_movements['significant_movements'])

            # Identify market inefficiencies
            if game_movements.get('market_inefficiencies'):
                movements['market_inefficiencies'].extend(game_movements['market_inefficiencies'])

            # Sharp action indicators
            if game_movements.get('sharp_indicators'):
                movements['sharp_action_indicators'].extend(game_movements['sharp_indicators'])

        return movements

    def _analyze_game_movements(self, game: Dict, game_id: str) -> Dict:
        """Analyze movements for a specific game"""
        current_time = datetime.now()

        # Get historical data for comparison
        historical_odds = self.market_history.get(game_id, [])

        game_analysis = {
            'game_id': game_id,
            'home_team': game.get('home_team'),
            'away_team': game.get('away_team'),
            'commence_time': game.get('commence_time'),
            'current_bookmakers': [],
            'line_movements': {},
            'significant_movements': [],
            'market_inefficiencies': [],
            'sharp_indicators': [],
            'consensus_data': {},
            'best_odds': {},
            'arbitrage_opportunities': []
        }

        # Process each bookmaker
        bookmaker_data = {}
        for bookmaker in game.get('bookmakers', []):
            bookmaker_name = bookmaker.get('title')
            markets = self._process_bookmaker_markets(bookmaker.get('markets', []))

            bookmaker_data[bookmaker_name] = {
                'last_update': bookmaker.get('last_update'),
                'markets': markets
            }

            game_analysis['current_bookmakers'].append({
                'name': bookmaker_name,
                'spread_home': markets.get('spread_home'),
                'spread_away': markets.get('spread_away'),
                'total_over': markets.get('total_over'),
                'total_under': markets.get('total_under'),
                'moneyline_home': markets.get('moneyline_home'),
                'moneyline_away': markets.get('moneyline_away'),
                'last_update': bookmaker.get('last_update')
            })

        # Calculate consensus and best odds
        game_analysis['consensus_data'] = self._calculate_consensus_odds(bookmaker_data)
        game_analysis['best_odds'] = self._find_best_odds(bookmaker_data)

        # Detect movements if we have historical data
        if historical_odds:
            game_analysis['line_movements'] = self._detect_line_movements(
                historical_odds, bookmaker_data, current_time
            )

            # Identify significant movements
            game_analysis['significant_movements'] = self._identify_significant_movements(
                game_analysis['line_movements']
            )

            # Detect sharp action
            game_analysis['sharp_indicators'] = self._detect_sharp_action(
                game_analysis['line_movements'], bookmaker_data
            )

        # Find market inefficiencies
        game_analysis['market_inefficiencies'] = self._find_market_inefficiencies(bookmaker_data)

        # Find arbitrage opportunities
        game_analysis['arbitrage_opportunities'] = self._find_arbitrage_opportunities(bookmaker_data)

        # Update historical data
        self._update_market_history(game_id, bookmaker_data, current_time)

        return game_analysis

    def _process_bookmaker_markets(self, markets: List[Dict]) -> Dict:
        """Process markets from a bookmaker"""
        processed = {
            'spread_home': None, 'spread_away': None,
            'spread_home_odds': None, 'spread_away_odds': None,
            'total_over': None, 'total_under': None,
            'total_over_odds': None, 'total_under_odds': None,
            'moneyline_home': None, 'moneyline_away': None
        }

        for market in markets:
            market_key = market.get('key')
            outcomes = market.get('outcomes', [])

            if market_key == 'spreads' and len(outcomes) >= 2:
                # Spreads
                for outcome in outcomes:
                    if outcome.get('point', 0) > 0:
                        processed['spread_home'] = outcome.get('point')
                        processed['spread_home_odds'] = outcome.get('price')
                    else:
                        processed['spread_away'] = outcome.get('point')
                        processed['spread_away_odds'] = outcome.get('price')

            elif market_key == 'totals' and len(outcomes) >= 2:
                # Totals
                for outcome in outcomes:
                    if outcome.get('name') == 'Over':
                        processed['total_over'] = outcome.get('point')
                        processed['total_over_odds'] = outcome.get('price')
                    elif outcome.get('name') == 'Under':
                        processed['total_under'] = outcome.get('point')
                        processed['total_under_odds'] = outcome.get('price')

            elif market_key == 'h2h' and len(outcomes) >= 2:
                # Moneylines
                processed['moneyline_home'] = outcomes[0].get('price')
                processed['moneyline_away'] = outcomes[1].get('price')

        return processed

    def _calculate_consensus_odds(self, bookmaker_data: Dict) -> Dict:
        """Calculate consensus odds across all bookmakers"""
        spreads_home = []
        totals_over = []
        moneylines_home = []
        moneylines_away = []

        for bookmaker, data in bookmaker_data.items():
            markets = data.get('markets', {})

            if markets.get('spread_home') is not None:
                spreads_home.append(markets['spread_home'])
            if markets.get('total_over') is not None:
                totals_over.append(markets['total_over'])
            if markets.get('moneyline_home') is not None:
                moneylines_home.append(markets['moneyline_home'])
            if markets.get('moneyline_away') is not None:
                moneylines_away.append(markets['moneyline_away'])

        return {
            'consensus_spread': self._calculate_median(spreads_home) if spreads_home else None,
            'consensus_total': self._calculate_median(totals_over) if totals_over else None,
            'consensus_ml_home': self._calculate_median(moneylines_home) if moneylines_home else None,
            'consensus_ml_away': self._calculate_median(moneylines_away) if moneylines_away else None,
            'spread_variance': self._calculate_variance(spreads_home) if spreads_home else 0,
            'total_variance': self._calculate_variance(totals_over) if totals_over else 0,
            'bookmaker_count': len(bookmaker_data)
        }

    def _find_best_odds(self, bookmaker_data: Dict) -> Dict:
        """Find best odds across all bookmakers"""
        best_odds = {
            'best_spread_home': {'value': None, 'odds': None, 'bookmaker': None},
            'best_spread_away': {'value': None, 'odds': None, 'bookmaker': None},
            'best_total_over': {'value': None, 'odds': None, 'bookmaker': None},
            'best_total_under': {'value': None, 'odds': None, 'bookmaker': None},
            'best_ml_home': {'odds': None, 'bookmaker': None},
            'best_ml_away': {'odds': None, 'bookmaker': None}
        }

        for bookmaker, data in bookmaker_data.items():
            markets = data.get('markets', {})

            # Best spread home (highest point value)
            if markets.get('spread_home') is not None:
                if (best_odds['best_spread_home']['value'] is None or
                    markets['spread_home'] > best_odds['best_spread_home']['value']):
                    best_odds['best_spread_home'] = {
                        'value': markets['spread_home'],
                        'odds': markets.get('spread_home_odds'),
                        'bookmaker': bookmaker
                    }

            # Best spread away (lowest point value - more negative)
            if markets.get('spread_away') is not None:
                if (best_odds['best_spread_away']['value'] is None or
                    markets['spread_away'] < best_odds['best_spread_away']['value']):
                    best_odds['best_spread_away'] = {
                        'value': markets['spread_away'],
                        'odds': markets.get('spread_away_odds'),
                        'bookmaker': bookmaker
                    }

            # Best total over (lowest total)
            if markets.get('total_over') is not None:
                if (best_odds['best_total_over']['value'] is None or
                    markets['total_over'] < best_odds['best_total_over']['value']):
                    best_odds['best_total_over'] = {
                        'value': markets['total_over'],
                        'odds': markets.get('total_over_odds'),
                        'bookmaker': bookmaker
                    }

            # Best total under (highest total)
            if markets.get('total_under') is not None:
                if (best_odds['best_total_under']['value'] is None or
                    markets['total_under'] > best_odds['best_total_under']['value']):
                    best_odds['best_total_under'] = {
                        'value': markets['total_under'],
                        'odds': markets.get('total_under_odds'),
                        'bookmaker': bookmaker
                    }

            # Best moneylines (highest odds = better payout)
            if markets.get('moneyline_home') is not None:
                if (best_odds['best_ml_home']['odds'] is None or
                    markets['moneyline_home'] > best_odds['best_ml_home']['odds']):
                    best_odds['best_ml_home'] = {
                        'odds': markets['moneyline_home'],
                        'bookmaker': bookmaker
                    }

            if markets.get('moneyline_away') is not None:
                if (best_odds['best_ml_away']['odds'] is None or
                    markets['moneyline_away'] > best_odds['best_ml_away']['odds']):
                    best_odds['best_ml_away'] = {
                        'odds': markets['moneyline_away'],
                        'bookmaker': bookmaker
                    }

        return best_odds

    def _detect_line_movements(self, historical_odds: List[Dict], current_data: Dict, current_time: datetime) -> Dict:
        """Detect line movements from historical data"""
        movements = {
            'spread_movements': [],
            'total_movements': [],
            'moneyline_movements': [],
            'movement_velocity': {},
            'movement_direction': {},
            'steam_moves': []
        }

        # Get most recent historical point (last 5 minutes)
        recent_historical = None
        for hist_point in reversed(historical_odds):
            if (current_time - datetime.fromisoformat(hist_point['timestamp'])).seconds < 300:
                recent_historical = hist_point
                break

        if not recent_historical:
            return movements

        # Compare current vs recent historical
        for bookmaker, current_markets in current_data.items():
            if bookmaker in recent_historical.get('data', {}):
                hist_markets = recent_historical['data'][bookmaker]['markets']

                # Spread movements
                self._track_spread_movements(
                    movements, bookmaker, hist_markets, current_markets['markets']
                )

                # Total movements
                self._track_total_movements(
                    movements, bookmaker, hist_markets, current_markets['markets']
                )

                # Moneyline movements
                self._track_moneyline_movements(
                    movements, bookmaker, hist_markets, current_markets['markets']
                )

        # Detect steam moves (rapid movement across multiple books)
        movements['steam_moves'] = self._detect_steam_moves(movements)

        return movements

    def _track_spread_movements(self, movements: Dict, bookmaker: str, hist_markets: Dict, current_markets: Dict):
        """Track spread line movements"""
        hist_spread_home = hist_markets.get('spread_home')
        current_spread_home = current_markets.get('spread_home')

        if hist_spread_home is not None and current_spread_home is not None:
            movement = current_spread_home - hist_spread_home
            if abs(movement) >= 0.5:  # Significant movement threshold
                movements['spread_movements'].append({
                    'bookmaker': bookmaker,
                    'previous_line': hist_spread_home,
                    'current_line': current_spread_home,
                    'movement': movement,
                    'direction': 'home_favorable' if movement > 0 else 'away_favorable',
                    'magnitude': 'large' if abs(movement) >= 1.0 else 'moderate'
                })

    def _track_total_movements(self, movements: Dict, bookmaker: str, hist_markets: Dict, current_markets: Dict):
        """Track total line movements"""
        hist_total = hist_markets.get('total_over')
        current_total = current_markets.get('total_over')

        if hist_total is not None and current_total is not None:
            movement = current_total - hist_total
            if abs(movement) >= 0.5:  # Significant movement threshold
                movements['total_movements'].append({
                    'bookmaker': bookmaker,
                    'previous_line': hist_total,
                    'current_line': current_total,
                    'movement': movement,
                    'direction': 'over_favorable' if movement < 0 else 'under_favorable',
                    'magnitude': 'large' if abs(movement) >= 1.0 else 'moderate'
                })

    def _track_moneyline_movements(self, movements: Dict, bookmaker: str, hist_markets: Dict, current_markets: Dict):
        """Track moneyline movements"""
        hist_ml_home = hist_markets.get('moneyline_home')
        current_ml_home = current_markets.get('moneyline_home')

        if hist_ml_home is not None and current_ml_home is not None:
            movement = current_ml_home - hist_ml_home
            if abs(movement) >= 10:  # Significant movement threshold
                movements['moneyline_movements'].append({
                    'bookmaker': bookmaker,
                    'team': 'home',
                    'previous_odds': hist_ml_home,
                    'current_odds': current_ml_home,
                    'movement': movement,
                    'direction': 'lengthened' if movement > 0 else 'shortened',
                    'magnitude': 'large' if abs(movement) >= 25 else 'moderate'
                })

    def _detect_steam_moves(self, movements: Dict) -> List[Dict]:
        """Detect steam moves (coordinated movement across multiple books)"""
        steam_moves = []

        # Spread steam moves
        spread_movements = movements.get('spread_movements', [])
        if len(spread_movements) >= 3:  # Multiple books moving same direction
            directions = [move['direction'] for move in spread_movements]
            if len(set(directions)) == 1:  # All same direction
                steam_moves.append({
                    'type': 'spread_steam',
                    'direction': directions[0],
                    'bookmaker_count': len(spread_movements),
                    'avg_movement': sum(abs(move['movement']) for move in spread_movements) / len(spread_movements),
                    'severity': 'high' if len(spread_movements) >= 5 else 'moderate'
                })

        # Total steam moves
        total_movements = movements.get('total_movements', [])
        if len(total_movements) >= 3:
            directions = [move['direction'] for move in total_movements]
            if len(set(directions)) == 1:
                steam_moves.append({
                    'type': 'total_steam',
                    'direction': directions[0],
                    'bookmaker_count': len(total_movements),
                    'avg_movement': sum(abs(move['movement']) for move in total_movements) / len(total_movements),
                    'severity': 'high' if len(total_movements) >= 5 else 'moderate'
                })

        return steam_moves

    def _identify_significant_movements(self, line_movements: Dict) -> List[Dict]:
        """Identify significant movements that warrant attention"""
        significant = []

        # Large spread movements
        for movement in line_movements.get('spread_movements', []):
            if movement['magnitude'] == 'large':
                significant.append({
                    'type': 'spread_movement',
                    'bookmaker': movement['bookmaker'],
                    'description': f"Spread moved {movement['movement']} points to {movement['current_line']}",
                    'impact': 'high',
                    'direction': movement['direction']
                })

        # Large total movements
        for movement in line_movements.get('total_movements', []):
            if movement['magnitude'] == 'large':
                significant.append({
                    'type': 'total_movement',
                    'bookmaker': movement['bookmaker'],
                    'description': f"Total moved {movement['movement']} points to {movement['current_line']}",
                    'impact': 'high',
                    'direction': movement['direction']
                })

        # Steam moves
        for steam in line_movements.get('steam_moves', []):
            significant.append({
                'type': 'steam_move',
                'description': f"{steam['type']} across {steam['bookmaker_count']} books",
                'impact': 'very_high',
                'severity': steam['severity']
            })

        return significant

    def _detect_sharp_action(self, line_movements: Dict, bookmaker_data: Dict) -> List[Dict]:
        """Detect potential sharp action indicators"""
        sharp_indicators = []

        # Steam moves are often sharp action
        for steam in line_movements.get('steam_moves', []):
            sharp_indicators.append({
                'type': 'steam_move_sharp',
                'confidence': 85,
                'description': f"Steam move detected: {steam['type']} across {steam['bookmaker_count']} books",
                'action_type': 'sharp_money'
            })

        # Reverse line movement (line moves opposite to public betting)
        # This would require public betting data integration
        # For now, we'll use proxy indicators

        # Line movement against the larger side
        spread_movements = line_movements.get('spread_movements', [])
        if len(spread_movements) >= 2:
            # Look for consistent movement in one direction
            directions = [move['direction'] for move in spread_movements]
            if len(set(directions)) == 1:
                sharp_indicators.append({
                    'type': 'consistent_movement',
                    'confidence': 70,
                    'description': f"Consistent line movement: {directions[0]}",
                    'action_type': 'professional_money'
                })

        return sharp_indicators

    def _find_market_inefficiencies(self, bookmaker_data: Dict) -> List[Dict]:
        """Find market inefficiencies between bookmakers"""
        inefficiencies = []

        # Collect all spreads and totals
        spreads = {}
        totals = {}
        moneylines = {}

        for bookmaker, data in bookmaker_data.items():
            markets = data.get('markets', {})

            if markets.get('spread_home') is not None:
                spreads[bookmaker] = markets['spread_home']
            if markets.get('total_over') is not None:
                totals[bookmaker] = markets['total_over']
            if markets.get('moneyline_home') is not None:
                moneylines[bookmaker] = markets['moneyline_home']

        # Find spread inefficiencies
        if len(spreads) >= 3:
            spread_values = list(spreads.values())
            spread_range = max(spread_values) - min(spread_values)

            if spread_range >= 1.0:  # Significant spread difference
                best_book = max(spreads, key=spreads.get)
                worst_book = min(spreads, key=spreads.get)

                inefficiencies.append({
                    'type': 'spread_inefficiency',
                    'value_difference': spread_range,
                    'best_line': {'bookmaker': best_book, 'value': spreads[best_book]},
                    'worst_line': {'bookmaker': worst_book, 'value': spreads[worst_book]},
                    'opportunity': 'middle' if spread_range >= 2.0 else 'line_shopping',
                    'confidence': 90 if spread_range >= 2.0 else 75
                })

        # Find total inefficiencies
        if len(totals) >= 3:
            total_values = list(totals.values())
            total_range = max(total_values) - min(total_values)

            if total_range >= 1.0:
                best_over_book = min(totals, key=totals.get)  # Lowest total for over bets
                best_under_book = max(totals, key=totals.get)  # Highest total for under bets

                inefficiencies.append({
                    'type': 'total_inefficiency',
                    'value_difference': total_range,
                    'best_over_line': {'bookmaker': best_over_book, 'value': totals[best_over_book]},
                    'best_under_line': {'bookmaker': best_under_book, 'value': totals[best_under_book]},
                    'opportunity': 'middle' if total_range >= 2.0 else 'line_shopping',
                    'confidence': 90 if total_range >= 2.0 else 75
                })

        return inefficiencies

    def _find_arbitrage_opportunities(self, bookmaker_data: Dict) -> List[Dict]:
        """Find arbitrage opportunities across bookmakers"""
        arbitrage_opportunities = []

        # This is a simplified arbitrage detection
        # In practice, would need more sophisticated calculations

        moneylines_home = {}
        moneylines_away = {}

        for bookmaker, data in bookmaker_data.items():
            markets = data.get('markets', {})

            if markets.get('moneyline_home') is not None:
                moneylines_home[bookmaker] = markets['moneyline_home']
            if markets.get('moneyline_away') is not None:
                moneylines_away[bookmaker] = markets['moneyline_away']

        if len(moneylines_home) >= 2 and len(moneylines_away) >= 2:
            best_home_odds = max(moneylines_home.values())
            best_away_odds = max(moneylines_away.values())

            best_home_book = max(moneylines_home, key=moneylines_home.get)
            best_away_book = max(moneylines_away, key=moneylines_away.get)

            # Convert American odds to implied probability
            home_prob = self._american_to_probability(best_home_odds)
            away_prob = self._american_to_probability(best_away_odds)

            total_prob = home_prob + away_prob

            if total_prob < 0.98:  # Arbitrage opportunity (accounting for vig)
                arbitrage_opportunities.append({
                    'type': 'moneyline_arbitrage',
                    'profit_margin': round((1 - total_prob) * 100, 2),
                    'home_bet': {
                        'bookmaker': best_home_book,
                        'odds': best_home_odds,
                        'implied_prob': round(home_prob * 100, 2)
                    },
                    'away_bet': {
                        'bookmaker': best_away_book,
                        'odds': best_away_odds,
                        'implied_prob': round(away_prob * 100, 2)
                    },
                    'confidence': 95
                })

        return arbitrage_opportunities

    def get_sharp_bettor_insights(self, game_id: str = None) -> Dict:
        """Get insights specifically for sharp bettors"""
        try:
            live_odds = self.get_live_odds_movements(game_id)

            sharp_insights = {
                'steam_moves': [],
                'reverse_line_movement': [],
                'low_hold_opportunities': [],
                'closing_line_value': [],
                'market_maker_moves': [],
                'syndicate_action': [],
                'recommendation': 'monitor'
            }

            for game in live_odds.get('games', []):
                # Extract steam moves
                for steam in game.get('line_movements', {}).get('steam_moves', []):
                    if steam.get('severity') == 'high':
                        sharp_insights['steam_moves'].append({
                            'game': f"{game['away_team']} @ {game['home_team']}",
                            'type': steam['type'],
                            'direction': steam['direction'],
                            'books_moved': steam['bookmaker_count'],
                            'action': 'follow' if steam['bookmaker_count'] >= 5 else 'monitor'
                        })

                # Identify low hold opportunities
                for inefficiency in game.get('market_inefficiencies', []):
                    if inefficiency.get('confidence', 0) >= 85:
                        sharp_insights['low_hold_opportunities'].append({
                            'game': f"{game['away_team']} @ {game['home_team']}",
                            'type': inefficiency['type'],
                            'opportunity': inefficiency['opportunity'],
                            'value_difference': inefficiency['value_difference'],
                            'confidence': inefficiency['confidence']
                        })

                # Market maker identification
                sharp_insights['market_maker_moves'].extend(
                    self._identify_market_maker_moves(game)
                )

            # Generate sharp betting recommendation
            sharp_insights['recommendation'] = self._generate_sharp_recommendation(sharp_insights)

            return sharp_insights

        except Exception as e:
            logger.error(f"❌ Error generating sharp bettor insights: {e}")
            return {}

    def _identify_market_maker_moves(self, game: Dict) -> List[Dict]:
        """Identify moves by market-making sportsbooks"""
        market_makers = ['Pinnacle', 'Bookmaker', 'CRIS']  # Known sharp books
        market_maker_moves = []

        for bookmaker_data in game.get('current_bookmakers', []):
            if bookmaker_data['name'] in market_makers:
                # Check if this book moved first or differently
                market_maker_moves.append({
                    'game': f"{game['away_team']} @ {game['home_team']}",
                    'bookmaker': bookmaker_data['name'],
                    'action': 'market_setting',
                    'significance': 'high'
                })

        return market_maker_moves

    def _generate_sharp_recommendation(self, sharp_insights: Dict) -> str:
        """Generate recommendation for sharp bettors"""
        steam_count = len(sharp_insights.get('steam_moves', []))
        inefficiency_count = len(sharp_insights.get('low_hold_opportunities', []))
        market_maker_count = len(sharp_insights.get('market_maker_moves', []))

        if steam_count >= 2 and inefficiency_count >= 1:
            return 'aggressive_action'
        elif steam_count >= 1 or inefficiency_count >= 2:
            return 'selective_action'
        elif market_maker_count >= 1:
            return 'follow_market_makers'
        else:
            return 'monitor_only'

    def start_live_monitoring(self, interval_seconds: int = 30):
        """Start live monitoring of odds movements"""
        self.is_monitoring = True

        def monitor_loop():
            while self.is_monitoring:
                try:
                    # Fetch live odds
                    live_data = self.get_live_odds_movements()

                    # Check for alerts
                    self._check_market_alerts(live_data)

                    # Sleep until next update
                    time.sleep(interval_seconds)

                except Exception as e:
                    logger.error(f"Error in live monitoring: {e}")
                    time.sleep(interval_seconds)

        # Start monitoring in separate thread
        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"📊 Started live odds monitoring (every {interval_seconds}s)")

    def stop_live_monitoring(self):
        """Stop live monitoring"""
        self.is_monitoring = False
        logger.info("🛑 Stopped live odds monitoring")

    def _check_market_alerts(self, live_data: Dict):
        """Check for market alert conditions"""
        for movement in live_data.get('significant_movements', []):
            if movement.get('impact') == 'very_high':
                alert = {
                    'type': 'significant_movement',
                    'message': movement.get('description'),
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'high'
                }
                self.market_alerts.append(alert)
                logger.warning(f"🚨 Market Alert: {alert['message']}")

    def get_market_alerts(self, since_timestamp: str = None) -> List[Dict]:
        """Get market alerts since timestamp"""
        if since_timestamp:
            since_dt = datetime.fromisoformat(since_timestamp)
            return [
                alert for alert in self.market_alerts
                if datetime.fromisoformat(alert['timestamp']) > since_dt
            ]
        return self.market_alerts

    # Utility methods
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median of a list"""
        if not values:
            return 0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        return sorted_values[n//2]

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / (len(values) - 1)

    def _american_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def _update_market_history(self, game_id: str, bookmaker_data: Dict, timestamp: datetime):
        """Update market history for tracking movements"""
        if game_id not in self.market_history:
            self.market_history[game_id] = []

        history_entry = {
            'timestamp': timestamp.isoformat(),
            'data': bookmaker_data
        }

        self.market_history[game_id].append(history_entry)

        # Keep only last 24 hours of data
        cutoff_time = timestamp - timedelta(hours=24)
        self.market_history[game_id] = [
            entry for entry in self.market_history[game_id]
            if datetime.fromisoformat(entry['timestamp']) > cutoff_time
        ]

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
live_betting_service = LiveBettingService()