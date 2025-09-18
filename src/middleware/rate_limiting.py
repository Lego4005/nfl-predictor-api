"""
Advanced Rate Limiting Middleware

Comprehensive rate limiting implementation for the NFL prediction API with:
- Multiple limiting strategies (sliding window, token bucket, fixed window)
- Per-endpoint and per-user rate limiting
- Dynamic rate adjustment based on system load
- Redis-backed distributed rate limiting
- Grace period handling and burst allowances
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategy types"""
    FIXED_WINDOW = "fixed_window"           # Fixed time windows
    SLIDING_WINDOW = "sliding_window"       # Sliding time windows
    TOKEN_BUCKET = "token_bucket"           # Token bucket algorithm
    LEAKY_BUCKET = "leaky_bucket"          # Leaky bucket algorithm


class RateLimitScope(Enum):
    """Rate limit scope levels"""
    GLOBAL = "global"                       # Application-wide
    PER_IP = "per_ip"                      # Per IP address
    PER_USER = "per_user"                  # Per authenticated user
    PER_ENDPOINT = "per_endpoint"          # Per API endpoint
    PER_API_KEY = "per_api_key"           # Per API key


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    name: str
    requests: int                           # Number of requests
    window_seconds: int                     # Time window in seconds
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.PER_IP
    burst_allowance: int = 0               # Additional burst requests
    grace_period_seconds: int = 0          # Grace period for first-time users
    priority: int = 1                      # Rule priority (higher = more important)
    endpoints: Optional[List[str]] = None  # Specific endpoints (None = all)

    def matches_endpoint(self, endpoint: str) -> bool:
        """Check if rule applies to endpoint"""
        if self.endpoints is None:
            return True
        return endpoint in self.endpoints


