#!/usr/bin/env python3
"""
Comprehensive Prediction System Integration Demo
Demonstrates the complete 27-category prediction system with AI Council consensus
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.prediction_engine.comprehensive_prediction_categories import get_prediction_categories
from src.ml.prediction_engine.category_specific_algorithms import CategorySpecificPredictor
from src.ml.expert_competition.council_selector import AICouncilSelector
from src.ml.expert_competition.voting_consensus import VoteWeightCalculator, ConsensusBuilder


class MockExpert:
    """Mock expert for demonstration purposes"""
    
    def __init__(self, expert_id: str, name: str, personality_profile: Dict[str, float], performance_metrics: Dict[str, Any]):
        self.expert_id = expert_id
        self.name = name
        self.personality_traits = personality_profile
        
        # Performance metrics
        self.total_predictions = performance_metrics.get('total_predictions', 50)
        self.overall_accuracy = performance_metrics.get('overall_accuracy', 0.6)
        self.recent_trend = performance_metrics.get('recent_trend', 'stable')
        self.consistency_score = performance_metrics.get('consistency_score', 0.6)
        self.confidence_calibration = performance_metrics.get('confidence_calibration', 0.6)
        self.specialization_strength = performance_metrics.get('specialization_strength', {'general': 0.6})
        self.council_appearances = performance_metrics.get('council_appearances', 1)


def create_expert_pool() -> Dict[str, MockExpert]:
    """Create a diverse pool of 15 mock experts with different personalities"""
    
    expert_configs = [
        {
            'id': 'conservative_analyst',
            'name': 'The Conservative Analyst',
            'personality': {
                'risk_tolerance': 0.2,
                'analytics_trust': 0.9,
                'contrarian_tendency': 0.1,
                'optimism': 0.4,
                'chaos_comfort': 0.2,
                'confidence_level': 0.7,
                'market_trust': 0.8,
                'value_seeking': 0.6
            },
            'performance': {
                'total_predictions': 65,
                'overall_accuracy': 0.68,
                'recent_trend': 'stable',
                'consistency_score': 0.85,
                'confidence_calibration': 0.82,
                'specialization_strength': {'game_outcome': 0.9, 'situational': 0.7},
                'council_appearances': 8
            }
        },
        {
            'id': 'risk_taking_gambler',
            'name': 'The Risk-Taking Gambler',
            'personality': {
                'risk_tolerance': 0.9,
                'analytics_trust': 0.3,
                'contrarian_tendency': 0.7,
                'optimism': 0.8,
                'chaos_comfort': 0.9,
                'confidence_level': 0.8,
                'market_trust': 0.2,
                'value_seeking': 0.9
            },
            'performance': {
                'total_predictions': 72,
                'overall_accuracy': 0.61,
                'recent_trend': 'improving',
                'consistency_score': 0.45,
                'confidence_calibration': 0.55,
                'specialization_strength': {'betting_market': 0.8, 'live_scenario': 0.7},
                'council_appearances': 3
            }
        },
        {
            'id': 'contrarian_rebel',
            'name': 'The Contrarian Rebel',
            'personality': {
                'risk_tolerance': 0.7,
                'analytics_trust': 0.4,
                'contrarian_tendency': 0.9,
                'optimism': 0.3,
                'chaos_comfort': 0.8,
                'confidence_level': 0.9,
                'market_trust': 0.1,
                'value_seeking': 0.8
            },
            'performance': {
                'total_predictions': 58,
                'overall_accuracy': 0.64,
                'recent_trend': 'improving',
                'consistency_score': 0.52,
                'confidence_calibration': 0.61,
                'specialization_strength': {'betting_market': 0.85, 'game_outcome': 0.6},
                'council_appearances': 5
            }
        },
        {
            'id': 'value_hunter',
            'name': 'The Value Hunter',
            'personality': {
                'risk_tolerance': 0.6,
                'analytics_trust': 0.8,
                'contrarian_tendency': 0.6,
                'optimism': 0.5,
                'chaos_comfort': 0.4,
                'confidence_level': 0.6,
                'market_trust': 0.3,
                'value_seeking': 0.9
            },
            'performance': {
                'total_predictions': 69,
                'overall_accuracy': 0.66,
                'recent_trend': 'stable',
                'consistency_score': 0.78,
                'confidence_calibration': 0.75,
                'specialization_strength': {'betting_market': 0.9, 'situational': 0.65},
                'council_appearances': 6
            }
        },
        {
            'id': 'momentum_rider',
            'name': 'The Momentum Rider',
            'personality': {
                'risk_tolerance': 0.8,
                'analytics_trust': 0.5,
                'contrarian_tendency': 0.2,
                'optimism': 0.7,
                'chaos_comfort': 0.7,
                'confidence_level': 0.7,
                'market_trust': 0.6,
                'value_seeking': 0.4
            },
            'performance': {
                'total_predictions': 61,
                'overall_accuracy': 0.62,
                'recent_trend': 'declining',
                'consistency_score': 0.48,
                'confidence_calibration': 0.58,
                'specialization_strength': {'situational': 0.8, 'live_scenario': 0.6},
                'council_appearances': 4
            }
        }
    ]
    
    # Add 10 more experts with varying characteristics
    additional_experts = []
    for i in range(10):
        additional_experts.append({
            'id': f'expert_{i+6}',
            'name': f'Expert {i+6}',
            'personality': {
                'risk_tolerance': 0.3 + (i * 0.07),
                'analytics_trust': 0.4 + (i * 0.05),
                'contrarian_tendency': 0.2 + (i * 0.06),
                'optimism': 0.4 + (i * 0.04),
                'chaos_comfort': 0.3 + (i * 0.05),
                'confidence_level': 0.5 + (i * 0.03),
                'market_trust': 0.3 + (i * 0.04),
                'value_seeking': 0.4 + (i * 0.05)
            },
            'performance': {
                'total_predictions': 45 + i * 3,
                'overall_accuracy': 0.52 + (i * 0.015),
                'recent_trend': ['stable', 'improving', 'declining'][i % 3],
                'consistency_score': 0.5 + (i * 0.025),
                'confidence_calibration': 0.55 + (i * 0.02),
                'specialization_strength': {
                    ['game_outcome', 'betting_market', 'player_props', 'situational'][i % 4]: 0.6 + (i * 0.02)
                },
                'council_appearances': i % 3 + 1
            }
        })
    
    expert_configs.extend(additional_experts)
    
    # Create expert instances
    experts = {}
    for config in expert_configs:
        expert = MockExpert(
            config['id'],
            config['name'],
            config['personality'],
            config['performance']
        )
        experts[expert.expert_id] = expert
    
    return experts


def create_sample_game_data() -> Dict[str, Any]:
    """Create comprehensive sample game data"""
    return {
        'game_id': 'demo_2024_week_5_buf_kc',
        'home_team': 'Kansas City Chiefs',
        'away_team': 'Buffalo Bills',
        'game_time': '2024-10-15T20:20:00Z',
        'location': 'Arrowhead Stadium',
        
        # Betting lines
        'spread': -3.5,  # Chiefs favored by 3.5
        'total': 47.5,
        'first_half_total': 23.5,
        
        # Weather conditions
        'weather': {
            'temperature': 68,
            'wind_speed': 12,
            'precipitation': 0.0,
            'conditions': 'Clear',
            'humidity': 0.65
        },
        
        # Injury reports
        'injuries': {
            'home': [
                {'player': 'WR1', 'severity': 'questionable', 'is_starter': True, 'position': 'WR'},
                {'player': 'OL3', 'severity': 'doubtful', 'is_starter': False, 'position': 'OL'}
            ],
            'away': [
                {'player': 'RB2', 'severity': 'out', 'is_starter': False, 'position': 'RB'},
                {'player': 'CB1', 'severity': 'probable', 'is_starter': True, 'position': 'CB'}
            ]
        },
        
        # Team statistics
        'team_stats': {
            'home': {
                'offensive_efficiency': 0.78,
                'defensive_efficiency': 0.72,
                'pace_factor': 1.05,
                'red_zone_efficiency': 0.68,
                'turnover_margin': 0.8
            },
            'away': {
                'offensive_efficiency': 0.81,
                'defensive_efficiency': 0.75,
                'pace_factor': 0.98,
                'red_zone_efficiency': 0.72,
                'turnover_margin': 1.2
            }
        },
        
        # Market data
        'public_betting_percentage': 0.72,  # 72% on Chiefs
        'public_total_percentage': 0.58,    # 58% on over
        'line_movement': {
            'spread_movement': -0.5,  # Line moved toward Chiefs
            'total_movement': 1.0     # Total moved up
        },
        'sharp_money_indicator': 'away',  # Sharp money on Bills
        
        # Coaching and strategic factors
        'coaching': {
            'home_experience': 12,
            'away_experience': 8,
            'home_first_half_performance': 0.68,
            'away_first_half_performance': 0.61,
            'home_timeout_efficiency': 0.75,
            'away_timeout_efficiency': 0.70
        },
        
        # Situational factors
        'is_divisional': False,
        'is_prime_time': True,
        'home_momentum': 78,
        'away_momentum': 65,
        'playoff_implications': True,
        
        # Venue and travel
        'venue': {
            'crowd_factor': 1.15,  # Loud stadium
            'altitude': 912,       # Kansas City elevation
            'field_type': 'grass'
        },
        'travel': {
            'home_rest_days': 7,
            'away_rest_days': 6,
            'travel_distance': 1247,
            'time_zone_change': 1
        },
        
        # Historical context
        'head_to_head': {
            'last_5_games': [1, 0, 1, 0, 1],  # Alternating wins
            'home_record_vs_away': {'wins': 3, 'losses': 2},
            'avg_total_last_5': 52.4
        }
    }


async def demonstrate_comprehensive_prediction_system():
    """Demonstrate the complete prediction system workflow"""
    
    print("🏈 NFL Comprehensive Prediction System Demo")
    print("=" * 60)
    
    # Step 1: Initialize system components
    print("🔧 Initializing system components...")
    prediction_categories = get_prediction_categories()
    category_predictor = CategorySpecificPredictor()
    council_selector = AICouncilSelector()
    vote_calculator = VoteWeightCalculator()
    consensus_builder = ConsensusBuilder(vote_calculator)
    
    # Step 2: Create expert pool and game data
    print("👥 Creating expert pool...")
    experts = create_expert_pool()
    game_data = create_sample_game_data()
    
    print(f"   Created {len(experts)} experts")
    print(f"   Game: {game_data['away_team']} @ {game_data['home_team']}")
    print(f"   Spread: {game_data['home_team']} {game_data['spread']}")
    print(f"   Total: {game_data['total']}")
    
    # Step 3: Generate predictions from all experts
    print("\n🔮 Generating expert predictions...")
    expert_predictions = {}
    
    for expert_id, expert in experts.items():
        try:
            prediction = category_predictor.generate_comprehensive_prediction(expert, game_data)
            expert_predictions[expert_id] = prediction
            print(f"   ✅ {expert.name}: {prediction.winner_prediction} ({prediction.confidence_overall:.2f})")
        except Exception as e:
            print(f"   ❌ {expert.name}: Failed - {e}")
    
    print(f"\n📊 Generated {len(expert_predictions)} predictions successfully")
    
    # Step 4: Select AI Council
    print("\n🏛️ Selecting AI Council...")
    council_members = await council_selector.select_top_performers(experts)
    
    print(f"   Selected {len(council_members)} council members:")
    for expert_id in council_members:
        expert = experts[expert_id]
        print(f"     🏆 {expert.name}: {expert.overall_accuracy:.1%} accuracy, {expert.recent_trend} trend")
    
    # Step 5: Calculate vote weights
    print("\n⚖️ Calculating vote weights...")
    council_experts = [experts[expert_id] for expert_id in council_members]
    expert_confidences = {
        expert_id: expert_predictions[expert_id].confidence_overall 
        for expert_id in council_members
    }
    
    vote_weights = vote_calculator.calculate_vote_weights(council_experts, expert_confidences)
    
    print("   Vote weight breakdown:")
    for weight in vote_weights:
        print(f"     {weight.expert_id}: {weight.normalized_weight:.3f}")
        print(f"       Accuracy: {weight.accuracy_component:.3f}, Recent: {weight.recent_performance_component:.3f}")
        print(f"       Confidence: {weight.confidence_component:.3f}, Tenure: {weight.council_tenure_component:.3f}")
    
    # Step 6: Build consensus across key categories
    print("\n🤝 Building AI Council consensus...")
    
    council_predictions = {
        expert_id: expert_predictions[expert_id] 
        for expert_id in council_members
    }
    
    key_categories = [
        'winner_prediction', 'exact_score_home', 'exact_score_away', 'margin_of_victory',
        'against_the_spread', 'totals_over_under', 'first_half_winner',
        'qb_passing_yards', 'qb_touchdowns', 'weather_impact_score', 'home_field_advantage'
    ]
    
    consensus_results = {}
    
    for category in key_categories:
        consensus = consensus_builder.build_consensus(
            council_predictions, council_experts, category
        )
        consensus_results[category] = consensus
        
        if consensus.consensus_value is not None:
            print(f"   📋 {category}: {consensus.consensus_value}")
            print(f"       Confidence: {consensus.confidence_score:.3f}, Agreement: {consensus.agreement_level:.3f}")
    
    # Step 7: Generate final prediction summary
    print("\n📈 Final AI Council Prediction Summary:")
    print("=" * 40)
    
    winner = consensus_results['winner_prediction'].consensus_value
    home_score = consensus_results['exact_score_home'].consensus_value
    away_score = consensus_results['exact_score_away'].consensus_value
    spread_pick = consensus_results['against_the_spread'].consensus_value
    total_pick = consensus_results['totals_over_under'].consensus_value
    
    winning_team = game_data['home_team'] if winner == 'home' else game_data['away_team']
    
    print(f"🏆 Winner: {winning_team}")
    print(f"📊 Final Score: {game_data['home_team']} {int(home_score)} - {int(away_score)} {game_data['away_team']}")
    print(f"📈 Spread: {spread_pick.title()} team covers")
    print(f"📉 Total: {total_pick.title()} {game_data['total']}")
    print(f"⚡ QB Passing Yards: {consensus_results['qb_passing_yards'].consensus_value:.0f}")
    print(f"🌦️ Weather Impact: {consensus_results['weather_impact_score'].consensus_value:.2f}")
    print(f"🏠 Home Field Advantage: {consensus_results['home_field_advantage'].consensus_value:.1f} points")
    
    # Step 8: Show category breakdown
    print(f"\n📋 Complete Category Analysis:")
    summary = prediction_categories.get_category_summary()
    
    print(f"   Total Categories: {summary['total_categories']}")
    for group, count in summary['categories_by_group'].items():
        group_consensus = [c for c in consensus_results.values() 
                         if prediction_categories.get_category(c.category) and 
                         prediction_categories.get_category(c.category).group.value == group]
        completed = len([c for c in group_consensus if c.consensus_value is not None])
        print(f"   {group.title()}: {completed}/{count} categories predicted")
    
    # Step 9: Show confidence metrics
    print(f"\n🎯 Confidence Analysis:")
    avg_confidence = sum(c.confidence_score for c in consensus_results.values() 
                        if c.consensus_value is not None) / len([c for c in consensus_results.values() 
                        if c.consensus_value is not None])
    avg_agreement = sum(c.agreement_level for c in consensus_results.values() 
                       if c.consensus_value is not None) / len([c for c in consensus_results.values() 
                       if c.consensus_value is not None])
    
    print(f"   Average Confidence: {avg_confidence:.3f}")
    print(f"   Average Agreement: {avg_agreement:.3f}")
    print(f"   Council Stability: High ({len(council_members)}/15 experts selected)")
    
    print(f"\n🎉 Comprehensive prediction system demonstration completed!")
    print(f"   ✅ 27 prediction categories implemented")
    print(f"   ✅ 15 expert pool with personality-driven algorithms")
    print(f"   ✅ Dynamic AI Council selection")
    print(f"   ✅ Weighted consensus building")
    print(f"   ✅ Multi-factor confidence analysis")


if __name__ == "__main__":
    asyncio.run(demonstrate_comprehensive_prediction_system())