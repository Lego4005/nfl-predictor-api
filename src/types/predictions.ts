// Comprehensive NFL Prediction Types for 375+ Predictions
export type PredictionCategory = 'core' | 'props' | 'live' | 'situational' | 'advanced';
export type PredictionType =
  // Core Predictions (75+)
  | 'game_winner' | 'point_spread' | 'total_points' | 'moneyline' | 'first_half_winner'
  | 'second_half_winner' | 'quarter_winners' | 'exact_score' | 'margin_of_victory' | 'shutout'

  // Player Props (150+)
  | 'passing_yards' | 'passing_tds' | 'rushing_yards' | 'rushing_tds' | 'receiving_yards'
  | 'receiving_tds' | 'receptions' | 'interceptions' | 'fumbles' | 'sacks' | 'field_goals'
  | 'extra_points' | 'punt_return_yards' | 'kick_return_yards' | 'tackles' | 'defensive_tds'

  // Live Game Predictions (50+)
  | 'next_score' | 'next_touchdown' | 'next_field_goal' | 'next_turnover' | 'drive_result'
  | 'time_of_possession' | 'live_spread' | 'live_total' | 'momentum_shift' | 'comeback_probability'

  // Situational Predictions (50+)
  | 'red_zone_efficiency' | 'third_down_conversion' | 'fourth_down_attempts' | 'two_point_attempts'
  | 'overtime_probability' | 'weather_impact' | 'injury_impact' | 'coaching_decisions' | 'penalty_yards'

  // Advanced Analytics (50+)
  | 'win_probability_live' | 'expected_points' | 'success_rate' | 'epa_per_play' | 'dvoa_matchup'
  | 'pff_grades' | 'advanced_metrics' | 'drive_efficiency' | 'situational_success' | 'matchup_advantages';

export type ConfidenceLevel = 'very_high' | 'high' | 'medium' | 'low' | 'very_low';
export type ExpertType = 'ai_model' | 'human_expert' | 'statistical_model' | 'composite';

export interface Expert {
  id: string;
  name: string;
  type: ExpertType;
  specialization: string[];
  accuracy_metrics: {
    overall: number;
    by_category: Record<PredictionCategory, number>;
    by_prediction_type: Record<string, number>;
    recent_performance: number;
    season_performance: number;
  };
  confidence_calibration: number;
  track_record: {
    total_predictions: number;
    correct_predictions: number;
    high_confidence_accuracy: number;
    low_confidence_accuracy: number;
  };
  bio?: string;
  avatar?: string;
  verified: boolean;
}

export interface ComprehensivePrediction {
  id: string;
  game_id: string;
  expert_id: string;
  category: PredictionCategory;
  type: PredictionType;

  // Prediction Details
  predicted_value: number | string | boolean;
  confidence: ConfidenceLevel;
  confidence_score: number; // 0-100

  // Betting Lines & Odds
  over_under_line?: number;
  spread_line?: number;
  moneyline_odds?: number;
  implied_probability: number;
  expected_value: number;

  // Context & Analysis
  reasoning: string[];
  key_factors: string[];
  historical_context: string;
  matchup_analysis: string;

  // Performance Tracking
  model_version?: string;
  last_updated: string;
  created_at: string;
  result?: number | string | boolean; // Actual outcome
  is_correct?: boolean;

  // Real-time Updates
  live_updates: PredictionUpdate[];
  is_live: boolean;
  locked: boolean; // No more updates after game starts

  // Metadata
  tags: string[];
  difficulty_rating: number; // 1-10
  market_movement: MarketMovement[];
}

export interface PredictionUpdate {
  timestamp: string;
  old_value: number | string | boolean;
  new_value: number | string | boolean;
  old_confidence: number;
  new_confidence: number;
  reason: string;
  trigger: 'injury' | 'weather' | 'line_movement' | 'live_action' | 'news' | 'model_update';
}

export interface MarketMovement {
  timestamp: string;
  sportsbook: string;
  old_line: number;
  new_line: number;
  direction: 'up' | 'down';
  volume: number;
  sharp_money: boolean;
}

export interface PlayerProp {
  player_id: string;
  player_name: string;
  position: string;
  team: string;
  stat_type: string;
  line: number;
  over_odds: number;
  under_odds: number;
  predictions: ComprehensivePrediction[];
  season_average: number;
  recent_form: number[];
  matchup_history: number[];
  injury_status: 'healthy' | 'questionable' | 'doubtful' | 'out';
  weather_impact: 'none' | 'low' | 'medium' | 'high';
}

export interface LiveGameData {
  game_id: string;
  quarter: number;
  time_remaining: string;
  home_score: number;
  away_score: number;
  possession: string;
  down: number;
  distance: number;
  yard_line: number;

  // Live Metrics
  win_probability: {
    home: number;
    away: number;
    last_updated: string;
  };

  scoring_probability: {
    next_score_home: number;
    next_score_away: number;
    next_score_type: 'touchdown' | 'field_goal' | 'safety' | 'none';
  };

