// Dashboard Types for NFL Prediction System

export interface Game {
  id: string;
  homeTeam: Team;
  awayTeam: Team;
  gameTime: string;
  week: number;
  season: number;
  isLive: boolean;
  quarter?: string;
  timeRemaining?: string;
  homeScore?: number;
  awayScore?: number;
  venue?: string;
  weather?: WeatherConditions;
}

export interface Team {
  id: string;
  name: string;
  city: string;
  abbreviation: string;
  logo: string;
  primaryColor: string;
  secondaryColor: string;
  record: TeamRecord;
  stats?: TeamStats;
  injuries?: InjuryReport[];
}

export interface TeamRecord {
  wins: number;
  losses: number;
  ties: number;
  winPercentage?: number;
  streak?: string;
}

export interface TeamStats {
  offense: {
    pointsPerGame: number;
    yardsPerGame: number;
    passingYards: number;
    rushingYards: number;
    turnovers: number;
  };
  defense: {
    pointsAllowed: number;
    yardsAllowed: number;
    sacks: number;
    interceptions: number;
    forcedFumbles: number;
  };
  specialTeams: {
    kickReturnAvg: number;
    puntReturnAvg: number;
    fieldGoalPct: number;
  };
}

export interface Prediction {
  gameId: string;
  homeTeamWinProbability: number;
  awayTeamWinProbability: number;
  predictedHomeScore: number;
  predictedAwayScore: number;
  confidence: PredictionConfidence;
  modelAccuracy: number;
  keyFactors: string[];
  lastUpdated: string;
  modelVersion?: string;
  historicalMatchupData?: HistoricalMatchup[];
}

export type PredictionConfidence = 'high' | 'medium' | 'low';

export interface BettingOdds {
  gameId: string;
  sportsbook: string;
  homeOdds: number;
  awayOdds: number;
  overUnder: number;
  spread: number;
  lastUpdated: string;
  homeSpreadOdds?: number;
  awaySpreadOdds?: number;
  overOdds?: number;
  underOdds?: number;
}

export interface InjuryReport {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  severity: InjurySeverity;
  impactScore: number;
  status: InjuryStatus;
  description: string;
  estimatedReturn?: string;
  replacementPlayer?: string;
}

export type InjurySeverity = 'critical' | 'moderate' | 'minor';
export type InjuryStatus = 'Out' | 'Doubtful' | 'Questionable' | 'Probable' | 'Healthy';

export interface BettingInsight {
  gameId: string;
  recommendation: BettingRecommendation;
  confidence: number;
  expectedValue: number;
  reasoning: string[];
  riskLevel: RiskLevel;
  suggestedBetTypes?: BetType[];
  bankrollPercentage?: number;
}

export type BettingRecommendation = 'strong_bet' | 'value_bet' | 'avoid' | 'wait';
export type RiskLevel = 'low' | 'medium' | 'high';
export type BetType = 'moneyline' | 'spread' | 'over_under' | 'prop';

export interface WeatherConditions {
  temperature: number;
  humidity: number;
  windSpeed: number;
  windDirection: string;
  precipitation: number;
  conditions: string;
  impact: WeatherImpact;
}

export type WeatherImpact = 'minimal' | 'moderate' | 'significant';

export interface HistoricalMatchup {
  date: string;
  homeScore: number;
  awayScore: number;
  venue: string;
  conditions: string;
}

export interface ModelPerformance {
  week: string;
  accuracy: number;
  predictions: number;
  correct: number;
  averageConfidence: number;
  bestPredictions: string[];
  worstPredictions: string[];
}

export interface DashboardFilters {
  gameStatus: 'all' | 'live' | 'upcoming' | 'completed';
  teams: string[];
  confidence: PredictionConfidence[];
  week: number[];
  dateRange: {
    start: string;
    end: string;
  };
}

export interface DashboardSettings {
  theme: 'light' | 'dark' | 'auto';
  refreshInterval: number;
  defaultView: 'grid' | 'list';
  enableNotifications: boolean;
  favoriteTeams: string[];
  hideSpoilers: boolean;
}

export interface LiveGameUpdate {
  gameId: string;
  homeScore: number;
  awayScore: number;
  quarter: string;
  timeRemaining: string;
  lastPlay: string;
  possession: string;
  down?: number;
  distance?: number;
  yardLine?: number;
}

export interface NotificationConfig {
  gameStart: boolean;
  scoreUpdate: boolean;
  predictionUpdate: boolean;
  injuryNews: boolean;
  oddsChange: boolean;
  favoriteTeamsOnly: boolean;
}

// API Response Types
export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
  metadata?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

export interface GamePredictionResponse extends APIResponse<{
  games: Game[];
  predictions: Prediction[];
  lastUpdated: string;
}> {}

export interface BettingOddsResponse extends APIResponse<{
  odds: BettingOdds[];
  lastUpdated: string;
  sources: string[];
}> {}

export interface InjuryReportResponse extends APIResponse<{
  injuries: InjuryReport[];
  lastUpdated: string;
  summary: {
    critical: number;
    moderate: number;
    minor: number;
  };
}> {}

// Chart Data Types
export interface ChartDataPoint {
  name: string;
  value: number;
  category?: string;
  color?: string;
}

export interface HeatmapDataPoint {
  x: string;
  y: string;
  value: number;
  category: string;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  category: string;
}

// Error Types
export class DashboardError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: any
  ) {
    super(message);
    this.name = 'DashboardError';
  }
}

export class APIError extends DashboardError {
  constructor(
    message: string,
    public statusCode: number,
    details?: any
  ) {
    super(message, 'API_ERROR', details);
  }
}