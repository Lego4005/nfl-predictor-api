/**
 * Comprehensive NFL Prediction Categories
 * 27+ prediction categories organized by group for complete game coverage
 */

import { PredictionCategory } from '@/types/predictions';

export interface PredictionCategoryConfig {
  id: string;
  name: string;
  description: string;
  group: PredictionCategoryGroup;
  difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  confidence_weight: number; // How much confidence affects this prediction type
  expert_specializations: string[]; // Which expert types excel at this
  betting_relevance: 'high' | 'medium' | 'low';
  real_time_updates: boolean; // Whether this updates during live games
  data_requirements: string[];
  example_predictions: string[];
}

export interface PredictionCategoryGroup {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  priority: number; // Display order
}

// Prediction Category Groups
export const PREDICTION_GROUPS: PredictionCategoryGroup[] = [
  {
    id: 'game_outcome',
    name: 'Game Outcome',
    description: 'Core game result predictions',
    icon: '🏈',
    color: 'blue',
    priority: 1
  },
  {
    id: 'scoring_metrics',
    name: 'Scoring & Totals',
    description: 'Points, touchdowns, and scoring predictions',
    icon: '🎯',
    color: 'green',
    priority: 2
  },
  {
    id: 'player_performance',
    name: 'Player Performance',
    description: 'Individual player statistical predictions',
    icon: '⭐',
    color: 'purple',
    priority: 3
  },
  {
    id: 'team_statistics',
    name: 'Team Statistics',
    description: 'Team-level performance metrics',
    icon: '📊',
    color: 'orange',
    priority: 4
  },
  {
    id: 'situational_analysis',
    name: 'Situational Analysis',
    description: 'Context-specific game situations',
    icon: '🧠',
    color: 'red',
    priority: 5
  },
  {
    id: 'live_developments',
    name: 'Live Developments',
    description: 'Real-time game flow predictions',
    icon: '⚡',
    color: 'yellow',
    priority: 6
  },
  {
    id: 'betting_markets',
    name: 'Betting Markets',
    description: 'Sportsbook and betting-focused predictions',
    icon: '💰',
    color: 'emerald',
    priority: 7
  },
  {
    id: 'advanced_analytics',
    name: 'Advanced Analytics',
    description: 'Statistical and analytical predictions',
    icon: '🔬',
    color: 'indigo',
    priority: 8
  }
];

