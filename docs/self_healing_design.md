# Self-Healing Expert System Design

## Overview

The self-healing mechanism enables the expert system to automatically detect prediction failures, analyze root causes, adjust factor weights, and validate corrections. This creates a resilient system that improves over time without manual intervention.

## 1. Failure Detection Algorithm

### Rolling Window Tracker

Track the last 5 predictions for each expert personality to detect performance degradation.

```typescript
interface PredictionResult {
  gameId: string;
  prediction: string; // 'home' | 'away'
  actual: string;
  correct: boolean;
  confidence: number;
  timestamp: Date;
  factors: FactorWeights;
}

interface RollingWindow {
  expertId: string;
  results: PredictionResult[];
  accuracy: number;
  lastUpdated: Date;
}

class FailureDetector {
  private readonly WINDOW_SIZE = 5;
  private readonly ACCURACY_THRESHOLD = 0.50;
  private readonly MIN_PREDICTIONS = 3; // Need at least 3 to trigger

  async checkPerformance(expertId: string): Promise<{
    needsHealing: boolean;
    accuracy: number;
    failurePattern: string | null;
  }> {
    const window = await this.getRollingWindow(expertId);

    // Need minimum predictions before triggering
    if (window.results.length < this.MIN_PREDICTIONS) {
      return { needsHealing: false, accuracy: 1.0, failurePattern: null };
    }

    const accuracy = this.calculateAccuracy(window.results);

    if (accuracy < this.ACCURACY_THRESHOLD) {
      const pattern = await this.identifyFailurePattern(window.results);

      await this.logFailureDetection({
        expertId,
        accuracy,
        pattern,
        windowSize: window.results.length,
        timestamp: new Date()
      });

      return { needsHealing: true, accuracy, failurePattern: pattern };
    }

    return { needsHealing: false, accuracy, failurePattern: null };
  }

  private calculateAccuracy(results: PredictionResult[]): number {
    const correct = results.filter(r => r.correct).length;
    return correct / results.length;
  }

  private async getRollingWindow(expertId: string): Promise<RollingWindow> {
    // Retrieve from memory service
    const key = `expert:${expertId}:rolling_window`;
    return await memoryService.retrieve(key) || {
      expertId,
      results: [],
      accuracy: 1.0,
      lastUpdated: new Date()
    };
  }

  private async identifyFailurePattern(results: PredictionResult[]): Promise<string> {
    const failures = results.filter(r => !r.correct);

    // Analyze common characteristics of failures
    const patterns = {
      overconfident: failures.filter(f => f.confidence > 0.8).length / failures.length,
      underconfident: failures.filter(f => f.confidence < 0.4).length / failures.length,
      homeOvervalued: failures.filter(f => f.prediction === 'home').length / failures.length,
      awayOvervalued: failures.filter(f => f.prediction === 'away').length / failures.length
    };

    // Return dominant pattern
    const dominant = Object.entries(patterns)
      .sort(([, a], [, b]) => b - a)[0];

    return dominant[1] > 0.6 ? dominant[0] : 'mixed_factors';
  }
}
```

### Trigger Conditions

**Primary Trigger**: Accuracy < 50% over last 5 games (minimum 3 games)

**Secondary Triggers**:
- Confidence calibration off by >30% (predicted 80% confident but only 40% accurate)
- Consistent bias (all failures on home or away picks)
- Sudden drop (from >70% to <50% in 3 games)

## 2. Root Cause Analysis

### Factor Contribution Analysis

Determine which factors contributed most to failed predictions.

```typescript
interface FactorWeights {
  homeFieldAdvantage: number;
  recentForm: number;
  headToHead: number;
  injuries: number;
  weather: number;
  restDays: number;
  divisionGame: number;
  playoff: number;
}

interface FactorAnalysis {
  factor: keyof FactorWeights;
  currentWeight: number;
  successWeight: number; // Average weight in successful predictions
  failureWeight: number; // Average weight in failed predictions
  impact: number; // Difference between success and failure
  recommendation: 'increase' | 'decrease' | 'maintain';
}

class RootCauseAnalyzer {
  async analyzeFactors(
    expertId: string,
    rollingWindow: RollingWindow
  ): Promise<FactorAnalysis[]> {
    const successes = rollingWindow.results.filter(r => r.correct);
    const failures = rollingWindow.results.filter(r => !r.correct);

    const factorKeys = Object.keys(failures[0].factors) as Array<keyof FactorWeights>;

    const analyses: FactorAnalysis[] = [];

    for (const factor of factorKeys) {
      const successWeight = this.averageWeight(successes, factor);
      const failureWeight = this.averageWeight(failures, factor);
      const impact = Math.abs(successWeight - failureWeight);

      const currentWeight = failures[0].factors[factor]; // Latest

      let recommendation: 'increase' | 'decrease' | 'maintain';

      if (impact < 0.1) {
        recommendation = 'maintain';
      } else if (successWeight > failureWeight) {
        recommendation = 'increase';
      } else {
        recommendation = 'decrease';
      }

      analyses.push({
        factor,
        currentWeight,
        successWeight,
        failureWeight,
        impact,
        recommendation
      });
    }

    // Sort by impact (most problematic first)
    return analyses.sort((a, b) => b.impact - a.impact);
  }

  private averageWeight(
    results: PredictionResult[],
    factor: keyof FactorWeights
  ): number {
    const sum = results.reduce((acc, r) => acc + r.factors[factor], 0);
    return sum / results.length;
  }

  async generateDiagnosticReport(
    expertId: string,
    analyses: FactorAnalysis[]
  ): Promise<string> {
    const topIssues = analyses.filter(a => a.impact > 0.15).slice(0, 3);

    let report = `## Root Cause Analysis for Expert ${expertId}\n\n`;
    report += `**Timestamp**: ${new Date().toISOString()}\n\n`;
    report += `### Top Contributing Factors to Failures\n\n`;

    for (const issue of topIssues) {
      report += `**${issue.factor}**\n`;
      report += `- Current Weight: ${issue.currentWeight.toFixed(3)}\n`;
      report += `- Success Average: ${issue.successWeight.toFixed(3)}\n`;
      report += `- Failure Average: ${issue.failureWeight.toFixed(3)}\n`;
      report += `- Impact Score: ${issue.impact.toFixed(3)}\n`;
      report += `- Recommendation: ${issue.recommendation.toUpperCase()}\n\n`;
    }

    return report;
  }
}
```

### Pattern Recognition

Identify systemic issues beyond individual factors:

```typescript
interface SystemicPattern {
  type: 'bias' | 'overfit' | 'underfit' | 'noise';
  description: string;
  severity: 'low' | 'medium' | 'high';
  recommendation: string;
}

