# Belief Revision System - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### 1. Import and Initialize
```python
from src.ml.adaptive_belief_revision import BeliefRevisionService
from supabase import create_client

# Setup
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
service = BeliefRevisionService(supabase)
await service.initialize()
```

### 2. Check for Issues (After Each Game)
```python
# Get recent predictions with outcomes
recent_predictions = [
    {
        'game_id': 'game_123',
        'was_correct': False,
        'confidence': 0.85,
        'predicted_margin': 10,
        'actual_margin': -8
    },
    # ... more predictions
]

# Detect if revision needed
triggers = await service.check_revision_triggers(
    expert_id='expert_1',
    recent_predictions=recent_predictions,
    window_size=10  # Look at last 10 games
)

if triggers:
    print(f"🔔 {len(triggers)} issues detected!")
```

### 3. Generate and Apply Actions
```python
if triggers:
    # Get current expert configuration
    current_state = {
        'confidence_multiplier': 1.0,
        'high_confidence_threshold': 0.75,
        'factor_weights': {...}
    }

    # Generate actions
    actions = await service.generate_revision_actions(
        expert_id='expert_1',
        triggers=triggers,
        current_state=current_state
    )

    # Apply actions (your implementation)
    for action in actions:
        if action.action == RevisionAction.ADJUST_CONFIDENCE_THRESHOLD:
            # Update confidence settings
            expert.confidence_multiplier = action.parameters['confidence_multiplier']
        elif action.action == RevisionAction.CHANGE_FACTOR_WEIGHTS:
            # Update factor weights
            expert.update_weights(action.parameters['weight_adjustments'])
        # ... handle other actions

    # Store the revision
    revision = BeliefRevisionRecord(
        revision_id=generate_unique_id(),
        expert_id='expert_1',
        trigger=triggers[0],
        actions=actions,
        pre_revision_state=current_state,
        post_revision_state=get_new_state(expert),
        timestamp=datetime.now()
    )
    await service.store_revision(revision)
```

### 4. Measure Effectiveness (After More Games)
```python
# After 5+ more games with outcomes
post_revision_predictions = [
    {'game_id': 'game_124', 'was_correct': True, 'confidence': 0.72},
    {'game_id': 'game_125', 'was_correct': True, 'confidence': 0.68},
    # ... more predictions
]

effectiveness = await service.measure_revision_effectiveness(
    revision_id=revision.revision_id,
    post_revision_predictions=post_revision_predictions,
    window_size=5
)

print(f"📈 Revision effectiveness: {effectiveness:.0%}")
```

## 🎯 What Gets Detected?

### 1. Consecutive Incorrect (Threshold: 3+)
```python
# Example: Expert wrong 3+ times in a row
[False, False, False] → TRIGGER
Action: Reduce confidence multiplier
```

### 2. Confidence Misalignment (Threshold: 2+ high-conf errors)
```python
# Example: Expert very confident but wrong
[{conf: 0.85, wrong}, {conf: 0.90, wrong}] → TRIGGER
Action: Raise confidence threshold
```

### 3. Pattern Repetition (Threshold: 3+ same pattern)
```python
# Example: Keeps predicting wrong direction
[margin: +10 actual: -8, margin: +12 actual: -10, ...] → TRIGGER
Action: Adjust factor weights
```

### 4. Performance Decline (Threshold: 15%+ drop)
```python
# Example: First 5 games: 80% accuracy, Last 5 games: 60% accuracy
Decline: 20% → TRIGGER
Action: Shift to conservative strategy
```

## ⚡ What Actions Are Generated?

### Action 1: Adjust Confidence Threshold
```python
# Reduces overconfidence
{
    'action': 'adjust_confidence_threshold',
    'parameters': {
        'confidence_multiplier': 0.85,  # Reduced from 1.0
        'high_confidence_threshold': 0.85  # Raised from 0.75
    }
}
```

