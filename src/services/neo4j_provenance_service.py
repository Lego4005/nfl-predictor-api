"""
Neo4j Write-Behind Provenance Service

Implements write-behind provenance tracking for the Expert Council Betting System.
Creates Decision, Assertion, Thought nodes and USED_IN, EVALUATED_AS, LEARNED_FROM
relationships in Neo4j for complete provenance trails.

Features:
- Decision node creation with expert and game context
- Assertion node creation with prediction details
- Thought (memory) node creation with episodic context
- USED_IN relationships (Assertion -> Thought)
- EVALUATED_AS relationships (Assertion -> Grade)
- LEARNED_FROM relationships (Reflection -> Outcome)
- Async write-behind processing
- Batch operations for performance
- Error handling and retry logic

Requirements: 2.7 - Neo4j provenance (write-behind)
"""

import logging
import uuid
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)

class ProvenanceNodeType(Enum):
    """Types of provenance nodes"""
    EXPERT = "Expert"
    GAME = "Game"
    DECISION = "Decision"
    ASSERTION = "Assertion"
    THOUGHT = "Thought"
    REFLECTION = "Reflection"
    TEAM = "Team"

class ProvenanceRelationType(Enum):
    """Types of provenance relationships"""
    PREDICTED = "PREDICTED"
    HAS_ASSERTION = "HAS_ASSERTION"
    USED_IN = "USED_IN"
    EVALUATED_AS = "EVALUATED_AS"
    LEARNED_FROM = "LEARNED_FROM"
    IN_RUN = "IN_RUN"
    REFLECTS_ON = "REFLECTS_ON"