class PatternRecognizer {
  async identifySystemicIssues(
    rollingWindow: RollingWindow
  ): Promise<SystemicPattern[]> {
    const patterns: SystemicPattern[] = [];

    // Check for bias
    const homeFailures = rollingWindow.results.filter(
      r => !r.correct && r.prediction === 'home'
    ).length;
    const awayFailures = rollingWindow.results.filter(
      r => !r.correct && r.prediction === 'away'
    ).length;

    if (Math.abs(homeFailures - awayFailures) >= 3) {
      patterns.push({
        type: 'bias',
        description: homeFailures > awayFailures
          ? 'Overvaluing home team advantage'
          : 'Undervaluing home team advantage',
        severity: 'high',
        recommendation: 'Adjust homeFieldAdvantage weight'
      });
    }

    // Check for overfitting (too confident on failures)
    const overconfidentFailures = rollingWindow.results.filter(
      r => !r.correct && r.confidence > 0.75
    ).length;

    if (overconfidentFailures >= 3) {
      patterns.push({
        type: 'overfit',
        description: 'High confidence on incorrect predictions',
        severity: 'high',
        recommendation: 'Reduce factor weights globally by 10-15%'
      });
    }

    // Check for underfitting (right factors, wrong weights)
    const lowConfidenceSuccesses = rollingWindow.results.filter(
      r => r.correct && r.confidence < 0.55
    ).length;

    if (lowConfidenceSuccesses >= 2) {
      patterns.push({
        type: 'underfit',
        description: 'Correct predictions with low confidence',
        severity: 'medium',
        recommendation: 'Increase weights on successful factors'
      });
    }

    return patterns;
  }
}
```

## 3. Automatic Correction Strategy

### Weight Adjustment Algorithm

Apply corrections based on root cause analysis with safety constraints.

```typescript
interface CorrectionPlan {
  expertId: string;
  originalWeights: FactorWeights;
  adjustedWeights: FactorWeights;
  changes: Array<{
    factor: keyof FactorWeights;
    oldValue: number;
    newValue: number;
    percentChange: number;
  }>;
  rationale: string;
  timestamp: Date;
}

class WeightCorrector {
  private readonly MAX_ADJUSTMENT = 0.25; // Max 25% change per correction
  private readonly MIN_WEIGHT = 0.05; // Minimum weight value
  private readonly MAX_WEIGHT = 0.95; // Maximum weight value

  async createCorrectionPlan(
    expertId: string,
    currentWeights: FactorWeights,
    analyses: FactorAnalysis[],
    patterns: SystemicPattern[]
  ): Promise<CorrectionPlan> {
    const adjustedWeights = { ...currentWeights };
    const changes: CorrectionPlan['changes'] = [];

    // Apply factor-specific adjustments
    for (const analysis of analyses) {
      if (analysis.recommendation === 'maintain') continue;

      const oldValue = currentWeights[analysis.factor];
      const targetValue = this.calculateTargetWeight(
        oldValue,
        analysis.successWeight,
        analysis.recommendation
      );

      const newValue = this.applyConstraints(targetValue);
      const percentChange = ((newValue - oldValue) / oldValue) * 100;

      adjustedWeights[analysis.factor] = newValue;

      changes.push({
        factor: analysis.factor,
        oldValue,
        newValue,
        percentChange
      });
    }

    // Apply systemic corrections
    for (const pattern of patterns) {
      if (pattern.type === 'overfit') {
        // Reduce all weights proportionally
        for (const key of Object.keys(adjustedWeights) as Array<keyof FactorWeights>) {
          adjustedWeights[key] = this.applyConstraints(
            adjustedWeights[key] * 0.85
          );
        }
      }
    }

    // Normalize weights to sum to reasonable range
    this.normalizeWeights(adjustedWeights);

    const rationale = this.generateRationale(analyses, patterns, changes);

    return {
      expertId,
      originalWeights: currentWeights,
      adjustedWeights,
      changes,
      rationale,
      timestamp: new Date()
    };
  }

