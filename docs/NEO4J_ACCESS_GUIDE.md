# Neo4j Access Guide for Kiro & Training Scripts

**Complete guide for accessing Neo4j graph database in the NFL Expert Learning System**

---

## 🔌 Connection Details

**Container**: `nfl-neo4j`
**Version**: Neo4j 5.25.1 Community Edition
**Status**: Running and healthy ✓

### Ports
- **HTTP Browser**: http://localhost:7475
- **Bolt Protocol**: bolt://localhost:7688

### Credentials
```bash
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=nflpredictor123
NEO4J_HTTP_URL=http://localhost:7475
```

---

## 📦 Installation

### 1. Install Python Driver

```bash
# Install from requirements
pip install -r requirements.txt

# Or install directly
pip install neo4j==5.25.0
```

### 2. Verify Connection

```bash
# Test Neo4j is running
docker exec nfl-neo4j cypher-shell -u neo4j -p nflpredictor123 "RETURN 1"

# Run example script
python scripts/neo4j_usage_example.py
```

---

## 🐍 Python Usage

### Quick Start

```python
from services.neo4j_service import get_neo4j_service

# Get service instance
neo4j = get_neo4j_service()

# Health check
if neo4j.health_check():
    print("Connected!")

# List all experts
experts = neo4j.list_experts()
for expert in experts:
    print(f"{expert['name']} - {expert['personality']}")

# Close when done
neo4j.close()
```

### Complete Example

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.neo4j_service import Neo4jService
from dotenv import load_dotenv

load_dotenv()

# Initialize service
neo4j = Neo4jService()

# Check connection
if not neo4j.health_check():
    print("Failed to connect to Neo4j")
    exit(1)

# Get expert
expert = neo4j.get_expert("momentum_rider")
print(f"Expert: {expert['name']}")

# Create game
neo4j.create_game(
    game_id="KC_DEN_2024_W1",
    home_team="KC",
    away_team="DEN",
    season=2024,
    week=1,
    game_date="2024-09-05"
)

# Record prediction
neo4j.record_prediction(
    expert_id="momentum_rider",
    game_id="KC_DEN_2024_W1",
    winner="KC",
    confidence=0.75,
    win_probability=0.68,
    reasoning="Chiefs 3-game win streak creates strong momentum"
)

# Get predictions
predictions = neo4j.get_expert_predictions("momentum_rider", limit=10)
for pred in predictions:
    print(f"{pred['home_team']} vs {pred['away_team']}: {pred['predicted_winner']}")

neo4j.close()
```

---

## 🔍 Common Operations

### 1. Expert Operations

```python
# Get all experts
experts = neo4j.list_experts()

# Get specific expert
expert = neo4j.get_expert("conservative_analyzer")

# Custom expert query
query = """
MATCH (e:Expert)
WHERE e.decision_style = 'data_driven'
RETURN e.name, e.id
"""
results = neo4j.execute_query(query)
```

### 2. Team Operations

```python
# Get all teams
teams = neo4j.list_teams()

# Filter by division
afc_west = neo4j.list_teams(division="AFC West")

# Get specific team
team = neo4j.get_team("KC")
```

### 3. Game & Prediction Operations

```python
# Create game
neo4j.create_game(
    game_id="KC_BUF_2024_W10",
    home_team="KC",
    away_team="BUF",
    season=2024,
    week=10,
    game_date="2024-10-13"
)

# Record prediction
neo4j.record_prediction(
    expert_id="contrarian_rebel",
    game_id="KC_BUF_2024_W10",
    winner="BUF",
    confidence=0.82,
    win_probability=0.58,
    reasoning="Public heavily on Chiefs - fade opportunity"
)

# Get expert's predictions
predictions = neo4j.get_expert_predictions("contrarian_rebel", limit=20)
```

### 4. Memory & Provenance

```python
# Record memory usage
neo4j.record_memory_usage(
    memory_id="mem_12345",
    game_id="KC_BUF_2024_W10",
    expert_id="weather_specialist",
    influence_weight=0.85,
    retrieval_rank=1
)

# Get prediction provenance
memories = neo4j.get_prediction_provenance(
    expert_id="weather_specialist",
    game_id="KC_BUF_2024_W10"
)
```

### 5. Custom Queries

```python
# Expert accuracy by team
query = """
MATCH (e:Expert {id: $expert_id})-[p:PREDICTED]->(g:Game)
WHERE g.home_team = $team_id OR g.away_team = $team_id
RETURN AVG(p.accuracy) as avg_accuracy, COUNT(p) as prediction_count
"""
results = neo4j.execute_query(query, {
    "expert_id": "conservative_analyzer",
    "team_id": "KC"
})

# Team rivalry history
query = """
MATCH (t1:Team {id: $team1})-[f:FACED]->(t2:Team {id: $team2})
RETURN f.games, f.wins, f.losses, f.avg_margin
"""
rivalry = neo4j.execute_query(query, {"team1": "KC", "team2": "DEN"})
```

---

## 🧪 Testing & Development

### Run Example Script

```bash
python scripts/neo4j_usage_example.py
```

### Direct Cypher Shell

```bash
# Access Neo4j shell
docker exec -it nfl-neo4j cypher-shell -u neo4j -p nflpredictor123

