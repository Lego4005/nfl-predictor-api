# 🧪 Memory Learning Experiment - Complete Guide

## Overview

This experiment scientifically proves whether **episodic memory makes LLM experts smarter** over time.

**Design:** Controlled A/B test comparing:
- **Control Group:** 15 experts WITHOUT memory (fresh predictions every game)
- **Experimental Group:** 15 experts WITH memory (accumulate and use past experiences)

**Hypothesis:** Memory-enabled experts will show statistically significant accuracy improvement over 30-40 games, while no-memory experts stay flat.

---

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install scipy matplotlib numpy

# Ensure local LLM is running
curl http://192.168.254.253:1234/v1/models
```

### 2. Quick Test (5 games, ~2-3 minutes)

```bash
cd /home/iris/code/experimental/nfl-predictor-api
python3 scripts/quick_test_memory_experiment.py
```

This runs a 5-game test to verify:
- ✅ Local LLM connection works
- ✅ Supabase data loading works
- ✅ 30 experts can make predictions
- ✅ Memory storage/retrieval works
- ✅ Results export works

### 3. Full Experiment (40 games, ~8-10 minutes)

```bash
python3 scripts/prove_memory_learning.py
```

This runs the complete experiment:
- Loads 40 completed NFL games from Supabase
- 30 experts (15 memory, 15 no-memory) predict each game
- Tracks accuracy, learning curves, confidence
- Exports detailed results to `results/` directory

### 4. Analyze Results

```bash
python3 scripts/analyze_memory_experiment.py results/<experiment_id>_results.json
```

Generates:
- Statistical significance testing (paired t-test)
- Learning curve analysis
- Per-personality breakdown
- Markdown summary report

---

## Understanding the Output

### During Experiment

```
🏈 GAME 15/40: KC @ BUF
   Week 5, Actual: BUF 24-21

   ✅ ConservativeAnalyzer (Memory): KC (acc: 0.42)
   ❌ ConservativeAnalyzer (No Memory): KC (acc: 0.38)
   ✅ RiskTakingGambler (Memory): BUF (acc: 0.78)
   ...

   📊 Game 15 Summary:
      Memory Group: 64.2% avg accuracy
      No-Memory Group: 58.7% avg accuracy
      Difference: +5.5%
```

### Final Summary

```
📊 OVERALL RESULTS:
   Memory Group: 68.3% accuracy (600 predictions)
   No-Memory Group: 62.1% accuracy (600 predictions)
   Improvement: +6.2%

📈 LEARNING CURVE (Memory Group):
   Games 1-10: 58.4%
   Final 10 games: 72.8%
   Learning Improvement: +14.4%
```

### Analysis Report

The analysis script generates:

**Markdown Report** (`results/<experiment_id>_analysis.md`):
- Overall accuracy comparison
- Statistical significance (p-value)
- Learning curve trends
- Conclusion and recommendations

**JSON Data** (`results/<experiment_id>_detailed_analysis.json`):
- Complete statistical breakdown
- Per-expert metrics
- Exportable for further analysis

---

## Success Criteria

### ✅ **Experiment Succeeds If:**

1. **Statistical Significance:** p < 0.05 (paired t-test)
2. **Practical Improvement:** Memory group >5% better than no-memory
3. **Learning Curve:** Positive slope for memory group (improving over time)
4. **Consistency:** At least 10/15 personalities show improvement
5. **Sustainability:** Improvement holds in final validation games

**Example Success:**
```
Overall Results:
  Memory: 71.2% accuracy
  No-Memory: 63.8% accuracy
  Difference: +7.4%
  P-value: 0.0032 ✅ SIGNIFICANT

Learning Curve:
  Memory: Games 1-10: 59% → Final 10: 75% (+16%)
  No-Memory: Games 1-10: 61% → Final 10: 63% (+2%)

