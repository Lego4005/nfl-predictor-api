"""
Resilient Connection and Error Handling System

Advanced error handling, retry logic, and connection management for the real-time
NFL data pipeline. Provides circuit breakers, exponential backoff, and graceful
degradation strategies.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import random

from aiohttp import ClientSession, ClientTimeout, ClientError
from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"                # Minor errors, continue operation
    MEDIUM = "medium"          # Moderate errors, may affect some features
    HIGH = "high"             # Serious errors, significant impact
    CRITICAL = "critical"     # Critical errors, service degradation


class ConnectionState(Enum):
    """Connection state enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"             # Circuit breaker triggered
    HALF_OPEN = "half_open"   # Testing if service recovered


@dataclass
class ErrorInfo:
    """Information about an error"""
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime
    count: int = 1
    last_occurrence: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Retry configuration settings"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: Tuple[Exception, ...] = (ClientConnectionError, ClientResponseError)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: Exception = Exception
    name: str = "default"


class CircuitBreaker:
    """
    Circuit breaker implementation for handling service failures

    Protects against cascading failures by stopping requests to failing services
    and allowing them time to recover.
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker

        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.config.name} entering half-open state")
            else:
                raise Exception(f"Circuit breaker {self.config.name} is open")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        if self.last_failure_time is None:
            return True

        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful function execution"""
        self.failure_count = 0
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker {self.config.name} reset to closed state")

    def _on_failure(self):
        """Handle function execution failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.config.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.config.name} opened due to {self.failure_count} failures")

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state information"""
        return {
            'name': self.config.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'failure_threshold': self.config.failure_threshold,
            'recovery_timeout': self.config.recovery_timeout
        }


class RetryHandler:
    """
    Advanced retry handler with exponential backoff and jitter

    Provides intelligent retry logic for handling transient failures
    with configurable backoff strategies.
    """

    def __init__(self, config: RetryConfig):
        """
        Initialize retry handler

        Args:
            config: Retry configuration
        """
        self.config = config

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        context: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Function arguments
            context: Context description for logging
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        context_str = f" ({context})" if context else ""

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"Retry successful on attempt {attempt + 1}{context_str}")

                return result

            except self.config.retry_on_exceptions as e:
                last_exception = e
                attempt_num = attempt + 1

                if attempt_num < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt_num} failed{context_str}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_attempts} attempts failed{context_str}")

            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable exception{context_str}: {str(e)}")
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"All retry attempts failed{context_str}")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


