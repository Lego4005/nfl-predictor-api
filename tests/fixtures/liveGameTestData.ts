/**
 * Realistic Test Data for Live Game Conditions
 * Comprehensive test data that simulates various live game scenarios
 */

import { WebSocketEventType } from '../../src/services/websocketService';

// Team data with realistic information
export const NFL_TEAMS = {
  AFC_EAST: [
    { name: 'Buffalo Bills', city: 'Buffalo', abbreviation: 'BUF', colors: ['#00338D', '#C60C30'] },
    { name: 'Miami Dolphins', city: 'Miami', abbreviation: 'MIA', colors: ['#008E97', '#FC4C02'] },
    { name: 'New England Patriots', city: 'New England', abbreviation: 'NE', colors: ['#002244', '#C60C30'] },
    { name: 'New York Jets', city: 'New York', abbreviation: 'NYJ', colors: ['#125740', '#000000'] }
  ],
  AFC_NORTH: [
    { name: 'Baltimore Ravens', city: 'Baltimore', abbreviation: 'BAL', colors: ['#241773', '#000000'] },
    { name: 'Cincinnati Bengals', city: 'Cincinnati', abbreviation: 'CIN', colors: ['#FB4F14', '#000000'] },
    { name: 'Cleveland Browns', city: 'Cleveland', abbreviation: 'CLE', colors: ['#311D00', '#FF3C00'] },
    { name: 'Pittsburgh Steelers', city: 'Pittsburgh', abbreviation: 'PIT', colors: ['#FFB612', '#000000'] }
  ],
  AFC_SOUTH: [
    { name: 'Houston Texans', city: 'Houston', abbreviation: 'HOU', colors: ['#03202F', '#A71930'] },
    { name: 'Indianapolis Colts', city: 'Indianapolis', abbreviation: 'IND', colors: ['#002C5F', '#A2AAAD'] },
    { name: 'Jacksonville Jaguars', city: 'Jacksonville', abbreviation: 'JAX', colors: ['#006778', '#9F792C'] },
    { name: 'Tennessee Titans', city: 'Tennessee', abbreviation: 'TEN', colors: ['#0C2340', '#4B92DB'] }
  ],
  AFC_WEST: [
    { name: 'Denver Broncos', city: 'Denver', abbreviation: 'DEN', colors: ['#FB4F14', '#002244'] },
    { name: 'Kansas City Chiefs', city: 'Kansas City', abbreviation: 'KC', colors: ['#E31837', '#FFB81C'] },
    { name: 'Las Vegas Raiders', city: 'Las Vegas', abbreviation: 'LV', colors: ['#000000', '#A5ACAF'] },
    { name: 'Los Angeles Chargers', city: 'Los Angeles', abbreviation: 'LAC', colors: ['#0080C6', '#FFC20E'] }
  ],
  NFC_EAST: [
    { name: 'Dallas Cowboys', city: 'Dallas', abbreviation: 'DAL', colors: ['#003594', '#041E42'] },
    { name: 'New York Giants', city: 'New York', abbreviation: 'NYG', colors: ['#0B2265', '#A71930'] },
    { name: 'Philadelphia Eagles', city: 'Philadelphia', abbreviation: 'PHI', colors: ['#004C54', '#A5ACAF'] },
    { name: 'Washington Commanders', city: 'Washington', abbreviation: 'WAS', colors: ['#5A1414', '#FFB612'] }
  ],
  NFC_NORTH: [
    { name: 'Chicago Bears', city: 'Chicago', abbreviation: 'CHI', colors: ['#0B162A', '#C83803'] },
    { name: 'Detroit Lions', city: 'Detroit', abbreviation: 'DET', colors: ['#0076B6', '#B0B7BC'] },
    { name: 'Green Bay Packers', city: 'Green Bay', abbreviation: 'GB', colors: ['#203731', '#FFB612'] },
    { name: 'Minnesota Vikings', city: 'Minnesota', abbreviation: 'MIN', colors: ['#4F2683', '#FFC62F'] }
  ],
  NFC_SOUTH: [
    { name: 'Atlanta Falcons', city: 'Atlanta', abbreviation: 'ATL', colors: ['#A71930', '#000000'] },
    { name: 'Carolina Panthers', city: 'Carolina', abbreviation: 'CAR', colors: ['#0085CA', '#101820'] },
    { name: 'New Orleans Saints', city: 'New Orleans', abbreviation: 'NO', colors: ['#D3BC8D', '#101820'] },
    { name: 'Tampa Bay Buccaneers', city: 'Tampa Bay', abbreviation: 'TB', colors: ['#D50A0A', '#FF7900'] }
  ],
  NFC_WEST: [
    { name: 'Arizona Cardinals', city: 'Arizona', abbreviation: 'ARI', colors: ['#97233F', '#000000'] },
    { name: 'Los Angeles Rams', city: 'Los Angeles', abbreviation: 'LAR', colors: ['#003594', '#FFA300'] },
    { name: 'San Francisco 49ers', city: 'San Francisco', abbreviation: 'SF', colors: ['#AA0000', '#B3995D'] },
    { name: 'Seattle Seahawks', city: 'Seattle', abbreviation: 'SEA', colors: ['#002244', '#69BE28'] }
  ]
};

