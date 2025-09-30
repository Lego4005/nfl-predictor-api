# 🏗️ Backtest System Architecture Analysis

## Current Expert System Design

### Input Format: `UniversalGameData`
Your experts expect a structured dataclass:

```python
@dataclass
class UniversalGameData:
    # Required fields
    home_team: str
    away_team: str
    game_time: str
    location: str

    # Optional dicts (all default to {})
    weather: Dict[str, Any]           # {temperature, wind_speed, conditions}
    injuries: Dict[str, List[Dict]]   # {home: [...], away: [...]}
    team_stats: Dict[str, Dict]       # {home: {...}, away: {...}}
    line_movement: Dict[str, Any]     # {opening_line, current_line, public_percentage}
    public_betting: Dict[str, Any]
    recent_news: List[Dict]
    head_to_head: Dict[str, Any]
    coaching_info: Dict[str, Any]
```

### Expert Structure: Stateful Objects
- Each expert is an instance of `PersonalityDrivenExpert`
- They maintain internal state (personality, memory, decision history)
- They have optional `memory_service` for Supabase persistence
- Prediction method: `make_personality_driven_prediction(universal_data) -> Dict`

### Data Flow
```
NFLverse CSV → Parse to UniversalGameData → Expert.predict() → Store Memory → Next Week
```

---

## Mapping NFLverse Data to UniversalGameData

### Available NFLverse Datasets:
1. **play_by_play.csv** - Every play, EPA, CPOE, success rate
2. **weekly_stats.csv** - Team/player performance by week
3. **standings.csv** - Wins, losses, point differential
4. **schedules.csv** - Game dates, scores, results

### Required Transformations:

```python
def nflverse_to_universal_game_data(
    game_row,           # From schedules.csv
    weekly_stats_home,  # From weekly_stats.csv (home team)
    weekly_stats_away,  # From weekly_stats.csv (away team)
    standings_home,     # From standings.csv (home team)
    standings_away      # From standings.csv (away team)
) -> UniversalGameData:

    return UniversalGameData(
        home_team=game_row['home_team'],
        away_team=game_row['away_team'],
        game_time=game_row['gameday'],
        location=game_row['location'] if 'location' in game_row else game_row['home_team'],

        # Team stats from cumulative performance up to this week
        team_stats={
            'home': {
                'offensive_yards_per_game': weekly_stats_home['yards_per_game'],
                'points_per_game': weekly_stats_home['points_per_game'],
                'turnovers_per_game': weekly_stats_home['turnovers_per_game'],
                'third_down_pct': weekly_stats_home['third_down_conversion_pct'],
                'red_zone_pct': weekly_stats_home['red_zone_td_pct'],
                # Add EPA, CPOE, etc.
            },
            'away': {
                # Same stats for away team
            }
        },

        # Minimal required fields (can enhance later)
        weather={},  # NFLverse doesn't have weather
        injuries={'home': [], 'away': []},  # NFLverse doesn't have injuries
        line_movement={},  # NFLverse doesn't have betting lines
        public_betting={},
        recent_news=[],
        head_to_head={},
        coaching_info={}
    )
```

---

## Which Statistics Do Your Experts Actually Use?

Looking at `personality_driven_experts.py`, I see your experts call:
```python
def process_through_personality_lens(self, universal_data: UniversalGameData) -> Dict[str, float]
```

This returns factor weights. Let me check what factors are actually computed...

### Core Factors Your Experts Use:
Based on `ConservativeAnalyzer` and other expert implementations, they typically weight:

1. **Point Differential** (from standings)
2. **Offensive Performance** (yards/game, points/game)
3. **Defensive Performance** (yards allowed, points allowed)
4. **Turnover Differential**
5. **Home Field Advantage** (implicit from home/away)
6. **Recent Form** (last 3 games performance)
7. **Head-to-Head History** (if available)

### Minimum NFLverse Data Required:
- ✅ **schedules.csv**: Game results, scores, home/away
- ✅ **weekly_stats.csv**: Yards, points, turnovers (aggregated week-by-week)
- ⚠️ **Weather, injuries, betting**: Not in NFLverse (can mock or leave empty)

---

## Backtest System Design

### Option 1: Local Testing (RECOMMENDED)
**Architecture**:
```
Local SQLite DB ← Backtest Harness → Supabase (for validation)
     ↓
  Experts run with memory isolation
     ↓
  Results compared to actual outcomes
```

