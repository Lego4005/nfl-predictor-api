import { Game, Prediction, BettingOdds, Team, InjuryReport, ModelPerformance } from '../types/dashboard';

// Date and Time Utilities
export const formatGameTime = (gameTime: string): string => {
  const date = new Date(gameTime);
  return date.toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const getTimeUntilGame = (gameTime: string): string => {
  const now = new Date();
  const game = new Date(gameTime);
  const diff = game.getTime() - now.getTime();

  if (diff < 0) return 'Game Started';

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours < 24) {
    return `${hours}h ${minutes}m`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return `${days}d ${remainingHours}h`;
};

export const isGameLiveNow = (game: Game): boolean => {
  if (!game.isLive) return false;

  const now = new Date();
  const gameTime = new Date(game.gameTime);
  const threeHoursLater = new Date(gameTime.getTime() + (3 * 60 * 60 * 1000));

  return now >= gameTime && now <= threeHoursLater;
};

// Prediction Utilities
export const getPredictionConfidenceColor = (confidence: string): string => {
  switch (confidence) {
    case 'high': return 'text-green-600 dark:text-green-400';
    case 'medium': return 'text-yellow-600 dark:text-yellow-400';
    case 'low': return 'text-red-600 dark:text-red-400';
    default: return 'text-gray-600 dark:text-gray-400';
  }
};

export const calculateSpreadCover = (prediction: Prediction, spread: number): {
  covers: boolean;
  margin: number;
} => {
  const predictedMargin = prediction.predictedHomeScore - prediction.predictedAwayScore;
  const covers = predictedMargin > spread;
  const margin = Math.abs(predictedMargin - spread);

  return { covers, margin };
};

export const getImpliedProbability = (odds: number): number => {
  if (odds > 0) {
    return 100 / (odds + 100);
  } else {
    return Math.abs(odds) / (Math.abs(odds) + 100);
  }
};

export const calculateExpectedValue = (
  prediction: Prediction,
  odds: BettingOdds,
  betType: 'home' | 'away'
): number => {
  const winProb = betType === 'home' ? prediction.homeTeamWinProbability : prediction.awayTeamWinProbability;
  const oddsValue = betType === 'home' ? odds.homeOdds : odds.awayOdds;
  const impliedProb = getImpliedProbability(oddsValue);

  return (winProb - impliedProb) * 100;
};

// Team Utilities
export const getTeamRecord = (team: Team): string => {
  return `${team.record.wins}-${team.record.losses}${team.record.ties > 0 ? `-${team.record.ties}` : ''}`;
};

export const getWinPercentage = (team: Team): number => {
  const totalGames = team.record.wins + team.record.losses + team.record.ties;
  if (totalGames === 0) return 0;

  return (team.record.wins + (team.record.ties * 0.5)) / totalGames;
};

export const compareTeamStrength = (team1: Team, team2: Team): number => {
  const team1WinPct = getWinPercentage(team1);
  const team2WinPct = getWinPercentage(team2);

  return team1WinPct - team2WinPct;
};

// Injury Impact Utilities
export const getInjurySeverityColor = (severity: string): string => {
  switch (severity) {
    case 'critical': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-500';
    case 'moderate': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-500';
    case 'minor': return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-500';
    default: return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 border-gray-500';
  }
};

export const calculateTeamInjuryImpact = (injuries: InjuryReport[]): number => {
  return injuries.reduce((total, injury) => total + injury.impactScore, 0) / injuries.length || 0;
};

export const getPositionImpact = (position: string): number => {
  const impactMap: { [key: string]: number } = {
    'QB': 10,
    'RB': 7,
    'WR': 6,
    'TE': 5,
    'OL': 6,
    'DE': 7,
    'DT': 6,
    'LB': 6,
    'CB': 7,
    'S': 6,
    'K': 3,
    'P': 2
  };

  return impactMap[position] || 5;
};

// Betting Utilities
export const formatOdds = (odds: number): string => {
  return odds > 0 ? `+${odds}` : odds.toString();
};

export const calculatePayout = (bet: number, odds: number): number => {
  if (odds > 0) {
    return bet + (bet * odds / 100);
  } else {
    return bet + (bet * 100 / Math.abs(odds));
  }
};

export const getOddsMovement = (currentOdds: number, previousOdds: number): {
  direction: 'up' | 'down' | 'same';
  change: number;
} => {
  const change = currentOdds - previousOdds;
  let direction: 'up' | 'down' | 'same' = 'same';

  if (change > 0) direction = 'up';
  else if (change < 0) direction = 'down';

  return { direction, change };
};

// Chart Data Utilities
export const generateColorFromString = (str: string): string => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }

  const hue = hash % 360;
  return `hsl(${hue}, 70%, 50%)`;
};