Conclusion: Memory significantly improves performance!
```

### ⚠️ **Experiment Inconclusive If:**

1. **Borderline Significance:** 0.05 < p < 0.10
2. **Small Effect Size:** <3% improvement
3. **High Variance:** Large standard deviations mask signal
4. **Mixed Results:** Some personalities improve, others don't

**Action:** Run larger experiment (100+ games)

### ❌ **Experiment Fails If:**

1. **No Significance:** p >= 0.10
2. **No Improvement:** Memory group same or worse than no-memory
3. **Flat Learning Curve:** No upward trend
4. **Negative Results:** Memory actually hurts performance

**Action:** Investigate why (LLM limitations? bad memory format? data quality?)

---

## Understanding the Experts

### 15 Personality Types

| Expert | Personality | Expected Behavior |
|--------|------------|-------------------|
| **Conservative** | Risk-averse | Favors favorites, safe bets |
| **Gambler** | High variance | Chases upsets, aggressive |
| **Contrarian** | Fade public | Zigs when others zag |
| **Value** | Line hunter | Seeks market inefficiencies |
| **Momentum** | Trend follower | Rides hot streaks |
| **Scholar** | Stats-driven | Fundamentals only |
| **Chaos** | Entropy | Embraces unpredictability |
| **Gut** | Intuitive | Trusts instinct |
| **Quant** | Pure math | Numbers-only approach |
| **Reversal** | Mean reversion | Bets against streaks |
| **Fader** | Media contrarian | Fades narratives |
| **Sharp** | Pro follower | Follows sharp money |
| **Underdog** | Dog specialist | Loves underdogs |
| **Consensus** | Majority | Wisdom of crowds |
| **Exploiter** | Arbitrage | Finds inefficiencies |

### Memory vs No-Memory

**Memory Group:**
- Retrieves 5 similar past games before predicting
- Learns from successes and failures
- Adjusts strategy based on outcomes
- Stores reflection/lesson after each game

**No-Memory Group:**
- Makes fresh prediction every time
- No context from past games
- Pure personality-based decisions
- Simulates baseline without learning

---

## Technical Details

### Data Flow

```
1. Load Games from Supabase
   ↓
2. For Each Game:
   ↓
   2a. Memory Group: Retrieve similar past games
   2b. No-Memory Group: Skip retrieval
   ↓
3. Generate LLM Prediction
   ↓
4. Evaluate vs Actual Outcome
   ↓
5. Memory Group: Store New Memory
   ↓
6. Record Results
   ↓
7. Next Game

8. Final Analysis → Statistical Report
```

### Performance Optimization

**Batching:** Processes 5 experts concurrently
- 30 experts / 5 batches = 6 batches
- 6 batches × 2 seconds = 12 seconds per game
- 40 games × 12 seconds = 8 minutes total

**Caching:** Results stored immediately after each game
- If script crashes, can resume from checkpoint
- Partial results still analyzable

### Memory Storage

**Episodic Memory Format:**
```json
{
  "expert_id": "conservative-mem-001",
  "game_id": "game_15",
  "prediction_summary": {
    "winner": "KC",
    "margin": 7,
    "confidence": 8
  },
  "actual_outcome": {
    "winner": "BUF",
    "home_score": 24,
    "away_score": 21
  },
  "lesson_learned": "Underestimated home field advantage in cold weather",
  "emotional_weight": 0.9,
  "surprise_factor": 0.8
}
```

### Accuracy Scoring

**Composite Score (0.0 - 1.0):**
- **Winner:** 50% (0.5 for correct, 0 for wrong)
- **Margin:** 30% (scaled by error: 0-14 points = full credit)
- **Total:** 20% (scaled by error: 0-20 points = full credit)

**Example:**
- Predicted: KC by 7, Total 48
- Actual: BUF by 3, Total 45
- Winner: ❌ (0 points)
- Margin error: 10 points → 0.29 × 0.3 = 0.087
- Total error: 3 points → 0.85 × 0.2 = 0.170
- **Total Score: 0.257 (25.7%)**

---

## Troubleshooting

### "No completed games found"

**Problem:** Supabase has no games with scores
**Solution:** Script automatically falls back to simulated games

### "LLM connection timeout"

**Problem:** Local LLM not responding
**Solution:**
```bash
# Check LLM is running
curl http://192.168.254.253:1234/v1/models

