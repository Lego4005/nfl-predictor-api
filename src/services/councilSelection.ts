/**
 * AI Council Selection Algorithm
 * Manages the dynamic selection of top 5 experts for the AI Council
 */

import { ExpertPersonality, EXPERT_PERSONALITIES } from '@/data/expertPersonalities';
import { PredictionCategory } from '@/types/predictions';

export interface CouncilSelectionCriteria {
  overall_accuracy_weight: number; // 35%
  recent_performance_weight: number; // 25%
  consistency_weight: number; // 20%
  confidence_calibration_weight: number; // 10%
  specialization_weight: number; // 10%
}

export interface CouncilMember extends ExpertPersonality {
  selection_score: number;
  rank: number;
  voting_weight: number;
  selection_reasons: string[];
  promotion_from?: number; // Previous rank if promoted
  demotion_from?: number; // Previous rank if demoted
}

export interface CouncilSelection {
  council_members: CouncilMember[];
  selection_timestamp: string;
  next_evaluation: string;
  selection_criteria: CouncilSelectionCriteria;
  changes: CouncilChange[];
  performance_summary: {
    average_accuracy: number;
    total_predictions: number;
    confidence_calibration: number;
    specialization_coverage: Record<PredictionCategory, number>;
  };
}

export interface CouncilChange {
  type: 'promotion' | 'demotion' | 'new_member' | 'removed';
  expert_id: string;
  expert_name: string;
  old_position?: number;
  new_position?: number;
  reason: string;
  impact_score: number; // -10 to 10
}

const DEFAULT_SELECTION_CRITERIA: CouncilSelectionCriteria = {
  overall_accuracy_weight: 0.35,
  recent_performance_weight: 0.25,
  consistency_weight: 0.20,
  confidence_calibration_weight: 0.10,
  specialization_weight: 0.10
};

export class CouncilSelectionAlgorithm {
  private criteria: CouncilSelectionCriteria;
  private currentCouncil: CouncilMember[] = [];

  constructor(criteria: CouncilSelectionCriteria = DEFAULT_SELECTION_CRITERIA) {
    this.criteria = criteria;
    this.initializeCurrentCouncil();
  }

  private initializeCurrentCouncil(): void {
    // Initialize with current council members from expert personalities
    this.currentCouncil = EXPERT_PERSONALITIES
      .filter(expert => expert.council_position !== undefined)
      .map(expert => this.convertToCouncilMember(expert, 0, []))
      .sort((a, b) => (a.council_position || 0) - (b.council_position || 0));
  }

  /**
   * Calculate selection score for an expert
   */
  private calculateSelectionScore(expert: ExpertPersonality): number {
    // Overall accuracy component (35%)
    const accuracyScore = expert.accuracy_metrics.overall * this.criteria.overall_accuracy_weight;

    // Recent performance component (25%)
    const recentScore = expert.accuracy_metrics.recent_performance * this.criteria.recent_performance_weight;

    // Consistency score (20%) - based on standard deviation of performance
    const consistencyScore = this.calculateConsistencyScore(expert) * this.criteria.consistency_weight;

    // Confidence calibration component (10%)
    const calibrationScore = expert.confidence_calibration * this.criteria.confidence_calibration_weight;

    // Specialization strength component (10%)
    const specializationScore = this.calculateSpecializationScore(expert) * this.criteria.specialization_weight;

    return accuracyScore + recentScore + consistencyScore + calibrationScore + specializationScore;
  }

  /**
   * Calculate consistency score based on performance variance
   */
  private calculateConsistencyScore(expert: ExpertPersonality): number {
    // Mock calculation - in real implementation, use historical performance data
    const categoryAccuracies = Object.values(expert.accuracy_metrics.by_category);
    const mean = categoryAccuracies.reduce((sum, acc) => sum + acc, 0) / categoryAccuracies.length;
    const variance = categoryAccuracies.reduce((sum, acc) => sum + Math.pow(acc - mean, 2), 0) / categoryAccuracies.length;
    const standardDeviation = Math.sqrt(variance);
    
    // Lower standard deviation = higher consistency
    // Normalize to 0-1 scale (assuming max std dev of 0.2)
    return Math.max(0, 1 - (standardDeviation / 0.2));
  }

