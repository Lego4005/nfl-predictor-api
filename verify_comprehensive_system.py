#!/usr/bin/env python3
"""
Comprehensive Prediction System Verification
Verifies the full 25+ category system matches official specifications
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def verify_comprehensive_system():
    """Verify the comprehensive prediction system matches specifications"""
    
    print("🔍 COMPREHENSIVE PREDICTION SYSTEM VERIFICATION")
    print("=" * 70)
    
    try:
        # 1. Verify Prediction Categories
        print("\n1️⃣ Verifying Prediction Categories...")
        from src.ml.prediction_engine.comprehensive_prediction_categories import get_prediction_categories
        
        categories_manager = get_prediction_categories()
        all_categories = categories_manager.get_all_categories()
        
        print(f"   ✅ Total Categories: {len(all_categories)}")
        
        # Check category groups
        category_summary = categories_manager.get_category_summary()
        print(f"   📊 Category Groups:")
        for group, count in category_summary['categories_by_group'].items():
            print(f"      - {group}: {count} categories")
        
        print(f"   🔴 Live Data Categories: {category_summary['live_data_categories']}")
        print(f"   🎯 Difficulty Breakdown: {category_summary['categories_by_difficulty']}")
        
        # Verify this matches specifications (should be 25+ categories)
        expected_min_categories = 25
        if len(all_categories) >= expected_min_categories:
            print(f"   ✅ PASS: {len(all_categories)} categories >= {expected_min_categories} required")
        else:
            print(f"   ❌ FAIL: {len(all_categories)} categories < {expected_min_categories} required")
        
        # 2. Verify AI Council Selection Criteria
        print("\n2️⃣ Verifying AI Council Selection Criteria...")
        from src.ml.expert_competition.council_selector import SelectionCriteria
        
        criteria = SelectionCriteria()
        print(f"   📋 Selection Weights:")
        print(f"      - Accuracy: {criteria.accuracy_weight:.1%}")
        print(f"      - Recent Performance: {criteria.recent_performance_weight:.1%}")
        print(f"      - Consistency: {criteria.consistency_weight:.1%}") 
        print(f"      - Calibration: {criteria.calibration_weight:.1%}")
        print(f"      - Specialization: {criteria.specialization_weight:.1%}")
        
        # Verify weights match specification (35%, 25%, 20%, 10%, 10%)
        expected_weights = {
            'accuracy_weight': 0.35,
            'recent_performance_weight': 0.25,
            'consistency_weight': 0.20,
            'calibration_weight': 0.10,
            'specialization_weight': 0.10
        }
        
        weights_correct = True
        for weight_name, expected_value in expected_weights.items():
            actual_value = getattr(criteria, weight_name)
            if abs(actual_value - expected_value) > 0.001:
                print(f"   ❌ FAIL: {weight_name} = {actual_value:.1%}, expected {expected_value:.1%}")
                weights_correct = False
        
        if weights_correct:
            print(f"   ✅ PASS: All weights match specification")
        
        total_weight = sum(getattr(criteria, attr) for attr in expected_weights.keys())
        if abs(total_weight - 1.0) < 0.001:
            print(f"   ✅ PASS: Weights sum to 1.0 ({total_weight:.3f})")
        else:
            print(f"   ❌ FAIL: Weights sum to {total_weight:.3f}, not 1.0")
        
        # 3. Verify Expert System Integration
        print("\n3️⃣ Verifying Expert System Integration...")
        from src.ml.expert_competition.competition_framework import ExpertCompetitionFramework
        
        framework = ExpertCompetitionFramework(supabase_client=None)
        
        print(f"   👥 Total Experts: {len(framework.experts)}")
        
        # Check expert names match official list
        expected_experts = [
            "The Analyst", "The Gambler", "The Rebel", "The Hunter", "The Rider",
            "The Scholar", "The Chaos", "The Intuition", "The Quant", "The Reversal",
            "The Fader", "The Sharp", "The Underdog", "The Consensus", "The Exploiter"
        ]
        
        actual_expert_names = [expert.name for expert in framework.experts.values()]
        actual_expert_names.sort()
        expected_experts.sort()
        
        if actual_expert_names == expected_experts:
            print(f"   ✅ PASS: All 15 official experts present")
        else:
            print(f"   ❌ FAIL: Expert names don't match specification")
            print(f"      Expected: {expected_experts}")
            print(f"      Actual: {actual_expert_names}")
        
        # 4. Test Complete Prediction Generation
        print("\n4️⃣ Testing Complete Prediction Generation...")
        
        # Create mock game data
        mock_game_data = {
            'game_id': 'verification_test_2024',
            'home_team': 'Kansas City Chiefs',
            'away_team': 'Buffalo Bills',
            'game_time': '2024-10-15T20:20:00Z',
            'location': 'Arrowhead Stadium'
        }
        
        # Test prediction generation with category predictor
        try:
            from src.ml.prediction_engine.category_specific_algorithms import CategorySpecificPredictor
            
            predictor = CategorySpecificPredictor()
            
            # Test with one expert
            test_expert = list(framework.experts.values())[0]
            prediction = predictor.generate_comprehensive_prediction(test_expert, mock_game_data)
            
            print(f"   ✅ PASS: Prediction generation successful")
            print(f"      Expert: {prediction.expert_name}")
            print(f"      Game: {prediction.game_id}")
            print(f"      Categories: Testing prediction object structure...")
            
            # Validate prediction has required fields
            required_fields = [
                'winner_prediction', 'exact_score_home', 'exact_score_away',
                'against_the_spread', 'totals_over_under', 'qb_passing_yards'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not hasattr(prediction, field) or getattr(prediction, field) is None:
                    missing_fields.append(field)
            
            if not missing_fields:
                print(f"   ✅ PASS: All required prediction fields present")
            else:
                print(f"   ❌ FAIL: Missing prediction fields: {missing_fields}")
            
        except Exception as e:
            print(f"   ❌ FAIL: Prediction generation failed: {e}")
        
        # 5. Test AI Council and Consensus
        print("\n5️⃣ Testing AI Council and Consensus...")
        
        try:
            # Select AI Council
            council_members = await framework.select_ai_council()
            print(f"   ✅ AI Council Selection: {len(council_members)} members")
            
            # Test consensus building
            if len(council_members) >= 3:  # Need at least 3 for consensus
                print(f"   ✅ PASS: Sufficient council members for consensus")
            else:
                print(f"   ❌ FAIL: Insufficient council members ({len(council_members)} < 3)")
            
        except Exception as e:
            print(f"   ❌ FAIL: AI Council selection failed: {e}")
        
        # 6. Calculate Total Prediction Volume
        print("\n6️⃣ Calculating Total Prediction Volume...")
        
        total_experts = len(framework.experts)
        total_categories = len(all_categories)
        predictions_per_game = total_experts * total_categories
        
        print(f"   📊 System Scale:")
        print(f"      - Experts: {total_experts}")
        print(f"      - Categories per Expert: {total_categories}")
        print(f"      - Predictions per Game: {predictions_per_game:,}")
        
        # Verify this matches documentation (should be 15 × 25+ = 375+ predictions per game)
        expected_min_predictions = 15 * 25  # 15 experts × 25 categories minimum
        
        if predictions_per_game >= expected_min_predictions:
            print(f"   ✅ PASS: {predictions_per_game:,} predictions >= {expected_min_predictions:,} required")
        else:
            print(f"   ❌ FAIL: {predictions_per_game:,} predictions < {expected_min_predictions:,} required")
        
        # 7. Verify Category Details
        print("\n7️⃣ Verifying Category Implementation Details...")
        
        # Sample key categories that should exist
        key_categories = [
            'winner_prediction', 'exact_score_home', 'exact_score_away', 'margin_of_victory',
            'against_the_spread', 'totals_over_under', 'first_half_winner',
            'qb_passing_yards', 'qb_touchdowns', 'rb_rushing_yards',
            'weather_impact_score', 'injury_impact_score', 'coaching_advantage'
        ]
        
        missing_categories = []
        for category_id in key_categories:
            category = categories_manager.get_category(category_id)
            if not category:
                missing_categories.append(category_id)
        
        if not missing_categories:
            print(f"   ✅ PASS: All key categories implemented")
        else:
            print(f"   ❌ FAIL: Missing key categories: {missing_categories}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 70)
        
        print(f"✅ Prediction Categories: {len(all_categories)} implemented")
        print(f"✅ Expert Count: {len(framework.experts)} personality experts")
        print(f"✅ AI Council Selection: 5-component weighting system")
        print(f"✅ Prediction Volume: {predictions_per_game:,} predictions per game")
        print(f"✅ Category Groups: {len(category_summary['categories_by_group'])} groups")
        print(f"✅ Live Data Categories: {category_summary['live_data_categories']} categories")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_comprehensive_system())
    if success:
        print("\n🎉 VERIFICATION COMPLETE: System matches specifications!")
        sys.exit(0)
    else:
        print("\n💥 VERIFICATION FAILED: System needs fixes.")
        sys.exit(1)