  private calculateTargetWeight(
    current: number,
    target: number,
    direction: 'increase' | 'decrease'
  ): number {
    // Move 40% of the way toward target, capped by MAX_ADJUSTMENT
    const delta = (target - current) * 0.4;
    const cappedDelta = Math.sign(delta) * Math.min(
      Math.abs(delta),
      current * this.MAX_ADJUSTMENT
    );

    return current + cappedDelta;
  }

  private applyConstraints(value: number): number {
    return Math.max(
      this.MIN_WEIGHT,
      Math.min(this.MAX_WEIGHT, value)
    );
  }

  private normalizeWeights(weights: FactorWeights): void {
    const sum = Object.values(weights).reduce((a, b) => a + b, 0);
    const target = 4.0; // Target sum for normalized weights

    if (Math.abs(sum - target) > 0.5) {
      const factor = target / sum;
      for (const key of Object.keys(weights) as Array<keyof FactorWeights>) {
        weights[key] = this.applyConstraints(weights[key] * factor);
      }
    }
  }

  private generateRationale(
    analyses: FactorAnalysis[],
    patterns: SystemicPattern[],
    changes: CorrectionPlan['changes']
  ): string {
    let rationale = 'Automatic correction applied:\n\n';

    const majorChanges = changes.filter(c => Math.abs(c.percentChange) > 10);
    if (majorChanges.length > 0) {
      rationale += 'Major adjustments:\n';
      for (const change of majorChanges) {
        rationale += `- ${change.factor}: ${change.percentChange > 0 ? '+' : ''}${change.percentChange.toFixed(1)}%\n`;
      }
    }

    if (patterns.length > 0) {
      rationale += '\nSystemic issues addressed:\n';
      for (const pattern of patterns) {
        rationale += `- ${pattern.type}: ${pattern.description}\n`;
      }
    }

    return rationale;
  }

  async applyCorrectionPlan(plan: CorrectionPlan): Promise<void> {
    // Store new weights
    await memoryService.store(
      `expert:${plan.expertId}:current_weights`,
      plan.adjustedWeights
    );

    // Store backup of old weights
    await memoryService.store(
      `expert:${plan.expertId}:backup_weights:${plan.timestamp.getTime()}`,
      plan.originalWeights,
      { ttl: 30 * 24 * 60 * 60 } // Keep for 30 days
    );

    // Log correction
    await this.logCorrection(plan);
  }

  private async logCorrection(plan: CorrectionPlan): Promise<void> {
    const log = {
      type: 'weight_correction',
      expertId: plan.expertId,
      timestamp: plan.timestamp,
      changes: plan.changes,
      rationale: plan.rationale
    };

    await memoryService.store(
      `expert:${plan.expertId}:corrections:${plan.timestamp.getTime()}`,
      log
    );
  }
}
```

## 4. Validation Strategy

### A/B Testing Approach

Test corrected weights on next prediction before fully committing.

```typescript
interface ValidationResult {
  testPrediction: {
    winner: string;
    confidence: number;
    weights: FactorWeights;
  };
  controlPrediction: {
    winner: string;
    confidence: number;
    weights: FactorWeights;
  };
  actual: string | null; // null until game completes
  testCorrect: boolean | null;
  controlCorrect: boolean | null;
  decision: 'adopt' | 'reject' | 'pending';
  timestamp: Date;
}

class CorrectionValidator {
  async validateCorrection(
    expertId: string,
    gameId: string,
    correctionPlan: CorrectionPlan
  ): Promise<ValidationResult> {
    const gameData = await this.fetchGameData(gameId);

    // Generate prediction with NEW weights
    const testPrediction = await this.generatePrediction(
      gameData,
      correctionPlan.adjustedWeights
    );

    // Generate prediction with OLD weights
    const controlPrediction = await this.generatePrediction(
      gameData,
      correctionPlan.originalWeights
    );

    const result: ValidationResult = {
      testPrediction,
      controlPrediction,
      actual: null,
      testCorrect: null,
      controlCorrect: null,
      decision: 'pending',
      timestamp: new Date()
    };

    // Store validation for later evaluation
    await memoryService.store(
      `expert:${expertId}:validation:${gameId}`,
      result
    );

    return result;
  }