  /**
   * Calculate specialization score based on category expertise
   */
  private calculateSpecializationScore(expert: ExpertPersonality): number {
    // Calculate average accuracy in primary expertise areas
    const primaryAccuracies = expert.primary_expertise.map(category => 
      expert.accuracy_metrics.by_category[category] || 0
    );
    
    return primaryAccuracies.reduce((sum, acc) => sum + acc, 0) / primaryAccuracies.length;
  }

  /**
   * Calculate voting weight based on performance metrics
   */
  private calculateVotingWeight(expert: ExpertPersonality, rank: number): number {
    // Base weight distribution: 1st: 24%, 2nd: 22%, 3rd: 20%, 4th: 18%, 5th: 16%
    const baseWeights = [0.24, 0.22, 0.20, 0.18, 0.16];
    const baseWeight = baseWeights[rank - 1] || 0.16;

    // Adjust based on performance relative to other council members
    const performanceMultiplier = Math.min(1.2, expert.accuracy_metrics.overall / 0.6);
    
    return Math.round(baseWeight * performanceMultiplier * 100) / 100;
  }

  /**
   * Generate selection reasons for a council member
   */
  private generateSelectionReasons(expert: ExpertPersonality, rank: number): string[] {
    const reasons: string[] = [];
    
    if (expert.accuracy_metrics.overall >= 0.7) {
      reasons.push(`Exceptional overall accuracy (${(expert.accuracy_metrics.overall * 100).toFixed(1)}%)`);
    }
    
    if (expert.accuracy_metrics.recent_performance > expert.accuracy_metrics.overall) {
      reasons.push('Improving recent performance trend');
    }
    
    if (expert.confidence_calibration >= 0.8) {
      reasons.push('Excellent confidence calibration');
    }
    
    if (expert.primary_expertise.length >= 2) {
      reasons.push(`Multi-category expertise (${expert.primary_expertise.join(', ')})`);
    }
    
    if (rank === 1) {
      reasons.push('Top-ranked expert with consistent performance');
    }
    
    return reasons;
  }

  /**
   * Convert expert to council member
   */
  private convertToCouncilMember(
    expert: ExpertPersonality, 
    selectionScore: number,
    reasons: string[]
  ): CouncilMember {
    const rank = expert.council_position || 0;
    return {
      ...expert,
      selection_score: selectionScore,
      rank,
      voting_weight: this.calculateVotingWeight(expert, rank),
      selection_reasons: reasons,
      council_position: rank,
      council_weight: this.calculateVotingWeight(expert, rank)
    };
  }

  /**
   * Detect changes between old and new council
   */
  private detectChanges(oldCouncil: CouncilMember[], newCouncil: CouncilMember[]): CouncilChange[] {
    const changes: CouncilChange[] = [];
    
    // Create maps for easy lookup
    const oldMap = new Map(oldCouncil.map(member => [member.id, member]));
    const newMap = new Map(newCouncil.map(member => [member.id, member]));
    
    // Check for promotions, demotions, and position changes
    newCouncil.forEach(newMember => {
      const oldMember = oldMap.get(newMember.id);
      
      if (!oldMember) {
        // New member
        changes.push({
          type: 'new_member',
          expert_id: newMember.id,
          expert_name: newMember.name,
          new_position: newMember.rank,
          reason: `Promoted to council with selection score of ${newMember.selection_score.toFixed(3)}`,
          impact_score: 8
        });
      } else if (oldMember.rank !== newMember.rank) {
        // Position change
        const isPromotion = newMember.rank < oldMember.rank;
        changes.push({
          type: isPromotion ? 'promotion' : 'demotion',
          expert_id: newMember.id,
          expert_name: newMember.name,
          old_position: oldMember.rank,
          new_position: newMember.rank,
          reason: isPromotion 
            ? `Improved performance (score: ${newMember.selection_score.toFixed(3)})`
            : `Declining performance (score: ${newMember.selection_score.toFixed(3)})`,
          impact_score: isPromotion ? 6 : -6
        });
      }
    });
    
    // Check for removed members
    oldCouncil.forEach(oldMember => {
      if (!newMap.has(oldMember.id)) {
        changes.push({
          type: 'removed',
          expert_id: oldMember.id,
          expert_name: oldMember.name,
          old_position: oldMember.rank,
          reason: 'Removed due to poor performance',
          impact_score: -8
        });
      }
    });
    
    return changes;
  }

