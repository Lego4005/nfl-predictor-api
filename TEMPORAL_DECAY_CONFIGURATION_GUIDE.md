# Temporal Decay Configuration Prompt for Expert Memory Systems

## Core Concept

Each expert in the NFL prediction system needs to weight historical information differently based on the stability of the factors they analyze. Some factors remain relevant for years while others become outdated in weeks. The temporal decay half-life determines how quickly meies lose relevance for each expert.

**Half-life definition**: The number of days after which a memory retains 50% of its original weight. A memory that is two half-lives old retains 25% weight, three half-lives old retains 12.5% weight, and so on following exponential decay.

## Expert-Specific Temporal Decay Parameters

### 1. Conservative Analyzer (Half-life: 450 days)

**Rationale**: This expert values proven, stable patterns that persist across seasons. Historical win rates and fundamental team quality metrics change slowly. A conservative approach to predictions should match a conservative approach to discounting historical data.

**Memory categories**:
- Team quality assessments: 540-day half-life (very stable)
- Historical matchup patterns: 450-day half-life (moderately stable)
- Coaching tendencies: 270-day half-life (changes with coordinator turnover)

**Why this matters**: The conservative analyzer builds confidence through accumulated evidence. Rapid decay would undermine their analytical foundation by constantly erasing the historical patterns that make conservative predictions reliable.

---

### 2. Aggressive Gambler (Half-life: 120 days)

**Rationale**: This expert chases emerging opportunities and contrarian value, which requires sensitivity to recent shifts in team performance and public perception. Old upset patterns have limited predictive value because the circumstances that created them have likely changed.

**Memory categories**:
- Recent upset patterns: 90-day half-life (very short - upsets are context-specific)
- Emotional narrative memories: 120-day half-life (narratives shift quickly)
- Value betting opportunities: 150-day half-life (market evolves but not instantly)

**Why this matters**: The aggressive gambler's edge comes from spotting what changed recently, not what was true last season. Longer decay would cause them to chase stale patterns that the market has already corrected.

---

### 3. Weather Specialist (Half-life: 730 days)

**Rationale**: Weather physics don't change. How wind affects passing at Soldier Field in December is remarkably consistent across years. Stadium characteristics remain stable unless major renovations occur. This expert should have the longest memory because environmental factors are the most stable.

**Memory categories**:
- Weather impact patterns: 900-day half-life (physics is timeless)
- Stadium-specific conditions: 730-day half-life (very stable)
- Team adaptation to weather: 365-day half-life (rosters change)

**Why this matters**: A memory about how 20mph crosswinds affected passing accuracy at MetLife Stadium three years ago remains highly relevant today. Weather analysis benefits from deep historical data more than any other analytical approach.

---

### 4. Injury Tracker (Half-life: 180 days)

**Rationale**: Injury impacts are player and context-specific, with moderate decay. The effect of losing a star quarterback remains similar across seasons, but specific players age, leave teams, or develop differently. Backup quality changes annually with roster turnover.

**Memory categories**:
- Position-specific injury impacts: 270-day half-life (fairly stable)
- Individual player injury patterns: 180-day half-life (player-specific, moderate stability)
- Depth chart quality assessments: 120-day half-life (roster turnover is constant)

**Why this matters**: The injury tracker needs recent data about current roster compositions and backup quality, but general principles about position importance (losing your QB1 matters more than losing your RB2) remain stable over longer periods.

---

### 5. Market Reader (Half-life: 90 days)

**Rationale**: Betting markets evolve rapidly as analytics improve, public sophistication increases, and sharp bettors refine their approaches. What constituted sharp money movement last season may not indicate the same thing this season. This expert needs the second-shortest memory after the aggressive gambler.

**Memory categories**:
- Line movement patterns: 60-day half-life (markets adapt quickly)
- Sharp vs square indicators: 90-day half-life (market sophistication increases)
- Public betting tendencies: 120-day half-life (public learns slowly but does learn)

**Why this matters**: Market reading requires understanding current market dynamics, not historical ones. A line movement pattern that signaled value in Week 1 might be a trap by Week 17 because the market learned. Short decay keeps this expert sharp and current.

---

### 6. Statistical Purist (Half-life: 365 days)

**Rationale**: Advanced metrics like DVOA and EPA are designed to capture current team quality, but the relationships between these metrics and outcomes remain relatively stable. Statistical patterns persist longer than narratives but decay faster than physical phenomena like weather.

**Memory categories**:
- Metric-to-outcome correlations: 450-day half-life (statistical relationships are stable)
- Team performance metrics: 270-day half-life (team quality changes each season)
- Algorithm validation results: 365-day half-life (moderate decay)

