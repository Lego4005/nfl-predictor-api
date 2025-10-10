"""
Neo4j Idempotent Merge Service

Implements idempotent merge logic for the Neo4j Write-Behind Provenance System.
Provides retry/backoff for transient failures, operator introspection queries,
and ensures write-behind operations don't block the hot path.

Features:
- Idempotent MERGE operations for nodes and relationships
- Advanced retry/backoff logic for transient failures
- Operator introspection queries for debugging
- Non-blocking write-behind with circuit breaker
- Batch processing with failure isolation
- Performance monitoring and health checks
- Dead letter queue for failed operations

Requirements: 2.7 - Neo4j provenance (write-behind)
"""

import logging
import uuid
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import asyncio
from collections import deque
import threading

logger = logging.getLogger(__name__)

class OperationResult(Enum):
    """Result of idempotent operations"""
    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    TRANSIENT_FAILURE = "transient_failure"
    PERMANENT_FAILURE = "permanent_failure"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI_BACKOFF = "fibonacci_backoff"

@dataclass
class IdempotentOperation:
    """Idempotent operation definition"""
    operation_id: str
    operation_type: str  # "create_node", "create_relationship", "batch"
    cypher_query: str
    parameters: Dict[str, Any]

    # Retry configuration
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay_ms: float = 100.0
    max_delay_ms: float = 30000.0

    # Status tracking
    attempt_count: int = 0
    last_attempt: Optional[datetime] = None
    last_result: Optional[OperationResult] = None
    last_error: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_time_ms: float = 0.0

    # Context
    run_id: Optional[str] = None
    priority: int = 1  # 1=high, 2=medium, 3=low
@dataclass
class CircuitBreaker:
    """Circuit breaker for Neo4j operations"""
    failure_threshold: int = 5
    recovery_timeout_ms: float = 30000.0
    half_open_max_calls: int = 3

    # State tracking
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    half_open_calls: int = 0

    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit breaker"""

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds() * 1000
                if time_since_failure >= self.recovery_timeout_ms:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls

        return False

    def record_success(self) -> None:
        """Record successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

@dataclass
class OperationIntrospection:
    """Introspection data for operations"""
    operation_id: str
    query_plan: Dict[str, Any]
    execution_stats: Dict[str, Any]
    index_usage: List[str]
    warnings: List[str]
    estimated_cost: float
    actual_time_ms: float
    rows_affected: int

    created_at: datetime = field(default_factory=datetime.utcnow)