  async evaluateValidation(
    expertId: string,
    gameId: string,
    actualWinner: string
  ): Promise<'adopt' | 'reject' | 'neutral'> {
    const validation = await memoryService.retrieve<ValidationResult>(
      `expert:${expertId}:validation:${gameId}`
    );

    if (!validation) {
      throw new Error('Validation not found');
    }

    validation.actual = actualWinner;
    validation.testCorrect = validation.testPrediction.winner === actualWinner;
    validation.controlCorrect = validation.controlPrediction.winner === actualWinner;

    // Decision logic
    if (validation.testCorrect && !validation.controlCorrect) {
      validation.decision = 'adopt';
      await this.adoptCorrection(expertId);
    } else if (!validation.testCorrect && validation.controlCorrect) {
      validation.decision = 'reject';
      await this.rollbackCorrection(expertId);
    } else {
      validation.decision = 'pending'; // Need more data
    }

    // Update validation record
    await memoryService.store(
      `expert:${expertId}:validation:${gameId}`,
      validation
    );

    await this.logValidation(expertId, validation);

    return validation.decision === 'pending' ? 'neutral' : validation.decision;
  }

  private async generatePrediction(
    gameData: any,
    weights: FactorWeights
  ): Promise<ValidationResult['testPrediction']> {
    // Use the expert's prediction logic with specified weights
    // This would call the actual expert service methods
    // Simplified for documentation

    const factors = this.calculateFactors(gameData);
    const score = this.calculateScore(factors, weights);

    return {
      winner: score > 0 ? 'home' : 'away',
      confidence: Math.abs(score),
      weights
    };
  }

  private calculateFactors(gameData: any): any {
    // Extract factors from game data
    return {};
  }

  private calculateScore(factors: any, weights: FactorWeights): number {
    // Calculate weighted score
    return 0;
  }

  private async fetchGameData(gameId: string): Promise<any> {
    // Fetch from database or API
    return {};
  }

  private async adoptCorrection(expertId: string): Promise<void> {
    // Correction already applied, just log adoption
    await this.logDecision(expertId, 'adopted', 'Validation successful');
  }

  private async rollbackCorrection(expertId: string): Promise<void> {
    // Restore backup weights
    const backups = await memoryService.list(`expert:${expertId}:backup_weights:*`);
    const latest = backups.sort().pop();

    if (latest) {
      const oldWeights = await memoryService.retrieve<FactorWeights>(latest);
      await memoryService.store(
        `expert:${expertId}:current_weights`,
        oldWeights
      );

      await this.logDecision(expertId, 'rolled_back', 'Validation failed');
    }
  }

  private async logValidation(
    expertId: string,
    validation: ValidationResult
  ): Promise<void> {
    const log = {
      type: 'correction_validation',
      expertId,
      validation,
      timestamp: new Date()
    };

    await memoryService.store(
      `expert:${expertId}:validation_logs:${validation.timestamp.getTime()}`,
      log
    );
  }

  private async logDecision(
    expertId: string,
    decision: string,
    reason: string
  ): Promise<void> {
    const log = {
      type: 'correction_decision',
      expertId,
      decision,
      reason,
      timestamp: new Date()
    };

    await memoryService.store(
      `expert:${expertId}:decisions:${Date.now()}`,
      log
    );
  }
}
```

### Multi-Prediction Validation

For ambiguous results, validate over multiple predictions.

```typescript
class MultiPredictionValidator {
  private readonly VALIDATION_WINDOW = 3; // Validate over 3 games

  async startMultiValidation(
    expertId: string,
    correctionPlan: CorrectionPlan
  ): Promise<string> {
    const validationId = `mv_${Date.now()}`;

    const validation = {
      id: validationId,
      expertId,
      correctionPlan,
      predictions: [],
      testScore: 0,
      controlScore: 0,
      status: 'active',
      startedAt: new Date()
    };

    await memoryService.store(
      `expert:${expertId}:multi_validation:${validationId}`,
      validation
    );

    return validationId;
  }

  async addValidationPrediction(
    expertId: string,
    validationId: string,
    gameId: string,
    actualWinner: string
  ): Promise<'continue' | 'adopt' | 'reject'> {
    const validation = await memoryService.retrieve(
      `expert:${expertId}:multi_validation:${validationId}`
    );

    const singleValidation = await memoryService.retrieve<ValidationResult>(
      `expert:${expertId}:validation:${gameId}`
    );

    if (!singleValidation || !validation) {
      throw new Error('Validation not found');
    }

    // Update scores
    if (singleValidation.testCorrect) validation.testScore++;
    if (singleValidation.controlCorrect) validation.controlScore++;

    validation.predictions.push(gameId);

    // Check if we have enough predictions
    if (validation.predictions.length >= this.VALIDATION_WINDOW) {
      validation.status = 'completed';

      if (validation.testScore > validation.controlScore) {
        await this.adoptCorrection(expertId);
        await this.logMultiValidation(validation, 'adopted');
        return 'adopt';
      } else if (validation.testScore < validation.controlScore) {
        await this.rollbackCorrection(expertId);
        await this.logMultiValidation(validation, 'rejected');
        return 'reject';
      }
      // If tied, adopt (conservative improvement)
      await this.adoptCorrection(expertId);
      await this.logMultiValidation(validation, 'adopted_tie');
      return 'adopt';
    }

    await memoryService.store(
      `expert:${expertId}:multi_validation:${validationId}`,
      validation
    );

    return 'continue';
  }

  private async adoptCorrection(expertId: string): Promise<void> {
    // Weights already applied, just finalize
  }

