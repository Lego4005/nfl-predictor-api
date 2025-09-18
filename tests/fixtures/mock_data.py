"""
Comprehensive Mock Data Generators for NFL Predictor Platform Tests
Provides realistic mock data for games, predictions, odds, users, and system metrics.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from enum import Enum
import uuid
import json


class GameStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    HALFTIME = "halftime"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class BetType(Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PROP = "prop"


class UserRole(Enum):
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


@dataclass
class NFLTeam:
    """NFL Team data structure"""
    id: str
    name: str
    city: str
    abbreviation: str
    conference: str
    division: str
    logo_url: str


class MockDataGenerator:
    """Comprehensive mock data generator for NFL Predictor Platform"""

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional random seed for reproducible data"""
        if seed:
            random.seed(seed)
            np.random.seed(seed)

        self.nfl_teams = self._create_nfl_teams()
        self.sportsbooks = [
            "DraftKings", "FanDuel", "BetMGM", "Caesars", "PointsBet",
            "WynnBET", "Barstool", "FOX Bet", "BetRivers", "Unibet"
        ]

    def _create_nfl_teams(self) -> List[NFLTeam]:
        """Create comprehensive NFL team data"""
        teams_data = [
            # AFC East
            ("bills", "Buffalo Bills", "Buffalo", "BUF", "AFC", "East"),
            ("dolphins", "Miami Dolphins", "Miami", "MIA", "AFC", "East"),
            ("patriots", "New England Patriots", "New England", "NE", "AFC", "East"),
            ("jets", "New York Jets", "New York", "NYJ", "AFC", "East"),

            # AFC North
            ("ravens", "Baltimore Ravens", "Baltimore", "BAL", "AFC", "North"),
            ("bengals", "Cincinnati Bengals", "Cincinnati", "CIN", "AFC", "North"),
            ("browns", "Cleveland Browns", "Cleveland", "CLE", "AFC", "North"),
            ("steelers", "Pittsburgh Steelers", "Pittsburgh", "PIT", "AFC", "North"),

            # AFC South
            ("texans", "Houston Texans", "Houston", "HOU", "AFC", "South"),
            ("colts", "Indianapolis Colts", "Indianapolis", "IND", "AFC", "South"),
            ("jaguars", "Jacksonville Jaguars", "Jacksonville", "JAX", "AFC", "South"),
            ("titans", "Tennessee Titans", "Tennessee", "TEN", "AFC", "South"),

            # AFC West
            ("broncos", "Denver Broncos", "Denver", "DEN", "AFC", "West"),
            ("chiefs", "Kansas City Chiefs", "Kansas City", "KC", "AFC", "West"),
            ("raiders", "Las Vegas Raiders", "Las Vegas", "LV", "AFC", "West"),
            ("chargers", "Los Angeles Chargers", "Los Angeles", "LAC", "AFC", "West"),

            # NFC East
            ("cowboys", "Dallas Cowboys", "Dallas", "DAL", "NFC", "East"),
            ("giants", "New York Giants", "New York", "NYG", "NFC", "East"),
            ("eagles", "Philadelphia Eagles", "Philadelphia", "PHI", "NFC", "East"),
            ("commanders", "Washington Commanders", "Washington", "WAS", "NFC", "East"),

            # NFC North
            ("bears", "Chicago Bears", "Chicago", "CHI", "NFC", "North"),
            ("lions", "Detroit Lions", "Detroit", "DET", "NFC", "North"),
            ("packers", "Green Bay Packers", "Green Bay", "GB", "NFC", "North"),
            ("vikings", "Minnesota Vikings", "Minnesota", "MIN", "NFC", "North"),

            # NFC South
            ("falcons", "Atlanta Falcons", "Atlanta", "ATL", "NFC", "South"),
            ("panthers", "Carolina Panthers", "Carolina", "CAR", "NFC", "South"),
            ("saints", "New Orleans Saints", "New Orleans", "NO", "NFC", "South"),
            ("buccaneers", "Tampa Bay Buccaneers", "Tampa Bay", "TB", "NFC", "South"),

            # NFC West
            ("cardinals", "Arizona Cardinals", "Arizona", "ARI", "NFC", "West"),
            ("rams", "Los Angeles Rams", "Los Angeles", "LAR", "NFC", "West"),
            ("seahawks", "Seattle Seahawks", "Seattle", "SEA", "NFC", "West"),
            ("49ers", "San Francisco 49ers", "San Francisco", "SF", "NFC", "West")
        ]

        teams = []
        for team_id, name, city, abbr, conf, div in teams_data:
            teams.append(NFLTeam(
                id=team_id,
                name=name,
                city=city,
                abbreviation=abbr,
                conference=conf,
                division=div,
                logo_url=f"https://static.nfl.com/logos/teams/{abbr}.png"
            ))

        return teams

    def generate_game_data(self, num_games: int = 16) -> List[Dict[str, Any]]:
        """Generate realistic NFL game data"""
        games = []
        current_date = datetime.utcnow()

        for i in range(num_games):
            home_team = random.choice(self.nfl_teams)
            away_team = random.choice([t for t in self.nfl_teams if t.id != home_team.id])

            # Schedule games over next few days
            game_time = current_date + timedelta(
                days=random.randint(0, 14),
                hours=random.choice([13, 16, 20]),  # 1 PM, 4 PM, 8 PM ET
                minutes=random.choice([0, 30])
            )

            game_status = random.choice(list(GameStatus))

            # Generate realistic scores based on game status
            if game_status in [GameStatus.FINAL, GameStatus.IN_PROGRESS, GameStatus.HALFTIME]:
                home_score = random.randint(0, 45)
                away_score = random.randint(0, 45)
                quarter = random.randint(1, 4) if game_status == GameStatus.IN_PROGRESS else 4
                time_remaining = f"{random.randint(0, 15):02d}:{random.randint(0, 59):02d}" if game_status == GameStatus.IN_PROGRESS else "0:00"
            else:
                home_score = 0
                away_score = 0
                quarter = 1
                time_remaining = "15:00"

            game = {
                'game_id': f'nfl_2024_week_{random.randint(1, 18)}_{home_team.id}_{away_team.id}',
                'home_team': {
                    'id': home_team.id,
                    'name': home_team.name,
                    'abbreviation': home_team.abbreviation,
                    'city': home_team.city,
                    'logo_url': home_team.logo_url
                },
                'away_team': {
                    'id': away_team.id,
                    'name': away_team.name,
                    'abbreviation': away_team.abbreviation,
                    'city': away_team.city,
                    'logo_url': away_team.logo_url
                },
                'start_time': game_time.isoformat(),
                'game_status': game_status.value,
                'home_score': home_score,
                'away_score': away_score,
                'quarter': quarter,
                'time_remaining': time_remaining,
                'week': random.randint(1, 18),
                'season': 2024,
                'weather': self._generate_weather_data(),
                'venue': f"{home_team.city} Stadium",
                'broadcast': random.choice(['CBS', 'FOX', 'NBC', 'ESPN', 'Prime Video']),
                'is_divisional': home_team.division == away_team.division,
                'is_conference': home_team.conference == away_team.conference
            }

            games.append(game)

        return games

    def _generate_weather_data(self) -> Dict[str, Any]:
        """Generate realistic weather data for games"""
        weather_conditions = ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Rain', 'Snow', 'Windy']

        return {
            'temperature': random.randint(25, 85),  # Fahrenheit
            'conditions': random.choice(weather_conditions),
            'wind_speed': random.randint(0, 25),  # mph
            'wind_direction': random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
            'humidity': random.randint(30, 90),  # percentage
            'precipitation_chance': random.randint(0, 100)  # percentage
        }

    def generate_prediction_data(self, games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic ML prediction data for games"""
        predictions = []

        for game in games:
            # Generate realistic probabilities that sum to 1
            base_prob = 0.5 + random.uniform(-0.15, 0.15)  # 35% to 65% range
            home_win_prob = max(0.1, min(0.9, base_prob))
            away_win_prob = 1.0 - home_win_prob

            # Generate confidence level based on probability spread
            prob_spread = abs(home_win_prob - away_win_prob)
            confidence = 0.5 + (prob_spread * 0.5)  # Higher confidence when more certain

            prediction = {
                'game_id': game['game_id'],
                'model_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                'home_win_probability': round(home_win_prob, 4),
                'away_win_probability': round(away_win_prob, 4),
                'predicted_spread': round(random.uniform(-14, 14), 1),
                'predicted_total': round(random.uniform(35, 65), 1),
                'confidence_level': round(confidence, 4),
                'last_updated': datetime.utcnow().isoformat(),
                'factors': {
                    'home_field_advantage': round(random.uniform(0.02, 0.08), 3),
                    'recent_form': round(random.uniform(-0.1, 0.1), 3),
                    'head_to_head': round(random.uniform(-0.05, 0.05), 3),
                    'injury_impact': round(random.uniform(-0.08, 0.08), 3),
                    'weather_impact': round(random.uniform(-0.03, 0.03), 3)
                },
                'feature_importance': {
                    'offensive_rating': round(random.uniform(0.15, 0.25), 3),
                    'defensive_rating': round(random.uniform(0.15, 0.25), 3),
                    'recent_performance': round(random.uniform(0.10, 0.20), 3),
                    'coaching': round(random.uniform(0.05, 0.15), 3),
                    'injuries': round(random.uniform(0.05, 0.15), 3),
                    'weather': round(random.uniform(0.02, 0.08), 3),
                    'motivation': round(random.uniform(0.02, 0.08), 3),
                    'travel': round(random.uniform(0.01, 0.05), 3)
                }
            }

            predictions.append(prediction)

        return predictions

    def generate_odds_data(self, games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic sportsbook odds data"""
        all_odds = []

        for game in games:
            # Generate odds for each sportsbook
            for sportsbook in self.sportsbooks:
                # Base spread and total
                base_spread = random.uniform(-14, 14)
                base_total = random.uniform(35, 65)

                # Add sportsbook-specific variance
                spread_variance = random.uniform(-0.5, 0.5)
                total_variance = random.uniform(-2, 2)

                spread = round(base_spread + spread_variance, 1)
                total = round(base_total + total_variance, 1)

                # Generate moneylines based on spread
                if spread > 0:  # Away team favored
                    home_moneyline = self._spread_to_moneyline(-abs(spread))
                    away_moneyline = self._spread_to_moneyline(abs(spread))
                else:  # Home team favored
                    home_moneyline = self._spread_to_moneyline(abs(spread))
                    away_moneyline = self._spread_to_moneyline(-abs(spread))

                odds = {
                    'game_id': game['game_id'],
                    'sportsbook': sportsbook,
                    'timestamp': datetime.utcnow().isoformat(),
                    'spread': {
                        'home': spread,
                        'away': -spread,
                        'home_odds': random.choice([-105, -110, -115, -120]),
                        'away_odds': random.choice([-105, -110, -115, -120])
                    },
                    'moneyline': {
                        'home': home_moneyline,
                        'away': away_moneyline
                    },
                    'total': {
                        'over': total,
                        'under': total,
                        'over_odds': random.choice([-105, -110, -115, -120]),
                        'under_odds': random.choice([-105, -110, -115, -120])
                    }
                }

                all_odds.append(odds)

        return all_odds

    def _spread_to_moneyline(self, spread: float) -> int:
        """Convert point spread to approximate moneyline"""
        # Simplified conversion formula
        if spread >= 0:
            # Underdog
            return int(100 + (spread * 20))
        else:
            # Favorite
            return int(-100 - (abs(spread) * 25))

    def generate_user_data(self, num_users: int = 100) -> List[Dict[str, Any]]:
        """Generate realistic user data"""
        users = []

        first_names = ['John', 'Sarah', 'Mike', 'Emily', 'David', 'Lisa', 'Chris', 'Anna', 'Tom', 'Maria']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

        for i in range(num_users):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            user = {
                'user_id': str(uuid.uuid4()),
                'username': f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}",
                'email': f"{first_name.lower()}.{last_name.lower()}@example.com",
                'first_name': first_name,
                'last_name': last_name,
                'role': random.choice(list(UserRole)).value,
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                'last_login': (datetime.utcnow() - timedelta(hours=random.randint(1, 168))).isoformat(),
                'preferences': {
                    'favorite_teams': random.sample([team.abbreviation for team in self.nfl_teams], random.randint(1, 3)),
                    'notification_settings': {
                        'email': random.choice([True, False]),
                        'push': random.choice([True, False]),
                        'sms': random.choice([True, False])
                    },
                    'betting_preferences': {
                        'risk_tolerance': random.choice(['low', 'medium', 'high']),
                        'max_bet_amount': random.randint(25, 500),
                        'preferred_bet_types': random.sample(
                            [bt.value for bt in BetType],
                            random.randint(1, len(BetType))
                        )
                    }
                },
                'subscription': {
                    'type': random.choice(['free', 'premium', 'pro']),
                    'expires_at': (datetime.utcnow() + timedelta(days=random.randint(1, 365))).isoformat() if random.choice([True, False]) else None,
                    'auto_renew': random.choice([True, False])
                },
                'statistics': {
                    'total_bets': random.randint(0, 1000),
                    'winning_bets': random.randint(0, 500),
                    'total_wagered': round(random.uniform(0, 50000), 2),
                    'total_winnings': round(random.uniform(0, 60000), 2),
                    'current_streak': random.randint(-10, 15),
                    'best_streak': random.randint(1, 20),
                    'worst_streak': random.randint(-20, -1)
                }
            }

            users.append(user)

        return users

    def generate_bet_history(self, user_id: str, num_bets: int = 50) -> List[Dict[str, Any]]:
        """Generate realistic betting history for a user"""
        bet_history = []

        for i in range(num_bets):
            bet_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
            bet_type = random.choice(list(BetType))
            amount = round(random.uniform(10, 500), 2)
            odds = random.randint(-300, 300)

            # Determine result based on realistic win rate (~45%)
            result = random.choices(['win', 'loss', 'push'], weights=[45, 50, 5])[0]

            if result == 'win':
                if odds > 0:
                    payout = amount * (odds / 100)
                else:
                    payout = amount * (100 / abs(odds))
                payout += amount  # Include original stake
            elif result == 'push':
                payout = amount  # Return stake
            else:
                payout = 0

            bet = {
                'bet_id': str(uuid.uuid4()),
                'user_id': user_id,
                'game_id': f'nfl_2024_week_{random.randint(1, 18)}_game_{random.randint(1, 16)}',
                'bet_type': bet_type.value,
                'amount': amount,
                'odds': odds,
                'placed_at': bet_date.isoformat(),
                'settled_at': (bet_date + timedelta(hours=random.randint(2, 6))).isoformat() if result != 'pending' else None,
                'result': result,
                'payout': round(payout, 2),
                'profit_loss': round(payout - amount, 2),
                'sportsbook': random.choice(self.sportsbooks),
                'details': {
                    'selection': random.choice(['home', 'away', 'over', 'under']),
                    'line': round(random.uniform(-14, 14), 1) if bet_type == BetType.SPREAD else round(random.uniform(35, 65), 1),
                    'confidence': round(random.uniform(0.5, 0.9), 2)
                }
            }

            bet_history.append(bet)

        return bet_history

    def generate_system_health_data(self) -> Dict[str, Any]:
        """Generate realistic system health metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'status': random.choice(['healthy', 'warning', 'error']),
            'uptime_seconds': random.randint(3600, 2592000),  # 1 hour to 30 days
            'api': {
                'status': 'healthy',
                'response_time_ms': random.randint(50, 500),
                'requests_per_second': random.randint(100, 2000),
                'error_rate': round(random.uniform(0, 5), 2)
            },
            'database': {
                'status': random.choice(['healthy', 'warning']),
                'connections': random.randint(10, 100),
                'query_time_ms': random.randint(5, 100),
                'cpu_usage': round(random.uniform(10, 80), 1),
                'memory_usage': round(random.uniform(40, 90), 1)
            },
            'websocket': {
                'status': 'healthy',
                'active_connections': random.randint(50, 1000),
                'messages_per_second': random.randint(10, 500),
                'connection_errors': random.randint(0, 10)
            },
            'ml_models': {
                'status': 'healthy',
                'last_training': (datetime.utcnow() - timedelta(hours=random.randint(1, 24))).isoformat(),
                'accuracy': round(random.uniform(0.55, 0.75), 3),
                'predictions_per_hour': random.randint(100, 1000)
            },
            'cache': {
                'status': 'healthy',
                'hit_rate': round(random.uniform(0.8, 0.95), 3),
                'memory_usage': round(random.uniform(30, 80), 1),
                'keys_count': random.randint(1000, 10000)
            },
            'queue': {
                'status': 'healthy',
                'pending_jobs': random.randint(0, 100),
                'processing_rate': random.randint(10, 100),
                'failed_jobs': random.randint(0, 5)
            }
        }

    def generate_analytics_data(self, days: int = 30) -> Dict[str, Any]:
        """Generate analytics data for dashboard"""
        dates = [(datetime.utcnow() - timedelta(days=i)) for i in range(days)]
        dates.reverse()

        # Generate time series data
        daily_users = []
        daily_predictions = []
        daily_accuracy = []

        for date in dates:
            daily_users.append({
                'date': date.date().isoformat(),
                'active_users': random.randint(500, 2000),
                'new_users': random.randint(10, 100),
                'premium_users': random.randint(100, 500)
            })

            daily_predictions.append({
                'date': date.date().isoformat(),
                'total_predictions': random.randint(100, 500),
                'successful_predictions': random.randint(55, 350),
                'accuracy_rate': round(random.uniform(0.52, 0.68), 3)
            })

            daily_accuracy.append({
                'date': date.date().isoformat(),
                'model_accuracy': round(random.uniform(0.55, 0.70), 3),
                'spread_accuracy': round(random.uniform(0.48, 0.58), 3),
                'total_accuracy': round(random.uniform(0.50, 0.65), 3)
            })

        return {
            'daily_users': daily_users,
            'daily_predictions': daily_predictions,
            'daily_accuracy': daily_accuracy,
            'summary': {
                'total_active_users': sum(d['active_users'] for d in daily_users[-7:]),  # Last 7 days
                'total_predictions': sum(d['total_predictions'] for d in daily_predictions[-7:]),
                'average_accuracy': np.mean([d['model_accuracy'] for d in daily_accuracy[-7:]]),
                'user_growth_rate': round(random.uniform(-5, 15), 2),  # Percentage
                'revenue': round(random.uniform(10000, 50000), 2)
            }
        }

    def generate_websocket_test_data(self) -> List[Dict[str, Any]]:
        """Generate WebSocket test messages"""
        event_types = [
            'game_update', 'prediction_update', 'odds_update',
            'score_update', 'notification', 'system_alert'
        ]

        messages = []
        for i in range(10):
            event_type = random.choice(event_types)

            if event_type == 'game_update':
                data = {
                    'game_id': f'test_game_{i}',
                    'home_score': random.randint(0, 35),
                    'away_score': random.randint(0, 35),
                    'quarter': random.randint(1, 4),
                    'time_remaining': f"{random.randint(0, 15):02d}:{random.randint(0, 59):02d}"
                }
            elif event_type == 'prediction_update':
                data = {
                    'game_id': f'test_game_{i}',
                    'home_win_probability': round(random.uniform(0.3, 0.7), 3),
                    'away_win_probability': round(random.uniform(0.3, 0.7), 3),
                    'confidence': round(random.uniform(0.6, 0.9), 3)
                }
            elif event_type == 'odds_update':
                data = {
                    'game_id': f'test_game_{i}',
                    'sportsbook': random.choice(self.sportsbooks),
                    'spread': round(random.uniform(-14, 14), 1),
                    'moneyline_home': random.randint(-300, 300),
                    'moneyline_away': random.randint(-300, 300)
                }
            else:
                data = {
                    'message': f'Test {event_type} message {i}',
                    'level': random.choice(['info', 'warning', 'error']),
                    'timestamp': datetime.utcnow().isoformat()
                }

            message = {
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': str(uuid.uuid4())
            }

            messages.append(message)

        return messages


# Convenience functions for quick data generation
def quick_game_data(count: int = 16, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Quick function to generate game data"""
    generator = MockDataGenerator(seed=seed)
    return generator.generate_game_data(count)


