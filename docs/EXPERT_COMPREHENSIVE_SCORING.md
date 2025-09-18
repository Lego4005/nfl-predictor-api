# Comprehensive Expert Scoring System - All Predictions

## The Full Prediction Matrix

Based on PREDICTION_SYSTEM_OVERVIEW.md, each of our 15 experts makes **20+ different prediction types** per game:

```typescript
interface ExpertCompletePredictions {
  expertId: string;
  gameId: string;

  // === CORE GAME PREDICTIONS ===
  gameOutcome: {
    homeWinProb: number;  // 0-100%
    awayWinProb: number;  // 0-100%
    confidence: number;
    actualResult?: 'correct' | 'incorrect';
    points: number;
  };

  exactScore: {
    homeScore: number;
    awayScore: number;
    confidence: number;
    accuracy?: 'exact' | 'within3' | 'within7' | 'wrong';
    points: number;
  };

  marginOfVictory: {
    margin: number;
    winningTeam: 'home' | 'away';
    confidence: number;
    accuracy?: number;  // Distance from actual
    points: number;
  };

  // === BETTING PREDICTIONS ===
  againstTheSpread: {
    pick: 'home' | 'away';
    predictedSpread: number;
    confidence: number;
    spreadEdge: number;  // vs market
    actualResult?: 'cover' | 'push' | 'fail';
    points: number;
  };

  totals: {
    pick: 'over' | 'under';
    predictedTotal: number;
    confidence: number;
    actualResult?: 'correct' | 'push' | 'incorrect';
    points: number;
  };

  moneylineValue: {
    recommendedBet: 'home' | 'away' | 'no_bet';
    expectedROI: number;
    confidence: number;
    actualROI?: number;
    points: number;
  };

  // === LIVE GAME PREDICTIONS (Updated each quarter) ===
  liveWinProbability: {
    q1: { home: number; away: number; accuracy?: number };
    q2: { home: number; away: number; accuracy?: number };
    q3: { home: number; away: number; accuracy?: number };
    q4: { home: number; away: number; accuracy?: number };
    points: number;  // Total for all quarters
  };

  nextScore: {
    predictions: Array<{
      quarter: number;
      team: 'home' | 'away' | 'none';
      scoreType: 'touchdown' | 'field_goal' | 'safety' | 'none';
      probability: number;
      actualResult?: 'correct' | 'incorrect';
    }>;
    totalPoints: number;
  };

  driveOutcomes: {
    predictions: Array<{
      driveId: string;
      predictedOutcome: 'touchdown' | 'field_goal' | 'punt' | 'turnover' | 'downs';
      probability: number;
      actualOutcome?: string;
      correct?: boolean;
    }>;
    accuracy: number;
    points: number;
  };

  fourthDownDecisions: {
    recommendations: Array<{
      situation: string;
      recommendation: 'go_for_it' | 'field_goal' | 'punt';
      successProbability: number;
      expectedValue: number;
      actualDecision?: string;
      outcome?: 'success' | 'failure';
    }>;
    accuracy: number;
    points: number;
  };

  // === PLAYER PROPS (Per key player) ===
  playerProps: {
    passing: Array<{
      playerId: string;
      playerName: string;
      yards: { prediction: number; actual?: number; accuracy?: number };
      touchdowns: { prediction: number; actual?: number; correct?: boolean };
      completions: { prediction: number; actual?: number; accuracy?: number };
      interceptions: { prediction: number; actual?: number; correct?: boolean };
      points: number;
    }>;

    rushing: Array<{
      playerId: string;
      playerName: string;
      yards: { prediction: number; actual?: number; accuracy?: number };
      attempts: { prediction: number; actual?: number; accuracy?: number };
      touchdowns: { prediction: number; actual?: number; correct?: boolean };
      longestRush: { prediction: number; actual?: number; accuracy?: number };
      points: number;
    }>;

    receiving: Array<{
      playerId: string;
      playerName: string;
      yards: { prediction: number; actual?: number; accuracy?: number };
      receptions: { prediction: number; actual?: number; accuracy?: number };
      touchdowns: { prediction: number; actual?: number; correct?: boolean };
      targets: { prediction: number; actual?: number; accuracy?: number };
      points: number;
    }>;

    fantasyPoints: Array<{
      playerId: string;
      playerName: string;
      predictedPoints: number;
      actualPoints?: number;
      accuracy?: number;  // Within 3 points = accurate
      points: number;
    }>;
  };

  // === CONTEXTUAL PREDICTIONS ===
  weatherImpact: {
    passingImpact: number;  // -1 to 1 scale
    rushingImpact: number;
    kickingImpact: number;
    totalImpact: number;
    actualImpact?: number;
    accuracy?: number;
    points: number;
  };

  momentumShifts: {
    predictions: Array<{
      quarter: number;
      shiftType: 'massive' | 'moderate' | 'slight' | 'neutral';
      direction: 'home' | 'away';
      confidence: number;
      actualShift?: string;
      correct?: boolean;
    }>;
    accuracy: number;
    points: number;
  };

  injuryImpact: {
    homeImpact: number;  // 0-1 scale
    awayImpact: number;
    keyPlayerAdjustments: Array<{
      player: string;
      impact: number;
      actualImpact?: number;
    }>;
    accuracy: number;
    points: number;
  };

  // === AGGREGATE SCORING ===
  totalPredictionsMade: number;
  totalPredictionsCorrect: number;
  totalPointsEarned: number;
  categoryScores: {
    coreGame: number;
    betting: number;
    liveGame: number;
    playerProps: number;
    contextual: number;
  };
}
```