  private async rollbackCorrection(expertId: string): Promise<void> {
    // Restore from backup
  }

  private async logMultiValidation(validation: any, outcome: string): Promise<void> {
    const log = {
      type: 'multi_validation',
      validation,
      outcome,
      timestamp: new Date()
    };

    await memoryService.store(
      `expert:${validation.expertId}:multi_validation_logs:${Date.now()}`,
      log
    );
  }
}
```

## 5. Rollback Triggers

### Automatic Rollback Conditions

```typescript
interface RollbackTrigger {
  type: 'validation_failed' | 'performance_degraded' | 'manual' | 'safety_threshold';
  reason: string;
  timestamp: Date;
  metrics: {
    accuracyBefore: number;
    accuracyAfter: number;
    confidenceBefore: number;
    confidenceAfter: number;
  };
}

class RollbackManager {
  private readonly PERFORMANCE_THRESHOLD = 0.40; // Rollback if accuracy drops below 40%
  private readonly CONFIDENCE_DROP_THRESHOLD = 0.20; // Rollback if confidence drops >20%

  async checkRollbackConditions(
    expertId: string,
    correctionPlan: CorrectionPlan
  ): Promise<RollbackTrigger | null> {
    // Get performance before correction
    const beforeWindow = await this.getHistoricalWindow(
      expertId,
      correctionPlan.timestamp
    );

    // Get performance after correction
    const afterWindow = await this.getCurrentWindow(expertId);

    if (afterWindow.results.length < 2) {
      return null; // Not enough data yet
    }

    const metrics = {
      accuracyBefore: this.calculateAccuracy(beforeWindow.results),
      accuracyAfter: this.calculateAccuracy(afterWindow.results),
      confidenceBefore: this.averageConfidence(beforeWindow.results),
      confidenceAfter: this.averageConfidence(afterWindow.results)
    };

    // Check performance degradation
    if (metrics.accuracyAfter < this.PERFORMANCE_THRESHOLD) {
      return {
        type: 'performance_degraded',
        reason: `Accuracy dropped to ${(metrics.accuracyAfter * 100).toFixed(1)}%`,
        timestamp: new Date(),
        metrics
      };
    }

    // Check confidence drop
    const confidenceDrop = metrics.confidenceBefore - metrics.confidenceAfter;
    if (confidenceDrop > this.CONFIDENCE_DROP_THRESHOLD) {
      return {
        type: 'safety_threshold',
        reason: `Confidence dropped by ${(confidenceDrop * 100).toFixed(1)}%`,
        timestamp: new Date(),
        metrics
      };
    }

    // Check if making things worse
    if (metrics.accuracyAfter < metrics.accuracyBefore - 0.15) {
      return {
        type: 'performance_degraded',
        reason: 'Correction reduced accuracy',
        timestamp: new Date(),
        metrics
      };
    }

    return null;
  }

  async executeRollback(
    expertId: string,
    trigger: RollbackTrigger
  ): Promise<void> {
    // Find most recent backup
    const backups = await memoryService.list(`expert:${expertId}:backup_weights:*`);
    const latestBackup = backups.sort().pop();

    if (!latestBackup) {
      throw new Error('No backup weights found for rollback');
    }

    const originalWeights = await memoryService.retrieve<FactorWeights>(latestBackup);

    // Restore original weights
    await memoryService.store(
      `expert:${expertId}:current_weights`,
      originalWeights
    );

    // Log rollback
    await this.logRollback(expertId, trigger, originalWeights);

    // Mark expert for manual review
    await memoryService.store(
      `expert:${expertId}:needs_review`,
      {
        reason: trigger.reason,
        trigger,
        timestamp: new Date()
      }
    );
  }

  private calculateAccuracy(results: PredictionResult[]): number {
    const correct = results.filter(r => r.correct).length;
    return correct / results.length;
  }

  private averageConfidence(results: PredictionResult[]): number {
    const sum = results.reduce((acc, r) => acc + r.confidence, 0);
    return sum / results.length;
  }

  private async getHistoricalWindow(
    expertId: string,
    before: Date
  ): Promise<RollingWindow> {
    // Retrieve historical window before correction
    return {} as RollingWindow;
  }

  private async getCurrentWindow(expertId: string): Promise<RollingWindow> {
    // Retrieve current window
    return {} as RollingWindow;
  }

  private async logRollback(
    expertId: string,
    trigger: RollbackTrigger,
    restoredWeights: FactorWeights
  ): Promise<void> {
    const log = {
      type: 'rollback',
      expertId,
      trigger,
      restoredWeights,
      timestamp: new Date()
    };

    await memoryService.store(
      `expert:${expertId}:rollbacks:${Date.now()}`,
      log
    );
  }
}
```

### Manual Override System

```typescript
interface ManualOverride {
  expertId: string;
  action: 'pause_healing' | 'force_rollback' | 'approve_correction' | 'adjust_weights';
  reason: string;
  operator: string;
  timestamp: Date;
  data?: any;
}

