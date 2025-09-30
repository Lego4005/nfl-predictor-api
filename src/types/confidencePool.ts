/**
 * Confidence Pool Types - Real-time Expert Betting System
 * Complete type definitions for the Confidence Pool feature
 */

// Expert Bankroll Types
export interface ExpertBankroll {
  expert_id: string;
  expert_name: string;
  expert_emoji: string;
  archetype: string;
  current_balance: number;
  starting_balance: number;
  peak_balance: number;
  lowest_balance: number;
  total_wagered: number;
  total_won: number;
  total_lost: number;
  change_percent: number;
  change_amount: number;
  status: 'safe' | 'warning' | 'danger' | 'eliminated';
  risk_level: 'conservative' | 'moderate' | 'aggressive' | 'extreme';
  last_updated: string;
}

export interface BankrollHistory {
  timestamp: string;
  balance: number;
  change: number;
  reason: 'bet_won' | 'bet_lost' | 'bet_push' | 'adjustment';
  bet_id?: string;
}

export interface RiskMetrics {
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  bankruptcy_risk: number;
  kelly_deviation: number;
}

// Betting Types
export interface LiveBet {
  bet_id: string;
  expert_id: string;
  expert_name: string;
  expert_emoji: string;
  game_id: string;
  home_team: string;
  away_team: string;
  bet_type: 'spread' | 'moneyline' | 'total' | 'props';
  prediction: string;
  bet_amount: number;
  bankroll_percentage: number;
  vegas_odds: string;
  confidence: number;
  risk_level: 'low' | 'medium' | 'high' | 'extreme';
  reasoning: string[];
  potential_payout: number;
  placed_at: string;
  status: 'pending' | 'won' | 'lost' | 'push';
  settled_at?: string;
  actual_payout?: number;
}

export interface BettingSummary {
  total_at_risk: number;
  potential_payout: number;
  avg_confidence: number;
  total_bets: number;
  experts_active: number;
}

// Council Prediction Types
export interface CouncilPrediction {
  expert_id: string;
  expert_name: string;
  expert_emoji: string;
  archetype: string;
  accuracy_overall: number;
  accuracy_recent: number;
  council_position: number;
  vote_weight: number;
  game_id: string;
  game_details: {
    home_team: string;
    away_team: string;
    game_time: string;
    week: number;
  };
  prediction: {
    team: string;
    team_name: string;
    confidence: number;
    confidence_rank: number; // 1-16 ranking
    reasoning: string[];
  };
  vote_components: {
    accuracy: number;
    recent_performance: number;
    confidence: number;
    specialization: number;
  };
}

export interface WeeklyCouncilData {
  week: number;
  season: number;
  council_members: {
    expert_id: string;
    rank: number;
    selection_score: number;
    reason_selected: string;
  }[];
  total_predictions: number;
  consensus_quality: number;
}

// Expert Memory Types
export interface ExpertMemory {
  memory_id: string;
  expert_id: string;
  game_id: string;
  game_details: {
    teams: string;
    date: string;
    outcome: string;
  };
  memory_type: 'lesson_learned' | 'success_pattern' | 'failure_analysis' | 'insight';
  content: string;
  emotional_valence: number; // -1 to 1
  importance_score: number; // 0 to 1
  recalled_count: number;
  created_at: string;
  last_recalled: string;
  tags: string[];
}

export interface MemoryLaneFilters {
  expert_id?: string;
  memory_type?: ExpertMemory['memory_type'];
  min_importance?: number;
  emotional_filter?: 'positive' | 'negative' | 'neutral' | 'all';
  time_range?: 'week' | 'month' | 'season' | 'all_time';
}