// Comprehensive Prediction Categories (27+ categories)
export const PREDICTION_CATEGORIES: PredictionCategoryConfig[] = [
  // Game Outcome Group (5 categories)
  {
    id: 'game_winner',
    name: 'Game Winner',
    description: 'Predict which team will win the game',
    group: PREDICTION_GROUPS[0],
    difficulty: 'easy',
    confidence_weight: 0.8,
    expert_specializations: ['analyst', 'veteran', 'scholar'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['team_records', 'head_to_head', 'current_form'],
    example_predictions: ['Chiefs win', 'Bills win', 'Tie (rare)']
  },
  {
    id: 'point_spread',
    name: 'Point Spread',
    description: 'Predict if favorite covers the spread',
    group: PREDICTION_GROUPS[0],
    difficulty: 'medium',
    confidence_weight: 0.7,
    expert_specializations: ['sharp', 'quant', 'contrarian'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['betting_lines', 'team_strength', 'injury_reports'],
    example_predictions: ['Chiefs -3.5 (cover)', 'Bills +3.5 (cover)']
  },
  {
    id: 'moneyline_value',
    name: 'Moneyline Value',
    description: 'Identify value in moneyline betting odds',
    group: PREDICTION_GROUPS[0],
    difficulty: 'hard',
    confidence_weight: 0.6,
    expert_specializations: ['gambler', 'sharp', 'hunter'],
    betting_relevance: 'high',
    real_time_updates: false,
    data_requirements: ['odds_comparison', 'implied_probability', 'market_movement'],
    example_predictions: ['Chiefs -150 (value)', 'Bills +130 (value)']
  },
  {
    id: 'exact_score',
    name: 'Exact Score',
    description: 'Predict the exact final score',
    group: PREDICTION_GROUPS[0],
    difficulty: 'expert',
    confidence_weight: 0.3,
    expert_specializations: ['total_predictor', 'quant'],
    betting_relevance: 'medium',
    real_time_updates: false,
    data_requirements: ['scoring_averages', 'defensive_efficiency', 'pace_factors'],
    example_predictions: ['Chiefs 27, Bills 24', 'Bills 21, Chiefs 17']
  },
  {
    id: 'margin_victory',
    name: 'Margin of Victory',
    description: 'Predict the winning margin range',
    group: PREDICTION_GROUPS[0],
    difficulty: 'hard',
    confidence_weight: 0.5,
    expert_specializations: ['analyst', 'quant', 'veteran'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['historical_margins', 'team_strength_differential'],
    example_predictions: ['1-3 points', '4-7 points', '8-14 points', '15+ points']
  },

  // Scoring & Totals Group (4 categories)
  {
    id: 'total_points',
    name: 'Total Points Over/Under',
    description: 'Predict if total points go over or under the line',
    group: PREDICTION_GROUPS[1],
    difficulty: 'medium',
    confidence_weight: 0.7,
    expert_specializations: ['total_predictor', 'weather_expert', 'quant'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['team_pace', 'defensive_efficiency', 'weather_conditions'],
    example_predictions: ['Over 47.5', 'Under 47.5']
  },
  {
    id: 'first_half_total',
    name: 'First Half Total',
    description: 'Predict first half scoring total',
    group: PREDICTION_GROUPS[1],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['momentum_tracker', 'total_predictor'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['first_half_averages', 'slow_start_tendencies'],
    example_predictions: ['Over 24.5', 'Under 24.5']
  },
  {
    id: 'highest_scoring_quarter',
    name: 'Highest Scoring Quarter',
    description: 'Predict which quarter will have the most points',
    group: PREDICTION_GROUPS[1],
    difficulty: 'hard',
    confidence_weight: 0.4,
    expert_specializations: ['momentum_tracker', 'scholar'],
    betting_relevance: 'low',
    real_time_updates: true,
    data_requirements: ['quarter_by_quarter_stats', 'game_flow_patterns'],
    example_predictions: ['1st Quarter', '2nd Quarter', '3rd Quarter', '4th Quarter']
  },
  {
    id: 'total_touchdowns',
    name: 'Total Touchdowns',
    description: 'Predict total touchdowns scored in game',
    group: PREDICTION_GROUPS[1],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['total_predictor', 'scout'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['red_zone_efficiency', 'touchdown_rates'],
    example_predictions: ['Over 5.5', 'Under 5.5', 'Exactly 6']
  },

  // Player Performance Group (8 categories)
  {
    id: 'qb_passing_yards',
    name: 'QB Passing Yards',
    description: 'Quarterback passing yards over/under',
    group: PREDICTION_GROUPS[2],
    difficulty: 'easy',
    confidence_weight: 0.8,
    expert_specializations: ['scout', 'props_expert'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['qb_averages', 'defensive_pass_ranking', 'weather'],
    example_predictions: ['Mahomes Over 275.5', 'Allen Under 285.5']
  },
  {
    id: 'qb_passing_tds',
    name: 'QB Passing Touchdowns',
    description: 'Quarterback passing touchdowns',
    group: PREDICTION_GROUPS[2],
    difficulty: 'medium',
    confidence_weight: 0.7,
    expert_specializations: ['scout', 'red_zone_expert'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['red_zone_targets', 'td_rate', 'defensive_td_allowed'],
    example_predictions: ['Mahomes Over 2.5', 'Allen Exactly 3']
  },
  {
    id: 'rushing_yards_leader',
    name: 'Leading Rusher',
    description: 'Predict game leading rusher and yards',
    group: PREDICTION_GROUPS[2],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['scout', 'matchup_expert'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['rb_depth_charts', 'run_defense_ranking', 'game_script'],
    example_predictions: ['Hunt 85+ yards', 'Cook 75+ yards']
  },
  {
    id: 'receiving_yards_leader',
    name: 'Leading Receiver',
    description: 'Predict game leading receiver and yards',
    group: PREDICTION_GROUPS[2],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['scout', 'matchup_expert'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['target_share', 'coverage_matchups', 'injury_status'],
    example_predictions: ['Kelce 90+ yards', 'Diggs 85+ yards']
  },
  {
    id: 'anytime_touchdown',
    name: 'Anytime Touchdown Scorer',
    description: 'Predict players to score touchdowns',
    group: PREDICTION_GROUPS[2],
    difficulty: 'medium',
    confidence_weight: 0.5,
    expert_specializations: ['scout', 'red_zone_expert'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['red_zone_touches', 'goal_line_usage', 'td_probability'],
    example_predictions: ['Mahomes Yes', 'Kelce Yes', 'Hunt No']
  },
  {
    id: 'first_touchdown',
    name: 'First Touchdown Scorer',
    description: 'Predict first touchdown scorer of game',
    group: PREDICTION_GROUPS[2],
    difficulty: 'hard',
    confidence_weight: 0.3,
    expert_specializations: ['scout', 'opening_drive_expert'],
    betting_relevance: 'high',
    real_time_updates: false,
    data_requirements: ['opening_drive_success', 'early_game_usage'],
    example_predictions: ['Kelce +650', 'Hunt +800', 'Allen +900']
  },
  {
    id: 'kicker_performance',
    name: 'Kicker Points',
    description: 'Predict kicker total points scored',
    group: PREDICTION_GROUPS[2],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['special_teams_expert', 'weather_expert'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['kicker_accuracy', 'weather_conditions', 'red_zone_efficiency'],
    example_predictions: ['Butker Over 8.5', 'Bass Under 7.5']
  },
  {
    id: 'defensive_player_props',
    name: 'Defensive Performance',
    description: 'Sacks, interceptions, defensive touchdowns',
    group: PREDICTION_GROUPS[2],
    difficulty: 'hard',
    confidence_weight: 0.4,
    expert_specializations: ['defensive_expert', 'scout'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['pass_rush_rate', 'interception_rate', 'turnover_probability'],
    example_predictions: ['Chris Jones 1+ sacks', 'Sauce Gardner 1+ INT']
  },

  // Team Statistics Group (4 categories)
  {
    id: 'team_turnovers',
    name: 'Team Turnovers',
    description: 'Predict total turnovers by each team',
    group: PREDICTION_GROUPS[3],
    difficulty: 'medium',
    confidence_weight: 0.5,
    expert_specializations: ['turnover_expert', 'defensive_expert'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['turnover_rates', 'pressure_rates', 'ball_security'],
    example_predictions: ['Chiefs 0-1', 'Bills 1-2', 'Total Over 3.5']
  },
  {
    id: 'total_penalties',
    name: 'Total Penalties',
    description: 'Predict penalty yards and counts',
    group: PREDICTION_GROUPS[3],
    difficulty: 'hard',
    confidence_weight: 0.4,
    expert_specializations: ['discipline_expert', 'referee_expert'],
    betting_relevance: 'low',
    real_time_updates: true,
    data_requirements: ['penalty_rates', 'referee_tendencies', 'game_importance'],
    example_predictions: ['Over 110.5 penalty yards', 'Under 12.5 total penalties']
  },
  {
    id: 'time_possession',
    name: 'Time of Possession',
    description: 'Predict which team controls the clock',
    group: PREDICTION_GROUPS[3],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['game_flow_expert', 'veteran'],
    betting_relevance: 'low',
    real_time_updates: true,
    data_requirements: ['pace_of_play', 'run_game_efficiency', 'defensive_strength'],
    example_predictions: ['Chiefs 32+ minutes', 'Bills 28+ minutes']
  },
  {
    id: 'total_yards',
    name: 'Total Team Yards',
    description: 'Predict total offensive yards per team',
    group: PREDICTION_GROUPS[3],
    difficulty: 'medium',
    confidence_weight: 0.7,
    expert_specializations: ['offensive_expert', 'matchup_analyst'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['yards_per_play', 'defensive_efficiency', 'pace_factors'],
    example_predictions: ['Chiefs Over 375.5', 'Bills Under 350.5']
  },

  // Situational Analysis Group (3 categories)
  {
    id: 'red_zone_efficiency',
    name: 'Red Zone Efficiency',
    description: 'Red zone touchdown conversion rates',
    group: PREDICTION_GROUPS[4],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['red_zone_expert', 'scout'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['red_zone_stats', 'goal_line_personnel', 'defensive_red_zone'],
    example_predictions: ['Chiefs 3/4 red zone TDs', 'Bills 2/3 red zone TDs']
  },
  {
    id: 'third_down_conversions',
    name: 'Third Down Conversions',
    description: 'Third down conversion success rates',
    group: PREDICTION_GROUPS[4],
    difficulty: 'medium',
    confidence_weight: 0.6,
    expert_specializations: ['situational_expert', 'third_down_expert'],
    betting_relevance: 'low',
    real_time_updates: true,
    data_requirements: ['third_down_stats', 'pass_rush_on_third', 'blitz_frequency'],
    example_predictions: ['Chiefs Over 45%', 'Bills Under 40%']
  },
  {
    id: 'weather_impact',
    name: 'Weather Impact',
    description: 'How weather affects game outcome',
    group: PREDICTION_GROUPS[4],
    difficulty: 'hard',
    confidence_weight: 0.5,
    expert_specializations: ['weather_expert', 'outdoor_specialist'],
    betting_relevance: 'medium',
    real_time_updates: false,
    data_requirements: ['weather_forecast', 'dome_vs_outdoor', 'historical_weather_games'],
    example_predictions: ['Significant impact', 'Minimal impact', 'Favors running game']
  },

  // Live Developments Group (2 categories)
  {
    id: 'next_score',
    name: 'Next Score Type',
    description: 'Predict type of next scoring play',
    group: PREDICTION_GROUPS[5],
    difficulty: 'hard',
    confidence_weight: 0.4,
    expert_specializations: ['live_expert', 'momentum_tracker'],
    betting_relevance: 'high',
    real_time_updates: true,
    data_requirements: ['current_drive_position', 'down_distance', 'time_remaining'],
    example_predictions: ['Touchdown', 'Field Goal', 'Safety', 'No Score']
  },
  {
    id: 'comeback_probability',
    name: 'Comeback Likelihood',
    description: 'Probability of trailing team comeback',
    group: PREDICTION_GROUPS[5],
    difficulty: 'expert',
    confidence_weight: 0.3,
    expert_specializations: ['comeback_expert', 'clutch_expert'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['score_differential', 'time_remaining', 'team_comeback_history'],
    example_predictions: ['High (>70%)', 'Medium (30-70%)', 'Low (<30%)']
  },

  // Betting Markets Group (2 categories)
  {
    id: 'line_movement',
    name: 'Line Movement Direction',
    description: 'Predict how betting lines will move',
    group: PREDICTION_GROUPS[6],
    difficulty: 'expert',
    confidence_weight: 0.3,
    expert_specializations: ['line_movement_expert', 'sharp'],
    betting_relevance: 'high',
    real_time_updates: false,
    data_requirements: ['betting_volume', 'sharp_money', 'public_betting_percentage'],
    example_predictions: ['Spread moves toward Chiefs', 'Total moves up', 'No significant movement']
  },
  {
    id: 'value_bets',
    name: 'Best Value Bets',
    description: 'Identify highest expected value bets',
    group: PREDICTION_GROUPS[6],
    difficulty: 'expert',
    confidence_weight: 0.4,
    expert_specializations: ['value_expert', 'sharp', 'hunter'],
    betting_relevance: 'high',
    real_time_updates: false,
    data_requirements: ['odds_comparison', 'implied_vs_actual_probability', 'edge_calculation'],
    example_predictions: ['Bills +3.5 (4.2% edge)', 'Under 47.5 (2.8% edge)']
  },

  // Advanced Analytics Group (2 categories)
  {
    id: 'win_probability_live',
    name: 'Live Win Probability',
    description: 'Real-time win probability updates',
    group: PREDICTION_GROUPS[7],
    difficulty: 'expert',
    confidence_weight: 0.5,
    expert_specializations: ['win_prob_expert', 'analytics_expert'],
    betting_relevance: 'medium',
    real_time_updates: true,
    data_requirements: ['game_situation', 'team_efficiency', 'time_remaining'],
    example_predictions: ['Chiefs 65%', 'Bills 35%', 'Toss-up (50/50)']
  },
  {
    id: 'advanced_metrics',
    name: 'Advanced Performance Metrics',
    description: 'EPA, DVOA, success rate predictions',
    group: PREDICTION_GROUPS[7],
    difficulty: 'expert',
    confidence_weight: 0.4,
    expert_specializations: ['analytics_expert', 'quant'],
    betting_relevance: 'low',
    real_time_updates: true,
    data_requirements: ['advanced_stats', 'efficiency_metrics', 'situational_success'],
    example_predictions: ['Chiefs +0.15 EPA/play', 'Bills 55% success rate']
  }
];

// Helper functions
export const getCategoriesByGroup = (groupId: string): PredictionCategoryConfig[] => {
  return PREDICTION_CATEGORIES.filter(category => category.group.id === groupId);
};

export const getCategoryById = (categoryId: string): PredictionCategoryConfig | undefined => {
  return PREDICTION_CATEGORIES.find(category => category.id === categoryId);
};

export const getCategoriesByDifficulty = (difficulty: PredictionCategoryConfig['difficulty']): PredictionCategoryConfig[] => {
  return PREDICTION_CATEGORIES.filter(category => category.difficulty === difficulty);
};

export const getCategoriesByBettingRelevance = (relevance: PredictionCategoryConfig['betting_relevance']): PredictionCategoryConfig[] => {
  return PREDICTION_CATEGORIES.filter(category => category.betting_relevance === relevance);
};

export const getExpertSpecializations = (expertType: string): PredictionCategoryConfig[] => {
  return PREDICTION_CATEGORIES.filter(category => 
    category.expert_specializations.includes(expertType)
  );
};

export const getRealtimeCategories = (): PredictionCategoryConfig[] => {
  return PREDICTION_CATEGORIES.filter(category => category.real_time_updates);
};

// Category statistics
export const getCategoryStats = () => {
  return {
    total_categories: PREDICTION_CATEGORIES.length,
    by_group: PREDICTION_GROUPS.reduce((acc, group) => {
      acc[group.id] = getCategoriesByGroup(group.id).length;
      return acc;
    }, {} as Record<string, number>),
    by_difficulty: {
      easy: getCategoriesByDifficulty('easy').length,
      medium: getCategoriesByDifficulty('medium').length,
      hard: getCategoriesByDifficulty('hard').length,
      expert: getCategoriesByDifficulty('expert').length
    },
    by_betting_relevance: {
      high: getCategoriesByBettingRelevance('high').length,
      medium: getCategoriesByBettingRelevance('medium').length,
      low: getCategoriesByBettingRelevance('low').length
    },
    realtime_enabled: getRealtimeCategories().length
  };
};