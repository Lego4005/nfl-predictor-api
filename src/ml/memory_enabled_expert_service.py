"""
Memory-Enabled Expert Prediction Service
Integrates episodic memory, belief revision, and reasoning chain logging
with the personality-driven experts system for learning-based predictions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.personality_driven_experts import (
    PersonalityDrivenExpert, UniversalGameData,
    ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel, ValueHunter, MomentumRider,
    FundamentalistScholar, ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
    TrendReversalSpecialist, PopularNarrativeFader, SharpMoneyFollower, UnderdogChampion,
    ConsensusFollower, MarketInefficiencyExploiter
)
from ml.episodic_memory_manager import EpisodicMemoryManager, EmotionalState, MemoryType
from ml.belief_revision_service import BeliefRevisionService, RevisionType, RevisionTrigger
from ml.reasoning_chain_logger import ReasoningChainLogger, ReasoningFactor, ConfidenceBreakdown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryEnabledExpert(PersonalityDrivenExpert):
    """Enhanced personality expert with integrated memory services"""

    def __init__(self, base_expert: PersonalityDrivenExpert,
                 memory_manager: EpisodicMemoryManager,
                 belief_service: BeliefRevisionService,
                 reasoning_logger: ReasoningChainLogger):
        # Copy all attributes from base expert
        super().__init__(
            expert_id=base_expert.expert_id,
            name=base_expert.name,
            personality_profile=base_expert.personality
        )

        # Add memory services
        self.memory_manager = memory_manager
        self.belief_service = belief_service
        self.reasoning_logger = reasoning_logger

        # Track previous predictions for belief revision
        self.previous_predictions = {}

        # Learning statistics
        self.memory_enhanced_predictions = 0
        self.accuracy_improvements = []

    def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]:
        """Enhanced processing that includes memory retrieval"""
        # Get base personality processing
        base_weights = super().process_through_personality_lens(universal_data)

        # Enhance with memory-based learning (will be implemented in make_prediction)
        return base_weights

    async def make_memory_enhanced_prediction(self, universal_data: UniversalGameData) -> Dict[str, Any]:
        """Make prediction enhanced with episodic memory and learning"""

        game_key = f"{universal_data.away_team}@{universal_data.home_team}"

        # Step 1: Retrieve similar past experiences
        similar_memories = await self._retrieve_relevant_memories(universal_data)

        # Step 2: Make base personality prediction
        base_prediction = self.make_personality_driven_prediction(universal_data)

        # Step 3: Enhance prediction with memory insights
        enhanced_prediction = await self._enhance_prediction_with_memory(
            base_prediction, similar_memories, universal_data
        )

        # Step 4: Check for belief revision
        await self._check_and_log_belief_revision(game_key, enhanced_prediction)

        # Step 5: Log detailed reasoning chain
        reasoning_chain_id = await self._log_enhanced_reasoning_chain(
            universal_data, enhanced_prediction, similar_memories
        )

        # Step 6: Store prediction for future belief revision detection
        self.previous_predictions[game_key] = enhanced_prediction.copy()

        # Add memory metadata
        enhanced_prediction.update({
            'memory_enhanced': True,
            'similar_experiences': len(similar_memories),
            'reasoning_chain_id': reasoning_chain_id,
            'memory_confidence_adjustment': enhanced_prediction.get('memory_confidence_boost', 0),
            'learning_insights': enhanced_prediction.get('learning_insights', [])
        })

        self.memory_enhanced_predictions += 1

        logger.info(f"🧠 {self.name}: Memory-enhanced prediction completed "
                   f"({len(similar_memories)} memories consulted)")

        return enhanced_prediction

    async def _retrieve_relevant_memories(self, universal_data: UniversalGameData) -> List[Dict[str, Any]]:
        """Retrieve relevant episodic memories for current situation"""

        try:
            current_situation = {
                'home_team': universal_data.home_team,
                'away_team': universal_data.away_team,
                'weather_conditions': universal_data.weather,
                'injury_context': universal_data.injuries,
                'market_conditions': universal_data.line_movement
            }

            # Get similar memories from episodic memory manager
            memories = await self.memory_manager.retrieve_similar_memories(
                expert_id=self.expert_id,
                current_situation=current_situation,
                limit=8
            )

            logger.info(f"🔍 {self.name}: Retrieved {len(memories)} relevant memories")
            return memories

        except Exception as e:
            logger.warning(f"⚠️ {self.name}: Could not retrieve memories: {e}")
            return []

    async def _enhance_prediction_with_memory(self, base_prediction: Dict[str, Any],
                                            memories: List[Dict[str, Any]],
                                            universal_data: UniversalGameData) -> Dict[str, Any]:
        """Enhance base prediction using insights from similar memories"""

        enhanced = base_prediction.copy()

        if not memories:
            enhanced['learning_insights'] = ["No similar past experiences found"]
            return enhanced

        # Analyze memory patterns
        memory_analysis = self._analyze_memory_patterns(memories)

        # Apply memory-based learning
        confidence_adjustment = 0
        learning_insights = []

        # Pattern 1: Success rate in similar situations
        if memory_analysis['success_rate'] > 0.7:
            confidence_adjustment += 0.05
            learning_insights.append(f"High success rate ({memory_analysis['success_rate']:.0%}) in similar situations")
        elif memory_analysis['success_rate'] < 0.3:
            confidence_adjustment -= 0.05
            learning_insights.append(f"Low success rate ({memory_analysis['success_rate']:.0%}) in similar situations - being cautious")

        # Pattern 2: Emotional pattern recognition
        dominant_emotion = memory_analysis.get('dominant_emotion')
        if dominant_emotion == 'euphoria' and memory_analysis['success_rate'] > 0.6:
            confidence_adjustment += 0.03
            learning_insights.append("Past euphoric moments were justified - high confidence warranted")
        elif dominant_emotion == 'devastation':
            confidence_adjustment -= 0.03
            learning_insights.append("Remember past devastating misses - tempering confidence")

        # Pattern 3: Weather pattern learning
        weather_pattern = self._analyze_weather_patterns(memories, universal_data.weather)
        if weather_pattern:
            confidence_adjustment += weather_pattern['adjustment']
            learning_insights.append(weather_pattern['insight'])

        # Pattern 4: Market pattern learning
        market_pattern = self._analyze_market_patterns(memories, universal_data.line_movement)
        if market_pattern:
            confidence_adjustment += market_pattern['adjustment']
            learning_insights.append(market_pattern['insight'])

        # Apply confidence adjustment
        original_confidence = enhanced.get('winner_confidence', 0.5)
        enhanced['winner_confidence'] = max(0.1, min(0.95, original_confidence + confidence_adjustment))
        enhanced['memory_confidence_boost'] = confidence_adjustment
        enhanced['learning_insights'] = learning_insights
        enhanced['memory_analysis'] = memory_analysis

        if confidence_adjustment != 0:
            logger.info(f"🎯 {self.name}: Memory adjusted confidence by {confidence_adjustment:+.3f}")

        return enhanced

    def _analyze_memory_patterns(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns from retrieved memories"""

        if not memories:
            return {'success_rate': 0.5, 'total_memories': 0}

        total_memories = len(memories)
        successful_predictions = 0
        emotional_states = []
        confidence_levels = []

        for memory in memories:
            try:
                # Parse memory data
                prediction_data = json.loads(memory.get('prediction_data', '{}'))
                actual_outcome = json.loads(memory.get('actual_outcome', '{}'))

                # Check if prediction was successful
                predicted_winner = prediction_data.get('winner')
                actual_winner = actual_outcome.get('winner')

                if predicted_winner == actual_winner:
                    successful_predictions += 1

                # Collect emotional states and confidence
                emotional_states.append(memory.get('emotional_state', 'neutral'))
                confidence_levels.append(prediction_data.get('confidence', 0.5))

            except Exception as e:
                logger.warning(f"Error parsing memory: {e}")
                continue

        success_rate = successful_predictions / total_memories if total_memories > 0 else 0.5

        # Find dominant emotional state
        from collections import Counter
        emotion_counts = Counter(emotional_states)
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else 'neutral'

        avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0.5

        return {
            'success_rate': success_rate,
            'total_memories': total_memories,
            'successful_predictions': successful_predictions,
            'dominant_emotion': dominant_emotion,
            'avg_past_confidence': avg_confidence,
            'emotion_distribution': dict(emotion_counts)
        }

    def _analyze_weather_patterns(self, memories: List[Dict[str, Any]],
                                current_weather: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze weather-related prediction patterns"""

        if not current_weather or not memories:
            return None

        current_temp = current_weather.get('temperature', 70)
        current_wind = current_weather.get('wind_speed', 0)
        current_conditions = current_weather.get('conditions', 'clear').lower()

        similar_weather_memories = []

        for memory in memories:
            try:
                contextual_factors = json.loads(memory.get('contextual_factors', '[]'))
                for factor in contextual_factors:
                    if factor.get('type') == 'weather':
                        # Check for similar weather conditions
                        if (abs(current_temp - factor.get('temperature', 70)) < 10 and
                            abs(current_wind - factor.get('wind_speed', 0)) < 10):
                            similar_weather_memories.append(memory)
                            break
            except:
                continue

        if len(similar_weather_memories) < 2:
            return None

        # Analyze success rate in similar weather
        weather_analysis = self._analyze_memory_patterns(similar_weather_memories)

        if weather_analysis['success_rate'] > 0.7:
            return {
                'adjustment': 0.02,
                'insight': f"Strong performance in similar weather conditions ({weather_analysis['success_rate']:.0%} success rate)"
            }
        elif weather_analysis['success_rate'] < 0.3:
            return {
                'adjustment': -0.02,
                'insight': f"Poor performance in similar weather conditions ({weather_analysis['success_rate']:.0%} success rate)"
            }

        return None

    def _analyze_market_patterns(self, memories: List[Dict[str, Any]],
                               current_market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze market movement prediction patterns"""

        if not current_market or not memories:
            return None

        current_public_percentage = current_market.get('public_percentage', 50)

        # Look for memories with similar public betting patterns
        similar_market_memories = []

        for memory in memories:
            try:
                prediction_data = json.loads(memory.get('prediction_data', '{}'))
                market_data = prediction_data.get('line_movement', {})

                if market_data and 'public_percentage' in market_data:
                    memory_public = market_data['public_percentage']
                    # Similar if both heavily public or both contrarian
                    if abs(memory_public - current_public_percentage) < 15:
                        similar_market_memories.append(memory)
            except:
                continue

        if len(similar_market_memories) < 2:
            return None

        market_analysis = self._analyze_memory_patterns(similar_market_memories)

        if market_analysis['success_rate'] > 0.7:
            return {
                'adjustment': 0.03,
                'insight': f"Strong track record with similar market conditions ({market_analysis['success_rate']:.0%})"
            }
        elif market_analysis['success_rate'] < 0.3:
            return {
                'adjustment': -0.03,
                'insight': f"Struggles with similar market conditions ({market_analysis['success_rate']:.0%})"
            }

        return None

    async def _check_and_log_belief_revision(self, game_key: str, current_prediction: Dict[str, Any]):
        """Check for belief revision if we have a previous prediction"""

        if game_key not in self.previous_predictions:
            return  # No previous prediction to compare

        try:
            previous_prediction = self.previous_predictions[game_key]

            # Check for belief revision
            revision = await self.belief_service.detect_belief_revision(
                expert_id=self.expert_id,
                game_id=game_key,
                original_prediction=previous_prediction,
                new_prediction=current_prediction,
                trigger_data={'memory_enhanced': True}
            )

            if revision:
                logger.info(f"🔄 {self.name}: Belief revision detected - {revision.revision_type.value} "
                           f"(impact: {revision.impact_score:.2f})")

        except Exception as e:
            logger.warning(f"⚠️ {self.name}: Could not check belief revision: {e}")

    async def _log_enhanced_reasoning_chain(self, universal_data: UniversalGameData,
                                          prediction: Dict[str, Any],
                                          memories: List[Dict[str, Any]]) -> str:
        """Log comprehensive reasoning chain including memory influences"""

        try:
            # Create reasoning factors including memory insights
            reasoning_factors = []

            # Base personality factors
            for factor_name in prediction.get('key_factors', []):
                reasoning_factors.append({
                    'factor': factor_name,
                    'value': f"Personality trait: {factor_name}",
                    'weight': 0.7,
                    'confidence': 0.8,
                    'source': 'personality_analysis'
                })

            # Memory-based factors
            learning_insights = prediction.get('learning_insights', [])
            for i, insight in enumerate(learning_insights):
                reasoning_factors.append({
                    'factor': f'memory_insight_{i+1}',
                    'value': insight,
                    'weight': 0.6,
                    'confidence': 0.75,
                    'source': 'episodic_memory'
                })

            # Weather and market factors if significant
            if universal_data.weather and universal_data.weather.get('wind_speed', 0) > 15:
                reasoning_factors.append({
                    'factor': 'weather_conditions',
                    'value': f"High wind: {universal_data.weather['wind_speed']}mph",
                    'weight': 0.4,
                    'confidence': 0.6,
                    'source': 'environmental_data'
                })

            # Confidence breakdown
            confidence_scores = {
                'overall': prediction.get('winner_confidence', 0.5),
                'winner': prediction.get('winner_confidence', 0.5),
                'spread': prediction.get('winner_confidence', 0.5) * 0.9,
                'total': prediction.get('winner_confidence', 0.5) * 0.8
            }

            # Generate personality-appropriate monologue
            monologue = self._generate_memory_enhanced_monologue(prediction, memories)

            # Log reasoning chain
            chain_id = await self.reasoning_logger.log_reasoning_chain(
                expert_id=self.expert_id,
                game_id=f"{universal_data.away_team}@{universal_data.home_team}",
                prediction=prediction,
                factors=reasoning_factors,
                monologue=monologue,
                confidence=confidence_scores,
                expert_personality=self.personality.decision_style
            )

            return chain_id

        except Exception as e:
            logger.warning(f"⚠️ {self.name}: Could not log reasoning chain: {e}")
            return "unknown"

    def _generate_memory_enhanced_monologue(self, prediction: Dict[str, Any],
                                          memories: List[Dict[str, Any]]) -> str:
        """Generate internal monologue including memory influences"""

        base_reasoning = prediction.get('reasoning', '')
        memory_boost = prediction.get('memory_confidence_boost', 0)
        insights = prediction.get('learning_insights', [])

        # Add memory context to monologue
        if memories and insights:
            memory_context = f" Drawing from {len(memories)} similar past experiences: "
            memory_context += "; ".join(insights[:2])  # Top 2 insights

            if memory_boost > 0:
                memory_context += f". Past success in similar situations boosts my confidence by {memory_boost:.1%}"
            elif memory_boost < 0:
                memory_context += f". Past struggles in similar situations temper my confidence by {abs(memory_boost):.1%}"

            return base_reasoning + memory_context

        return base_reasoning

    async def process_game_outcome(self, game_id: str, actual_outcome: Dict[str, Any],
                                 my_prediction: Dict[str, Any]):
        """Process game outcome and create episodic memory"""

        try:
            # Create episodic memory
            memory = await self.memory_manager.create_episodic_memory(
                expert_id=self.expert_id,
                game_id=game_id,
                prediction_data=my_prediction,
                actual_outcome=actual_outcome
            )

            # Calculate accuracy for learning
            predicted_winner = my_prediction.get('winner_prediction', 'unknown')
            actual_winner = actual_outcome.get('winner', 'unknown')
            was_correct = predicted_winner == actual_winner

            # Track accuracy improvement
            self.accuracy_improvements.append({
                'correct': was_correct,
                'confidence': my_prediction.get('winner_confidence', 0.5),
                'memory_enhanced': my_prediction.get('memory_enhanced', False),
                'timestamp': datetime.utcnow()
            })

            # Log the learning experience
            if was_correct:
                logger.info(f"✅ {self.name}: Correct prediction! Memory: {memory.emotional_state.value}")
            else:
                logger.info(f"❌ {self.name}: Incorrect prediction. Learning from experience: {memory.emotional_state.value}")

            return memory

        except Exception as e:
            logger.error(f"❌ {self.name}: Could not process game outcome: {e}")
            return None


class MemoryEnabledExpertService:
    """Service managing memory-enabled personality experts"""

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config

        # Initialize memory services
        self.memory_manager = EpisodicMemoryManager(db_config)
        self.belief_service = BeliefRevisionService(db_config)
        self.reasoning_logger = ReasoningChainLogger()

        # Create memory-enabled experts
        self.memory_experts = []
        self.initialized = False

    async def initialize(self):
        """Initialize all services and create memory-enabled experts"""

        try:
            # Initialize memory services
            await self.memory_manager.initialize()
            await self.belief_service.initialize()
            # reasoning_logger doesn't need async init

            # Create base personality experts
            base_experts = [
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

            # Wrap each with memory capabilities
            for base_expert in base_experts:
                memory_expert = MemoryEnabledExpert(
                    base_expert=base_expert,
                    memory_manager=self.memory_manager,
                    belief_service=self.belief_service,
                    reasoning_logger=self.reasoning_logger
                )
                self.memory_experts.append(memory_expert)

            self.initialized = True
            logger.info(f"✅ Memory-Enabled Expert Service initialized with {len(self.memory_experts)} experts")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Memory-Enabled Expert Service: {e}")
            raise

    async def generate_memory_enhanced_predictions(self, universal_data: UniversalGameData) -> Dict[str, Any]:
        """Generate predictions from all memory-enabled experts"""

        if not self.initialized:
            await self.initialize()

        game_key = f"{universal_data.away_team}@{universal_data.home_team}"

        # Generate predictions from all experts
        all_predictions = []
        memory_stats = {
            'total_memories_consulted': 0,
            'experts_with_memories': 0,
            'average_confidence_adjustment': 0
        }

        for expert in self.memory_experts:
            try:
                prediction = await expert.make_memory_enhanced_prediction(universal_data)
                all_predictions.append(prediction)

                # Track memory usage
                if prediction.get('memory_enhanced'):
                    memory_stats['total_memories_consulted'] += prediction.get('similar_experiences', 0)
                    if prediction.get('similar_experiences', 0) > 0:
                        memory_stats['experts_with_memories'] += 1
                    memory_stats['average_confidence_adjustment'] += prediction.get('memory_confidence_boost', 0)

            except Exception as e:
                logger.error(f"❌ Error getting prediction from {expert.name}: {e}")
                continue

        # Calculate averages
        if memory_stats['experts_with_memories'] > 0:
            memory_stats['average_confidence_adjustment'] /= memory_stats['experts_with_memories']

        # Calculate consensus
        consensus = self._calculate_memory_enhanced_consensus(all_predictions)

        return {
            'game_info': {
                'matchup': game_key,
                'timestamp': datetime.utcnow().isoformat()
            },
            'all_predictions': all_predictions,
            'consensus': consensus,
            'memory_stats': memory_stats,
            'learning_summary': self._generate_learning_summary(all_predictions)
        }

    def _calculate_memory_enhanced_consensus(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus with memory enhancement weighting"""

        if not predictions:
            return {}

        # Weight predictions by memory enhancement and confidence
        weighted_votes = []
        total_weight = 0

        for pred in predictions:
            confidence = pred.get('winner_confidence', 0.5)
            memory_boost = abs(pred.get('memory_confidence_boost', 0))

            # Higher weight for memory-enhanced predictions with significant learning
            weight = confidence * (1 + memory_boost * 2)

            weighted_votes.append({
                'winner': pred.get('winner_prediction'),
                'weight': weight,
                'expert': pred.get('expert_name')
            })
            total_weight += weight

        # Calculate weighted winner
        winner_weights = {}
        for vote in weighted_votes:
            winner = vote['winner']
            if winner not in winner_weights:
                winner_weights[winner] = 0
            winner_weights[winner] += vote['weight']

        consensus_winner = max(winner_weights.items(), key=lambda x: x[1])[0]
        consensus_confidence = winner_weights[consensus_winner] / total_weight

        return {
            'winner': consensus_winner,
            'confidence': consensus_confidence,
            'expert_count': len(predictions),
            'memory_enhanced_count': sum(1 for p in predictions if p.get('memory_enhanced')),
            'winner_distribution': {k: v/total_weight for k, v in winner_weights.items()}
        }

    def _generate_learning_summary(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of learning insights across all experts"""

        all_insights = []
        confidence_adjustments = []

        for pred in predictions:
            if pred.get('learning_insights'):
                all_insights.extend(pred['learning_insights'])

            if pred.get('memory_confidence_boost'):
                confidence_adjustments.append(pred['memory_confidence_boost'])

        # Aggregate insights
        from collections import Counter
        insight_themes = Counter()

        for insight in all_insights:
            if 'success rate' in insight.lower():
                insight_themes['success_rate_patterns'] += 1
            elif 'weather' in insight.lower():
                insight_themes['weather_patterns'] += 1
            elif 'market' in insight.lower():
                insight_themes['market_patterns'] += 1
            elif 'confidence' in insight.lower():
                insight_themes['confidence_patterns'] += 1

        return {
            'total_insights': len(all_insights),
            'insight_themes': dict(insight_themes),
            'confidence_adjustments': {
                'positive': len([adj for adj in confidence_adjustments if adj > 0]),
                'negative': len([adj for adj in confidence_adjustments if adj < 0]),
                'average': sum(confidence_adjustments) / len(confidence_adjustments) if confidence_adjustments else 0
            },
            'top_insights': all_insights[:5]  # Top 5 insights
        }

    async def process_game_outcomes(self, game_results: List[Dict[str, Any]]):
        """Process multiple game outcomes and update expert memories"""

        if not self.initialized:
            await self.initialize()

        results_summary = {
            'games_processed': 0,
            'memories_created': 0,
            'expert_learning_updates': {}
        }

        for game_result in game_results:
            try:
                game_id = game_result['game_id']
                actual_outcome = game_result['actual_outcome']
                expert_predictions = game_result.get('expert_predictions', [])

                # Process outcome for each expert
                for expert in self.memory_experts:
                    # Find this expert's prediction
                    expert_pred = None
                    for pred in expert_predictions:
                        if pred.get('expert_name') == expert.name:
                            expert_pred = pred
                            break

                    if expert_pred:
                        memory = await expert.process_game_outcome(
                            game_id=game_id,
                            actual_outcome=actual_outcome,
                            my_prediction=expert_pred
                        )

                        if memory:
                            results_summary['memories_created'] += 1

                            # Track expert learning
                            if expert.expert_id not in results_summary['expert_learning_updates']:
                                results_summary['expert_learning_updates'][expert.expert_id] = {
                                    'name': expert.name,
                                    'memories_added': 0,
                                    'recent_accuracy': 0
                                }

                            expert_update = results_summary['expert_learning_updates'][expert.expert_id]
                            expert_update['memories_added'] += 1

                            # Calculate recent accuracy
                            recent_results = expert.accuracy_improvements[-10:]  # Last 10 predictions
                            if recent_results:
                                correct_count = sum(1 for r in recent_results if r['correct'])
                                expert_update['recent_accuracy'] = correct_count / len(recent_results)

                results_summary['games_processed'] += 1

            except Exception as e:
                logger.error(f"❌ Error processing game outcome: {e}")
                continue

        logger.info(f"✅ Processed {results_summary['games_processed']} games, "
                   f"created {results_summary['memories_created']} memories")

        return results_summary

    async def get_expert_memory_analytics(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive memory analytics for experts"""

        if not self.initialized:
            await self.initialize()

        analytics = {}

        experts_to_analyze = [expert for expert in self.memory_experts
                            if expert_id is None or expert.expert_id == expert_id]

        for expert in experts_to_analyze:
            try:
                # Get memory stats from episodic memory manager
                memory_stats = await self.memory_manager.get_memory_stats(expert.expert_id)

                # Get belief revision patterns
                revision_patterns = await self.belief_service.analyze_revision_patterns(expert.expert_id)

                # Calculate learning metrics
                recent_predictions = expert.accuracy_improvements[-20:]  # Last 20
                memory_enhanced_predictions = [p for p in recent_predictions if p.get('memory_enhanced', False)]

                learning_metrics = {
                    'total_predictions': len(expert.accuracy_improvements),
                    'memory_enhanced_predictions': expert.memory_enhanced_predictions,
                    'recent_accuracy': 0,
                    'memory_enhanced_accuracy': 0,
                    'confidence_calibration': 0
                }

                if recent_predictions:
                    learning_metrics['recent_accuracy'] = sum(p['correct'] for p in recent_predictions) / len(recent_predictions)

                if memory_enhanced_predictions:
                    learning_metrics['memory_enhanced_accuracy'] = sum(p['correct'] for p in memory_enhanced_predictions) / len(memory_enhanced_predictions)

                analytics[expert.expert_id] = {
                    'name': expert.name,
                    'personality_style': expert.personality.decision_style,
                    'memory_stats': memory_stats,
                    'revision_patterns': revision_patterns.get(expert.expert_id, {}),
                    'learning_metrics': learning_metrics
                }

            except Exception as e:
                logger.error(f"❌ Error getting analytics for {expert.name}: {e}")
                continue

        return analytics

    async def close(self):
        """Close all services"""
        try:
            await self.memory_manager.close()
            await self.belief_service.close()
            await self.reasoning_logger.close()
            logger.info("✅ Memory-Enabled Expert Service closed")
        except Exception as e:
            logger.error(f"❌ Error closing services: {e}")


# Example usage and testing
async def main():
    """Test the memory-enabled expert service"""

    # Database configuration (adjust for your setup)
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'your_user',
        'password': 'your_password',
        'database': 'nfl_predictor'
    }

    print("🧠 Testing Memory-Enabled Expert Prediction Service")
    print("=" * 60)

    # Initialize service
    service = MemoryEnabledExpertService(db_config)
    await service.initialize()

    # Create test game data
    universal_data = UniversalGameData(
        home_team="KC",
        away_team="BAL",
        game_time="2024-01-15 21:00:00",
        location="Kansas City",
        weather={
            'temperature': 28,
            'wind_speed': 22,
            'conditions': 'Snow',
            'humidity': 85
        },
        injuries={
            'home': [{'position': 'WR', 'severity': 'questionable', 'probability_play': 0.6}],
            'away': [{'position': 'RB', 'severity': 'doubtful', 'probability_play': 0.3}]
        },
        line_movement={
            'opening_line': -2.5,
            'current_line': -1.0,
            'public_percentage': 78
        },
        team_stats={
            'home': {'offensive_yards_per_game': 415, 'defensive_yards_allowed': 298},
            'away': {'offensive_yards_per_game': 389, 'defensive_yards_allowed': 312}
        }
    )

    print(f"🏈 Test Game: {universal_data.away_team} @ {universal_data.home_team}")
    print(f"🌨️ Weather: {universal_data.weather['temperature']}°F, {universal_data.weather['wind_speed']}mph wind, {universal_data.weather['conditions']}")

    # Generate memory-enhanced predictions
    predictions_result = await service.generate_memory_enhanced_predictions(universal_data)

    print(f"\n🎭 Memory-Enhanced Expert Predictions:")
    print("-" * 50)

    for pred in predictions_result['all_predictions'][:5]:  # Show top 5
        memory_indicator = "🧠" if pred.get('memory_enhanced') else "🤖"
        confidence = pred.get('winner_confidence', 0.5)
        memory_boost = pred.get('memory_confidence_boost', 0)

        print(f"{memory_indicator} {pred.get('expert_name', 'Unknown'):12} | "
              f"Winner: {pred.get('winner_prediction', 'N/A'):4} | "
              f"Conf: {confidence:5.1%} ({memory_boost:+.2f}) | "
              f"Memories: {pred.get('similar_experiences', 0)}")

    print(f"\n📊 Memory Statistics:")
    memory_stats = predictions_result['memory_stats']
    print(f"   Total memories consulted: {memory_stats['total_memories_consulted']}")
    print(f"   Experts with memory insights: {memory_stats['experts_with_memories']}")
    print(f"   Average confidence adjustment: {memory_stats['average_confidence_adjustment']:+.3f}")

    print(f"\n🎯 Consensus (Memory-Enhanced):")
    consensus = predictions_result['consensus']
    print(f"   Winner: {consensus.get('winner', 'N/A')}")
    print(f"   Confidence: {consensus.get('confidence', 0):.1%}")
    print(f"   Memory-enhanced experts: {consensus.get('memory_enhanced_count', 0)}/{consensus.get('expert_count', 0)}")

    print(f"\n🧠 Learning Summary:")
    learning = predictions_result['learning_summary']
    print(f"   Total insights generated: {learning['total_insights']}")
    print(f"   Confidence adjustments: {learning['confidence_adjustments']['positive']} positive, {learning['confidence_adjustments']['negative']} negative")

    if learning['top_insights']:
        print(f"   Top insights:")
        for insight in learning['top_insights'][:3]:
            print(f"     • {insight}")

    # Simulate game outcome and learning
    print(f"\n⚽ Simulating Game Outcome for Learning...")
    actual_outcome = {
        'winner': 'BAL',  # Upset!
        'home_score': 17,
        'away_score': 20,
        'margin': 3
    }

    game_results = [{
        'game_id': f"{universal_data.away_team}@{universal_data.home_team}",
        'actual_outcome': actual_outcome,
        'expert_predictions': predictions_result['all_predictions']
    }]

    learning_results = await service.process_game_outcomes(game_results)
    print(f"✅ Learning complete: {learning_results['memories_created']} new memories created")

    # Get analytics
    print(f"\n📈 Expert Learning Analytics:")
    analytics = await service.get_expert_memory_analytics()

    for expert_id, data in list(analytics.items())[:3]:  # Show top 3
        print(f"   {data['name']:15} | "
              f"Memories: {data['memory_stats'].get('total_memories', 0):2} | "
              f"Accuracy: {data['learning_metrics']['recent_accuracy']:5.1%}")

    await service.close()
    print(f"\n🎉 Memory-Enhanced Expert System Test Complete!")

if __name__ == "__main__":
    asyncio.run(main())