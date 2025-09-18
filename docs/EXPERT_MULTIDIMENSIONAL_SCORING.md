# Expert Multi-Dimensional Prediction & Scoring System

## The Problem You Identified
Currently tracking only win/loss is too simplistic. We need granular tracking of MULTIPLE prediction types per game to identify strengths/weaknesses and enable targeted improvement.

---

## Multi-Dimensional Prediction Portfolio

### Each Expert Makes 7 Predictions Per Game:

```typescript
interface ExpertGamePredictions {
  gameId: string;
  expertId: string;

  predictions: {
    // 1. WIN/LOSS (Binary)
    winner: {
      pick: 'home' | 'away';
      confidence: number;  // 0-100%
      reasoning: string;
      actualResult?: 'correct' | 'incorrect';
      points: number;  // Points earned/lost
    };

    // 2. SPREAD (Point Differential)
    spread: {
      pick: 'home' | 'away';  // Who covers
      predictedSpread: number;  // -7.5, +3.5, etc
      confidence: number;
      actualSpread?: number;
      accuracy?: 'exact' | 'correct_side' | 'wrong';
      points: number;
    };

    // 3. TOTAL POINTS (Over/Under)
    total: {
      pick: 'over' | 'under';
      predictedTotal: number;  // 45.5, 52.5, etc
      confidence: number;
      actualTotal?: number;
      accuracy?: 'exact' | 'correct_side' | 'wrong';
      points: number;
    };

    // 4. EXACT SCORES
    exactScore: {
      homeScore: number;
      awayScore: number;
      confidence: number;
      actualHome?: number;
      actualAway?: number;
      accuracy?: number;  // Distance from actual
      points: number;
    };

    // 5. MARGIN OF VICTORY
    margin: {
      predictedMargin: number;
      winningTeam: 'home' | 'away';
      confidence: number;
      actualMargin?: number;
      accuracy?: number;  // How close in points
      points: number;
    };

    // 6. FIRST HALF WINNER
    firstHalf: {
      pick: 'home' | 'away' | 'tie';
      confidence: number;
      actualResult?: 'correct' | 'incorrect';
      points: number;
    };

    // 7. HIGHEST SCORING QUARTER
    highestQuarter: {
      pick: 1 | 2 | 3 | 4;
      confidence: number;
      actualResult?: number;
      accuracy?: 'correct' | 'incorrect';
      points: number;
    };
  };

  // Aggregate Scoring
  totalPointsEarned: number;
  predictionsMade: number;
  predictionsCorrect: number;
  weightedAccuracy: number;  // Confidence-weighted
}
```

---

## Scoring System Per Prediction Type

### Point Values by Difficulty:

```javascript
const SCORING_MATRIX = {
  winner: {
    correct: 10,
    incorrect: -5,
    confidenceMultiplier: 1.5,  // High confidence = more risk/reward
  },

  spread: {
    exact: 25,      // Nail the spread exactly
    correctSide: 15,  // Right side of spread
    incorrect: -10,
    confidenceMultiplier: 2.0,
  },

  total: {
    exact: 20,
    correctSide: 12,
    incorrect: -8,
    confidenceMultiplier: 1.8,
  },

  exactScore: {
    bothCorrect: 100,  // Jackpot!
    oneCorrect: 25,
    withinThree: 10,
    wayOff: -15,
    confidenceMultiplier: 3.0,  // High risk, high reward
  },

  margin: {
    exact: 50,
    withinThree: 20,
    withinSeven: 10,
    wrongTeamWon: -20,
    confidenceMultiplier: 2.5,
  },

  firstHalf: {
    correct: 15,
    incorrect: -7,
    confidenceMultiplier: 1.3,
  },

  highestQuarter: {
    correct: 20,
    incorrect: -5,
    confidenceMultiplier: 1.5,
  }
};
```

---

## Expert Specialization Tracking

### Performance Matrix Per Expert:

