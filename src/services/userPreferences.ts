/**
 * User Prediction Access Modes and Preference System
 * Manages how users access and customize their prediction experience
 */

import { ExpertPersonality } from '@/data/expertPersonalities';
import { PredictionCategory } from '@/types/predictions';

export type PredictionAccessMode = 
  | 'council_consensus'      // AI Council consensus (default)
  | 'individual_expert'      // Follow specific expert
  | 'category_shopping'      // Mix experts by category
  | 'confidence_based'       // Follow highest confidence
  | 'contrarian_mode'        // Fade the consensus
  | 'custom_weighted';       // Custom expert weights

export interface UserPreferences {
  id: string;
  userId: string;
  
  // Prediction Access Settings
  predictionMode: PredictionAccessMode;
  selectedExpertId?: string; // For individual_expert mode
  customWeights?: Record<string, number>; // For custom_weighted mode
  categoryExperts?: Record<PredictionCategory, string>; // For category_shopping mode
  
  // Content Preferences
  showExpertReasoning: boolean;
  showConfidenceIntervals: boolean;
  showHistoricalAccuracy: boolean;
  showBettingOdds: boolean;
  showMarketMovement: boolean;
  
  // Notification Settings
  expertRankingChanges: boolean;
  consensusUpdates: boolean;
  predictionAlerts: boolean;
  gameStartReminders: boolean;
  
  // Display Preferences
  expertDisplayMode: 'grid' | 'list' | 'compact';
  predictionSortBy: 'confidence' | 'category' | 'expert' | 'time';
  hideLowConfidencePredictions: boolean;
  minConfidenceThreshold: number;
  
  // Risk Preferences
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  valueThreshold: number; // Minimum expected value for bet recommendations
  bankrollManagement: boolean;
  
  // Advanced Settings
  enableLivePredictions: boolean;
  autoUpdateFrequency: number; // seconds
  experimentalFeatures: boolean;
  
  // Favorites and Follows
  favoriteExperts: string[];
  followedTeams: string[];
  favoriteCategories: PredictionCategory[];
  
  // Performance Tracking
  trackPersonalAccuracy: boolean;
  compareToExperts: boolean;
  showPersonalStats: boolean;
  
  createdAt: string;
  updatedAt: string;
}

export interface PredictionAccess {
  mode: PredictionAccessMode;
  description: string;
  icon: string;
  features: string[];
  expertSelection: ExpertSelectionStrategy;
  confidenceWeighting: ConfidenceWeightingStrategy;
  riskProfile: 'low' | 'medium' | 'high';
  recommended: boolean;
}

export interface ExpertSelectionStrategy {
  type: 'consensus' | 'single' | 'weighted' | 'category_specific' | 'performance_based';
  criteria: string[];
  fallback?: string; // What to do when primary strategy fails
}

export interface ConfidenceWeightingStrategy {
  type: 'equal' | 'performance_weighted' | 'confidence_weighted' | 'recency_weighted';
  parameters: Record<string, number>;
}

