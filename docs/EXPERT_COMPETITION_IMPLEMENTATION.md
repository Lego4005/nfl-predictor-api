# NFL Predictor - 15 Expert Competition System Implementation Plan

## Vision

Create a competitive prediction ecosystem where 15 pseudo-expert models compete for leaderboard positions. Only the top 5 performers influence the consensus prediction, creating a gamified, self-improving system.

---

## Phase 1: Fix Core Issues (Immediate)

### Task 1.1: Fix PlayerPropsEngine Initialization

**Problem:** `PlayerPropsEngine.__init__() takes 1 positional argument but 3 were given`
**Solution:**

```python
# In src/ml/prediction_service.py, line ~50
# Change from:
self.props_engine = PlayerPropsEngine(self.data_pipeline, self.feature_engine)
# To:
self.props_engine = PlayerPropsEngine()
```

### Task 1.2: Fix ML Service Global Variable

**Problem:** `UnboundLocalError: local variable 'ml_service' referenced before assignment`
**Solution:**

```python
# In working_server.py, add at top:
ml_service = None  # Global declaration

# In startup event:
global ml_service
ml_service = MLPredictionService()
```

### Task 1.3: Initialize Basic ML Service

- Fix import paths
- Ensure all dependencies loaded
- Create fallback for missing data

---

## Phase 2: Create 15 Expert Personas

### Task 2.1: Define Expert Models

```python
EXPERT_MODELS = [
    # Statistical Experts (5)
    {"id": "stats_master", "name": "The Statistician", "type": "statistical", "specialty": "historical_patterns"},
    {"id": "elo_prophet", "name": "ELO Prophet", "type": "statistical", "specialty": "power_ratings"},
    {"id": "spread_sage", "name": "Spread Sage", "type": "statistical", "specialty": "betting_lines"},
    {"id": "momentum_maven", "name": "Momentum Maven", "type": "statistical", "specialty": "recent_form"},
    {"id": "bayesian_brain", "name": "Bayesian Brain", "type": "statistical", "specialty": "probability_theory"},

    # AI Experts (5)
    {"id": "claude_analyst", "name": "Claude Analyst", "type": "ai", "model": "claude-4-sonnet"},
    {"id": "gemini_guru", "name": "Gemini Guru", "type": "ai", "model": "gemini-2.5-pro"},
    {"id": "gpt_gladiator", "name": "GPT Gladiator", "type": "ai", "model": "gpt-4.1-mini"},
    {"id": "deepseek_detective", "name": "DeepSeek Detective", "type": "ai", "model": "deepseek-chat-v3"},
    {"id": "grok_genius", "name": "Grok Genius", "type": "ai", "model": "grok-code-fast-1"},

    # ML Experts (5)
    {"id": "neural_prophet", "name": "Neural Prophet", "type": "ml", "algorithm": "deep_neural_network"},
    {"id": "forest_ranger", "name": "Forest Ranger", "type": "ml", "algorithm": "random_forest"},
    {"id": "gradient_guru", "name": "Gradient Guru", "type": "ml", "algorithm": "xgboost"},
    {"id": "ensemble_emperor", "name": "Ensemble Emperor", "type": "ml", "algorithm": "stacking"},
    {"id": "pattern_prophet", "name": "Pattern Prophet", "type": "ml", "algorithm": "lightgbm"}
]
```

### Task 2.2: Create Expert Base Class

```python
class ExpertPredictor:
    def __init__(self, expert_config):
        self.id = expert_config['id']
        self.name = expert_config['name']
        self.type = expert_config['type']
        self.total_predictions = 0
        self.correct_predictions = 0
        self.recent_accuracy = []  # Last 20 games
        self.leaderboard_position = None
        self.confidence_adjustment = 1.0

    def make_prediction(self, game_data):
        # Each expert has unique prediction logic
        pass

    def explain_reasoning(self):
        # Return explanation for prediction
        pass

    def update_performance(self, was_correct):
        # Track accuracy and adjust confidence
        pass
```

---

## Phase 3: Performance Tracking System

### Task 3.1: Database Schema

