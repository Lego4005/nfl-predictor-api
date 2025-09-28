// AI Council Dashboard Types for Enhanced Prediction System

export interface VoteWeight {
  expertId: string;
  overallWeight: number;
  accuracyComponent: number;
  recentPerformanceComponent: number;
  confidenceComponent: number;
  councilTenureComponent: number;
  normalizedWeight: number;
}

export interface CouncilMember {
  expertId: string;
  expertName: string;
  overallAccuracy: number;
  recentTrend: 'improving' | 'declining' | 'stable';
  voteWeight: VoteWeight;
  predictions: CategoryPrediction[];
  specialization: string[];
  joinDate: string;
  totalVotes: number;
  consensusAlignment: number; // How often they agree with council consensus
}

export interface CategoryPrediction {
  categoryId: string;
  categoryName: string;
  group: PredictionCategoryGroup;
  expertValue: any;
  consensusValue: any;
  confidence: number;
  agreement: number;
  isOutlier: boolean;
  reasoning?: string[];
  lastUpdated: string;
}

export interface ConsensusResult {
  gameId: string;
  categoryId: string;
  consensusValue: any;
  confidence: number;
  agreement: number;
  totalExperts: number;
  votingBreakdown: VotingBreakdown;
  weightedScore: number;
  conflictingExperts: string[];
  timestamp: string;
}

export interface VotingBreakdown {
  unanimous: number;
  strongMajority: number; // >75%
  simpleMajority: number; // 50-75%
  split: number; // <50%
  abstained: number;
}

export interface CouncilDecision {
  id: string;
  gameId: string;
  decisionType: 'consensus' | 'majority' | 'expert_override';
  categoryId: string;
  finalValue: any;
  confidence: number;
  votingRound: number;
  timestamp: string;
  participatingExperts: string[];
  dissenting: string[];
  reasoning: string;
}

export type PredictionCategoryGroup = 
  | 'game_outcome' 
  | 'betting_markets' 
  | 'live_scenarios' 
  | 'player_props' 
  | 'situational_analysis';

export interface AICouncilDashboardProps {
  gameId: string;
  councilMembers: CouncilMember[];
  consensusData: ConsensusResult[];
  voteWeights: VoteWeight[];
  onExpertSelect: (expertId: string) => void;
  refreshInterval: number;
}

export interface CouncilMemberCardProps {
  member: CouncilMember;
  isSelected: boolean;
  onSelect: (expertId: string) => void;
  showDetailedMetrics: boolean;
}

export interface VoteWeightBreakdownProps {
  voteWeight: VoteWeight;
  showComponents: boolean;
  animated: boolean;
}

export interface ConsensusVisualizationProps {
  consensusResults: ConsensusResult[];
  activeCategoryFilter: PredictionCategoryGroup | 'all';
  showConfidenceIndicators: boolean;
}

export interface CouncilDecisionTimelineProps {
  decisions: CouncilDecision[];
  gameId: string;
  maxItems?: number;
}

// Expert Battle Comparison Types
export interface ExpertBattleProps {
  expertIds: string[];
  comparisonMetric: 'accuracy' | 'confidence' | 'roi' | 'consistency';
  timeRange: 'week' | 'month' | 'season' | 'all_time';
}

export interface HeadToHeadComparison {
  expert1: CouncilMember;
  expert2: CouncilMember;
  battleRecord: {
    wins: number;
    losses: number;
    ties: number;
    winPercentage: number;
  };
  categoryDominance: Record<PredictionCategoryGroup, {
    expert1Wins: number;
    expert2Wins: number;
    ties: number;
  }>;
  recentForm: {
    expert1Streak: number;
    expert2Streak: number;
    momentum: 'expert1' | 'expert2' | 'neutral';
  };
}

export interface DisagreementAnalysis {
  categoryId: string;
  categoryName: string;
  conflictLevel: 'high' | 'medium' | 'low';
  expertPositions: Array<{
    expertId: string;
    position: any;
    confidence: number;
    reasoning: string[];
  }>;
  marketImplication: 'significant' | 'moderate' | 'minimal';
}

export interface ExpertSpecialization {
  expertId: string;
  strengths: Array<{
    category: PredictionCategoryGroup;
    proficiencyScore: number; // 0-100
    sampleSize: number;
  }>;
  weaknesses: Array<{
    category: PredictionCategoryGroup;
    proficiencyScore: number;
    sampleSize: number;
  }>;
  overallVersatility: number; // How well they perform across all categories
}

// 27 Category Prediction System Types
export interface PredictionCategoriesGridProps {
  expertPredictions: ExpertPrediction[];
  consensusResults: ConsensusResult[];
  activeCategoryFilter: PredictionCategoryGroup | 'all';
  onCategorySelect: (categoryId: string) => void;
  showConfidenceIndicators: boolean;
}

export interface ExpertPrediction {
  expertId: string;
  gameId: string;
  predictions: CategoryPrediction[];
  overallConfidence: number;
  submissionTime: string;
  lastUpdated: string;
}

export interface CategoryDisplayConfig {
  group: PredictionCategoryGroup;
  displayPriority: 'high' | 'medium' | 'low';
  cardSize: 'large' | 'medium' | 'compact';
  categories: string[];
  defaultExpanded: boolean;
}

// Real-time Update Types
export interface LiveUpdateMessage {
  type: 'CONSENSUS_UPDATE' | 'EXPERT_PREDICTION' | 'VOTE_WEIGHT_CHANGE' | 'GAME_EVENT';
  gameId: string;
  data: any;
  timestamp: string;
  affectedCategories: string[];
  priority: 'high' | 'medium' | 'low';
}

export interface WebSocketConnectionState {
  connected: boolean;
  lastHeartbeat: string;
  reconnectAttempts: number;
  latency: number;
}

// Performance Tracking Types
export interface ExpertPerformanceMetrics {
  expertId: string;
  timeframe: 'daily' | 'weekly' | 'monthly' | 'seasonal';
  accuracy: {
    overall: number;
    byCategory: Record<PredictionCategoryGroup, number>;
    trend: Array<{
      date: string;
      accuracy: number;
    }>;
  };
  confidence: {
    calibration: number; // How well confidence matches actual accuracy
    overconfidence: number; // Tendency to be overconfident
    reliability: number; // Consistency of confidence levels
  };
  betting: {
    roi: number;
    units: number;
    winRate: number;
    averageOdds: number;
  };
  councilContribution: {
    votesSubmitted: number;
    consensusInfluence: number; // How much their votes affect final consensus
    disagreementRate: number; // How often they disagree with consensus
  };
}

export interface SystemHealthMetrics {
  expertAvailability: number; // Percentage of experts currently active
  dataFreshness: number; // How recent the data is (in minutes)
  predictionCoverage: number; // Percentage of categories with predictions
  consensusQuality: number; // Overall quality score of consensus
  systemLoad: number; // Current system performance
  wsConnections: number; // Active WebSocket connections
}