// Get all teams as a flat array
export const ALL_TEAMS = Object.values(NFL_TEAMS).flat();

// Game scenarios with realistic progressions
export const GAME_SCENARIOS = {
  BLOWOUT: {
    name: 'Blowout Victory',
    description: 'One-sided game with dominant performance',
    progression: [
      { quarter: 1, time: '15:00', home_score: 0, away_score: 0, status: 'live' },
      { quarter: 1, time: '08:30', home_score: 7, away_score: 0, status: 'live' },
      { quarter: 1, time: '03:45', home_score: 14, away_score: 0, status: 'live' },
      { quarter: 2, time: '12:15', home_score: 21, away_score: 0, status: 'live' },
      { quarter: 2, time: '05:20', home_score: 28, away_score: 3, status: 'live' },
      { quarter: 3, time: '09:30', home_score: 35, away_score: 3, status: 'live' },
      { quarter: 4, time: '12:00', home_score: 42, away_score: 10, status: 'live' },
      { quarter: 4, time: '00:00', home_score: 42, away_score: 10, status: 'final' }
    ]
  },

  NAIL_BITER: {
    name: 'Nail-biting Finish',
    description: 'Close game decided in final moments',
    progression: [
      { quarter: 1, time: '15:00', home_score: 0, away_score: 0, status: 'live' },
      { quarter: 1, time: '06:20', home_score: 7, away_score: 0, status: 'live' },
      { quarter: 1, time: '02:15', home_score: 7, away_score: 7, status: 'live' },
      { quarter: 2, time: '11:30', home_score: 14, away_score: 7, status: 'live' },
      { quarter: 2, time: '04:45', home_score: 14, away_score: 14, status: 'live' },
      { quarter: 3, time: '08:15', home_score: 21, away_score: 14, status: 'live' },
      { quarter: 3, time: '03:30', home_score: 21, away_score: 21, status: 'live' },
      { quarter: 4, time: '07:45', home_score: 28, away_score: 21, status: 'live' },
      { quarter: 4, time: '02:30', home_score: 28, away_score: 28, status: 'live' },
      { quarter: 4, time: '00:03', home_score: 31, away_score: 28, status: 'live' },
      { quarter: 4, time: '00:00', home_score: 31, away_score: 28, status: 'final' }
    ]
  },

  COMEBACK: {
    name: 'Epic Comeback',
    description: 'Team overcomes large deficit',
    progression: [
      { quarter: 1, time: '15:00', home_score: 0, away_score: 0, status: 'live' },
      { quarter: 1, time: '10:30', home_score: 0, away_score: 7, status: 'live' },
      { quarter: 1, time: '04:15', home_score: 0, away_score: 14, status: 'live' },
      { quarter: 2, time: '09:45', home_score: 0, away_score: 21, status: 'live' },
      { quarter: 2, time: '02:20', home_score: 7, away_score: 21, status: 'live' },
      { quarter: 3, time: '11:10', home_score: 14, away_score: 21, status: 'live' },
      { quarter: 3, time: '05:35', home_score: 21, away_score: 21, status: 'live' },
      { quarter: 4, time: '08:20', home_score: 28, away_score: 21, status: 'live' },
      { quarter: 4, time: '00:00', home_score: 28, away_score: 21, status: 'final' }
    ]
  },

  OVERTIME_THRILLER: {
    name: 'Overtime Thriller',
    description: 'Game goes to overtime with dramatic finish',
    progression: [
      { quarter: 1, time: '15:00', home_score: 0, away_score: 0, status: 'live' },
      { quarter: 1, time: '07:30', home_score: 7, away_score: 0, status: 'live' },
      { quarter: 2, time: '10:15', home_score: 7, away_score: 7, status: 'live' },
      { quarter: 2, time: '03:40', home_score: 14, away_score: 7, status: 'live' },
      { quarter: 3, time: '08:50', home_score: 14, away_score: 14, status: 'live' },
      { quarter: 4, time: '12:25', home_score: 21, away_score: 14, status: 'live' },
      { quarter: 4, time: '01:45', home_score: 21, away_score: 21, status: 'live' },
      { quarter: 4, time: '00:00', home_score: 21, away_score: 21, status: 'overtime' },
      { quarter: 5, time: '10:00', home_score: 21, away_score: 21, status: 'overtime' },
      { quarter: 5, time: '06:30', home_score: 28, away_score: 21, status: 'final' }
    ]
  },

  DEFENSIVE_BATTLE: {
    name: 'Defensive Struggle',
    description: 'Low-scoring defensive game',
    progression: [
      { quarter: 1, time: '15:00', home_score: 0, away_score: 0, status: 'live' },
      { quarter: 1, time: '08:15', home_score: 3, away_score: 0, status: 'live' },
      { quarter: 2, time: '11:20', home_score: 3, away_score: 3, status: 'live' },
      { quarter: 3, time: '06:45', home_score: 6, away_score: 3, status: 'live' },
      { quarter: 4, time: '09:30', home_score: 6, away_score: 6, status: 'live' },
      { quarter: 4, time: '03:15', home_score: 9, away_score: 6, status: 'live' },
      { quarter: 4, time: '00:00', home_score: 9, away_score: 6, status: 'final' }
    ]
  },

  HIGH_SCORING: {
    name: 'Shootout',
    description: 'High-scoring offensive showcase',
    progression: [
      { quarter: 1, time: '15:00', home_score: 0, away_score: 0, status: 'live' },
      { quarter: 1, time: '11:45', home_score: 7, away_score: 0, status: 'live' },
      { quarter: 1, time: '07:20', home_score: 7, away_score: 7, status: 'live' },
      { quarter: 1, time: '02:30', home_score: 14, away_score: 7, status: 'live' },
      { quarter: 2, time: '13:15', home_score: 14, away_score: 14, status: 'live' },
      { quarter: 2, time: '08:40', home_score: 21, away_score: 14, status: 'live' },
      { quarter: 2, time: '04:10', home_score: 21, away_score: 21, status: 'live' },
      { quarter: 2, time: '01:05', home_score: 28, away_score: 21, status: 'live' },
      { quarter: 3, time: '10:30', home_score: 28, away_score: 28, status: 'live' },
      { quarter: 3, time: '05:15', home_score: 35, away_score: 28, status: 'live' },
      { quarter: 4, time: '11:45', home_score: 35, away_score: 35, status: 'live' },
      { quarter: 4, time: '06:20', home_score: 42, away_score: 35, status: 'live' },
      { quarter: 4, time: '02:10', home_score: 42, away_score: 42, status: 'live' },
      { quarter: 4, time: '00:00', home_score: 49, away_score: 42, status: 'final' }
    ]
  }
};

