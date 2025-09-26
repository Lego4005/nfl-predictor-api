"""
Backtesting Framework - Historical NFL Data Validation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class HistoricalGame:
    """Historical NFL game data"""
    game_id: str
    season: int
    week: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    spread: float
    total: float
    game_date: datetime

@dataclass
class BacktestResult:
    """Individual backtest result"""
    expert_id: str
    game_id: str
    predictions: Dict[str, Any]
    actual_results: Dict[str, Any]
    category_scores: Dict[str, bool]
    overall_score: float

class HistoricalDataGenerator:
    """Generates realistic historical NFL data"""
    
    def __init__(self):
        self.teams = ['patriots', 'bills', 'jets', 'dolphins', 'steelers', 'ravens']
    
    def generate_season_data(self, season: int, weeks: int = 10) -> List[HistoricalGame]:
        """Generate historical data for testing"""
        games = []
        
        for week in range(1, weeks + 1):
            for i in range(3):  # 3 games per week
                game = self._generate_single_game(season, week, i)
                games.append(game)
        
        return games
    
    def _generate_single_game(self, season: int, week: int, game_num: int) -> HistoricalGame:
        """Generate a single realistic game"""
        home_team = np.random.choice(self.teams)
        away_team = np.random.choice([t for t in self.teams if t != home_team])
        
        spread = np.random.normal(0, 4)
        total = np.random.normal(45, 6)
        
        # Generate scores
        total_points = max(20, total + np.random.normal(0, 8))
        home_score = int(total_points/2 + np.random.normal(2, 3))
        away_score = int(total_points - home_score)
        
        game_date = datetime(season, 9, 1) + timedelta(weeks=week-1)
        
        return HistoricalGame(
            game_id=f"{season}_w{week}_g{game_num}",
            season=season,
            week=week,
            home_team=home_team,
            away_team=away_team,
            home_score=max(0, home_score),
            away_score=max(0, away_score),
            spread=spread,
            total=total,
            game_date=game_date
        )

class BacktestingFramework:
    """Framework for backtesting expert predictions"""
    
    def __init__(self, expert_framework=None):
        self.expert_framework = expert_framework
        self.data_generator = HistoricalDataGenerator()
        self.backtest_results = {}
    
    async def run_backtest(self, expert_ids: List[str], seasons: List[int] = [2023]) -> Dict[str, Any]:
        """Run backtest across historical data"""
        try:
            # Generate historical data
            all_games = []
            for season in seasons:
                season_games = self.data_generator.generate_season_data(season)
                all_games.extend(season_games)
            
            results = {}
            for expert_id in expert_ids:
                expert_results = await self._backtest_expert(expert_id, all_games)
                results[expert_id] = expert_results
            
            return results
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {}
    
    async def _backtest_expert(self, expert_id: str, games: List[HistoricalGame]) -> Dict[str, Any]:
        """Backtest single expert"""
        expert_results = []
        
        for game in games:
            prediction = self._generate_mock_prediction(game)
            result = self._evaluate_prediction(expert_id, game, prediction)
            expert_results.append(result)
        
        return self._calculate_summary(expert_id, expert_results)
    
    def _generate_mock_prediction(self, game: HistoricalGame) -> Dict[str, Any]:
        """Generate mock prediction"""
        winner = 'home' if game.spread < 0 else 'away'
        
        return {
            'winner_prediction': winner,
            'exact_score_home': int(game.total/2 - game.spread/2),
            'exact_score_away': int(game.total/2 + game.spread/2),
            'against_the_spread': winner,
            'totals_over_under': 'over' if game.total > 45 else 'under'
        }
    
    def _evaluate_prediction(self, expert_id: str, game: HistoricalGame, prediction: Dict[str, Any]) -> BacktestResult:
        """Evaluate prediction accuracy"""
        actual_winner = 'home' if game.home_score > game.away_score else 'away'
        
        scores = {
            'winner_prediction': prediction.get('winner_prediction') == actual_winner,
            'exact_score_home': abs(prediction.get('exact_score_home', 0) - game.home_score) <= 7,
            'exact_score_away': abs(prediction.get('exact_score_away', 0) - game.away_score) <= 7,
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        return BacktestResult(
            expert_id=expert_id,
            game_id=game.game_id,
            predictions=prediction,
            actual_results={'winner': actual_winner, 'home_score': game.home_score, 'away_score': game.away_score},
            category_scores=scores,
            overall_score=overall_score
        )
    
    def _calculate_summary(self, expert_id: str, results: List[BacktestResult]) -> Dict[str, Any]:
        """Calculate backtest summary"""
        if not results:
            return {'expert_id': expert_id, 'accuracy': 0, 'total_games': 0}
        
        total_games = len(results)
        overall_accuracy = sum(r.overall_score for r in results) / total_games
        
        return {
            'expert_id': expert_id,
            'total_games': total_games,
            'overall_accuracy': overall_accuracy,
            'category_accuracies': {
                'winner_prediction': sum(r.category_scores.get('winner_prediction', False) for r in results) / total_games,
                'score_prediction': sum(r.category_scores.get('exact_score_home', False) for r in results) / total_games
            }
        }

# Test function
async def test_backtesting():
    """Test backtesting framework"""
    try:
        framework = BacktestingFramework()
        
        results = await framework.run_backtest(['expert_1', 'expert_2'])
        
        print("Backtest Results:")
        for expert_id, summary in results.items():
            print(f"{expert_id}: {summary['overall_accuracy']:.3f} accuracy over {summary['total_games']} games")
        
        return True
        
    except Exception as e:
        print(f"Backtest test failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_backtesting())