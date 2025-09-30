"""
Backtest Runner for Personality-Driven NFL Experts

This module orchestrates chronological backtesting by:
1. Looping through a season chronologically
2. Building temporally safe UniversalGameData for each game
3. Getting expert predictions using only historically available data
4. Storing predictions and revealing actual outcomes
5. Optionally triggering learning based on results

The runner ensures temporal sequencing and prediction-outcome pairing
to evaluate expert performance and learning capabilities.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import necessary services and data structures
try:
    from .historical_data_service import HistoricalDataService
    from .universal_game_data_builder import UniversalGameDataBuilder, UniversalGameData
except ImportError:
    from src.services.historical_data_service import HistoricalDataService
    from src.services.universal_game_data_builder import UniversalGameDataBuilder, UniversalGameData

try:
    from ..ml.personality_driven_experts import PersonalityDrivenExpert
except ImportError:
    from src.ml.personality_driven_experts import PersonalityDrivenExpert

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """Learning configuration modes for backtesting"""
    BASELINE = "baseline"  # No learning, static behavior
    MEMORY_ONLY = "memory_only"  # Episodic memory without belief revision
    FULL_LEARNING = "full_learning"  # Memory + belief revision + weight adaptation


@dataclass
class PredictionRecord:
    """Record of an expert's prediction and actual outcome"""
    # Game identification
    game_id: str
    season: int
    week: int
    home_team: str
    away_team: str
    game_date: str
    
    # Expert prediction
    expert_id: str
    prediction: Dict[str, Any]
    confidence: float
    reasoning: List[str]
    prediction_timestamp: str
    
    # Actual outcome
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None
    actual_winner: Optional[str] = None
    outcome_revealed: bool = False
    
    # Accuracy assessment
    correct_winner: Optional[bool] = None
    correct_spread: Optional[bool] = None
    correct_total: Optional[bool] = None
    overall_accuracy: Optional[float] = None
    
    # Learning context
    learning_mode: LearningMode = LearningMode.BASELINE
    learning_triggered: bool = False
    belief_revision_occurred: bool = False
    memory_stored: bool = False


@dataclass
class BacktestResults:
    """Complete results from a backtest run"""
    expert_id: str
    season: int
    learning_mode: LearningMode
    
    # Game records
    predictions: List[PredictionRecord] = field(default_factory=list)
    
    # Performance metrics
    total_games: int = 0
    correct_winners: int = 0
    correct_spreads: int = 0
    correct_totals: int = 0
    
    # Accuracy rates
    winner_accuracy: float = 0.0
    spread_accuracy: float = 0.0
    total_accuracy: float = 0.0
    overall_accuracy: float = 0.0
    
    # Learning statistics
    learning_events: int = 0
    belief_revisions: int = 0
    memories_created: int = 0
    
    # Temporal performance
    early_season_accuracy: float = 0.0  # First 4 weeks
    mid_season_accuracy: float = 0.0    # Weeks 5-12
    late_season_accuracy: float = 0.0   # Weeks 13+
    
    # Performance trend
    accuracy_by_week: Dict[int, float] = field(default_factory=dict)
    rolling_accuracy: List[float] = field(default_factory=list)


