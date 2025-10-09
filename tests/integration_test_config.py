"""
Integration Test Configuratio
nfiguration settings and utilities for NFL Expert Prediction System integration tests.
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TestConfiguration:
    """Configuration for integration tests"""

    # Test environment settings
    test_database_url: str = "sqlite:///:memory:"
    test_redis_db: int = 15
    test_timeout_seconds: int = 30

    # Mock data settings
    mock_experts_count: int = 15
    mock_games_count: int = 10
    mock_memories_per_expert: int = 20

    # Performance test settings
    concurrent_requests_count: int = 5
    memory_retrieval_timeout: float = 2.0
    prediction_generation_timeout: float = 10.0

    # Test data paths
    test_data_dir: str = "tests/fixtures"
    mock_responses_dir: str = "tests/mocks"

    # Expert configurations for testing
    test_expert_configs: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        if self.test_expert_configs is None:
            self.test_expert_configs = {
                'conservative_analyzer': {
                    'name': 'The Analyst',
                    'model': 'anthropic/claude-sonnet-4.5',
                    'personality_traits': {
                        'risk_tolerance': 0.2,
                        'analytics_trust': 0.9,
                        'optimism': 0.4,
                        'contrarian_tendency': 0.1
                    },
                    'expected_confidence_range': (0.45, 0.65),
                    'expected_reasoning_patterns': [
                        'Statistical analysis',
                        'Historical data',
                        'Defensive metrics'
                    ]
                },
                'risk_taking_gambler': {
                    'name': 'The Gambler',
                    'model': 'x-ai/grok-4-fast',
                    'personality_traits': {
                        'risk_tolerance': 0.9,
                        'analytics_trust': 0.3,
                        'optimism': 0.7,
                        'contrarian_tendency': 0.6
                    },
                    'expected_confidence_range': (0.65, 0.85),
                    'expected_reasoning_patterns': [
                        'Momentum',
                        'Upset potential',
                        'High-risk play'
                    ]
                },
                'contrarian_rebel': {
                    'name': 'The Rebel',
                    'model': 'google/gemini-2.5-flash-preview-09-2025',
                    'personality_traits': {
                        'risk_tolerance': 0.7,
                        'analytics_trust': 0.5,
                        'optimism': 0.3,
                        'contrarian_tendency': 0.9
                    },
                    'expected_confidence_range': (0.50, 0.75),
                    'expected_reasoning_patterns': [
                        'Going against public opinion',
                        'Market overreaction',
                        'Contrarian play'
                    ]
                }
            }

# Global test configuration instance
TEST_CONFIG = TestConfiguration()

# Test data generators
class TestDataGenerator:
    """Generate test data for integration tests"""

    @staticmethod
    def generate_game_contexts(count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample game contexts for testing"""
        games = []
        teams = ['KC', 'DEN', 'BUF', 'MIA', 'DAL', 'NYG', 'SF', 'LAR']

        for i in range(count):
            home_team = teams[i % len(teams)]
            away_team = teams[(i + 1) % len(teams)]

            game = {
                'game_id': f'nfl_2024_week_{(i % 17) + 1}_{away_team.lower()}_{home_team.lower()}',
                'home_team': home_team,
                'away_team': away_team,
                'season': 2024,
                'week': (i % 17) + 1,
                'game_date': datetime(2024, 9, 8 + i, 13, 0),
                'is_divisional': i % 3 == 0,
                'is_primetime': i % 4 == 0,
                'current_spread': -3.5 + (i * 0.5),
                'total_line': 45.5 + i,
                'weather_conditions': {
                    'temperature': 70 + (i * 2),
                    'wind_speed': 5 + i,
                    'conditions': 'Clear' if i % 2 == 0 else 'Cloudy'
                }
            }
            games.append(game)

        return games

    @staticmethod
    def generate_historical_games(count: int = 10) -> List[Dict[str, Any]]:
        """Generate historical games for training loop testing"""
        games = []
        teams = ['KC', 'DEN', 'BUF', 'MIA', 'DAL', 'NYG']

        for i in range(count):
            home_team = teams[i % len(teams)]
            away_team = teams[(i + 1) % len(teams)]

            # Generate realistic final scores
            home_score = 17 + (i % 14)
            away_score = 14 + ((i + 3) % 17)

            game = {
                'game_id': f'nfl_2023_week_{(i % 17) + 1}_{away_team.lower()}_{home_team.lower()}',
                'home_team': home_team,
                'away_team': away_team,
                'season': 2023,
                'week': (i % 17) + 1,
                'game_date': f'2023-09-{10 + i:02d}T13:00:00Z',
                'final_score': {'home': home_score, 'away': away_score},
                'spread_result': f'{home_team} -3.5 {"covered" if home_score - away_score > 3.5 else "did not cover"}',
                'total_result': f'{"over" if home_score + away_score > 45.5 else "under"} 45.5'
            }
            games.append(game)

        return games

    @staticmethod
    def generate_memory_data(expert_id: str, count: int = 20) -> List[Dict[str, Any]]:
        """Generate sample memory data for testing"""
        memories = []
        teams = ['KC', 'DEN', 'BUF', 'MIA', 'DAL', 'NYG']
        memory_types = ['prediction_outcome', 'success_pattern', 'failure_analysis', 'confidence_calibration']

        for i in range(count):
            home_team = teams[i % len(teams)]
            away_team = teams[(i + 1) % len(teams)]

            memory = {
                'memory_id': f'mem_{expert_id}_{i:03d}',
                'expert_id': expert_id,
                'game_id': f'nfl_2023_week_{(i % 17) + 1}_{away_team.lower()}_{home_team.lower()}',
                'memory_type': memory_types[i % len(memory_types)],
                'home_team': home_team,
                'away_team': away_team,
                'contextual_factors': [
                    {'factor': 'home_team', 'value': home_team},
                    {'factor': 'away_team', 'value': away_team},
                    {'factor': 'is_divisional', 'value': i % 3 == 0}
                ],
                'lessons_learned': [f'{home_team} performs well at home', 'Weather was a factor'],
                'emotional_intensity': 0.3 + (i % 7) * 0.1,
                'memory_vividness': 0.4 + (i % 6) * 0.1,
                'created_at': f'2023-{9 + (i // 30):02d}-{(i % 30) + 1:02d}T13:00:00Z',
                'access_count': i % 10,
                'memory_decay': 1.0 - (i * 0.01)
            }
            memories.append(memory)

        return memories

