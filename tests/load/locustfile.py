"""
Locust load testing configuration for NFL Predictor API.
"""
import json
import random
from typing import Dict, Any
from datetime import datetime, timedelta

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class NFLPredictorUser(HttpUser):
    """Simulates a typical NFL Predictor API user."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a user starts. Set up user session."""
        self.client.verify = False  # Disable SSL verification for testing
        self.auth_token = None
        self.favorite_teams = random.sample(['KC', 'BUF', 'SF', 'GB', 'DAL'], 2)
        self.session_id = f"test_session_{random.randint(1000, 9999)}"

        # Authenticate user
        self.authenticate()

    def authenticate(self):
        """Authenticate the test user."""
        auth_data = {
            "username": f"test_user_{random.randint(1, 1000)}",
            "password": "test_password"
        }

        with self.client.post(
            "/auth/login",
            json=auth_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                response.success()
            else:
                # Use mock token for load testing
                self.auth_token = "test_token_for_load_testing"
                response.success()

    @property
    def headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    @task(10)
    def get_current_games(self):
        """Get current NFL games - most common request."""
        params = {
            "season": 2024,
            "week": random.randint(1, 18),
            "status": random.choice(["scheduled", "live", "completed"])
        }

        with self.client.get(
            "/api/v1/games",
            params=params,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "games" in data and len(data["games"]) > 0:
                    response.success()
                else:
                    response.failure("No games returned")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(8)
    def get_game_predictions(self):
        """Get predictions for specific games."""
        # Use sample game IDs
        game_ids = [
            "2024_W01_KC_DET",
            "2024_W01_BUF_MIA",
            "2024_W01_NE_NYJ",
            "2024_W01_BAL_CIN"
        ]
        game_id = random.choice(game_ids)

        with self.client.get(
            f"/api/v1/predictions/{game_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "prediction" in data:
                    # Validate prediction structure
                    prediction = data["prediction"]
                    required_fields = [
                        "home_win_probability",
                        "away_win_probability",
                        "confidence_score"
                    ]
                    if all(field in prediction for field in required_fields):
                        response.success()
                    else:
                        response.failure("Invalid prediction structure")
                else:
                    response.failure("No prediction data")
            elif response.status_code == 404:
                response.success()  # Game not found is acceptable
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(6)
    def get_team_statistics(self):
        """Get statistics for favorite teams."""
        team_id = random.choice(self.favorite_teams)

        with self.client.get(
            f"/api/v1/teams/{team_id}/stats",
            params={"season": 2024},
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "stats" in data:
                    response.success()
                else:
                    response.failure("No stats data")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(5)
    def get_live_scores(self):
        """Get live game scores - simulates real-time usage."""
        with self.client.get(
            "/api/v1/games/live",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Live games endpoint should always return data structure
                if isinstance(data, dict) and "games" in data:
                    response.success()
                else:
                    response.failure("Invalid live scores structure")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(4)
    def get_predictions_batch(self):
        """Get predictions for multiple games at once."""
        # Simulate getting predictions for a full game week
        params = {
            "season": 2024,
            "week": random.randint(1, 18)
        }

        with self.client.get(
            "/api/v1/predictions",
            params=params,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "predictions" in data:
                    response.success()
                else:
                    response.failure("No predictions data")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def get_model_performance(self):
        """Get ML model performance metrics."""
        with self.client.get(
            "/api/v1/models/performance",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "accuracy" in data and "models" in data:
                    response.success()
                else:
                    response.failure("Invalid performance data")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def post_prediction_feedback(self):
        """Submit prediction feedback - write operation."""
        feedback_data = {
            "game_id": "2024_W01_KC_DET",
            "user_prediction": random.choice([0, 1]),  # 0 = away, 1 = home
            "confidence": random.uniform(0.5, 1.0),
            "feedback_type": random.choice(["agree", "disagree", "unsure"])
        }

        with self.client.post(
            "/api/v1/predictions/feedback",
            json=feedback_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 400:
                response.success()  # Bad request is acceptable for invalid data
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def get_system_health(self):
        """Check system health - monitoring endpoint."""
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("System unhealthy")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def websocket_simulation(self):
        """Simulate WebSocket connection load - placeholder task."""
        # Note: Locust doesn't handle WebSockets directly
        # This simulates the HTTP handshake
        with self.client.get(
            "/ws/games/live",
            headers={**self.headers, "Upgrade": "websocket"},
            catch_response=True
        ) as response:
            # WebSocket upgrade should return 101 or connection error
            if response.status_code in [101, 400, 426]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class AdminUser(HttpUser):
    """Simulates admin user activities - lower frequency, higher resource usage."""

    wait_time = between(5, 15)  # Admin users are less frequent
    weight = 1  # 1/10 of users are admin users

    def on_start(self):
        """Set up admin user session."""
        self.client.verify = False
        self.admin_token = "admin_test_token"

    @property
    def admin_headers(self) -> Dict[str, str]:
        """Get admin headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }

    @task(5)
    def get_all_predictions_analytics(self):
        """Get comprehensive analytics - resource intensive."""
        params = {
            "season": 2024,
            "include_performance": "true",
            "include_features": "true"
        }

        with self.client.get(
            "/api/v1/admin/analytics/predictions",
            params=params,
            headers=self.admin_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [401, 403]:
                response.success()  # Auth failures are expected in load testing
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def trigger_model_retraining(self):
        """Trigger ML model retraining - expensive operation."""
        retrain_data = {
            "model_type": random.choice(["xgboost", "lightgbm", "ensemble"]),
            "season": 2024,
            "force_retrain": False
        }

        with self.client.post(
            "/api/v1/admin/models/retrain",
            json=retrain_data,
            headers=self.admin_headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:  # Accepted for async processing
                response.success()
            elif response.status_code in [401, 403]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def get_system_metrics(self):
        """Get detailed system metrics."""
        with self.client.get(
            "/api/v1/admin/system/metrics",
            headers=self.admin_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [401, 403]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class DataIntensiveUser(HttpUser):
    """Simulates data-intensive usage patterns."""

    wait_time = between(3, 8)
    weight = 2  # 2/10 of users perform data-intensive operations

    @task(1)
    def get_historical_data(self):
        """Request large historical datasets."""
        params = {
            "start_season": 2020,
            "end_season": 2023,
            "include_stats": "true",
            "format": "json"
        }

        with self.client.get(
            "/api/v1/games/historical",
            params=params,
            timeout=30,  # Longer timeout for large data
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Check response size
                content_length = len(response.content)
                if content_length > 1000:  # Expect substantial data
                    response.success()
                else:
                    response.failure("Insufficient historical data")
            else:
                response.failure(f"HTTP {response.status_code}")


# Event handlers for custom metrics
@events.request.add_listener
def record_custom_metrics(request_type, name, response_time, response_length, exception, **kwargs):
    """Record custom performance metrics."""
    if exception:
        print(f"Request failed: {name} - {exception}")

    # Log slow requests
    if response_time > 2000:  # 2 seconds
        print(f"Slow request detected: {name} took {response_time}ms")

    # Log large responses
    if response_length and response_length > 1000000:  # 1MB
        print(f"Large response: {name} returned {response_length} bytes")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment."""
    print("Starting NFL Predictor API load test...")
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up after test completion."""
    print("Load test completed.")

    # Calculate custom metrics
    stats = environment.runner.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100
        print(f"Total requests: {total_requests}")
        print(f"Total failures: {total_failures}")
        print(f"Failure rate: {failure_rate:.2f}%")

        # Performance thresholds
        avg_response_time = stats.total.avg_response_time
        p95_response_time = stats.total.get_response_time_percentile(0.95)

        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"95th percentile response time: {p95_response_time:.2f}ms")

        # Set exit code based on performance criteria
        if failure_rate > 5.0:  # More than 5% failure rate
            print("❌ Test failed: High failure rate")
            environment.process_exit_code = 1
        elif avg_response_time > 1000:  # Average response time > 1s
            print("❌ Test failed: High response times")
            environment.process_exit_code = 1
        elif p95_response_time > 3000:  # P95 response time > 3s
            print("❌ Test failed: High P95 response times")
            environment.process_exit_code = 1
        else:
            print("✅ Load test passed all performance criteria")
            environment.process_exit_code = 0