class ResilientConnection:
    """
    Resilient connection manager with automatic recovery

    Manages connections to external services with automatic retry,
    circuit breaking, and graceful degradation capabilities.
    """

    def __init__(
        self,
        service_name: str,
        base_url: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        timeout_seconds: int = 30
    ):
        """
        Initialize resilient connection

        Args:
            service_name: Name of the service
            base_url: Base URL for the service
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration
            timeout_seconds: Request timeout in seconds
        """
        self.service_name = service_name
        self.base_url = base_url
        self.state = ConnectionState.HEALTHY

        # Configuration
        self.retry_config = retry_config or RetryConfig()
        circuit_config = circuit_config or CircuitBreakerConfig(name=service_name)
        self.circuit_breaker = CircuitBreaker(circuit_config)

        # HTTP session
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=timeout_seconds)

        # Error tracking
        self.error_history: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.last_success_time: Optional[datetime] = None
        self.last_failure_time: Optional[datetime] = None

        # Retry handler
        self.retry_handler = RetryHandler(self.retry_config)

        # Health check
        self.health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the connection"""
        try:
            await self._create_session()
            self.state = ConnectionState.HEALTHY

            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            logger.info(f"Resilient connection to {self.service_name} initialized")

        except Exception as e:
            logger.error(f"Failed to initialize connection to {self.service_name}: {e}")
            self.state = ConnectionState.FAILED
            raise

    async def shutdown(self):
        """Shutdown the connection and cleanup resources"""
        try:
            # Cancel health check task
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Close HTTP session
            if self.session and not self.session.closed:
                await self.session.close()

            logger.info(f"Resilient connection to {self.service_name} shutdown")

        except Exception as e:
            logger.error(f"Error shutting down connection to {self.service_name}: {e}")

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with resilience features

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request parameters

        Returns:
            Response data

        Raises:
            Exception: If request fails after all retries
        """
        if self.state == ConnectionState.FAILED:
            raise Exception(f"Connection to {self.service_name} is in failed state")

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        async def _make_request():
            if not self.session or self.session.closed:
                await self._create_session()

            async with self.session.request(method, url, timeout=self.timeout, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

        try:
            # Execute request with circuit breaker and retry
            result = await self.circuit_breaker.call(
                self.retry_handler.execute_with_retry,
                _make_request,
                context=f"{method} {endpoint}"
            )

            self._record_success()
            return result

        except Exception as e:
            self._record_failure(e, f"{method} {endpoint}")
            raise

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return await self.request("POST", endpoint, **kwargs)

    async def _create_session(self):
        """Create new HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

        self.session = ClientSession(
            timeout=self.timeout,
            headers={
                'User-Agent': 'NFL-Predictor-ResilientClient/1.0'
            }
        )

    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check for {self.service_name}: {e}")

    async def _perform_health_check(self):
        """Perform health check on the service"""
        try:
            # Simple health check - attempt a basic request
            if self.session and not self.session.closed:
                async with self.session.get(
                    self.base_url,
                    timeout=ClientTimeout(total=10)
                ) as response:
                    if response.status < 500:
                        if self.state != ConnectionState.HEALTHY:
                            self.state = ConnectionState.HEALTHY
                            logger.info(f"Health check passed for {self.service_name}")
                    else:
                        self._update_state_on_failure()

        except Exception as e:
            logger.warning(f"Health check failed for {self.service_name}: {e}")
            self._update_state_on_failure()

    def _record_success(self):
        """Record successful operation"""
        self.last_success_time = datetime.utcnow()

        if self.state != ConnectionState.HEALTHY:
            self.state = ConnectionState.HEALTHY
            logger.info(f"Connection to {self.service_name} recovered")

    def _record_failure(self, error: Exception, context: str = ""):
        """Record failed operation"""
        self.last_failure_time = datetime.utcnow()

        # Determine error severity
        severity = self._classify_error(error)

        # Record error
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            timestamp=datetime.utcnow(),
            context={'operation': context}
        )

        self.error_history.append(error_info)

        # Update error counts
        error_key = f"{type(error).__name__}:{str(error)[:100]}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Limit error history size
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-50:]

        # Update connection state
        self._update_state_on_failure()

        logger.error(f"Operation failed for {self.service_name} ({context}): {error}")

    def _classify_error(self, error: Exception) -> ErrorSeverity:
        """Classify error severity"""
        if isinstance(error, ClientConnectionError):
            return ErrorSeverity.HIGH
        elif isinstance(error, ClientResponseError):
            if error.status >= 500:
                return ErrorSeverity.HIGH
            elif error.status >= 400:
                return ErrorSeverity.MEDIUM
            else:
                return ErrorSeverity.LOW
        elif isinstance(error, asyncio.TimeoutError):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _update_state_on_failure(self):
        """Update connection state based on failure"""
        if self.state == ConnectionState.HEALTHY:
            self.state = ConnectionState.DEGRADED
        elif self.state == ConnectionState.DEGRADED:
            # Check if we should move to failed state
            recent_failures = sum(
                1 for error in self.error_history[-10:]
                if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            )

            if recent_failures >= 5:
                self.state = ConnectionState.FAILED
                logger.error(f"Connection to {self.service_name} marked as failed")

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status and metrics"""
        recent_errors = self.error_history[-10:] if self.error_history else []

        return {
            'service_name': self.service_name,
            'state': self.state.value,
            'base_url': self.base_url,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'circuit_breaker': self.circuit_breaker.get_state(),
            'error_summary': {
                'total_errors': len(self.error_history),
                'recent_errors': len(recent_errors),
                'top_errors': sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'configuration': {
                'max_retries': self.retry_config.max_attempts,
                'timeout_seconds': self.timeout.total,
                'health_check_interval': self.health_check_interval
            }
        }


class ConnectionManager:
    """
    Manages multiple resilient connections

    Provides centralized management of connections to multiple services
    with coordinated health monitoring and fallback strategies.
    """

    def __init__(self):
        """Initialize connection manager"""
        self.connections: Dict[str, ResilientConnection] = {}
        self._monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize connection manager"""
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Connection manager initialized")

    async def shutdown(self):
        """Shutdown connection manager"""
        try:
            # Cancel monitoring task
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            # Shutdown all connections
            for connection in self.connections.values():
                await connection.shutdown()

            logger.info("Connection manager shutdown complete")

        except Exception as e:
            logger.error(f"Error shutting down connection manager: {e}")

    def add_connection(
        self,
        name: str,
        base_url: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        timeout_seconds: int = 30
    ) -> ResilientConnection:
        """Add a new resilient connection"""
        connection = ResilientConnection(
            service_name=name,
            base_url=base_url,
            retry_config=retry_config,
            circuit_config=circuit_config,
            timeout_seconds=timeout_seconds
        )

        self.connections[name] = connection
        return connection

    async def initialize_connection(self, name: str):
        """Initialize a specific connection"""
        if name in self.connections:
            await self.connections[name].initialize()
        else:
            raise ValueError(f"Connection {name} not found")

    async def initialize_all_connections(self):
        """Initialize all connections"""
        for name, connection in self.connections.items():
            try:
                await connection.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize connection {name}: {e}")

    def get_connection(self, name: str) -> ResilientConnection:
        """Get connection by name"""
        if name not in self.connections:
            raise ValueError(f"Connection {name} not found")
        return self.connections[name]

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(300)  # Monitor every 5 minutes
                await self._check_all_connections()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")

    async def _check_all_connections(self):
        """Check health of all connections"""
        healthy_count = 0
        total_count = len(self.connections)

        for name, connection in self.connections.items():
            if connection.state == ConnectionState.HEALTHY:
                healthy_count += 1

        health_percentage = (healthy_count / total_count * 100) if total_count > 0 else 100

        if health_percentage < 50:
            logger.warning(f"Connection health degraded: {healthy_count}/{total_count} connections healthy")

        logger.info(f"Connection health check: {healthy_count}/{total_count} connections healthy ({health_percentage:.1f}%)")

    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall connection status"""
        connection_statuses = {}
        state_counts = {state.value: 0 for state in ConnectionState}

        for name, connection in self.connections.items():
            info = connection.get_connection_info()
            connection_statuses[name] = info
            state_counts[info['state']] += 1

        total_connections = len(self.connections)
        health_percentage = (state_counts['healthy'] / total_connections * 100) if total_connections > 0 else 100

        return {
            'total_connections': total_connections,
            'state_distribution': state_counts,
            'health_percentage': health_percentage,
            'connections': connection_statuses
        }


# Global connection manager instance
connection_manager = ConnectionManager()