### Action 2: Change Factor Weights
```python
# Adjusts prediction factor importance
{
    'action': 'change_factor_weights',
    'parameters': {
        'weight_adjustments': {
            'matchup_analysis': +0.20,
            'gut_instinct': -0.15,
            'defensive_ratings': +0.15
        }
    }
}
```

### Action 3: Update Strategy
```python
# Changes overall approach
{
    'action': 'update_strategy',
    'parameters': {
        'strategy_shift': 'conservative',
        'analysis_depth': 'increased'
    }
}
```

## 📊 Configuration (Optional)

### Customize Thresholds
```python
service.revision_thresholds = {
    'consecutive_incorrect_threshold': 4,      # More lenient (default: 3)
    'confidence_misalignment_threshold': 0.30, # More lenient (default: 0.25)
    'pattern_repetition_threshold': 4,         # More lenient (default: 3)
    'performance_decline_threshold': 0.20,     # More lenient (default: 0.15)
}
```

## 🔍 Monitoring & Analysis

### View Revision History
```python
revisions = await service.retrieve_revisions(
    expert_id='expert_1',
    limit=10
)

for rev in revisions:
    print(f"Revision: {rev['revision_id']}")
    print(f"Trigger: {rev['trigger_type']}")
    print(f"Effectiveness: {rev['effectiveness_score']:.0%}")
```

### Common Patterns
```python
# Check all experts
all_revisions = await service.retrieve_revisions(expert_id=None)

# Group by trigger type
from collections import Counter
trigger_counts = Counter(r['trigger_type'] for r in all_revisions)
print(f"Most common trigger: {trigger_counts.most_common(1)}")
```

## 🎓 Best Practices

### 1. Run After Every Game Outcome
```python
async def handle_game_outcome(expert_id, prediction, outcome):
    # Store outcome
    await store_prediction_outcome(expert_id, prediction, outcome)

    # Check for issues
    recent = await get_recent_predictions(expert_id, limit=10)
    triggers = await service.check_revision_triggers(expert_id, recent)

    if triggers:
        await handle_revision(expert_id, triggers)
```

### 2. Apply Actions Gradually
```python
# Don't apply all actions at once
# Start with highest priority
priority_action = actions[0]
await apply_single_action(expert_id, priority_action)

# Monitor results before applying more
```

### 3. Track Effectiveness
```python
# Always measure if revisions helped
await service.measure_revision_effectiveness(
    revision_id=revision_id,
    post_revision_predictions=new_predictions
)

# Rollback ineffective revisions
if effectiveness < 0.3:
    await revert_revision(revision_id)
```

### 4. Set Appropriate Windows
```python
# Short window for rapid adaptation (5-7 games)
triggers = await service.check_revision_triggers(
    expert_id=expert_id,
    recent_predictions=recent,
    window_size=5
)

# Longer window for stable patterns (10-15 games)
triggers = await service.check_revision_triggers(
    expert_id=expert_id,
    recent_predictions=recent,
    window_size=15
)
```

## 🚨 Common Pitfalls

### ❌ Don't: Over-react to Small Samples
```python
# Bad: Only 3 predictions
recent = get_recent_predictions(expert_id, limit=3)
triggers = await service.check_revision_triggers(expert_id, recent)
# Not enough data for reliable detection
```

✅ **Do**: Wait for sufficient data
```python
# Good: 10+ predictions
recent = get_recent_predictions(expert_id, limit=10)
if len(recent) >= 10:
    triggers = await service.check_revision_triggers(expert_id, recent)
```

### ❌ Don't: Apply All Actions Immediately
```python
# Bad: Apply everything at once
for action in actions:
    apply_immediately(action)
# May over-correct
```

✅ **Do**: Apply incrementally
```python
# Good: Apply highest priority first
priority_actions = sorted(actions, key=lambda x: x.priority, reverse=True)
await apply_action(priority_actions[0])
await monitor_results()
```

