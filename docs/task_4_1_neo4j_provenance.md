# Task 4.1: Neo4j Write-Behind Provenance Service - Implementation Guide

## Overview

Task 4.1 impleo4j Write-Behind Provenance Service that creates Decision, Assertion, Thought nodes and USED_IN, EVALUATED_AS, LEARNED_FROM relationships for complete provenance trails in the Expert Council Betting System.

## Implementation

### Core Service (`src/services/neo4j_provenance_service.py`)

The Neo4j Provenance Service provides comprehensive write-behind provenance tracking with:

1. **Decision Node Creation**: Expert decisions with game context
2. **Assertion Node Creation**: Individual predictions with details
3. **Thought Node Creation**: Episodic memories used in decisions
4. **Relationship Management**: USED_IN, EVALUATED_AS, LEARNED_FROM relationships
5. **Async Processing**: Write-behind with thread pool and retry logic

### Key Components

#### Provenance Trail Creation Flow
```
1. Expert makes decision on game
2. Create Expert, Game, Decision nodes
3. For each prediction:
   - Create Assertion node
   - Create HAS_ASSERTION relationship (Decision → Assertion)
   - For each memory used:
     - Create Thought node
     - Create USED_IN relationship (Assertion → Thought)
4. After grading:
   - Create EVALUATED_AS relationship (Assertion → Grade)
5. After learning:
   - Create LEARNED_FROM relationship (Expert → Game)
6. Link to run: IN_RUN relationship (Decision → Run)
```

#### Node Types and Properties

**Expert Node**
```python
{
    'expert_id': 'conservative_analyzer',
    'created_at': '2025-10-09T20:15:30.123456'
}
```

**Game Node**
```python
{
    'game_id': 'KC_vs_BUF_2025_W1',
    'created_at': '2025-10-09T20:15:30.123456'
}
```

**Decision Node**
```python
{
    'decision_id': 'decision_001',
    'expert_id': 'conservative_analyzer',
    'game_id': 'KC_vs_BUF_2025_W1',
    'created_at': '2025-10-09T20:15:30.123456'
}
```

**Assertion Node**
```python
{
    'assertion_id': 'assertion_001',
    'category': 'game_winner',
    'pred_type': 'binary',
    'value': True,
    'confidence': 0.8,
    'stake_units': 5.0,
    'created_at': '2025-10-09T20:15:30.123456'
}
```

**Thought Node**
```python
{
    'memory_id': 'memory_001',
    'content': 'KC has strong home field advantage in cold weather',
    'embedding_vector': [0.1, 0.2, ...],
    'similarity_score': 0.92,
    'recency_score': 0.8,
    'created_at': '2025-10-09T20:15:30.123456'
}
```

### Relationship Types and Properties

#### PREDICTED Relationship
```cypher
(Expert)-[:PREDICTED {
    game_id: 'KC_vs_BUF_2025_W1',
    timestamp: '2025-10-09T20:15:30.123456'
}]->(Decision)
```

#### HAS_ASSERTION Relationship
```cypher
(Decision)-[:HAS_ASSERTION {
    category: 'game_winner',
    confidence: 0.8
}]->(Assertion)
```

#### USED_IN Relationship
```cypher
(Assertion)-[:USED_IN {
    weight: 0.8,
    rank: 1,
    score: 0.92,
    category: 'game_winner'
}]->(Thought)
```

#### EVALUATED_AS Relationship
```cypher
(Assertion)-[:EVALUATED_AS {
    final_score: 0.95,
    exact_match: true,
    grading_method: 'binary_exact_brier',
    evaluated_at: '2025-10-09T20:15:30.123456'
}]->(Grade)
```

#### LEARNED_FROM Relationship
```cypher
(Expert)-[:LEARNED_FROM {
    learning_type: 'beta_calibration',
    update_id: 'update_001',
    category: 'game_winner',
    improvement: 0.05,
    learned_at: '2025-10-09T20:15:30.123456'
}]->(Game)
```

### Data Structures

#### ProvenanceNode
```python
@dataclass
class ProvenanceNode:
    node_id: str
    node_type: ProvenanceNodeType
    properties: Dict[str, Any]
    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ProvenanceOperationStatus = ProvenanceOperationStatus.PENDING
```

#### ProvenanceRelationship
```python
@dataclass
class ProvenanceRelationship:
    relationship_id: str
    relationship_type: ProvenanceRelationType
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ProvenanceOperationStatus = ProvenanceOperationStatus.PENDING
```

#### ProvenanceOperation
```python
@dataclass
class ProvenanceOperation:
    operation_id: str
    nodes: List[ProvenanceNode] = field(default_factory=list)
    relationships: List[ProvenanceRelationship] = field(default_factory=list)
    run_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: ProvenanceOperationStatus = ProvenanceOperationStatus.PENDING
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0
```

### Neo4j Integration

The service is designed for easy integration with real Neo4j drivers:

```python
def _create_node_in_neo4j(self, node: ProvenanceNode) -> bool:
    """Create a node in Neo4j"""

    try:
        if self.neo4j_client:
            # Real implementation:
            with self.neo4j_client.session() as session:
                query = f"""
                MERGE (n:{node.node_type.value} {{id: $id}})
                SET n += $properties
                SET n.run_id = $run_id
                """
                session.run(query,
                           id=node.node_id,
                           properties=node.properties,
                           run_id=node.run_id)
                return True

        # Mock implementation for testing
        return self._mock_node_creation()

    except Exception as e:
        logger.error(f"Failed to create node {node.node_id}: {e}")
        return False
```

### Provenance Queries

#### Complete Provenance Trail
```cypher
MATCH (d:Decision {decision_id: $decision_id})
OPTIONAL MATCH (d)-[:HAS_ASSERTION]->(a:Assertion)
OPTIONAL MATCH (a)-[:USED_IN]->(t:Thought)
OPTIONAL MATCH (a)-[:EVALUATED_AS]->(g)
RETURN d, collect(a) as assertions, collect(t) as thoughts
```

#### Why Lineage Query
```cypher
MATCH (a:Assertion {assertion_id: $assertion_id})-[:USED_IN]->(t:Thought)
RETURN t.memory_id as memory_id, t.content as content,
       t.similarity_score as score
ORDER BY score DESC
```

#### Run-Scoped Provenance
```cypher
MATCH (d:Decision {run_id: $run_id})
MATCH (d)-[:HAS_ASSERTION]->(a:Assertion)
MATCH (a)-[:USED_IN]->(t:Thought)
RETURN d, a, t
```

## API Methods

### Core Provenance Methods

- `create_decision_provenance()`: Create complete provenance trail for expert decision
- `create_evaluation_provenance()`: Create provenance for assertion evaluation/grading
- `create_learning_provenance()`: Create provenance for learning updates and reflections

### Query Methods

- `get_provenance_trail()`: Get complete provenance trail for a decision
- `query_why_lineage()`: Query 'why' lineage for an assertion
- `get_operation_status()`: Get status of a specific operation

### Monitoring Methods

- `get_performance_metrics()`: Get performance metrics for provenance operations
- `get_recent_operations()`: Get recent operations with status
- `update_config()`: Update service configuration

### Internal Methods

- `_create_expert_node()`: Create Expert node
- `_create_game_node()`: Create Game node
- `_create_decision_node()`: Create Decision node
- `_create_assertion_provenance()`: Create Assertion node and relationships
- `_create_thought_node()`: Create Thought (memory) node
- `_create_relationship()`: Create provenance relationship

## Integration Points

### With Neo4j Constraints Service (Task 4.0)
- Uses constraint foundation for node uniqueness
- Leverages run scoping for provenance isolation
- Integrates with current run tracking

### With Grading Service (Task 3.1)
- Creates EVALUATED_AS relationships from grading results
- Links assertions to their evaluation outcomes
- Tracks grading method and accuracy scores

### With Learning Service (Task 3.3)
- Creates LEARNED_FROM relationships from learning updates
- Links experts to games they learned from
- Tracks learning types and improvements

### With Reflection Service (Task 3.4)
- Creates REFLECTS_ON relationships from reflections
- Links reflections to games and outcomes
- Tracks reflection insights and lessons

## Performance Characteristics

- **Async Processing**: Non-blocking write-behind with thread pool
- **Batch Operations**: Configurable batch size for high-volume scenarios
- **Retry Logic**: Exponential backoff for transient failures
- **Memory Efficiency**: Lightweight operation tracking
- **Scalability**: Designed for production Neo4j clusters

## Testing

Comprehensive test coverage includes:
- Service initialization and configuration
- Node creation (Expert, Game, Decision, Assertion, Thought)
- Relationship creation (PREDICTED, HAS_ASSERTION, USED_IN, EVALUATED_AS, LEARNED_FROM)
- Complete decision provenance trail creation
- Evaluation and learning provenance tracking
- Provenance trail and why lineage querying
- Operation status tracking and monitoring
- Performance metrics and analytics
- Async processing with retry logic
- Configuration management and updates

## Next Steps

1. **Neo4j Driver Integration**: Connect to real Neo4j database with authentication
2. **Idempotent Merge Logic**: Implement task 4.2 for reliable writes
3. **Service Integration**: Connect to grading, learning, and reflection services
4. **Batch Processing**: Optimize for high-volume provenance operations
5. **Production Deployment**: Deploy with Neo4j cluster configuration

## Requirements Satisfied

✅ **2.7 - Neo4j provenance (write-behind)**
- Decision, Assertion, Thought node creation
- USED_IN, EVALUATED_AS, LEARNED_FROM relationships
- Complete provenance trails with run scoping
- Write-behind processing with async operations
- Provenance querying and lineage tracking
- Performance monitoring and error handling
