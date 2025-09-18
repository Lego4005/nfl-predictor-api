import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadialBarChart, RadialBar, PieChart, Pie, Cell, Treemap, Heatmap
} from 'recharts';
import {
  TrendingUp, TrendingDown, Clock, Target, AlertTriangle, Activity,
  Sun, Moon, RefreshCw, Filter, Settings, Zap, Brain, Trophy,
  Users, BarChart3, LineChart as LineChartIcon, MapPin, Calendar
} from 'lucide-react';

// Types and interfaces
interface Game {
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
}

interface Team {
  id: string;
  name: string;
  city: string;
  abbreviation: string;
  logo: string;
  primaryColor: string;
  secondaryColor: string;
  record: {
    wins: number;
    losses: number;
    ties: number;
  };
}

interface Prediction {
  gameId: string;
  homeTeamWinProbability: number;
  awayTeamWinProbability: number;
  predictedHomeScore: number;
  predictedAwayScore: number;
  confidence: 'high' | 'medium' | 'low';
  modelAccuracy: number;
  keyFactors: string[];
  lastUpdated: string;
}

interface BettingOdds {
  gameId: string;
  sportsbook: string;
  homeOdds: number;
  awayOdds: number;
  overUnder: number;
  spread: number;
  lastUpdated: string;
}

interface InjuryReport {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  severity: 'critical' | 'moderate' | 'minor';
  impactScore: number;
  status: string;
  description: string;
}

interface BettingInsight {
  gameId: string;
  recommendation: 'strong_bet' | 'value_bet' | 'avoid' | 'wait';
  confidence: number;
  expectedValue: number;
  reasoning: string[];
  riskLevel: 'low' | 'medium' | 'high';
}

// Mock data generators
const generateMockTeams = (): Team[] => [
  { id: '1', name: 'Chiefs', city: 'Kansas City', abbreviation: 'KC', logo: '🏈', primaryColor: '#E31837', secondaryColor: '#FFB612', record: { wins: 8, losses: 2, ties: 0 } },
  { id: '2', name: 'Bills', city: 'Buffalo', abbreviation: 'BUF', logo: '🦬', primaryColor: '#00338D', secondaryColor: '#C60C30', record: { wins: 7, losses: 3, ties: 0 } },
  { id: '3', name: 'Cowboys', city: 'Dallas', abbreviation: 'DAL', logo: '⭐', primaryColor: '#041E42', secondaryColor: '#869397', record: { wins: 6, losses: 4, ties: 0 } },
  { id: '4', name: 'Patriots', city: 'New England', abbreviation: 'NE', logo: '🏛️', primaryColor: '#002244', secondaryColor: '#C60C30', record: { wins: 5, losses: 5, ties: 0 } },
];

const generateMockGames = (teams: Team[]): Game[] => [
  {
    id: '1',
    homeTeam: teams[0],
    awayTeam: teams[1],
    gameTime: '2024-01-15T20:00:00Z',
    week: 15,
    season: 2024,
    isLive: true,
    quarter: '2nd',
    timeRemaining: '8:34',
    homeScore: 14,
    awayScore: 10
  },
  {
    id: '2',
    homeTeam: teams[2],
    awayTeam: teams[3],
    gameTime: '2024-01-16T18:00:00Z',
    week: 15,
    season: 2024,
    isLive: false
  },
];

const generateMockPredictions = (): Prediction[] => [
  {
    gameId: '1',
    homeTeamWinProbability: 0.68,
    awayTeamWinProbability: 0.32,
    predictedHomeScore: 24,
    predictedAwayScore: 17,
    confidence: 'high',
    modelAccuracy: 0.73,
    keyFactors: ['Home field advantage', 'Recent offensive performance', 'Defensive matchup'],
    lastUpdated: '2024-01-15T19:45:00Z'
  },
  {
    gameId: '2',
    homeTeamWinProbability: 0.52,
    awayTeamWinProbability: 0.48,
    predictedHomeScore: 21,
    predictedAwayScore: 20,
    confidence: 'medium',
    modelAccuracy: 0.69,
    keyFactors: ['Similar team strength', 'Weather conditions', 'Injury concerns'],
    lastUpdated: '2024-01-16T17:30:00Z'
  },
];