# Mock response generators
class MockResponseGenerator:
    """Generate mock AI and API responses for testing"""

    @staticmethod
    def generate_ai_prediction_response(expert_id: str, confidence_level: str = 'medium') -> Dict[str, Any]:
        """Generate mock AI prediction response"""
        config = TEST_CONFIG.test_expert_configs.get(expert_id, {})

        # Adjust confidence based on expert personality
        if confidence_level == 'low':
            confidence = config.get('expected_confidence_range', (0.4, 0.6))[0]
        elif confidence_level == 'high':
            confidence = config.get('expected_confidence_range', (0.4, 0.6))[1]
        else:
            confidence_range = config.get('expected_confidence_range', (0.5, 0.7))
            confidence = (confidence_range[0] + confidence_range[1]) / 2

        reasoning_patterns = config.get('expected_reasoning_patterns', ['Generic analysis'])

        return {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'game_winner': {
                            'prediction': 'KC',
                            'confidence': confidence,
                            'reasoning': f'{reasoning_patterns[0]} suggests KC will win'
                        },
                        'point_spread': {
                            'prediction': 'KC -3.5',
                            'confidence': confidence - 0.05,
                            'reasoning': f'{reasoning_patterns[0]} supports the spread'
                        },
                        'total_points': {
                            'prediction': 'over 45.5',
                            'confidence': confidence - 0.1,
                            'reasoning': 'Both teams have strong offenses'
                        },
                        'confidence_overall': confidence,
                        'key_factors': reasoning_patterns,
                        'reasoning': f'{config.get("name", "Expert")} analysis based on {reasoning_patterns[0]}'
                    })
                }
            }]
        }

    @staticmethod
    def generate_memory_retrieval_response(expert_id: str, game_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock memory retrieval response"""
        memories = TestDataGenerator.generate_memory_data(expert_id, 5)

        # Add similarity scores and relevance explanations
        for i, memory in enumerate(memories):
            memory['similarity_score'] = 0.9 - (i * 0.1)
            memory['relevance_explanation'] = f"Similar game context: {memory['home_team']} vs {memory['away_team']}"
            memory['bucket_type'] = ['team_specific', 'matchup_specific', 'situational'][i % 3]

        return memories

# Test validation utilities
class TestValidationUtils:
    """Utilities for validating test results"""

    @staticmethod
    def validate_prediction_structure(prediction: Dict[str, Any]) -> List[str]:
        """Validate prediction structure and return list of errors"""
        errors = []

        required_fields = [
            'expert_id', 'confidence_overall', 'reasoning', 'key_factors'
        ]

        for field in required_fields:
            if field not in prediction:
                errors.append(f"Missing required field: {field}")

        # Validate confidence range
        if 'confidence_overall' in prediction:
            confidence = prediction['confidence_overall']
            if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
                errors.append(f"Invalid confidence_overall: {confidence}")

        # Validate reasoning
        if 'reasoning' in prediction:
            reasoning = prediction['reasoning']
            if not isinstance(reasoning, str) or len(reasoning.strip()) == 0:
                errors.append("Reasoning must be a non-empty string")

        return errors

    @staticmethod
    def validate_memory_structure(memory: Dict[str, Any]) -> List[str]:
        """Validate memory structure and return list of errors"""
        errors = []

        required_fields = [
            'memory_id', 'expert_id', 'memory_type'
        ]

        for field in required_fields:
            if field not in memory:
                errors.append(f"Missing required field: {field}")

        # Validate similarity score if present
        if 'similarity_score' in memory:
            score = memory['similarity_score']
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                errors.append(f"Invalid similarity_score: {score}")

        return errors

    @staticmethod
    def validate_expert_consistency(predictions: List[Dict[str, Any]], expert_id: str) -> List[str]:
        """Validate expert personality consistency across predictions"""
        errors = []

        if not predictions:
            return ["No predictions to validate"]

        config = TEST_CONFIG.test_expert_configs.get(expert_id, {})
        expected_range = config.get('expected_confidence_range', (0.0, 1.0))
        expected_patterns = config.get('expected_reasoning_patterns', [])

        # Check confidence consistency
        confidences = [p.get('confidence_overall', 0.5) for p in predictions]
        avg_confidence = sum(confidences) / len(confidences)

        if not expected_range[0] <= avg_confidence <= expected_range[1]:
            errors.append(f"Average confidence {avg_confidence:.2f} outside expected range {expected_range}")

        # Check reasoning pattern consistency
        if expected_patterns:
            for prediction in predictions:
                reasoning = prediction.get('reasoning', '')
                key_factors = prediction.get('key_factors', [])

                pattern_found = False
                for pattern in expected_patterns:
                    if pattern.lower() in reasoning.lower() or any(pattern.lower() in factor.lower() for factor in key_factors):
                        pattern_found = True
                        break

                if not pattern_found:
                    errors.append(f"No expected reasoning patterns found in prediction: {prediction.get('game_id', 'unknown')}")

        return errors

# Export commonly used items
__all__ = [
    'TEST_CONFIG',
    'TestDataGenerator',
    'MockResponseGenerator',
    'TestValidationUtils'
]

# Import json for mock responses
import json
