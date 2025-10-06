"""
Core Reconciliation Service for Automated Learning System

This service implements the mandatory 6-step post-game reconciliation workflow
that runs after every completed NFL game to enable automated learning.

The 6 mandatory steps are:
1. Accuracy Analysis - Compare predictions vs actual outcomes
2. Learnication - Route insights to team_knowledge vs matchup_memories
3. Team Knowledge Updates - Update persistent team attributes
4. Matchup Memory Updates - Update team-vs-team specific memories
5. Memory Decay Application - Apply time and performance-based decay
6. Workflow Completion Logging - Log successful completion

This system ensures the AI gets smarter after every game without manual intervention.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass

from supabase import Client as SupabaseClient


@dataclass
class GameResult:
    """Actual game outcome data"""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    game_date: datetime
    final_stats: Dict[str, Any]


@dataclass
class ExpertPrediction:
    """Expert prediction data with confidence scores"""
    expert_id: str
    game_id: str
    predictions: Dict[str, Any]  # All 30+ prediction categories
    confidence_scores: Dict[str, float]
    reasoning_factors: List[str]


@dataclass
class AccuracyAnalysis:
    """Results of accuracy analysis for a prediction"""
    category: str
    predicted_value: Any
    actual_value: Any
    accuracy_score: float
    confidence_was_appropriate: bool
    contributing_factors: List[str]
    error_magnitude: float
    error_direction: str  # 'over' or 'under'


class ReconciliationService:
    """
    Core service that implements the mandatory post-game reconciliation workflow.

    This service is the heart of the automated learning system - it processes
    every completed game and updates the AI's knowledge base automatically.
    """

    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

    async def process_completed_game(self, game_id: str) -> bool:
        """
        Main entry point for processing a completed game.

        Executes the mandatory 6-step reconciliation workflow:
        1. Retrieve game data and expert predictions
        2. Execute 6-step workflow
        3. Log completion or failure

        Args:
            game_id: Unique identifier for the completed game

        Returns:
            bool: True if workflow completed successfully, False otherwise
        """
        workflow_start_time = datetime.now()

        try:
            self.logger.info(f"Starting reconciliation workflow for game {game_id}")

            # Step 0: Retrieve required data
            game_result = await self._get_game_result(game_id)
            expert_predictions = await self._get_expert_predictions(game_id)

            if not game_result or not expert_predictions:
                self.logger.error(f"Missing data for game {game_id}")
                return False

            # Execute the 6 mandatory steps
            steps_completed = []

            # Step 1: Accuracy Analysis
            accuracy_analyses = await self._step_1_accuracy_analysis(
                game_result, expert_predictions
            )
            steps_completed.append("accuracy_analysis")
            self.logger.info(f"Step 1 completed: Analyzed {len(accuracy_analyses)} predictions")

            # Step 2: Learning Classification
            team_learnings, matchup_learnings = await self._step_2_learning_classification(
                accuracy_analyses, game_result
            )
            steps_completed.append("learning_classification")
            self.logger.info(f"Step 2 completed: {len(team_learnings)} team learnings, {len(matchup_learnings)} matchup learnings")

            # Step 3: Team Knowledge Updates
            await self._step_3_team_knowledge_updates(team_learnings, game_result)
            steps_completed.append("team_knowledge_updates")
            self.logger.info("Step 3 completed: Team knowledge updated")

            # Step 4: Matchup Memory Updates
            await self._step_4_matchup_memory_updates(matchup_learnings, game_result)
            steps_completed.append("matchup_memory_updates")
            self.logger.info("Step 4 completed: Matchup memories updated")

            # Step 5: Memory Decay Application
            await self._step_5_memory_decay_application()
            steps_completed.append("memory_decay_application")
            self.logger.info("Step 5 completed: Memory decay applied")

            # Step 6: Workflow Completion Logging
            await self._step_6_workflow_completion_logging(
                game_id, workflow_start_time, steps_completed, success=True
            )
            steps_completed.append("workflow_completion_logging")

            # Mark game as reconciled
            await self._mark_game_reconciled(game_id)

            workflow_duration = (datetime.now() - workflow_start_time).total_seconds()
            self.logger.info(f"Reconciliation workflow completed for game {game_id} in {workflow_duration:.2f}s")

            return True

        except Exception as e:
            self.logger.error(f"Reconciliation workflow failed for game {game_id}: {str(e)}")

            # Log the failure
            await self._log_workflow_failure(
                game_id, workflow_start_time, str(e), steps_completed
            )

            return False

    async def _get_game_result(self, game_id: str) -> Optional[GameResult]:
        """Retrieve actual game outcome data from nfl_games table"""
        try:
            response = self.supabase.table('nfl_games').select('*').eq('game_id', game_id).execute()

            if not response.data:
                self.logger.error(f"No game data found for {game_id}")
                return None

            game_data = response.data[0]

            return GameResult(
                game_id=game_data['game_id'],
                home_team=game_data['home_team'],
                away_team=game_data['away_team'],
                home_score=game_data['home_score'] or 0,
                away_score=game_data['away_score'] or 0,
                game_date=datetime.fromisoformat(game_data['game_date']),
                final_stats=game_data  # Full game data for detailed analysis
            )

        except Exception as e:
            self.logger.error(f"Error retrieving game result for {game_id}: {str(e)}")
            return None

    async def _get_expert_predictions(self, game_id: str) -> List[ExpertPrediction]:
        """Retrieve all expert predictions for the game"""
        try:
            response = self.supabase.table('expert_reasoning_chains').select('*').eq('game_id', game_id).execute()

            expert_predictions = []
            for prediction_data in response.data:
                expert_predictions.append(ExpertPrediction(
                    expert_id=prediction_data['expert_id'],
                    game_id=prediction_data['game_id'],
                    predictions=prediction_data['prediction'],
                    confidence_scores=prediction_data['confidence_scores'],
                    reasoning_factors=prediction_data['reasoning_factors']
                ))

            self.logger.info(f"Retrieved {len(expert_predictions)} expert predictions for game {game_id}")
            return expert_predictions

        except Exception as e:
            self.logger.error(f"Error retrieving expert predictions for {game_id}: {str(e)}")
            return []

    async def _step_1_accuracy_analysis(
        self,
        game_result: GameResult,
        expert_predictions: List[ExpertPrediction]
    ) -> Dict[str, List[AccuracyAnalysis]]:
        """
        MANDATORY STEP 1: Analyze accuracy of all predictions

        Compares each expert's predictions against actual outcomes across
        all 30+ prediction categories and calculates accuracy scores.
        """
        accuracy_analyses = {}

        for expert_prediction in expert_predictions:
            expert_analyses = []

            # Analyze each prediction category
            for category, predicted_value in expert_prediction.predictions.items():
                actual_value = self._get_actual_value_for_category(category, game_result)

                if actual_value is not None:
                    accuracy_score = self._calculate_accuracy_score(
                        category, predicted_value, actual_value
                    )

                    confidence_score = expert_prediction.confidence_scores.get(category, 0.5)
                    confidence_appropriate = self._validate_confidence_calibration(
                        confidence_score, accuracy_score
                    )

                    analysis = AccuracyAnalysis(
                        category=category,
                        predicted_value=predicted_value,
                        actual_value=actual_value,
                        accuracy_score=accuracy_score,
                        confidence_was_appropriate=confidence_appropriate,
                        contributing_factors=expert_prediction.reasoning_factors,
                        error_magnitude=abs(float(predicted_value) - float(actual_value)) if isinstance(predicted_value, (int, float)) and isinstance(actual_value, (int, float)) else 0,
                        error_direction='over' if isinstance(predicted_value, (int, float)) and isinstance(actual_value, (int, float)) and float(predicted_value) > float(actual_value) else 'under' if isinstance(predicted_value, (int, float)) and isinstance(actual_value, (int, float)) and float(predicted_value) < float(actual_value) else 'neutral'
                    )

                    expert_analyses.append(analysis)

            accuracy_analyses[expert_prediction.expert_id] = expert_analyses

        return accuracy_analyses

    async def _step_2_learning_classification(
        self,
        accuracy_analyses: Dict[str, List[AccuracyAnalysis]],
        game_result: GameResult
    ) -> Tuple[Dict[str, List[Dict]], List[Dict]]:
        """
        MANDATORY STEP 2: Classify learnings as team-specific vs matchup-specific

        Routes successful predictions and insights to the appropriate storage:
        - Team-specific patterns go to team_knowledge table
        - Matchup-specific patterns go to matchup_memories table
        """
        team_learnings = {'home_team': [], 'away_team': []}
        matchup_learnings = []

        for expert_id, analyses in accuracy_analyses.items():
            for analysis in analyses:
                # Focus on successful predictions (accuracy > 0.8)
                if analysis.accuracy_score > 0.8:
                    insights = self._extract_success_insights(analysis, game_result)

                    for insight in insights:
                        if self._is_team_specific_pattern(insight):
                            # Route to team_knowledge
                            affected_team = self._determine_affected_team(insight, game_result)
                            team_learnings[affected_team].append({
                                'expert_id': expert_id,
                                'insight': insight,
                                'validation_score': analysis.accuracy_score,
                                'category': analysis.category,
                                'game_context': {
                                    'game_id': game_result.game_id,
                                    'date': game_result.game_date.isoformat(),
                                    'opponent': game_result.away_team if affected_team == 'home_team' else game_result.home_team
                                }
                            })
                        elif self._is_matchup_specific_pattern(insight):
                            # Route to matchup_memories
                            matchup_learnings.append({
                                'expert_id': expert_id,
                                'insight': insight,
                                'validation_score': analysis.accuracy_score,
                                'category': analysis.category,
                                'matchup_context': {
                                    'home_team': game_result.home_team,
                                    'away_team': game_result.away_team,
                                    'game_id': game_result.game_id,
                                    'date': game_result.game_date.isoformat()
                                }
                            })

                # Handle failed predictions (accuracy < 0.4) - schedule factor decay
                elif analysis.accuracy_score < 0.4:
                    for factor in analysis.contributing_factors:
                        await self._schedule_factor_decay(factor, analysis.error_magnitude)

        return team_learnings, matchup_learnings

    async def _step_3_team_knowledge_updates(
        self,
        team_learnings: Dict[str, List[Dict]],
        game_result: GameResult
    ) -> None:
        """
        MANDATORY STEP 3: Update team knowledge using weighted averages

        Updates persistent team attributes in the team_knowledge table
        using weighted averages based on confidence and recency.
        """
        for team_type, learnings in team_learnings.items():
            team_id = game_result.home_team if team_type == 'home_team' else game_result.away_team

            for learning in learnings:
                expert_id = learning['expert_id']

                # Get or create team knowledge record
                team_knowledge = await self._get_team_knowledge(team_id, expert_id)

                # Update patterns with weighted average
                pattern_key = learning['insight']['pattern']['key']
                new_evidence = learning['validation_score']

                if pattern_key in team_knowledge['pattern_confidence_scores']:
                    # Update existing pattern
                    existing = team_knowledge['pattern_confidence_scores'][pattern_key]
                    sample_size = existing.get('sample_size', 1)

                    # Calculate update weight (more recent evidence gets higher weight)
                    new_weight = self._calculate_update_weight(sample_size, new_evidence)

                    updated_confidence = (
                        existing['confidence'] * (1 - new_weight) +
                        new_evidence * new_weight
                    )

                    team_knowledge['pattern_confidence_scores'][pattern_key] = {
                        'confidence': updated_confidence,
                        'sample_size': sample_size + 1,
                        'last_validated': datetime.now().isoformat(),
                        'recent_accuracy': existing.get('recent_accuracy', [])[-4:] + [new_evidence]
                    }
                else:
                    # Create new pattern
                    team_knowledge['pattern_confidence_scores'][pattern_key] = {
                        'confidence': new_evidence,
                        'sample_size': 1,
                        'created': datetime.now().isoformat(),
                        'last_validated': datetime.now().isoformat(),
                        'recent_accuracy': [new_evidence]
                    }

                # Apply time-based decay to unvalidated patterns
                await self._apply_time_decay(team_knowledge['pattern_confidence_scores'])

                # Save updated team knowledge
                await self._save_team_knowledge(team_id, expert_id, team_knowledge)

    async def _step_4_matchup_memory_updates(
        self,
        matchup_learnings: List[Dict],
        game_result: GameResult
    ) -> None:
        """
        MANDATORY STEP 4: Update matchup memories with rolling 15-game history

        Updates team-vs-team specific memories in the matchup_memories table,
        maintaining a rolling window of the last 15 games per team pairing.
        """
        matchup_id = f"{game_result.home_team}_vs_{game_result.away_team}"

        for learning in matchup_learnings:
            expert_id = learning['expert_id']

            # Create new memory entry
            new_memory = {
                'matchup_id': matchup_id,
                'expert_id': expert_id,
                'game_date': game_result.game_date.date(),
                'pre_game_analysis': {},  # Could be populated from prediction data
                'predictions': learning['insight'],
                'actual_results': {
                    'home_score': game_result.home_score,
                    'away_score': game_result.away_score,
                    'winner': game_result.home_team if game_result.home_score > game_result.away_score else game_result.away_team
                },
                'post_game_insights': learning['insight'],
                'accuracy_scores': {learning['category']: learning['validation_score']},
                'learning_updates': learning['insight']
            }

            # Insert new memory
            await self.supabase.table('matchup_memories').insert(new_memory).execute()

            # Maintain rolling 15-game window
            await self._maintain_matchup_memory_window(matchup_id, expert_id)

    async def _step_5_memory_decay_application(self) -> None:
        """
        MANDATORY STEP 5: Apply memory decay rules

        Applies time-based and performance-based decay to memory patterns:
        - 5% monthly decay for unvalidated patterns
        - Performance-based decay for patterns with <50% accuracy
        - Purge patterns with confidence scores below 20%
        """
        # Apply decay to team knowledge patterns
        team_knowledge_response = self.supabase.table('team_knowledge').select('*').execute()

        for record in team_knowledge_response.data:
            patterns = record['pattern_confidence_scores']
            updated_patterns = {}

            for pattern_key, pattern in patterns.items():
                days_since_validation = (
                    datetime.now() - datetime.fromisoformat(pattern['last_validated'])
                ).days

                # Time-based decay (5% per month)
                if days_since_validation > 30:
                    months_elapsed = days_since_validation / 30
                    decay_factor = 0.95 ** months_elapsed
                    pattern['confidence'] *= decay_factor

                # Performance-based decay
                recent_accuracy = pattern.get('recent_accuracy', [])
                if recent_accuracy and sum(recent_accuracy) / len(recent_accuracy) < 0.5:
                    pattern['confidence'] *= 0.9  # 10% decay for poor performance

                # Keep pattern if confidence is above threshold
                if pattern['confidence'] >= 0.2:
                    updated_patterns[pattern_key] = pattern

            # Update the record
            await self.supabase.table('team_knowledge').update({
                'pattern_confidence_scores': updated_patterns,
                'last_updated': datetime.now().isoformat()
            }).eq('id', record['id']).execute()

    async def _step_6_workflow_completion_logging(
        self,
        game_id: str,
        workflow_start_time: datetime,
        steps_completed: List[str],
        success: bool
    ) -> None:
        """
        MANDATORY STEP 6: Log workflow completion

        Records successful completion of the reconciliation workflow
        in the reconciliation_workflow_logs table for monitoring.
        """
        workflow_end_time = datetime.now()
        workflow_duration = (workflow_end_time - workflow_start_time).total_seconds()

        log_entry = {
            'game_id': game_id,
            'workflow_start_time': workflow_start_time.isoformat(),
            'workflow_end_time': workflow_end_time.isoformat(),
            'workflow_duration': workflow_duration,
            'steps_completed': steps_completed,
            'success': success
        }

        await self.supabase.table('reconciliation_workflow_logs').insert(log_entry).execute()

    # Helper methods

    def _get_actual_value_for_category(self, category: str, game_result: GameResult) -> Any:
        """Extract actual value for a prediction category from game results"""
        category_mappings = {
            'winner': game_result.home_team if game_result.home_score > game_result.away_score else game_result.away_team,
            'home_score': game_result.home_score,
            'away_score': game_result.away_score,
            'total_points': game_result.home_score + game_result.away_score,
            'point_spread': game_result.home_score - game_result.away_score,
            # Add more category mappings as needed
        }

        return category_mappings.get(category)

    def _calculate_accuracy_score(self, category: str, predicted: Any, actual: Any) -> float:
        """Calculate accuracy score for a prediction"""
        if category in ['winner']:
            return 1.0 if predicted == actual else 0.0
        elif category in ['home_score', 'away_score', 'total_points', 'point_spread']:
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                error = abs(predicted - actual)
                # Accuracy decreases with error magnitude
                return max(0.0, 1.0 - (error / 50.0))  # 50-point error = 0 accuracy

        return 0.5  # Default for unknown categories

    def _validate_confidence_calibration(self, confidence: float, accuracy: float) -> bool:
        """Check if confidence was appropriately calibrated"""
        # Simple calibration check - confidence should roughly match accuracy
        return abs(confidence - accuracy) < 0.3

    def _extract_success_insights(self, analysis: AccuracyAnalysis, game_result: GameResult) -> List[Dict]:
        """Extract actionable insights from successful predictions"""
        insights = []

        if analysis.accuracy_score > 0.8:
            insight = {
                'pattern': {
                    'key': f"{analysis.category}_success_pattern",
                    'description': f"Successful {analysis.category} prediction pattern",
                    'factors': analysis.contributing_factors
                },
                'validation_score': analysis.accuracy_score,
                'context': {
                    'category': analysis.category,
                    'predicted': analysis.predicted_value,
                    'actual': analysis.actual_value
                }
            }
            insights.append(insight)

        return insights

    def _is_team_specific_pattern(self, insight: Dict) -> bool:
        """Determine if an insight is team-specific"""
        team_specific_categories = [
            'home_advantage', 'offensive_style', 'defensive_strength',
            'coaching_tendencies', 'player_performance'
        ]

        return any(category in insight['pattern']['key'] for category in team_specific_categories)

    def _is_matchup_specific_pattern(self, insight: Dict) -> bool:
        """Determine if an insight is matchup-specific"""
        matchup_specific_categories = [
            'head_to_head', 'style_matchup', 'historical_performance',
            'rivalry_factor', 'divisional_game'
        ]

        return any(category in insight['pattern']['key'] for category in matchup_specific_categories)

    def _determine_affected_team(self, insight: Dict, game_result: GameResult) -> str:
        """Determine which team the insight applies to"""
        # Simple heuristic - could be made more sophisticated
        if 'home' in insight['pattern']['key'].lower():
            return 'home_team'
        elif 'away' in insight['pattern']['key'].lower():
            return 'away_team'
        else:
            return 'home_team'  # Default

    async def _schedule_factor_decay(self, factor: str, error_magnitude: float) -> None:
        """Schedule decay for factors that contributed to failed predictions"""
        # This could be implemented as a separate decay scheduling system
        self.logger.info(f"Scheduling decay for factor {factor} with error magnitude {error_magnitude}")

    async def _get_team_knowledge(self, team_id: str, expert_id: str) -> Dict:
        """Get or create team knowledge record"""
        response = self.supabase.table('team_knowledge').select('*').eq('team_id', team_id).eq('expert_id', expert_id).execute()

        if response.data:
            return response.data[0]
        else:
            # Create new record
            new_record = {
                'team_id': team_id,
                'expert_id': expert_id,
                'current_injuries': {},
                'player_stats': {},
                'home_advantage_factors': {},
                'coaching_tendencies': {},
                'pattern_confidence_scores': {}
            }

            insert_response = await self.supabase.table('team_knowledge').insert(new_record).execute()
            return insert_response.data[0]

    def _calculate_update_weight(self, sample_size: int, new_evidence: float) -> float:
        """Calculate weight for updating existing patterns"""
        # More samples = lower weight for new evidence (more stable)
        # Higher confidence in new evidence = higher weight
        base_weight = 1.0 / (1.0 + sample_size * 0.1)
        confidence_multiplier = new_evidence  # Higher accuracy gets more weight

        return min(0.5, base_weight * confidence_multiplier)

    async def _apply_time_decay(self, patterns: Dict) -> None:
        """Apply time-based decay to patterns"""
        current_time = datetime.now()

        for pattern_key, pattern in patterns.items():
            last_validated = datetime.fromisoformat(pattern['last_validated'])
            days_elapsed = (current_time - last_validated).days

            if days_elapsed > 30:
                months_elapsed = days_elapsed / 30
                decay_factor = 0.95 ** months_elapsed
                pattern['confidence'] *= decay_factor

    async def _save_team_knowledge(self, team_id: str, expert_id: str, team_knowledge: Dict) -> None:
        """Save updated team knowledge to database"""
        await self.supabase.table('team_knowledge').update({
            'current_injuries': team_knowledge['current_injuries'],
            'player_stats': team_knowledge['player_stats'],
            'home_advantage_factors': team_knowledge['home_advantage_factors'],
            'coaching_tendencies': team_knowledge['coaching_tendencies'],
            'pattern_confidence_scores': team_knowledge['pattern_confidence_scores'],
            'last_updated': datetime.now().isoformat()
        }).eq('team_id', team_id).eq('expert_id', expert_id).execute()

    async def _maintain_matchup_memory_window(self, matchup_id: str, expert_id: str) -> None:
        """Maintain rolling 15-game window for matchup memories"""
        # Get all memories for this matchup and expert
        response = self.supabase.table('matchup_memories').select('*').eq('matchup_id', matchup_id).eq('expert_id', expert_id).order('game_date', desc=True).execute()

        # Keep only the most recent 15 games
        if len(response.data) > 15:
            memories_to_delete = response.data[15:]
            for memory in memories_to_delete:
                await self.supabase.table('matchup_memories').delete().eq('id', memory['id']).execute()

    async def _mark_game_reconciled(self, game_id: str) -> None:
        """Mark game as reconciled in nfl_games table"""
        await self.supabase.table('nfl_games').update({
            'reconciliation_completed': True,
            'reconciliation_timestamp': datetime.now().isoformat()
        }).eq('game_id', game_id).execute()

    async def _log_workflow_failure(
        self,
        game_id: str,
        workflow_start_time: datetime,
        error_message: str,
        completed_steps: List[str]
    ) -> None:
        """Log workflow failure for debugging"""
        failure_entry = {
            'game_id': game_id,
            'workflow_start_time': workflow_start_time.isoformat(),
            'failure_time': datetime.now().isoformat(),
            'error_message': error_message,
            'completed_steps': completed_steps,
            'failed_step': completed_steps[-1] if completed_steps else 'initialization',
            'retry_count': 0
        }

        await self.supabase.table('workflow_failures').insert(failure_entry).execute()
