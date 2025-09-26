"""
Enhanced Expert Competition Framework
Manages 15 competing experts with dynamic ranking and council selection
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import asyncio
import json
import numpy as np

# Import prediction engine components
from ..prediction_engine.comprehensive_prediction_categories import ExpertPrediction
from ..prediction_engine.category_specific_algorithms import CategorySpecificPredictor

# Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    # Mock for development
    class Client:
        pass

logger = logging.getLogger(__name__)

@dataclass
class ExpertPerformanceMetrics:
    """Comprehensive performance metrics for an expert"""
    expert_id: str
    overall_accuracy: float
    category_accuracies: Dict[str, float]
    confidence_calibration: float
    recent_trend: str  # 'improving', 'declining', 'stable'
    total_predictions: int
    correct_predictions: int
    leaderboard_score: float
    current_rank: int
    peak_rank: int
    consistency_score: float
    specialization_strength: Dict[str, float]
    last_updated: datetime

@dataclass
class CompetitionRound:
    """Single competition round (typically one week)"""
    round_id: str
    week: int
    season: int
    games: List[str]
    expert_performances: Dict[str, ExpertPerformanceMetrics]
    council_members: List[str]
    round_winner: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

class ExpertCompetitionFramework:
    """Main framework for managing expert competition"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase = supabase_client
        self.experts: Dict[str, Any] = {}
        
        # Initialize subsystems
        from .ranking_system import ExpertRankingSystem
        from .council_selector import AICouncilSelector
        from .performance_evaluator import PerformanceEvaluator
        from .voting_consensus import VoteWeightCalculator, ConsensusBuilder
        from .explanation_generator import ExplanationGenerator
        
        self.ranking_system = ExpertRankingSystem()
        self.council_selector = AICouncilSelector()
        self.performance_evaluator = PerformanceEvaluator()
        
        # Initialize AI Council voting components
        self.vote_weight_calculator = VoteWeightCalculator()
        self.consensus_builder = ConsensusBuilder(self.vote_weight_calculator)
        self.explanation_generator = ExplanationGenerator()
        
        # Initialize prediction engine
        self.category_predictor = CategorySpecificPredictor()
        
        # Competition state
        self.current_round: Optional[CompetitionRound] = None
        self.leaderboard: List[ExpertPerformanceMetrics] = []
        self.ai_council: List[str] = []
        
        # Initialize experts
        self._initialize_15_experts()
    
    def _initialize_15_experts(self) -> None:
        """Initialize all 15 personality-driven experts"""
        try:
            # Import existing personality-driven experts
            from ..personality_driven_experts import (
                ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel, 
                ValueHunter, MomentumRider, FundamentalistScholar,
                ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
                TrendReversalSpecialist, PopularNarrativeFader, 
                SharpMoneyFollower, UnderdogChampion, ConsensusFollower,
                MarketInefficiencyExploiter
            )
            
            expert_classes = [
                ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel,
                ValueHunter, MomentumRider, FundamentalistScholar,
                ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
                TrendReversalSpecialist, PopularNarrativeFader,
                SharpMoneyFollower, UnderdogChampion, ConsensusFollower,
                MarketInefficiencyExploiter
            ]
            
            for expert_class in expert_classes:
                try:
                    expert = expert_class()
                    self.experts[expert.expert_id] = expert
                    
                    # Load expert state from database if available
                    if self.supabase:
                        self._load_expert_state(expert)
                        
                except Exception as e:
                    logger.error(f"Failed to initialize expert {expert_class.__name__}: {e}")
            
            logger.info(f"✅ Initialized {len(self.experts)} experts")
            
        except ImportError as e:
            logger.error(f"Failed to import personality experts: {e}")
            # Initialize with mock experts for testing
            self._initialize_mock_experts()
    
    def _initialize_mock_experts(self) -> None:
        """Initialize mock experts for testing when personality experts unavailable"""
        mock_expert_configs = [
            {"id": "conservative_analyzer", "name": "Conservative Analyzer", "personality": "analytical"},
            {"id": "risk_taking_gambler", "name": "Risk Taking Gambler", "personality": "aggressive"},
            {"id": "contrarian_rebel", "name": "Contrarian Rebel", "personality": "contrarian"},
            {"id": "value_hunter", "name": "Value Hunter", "personality": "analytical"},
            {"id": "momentum_rider", "name": "Momentum Rider", "personality": "trend_following"},
            {"id": "fundamentalist_scholar", "name": "Fundamentalist Scholar", "personality": "research_driven"},
            {"id": "chaos_theory_believer", "name": "Chaos Theory Believer", "personality": "complexity_focused"},
            {"id": "gut_instinct_expert", "name": "Gut Instinct Expert", "personality": "intuitive"},
            {"id": "statistics_purist", "name": "Statistics Purist", "personality": "mathematical"},
            {"id": "trend_reversal_specialist", "name": "Trend Reversal Specialist", "personality": "contrarian"},
            {"id": "popular_narrative_fader", "name": "Popular Narrative Fader", "personality": "contrarian"},
            {"id": "sharp_money_follower", "name": "Sharp Money Follower", "personality": "market_focused"},
            {"id": "underdog_champion", "name": "Underdog Champion", "personality": "underdog_focused"},
            {"id": "consensus_follower", "name": "Consensus Follower", "personality": "consensus_driven"},
            {"id": "market_inefficiency_exploiter", "name": "Market Inefficiency Exploiter", "personality": "efficiency_focused"}
        ]
        
        from .mock_expert import MockExpert
        
        for config in mock_expert_configs:
            expert = MockExpert(
                expert_id=config["id"],
                name=config["name"],
                personality=config["personality"]
            )
            self.experts[expert.expert_id] = expert
            
            # Load expert state from database if available
            if self.supabase:
                self._load_expert_state(expert)
        
        logger.info(f"✅ Initialized {len(self.experts)} mock experts")
    
    def _load_expert_state(self, expert: Any) -> None:
        """Load expert's persistent state from database"""
        try:
            if not self.supabase:
                return
            
            result = self.supabase.table('enhanced_expert_models') \
                .select('*') \
                .eq('expert_id', expert.expert_id) \
                .single() \
                .execute()
            
            if result.data:
                # Load performance metrics
                expert.total_predictions = result.data.get('total_predictions', 0)
                expert.correct_predictions = result.data.get('correct_predictions', 0)
                expert.overall_accuracy = result.data.get('overall_accuracy', 0.5)
                expert.current_rank = result.data.get('current_rank', 999)
                expert.peak_rank = result.data.get('peak_rank', 999)
                expert.leaderboard_score = result.data.get('leaderboard_score', 0)
                expert.category_accuracies = result.data.get('category_accuracies', {})
                expert.confidence_calibration = result.data.get('confidence_calibration', 0.5)
                expert.consistency_score = result.data.get('consistency_score', 0.5)
                
                # Load personality traits and algorithm parameters
                expert.personality_traits = result.data.get('personality_traits', {})
                expert.algorithm_parameters = result.data.get('algorithm_parameters', {})
                
                logger.info(f"📚 Loaded state for {expert.name}: {expert.total_predictions} predictions, rank {expert.current_rank}")
        
        except Exception as e:
            logger.warning(f"Could not load state for {expert.name}: {e}")
    
    async def select_ai_council(self, evaluation_window_weeks: int = 4) -> List[str]:
        """Select top 5 performing experts for AI Council"""
        try:
            council_members = await self.council_selector.select_top_performers(
                self.experts,
                evaluation_window_weeks=evaluation_window_weeks
            )
            
            # Update AI Council
            previous_council = self.ai_council.copy()
            self.ai_council = council_members
            
            # Identify promotions and demotions
            promoted = [expert_id for expert_id in council_members if expert_id not in previous_council]
            demoted = [expert_id for expert_id in previous_council if expert_id not in council_members]
            
            # Update database
            if self.supabase:
                await self._update_ai_council_in_db(council_members, promoted, demoted)
            
            # Update expert council participation counts
            for expert_id in council_members:
                if expert_id in self.experts:
                    expert = self.experts[expert_id]
                    expert.council_appearances = getattr(expert, 'council_appearances', 0) + 1
            
            logger.info(f"🏆 Selected AI Council: {[self.experts[expert_id].name for expert_id in council_members]}")
            if promoted:
                logger.info(f"📈 Promoted to council: {[self.experts[expert_id].name for expert_id in promoted]}")
            if demoted:
                logger.info(f"📉 Demoted from council: {[self.experts[expert_id].name for expert_id in demoted]}")
            
            return council_members
            
        except Exception as e:
            logger.error(f"Failed to select AI Council: {e}")
            # Return current council as fallback
            return self.ai_council[:5] if self.ai_council else list(self.experts.keys())[:5]
    
    async def calculate_expert_rankings(self) -> List[ExpertPerformanceMetrics]:
        """Calculate and update expert rankings"""
        try:
            rankings = await self.ranking_system.calculate_rankings(self.experts)
            
            # Update leaderboard
            self.leaderboard = rankings
            
            # Update expert objects with new rankings
            for i, metrics in enumerate(rankings):
                if metrics.expert_id in self.experts:
                    expert = self.experts[metrics.expert_id]
                    expert.current_rank = metrics.current_rank
                    expert.leaderboard_score = metrics.leaderboard_score
                    expert.overall_accuracy = metrics.overall_accuracy
                    
                    # Update peak rank if improved
                    if metrics.current_rank < getattr(expert, 'peak_rank', 999):
                        expert.peak_rank = metrics.current_rank
            
            # Update database
            if self.supabase:
                await self._update_rankings_in_db(rankings)
            
            # Check for significant rank changes and trigger notifications
            await self._check_rank_changes(rankings)
            
            logger.info(f"📊 Updated rankings for {len(rankings)} experts")
            return rankings
            
        except Exception as e:
            logger.error(f"Failed to calculate expert rankings: {e}")
            return self.leaderboard
    
    async def start_competition_round(self, week: int, season: int, games: List[str]) -> CompetitionRound:
        """Start a new competition round"""
        try:
            round_id = f"{season}_week_{week}"
            
            self.current_round = CompetitionRound(
                round_id=round_id,
                week=week,
                season=season,
                games=games,
                expert_performances={},
                council_members=self.ai_council.copy(),
                round_winner=None,
                started_at=datetime.now(),
                completed_at=None
            )
            
            # Store round start in database
            if self.supabase:
                await self._store_round_start(self.current_round)
            
            logger.info(f"🚀 Started competition round {round_id} with {len(games)} games")
            return self.current_round
            
        except Exception as e:
            logger.error(f"Failed to start competition round: {e}")
            raise
    
    async def complete_competition_round(self, game_results: Dict[str, Any]) -> CompetitionRound:
        """Complete current competition round and update performance"""
        try:
            if not self.current_round:
                raise ValueError("No active competition round")
            
            # Evaluate expert performances for this round
            expert_performances = await self.performance_evaluator.evaluate_round_performance(
                self.experts,
                self.current_round.games,
                game_results
            )
            
            self.current_round.expert_performances = expert_performances
            self.current_round.completed_at = datetime.now()
            
            # Determine round winner
            self.current_round.round_winner = self._determine_round_winner(expert_performances)
            
            # Update overall rankings
            await self.calculate_expert_rankings()
            
            # Select new AI Council if needed
            await self.select_ai_council()
            
            # Store round results
            if self.supabase:
                await self._store_round_results(self.current_round)
            
            # Trigger adaptations for underperforming experts
            await self._trigger_adaptation_if_needed(expert_performances)
            
            logger.info(f"🏁 Completed round {self.current_round.round_id}")
            logger.info(f"🥇 Round winner: {self.experts[self.current_round.round_winner].name if self.current_round.round_winner else 'None'}")
            
            return self.current_round
            
        except Exception as e:
            logger.error(f"Failed to complete competition round: {e}")
            raise
    
    async def generate_expert_predictions(self, game_data: Dict[str, Any]) -> Dict[str, ExpertPrediction]:
        """Generate comprehensive predictions from all experts for a game"""
        try:
            game_id = game_data.get('game_id', 'unknown')
            expert_predictions = {}
            
            for expert_id, expert in self.experts.items():
                try:
                    prediction = self.category_predictor.generate_comprehensive_prediction(
                        expert, game_data
                    )
                    expert_predictions[expert_id] = prediction
                    
                    # Store prediction in database if available
                    if self.supabase:
                        await self._store_expert_prediction(prediction)
                    
                    logger.debug(f"Generated prediction for {expert.name}: {prediction.winner_prediction}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate prediction for {expert.name}: {e}")
                    continue
            
            logger.info(f"Generated {len(expert_predictions)} expert predictions for game {game_id}")
            return expert_predictions
            
        except Exception as e:
            logger.error(f"Failed to generate expert predictions: {e}")
            return {}
    
    async def generate_ai_council_consensus(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI Council consensus predictions with explanations"""
        try:
            game_id = game_data.get('game_id', 'unknown')
            
            # Ensure we have an AI Council selected
            if not self.ai_council:
                await self.select_ai_council()
            
            # Generate predictions from all council members
            council_predictions = {}
            council_experts = []
            
            for expert_id in self.ai_council:
                if expert_id in self.experts:
                    expert = self.experts[expert_id]
                    council_experts.append(expert)
                    
                    # Generate prediction for this expert
                    prediction = self.category_predictor.generate_comprehensive_prediction(
                        expert, game_data
                    )
                    council_predictions[expert_id] = prediction
            
            if not council_predictions:
                return {
                    'game_id': game_id,
                    'error': 'No council predictions available',
                    'consensus': {},
                    'explanations': {}
                }
            
            # Calculate vote weights
            expert_confidences = {
                expert_id: pred.confidence_overall 
                for expert_id, pred in council_predictions.items()
            }
            
            vote_weights = self.vote_weight_calculator.calculate_vote_weights(
                council_experts, expert_confidences
            )
            
            expert_weights = {vw.expert_id: vw.normalized_weight for vw in vote_weights}
            
            # Build consensus for key prediction categories
            consensus_categories = [
                'winner_prediction', 'exact_score_home', 'exact_score_away',
                'margin_of_victory', 'against_the_spread', 'totals_over_under',
                'first_half_winner', 'qb_passing_yards', 'qb_touchdowns'
            ]
            
            consensus_results = {}
            for category in consensus_categories:
                consensus = self.consensus_builder.build_consensus(
                    council_predictions, council_experts, category
                )
                consensus_results[category] = consensus
            
            # Generate explanations
            from .explanation_generator import ExplanationContext
            
            explanation_context = ExplanationContext(
                game_data=game_data,
                council_experts=council_experts,
                individual_predictions=council_predictions,
                consensus_results=consensus_results,
                expert_weights=expert_weights
            )
            
            explanations = self.explanation_generator.generate_comprehensive_explanation(
                explanation_context
            )
            
            # Store consensus in database if available
            if self.supabase:
                await self._store_council_consensus(game_id, consensus_results, explanations)
            
            return {
                'game_id': game_id,
                'council_members': [
                    {
                        'expert_id': expert.expert_id,
                        'name': expert.name,
                        'weight': expert_weights.get(expert.expert_id, 0.0)
                    }
                    for expert in council_experts
                ],
                'consensus_predictions': {
                    category: {
                        'value': consensus.consensus_value,
                        'confidence': consensus.confidence_score,
                        'agreement': consensus.agreement_level,
                        'method': consensus.method_used
                    }
                    for category, consensus in consensus_results.items()
                    if consensus.consensus_value is not None
                },
                'explanations': explanations,
                'vote_weights': [
                    {
                        'expert_id': vw.expert_id,
                        'expert_name': next((e.name for e in council_experts if e.expert_id == vw.expert_id), vw.expert_id),
                        'normalized_weight': vw.normalized_weight,
                        'accuracy_component': vw.accuracy_component,
                        'recent_performance_component': vw.recent_performance_component,
                        'confidence_component': vw.confidence_component,
                        'council_tenure_component': vw.council_tenure_component
                    }
                    for vw in vote_weights
                ],
                'consensus_metadata': {
                    'total_categories_predicted': len([c for c in consensus_results.values() if c.consensus_value is not None]),
                    'average_confidence': sum(c.confidence_score for c in consensus_results.values()) / len(consensus_results) if consensus_results else 0,
                    'average_agreement': sum(c.agreement_level for c in consensus_results.values()) / len(consensus_results) if consensus_results else 0,
                    'prediction_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI Council consensus: {e}")
            import traceback
            traceback.print_exc()
            return {
                'game_id': game_data.get('game_id', 'unknown'),
                'error': str(e),
                'consensus': {},
                'explanations': {}
            }
        """Get detailed expert battle analysis for a specific game"""
        try:
            # Get all expert predictions for this game
            expert_predictions = await self._get_expert_predictions_for_game(game_id)
            
            return {
                'game_id': game_id,
                'total_experts': len(expert_predictions),
                'council_consensus': await self._get_council_consensus_for_game(game_id, expert_predictions),
                'expert_disagreements': await self._analyze_expert_disagreements(game_id, expert_predictions),
                'confidence_analysis': await self._analyze_confidence_levels(game_id, expert_predictions),
                'category_analysis': await self._analyze_category_predictions(game_id, expert_predictions),
                'specialization_relevance': await self._analyze_specialization_relevance(game_id, expert_predictions),
                'historical_performance': await self._get_historical_performance_context(game_id),
                'controversy_score': await self._calculate_controversy_score(game_id, expert_predictions),
                'upset_potential': await self._analyze_upset_potential(game_id, expert_predictions)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate expert battle analysis: {e}")
            return {'game_id': game_id, 'error': str(e)}
    
    async def trigger_expert_adaptation(self, expert_id: str, performance_issue: str) -> bool:
        """Trigger adaptation for underperforming expert"""
        try:
            if expert_id not in self.experts:
                logger.error(f"Expert {expert_id} not found")
                return False
            
            expert = self.experts[expert_id]
            
            # Import and use adaptation engine
            from ..self_healing.adaptation_engine import AdaptationEngine
            adaptation_engine = AdaptationEngine(supabase_client=self.supabase)
            
            success = await adaptation_engine.adapt_expert(expert, performance_issue)
            
            if success:
                logger.info(f"🔧 Triggered adaptation for {expert.name} due to {performance_issue}")
            else:
                logger.warning(f"⚠️ Failed to trigger adaptation for {expert.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to trigger expert adaptation: {e}")
            return False
    
    def get_competition_status(self) -> Dict[str, Any]:
        """Get current competition status"""
        try:
            return {
                'total_experts': len(self.experts),
                'ai_council': [
                    {
                        'expert_id': expert_id,
                        'name': self.experts[expert_id].name,
                        'rank': getattr(self.experts[expert_id], 'current_rank', 999),
                        'accuracy': getattr(self.experts[expert_id], 'overall_accuracy', 0.5)
                    }
                    for expert_id in self.ai_council
                ],
                'current_round': {
                    'round_id': self.current_round.round_id if self.current_round else None,
                    'week': self.current_round.week if self.current_round else None,
                    'season': self.current_round.season if self.current_round else None,
                    'games_count': len(self.current_round.games) if self.current_round else 0,
                    'status': 'active' if self.current_round and not self.current_round.completed_at else 'completed'
                },
                'leaderboard_top_5': [
                    {
                        'expert_id': metrics.expert_id,
                        'name': self.experts[metrics.expert_id].name if metrics.expert_id in self.experts else 'Unknown',
                        'rank': metrics.current_rank,
                        'accuracy': metrics.overall_accuracy,
                        'score': metrics.leaderboard_score,
                        'trend': metrics.recent_trend
                    }
                    for metrics in self.leaderboard[:5]
                ],
                'system_health': {
                    'active_experts': len([e for e in self.experts.values() if getattr(e, 'status', 'active') == 'active']),
                    'council_stability': self._calculate_council_stability(),
                    'average_accuracy': np.mean([getattr(e, 'overall_accuracy', 0.5) for e in self.experts.values()]),
                    'prediction_volume': sum([getattr(e, 'total_predictions', 0) for e in self.experts.values()])
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get competition status: {e}")
            return {'error': str(e), 'last_updated': datetime.now().isoformat()}
    
    # Private helper methods
    def _determine_round_winner(self, performances: Dict[str, ExpertPerformanceMetrics]) -> Optional[str]:
        """Determine the winner of the competition round"""
        if not performances:
            return None
        
        try:
            best_performance = max(performances.values(), key=lambda p: p.leaderboard_score)
            return best_performance.expert_id
        except Exception as e:
            logger.error(f"Failed to determine round winner: {e}")
            return None
    
    def _calculate_council_stability(self) -> float:
        """Calculate AI Council stability (how often membership changes)"""
        # This would be calculated from historical council selections
        # For now, return a placeholder value
        return 0.8
    
    async def _trigger_adaptation_if_needed(self, performances: Dict[str, ExpertPerformanceMetrics]) -> None:
        """Trigger adaptations for experts with poor performance"""
        try:
            for expert_id, performance in performances.items():
                # Check if adaptation is needed based on performance criteria
                needs_adaptation = (
                    performance.overall_accuracy < 0.45 or  # Very low accuracy
                    performance.recent_trend == 'declining' or  # Declining trend
                    (performance.current_rank > 10 and performance.current_rank > performance.peak_rank + 3)  # Significant rank drop
                )
                
                if needs_adaptation:
                    issue_type = 'accuracy_drop' if performance.overall_accuracy < 0.45 else 'rank_decline'
                    await self.trigger_expert_adaptation(expert_id, issue_type)
                    
        except Exception as e:
            logger.error(f"Failed to trigger adaptations: {e}")
    
    # Prediction management methods
    async def _store_expert_prediction(self, prediction: ExpertPrediction) -> None:
        """Store expert prediction in database"""
        try:
            if not self.supabase:
                return
            
            prediction_data = prediction.to_dict()
            
            # Store in expert_predictions_enhanced table
            result = self.supabase.table('expert_predictions_enhanced').insert({
                'expert_id': prediction.expert_id,
                'game_id': prediction.game_id,
                'prediction_timestamp': prediction.prediction_timestamp.isoformat(),
                'prediction_data': prediction_data,
                'confidence_overall': prediction.confidence_overall,
                'confidence_by_category': prediction.confidence_by_category,
                'reasoning': prediction.reasoning,
                'key_factors': prediction.key_factors
            }).execute()
            
            logger.debug(f"Stored prediction for {prediction.expert_name} on game {prediction.game_id}")
            
        except Exception as e:
            logger.error(f"Failed to store expert prediction: {e}")
    
    async def _get_expert_predictions_for_game(self, game_id: str) -> Dict[str, ExpertPrediction]:
        """Get all expert predictions for a specific game"""
        try:
            if not self.supabase:
                return {}
            
            result = self.supabase.table('expert_predictions_enhanced') \
                .select('*') \
                .eq('game_id', game_id) \
                .execute()
            
            predictions = {}
            for row in result.data:
                prediction_data = row['prediction_data']
                prediction = ExpertPrediction(
                    expert_id=row['expert_id'],
                    expert_name=prediction_data.get('expert_name', 'Unknown'),
                    game_id=row['game_id'],
                    prediction_timestamp=datetime.fromisoformat(row['prediction_timestamp']),
                    confidence_overall=row['confidence_overall'],
                    reasoning=row['reasoning']
                )
                
                # Populate prediction fields from stored data
                for field, value in prediction_data.items():
                    if hasattr(prediction, field):
                        setattr(prediction, field, value)
                
                predictions[row['expert_id']] = prediction
            
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to get expert predictions for game {game_id}: {e}")
            return {}
    async def _update_ai_council_in_db(self, council_members: List[str], promoted: List[str], demoted: List[str]) -> None:
        """Update AI Council membership in database"""
        try:
            if not self.supabase:
                return
            
            # Store council selection record
            self.supabase.table('ai_council_selections').insert({
                'selection_timestamp': datetime.now().isoformat(),
                'council_members': council_members,
                'promoted_experts': promoted,
                'demoted_experts': demoted,
                'selection_criteria': 'performance_based'
            }).execute()
            
            # Update expert council participation counts
            for expert_id in council_members:
                self.supabase.table('enhanced_expert_models').update({
                    'council_appearances': self.supabase.rpc('increment_council_appearances', {'expert_id': expert_id})
                }).eq('expert_id', expert_id).execute()
            
            logger.info(f"Updated AI Council in database: {len(council_members)} members")
            
        except Exception as e:
            logger.error(f"Failed to update AI Council in database: {e}")
    
    async def _update_rankings_in_db(self, rankings: List[ExpertPerformanceMetrics]) -> None:
        """Update expert rankings in database"""
        try:
            if not self.supabase:
                return
            
            # Update each expert's ranking data
            for metrics in rankings:
                self.supabase.table('enhanced_expert_models').update({
                    'current_rank': metrics.current_rank,
                    'overall_accuracy': metrics.overall_accuracy,
                    'leaderboard_score': metrics.leaderboard_score,
                    'category_accuracies': metrics.category_accuracies,
                    'confidence_calibration': metrics.confidence_calibration,
                    'consistency_score': metrics.consistency_score,
                    'last_ranking_update': datetime.now().isoformat()
                }).eq('expert_id', metrics.expert_id).execute()
            
            # Store ranking snapshot
            self.supabase.table('ranking_history').insert({
                'ranking_timestamp': datetime.now().isoformat(),
                'rankings': [
                    {
                        'expert_id': m.expert_id,
                        'rank': m.current_rank,
                        'score': m.leaderboard_score,
                        'accuracy': m.overall_accuracy
                    }
                    for m in rankings
                ]
            }).execute()
            
            logger.info(f"Updated rankings for {len(rankings)} experts in database")
            
        except Exception as e:
            logger.error(f"Failed to update rankings in database: {e}")
    
    async def _check_rank_changes(self, rankings: List[ExpertPerformanceMetrics]) -> None:
        """Check for significant rank changes and trigger notifications"""
        try:
            significant_changes = []
            
            for metrics in rankings:
                if metrics.expert_id in self.experts:
                    expert = self.experts[metrics.expert_id]
                    previous_rank = getattr(expert, 'previous_rank', metrics.current_rank)
                    
                    rank_change = previous_rank - metrics.current_rank
                    
                    # Check for significant changes (>= 3 positions)
                    if abs(rank_change) >= 3:
                        change_type = 'promotion' if rank_change > 0 else 'demotion'
                        significant_changes.append({
                            'expert_id': metrics.expert_id,
                            'expert_name': expert.name,
                            'change_type': change_type,
                            'previous_rank': previous_rank,
                            'new_rank': metrics.current_rank,
                            'rank_change': rank_change
                        })
                    
                    # Update previous rank for next comparison
                    expert.previous_rank = metrics.current_rank
            
            if significant_changes:
                logger.info(f"Significant rank changes detected: {len(significant_changes)} experts")
                for change in significant_changes:
                    logger.info(f"  {change['expert_name']}: {change['change_type']} from #{change['previous_rank']} to #{change['new_rank']}")
            
        except Exception as e:
            logger.error(f"Failed to check rank changes: {e}")
    
    async def _store_round_start(self, round_data: CompetitionRound) -> None:
        """Store competition round start in database"""
        try:
            if not self.supabase:
                return
            
            self.supabase.table('competition_rounds').insert({
                'round_id': round_data.round_id,
                'week': round_data.week,
                'season': round_data.season,
                'games': round_data.games,
                'council_members': round_data.council_members,
                'started_at': round_data.started_at.isoformat(),
                'status': 'active'
            }).execute()
            
            logger.info(f"Stored round start for {round_data.round_id}")
            
        except Exception as e:
            logger.error(f"Failed to store round start: {e}")
    
    async def _store_round_results(self, round_data: CompetitionRound) -> None:
        """Store competition round results in database"""
        try:
            if not self.supabase:
                return
            
            # Store round completion
            self.supabase.table('competition_rounds').update({
                'completed_at': round_data.completed_at.isoformat(),
                'round_winner': round_data.round_winner,
                'expert_performances': {
                    expert_id: {
                        'overall_accuracy': metrics.overall_accuracy,
                        'leaderboard_score': metrics.leaderboard_score,
                        'current_rank': metrics.current_rank
                    }
                    for expert_id, metrics in round_data.expert_performances.items()
                }
            }).eq('round_id', round_data.round_id).execute()
            
            logger.info(f"Stored results for round {round_data.round_id}")
            
        except Exception as e:
            logger.error(f"Failed to store round results: {e}")
    
    # Analysis methods
    async def _get_council_consensus_for_game(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> Dict[str, Any]:
        """Get AI Council consensus for specific game"""
        try:
            council_predictions = {
                expert_id: predictions[expert_id] 
                for expert_id in self.ai_council 
                if expert_id in predictions
            }
            
            if not council_predictions:
                return {'consensus': 'No council predictions available'}
            
            # Calculate consensus winner
            home_votes = sum(1 for p in council_predictions.values() if p.winner_prediction == 'home')
            away_votes = len(council_predictions) - home_votes
            
            consensus_winner = 'home' if home_votes > away_votes else 'away'
            consensus_strength = max(home_votes, away_votes) / len(council_predictions)
            
            # Calculate average confidence
            avg_confidence = sum(p.confidence_overall for p in council_predictions.values()) / len(council_predictions)
            
            # Calculate spread consensus
            spreads = []
            for prediction in council_predictions.values():
                if prediction.exact_score_home is not None and prediction.exact_score_away is not None:
                    spread = prediction.exact_score_home - prediction.exact_score_away
                    spreads.append(spread)
            
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
            
            return {
                'consensus_winner': consensus_winner,
                'consensus_strength': consensus_strength,
                'home_votes': home_votes,
                'away_votes': away_votes,
                'average_confidence': avg_confidence,
                'consensus_spread': avg_spread,
                'council_size': len(council_predictions)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate council consensus: {e}")
            return {'consensus': 'Error calculating consensus'}
    
    async def _analyze_expert_disagreements(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> Dict[str, Any]:
        """Analyze areas where experts disagree most"""
        try:
            if len(predictions) < 2:
                return {'disagreements': 'Insufficient predictions for analysis'}
            
            # Analyze winner prediction disagreement
            home_predictions = sum(1 for p in predictions.values() if p.winner_prediction == 'home')
            away_predictions = len(predictions) - home_predictions
            winner_disagreement = min(home_predictions, away_predictions) / len(predictions)
            
            # Analyze score spread
            scores = []
            for prediction in predictions.values():
                if prediction.exact_score_home is not None and prediction.exact_score_away is not None:
                    total = prediction.exact_score_home + prediction.exact_score_away
                    scores.append(total)
            
            score_std = np.std(scores) if len(scores) > 1 else 0
            
            # Analyze confidence variance
            confidences = [p.confidence_overall for p in predictions.values()]
            confidence_std = np.std(confidences)
            
            return {
                'winner_disagreement_rate': winner_disagreement,
                'home_predictions': home_predictions,
                'away_predictions': away_predictions,
                'score_variance': score_std,
                'confidence_variance': confidence_std,
                'total_predictions': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze expert disagreements: {e}")
            return {'disagreements': 'Error analyzing disagreements'}
    
    async def _analyze_confidence_levels(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> Dict[str, Any]:
        """Analyze expert confidence levels and calibration"""
        try:
            if not predictions:
                return {'confidence_analysis': 'No predictions available'}
            
            confidences = [p.confidence_overall for p in predictions.values()]
            
            return {
                'average_confidence': np.mean(confidences),
                'confidence_std': np.std(confidences),
                'max_confidence': max(confidences),
                'min_confidence': min(confidences),
                'high_confidence_experts': sum(1 for c in confidences if c > 0.7),
                'low_confidence_experts': sum(1 for c in confidences if c < 0.4),
                'total_experts': len(confidences)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze confidence levels: {e}")
            return {'confidence_analysis': 'Error analyzing confidence'}
    
    async def _analyze_category_predictions(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> Dict[str, Any]:
        """Analyze predictions by category"""
        try:
            if not predictions:
                return {'category_analysis': 'No predictions available'}
            
            category_analysis = {}
            
            # Analyze spread predictions
            spread_predictions = {}
            for expert_id, prediction in predictions.items():
                if prediction.against_the_spread:
                    spread_predictions[expert_id] = prediction.against_the_spread
            
            if spread_predictions:
                home_spread = sum(1 for p in spread_predictions.values() if p == 'home')
                away_spread = sum(1 for p in spread_predictions.values() if p == 'away')
                push_spread = sum(1 for p in spread_predictions.values() if p == 'push')
                
                category_analysis['spread'] = {
                    'home_picks': home_spread,
                    'away_picks': away_spread,
                    'push_picks': push_spread,
                    'consensus': 'home' if home_spread > away_spread else 'away'
                }
            
            # Analyze over/under predictions
            total_predictions = {}
            for expert_id, prediction in predictions.items():
                if prediction.totals_over_under:
                    total_predictions[expert_id] = prediction.totals_over_under
            
            if total_predictions:
                over_picks = sum(1 for p in total_predictions.values() if p == 'over')
                under_picks = sum(1 for p in total_predictions.values() if p == 'under')
                
                category_analysis['totals'] = {
                    'over_picks': over_picks,
                    'under_picks': under_picks,
                    'consensus': 'over' if over_picks > under_picks else 'under'
                }
            
            return category_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze category predictions: {e}")
            return {'category_analysis': 'Error analyzing categories'}
    
    async def _analyze_specialization_relevance(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> Dict[str, Any]:
        """Analyze which expert specializations are most relevant"""
        try:
            if not predictions:
                return {'specialization_relevance': 'No predictions available'}
            
            # Analyze which personality types are most confident
            personality_confidence = {}
            for expert_id, prediction in predictions.items():
                if expert_id in self.experts:
                    expert = self.experts[expert_id]
                    personality = getattr(expert, 'personality', 'unknown')
                    
                    if personality not in personality_confidence:
                        personality_confidence[personality] = []
                    personality_confidence[personality].append(prediction.confidence_overall)
            
            # Calculate average confidence by personality
            avg_confidence_by_personality = {}
            for personality, confidences in personality_confidence.items():
                avg_confidence_by_personality[personality] = np.mean(confidences)
            
            # Find most relevant personalities
            sorted_personalities = sorted(
                avg_confidence_by_personality.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                'personality_relevance': dict(sorted_personalities),
                'most_relevant_personality': sorted_personalities[0][0] if sorted_personalities else 'unknown',
                'confidence_spread': max(avg_confidence_by_personality.values()) - min(avg_confidence_by_personality.values()) if avg_confidence_by_personality else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze specialization relevance: {e}")
            return {'specialization_relevance': 'Error analyzing specializations'}
    
    async def _calculate_controversy_score(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> float:
        """Calculate how controversial/disagreed-upon this game is"""
        try:
            if len(predictions) < 2:
                return 0.0
            
            # Calculate disagreement across multiple dimensions
            winner_disagreement = 0
            confidence_variance = 0
            spread_variance = 0
            
            # Winner disagreement
            home_votes = sum(1 for p in predictions.values() if p.winner_prediction == 'home')
            winner_disagreement = min(home_votes, len(predictions) - home_votes) / len(predictions)
            
            # Confidence variance
            confidences = [p.confidence_overall for p in predictions.values()]
            confidence_variance = np.std(confidences) / np.mean(confidences) if np.mean(confidences) > 0 else 0
            
            # Score variance
            total_scores = []
            for prediction in predictions.values():
                if prediction.exact_score_home is not None and prediction.exact_score_away is not None:
                    total_scores.append(prediction.exact_score_home + prediction.exact_score_away)
            
            if len(total_scores) > 1:
                spread_variance = np.std(total_scores) / np.mean(total_scores) if np.mean(total_scores) > 0 else 0
            
            # Combine into overall controversy score
            controversy_score = (winner_disagreement * 0.5 + confidence_variance * 0.3 + spread_variance * 0.2)
            
            return min(1.0, controversy_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate controversy score: {e}")
            return 0.5
    
    async def _analyze_upset_potential(self, game_id: str, predictions: Dict[str, ExpertPrediction]) -> Dict[str, Any]:
        """Analyze potential for upset based on expert predictions"""
        try:
            if not predictions:
                return {'upset_potential': 'No predictions available'}
            
            # Count contrarian picks (experts picking against public perception)
            contrarian_picks = 0
            low_confidence_picks = 0
            
            for expert_id, prediction in predictions.items():
                if expert_id in self.experts:
                    expert = self.experts[expert_id]
                    
                    # Check if expert has contrarian tendencies and is picking underdog
                    contrarian_tendency = getattr(expert, 'personality_traits', {}).get('contrarian_tendency', 0.5)
                    if hasattr(contrarian_tendency, 'value'):
                        contrarian_tendency = contrarian_tendency.value
                    
                    if contrarian_tendency > 0.7:
                        contrarian_picks += 1
                    
                    if prediction.confidence_overall < 0.6:
                        low_confidence_picks += 1
            
            # Calculate upset indicators
            upset_indicators = {
                'contrarian_experts': contrarian_picks,
                'low_confidence_experts': low_confidence_picks,
                'total_experts': len(predictions),
                'contrarian_percentage': contrarian_picks / len(predictions) if predictions else 0,
                'low_confidence_percentage': low_confidence_picks / len(predictions) if predictions else 0
            }
            
            # Overall upset potential score
            upset_score = (upset_indicators['contrarian_percentage'] * 0.6 + 
                          upset_indicators['low_confidence_percentage'] * 0.4)
            
            upset_indicators['upset_potential_score'] = upset_score
            upset_indicators['upset_risk'] = 'high' if upset_score > 0.6 else 'medium' if upset_score > 0.3 else 'low'
            
            return upset_indicators
            
        except Exception as e:
            logger.error(f"Failed to analyze upset potential: {e}")
            return {'upset_potential': 'Error analyzing upset potential'}
    
    async def _get_historical_performance_context(self, game_id: str) -> Dict[str, Any]:
        """Get historical performance context for similar games"""
        try:
            # This would analyze historical performance for similar game types
            # For now, return placeholder data structure
            return {
                'similar_games_analyzed': 10,
                'average_accuracy_in_similar': 0.65,
                'best_performing_expert_type': 'analytical',
                'historical_context': 'Analysis based on similar matchup types'
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical performance context: {e}")
            return {'historical_context': 'Error retrieving historical data'}


# Usage example
async def main():
    """Example usage of ExpertCompetitionFramework with comprehensive predictions"""
    try:
        # Initialize framework
        framework = ExpertCompetitionFramework()
        
        # Get current status
        status = framework.get_competition_status()
        print(f"Competition Status: {json.dumps(status, indent=2)}")
        
        # Example game data for prediction generation
        sample_game_data = {
            'game_id': 'nfl_2025_week1_chiefs_bills',
            'home_team': 'kansas_city_chiefs',
            'away_team': 'buffalo_bills',
            'spread': -2.5,  # Chiefs favored by 2.5
            'total': 52.5,
            'is_divisional': False,
            'weather': {
                'temperature': 75,
                'wind_speed': 8,
                'precipitation': 0
            },
            'injuries': {
                'home': [],
                'away': [{'player': 'John Doe', 'severity': 'questionable', 'is_starter': True}]
            },
            'travel': {
                'home_rest_days': 7,
                'away_rest_days': 6,
                'travel_distance': 1200
            },
            'venue': {
                'crowd_factor': 1.2,
                'altitude': 800
            },
            'coaching': {
                'home_experience': 8,
                'away_experience': 6
            },
            'home_momentum': 20,
            'away_momentum': -10
        }
        
        # Generate expert predictions
        print("\n=== Generating Expert Predictions ===")
        expert_predictions = await framework.generate_expert_predictions(sample_game_data)
        print(f"Generated {len(expert_predictions)} expert predictions")
        
        # Show sample predictions
        for expert_id, prediction in list(expert_predictions.items())[:3]:
            print(f"\n{prediction.expert_name}:")
            print(f"  Winner: {prediction.winner_prediction}")
            print(f"  Score: {prediction.exact_score_home}-{prediction.exact_score_away}")
            print(f"  Confidence: {prediction.confidence_overall:.2f}")
            print(f"  Reasoning: {prediction.reasoning[:100]}...")
        
        # Get expert battle analysis
        print("\n=== Expert Battle Analysis ===")
        battle_analysis = await framework.get_expert_battle_analysis(sample_game_data['game_id'])
        print(f"Battle Analysis: {json.dumps(battle_analysis, indent=2, default=str)}")
        
        # Start a competition round
        games = [sample_game_data['game_id'], "game_2", "game_3"]
        round_data = await framework.start_competition_round(1, 2025, games)
        print(f"\nStarted round: {round_data.round_id}")
        
        # Select AI Council
        council = await framework.select_ai_council()
        print(f"AI Council: {[framework.experts[expert_id].name for expert_id in council]}")
        
        # Calculate rankings
        rankings = await framework.calculate_expert_rankings()
        print(f"\nTop 5 Rankings:")
        for i, metrics in enumerate(rankings[:5]):
            expert_name = framework.experts[metrics.expert_id].name if metrics.expert_id in framework.experts else 'Unknown'
            print(f"  {i+1}. {expert_name} - Accuracy: {metrics.overall_accuracy:.3f}, Score: {metrics.leaderboard_score:.2f}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())