// Prediction Battle Types
export interface PredictionBattle {
  battle_id: string;
  game_id: string;
  game_details: {
    home_team: string;
    away_team: string;
    game_time: string;
    status: string;
  };
  category: 'spread' | 'total' | 'winner' | 'props';
  expert_a: {
    expert_id: string;
    expert_name: string;
    expert_emoji: string;
    prediction: string;
    confidence: number;
    bet_amount?: number;
    reasoning: string[];
  };
  expert_b: {
    expert_id: string;
    expert_name: string;
    expert_emoji: string;
    prediction: string;
    confidence: number;
    bet_amount?: number;
    reasoning: string[];
  };
  difference: number; // Prediction difference magnitude
  head_to_head_record: {
    expert_a_wins: number;
    expert_b_wins: number;
    ties: number;
    last_5: string; // e.g., "AABAA"
  };
  user_votes?: {
    expert_a: number;
    expert_b: number;
  };
  status: 'pending' | 'settled';
  winner?: 'expert_a' | 'expert_b' | 'tie';
}

// WebSocket Event Types
export interface BetPlacedEvent {
  type: 'bet_placed';
  bet: LiveBet;
  bankroll_update: {
    expert_id: string;
    old_balance: number;
    new_balance: number;
  };
}

export interface BetSettledEvent {
  type: 'bet_settled';
  bet_id: string;
  expert_id: string;
  result: 'won' | 'lost' | 'push';
  payout: number;
  bankroll_update: {
    old_balance: number;
    new_balance: number;
  };
}

export interface ExpertEliminatedEvent {
  type: 'expert_eliminated';
  expert_id: string;
  expert_name: string;
  expert_emoji: string;
  final_bankroll: number;
  elimination_reason: 'bankrupt' | 'disqualified';
  final_bet?: {
    game_id: string;
    bet_amount: number;
    result: 'lost';
  };
  season_stats: {
    total_bets: number;
    win_rate: number;
    roi: number;
    peak_balance: number;
  };
}

export interface LineMovementEvent {
  type: 'line_movement';
  game_id: string;
  line_type: 'spread' | 'total' | 'moneyline';
  old_value: number;
  new_value: number;
  movement: number;
  direction: 'up' | 'down';
  sharp_money: boolean;
  affected_experts: string[];
}

export interface BankrollUpdateEvent {
  type: 'bankroll_updated';
  expert_id: string;
  old_balance: number;
  new_balance: number;
  change: number;
  reason: 'bet_settled' | 'adjustment';
  bet_id?: string;
}

export type WebSocketEvent =
  | BetPlacedEvent
  | BetSettledEvent
  | ExpertEliminatedEvent
  | LineMovementEvent
  | BankrollUpdateEvent;

// Hook Options Types
export interface UseExpertBankrollsOptions {
  refetchInterval?: number;
  enabled?: boolean;
  sortBy?: 'balance' | 'roi' | 'risk' | 'change';
  filterByStatus?: ExpertBankroll['status'][];
}

export interface UseLiveBettingFeedOptions {
  game_id?: string;
  expert_id?: string;
  status?: LiveBet['status'];
  limit?: number;
  realtime?: boolean;
}

export interface UseCouncilPredictionsOptions {
  week?: number;
  season?: number;
  expert_id?: string;
  min_confidence?: number;
}

export interface UseExpertMemoriesOptions {
  expert_id?: string;
  limit?: number;
  offset?: number;
  filters?: MemoryLaneFilters;
}

export interface UsePredictionBattlesOptions {
  week?: number;
  min_difference?: number;
  category?: PredictionBattle['category'];
  status?: PredictionBattle['status'];
}

// Response Types
export interface BankrollsResponse {
  bankrolls: ExpertBankroll[];
  summary: {
    total_eliminated: number;
    avg_balance: number;
    total_wagered: number;
    most_aggressive: string;
    safest: string;
  };
  timestamp: string;
}

export interface BettingFeedResponse {
  bets: LiveBet[];
  summary: BettingSummary;
  timestamp: string;
}

export interface CouncilPredictionsResponse {
  predictions: CouncilPrediction[];
  weekly_data: WeeklyCouncilData;
  timestamp: string;
}

export interface MemoriesResponse {
  memories: ExpertMemory[];
  total_count: number;
  pagination: {
    offset: number;
    limit: number;
    has_more: boolean;
  };
}

export interface BattlesResponse {
  battles: PredictionBattle[];
  summary: {
    total_battles: number;
    avg_difference: number;
    most_contested_game: string;
  };
}