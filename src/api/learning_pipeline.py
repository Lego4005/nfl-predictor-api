"""
Real-Time Learning Pipeline for Personality-Driven Expert System
Processes game results to enable autonomous expert learning and evolution
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import autonomous expert system
from ml.autonomous_expert_system import AutonomousExpertSystem
from ml.expert_memory_service import ExpertMemoryService

# Import Supabase client
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["learning"])

# Initialize Supabase and expert system
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    expert_system = AutonomousExpertSystem(SUPABASE_URL, SUPABASE_KEY)
    memory_service = ExpertMemoryService(supabase)
    logger.info("🧠 Learning Pipeline connected to Supabase")
else:
    supabase = None
    expert_system = AutonomousExpertSystem()
    memory_service = None
    logger.warning("⚠️ Learning Pipeline running in offline mode")


# Pydantic Models
class GameResult(BaseModel):
    """Actual game result for learning"""
    winner: str = Field(..., description="Team that won")
    final_score: Dict[str, int] = Field(..., description="Final scores {home: X, away: Y}")
    actual_spread: float = Field(..., description="Actual point spread (negative = home favored)")
    actual_total: float = Field(..., description="Actual total points scored")
    key_events: Optional[List[str]] = Field(default=[], description="Important game events")
    weather_impact: Optional[bool] = Field(default=False, description="Whether weather was a factor")
    injuries_impact: Optional[bool] = Field(default=False, description="Whether injuries affected outcome")


class LearningResponse(BaseModel):
    """Response after processing learning"""
    game_id: str
    experts_updated: int
    learning_tasks_created: int
    peer_learning_shared: int
    average_performance: float
    best_expert: Dict[str, Any]
    worst_expert: Dict[str, Any]
    consensus_accuracy: float


class ExpertPerformanceUpdate(BaseModel):
    """Performance update for an expert"""
    expert_id: str
    game_id: str
    prediction_score: float
    weight_adjustments: Dict[str, float]
    new_accuracy: float
    learning_triggered: bool


class PeerLearningEvent(BaseModel):
    """Peer learning knowledge transfer"""
    teacher_id: str
    learner_ids: List[str]
    game_id: str
    knowledge_type: str
    success_factors: List[str]


# Endpoints

@router.post("/games/{game_id}/results", response_model=LearningResponse)
async def process_game_results(
    game_id: str,
    result: GameResult,
    background_tasks: BackgroundTasks
):
    """
    Process actual game results to trigger expert learning

    This endpoint:
    1. Scores each expert's prediction against actual results
    2. Updates expert weights based on performance
    3. Triggers peer learning for successful predictions
    4. Records algorithm evolution
    5. Updates competition rankings
    """
    try:
        # Validate game_id format
        if '@' not in game_id or '_' not in game_id:
            raise HTTPException(400, "Invalid game_id format. Expected: 'AWAY@HOME_YYYYMMDD'")

        # Parse teams from game_id
        parts = game_id.split('_')[0].split('@')
        away_team = parts[0]
        home_team = parts[1]

        # Calculate actual values
        home_score = result.final_score['home']
        away_score = result.final_score['away']
        actual_winner = home_team if home_score > away_score else away_team
        actual_spread = away_score - home_score  # Negative = home favored
        actual_total = home_score + away_score

        # Prepare actual result data
        actual_result = {
            'winner': actual_winner,
            'home_score': home_score,
            'away_score': away_score,
            'actual_spread': actual_spread,
            'actual_total': actual_total,
            'key_events': result.key_events,
            'weather_impact': result.weather_impact,
            'injuries_impact': result.injuries_impact
        }

        # Process learning asynchronously
        if expert_system.connected_to_db:
            # Trigger learning for all experts
            await expert_system.process_game_result(game_id, actual_result)

            # Get performance stats for response
            performance_stats = await _calculate_performance_stats(game_id, actual_result)

            # Trigger background learning tasks
            background_tasks.add_task(
                _process_advanced_learning,
                game_id,
                actual_result,
                performance_stats
            )

            return LearningResponse(
                game_id=game_id,
                experts_updated=15,  # All personality experts
                learning_tasks_created=performance_stats['learning_tasks'],
                peer_learning_shared=performance_stats['peer_shares'],
                average_performance=performance_stats['avg_score'],
                best_expert=performance_stats['best_expert'],
                worst_expert=performance_stats['worst_expert'],
                consensus_accuracy=performance_stats['consensus_accuracy']
            )
        else:
            # Offline mode - limited learning
            logger.warning(f"Cannot process learning for {game_id} - no database connection")
            return LearningResponse(
                game_id=game_id,
                experts_updated=0,
                learning_tasks_created=0,
                peer_learning_shared=0,
                average_performance=0.5,
                best_expert={'expert_id': 'unknown', 'score': 0},
                worst_expert={'expert_id': 'unknown', 'score': 0},
                consensus_accuracy=0.5
            )

    except Exception as e:
        logger.error(f"Error processing game results: {e}")
        raise HTTPException(500, f"Failed to process learning: {str(e)}")


@router.get("/experts/{expert_id}/evolution")
async def get_expert_evolution(expert_id: str, limit: int = 10):
    """
    Get evolution history for a specific expert
    Shows how their algorithm has changed over time
    """
    if not supabase:
        raise HTTPException(503, "Database connection required")

    try:
        result = supabase.table('expert_evolution') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .order('version', desc=True) \
            .limit(limit) \
            .execute()

        return {
            'expert_id': expert_id,
            'evolution_history': result.data,
            'total_versions': len(result.data),
            'latest_version': result.data[0]['version'] if result.data else 0
        }
    except Exception as e:
        logger.error(f"Error fetching evolution: {e}")
        raise HTTPException(500, "Failed to fetch evolution history")


@router.get("/experts/performance/summary")
async def get_performance_summary():
    """
    Get performance summary for all personality experts
    """
    if not expert_system.connected_to_db:
        raise HTTPException(503, "Database connection required")

    try:
        experts = expert_system.get_expert_details()

        # Sort by performance
        experts_sorted = sorted(
            experts,
            key=lambda x: x.get('performance', {}).get('avg_score', 0.5),
            reverse=True
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'total_experts': len(experts),
            'leaderboard': experts_sorted[:5],  # Top 5
            'strugglers': experts_sorted[-3:],   # Bottom 3
            'most_improved': _find_most_improved(experts),
            'most_consistent': _find_most_consistent(experts),
            'personality_performance': _analyze_personality_performance(experts)
        }
    except Exception as e:
        logger.error(f"Error fetching performance summary: {e}")
        raise HTTPException(500, "Failed to fetch performance summary")


@router.post("/experts/learning/trigger")
async def trigger_learning_cycle(background_tasks: BackgroundTasks):
    """
    Manually trigger a learning cycle for all experts
    Useful for processing backlog or forcing updates
    """
    if not expert_system.connected_to_db:
        raise HTTPException(503, "Database connection required")

    try:
        # Run learning cycle in background
        background_tasks.add_task(expert_system.run_learning_cycle)

        return {
            'status': 'triggered',
            'message': 'Learning cycle initiated in background',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering learning cycle: {e}")
        raise HTTPException(500, "Failed to trigger learning")


@router.get("/learning/queue/status")
async def get_learning_queue_status():
    """
    Get status of the learning queue
    """
    if not supabase:
        raise HTTPException(503, "Database connection required")

    try:
        # Get queue statistics
        result = supabase.table('expert_learning_queue') \
            .select('learning_type, processed, priority') \
            .execute()

        queue_stats = {
            'total_tasks': len(result.data),
            'processed': sum(1 for task in result.data if task['processed']),
            'pending': sum(1 for task in result.data if not task['processed']),
            'by_type': {},
            'by_priority': {}
        }

        for task in result.data:
            if not task['processed']:
                # Count by type
                task_type = task['learning_type']
                queue_stats['by_type'][task_type] = queue_stats['by_type'].get(task_type, 0) + 1

                # Count by priority
                priority = task['priority']
                queue_stats['by_priority'][priority] = queue_stats['by_priority'].get(priority, 0) + 1

        return queue_stats
    except Exception as e:
        logger.error(f"Error fetching queue status: {e}")
        raise HTTPException(500, "Failed to fetch queue status")


@router.get("/peer-learning/network")
async def get_peer_learning_network():
    """
    Visualize the peer learning network
    Shows which experts learn from which
    """
    if not supabase:
        raise HTTPException(503, "Database connection required")

    try:
        result = supabase.table('expert_peer_learning') \
            .select('learner_expert_id, teacher_expert_id, learning_type') \
            .execute()

        # Build network graph
        network = {}
        for edge in result.data:
            learner = edge['learner_expert_id']
            teacher = edge['teacher_expert_id']

            if teacher not in network:
                network[teacher] = {'teaches': [], 'learns_from': []}
            if learner not in network:
                network[learner] = {'teaches': [], 'learns_from': []}

            network[teacher]['teaches'].append(learner)
            network[learner]['learns_from'].append(teacher)

        # Calculate influence scores
        for expert in network:
            network[expert]['influence_score'] = len(network[expert]['teaches'])
            network[expert]['learning_score'] = len(network[expert]['learns_from'])

        return {
            'network': network,
            'most_influential': max(network.items(),
                                  key=lambda x: x[1]['influence_score'])[0] if network else None,
            'most_receptive': max(network.items(),
                                key=lambda x: x[1]['learning_score'])[0] if network else None,
            'total_edges': len(result.data)
        }
    except Exception as e:
        logger.error(f"Error building peer network: {e}")
        raise HTTPException(500, "Failed to build peer network")


# Helper functions

async def _calculate_performance_stats(game_id: str, actual_result: Dict) -> Dict:
    """Calculate performance statistics for the game"""
    if not supabase:
        return {
            'learning_tasks': 0,
            'peer_shares': 0,
            'avg_score': 0.5,
            'best_expert': {'expert_id': 'unknown', 'score': 0},
            'worst_expert': {'expert_id': 'unknown', 'score': 0},
            'consensus_accuracy': 0.5
        }

    try:
        # Get all expert predictions for this game
        result = supabase.table('expert_memory') \
            .select('*') \
            .eq('game_id', game_id) \
            .execute()

        if not result.data:
            return {
                'learning_tasks': 0,
                'peer_shares': 0,
                'avg_score': 0.5,
                'best_expert': {'expert_id': 'unknown', 'score': 0},
                'worst_expert': {'expert_id': 'unknown', 'score': 0},
                'consensus_accuracy': 0.5
            }

        scores = []
        best_score = 0
        worst_score = 1
        best_expert = None
        worst_expert = None

        for memory in result.data:
            # Calculate score for this prediction
            score = _score_prediction(memory['prediction'], actual_result)
            scores.append(score)

            if score > best_score:
                best_score = score
                best_expert = memory['expert_id']

            if score < worst_score:
                worst_score = score
                worst_expert = memory['expert_id']

        # Count high-performing predictions for peer sharing
        peer_shares = sum(1 for score in scores if score > 0.7)

        # Calculate consensus accuracy (simplified)
        avg_score = sum(scores) / len(scores) if scores else 0.5

        return {
            'learning_tasks': len(result.data),
            'peer_shares': peer_shares,
            'avg_score': avg_score,
            'best_expert': {'expert_id': best_expert, 'score': best_score},
            'worst_expert': {'expert_id': worst_expert, 'score': worst_score},
            'consensus_accuracy': avg_score
        }
    except Exception as e:
        logger.error(f"Error calculating performance stats: {e}")
        return {
            'learning_tasks': 0,
            'peer_shares': 0,
            'avg_score': 0.5,
            'best_expert': {'expert_id': 'error', 'score': 0},
            'worst_expert': {'expert_id': 'error', 'score': 0},
            'consensus_accuracy': 0.5
        }


def _score_prediction(prediction: Dict, actual_result: Dict) -> float:
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


async def _process_advanced_learning(game_id: str, actual_result: Dict, performance_stats: Dict):
    """Process advanced learning tasks in background"""
    try:
        logger.info(f"🎓 Processing advanced learning for {game_id}")

        # Identify patterns in successful predictions
        if performance_stats['best_expert']['score'] > 0.8:
            # This expert did exceptionally well - analyze why
            await _analyze_success_patterns(
                performance_stats['best_expert']['expert_id'],
                game_id
            )

        # Identify patterns in failed predictions
        if performance_stats['worst_expert']['score'] < 0.3:
            # This expert did poorly - analyze why
            await _analyze_failure_patterns(
                performance_stats['worst_expert']['expert_id'],
                game_id
            )

        logger.info(f"✅ Advanced learning complete for {game_id}")

    except Exception as e:
        logger.error(f"Error in advanced learning: {e}")


async def _analyze_success_patterns(expert_id: str, game_id: str):
    """Analyze what made this prediction successful"""
    if not supabase:
        return

    try:
        # Get the successful prediction
        result = supabase.table('expert_memory') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .eq('game_id', game_id) \
            .single() \
            .execute()

        if result.data:
            # Store pattern for future reference
            supabase.table('expert_learning_queue').insert({
                'expert_id': expert_id,
                'learning_type': 'pattern_detected',
                'data': {
                    'pattern': 'exceptional_success',
                    'factors': result.data['prediction'].get('key_factors', []),
                    'confidence': result.data['prediction'].get('winner_confidence', 0)
                },
                'priority': 8  # High priority
            }).execute()

    except Exception as e:
        logger.error(f"Error analyzing success patterns: {e}")


async def _analyze_failure_patterns(expert_id: str, game_id: str):
    """Analyze what made this prediction fail"""
    if not supabase:
        return

    try:
        # Get the failed prediction
        result = supabase.table('expert_memory') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .eq('game_id', game_id) \
            .single() \
            .execute()

        if result.data:
            # Store pattern for learning
            supabase.table('expert_learning_queue').insert({
                'expert_id': expert_id,
                'learning_type': 'pattern_detected',
                'data': {
                    'pattern': 'significant_failure',
                    'factors': result.data['prediction'].get('key_factors', []),
                    'confidence': result.data['prediction'].get('winner_confidence', 0)
                },
                'priority': 9  # Very high priority - learn from mistakes
            }).execute()

    except Exception as e:
        logger.error(f"Error analyzing failure patterns: {e}")


def _find_most_improved(experts: List[Dict]) -> Optional[Dict]:
    """Find the most improved expert"""
    best_improvement = 0
    most_improved = None

    for expert in experts:
        if 'performance' in expert:
            perf = expert['performance']
            if perf.get('trend') == 'improving' and perf.get('games', 0) >= 10:
                # Calculate improvement (recent vs overall)
                improvement = perf.get('recent_avg', 0.5) - perf.get('avg_score', 0.5)
                if improvement > best_improvement:
                    best_improvement = improvement
                    most_improved = expert

    return most_improved


def _find_most_consistent(experts: List[Dict]) -> Optional[Dict]:
    """Find the most consistent expert"""
    best_consistency = 0
    most_consistent = None

    for expert in experts:
        if 'performance' in expert:
            perf = expert['performance']
            consistency = perf.get('consistency', 0)
            if consistency > best_consistency:
                best_consistency = consistency
                most_consistent = expert

    return most_consistent


def _analyze_personality_performance(experts: List[Dict]) -> Dict:
    """Analyze performance by personality traits"""
    trait_performance = {
        'high_risk': [],
        'low_risk': [],
        'analytical': [],
        'emotional': [],
        'contrarian': [],
        'consensus': []
    }

    for expert in experts:
        traits = expert.get('personality_traits', {})
        perf_score = expert.get('performance', {}).get('avg_score', 0.5)

        # Categorize by dominant trait
        if traits.get('risk_taking', 0) > 0.7:
            trait_performance['high_risk'].append(perf_score)
        elif traits.get('risk_taking', 0) < 0.3:
            trait_performance['low_risk'].append(perf_score)

        if traits.get('analytical', 0) > 0.8:
            trait_performance['analytical'].append(perf_score)
        elif traits.get('emotional', 0) > 0.7:
            trait_performance['emotional'].append(perf_score)

        if traits.get('contrarian', 0) > 0.7:
            trait_performance['contrarian'].append(perf_score)
        elif traits.get('contrarian', 0) < 0.2:
            trait_performance['consensus'].append(perf_score)

    # Calculate averages
    for trait in trait_performance:
        scores = trait_performance[trait]
        trait_performance[trait] = {
            'avg_score': sum(scores) / len(scores) if scores else 0.5,
            'count': len(scores)
        }

    return trait_performance


# Export router
__all__ = ['router']