// Prediction data that correlates with game scenarios
export const generatePredictionData = (gameState: any, scenario: string = 'NAIL_BITER') => {
  const scoreDiff = gameState.home_score - gameState.away_score;
  const quarterProgress = (gameState.quarter - 1) / 4;
  const timeRemaining = parseFloat(gameState.time.split(':')[0]) + parseFloat(gameState.time.split(':')[1]) / 60;
  const timeElapsed = 1 - (timeRemaining / 15);

  let baseHomeWinProb = 0.5;

  // Adjust based on score difference
  baseHomeWinProb += scoreDiff * 0.03;

  // Adjust based on time remaining (more weight to score difference as game progresses)
  const timeWeight = quarterProgress * 0.5;
  baseHomeWinProb += scoreDiff * timeWeight * 0.02;

  // Scenario-specific adjustments
  switch (scenario) {
    case 'BLOWOUT':
      baseHomeWinProb += Math.abs(scoreDiff) > 14 ? (scoreDiff > 0 ? 0.3 : -0.3) : 0;
      break;
    case 'COMEBACK':
      if (gameState.quarter <= 2 && scoreDiff < -14) {
        baseHomeWinProb += 0.1; // Slightly favor comeback potential
      }
      break;
    case 'DEFENSIVE_BATTLE':
      baseHomeWinProb += scoreDiff * 0.05; // Field goals more impactful
      break;
  }

  // Clamp between 0.05 and 0.95
  const homeWinProb = Math.max(0.05, Math.min(0.95, baseHomeWinProb));
  const awayWinProb = 1 - homeWinProb;

  // Calculate confidence based on game state
  let confidence = 0.7;
  confidence += Math.abs(scoreDiff) * 0.02;
  confidence += quarterProgress * 0.2;
  confidence = Math.min(0.95, confidence);

  // Calculate predicted spread
  const predictedSpread = scoreDiff + (Math.random() - 0.5) * 4;

  return {
    home_win_probability: homeWinProb,
    away_win_probability: awayWinProb,
    predicted_spread: predictedSpread,
    confidence_level: confidence,
    model_version: '2.1.0'
  };
};