**Advantages**:
- Fast iteration (no API rate limits)
- Isolated testing (won't pollute production)
- Can run 5 seasons in < 1 hour
- Full control over data

**Stack**: Python + pandas + SQLite for local cache

---

### Option 2: Production Testing
**Architecture**:
```
NFLverse CSV → Parse → Experts → Supabase Production
```

**Advantages**:
- Memories persist in production database
- Can use for future predictions
- Real environment testing

**Disadvantages**:
- Slower (API calls for each memory)
- Pollutes production with historical data
- Harder to reset and retry

---

## Recommended Implementation Plan

### Phase 1: Data Pipeline (Build This First)
```python
class NFLverseDataLoader:
    def load_season(self, year: int) -> List[GameData]:
        """Load all games for a season, ordered chronologically"""

    def get_team_stats_before_game(self, team: str, week: int, season: int) -> Dict:
        """Get team's cumulative stats up to (but not including) this game"""

    def convert_to_universal_game_data(self, game_row, home_stats, away_stats) -> UniversalGameData:
        """Convert NFLverse format to your UniversalGameData format"""
```

### Phase 2: Temporal Simulation Harness
```python
class BacktestSimulator:
    def __init__(self, data_loader, experts, memory_manager):
        self.data_loader = data_loader
        self.experts = experts  # List of expert instances
        self.memory_manager = memory_manager  # Local or Supabase

    def run_season(self, year: int):
        """Run all experts through one season week-by-week"""
        games = self.data_loader.load_season(year)

        for game in games:
            # Get stats BEFORE this game
            universal_data = self.prepare_game_data(game)

            # Each expert makes prediction
            for expert in self.experts:
                prediction = expert.make_personality_driven_prediction(universal_data)

                # After game completes, store memory
                outcome = {'winner': game.winner, 'score': game.score}
                expert.process_game_outcome(game.id, outcome, prediction)

    def analyze_learning(self):
        """Compare accuracy in early weeks vs late weeks"""
```

### Phase 3: Validation Framework
```python
def validate_learning(expert_results):
    """Prove learning occurred"""

    # Test 1: Accuracy improves over time
    early_accuracy = accuracy(weeks 1-4)
    late_accuracy = accuracy(weeks 13-17)

    assert late_accuracy > early_accuracy, "No learning detected"

    # Test 2: Principles discovered
    assert len(expert.learned_principles) > 0

    # Test 3: Beliefs revised
    assert len(expert.belief_revisions) > 0
```

---

## Answers to Your Questions

### 1. What inputs do experts expect?
**Answer**: `UniversalGameData` dataclass (shown above). They receive it directly as a structured object, NOT by querying a database.

### 2. Are they stateful or stateless?
**Answer**: **Stateful objects**. Each expert is an instance that maintains:
- Personality traits
- Memory (local + optional Supabase)
- Decision history
- Performance tracking

Running 3 experts = 3 separate object instances in memory.

### 3. Where to run backtests?
**Recommendation**: **Local with SQLite first**, then validate against Supabase.

Workflow:
1. Run 5-season backtest locally (fast)
2. Analyze results and tune parameters
3. Re-run one season against Supabase to populate production
4. Use populated memories for future predictions

### 4. Programming environment?
**Answer**: Python + pandas is perfect. NFLverse CSVs load easily with pandas.

Your existing stack:
- ✅ Python experts
- ✅ Supabase Python client
- ✅ Dataclasses for structure
- ✅ asyncio for async operations

### 5. Which metrics do experts use?
**Critical metrics** (must compute from NFLverse):
- Offensive yards per game (cumulative)
- Points per game (cumulative)
- Defensive performance (points/yards allowed)
- Turnover differential
- Win/loss record
- Point differential

**Nice-to-have** (can add later):
- EPA (Expected Points Added)
- CPOE (Completion Percentage Over Expected)
- Success rate on plays
- Red zone efficiency

---

## What to Build First

I recommend building in this order:

### Step 1: Data Pipeline (2-3 hours)
Create `scripts/nflverse_data_loader.py`:
- Load schedules.csv, weekly_stats.csv
- Implement chronological game ordering
- Implement cumulative stats calculation
- Convert to UniversalGameData format

**Deliverable**: Can load any season and convert to expert-compatible format

### Step 2: Simple Test (30 minutes)
Create `scripts/test_one_game.py`:
- Load one game from 2020
- Feed to conservative_analyzer
- Verify prediction works
- Store memory locally

**Deliverable**: Prove data pipeline works end-to-end

### Step 3: Backtest Harness (3-4 hours)
Create `scripts/backtest_runner.py`:
- Run expert through full season
- Store memories after each game
- Track accuracy week-by-week
- Generate learning report

**Deliverable**: Can run 5-year backtest and prove learning

---

## Next Steps

Should I build:

**A) Data Pipeline First** - Parse NFLverse → UniversalGameData converter
**B) Test Harness First** - Backtest framework with mock data
**C) Full Integration** - End-to-end backtest with real data

My recommendation: **Start with A (Data Pipeline)**. Once we can load and convert the data correctly, everything else flows naturally.

Want me to build the NFLverse data loader?