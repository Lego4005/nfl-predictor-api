#!/usr/bin/env python3
"""
Validation Script for AI Game Narrator
Tests core functionality without external ML dependencies
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_structures():
    """Test basic data structures and classes"""
    print("🧪 Testing basic data structures...")

    try:
        # Test GameSituation enum
        from src.ml.ai_game_narrator import GameSituation
        assert GameSituation.FOURTH_DOWN.value == "fourth_down"
        assert GameSituation.RED_ZONE.value == "red_zone"
        print("✅ GameSituation enum working")

        # Test MomentumShift enum
        from src.ml.ai_game_narrator import MomentumShift
        assert MomentumShift.MASSIVE_POSITIVE.value == "massive_positive"
        print("✅ MomentumShift enum working")

        # Test GameState dataclass
        from src.ml.ai_game_narrator import GameState
        game_state = GameState(
            quarter=4,
            time_remaining="2:15",
            down=3,
            yards_to_go=7,
            yard_line=22,
            home_score=17,
            away_score=14,
            possession="home",
            last_play={},
            drive_info={},
            game_id="test_game",
            week=15,
            season=2024
        )
        assert game_state.quarter == 4
        assert game_state.possession == "home"
        print("✅ GameState dataclass working")

        return True

    except Exception as e:
        print(f"❌ Basic structures test failed: {e}")
        return False


def test_analyzer_components():
    """Test individual analyzer components"""
    print("🧪 Testing analyzer components...")

    try:
        # Test SituationAnalyzer
        from src.ml.ai_game_narrator import SituationAnalyzer, GameState

        analyzer = SituationAnalyzer()
        game_state = GameState(
            quarter=4, time_remaining="2:00", down=4, yards_to_go=2,
            yard_line=15, home_score=14, away_score=17, possession="home",
            last_play={}, drive_info={}, game_id="test", week=1, season=2024
        )

        situations = analyzer.identify_situation(game_state)
        assert len(situations) > 0
        print(f"✅ SituationAnalyzer identified {len(situations)} situations")

        pressure = analyzer.calculate_situation_pressure(game_state, situations)
        assert 0 <= pressure <= 1
        print(f"✅ Pressure calculation: {pressure:.2f}")

        # Test HistoricalComparator
        from src.ml.ai_game_narrator import HistoricalComparator

        comparator = HistoricalComparator()
        similar = comparator.find_similar_situations(game_state, limit=3)
        assert len(similar) <= 3
        print(f"✅ HistoricalComparator found {len(similar)} similar situations")

        success_rate = comparator.calculate_situation_success_rate(
            situations[0], {"home_field": True}
        )
        assert 0 <= success_rate <= 1
        print(f"✅ Success rate calculation: {success_rate:.1%}")

        return True

    except Exception as e:
        print(f"❌ Analyzer components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weather_analyzer():
    """Test weather impact analysis"""
    print("🧪 Testing weather analyzer...")

    try:
        from src.ml.ai_game_narrator import WeatherImpactAnalyzer, GameState

        weather_analyzer = WeatherImpactAnalyzer()

        # Test with dome game
        dome_weather = {"dome_game": False, "temperature": 72, "wind_speed": 0}
        game_state = GameState(
            quarter=2, time_remaining="10:00", down=1, yards_to_go=10,
            yard_line=50, home_score=0, away_score=0, possession="home",
            last_play={}, drive_info={}, game_id="test", week=1, season=2024
        )

        impact = weather_analyzer.analyze_weather_impact(dome_weather, game_state)
        assert "impact_level" in impact
        assert "narrative" in impact
        print(f"✅ Weather impact analysis: {impact['impact_level']}")

        # Test with severe weather
        severe_weather = {
            "dome_game": True, "temperature": 20, "wind_speed": 25,
            "precipitation": 0.3, "visibility": 3
        }
        severe_impact = weather_analyzer.analyze_weather_impact(severe_weather, game_state)
        print(f"✅ Severe weather impact: {severe_impact['impact_level']}")

        return True

    except Exception as e:
        print(f"❌ Weather analyzer test failed: {e}")
        return False


def test_decision_engine():
    """Test decision recommendation engine"""
    print("🧪 Testing decision engine...")

    try:
        from src.ml.ai_game_narrator import DecisionEngine, GameState

        engine = DecisionEngine()

        # Create 4th down scenario
        fourth_down_state = GameState(
            quarter=4, time_remaining="5:30", down=4, yards_to_go=2,
            yard_line=35, home_score=14, away_score=17, possession="home",
            last_play={}, drive_info={}, game_id="test", week=1, season=2024
        )

        context = {"pressure_level": 0.8, "weather_impact": 0.1}
        recommendation = engine.recommend_fourth_down_decision(fourth_down_state, context)

        assert recommendation is not None
        assert recommendation.recommendation in ["punt", "field_goal", "go_for_it"]
        assert 0 <= recommendation.success_probability <= 1
        print(f"✅ 4th down recommendation: {recommendation.recommendation} ({recommendation.success_probability:.1%})")

        return True

    except Exception as e:
        print(f"❌ Decision engine test failed: {e}")
        return False


def test_integration_without_ml():
    """Test integration without ML dependencies"""
    print("🧪 Testing integration (without ML models)...")

    try:
        # Mock the ML models to avoid dependencies
        import src.ml.ai_game_narrator as narrator_module

        # Create a mock predictor that doesn't require actual ML libraries
        class MockPredictor:
            def __init__(self):
                self.is_trained = False

            def load_model(self):
                pass

            def predict_proba(self, X):
                import random
                # Return mock probabilities
                return [[0.3, 0.5, 0.2] for _ in range(len(X) if hasattr(X, '__len__') else 1)]

        # Monkey patch the predictors
        original_ensemble = narrator_module.AdvancedEnsemblePredictor
        original_enhanced = narrator_module.EnhancedGamePredictor

        narrator_module.AdvancedEnsemblePredictor = MockPredictor
        narrator_module.EnhancedGamePredictor = MockPredictor

        # Now test the narrator
        from src.ml.ai_game_narrator import AIGameNarrator, GameState

        narrator = AIGameNarrator()

        game_state = GameState(
            quarter=4, time_remaining="2:15", down=3, yards_to_go=7,
            yard_line=22, home_score=17, away_score=14, possession="home",
            last_play={"type": "pass_complete", "yards": 12},
            drive_info={"plays": 8, "yards": 64},
            game_id="integration_test", week=15, season=2024
        )

        context = {
            "weather_data": {"temperature": 28, "wind_speed": 12, "dome_game": False},
            "team_stats": {"home": {"red_zone_efficiency": 0.72}},
            "recent_scoring": [{"team": "home", "points": 3, "time": "3:22"}]
        }

        insight = narrator.generate_comprehensive_insight(game_state, context)
        assert insight is not None
        print("✅ Comprehensive insight generation successful")

        summary = narrator.get_insight_summary(insight)
        assert "predictions" in summary
        assert "insights" in summary
        assert "momentum" in summary
        print("✅ Insight summary generation successful")

        # Restore original classes
        narrator_module.AdvancedEnsemblePredictor = original_ensemble
        narrator_module.EnhancedGamePredictor = original_enhanced

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_structures():
    """Test API-related structures"""
    print("🧪 Testing API structures...")

    try:
        from src.api.narrator_endpoints import GameStateRequest, ContextRequest, InsightRequest

        # Test Pydantic models
        game_state_data = {
            "quarter": 4,
            "time_remaining": "2:15",
            "down": 3,
            "yards_to_go": 7,
            "yard_line": 22,
            "home_score": 17,
            "away_score": 14,
            "possession": "home",
            "game_id": "test_game",
            "week": 15,
            "season": 2024
        }

        game_request = GameStateRequest(**game_state_data)
        assert game_request.quarter == 4
        assert game_request.possession == "home"
        print("✅ GameStateRequest validation working")

        context_data = {
            "weather_data": {"temperature": 65, "dome_game": True},
            "team_stats": {"home": {"red_zone_efficiency": 0.72}}
        }

        context_request = ContextRequest(**context_data)
        assert context_request.weather_data["dome_game"] is True
        print("✅ ContextRequest validation working")

        insight_data = {
            "game_state": game_state_data,
            "context": context_data
        }

        insight_request = InsightRequest(**insight_data)
        assert insight_request.game_state.quarter == 4
        print("✅ InsightRequest validation working")

        return True

    except Exception as e:
        print(f"❌ API structures test failed: {e}")
        return False


def main():
    """Run all validation tests"""
    print("🚀 Starting AI Game Narrator Validation")
    print("=" * 50)

    tests = [
        test_basic_structures,
        test_analyzer_components,
        test_weather_analyzer,
        test_decision_engine,
        test_integration_without_ml,
        test_api_structures
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print()
        if test():
            passed += 1
            print("✅ Test passed")
        else:
            print("❌ Test failed")

    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! AI Game Narrator is working correctly.")
        print("\n📋 Next Steps:")
        print("1. Install ML dependencies (pandas, tensorflow, etc.)")
        print("2. Train or load ML models")
        print("3. Set up Redis for caching")
        print("4. Configure ESPN API access")
        print("5. Deploy with Docker Compose")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)