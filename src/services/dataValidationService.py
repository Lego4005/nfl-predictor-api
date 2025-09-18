"""
Data Validation Service
Validates premium data quality, consistency, and reliability across all sources
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DataValidationService:
    """Validates premium data quality and consistency"""

    def __init__(self):
        # Validation thresholds
        self.validation_rules = {
            'odds': {
                'spread_range': {'min': -30, 'max': 30},
                'total_range': {'min': 20, 'max': 80},
                'moneyline_range': {'min': -2000, 'max': 2000},
                'max_bookmaker_variance': {'spread': 3.0, 'total': 5.0, 'moneyline': 200}
            },
            'player_props': {
                'passing_yards_range': {'min': 0, 'max': 600},
                'rushing_yards_range': {'min': 0, 'max': 300},
                'receiving_yards_range': {'min': 0, 'max': 300},
                'touchdowns_range': {'min': 0, 'max': 6},
                'completions_range': {'min': 0, 'max': 50}
            },
            'analytics': {
                'epa_range': {'min': -1.0, 'max': 1.0},
                'dvoa_range': {'min': -100, 'max': 100},
                'success_rate_range': {'min': 0, 'max': 1.0},
                'win_probability_range': {'min': 0, 'max': 100}
            },
            'game_feed': {
                'score_range': {'min': 0, 'max': 70},
                'quarter_range': {'min': 1, 'max': 5},  # Including OT
                'yard_line_range': {'min': 0, 'max': 100},
                'down_range': {'min': 1, 'max': 4}
            }
        }

        # Data quality metrics
        self.quality_metrics = {
            'completeness': 0.0,
            'accuracy': 0.0,
            'consistency': 0.0,
            'timeliness': 0.0,
            'reliability': 0.0
        }

        # Error tracking
        self.validation_errors = []
        self.data_anomalies = []
        self.quality_alerts = []

        logger.info("🔍 Data Validation Service initialized")

    def validate_odds_data(self, odds_data: List[Dict]) -> Dict:
        """Validate odds data quality and consistency"""
        validation_result = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'quality_score': 0.0,
            'metrics': {
                'total_games': len(odds_data),
                'valid_games': 0,
                'invalid_games': 0,
                'bookmaker_coverage': {},
                'line_consistency': {}
            },
            'recommendations': []
        }

        if not odds_data:
            validation_result['status'] = 'failed'
            validation_result['errors'].append('No odds data provided')
            return validation_result

        for game in odds_data:
            game_validation = self._validate_single_game_odds(game)

            if game_validation['is_valid']:
                validation_result['metrics']['valid_games'] += 1
            else:
                validation_result['metrics']['invalid_games'] += 1
                validation_result['errors'].extend(game_validation['errors'])

            validation_result['warnings'].extend(game_validation['warnings'])

        # Calculate overall quality score
        validation_result['quality_score'] = self._calculate_odds_quality_score(validation_result)

        # Generate recommendations
        validation_result['recommendations'] = self._generate_odds_recommendations(validation_result)

        # Update overall status
        if validation_result['metrics']['invalid_games'] > len(odds_data) * 0.1:  # >10% invalid
            validation_result['status'] = 'failed'
        elif validation_result['warnings']:
            validation_result['status'] = 'warning'

        return validation_result

    def _validate_single_game_odds(self, game: Dict) -> Dict:
        """Validate a single game's odds data"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        game_id = game.get('id', 'unknown')

        # Check required fields
        required_fields = ['id', 'home_team', 'away_team', 'bookmakers']
        for field in required_fields:
            if field not in game:
                result['errors'].append(f"Game {game_id}: Missing required field '{field}'")
                result['is_valid'] = False

        # Validate bookmaker data
        bookmakers = game.get('bookmakers', [])
        if not bookmakers:
            result['errors'].append(f"Game {game_id}: No bookmaker data")
            result['is_valid'] = False
        else:
            for bookmaker in bookmakers:
                bookmaker_validation = self._validate_bookmaker_odds(bookmaker, game_id)
                result['errors'].extend(bookmaker_validation['errors'])
                result['warnings'].extend(bookmaker_validation['warnings'])
                if not bookmaker_validation['is_valid']:
                    result['is_valid'] = False

        # Check odds consistency across bookmakers
        if len(bookmakers) > 1:
            consistency_check = self._check_odds_consistency(bookmakers, game_id)
            result['warnings'].extend(consistency_check['warnings'])

        return result

    def _validate_bookmaker_odds(self, bookmaker: Dict, game_id: str) -> Dict:
        """Validate odds from a single bookmaker"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        bookmaker_name = bookmaker.get('title', 'unknown')
        markets = bookmaker.get('markets', [])

        if not markets:
            result['errors'].append(f"Game {game_id}, Bookmaker {bookmaker_name}: No market data")
            result['is_valid'] = False
            return result

        for market in markets:
            market_key = market.get('key')
            outcomes = market.get('outcomes', [])

            if market_key == 'spreads':
                spread_validation = self._validate_spread_odds(outcomes, game_id, bookmaker_name)
                result['errors'].extend(spread_validation['errors'])
                result['warnings'].extend(spread_validation['warnings'])
                if not spread_validation['is_valid']:
                    result['is_valid'] = False

            elif market_key == 'totals':
                total_validation = self._validate_total_odds(outcomes, game_id, bookmaker_name)
                result['errors'].extend(total_validation['errors'])
                result['warnings'].extend(total_validation['warnings'])
                if not total_validation['is_valid']:
                    result['is_valid'] = False

            elif market_key == 'h2h':
                ml_validation = self._validate_moneyline_odds(outcomes, game_id, bookmaker_name)
                result['errors'].extend(ml_validation['errors'])
                result['warnings'].extend(ml_validation['warnings'])
                if not ml_validation['is_valid']:
                    result['is_valid'] = False

        return result

    def _validate_spread_odds(self, outcomes: List[Dict], game_id: str, bookmaker: str) -> Dict:
        """Validate spread odds"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}

        if len(outcomes) != 2:
            result['errors'].append(f"Game {game_id}, {bookmaker}: Spread should have 2 outcomes, got {len(outcomes)}")
            result['is_valid'] = False
            return result

        spreads = [outcome.get('point') for outcome in outcomes if outcome.get('point') is not None]

        if len(spreads) != 2:
            result['errors'].append(f"Game {game_id}, {bookmaker}: Invalid spread points")
            result['is_valid'] = False
            return result

        # Check spread range
        for spread in spreads:
            if not (self.validation_rules['odds']['spread_range']['min'] <= spread <=
                   self.validation_rules['odds']['spread_range']['max']):
                result['warnings'].append(f"Game {game_id}, {bookmaker}: Spread {spread} outside normal range")

        # Check if spreads are opposite
        if abs(spreads[0] + spreads[1]) > 0.1:  # Allow small floating point errors
            result['warnings'].append(f"Game {game_id}, {bookmaker}: Spreads not opposite: {spreads}")

        return result

    def _validate_total_odds(self, outcomes: List[Dict], game_id: str, bookmaker: str) -> Dict:
        """Validate total (over/under) odds"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}

        if len(outcomes) != 2:
            result['errors'].append(f"Game {game_id}, {bookmaker}: Total should have 2 outcomes, got {len(outcomes)}")
            result['is_valid'] = False
            return result

        totals = [outcome.get('point') for outcome in outcomes if outcome.get('point') is not None]

        if len(totals) != 2:
            result['errors'].append(f"Game {game_id}, {bookmaker}: Invalid total points")
            result['is_valid'] = False
            return result

        # Check total range
        total_value = totals[0]  # Should be same for over and under
        if not (self.validation_rules['odds']['total_range']['min'] <= total_value <=
               self.validation_rules['odds']['total_range']['max']):
            result['warnings'].append(f"Game {game_id}, {bookmaker}: Total {total_value} outside normal range")

        # Check if both totals are the same
        if abs(totals[0] - totals[1]) > 0.1:
            result['warnings'].append(f"Game {game_id}, {bookmaker}: Over/Under totals differ: {totals}")

        return result

    def _validate_moneyline_odds(self, outcomes: List[Dict], game_id: str, bookmaker: str) -> Dict:
        """Validate moneyline odds"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}

        if len(outcomes) != 2:
            result['errors'].append(f"Game {game_id}, {bookmaker}: Moneyline should have 2 outcomes, got {len(outcomes)}")
            result['is_valid'] = False
            return result

        odds = [outcome.get('price') for outcome in outcomes if outcome.get('price') is not None]

        if len(odds) != 2:
            result['errors'].append(f"Game {game_id}, {bookmaker}: Invalid moneyline odds")
            result['is_valid'] = False
            return result

        # Check moneyline range
        for odd in odds:
            if not (self.validation_rules['odds']['moneyline_range']['min'] <= odd <=
                   self.validation_rules['odds']['moneyline_range']['max']):
                result['warnings'].append(f"Game {game_id}, {bookmaker}: Moneyline {odd} outside normal range")

        # Check implied probability sum (should be > 100% due to vig)
        implied_probs = [self._odds_to_probability(odd) for odd in odds]
        total_prob = sum(implied_probs)

        if total_prob < 95:  # Too low, possible error
            result['warnings'].append(f"Game {game_id}, {bookmaker}: Implied probability sum too low: {total_prob:.1f}%")
        elif total_prob > 120:  # Too high vig
            result['warnings'].append(f"Game {game_id}, {bookmaker}: Very high vig: {total_prob:.1f}%")

        return result

    def _check_odds_consistency(self, bookmakers: List[Dict], game_id: str) -> Dict:
        """Check consistency across bookmakers"""
        result = {'warnings': []}

        # Collect all spreads, totals, and moneylines
        spreads = []
        totals = []
        moneylines = []

        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('point') is not None:
                            spreads.append(abs(outcome['point']))  # Use absolute value
                elif market['key'] == 'totals':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('point') is not None:
                            totals.append(outcome['point'])
                            break  # Only need one total value
                elif market['key'] == 'h2h':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('price') is not None:
                            moneylines.append(outcome['price'])

        # Check variance
        if len(spreads) > 1:
            spread_variance = max(spreads) - min(spreads)
            if spread_variance > self.validation_rules['odds']['max_bookmaker_variance']['spread']:
                result['warnings'].append(f"Game {game_id}: High spread variance: {spread_variance}")

        if len(totals) > 1:
            total_variance = max(totals) - min(totals)
            if total_variance > self.validation_rules['odds']['max_bookmaker_variance']['total']:
                result['warnings'].append(f"Game {game_id}: High total variance: {total_variance}")

        return result

    def validate_player_props_data(self, props_data: Dict) -> Dict:
        """Validate player props data"""
        validation_result = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'quality_score': 0.0,
            'metrics': {
                'total_players': 0,
                'valid_players': 0,
                'invalid_players': 0,
                'position_coverage': {},
                'projection_accuracy': {}
            },
            'recommendations': []
        }

        # Validate each position group
        for position in ['quarterbacks', 'running_backs', 'receivers']:
            players = props_data.get(position, [])
            validation_result['metrics']['total_players'] += len(players)

            for player in players:
                player_validation = self._validate_player_props(player, position)

                if player_validation['is_valid']:
                    validation_result['metrics']['valid_players'] += 1
                else:
                    validation_result['metrics']['invalid_players'] += 1
                    validation_result['errors'].extend(player_validation['errors'])

                validation_result['warnings'].extend(player_validation['warnings'])

        # Calculate quality score
        validation_result['quality_score'] = self._calculate_props_quality_score(validation_result)

        # Generate recommendations
        validation_result['recommendations'] = self._generate_props_recommendations(validation_result)

        return validation_result

    def _validate_player_props(self, player: Dict, position: str) -> Dict:
        """Validate individual player props"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}

        player_name = player.get('player_name', 'unknown')

        # Check required fields
        required_fields = ['player_name', 'team', 'position']
        for field in required_fields:
            if field not in player:
                result['errors'].append(f"Player {player_name}: Missing field '{field}'")
                result['is_valid'] = False

        # Position-specific validations
        if position == 'quarterbacks':
            result = self._validate_qb_props(player, result)
        elif position == 'running_backs':
            result = self._validate_rb_props(player, result)
        elif position == 'receivers':
            result = self._validate_wr_props(player, result)

        return result

    def _validate_qb_props(self, player: Dict, result: Dict) -> Dict:
        """Validate QB-specific props"""
        player_name = player.get('player_name', 'unknown')

        # Validate passing yards
        passing_yards = player.get('passing_yards')
        if passing_yards is not None:
            min_val = self.validation_rules['player_props']['passing_yards_range']['min']
            max_val = self.validation_rules['player_props']['passing_yards_range']['max']
            if not (min_val <= passing_yards <= max_val):
                result['warnings'].append(f"QB {player_name}: Passing yards {passing_yards} outside range {min_val}-{max_val}")

        # Validate passing touchdowns
        passing_tds = player.get('passing_touchdowns')
        if passing_tds is not None:
            min_val = self.validation_rules['player_props']['touchdowns_range']['min']
            max_val = self.validation_rules['player_props']['touchdowns_range']['max']
            if not (min_val <= passing_tds <= max_val):
                result['warnings'].append(f"QB {player_name}: Passing TDs {passing_tds} outside range {min_val}-{max_val}")

        # Validate completions
        completions = player.get('passing_completions')
        if completions is not None:
            min_val = self.validation_rules['player_props']['completions_range']['min']
            max_val = self.validation_rules['player_props']['completions_range']['max']
            if not (min_val <= completions <= max_val):
                result['warnings'].append(f"QB {player_name}: Completions {completions} outside range {min_val}-{max_val}")

        return result

    def _validate_rb_props(self, player: Dict, result: Dict) -> Dict:
        """Validate RB-specific props"""
        player_name = player.get('player_name', 'unknown')

        # Validate rushing yards
        rushing_yards = player.get('rushing_yards')
        if rushing_yards is not None:
            min_val = self.validation_rules['player_props']['rushing_yards_range']['min']
            max_val = self.validation_rules['player_props']['rushing_yards_range']['max']
            if not (min_val <= rushing_yards <= max_val):
                result['warnings'].append(f"RB {player_name}: Rushing yards {rushing_yards} outside range {min_val}-{max_val}")

        return result

    def _validate_wr_props(self, player: Dict, result: Dict) -> Dict:
        """Validate WR/TE-specific props"""
        player_name = player.get('player_name', 'unknown')

        # Validate receiving yards
        receiving_yards = player.get('receiving_yards')
        if receiving_yards is not None:
            min_val = self.validation_rules['player_props']['receiving_yards_range']['min']
            max_val = self.validation_rules['player_props']['receiving_yards_range']['max']
            if not (min_val <= receiving_yards <= max_val):
                result['warnings'].append(f"WR/TE {player_name}: Receiving yards {receiving_yards} outside range {min_val}-{max_val}")

        return result

    def validate_analytics_data(self, analytics_data: Dict) -> Dict:
        """Validate advanced analytics data"""
        validation_result = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'quality_score': 0.0,
            'metrics': {
                'epa_metrics_valid': 0,
                'dvoa_metrics_valid': 0,
                'success_rates_valid': 0,
                'consistency_score': 0.0
            },
            'recommendations': []
        }

        # Validate EPA data
        if 'offensive_epa_per_play' in analytics_data:
            epa_val = analytics_data['offensive_epa_per_play']
            if not self._is_in_range(epa_val, self.validation_rules['analytics']['epa_range']):
                validation_result['warnings'].append(f"EPA value {epa_val} outside normal range")
            else:
                validation_result['metrics']['epa_metrics_valid'] += 1

        # Validate DVOA data
        if 'total_dvoa' in analytics_data:
            dvoa_val = analytics_data['total_dvoa']
            if not self._is_in_range(dvoa_val, self.validation_rules['analytics']['dvoa_range']):
                validation_result['warnings'].append(f"DVOA value {dvoa_val} outside normal range")
            else:
                validation_result['metrics']['dvoa_metrics_valid'] += 1

        # Validate success rates
        if 'overall_success_rate' in analytics_data:
            success_val = analytics_data['overall_success_rate']
            if not self._is_in_range(success_val, self.validation_rules['analytics']['success_rate_range']):
                validation_result['warnings'].append(f"Success rate {success_val} outside normal range")
            else:
                validation_result['metrics']['success_rates_valid'] += 1

        # Calculate quality score
        validation_result['quality_score'] = self._calculate_analytics_quality_score(validation_result)

        return validation_result

    def validate_game_feed_data(self, game_feed: Dict) -> Dict:
        """Validate real-time game feed data"""
        validation_result = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'quality_score': 0.0,
            'metrics': {
                'required_fields_present': 0,
                'valid_game_state': True,
                'data_freshness': 'unknown'
            },
            'recommendations': []
        }

        # Check required fields
        required_fields = ['game_id', 'home_team', 'away_team', 'home_score', 'away_score', 'quarter']
        for field in required_fields:
            if field in game_feed:
                validation_result['metrics']['required_fields_present'] += 1
            else:
                validation_result['errors'].append(f"Missing required field: {field}")

        # Validate scores
        home_score = game_feed.get('home_score', 0)
        away_score = game_feed.get('away_score', 0)

        for score in [home_score, away_score]:
            if not self._is_in_range(score, self.validation_rules['game_feed']['score_range']):
                validation_result['warnings'].append(f"Score {score} outside normal range")

        # Validate quarter
        quarter = game_feed.get('quarter')
        if quarter and not self._is_in_range(quarter, self.validation_rules['game_feed']['quarter_range']):
            validation_result['warnings'].append(f"Quarter {quarter} outside valid range")

        # Check data freshness
        last_updated = game_feed.get('last_updated')
        if last_updated:
            try:
                update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                age_minutes = (datetime.now() - update_time.replace(tzinfo=None)).total_seconds() / 60

                if age_minutes > 5:  # Data older than 5 minutes
                    validation_result['warnings'].append(f"Data is {age_minutes:.1f} minutes old")
                    validation_result['metrics']['data_freshness'] = 'stale'
                else:
                    validation_result['metrics']['data_freshness'] = 'fresh'
            except:
                validation_result['warnings'].append("Invalid timestamp format")

        # Calculate quality score
        validation_result['quality_score'] = self._calculate_game_feed_quality_score(validation_result)

        return validation_result

    def run_comprehensive_validation(self, data_sources: Dict) -> Dict:
        """Run comprehensive validation across all data sources"""
        comprehensive_result = {
            'overall_status': 'passed',
            'timestamp': datetime.now().isoformat(),
            'data_sources': {},
            'overall_quality_score': 0.0,
            'critical_errors': [],
            'recommendations': [],
            'data_quality_summary': {
                'completeness': 0.0,
                'accuracy': 0.0,
                'consistency': 0.0,
                'timeliness': 0.0,
                'reliability': 0.0
            }
        }

        quality_scores = []

        # Validate each data source
        if 'odds' in data_sources:
            odds_validation = self.validate_odds_data(data_sources['odds'])
            comprehensive_result['data_sources']['odds'] = odds_validation
            quality_scores.append(odds_validation['quality_score'])

        if 'player_props' in data_sources:
            props_validation = self.validate_player_props_data(data_sources['player_props'])
            comprehensive_result['data_sources']['player_props'] = props_validation
            quality_scores.append(props_validation['quality_score'])

        if 'analytics' in data_sources:
            analytics_validation = self.validate_analytics_data(data_sources['analytics'])
            comprehensive_result['data_sources']['analytics'] = analytics_validation
            quality_scores.append(analytics_validation['quality_score'])

        if 'game_feed' in data_sources:
            feed_validation = self.validate_game_feed_data(data_sources['game_feed'])
            comprehensive_result['data_sources']['game_feed'] = feed_validation
            quality_scores.append(feed_validation['quality_score'])

        # Calculate overall quality score
        if quality_scores:
            comprehensive_result['overall_quality_score'] = sum(quality_scores) / len(quality_scores)

        # Determine overall status
        failed_sources = [name for name, result in comprehensive_result['data_sources'].items()
                         if result['status'] == 'failed']

        if failed_sources:
            comprehensive_result['overall_status'] = 'failed'
            comprehensive_result['critical_errors'] = failed_sources
        elif any(result['status'] == 'warning' for result in comprehensive_result['data_sources'].values()):
            comprehensive_result['overall_status'] = 'warning'

        # Generate overall recommendations
        comprehensive_result['recommendations'] = self._generate_comprehensive_recommendations(comprehensive_result)

        # Calculate data quality dimensions
        comprehensive_result['data_quality_summary'] = self._calculate_quality_dimensions(comprehensive_result)

        return comprehensive_result

    # Utility methods
    def _odds_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability percentage"""
        if american_odds > 0:
            return 100 / (american_odds + 100) * 100
        else:
            return abs(american_odds) / (abs(american_odds) + 100) * 100

    def _is_in_range(self, value: float, range_dict: Dict) -> bool:
        """Check if value is within specified range"""
        return range_dict['min'] <= value <= range_dict['max']

    def _calculate_odds_quality_score(self, validation_result: Dict) -> float:
        """Calculate quality score for odds data"""
        total_games = validation_result['metrics']['total_games']
        valid_games = validation_result['metrics']['valid_games']

        if total_games == 0:
            return 0.0

        base_score = (valid_games / total_games) * 100

        # Deduct points for warnings
        warning_penalty = min(len(validation_result['warnings']) * 2, 20)

        return max(0, base_score - warning_penalty)

    def _calculate_props_quality_score(self, validation_result: Dict) -> float:
        """Calculate quality score for player props data"""
        total_players = validation_result['metrics']['total_players']
        valid_players = validation_result['metrics']['valid_players']

        if total_players == 0:
            return 0.0

        base_score = (valid_players / total_players) * 100
        warning_penalty = min(len(validation_result['warnings']) * 1, 15)

        return max(0, base_score - warning_penalty)

    def _calculate_analytics_quality_score(self, validation_result: Dict) -> float:
        """Calculate quality score for analytics data"""
        valid_metrics = (validation_result['metrics']['epa_metrics_valid'] +
                        validation_result['metrics']['dvoa_metrics_valid'] +
                        validation_result['metrics']['success_rates_valid'])

        base_score = min(valid_metrics * 25, 100)  # Max 100 for 4+ valid metrics
        warning_penalty = min(len(validation_result['warnings']) * 3, 25)

        return max(0, base_score - warning_penalty)

    def _calculate_game_feed_quality_score(self, validation_result: Dict) -> float:
        """Calculate quality score for game feed data"""
        required_fields = validation_result['metrics']['required_fields_present']
        base_score = (required_fields / 6) * 100  # 6 required fields

        # Bonus for fresh data
        if validation_result['metrics']['data_freshness'] == 'fresh':
            base_score += 10
        elif validation_result['metrics']['data_freshness'] == 'stale':
            base_score -= 15

        warning_penalty = min(len(validation_result['warnings']) * 5, 30)

        return max(0, min(100, base_score - warning_penalty))

    def _generate_odds_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate recommendations for odds data"""
        recommendations = []

        if validation_result['metrics']['invalid_games'] > 0:
            recommendations.append("Review and filter invalid game data before processing")

        if len(validation_result['warnings']) > 10:
            recommendations.append("High number of warnings - review data source configuration")

        if validation_result['quality_score'] < 80:
            recommendations.append("Quality score below threshold - implement additional data cleaning")

        return recommendations

    def _generate_props_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate recommendations for player props data"""
        recommendations = []

        if validation_result['metrics']['invalid_players'] > 0:
            recommendations.append("Filter out players with invalid projections")

        if validation_result['quality_score'] < 85:
            recommendations.append("Implement projection validation before publishing")

        return recommendations

    def _generate_comprehensive_recommendations(self, comprehensive_result: Dict) -> List[str]:
        """Generate comprehensive recommendations"""
        recommendations = []

        if comprehensive_result['overall_quality_score'] < 80:
            recommendations.append("Overall data quality below threshold - review all data sources")

        if comprehensive_result['critical_errors']:
            recommendations.append(f"Critical errors in: {', '.join(comprehensive_result['critical_errors'])}")

        recommendations.append("Implement real-time data quality monitoring")
        recommendations.append("Set up automated alerts for data quality issues")

        return recommendations

    def _calculate_quality_dimensions(self, comprehensive_result: Dict) -> Dict:
        """Calculate data quality dimensions"""
        return {
            'completeness': min(100, comprehensive_result['overall_quality_score'] + 5),
            'accuracy': comprehensive_result['overall_quality_score'],
            'consistency': max(0, comprehensive_result['overall_quality_score'] - 10),
            'timeliness': 85.0,  # Based on data freshness
            'reliability': comprehensive_result['overall_quality_score']
        }

    def get_data_quality_report(self) -> Dict:
        """Generate comprehensive data quality report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'quality_metrics': self.quality_metrics,
            'recent_errors': self.validation_errors[-50:],  # Last 50 errors
            'data_anomalies': self.data_anomalies[-20:],    # Last 20 anomalies
            'quality_alerts': self.quality_alerts[-10:],    # Last 10 alerts
            'recommendations': [
                "Implement automated data quality checks",
                "Set up real-time monitoring dashboard",
                "Create data quality SLAs",
                "Establish data lineage tracking"
            ]
        }

# Create singleton instance
data_validation_service = DataValidationService()