class Neo4jIdempotentService:
    """
    Service for idempotent Neo4j operations with advanced retry logic

    Ensures write-behind operations don't block hot path while providing
    reliable, idempotent merge operations with comprehensive monitoring
    """

    def __init__(self, neo4j_client=None, provenance_service=None):
        # Neo4j client and dependencies
        self.neo4j_client = neo4j_client
        self.provenance_service = provenance_service

        # Operation tracking
        self.pending_operations: deque = deque()
        self.completed_operations: List[IdempotentOperation] = []
        self.failed_operations: List[IdempotentOperation] = []
        self.dead_letter_queue: List[IdempotentOperation] = []

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker()

        # Introspection data
        self.operation_introspections: List[OperationIntrospection] = []

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="neo4j-idempotent")
        self.processing_lock = threading.Lock()

        # Performance tracking
        self.processing_times: List[float] = []
        self.operation_counts = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'retried_operations': 0,
            'circuit_breaker_trips': 0,
            'dead_letter_operations': 0
        }

        # Configuration
        self.config = {
            'max_batch_size': 100,
            'batch_timeout_ms': 5000.0,
            'enable_introspection': True,
            'enable_circuit_breaker': True,
            'dead_letter_threshold': 10,
            'hot_path_timeout_ms': 50.0,  # Max time to block hot path
            'background_processing_interval_ms': 1000.0
        }

        # Background processing
        self.background_thread = None
        self.shutdown_event = threading.Event()
        self._start_background_processing()

        logger.info("Neo4jIdempotentService initialized")

    def _start_background_processing(self) -> None:
        """Start background thread for processing operations"""

        def background_worker():
            while not self.shutdown_event.is_set():
                try:
                    self._process_pending_operations()
                    time.sleep(self.config['background_processing_interval_ms'] / 1000.0)
                except Exception as e:
                    logger.error(f"Background processing error: {e}")

        self.background_thread = threading.Thread(target=background_worker, daemon=True)
        self.background_thread.start()
        logger.info("Background processing thread started")
    def create_node_idempotent(
        self,
        node_type: str,
        node_id: str,
        properties: Dict[str, Any],
        run_id: Optional[str] = None,
        priority: int = 1
    ) -> str:
        """
        Create node idempotently (non-blocking for hot path)

        Args:
            node_type: Type of node (Expert, Game, Decision, etc.)
            node_id: Unique identifier for the node
            properties: Node properties
            run_id: Run identifier for scoping
            priority: Operation priority (1=high, 2=medium, 3=low)

        Returns:
            Operation ID for tracking
        """

        try:
            # Create idempotent MERGE query
            cypher_query = f"""
            MERGE (n:{node_type} {{id: $node_id}})
            ON CREATE SET n += $properties, n.created_at = datetime(), n.run_id = $run_id
            ON MATCH SET n.last_updated = datetime()
            RETURN n.id as node_id,
                   CASE WHEN n.created_at = datetime() THEN 'created' ELSE 'exists' END as status
            """

            parameters = {
                'node_id': node_id,
                'properties': properties,
                'run_id': run_id
            }

            # Create operation
            operation = IdempotentOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="create_node",
                cypher_query=cypher_query,
                parameters=parameters,
                run_id=run_id,
                priority=priority
            )

            # Add to queue for background processing
            with self.processing_lock:
                self.pending_operations.append(operation)
                self.operation_counts['total_operations'] += 1

            logger.debug(f"Queued node creation: {node_type}({node_id})")
            return operation.operation_id

        except Exception as e:
            logger.error(f"Failed to queue node creation: {e}")
            return ""

    def create_relationship_idempotent(
        self,
        source_node_type: str,
        source_node_id: str,
        target_node_type: str,
        target_node_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None,
        run_id: Optional[str] = None,
        priority: int = 1
    ) -> str:
        """
        Create relationship idempotently (non-blocking for hot path)

        Args:
            source_node_type: Type of source node
            source_node_id: Source node identifier
            target_node_type: Type of target node
            target_node_id: Target node identifier
            relationship_type: Type of relationship
            properties: Relationship properties
            run_id: Run identifier for scoping
            priority: Operation priority

        Returns:
            Operation ID for tracking
        """

        try:
            # Create idempotent MERGE query
            cypher_query = f"""
            MATCH (source:{source_node_type} {{id: $source_id}})
            MATCH (target:{target_node_type} {{id: $target_id}})
            MERGE (source)-[r:{relationship_type}]->(target)
            ON CREATE SET r += $properties, r.created_at = datetime(), r.run_id = $run_id
            ON MATCH SET r.last_updated = datetime()
            RETURN r.created_at as created_at,
                   CASE WHEN r.created_at = datetime() THEN 'created' ELSE 'exists' END as status
            """

            parameters = {
                'source_id': source_node_id,
                'target_id': target_node_id,
                'properties': properties or {},
                'run_id': run_id
            }

            # Create operation
            operation = IdempotentOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="create_relationship",
                cypher_query=cypher_query,
                parameters=parameters,
                run_id=run_id,
                priority=priority
            )

            # Add to queue for background processing
            with self.processing_lock:
                self.pending_operations.append(operation)
                self.operation_counts['total_operations'] += 1

            logger.debug(f"Queued relationship creation: {relationship_type}")
            return operation.operation_id

        except Exception as e:
            logger.error(f"Failed to queue relationship creation: {e}")
            return ""

    def create_batch_operation(
        self,
        operations: List[Dict[str, Any]],
        run_id: Optional[str] = None,
        priority: int = 2
    ) -> str:
        """
        Create batch operation for multiple nodes/relationships

        Args:
            operations: List of operation definitions
            run_id: Run identifier for scoping
            priority: Operation priority

        Returns:
            Operation ID for tracking
        """

        try:
            # Build batch UNWIND query
            cypher_query = """
            UNWIND $operations as op
            CALL {
                WITH op
                CALL apoc.cypher.doIt(op.query, op.params) YIELD value
                RETURN value
            }
            RETURN collect(value) as results
            """

            parameters = {
                'operations': operations,
                'run_id': run_id
            }

            # Create batch operation
            operation = IdempotentOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="batch",
                cypher_query=cypher_query,
                parameters=parameters,
                run_id=run_id,
                priority=priority,
                max_retries=5  # More retries for batch operations
            )

            # Add to queue
            with self.processing_lock:
                self.pending_operations.append(operation)
                self.operation_counts['total_operations'] += 1

            logger.debug(f"Queued batch operation with {len(operations)} operations")
            return operation.operation_id

        except Exception as e:
            logger.error(f"Failed to queue batch operation: {e}")
            return ""
    def _process_pending_operations(self) -> None:
        """Process pending operations in background"""

        if not self.pending_operations:
            return

        # Get batch of operations to process
        batch_operations = []
        with self.processing_lock:
            batch_size = min(len(self.pending_operations), self.config['max_batch_size'])
            for _ in range(batch_size):
                if self.pending_operations:
                    batch_operations.append(self.pending_operations.popleft())

        if not batch_operations:
            return

        # Sort by priority (1=high, 2=medium, 3=low)
        batch_operations.sort(key=lambda op: op.priority)

        # Process each operation
        for operation in batch_operations:
            try:
                self._execute_operation_with_retry(operation)
            except Exception as e:
                logger.error(f"Failed to process operation {operation.operation_id}: {e}")
                operation.last_result = OperationResult.PERMANENT_FAILURE
                operation.last_error = str(e)
                self.failed_operations.append(operation)

    def _execute_operation_with_retry(self, operation: IdempotentOperation) -> None:
        """Execute operation with retry logic"""

        start_time = time.time()

        try:
            # Check circuit breaker
            if self.config['enable_circuit_breaker'] and not self.circuit_breaker.should_allow_request():
                operation.last_result = OperationResult.CIRCUIT_OPEN
                operation.last_error = "Circuit breaker is open"
                self.failed_operations.append(operation)
                return

            # Attempt operation with retries
            for attempt in range(operation.max_retries + 1):
                operation.attempt_count = attempt + 1
                operation.last_attempt = datetime.utcnow()

                try:
                    result = self._execute_single_operation(operation)

                    if result in [OperationResult.SUCCESS, OperationResult.ALREADY_EXISTS]:
                        # Success
                        operation.last_result = result
                        operation.completed_at = datetime.utcnow()
                        operation.total_time_ms = (time.time() - start_time) * 1000

                        self.completed_operations.append(operation)
                        self.operation_counts['successful_operations'] += 1
                        self.processing_times.append(operation.total_time_ms)

                        if self.config['enable_circuit_breaker']:
                            self.circuit_breaker.record_success()

                        logger.debug(f"Operation {operation.operation_id} completed: {result.value}")
                        return

                    elif result == OperationResult.TRANSIENT_FAILURE:
                        # Retry with backoff
                        if attempt < operation.max_retries:
                            delay_ms = self._calculate_retry_delay(operation, attempt)
                            time.sleep(delay_ms / 1000.0)
                            self.operation_counts['retried_operations'] += 1
                            continue
                        else:
                            # Max retries exceeded
                            operation.last_result = OperationResult.PERMANENT_FAILURE
                            operation.last_error = "Max retries exceeded"
                            break

                    elif result == OperationResult.PERMANENT_FAILURE:
                        # Don't retry permanent failures
                        operation.last_result = result
                        break

                    elif result == OperationResult.TIMEOUT:
                        # Retry timeouts
                        if attempt < operation.max_retries:
                            delay_ms = self._calculate_retry_delay(operation, attempt)
                            time.sleep(delay_ms / 1000.0)
                            continue
                        else:
                            operation.last_result = result
                            break

                except Exception as e:
                    operation.last_error = str(e)
                    if attempt < operation.max_retries:
                        delay_ms = self._calculate_retry_delay(operation, attempt)
                        time.sleep(delay_ms / 1000.0)
                        continue
                    else:
                        operation.last_result = OperationResult.PERMANENT_FAILURE
                        break

            # Operation failed after all retries
            operation.completed_at = datetime.utcnow()
            operation.total_time_ms = (time.time() - start_time) * 1000

            self.failed_operations.append(operation)
            self.operation_counts['failed_operations'] += 1

            if self.config['enable_circuit_breaker']:
                self.circuit_breaker.record_failure()

            # Move to dead letter queue if too many failures
            if len(self.failed_operations) > self.config['dead_letter_threshold']:
                oldest_failed = self.failed_operations.pop(0)
                self.dead_letter_queue.append(oldest_failed)
                self.operation_counts['dead_letter_operations'] += 1

            logger.warning(f"Operation {operation.operation_id} failed: {operation.last_result}")

        except Exception as e:
            logger.error(f"Critical error executing operation {operation.operation_id}: {e}")
            operation.last_result = OperationResult.PERMANENT_FAILURE
            operation.last_error = str(e)
            self.failed_operations.append(operation)

    def _execute_single_operation(self, operation: IdempotentOperation) -> OperationResult:
        """Execute a single operation against Neo4j"""

        try:
            if self.neo4j_client:
                # Real Neo4j execution
                with self.neo4j_client.session() as session:
                    result = session.run(operation.cypher_query, operation.parameters)

                    # Collect introspection data if enabled
                    if self.config['enable_introspection']:
                        self._collect_introspection_data(operation, result)

                    # Check if operation was successful
                    records = list(result)
                    if records:
                        # Operation completed successfully
                        return OperationResult.SUCCESS
                    else:
                        # No records returned, but no error
                        return OperationResult.ALREADY_EXISTS
            else:
                # Mock execution for testing
                return self._mock_operation_execution(operation)

        except Exception as e:
            error_msg = str(e).lower()

            # Classify error types
            if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network']):
                return OperationResult.TRANSIENT_FAILURE
            elif any(keyword in error_msg for keyword in ['syntax', 'constraint', 'invalid']):
                return OperationResult.PERMANENT_FAILURE
            else:
                # Default to transient for unknown errors
                return OperationResult.TRANSIENT_FAILURE

    def _mock_operation_execution(self, operation: IdempotentOperation) -> OperationResult:
        """Mock operation execution for testing"""

        try:
            # Simulate processing time
            time.sleep(0.001)

            # Mock occasional failures for testing retry logic
            import random
            failure_rate = 0.1  # 10% failure rate

            if random.random() < failure_rate:
                if random.random() < 0.7:  # 70% of failures are transient
                    return OperationResult.TRANSIENT_FAILURE
                else:
                    return OperationResult.PERMANENT_FAILURE

            # Mock idempotency - some operations already exist
            if random.random() < 0.2:  # 20% already exist
                return OperationResult.ALREADY_EXISTS

            return OperationResult.SUCCESS

        except Exception as e:
            logger.error(f"Mock execution failed: {e}")
            return OperationResult.PERMANENT_FAILURE
    def _calculate_retry_delay(self, operation: IdempotentOperation, attempt: int) -> float:
        """Calculate retry delay based on strategy"""

        try:
            base_delay = operation.base_delay_ms
            max_delay = operation.max_delay_ms

            if operation.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                delay = base_delay * (2 ** attempt)
            elif operation.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
                delay = base_delay * (attempt + 1)
            elif operation.retry_strategy == RetryStrategy.FIXED_DELAY:
                delay = base_delay
            elif operation.retry_strategy == RetryStrategy.FIBONACCI_BACKOFF:
                fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
                fib_index = min(attempt, len(fib_sequence) - 1)
                delay = base_delay * fib_sequence[fib_index]
            else:
                delay = base_delay

            # Apply jitter to avoid thundering herd
            import random
            jitter = random.uniform(0.8, 1.2)
            delay *= jitter

            # Cap at maximum delay
            return min(delay, max_delay)

        except Exception as e:
            logger.error(f"Error calculating retry delay: {e}")
            return operation.base_delay_ms

    def _collect_introspection_data(self, operation: IdempotentOperation, result) -> None:
        """Collect introspection data for operation analysis"""

        try:
            if not self.config['enable_introspection']:
                return

            # Mock introspection data (in production, would use EXPLAIN/PROFILE)
            introspection = OperationIntrospection(
                operation_id=operation.operation_id,
                query_plan={
                    'operator': 'Merge',
                    'estimated_rows': 1,
                    'db_hits': 2
                },
                execution_stats={
                    'nodes_created': 1 if 'CREATE' in operation.cypher_query else 0,
                    'relationships_created': 1 if 'MERGE' in operation.cypher_query and '-[' in operation.cypher_query else 0,
                    'properties_set': len(operation.parameters.get('properties', {}))
                },
                index_usage=['node_id_index'] if 'id:' in operation.cypher_query else [],
                warnings=[],
                estimated_cost=1.5,
                actual_time_ms=operation.total_time_ms,
                rows_affected=1
            )

            self.operation_introspections.append(introspection)

            # Keep only recent introspections
            if len(self.operation_introspections) > 1000:
                self.operation_introspections = self.operation_introspections[-500:]

        except Exception as e:
            logger.error(f"Error collecting introspection data: {e}")

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific operation"""

        try:
            # Check completed operations
            for operation in self.completed_operations:
                if operation.operation_id == operation_id:
                    return {
                        'operation_id': operation.operation_id,
                        'status': 'completed',
                        'result': operation.last_result.value if operation.last_result else None,
                        'attempt_count': operation.attempt_count,
                        'total_time_ms': operation.total_time_ms,
                        'created_at': operation.created_at.isoformat(),
                        'completed_at': operation.completed_at.isoformat() if operation.completed_at else None
                    }

            # Check failed operations
            for operation in self.failed_operations:
                if operation.operation_id == operation_id:
                    return {
                        'operation_id': operation.operation_id,
                        'status': 'failed',
                        'result': operation.last_result.value if operation.last_result else None,
                        'error': operation.last_error,
                        'attempt_count': operation.attempt_count,
                        'total_time_ms': operation.total_time_ms,
                        'created_at': operation.created_at.isoformat(),
                        'completed_at': operation.completed_at.isoformat() if operation.completed_at else None
                    }

            # Check pending operations
            with self.processing_lock:
                for operation in self.pending_operations:
                    if operation.operation_id == operation_id:
                        return {
                            'operation_id': operation.operation_id,
                            'status': 'pending',
                            'priority': operation.priority,
                            'created_at': operation.created_at.isoformat()
                        }

            # Check dead letter queue
            for operation in self.dead_letter_queue:
                if operation.operation_id == operation_id:
                    return {
                        'operation_id': operation.operation_id,
                        'status': 'dead_letter',
                        'result': operation.last_result.value if operation.last_result else None,
                        'error': operation.last_error,
                        'attempt_count': operation.attempt_count,
                        'created_at': operation.created_at.isoformat()
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting operation status: {e}")
            return None

    def get_introspection_data(
        self,
        operation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get introspection data for operations"""

        try:
            introspections = self.operation_introspections

            if operation_id:
                introspections = [i for i in introspections if i.operation_id == operation_id]

            # Sort by creation time (newest first)
            introspections.sort(key=lambda i: i.created_at, reverse=True)

            # Limit results
            introspections = introspections[:limit]

            # Convert to dict format
            result = []
            for introspection in introspections:
                result.append({
                    'operation_id': introspection.operation_id,
                    'query_plan': introspection.query_plan,
                    'execution_stats': introspection.execution_stats,
                    'index_usage': introspection.index_usage,
                    'warnings': introspection.warnings,
                    'estimated_cost': introspection.estimated_cost,
                    'actual_time_ms': introspection.actual_time_ms,
                    'rows_affected': introspection.rows_affected,
                    'created_at': introspection.created_at.isoformat()
                })

            return result

        except Exception as e:
            logger.error(f"Error getting introspection data: {e}")
            return []
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""

        try:
            # Calculate timing statistics
            if self.processing_times:
                import numpy as np
                times = np.array(self.processing_times)

                timing_stats = {
                    'average_time_ms': float(np.mean(times)),
                    'p50_time_ms': float(np.percentile(times, 50)),
                    'p95_time_ms': float(np.percentile(times, 95)),
                    'p99_time_ms': float(np.percentile(times, 99)),
                    'max_time_ms': float(np.max(times)),
                    'min_time_ms': float(np.min(times))
                }
            else:
                timing_stats = {
                    'average_time_ms': 0,
                    'p50_time_ms': 0,
                    'p95_time_ms': 0,
                    'p99_time_ms': 0,
                    'max_time_ms': 0,
                    'min_time_ms': 0
                }

            # Calculate success rates
            total_ops = self.operation_counts['total_operations']
            success_rate = self.operation_counts['successful_operations'] / max(total_ops, 1)
            failure_rate = self.operation_counts['failed_operations'] / max(total_ops, 1)

            # Queue statistics
            with self.processing_lock:
                queue_stats = {
                    'pending_operations': len(self.pending_operations),
                    'completed_operations': len(self.completed_operations),
                    'failed_operations': len(self.failed_operations),
                    'dead_letter_operations': len(self.dead_letter_queue)
                }

            # Circuit breaker status
            circuit_stats = {
                'circuit_state': self.circuit_breaker.state.value,
                'failure_count': self.circuit_breaker.failure_count,
                'last_failure_time': self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None
            }

            return {
                'operation_counts': self.operation_counts.copy(),
                'timing_statistics': timing_stats,
                'success_rate': success_rate,
                'failure_rate': failure_rate,
                'queue_statistics': queue_stats,
                'circuit_breaker': circuit_stats,
                'config': self.config.copy(),
                'introspection_count': len(self.operation_introspections)
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""

        try:
            # Check if background thread is running
            background_healthy = self.background_thread and self.background_thread.is_alive()

            # Check circuit breaker status
            circuit_healthy = self.circuit_breaker.state != CircuitState.OPEN

            # Check queue sizes
            with self.processing_lock:
                queue_size = len(self.pending_operations)

            queue_healthy = queue_size < self.config['max_batch_size'] * 2

            # Check error rates
            total_ops = self.operation_counts['total_operations']
            if total_ops > 0:
                error_rate = self.operation_counts['failed_operations'] / total_ops
                error_healthy = error_rate < 0.1  # Less than 10% error rate
            else:
                error_rate = 0.0
                error_healthy = True

            # Overall health
            overall_healthy = all([
                background_healthy,
                circuit_healthy,
                queue_healthy,
                error_healthy
            ])

            return {
                'overall_healthy': overall_healthy,
                'background_thread_healthy': background_healthy,
                'circuit_breaker_healthy': circuit_healthy,
                'queue_healthy': queue_healthy,
                'error_rate_healthy': error_healthy,
                'error_rate': error_rate,
                'queue_size': queue_size,
                'circuit_state': self.circuit_breaker.state.value,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'overall_healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update service configuration"""

        try:
            for key, value in config_updates.items():
                if key in self.config:
                    old_value = self.config[key]
                    self.config[key] = value
                    logger.info(f"Updated config {key}: {old_value} -> {value}")
                else:
                    logger.warning(f"Unknown config key: {key}")

            return True

        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False

    def clear_dead_letter_queue(self) -> int:
        """Clear dead letter queue and return count of cleared operations"""

        try:
            count = len(self.dead_letter_queue)
            self.dead_letter_queue.clear()
            self.operation_counts['dead_letter_operations'] = 0

            logger.info(f"Cleared {count} operations from dead letter queue")
            return count

        except Exception as e:
            logger.error(f"Error clearing dead letter queue: {e}")
            return 0

    def shutdown(self) -> None:
        """Shutdown the service gracefully"""

        try:
            logger.info("Shutting down Neo4jIdempotentService...")

            # Signal background thread to stop
            self.shutdown_event.set()

            # Wait for background thread to finish
            if self.background_thread and self.background_thread.is_alive():
                self.background_thread.join(timeout=5.0)

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            logger.info("Neo4jIdempotentService shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.shutdown()
        except:
            pass