```typescript
interface ExpertSpecialization {
  expertId: string;

  // Track accuracy by prediction type
  strengths: {
    winner: { accuracy: 0.75, sampleSize: 100, trend: 'improving' },
    spread: { accuracy: 0.45, sampleSize: 100, trend: 'declining' },
    total: { accuracy: 0.62, sampleSize: 100, trend: 'stable' },
    exactScore: { accuracy: 0.08, sampleSize: 100, trend: 'improving' },
    margin: { accuracy: 0.35, sampleSize: 100, trend: 'stable' },
    firstHalf: { accuracy: 0.68, sampleSize: 100, trend: 'improving' },
    highestQuarter: { accuracy: 0.25, sampleSize: 100, trend: 'stable' }
  };

  // Situational Performance
  situationalStrengths: {
    favorites: { accuracy: 0.82, confidence: 0.85 },
    underdogs: { accuracy: 0.41, confidence: 0.45 },
    primetime: { accuracy: 0.70, confidence: 0.75 },
    divisional: { accuracy: 0.65, confidence: 0.70 },
    highScoring: { accuracy: 0.58, confidence: 0.60 },
    lowScoring: { accuracy: 0.71, confidence: 0.72 },
    blowouts: { accuracy: 0.55, confidence: 0.58 },
    closeGames: { accuracy: 0.48, confidence: 0.50 }
  };

  // Adaptive Confidence Weights
  confidenceAdjustments: {
    winner: 1.0,      // Baseline confidence
    spread: 0.6,      // Reduce confidence (weak area)
    total: 0.85,      // Slight reduction
    exactScore: 0.3,  // Very low confidence
    margin: 0.5,      // Half confidence
    firstHalf: 0.9,   // High confidence
    highestQuarter: 0.4  // Low confidence
  };
}
```

---

## Learning & Improvement System

### 1. Reinforcement Learning Per Category:

```python
class ExpertLearning:
    def update_after_game(self, expert_id, game_results):
        # Get expert's predictions
        predictions = self.get_predictions(expert_id, game_results.game_id)

        # Update each prediction category
        for category in ['winner', 'spread', 'total', 'exactScore',
                        'margin', 'firstHalf', 'highestQuarter']:

            prediction = predictions[category]
            actual = game_results[category]

            # Calculate accuracy
            was_correct = self.evaluate_prediction(prediction, actual, category)

            # Update running accuracy
            self.update_category_accuracy(expert_id, category, was_correct)

            # Adjust future confidence
            if was_correct:
                # Increase confidence in this category
                self.confidence_weights[expert_id][category] *= 1.02
            else:
                # Decrease confidence
                self.confidence_weights[expert_id][category] *= 0.98

            # Identify patterns
            self.analyze_error_patterns(expert_id, category, prediction, actual)
```

### 2. Pattern Recognition:

```python
def analyze_error_patterns(self, expert_id, category, prediction, actual):
    """Identify why predictions fail"""

    patterns = {
        'home_bias': prediction.favored_home and actual.away_won,
        'overconfidence': prediction.confidence > 80 and not was_correct,
        'weather_miss': game.had_weather and prediction.ignored_weather,
        'injury_miss': game.had_key_injury and prediction.ignored_injury,
        'primetime_choke': game.is_primetime and not was_correct,
        'upset_blind': actual.was_upset and prediction.picked_favorite
    }

    # Store patterns for future adjustment
    self.expert_patterns[expert_id].append(patterns)

    # After 10 games, adjust strategy
    if len(self.expert_patterns[expert_id]) >= 10:
        self.adjust_expert_strategy(expert_id)
```

---

## Multiple Leaderboards

### Different Rankings for Different Skills:

```typescript
interface LeaderboardSystem {
  // Overall Leaderboard (weighted average of all)
  overall: ExpertRanking[];

  // Specialized Leaderboards
  categories: {
    straightUp: ExpertRanking[];     // Best at picking winners
    spreadMaster: ExpertRanking[];   // Best against the spread
    totalsGuru: ExpertRanking[];     // Best at over/under
    precisionScorer: ExpertRanking[]; // Best at exact scores
    marginExpert: ExpertRanking[];   // Best at victory margins
    firstHalfKing: ExpertRanking[];  // Best at first half
    quarterCaller: ExpertRanking[];  // Best at quarter predictions
  };

  // Situational Leaderboards
  situations: {
    upsetPicker: ExpertRanking[];    // Best at predicting upsets
    primetimePerformer: ExpertRanking[]; // Best in big games
    divisionalDominator: ExpertRanking[]; // Best at division games
    weatherWarrior: ExpertRanking[];  // Best in bad weather
  };
}
```

---

## UI Display - Expert Report Card