```sql
-- Expert performance tracking
CREATE TABLE expert_predictions (
    id UUID PRIMARY KEY,
    expert_id VARCHAR(50),
    game_id VARCHAR(100),
    prediction_date TIMESTAMP,
    home_team VARCHAR(50),
    away_team VARCHAR(50),
    predicted_winner VARCHAR(50),
    confidence FLOAT,
    reasoning TEXT,
    actual_winner VARCHAR(50),
    was_correct BOOLEAN,
    points_earned FLOAT
);

-- Expert stats
CREATE TABLE expert_stats (
    expert_id VARCHAR(50) PRIMARY KEY,
    total_predictions INTEGER,
    correct_predictions INTEGER,
    accuracy_rate FLOAT,
    recent_form FLOAT,  -- Last 20 games
    leaderboard_rank INTEGER,
    peak_rank INTEGER,
    weeks_on_board INTEGER,
    last_updated TIMESTAMP
);

-- Leaderboard history
CREATE TABLE leaderboard_history (
    week INTEGER,
    season INTEGER,
    rank INTEGER,
    expert_id VARCHAR(50),
    accuracy FLOAT,
    predictions_count INTEGER,
    PRIMARY KEY (week, season, rank)
);
```

### Task 3.2: Performance Metrics

```python
class PerformanceTracker:
    def calculate_expert_score(self, expert_id):
        # Weighted scoring system
        metrics = {
            'overall_accuracy': 0.3,     # 30% weight
            'recent_accuracy': 0.4,       # 40% weight (last 20 games)
            'confidence_calibration': 0.2, # 20% weight
            'consistency': 0.1            # 10% weight
        }
        return weighted_score

    def update_leaderboard(self):
        # Rank all 15 experts
        # Mark top 5 for consensus participation
        # Track position changes
        pass
```

---

## Phase 4: Competitive Dynamics

### Task 4.1: Leaderboard Rules

```python
LEADERBOARD_RULES = {
    "qualification_threshold": 10,  # Min predictions to qualify
    "top_performers": 5,            # Number on main board
    "weight_distribution": {
        1: 0.30,  # 1st place: 30% weight
        2: 0.25,  # 2nd place: 25% weight
        3: 0.20,  # 3rd place: 20% weight
        4: 0.15,  # 4th place: 15% weight
        5: 0.10   # 5th place: 10% weight
    },
    "rolling_window": 20,  # Games for recent form
    "demotion_threshold": 0.45,  # Below 45% accuracy risks demotion
}
```

### Task 4.2: Consensus Calculator

```python
class ConsensusBuilder:
    def calculate_consensus(self, game_id):
        # Get top 5 experts from leaderboard
        top_experts = self.get_top_5_experts()

        # Get their predictions
        predictions = []
        for rank, expert in enumerate(top_experts, 1):
            prediction = expert.make_prediction(game_id)
            weight = LEADERBOARD_RULES['weight_distribution'][rank]
            predictions.append({
                'expert': expert.name,
                'prediction': prediction,
                'weight': weight,
                'confidence': prediction.confidence
            })

        # Calculate weighted consensus
        consensus = self.weighted_average(predictions)
        return consensus
```

---

## Phase 5: Competition Features

### Task 5.1: Expert Motivation System

```python
class ExpertMotivation:
    def __init__(self, expert):
        self.expert = expert
        self.motivation_factors = {
            'leaderboard_pressure': 0,  # Pressure to stay on board
            'comeback_drive': 0,        # Drive to return to board
            'rivalry_intensity': 0,      # Competition with nearby experts
            'streak_confidence': 0       # Confidence from win streaks
        }

    def adjust_strategy(self):
        if self.expert.leaderboard_position <= 5:
            # On the board - play conservative
            self.expert.risk_tolerance *= 0.9
        elif self.expert.leaderboard_position == 6:
            # Just off board - take calculated risks
            self.expert.risk_tolerance *= 1.1
        else:
            # Far from board - bold predictions
            self.expert.risk_tolerance *= 1.2
```

### Task 5.2: Adaptive Learning

```python
class AdaptiveExpert:
    def learn_from_mistakes(self, game_result):
        # Analyze why prediction was wrong
        error_analysis = self.analyze_error(game_result)

        # Adjust strategy based on error type
        if error_analysis['type'] == 'upset':
            self.increase_upset_sensitivity()
        elif error_analysis['type'] == 'home_bias':
            self.reduce_home_advantage_weight()

        # Learn from successful experts
        if self.leaderboard_position > 5:
            self.study_top_performers()
```

---

## Phase 6: UI Implementation

### Task 6.1: Expert Cards Component

