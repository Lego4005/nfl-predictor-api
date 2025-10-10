"""
Neo4j Constraints and Run Scope Service

Implements Neo4j database constraints and run scoping for the Expert Council Betting System.
Sets up uniqueness constraints, creates run nodes, and manages provenance isolation
through run_id property scoping.

Features:
- Uniqueness constraints for all node types
- Run node creation and management
- Run scoping for provenance isolation
- Constraint validation and monitoring
- Database schema initializati
equirements: 2.7, 4.1 - Neo4j provenance (write-behind)
"""

import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ConstraintType(Enum):
    """Types of Neo4j constraints"""
    UNIQUENESS = "uniqueness"
    EXISTENCE = "existence"
    NODE_KEY = "node_key"

class ConstraintStatus(Enum):
    """Status of constraint operations"""
    PENDING = "pending"
    CREATED = "created"
    EXISTS = "exists"
    FAILED = "failed"
    DROPPED = "dropped"

@dataclass
class Neo4jConstraint:
    """Neo4j constraint definition"""
    constraint_name: str
    constraint_type: ConstraintType
    node_label: str
    property_name: str
    constraint_query: str
    status: ConstraintStatus = ConstraintStatus.PENDING
    created_at: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class RunNode:
    """Neo4j run node definition"""
    run_id: str
    run_name: str
    description: str
    created_at: datetime
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConstraintValidationResult:
    """Result of constraint validation"""
    constraint_name: str
    is_valid: bool
    violation_count: int
    sample_violations: List[Dict[str, Any]] = field(default_factory=list)
    validation_time: datetime = field(default_factory=datetime.utcnow)

