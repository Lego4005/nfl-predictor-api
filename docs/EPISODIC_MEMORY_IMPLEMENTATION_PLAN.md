# Episodic Memory System - Implementation Plan

## 🎯 Project Status

- ✅ Migrated from domain-biased to personality-driven experts
- ✅ Created learning pipeline for processing game results
- ✅ Designed episodic memory database schema (migration 010)
- ✅ APPLIED episodic memory migration to database
- 🔄 Ready to implement Python services

## 📋 Next Session Tasks

### ~~Priority 1: Apply Database Migration~~ ✅ COMPLETE

Database now has all episodic memory tables active!

### Priority 2: Implement Reasoning Chain Logger

Create `src/ml/reasoning_chain_logger.py`:

- Store WHY each prediction was made
- Track factor weights and confidence
- Generate internal monologue for each expert

### Priority 3: Belief Revision Service

Create `src/ml/belief_revision_service.py`:

- Track when experts change their minds
- Store causal chains for belief updates
- Calculate impact scores for revisions

### Priority 4: Episodic Memory Manager

Create `src/ml/episodic_memory_manager.py`:

- Store game-specific memories
- Calculate surprise factor and emotional weight
- Implement memory decay and reinforcement

### Priority 5: Connect to Existing System

Update `autonomous_expert_system.py`:

- Integrate reasoning chains into predictions
- Trigger belief revisions after game results
- Access episodic memories for similar games

## 🚀 Claude-Flow Command for Next Session

```bash
npx claude-flow sparc run architect "Implement episodic memory system for personality-driven NFL experts. Focus on: 1) Reasoning chain logging (WHY predictions are made), 2) Belief revision tracking (HOW experts change their minds), 3) Episodic memory storage (WHAT experts remember), 4) Memory compression (prevent infinite growth). Use existing migration 010_episodic_memory_system.sql as database schema."
```

## 📦 Key Files to Reference

### Database Schema

- `/src/database/migrations/010_episodic_memory_system.sql` - Complete schema

### Existing System

- `/src/ml/autonomous_expert_system.py` - Main system to enhance
- `/src/ml/personality_driven_experts.py` - 15 expert implementations
- `/src/ml/expert_memory_service.py` - Current memory service
- `/src/api/learning_pipeline.py` - Learning pipeline endpoints

### Documentation

- `/docs/PERSONALITY_EXPERTS_SUMMARY.md` - System overview
- `/docs/LEARNING_PIPELINE_API.md` - API documentation
- `/docs/MIGRATION_NOTES.md` - Why we moved from domain-biased

## 🎯 Success Criteria

1. **Reasoning Transparency**: Can see WHY each expert made their prediction
2. **Belief Evolution**: Track how expert beliefs change over time
3. **Memory Efficiency**: Old games compress into learned principles
4. **Causal Understanding**: Experts explain their reasoning updates
5. **Factor Discovery**: Experts identify new correlations

## 💡 Implementation Tips

### For Reasoning Chains

```python
reasoning = {
    "factors": [
        {"name": "home_advantage", "weight": 0.3, "value": "Jets at home"},
        {"name": "rest_days", "weight": 0.2, "value": "Bills on short rest"}
    ],
    "internal_thought": "Division games are always close, but rest matters",
    "confidence_breakdown": {"winner": 0.7, "spread": 0.5, "total": 0.6}
}
```

### For Belief Revisions

```python
revision = {
    "old": "Weather always helps underdogs",
    "new": "Weather helps teams with better run games",
    "trigger": "5 games where favorite dominated in rain",
    "impact": 0.15  # This changes 15% of predictions
}
```

### For Episodic Memory

```python
memory = {
    "game": "BUF@NYJ_20250915",
    "surprise": 0.8,  # Very unexpected outcome
    "lesson": "Primetime division games break normal patterns",
    "emotional_weight": 0.9  # The Gambler will remember this strongly
}
```

## 🔄 Memory Compression Strategy

After 100 games, compress to principles:

1. Group similar games by context
2. Extract common patterns
3. Create principle statements
4. Validate statistically
5. Archive raw memories

## 🎮 Fun Internal Betting Pool

Track hypothetical performance:

- Each expert starts with $10k virtual money
- Bet size = confidence * $100
- Update bankrolls after each game
- Show which expert would be "richest"

## 📊 Performance Metrics to Track

1. **Prediction Accuracy**: Winner, spread, total
2. **Belief Stability**: How often beliefs change
3. **Memory Utilization**: How often past games influence decisions
4. **Factor Discovery Rate**: New patterns identified
5. **Confidence Calibration**: Actual accuracy vs stated confidence

## 🚨 Critical Reminders

1. **Don't let memories grow infinitely** - Compress after 100 games
2. **Validate discovered factors** - Require statistical significance
3. **Preserve personality traits** - The Rebel stays rebellious
4. **Keep reasoning interpretable** - Must be able to explain decisions
5. **Test with real games** - Use actual NFL results for validation

## 📝 Sample Test Flow

1. Make predictions for upcoming game
2. Store reasoning chains
3. Process actual results
4. Trigger belief revisions if needed
5. Create episodic memories
6. Compress old memories if > 100
7. Discover new factors from patterns
8. Update virtual bankrolls

## 🎯 End Goal

A system where each expert:

- Explains their reasoning clearly
- Learns from mistakes with causal understanding
- Develops unique knowledge over time
- Discovers non-obvious patterns
- Maintains interpretable decision-making

## 💾 Context for Next Session

The personality-driven expert system is ready for deep learning enhancement. The database schema (migration 010) provides tables for reasoning chains, belief revisions, episodic memories, learned principles, and factor discovery. The next step is implementing the Python services to populate and utilize these tables, creating truly autonomous learning agents that understand WHY they succeed or fail.

---

Ready to continue with: `npx claude-flow sparc run architect "<task>"`