---

## Hierarchical Scoring System

### Level 1: Major Categories
Each expert is scored across 5 major categories:

```typescript
const CATEGORY_WEIGHTS = {
  coreGame: 0.25,     // 25% - Basic game predictions
  betting: 0.20,      // 20% - ATS, O/U, moneyline
  liveGame: 0.15,     // 15% - In-game adjustments
  playerProps: 0.25,  // 25% - Player performance
  contextual: 0.15    // 15% - Weather, momentum, injuries
};
```

### Level 2: Prediction Types Within Categories

```typescript
const PREDICTION_DIFFICULTY_MULTIPLIERS = {
  // Core Game (Higher difficulty = more points)
  gameOutcome: 1.0,        // Base difficulty
  exactScore: 5.0,         // Very hard
  marginOfVictory: 2.5,    // Hard

  // Betting
  againstTheSpread: 1.5,   // Moderate
  totals: 1.3,             // Moderate
  moneylineValue: 1.8,     // Harder

  // Live Game
  liveWinProbability: 1.2, // Per quarter
  nextScore: 2.0,          // Hard
  driveOutcomes: 1.5,      // Moderate
  fourthDownDecisions: 2.5, // Very situational

  // Player Props
  passingYards: 1.5,
  rushingYards: 1.8,       // Harder to predict
  receivingYards: 1.6,
  touchdowns: 3.0,         // Very hard
  fantasyPoints: 2.0,      // Moderate-hard

  // Contextual
  weatherImpact: 1.0,
  momentumShifts: 2.5,     // Hard to predict
  injuryImpact: 1.5
};
```

---

## Dynamic Scoring Formula

```typescript
class ExpertScoringEngine {
  calculateScore(prediction: any, actual: any, type: string): number {
    const baseDifficulty = PREDICTION_DIFFICULTY_MULTIPLIERS[type];
    const confidence = prediction.confidence / 100;

    // Base points for correct prediction
    let basePoints = this.getBasePoints(type, prediction, actual);

    // Apply confidence multiplier (risk/reward)
    // High confidence on correct = bonus
    // High confidence on incorrect = penalty
    const confidenceMultiplier = prediction.correct
      ? 1 + (confidence * 0.5)  // Up to 50% bonus
      : 1 - (confidence * 0.5); // Up to 50% penalty

    // Apply difficulty multiplier
    const difficultyBonus = baseDifficulty;

    // Apply accuracy gradient (closer = more points)
    const accuracyMultiplier = this.getAccuracyMultiplier(type, prediction, actual);

    // Final score
    return basePoints * confidenceMultiplier * difficultyBonus * accuracyMultiplier;
  }

  getAccuracyMultiplier(type: string, prediction: any, actual: any): number {
    switch(type) {
      case 'exactScore':
        if (prediction.homeScore === actual.homeScore &&
            prediction.awayScore === actual.awayScore) return 3.0; // Jackpot!
        const totalDiff = Math.abs(prediction.homeScore - actual.homeScore) +
                         Math.abs(prediction.awayScore - actual.awayScore);
        if (totalDiff <= 3) return 1.5;
        if (totalDiff <= 7) return 1.0;
        if (totalDiff <= 14) return 0.5;
        return 0.1;

      case 'passingYards':
        const yardDiff = Math.abs(prediction.yards - actual.yards);
        if (yardDiff <= 10) return 2.0;
        if (yardDiff <= 25) return 1.5;
        if (yardDiff <= 50) return 1.0;
        if (yardDiff <= 75) return 0.5;
        return 0.1;

      // ... more accuracy gradients for each type

      default:
        return prediction.correct ? 1.0 : 0.0;
    }
  }
}
```