// Odds data from various sportsbooks
export const SPORTSBOOK_ODDS = {
  DRAFTKINGS: {
    name: 'DraftKings',
    reputation: 'premium',
    updateFrequency: 'high'
  },
  FANDUEL: {
    name: 'FanDuel',
    reputation: 'premium',
    updateFrequency: 'high'
  },
  BETMGM: {
    name: 'BetMGM',
    reputation: 'standard',
    updateFrequency: 'medium'
  },
  CAESARS: {
    name: 'Caesars',
    reputation: 'standard',
    updateFrequency: 'medium'
  },
  POINTSBET: {
    name: 'PointsBet',
    reputation: 'standard',
    updateFrequency: 'low'
  }
};

export const generateOddsData = (gameState: any, sportsbook: string) => {
  const scoreDiff = gameState.home_score - gameState.away_score;
  const baseSpread = -scoreDiff + (Math.random() - 0.5) * 2;

  // Sportsbook-specific adjustments
  const bookAdjustment = {
    'DraftKings': 0,
    'FanDuel': 0.5,
    'BetMGM': -0.5,
    'Caesars': 0.25,
    'PointsBet': -0.25
  }[sportsbook] || 0;

  const adjustedSpread = baseSpread + bookAdjustment;

  // Calculate moneylines based on spread
  const homeMoneyline = adjustedSpread > 0
    ? 100 + (adjustedSpread * 20)
    : -100 - (Math.abs(adjustedSpread) * 20);

  const awayMoneyline = adjustedSpread < 0
    ? 100 + (Math.abs(adjustedSpread) * 20)
    : -100 - (adjustedSpread * 20);

  // Calculate over/under based on scoring pace
  const totalScore = gameState.home_score + gameState.away_score;
  const quarterProgress = gameState.quarter / 4;
  const projectedTotal = quarterProgress > 0 ? (totalScore / quarterProgress) : 45;
  const overUnder = Math.round((projectedTotal + (Math.random() - 0.5) * 10) * 2) / 2;

  return {
    sportsbook,
    spread: Math.round(adjustedSpread * 2) / 2, // Round to nearest 0.5
    moneyline_home: Math.round(homeMoneyline),
    moneyline_away: Math.round(awayMoneyline),
    over_under: overUnder
  };
};