# Restart LLM service if needed
```

### "Memory storage failed"

**Problem:** Supabase table doesn't exist
**Solution:** Check `expert_episodic_memories` table exists

### "Script crashes mid-experiment"

**Problem:** Network error or LLM failure
**Solution:** Re-run script - it will resume from last completed game

---

## Next Steps After Results

### If Memory Helps (p < 0.05, >5% improvement):

1. **Deploy to Production**
   - Enable memory for all experts in production system
   - Set up continuous learning pipeline
   - Monitor real-time performance

2. **Optimize Memory Retrieval**
   - Add vector embeddings for better similarity search
   - Tune memory decay parameters
   - Implement memory importance weighting

3. **Scale Up**
   - Increase to 100+ game learning phase
   - Add more expert personalities
   - Integrate with ML ensemble

### If Memory Doesn't Help (p >= 0.10, <2% improvement):

1. **Investigate Root Cause**
   - Is LLM utilizing memory context effectively?
   - Is memory retrieval finding relevant games?
   - Is memory format optimal for LLM consumption?

2. **Try Alternatives**
   - Different memory encoding (structured vs narrative)
   - Longer context windows
   - Hybrid: memory + traditional ML features

3. **Benchmark Against ML**
   - Compare to XGBoost/LSTM ensemble
   - Evaluate cost/performance trade-off
   - Consider pure statistical approach

### If Inconclusive (borderline results):

1. **Run Larger Experiment**
   - 100+ games for more statistical power
   - Multiple seasons for generalization
   - More expert personalities

2. **Refine Methodology**
   - Better memory similarity matching
   - Improved prompt engineering
   - Confidence calibration

3. **A/B Test Variations**
   - Different memory retrieval strategies
   - Various context window sizes
   - Alternative personality definitions

---

## File Structure

```
scripts/
├── prove_memory_learning.py          # Main experiment runner
├── analyze_memory_experiment.py      # Statistical analysis
└── quick_test_memory_experiment.py   # Quick 5-game test

results/
├── memory_proof_v1_<timestamp>_results.json
├── memory_proof_v1_<timestamp>_analysis.md
└── memory_proof_v1_<timestamp>_detailed_analysis.json

docs/
└── MEMORY_EXPERIMENT_GUIDE.md        # This file
```

---

## FAQ

**Q: How long does the full experiment take?**
A: ~8-10 minutes for 40 games (with batching)

**Q: Can I run multiple experiments in parallel?**
A: Yes, each gets unique experiment_id

**Q: What if I don't have 40 completed games?**
A: Script falls back to simulated games for testing

**Q: Can I test with more than 40 games?**
A: Yes, pass different limit: `experiment.run_experiment(num_games=100)`

**Q: How do I interpret the p-value?**
A: p < 0.05 = statistically significant, p >= 0.05 = not significant

**Q: What's a good accuracy target?**
A: NFL prediction baseline ~50-55%, good systems reach 65-70%, excellent 70%+

**Q: Do I need GPU for this?**
A: No, local LLM runs on GPU but experiment script is CPU-only

**Q: Can I customize expert personalities?**
A: Yes, edit `_get_personality_traits()` in prove_memory_learning.py

**Q: How do I add vector embeddings?**
A: See LLM_EXPERT_SYSTEM_ANALYSIS.md Phase 2 for implementation

**Q: Can I visualize learning curves?**
A: Yes, analysis script can generate matplotlib charts (add to analyze_memory_experiment.py)

---

## Support

- **Issues:** Check /docs/LLM_EXPERT_SYSTEM_ANALYSIS.md
- **Architecture:** See /docs/ensemble_implementation_summary.md
- **Local LLM:** Verify connection: `curl http://192.168.254.253:1234/v1/models`

---

*Generated: 2025-09-30*
*NFL Predictor API - Memory Learning Experiment*