---

## Expert Specialization Matrix

Each expert develops a unique "skill fingerprint":

```typescript
interface ExpertSkillMatrix {
  expertId: string;

  // Performance by category (0-100 scale)
  categoryMastery: {
    coreGame: 72,
    betting: 45,
    liveGame: 68,
    playerProps: 81,  // This expert excels at player props!
    contextual: 55
  };

  // Granular strengths (0-100 scale)
  predictionStrengths: {
    // Core
    gameOutcome: 85,
    exactScore: 12,    // Terrible at exact scores
    marginOfVictory: 58,

    // Betting
    againstTheSpread: 48,
    totals: 62,
    moneylineValue: 41,

    // Player Props broken down
    qbProps: 88,       // Great at QBs!
    rbProps: 75,
    wrProps: 82,
    teProps: 61,

    // Situational
    primetimeGames: 78,
    divisionalGames: 65,
    weatherGames: 42,  // Struggles in weather
    upsets: 71,        // Good at spotting upsets
    blowouts: 55
  };

  // Learning trends
  improvementRate: {
    weekly: +2.3,      // % improvement per week
    categoryTrends: {
      coreGame: +1.2,
      betting: -0.5,   // Getting worse at betting
      liveGame: +3.1,  // Rapidly improving!
      playerProps: +2.8,
      contextual: 0.0
    }
  };

  // Confidence calibration by category
  confidenceCalibration: {
    coreGame: 0.92,     // Well calibrated
    betting: 0.71,      // Overconfident
    liveGame: 0.88,
    playerProps: 0.95,  // Very well calibrated
    contextual: 0.65    // Too confident
  };
}
```

---

## Multiple Specialized Leaderboards

```typescript
interface ComprehensiveLeaderboards {
  // Master leaderboard (overall performance)
  overall: LeaderboardEntry[];

  // Category Champions
  categories: {
    coreGameMaster: LeaderboardEntry[];    // Best at basic predictions
    bettingSharp: LeaderboardEntry[];      // Best at ATS/O/U
    liveGameGuru: LeaderboardEntry[];      // Best at in-game adjustments
    propsProphet: LeaderboardEntry[];      // Best at player props
    contextualKing: LeaderboardEntry[];    // Best at weather/momentum
  };

  // Specialized Excellence
  specialists: {
    exactScoreWizard: LeaderboardEntry[];  // Rare exact score hits
    upsetPicker: LeaderboardEntry[];       // Best at predicting upsets
    qbWhisperer: LeaderboardEntry[];       // Best at QB props
    rbGuru: LeaderboardEntry[];            // Best at RB props
    weatherMaster: LeaderboardEntry[];     // Best in bad weather
    primetimePerformer: LeaderboardEntry[]; // Best in big games
    fourthDownGenius: LeaderboardEntry[];  // Best at 4th down calls
    comebackPredictor: LeaderboardEntry[]; // Best at live adjustments
  };

  // Consistency Awards
  reliability: {
    mostConsistent: LeaderboardEntry[];    // Lowest variance
    bestCalibrated: LeaderboardEntry[];    // Confidence matches results
    steadyImprover: LeaderboardEntry[];    // Consistent growth
  };
}
```

---

## Learning & Adaptation System

### Pattern Recognition