// Weather conditions that affect gameplay
export const WEATHER_CONDITIONS = [
  { condition: 'clear', temperature: 72, wind: 5, description: 'Perfect conditions' },
  { condition: 'rain', temperature: 45, wind: 12, description: 'Light rain' },
  { condition: 'snow', temperature: 28, wind: 18, description: 'Snow flurries' },
  { condition: 'windy', temperature: 55, wind: 25, description: 'High winds' },
  { condition: 'extreme_cold', temperature: -5, wind: 15, description: 'Extreme cold' },
  { condition: 'dome', temperature: 72, wind: 0, description: 'Indoor/Dome' }
];

// Sunday schedule generator
export const generateSundaySchedule = (week: number = 1): any[] => {
  const games = [];
  const timeSlots = ['13:00', '13:00', '13:00', '13:00', '16:05', '16:25', '16:25', '20:20'];

  // Select random team matchups
  const availableTeams = [...ALL_TEAMS];

  for (let i = 0; i < 8; i++) {
    // Pick two random teams
    const homeIndex = Math.floor(Math.random() * availableTeams.length);
    const homeTeam = availableTeams.splice(homeIndex, 1)[0];

    const awayIndex = Math.floor(Math.random() * availableTeams.length);
    const awayTeam = availableTeams.splice(awayIndex, 1)[0];

    const scenario = Object.keys(GAME_SCENARIOS)[Math.floor(Math.random() * Object.keys(GAME_SCENARIOS).length)];
    const weather = WEATHER_CONDITIONS[Math.floor(Math.random() * WEATHER_CONDITIONS.length)];

    games.push({
      game_id: `nfl_week${week}_game${i + 1}`,
      home_team: homeTeam.name,
      away_team: awayTeam.name,
      home_abbreviation: homeTeam.abbreviation,
      away_abbreviation: awayTeam.abbreviation,
      scheduled_time: timeSlots[i],
      scenario: scenario,
      weather: weather,
      week: week,
      season: 2024
    });
  }

  return games;
};

// Message generators for WebSocket testing
export const createGameUpdateMessage = (gameId: string, gameState: any) => ({
  event_type: WebSocketEventType.GAME_UPDATE,
  data: {
    game_id: gameId,
    home_team: gameState.home_team,
    away_team: gameState.away_team,
    home_score: gameState.home_score,
    away_score: gameState.away_score,
    quarter: gameState.quarter,
    time_remaining: gameState.time,
    game_status: gameState.status,
    updated_at: new Date().toISOString()
  },
  timestamp: new Date().toISOString()
});

