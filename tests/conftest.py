"""
Comprehensive Test Configuration for NFL Predictor API Test Suite.
Enhanced with all fixtures needed for 375+ prediction testing across 15 experts.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import redis
import sqlite3
from typing import Dict, List, Any, Generator, AsyncGenerator
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

# Test environment setup
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6380/0"

# Import application modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.api.app import app
    from src.ml.comprehensive_expert_models import ComprehensiveExpertCouncil
except ImportError:
    # Fallback for tests running without full app
    app = None
    ComprehensiveExpertCouncil = None

# Import mock data generator (create if doesn't exist)
try:
    from fixtures.mock_data import MockDataGenerator, quick_game_data, quick_user_data
except ImportError:
    # Fallback mock data generator
    class MockDataGenerator:
        def __init__(self, seed=42):
            self.seed = seed
            np.random.seed(seed)

        def generate_game_data(self, count):
            return [{"game_id": f"test_{i}", "home_team": "KC", "away_team": "DET"} for i in range(count)]

        def generate_prediction_data(self, games):
            return [{"game_id": game["game_id"], "prediction": "test"} for game in games]

        def generate_odds_data(self, games):
            return [{"game_id": game["game_id"], "spread": -3.5} for game in games]

        def generate_user_data(self, count):
            return [{"user_id": f"user_{i}", "username": f"test_user_{i}"} for i in range(count)]

        def generate_bet_history(self, user_id, count):
            return [{"bet_id": f"bet_{i}", "user_id": user_id} for i in range(count)]

        def generate_system_health_data(self):
            return {"status": "healthy", "uptime": 1000}

        def generate_websocket_test_data(self):
            return [{"type": "test", "data": "mock"}]

    quick_game_data = lambda: {"game_id": "test", "home_team": "KC", "away_team": "DET"}
    quick_user_data = lambda: {"user_id": "test_user", "username": "testuser"}


# Global test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        'database': {
            'url': 'sqlite:///:memory:',
            'echo': False
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 15,  # Use separate DB for tests
            'decode_responses': True
        },
        'websocket': {
            'test_url': 'ws://localhost:8000/ws/test',
            'timeout': 5.0
        },
        'api': {
            'base_url': 'http://localhost:8000',
            'timeout': 10.0
        },
        'auth': {
            'secret_key': 'test_secret_key_for_jwt_12345',
            'algorithm': 'HS256',
            'token_expiry_minutes': 60
        },
        'ml': {
            'test_model_path': '/tmp/test_models/',
            'feature_count': 20,
            'min_accuracy': 0.55
        }
    }


# Mock data fixtures
@pytest.fixture
def mock_data_generator():
    """Mock data generator with fixed seed for reproducible tests"""
    return MockDataGenerator(seed=42)


@pytest.fixture
def sample_games(mock_data_generator):
    """Sample NFL game data"""
    return mock_data_generator.generate_game_data(10)


@pytest.fixture
def sample_predictions(mock_data_generator, sample_games):
    """Sample prediction data"""
    return mock_data_generator.generate_prediction_data(sample_games)


@pytest.fixture
def sample_odds(mock_data_generator, sample_games):
    """Sample odds data"""
    return mock_data_generator.generate_odds_data(sample_games)


@pytest.fixture
def sample_users(mock_data_generator):
    """Sample user data"""
    return mock_data_generator.generate_user_data(5)


@pytest.fixture
def sample_bet_history(mock_data_generator, sample_users):
    """Sample betting history"""
    user_id = sample_users[0]['user_id']
    return mock_data_generator.generate_bet_history(user_id, 20)


@pytest.fixture
def sample_system_health(mock_data_generator):
    """Sample system health data"""
    return mock_data_generator.generate_system_health_data()


# Database fixtures
@pytest.fixture
def temp_database():
    """Temporary SQLite database for testing"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    # Create connection
    conn = sqlite3.connect(temp_db.name)

    # Create test tables
    conn.execute('''
        CREATE TABLE games (
            id TEXT PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            start_time TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE predictions (
            id TEXT PRIMARY KEY,
            game_id TEXT,
            home_win_prob REAL,
            away_win_prob REAL,
            confidence REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            role TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE bets (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            game_id TEXT,
            bet_type TEXT,
            amount REAL,
            odds INTEGER,
            result TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')

    conn.commit()

    yield conn

    # Cleanup
    conn.close()
    os.unlink(temp_db.name)


# Mock Redis fixture
@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    redis_mock = MagicMock()

    # Mock basic Redis operations
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    redis_mock.hget.return_value = None
    redis_mock.hset.return_value = True
    redis_mock.hgetall.return_value = {}
    redis_mock.incr.return_value = 1
    redis_mock.decr.return_value = 0

    # Mock pub/sub
    pubsub_mock = MagicMock()
    pubsub_mock.subscribe.return_value = None
    pubsub_mock.unsubscribe.return_value = None
    pubsub_mock.get_message.return_value = None
    redis_mock.pubsub.return_value = pubsub_mock

    with patch('redis.Redis', return_value=redis_mock):
        yield redis_mock


# WebSocket test fixtures
@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing"""
    websocket_mock = AsyncMock()
    websocket_mock.accept = AsyncMock()
    websocket_mock.send_text = AsyncMock()
    websocket_mock.send_json = AsyncMock()
    websocket_mock.receive_text = AsyncMock()
    websocket_mock.receive_json = AsyncMock()
    websocket_mock.close = AsyncMock()

    return websocket_mock


@pytest.fixture
def websocket_messages(mock_data_generator):
    """Sample WebSocket messages"""
    return mock_data_generator.generate_websocket_test_data()


# ML Model fixtures
@pytest.fixture
def temp_model_directory():
    """Temporary directory for ML models"""
    temp_dir = tempfile.mkdtemp(prefix='nfl_predictor_models_')
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ml_model():
    """Mock ML model for testing"""
    model_mock = MagicMock()

    # Mock methods
    model_mock.fit.return_value = None
    model_mock.predict.return_value = np.array([0, 1, 1, 0])
    model_mock.predict_proba.return_value = np.array([
        [0.6, 0.4], [0.3, 0.7], [0.2, 0.8], [0.9, 0.1]
    ])
    model_mock.score.return_value = 0.65

    # Mock attributes
    model_mock.feature_importances_ = np.random.rand(10)

    return model_mock


@pytest.fixture
def sample_training_data():
    """Sample training data for ML models"""
    np.random.seed(42)
    n_samples = 1000
    n_features = 15

    # Generate realistic NFL features
    X = pd.DataFrame({
        'home_power_rating': np.random.normal(100, 15, n_samples),
        'away_power_rating': np.random.normal(100, 15, n_samples),
        'home_off_rating': np.random.normal(100, 20, n_samples),
        'away_off_rating': np.random.normal(100, 20, n_samples),
        'home_def_rating': np.random.normal(100, 20, n_samples),
        'away_def_rating': np.random.normal(100, 20, n_samples),
        'home_recent_wins': np.random.poisson(3, n_samples),
        'away_recent_wins': np.random.poisson(3, n_samples),
        'week': np.random.randint(1, 18, n_samples),
        'is_divisional': np.random.binomial(1, 0.25, n_samples),
        'home_rest_days': np.random.randint(4, 14, n_samples),
        'away_rest_days': np.random.randint(4, 14, n_samples),
        'weather_score': np.random.uniform(0, 100, n_samples),
        'home_injury_impact': np.random.uniform(-10, 10, n_samples),
        'away_injury_impact': np.random.uniform(-10, 10, n_samples)
    })

    # Generate realistic targets
    home_advantage = (X['home_power_rating'] - X['away_power_rating']) / 100
    recent_form = (X['home_recent_wins'] - X['away_recent_wins']) / 10
    divisional_factor = X['is_divisional'] * 0.1
    random_noise = np.random.normal(0, 0.3, n_samples)

    win_prob = 0.5 + home_advantage * 0.3 + recent_form * 0.2 + divisional_factor + random_noise * 0.1
    y = (win_prob > 0.5).astype(int)

    return X, y


# API test fixtures
@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API testing"""
    return AsyncMock()


@pytest.fixture
def api_test_data():
    """Test data for API endpoints"""
    return {
        'valid_login': {
            'username': 'testuser',
            'password': 'SecurePassword123!'
        },
        'invalid_login': {
            'username': 'baduser',
            'password': 'wrongpassword'
        },
        'valid_prediction_request': {
            'game_id': 'nfl_2024_week_1_chiefs_ravens',
            'bet_type': 'moneyline',
            'amount': 100.0
        },
        'invalid_prediction_request': {
            'bet_type': 'moneyline'
            # Missing required fields
        }
    }


# Authentication fixtures
@pytest.fixture
def valid_jwt_token(test_config):
    """Valid JWT token for testing"""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        'user_id': 'test_user_123',
        'username': 'testuser',
        'role': 'premium',
        'exp': datetime.utcnow() + timedelta(minutes=test_config['auth']['token_expiry_minutes'])
    }

    return jwt.encode(
        payload,
        test_config['auth']['secret_key'],
        algorithm=test_config['auth']['algorithm']
    )


@pytest.fixture
def expired_jwt_token(test_config):
    """Expired JWT token for testing"""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        'user_id': 'test_user_123',
        'username': 'testuser',
        'role': 'premium',
        'exp': datetime.utcnow() - timedelta(minutes=60)  # Expired 1 hour ago
    }

    return jwt.encode(
        payload,
        test_config['auth']['secret_key'],
        algorithm=test_config['auth']['algorithm']
    )


# Performance test fixtures
@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing"""
    generator = MockDataGenerator(seed=42)

    return {
        'games': generator.generate_game_data(100),
        'users': generator.generate_user_data(1000),
        'large_odds_dataset': [],  # Would generate large odds dataset
        'stress_test_messages': generator.generate_websocket_test_data() * 100
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically cleanup temporary files after tests"""
    yield

    # Clean up any temporary files created during tests
    temp_patterns = [
        '/tmp/test_*.pkl',
        '/tmp/nfl_predictor_test_*',
        '/tmp/sample_*.json'
    ]

    import glob
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.unlink(file_path)
            except (OSError, FileNotFoundError):
                pass


# Pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "asyncio: marks tests as asyncio tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


# Test utilities
@pytest.fixture
def assert_within_tolerance():
    """Utility for asserting values within tolerance"""
    def _assert_within_tolerance(actual, expected, tolerance=0.01):
        assert abs(actual - expected) <= tolerance, \
            f"Value {actual} not within {tolerance} of expected {expected}"
    return _assert_within_tolerance


@pytest.fixture
def wait_for_condition():
    """Utility for waiting for a condition to be met"""
    async def _wait_for_condition(condition, timeout=5.0, interval=0.1):
        import asyncio

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if condition():
                return True
            await asyncio.sleep(interval)
        return False

    return _wait_for_condition


# Session-scoped fixtures for expensive setup
@pytest.fixture(scope="session")
def trained_test_model():
    """Pre-trained model for testing (expensive to create)"""
    from sklearn.ensemble import RandomForestClassifier

    # Generate training data once per session
    np.random.seed(42)
    X = np.random.rand(1000, 10)
    y = np.random.randint(0, 2, 1000)

    # Train model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    return model, X, y


# Async fixtures
@pytest.fixture
async def async_mock_database():
    """Async mock database connection"""
    db_mock = AsyncMock()

    db_mock.execute.return_value = AsyncMock()
    db_mock.fetch.return_value = []
    db_mock.fetchrow.return_value = None
    db_mock.fetchval.return_value = None

    yield db_mock

    # Cleanup
    await db_mock.close()


# Context managers for testing
@pytest.fixture
def temp_environment_vars():
    """Temporarily set environment variables for testing"""
    import os

    def _set_env_vars(**kwargs):
        from contextlib import contextmanager

        @contextmanager
        def env_context():
            old_vars = {}
            try:
                # Set new variables
                for key, value in kwargs.items():
                    old_vars[key] = os.environ.get(key)
                    os.environ[key] = str(value)
                yield
            finally:
                # Restore old variables
                for key, old_value in old_vars.items():
                    if old_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = old_value

        return env_context()

    return _set_env_vars