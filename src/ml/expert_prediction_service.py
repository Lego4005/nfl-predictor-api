"""
Expert Prediction Service
Integrates 15 competing expert models with live data to generate predictions
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.personality_driven_experts import (
    ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel, ValueHunter, MomentumRider,
    FundamentalistScholar, ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
    TrendReversalSpecialist, PopularNarrativeFader, SharpMoneyFollower, UnderdogChampion,
    ConsensusFollower, MarketInefficiencyExploiter, UniversalGameData
)
from ml.expert_models import ExpertPrediction  # Keep for data structure
from services.live_data_service import live_data_service
from ml.supabase_historical_service import supabase_historical_service
from utils.date_utils import DateUtils

logger = logging.getLogger(__name__)


class ExpertPredictionService:
    """Service to generate predictions from 15 competing experts"""

    def __init__(self):
        # Initialize personality-driven experts
        self.personality_experts = [
            ConservativeAnalyzer(),     # The Analyst
            RiskTakingGambler(),        # The Gambler
            ContrarianRebel(),          # The Rebel
            ValueHunter(),              # The Hunter
            MomentumRider(),            # The Rider
            FundamentalistScholar(),    # The Scholar
            ChaosTheoryBeliever(),      # The Chaos
            GutInstinctExpert(),        # The Intuition
            StatisticsPurist(),         # The Quant
            TrendReversalSpecialist(),  # The Reversal
            PopularNarrativeFader(),    # The Fader
            SharpMoneyFollower(),       # The Sharp
            UnderdogChampion(),         # The Underdog
            ConsensusFollower(),        # The Consensus
            MarketInefficiencyExploiter() # The Exploiter
        ]

        self.live_data = live_data_service
        self.historical_data = supabase_historical_service
        logger.info("🎭 Expert Prediction Service initialized with 15 personality-driven autonomous experts")

    def get_tonights_games(self) -> List[Dict]:
        """Get tonight's NFL games with proper timezone handling"""
        try:
            # Get upcoming games from live data service
            games = self.live_data.get_upcoming_games()

            # Use DateUtils to filter tonight's games properly
            tonights_games = DateUtils.get_tonights_games(games)

            logger.info(f"📅 Found {len(tonights_games)} games for tonight using DateUtils")

            # Log each game with proper timing info
            for game in tonights_games:
                home = game.get('home_team', 'N/A')
                away = game.get('away_team', 'N/A')
                game_time_et = game.get('game_time_et', 'N/A')
                status = game.get('status', 'unknown')
                logger.info(f"  • {away} @ {home} at {game_time_et} ({status})")

            return tonights_games

        except Exception as e:
            logger.error(f"Error fetching tonight's games: {e}")
            # Return mock games for testing
            return self._get_mock_games()

    def generate_all_expert_predictions(self, home_team: str, away_team: str) -> Dict:
        """Generate predictions from all 15 experts for a game"""

        # Get comprehensive game data
        game_data = self.live_data.get_comprehensive_game_data(home_team, away_team)

        # Enrich with historical data from Supabase
        spread = game_data.get('spread', 0)
        total = game_data.get('total', 45.5)

        # Find similar historical games using Supabase
        similar_games = self.historical_data.find_similar_games_vector(
            home_team, away_team, spread, total, limit=10
        )

        # Get team performance history from Supabase
        home_performance = self.historical_data.get_team_performance_history(home_team, 10)
        away_performance = self.historical_data.get_team_performance_history(away_team, 10)

        # Add historical context to game data
        game_data['similar_games'] = similar_games
        game_data['home_team_history'] = home_performance
        game_data['away_team_history'] = away_performance

        logger.info(f"📊 Enriched with {len(similar_games)} similar games from Supabase")

        # Convert game_data to UniversalGameData format
        universal_data = self._convert_to_universal_data(home_team, away_team, game_data)

        # Get predictions from all 15 personality-driven experts
        all_predictions = []
        for expert in self.personality_experts:
            prediction = expert.make_personality_driven_prediction(universal_data)
            # Convert to ExpertPrediction format for compatibility
            expert_pred = self._convert_personality_prediction(expert, prediction, home_team, away_team)
            all_predictions.append(expert_pred)

        # Calculate consensus from personality experts
        consensus = self._calculate_personality_consensus(all_predictions)

        return {
            'game_info': {
                'home_team': home_team,
                'away_team': away_team,
                'kickoff': datetime.now().isoformat(),
                'spread': game_data.get('spread'),
                'total': game_data.get('total'),
                'weather': game_data.get('weather')
            },
            'all_expert_predictions': self._format_predictions(all_predictions),
            'top5_consensus': consensus,
            'personality_expert_info': self._get_personality_info(),
            'prediction_timestamp': datetime.now().isoformat()
        }

    def _format_predictions(self, predictions: List[ExpertPrediction]) -> List[Dict]:
        """Format expert predictions for API response"""
        formatted = []

        for pred in predictions:
            formatted.append({
                'expert_id': pred.expert_id,
                'expert_name': pred.expert_name,
                'predictions': {
                    'game_outcome': {
                        'winner': pred.game_outcome['winner'],
                        'confidence': pred.game_outcome['confidence'],
                        'reasoning': pred.game_outcome['reasoning']
                    },
                    'spread': {
                        'pick': pred.against_the_spread['pick'],
                        'confidence': pred.against_the_spread['confidence']
                    },
                    'total': {
                        'pick': pred.totals['pick'],
                        'confidence': pred.totals['confidence']
                    },
                    'exact_score': {
                        'home': pred.exact_score['home_score'],
                        'away': pred.exact_score['away_score'],
                        'confidence': pred.exact_score['confidence']
                    },
                    'margin': {
                        'points': pred.margin_of_victory['margin'],
                        'winner': pred.margin_of_victory['winner']
                    }
                },
                'confidence_overall': pred.confidence_overall,
                'key_factors': pred.key_factors,
                'reasoning': pred.reasoning
            })

        # Sort by overall confidence (highest first)
        formatted.sort(key=lambda x: x['confidence_overall'], reverse=True)

        return formatted

    def get_expert_battle_card(self, game_id: str) -> Dict:
        """Get a battle card showing how experts compete on this game"""

        # For demo, use sample teams
        home_team = "KC"
        away_team = "BAL"

        predictions_data = self.generate_all_expert_predictions(home_team, away_team)

        # Create battle card format
        battle_card = {
            'game_id': game_id,
            'matchup': f"{away_team} @ {home_team}",

            # Expert showdown
            'expert_showdown': {
                'most_confident': self._get_most_confident(predictions_data['all_expert_predictions']),
                'biggest_disagreement': self._find_biggest_disagreement(predictions_data['all_expert_predictions']),
                'consensus_vs_contrarian': self._consensus_vs_contrarian(predictions_data['all_expert_predictions'])
            },

            # Prediction breakdown
            'prediction_breakdown': {
                'winner_votes': self._count_winner_votes(predictions_data['all_expert_predictions']),
                'spread_votes': self._count_spread_votes(predictions_data['all_expert_predictions']),
                'total_votes': self._count_total_votes(predictions_data['all_expert_predictions'])
            },

            # Top 5 vs Bottom 10
            'top5_vs_field': {
                'top5_consensus': predictions_data['top5_consensus'],
                'field_average': self._calculate_field_average(predictions_data['all_expert_predictions'][5:])
            },

            # Expert specialization matches
            'best_suited_experts': self._find_best_suited_experts(predictions_data['all_expert_predictions'], predictions_data['game_info'])
        }

        return battle_card

    def _get_most_confident(self, predictions: List[Dict]) -> Dict:
        """Find the most confident expert"""
        if not predictions:
            return {}
        return predictions[0]  # Already sorted by confidence

    def _find_biggest_disagreement(self, predictions: List[Dict]) -> Dict:
        """Find where experts disagree most"""
        if len(predictions) < 2:
            return {}

        # Find spread disagreement
        spreads = [p['predictions']['spread']['pick'] for p in predictions]
        home_spread_picks = sum(1 for s in spreads if s == predictions[0]['predictions']['game_outcome']['winner'])

        return {
            'category': 'spread' if len(set(spreads)) > 1 else 'winner',
            'split': f"{home_spread_picks} vs {len(spreads) - home_spread_picks}",
            'controversy_level': 'high' if abs(home_spread_picks - (len(spreads) / 2)) < 2 else 'low'
        }

    def _consensus_vs_contrarian(self, predictions: List[Dict]) -> Dict:
        """Compare consensus picks vs contrarian experts"""
        winners = [p['predictions']['game_outcome']['winner'] for p in predictions]

        # Find most common pick
        from collections import Counter
        winner_counts = Counter(winners)
        consensus_pick = winner_counts.most_common(1)[0][0]
        consensus_count = winner_counts.most_common(1)[0][1]

        contrarians = [p for p in predictions if p['predictions']['game_outcome']['winner'] != consensus_pick]

        return {
            'consensus_pick': consensus_pick,
            'consensus_count': consensus_count,
            'contrarian_count': len(contrarians),
            'contrarian_experts': [c['expert_name'] for c in contrarians[:3]]  # Top 3 contrarians
        }

    def _count_winner_votes(self, predictions: List[Dict]) -> Dict:
        """Count votes for each team to win"""
        winners = [p['predictions']['game_outcome']['winner'] for p in predictions]
        from collections import Counter
        return dict(Counter(winners))

    def _count_spread_votes(self, predictions: List[Dict]) -> Dict:
        """Count votes for spread picks"""
        spreads = [p['predictions']['spread']['pick'] for p in predictions]
        from collections import Counter
        return dict(Counter(spreads))

    def _count_total_votes(self, predictions: List[Dict]) -> Dict:
        """Count votes for over/under"""
        totals = [p['predictions']['total']['pick'] for p in predictions]
        from collections import Counter
        return dict(Counter(totals))

    def _calculate_field_average(self, predictions: List[Dict]) -> Dict:
        """Calculate average predictions from experts 6-15"""
        if not predictions:
            return {}

        avg_confidence = sum(p['confidence_overall'] for p in predictions) / len(predictions)

        # Most common picks
        winners = [p['predictions']['game_outcome']['winner'] for p in predictions]
        from collections import Counter
        winner_counts = Counter(winners)

        return {
            'average_confidence': round(avg_confidence, 3),
            'most_picked_winner': winner_counts.most_common(1)[0][0] if winner_counts else None,
            'expert_count': len(predictions)
        }

    def _find_best_suited_experts(self, predictions: List[Dict], game_info: Dict) -> List[str]:
        """Find experts best suited for this game type"""
        best_suited = []

        # Check for special game conditions
        if game_info.get('weather', {}).get('wind_speed', 0) > 15:
            best_suited.append("Weather Wizard")

        if game_info.get('spread', 0) > 7:
            best_suited.append("Road Warrior")  # Big underdog

        if datetime.now().hour >= 20:
            best_suited.append("Primetime Performer")

        # Add the most confident expert
        if predictions:
            best_suited.append(predictions[0]['expert_name'])

        return list(set(best_suited))[:5]  # Top 5 unique

    def _convert_to_universal_data(self, home_team: str, away_team: str, game_data: Dict) -> UniversalGameData:
        """Convert game_data to UniversalGameData format for personality experts"""
        return UniversalGameData(
            home_team=home_team,
            away_team=away_team,
            game_time=game_data.get('commence_time', datetime.now().isoformat()),
            location=game_data.get('location', 'Stadium'),
            weather=game_data.get('weather', {}),
            injuries=game_data.get('injuries', {}),
            team_stats=game_data.get('team_stats', {}),
            line_movement=game_data.get('line_movement', {}),
            public_betting=game_data.get('public_betting', {}),
            recent_news=game_data.get('recent_news', []),
            head_to_head=game_data.get('head_to_head', {}),
            coaching_info=game_data.get('coaching_info', {})
        )

    def _convert_personality_prediction(self, expert, prediction: Dict, home_team: str, away_team: str) -> ExpertPrediction:
        """Convert personality expert prediction to ExpertPrediction format"""

        # Calculate exact scores from spread and total
        spread_pred = prediction.get('spread_prediction', 0)
        total_pred = prediction.get('total_prediction', 45)

        if spread_pred > 0:  # Away team favored
            away_score = int((total_pred + spread_pred) / 2)
            home_score = int(total_pred - away_score)
        else:  # Home team favored
            home_score = int((total_pred - spread_pred) / 2)
            away_score = int(total_pred - home_score)

        return ExpertPrediction(
            expert_id=expert.expert_id,
            expert_name=expert.name,
            game_id=f"{away_team}@{home_team}",
            game_outcome={
                'winner': prediction.get('winner_prediction', 'home'),
                'confidence': prediction.get('winner_confidence', 0.5),
                'reasoning': prediction.get('reasoning', 'Personality-driven analysis')
            },
            exact_score={
                'home_score': home_score,
                'away_score': away_score,
                'confidence': prediction.get('winner_confidence', 0.5)
            },
            margin_of_victory={
                'margin': abs(spread_pred),
                'winner': prediction.get('winner_prediction', 'home')
            },
            against_the_spread={
                'pick': prediction.get('winner_prediction', 'home'),
                'confidence': prediction.get('winner_confidence', 0.5)
            },
            totals={
                'pick': 'over' if total_pred > 45 else 'under',
                'confidence': prediction.get('winner_confidence', 0.5)
            },
            moneyline_value={
                'expected_value': prediction.get('winner_confidence', 0.5),
                'recommendation': 'bet' if prediction.get('winner_confidence', 0.5) > 0.6 else 'pass'
            },
            first_half_winner={
                'winner': prediction.get('winner_prediction', 'home'),
                'confidence': prediction.get('winner_confidence', 0.5) * 0.8
            },
            highest_scoring_quarter={
                'quarter': 'Q2',
                'confidence': 0.3
            },
            player_props={},
            confidence_overall=prediction.get('winner_confidence', 0.5),
            reasoning=prediction.get('reasoning', 'Personality-driven analysis'),
            key_factors=prediction.get('key_factors', ['Personality-based analysis']),
            prediction_timestamp=datetime.now()
        )

    def _calculate_personality_consensus(self, predictions: List[ExpertPrediction]) -> Dict:
        """Calculate consensus from personality expert predictions"""
        if not predictions:
            return {}

        # Winner consensus
        winners = [p.game_outcome['winner'] for p in predictions]
        from collections import Counter
        winner_counts = Counter(winners)
        consensus_winner = winner_counts.most_common(1)[0][0]

        # Average confidence
        avg_confidence = sum(p.confidence_overall for p in predictions) / len(predictions)

        # Average spread
        spreads = [abs(p.margin_of_victory['margin']) for p in predictions]
        avg_spread = sum(spreads) / len(spreads)

        return {
            'winner': consensus_winner,
            'confidence': avg_confidence,
            'spread': avg_spread,
            'expert_count': len(predictions),
            'agreement_level': winner_counts.most_common(1)[0][1] / len(predictions)
        }

    def _get_personality_info(self) -> List[Dict]:
        """Get information about personality experts"""
        return [
            {
                'expert_id': expert.expert_id,
                'name': expert.name,
                'personality_traits': {trait: t.value for trait, t in expert.personality.traits.items()},
                'decision_style': expert.personality.decision_style,
                'learning_rate': expert.personality.learning_rate
            }
            for expert in self.personality_experts
        ]

    def _get_mock_games(self) -> List[Dict]:
        """Get mock games for testing"""
        return [
            {
                'game_id': 'mock_1',
                'home_team': 'KC',
                'away_team': 'BAL',
                'commence_time': datetime.now().isoformat(),
                'spread': -3.5,
                'total': 48.5,
                'home_moneyline': -165,
                'away_moneyline': +145
            },
            {
                'game_id': 'mock_2',
                'home_team': 'BUF',
                'away_team': 'MIA',
                'commence_time': datetime.now().isoformat(),
                'spread': -7,
                'total': 51.5,
                'home_moneyline': -280,
                'away_moneyline': +230
            }
        ]

    def simulate_competition_round(self, week: int = 2) -> Dict:
        """Simulate a full competition round for all experts"""

        # Get games for the week
        games = self.get_tonights_games()
        if not games:
            games = self._get_mock_games()

        round_results = {
            'week': week,
            'games': [],
            'leaderboard_changes': {},
            'round_winner': None,
            'biggest_mover': None
        }

        # Track points earned this round
        round_points = {expert.expert_id: 0 for expert in self.personality_experts}

        for game in games[:2]:  # Limit to 2 games for demo
            home = game['home_team']
            away = game['away_team']

            # Generate all predictions
            game_predictions = self.generate_all_expert_predictions(home, away)

            # Simulate game result (mock for now)
            actual_result = self._simulate_game_result(home, away, game)

            # Score each expert's predictions
            for pred in game_predictions['all_expert_predictions']:
                points = self._score_prediction(pred, actual_result)
                round_points[pred['expert_id']] += points

            round_results['games'].append({
                'matchup': f"{away} @ {home}",
                'actual_result': actual_result,
                'expert_scores': {pred['expert_id']: self._score_prediction(pred, actual_result)
                                  for pred in game_predictions['all_expert_predictions']}
            })

        # Determine round winner
        round_winner = max(round_points.items(), key=lambda x: x[1])
        winner_expert = next(expert for expert in self.personality_experts if expert.expert_id == round_winner[0])
        round_results['round_winner'] = {
            'expert_id': round_winner[0],
            'points': round_winner[1],
            'name': winner_expert.name
        }

        # Create mock leaderboard from round points
        round_results['updated_leaderboard'] = [
            {
                'expert_id': expert_id,
                'name': next(expert.name for expert in self.personality_experts if expert.expert_id == expert_id),
                'points': points
            }
            for expert_id, points in sorted(round_points.items(), key=lambda x: x[1], reverse=True)
        ][:10]

        return round_results

    def _simulate_game_result(self, home: str, away: str, game: Dict) -> Dict:
        """Simulate a game result (mock for demonstration)"""
        import random

        # Use spread to influence result
        spread = game.get('spread', 0)
        total = game.get('total', 45)

        # Simulate scores
        if spread < 0:  # Home favored
            home_score = random.randint(20, 35)
            away_score = home_score + int(spread) + random.randint(-7, 7)
        else:
            away_score = random.randint(20, 35)
            home_score = away_score - int(spread) + random.randint(-7, 7)

        # Ensure positive scores
        home_score = max(0, home_score)
        away_score = max(0, away_score)

        actual_total = home_score + away_score

        return {
            'winner': home if home_score > away_score else away,
            'home_score': home_score,
            'away_score': away_score,
            'margin': abs(home_score - away_score),
            'total': actual_total,
            'spread_cover': home if (home_score - away_score) > spread else away,
            'total_result': 'over' if actual_total > total else 'under'
        }

    def _score_prediction(self, prediction: Dict, actual: Dict) -> float:
        """Score an expert's prediction against actual result"""
        points = 0

        # Score game winner (10 points base)
        if prediction['predictions']['game_outcome']['winner'] == actual['winner']:
            confidence = prediction['predictions']['game_outcome']['confidence']
            points += 10 * (1 + confidence * 0.5)
        else:
            points -= 5

        # Score spread (15 points base)
        if prediction['predictions']['spread']['pick'] == actual['spread_cover']:
            confidence = prediction['predictions']['spread']['confidence']
            points += 15 * (1 + confidence * 0.5)
        else:
            points -= 10

        # Score total (12 points base)
        if prediction['predictions']['total']['pick'] == actual['total_result']:
            confidence = prediction['predictions']['total']['confidence']
            points += 12 * (1 + confidence * 0.5)
        else:
            points -= 8

        # Score exact score (bonus points)
        pred_home = prediction['predictions']['exact_score']['home']
        pred_away = prediction['predictions']['exact_score']['away']

        if pred_home == actual['home_score'] and pred_away == actual['away_score']:
            points += 100  # Jackpot!
        elif pred_home == actual['home_score'] or pred_away == actual['away_score']:
            points += 25  # Got one team right
        elif abs(pred_home - actual['home_score']) <= 3 and abs(pred_away - actual['away_score']) <= 3:
            points += 10  # Close

        # Score margin
        pred_margin = prediction['predictions']['margin']['points']
        if abs(pred_margin - actual['margin']) == 0:
            points += 50
        elif abs(pred_margin - actual['margin']) <= 3:
            points += 20
        elif abs(pred_margin - actual['margin']) <= 7:
            points += 10

        return points


# Create singleton instance
expert_prediction_service = ExpertPredictionService()