const generateMockOdds = (): BettingOdds[] => [
  { gameId: '1', sportsbook: 'DraftKings', homeOdds: -150, awayOdds: +130, overUnder: 44.5, spread: -3.5, lastUpdated: '2024-01-15T19:50:00Z' },
  { gameId: '1', sportsbook: 'FanDuel', homeOdds: -145, awayOdds: +125, overUnder: 45, spread: -3, lastUpdated: '2024-01-15T19:52:00Z' },
  { gameId: '2', sportsbook: 'BetMGM', homeOdds: -105, awayOdds: -115, overUnder: 42, spread: +1, lastUpdated: '2024-01-16T17:45:00Z' },
];

// Component: Live Score Ticker
const LiveScoreTicker: React.FC<{ games: Game[] }> = ({ games }) => {
  const [currentGameIndex, setCurrentGameIndex] = useState(0);
  const liveGames = games.filter(game => game.isLive);

  useEffect(() => {
    if (liveGames.length > 1) {
      const interval = setInterval(() => {
        setCurrentGameIndex((prev) => (prev + 1) % liveGames.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [liveGames.length]);

  if (liveGames.length === 0) {
    return (
      <div className="bg-gray-800 text-white py-2 px-4 text-center">
        <span className="text-sm">No live games currently</span>
      </div>
    );
  }

  const currentGame = liveGames[currentGameIndex];

  return (
    <motion.div
      className="bg-gradient-to-r from-red-600 to-red-700 text-white py-3 px-4 overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-center space-x-6">
        <div className="flex items-center space-x-2">
          <span className="live-indicator"></span>
          <span className="font-semibold text-sm">LIVE</span>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{currentGame.awayTeam.logo}</span>
            <span className="font-bold">{currentGame.awayTeam.abbreviation}</span>
            <span className="text-2xl font-bold">{currentGame.awayScore || 0}</span>
          </div>

          <span className="text-gray-300">@</span>

          <div className="flex items-center space-x-2">
            <span className="text-2xl font-bold">{currentGame.homeScore || 0}</span>
            <span className="font-bold">{currentGame.homeTeam.abbreviation}</span>
            <span className="text-lg">{currentGame.homeTeam.logo}</span>
          </div>
        </div>

        <div className="text-sm">
          <div className="font-medium">{currentGame.quarter} Quarter</div>
          <div className="text-gray-200">{currentGame.timeRemaining}</div>
        </div>
      </div>
    </motion.div>
  );
};

// Component: Prediction Card
const PredictionCard: React.FC<{ game: Game; prediction: Prediction }> = ({ game, prediction }) => {
  const confidenceColor = prediction.confidence === 'high' ? 'text-green-600 dark:text-green-400' :
                          prediction.confidence === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
                          'text-red-600 dark:text-red-400';

  return (
    <motion.div
      className="card card-hover p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -5 }}
    >
      {game.isLive && (
        <div className="flex items-center space-x-2 mb-4">
          <span className="live-indicator"></span>
          <span className="text-sm font-semibold text-red-600 dark:text-red-400">LIVE</span>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{game.awayTeam.logo}</span>
          <div>
            <div className="font-bold text-lg">{game.awayTeam.city} {game.awayTeam.name}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {game.awayTeam.record.wins}-{game.awayTeam.record.losses}
            </div>
          </div>
        </div>

        <div className="text-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">@</div>
          <div className="text-xs text-gray-500">
            {new Date(game.gameTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="font-bold text-lg">{game.homeTeam.city} {game.homeTeam.name}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {game.homeTeam.record.wins}-{game.homeTeam.record.losses}
            </div>
          </div>
          <span className="text-2xl">{game.homeTeam.logo}</span>
        </div>
      </div>

      {game.isLive && game.homeScore !== undefined && game.awayScore !== undefined && (
        <div className="flex justify-between items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-3 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{game.awayScore}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Current</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">{game.quarter} • {game.timeRemaining}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{game.homeScore}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Current</div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Win Probability</span>
          <span className={`text-sm font-bold ${confidenceColor}`}>
            {prediction.confidence.toUpperCase()} CONFIDENCE
          </span>
        </div>

        <div className="relative">
          <div className="flex h-8 rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700">
            <motion.div
              className="bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold"
              style={{ width: `${prediction.awayTeamWinProbability * 100}%` }}
              initial={{ width: 0 }}
              animate={{ width: `${prediction.awayTeamWinProbability * 100}%` }}
              transition={{ duration: 1, delay: 0.5 }}
            >
              {prediction.awayTeamWinProbability > 0.15 && `${(prediction.awayTeamWinProbability * 100).toFixed(0)}%`}
            </motion.div>
            <motion.div
              className="bg-gradient-to-r from-green-500 to-green-600 flex items-center justify-center text-white text-xs font-bold"
              style={{ width: `${prediction.homeTeamWinProbability * 100}%` }}
              initial={{ width: 0 }}
              animate={{ width: `${prediction.homeTeamWinProbability * 100}%` }}
              transition={{ duration: 1, delay: 0.7 }}
            >
              {prediction.homeTeamWinProbability > 0.15 && `${(prediction.homeTeamWinProbability * 100).toFixed(0)}%`}
            </motion.div>
          </div>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-blue-600 dark:text-blue-400 font-medium">
            {game.awayTeam.abbreviation}: {(prediction.awayTeamWinProbability * 100).toFixed(1)}%
          </span>
          <span className="text-green-600 dark:text-green-400 font-medium">
            {game.homeTeam.abbreviation}: {(prediction.homeTeamWinProbability * 100).toFixed(1)}%
          </span>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
          <div className="flex justify-between text-sm mb-2">
            <span>Predicted Score:</span>
            <span className="font-medium">
              {game.awayTeam.abbreviation} {prediction.predictedAwayScore} - {prediction.predictedHomeScore} {game.homeTeam.abbreviation}
            </span>
          </div>

          <div className="flex justify-between text-sm mb-2">
            <span>Model Accuracy:</span>
            <span className="font-medium">{(prediction.modelAccuracy * 100).toFixed(1)}%</span>
          </div>

          <div className="mt-3">
            <div className="text-sm font-medium mb-2">Key Factors:</div>
            <div className="flex flex-wrap gap-1">
              {prediction.keyFactors.map((factor, index) => (
                <span key={index} className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs rounded-full">
                  {factor}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// Component: Odds Comparison
const OddsComparison: React.FC<{ gameId: string; odds: BettingOdds[] }> = ({ gameId, odds }) => {
  const gameOdds = odds.filter(odd => odd.gameId === gameId);

  if (gameOdds.length === 0) {
    return null;
  }

  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center space-x-2 mb-4">
        <Target className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-bold">Betting Odds</h3>
      </div>

      <div className="space-y-3">
        {gameOdds.map((odd, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="font-medium text-sm">{odd.sportsbook}</div>

            <div className="flex space-x-4 text-sm">
              <div className="text-center">
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Moneyline</div>
                <div className="space-x-2">
                  <span className={`betting-odds ${odd.awayOdds < 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {odd.awayOdds > 0 ? '+' : ''}{odd.awayOdds}
                  </span>
                  <span className={`betting-odds ${odd.homeOdds < 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {odd.homeOdds > 0 ? '+' : ''}{odd.homeOdds}
                  </span>
                </div>
              </div>

              <div className="text-center">
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Spread</div>
                <div className="betting-odds">
                  {odd.spread > 0 ? '+' : ''}{odd.spread}
                </div>
              </div>

              <div className="text-center">
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">O/U</div>
                <div className="betting-odds">{odd.overUnder}</div>
              </div>
            </div>

            <div className="text-xs text-gray-500">
              {new Date(odd.lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex items-center space-x-2 mb-2">
          <Brain className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span className="text-sm font-medium text-blue-800 dark:text-blue-300">Best Value</span>
        </div>
        <div className="text-sm text-blue-700 dark:text-blue-400">
          Shop around for the best odds. Even small differences can impact your long-term returns.
        </div>
      </div>
    </motion.div>
  );
};

// Component: Win Probability Chart
const WinProbabilityChart: React.FC<{ predictions: Prediction[], games: Game[] }> = ({ predictions, games }) => {
  const chartData = predictions.map(prediction => {
    const game = games.find(g => g.id === prediction.gameId);
    return {
      game: game ? `${game.awayTeam.abbreviation} @ ${game.homeTeam.abbreviation}` : 'Unknown',
      away: Math.round(prediction.awayTeamWinProbability * 100),
      home: Math.round(prediction.homeTeamWinProbability * 100),
      confidence: prediction.confidence
    };
  });

  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-bold">Win Probability Analysis</h3>
        </div>
        <div className="flex space-x-2 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            <span>Away</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Home</span>
          </div>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="game"
              angle={-45}
              textAnchor="end"
              height={60}
              fontSize={10}
            />
            <YAxis
              domain={[0, 100]}
              label={{ value: 'Win Probability (%)', angle: -90, position: 'insideLeft' }}
              fontSize={12}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: 'none',
                borderRadius: '8px',
                color: 'white'
              }}
              formatter={(value: any) => [`${value}%`, '']}
            />
            <Bar dataKey="away" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="home" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};

// Component: Team Performance Heatmap
const TeamStats: React.FC<{ teams: Team[] }> = ({ teams }) => {
  const generateHeatmapData = () => {
    const metrics = ['Offense', 'Defense', 'Special Teams', 'Coaching', 'Momentum'];
    const data: any[] = [];

    teams.forEach(team => {
      metrics.forEach(metric => {
        data.push({
          team: team.abbreviation,
          metric,
          value: Math.random() * 100,
          performance: Math.random() > 0.5 ? 'good' : 'poor'
        });
      });
    });

    return data;
  };

  const heatmapData = generateHeatmapData();
  const metrics = ['Offense', 'Defense', 'Special Teams', 'Coaching', 'Momentum'];

  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center space-x-2 mb-6">
        <Activity className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-bold">Team Performance Matrix</h3>
      </div>

      <div className="grid grid-cols-6 gap-2">
        <div className="text-xs font-medium text-gray-600 dark:text-gray-400"></div>
        {metrics.map(metric => (
          <div key={metric} className="text-xs font-medium text-gray-600 dark:text-gray-400 text-center p-2">
            {metric}
          </div>
        ))}

        {teams.map(team => (
          <React.Fragment key={team.id}>
            <div className="text-sm font-medium flex items-center space-x-2 p-2">
              <span>{team.logo}</span>
              <span>{team.abbreviation}</span>
            </div>
            {metrics.map(metric => {
              const dataPoint = heatmapData.find(d => d.team === team.abbreviation && d.metric === metric);
              const intensity = dataPoint ? dataPoint.value : 0;
              const backgroundColor = `rgba(${intensity > 50 ? '34, 197, 94' : '239, 68, 68'}, ${intensity / 100})`;

              return (
                <motion.div
                  key={`${team.id}-${metric}`}
                  className="p-3 rounded text-center text-xs font-medium text-white"
                  style={{ backgroundColor }}
                  whileHover={{ scale: 1.1 }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: Math.random() * 0.5 }}
                >
                  {Math.round(intensity)}
                </motion.div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </motion.div>
  );
};

// Component: Injury Impact Analysis
const InjuryImpactAnalysis: React.FC = () => {
  const mockInjuries: InjuryReport[] = [
    {
      playerId: '1',
      playerName: 'Patrick Mahomes',
      position: 'QB',
      team: 'KC',
      severity: 'moderate',
      impactScore: 8.5,
      status: 'Questionable',
      description: 'Ankle sprain'
    },
    {
      playerId: '2',
      playerName: 'Josh Allen',
      position: 'QB',
      team: 'BUF',
      severity: 'minor',
      impactScore: 3.2,
      status: 'Probable',
      description: 'Shoulder soreness'
    },
    {
      playerId: '3',
      playerName: 'Dak Prescott',
      position: 'QB',
      team: 'DAL',
      severity: 'critical',
      impactScore: 9.8,
      status: 'Doubtful',
      description: 'Hamstring injury'
    }
  ];

  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case 'critical': return 'injury-critical';
      case 'moderate': return 'injury-moderate';
      case 'minor': return 'injury-minor';
      default: return '';
    }
  };

  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center space-x-2 mb-6">
        <AlertTriangle className="w-5 h-5 text-yellow-600" />
        <h3 className="text-lg font-bold">Injury Impact Analysis</h3>
      </div>

      <div className="space-y-4">
        {mockInjuries.map(injury => (
          <motion.div
            key={injury.playerId}
            className={`p-4 rounded-lg border-l-4 ${getSeverityClass(injury.severity)}`}
            whileHover={{ x: 5 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <div className="font-bold">{injury.playerName}</div>
                <div className="text-sm px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">
                  {injury.position}
                </div>
                <div className="text-sm font-medium">{injury.team}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold">Impact: {injury.impactScore}/10</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">{injury.status}</div>
              </div>
            </div>

            <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              {injury.description}
            </div>

            <div className="flex items-center justify-between">
              <div className={`text-xs px-2 py-1 rounded-full font-medium ${getSeverityClass(injury.severity)}`}>
                {injury.severity.toUpperCase()}
              </div>
              <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <motion.div
                  className="h-2 rounded-full bg-gradient-to-r from-yellow-400 to-red-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${injury.impactScore * 10}%` }}
                  transition={{ duration: 1, delay: 0.3 }}
                />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

// Component: Betting Insights
const BettingInsights: React.FC<{ predictions: Prediction[], odds: BettingOdds[] }> = ({ predictions, odds }) => {
  const generateInsights = (): BettingInsight[] => {
    return predictions.map(prediction => {
      const gameOdds = odds.filter(odd => odd.gameId === prediction.gameId);
      const avgHomeOdds = gameOdds.reduce((sum, odd) => sum + odd.homeOdds, 0) / gameOdds.length;

      const expectedValue = (prediction.homeTeamWinProbability - (1 / (1 + Math.abs(avgHomeOdds) / 100))) * 100;

      return {
        gameId: prediction.gameId,
        recommendation: expectedValue > 10 ? 'strong_bet' : expectedValue > 5 ? 'value_bet' : expectedValue < -5 ? 'avoid' : 'wait',
        confidence: prediction.confidence === 'high' ? 0.85 : prediction.confidence === 'medium' ? 0.65 : 0.45,
        expectedValue,
        reasoning: [
          `Model confidence: ${prediction.confidence}`,
          `Win probability: ${(prediction.homeTeamWinProbability * 100).toFixed(1)}%`,
          `Expected value: ${expectedValue.toFixed(1)}%`
        ],
        riskLevel: Math.abs(expectedValue) > 10 ? 'high' : Math.abs(expectedValue) > 5 ? 'medium' : 'low'
      };
    });
  };

  const insights = generateInsights();

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'strong_bet': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      case 'value_bet': return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30';
      case 'avoid': return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      default: return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
    }
  };

  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="flex items-center space-x-2 mb-6">
        <Brain className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-bold">AI Betting Insights</h3>
      </div>

      <div className="space-y-4">
        {insights.map(insight => {
          const prediction = predictions.find(p => p.gameId === insight.gameId);

          return (
            <motion.div
              key={insight.gameId}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`px-3 py-1 rounded-full text-sm font-bold ${getRecommendationColor(insight.recommendation)}`}>
                  {insight.recommendation.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-sm">
                  Confidence: <span className="font-bold">{(insight.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                {insight.reasoning.map((reason, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 bg-primary-500 rounded-full"></div>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>

              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between text-sm">
                  <span>Risk Level:</span>
                  <span className={`font-medium ${
                    insight.riskLevel === 'high' ? 'text-red-600 dark:text-red-400' :
                    insight.riskLevel === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
                    'text-green-600 dark:text-green-400'
                  }`}>
                    {insight.riskLevel.toUpperCase()}
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

// Component: Historical Accuracy Tracking
const HistoricalAccuracy: React.FC = () => {
  const accuracyData = [
    { week: 'Week 10', accuracy: 68, predictions: 16, correct: 11 },
    { week: 'Week 11', accuracy: 73, predictions: 14, correct: 10 },
    { week: 'Week 12', accuracy: 71, predictions: 13, correct: 9 },
    { week: 'Week 13', accuracy: 76, predictions: 15, correct: 11 },
    { week: 'Week 14', accuracy: 69, predictions: 16, correct: 11 },
    { week: 'Week 15', accuracy: 81, predictions: 16, correct: 13 },
  ];

  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center space-x-2 mb-6">
        <Trophy className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-bold">Model Performance</h3>
      </div>

      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={accuracyData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="week" fontSize={12} />
            <YAxis
              domain={[50, 100]}
              label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
              fontSize={12}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: 'none',
                borderRadius: '8px',
                color: 'white'
              }}
              formatter={(value: any, name: any) => [`${value}%`, 'Accuracy']}
            />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 6 }}
              activeDot={{ r: 8, stroke: '#3b82f6', strokeWidth: 2, fill: 'white' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">73.2%</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Season Average</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">89</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total Predictions</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">65</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Correct Picks</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">81%</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Best Week</div>
        </div>
      </div>
    </motion.div>
  );
};

// Main Component: Smart Dashboard
const SmartDashboard: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');

  // Mock data
  const teams = generateMockTeams();
  const games = generateMockGames(teams);
  const predictions = generateMockPredictions();
  const odds = generateMockOdds();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setRefreshing(false);
  };

  const filteredGames = games.filter(game => {
    if (activeFilter === 'live') return game.isLive;
    if (activeFilter === 'upcoming') return !game.isLive;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Live Score Ticker */}
      <LiveScoreTicker games={games} />

      {/* Header */}
      <motion.div
        className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                NFL Smart Dashboard
              </h1>
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">AI-Powered</span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Filter Buttons */}
              <div className="hidden md:flex space-x-2">
                {['all', 'live', 'upcoming'].map(filter => (
                  <button
                    key={filter}
                    onClick={() => setActiveFilter(filter)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      activeFilter === filter
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                    }`}
                  >
                    {filter.charAt(0).toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>

              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
              </button>

              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeFilter}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="space-y-8"
          >
            {/* Game Predictions Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {filteredGames.map(game => {
                const gamePrediction = predictions.find(p => p.gameId === game.id);
                return gamePrediction ? (
                  <PredictionCard key={game.id} game={game} prediction={gamePrediction} />
                ) : null;
              })}
            </div>

            {/* Analytics Dashboard */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2">
                <WinProbabilityChart predictions={predictions} games={games} />
              </div>
              <div>
                <HistoricalAccuracy />
              </div>
            </div>

            {/* Team Performance and Odds */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TeamStats teams={teams} />
              <div className="space-y-6">
                {games.map(game => (
                  <OddsComparison key={game.id} gameId={game.id} odds={odds} />
                ))}
              </div>
            </div>

            {/* Injury Analysis and Betting Insights */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <InjuryImpactAnalysis />
              <BettingInsights predictions={predictions} odds={odds} />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default SmartDashboard;