export const PREDICTION_ACCESS_MODES: Record<PredictionAccessMode, PredictionAccess> = {
  council_consensus: {
    mode: 'council_consensus',
    description: 'Follow AI Council consensus predictions with weighted voting',
    icon: '👑',
    features: [
      'Top 5 expert consensus',
      'Performance-weighted voting',
      'Transparent decision process',
      'Highest overall accuracy'
    ],
    expertSelection: {
      type: 'consensus',
      criteria: ['council_membership', 'voting_weight', 'recent_performance'],
      fallback: 'highest_accuracy'
    },
    confidenceWeighting: {
      type: 'performance_weighted',
      parameters: {
        accuracy_weight: 0.4,
        recent_performance_weight: 0.3,
        confidence_calibration_weight: 0.3
      }
    },
    riskProfile: 'medium',
    recommended: true
  },

  individual_expert: {
    mode: 'individual_expert',
    description: 'Follow predictions from a single chosen expert',
    icon: '🎯',
    features: [
      'Complete expert loyalty',
      'Consistent prediction style',
      'Deep expert analysis',
      'Personal connection'
    ],
    expertSelection: {
      type: 'single',
      criteria: ['user_selection'],
      fallback: 'council_consensus'
    },
    confidenceWeighting: {
      type: 'equal',
      parameters: {}
    },
    riskProfile: 'medium',
    recommended: false
  },

  category_shopping: {
    mode: 'category_shopping',
    description: 'Choose different experts for different prediction categories',
    icon: '🛒',
    features: [
      'Category-specific expertise',
      'Specialized knowledge',
      'Flexible approach',
      'Optimized accuracy per category'
    ],
    expertSelection: {
      type: 'category_specific',
      criteria: ['category_accuracy', 'specialization_match', 'confidence_calibration'],
      fallback: 'highest_category_accuracy'
    },
    confidenceWeighting: {
      type: 'confidence_weighted',
      parameters: {
        confidence_multiplier: 1.2,
        min_confidence: 0.5
      }
    },
    riskProfile: 'medium',
    recommended: false
  },

  confidence_based: {
    mode: 'confidence_based',
    description: 'Follow the highest confidence predictions regardless of expert',
    icon: '💪',
    features: [
      'Maximum confidence',
      'Dynamic expert selection',
      'High conviction plays',
      'Performance-driven'
    ],
    expertSelection: {
      type: 'performance_based',
      criteria: ['confidence_level', 'confidence_calibration', 'category_accuracy'],
      fallback: 'highest_confidence'
    },
    confidenceWeighting: {
      type: 'confidence_weighted',
      parameters: {
        confidence_threshold: 0.75,
        confidence_multiplier: 1.5
      }
    },
    riskProfile: 'high',
    recommended: false
  },

  contrarian_mode: {
    mode: 'contrarian_mode',
    description: 'Fade consensus and find value in unpopular opinions',
    icon: '🏴‍☠️',
    features: [
      'Anti-consensus approach',
      'Value identification',
      'Market inefficiency exploitation',
      'High risk/reward potential'
    ],
    expertSelection: {
      type: 'consensus',
      criteria: ['minority_opinion', 'contrarian_success', 'value_identification'],
      fallback: 'lowest_consensus'
    },
    confidenceWeighting: {
      type: 'recency_weighted',
      parameters: {
        recency_factor: 0.8,
        contrarian_boost: 1.3
      }
    },
    riskProfile: 'high',
    recommended: false
  },

  custom_weighted: {
    mode: 'custom_weighted',
    description: 'Create your own expert weighting system',
    icon: '⚖️',
    features: [
      'Full customization',
      'Personal weighting',
      'Advanced control',
      'Experimental approach'
    ],
    expertSelection: {
      type: 'weighted',
      criteria: ['user_weights', 'expert_availability'],
      fallback: 'equal_weights'
    },
    confidenceWeighting: {
      type: 'equal',
      parameters: {}
    },
    riskProfile: 'medium',
    recommended: false
  }
};

export class UserPreferenceManager {
  private preferences: UserPreferences;
  private storageKey: string;

  constructor(userId: string) {
    this.storageKey = `user_preferences_${userId}`;
    this.preferences = this.loadPreferences(userId);
  }

