#!/usr/bin/env python3
"""
API Rate Limiting and Retry Logic System

Implements intelligent rate limiting, retry logic with exponential backoff,
and API usage optimization for AI model calls.

Requirements: 10.1, 10.2, 10.3, 10.6
"""

import logging
import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_capacity: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF


@dataclass
class APICallResult:
    """Result of an API call with retry information"""
    success: bool
    response: Any = None
    error: Optional[Exception] = None
    attempts: int = 1
    total_delay_seconds: float = 0.0
    rate_limited: bool = False
    final_attempt: bool = True


class TokenBucket:
    """Token bucket implementation for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if not enough tokens available
        """
        with self._lock:
            now = time.time()

            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time until tokens are available"""
        with self._lock:
            if self.tokens >= tokens:
                return 0.0

            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate


class SlidingWindowRateLimiter:
    """Sliding window rate limiter"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = threading.Lock()

    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        with self._lock:
            now = time.time()

            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()

            return len(self.requests) < self.max_requests

    def record_request(self):
        """Record a new request"""
        with self._lock:
            self.requests.append(time.time())

    def get_wait_time(self) -> float:
        """Get estimated wait time until request can proceed"""
        with self._lock:
            if self.can_proceed():
                return 0.0

            # Wait until the oldest request falls outside the window
            if self.requests:
                oldest_request = self.requests[0]
                return max(0.0, oldest_request + self.window_seconds - time.time())
            return 0.0


class APIRateLimiter:
    """
    Comprehensive API rate limiter with multiple strategies and per-model limits.
    """

    def __init__(self):
        self.model_configs: Dict[str, RateLimitConfig] = {}
        self.model_limiters: Dict[str, Any] = {}
        self.global_limiter: Optional[Any] = None
        self._lock = threading.Lock()

        # Default configurations for different model providers
        self.default_configs = {
            'openai': RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_capacity=10
            ),
            'anthropic': RateLimitConfig(
                requests_per_minute=50,
                requests_per_hour=800,
                burst_capacity=8
            ),
            'google': RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=2000,
                burst_capacity=15
            ),
            'x-ai': RateLimitConfig(
                requests_per_minute=40,
                requests_per_hour=600,
                burst_capacity=6
            ),
            'deepseek': RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=400,
                burst_capacity=5
            )
        }

        # Initialize default limiters
        self._initialize_default_limiters()

        logger.info("✅ API Rate Limiter initialized")

    def _initialize_default_limiters(self):
        """Initialize rate limiters for default model providers"""
        for provider, config in self.default_configs.items():
            self.configure_model_limits(provider, config)

    def configure_model_limits(self, model_or_provider: str, config: RateLimitConfig):
        """
        Configure rate limits for a specific model or provider.

        Args:
            model_or_provider: Model name or provider name
            config: Rate limiting configuration
        """
        with self._lock:
            self.model_configs[model_or_provider] = config

            if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                # Create token bucket with per-minute rate
                refill_rate = config.requests_per_minute / 60.0  # tokens per second
                self.model_limiters[model_or_provider] = TokenBucket(
                    capacity=config.burst_capacity,
                    refill_rate=refill_rate
                )
            elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                self.model_limiters[model_or_provider] = SlidingWindowRateLimiter(
                    max_requests=config.requests_per_minute,
                    window_seconds=60
                )

            logger.info(f"✅ Configured rate limits for {model_or_provider}: {config.requests_per_minute}/min")

    def _get_provider_from_model(self, model: str) -> str:
        """Extract provider name from model string"""
        if '/' in model:
            return model.split('/')[0]
        return model

    def can_make_request(self, model: str) -> bool:
        """
        Check if a request can be made for the given model.

        Args:
            model: Model name (e.g., 'openai/gpt-4', 'anthropic/claude-3')

        Returns:
            True if request can proceed, False if rate limited
        """
        provider = self._get_provider_from_model(model)

        # Check model-specific limiter first
        if model in self.model_limiters:
            limiter = self.model_limiters[model]
        elif provider in self.model_limiters:
            limiter = self.model_limiters[provider]
        else:
            # No specific limits configured, allow request
            return True

        if isinstance(limiter, TokenBucket):
            return limiter.consume(1)
        elif isinstance(limiter, SlidingWindowRateLimiter):
            can_proceed = limiter.can_proceed()
            if can_proceed:
                limiter.record_request()
            return can_proceed

        return True

    def get_wait_time(self, model: str) -> float:
        """
        Get estimated wait time before request can be made.

        Args:
            model: Model name

        Returns:
            Wait time in seconds
        """
        provider = self._get_provider_from_model(model)

        # Check model-specific limiter first
        if model in self.model_limiters:
            limiter = self.model_limiters[model]
        elif provider in self.model_limiters:
            limiter = self.model_limiters[provider]
        else:
            return 0.0

        if hasattr(limiter, 'get_wait_time'):
            return limiter.get_wait_time()

        return 0.0

    async def wait_for_capacity(self, model: str, timeout_seconds: float = 300.0):
        """
        Wait until capacity is available for the model.

        Args:
            model: Model name
            timeout_seconds: Maximum time to wait

        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if self.can_make_request(model):
                return

            wait_time = min(self.get_wait_time(model), 5.0)  # Max 5 second waits
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

        raise asyncio.TimeoutError(f"Rate limit timeout for model {model}")


class RetryHandler:
    """
    Handles retry logic with various backoff strategies.
    """

    def __init__(self, config: RetryConfig):
        self.config = config

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt number.

        Args:
            attempt: Attempt number (1-based)

        Returns:
            Delay in seconds
        """
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay_seconds * (self.config.backoff_multiplier ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay_seconds * attempt
        else:  # FIXED_DELAY
            delay = self.config.base_delay_seconds

        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay_seconds)

        # Add jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.0, delay)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """
        Determine if operation should be retried.

        Args:
            attempt: Current attempt number (1-based)
            error: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.config.max_retries:
            return False

        # Check for retryable errors
        error_str = str(error).lower()

        # Rate limiting errors
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
            return True

        # Temporary network errors
        if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', '502', '503', '504']):
            return True

        # Server errors
        if any(keyword in error_str for keyword in ['500', 'internal server error', 'service unavailable']):
            return True

        return False