def quick_prediction_data(games: List[Dict[str, Any]], seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Quick function to generate prediction data"""
    generator = MockDataGenerator(seed=seed)
    return generator.generate_prediction_data(games)


def quick_odds_data(games: List[Dict[str, Any]], seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Quick function to generate odds data"""
    generator = MockDataGenerator(seed=seed)
    return generator.generate_odds_data(games)


def quick_user_data(count: int = 10, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Quick function to generate user data"""
    generator = MockDataGenerator(seed=seed)
    return generator.generate_user_data(count)


if __name__ == "__main__":
    # Example usage
    generator = MockDataGenerator(seed=42)

    # Generate sample data
    games = generator.generate_game_data(5)
    predictions = generator.generate_prediction_data(games)
    odds = generator.generate_odds_data(games)
    users = generator.generate_user_data(3)

    print("Generated sample data:")
    print(f"Games: {len(games)}")
    print(f"Predictions: {len(predictions)}")
    print(f"Odds entries: {len(odds)}")
    print(f"Users: {len(users)}")

    # Save to files for inspection
    with open('/tmp/sample_games.json', 'w') as f:
        json.dump(games, f, indent=2)

    with open('/tmp/sample_predictions.json', 'w') as f:
        json.dump(predictions, f, indent=2)

    print("Sample data saved to /tmp/sample_*.json files")