class Neo4jConstraintsService:
    """
    Service for managing Neo4j constraints and run scoping

    Handles uniqueness constraints, run node creation, and provenance isolation
    through run_id property scoping
    """

    def __init__(self, neo4j_client=None):
        # Mock Neo4j client (in production, would be real Neo4j driver)
        self.neo4j_client = neo4j_client

        # Constraint definitions
        self.constraints = self._define_constraints()

        # Run tracking
        self.runs: Dict[str, RunNode] = {}
        self.current_run_id: Optional[str] = None

        # Performance tracking
        self.constraint_creation_times: List[float] = []
        self.validation_times: List[float] = []
        self.operation_counts = {
            'constraints_created': 0,
            'constraints_failed': 0,
            'runs_created': 0,
            'validations_performed': 0
        }

        logger.info("Neo4jConstraintsService initialized")

    def _define_constraints(self) -> List[Neo4jConstraint]:
        """Define all required uniqueness constraints"""

        constraints = [
            # Expert uniqueness constraint
            Neo4jConstraint(
                constraint_name="expert_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Expert",
                property_name="expert_id",
                constraint_query="CREATE CONSTRAINT expert_id_unique FOR (e:Expert) REQUIRE e.expert_id IS UNIQUE"
            ),

            # Team uniqueness constraint
            Neo4jConstraint(
                constraint_name="team_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Team",
                property_name="team_id",
                constraint_query="CREATE CONSTRAINT team_id_unique FOR (t:Team) REQUIRE t.team_id IS UNIQUE"
            ),

            # Game uniqueness constraint
            Neo4jConstraint(
                constraint_name="game_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Game",
                property_name="game_id",
                constraint_query="CREATE CONSTRAINT game_id_unique FOR (g:Game) REQUIRE g.game_id IS UNIQUE"
            ),

            # Decision uniqueness constraint
            Neo4jConstraint(
                constraint_name="decision_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Decision",
                property_name="decision_id",
                constraint_query="CREATE CONSTRAINT decision_id_unique FOR (d:Decision) REQUIRE d.decision_id IS UNIQUE"
            ),

            # Assertion uniqueness constraint
            Neo4jConstraint(
                constraint_name="assertion_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Assertion",
                property_name="assertion_id",
                constraint_query="CREATE CONSTRAINT assertion_id_unique FOR (a:Assertion) REQUIRE a.assertion_id IS UNIQUE"
            ),

            # Thought (memory) uniqueness constraint
            Neo4jConstraint(
                constraint_name="memory_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Thought",
                property_name="memory_id",
                constraint_query="CREATE CONSTRAINT memory_id_unique FOR (th:Thought) REQUIRE th.memory_id IS UNIQUE"
            ),

            # Reflection uniqueness constraint
            Neo4jConstraint(
                constraint_name="reflection_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Reflection",
                property_name="reflection_id",
                constraint_query="CREATE CONSTRAINT reflection_id_unique FOR (r:Reflection) REQUIRE r.reflection_id IS UNIQUE"
            ),

            # Run uniqueness constraint
            Neo4jConstraint(
                constraint_name="run_id_unique",
                constraint_type=ConstraintType.UNIQUENESS,
                node_label="Run",
                property_name="run_id",
                constraint_query="CREATE CONSTRAINT run_id_unique FOR (run:Run) REQUIRE run.run_id IS UNIQUE"
            )
        ]

        return constraints

    def initialize_database_schema(self) -> Dict[str, Any]:
        """Initialize the complete Neo4j database schema with constraints"""

        start_time = datetime.utcnow()

        try:
            logger.info("Initializing Neo4j database schema...")

            # Create all constraints
            constraint_results = self.create_all_constraints()

            # Create default run if none exists
            if not self.current_run_id:
                default_run = self.create_run(
                    run_id="run_2025_pilot4",
                    run_name="2025 Pilot Phase 4",
                    description="Initial pilot run for Expert Council Betting System"
                )
                if default_run:
                    self.set_current_run("run_2025_pilot4")

            # Validate schema
            validation_results = self.validate_all_constraints()

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            schema_result = {
                'initialization_successful': True,
                'processing_time_ms': processing_time,
                'constraints_created': len([c for c in constraint_results if c['status'] == 'created']),
                'constraints_existing': len([c for c in constraint_results if c['status'] == 'exists']),
                'constraints_failed': len([c for c in constraint_results if c['status'] == 'failed']),
                'current_run_id': self.current_run_id,
                'validation_results': validation_results,
                'constraint_details': constraint_results
            }

            logger.info(f"Schema initialization completed in {processing_time:.1f}ms")
            return schema_result

        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                'initialization_successful': False,
                'processing_time_ms': processing_time,
                'error': str(e),
                'constraints_created': 0,
                'constraints_existing': 0,
                'constraints_failed': len(self.constraints),
                'current_run_id': None,
                'validation_results': [],
                'constraint_details': []
            }

    def create_all_constraints(self) -> List[Dict[str, Any]]:
        """Create all defined uniqueness constraints"""

        results = []

        for constraint in self.constraints:
            try:
                start_time = time.time()

                # Check if constraint already exists
                if self._constraint_exists(constraint.constraint_name):
                    constraint.status = ConstraintStatus.EXISTS
                    constraint.created_at = datetime.utcnow()

                    results.append({
                        'constraint_name': constraint.constraint_name,
                        'status': 'exists',
                        'node_label': constraint.node_label,
                        'property_name': constraint.property_name,
                        'processing_time_ms': 0
                    })
                    continue

                # Create the constraint
                success = self._execute_constraint_query(constraint.constraint_query)

                processing_time = (time.time() - start_time) * 1000
                self.constraint_creation_times.append(processing_time)

                if success:
                    constraint.status = ConstraintStatus.CREATED
                    constraint.created_at = datetime.utcnow()
                    self.operation_counts['constraints_created'] += 1

                    results.append({
                        'constraint_name': constraint.constraint_name,
                        'status': 'created',
                        'node_label': constraint.node_label,
                        'property_name': constraint.property_name,
                        'processing_time_ms': processing_time
                    })

                    logger.info(f"Created constraint: {constraint.constraint_name}")

                else:
                    constraint.status = ConstraintStatus.FAILED
                    constraint.error_message = "Constraint creation failed"
                    self.operation_counts['constraints_failed'] += 1

                    results.append({
                        'constraint_name': constraint.constraint_name,
                        'status': 'failed',
                        'node_label': constraint.node_label,
                        'property_name': constraint.property_name,
                        'processing_time_ms': processing_time,
                        'error': constraint.error_message
                    })

                    logger.error(f"Failed to create constraint: {constraint.constraint_name}")

            except Exception as e:
                constraint.status = ConstraintStatus.FAILED
                constraint.error_message = str(e)
                self.operation_counts['constraints_failed'] += 1

                results.append({
                    'constraint_name': constraint.constraint_name,
                    'status': 'failed',
                    'node_label': constraint.node_label,
                    'property_name': constraint.property_name,
                    'processing_time_ms': 0,
                    'error': str(e)
                })

                logger.error(f"Exception creating constraint {constraint.constraint_name}: {e}")

        return results

    def create_run(
        self,
        run_id: str,
        run_name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[RunNode]:
        """Create a new run node for provenance isolation"""

        try:
            # Check if run already exists
            if run_id in self.runs:
                logger.info(f"Run {run_id} already exists")
                return self.runs[run_id]

            # Create run node
            run_node = RunNode(
                run_id=run_id,
                run_name=run_name,
                description=description,
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )

            # Execute Neo4j query to create run node
            create_query = f"""
            CREATE (run:Run {{
                run_id: $run_id,
                run_name: $run_name,
                description: $description,
                created_at: $created_at,
                status: $status,
                metadata: $metadata
            }})
            RETURN run
            """

            parameters = {
                'run_id': run_id,
                'run_name': run_name,
                'description': description,
                'created_at': run_node.created_at.isoformat(),
                'status': run_node.status,
                'metadata': run_node.metadata
            }

            success = self._execute_query(create_query, parameters)

            if success:
                self.runs[run_id] = run_node
                self.operation_counts['runs_created'] += 1

                logger.info(f"Created run node: {run_id}")
                return run_node
            else:
                logger.error(f"Failed to create run node: {run_id}")
                return None

        except Exception as e:
            logger.error(f"Exception creating run {run_id}: {e}")
            return None

    def set_current_run(self, run_id: str) -> bool:
        """Set the current run for provenance scoping"""

        try:
            if run_id not in self.runs:
                logger.error(f"Run {run_id} does not exist")
                return False

            self.current_run_id = run_id
            logger.info(f"Set current run to: {run_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to set current run {run_id}: {e}")
            return False

    def link_decision_to_run(self, decision_id: str, run_id: Optional[str] = None) -> bool:
        """Link a decision to a run for provenance isolation"""

        try:
            target_run_id = run_id or self.current_run_id

            if not target_run_id:
                logger.error("No run ID specified and no current run set")
                return False

            if target_run_id not in self.runs:
                logger.error(f"Run {target_run_id} does not exist")
                return False

            # Create relationship query
            link_query = """
            MATCH (d:Decision {decision_id: $decision_id})
            MATCH (run:Run {run_id: $run_id})
            MERGE (d)-[:IN_RUN]->(run)
            RETURN d, run
            """

            parameters = {
                'decision_id': decision_id,
                'run_id': target_run_id
            }

            success = self._execute_query(link_query, parameters)

            if success:
                logger.debug(f"Linked decision {decision_id} to run {target_run_id}")
                return True
            else:
                logger.error(f"Failed to link decision {decision_id} to run {target_run_id}")
                return False

        except Exception as e:
            logger.error(f"Exception linking decision {decision_id} to run: {e}")
            return False

    def add_run_id_to_node(
        self,
        node_label: str,
        node_id: str,
        id_property: str,
        run_id: Optional[str] = None
    ) -> bool:
        """Add run_id property to a node for scoping"""

        try:
            target_run_id = run_id or self.current_run_id

            if not target_run_id:
                logger.error("No run ID specified and no current run set")
                return False

            # Update node with run_id property
            update_query = f"""
            MATCH (n:{node_label} {{{id_property}: $node_id}})
            SET n.run_id = $run_id
            RETURN n
            """

            parameters = {
                'node_id': node_id,
                'run_id': target_run_id
            }

            success = self._execute_query(update_query, parameters)

            if success:
                logger.debug(f"Added run_id {target_run_id} to {node_label} {node_id}")
                return True
            else:
                logger.error(f"Failed to add run_id to {node_label} {node_id}")
                return False

        except Exception as e:
            logger.error(f"Exception adding run_id to {node_label} {node_id}: {e}")
            return False

    def validate_all_constraints(self) -> List[ConstraintValidationResult]:
        """Validate all constraints by checking for violations"""

        validation_results = []

        for constraint in self.constraints:
            if constraint.status not in [ConstraintStatus.CREATED, ConstraintStatus.EXISTS]:
                continue

            try:
                start_time = time.time()

                # Create validation query
                validation_query = self._create_validation_query(constraint)

                # Execute validation
                violations = self._execute_validation_query(validation_query, constraint)

                processing_time = (time.time() - start_time) * 1000
                self.validation_times.append(processing_time)

                result = ConstraintValidationResult(
                    constraint_name=constraint.constraint_name,
                    is_valid=len(violations) == 0,
                    violation_count=len(violations),
                    sample_violations=violations[:5],  # First 5 violations as sample
                    validation_time=datetime.utcnow()
                )

                validation_results.append(result)
                self.operation_counts['validations_performed'] += 1

                if result.is_valid:
                    logger.debug(f"Constraint {constraint.constraint_name} is valid")
                else:
                    logger.warning(f"Constraint {constraint.constraint_name} has {result.violation_count} violations")

            except Exception as e:
                logger.error(f"Validation failed for constraint {constraint.constraint_name}: {e}")

                result = ConstraintValidationResult(
                    constraint_name=constraint.constraint_name,
                    is_valid=False,
                    violation_count=-1,  # Indicates validation error
                    sample_violations=[],
                    validation_time=datetime.utcnow()
                )
                validation_results.append(result)

        return validation_results

    def _constraint_exists(self, constraint_name: str) -> bool:
        """Check if a constraint already exists (mock implementation)"""

        try:
            # Mock constraint existence check
            # In production, would query Neo4j system database
            check_query = "SHOW CONSTRAINTS"

            # Mock response - assume some constraints might already exist
            existing_constraints = self._execute_system_query(check_query)

            return constraint_name in [c.get('name', '') for c in existing_constraints]

        except Exception as e:
            logger.error(f"Error checking constraint existence: {e}")
            return False

    def _execute_constraint_query(self, query: str) -> bool:
        """Execute a constraint creation query (mock implementation)"""

        try:
            # Mock constraint creation
            # In production, would use Neo4j driver
            if self.neo4j_client:
                # Real implementation would be:
                # with self.neo4j_client.session() as session:
                #     session.run(query)
                pass

            # Mock success (with occasional failures for testing)
            import random
            return random.random() > 0.1  # 90% success rate

        except Exception as e:
            logger.error(f"Constraint query execution failed: {e}")
            return False

    def _execute_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Execute a general Neo4j query (mock implementation)"""

        try:
            # Mock query execution
            # In production, would use Neo4j driver
            if self.neo4j_client:
                # Real implementation would be:
                # with self.neo4j_client.session() as session:
                #     result = session.run(query, parameters)
                #     return result.single() is not None
                pass

            # Mock success
            logger.debug(f"Executed query: {query[:50]}... with params: {list(parameters.keys())}")
            return True

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return False

    def _execute_system_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a system query (mock implementation)"""

        try:
            # Mock system query for constraint checking
            # In production, would query Neo4j system database

            # Return mock existing constraints
            mock_constraints = [
                {'name': 'expert_id_unique', 'type': 'UNIQUENESS'},
                {'name': 'team_id_unique', 'type': 'UNIQUENESS'}
            ]

            return mock_constraints

        except Exception as e:
            logger.error(f"System query execution failed: {e}")
            return []

    def _create_validation_query(self, constraint: Neo4jConstraint) -> str:
        """Create a query to validate constraint uniqueness"""

        # Create query to find duplicate values
        validation_query = f"""
        MATCH (n:{constraint.node_label})
        WITH n.{constraint.property_name} as prop_value, collect(n) as nodes
        WHERE size(nodes) > 1
        RETURN prop_value, size(nodes) as duplicate_count,
               [node in nodes | {{id: id(node), properties: properties(node)}}][0..5] as sample_nodes
        """

        return validation_query

    def _execute_validation_query(
        self,
        query: str,
        constraint: Neo4jConstraint
    ) -> List[Dict[str, Any]]:
        """Execute validation query and return violations"""

        try:
            # Mock validation query execution
            # In production, would execute against Neo4j

            # Mock some violations for testing
            if constraint.constraint_name == "decision_id_unique":
                return [
                    {
                        'prop_value': 'duplicate_decision_123',
                        'duplicate_count': 2,
                        'sample_nodes': [
                            {'id': 1001, 'properties': {'decision_id': 'duplicate_decision_123'}},
                            {'id': 1002, 'properties': {'decision_id': 'duplicate_decision_123'}}
                        ]
                    }
                ]

            # Most constraints are valid
            return []

        except Exception as e:
            logger.error(f"Validation query execution failed: {e}")
            return []

    def get_constraint_status(self) -> Dict[str, Any]:
        """Get status of all constraints"""

        try:
            constraint_summary = {}

            for constraint in self.constraints:
                constraint_summary[constraint.constraint_name] = {
                    'status': constraint.status.value,
                    'node_label': constraint.node_label,
                    'property_name': constraint.property_name,
                    'created_at': constraint.created_at.isoformat() if constraint.created_at else None,
                    'error_message': constraint.error_message
                }

            return {
                'constraints': constraint_summary,
                'total_constraints': len(self.constraints),
                'created_count': len([c for c in self.constraints if c.status == ConstraintStatus.CREATED]),
                'existing_count': len([c for c in self.constraints if c.status == ConstraintStatus.EXISTS]),
                'failed_count': len([c for c in self.constraints if c.status == ConstraintStatus.FAILED]),
                'current_run_id': self.current_run_id,
                'total_runs': len(self.runs)
            }

        except Exception as e:
            logger.error(f"Failed to get constraint status: {e}")
            return {'error': str(e)}

    def get_run_status(self) -> Dict[str, Any]:
        """Get status of all runs"""

        try:
            run_summary = {}

            for run_id, run_node in self.runs.items():
                run_summary[run_id] = {
                    'run_name': run_node.run_name,
                    'description': run_node.description,
                    'status': run_node.status,
                    'created_at': run_node.created_at.isoformat(),
                    'metadata': run_node.metadata,
                    'is_current': run_id == self.current_run_id
                }

            return {
                'runs': run_summary,
                'total_runs': len(self.runs),
                'current_run_id': self.current_run_id,
                'active_runs': len([r for r in self.runs.values() if r.status == 'active'])
            }

        except Exception as e:
            logger.error(f"Failed to get run status: {e}")
            return {'error': str(e)}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for constraint operations"""

        try:
            if not self.constraint_creation_times:
                return {
                    'total_operations': sum(self.operation_counts.values()),
                    'average_constraint_time_ms': 0,
                    'average_validation_time_ms': 0,
                    'operation_counts': self.operation_counts.copy(),
                    'constraints_status': self.get_constraint_status(),
                    'runs_status': self.get_run_status()
                }

            import numpy as np

            constraint_times = np.array(self.constraint_creation_times)
            validation_times = np.array(self.validation_times) if self.validation_times else np.array([0])

            return {
                'total_operations': sum(self.operation_counts.values()),
                'average_constraint_time_ms': float(np.mean(constraint_times)),
                'p95_constraint_time_ms': float(np.percentile(constraint_times, 95)),
                'max_constraint_time_ms': float(np.max(constraint_times)),
                'average_validation_time_ms': float(np.mean(validation_times)),
                'p95_validation_time_ms': float(np.percentile(validation_times, 95)),
                'operation_counts': self.operation_counts.copy(),
                'constraints_status': self.get_constraint_status(),
                'runs_status': self.get_run_status()
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}

    def drop_all_constraints(self) -> Dict[str, Any]:
        """Drop all constraints (for testing/cleanup)"""

        try:
            logger.warning("Dropping all constraints - this should only be used for testing!")

            dropped_count = 0
            failed_count = 0

            for constraint in self.constraints:
                if constraint.status in [ConstraintStatus.CREATED, ConstraintStatus.EXISTS]:
                    try:
                        drop_query = f"DROP CONSTRAINT {constraint.constraint_name}"
                        success = self._execute_constraint_query(drop_query)

                        if success:
                            constraint.status = ConstraintStatus.DROPPED
                            dropped_count += 1
                        else:
                            failed_count += 1

                    except Exception as e:
                        logger.error(f"Failed to drop constraint {constraint.constraint_name}: {e}")
                        failed_count += 1

            return {
                'dropped_count': dropped_count,
                'failed_count': failed_count,
                'total_constraints': len(self.constraints)
            }

        except Exception as e:
            logger.error(f"Failed to drop constraints: {e}")
            return {'error': str(e)}

    def clear_all_data(self) -> None:
        """Clear all data (for testing)"""
        self.runs.clear()
        self.current_run_id = None
        self.constraint_creation_times.clear()
        self.validation_times.clear()
        self.operation_counts = {
            'constraints_created': 0,
            'constraints_failed': 0,
            'runs_created': 0,
            'validations_performed': 0
        }

        # Reset constraint statuses
        for constraint in self.constraints:
            constraint.status = ConstraintStatus.PENDING
            constraint.created_at = None
            constraint.error_message = None