```python
class ExpertLearningEngine:
    def analyze_prediction_patterns(self, expert_id: str):
        patterns = {
            'strength_patterns': [],
            'weakness_patterns': [],
            'improvement_opportunities': []
        }

        # Identify where expert excels
        if accuracy['qbProps'] > 80 and accuracy['primetimeGames'] > 75:
            patterns['strength_patterns'].append({
                'pattern': 'Elite QB predictor in primetime',
                'confidence_adjustment': 1.2,  # Boost confidence here
                'weight_adjustment': 1.3       # More weight in consensus
            })

        # Identify weaknesses
        if accuracy['weatherGames'] < 40 and accuracy['rushingProps'] < 45:
            patterns['weakness_patterns'].append({
                'pattern': 'Poor in weather, especially rushing',
                'confidence_adjustment': 0.5,  # Reduce confidence
                'weight_adjustment': 0.3       # Less weight in consensus
            })

        # Find improvement opportunities
        if trend['liveGame'] > 3.0:  # Rapidly improving
            patterns['improvement_opportunities'].append({
                'area': 'Live game adjustments',
                'action': 'Increase exposure to live predictions',
                'expected_gain': '+5% accuracy in 2 weeks'
            })

        return patterns
```

### Adaptive Confidence

```python
def adjust_expert_confidence(self, expert: Expert, game_context: GameContext):
    base_confidence = expert.default_confidence

    # Adjust based on historical performance in this context
    adjustments = []

    # Situational adjustments
    if game_context.is_primetime and expert.primetime_accuracy > 0.7:
        adjustments.append(1.15)  # 15% boost

    if game_context.has_weather and expert.weather_accuracy < 0.4:
        adjustments.append(0.6)   # 40% reduction

    if game_context.is_divisional and expert.divisional_accuracy > 0.65:
        adjustments.append(1.1)   # 10% boost

    # Category-specific adjustments
    for category in ['coreGame', 'betting', 'liveGame', 'playerProps', 'contextual']:
        if expert.requesting_prediction_for == category:
            adjustments.append(expert.category_confidence[category])

    # Apply all adjustments
    final_confidence = base_confidence
    for adj in adjustments:
        final_confidence *= adj

    return min(0.95, max(0.05, final_confidence))  # Cap between 5-95%
```

---

## UI Visualization - Expert Report Card

```jsx
const ExpertComprehensiveReportCard = ({ expert, gameId }) => {
  return (
    <div className="expert-report-card">
      {/* Skill Radar Chart */}
      <RadarChart
        data={expert.skillMatrix}
        categories={['Core', 'Betting', 'Live', 'Props', 'Context']}
      />

      {/* Heat Map Grid - All Predictions */}
      <div className="prediction-heatmap">
        {Object.entries(expert.allPredictions).map(([category, predictions]) => (
          <div className="category-section" key={category}>
            <h4>{category}</h4>
            <div className="prediction-grid">
              {predictions.map(pred => (
                <div
                  className={`pred-cell ${getColorClass(pred.accuracy)}`}
                  title={`${pred.confidence}% confidence, ${pred.points} points`}
                >
                  <span className="type">{pred.type}</span>
                  <span className="accuracy">{pred.accuracy}%</span>
                  <span className="trend">{pred.trend}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Specialization Badges */}
      <div className="specializations">
        {expert.topSpecializations.map(spec => (
          <Badge
            key={spec}
            type={spec}
            rank={expert.getRankIn(spec)}
            accuracy={expert.getAccuracyIn(spec)}
          />
        ))}
      </div>

      {/* Improvement Trajectory */}
      <LineChart
        title="30-Day Improvement"
        data={expert.improvementHistory}
        categories={['Overall', 'Core', 'Betting', 'Live', 'Props']}
      />
    </div>
  );
};
```

---

## Implementation Impact

### Scale of Predictions
- **15 experts** × **20+ prediction types** × **16 games/week** = **4,800+ predictions per week**
- Each prediction tracked individually for accuracy
- Patterns emerge showing true expert specialization

### Benefits
1. **Hyper-specialization**: Experts naturally find their niches
2. **Targeted Improvement**: Fix specific weaknesses, not everything
3. **Rich Competition**: Multiple ways to excel and compete
4. **User Trust**: See exactly what each expert is good/bad at
5. **Better Consensus**: Use the right expert for each prediction type

This comprehensive system creates a living, learning ecosystem where each expert evolves based on thousands of micro-performances rather than simple win/loss tracking!