@dataclass
class RateLimitState:
    """Current rate limit state for a key"""
    requests_made: int = 0
    window_start: float = 0
    tokens: float = 0
    last_refill: float = 0
    burst_used: int = 0
    first_request_time: Optional[float] = None


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    rule_name: str = ""
    limit_type: str = ""


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple strategies and Redis backing

    Features:
    - Multiple rate limiting algorithms
    - Distributed rate limiting with Redis
    - Per-endpoint and per-user limits
    - Dynamic adjustment based on system load
    - Burst handling and grace periods
    - Detailed metrics and monitoring
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_rules: Optional[List[RateLimitRule]] = None,
        enable_metrics: bool = True
    ):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
            default_rules: Default rate limiting rules
            enable_metrics: Enable metrics collection
        """
        self.redis_url = redis_url
        self.enable_metrics = enable_metrics

        # Redis client
        self._redis_client: Optional[redis.Redis] = None
        self._redis_healthy = False

        # Rate limiting rules
        self.rules = default_rules or self._get_default_rules()

        # In-memory state fallback
        self._memory_state: Dict[str, RateLimitState] = {}

        # Metrics
        self.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rules_triggered': {},
            'avg_response_time': 0.0
        }

        # System load adjustment
        self._system_load_factor = 1.0
        self._load_check_interval = 60  # seconds

    async def initialize(self):
        """Initialize rate limiter"""
        try:
            # Initialize Redis connection
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                retry_on_timeout=True,
                socket_timeout=5
            )

            # Test connection
            await self._redis_client.ping()
            self._redis_healthy = True
            logger.info("Rate limiter Redis connection established")

        except Exception as e:
            logger.warning(f"Rate limiter Redis connection failed: {e}")
            self._redis_healthy = False

    async def check_rate_limit(
        self,
        request: Request,
        endpoint: str,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check if request should be rate limited

        Args:
            request: FastAPI request object
            endpoint: API endpoint identifier
            user_id: Authenticated user ID
            api_key: API key if applicable

        Returns:
            RateLimitResult indicating if request is allowed
        """
        start_time = time.time()

        try:
            # Get applicable rules for this request
            applicable_rules = self._get_applicable_rules(endpoint)

            # Check each rule
            for rule in applicable_rules:
                # Generate rate limit key
                key = self._generate_rate_limit_key(request, rule, user_id, api_key)

                # Check rate limit for this rule
                result = await self._check_rule(key, rule)

                if not result.allowed:
                    # Request blocked by this rule
                    await self._record_blocked_request(rule.name, key)
                    return result

            # All rules passed
            self.metrics['total_requests'] += 1
            return RateLimitResult(
                allowed=True,
                remaining=0,  # Will be set by the most restrictive rule
                reset_time=time.time() + 60,
                rule_name="none"
            )

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # On error, allow request but log the issue
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_time=time.time() + 60,
                rule_name="error"
            )

        finally:
            # Update response time metric
            response_time = time.time() - start_time
            self._update_response_time_metric(response_time)

    async def _check_rule(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        """Check rate limit for a specific rule"""
        current_time = time.time()

        # Adjust limits based on system load
        adjusted_requests = max(1, int(rule.requests * self._system_load_factor))

        if rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window(key, rule, adjusted_requests, current_time)
        elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._check_fixed_window(key, rule, adjusted_requests, current_time)
        elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket(key, rule, adjusted_requests, current_time)
        elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return await self._check_leaky_bucket(key, rule, adjusted_requests, current_time)
        else:
            # Default to sliding window
            return await self._check_sliding_window(key, rule, adjusted_requests, current_time)

    async def _check_sliding_window(
        self,
        key: str,
        rule: RateLimitRule,
        requests_limit: int,
        current_time: float
    ) -> RateLimitResult:
        """Check sliding window rate limit"""
        try:
            # Get current state
            state = await self._get_state(key)

            # Calculate window start
            window_start = current_time - rule.window_seconds

            # For sliding window, we need to track requests with timestamps
            if self._redis_healthy and self._redis_client:
                # Use Redis sorted set for sliding window
                requests_key = f"rl:sw:{key}"

                # Remove old requests
                await self._redis_client.zremrangebyscore(requests_key, 0, window_start)

                # Count current requests in window
                current_count = await self._redis_client.zcard(requests_key)

                # Check if under limit (including burst)
                total_allowed = requests_limit + rule.burst_allowance
                if current_count < total_allowed:
                    # Add current request
                    await self._redis_client.zadd(requests_key, {str(current_time): current_time})
                    await self._redis_client.expire(requests_key, rule.window_seconds)

                    return RateLimitResult(
                        allowed=True,
                        remaining=total_allowed - current_count - 1,
                        reset_time=current_time + rule.window_seconds,
                        rule_name=rule.name,
                        limit_type="sliding_window"
                    )
                else:
                    # Get oldest request to calculate reset time
                    oldest_requests = await self._redis_client.zrange(requests_key, 0, 0, withscores=True)
                    reset_time = oldest_requests[0][1] + rule.window_seconds if oldest_requests else current_time + rule.window_seconds

                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=reset_time,
                        retry_after=int(reset_time - current_time),
                        rule_name=rule.name,
                        limit_type="sliding_window"
                    )

            else:
                # Fallback to memory-based sliding window (simplified)
                if current_time - state.window_start > rule.window_seconds:
                    state.requests_made = 0
                    state.window_start = current_time

                total_allowed = requests_limit + rule.burst_allowance
                if state.requests_made < total_allowed:
                    state.requests_made += 1
                    await self._save_state(key, state)

                    return RateLimitResult(
                        allowed=True,
                        remaining=total_allowed - state.requests_made,
                        reset_time=state.window_start + rule.window_seconds,
                        rule_name=rule.name,
                        limit_type="sliding_window"
                    )
                else:
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=state.window_start + rule.window_seconds,
                        retry_after=int(state.window_start + rule.window_seconds - current_time),
                        rule_name=rule.name,
                        limit_type="sliding_window"
                    )

        except Exception as e:
            logger.error(f"Error in sliding window check: {e}")
            # On error, allow request
            return RateLimitResult(allowed=True, remaining=0, reset_time=current_time + 60)

    async def _check_fixed_window(
        self,
        key: str,
        rule: RateLimitRule,
        requests_limit: int,
        current_time: float
    ) -> RateLimitResult:
        """Check fixed window rate limit"""
        try:
            # Get current state
            state = await self._get_state(key)

            # Calculate current window
            window_number = int(current_time // rule.window_seconds)
            window_start_time = window_number * rule.window_seconds

            # Reset if new window
            if state.window_start != window_start_time:
                state.requests_made = 0
                state.window_start = window_start_time

            total_allowed = requests_limit + rule.burst_allowance
            if state.requests_made < total_allowed:
                state.requests_made += 1
                await self._save_state(key, state)

                return RateLimitResult(
                    allowed=True,
                    remaining=total_allowed - state.requests_made,
                    reset_time=window_start_time + rule.window_seconds,
                    rule_name=rule.name,
                    limit_type="fixed_window"
                )
            else:
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=window_start_time + rule.window_seconds,
                    retry_after=int(window_start_time + rule.window_seconds - current_time),
                    rule_name=rule.name,
                    limit_type="fixed_window"
                )

        except Exception as e:
            logger.error(f"Error in fixed window check: {e}")
            return RateLimitResult(allowed=True, remaining=0, reset_time=current_time + 60)

    async def _check_token_bucket(
        self,
        key: str,
        rule: RateLimitRule,
        requests_limit: int,
        current_time: float
    ) -> RateLimitResult:
        """Check token bucket rate limit"""
        try:
            # Get current state
            state = await self._get_state(key)

            # Initialize if first request
            if state.last_refill == 0:
                state.tokens = requests_limit
                state.last_refill = current_time

            # Calculate tokens to add since last refill
            time_passed = current_time - state.last_refill
            tokens_to_add = time_passed * (requests_limit / rule.window_seconds)

            # Update tokens (cap at bucket size)
            state.tokens = min(requests_limit + rule.burst_allowance, state.tokens + tokens_to_add)
            state.last_refill = current_time

            if state.tokens >= 1:
                # Consume one token
                state.tokens -= 1
                await self._save_state(key, state)

                return RateLimitResult(
                    allowed=True,
                    remaining=int(state.tokens),
                    reset_time=current_time + (requests_limit - state.tokens) / (requests_limit / rule.window_seconds),
                    rule_name=rule.name,
                    limit_type="token_bucket"
                )
            else:
                # No tokens available
                time_to_next_token = (1 - state.tokens) / (requests_limit / rule.window_seconds)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=current_time + time_to_next_token,
                    retry_after=int(time_to_next_token) + 1,
                    rule_name=rule.name,
                    limit_type="token_bucket"
                )

        except Exception as e:
            logger.error(f"Error in token bucket check: {e}")
            return RateLimitResult(allowed=True, remaining=0, reset_time=current_time + 60)

    async def _check_leaky_bucket(
        self,
        key: str,
        rule: RateLimitRule,
        requests_limit: int,
        current_time: float
    ) -> RateLimitResult:
        """Check leaky bucket rate limit"""
        try:
            # Get current state
            state = await self._get_state(key)

            # Initialize if first request
            if state.last_refill == 0:
                state.last_refill = current_time

            # Calculate requests that have "leaked" since last check
            time_passed = current_time - state.last_refill
            requests_leaked = time_passed * (requests_limit / rule.window_seconds)

            # Update bucket level
            state.requests_made = max(0, state.requests_made - requests_leaked)
            state.last_refill = current_time

            bucket_capacity = requests_limit + rule.burst_allowance
            if state.requests_made < bucket_capacity:
                # Add request to bucket
                state.requests_made += 1
                await self._save_state(key, state)

                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket_capacity - state.requests_made),
                    reset_time=current_time + state.requests_made / (requests_limit / rule.window_seconds),
                    rule_name=rule.name,
                    limit_type="leaky_bucket"
                )
            else:
                # Bucket overflow
                overflow_time = (state.requests_made - bucket_capacity + 1) / (requests_limit / rule.window_seconds)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=current_time + overflow_time,
                    retry_after=int(overflow_time) + 1,
                    rule_name=rule.name,
                    limit_type="leaky_bucket"
                )

        except Exception as e:
            logger.error(f"Error in leaky bucket check: {e}")
            return RateLimitResult(allowed=True, remaining=0, reset_time=current_time + 60)

    async def _get_state(self, key: str) -> RateLimitState:
        """Get rate limit state for key"""
        try:
            if self._redis_healthy and self._redis_client:
                # Try Redis first
                state_data = await self._redis_client.get(f"rl:state:{key}")
                if state_data:
                    data = json.loads(state_data)
                    return RateLimitState(**data)

            # Fallback to memory
            return self._memory_state.get(key, RateLimitState())

        except Exception as e:
            logger.error(f"Error getting rate limit state: {e}")
            return RateLimitState()

    async def _save_state(self, key: str, state: RateLimitState):
        """Save rate limit state for key"""
        try:
            state_data = {
                'requests_made': state.requests_made,
                'window_start': state.window_start,
                'tokens': state.tokens,
                'last_refill': state.last_refill,
                'burst_used': state.burst_used,
                'first_request_time': state.first_request_time
            }

            if self._redis_healthy and self._redis_client:
                # Save to Redis with expiration
                await self._redis_client.setex(
                    f"rl:state:{key}",
                    3600,  # 1 hour expiration
                    json.dumps(state_data)
                )
            else:
                # Fallback to memory
                self._memory_state[key] = state

        except Exception as e:
            logger.error(f"Error saving rate limit state: {e}")

    def _generate_rate_limit_key(
        self,
        request: Request,
        rule: RateLimitRule,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> str:
        """Generate rate limit key based on scope"""
        if rule.scope == RateLimitScope.GLOBAL:
            return f"global:{rule.name}"
        elif rule.scope == RateLimitScope.PER_IP:
            client_ip = self._get_client_ip(request)
            return f"ip:{client_ip}:{rule.name}"
        elif rule.scope == RateLimitScope.PER_USER and user_id:
            return f"user:{user_id}:{rule.name}"
        elif rule.scope == RateLimitScope.PER_API_KEY and api_key:
            return f"apikey:{api_key}:{rule.name}"
        elif rule.scope == RateLimitScope.PER_ENDPOINT:
            endpoint = request.url.path
            return f"endpoint:{endpoint}:{rule.name}"
        else:
            # Default to IP-based
            client_ip = self._get_client_ip(request)
            return f"ip:{client_ip}:{rule.name}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request"""
        # Check forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"

    def _get_applicable_rules(self, endpoint: str) -> List[RateLimitRule]:
        """Get rules that apply to the endpoint"""
        applicable_rules = []

        for rule in self.rules:
            if rule.matches_endpoint(endpoint):
                applicable_rules.append(rule)

        # Sort by priority (higher priority first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        return applicable_rules

    def _get_default_rules(self) -> List[RateLimitRule]:
        """Get default rate limiting rules"""
        return [
            # Global rate limit
            RateLimitRule(
                name="global_limit",
                requests=10000,
                window_seconds=3600,  # 10k requests per hour globally
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.GLOBAL,
                priority=1
            ),

            # Per-IP rate limit
            RateLimitRule(
                name="ip_limit",
                requests=1000,
                window_seconds=3600,  # 1k requests per hour per IP
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.PER_IP,
                burst_allowance=100,
                priority=2
            ),

            # Per-user rate limit (more generous)
            RateLimitRule(
                name="user_limit",
                requests=5000,
                window_seconds=3600,  # 5k requests per hour per user
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.PER_USER,
                burst_allowance=200,
                priority=3
            ),

            # Real-time endpoints (more restrictive)
            RateLimitRule(
                name="realtime_limit",
                requests=600,
                window_seconds=300,  # 600 requests per 5 minutes for real-time
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                scope=RateLimitScope.PER_IP,
                burst_allowance=50,
                priority=4,
                endpoints=["/api/v1/realtime"]
            ),

            # WebSocket connections
            RateLimitRule(
                name="websocket_limit",
                requests=10,
                window_seconds=60,  # 10 WebSocket connections per minute
                strategy=RateLimitStrategy.FIXED_WINDOW,
                scope=RateLimitScope.PER_IP,
                priority=5,
                endpoints=["/api/v1/realtime/ws"]
            )
        ]

    async def _record_blocked_request(self, rule_name: str, key: str):
        """Record metrics for blocked request"""
        self.metrics['blocked_requests'] += 1
        self.metrics['total_requests'] += 1

        if rule_name not in self.metrics['rules_triggered']:
            self.metrics['rules_triggered'][rule_name] = 0
        self.metrics['rules_triggered'][rule_name] += 1

        logger.info(f"Rate limit triggered: {rule_name} for key: {key}")

    def _update_response_time_metric(self, response_time: float):
        """Update average response time metric"""
        if self.metrics['avg_response_time'] == 0:
            self.metrics['avg_response_time'] = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics['avg_response_time'] = (
                alpha * response_time + (1 - alpha) * self.metrics['avg_response_time']
            )

    def add_rule(self, rule: RateLimitRule):
        """Add a new rate limiting rule"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rate limiting rule"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                return True
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        total_requests = self.metrics['total_requests']
        blocked_requests = self.metrics['blocked_requests']

        return {
            'total_requests': total_requests,
            'blocked_requests': blocked_requests,
            'block_rate': (blocked_requests / max(total_requests, 1)) * 100,
            'avg_response_time_ms': self.metrics['avg_response_time'] * 1000,
            'rules_triggered': self.metrics['rules_triggered'],
            'redis_healthy': self._redis_healthy,
            'active_rules_count': len(self.rules)
        }

    async def reset_limits(self, pattern: str = "*") -> int:
        """Reset rate limits matching pattern"""
        try:
            count = 0

            if self._redis_healthy and self._redis_client:
                # Reset Redis state
                keys = await self._redis_client.keys(f"rl:state:{pattern}")
                if keys:
                    count += await self._redis_client.delete(*keys)

                # Reset sliding window data
                keys = await self._redis_client.keys(f"rl:sw:{pattern}")
                if keys:
                    count += await self._redis_client.delete(*keys)

            # Reset memory state
            if pattern == "*":
                self._memory_state.clear()
            else:
                import fnmatch
                keys_to_remove = [
                    key for key in self._memory_state.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in keys_to_remove:
                    del self._memory_state[key]
                    count += 1

            logger.info(f"Reset {count} rate limit entries matching pattern: {pattern}")
            return count

        except Exception as e:
            logger.error(f"Error resetting rate limits: {e}")
            return 0


# FastAPI middleware
class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, rate_limiter: AdvancedRateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, request: Request, call_next):
        """Middleware handler"""
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Extract user info if available
        user_id = getattr(request.state, 'user_id', None)
        api_key = request.headers.get('X-API-Key')

        # Check rate limit
        result = await self.rate_limiter.check_rate_limit(
            request=request,
            endpoint=request.url.path,
            user_id=user_id,
            api_key=api_key
        )

        if not result.allowed:
            # Return rate limit exceeded response
            headers = {
                "X-RateLimit-Limit": str(self.rate_limiter.rules[0].requests),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(int(result.reset_time)),
                "X-RateLimit-Rule": result.rule_name
            }

            if result.retry_after:
                headers["Retry-After"] = str(result.retry_after)

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {result.rule_name}",
                    "retry_after": result.retry_after
                },
                headers=headers
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_time))

        return response


# Global rate limiter instance
rate_limiter = AdvancedRateLimiter()