  /**
   * Calculate performance summary for the council
   */
  private calculatePerformanceSummary(council: CouncilMember[]): CouncilSelection['performance_summary'] {
    const totalPredictions = council.reduce((sum, member) => 
      sum + member.track_record.total_predictions, 0);
    
    const averageAccuracy = council.reduce((sum, member) => 
      sum + member.accuracy_metrics.overall, 0) / council.length;
    
    const averageCalibration = council.reduce((sum, member) => 
      sum + member.confidence_calibration, 0) / council.length;
    
    // Calculate specialization coverage
    const specializationCoverage: Record<PredictionCategory, number> = {
      core: 0,
      props: 0,
      live: 0,
      situational: 0,
      advanced: 0
    };
    
    council.forEach(member => {
      member.primary_expertise.forEach(category => {
        specializationCoverage[category] += 1;
      });
    });
    
    return {
      average_accuracy: averageAccuracy,
      total_predictions: totalPredictions,
      confidence_calibration: averageCalibration,
      specialization_coverage: specializationCoverage
    };
  }

  /**
   * Perform council selection
   */
  public selectCouncil(): CouncilSelection {
    // Calculate selection scores for all experts
    const scoredExperts = EXPERT_PERSONALITIES.map(expert => ({
      expert,
      score: this.calculateSelectionScore(expert),
      reasons: this.generateSelectionReasons(expert, 0)
    }));
    
    // Sort by selection score (descending)
    scoredExperts.sort((a, b) => b.score - a.score);
    
    // Select top 5 for council
    const newCouncil: CouncilMember[] = scoredExperts.slice(0, 5).map((item, index) => {
      const rank = index + 1;
      return this.convertToCouncilMember(item.expert, item.score, item.reasons);
    });
    
    // Update ranks and voting weights
    newCouncil.forEach((member, index) => {
      member.rank = index + 1;
      member.voting_weight = this.calculateVotingWeight(member, member.rank);
    });
    
    // Detect changes
    const changes = this.detectChanges(this.currentCouncil, newCouncil);
    
    // Update current council
    this.currentCouncil = newCouncil;
    
    // Calculate next evaluation date (weekly on Tuesdays)
    const nextEvaluation = new Date();
    nextEvaluation.setDate(nextEvaluation.getDate() + 7);
    nextEvaluation.setHours(9, 0, 0, 0); // 9 AM Tuesday
    
    return {
      council_members: newCouncil,
      selection_timestamp: new Date().toISOString(),
      next_evaluation: nextEvaluation.toISOString(),
      selection_criteria: this.criteria,
      changes,
      performance_summary: this.calculatePerformanceSummary(newCouncil)
    };
  }

  /**
   * Get current council
   */
  public getCurrentCouncil(): CouncilMember[] {
    return this.currentCouncil;
  }

  /**
   * Update selection criteria
   */
  public updateCriteria(criteria: Partial<CouncilSelectionCriteria>): void {
    this.criteria = { ...this.criteria, ...criteria };
  }

  /**
   * Simulate council selection with different criteria
   */
  public simulateSelection(criteria: Partial<CouncilSelectionCriteria>): CouncilSelection {
    const originalCriteria = { ...this.criteria };
    this.updateCriteria(criteria);
    
    const result = this.selectCouncil();
    
    // Restore original criteria
    this.criteria = originalCriteria;
    
    return result;
  }
}

// Export singleton instance
export const councilSelector = new CouncilSelectionAlgorithm();

// Helper functions
export const getCurrentCouncil = (): CouncilMember[] => {
  return councilSelector.getCurrentCouncil();
};

export const performCouncilSelection = (): CouncilSelection => {
  return councilSelector.selectCouncil();
};

export const simulateCouncilSelection = (criteria: Partial<CouncilSelectionCriteria>): CouncilSelection => {
  return councilSelector.simulateSelection(criteria);
};