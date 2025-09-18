import React, { memo, useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Pause, Clock, Target, TrendingUp, TrendingDown,
  Zap, Activity, AlertTriangle, Maximize2, Minimize2,
  RefreshCw, Volume2, VolumeX, Settings, Eye,
  ArrowRight, BarChart3, Users, Calendar
} from 'lucide-react';
import {
  LiveGameData, ComprehensivePrediction, GameEvent, RealtimeUpdate
} from '../types/predictions';
import { Game } from '../types/dashboard';

interface LiveGameDashboardProps {
  liveGames: LiveGameData[];
  livePredictions: ComprehensivePrediction[];
  onGameSelect?: (gameId: string) => void;
  onPredictionUpdate?: (prediction: ComprehensivePrediction) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
  className?: string;
}

interface GameDisplay extends LiveGameData {
  game_info: Game;
  updated_predictions: ComprehensivePrediction[];
  momentum_changes: number;
  critical_events: GameEvent[];
  prediction_accuracy: number;
}

const LiveGameDashboard: React.FC<LiveGameDashboardProps> = memo(({
  liveGames,
  livePredictions,
  onGameSelect,
  onPredictionUpdate,
  autoRefresh = true,
  refreshInterval = 5000,
  className = ''
}) => {
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [expandedView, setExpandedView] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [realtimeUpdates, setRealtimeUpdates] = useState<RealtimeUpdate[]>([]);

  // Enhanced game data with predictions and events
  const enhancedGames = useMemo((): GameDisplay[] => {
    return liveGames.map(game => {
      const gamePredictions = livePredictions.filter(p => p.game_id === game.game_id);
      const recentEvents = game.key_events.slice(-5);

      // Calculate momentum changes in last 5 minutes
      const recentMomentumEvents = game.key_events.filter(event => {
        const eventTime = new Date(event.timestamp);
        const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
        return eventTime > fiveMinutesAgo;
      });

      // Calculate prediction accuracy for live updates
      const correctPredictions = gamePredictions.filter(p => p.is_correct).length;
      const totalPredictions = gamePredictions.filter(p => p.is_correct !== undefined).length;
      const predictionAccuracy = totalPredictions > 0 ? correctPredictions / totalPredictions : 0;

      return {
        ...game,
        game_info: {} as Game, // Would be populated with actual game info
        updated_predictions: gamePredictions,
        momentum_changes: recentMomentumEvents.length,
        critical_events: recentEvents.filter(e => Math.abs(e.impact_score) >= 7),
        prediction_accuracy: predictionAccuracy
      };
    });
  }, [liveGames, livePredictions]);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setLastUpdated(new Date());
      // Trigger data refresh - would typically call API
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Handle real-time updates
  useEffect(() => {
    // Simulate real-time updates - would be from WebSocket
    const interval = setInterval(() => {
      const newUpdate: RealtimeUpdate = {
        type: 'game_event',
        timestamp: new Date().toISOString(),
        data: {
          event: 'score_update',
          game_id: enhancedGames[0]?.game_id,
        },
        affected_predictions: [],
        severity: 'medium'
      };

      setRealtimeUpdates(prev => [newUpdate, ...prev.slice(0, 9)]);
    }, 10000);

    return () => clearInterval(interval);
  }, [enhancedGames]);

  const getQuarterDisplay = (quarter: number) => {
    switch (quarter) {
      case 1: return '1st';
      case 2: return '2nd';
      case 3: return '3rd';
      case 4: return '4th';
      case 5: return 'OT';
      default: return 'Final';
    }
  };

  const getMomentumColor = (strength: number) => {
    if (strength > 50) return 'text-green-500';
    if (strength > 20) return 'text-yellow-500';
    if (strength < -50) return 'text-red-500';
    if (strength < -20) return 'text-orange-500';
    return 'text-gray-500';
  };

  const getWinProbabilityChange = (current: number, previous: number = 50) => {
    const change = current - previous;
    return {
      value: Math.abs(change),
      direction: change > 0 ? 'up' : 'down',
      significant: Math.abs(change) > 10
    };
  };

  const LiveGameCard = ({ game }: { game: GameDisplay }) => {
    const winProbChange = getWinProbabilityChange(game.win_probability.home);
    const isSelected = selectedGame === game.game_id;

    return (
      <motion.div
        className={`
          relative p-4 rounded-xl border transition-all duration-200 cursor-pointer
          ${isSelected
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md'
          }
          bg-white dark:bg-gray-800
        `}
        whileHover={{ y: -2 }}
        onClick={() => {
          setSelectedGame(game.game_id);
          onGameSelect?.(game.game_id);
        }}
        layout
      >
        {/* Live Indicator */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <motion.div
              className="w-3 h-3 bg-red-500 rounded-full"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className="text-sm font-semibold text-red-600 dark:text-red-400">
              LIVE
            </span>
          </div>

          <div className="text-xs text-gray-500">
            {getQuarterDisplay(game.quarter)} • {game.time_remaining}
          </div>
        </div>

        {/* Score Display */}
        <div className="flex items-center justify-between mb-4">
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Away</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {game.away_score}
            </div>
          </div>

          <div className="text-center">
            <div className="text-xs text-gray-500">vs</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {game.down && `${game.down} & ${game.distance}`}
            </div>
          </div>

          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Home</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {game.home_score}
            </div>
          </div>
        </div>

        {/* Win Probability */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs mb-1">
            <span>Win Probability</span>
            <div className="flex items-center space-x-1">
              {winProbChange.significant && (
                <motion.div
                  className={`flex items-center ${
                    winProbChange.direction === 'up' ? 'text-green-500' : 'text-red-500'
                  }`}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                >
                  {winProbChange.direction === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  <span>{winProbChange.value.toFixed(1)}%</span>
                </motion.div>
              )}
            </div>
          </div>

          <div className="relative">
            <div className="flex h-6 rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700">
              <motion.div
                className="bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold"
                style={{ width: `${game.win_probability.away}%` }}
                initial={{ width: 0 }}
                animate={{ width: `${game.win_probability.away}%` }}
                transition={{ duration: 1 }}
              >
                {game.win_probability.away > 15 && `${game.win_probability.away.toFixed(0)}%`}
              </motion.div>
              <motion.div
                className="bg-gradient-to-r from-green-500 to-green-600 flex items-center justify-center text-white text-xs font-bold"
                style={{ width: `${game.win_probability.home}%` }}
                initial={{ width: 0 }}
                animate={{ width: `${game.win_probability.home}%` }}
                transition={{ duration: 1 }}
              >
                {game.win_probability.home > 15 && `${game.win_probability.home.toFixed(0)}%`}
              </motion.div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {game.updated_predictions.length}
            </div>
            <div className="text-xs text-gray-500">Live Predictions</div>
          </div>

          <div className="text-center">
            <div className={`text-lg font-bold ${getMomentumColor(game.momentum.strength)}`}>
              {Math.abs(game.momentum.strength)}
            </div>
            <div className="text-xs text-gray-500">Momentum</div>
          </div>

          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {(game.prediction_accuracy * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">Accuracy</div>
          </div>
        </div>

        {/* Recent Events */}
        {game.critical_events.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs text-gray-500 mb-1">Critical Events</div>
            {game.critical_events.slice(0, 2).map((event, index) => (
              <motion.div
                key={index}
                className="text-xs p-2 bg-gray-50 dark:bg-gray-700 rounded"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{event.event_type}</span>
                  <span className="text-gray-500">{event.time}</span>
                </div>
                <div className="text-gray-600 dark:text-gray-400">{event.description}</div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Scoring Probability */}
        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-xs text-gray-500 mb-2">Next Score Probability</div>
          <div className="flex items-center justify-between text-xs">
            <span>
              Home: {game.scoring_probability.next_score_home.toFixed(1)}%
            </span>
            <span className="capitalize text-gray-600 dark:text-gray-400">
              {game.scoring_probability.next_score_type}
            </span>
            <span>
              Away: {game.scoring_probability.next_score_away.toFixed(1)}%
            </span>
          </div>
        </div>
      </motion.div>
    );
  };

  const RealtimeUpdatesFeed = () => (
    <motion.div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-white">
          Live Updates
        </h3>
        <div className="flex items-center space-x-2">
          <motion.div
            className="w-2 h-2 bg-green-500 rounded-full"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className="text-xs text-green-600 dark:text-green-400">Live</span>
        </div>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        <AnimatePresence>
          {realtimeUpdates.map((update, index) => (
            <motion.div
              key={index}
              className="flex items-start space-x-3 p-2 bg-gray-50 dark:bg-gray-700 rounded"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
            >
              <div className={`
                w-2 h-2 rounded-full mt-2 flex-shrink-0
                ${update.severity === 'critical' ? 'bg-red-500' :
                  update.severity === 'high' ? 'bg-orange-500' :
                  update.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                }
              `} />
              <div className="flex-1 min-w-0">
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {new Date(update.timestamp).toLocaleTimeString()}
                </div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {update.type.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">
                  {JSON.stringify(update.data.event || update.data).replace(/"/g, '')}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {realtimeUpdates.length === 0 && (
        <div className="text-center py-4 text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Waiting for live updates...</p>
        </div>
      )}
    </motion.div>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Live Games Dashboard
          </h2>
          <p className="text-sm text-gray-500">
            Real-time predictions and game tracking • Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={`
              p-2 rounded-lg border transition-colors
              ${soundEnabled
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                : 'border-gray-200 dark:border-gray-700 text-gray-500'
              }
            `}
          >
            {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          <button
            onClick={() => setExpandedView(!expandedView)}
            className="p-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            {expandedView ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={() => setLastUpdated(new Date())}
            className="p-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Live Games Grid */}
      {enhancedGames.length > 0 ? (
        <div className={`
          grid gap-6
          ${expandedView
            ? 'grid-cols-1 lg:grid-cols-2'
            : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
          }
        `}>
          <AnimatePresence>
            {enhancedGames.map((game) => (
              <LiveGameCard key={game.game_id} game={game} />
            ))}
          </AnimatePresence>

          {/* Real-time Updates Panel */}
          {expandedView && (
            <div className="lg:col-span-2">
              <RealtimeUpdatesFeed />
            </div>
          )}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-2">
            No Live Games
          </h3>
          <p className="text-gray-500 mb-6">
            All games have concluded. Check back during game times for live updates.
          </p>
          <div className="text-sm text-gray-400">
            Next game starts in: 2 hours 34 minutes
          </div>
        </motion.div>
      )}

      {/* Real-time Updates (Non-expanded) */}
      {!expandedView && enhancedGames.length > 0 && (
        <RealtimeUpdatesFeed />
      )}
    </div>
  );
});

LiveGameDashboard.displayName = 'LiveGameDashboard';

export default LiveGameDashboard;