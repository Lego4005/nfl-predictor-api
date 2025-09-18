"""
Autonomous Expert System - Complete Integration with Supabase
Connects personality-driven experts with persistent memory, learning, and tool access
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Supabase client
from supabase import create_client, Client

# Expert components
from ml.personality_driven_experts import (
    ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel, ValueHunter, MomentumRider,
    FundamentalistScholar, ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
    TrendReversalSpecialist, PopularNarrativeFader, SharpMoneyFollower, UnderdogChampion,
    ConsensusFollower, MarketInefficiencyExploiter, UniversalGameData
)
from ml.expert_memory_service import ExpertMemoryService

logger = logging.getLogger(__name__)


class AutonomousExpertSystem:
    """
    Complete autonomous expert system with:
    - 15 personality-driven experts
    - Persistent memory in Supabase
    - Historical learning from past predictions
    - Tool access for external data
    - Peer learning between experts
    - Evolution tracking
    """

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize the autonomous expert system with Supabase integration"""

        # Initialize Supabase client
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.memory_service = ExpertMemoryService(self.supabase)
            self.connected_to_db = True
            logger.info("🧠 Autonomous Expert System connected to Supabase")
        else:
            self.supabase = None
            self.memory_service = None
            self.connected_to_db = False
            logger.warning("⚠️ Running in offline mode - no persistent memory")

        # Initialize all 15 personality experts with memory service
        self.experts = self._initialize_experts()

        # Track active predictions
        self.active_predictions = {}

        logger.info(f"✅ Initialized {len(self.experts)} autonomous personality experts")

    def _initialize_experts(self) -> List:
        """Initialize all 15 personality experts with memory service"""
        experts = [
            ConservativeAnalyzer(memory_service=self.memory_service),     # The Analyst
            RiskTakingGambler(memory_service=self.memory_service),        # The Gambler
            ContrarianRebel(memory_service=self.memory_service),          # The Rebel
            ValueHunter(memory_service=self.memory_service),              # The Hunter
            MomentumRider(memory_service=self.memory_service),            # The Rider
            FundamentalistScholar(memory_service=self.memory_service),    # The Scholar
            ChaosTheoryBeliever(memory_service=self.memory_service),      # The Chaos
            GutInstinctExpert(memory_service=self.memory_service),        # The Intuition
            StatisticsPurist(memory_service=self.memory_service),         # The Quant
            TrendReversalSpecialist(memory_service=self.memory_service),  # The Reversal
            PopularNarrativeFader(memory_service=self.memory_service),    # The Fader
            SharpMoneyFollower(memory_service=self.memory_service),       # The Sharp
            UnderdogChampion(memory_service=self.memory_service),         # The Underdog
            ConsensusFollower(memory_service=self.memory_service),        # The Consensus
            MarketInefficiencyExploiter(memory_service=self.memory_service) # The Exploiter
        ]

        # Load expert states from database if connected
        if self.connected_to_db:
            for expert in experts:
                self._load_expert_state(expert)

        return experts

    def _load_expert_state(self, expert):
        """Load expert state from database"""
        try:
            if not self.connected_to_db:
                return

            # Get expert data from database
            result = self.supabase.table('personality_experts') \
                .select('*') \
                .eq('expert_id', expert.expert_id) \
                .single() \
                .execute()

            if result.data:
                expert.loaded_weights = result.data.get('current_weights', {})
                expert.performance_stats = result.data.get('performance_stats', {})
                logger.info(f"📚 Loaded state for {expert.name}")

        except Exception as e:
            logger.warning(f"Could not load state for {expert.name}: {e}")

    async def generate_predictions(self, home_team: str, away_team: str,
                                  game_data: Dict = None) -> Dict:
        """Generate predictions from all autonomous experts with learning"""

        # Create game ID
        game_id = f"{away_team}@{home_team}_{datetime.now().strftime('%Y%m%d')}"

        # Convert to UniversalGameData format
        universal_data = self._create_universal_data(home_team, away_team, game_data or {})

        # Collect predictions from all experts
        all_predictions = []

        if self.connected_to_db:
            # Async predictions with memory and tool access
            tasks = []
            for expert in self.experts:
                task = self._get_expert_prediction_async(expert, universal_data, game_id)
                tasks.append(task)

            all_predictions = await asyncio.gather(*tasks)
        else:
            # Sync predictions without database features
            for expert in self.experts:
                prediction = expert.make_personality_driven_prediction_sync(universal_data)
                all_predictions.append({
                    'expert_id': expert.expert_id,
                    'name': expert.name,
                    'prediction': prediction,
                    'personality': {trait: t.value for trait, t in expert.personality.traits.items()}
                })

        # Store active predictions for later learning
        self.active_predictions[game_id] = {
            'timestamp': datetime.now().isoformat(),
            'predictions': all_predictions
        }

        # Calculate consensus
        consensus = self._calculate_consensus(all_predictions)

        return {
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'expert_predictions': all_predictions,
            'consensus': consensus,
            'using_memory': self.connected_to_db,
            'timestamp': datetime.now().isoformat()
        }

    async def _get_expert_prediction_async(self, expert, universal_data, game_id) -> Dict:
        """Get prediction from expert with memory and learning"""
        try:
            # Make prediction with full features
            prediction = await expert.make_personality_driven_prediction(universal_data, game_id)

            # Get performance stats if available
            performance = {}
            if self.memory_service:
                performance = self.memory_service.get_expert_performance_stats(expert.expert_id)

            return {
                'expert_id': expert.expert_id,
                'name': expert.name,
                'prediction': prediction,
                'personality': {trait: t.value for trait, t in expert.personality.traits.items()},
                'performance': performance,
                'used_memory': True,
                'used_tools': bool(expert.tools_cache)
            }

        except Exception as e:
            logger.error(f"Error getting prediction from {expert.name}: {e}")
            # Fallback to sync prediction
            prediction = expert.make_personality_driven_prediction_sync(universal_data)
            return {
                'expert_id': expert.expert_id,
                'name': expert.name,
                'prediction': prediction,
                'personality': {trait: t.value for trait, t in expert.personality.traits.items()},
                'performance': {},
                'used_memory': False,
                'used_tools': False
            }

    async def process_game_result(self, game_id: str, actual_result: Dict):
        """Process actual game results for learning"""
        if not self.connected_to_db or not self.memory_service:
            logger.warning("Cannot process results without database connection")
            return

        try:
            # Trigger learning for all experts
            await self.memory_service.learn_from_result(game_id, actual_result)

            # Find successful predictions for peer learning
            if game_id in self.active_predictions:
                predictions = self.active_predictions[game_id]['predictions']

                for pred_data in predictions:
                    # Calculate how well this prediction did
                    score = self._score_prediction(pred_data['prediction'], actual_result)

                    # Share successful predictions (score > 0.7)
                    if score > 0.7:
                        await self.memory_service.share_peer_learning(
                            pred_data['expert_id'],
                            game_id
                        )

                # Clean up active predictions
                del self.active_predictions[game_id]

            logger.info(f"🎓 Processed learning for game {game_id}")

        except Exception as e:
            logger.error(f"Error processing game result: {e}")

    def _score_prediction(self, prediction: Dict, actual_result: Dict) -> float:
        """Score a prediction against actual result"""
        score = 0.0
        components = 0

        # Winner (40% weight)
        if 'winner_prediction' in prediction and 'winner' in actual_result:
            if prediction['winner_prediction'] == actual_result['winner']:
                score += 0.4
            components += 1

        # Spread (30% weight)
        if 'spread_prediction' in prediction and 'actual_spread' in actual_result:
            spread_error = abs(prediction['spread_prediction'] - actual_result['actual_spread'])
            spread_score = max(0, 1 - (spread_error / 14))  # 14 points = 0 score
            score += 0.3 * spread_score
            components += 1

        # Total (30% weight)
        if 'total_prediction' in prediction and 'actual_total' in actual_result:
            total_error = abs(prediction['total_prediction'] - actual_result['actual_total'])
            total_score = max(0, 1 - (total_error / 20))  # 20 points = 0 score
            score += 0.3 * total_score
            components += 1

        return score if components > 0 else 0.5

    def _calculate_consensus(self, predictions: List[Dict]) -> Dict:
        """Calculate consensus from all expert predictions"""
        if not predictions:
            return {}

        # Extract predictions
        winners = []
        spreads = []
        totals = []
        confidences = []

        for pred_data in predictions:
            pred = pred_data['prediction']
            if 'winner_prediction' in pred:
                winners.append(pred['winner_prediction'])
            if 'spread_prediction' in pred:
                spreads.append(pred['spread_prediction'])
            if 'total_prediction' in pred:
                totals.append(pred['total_prediction'])
            if 'winner_confidence' in pred:
                confidences.append(pred['winner_confidence'])

        # Calculate consensus
        from collections import Counter

        consensus = {}

        if winners:
            winner_counts = Counter(winners)
            consensus['winner'] = winner_counts.most_common(1)[0][0]
            consensus['winner_agreement'] = winner_counts.most_common(1)[0][1] / len(winners)

        if spreads:
            consensus['spread'] = sum(spreads) / len(spreads)
            consensus['spread_std'] = self._calculate_std(spreads)

        if totals:
            consensus['total'] = sum(totals) / len(totals)
            consensus['total_std'] = self._calculate_std(totals)

        if confidences:
            consensus['avg_confidence'] = sum(confidences) / len(confidences)
            consensus['confidence_range'] = (min(confidences), max(confidences))

        return consensus

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _create_universal_data(self, home_team: str, away_team: str, game_data: Dict) -> UniversalGameData:
        """Create UniversalGameData from game data"""
        return UniversalGameData(
            home_team=home_team,
            away_team=away_team,
            game_time=game_data.get('game_time', datetime.now().isoformat()),
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

    def get_expert_details(self) -> List[Dict]:
        """Get details about all experts"""
        details = []

        for expert in self.experts:
            expert_info = {
                'expert_id': expert.expert_id,
                'name': expert.name,
                'personality_traits': {trait: t.value for trait, t in expert.personality.traits.items()},
                'decision_style': expert.personality.decision_style,
                'learning_rate': expert.personality.learning_rate
            }

            # Add performance if connected to database
            if self.memory_service:
                expert_info['performance'] = self.memory_service.get_expert_performance_stats(expert.expert_id)

            details.append(expert_info)

        return details

    async def run_learning_cycle(self):
        """Run a complete learning cycle for all experts"""
        if not self.connected_to_db:
            logger.warning("Learning cycle requires database connection")
            return

        logger.info("🔄 Running learning cycle for all experts...")

        # Process learning queue
        await self.memory_service._process_learning_queue()

        logger.info("✅ Learning cycle complete")


# Factory function for creating the system
def create_autonomous_expert_system(supabase_url: str = None, supabase_key: str = None):
    """Create an autonomous expert system with optional Supabase integration"""
    return AutonomousExpertSystem(supabase_url, supabase_key)