class APICallManager:
    """
    Manages API calls with rate limiting and retry logic.
    """

    def __init__(
        self,
        rate_limiter: Optional[APIRateLimiter] = None,
        default_retry_config: Optional[RetryConfig] = None
    ):
        self.rate_limiter = rate_limiter or APIRateLimiter()
        self.default_retry_config = default_retry_config or RetryConfig()

        # Statistics tracking
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rate_limited_calls': 0,
            'retried_calls': 0,
            'total_retry_attempts': 0
        }

        logger.info("✅ API Call Manager initialized")

    async def make_api_call(
        self,
        api_function: Callable[..., Awaitable[Any]],
        model: str,
        *args,
        retry_config: Optional[RetryConfig] = None,
        **kwargs
    ) -> APICallResult:
        """
        Make an API call with rate limiting and retry logic.

        Args:
            api_function: Async function to call
            model: Model name for rate limiting
            *args: Arguments to pass to api_function
            retry_config: Custom retry configuration
            **kwargs: Keyword arguments to pass to api_function

        Returns:
            APICallResult with response and metadata
        """
        retry_config = retry_config or self.default_retry_config
        retry_handler = RetryHandler(retry_config)

        self.stats['total_calls'] += 1

        total_delay = 0.0
        last_error = None

        for attempt in range(1, retry_config.max_retries + 1):
            try:
                # Check rate limits
                if not self.rate_limiter.can_make_request(model):
                    self.stats['rate_limited_calls'] += 1
                    wait_time = self.rate_limiter.get_wait_time(model)

                    if wait_time > 0:
                        logger.info(f"⏳ Rate limited for {model}, waiting {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        total_delay += wait_time

                # Make the API call
                response = await api_function(*args, **kwargs)

                # Success
                self.stats['successful_calls'] += 1
                if attempt > 1:
                    self.stats['retried_calls'] += 1
                    self.stats['total_retry_attempts'] += attempt - 1

                return APICallResult(
                    success=True,
                    response=response,
                    attempts=attempt,
                    total_delay_seconds=total_delay,
                    rate_limited=total_delay > 0,
                    final_attempt=True
                )

            except Exception as error:
                last_error = error

                # Check if we should retry
                if attempt < retry_config.max_retries and retry_handler.should_retry(attempt, error):
                    delay = retry_handler.calculate_delay(attempt)
                    total_delay += delay

                    logger.warning(f"⚠️ API call failed (attempt {attempt}/{retry_config.max_retries}), "
                                 f"retrying in {delay:.1f}s: {str(error)[:100]}")

                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final failure
                    self.stats['failed_calls'] += 1
                    if attempt > 1:
                        self.stats['total_retry_attempts'] += attempt - 1

                    return APICallResult(
                        success=False,
                        error=last_error,
                        attempts=attempt,
                        total_delay_seconds=total_delay,
                        rate_limited=total_delay > 0,
                        final_attempt=True
                    )

        # Should not reach here, but handle edge case
        self.stats['failed_calls'] += 1
        return APICallResult(
            success=False,
            error=last_error or Exception("Unknown error"),
            attempts=retry_config.max_retries,
            total_delay_seconds=total_delay,
            final_attempt=True
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get API call statistics"""
        total_calls = self.stats['total_calls']
        success_rate = self.stats['successful_calls'] / total_calls if total_calls > 0 else 0
        retry_rate = self.stats['retried_calls'] / total_calls if total_calls > 0 else 0

        return {
            **self.stats,
            'success_rate': success_rate,
            'retry_rate': retry_rate,
            'avg_retries_per_call': self.stats['total_retry_attempts'] / total_calls if total_calls > 0 else 0
        }


# Global instances
_global_rate_limiter: Optional[APIRateLimiter] = None
_global_call_manager: Optional[APICallManager] = None


def get_api_rate_limiter() -> APIRateLimiter:
    """Get the global API rate limiter instance"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = APIRateLimiter()
    return _global_rate_limiter


def get_api_call_manager() -> APICallManager:
    """Get the global API call manager instance"""
    global _global_call_manager
    if _global_call_manager is None:
        _global_call_manager = APICallManager()
    return _global_call_manager