export const createPredictionUpdateMessage = (gameId: string, gameState: any, scenario: string) => {
  const predictionData = generatePredictionData(gameState, scenario);

  return {
    event_type: WebSocketEventType.PREDICTION_UPDATE,
    data: {
      game_id: gameId,
      home_team: gameState.home_team,
      away_team: gameState.away_team,
      ...predictionData,
      updated_at: new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  };
};

export const createOddsUpdateMessage = (gameId: string, gameState: any, sportsbook: string) => {
  const oddsData = generateOddsData(gameState, sportsbook);

  return {
    event_type: WebSocketEventType.ODDS_UPDATE,
    data: {
      game_id: gameId,
      home_team: gameState.home_team,
      away_team: gameState.away_team,
      ...oddsData,
      updated_at: new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  };
};

// Simulate complete game progression
export class GameSimulator {
  private gameId: string;
  private scenario: string;
  private homeTeam: string;
  private awayTeam: string;
  private currentStateIndex: number = 0;
  private progression: any[];

  constructor(gameId: string, homeTeam: string, awayTeam: string, scenario: string = 'NAIL_BITER') {
    this.gameId = gameId;
    this.scenario = scenario;
    this.homeTeam = homeTeam;
    this.awayTeam = awayTeam;
    this.progression = GAME_SCENARIOS[scenario as keyof typeof GAME_SCENARIOS].progression;
  }

  getNextState() {
    if (this.currentStateIndex >= this.progression.length) {
      return null;
    }

    const state = this.progression[this.currentStateIndex];
    this.currentStateIndex++;

    return {
      ...state,
      home_team: this.homeTeam,
      away_team: this.awayTeam
    };
  }

  getCurrentState() {
    if (this.currentStateIndex === 0) return null;

    const state = this.progression[this.currentStateIndex - 1];
    return {
      ...state,
      home_team: this.homeTeam,
      away_team: this.awayTeam
    };
  }

  isComplete() {
    return this.currentStateIndex >= this.progression.length;
  }

  reset() {
    this.currentStateIndex = 0;
  }

  // Generate all messages for current state
  generateAllMessages() {
    const currentState = this.getCurrentState();
    if (!currentState) return [];

    const messages = [];

    // Game update
    messages.push(createGameUpdateMessage(this.gameId, currentState));

    // Prediction update
    messages.push(createPredictionUpdateMessage(this.gameId, currentState, this.scenario));

    // Odds updates from multiple sportsbooks
    Object.keys(SPORTSBOOK_ODDS).forEach(sportsbook => {
      messages.push(createOddsUpdateMessage(this.gameId, currentState, SPORTSBOOK_ODDS[sportsbook as keyof typeof SPORTSBOOK_ODDS].name));
    });

    return messages;
  }
}

// Test data presets for common scenarios
export const TEST_PRESETS = {
  SINGLE_GAME: {
    name: 'Single Game Test',
    games: [
      { homeTeam: 'Patriots', awayTeam: 'Bills', scenario: 'NAIL_BITER' }
    ]
  },

  SUNDAY_AFTERNOON: {
    name: 'Sunday Afternoon Games',
    games: generateSundaySchedule().slice(0, 4)
  },

  PRIME_TIME: {
    name: 'Prime Time Game',
    games: [
      { homeTeam: 'Cowboys', awayTeam: 'Packers', scenario: 'OVERTIME_THRILLER' }
    ]
  },

  PLAYOFF_WEEKEND: {
    name: 'Playoff Weekend',
    games: [
      { homeTeam: 'Chiefs', awayTeam: 'Bills', scenario: 'NAIL_BITER' },
      { homeTeam: '49ers', awayTeam: 'Seahawks', scenario: 'COMEBACK' },
      { homeTeam: 'Ravens', awayTeam: 'Steelers', scenario: 'DEFENSIVE_BATTLE' },
      { homeTeam: 'Cowboys', awayTeam: 'Eagles', scenario: 'HIGH_SCORING' }
    ]
  },

  SUPER_BOWL: {
    name: 'Super Bowl',
    games: [
      { homeTeam: 'Chiefs', awayTeam: '49ers', scenario: 'OVERTIME_THRILLER' }
    ]
  }
};

export default {
  NFL_TEAMS,
  ALL_TEAMS,
  GAME_SCENARIOS,
  SPORTSBOOK_ODDS,
  WEATHER_CONDITIONS,
  generateSundaySchedule,
  createGameUpdateMessage,
  createPredictionUpdateMessage,
  createOddsUpdateMessage,
  GameSimulator,
  TEST_PRESETS
};