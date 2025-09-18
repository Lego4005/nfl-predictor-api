"""
Memory-Enhanced Expert Prediction Endpoints
Integrates the memory-enabled expert system with existing API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import os
import asyncio

from ml.memory_enabled_expert_service import MemoryEnabledExpertService
from ml.personality_driven_experts import UniversalGameData
from api.prediction_models import ExpertPerformanceResponse

# Configure logging
logger = logging.getLogger(__name__)

# Router for memory-enhanced endpoints
router = APIRouter(prefix="/api/v1/memory", tags=["Memory-Enhanced Experts"])

# Global service instance (will be initialized on startup)
memory_service: Optional[MemoryEnabledExpertService] = None

async def get_memory_service() -> MemoryEnabledExpertService:
    """Dependency to get the memory service"""
    global memory_service
    if memory_service is None:
        raise HTTPException(status_code=503, detail="Memory service not initialized")
    return memory_service

async def initialize_memory_service():
    """Initialize the memory service on startup"""
    global memory_service

    try:
        # Database configuration from environment
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'database': os.getenv('DB_NAME', 'nfl_predictor')
        }

        memory_service = MemoryEnabledExpertService(db_config)
        await memory_service.initialize()
        logger.info("✅ Memory-enhanced expert service initialized")

    except Exception as e:
        logger.error(f"❌ Failed to initialize memory service: {e}")
        raise

async def shutdown_memory_service():
    """Shutdown the memory service"""
    global memory_service
    if memory_service:
        await memory_service.close()
        logger.info("✅ Memory service shutdown complete")

@router.get("/experts/predictions/{home_team}/{away_team}")
async def get_memory_enhanced_predictions(
    home_team: str,
    away_team: str,
    include_learning_insights: bool = True,
    service: MemoryEnabledExpertService = Depends(get_memory_service)
):
    """
    Get memory-enhanced predictions from all personality experts

    This endpoint generates predictions that incorporate:
    - Episodic memories from similar past games
    - Belief revision tracking for evolving expert opinions
    - Reasoning chain logging for detailed analysis
    - Learning-based confidence adjustments
    """
    try:
        logger.info(f"🧠 Generating memory-enhanced predictions for {away_team} @ {home_team}")

        # Create universal game data (simplified for demo - in production would fetch real data)
        universal_data = UniversalGameData(
            home_team=home_team.upper(),
            away_team=away_team.upper(),
            game_time=datetime.now().isoformat(),
            location=f"{home_team} Stadium",
            weather={'temperature': 65, 'wind_speed': 8, 'conditions': 'Clear'},
            injuries={'home': [], 'away': []},
            line_movement={'opening_line': -3.0, 'current_line': -2.5, 'public_percentage': 65},
            team_stats={
                'home': {'offensive_yards_per_game': 350, 'defensive_yards_allowed': 320},
                'away': {'offensive_yards_per_game': 340, 'defensive_yards_allowed': 330}
            }
        )

        # Generate memory-enhanced predictions
        result = await service.generate_memory_enhanced_predictions(universal_data)

        # Format response
        response = {
            'game_info': {
                'matchup': f"{away_team} @ {home_team}",
                'timestamp': datetime.utcnow().isoformat(),
                'memory_enhanced': True
            },
            'expert_predictions': [],
            'consensus': result['consensus'],
            'memory_statistics': result['memory_stats'],
            'system_info': {
                'total_experts': len(result['all_predictions']),
                'memory_enabled_experts': sum(1 for p in result['all_predictions'] if p.get('memory_enhanced')),
                'service_version': '2.0.0-memory'
            }
        }

        # Format expert predictions
        for pred in result['all_predictions']:
            expert_data = {
                'expert_id': pred.get('expert_id', pred.get('expert_name', '').lower().replace(' ', '_')),
                'expert_name': pred.get('expert_name', 'Unknown Expert'),
                'personality_style': pred.get('personality_style', 'unknown'),
                'prediction': {
                    'winner': pred.get('winner_prediction', 'unknown'),
                    'confidence': pred.get('winner_confidence', 0.5),
                    'spread_prediction': pred.get('spread_prediction', 0),
                    'total_prediction': pred.get('total_prediction', 45)
                },
                'memory_enhancement': {
                    'enabled': pred.get('memory_enhanced', False),
                    'similar_experiences': pred.get('similar_experiences', 0),
                    'confidence_adjustment': pred.get('memory_confidence_boost', 0),
                    'reasoning_chain_id': pred.get('reasoning_chain_id', 'unknown')
                }
            }

            # Add learning insights if requested
            if include_learning_insights:
                expert_data['learning_insights'] = pred.get('learning_insights', [])
                expert_data['memory_analysis'] = pred.get('memory_analysis', {})

            response['expert_predictions'].append(expert_data)

        # Add learning summary
        if include_learning_insights:
            response['learning_summary'] = result['learning_summary']

        logger.info(f"✅ Generated {len(response['expert_predictions'])} memory-enhanced predictions")
        return response

    except Exception as e:
        logger.error(f"❌ Error generating memory-enhanced predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction generation failed: {str(e)}")

@router.post("/experts/outcomes")
async def process_game_outcomes(
    game_outcomes: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    service: MemoryEnabledExpertService = Depends(get_memory_service)
):
    """
    Process game outcomes to create episodic memories and update expert learning

    Expected format for each game outcome:
    {
        "game_id": "string",
        "actual_outcome": {
            "winner": "team_code",
            "home_score": int,
            "away_score": int,
            "margin": int
        },
        "expert_predictions": [...] // Previous predictions from the experts
    }
    """
    try:
        logger.info(f"🎯 Processing {len(game_outcomes)} game outcomes for learning")

        # Process outcomes asynchronously in background
        background_tasks.add_task(
            service.process_game_outcomes,
            game_outcomes
        )

        return {
            'status': 'accepted',
            'games_queued': len(game_outcomes),
            'message': 'Game outcomes queued for processing. Expert memories will be updated in background.',
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error processing game outcomes: {e}")
        raise HTTPException(status_code=500, detail=f"Outcome processing failed: {str(e)}")

@router.get("/experts/{expert_id}/memory")
async def get_expert_memory_profile(
    expert_id: str,
    include_recent_memories: bool = True,
    memory_limit: int = 10,
    service: MemoryEnabledExpertService = Depends(get_memory_service)
):
    """Get comprehensive memory profile for a specific expert"""
    try:
        logger.info(f"📊 Getting memory profile for expert {expert_id}")

        # Get expert analytics
        analytics = await service.get_expert_memory_analytics(expert_id)

        if expert_id not in analytics:
            raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")

        expert_data = analytics[expert_id]

        response = {
            'expert_info': {
                'expert_id': expert_id,
                'name': expert_data['name'],
                'personality_style': expert_data['personality_style']
            },
            'memory_statistics': expert_data['memory_stats'],
            'learning_metrics': expert_data['learning_metrics'],
            'belief_revision_patterns': expert_data.get('revision_patterns', {}),
            'performance_summary': {
                'total_predictions': expert_data['learning_metrics']['total_predictions'],
                'memory_enhanced_predictions': expert_data['learning_metrics']['memory_enhanced_predictions'],
                'recent_accuracy': expert_data['learning_metrics']['recent_accuracy']
            }
        }

        # Add recent memories if requested
        if include_recent_memories:
            try:
                # This would require additional method in the service
                # For now, return placeholder
                response['recent_memories'] = {
                    'count': expert_data['memory_stats'].get('total_memories', 0),
                    'note': 'Recent memory details available via /experts/{expert_id}/memories endpoint'
                }
            except Exception as e:
                logger.warning(f"Could not fetch recent memories: {e}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting expert memory profile: {e}")
        raise HTTPException(status_code=500, detail=f"Memory profile retrieval failed: {str(e)}")

@router.get("/analytics/system")
async def get_memory_system_analytics(
    service: MemoryEnabledExpertService = Depends(get_memory_service)
):
    """Get comprehensive analytics for the entire memory system"""
    try:
        logger.info("📈 Getting system-wide memory analytics")

        # Get analytics for all experts
        all_analytics = await service.get_expert_memory_analytics()

        # Aggregate system statistics
        total_predictions = sum(data['learning_metrics']['total_predictions'] for data in all_analytics.values())
        total_memories = sum(data['memory_stats'].get('total_memories', 0) for data in all_analytics.values())
        memory_enhanced_predictions = sum(data['learning_metrics']['memory_enhanced_predictions'] for data in all_analytics.values())

        # Calculate average accuracy
        accuracies = [data['learning_metrics']['recent_accuracy'] for data in all_analytics.values() if data['learning_metrics']['recent_accuracy'] > 0]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0

        # Find top performers
        top_performers = sorted(
            all_analytics.items(),
            key=lambda x: x[1]['learning_metrics']['recent_accuracy'],
            reverse=True
        )[:5]

        response = {
            'system_overview': {
                'total_experts': len(all_analytics),
                'total_predictions': total_predictions,
                'total_memories': total_memories,
                'memory_enhanced_predictions': memory_enhanced_predictions,
                'memory_enhancement_rate': memory_enhanced_predictions / total_predictions if total_predictions > 0 else 0,
                'average_accuracy': avg_accuracy
            },
            'expert_performance': {
                'top_performers': [
                    {
                        'expert_id': expert_id,
                        'name': data['name'],
                        'accuracy': data['learning_metrics']['recent_accuracy'],
                        'predictions': data['learning_metrics']['total_predictions']
                    }
                    for expert_id, data in top_performers
                ],
                'performance_distribution': {
                    'high_accuracy': len([a for a in accuracies if a > 0.6]),
                    'medium_accuracy': len([a for a in accuracies if 0.4 <= a <= 0.6]),
                    'low_accuracy': len([a for a in accuracies if a < 0.4])
                }
            },
            'memory_insights': {
                'total_memory_banks': len(all_analytics),
                'experts_with_memories': len([data for data in all_analytics.values() if data['memory_stats'].get('total_memories', 0) > 0]),
                'avg_memories_per_expert': total_memories / len(all_analytics) if all_analytics else 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        return response

    except Exception as e:
        logger.error(f"❌ Error getting system analytics: {e}")
        raise HTTPException(status_code=500, detail=f"System analytics retrieval failed: {str(e)}")

@router.get("/experts/battle/{home_team}/{away_team}")
async def get_memory_enhanced_battle_card(
    home_team: str,
    away_team: str,
    service: MemoryEnabledExpertService = Depends(get_memory_service)
):
    """Get expert battle card showing memory-enhanced competition"""
    try:
        logger.info(f"⚔️ Creating memory battle card for {away_team} @ {home_team}")

        # Get memory-enhanced predictions
        universal_data = UniversalGameData(
            home_team=home_team.upper(),
            away_team=away_team.upper(),
            game_time=datetime.now().isoformat(),
            location=f"{home_team} Stadium",
            weather={'temperature': 65, 'wind_speed': 8, 'conditions': 'Clear'},
            injuries={'home': [], 'away': []},
            line_movement={'opening_line': -3.0, 'current_line': -2.5, 'public_percentage': 65},
            team_stats={
                'home': {'offensive_yards_per_game': 350, 'defensive_yards_allowed': 320},
                'away': {'offensive_yards_per_game': 340, 'defensive_yards_allowed': 330}
            }
        )

        result = await service.generate_memory_enhanced_predictions(universal_data)

        # Create battle card
        predictions = result['all_predictions']

        # Find most confident memory-enhanced expert
        memory_experts = [p for p in predictions if p.get('memory_enhanced') and p.get('similar_experiences', 0) > 0]
        most_confident_memory = max(memory_experts, key=lambda x: x.get('winner_confidence', 0)) if memory_experts else None

        # Find biggest memory boost
        biggest_boost = max(predictions, key=lambda x: abs(x.get('memory_confidence_boost', 0)))

        # Count winner votes
        winner_votes = {}
        for pred in predictions:
            winner = pred.get('winner_prediction', 'unknown')
            if winner not in winner_votes:
                winner_votes[winner] = {'total': 0, 'memory_enhanced': 0}
            winner_votes[winner]['total'] += 1
            if pred.get('memory_enhanced'):
                winner_votes[winner]['memory_enhanced'] += 1

        response = {
            'game_info': {
                'matchup': f"{away_team} @ {home_team}",
                'timestamp': datetime.utcnow().isoformat()
            },
            'memory_battle_stats': {
                'experts_with_memories': len(memory_experts),
                'total_memories_consulted': sum(p.get('similar_experiences', 0) for p in predictions),
                'avg_memory_confidence_boost': sum(p.get('memory_confidence_boost', 0) for p in predictions) / len(predictions)
            },
            'expert_highlights': {
                'most_confident_memory_expert': {
                    'name': most_confident_memory['expert_name'] if most_confident_memory else None,
                    'confidence': most_confident_memory['winner_confidence'] if most_confident_memory else 0,
                    'memories_used': most_confident_memory['similar_experiences'] if most_confident_memory else 0,
                    'winner_pick': most_confident_memory['winner_prediction'] if most_confident_memory else None
                },
                'biggest_memory_adjustment': {
                    'name': biggest_boost['expert_name'],
                    'adjustment': biggest_boost.get('memory_confidence_boost', 0),
                    'direction': 'increased' if biggest_boost.get('memory_confidence_boost', 0) > 0 else 'decreased'
                }
            },
            'prediction_breakdown': {
                'winner_votes': winner_votes,
                'consensus': result['consensus'],
                'memory_vs_base_comparison': {
                    'memory_enhanced_consensus': result['consensus']['winner'],
                    'memory_enhanced_confidence': result['consensus']['confidence']
                }
            },
            'learning_highlights': result['learning_summary']['top_insights'][:3]
        }

        return response

    except Exception as e:
        logger.error(f"❌ Error creating memory battle card: {e}")
        raise HTTPException(status_code=500, detail=f"Battle card creation failed: {str(e)}")

@router.get("/health")
async def memory_service_health():
    """Health check for memory service"""
    global memory_service

    if memory_service is None:
        return {
            'status': 'unhealthy',
            'message': 'Memory service not initialized',
            'timestamp': datetime.utcnow().isoformat()
        }

    try:
        # Simple check - could be expanded to test database connections
        return {
            'status': 'healthy',
            'service': 'memory-enhanced-experts',
            'version': '2.0.0',
            'experts_loaded': len(memory_service.memory_experts),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }

# Add startup and shutdown event handlers
async def startup_event():
    """Initialize memory service on startup"""
    await initialize_memory_service()

async def shutdown_event():
    """Shutdown memory service"""
    await shutdown_memory_service()

# Export the router and event handlers
__all__ = ['router', 'startup_event', 'shutdown_event', 'initialize_memory_service', 'shutdown_memory_service']