  private getDefaultPreferences(userId: string): UserPreferences {
    return {
      id: `pref_${userId}_${Date.now()}`,
      userId,
      
      // Prediction Access Settings
      predictionMode: 'council_consensus',
      selectedExpertId: undefined,
      customWeights: undefined,
      categoryExperts: undefined,
      
      // Content Preferences
      showExpertReasoning: true,
      showConfidenceIntervals: true,
      showHistoricalAccuracy: true,
      showBettingOdds: true,
      showMarketMovement: false,
      
      // Notification Settings
      expertRankingChanges: true,
      consensusUpdates: false,
      predictionAlerts: true,
      gameStartReminders: true,
      
      // Display Preferences
      expertDisplayMode: 'grid',
      predictionSortBy: 'confidence',
      hideLowConfidencePredictions: false,
      minConfidenceThreshold: 0.5,
      
      // Risk Preferences
      riskTolerance: 'moderate',
      valueThreshold: 0.02, // 2% edge minimum
      bankrollManagement: true,
      
      // Advanced Settings
      enableLivePredictions: true,
      autoUpdateFrequency: 30,
      experimentalFeatures: false,
      
      // Favorites and Follows
      favoriteExperts: [],
      followedTeams: [],
      favoriteCategories: ['core', 'props'],
      
      // Performance Tracking
      trackPersonalAccuracy: true,
      compareToExperts: true,
      showPersonalStats: true,
      
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  private loadPreferences(userId: string): UserPreferences {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Merge with defaults to ensure all properties exist
        return { ...this.getDefaultPreferences(userId), ...parsed };
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
    
    return this.getDefaultPreferences(userId);
  }

  private savePreferences(): void {
    try {
      this.preferences.updatedAt = new Date().toISOString();
      localStorage.setItem(this.storageKey, JSON.stringify(this.preferences));
    } catch (error) {
      console.error('Error saving user preferences:', error);
    }
  }

  // Getters
  public getPreferences(): UserPreferences {
    return { ...this.preferences };
  }

  public getPredictionMode(): PredictionAccessMode {
    return this.preferences.predictionMode;
  }

  public getSelectedExpert(): string | undefined {
    return this.preferences.selectedExpertId;
  }

  public getCategoryExperts(): Record<PredictionCategory, string> | undefined {
    return this.preferences.categoryExperts;
  }

  public getCustomWeights(): Record<string, number> | undefined {
    return this.preferences.customWeights;
  }

  public getRiskTolerance(): 'conservative' | 'moderate' | 'aggressive' {
    return this.preferences.riskTolerance;
  }

  public getMinConfidenceThreshold(): number {
    return this.preferences.minConfidenceThreshold;
  }

  public getFavoriteExperts(): string[] {
    return [...this.preferences.favoriteExperts];
  }

  // Setters
  public setPredictionMode(mode: PredictionAccessMode): void {
    this.preferences.predictionMode = mode;
    this.savePreferences();
  }

  public setSelectedExpert(expertId: string | undefined): void {
    this.preferences.selectedExpertId = expertId;
    if (expertId) {
      this.preferences.predictionMode = 'individual_expert';
    }
    this.savePreferences();
  }

  public setCategoryExperts(categoryExperts: Record<PredictionCategory, string>): void {
    this.preferences.categoryExperts = categoryExperts;
    this.preferences.predictionMode = 'category_shopping';
    this.savePreferences();
  }

  public setCustomWeights(weights: Record<string, number>): void {
    this.preferences.customWeights = weights;
    this.preferences.predictionMode = 'custom_weighted';
    this.savePreferences();
  }

  public updateContentPreferences(updates: Partial<Pick<UserPreferences, 
    'showExpertReasoning' | 'showConfidenceIntervals' | 'showHistoricalAccuracy' | 
    'showBettingOdds' | 'showMarketMovement'>>): void {
    Object.assign(this.preferences, updates);
    this.savePreferences();
  }

  public updateDisplayPreferences(updates: Partial<Pick<UserPreferences,
    'expertDisplayMode' | 'predictionSortBy' | 'hideLowConfidencePredictions' | 
    'minConfidenceThreshold'>>): void {
    Object.assign(this.preferences, updates);
    this.savePreferences();
  }

  public updateNotificationSettings(updates: Partial<Pick<UserPreferences,
    'expertRankingChanges' | 'consensusUpdates' | 'predictionAlerts' | 
    'gameStartReminders'>>): void {
    Object.assign(this.preferences, updates);
    this.savePreferences();
  }

  public updateRiskPreferences(updates: Partial<Pick<UserPreferences,
    'riskTolerance' | 'valueThreshold' | 'bankrollManagement'>>): void {
    Object.assign(this.preferences, updates);
    this.savePreferences();
  }

  public addFavoriteExpert(expertId: string): void {
    if (!this.preferences.favoriteExperts.includes(expertId)) {
      this.preferences.favoriteExperts.push(expertId);
      this.savePreferences();
    }
  }

  public removeFavoriteExpert(expertId: string): void {
    const index = this.preferences.favoriteExperts.indexOf(expertId);
    if (index > -1) {
      this.preferences.favoriteExperts.splice(index, 1);
      this.savePreferences();
    }
  }

  public addFollowedTeam(teamId: string): void {
    if (!this.preferences.followedTeams.includes(teamId)) {
      this.preferences.followedTeams.push(teamId);
      this.savePreferences();
    }
  }

  public removeFollowedTeam(teamId: string): void {
    const index = this.preferences.followedTeams.indexOf(teamId);
    if (index > -1) {
      this.preferences.followedTeams.splice(index, 1);
      this.savePreferences();
    }
  }

  // Utility methods
  public shouldShowExpertReasoning(): boolean {
    return this.preferences.showExpertReasoning;
  }

  public shouldShowConfidenceIntervals(): boolean {
    return this.preferences.showConfidenceIntervals;
  }

  public shouldShowBettingOdds(): boolean {
    return this.preferences.showBettingOdds;
  }

  public shouldHideLowConfidencePredictions(): boolean {
    return this.preferences.hideLowConfidencePredictions;
  }

  public isExpertFavorited(expertId: string): boolean {
    return this.preferences.favoriteExperts.includes(expertId);
  }

  public isTeamFollowed(teamId: string): boolean {
    return this.preferences.followedTeams.includes(teamId);
  }

  public getAccessModeConfig(): PredictionAccess {
    return PREDICTION_ACCESS_MODES[this.preferences.predictionMode];
  }

  public validateCustomWeights(weights: Record<string, number>): boolean {
    const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
    return Math.abs(total - 1.0) < 0.01; // Allow small floating point errors
  }

  public normalizeCustomWeights(weights: Record<string, number>): Record<string, number> {
    const total = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
    const normalized: Record<string, number> = {};
    
    for (const [expertId, weight] of Object.entries(weights)) {
      normalized[expertId] = weight / total;
    }
    
    return normalized;
  }

  // Reset methods
  public resetToDefaults(): void {
    const userId = this.preferences.userId;
    this.preferences = this.getDefaultPreferences(userId);
    this.savePreferences();
  }

  public resetPredictionMode(): void {
    this.preferences.predictionMode = 'council_consensus';
    this.preferences.selectedExpertId = undefined;
    this.preferences.customWeights = undefined;
    this.preferences.categoryExperts = undefined;
    this.savePreferences();
  }

  // Export/Import
  public exportPreferences(): string {
    return JSON.stringify(this.preferences, null, 2);
  }

  public importPreferences(preferencesJson: string): boolean {
    try {
      const imported = JSON.parse(preferencesJson);
      // Validate structure
      if (imported.userId && imported.predictionMode) {
        this.preferences = { ...this.getDefaultPreferences(imported.userId), ...imported };
        this.savePreferences();
        return true;
      }
    } catch (error) {
      console.error('Error importing preferences:', error);
    }
    return false;
  }
}

// Global preference manager instance
let globalPreferenceManager: UserPreferenceManager | null = null;

export const getUserPreferenceManager = (userId: string): UserPreferenceManager => {
  if (!globalPreferenceManager || globalPreferenceManager.getPreferences().userId !== userId) {
    globalPreferenceManager = new UserPreferenceManager(userId);
  }
  return globalPreferenceManager;
};

// Utility functions
export const getRecommendedAccessMode = (
  userExperience: 'beginner' | 'intermediate' | 'advanced',
  riskTolerance: 'conservative' | 'moderate' | 'aggressive'
): PredictionAccessMode => {
  if (userExperience === 'beginner') {
    return 'council_consensus';
  }
  
  if (userExperience === 'intermediate') {
    if (riskTolerance === 'aggressive') {
      return 'confidence_based';
    }
    return 'council_consensus';
  }
  
  // Advanced users
  if (riskTolerance === 'conservative') {
    return 'council_consensus';
  } else if (riskTolerance === 'aggressive') {
    return 'contrarian_mode';
  }
  return 'category_shopping';
};

export const calculatePersonalizedPrediction = (
  predictions: any[],
  preferences: UserPreferences,
  experts: ExpertPersonality[]
): any => {
  // This would implement the logic to filter and weight predictions
  // based on user preferences and selected access mode
  // For now, return mock implementation
  
  const accessConfig = PREDICTION_ACCESS_MODES[preferences.predictionMode];
  
  // Filter by confidence threshold
  let filtered = predictions.filter(p => 
    !preferences.hideLowConfidencePredictions || 
    p.confidence >= preferences.minConfidenceThreshold
  );
  
  // Apply access mode logic
  switch (preferences.predictionMode) {
    case 'individual_expert':
      filtered = filtered.filter(p => p.expertId === preferences.selectedExpertId);
      break;
      
    case 'confidence_based':
      filtered = filtered.filter(p => p.confidence >= 0.75);
      break;
      
    case 'contrarian_mode':
      // Flip consensus predictions
      filtered = filtered.map(p => ({
        ...p,
        prediction: !p.prediction, // Simplified contrarian logic
        reasoning: `Contrarian play: ${p.reasoning}`
      }));
      break;
  }
  
  return filtered;
};