```jsx
const ExpertReportCard = ({ expert, gameId }) => {
  return (
    <div className="expert-report-card">
      <h3>{expert.name}'s Predictions</h3>

      {/* Visual Heat Map of Strengths */}
      <div className="strength-heatmap">
        {Object.entries(expert.predictions).map(([category, pred]) => (
          <div
            className={`prediction-cell ${getPerfClass(pred.historicalAccuracy)}`}
            key={category}
          >
            <span className="category">{category}</span>
            <span className="pick">{pred.pick}</span>
            <span className="confidence">{pred.confidence}%</span>
            <span className="accuracy">{pred.historicalAccuracy}% historical</span>
            <div className="points">
              {pred.actualResult && (
                <span className={pred.points > 0 ? 'positive' : 'negative'}>
                  {pred.points > 0 ? '+' : ''}{pred.points}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Specialization Badges */}
      <div className="specialization-badges">
        {expert.specializations.map(spec => (
          <Badge key={spec} type={spec} />
        ))}
      </div>

      {/* Performance Trend */}
      <div className="performance-trend">
        <MiniChart data={expert.recentPerformance} />
      </div>
    </div>
  );
};
```

---

## Consensus Building with Specialization

```typescript
class SpecializedConsensus {
  buildConsensus(predictions: ExpertPredictions[], game: GameData) {
    const consensus = {};

    // For each prediction category, weight by expert specialization
    for (const category of PREDICTION_CATEGORIES) {
      // Get top 5 experts FOR THIS SPECIFIC CATEGORY
      const categoryExperts = this.getTopExpertsForCategory(category);

      // Weight their predictions based on category-specific performance
      const weightedPredictions = categoryExperts.map(expert => ({
        prediction: predictions.find(p => p.expertId === expert.id)[category],
        weight: expert.categoryAccuracy[category] * expert.confidenceAdjustment[category]
      }));

      // Calculate category consensus
      consensus[category] = this.calculateWeightedAverage(weightedPredictions);
    }

    return consensus;
  }

  getTopExpertsForCategory(category: string) {
    // Different experts might be top 5 for different categories!
    return this.experts
      .sort((a, b) => b.categoryAccuracy[category] - a.categoryAccuracy[category])
      .slice(0, 5);
  }
}
```

---

## Improvement Metrics Dashboard

```typescript
interface ImprovementTracking {
  expertId: string;

  // Weekly improvement rates
  weeklyImprovement: {
    winner: +2.3,      // % improvement
    spread: -1.5,      // % decline
    total: +0.8,
    exactScore: +5.2,  // Big improvement!
    margin: 0.0,
    firstHalf: +1.1,
    highestQuarter: -3.2
  };

  // Learning achievements
  achievements: [
    { type: 'UPSET_SPECIALIST', unlockedAt: '2025-09-10' },
    { type: 'SPREAD_MASTER', unlockedAt: '2025-09-12' },
    { type: 'CONSISTENT_PERFORMER', unlockedAt: '2025-09-14' }
  ];

  // Recommended adjustments
  recommendations: [
    "Reduce confidence on road underdogs (-15% accuracy)",
    "Increase confidence on divisional games (+8% accuracy)",
    "Avoid exact score predictions in weather games (-40% accuracy)"
  ];
}
```

---

## Implementation Benefits

### 1. **Granular Improvement**
- Experts improve in specific areas, not just overall
- Targeted algorithm adjustments per prediction type
- Natural specialization emerges

### 2. **Better User Experience**
- See which expert to trust for which prediction
- Multiple leaderboards create more engagement
- Transparency in strengths/weaknesses

### 3. **Smarter Consensus**
- Use spread specialists for spread consensus
- Use totals experts for O/U consensus
- Dynamic expert selection per category

### 4. **Continuous Learning**
- Identify patterns in failures
- Automatic confidence adjustments
- Reinforcement learning per category

---

## Next Steps

1. **Modify Database Schema** - Add tables for multi-dimensional predictions
2. **Update Expert Classes** - Implement 7 prediction methods per expert
3. **Create Scoring Engine** - Calculate points per prediction type
4. **Build Learning System** - Track patterns and adjust strategies
5. **Design UI Components** - Heat maps, report cards, multiple leaderboards
6. **Test with Historical Data** - Validate scoring and improvement systems

This creates a truly intelligent system where each expert evolves and specializes based on their actual performance!