# Example queries
MATCH (e:Expert) RETURN e.name, e.personality LIMIT 5;
MATCH (t:Team) WHERE t.division = 'AFC West' RETURN t.name;
MATCH (e:Expert)-[p:PREDICTED]->(g:Game) RETURN e.name, count(p) as predictions;
```

### Neo4j Browser

Open http://localhost:7475 in your browser

**Login credentials:**
- Username: `neo4j`
- Password: `nflpredictor123`

---

## 🎯 Use Cases for Kiro

### 1. Training Script Integration

```python
# In your training script
from services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# Record each prediction during training
for expert_type in expert_types:
    prediction = expert.predict(game_data)

    # Store in Neo4j
    neo4j.record_prediction(
        expert_id=expert_type,
        game_id=game.id,
        winner=prediction.winner,
        confidence=prediction.confidence,
        win_probability=prediction.win_prob,
        reasoning=prediction.reasoning
    )

    # Track memory usage
    for memory in prediction.memories_used:
        neo4j.record_memory_usage(
            memory_id=memory.id,
            game_id=game.id,
            expert_id=expert_type,
            influence_weight=memory.weight,
            retrieval_rank=memory.rank
        )
```

### 2. Expert Performance Analysis

```python
# Analyze expert accuracy patterns
query = """
MATCH (e:Expert)-[p:PREDICTED]->(g:Game)
WHERE g.season = 2024
WITH e,
     AVG(p.accuracy) as avg_accuracy,
     COUNT(p) as total_predictions,
     SUM(CASE WHEN p.accuracy = 1.0 THEN 1 ELSE 0 END) as correct_predictions
RETURN e.name as expert,
       avg_accuracy,
       total_predictions,
       correct_predictions,
       toFloat(correct_predictions) / total_predictions as win_rate
ORDER BY avg_accuracy DESC
"""
results = neo4j.execute_query(query)
```

### 3. Memory Influence Tracking

```python
# Find which memories most influence predictions
query = """
MATCH (m:Memory)-[u:USED_IN]->(g:Game)
WHERE g.season = 2024
WITH m, AVG(u.influence_weight) as avg_influence, COUNT(u) as usage_count
WHERE usage_count > 5
RETURN m.id, m.type, m.content, avg_influence, usage_count
ORDER BY avg_influence DESC
LIMIT 20
"""
influential_memories = neo4j.execute_query(query)
```

---

## 🛠 Database Management

### Docker Commands

```bash
# Start Neo4j
docker-compose -f docker-compose.neo4j.yml up -d

# Stop Neo4j
docker-compose -f docker-compose.neo4j.yml down

# View logs
docker logs nfl-neo4j

# Check status
docker ps | grep neo4j

# Restart
docker restart nfl-neo4j
```

### Backup & Restore

```bash
# Export data
docker exec nfl-neo4j cypher-shell -u neo4j -p nflpredictor123 \
  "CALL apoc.export.cypher.all('/var/lib/neo4j/import/backup.cypher', {})"

# Import data
docker exec nfl-neo4j cypher-shell -u neo4j -p nflpredictor123 \
  < /path/to/backup.cypher
```

---

## 📊 Database Schema

### Node Types

**Expert** - AI prediction expert personalities
```
Properties: id, name, personality, decision_style
```

**Team** - NFL teams
```
Properties: id, name, division, conference
```

**Game** - NFL games
```
Properties: id, home_team, away_team, season, week, date
```

**Memory** - Expert learning memories
```
Properties: id, type, content, created_at
```

### Relationship Types

**PREDICTED** - Expert → Game
```
Properties: winner, confidence, win_probability, reasoning, accuracy, created_at
```

**USED_IN** - Memory → Game
```
Properties: expert_id, influence_weight, retrieval_rank
```

**FACED** - Team → Team
```
Properties: games, wins, losses, last_game, avg_margin
```

**KNOWS_TEAM** - Expert → Team
```
Properties: knowledge_strength, games_analyzed, accuracy_rate, confidence
```

**LEARNED_FROM** - Expert → Game
```
Properties: lesson, confidence_change, memory_formed
```

---

## 🐛 Troubleshooting

### Connection Issues

```python
# Check if Neo4j is running
docker ps | grep nfl-neo4j

# Test connection
from services.neo4j_service import Neo4jService
neo4j = Neo4jService()
print(neo4j.health_check())
```

### Environment Variables

Ensure `.env` file has:
```bash
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=nflpredictor123
```

### Common Errors

**Connection Refused**:
- Check Neo4j container is running: `docker ps`
- Verify port 7688 is open: `netstat -an | grep 7688`

**Authentication Failed**:
- Verify credentials in `.env` match container
- Reset password: `docker exec nfl-neo4j neo4j-admin set-initial-password nflpredictor123`

---

## 📚 Additional Resources

- **Neo4j Python Driver Docs**: https://neo4j.com/docs/python-manual/current/
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/current/
- **Neo4j Browser Guide**: http://localhost:7475/browser/

---

**Neo4j 5.25.1 is ready for Kiro and training scripts!** 🚀