### ❌ Don't: Ignore Effectiveness Scores
```python
# Bad: Never check if revisions helped
await store_revision(revision)
# Move on without measuring
```

✅ **Do**: Track and learn
```python
# Good: Measure effectiveness
effectiveness = await service.measure_revision_effectiveness(...)
if effectiveness < 0.3:
    logger.warning(f"Revision {revision_id} was ineffective!")
    await consider_rollback(revision_id)
```

## 📈 Expected Results

### Typical Improvements
- **Accuracy**: +5-10% after effective revision
- **Confidence Calibration**: Better alignment between confidence and correctness
- **Error Patterns**: Reduced repetition of same mistakes
- **Adaptability**: Faster recovery from performance slumps

### Timeline
- **Detection**: Immediate (after 3-10 games)
- **Action**: Applied within 1 game
- **Effectiveness**: Measurable after 5-10 games
- **Stabilization**: Full effect visible after 15-20 games

## 🔗 Integration Examples

### With Existing Expert System
```python
class EnhancedExpert:
    def __init__(self, expert_id):
        self.expert_id = expert_id
        self.belief_service = BeliefRevisionService(supabase)
        self.prediction_history = []

    async def make_prediction(self, game_data):
        # Standard prediction
        prediction = await self.predict(game_data)

        # Store for later analysis
        self.prediction_history.append({
            'prediction': prediction,
            'game_data': game_data,
            'timestamp': datetime.now()
        })

        return prediction

    async def record_outcome(self, game_id, outcome):
        # Find prediction
        pred = next(p for p in self.prediction_history if p['game_id'] == game_id)
        pred['was_correct'] = self.evaluate(pred, outcome)

        # Check if revision needed
        triggers = await self.belief_service.check_revision_triggers(
            expert_id=self.expert_id,
            recent_predictions=self.get_recent_with_outcomes()
        )

        if triggers:
            await self.adapt_strategy(triggers)
```

## 🛠️ Troubleshooting

### Issue: No Triggers Detected
**Possible Causes:**
- Not enough predictions (need 3+ minimum)
- Performance is stable (no issues)
- Thresholds too strict

**Solution:**
```python
# Check prediction count
if len(recent_predictions) < 3:
    print("Need more predictions")

# Lower thresholds temporarily
service.revision_thresholds['consecutive_incorrect_threshold'] = 2
```

### Issue: Too Many Triggers
**Possible Causes:**
- Expert genuinely struggling
- Thresholds too sensitive
- Insufficient data quality

**Solution:**
```python
# Raise thresholds
service.revision_thresholds['consecutive_incorrect_threshold'] = 4
service.revision_thresholds['confidence_misalignment_threshold'] = 0.35

# Or filter by severity
high_severity = [t for t in triggers if t.severity > 0.5]
```

### Issue: Revisions Not Helping
**Possible Causes:**
- Actions not being applied correctly
- Need different action types
- Underlying data quality issues

**Solution:**
```python
# Verify actions are applied
print(f"Pre-revision state: {revision.pre_revision_state}")
print(f"Post-revision state: {revision.post_revision_state}")

# Try different actions
# Instead of confidence adjustment, try weight changes
```

## 📞 Need Help?

- **Documentation**: `/docs/BELIEF_REVISION_IMPLEMENTATION.md`
- **Examples**: `/examples/belief_revision_demo.py`
- **Tests**: `/tests/ml/test_adaptive_belief_revision.py`

## ✅ Checklist for Integration

- [ ] Import BeliefRevisionService
- [ ] Initialize with Supabase client
- [ ] Hook into prediction outcome handler
- [ ] Implement action application logic
- [ ] Add effectiveness monitoring
- [ ] Set up logging/alerting
- [ ] Configure thresholds (if needed)
- [ ] Test with historical data
- [ ] Monitor first 10 revisions
- [ ] Adjust based on results

---

**You're ready to go! The system will automatically detect and adapt to improve expert predictions.**