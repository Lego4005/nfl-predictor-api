"""
Automated Result Collection Service
Fetches live game results and updates prediction accuracy
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import PredictionResult
from .calculation_engine import accuracy_engine
from ..database.models import Prediction
from ..database.connection import get_db
from ..api.espn_api_client import ESPNAPIClient
from ..api.nfl_api_client import NFLAPIClient

logger = logging.getLogger(__name__)

class ResultCollectionService:
    """Service for collecting and processing game results"""
    
    def __init__(self):
        self.espn_client = ESPNAPIClient()
        self.nfl_client = NFLAPIClient()
        self.collection_sources = ['espn', 'nfl_api']
    
    async def collect_weekly_results(self, season: int, week: int) -> Dict:
        """Collect all game results for a specific week"""
        try:
            logger.info(f"Collecting results for Season {season}, Week {week}")
            
            results_collected = []
            errors = []
            
            # Try each data source
            for source in self.collection_sources:
                try:
                    if source == 'espn':
                        games = await self._collect_espn_results(season, week)
                    elif source == 'nfl_api':
                        games = await self._collect_nfl_results(season, week)
                    else:
                        continue
                    
                    for game in games:
                        result = await self._process_game_result(game, source)
                        if result['success']:
                            results_collected.append(result['game_id'])
                        else:
                            errors.append(result['error'])
                    
                    break  # Use first successful source
                    
                except Exception as e:
                    logger.error(f"Error collecting from {source}: {e}")
                    errors.append(f"{source}: {str(e)}")
                    continue
            
            # Update prediction accuracy for collected results
            accuracy_updates = await self._update_prediction_accuracy(season, week)
            
            return {
                'success': True,
                'season': season,
                'week': week,
                'results_collected': len(results_collected),
                'games': results_collected,
                'accuracy_updates': accuracy_updates,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error in weekly result collection: {e}")
            return {
                'success': False,
                'error': str(e),
                'season': season,
                'week': week
            }
    
    async def _collect_espn_results(self, season: int, week: int) -> List[Dict]:
        """Collect results from ESPN API"""
        try:
            # Get games for the week
            games_data = await self.espn_client.get_week_games(season, week)
            
            processed_games = []
            for game in games_data.get('games', []):
                if game.get('status', {}).get('type', {}).get('name') == 'STATUS_FINAL':
                    processed_game = {
                        'game_id': f"espn_{game['id']}",
                        'home_team': game['competitions'][0]['competitors'][0]['team']['abbreviation'],
                        'away_team': game['competitions'][0]['competitors'][1]['team']['abbreviation'],
                        'home_score': int(game['competitions'][0]['competitors'][0]['score']),
                        'away_score': int(game['competitions'][0]['competitors'][1]['score']),
                        'game_date': game['date'],
                        'status': 'final',
                        'spread_line': game.get('competitions', [{}])[0].get('odds', [{}])[0].get('spread'),
                        'total_line': game.get('competitions', [{}])[0].get('odds', [{}])[0].get('overUnder')
                    }
                    processed_games.append(processed_game)
            
            return processed_games
            
        except Exception as e:
            logger.error(f"Error collecting ESPN results: {e}")
            raise
    
    async def _collect_nfl_results(self, season: int, week: int) -> List[Dict]:
        """Collect results from NFL API"""
        try:
            # Get games for the week
            games_data = await self.nfl_client.get_week_scores(season, week)
            
            processed_games = []
            for game in games_data.get('games', []):
                if game.get('gameStatus') == 'FINAL':
                    processed_game = {
                        'game_id': f"nfl_{game['gameId']}",
                        'home_team': game['homeTeam']['abbreviation'],
                        'away_team': game['awayTeam']['abbreviation'],
                        'home_score': int(game['homeTeam']['score']),
                        'away_score': int(game['awayTeam']['score']),
                        'game_date': game['gameDate'],
                        'status': 'final',
                        'spread_line': game.get('bettingLines', {}).get('spread'),
                        'total_line': game.get('bettingLines', {}).get('total')
                    }
                    processed_games.append(processed_game)
            
            return processed_games
            
        except Exception as e:
            logger.error(f"Error collecting NFL API results: {e}")
            raise
    
    async def _process_game_result(self, game_data: Dict, source: str) -> Dict:
        """Process and store a single game result"""
        with get_db() as db:
            try:
                game_id = game_data['game_id']
                
                # Check if result already exists
                existing_result = db.query(PredictionResult).filter_by(game_id=game_id).first()
                
                if existing_result:
                    # Update existing result
                    result = existing_result
                else:
                    # Create new result
                    result = PredictionResult(game_id=game_id)
                    db.add(result)
                
                # Update result data
                result.home_team = game_data['home_team']
                result.away_team = game_data['away_team']
                result.home_score = game_data['home_score']
                result.away_score = game_data['away_score']
                result.game_status = 'final'
                result.result_source = source
                result.game_date = datetime.fromisoformat(game_data['game_date'].replace('Z', '+00:00'))
                
                # Set betting lines if available
                if game_data.get('spread_line'):
                    result.spread_line = float(game_data['spread_line'])
                if game_data.get('total_line'):
                    result.total_line = float(game_data['total_line'])
                
                # Calculate derived results
                result.winner = self._determine_winner(game_data['home_score'], game_data['away_score'])
                
                if result.spread_line:
                    result.ats_winner = self._determine_ats_winner(
                        game_data['home_score'], game_data['away_score'], result.spread_line
                    )
                
                if result.total_line:
                    total_score = game_data['home_score'] + game_data['away_score']
                    result.total_result = self._determine_total_result(total_score, result.total_line)
                
                db.commit()
                
                return {
                    'success': True,
                    'game_id': game_id,
                    'result_id': str(result.id)
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error processing game result: {e}")
                return {
                    'success': False,
                    'game_id': game_data.get('game_id', 'unknown'),
                    'error': str(e)
                }
    
    def _determine_winner(self, home_score: int, away_score: int) -> str:
        """Determine the straight-up winner"""
        if home_score > away_score:
            return 'home'
        elif away_score > home_score:
            return 'away'
        else:
            return 'tie'
    
    def _determine_ats_winner(self, home_score: int, away_score: int, spread: float) -> str:
        """Determine the against-the-spread winner"""
        # Spread is typically given for home team (negative means home is favored)
        home_ats_score = home_score + spread
        
        if home_ats_score > away_score:
            return 'home'
        elif home_ats_score < away_score:
            return 'away'
        else:
            return 'push'
    
    def _determine_total_result(self, total_score: int, total_line: float) -> str:
        """Determine if the total went over or under"""
        if total_score > total_line:
            return 'over'
        elif total_score < total_line:
            return 'under'
        else:
            return 'push'
    
    async def _update_prediction_accuracy(self, season: int, week: int) -> Dict:
        """Update prediction accuracy for all predictions with new results"""
        with get_db() as db:
            try:
                # Get all predictions for this week that don't have accuracy calculated
                predictions = db.query(Prediction).filter(
                    and_(
                        Prediction.season == season,
                        Prediction.week == week,
                        Prediction.is_correct.is_(None)
                    )
                ).all()
                
                updates_made = 0
                errors = []
                
                for prediction in predictions:
                    try:
                        # Find matching result
                        result = self._find_matching_result(db, prediction)
                        
                        if result:
                            # Calculate accuracy
                            accuracy_result = accuracy_engine.calculate_prediction_accuracy(
                                str(prediction.id), str(result.id)
                            )
                            
                            if accuracy_result['success']:
                                # Update prediction with result
                                prediction.is_correct = accuracy_result['is_correct']
                                prediction.actual_result = {
                                    'winner': result.winner,
                                    'ats_winner': result.ats_winner,
                                    'total_result': result.total_result,
                                    'home_score': result.home_score,
                                    'away_score': result.away_score
                                }
                                prediction.result_updated_at = datetime.utcnow()
                                updates_made += 1
                            else:
                                errors.append(f"Prediction {prediction.id}: {accuracy_result['error']}")
                    
                    except Exception as e:
                        errors.append(f"Prediction {prediction.id}: {str(e)}")
                        continue
                
                db.commit()
                
                # Update performance history
                history_update = accuracy_engine.update_performance_history('weekly', season, week)
                
                return {
                    'predictions_updated': updates_made,
                    'errors': errors,
                    'performance_history_updated': history_update.get('success', False)
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating prediction accuracy: {e}")
                return {
                    'predictions_updated': 0,
                    'errors': [str(e)],
                    'performance_history_updated': False
                }
    
    def _find_matching_result(self, db: Session, prediction: Prediction) -> Optional[PredictionResult]:
        """Find the matching game result for a prediction"""
        try:
            # Try to match by teams and week
            result = db.query(PredictionResult).filter(
                and_(
                    PredictionResult.home_team == prediction.home_team,
                    PredictionResult.away_team == prediction.away_team,
                    PredictionResult.game_status == 'final'
                )
            ).first()
            
            if not result:
                # Try reverse team matching (in case home/away are swapped)
                result = db.query(PredictionResult).filter(
                    and_(
                        PredictionResult.home_team == prediction.away_team,
                        PredictionResult.away_team == prediction.home_team,
                        PredictionResult.game_status == 'final'
                    )
                ).first()
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding matching result: {e}")
            return None
    
    async def collect_live_results(self) -> Dict:
        """Collect results for games that have recently finished"""
        try:
            current_time = datetime.utcnow()
            
            # Get current NFL season and week (simplified calculation)
            current_season = current_time.year if current_time.month >= 9 else current_time.year - 1
            
            # Calculate current week (simplified - in production use actual NFL schedule)
            season_start = datetime(current_season, 9, 1)
            weeks_since_start = (current_time - season_start).days // 7
            current_week = min(max(1, weeks_since_start + 1), 18)
            
            # Collect results for current week
            result = await self.collect_weekly_results(current_season, current_week)
            
            # Also check previous week in case of delayed results
            if current_week > 1:
                prev_week_result = await self.collect_weekly_results(current_season, current_week - 1)
                result['previous_week_updates'] = prev_week_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error in live result collection: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global result collection service instance
result_collector = ResultCollectionService()