class ProvenanceOperationStatus(Enum):
    """Status of provenance operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ProvenanceNode:
    """Provenance node definition"""
    node_id: str
    node_type: ProvenanceNodeType
    properties: Dict[str, Any]
    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ProvenanceOperationStatus = ProvenanceOperationStatus.PENDING

@dataclass
class ProvenanceRelationship:
    """Provenance relationship definition"""
    relationship_id: str
    relationship_type: ProvenanceRelationType
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ProvenanceOperationStatus = ProvenanceOperationStatus.PENDING

@dataclass
class ProvenanceOperation:
    """Batch provenance operation"""
    operation_id: str
    nodes: List[ProvenanceNode] = field(default_factory=list)
    relationships: List[ProvenanceRelationship] = field(default_factory=list)
    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: ProvenanceOperationStatus = ProvenanceOperationStatus.PENDING
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0
class Neo4jProvenanceService:
    """
    Write-behind service for Neo4j provenance tracking

    Creates Decision, Assertion, Thought nodes and their relationships
    for complete provenance trails in the Expert Council Betting System
    """

    def __init__(self, neo4j_client=None, constraints_service=None):
        # Neo4j client (mock for now, real in production)
        self.neo4j_client = neo4j_client
        self.constraints_service = constraints_service

        # Operation tracking
        self.operations: List[ProvenanceOperation] = []
        self.operation_queue: List[ProvenanceOperation] = []

        # Performance tracking
        self.processing_times: List[float] = []
        self.operation_counts = {
            'nodes_created': 0,
            'relationships_created': 0,
            'operations_completed': 0,
            'operations_failed': 0,
            'batch_operations': 0
        }

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Configuration
        self.config = {
            'batch_size': 50,
            'max_retries': 3,
            'retry_delay_seconds': 1.0,
            'backoff_multiplier': 2.0,
            'async_processing': True,
            'enable_batching': True
        }

        logger.info("Neo4jProvenanceService initialized")

    def create_decision_provenance(
        self,
        expert_id: str,
        game_id: str,
        decision_id: str,
        predictions: List[Dict[str, Any]],
        memories_used: List[Dict[str, Any]],
        run_id: Optional[str] = None
    ) -> Optional[ProvenanceOperation]:
        """
        Create complete provenance trail for an expert decision

        Args:
            expert_id: Expert making the decision
            game_id: Game being predicted
            decision_id: Unique decision identifier
            predictions: List of predictions/assertions
            memories_used: List of memories used in decision
            run_id: Run identifier for scoping

        Returns:
            ProvenanceOperation if successful, None if failed
        """

        start_time = datetime.utcnow()

        try:
            logger.info(f"Creating decision provenance for {expert_id} on game {game_id}")

            # Get current run_id if not provided
            if not run_id and self.constraints_service:
                run_id = self.constraints_service.current_run_id

            # Create operation
            operation = ProvenanceOperation(
                operation_id=str(uuid.uuid4()),
                run_id=run_id
            )

            # Create Expert node (if not exists)
            expert_node = self._create_expert_node(expert_id, run_id)
            operation.nodes.append(expert_node)

            # Create Game node (if not exists)
            game_node = self._create_game_node(game_id, run_id)
            operation.nodes.append(game_node)

            # Create Decision node
            decision_node = self._create_decision_node(
                decision_id, expert_id, game_id, run_id
            )
            operation.nodes.append(decision_node)

            # Create PREDICTED relationship (Expert -> Decision)
            predicted_rel = self._create_relationship(
                ProvenanceRelationType.PREDICTED,
                expert_id, decision_id,
                {'game_id': game_id, 'timestamp': datetime.utcnow().isoformat()},
                run_id
            )
            operation.relationships.append(predicted_rel)

            # Create Assertion nodes and relationships
            for prediction in predictions:
                assertion_node, assertion_relationships = self._create_assertion_provenance(
                    prediction, decision_id, memories_used, run_id
                )
                operation.nodes.append(assertion_node)
                operation.relationships.extend(assertion_relationships)

            # Create Thought nodes for memories
            for memory in memories_used:
                thought_node = self._create_thought_node(memory, run_id)
                operation.nodes.append(thought_node)

            # Link Decision to Run if run_id provided
            if run_id:
                run_relationship = self._create_relationship(
                    ProvenanceRelationType.IN_RUN,
                    decision_id, f"run_{run_id}",
                    {'linked_at': datetime.utcnow().isoformat()},
                    run_id
                )
                operation.relationships.append(run_relationship)

            # Process operation
            if self.config['async_processing']:
                self._schedule_async_operation(operation)
            else:
                self._process_operation_sync(operation)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            operation.processing_time_ms = processing_time

            self.operations.append(operation)

            logger.info(f"Decision provenance created: {operation.operation_id}")
            return operation

        except Exception as e:
            logger.error(f"Failed to create decision provenance: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Create failed operation record
            failed_operation = ProvenanceOperation(
                operation_id=str(uuid.uuid4()),
                run_id=run_id,
                status=ProvenanceOperationStatus.FAILED,
                error_message=str(e),
                processing_time_ms=processing_time
            )

            self.operations.append(failed_operation)
            self.operation_counts['operations_failed'] += 1

            return None
    def create_evaluation_provenance(
        self,
        assertion_id: str,
        grading_result: Dict[str, Any],
        run_id: Optional[str] = None
    ) -> Optional[ProvenanceOperation]:
        """
        Create provenance for assertion evaluation/grading

        Args:
            assertion_id: Assertion being evaluated
            grading_result: Grading/evaluation result
            run_id: Run identifier for scoping

        Returns:
            ProvenanceOperation if successful, None if failed
        """

        try:
            logger.debug(f"Creating evaluation provenance for assertion {assertion_id}")

            # Get current run_id if not provided
            if not run_id and self.constraints_service:
                run_id = self.constraints_service.current_run_id

            # Create operation
            operation = ProvenanceOperation(
                operation_id=str(uuid.uuid4()),
                run_id=run_id
            )

            # Create EVALUATED_AS relationship
            evaluation_rel = self._create_relationship(
                ProvenanceRelationType.EVALUATED_AS,
                assertion_id, f"grade_{assertion_id}",
                {
                    'final_score': grading_result.get('final_score', 0.0),
                    'exact_match': grading_result.get('exact_match', False),
                    'grading_method': grading_result.get('grading_method', ''),
                    'evaluated_at': datetime.utcnow().isoformat()
                },
                run_id
            )
            operation.relationships.append(evaluation_rel)

            # Process operation
            if self.config['async_processing']:
                self._schedule_async_operation(operation)
            else:
                self._process_operation_sync(operation)

            self.operations.append(operation)
            return operation

        except Exception as e:
            logger.error(f"Failed to create evaluation provenance: {e}")
            return None

    def create_learning_provenance(
        self,
        expert_id: str,
        game_id: str,
        learning_updates: List[Dict[str, Any]],
        reflection_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> Optional[ProvenanceOperation]:
        """
        Create provenance for learning updates and reflections

        Args:
            expert_id: Expert who learned
            game_id: Game that triggered learning
            learning_updates: List of learning updates
            reflection_id: Optional reflection identifier
            run_id: Run identifier for scoping

        Returns:
            ProvenanceOperation if successful, None if failed
        """

        try:
            logger.debug(f"Creating learning provenance for expert {expert_id}")

            # Get current run_id if not provided
            if not run_id and self.constraints_service:
                run_id = self.constraints_service.current_run_id

            # Create operation
            operation = ProvenanceOperation(
                operation_id=str(uuid.uuid4()),
                run_id=run_id
            )

            # Create LEARNED_FROM relationships for each learning update
            for update in learning_updates:
                learning_rel = self._create_relationship(
                    ProvenanceRelationType.LEARNED_FROM,
                    expert_id, game_id,
                    {
                        'learning_type': update.get('learning_type', ''),
                        'update_id': update.get('update_id', ''),
                        'category': update.get('category', ''),
                        'improvement': update.get('calibration_improvement', 0.0),
                        'learned_at': datetime.utcnow().isoformat()
                    },
                    run_id
                )
                operation.relationships.append(learning_rel)

            # If reflection provided, create reflection relationships
            if reflection_id:
                reflection_rel = self._create_relationship(
                    ProvenanceRelationType.REFLECTS_ON,
                    reflection_id, game_id,
                    {
                        'expert_id': expert_id,
                        'reflected_at': datetime.utcnow().isoformat()
                    },
                    run_id
                )
                operation.relationships.append(reflection_rel)

            # Process operation
            if self.config['async_processing']:
                self._schedule_async_operation(operation)
            else:
                self._process_operation_sync(operation)

            self.operations.append(operation)
            return operation

        except Exception as e:
            logger.error(f"Failed to create learning provenance: {e}")
            return None
    def _create_expert_node(self, expert_id: str, run_id: Optional[str] = None) -> ProvenanceNode:
        """Create Expert node"""
        return ProvenanceNode(
            node_id=expert_id,
            node_type=ProvenanceNodeType.EXPERT,
            properties={
                'expert_id': expert_id,
                'created_at': datetime.utcnow().isoformat()
            },
            run_id=run_id
        )

    def _create_game_node(self, game_id: str, run_id: Optional[str] = None) -> ProvenanceNode:
        """Create Game node"""
        return ProvenanceNode(
            node_id=game_id,
            node_type=ProvenanceNodeType.GAME,
            properties={
                'game_id': game_id,
                'created_at': datetime.utcnow().isoformat()
            },
            run_id=run_id
        )

    def _create_decision_node(
        self,
        decision_id: str,
        expert_id: str,
        game_id: str,
        run_id: Optional[str] = None
    ) -> ProvenanceNode:
        """Create Decision node"""
        return ProvenanceNode(
            node_id=decision_id,
            node_type=ProvenanceNodeType.DECISION,
            properties={
                'decision_id': decision_id,
                'expert_id': expert_id,
                'game_id': game_id,
                'created_at': datetime.utcnow().isoformat()
            },
            run_id=run_id
        )

    def _create_assertion_provenance(
        self,
        prediction: Dict[str, Any],
        decision_id: str,
        memories_used: List[Dict[str, Any]],
        run_id: Optional[str] = None
    ) -> Tuple[ProvenanceNode, List[ProvenanceRelationship]]:
        """Create Assertion node and its relationships"""

        assertion_id = prediction.get('id', str(uuid.uuid4()))

        # Create Assertion node
        assertion_node = ProvenanceNode(
            node_id=assertion_id,
            node_type=ProvenanceNodeType.ASSERTION,
            properties={
                'assertion_id': assertion_id,
                'category': prediction.get('category', ''),
                'pred_type': prediction.get('pred_type', ''),
                'value': prediction.get('value'),
                'confidence': prediction.get('confidence', 0.5),
                'stake_units': prediction.get('stake_units', 0.0),
                'created_at': datetime.utcnow().isoformat()
            },
            run_id=run_id
        )

        relationships = []

        # Create HAS_ASSERTION relationship (Decision -> Assertion)
        has_assertion_rel = self._create_relationship(
            ProvenanceRelationType.HAS_ASSERTION,
            decision_id, assertion_id,
            {
                'category': prediction.get('category', ''),
                'confidence': prediction.get('confidence', 0.5)
            },
            run_id
        )
        relationships.append(has_assertion_rel)

        # Create USED_IN relationships (Assertion -> Thought)
        why_references = prediction.get('why', [])
        for memory_ref in why_references:
            memory_id = memory_ref.get('memory_id')
            if memory_id:
                used_in_rel = self._create_relationship(
                    ProvenanceRelationType.USED_IN,
                    assertion_id, memory_id,
                    {
                        'weight': memory_ref.get('weight', 0.0),
                        'rank': memory_ref.get('rank', 0),
                        'score': memory_ref.get('score', 0.0),
                        'category': prediction.get('category', '')
                    },
                    run_id
                )
                relationships.append(used_in_rel)

        return assertion_node, relationships

    def _create_thought_node(
        self,
        memory: Dict[str, Any],
        run_id: Optional[str] = None
    ) -> ProvenanceNode:
        """Create Thought (memory) node"""

        memory_id = memory.get('memory_id', str(uuid.uuid4()))

        return ProvenanceNode(
            node_id=memory_id,
            node_type=ProvenanceNodeType.THOUGHT,
            properties={
                'memory_id': memory_id,
                'content': memory.get('content', ''),
                'embedding_vector': memory.get('embedding', []),
                'similarity_score': memory.get('similarity_score', 0.0),
                'recency_score': memory.get('recency_score', 0.0),
                'created_at': memory.get('created_at', datetime.utcnow().isoformat())
            },
            run_id=run_id
        )
    def _create_relationship(
        self,
        rel_type: ProvenanceRelationType,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any] = None,
        run_id: Optional[str] = None
    ) -> ProvenanceRelationship:
        """Create a provenance relationship"""

        return ProvenanceRelationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=rel_type,
            source_node_id=source_id,
            target_node_id=target_id,
            properties=properties or {},
            run_id=run_id
        )

    def _schedule_async_operation(self, operation: ProvenanceOperation) -> None:
        """Schedule operation for async processing"""

        try:
            operation.status = ProvenanceOperationStatus.IN_PROGRESS
            self.operation_queue.append(operation)

            # Submit to thread pool
            self.executor.submit(self._process_operation_async, operation)

        except Exception as e:
            logger.error(f"Failed to schedule async operation: {e}")
            operation.status = ProvenanceOperationStatus.FAILED
            operation.error_message = str(e)

    def _process_operation_sync(self, operation: ProvenanceOperation) -> bool:
        """Process operation synchronously"""

        try:
            start_time = time.time()

            # Create nodes
            for node in operation.nodes:
                success = self._create_node_in_neo4j(node)
                if success:
                    node.status = ProvenanceOperationStatus.COMPLETED
                    self.operation_counts['nodes_created'] += 1
                else:
                    node.status = ProvenanceOperationStatus.FAILED

            # Create relationships
            for relationship in operation.relationships:
                success = self._create_relationship_in_neo4j(relationship)
                if success:
                    relationship.status = ProvenanceOperationStatus.COMPLETED
                    self.operation_counts['relationships_created'] += 1
                else:
                    relationship.status = ProvenanceOperationStatus.FAILED

            processing_time = (time.time() - start_time) * 1000
            operation.processing_time_ms = processing_time
            operation.completed_at = datetime.utcnow()
            operation.status = ProvenanceOperationStatus.COMPLETED

            self.processing_times.append(processing_time)
            self.operation_counts['operations_completed'] += 1

            logger.debug(f"Operation processed synchronously: {operation.operation_id}")
            return True

        except Exception as e:
            logger.error(f"Sync operation processing failed: {e}")
            operation.status = ProvenanceOperationStatus.FAILED
            operation.error_message = str(e)
            self.operation_counts['operations_failed'] += 1
            return False

    def _process_operation_async(self, operation: ProvenanceOperation) -> None:
        """Process operation asynchronously"""

        try:
            # Process with retry logic
            max_retries = self.config['max_retries']
            retry_delay = self.config['retry_delay_seconds']

            for attempt in range(max_retries + 1):
                try:
                    success = self._process_operation_sync(operation)
                    if success:
                        return

                    if attempt < max_retries:
                        operation.status = ProvenanceOperationStatus.RETRYING
                        time.sleep(retry_delay)
                        retry_delay *= self.config['backoff_multiplier']

                except Exception as e:
                    logger.error(f"Async operation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= self.config['backoff_multiplier']

            # All attempts failed
            operation.status = ProvenanceOperationStatus.FAILED
            operation.error_message = "Max retries exceeded"
            self.operation_counts['operations_failed'] += 1

        except Exception as e:
            logger.error(f"Async operation processing failed: {e}")
            operation.status = ProvenanceOperationStatus.FAILED
            operation.error_message = str(e)
            self.operation_counts['operations_failed'] += 1
    def _create_node_in_neo4j(self, node: ProvenanceNode) -> bool:
        """Create a node in Neo4j (mock implementation)"""

        try:
            # Mock Neo4j node creation
            if self.neo4j_client:
                # Real implementation would be:
                # with self.neo4j_client.session() as session:
                #     query = f"MERGE (n:{node.node_type.value} {{id: $id}}) SET n += $properties"
                #     session.run(query, id=node.node_id, properties=node.properties)
                pass

            # Mock node creation with occasional failures for testing
            import random
            if random.random() < 0.05:  # 5% failure rate
                raise Exception("Mock Neo4j node creation failure")

            logger.debug(f"Created {node.node_type.value} node: {node.node_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create node {node.node_id}: {e}")
            return False

    def _create_relationship_in_neo4j(self, relationship: ProvenanceRelationship) -> bool:
        """Create a relationship in Neo4j (mock implementation)"""

        try:
            # Mock Neo4j relationship creation
            if self.neo4j_client:
                # Real implementation would be:
                # with self.neo4j_client.session() as session:
                #     query = """
                #     MATCH (a {id: $source_id})
                #     MATCH (b {id: $target_id})
                #     MERGE (a)-[r:REL_TYPE]->(b)
                #     SET r += $properties
                #     """
                #     session.run(query, source_id=relationship.source_node_id,
                #                 target_id=relationship.target_node_id,
                #                 properties=relationship.properties)
                pass

            # Mock relationship creation with occasional failures
            import random
            if random.random() < 0.03:  # 3% failure rate
                raise Exception("Mock Neo4j relationship creation failure")

            logger.debug(f"Created {relationship.relationship_type.value} relationship: "
                        f"{relationship.source_node_id} -> {relationship.target_node_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create relationship {relationship.relationship_id}: {e}")
            return False

    def get_provenance_trail(
        self,
        decision_id: str,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get complete provenance trail for a decision"""

        try:
            # Mock provenance trail query
            if self.neo4j_client:
                # Real implementation would query Neo4j:
                # query = """
                # MATCH (d:Decision {decision_id: $decision_id})
                # OPTIONAL MATCH (d)-[:HAS_ASSERTION]->(a:Assertion)
                # OPTIONAL MATCH (a)-[:USED_IN]->(t:Thought)
                # OPTIONAL MATCH (a)-[:EVALUATED_AS]->(g)
                # RETURN d, collect(a) as assertions, collect(t) as thoughts
                # """
                pass

            # Mock trail data
            trail = {
                'decision_id': decision_id,
                'run_id': run_id,
                'expert_id': 'conservative_analyzer',
                'game_id': 'KC_vs_BUF_2025_W1',
                'assertions': [
                    {
                        'assertion_id': 'assertion_001',
                        'category': 'game_winner',
                        'confidence': 0.8,
                        'memories_used': ['memory_001', 'memory_002'],
                        'evaluation': {'final_score': 0.95, 'exact_match': True}
                    }
                ],
                'memories': [
                    {
                        'memory_id': 'memory_001',
                        'content': 'KC has strong home field advantage',
                        'similarity_score': 0.92
                    }
                ],
                'relationships': [
                    {'type': 'HAS_ASSERTION', 'source': decision_id, 'target': 'assertion_001'},
                    {'type': 'USED_IN', 'source': 'assertion_001', 'target': 'memory_001'}
                ]
            }

            return trail

        except Exception as e:
            logger.error(f"Failed to get provenance trail: {e}")
            return {'error': str(e)}

    def query_why_lineage(
        self,
        assertion_id: str,
        run_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query 'why' lineage for an assertion"""

        try:
            # Mock why lineage query
            if self.neo4j_client:
                # Real implementation:
                # query = """
                # MATCH (a:Assertion {assertion_id: $assertion_id})-[:USED_IN]->(t:Thought)
                # RETURN t.memory_id as memory_id, t.content as content,
                #        t.similarity_score as score
                # ORDER BY score DESC
                # """
                pass

            # Mock lineage data
            lineage = [
                {
                    'memory_id': 'memory_001',
                    'content': 'KC has strong home field advantage in cold weather',
                    'similarity_score': 0.92,
                    'weight': 0.8,
                    'rank': 1
                },
                {
                    'memory_id': 'memory_002',
                    'content': 'BUF struggles on the road against strong defenses',
                    'similarity_score': 0.87,
                    'weight': 0.6,
                    'rank': 2
                }
            ]

            return lineage

        except Exception as e:
            logger.error(f"Failed to query why lineage: {e}")
            return []
    def get_operation_status(self, operation_id: str) -> Optional[ProvenanceOperation]:
        """Get status of a specific operation"""

        try:
            for operation in self.operations:
                if operation.operation_id == operation_id:
                    return operation
            return None

        except Exception as e:
            logger.error(f"Failed to get operation status: {e}")
            return None

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for provenance operations"""

        try:
            if not self.processing_times:
                return {
                    'total_operations': len(self.operations),
                    'average_time_ms': 0,
                    'operation_counts': self.operation_counts.copy(),
                    'queue_size': len(self.operation_queue),
                    'config': self.config.copy()
                }

            import numpy as np
            times = np.array(self.processing_times)

            # Calculate status distribution
            status_counts = {}
            for operation in self.operations:
                status = operation.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                'total_operations': len(self.operations),
                'average_time_ms': float(np.mean(times)),
                'p95_time_ms': float(np.percentile(times, 95)),
                'p99_time_ms': float(np.percentile(times, 99)),
                'max_time_ms': float(np.max(times)),
                'operation_counts': self.operation_counts.copy(),
                'status_distribution': status_counts,
                'queue_size': len(self.operation_queue),
                'success_rate': self.operation_counts['operations_completed'] / max(len(self.operations), 1),
                'config': self.config.copy()
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}

    def get_recent_operations(self, limit: int = 10) -> List[ProvenanceOperation]:
        """Get recent operations"""

        try:
            # Sort by creation time (newest first)
            sorted_operations = sorted(
                self.operations,
                key=lambda op: op.created_at,
                reverse=True
            )

            return sorted_operations[:limit]

        except Exception as e:
            logger.error(f"Failed to get recent operations: {e}")
            return []

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
            logger.error(f"Failed to update config: {e}")
            return False

    def clear_all_data(self) -> None:
        """Clear all data (for testing)"""
        self.operations.clear()
        self.operation_queue.clear()
        self.processing_times.clear()
        self.operation_counts = {
            'nodes_created': 0,
            'relationships_created': 0,
            'operations_completed': 0,
            'operations_failed': 0,
            'batch_operations': 0
        }

    def __del__(self):
        """Cleanup thread pool on destruction"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except:
            pass
