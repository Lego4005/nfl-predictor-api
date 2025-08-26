// Core NFL data types
export interface GamePrediction {
  home: string;
  away: string;
  matchup: string;
  su_pick: string;
  su_confidence: number;
  source: DataSource;
  timestamp: string;
}

export interface ATSPrediction {
  matchup: string;
  ats_pick: string;
  spread: number;
  ats_confidence: number;
  source: DataSource;
  timestamp: string;
}

export interface TotalsPrediction {
  matchup: string;
  tot_pick: string;
  total_line: number;
  tot_confidence: number;
  source: DataSource;
  timestamp: string;
}

export interface PropBet {
  player: string;
  prop_type: PropType;
  units: string;
  line: number;
  pick: 'Over' | 'Under';
  confidence: number;
  bookmaker: string;
  team: string;
  opponent: string;
  source: DataSource;
  timestamp: string;
}

export interface FantasyPick {
  player: string;
  position: Position;
  salary: number;
  projected_points: number;
  value_score: number;
  source: DataSource;
  timestamp: string;
}

// Enums
export enum DataSource {
  ODDS_API = 'odds_api',
  SPORTSDATA_IO = 'sportsdata_io',
  ESPN_API = 'espn_api',
  NFL_API = 'nfl_api',
  RAPID_API = 'rapid_api',
  CACHE = 'cache',
  MOCK = 'mock'
}

export enum PropType {
  PASSING_YARDS = 'Passing Yards',
  RUSHING_YARDS = 'Rushing Yards',
  RECEIVING_YARDS = 'Receiving Yards',
  RECEPTIONS = 'Receptions',
  TOUCHDOWNS = 'Touchdowns',
  FANTASY_POINTS = 'Fantasy Points'
}

export enum Position {
  QB = 'QB',
  RB = 'RB',
  WR = 'WR',
  TE = 'TE',
  K = 'K',
  DST = 'DST'
}