**Why this matters**: The statistical purist trusts that mathematical relationships between metrics and outcomes persist, but needs to account for evolving offensive and defensive schemes that might change which metrics matter most. One-year half-life balances stability with adaptation.

---

### 7. Contrarian Expert (Half-life: 150 days)

**Rationale**: Public betting tendencies and media narratives shift moderately fast. What the public overvalued six months ago might be appropriately valued today, or the public might have overcorrected. Contrarian opportunities emerge and disappear as the crowd learns.

**Memory categories**:
- Public overreaction patterns: 120-day half-life (public learns from mistakes)
- Media narrative impacts: 150-day half-life (hype cycles are seasonal)
- Contrarian success rates: 180-day half-life (track recent edge persistence)

**Why this matters**: The contrarian expert's edge erodes as the market corrects for biases. What worked as a contrarian play last season might now be the consensus view. Moderate decay ensures they're fading current biases, not outdated ones.

---

### 8. Home Field Guru (Half-life: 540 days)

**Rationale**: Home field advantages are surprisingly stable across years. Stadium acoustics, crowd impact, and travel burdens don't change rapidly. However, individual team home records can fluctuate with roster quality, so a balance between long-term venue effects and current team performance is needed.

**Memory categories**:
- Venue-specific advantages: 730-day half-life (stadiums don't change)
- Team-specific home performance: 365-day half-life (roster-dependent)
- Travel impact patterns: 540-day half-life (geography is stable)

**Why this matters**: The home field guru combines stable environmental factors (stadium, location) with moderately variable factors (current team quality at home). Longer decay captures persistent venue advantages while still adapting to roster changes.

---

### 9. Divisional Specialist (Half-life: 270 days)

**Rationale**: Divisional rivalries have both stable elements (geographic proximity, frequent play) and changing elements (coaching changes, roster turnover). Familiarity effects persist but get refreshed regularly with staff changes. Moderate decay captures both aspects.

**Memory categories**:
- Coaching matchup history: 180-day half-life (coordinators change frequently)
- Divisional rivalry patterns: 365-day half-life (some patterns persist)
- Head-to-head results: 270-day half-life (recent games matter more)

**Why this matters**: Division games feature both "these teams always play each other close" stability and "but this year's Chiefs are completely different from last year's" volatility. Moderate decay weights recent divisional clashes appropriately while not completely forgetting historical rivalry dynamics.

---

### 10. Primetime Analyst (Half-life: 365 days)

**Rationale**: Teams' ability to perform under the bright lights is somewhat stable (certain franchises and quarterbacks consistently excel or struggle in primetime), but rosters change annually and pressure handling is player-specific.

**Memory categories**:
- Franchise primetime tendencies: 540-day half-life (organizational patterns persist)
- Individual player primetime performance: 270-day half-life (player-specific, moderate duration)
- Coaching primetime records: 365-day half-life (coach-specific but evolves)

**Why this matters**: Primetime performance has both psychological and talent components. Organizations develop reputations, but those reputations can change with new leadership. One-year half-life balances franchise history with recent roster reality.

---

### 11. Coaching Evaluator (Half-life: 240 days)

**Rationale**: Coaching tendencies are moderately stable but evolve as coordinators change, schemes adapt, and coaches learn from each other. A coach's play-calling from two seasons ago might not reflect their current approach after offseason study and coordinator hires.

**Memory categories**:
- Head coach decision-making: 365-day half-life (coaches evolve slowly)
- Coordinator tendencies: 180-day half-life (coordinators change jobs frequently)
- Coach vs coach matchups: 240-day half-life (balance of stability and change)

**Why this matters**: Coaching analysis requires understanding both persistent coaching philosophy (Andy Reid will always value tempo) and recent tactical evolution (but his current offense differs from his 2020 offense). Moderate decay keeps focus on current coaching approaches.

---

### 12. Momentum Tracker (Half-life: 45 days)

**Rationale**: This expert should have the shortest memory of all because momentum is inherently short-term. A team's hot streak from three months ago is completely irrelevant to their current momentum state. Rapid decay ensures this expert focuses exclusively on recent performance.

**Memory categories**:
- Win/loss streak patterns: 30-day half-life (extremely short-term)
- Confidence and psychology indicators: 45-day half-life (current season only)
- Recent performance trends: 60-day half-life (last 4-6 games maximum)

**Why this matters**: The entire concept of momentum trading is that recent performance predicts immediate future performance until a clear reversal occurs. Long memory would contaminate momentum signals with irrelevant historical data. This expert needs to forget quickly and focus intensely on the present.

---

### 13. Underdog Hunter (Half-life: 180 days)

**Rationale**: Underdog value opportunities emerge from both stable patterns (home underdogs cover more often) and evolving market inefficiencies. Moderate decay allows learning from recent underdog performance while maintaining some longer-term pattern recognition.

**Memory categories**:
- Underdog coverage patterns: 270-day half-life (some patterns are stable)
- Point spread value analysis: 150-day half-life (market efficiency evolves)
- Underdog situation identification: 180-day half-life (balanced approach)

**Why this matters**: The underdog hunter combines systematic pattern exploitation with adaptive market reading. Too much decay loses valuable stable patterns (certain point spread ranges consistently favor dogs), too little decay causes chasing outdated value that the market has corrected.

---

### 14. Total Predictor (Half-life: 300 days)

**Rationale**: Scoring environments change with rule adjustments and league-wide offensive trends, but pace and efficiency metrics remain meaningful across seasons. Moderate-to-long decay captures persistent relationships between pace and scoring while adapting to shifting league scoring averages.

**Memory categories**:
- Pace-to-scoring relationships: 450-day half-life (mathematical relationships stable)
- League scoring trends: 270-day half-life (gradual evolution)
- Team-specific totals patterns: 300-day half-life (rosters change annually)

**Why this matters**: The total predictor analyzes both stable mathematical relationships (faster pace generally means more points) and evolving league contexts (but average scoring changes year to year). Medium decay balances these time scales appropriately.

---

### 15. Situational Expert (Half-life: 210 days)

**Rationale**: Situational motivation patterns (must-win games, playoff implications) have both stable psychological elements and team-specific factors that change with roster quality and coaching. Moderate decay captures both dimensions.

**Memory categories**:
- Motivation impact patterns: 300-day half-life (psychology is somewhat stable)
- Team-specific situational response: 180-day half-life (roster and coaching dependent)
- Playoff scenario impacts: 210-day half-life (balanced moderate decay)

**Why this matters**: Teams generally respond to motivation and pressure in somewhat predictable ways, but specific rosters handle pressure differently. Moderate decay ensures the situational expert learns from recent high-pressure games while maintaining understanding of general motivation dynamics.

---

## Implementation Guidelines

### Applying Temporal Decay in Memory Retrieval

When retrieving memories for any expert, apply the following combined scoring formula:

```
final_score = (similarity_weight × similarity_score) + (temporal_weight × temporal_decay_score)

Where:
- similarity_weight: 0.70 (how well this memory matches the current situation)
- temporal_weight: 0.30 (how recent this memory is)
- temporal_decay_score = 0.5^(days_old / expert_half_life)
```

### Adjusting for Different Memory Types

Within each expert, different categories of memories may warrant different half-lives as specified in the breakdowns above. The system should tag memories with category labels and apply category-specific decay when that granularity is available.

### Belief Revision Temporal Scaling

When updating expert beliefs based on prediction outcomes, scale the learning rate by temporal decay:

```
adjusted_learning_magnitude = base_learning_rate × 0.5^(days_since_outcome / expert_half_life)
```

This ensures recent outcomes influence belief updates more strongly than old outcomes, preventing ancient results from continuing to shift beliefs long after they've become irrelevant.

### Dynamic Half-Life Adjustment

The orchestrator may discover through shadow mode testing that certain experts perform better with different half-life parameters than initially configured. Allow half-life to be a tunable hyperparameter that the orchestrator can optimize per expert based on prediction accuracy over time.

---

## Summary Table

| Expert | Half-Life (days) | Decay Speed | Reasoning |
|--------|------------------|-------------|-----------|
| Momentum Tracker | 45 | Extremely Fast | Momentum is inherently short-term |
| Market Reader | 90 | Very Fast | Markets evolve rapidly |
| Aggressive Gambler | 120 | Fast | Opportunities emerge and disappear quickly |
| Contrarian Expert | 150 | Moderately Fast | Public biases shift over months |
| Injury Tracker | 180 | Moderate | Rosters change but position importance stable |
| Underdog Hunter | 180 | Moderate | Balance pattern exploitation and adaptation |
| Situational Expert | 210 | Moderate | Motivation patterns moderately stable |
| Coaching Evaluator | 240 | Moderate | Coaching evolves but not rapidly |
| Divisional Specialist | 270 | Moderate-Slow | Familiarity and rivalry have persistence |
| Total Predictor | 300 | Moderate-Slow | Scoring relationships fairly stable |
| Statistical Purist | 365 | Slow | Mathematical relationships persist |
| Primetime Analyst | 365 | Slow | Performance under pressure somewhat stable |
| Conservative Analyzer | 450 | Very Slow | Proven patterns change gradually |
| Home Field Guru | 540 | Very Slow | Venue advantages highly stable |
| Weather Specialist | 730 | Extremely Slow | Physics doesn't change |

This configuration ensures each expert's memory system aligns with the temporal dynamics of the factors they analyze, creating a more accurate and adaptive prediction system overall.
