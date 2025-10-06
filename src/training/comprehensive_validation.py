"""
Comprehensive Validation Framework for NFL Prediction System

This module implements systematic testing arse game scenarios
to validate expert personality differentiation and prediction reasonableness.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from training.expert_configuration import ExpertType, ExpertConfigurationManager
from training.temporal_decay_calculator import TemporalDecayCalculator
from training.memory_retrieval_system import MemoryRetrievalSystem
from training.prediction_generator import PredictionGenerator, PredictionType


@dataclass
class ValidationResult:
    """Results from validation testing"""
    test_name: str
    game_context: Dict[str, Any]
    expert_predictions: Dict[str, Any]
    analysis: Dict[str, Any]
    issues_found: List[str]
    passed: bool


class ComprehensiveValidator:
    """Comprehensive validation framework for expert prediction system"""

    def __init__(self):
        self.config_manager = ExpertConfigurationManager()
        self.temporal_calculator = TemporalDecayCalculator(self.config_manager)
        self.memory_retrieval = MemoryRetrievalSystem(self.config_manager, self.temporal_calculator)
        self.prediction_generator = PredictionGenerator(
            self.config_manager, self.temporal_calculator, self.memory_retrieval
        )

    async def run_comprehensive_validation(self) -> Dict[str, ValidationResult]:
        """Run all validation tests"""

        print("🔍 NFL Prediction System - Comprehensive Validation")
        print("=" * 60)

        validation_results = {}

        # Test 1: Neutral game scenario (no extreme factors)
        print("\\n1. Testing Neutral Game Scenario...")
        validation_results['neutral_game'] = await self._test_neutral_game()

        # Test 2: Extreme weather game
        print("\\n2. Testing Extreme Weather Game...")
        validation_results['extreme_weather'] = await self._test_extreme_weather_game()

        # Test 3: Missing data scenarios
        print("\\n3. Testing Missing Data Scenarios...")
        validation_results['missing_data'] = await self._test_missing_data_scenarios()

        # Test 4: Conflicting signals game
        print("\\n4. Testing Conflicting Signals Game...")
        validation_results['conflicting_signals'] = await self._test_conflicting_signals_game()

        # Test 5: Prediction reasonableness bounds
        print("\\n5. Testing Prediction Reasonableness...")
        validation_results['reasonableness'] = await self._test_prediction_reasonableness()

        # Generate comprehensive report
        self._generate_validation_report(validation_results)

        return validation_results

    async def _test_neutral_game(self) -> ValidationResult:
        """Test game with balanced characteristics - no extreme triggers"""

        neutral_game_context = {
            'home_team': 'SEA',
            'away_team': 'ARI',
            'week': 8,
            'season': 2024,
            'weather': {
                'temperature': 68,
                'wind_speed': 5,
                'conditions': 'clear'
            },
            'division_game': False,
            'line_movement': {
                'opening': -2.5,
                'current': -2.5  # No movement
            },
            'total_line': 44.0,
            'public_betting': {
                'home': 52,  # Balanced
                'away': 48
            },
            'momentum': {
                'home': 'neutral_2_2_record',
                'away': 'neutral_2_2_record'
            }
        }

        # Generate predictions from all experts
        expert_predictions = {}
        issues_found = []

        for expert_type in ExpertType:
            try:
                predictions = await self.prediction_generator.generate_prediction(
                    expert_type, neutral_game_context, [PredictionType.WINNER]
                )

                winner_pred = predictions[0]
                expert_predictions[expert_type.value] = {
                    'winner': winner_pred.predicted_winner,
                    'win_probability': winner_pred.win_probability,
                    'confidence': winner_pred.confidence_level,
                    'reasoning': winner_pred.reasoning_chain
                }

            except Exception as e:
                issues_found.append(f"{expert_type.value}: {str(e)}")

        # Analyze results
        analysis = self._analyze_neutral_game_results(expert_predictions, neutral_game_context)

        return ValidationResult(
            test_name="Neutral Game Scenario",
            game_context=neutral_game_context,
            expert_predictions=expert_predictions,
            analysis=analysis,
            issues_found=issues_found,
            passed=len(issues_found) == 0 and analysis['reasonable_distribution']
        )

    def _analyze_neutral_game_results(
        self,
        expert_predictions: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze neutral game prediction results"""

        analysis = {
            'total_experts': len(expert_predictions),
            'home_supporters': 0,
            'away_supporters': 0,
            'confidence_range': {'min': 1.0, 'max': 0.0, 'avg': 0.0},
            'win_prob_range': {'min': 1.0, 'max': 0.0, 'avg': 0.0},
            'extreme_predictions': [],
            'reasonable_distribution': True
        }

        confidences = []
        win_probs = []

        for expert_id, pred_data in expert_predictions.items():
            # Count supporters
            if pred_data['winner'] == game_context['home_team']:
                analysis['home_supporters'] += 1
            else:
                analysis['away_supporters'] += 1

            # Collect confidence and probability data
            confidence = pred_data['confidence']
            win_prob = pred_data['win_probability']

            confidences.append(confidence)
            win_probs.append(win_prob)

            # Check for extreme predictions
            if win_prob >= 0.80 or win_prob <= 0.20:
                analysis['extreme_predictions'].append({
                    'expert': expert_id,
                    'win_probability': win_prob,
                    'confidence': confidence
                })

            if confidence >= 0.60:  # High confidence in neutral game is suspicious
                analysis['extreme_predictions'].append({
                    'expert': expert_id,
                    'type': 'high_confidence_neutral',
                    'confidence': confidence
                })

        # Calculate ranges
        if confidences:
            analysis['confidence_range'] = {
                'min': min(confidences),
                'max': max(confidences),
                'avg': sum(confidences) / len(confidences)
            }

        if win_probs:
            analysis['win_prob_range'] = {
                'min': min(win_probs),
                'max': max(win_probs),
                'avg': sum(win_probs) / len(win_probs)
            }

        # Check if distribution is reasonable
        analysis['reasonable_distribution'] = (
            len(analysis['extreme_predictions']) <= 2 and  # Max 2 extreme predictions
            analysis['confidence_range']['max'] <= 0.50 and  # No high confidence in neutral game
            0.30 <= analysis['win_prob_range']['avg'] <= 0.70  # Reasonable average
        )

        return analysis

    async def _test_extreme_weather_game(self) -> ValidationResult:
        """Test game with extreme weather conditions"""

        extreme_weather_context = {
            'home_team': 'GB',
            'away_team': 'CHI',
            'week': 15,
            'season': 2024,
            'weather': {
                'temperature': 8,  # Extreme cold
                'wind_speed': 25,  # High winds
                'conditions': 'blizzard'
            },
            'division_game': True,
            'line_movement': {
                'opening': -3.0,
                'current': -1.5  # Line moved toward underdog (weather impact)
            },
            'total_line': 38.5,  # Low total due to weather
            'public_betting': {
                'home': 58,
                'away': 42
            },
            'momentum': {
                'home': 'neutral_3_2_record',
                'away': 'cold_1_4_record'
            }
        }

        # Test specific experts that should react differently to weather
        weather_sensitive_experts = [
            ExpertType.FUNDAMENTALIST_SCHOLAR,  # Should analyze weather impact deeply
            ExpertType.GUT_INSTINCT_EXPERT,     # Should barely mention weather
            ExpertType.STATISTICS_PURIST,       # Should quantify weather effects
            ExpertType.CHAOS_THEORY_BELIEVER    # Should see weather as chaos factor
        ]

        expert_predictions = {}
        issues_found = []

        for expert_type in weather_sensitive_experts:
            try:
                predictions = await self.prediction_generator.generate_prediction(
                    expert_type, extreme_weather_context, [PredictionType.WINNER, PredictionType.TOTAL]
                )

                winner_pred = predictions[0]
                total_pred = predictions[1]

                expert_predictions[expert_type.value] = {
                    'winner': winner_pred.predicted_winner,
                    'win_probability': winner_pred.win_probability,
                    'confidence': winner_pred.confidence_level,
                    'total': total_pred.predicted_total,
                    'total_confidence': total_pred.total_confidence,
                    'reasoning': winner_pred.reasoning_chain,
                    'mentions_weather': any('weather' in reason.lower() or 'cold' in reason.lower()
                                          or 'wind' in reason.lower() or 'blizzard' in reason.lower()
                                          for reason in winner_pred.reasoning_chain)
                }

            except Exception as e:
                issues_found.append(f"{expert_type.value}: {str(e)}")

        # Analyze weather sensitivity
        analysis = self._analyze_weather_sensitivity(expert_predictions, extreme_weather_context)

        return ValidationResult(
            test_name="Extreme Weather Game",
            game_context=extreme_weather_context,
            expert_predictions=expert_predictions,
            analysis=analysis,
            issues_found=issues_found,
            passed=len(issues_found) == 0 and analysis['appropriate_weather_response']
        )

    def _analyze_weather_sensitivity(
        self,
        expert_predictions: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how experts respond to extreme weather"""

        analysis = {
            'weather_mentions': {},
            'total_adjustments': {},
            'appropriate_weather_response': True,
            'issues': []
        }

        baseline_total = game_context['total_line']  # 38.5

        for expert_id, pred_data in expert_predictions.items():
            # Check weather mentions in reasoning
            analysis['weather_mentions'][expert_id] = pred_data['mentions_weather']

            # Check total adjustments
            predicted_total = pred_data['total']
            adjustment = predicted_total - baseline_total
            analysis['total_adjustments'][expert_id] = adjustment

            # Validate expert-specific responses
            if expert_id == 'fundamentalist_scholar':
                if not pred_data['mentions_weather']:
                    analysis['issues'].append("Scholar should analyze weather impact")
                    analysis['appropriate_weather_response'] = False

            elif expert_id == 'gut_instinct_expert':
                if pred_data['mentions_weather']:
                    # Gut expert might mention weather but shouldn't focus on it
                    pass

            elif expert_id == 'statistics_purist':
                if not pred_data['mentions_weather']:
                    analysis['issues'].append("Quant should quantify weather effects")
                    analysis['appropriate_weather_response'] = False

        return analysis

    async def _test_missing_data_scenarios(self) -> ValidationResult:
        """Test how experts handle missing data"""

        missing_data_context = {
            'home_team': 'LAR',
            'away_team': 'SF',
            'week': 12,
            'season': 2024,
            # Missing weather data
            'division_game': True,
            'line_movement': {
                'opening': -6.0,
                'current': -6.0
            },
            'total_line': 47.0,
            # Missing public betting data
            # Missing momentum data
        }

        # Test experts that rely on missing data
        data_dependent_experts = [
            ExpertType.CONTRARIAN_REBEL,      # Needs public betting data
            ExpertType.MOMENTUM_RIDER,        # Needs momentum data
            ExpertType.POPULAR_NARRATIVE_FADER # Needs public betting data
        ]

        expert_predictions = {}
        issues_found = []

        for expert_type in data_dependent_experts:
            try:
                predictions = await self.prediction_generator.generate_prediction(
                    expert_type, missing_data_context, [PredictionType.WINNER]
                )

                winner_pred = predictions[0]
                expert_predictions[expert_type.value] = {
                    'winner': winner_pred.predicted_winner,
                    'win_probability': winner_pred.win_probability,
                    'confidence': winner_pred.confidence_level,
                    'reasoning': winner_pred.reasoning_chain,
                    'handled_missing_data': True  # If we get here, it didn't crash
                }

            except Exception as e:
                issues_found.append(f"{expert_type.value}: Failed with missing data - {str(e)}")
                expert_predictions[expert_type.value] = {
                    'handled_missing_data': False,
                    'error': str(e)
                }

        analysis = {
            'experts_tested': len(data_dependent_experts),
            'successful_predictions': len([p for p in expert_predictions.values()
                                         if p.get('handled_missing_data', False)]),
            'graceful_degradation': len(issues_found) == 0
        }

        return ValidationResult(
            test_name="Missing Data Scenarios",
            game_context=missing_data_context,
            expert_predictions=expert_predictions,
            analysis=analysis,
            issues_found=issues_found,
            passed=analysis['graceful_degradation']
        )

    async def _test_conflicting_signals_game(self) -> ValidationResult:
        """Test game with conflicting analytical signals"""

        conflicting_signals_context = {
            'home_team': 'MIA',
            'away_team': 'BUF',
            'week': 13,
            'season': 2024,
            'weather': {
                'temperature': 15,  # Very cold (bad for MIA)
                'wind_speed': 20,
                'conditions': 'snow'
            },
            'division_game': True,
            'line_movement': {
                'opening': -1.0,
                'current': -3.5  # Sharp money on home team despite weather
            },
            'total_line': 41.0,
            'public_betting': {
                'home': 35,  # Public on away team (weather concern)
                'away': 65
            },
            'momentum': {
                'home': 'hot_4_game_win_streak',  # Hot but weather disadvantage
                'away': 'neutral_3_2_record'
            }
        }

        # Test experts who should struggle with conflicting signals
        conflicted_experts = [
            ExpertType.MOMENTUM_RIDER,           # Hot streak vs weather disadvantage
            ExpertType.CONTRARIAN_REBEL,         # Public on away but sharp money on home
            ExpertType.SHARP_MONEY_FOLLOWER,     # Sharp money vs weather logic
            ExpertType.UNDERDOG_CHAMPION         # Home is now favorite despite weather
        ]

        expert_predictions = {}
        issues_found = []

        for expert_type in conflicted_experts:
            try:
                predictions = await self.prediction_generator.generate_prediction(
                    expert_type, conflicting_signals_context, [PredictionType.WINNER]
                )

                winner_pred = predictions[0]
                expert_predictions[expert_type.value] = {
                    'winner': winner_pred.predicted_winner,
                    'win_probability': winner_pred.win_probability,
                    'confidence': winner_pred.confidence_level,
                    'reasoning': winner_pred.reasoning_chain
                }

            except Exception as e:
                issues_found.append(f"{expert_type.value}: {str(e)}")

        # Analyze how experts handled conflicts
        analysis = self._analyze_conflicting_signals(expert_predictions, conflicting_signals_context)

        return ValidationResult(
            test_name="Conflicting Signals Game",
            game_context=conflicting_signals_context,
            expert_predictions=expert_predictions,
            analysis=analysis,
            issues_found=issues_found,
            passed=len(issues_found) == 0 and analysis['handled_conflicts_appropriately']
        )

    def _analyze_conflicting_signals(
        self,
        expert_predictions: Dict[str, Any],
        game_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how experts handled conflicting signals"""

        analysis = {
            'confidence_appropriately_reduced': True,
            'experts_acknowledged_conflict': 0,
            'handled_conflicts_appropriately': True,
            'conflict_details': {}
        }

        for expert_id, pred_data in expert_predictions.items():
            confidence = pred_data['confidence']
            reasoning = pred_data['reasoning']

            # Check if confidence is appropriately reduced due to conflicting signals
            if confidence > 0.40:  # High confidence despite conflicts
                analysis['confidence_appropriately_reduced'] = False
                analysis['handled_conflicts_appropriately'] = False

            # Check if reasoning acknowledges the conflict
            reasoning_text = ' '.join(reasoning).lower()
            conflict_words = ['however', 'but', 'although', 'despite', 'conflict', 'tension']
            if any(word in reasoning_text for word in conflict_words):
                analysis['experts_acknowledged_conflict'] += 1

            analysis['conflict_details'][expert_id] = {
                'confidence': confidence,
                'acknowledged_conflict': any(word in reasoning_text for word in conflict_words)
            }

        return analysis

    async def _test_prediction_reasonableness(self) -> ValidationResult:
        """Test prediction reasonableness across multiple games"""

        # Create 5 diverse test games
        test_games = [
            self._create_heavy_favorite_game(),
            self._create_pick_em_game(),
            self._create_high_total_game(),
            self._create_low_total_game(),
            self._create_primetime_game()
        ]

        all_predictions = {}
        issues_found = []

        for i, game_context in enumerate(test_games):
            game_predictions = {}

            # Test 5 representative experts per game
            test_experts = [
                ExpertType.CONSERVATIVE_ANALYZER,
                ExpertType.RISK_TAKING_GAMBLER,
                ExpertType.STATISTICS_PURIST,
                ExpertType.UNDERDOG_CHAMPION,
                ExpertType.CHAOS_THEORY_BELIEVER
            ]

            for expert_type in test_experts:
                try:
                    predictions = await self.prediction_generator.generate_prediction(
                        expert_type, game_context, [PredictionType.WINNER, PredictionType.TOTAL]
                    )

                    winner_pred = predictions[0]
                    total_pred = predictions[1]

                    game_predictions[expert_type.value] = {
                        'winner_prob': winner_pred.win_probability,
                        'confidence': winner_pred.confidence_level,
                        'total': total_pred.predicted_total,
                        'total_confidence': total_pred.total_confidence
                    }

                except Exception as e:
                    issues_found.append(f"Game {i+1}, {expert_type.value}: {str(e)}")

            all_predictions[f'game_{i+1}'] = {
                'context': game_context,
                'predictions': game_predictions
            }

        # Analyze reasonableness across all games
        analysis = self._analyze_prediction_reasonableness(all_predictions)

        return ValidationResult(
            test_name="Prediction Reasonableness",
            game_context={'multiple_games': len(test_games)},
            expert_predictions=all_predictions,
            analysis=analysis,
            issues_found=issues_found,
            passed=len(issues_found) == 0 and analysis['all_reasonable']
        )

    def _analyze_prediction_reasonableness(self, all_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prediction reasonableness across multiple games"""

        all_win_probs = []
        all_confidences = []
        all_totals = []
        extreme_predictions = []

        for game_id, game_data in all_predictions.items():
            for expert_id, pred_data in game_data['predictions'].items():
                win_prob = pred_data['winner_prob']
                confidence = pred_data['confidence']
                total = pred_data['total']

                all_win_probs.append(win_prob)
                all_confidences.append(confidence)
                all_totals.append(total)

                # Flag extreme predictions
                if win_prob <= 0.15 or win_prob >= 0.85:
                    extreme_predictions.append({
                        'game': game_id,
                        'expert': expert_id,
                        'win_prob': win_prob,
                        'type': 'extreme_win_probability'
                    })

                if confidence >= 0.80:
                    extreme_predictions.append({
                        'game': game_id,
                        'expert': expert_id,
                        'confidence': confidence,
                        'type': 'extreme_confidence'
                    })

                if total <= 20 or total >= 70:
                    extreme_predictions.append({
                        'game': game_id,
                        'expert': expert_id,
                        'total': total,
                        'type': 'extreme_total'
                    })

        analysis = {
            'total_predictions': len(all_win_probs),
            'win_prob_stats': {
                'min': min(all_win_probs),
                'max': max(all_win_probs),
                'avg': sum(all_win_probs) / len(all_win_probs),
                'std': self._calculate_std(all_win_probs)
            },
            'confidence_stats': {
                'min': min(all_confidences),
                'max': max(all_confidences),
                'avg': sum(all_confidences) / len(all_confidences),
                'std': self._calculate_std(all_confidences)
            },
            'total_stats': {
                'min': min(all_totals),
                'max': max(all_totals),
                'avg': sum(all_totals) / len(all_totals),
                'std': self._calculate_std(all_totals)
            },
            'extreme_predictions': extreme_predictions,
            'extreme_count': len(extreme_predictions),
            'all_reasonable': len(extreme_predictions) <= 3  # Allow some extremes
        }

        return analysis

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def _create_heavy_favorite_game(self) -> Dict[str, Any]:
        """Create game with heavy favorite"""
        return {
            'home_team': 'BUF',
            'away_team': 'NYJ',
            'week': 10,
            'season': 2024,
            'weather': {'temperature': 45, 'wind_speed': 8, 'conditions': 'clear'},
            'line_movement': {'opening': -13.5, 'current': -14.0},
            'total_line': 42.0,
            'public_betting': {'home': 85, 'away': 15},
            'momentum': {'home': 'hot_5_game_win_streak', 'away': 'cold_0_6_record'}
        }

    def _create_pick_em_game(self) -> Dict[str, Any]:
        """Create pick'em game"""
        return {
            'home_team': 'CIN',
            'away_team': 'BAL',
            'week': 9,
            'season': 2024,
            'weather': {'temperature': 55, 'wind_speed': 6, 'conditions': 'clear'},
            'line_movement': {'opening': -1.0, 'current': -0.5},
            'total_line': 48.5,
            'public_betting': {'home': 51, 'away': 49},
            'momentum': {'home': 'neutral_3_3_record', 'away': 'neutral_4_2_record'}
        }

    def _create_high_total_game(self) -> Dict[str, Any]:
        """Create high-scoring game"""
        return {
            'home_team': 'KC',
            'away_team': 'LAC',
            'week': 7,
            'season': 2024,
            'weather': {'temperature': 78, 'wind_speed': 2, 'conditions': 'dome'},
            'line_movement': {'opening': -3.0, 'current': -2.5},
            'total_line': 54.5,
            'public_betting': {'home': 62, 'away': 38},
            'momentum': {'home': 'hot_offense_35_ppg', 'away': 'hot_offense_32_ppg'}
        }

    def _create_low_total_game(self) -> Dict[str, Any]:
        """Create low-scoring game"""
        return {
            'home_team': 'PIT',
            'away_team': 'CLE',
            'week': 14,
            'season': 2024,
            'weather': {'temperature': 22, 'wind_speed': 18, 'conditions': 'snow'},
            'line_movement': {'opening': -2.5, 'current': -1.5},
            'total_line': 36.5,
            'public_betting': {'home': 48, 'away': 52},
            'momentum': {'home': 'defensive_struggle', 'away': 'offensive_struggles'}
        }

    def _create_primetime_game(self) -> Dict[str, Any]:
        """Create primetime game"""
        return {
            'home_team': 'DAL',
            'away_team': 'PHI',
            'week': 16,
            'season': 2024,
            'weather': {'temperature': 42, 'wind_speed': 12, 'conditions': 'clear'},
            'line_movement': {'opening': -4.0, 'current': -6.5},
            'total_line': 45.5,
            'public_betting': {'home': 73, 'away': 27},
            'momentum': {'home': 'primetime_struggles', 'away': 'playoff_push'},
            'primetime': True
        }

    def _generate_validation_report(self, validation_results: Dict[str, ValidationResult]):
        """Generate comprehensive validation report"""

        print("\\n" + "=" * 60)
        print("COMPREHENSIVE VALIDATION REPORT")
        print("=" * 60)

        total_tests = len(validation_results)
        passed_tests = sum(1 for result in validation_results.values() if result.passed)

        print(f"\\nOverall Results: {passed_tests}/{total_tests} tests passed")
        print(f"Success Rate: {passed_tests/total_tests:.1%}")

        for test_name, result in validation_results.items():
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\\n{status} {result.test_name}")

            if result.issues_found:
                print("  Issues:")
                for issue in result.issues_found:
                    print(f"    • {issue}")

            # Print key analysis points
            if 'extreme_predictions' in result.analysis:
                extreme_count = len(result.analysis['extreme_predictions'])
                if extreme_count > 0:
                    print(f"  Extreme predictions: {extreme_count}")

            if 'confidence_range' in result.analysis:
                conf_range = result.analysis['confidence_range']
                print(f"  Confidence range: {conf_range['min']:.1%} - {conf_range['max']:.1%}")

        print("\\n" + "=" * 60)

        if passed_tests == total_tests:
            print("🎉 ALL VALIDATION TESTS PASSED - System ready for training loop")
        else:
            print("⚠️  VALIDATION ISSUES FOUND - Fix before building training loop")

        print("=" * 60)


async def run_validation():
    """Run the comprehensive validation suite"""
    validator = ComprehensiveValidator()
    results = await validator.run_comprehensive_validation()
    return results


if __name__ == "__main__":
    asyncio.run(run_validation())
