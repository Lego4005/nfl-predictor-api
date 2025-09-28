"""
AI Expert System API Integration
Demonstrates the complete AI Expert System functionality through API endpoints
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json
import logging

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ml.expert_competition.competition_framework import ExpertCompetitionFramework

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIExpertSystemAPI:
    """API interface for the complete AI Expert System"""
    
    def __init__(self, supabase_client=None):
        """Initialize the AI Expert System"""
        self.framework = ExpertCompetitionFramework(supabase_client=supabase_client)
        self.initialized = True
        logger.info("🚀 AI Expert System API initialized successfully")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = self.framework.get_competition_status()
            
            # Add additional API-specific information
            status.update({
                'api_version': '1.0.0',
                'system_initialized': self.initialized,
                'expert_details': [
                    {
                        'expert_id': expert_id,
                        'name': expert.name,
                        'personality': getattr(expert, 'personality', 'unknown'),
                        'total_predictions': getattr(expert, 'total_predictions', 0),
                        'accuracy': getattr(expert, 'overall_accuracy', 0.5),
                        'current_rank': getattr(expert, 'current_rank', 999),
                        'status': getattr(expert, 'status', 'active')
                    }
                    for expert_id, expert in self.framework.experts.items()
                ]
            })
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e), 'system_initialized': False}
    
    async def get_expert_rankings(self) -> Dict[str, Any]:
        """Get current expert rankings with detailed metrics"""
        try:
            rankings = await self.framework.calculate_expert_rankings()
            
            return {
                'success': True,
                'rankings': [
                    {
                        'rank': metrics.current_rank,
                        'expert_id': metrics.expert_id,
                        'expert_name': self.framework.experts[metrics.expert_id].name if metrics.expert_id in self.framework.experts else 'Unknown',
                        'leaderboard_score': round(metrics.leaderboard_score, 2),
                        'overall_accuracy': round(metrics.overall_accuracy, 3),
                        'recent_trend': metrics.recent_trend,
                        'consistency_score': round(metrics.consistency_score, 3),
                        'total_predictions': metrics.total_predictions,
                        'correct_predictions': metrics.correct_predictions,
                        'peak_rank': metrics.peak_rank,
                        'category_accuracies': metrics.category_accuracies,
                        'last_updated': metrics.last_updated.isoformat()
                    }
                    for metrics in rankings
                ],
                'total_experts': len(rankings),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get expert rankings: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_ai_council(self, evaluation_window_weeks: int = 4) -> Dict[str, Any]:
        """Get current AI Council with selection details"""
        try:
            council_members = await self.framework.select_ai_council(evaluation_window_weeks)
            
            # Get detailed council information
            council_details = []
            for expert_id in council_members:
                if expert_id in self.framework.experts:
                    expert = self.framework.experts[expert_id]
                    council_details.append({
                        'expert_id': expert_id,
                        'name': expert.name,
                        'personality': getattr(expert, 'personality', 'unknown'),
                        'current_rank': getattr(expert, 'current_rank', 999),
                        'accuracy': getattr(expert, 'overall_accuracy', 0.5),
                        'council_appearances': getattr(expert, 'council_appearances', 0),
                        'specializations': expert.get_specializations() if hasattr(expert, 'get_specializations') else []
                    })
            
            return {
                'success': True,
                'council_members': council_details,
                'council_size': len(council_details),
                'evaluation_window_weeks': evaluation_window_weeks,
                'selection_criteria': {
                    'accuracy_weight': 0.35,
                    'recent_performance_weight': 0.25,
                    'consistency_weight': 0.20,
                    'confidence_calibration_weight': 0.10,
                    'specialization_weight': 0.10
                },
                'selected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AI Council: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_expert_predictions(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions from all experts for a game"""
        try:
            # Since we don't have the full category predictor available, simulate predictions
            predictions = {}
            
            for expert_id, expert in self.framework.experts.items():
                # Create mock prediction
                import random
                
                home_win_prob = 0.5 + random.uniform(-0.25, 0.25)
                confidence = 0.4 + random.uniform(0, 0.4)
                
                prediction = {
                    'expert_id': expert_id,
                    'expert_name': expert.name,
                    'game_id': game_data.get('game_id', 'unknown'),
                    'predictions': {
                        'winner_prediction': 'home' if home_win_prob > 0.5 else 'away',
                        'home_win_probability': round(home_win_prob, 3),
                        'away_win_probability': round(1 - home_win_prob, 3),
                        'exact_score_home': int(24 + random.uniform(-7, 10)),
                        'exact_score_away': int(21 + random.uniform(-7, 10)),
                        'spread_prediction': round((home_win_prob - 0.5) * 20, 1),
                        'total_prediction': round(45 + random.uniform(-10, 10), 1),
                        'against_the_spread': random.choice(['home', 'away', 'push']),
                        'totals_over_under': random.choice(['over', 'under'])
                    },
                    'confidence_overall': round(confidence, 2),
                    'reasoning': f"Mock prediction from {expert.name} based on personality-driven analysis",
                    'key_factors': [
                        f"{expert.name} personality analysis",
                        "Team matchup evaluation",
                        "Historical performance review"
                    ],
                    'prediction_timestamp': datetime.now().isoformat()
                }
                
                predictions[expert_id] = prediction
            
            return {
                'success': True,
                'game_id': game_data.get('game_id', 'unknown'),
                'game_info': {
                    'home_team': game_data.get('home_team', 'Unknown'),
                    'away_team': game_data.get('away_team', 'Unknown'),
                    'game_time': game_data.get('game_time', 'Unknown')
                },
                'expert_predictions': predictions,
                'total_experts': len(predictions),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate expert predictions: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_ai_council_consensus(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI Council consensus prediction"""
        try:
            # Get AI Council
            if not self.framework.ai_council:
                await self.framework.select_ai_council()
            
            # Generate mock council predictions
            council_predictions = {}
            council_experts = []
            
            for expert_id in self.framework.ai_council:
                if expert_id in self.framework.experts:
                    expert = self.framework.experts[expert_id]
                    council_experts.append(expert)
                    
                    # Create mock prediction
                    import random
                    
                    home_win_prob = 0.5 + random.uniform(-0.3, 0.3)
                    confidence = 0.5 + random.uniform(-0.2, 0.3)
                    
                    mock_prediction = type('MockPrediction', (), {
                        'expert_id': expert_id,
                        'expert_name': expert.name,
                        'winner_prediction': 'home' if home_win_prob > 0.5 else 'away',
                        'exact_score_home': int(24 + random.uniform(-7, 10)),
                        'exact_score_away': int(21 + random.uniform(-7, 10)),
                        'against_the_spread': random.choice(['home', 'away', 'push']),
                        'totals_over_under': random.choice(['over', 'under']),
                        'confidence_overall': confidence,
                        'confidence_by_category': {
                            'winner_prediction': confidence + random.uniform(-0.1, 0.1)
                        }
                    })()
                    
                    council_predictions[expert_id] = mock_prediction
            
            # Calculate vote weights
            expert_confidences = {
                expert_id: pred.confidence_overall 
                for expert_id, pred in council_predictions.items()
            }
            
            vote_weights = self.framework.vote_weight_calculator.calculate_vote_weights(
                council_experts, expert_confidences
            )
            
            # Build consensus for key categories
            consensus_categories = ['winner_prediction', 'exact_score_home', 'against_the_spread']
            consensus_results = {}
            
            for category in consensus_categories:
                consensus = self.framework.consensus_builder.build_consensus(
                    council_predictions, council_experts, category
                )
                consensus_results[category] = consensus
            
            return {
                'success': True,
                'game_id': game_data.get('game_id', 'unknown'),
                'game_info': {
                    'home_team': game_data.get('home_team', 'Unknown'),
                    'away_team': game_data.get('away_team', 'Unknown'),
                    'game_time': game_data.get('game_time', 'Unknown')
                },
                'ai_council': {
                    'members': [
                        {
                            'expert_id': expert.expert_id,
                            'name': expert.name,
                            'vote_weight': next((vw.normalized_weight for vw in vote_weights if vw.expert_id == expert.expert_id), 0.2),
                            'individual_prediction': {
                                'winner': council_predictions[expert.expert_id].winner_prediction,
                                'confidence': council_predictions[expert.expert_id].confidence_overall
                            }
                        }
                        for expert in council_experts
                    ]
                },
                'consensus_predictions': {
                    category: {
                        'value': consensus.consensus_value,
                        'confidence': round(consensus.confidence_score, 2),
                        'agreement_level': round(consensus.agreement_level, 2),
                        'method_used': consensus.method_used
                    }
                    for category, consensus in consensus_results.items()
                    if consensus.consensus_value is not None
                },
                'vote_weights': [
                    {
                        'expert_id': vw.expert_id,
                        'expert_name': next((e.name for e in council_experts if e.expert_id == vw.expert_id), vw.expert_id),
                        'normalized_weight': round(vw.normalized_weight, 3),
                        'components': {
                            'accuracy': round(vw.accuracy_component, 3),
                            'recent_performance': round(vw.recent_performance_component, 3),
                            'confidence': round(vw.confidence_component, 3),
                            'council_tenure': round(vw.council_tenure_component, 3)
                        }
                    }
                    for vw in vote_weights
                ],
                'consensus_metadata': {
                    'total_categories': len(consensus_results),
                    'successful_predictions': len([c for c in consensus_results.values() if c.consensus_value is not None]),
                    'average_confidence': round(sum(c.confidence_score for c in consensus_results.values()) / len(consensus_results), 2) if consensus_results else 0,
                    'average_agreement': round(sum(c.agreement_level for c in consensus_results.values()) / len(consensus_results), 2) if consensus_results else 0
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI Council consensus: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_competition_round(self, week: int, season: int, games: List[str], game_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a complete competition round"""
        try:
            # Start the round
            round_data = await self.framework.start_competition_round(week, season, games)
            
            result = {
                'success': True,
                'round_info': {
                    'round_id': round_data.round_id,
                    'week': round_data.week,
                    'season': round_data.season,
                    'games': round_data.games,
                    'started_at': round_data.started_at.isoformat()
                },
                'initial_council': [
                    {
                        'expert_id': expert_id,
                        'name': self.framework.experts[expert_id].name if expert_id in self.framework.experts else expert_id
                    }
                    for expert_id in round_data.council_members
                ]
            }
            
            # If game results provided, complete the round
            if game_results:
                try:
                    completed_round = await self.framework.complete_competition_round(game_results)
                    
                    result.update({
                        'round_completed': True,
                        'completed_at': completed_round.completed_at.isoformat(),
                        'round_winner': {
                            'expert_id': completed_round.round_winner,
                            'name': self.framework.experts[completed_round.round_winner].name if completed_round.round_winner and completed_round.round_winner in self.framework.experts else 'Unknown'
                        } if completed_round.round_winner else None,
                        'final_council': [
                            {
                                'expert_id': expert_id,
                                'name': self.framework.experts[expert_id].name if expert_id in self.framework.experts else expert_id
                            }
                            for expert_id in self.framework.ai_council
                        ],
                        'expert_performance_summary': {
                            'total_experts': len(completed_round.expert_performances),
                            'performance_evaluated': True
                        }
                    })
                    
                except Exception as e:
                    result.update({
                        'round_completed': False,
                        'completion_error': str(e),
                        'note': 'Round started successfully but completion had issues (this is expected in testing environment)'
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to run competition round: {e}")
            return {'success': False, 'error': str(e)}

# Example usage and testing
async def demo_ai_expert_system():
    """Demonstrate the complete AI Expert System API"""
    
    print("🚀 AI Expert System API Demo")
    print("=" * 50)
    
    # Initialize the API
    api = AIExpertSystemAPI()
    
    # 1. Get system status
    print("\n1️⃣ System Status:")
    status = await api.get_system_status()
    print(f"   Total Experts: {status.get('total_experts', 0)}")
    print(f"   System Health: {status.get('system_health', {}).get('active_experts', 0)} active experts")
    
    # 2. Get expert rankings
    print("\n2️⃣ Expert Rankings:")
    rankings = await api.get_expert_rankings()
    if rankings['success']:
        print("   Top 5 Experts:")
        for expert in rankings['rankings'][:5]:
            print(f"      #{expert['rank']}: {expert['expert_name']} - {expert['leaderboard_score']} points")
    
    # 3. Get AI Council
    print("\n3️⃣ AI Council:")
    council = await api.get_ai_council()
    if council['success']:
        print(f"   Council Size: {council['council_size']}")
        for member in council['council_members']:
            print(f"      - {member['name']} (Rank: #{member['current_rank']})")
    
    # 4. Generate predictions for a mock game
    print("\n4️⃣ Expert Predictions:")
    mock_game = {
        'game_id': 'demo_game_2024',
        'home_team': 'Kansas City Chiefs',
        'away_team': 'Buffalo Bills',
        'game_time': '2024-09-15T20:20:00Z'
    }
    
    predictions = await api.generate_expert_predictions(mock_game)
    if predictions['success']:
        print(f"   Generated predictions from {predictions['total_experts']} experts")
        # Show first 3 predictions
        sample_predictions = list(predictions['expert_predictions'].values())[:3]
        for pred in sample_predictions:
            winner = pred['predictions']['winner_prediction']
            confidence = pred['confidence_overall']
            print(f"      - {pred['expert_name']}: {winner} ({confidence} confidence)")
    
    # 5. Generate AI Council consensus
    print("\n5️⃣ AI Council Consensus:")
    consensus = await api.generate_ai_council_consensus(mock_game)
    if consensus['success']:
        print(f"   Council Decision: {consensus['consensus_predictions'].get('winner_prediction', {}).get('value', 'Unknown')}")
        print(f"   Consensus Confidence: {consensus['consensus_predictions'].get('winner_prediction', {}).get('confidence', 0)}")
        print(f"   Agreement Level: {consensus['consensus_predictions'].get('winner_prediction', {}).get('agreement_level', 0)}")
    
    # 6. Run a competition round
    print("\n6️⃣ Competition Round:")
    round_result = await api.run_competition_round(
        week=1, 
        season=2024, 
        games=['demo_game_2024'],
        game_results={'demo_game_2024': {'winner': 'home', 'final_score': '27-24'}}
    )
    
    if round_result['success']:
        print(f"   Round: {round_result['round_info']['round_id']}")
        print(f"   Completed: {round_result.get('round_completed', False)}")
        if round_result.get('round_winner'):
            print(f"   Winner: {round_result['round_winner']['name']}")
    
    print("\n✅ AI Expert System API Demo Complete!")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_ai_expert_system())