class ManualOverrideManager {
  async pauseSelfHealing(
    expertId: string,
    reason: string,
    operator: string
  ): Promise<void> {
    const override: ManualOverride = {
      expertId,
      action: 'pause_healing',
      reason,
      operator,
      timestamp: new Date()
    };

    await memoryService.store(
      `expert:${expertId}:healing_paused`,
      override
    );

    await this.logOverride(override);
  }

  async isHealingPaused(expertId: string): Promise<boolean> {
    const pause = await memoryService.retrieve(
      `expert:${expertId}:healing_paused`
    );
    return pause !== null;
  }

  async resumeSelfHealing(expertId: string): Promise<void> {
    await memoryService.delete(`expert:${expertId}:healing_paused`);
  }

  async forceRollback(
    expertId: string,
    reason: string,
    operator: string
  ): Promise<void> {
    const override: ManualOverride = {
      expertId,
      action: 'force_rollback',
      reason,
      operator,
      timestamp: new Date()
    };

    const rollbackManager = new RollbackManager();
    await rollbackManager.executeRollback(expertId, {
      type: 'manual',
      reason,
      timestamp: new Date(),
      metrics: {} as any
    });

    await this.logOverride(override);
  }

  private async logOverride(override: ManualOverride): Promise<void> {
    await memoryService.store(
      `expert:${override.expertId}:overrides:${Date.now()}`,
      override
    );
  }
}
```

## 6. Transparency & Logging

### Comprehensive Audit Trail

```typescript
interface AuditLog {
  id: string;
  expertId: string;
  eventType: 'detection' | 'analysis' | 'correction' | 'validation' | 'rollback' | 'override';
  timestamp: Date;
  data: any;
  outcome: string;
}

class TransparencyLogger {
  async logHealingEvent(
    expertId: string,
    eventType: AuditLog['eventType'],
    data: any,
    outcome: string
  ): Promise<void> {
    const log: AuditLog = {
      id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      expertId,
      eventType,
      timestamp: new Date(),
      data,
      outcome
    };

    // Store in memory service
    await memoryService.store(
      `expert:${expertId}:audit:${log.id}`,
      log,
      { ttl: 90 * 24 * 60 * 60 } // Keep for 90 days
    );

    // Also append to consolidated log
    await this.appendToConsolidatedLog(log);
  }

  async getHealingHistory(
    expertId: string,
    limit: number = 50
  ): Promise<AuditLog[]> {
    const keys = await memoryService.list(`expert:${expertId}:audit:*`);
    const logs = await Promise.all(
      keys.slice(0, limit).map(key => memoryService.retrieve<AuditLog>(key))
    );

    return logs.filter(log => log !== null).sort((a, b) =>
      b.timestamp.getTime() - a.timestamp.getTime()
    );
  }

  async generateTransparencyReport(expertId: string): Promise<string> {
    const history = await this.getHealingHistory(expertId);

    let report = `# Self-Healing Transparency Report\n\n`;
    report += `**Expert**: ${expertId}\n`;
    report += `**Generated**: ${new Date().toISOString()}\n\n`;

    report += `## Summary\n\n`;
    const corrections = history.filter(h => h.eventType === 'correction').length;
    const rollbacks = history.filter(h => h.eventType === 'rollback').length;
    const validations = history.filter(h => h.eventType === 'validation').length;

    report += `- Total Corrections: ${corrections}\n`;
    report += `- Total Rollbacks: ${rollbacks}\n`;
    report += `- Total Validations: ${validations}\n`;
    report += `- Success Rate: ${((corrections - rollbacks) / corrections * 100).toFixed(1)}%\n\n`;

    report += `## Recent Events\n\n`;
    for (const log of history.slice(0, 10)) {
      report += `### ${log.eventType.toUpperCase()} - ${log.timestamp.toISOString()}\n`;
      report += `**Outcome**: ${log.outcome}\n`;
      report += `**Details**:\n\`\`\`json\n${JSON.stringify(log.data, null, 2)}\n\`\`\`\n\n`;
    }

    return report;
  }

  private async appendToConsolidatedLog(log: AuditLog): Promise<void> {
    // Append to a consolidated log file for easy review
    const logLine = JSON.stringify(log) + '\n';

    // In production, this would write to a file or logging service
    // For now, store in memory with a consolidated key
    const consolidatedKey = `expert:${log.expertId}:consolidated_log`;
    const existing = await memoryService.retrieve<string>(consolidatedKey) || '';
    await memoryService.store(consolidatedKey, existing + logLine);
  }
}
```

### User-Facing Dashboard Data

```typescript
interface DashboardMetrics {
  expertId: string;
  currentAccuracy: number;
  rollingWindowAccuracy: number;
  healingStatus: 'healthy' | 'monitoring' | 'correcting' | 'validating' | 'rolled_back';
  lastCorrection: Date | null;
  totalCorrections: number;
  successfulCorrections: number;
  currentWeights: FactorWeights;
  weightChanges: Array<{
    factor: string;
    change: number;
    timestamp: Date;
  }>;
  pendingValidations: number;
}

