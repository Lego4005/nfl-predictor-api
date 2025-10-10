# Neo4j Graph Database Integration

<cite>
**Referenced Files in This Document**
- [neo4j_service.py](file://src/services/neo4j_service.py) - *Added in commit 498f641f*
- [docker-compose.neo4j.yml](file://docker-compose.neo4j.yml) - *Added in commit c50be93b*
- [KIRO_NEO4J_SETUP.md](file://KIRO_NEO4J_SETUP.md) - *Updated in commit 38aaba92*
- [NEO4J_ACCESS_GUIDE.md](file://docs/NEO4J_ACCESS_GUIDE.md) - *Added in commit 11af38e8*
- [neo4j_usage_example.py](file://scripts/neo4j_usage_example.py) - *Added in commit 06bac56b*
- [db_state_review.md](file://db_state_review.md) - *Updated in commit c50be93b*
</cite>

## Update Summary
**Changes Made**
- Added comprehensive documentation for Neo4j integration in the NFL predictor system
- Documented purpose, implementation, and usage patterns for decision provenance tracking
- Included setup instructions, API interfaces, and integration examples
- Added troubleshooting guidance and connection details
- Integrated content from multiple source files into cohesive documentation

## Table of Contents
- [Neo4j Graph Database Integration](#neo4j-graph-database-integration)
  - [Purpose and Architecture](#purpose-and-architecture)
  - [Setup and Configuration](#setup-and-configuration)
  - [API Interface](#api-interface)
  - [Integration with Supabase System](#integration-with-supabase-system)
  - [Usage Examples](#usage-examples)
  - [Troubleshooting](#troubleshooting)

## Purpose and Architecture
The Neo4j graph database integration serves as the core system for decision provenance tracking and expert memory retrieval within the NFL predictor system. It enables comprehensive tracking of AI expert predictions, their reasoning, and performance over time.

The architecture leverages Neo4j's graph capabilities to model relationships between experts, games, predictions, and memories. This allows for sophisticated analysis of prediction patterns, expert performance, and memory influence on decision-making.

### Core Components
- **Expert Nodes**: Represent AI prediction experts with personality and decision style attributes
- **Game Nodes**: Store NFL game metadata including teams, season, and week
- **Prediction Relationships**: Connect experts to games with prediction details and confidence metrics
- **Memory Nodes**: Capture learned patterns and contextual knowledge used in predictions
- **Team Nodes**: Store NFL team information and divisional relationships

**Section sources**
- [KIRO_NEO4J_SETUP.md](file://KIRO_NEO4J_SETUP.md) - *Updated in commit 38aaba92*
- [NEO4J_ACCESS_GUIDE.md](file://docs/NEO4J_ACCESS_GUIDE.md) - *Added in commit 11af38e8*

## Setup and Configuration
### Docker Configuration
The Neo4j instance is managed through Docker Compose with optimized settings for the prediction system.

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.25-community
    container_name: nfl-neo4j
    ports:
      - "7475:7474"  # HTTP
      - "7688:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/nflpredictor123
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_memory_pagecache_size=1G
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - ./neo4j_bootstrap.cypher:/var/lib/neo4j/import/bootstrap.cypher
```

### Connection Details
The system uses the following connection parameters:
- **URI**: `bolt://localhost:7688`
- **User**: `neo4j`
- **Password**: `nflpredictor123`
- **HTTP Browser**: `http://localhost:7475`

These are configured in environment variables:
```bash
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=nflpredictor123
```

### Initialization
To start the Neo4j service:
```bash
docker-compose -f docker-compose.neo4j.yml up -d
```

The container includes APOC and Graph Data Science plugins for advanced graph operations and data import/export capabilities.

**Section sources**
- [docker-compose.neo4j.yml](file://docker-compose.neo4j.yml) - *Added in commit c50be93b*
- [KIRO_NEO4J_SETUP.md](file://KIRO_NEO4J_SETUP.md) - *Updated in commit 38aaba92*

## API Interface
The Neo4j service provides a Python interface through the `Neo4jService` class, which abstracts the underlying graph database operations.

### Service Initialization
```python
from services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()
if not neo4j.health_check():
    raise Exception("Neo4j connection failed")
```

### Core Methods
#### Expert Operations
- `get_expert(expert_id)`: Retrieve expert details by ID
- `list_experts()`: Get all registered experts
- `list_teams(division=None)`: Retrieve teams, optionally filtered by division

#### Game and Prediction Management
- `create_game(game_id, home_team, away_team, season, week, game_date)`: Create a game node
- `record_prediction(expert_id, game_id, winner, confidence, win_probability, reasoning)`: Record an expert's prediction
- `get_expert_predictions(expert_id, limit=10)`: Retrieve recent predictions by an expert

#### Memory and Provenance Tracking
- `record_memory_usage(memory_id, game_id, expert_id, influence_weight, retrieval_rank)`: Track memory usage in predictions
- `get_prediction_provenance(expert_id, game_id)`: Retrieve memories that influenced a specific prediction

#### Query Execution
- `execute_query(query, parameters)`: Execute read queries and return results
- `execute_write(query, parameters)`: Execute write transactions and return summary

### Connection Management
The service uses a singleton pattern with context managers for efficient connection handling:
```python
@contextmanager
def session(self) -> Session:
    driver = self.connect()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()
```

**Section sources**
- [neo4j_service.py](file://src/services/neo4j_service.py) - *Added in commit 498f641f*
- [NEO4J_ACCESS_GUIDE.md](file://docs/NEO4J_ACCESS_GUIDE.md) - *Added in commit 11af38e8*

## Integration with Supabase System
The Neo4j integration complements the existing Supabase system by providing specialized graph-based storage for decision provenance and expert memory, while Supabase handles relational data and vector storage.

### Data Flow Pattern
1. **Prediction Generation**: Experts generate predictions using Supabase-stored historical data
2. **Provenance Recording**: Prediction details and reasoning are stored in Neo4j
3. **Memory Formation**: Significant prediction outcomes create memories in Neo4j
4. **Retrieval**: Future predictions query Neo4j for relevant memories and expert performance history
5. **Analysis**: Cross-system queries combine Supabase metrics with Neo4j relationship data

### Hybrid Architecture Benefits
- **Supabase**: Optimized for structured data, vector similarity search, and real-time subscriptions
- **Neo4j**: Optimized for relationship traversal, path finding, and graph algorithms
- **Combined**: Enables comprehensive analysis of prediction patterns and expert evolution

The integration follows a hybrid orchestration pattern where the Expert Council Betting System coordinates between both databases, using Neo4j for decision traceability and Supabase for operational data storage.

**Section sources**
- [KIRO_NEO4J_SETUP.md](file://KIRO_NEO4J_SETUP.md) - *Updated in commit 38aaba92*
- [NEO4J_ACCESS_GUIDE.md](file://docs/NEO4J_ACCESS_GUIDE.md) - *Added in commit 11af38e8*

## Usage Examples
### Basic Connection and Query
```python
from services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# List all experts
experts = neo4j.list_experts()
print(f"Found {len(experts)} experts")

# Get specific expert
expert = neo4j.get_expert("momentum_rider")
print(expert)

neo4j.close()
```

### Training Integration
```python
# In training script
from services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# For each game prediction
neo4j.create_game(
    game_id="KC_BUF_2024_W10",
    home_team="KC",
    away_team="BUF",
    season=2024,
    week=10,
    game_date="2024-10-13"
)

neo4j.record_prediction(
    expert_id="conservative_analyzer",
    game_id="KC_BUF_2024_W10",
    winner="KC",
    confidence=0.75,
    win_probability=0.65,
    reasoning="Home field advantage and defensive strength"
)

neo4j.close()
```

### Memory Tracking
```python
# Track memory influence
neo4j.record_memory_usage(
    memory_id="mem_12345",
    game_id="KC_BUF_2024_W10",
    expert_id="weather_specialist",
    influence_weight=0.85,
    retrieval_rank=1
)

# Retrieve prediction provenance
memories = neo4j.get_prediction_provenance(
    expert_id="weather_specialist",
    game_id="KC_BUF_2024_W10"
)
```

### Performance Analysis
```python
# Analyze expert accuracy
query = """
MATCH (e:Expert)-[p:PREDICTED]->(g:Game)
WHERE g.season = 2024
RETURN e.name,
       AVG(p.accuracy) as avg_accuracy,
       COUNT(p) as predictions
ORDER BY avg_accuracy DESC
"""
results = neo4j.execute_query(query)
```

**Section sources**
- [neo4j_usage_example.py](file://scripts/neo4j_usage_example.py) - *Added in commit 06bac56b*
- [KIRO_NEO4J_SETUP.md](file://KIRO_NEO4J_SETUP.md) - *Updated in commit 38aaba92*

## Troubleshooting
### Connection Issues
**Symptoms**: Connection refused, timeout errors
**Solutions**:
```bash
# Check container status
docker ps | grep nfl-neo4j

# Start if stopped
docker-compose -f docker-compose.neo4j.yml up -d

# Test connection
docker exec nfl-neo4j cypher-shell -u neo4j -p nflpredictor123 "RETURN 1"
```

### Authentication Problems
**Symptoms**: Authentication failed errors
**Solutions**:
- Verify credentials in `.env` file match container configuration
- Reset password: `docker exec nfl-neo4j neo4j-admin set-initial-password nflpredictor123`

### Python Module Import Errors
**Symptoms**: `ModuleNotFoundError: No module named 'neo4j'`
**Solutions**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install Neo4j driver
pip install neo4j==5.25.0
```

### Performance Issues
**Symptoms**: Slow query responses
**Solutions**:
- Verify memory settings in `docker-compose.neo4j.yml`
- Check for unindexed queries
- Monitor container resource usage

### Data Verification
Test the setup with the example script:
```bash
python scripts/neo4j_usage_example.py
```

Expected output includes connection health check, expert listing, and successful operation execution.

**Section sources**
- [db_state_review.md](file://db_state_review.md) - *Updated in commit c50be93b*
- [KIRO_NEO4J_SETUP.md](file://KIRO_NEO4J_SETUP.md) - *Updated in commit 38aaba92*
- [NEO4J_ACCESS_GUIDE.md](file://docs/NEO4J_ACCESS_GUIDE.md) - *Added in commit 11af38e8*