```jsx
const ExpertCard = ({ expert }) => {
  return (
    <div className={`expert-card ${expert.rank <= 5 ? 'on-board' : 'challenger'}`}>
      <div className="expert-header">
        <span className="rank">#{expert.rank}</span>
        <h3>{expert.name}</h3>
        <span className="type">{expert.type}</span>
      </div>

      <div className="expert-stats">
        <div className="accuracy">
          <span className="label">Accuracy</span>
          <span className="value">{expert.accuracy}%</span>
        </div>
        <div className="recent-form">
          <span className="label">Last 20</span>
          <span className="value">{expert.recentAccuracy}%</span>
        </div>
        <div className="streak">
          <span className="label">Streak</span>
          <span className={`value ${expert.streak > 0 ? 'winning' : 'losing'}`}>
            {expert.streak > 0 ? `W${expert.streak}` : `L${Math.abs(expert.streak)}`}
          </span>
        </div>
      </div>

      <div className="prediction">
        <h4>Tonight's Pick: {expert.prediction.team}</h4>
        <p className="confidence">Confidence: {expert.prediction.confidence}%</p>
        <p className="reasoning">{expert.prediction.reasoning}</p>
      </div>

      {expert.rank <= 5 && (
        <div className="board-badge">
          <span>BOARD MEMBER</span>
          <span className="weight">{expert.consensusWeight}% influence</span>
        </div>
      )}
    </div>
  );
};
```

### Task 6.2: Leaderboard Display

```jsx
const CompetitiveLeaderboard = () => {
  return (
    <div className="leaderboard-container">
      <div className="top-5-board">
        <h2>Expert Council - Top 5</h2>
        <div className="consensus-influence">
          These experts determine our consensus prediction
        </div>
        {top5Experts.map(expert => (
          <LeaderboardRow key={expert.id} expert={expert} />
        ))}
      </div>

      <div className="challengers">
        <h3>Challengers</h3>
        {challengerExperts.map(expert => (
          <ChallengerRow key={expert.id} expert={expert} />
        ))}
      </div>

      <div className="consensus-prediction">
        <h2>Consensus Prediction</h2>
        <div className="consensus-details">
          Weighted average of Top 5 experts
        </div>
      </div>
    </div>
  );
};
```

---

## Phase 7: Real-Time Updates

### Task 7.1: Live Performance Tracking

```python
class LiveTracker:
    async def track_game_result(self, game_id, result):
        # Update all expert predictions for this game
        for expert in self.experts:
            prediction = await self.get_expert_prediction(expert.id, game_id)
            was_correct = prediction.winner == result.winner

            # Update expert stats
            expert.update_performance(was_correct)

            # Check for leaderboard changes
            if self.check_leaderboard_change():
                await self.broadcast_leaderboard_update()
```

### Task 7.2: WebSocket Updates

```javascript
// Real-time expert updates
socket.on('expert_prediction', (data) => {
  updateExpertCard(data.expertId, data.prediction);
});

socket.on('leaderboard_change', (data) => {
  // Animate position changes
  animateLeaderboardUpdate(data.changes);

  // Highlight promotions/demotions
  if (data.newBoardMember) {
    celebratePromotion(data.newBoardMember);
  }
});

socket.on('consensus_update', (data) => {
  updateConsensusPrediction(data.consensus);
});
```

---

## Implementation Timeline

### Week 1: Foundation

- [ ] Fix PlayerPropsEngine error
- [ ] Fix ML service initialization
- [ ] Create expert base classes
- [ ] Set up database schema

### Week 2: Expert System

- [ ] Implement 15 expert personas
- [ ] Create prediction methods for each
- [ ] Build performance tracking
- [ ] Test individual predictions

### Week 3: Competition

- [ ] Implement leaderboard logic
- [ ] Create consensus calculator
- [ ] Add competitive dynamics
- [ ] Build motivation system

### Week 4: UI & Polish

- [ ] Create expert card components
- [ ] Build leaderboard display
- [ ] Add real-time updates
- [ ] Implement animations

### Week 5: Testing & Tuning

- [ ] Test with historical data
- [ ] Tune expert strategies
- [ ] Balance competition dynamics
- [ ] Launch with live games

---

## Success Metrics

1. **System Health**
   - All 15 experts making predictions
   - Leaderboard updating correctly
   - Consensus calculated from top 5

2. **Competition Dynamics**
   - Regular position changes
   - Experts adapting strategies
   - Improved accuracy over time

3. **User Engagement**
   - Users viewing individual experts
   - Following expert rivalries
   - Tracking leaderboard changes

4. **Prediction Accuracy**
   - Consensus > 60% accuracy
   - Top expert > 65% accuracy
   - System improving week-over-week

---

## Next Steps

1. **Immediate**: Fix the ML service errors to get basic predictions working
2. **Today**: Create the 15 expert personas and basic prediction logic
3. **This Week**: Implement performance tracking and leaderboard
4. **Next Week**: Build UI components and launch competitive system

This creates a truly competitive, gamified prediction ecosystem where experts fight for supremacy!
