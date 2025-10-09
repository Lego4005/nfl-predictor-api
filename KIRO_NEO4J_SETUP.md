# Kiro → Neo4j Setup Guide

**Quick setup guide for Kiro AI assistant to access Neo4j graph database**

---

## ✅ What's Ready

✓ **Neo4j 5.25.1** running in Docker (container: `nfl-neo4j`)
✓ **15 Expert nodes** initialized
✓ **32 NFL Team nodes** initialized
✓ **Python service** created (`src/services/neo4j_service.py`)
✓ **Example script** ready (`scripts/neo4j_usage_example.py`)
✓ **Full documentation** (`docs/NEO4J_ACCESS_GUIDE.md`)

---

## 🚀 Quick Start for Kiro

### Option 1: Use Existing Virtual Environment (Recommended)

```bash
# If venv exists, activate it
source venv/bin/activate  # or source env/bin/activate

# Install Neo4j driver
pip install neo4j==5.25.0

# Test connection
python scripts/neo4j_usage_example.py
```

### Option 2: Create New Virtual Environment

```bash
cd /home/iris/code/experimental/nfl-predictor-api

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Install all requirements (includes neo4j)
pip install -r requirements.txt

# Test Neo4j
python scripts/neo4j_usage_example.py
```

### Option 3: Use pipx (Isolated)

```bash
# Install pipx if needed
brew install pipx

# Install neo4j in isolated environment
pipx install neo4j
```

---

## 🔌 Connection Details

```python
# Already configured in .env
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=nflpredictor123
```

---

## 💻 Kiro Usage Examples

### Minimal Example

```python
from services.neo4j_service import get_neo4j_service

neo4j = get_neo4j_service()

# List experts
experts = neo4j.list_experts()
print(f"Found {len(experts)} experts")

# Get specific expert
expert = neo4j.get_expert("momentum_rider")
print(expert)

neo4j.close()
```

### Training Integration

```python
# In Kiro's training script
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
# Track which memories influenced predictions
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

---

## 🧪 Test Neo4j Access

### Method 1: Python Script

```bash
python scripts/neo4j_usage_example.py
```

Expected output:
```
============================================================
Neo4j Expert Learning System - Usage Example
============================================================

1. Health Check
----------------------------------------
✓ Neo4j connection healthy

2. List All Experts
----------------------------------------
Found 15 experts:
  - The Analyst (conservative_analyzer)
  - The Gambler (risk_taking_gambler)
  ...
```

### Method 2: Direct Cypher

```bash
docker exec nfl-neo4j cypher-shell -u neo4j -p nflpredictor123 \
  "MATCH (e:Expert) RETURN e.name LIMIT 5"
```

### Method 3: Browser

Open http://localhost:7475

Login: `neo4j` / `nflpredictor123`

---

## 📊 Database Schema for Kiro

### Nodes

**Expert (15 nodes)**
```cypher
(:Expert {
  id: "momentum_rider",
  name: "The Rider",
  personality: "trend_following",
  decision_style: "ride_streaks"
})
```

**Team (32 nodes)**
```cypher
(:Team {
  id: "KC",
  name: "Kansas City Chiefs",
  division: "AFC West",
  conference: "AFC"
})
```

**Game (created during training)**
```cypher
(:Game {
  id: "KC_BUF_2024_W10",
  home_team: "KC",
  away_team: "BUF",
  season: 2024,
  week: 10,
  date: date("2024-10-13")
})
```

**Memory (created during training)**
```cypher
(:Memory {
  id: "mem_12345",
  type: "contextual",
  content: "Cold weather reduces scoring"
})
```

### Relationships

**PREDICTED** (Expert → Game)
```cypher
-[:PREDICTED {
  winner: "KC",
  confidence: 0.75,
  win_probability: 0.65,
  reasoning: "Home field advantage",
  accuracy: 1.0,  // Set after game
  created_at: datetime()
}]->
```

**USED_IN** (Memory → Game)
```cypher
-[:USED_IN {
  expert_id: "weather_specialist",
  influence_weight: 0.85,
  retrieval_rank: 1
}]->
```

---

## 🎯 Kiro Training Workflow

### 1. Initialize Connection

```python
from services.neo4j_service import get_neo4j_service
neo4j = get_neo4j_service()

if not neo4j.health_check():
    raise Exception("Neo4j connection failed")
```

### 2. Process Training Data

```python
for game in historical_games:
    # Create game node
    neo4j.create_game(
        game_id=game.id,
        home_team=game.home,
        away_team=game.away,
        season=game.season,
        week=game.week,
        game_date=game.date
    )

    # Get predictions from each expert
    for expert_type in experts:
        prediction = expert.predict(game)

        # Store prediction
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

### 3. Analyze Results

```python
# Get expert performance
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

### 4. Close Connection

```python
neo4j.close()
```

---

## 🛠 Docker Management

```bash
# Check status
docker ps | grep nfl-neo4j

# View logs
docker logs nfl-neo4j

# Restart
docker restart nfl-neo4j

# Stop
docker stop nfl-neo4j

# Start
docker start nfl-neo4j
```

---

## 📚 Full Documentation

**Complete guide**: `docs/NEO4J_ACCESS_GUIDE.md`

**Python service**: `src/services/neo4j_service.py`

**Example script**: `scripts/neo4j_usage_example.py`

---

## 🐛 Troubleshooting

### Neo4j not running?

```bash
# Check container
docker ps -a | grep neo4j

# Start if stopped
docker-compose -f docker-compose.neo4j.yml up -d
```

### Can't import neo4j module?

```bash
# Activate virtual environment first
source venv/bin/activate

# Then install
pip install neo4j==5.25.0
```

### Connection refused?

```bash
# Check if Neo4j is healthy
docker exec nfl-neo4j cypher-shell -u neo4j -p nflpredictor123 "RETURN 1"
```

---

**Kiro has full access to Neo4j!** 🚀

The graph database is ready to track:
- Expert predictions and accuracy
- Team matchup history
- Memory influence on predictions
- Expert learning progression

Start training with `python scripts/neo4j_usage_example.py`