class DashboardService {
  async getExpertMetrics(expertId: string): Promise<DashboardMetrics> {
    const window = await this.getRollingWindow(expertId);
    const history = await this.getHealingHistory(expertId);
    const weights = await this.getCurrentWeights(expertId);

    const corrections = history.filter(h => h.eventType === 'correction');
    const rollbacks = history.filter(h => h.eventType === 'rollback');

    const status = await this.determineStatus(expertId, window);

    return {
      expertId,
      currentAccuracy: this.calculateCurrentAccuracy(expertId),
      rollingWindowAccuracy: window.accuracy,
      healingStatus: status,
      lastCorrection: corrections[0]?.timestamp || null,
      totalCorrections: corrections.length,
      successfulCorrections: corrections.length - rollbacks.length,
      currentWeights: weights,
      weightChanges: await this.getRecentWeightChanges(expertId),
      pendingValidations: await this.countPendingValidations(expertId)
    };
  }

  private calculateCurrentAccuracy(expertId: string): number {
    // Calculate current accuracy
    return 0;
  }

  private async getRollingWindow(expertId: string): Promise<RollingWindow> {
    return {} as RollingWindow;
  }

  private async getHealingHistory(expertId: string): Promise<AuditLog[]> {
    return [];
  }

  private async getCurrentWeights(expertId: string): Promise<FactorWeights> {
    return {} as FactorWeights;
  }

  private async determineStatus(
    expertId: string,
    window: RollingWindow
  ): Promise<DashboardMetrics['healingStatus']> {
    const isPaused = await memoryService.retrieve(`expert:${expertId}:healing_paused`);
    if (isPaused) return 'monitoring';

    const validations = await memoryService.list(`expert:${expertId}:validation:*`);
    if (validations.length > 0) return 'validating';

    if (window.accuracy < 0.50) return 'correcting';

    return 'healthy';
  }

  private async getRecentWeightChanges(
    expertId: string
  ): Promise<DashboardMetrics['weightChanges']> {
    const corrections = await memoryService.list(`expert:${expertId}:corrections:*`);
    const recent = corrections.slice(0, 5);

    const changes: DashboardMetrics['weightChanges'] = [];

    for (const key of recent) {
      const correction = await memoryService.retrieve<any>(key);
      for (const change of correction.changes) {
        changes.push({
          factor: change.factor,
          change: change.percentChange,
          timestamp: correction.timestamp
        });
      }
    }

    return changes;
  }

  private async countPendingValidations(expertId: string): Promise<number> {
    const validations = await memoryService.list(`expert:${expertId}:validation:*`);
    const pending = await Promise.all(
      validations.map(key => memoryService.retrieve<ValidationResult>(key))
    );

    return pending.filter(v => v && v.decision === 'pending').length;
  }
}
```

## 7. Implementation Integration

### Service Integration

```typescript
// In expert-service.ts

class ExpertServiceWithHealing {
  private failureDetector: FailureDetector;
  private rootCauseAnalyzer: RootCauseAnalyzer;
  private patternRecognizer: PatternRecognizer;
  private weightCorrector: WeightCorrector;
  private validator: CorrectionValidator;
  private rollbackManager: RollbackManager;
  private logger: TransparencyLogger;

  constructor() {
    this.failureDetector = new FailureDetector();
    this.rootCauseAnalyzer = new RootCauseAnalyzer();
    this.patternRecognizer = new PatternRecognizer();
    this.weightCorrector = new WeightCorrector();
    this.validator = new CorrectionValidator();
    this.rollbackManager = new RollbackManager();
    this.logger = new TransparencyLogger();
  }

  async generatePrediction(expertId: string, gameId: string): Promise<any> {
    // Check if healing is needed BEFORE making prediction
    const healthCheck = await this.failureDetector.checkPerformance(expertId);

    if (healthCheck.needsHealing) {
      await this.initiateHealingProcess(expertId, healthCheck);
    }

    // Generate prediction with current (possibly corrected) weights
    const prediction = await this.makePrediction(expertId, gameId);

    // Check for active validations
    const validations = await this.checkActiveValidations(expertId);
    if (validations.length > 0) {
      // Generate both test and control predictions for validation
      await this.validator.validateCorrection(expertId, gameId, validations[0]);
    }

    return prediction;
  }

  async recordPredictionResult(
    expertId: string,
    gameId: string,
    actual: string
  ): Promise<void> {
    // Record result in rolling window
    await this.updateRollingWindow(expertId, gameId, actual);

    // Check if this completes a validation
    const validation = await memoryService.retrieve<ValidationResult>(
      `expert:${expertId}:validation:${gameId}`
    );

    if (validation) {
      const decision = await this.validator.evaluateValidation(
        expertId,
        gameId,
        actual
      );

      await this.logger.logHealingEvent(
        expertId,
        'validation',
        { gameId, decision },
        `Validation ${decision}`
      );
    }

    // Check rollback conditions
    const correctionPlan = await this.getLatestCorrection(expertId);
    if (correctionPlan) {
      const rollbackTrigger = await this.rollbackManager.checkRollbackConditions(
        expertId,
        correctionPlan
      );

      if (rollbackTrigger) {
        await this.rollbackManager.executeRollback(expertId, rollbackTrigger);
        await this.logger.logHealingEvent(
          expertId,
          'rollback',
          rollbackTrigger,
          'Automatic rollback executed'
        );
      }
    }
  }