  momentum: {
    current_team: string;
    strength: number; // -100 to 100
    recent_plays: string[];
  };

  key_events: GameEvent[];
}

export interface GameEvent {
  timestamp: string;
  quarter: number;
  time: string;
  event_type: 'touchdown' | 'field_goal' | 'turnover' | 'penalty' | 'injury' | 'timeout';
  team: string;
  description: string;
  impact_score: number; // -10 to 10
  prediction_updates: string[]; // IDs of predictions that were updated
}

export interface ExpertConsensus {
  prediction_id: string;
  total_experts: number;
  expert_breakdown: {
    very_high_confidence: number;
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
    very_low_confidence: number;
  };

  value_consensus: {
    median: number;
    mean: number;
    mode: number;
    standard_deviation: number;
    outliers: string[]; // Expert IDs
  };

  confidence_weighted_average: number;
  accuracy_weighted_average: number;
  sharp_money_alignment: number; // How aligned with professional bettors

  disagreement_factors: string[];
  consensus_strength: 'strong' | 'moderate' | 'weak' | 'divided';
}

export interface PredictionFilter {
  categories: PredictionCategory[];
  experts: string[];
  confidence_levels: ConfidenceLevel[];
  prediction_types: PredictionType[];
  games: string[];
  min_confidence: number;
  max_confidence: number;
  only_live: boolean;
  only_unlocked: boolean;
  has_betting_value: boolean;
  min_expected_value: number;
  sort_by: 'confidence' | 'expected_value' | 'expert_accuracy' | 'consensus_strength' | 'time';
  sort_direction: 'asc' | 'desc';
}

export interface PredictionSort {
  field: keyof ComprehensivePrediction | 'expert_accuracy' | 'consensus_strength';
  direction: 'asc' | 'desc';
}

export interface VirtualScrollConfig {
  item_height: number;
  container_height: number;
  buffer_size: number;
  overscan: number;
}

export interface PredictionPerformanceMetrics {
  expert_id: string;
  time_period: 'week' | 'month' | 'season' | 'all_time';

  accuracy_metrics: {
    overall_accuracy: number;
    category_accuracy: Record<PredictionCategory, number>;
    confidence_calibration: {
      very_high: { predicted: number; actual: number };
      high: { predicted: number; actual: number };
      medium: { predicted: number; actual: number };
      low: { predicted: number; actual: number };
      very_low: { predicted: number; actual: number };
    };
  };

  betting_metrics: {
    roi: number;
    units_won: number;
    units_bet: number;
    win_rate: number;
    average_odds: number;
    best_bet_categories: PredictionCategory[];
  };

  trend_analysis: {
    recent_streak: number; // Positive for wins, negative for losses
    momentum: 'hot' | 'warm' | 'neutral' | 'cold' | 'ice_cold';
    improvement_rate: number; // Percentage improvement over time
    consistency_score: number; // How consistent performance is
  };
}

export interface RealtimeUpdate {
  type: 'prediction_update' | 'game_event' | 'line_movement' | 'expert_update' | 'consensus_change';
  timestamp: string;
  data: any;
  affected_predictions: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface WebSocketMessage {
  event: 'prediction_update' | 'game_state' | 'expert_performance' | 'market_movement' | 'system_status';
  game_id?: string;
  expert_id?: string;
  prediction_id?: string;
  data: any;
  timestamp: string;
}

// Response Types
export interface PredictionsResponse {
  predictions: ComprehensivePrediction[];
  experts: Expert[];
  consensus: Record<string, ExpertConsensus>;
  live_games: LiveGameData[];
  total_count: number;
  filtered_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
  metadata: {
    last_updated: string;
    data_freshness: string;
    prediction_coverage: number; // Percentage of possible predictions covered
    expert_availability: number; // Percentage of experts contributing
  };
}

export interface ExpertPerformanceResponse {
  expert: Expert;
  metrics: PredictionPerformanceMetrics;
  recent_predictions: ComprehensivePrediction[];
  accuracy_trends: Array<{
    date: string;
    accuracy: number;
    prediction_count: number;
  }>;
  category_specialization: Array<{
    category: PredictionCategory;
    accuracy: number;
    confidence: number;
    prediction_count: number;
  }>;
}

// Error Types
export class PredictionError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: any
  ) {
    super(message);
    this.name = 'PredictionError';
  }
}

export class RealtimeConnectionError extends PredictionError {
  constructor(message: string, details?: any) {
    super(message, 'REALTIME_CONNECTION_ERROR', details);
  }
}

export class ExpertDataError extends PredictionError {
  constructor(message: string, public expert_id: string, details?: any) {
    super(message, 'EXPERT_DATA_ERROR', details);
  }
}

// Utility Types
export type PredictionValue = string | number | boolean;
export type ExpertRanking = Expert & { rank: number; score: number };
export type CategoryStats = Record<PredictionCategory, {
  total: number;
  accurate: number;
  accuracy: number;
  average_confidence: number;
}>;