class BacktestRunner:
    """
    Orchestrates chronological backtesting of personality-driven experts
    
    The runner ensures temporal safety and proper prediction-outcome sequencing
    while providing hooks for learning and adaptation based on results.
    """
    
    def __init__(
        self,
        historical_service: HistoricalDataService,
        universal_builder: UniversalGameDataBuilder
    ):
        self.historical_service = historical_service
        self.universal_builder = universal_builder
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Tracking for learning and analytics
        self._prediction_records: List[PredictionRecord] = []
        self._learning_events: List[Dict[str, Any]] = []
        
        self.logger.info("🏃‍♂️ Backtest Runner initialized for chronological expert testing")
    
    async def run_season_backtest(
        self,
        expert: PersonalityDrivenExpert,
        season: int,
        learning_mode: LearningMode = LearningMode.BASELINE,
        start_week: int = 1,
        end_week: int = 18,
        game_filter: Optional[Dict[str, Any]] = None
    ) -> BacktestResults:
        """
        Run complete season backtest for a single expert
        
        Args:
            expert: Personality-driven expert to test
            season: Season year to backtest
            learning_mode: Learning configuration
            start_week: Starting week (default: 1)
            end_week: Ending week (default: 18)
            game_filter: Optional filter for specific games
            
        Returns:
            BacktestResults with complete performance analysis
        """
        try:
            self.logger.info(f"🏈 Starting {season} season backtest for {expert.name} ({learning_mode.value})")
            
            # Initialize expert for backtesting
            self._initialize_expert_for_backtest(expert, learning_mode)
            
            # Get chronological list of games for the season
            season_games = await self._get_season_games(season, start_week, end_week, game_filter)
            
            if not season_games:
                self.logger.warning(f"⚠️ No games found for {season} season")
                return self._create_empty_results(expert.expert_id, season, learning_mode)
            
            self.logger.info(f"📅 Found {len(season_games)} games for {season} season (Weeks {start_week}-{end_week})")
            
            # Process games chronologically
            results = BacktestResults(
                expert_id=expert.expert_id,
                season=season,
                learning_mode=learning_mode
            )
            
            for i, game in enumerate(season_games):
                self.logger.debug(f"🎯 Processing game {i+1}/{len(season_games)}: {game['away_team']} @ {game['home_team']}, Week {game['week']}")
                
                # Step 1: Build temporally safe game context
                universal_data = await self._build_game_context(
                    game['season'], game['week'], 
                    game['home_team'], game['away_team']
                )
                
                # Step 2: Get expert prediction using only historical data
                prediction_record = await self._get_expert_prediction(
                    expert, game, universal_data, learning_mode
                )
                
                # Step 3: Reveal actual outcome
                self._reveal_game_outcome(prediction_record, game)
                
                # Step 4: Calculate accuracy
                self._calculate_prediction_accuracy(prediction_record)
                
                # Step 5: Trigger learning if enabled
                if learning_mode != LearningMode.BASELINE:
                    await self._trigger_learning(
                        expert, prediction_record, universal_data, learning_mode
                    )
                
                # Store prediction record
                results.predictions.append(prediction_record)
                
                # Update rolling metrics
                self._update_rolling_metrics(results)
                
                # Log progress periodically
                if (i + 1) % 20 == 0:
                    current_accuracy = results.overall_accuracy
                    self.logger.info(f"📊 Progress: {i+1}/{len(season_games)} games, current accuracy: {current_accuracy:.1%}")
            
            # Calculate final results
            self._calculate_final_results(results)
            
            self.logger.info(f"✅ Completed {season} backtest for {expert.name}: {results.overall_accuracy:.1%} accuracy")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in season backtest: {e}")
            raise
    
    async def _get_season_games(
        self, 
        season: int, 
        start_week: int, 
        end_week: int, 
        game_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get chronologically ordered games for a season"""
        try:
            # Query all games for the season within week range
            query = self.historical_service.supabase.table('nfl_games') \
                .select('*') \
                .eq('season', season) \
                .gte('week', start_week) \
                .lte('week', end_week) \
                .not_.is_('home_score', 'null') \
                .order('week') \
                .order('game_date')
            
            # Apply additional filters if provided
            if game_filter:
                for key, value in game_filter.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            games = result.data or []
            
            # Sort chronologically to ensure proper temporal sequencing
            games.sort(key=lambda x: (x['week'], x['game_date'], x['game_id']))
            
            return games
            
        except Exception as e:
            self.logger.error(f"❌ Error getting season games: {e}")
            return []
    
    async def _build_game_context(
        self, 
        season: int, 
        week: int, 
        home_team: str, 
        away_team: str
    ) -> UniversalGameData:
        """Build temporally safe game context for prediction"""
        try:
            # Use UniversalGameDataBuilder with temporal cutoff enforcement
            universal_data = self.universal_builder.build_universal_game_data(
                season=season,
                week=week,
                home_team=home_team,
                away_team=away_team,
                include_current_week_stats=False  # Critical: exclude current week
            )
            
            return universal_data
            
        except Exception as e:
            self.logger.error(f"❌ Error building game context: {e}")
            raise
    
    async def _get_expert_prediction(
        self,
        expert: PersonalityDrivenExpert,
        game: Dict[str, Any],
        universal_data: UniversalGameData,
        learning_mode: LearningMode
    ) -> PredictionRecord:
        """Get expert's prediction using only historically available data"""
        try:
            # Get prediction from expert
            if hasattr(expert, 'make_personality_driven_prediction'):
                prediction = expert.make_personality_driven_prediction(universal_data)
            else:
                # Fallback for experts without the method
                prediction = self._make_basic_prediction(expert, universal_data)
            
            # Create prediction record
            record = PredictionRecord(
                game_id=game['game_id'],
                season=game['season'],
                week=game['week'],
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_date=game['game_date'],
                expert_id=expert.expert_id,
                prediction=prediction,
                confidence=prediction.get('confidence', 0.5),
                reasoning=prediction.get('reasoning', []),
                prediction_timestamp=datetime.now().isoformat(),
                learning_mode=learning_mode
            )
            
            return record
            
        except Exception as e:
            self.logger.error(f"❌ Error getting expert prediction: {e}")
            # Return fallback prediction
            return self._create_fallback_prediction(expert, game, learning_mode)
    
    def _reveal_game_outcome(self, record: PredictionRecord, game: Dict[str, Any]):
        """Reveal actual game outcome and store in prediction record"""
        try:
            record.actual_home_score = game['home_score']
            record.actual_away_score = game['away_score']
            
            # Determine actual winner
            if game['home_score'] > game['away_score']:
                record.actual_winner = record.home_team
            elif game['away_score'] > game['home_score']:
                record.actual_winner = record.away_team
            else:
                record.actual_winner = 'tie'
            
            record.outcome_revealed = True
            
            self.logger.debug(f"🏆 Outcome revealed: {record.away_team} {record.actual_away_score}-{record.actual_home_score} {record.home_team}")
            
        except Exception as e:
            self.logger.error(f"❌ Error revealing outcome: {e}")
    
    def _calculate_prediction_accuracy(self, record: PredictionRecord):
        """Calculate accuracy of expert's prediction"""
        try:
            if not record.outcome_revealed:
                return
            
            prediction = record.prediction
            
            # Winner accuracy
            predicted_winner = prediction.get('winner')
            if predicted_winner:
                record.correct_winner = (predicted_winner == record.actual_winner)
            
            # Spread accuracy (if predicted)
            predicted_spread = prediction.get('spread')
            if predicted_spread is not None:
                actual_spread = record.actual_home_score - record.actual_away_score
                # Consider spread correct if within 3 points
                record.correct_spread = abs(predicted_spread - actual_spread) <= 3
            
            # Total accuracy (if predicted)
            predicted_total = prediction.get('total')
            if predicted_total is not None:
                actual_total = record.actual_home_score + record.actual_away_score
                # Consider total correct if within 6 points
                record.correct_total = abs(predicted_total - actual_total) <= 6
            
            # Calculate overall accuracy (weighted combination)
            accuracy_components = []
            if record.correct_winner is not None:
                accuracy_components.append(1.0 if record.correct_winner else 0.0)
            if record.correct_spread is not None:
                accuracy_components.append(1.0 if record.correct_spread else 0.0)
            if record.correct_total is not None:
                accuracy_components.append(1.0 if record.correct_total else 0.0)
            
            if accuracy_components:
                record.overall_accuracy = sum(accuracy_components) / len(accuracy_components)
            else:
                record.overall_accuracy = 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating accuracy: {e}")
            record.overall_accuracy = 0.0
    
    # ... additional helper methods would continue here ...
    
    def _initialize_expert_for_backtest(self, expert: PersonalityDrivenExpert, learning_mode: LearningMode):
        """Initialize expert state for backtesting"""
        # Reset expert state if needed
        if hasattr(expert, 'reset_for_backtest'):
            expert.reset_for_backtest()
        
        # Configure learning mode
        if hasattr(expert, 'set_learning_mode'):
            expert.set_learning_mode(learning_mode)
    
    def _create_empty_results(self, expert_id: str, season: int, learning_mode: LearningMode) -> BacktestResults:
        """Create empty results for when no games are found"""
        return BacktestResults(
            expert_id=expert_id,
            season=season,
            learning_mode=learning_mode
        )
    
    def _update_rolling_metrics(self, results: BacktestResults):
        """Update rolling accuracy metrics"""
        if results.predictions:
            recent_predictions = results.predictions[-10:]  # Last 10 games
            recent_accuracies = [p.overall_accuracy for p in recent_predictions if p.overall_accuracy is not None]
            if recent_accuracies:
                rolling_accuracy = sum(recent_accuracies) / len(recent_accuracies)
                results.rolling_accuracy.append(rolling_accuracy)
    
    def _calculate_final_results(self, results: BacktestResults):
        """Calculate final summary statistics"""
        if not results.predictions:
            return
        
        # Basic counts
        results.total_games = len(results.predictions)
        
        # Accuracy calculations
        correct_winners = sum(1 for p in results.predictions if p.correct_winner)
        correct_spreads = sum(1 for p in results.predictions if p.correct_spread)
        correct_totals = sum(1 for p in results.predictions if p.correct_total)
        
        total_winner_predictions = sum(1 for p in results.predictions if p.correct_winner is not None)
        total_spread_predictions = sum(1 for p in results.predictions if p.correct_spread is not None)
        total_total_predictions = sum(1 for p in results.predictions if p.correct_total is not None)
        
        results.winner_accuracy = correct_winners / total_winner_predictions if total_winner_predictions > 0 else 0.0
        results.spread_accuracy = correct_spreads / total_spread_predictions if total_spread_predictions > 0 else 0.0
        results.total_accuracy = correct_totals / total_total_predictions if total_total_predictions > 0 else 0.0
        
        # Overall accuracy
        overall_accuracies = [p.overall_accuracy for p in results.predictions if p.overall_accuracy is not None]
        results.overall_accuracy = sum(overall_accuracies) / len(overall_accuracies) if overall_accuracies else 0.0
    
    def _make_basic_prediction(self, expert: PersonalityDrivenExpert, universal_data: UniversalGameData) -> Dict[str, Any]:
        """Fallback prediction method for experts without make_personality_driven_prediction"""
        # Simple fallback - favor home team slightly
        return {
            'winner': universal_data.home_team,
            'confidence': 0.55,
            'reasoning': ['Fallback prediction: home field advantage']
        }
    
    def _create_fallback_prediction(self, expert: PersonalityDrivenExpert, game: Dict[str, Any], learning_mode: LearningMode) -> PredictionRecord:
        """Create a fallback prediction record when expert prediction fails"""
        return PredictionRecord(
            game_id=game['game_id'],
            season=game['season'],
            week=game['week'],
            home_team=game['home_team'],
            away_team=game['away_team'],
            game_date=game['game_date'],
            expert_id=expert.expert_id,
            prediction={'winner': game['home_team'], 'confidence': 0.5},
            confidence=0.5,
            reasoning=['Fallback prediction due to error'],
            prediction_timestamp=datetime.now().isoformat(),
            learning_mode=learning_mode
        )
    
    async def _trigger_learning(
        self,
        expert: PersonalityDrivenExpert,
        record: PredictionRecord,
        universal_data: UniversalGameData,
        learning_mode: LearningMode
    ):
        """Trigger learning based on prediction outcome"""
        try:
            if learning_mode == LearningMode.BASELINE:
                return
            
            # Create learning context
            learning_context = {
                'prediction': record.prediction,
                'actual_outcome': {
                    'winner': record.actual_winner,
                    'home_score': record.actual_home_score,
                    'away_score': record.actual_away_score
                },
                'was_correct': record.correct_winner,
                'accuracy': record.overall_accuracy,
                'game_context': universal_data
            }
            
            # Episodic memory storage (if expert has memory service)
            if hasattr(expert, 'memory_service') and expert.memory_service:
                if learning_mode in [LearningMode.MEMORY_ONLY, LearningMode.FULL_LEARNING]:
                    try:
                        # Store game experience in episodic memory
                        await self._store_episodic_memory(expert, learning_context)
                        record.memory_stored = True
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not store episodic memory: {e}")
            
            # Belief revision (full learning mode only)
            if learning_mode == LearningMode.FULL_LEARNING:
                try:
                    # Check if belief revision should be triggered
                    revision_needed = self._should_trigger_belief_revision(record, expert)
                    if revision_needed:
                        await self._trigger_belief_revision(expert, learning_context)
                        record.belief_revision_occurred = True
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not trigger belief revision: {e}")
            
            record.learning_triggered = True
            
        except Exception as e:
            self.logger.error(f"❌ Error triggering learning: {e}")
    
    async def _store_episodic_memory(self, expert: PersonalityDrivenExpert, learning_context: Dict[str, Any]):
        """Store game experience in expert's episodic memory"""
        if hasattr(expert.memory_service, 'store_episodic_memory'):
            await expert.memory_service.store_episodic_memory(
                memory_type='game_result',
                content=learning_context,
                tags=['backtest', 'prediction_outcome']
            )
    
    def _should_trigger_belief_revision(self, record: PredictionRecord, expert: PersonalityDrivenExpert) -> bool:
        """Determine if belief revision should be triggered"""
        # Trigger revision if prediction was significantly wrong
        return record.overall_accuracy is not None and record.overall_accuracy < 0.3
    
    async def _trigger_belief_revision(self, expert: PersonalityDrivenExpert, learning_context: Dict[str, Any]):
        """Trigger belief revision based on prediction outcome"""
        if hasattr(expert, 'revise_beliefs'):
            await expert.revise_beliefs(learning_context)