export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value);
};

// Model Performance Utilities
export const calculateModelAccuracy = (predictions: Prediction[], actualResults: any[]): number => {
  if (predictions.length === 0) return 0;

  const correct = predictions.reduce((count, pred) => {
    const actual = actualResults.find(result => result.gameId === pred.gameId);
    if (!actual) return count;

    const predictedWinner = pred.homeTeamWinProbability > 0.5 ? 'home' : 'away';
    const actualWinner = actual.homeScore > actual.awayScore ? 'home' : 'away';

    return predictedWinner === actualWinner ? count + 1 : count;
  }, 0);

  return correct / predictions.length;
};

export const getConfidenceBucket = (predictions: Prediction[]): {
  high: number;
  medium: number;
  low: number;
} => {
  const buckets = { high: 0, medium: 0, low: 0 };

  predictions.forEach(pred => {
    buckets[pred.confidence]++;
  });

  return buckets;
};

// Data Validation Utilities
export const isValidPrediction = (prediction: Prediction): boolean => {
  return (
    prediction.homeTeamWinProbability >= 0 &&
    prediction.homeTeamWinProbability <= 1 &&
    prediction.awayTeamWinProbability >= 0 &&
    prediction.awayTeamWinProbability <= 1 &&
    Math.abs((prediction.homeTeamWinProbability + prediction.awayTeamWinProbability) - 1) < 0.01
  );
};

export const sanitizeGameData = (game: Game): Game => {
  return {
    ...game,
    homeScore: game.homeScore && game.homeScore >= 0 ? game.homeScore : undefined,
    awayScore: game.awayScore && game.awayScore >= 0 ? game.awayScore : undefined,
    quarter: game.quarter || undefined,
    timeRemaining: game.timeRemaining || undefined
  };
};

// Local Storage Utilities
export const saveToLocalStorage = (key: string, data: any): void => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
};

export const loadFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Failed to load from localStorage:', error);
    return defaultValue;
  }
};

// Animation Utilities
export const getStaggerDelay = (index: number, baseDelay: number = 0.1): number => {
  return baseDelay + (index * 0.05);
};

export const createSpringConfig = (damping: number = 0.8, stiffness: number = 100) => ({
  type: 'spring',
  damping,
  stiffness
});

// Responsive Utilities
export const getResponsiveColumns = (screenWidth: number): number => {
  if (screenWidth >= 1536) return 4; // 2xl
  if (screenWidth >= 1280) return 3; // xl
  if (screenWidth >= 1024) return 2; // lg
  return 1; // sm, md
};

export const isMobileDevice = (): boolean => {
  return window.innerWidth < 768;
};

// Export all utilities as a single object for easier imports
export const DashboardUtils = {
  formatGameTime,
  getTimeUntilGame,
  isGameLiveNow,
  getPredictionConfidenceColor,
  calculateSpreadCover,
  getImpliedProbability,
  calculateExpectedValue,
  getTeamRecord,
  getWinPercentage,
  compareTeamStrength,
  getInjurySeverityColor,
  calculateTeamInjuryImpact,
  getPositionImpact,
  formatOdds,
  calculatePayout,
  getOddsMovement,
  generateColorFromString,
  formatPercentage,
  formatCurrency,
  calculateModelAccuracy,
  getConfidenceBucket,
  isValidPrediction,
  sanitizeGameData,
  saveToLocalStorage,
  loadFromLocalStorage,
  getStaggerDelay,
  createSpringConfig,
  getResponsiveColumns,
  isMobileDevice
};