  private async initiateHealingProcess(
    expertId: string,
    healthCheck: any
  ): Promise<void> {
    await this.logger.logHealingEvent(
      expertId,
      'detection',
      healthCheck,
      'Performance degradation detected'
    );

    // Get rolling window
    const window = await this.getRollingWindow(expertId);

    // Analyze root causes
    const factorAnalyses = await this.rootCauseAnalyzer.analyzeFactors(
      expertId,
      window
    );

    const patterns = await this.patternRecognizer.identifySystemicIssues(window);

    await this.logger.logHealingEvent(
      expertId,
      'analysis',
      { factorAnalyses, patterns },
      'Root cause analysis completed'
    );

    // Create correction plan
    const currentWeights = await this.getCurrentWeights(expertId);
    const correctionPlan = await this.weightCorrector.createCorrectionPlan(
      expertId,
      currentWeights,
      factorAnalyses,
      patterns
    );

    // Apply correction
    await this.weightCorrector.applyCorrectionPlan(correctionPlan);

    await this.logger.logHealingEvent(
      expertId,
      'correction',
      correctionPlan,
      'Correction applied, awaiting validation'
    );
  }

  private async makePrediction(expertId: string, gameId: string): Promise<any> {
    // Implementation
    return {};
  }

  private async checkActiveValidations(expertId: string): Promise<any[]> {
    return [];
  }

  private async updateRollingWindow(
    expertId: string,
    gameId: string,
    actual: string
  ): Promise<void> {
    // Implementation
  }

  private async getLatestCorrection(expertId: string): Promise<CorrectionPlan | null> {
    const corrections = await memoryService.list(`expert:${expertId}:corrections:*`);
    if (corrections.length === 0) return null;

    const latest = corrections.sort().pop();
    return await memoryService.retrieve<CorrectionPlan>(latest);
  }

  private async getRollingWindow(expertId: string): Promise<RollingWindow> {
    return {} as RollingWindow;
  }

  private async getCurrentWeights(expertId: string): Promise<FactorWeights> {
    return {} as FactorWeights;
  }
}
```

## 8. Testing Strategy

### Unit Tests

```typescript
describe('Self-Healing System', () => {
  describe('FailureDetector', () => {
    it('should detect when accuracy drops below 50%', async () => {
      const detector = new FailureDetector();
      // Setup test data with 2/5 correct predictions
      const result = await detector.checkPerformance('test-expert');
      expect(result.needsHealing).toBe(true);
    });

    it('should not trigger with insufficient predictions', async () => {
      const detector = new FailureDetector();
      // Setup with only 2 predictions
      const result = await detector.checkPerformance('test-expert');
      expect(result.needsHealing).toBe(false);
    });
  });

  describe('WeightCorrector', () => {
    it('should limit adjustments to 25% per correction', async () => {
      const corrector = new WeightCorrector();
      // Test that large swings are constrained
    });

    it('should normalize weights after adjustment', async () => {
      const corrector = new WeightCorrector();
      // Test normalization logic
    });
  });

  describe('CorrectionValidator', () => {
    it('should adopt correction when test outperforms control', async () => {
      const validator = new CorrectionValidator();
      // Test validation logic
    });
  });
});
```

### Integration Tests

```typescript
describe('Self-Healing Integration', () => {
  it('should complete full healing cycle', async () => {
    // 1. Setup expert with declining accuracy
    // 2. Trigger healing detection
    // 3. Verify correction applied
    // 4. Validate correction
    // 5. Verify weights updated or rolled back
  });

  it('should rollback failed corrections', async () => {
    // Test rollback flow
  });
});
```

## 9. Monitoring & Alerts

### Key Metrics to Track

1. **Healing Frequency**: How often healing is triggered per expert
2. **Correction Success Rate**: % of corrections that improve performance
3. **Rollback Rate**: % of corrections that get rolled back
4. **Average Recovery Time**: Time from detection to validated correction
5. **Weight Stability**: How much weights fluctuate over time

### Alert Thresholds

- **Critical**: Expert accuracy < 40% after 3 games
- **Warning**: Healing triggered 3+ times in 1 week
- **Info**: Correction applied successfully
- **Error**: Rollback executed

## 10. Future Enhancements

1. **Multi-Factor Learning**: Learn correlations between factors
2. **Seasonal Adjustments**: Adapt to playoff vs regular season
3. **Team-Specific Models**: Custom weights per team matchup
4. **Ensemble Corrections**: Average multiple correction strategies
5. **Predictive Healing**: Anticipate failures before they occur
6. **Cross-Expert Learning**: Share successful corrections across experts

## Summary

This self-healing system provides:

- ✅ Automatic failure detection with 5-game rolling window
- ✅ Root cause analysis identifying problematic factors
- ✅ Constrained weight corrections (max 25% change)
- ✅ A/B testing validation before full adoption
- ✅ Automatic rollback on validation failure
- ✅ Complete transparency with audit logging
- ✅ Manual override capabilities
- ✅ Dashboard metrics for monitoring

The system balances automation with safety, ensuring experts continuously improve while preventing catastrophic failures.