/**
 * Mobile-Optimized Live Game Experience
 * Touch-first interactions with swipe gestures, performance optimization, and immersive design
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence, PanInfo, useMotionValue, useTransform } from 'framer-motion';
import {
  useWebSocket,
  WebSocketEventType,
  GameUpdate,
  PredictionUpdate,
  OddsUpdate
} from '../services/websocketService';
import { useSwipeGestures } from '../hooks/useSwipeGestures';
import { usePerformanceMonitor } from '../hooks/usePerformanceMonitor';
import TouchOptimizedButton from './TouchOptimizedButton';
import ProgressiveFieldVisualizer from './ProgressiveFieldVisualizer';
import MobileStatsLayer from './MobileStatsLayer';
import SwipeIndicator from './SwipeIndicator';

interface MobileLiveGameExperienceProps {
  gameId?: string;
  className?: string;
}

interface GameData {
  gameUpdate?: GameUpdate;
  prediction?: PredictionUpdate;
  odds?: OddsUpdate[];
}

interface StatsLayer {
  id: string;
  title: string;
  icon: string;
  component: React.ComponentType<{ data: GameData; gameId: string }>;
}

const MobileLiveGameExperience: React.FC<MobileLiveGameExperienceProps> = ({
  gameId,
  className = ''
}) => {
  const { isConnected, subscribe, unsubscribe, on, off } = useWebSocket({ autoConnect: true });
  const [gameData, setGameData] = useState<Map<string, GameData>>(new Map());
  const [activeGameId, setActiveGameId] = useState<string | null>(null);
  const [currentLayer, setCurrentLayer] = useState<number>(0);
  const [isLayerVisible, setIsLayerVisible] = useState(false);
  const [notifications, setNotifications] = useState<string[]>([]);

  const containerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // Performance monitoring
  const { startTracking, stopTracking, getMetrics } = usePerformanceMonitor();

  // Motion values for smooth animations
  const x = useMotionValue(0);
  const layerOpacity = useTransform(x, [-100, 0, 100], [0.3, 1, 0.3]);
  const layerScale = useTransform(x, [-100, 0, 100], [0.95, 1, 0.95]);

  // Stats layers configuration
  const statsLayers: StatsLayer[] = useMemo(() => [
    {
      id: 'overview',
      title: 'Game Overview',
      icon: '🏈',
      component: ({ data, gameId }) => (
        <div className="space-y-4">
          {data.gameUpdate && (
            <div className="game-score-mobile">
              <div className="scoreboard-mobile bg-gradient-to-r from-blue-900 to-green-900 p-6 rounded-xl text-white">
                <div className="flex justify-between items-center mb-4">
                  <div className="text-center flex-1">
                    <div className="text-lg font-bold">{data.gameUpdate.away_team}</div>
                    <div className="text-3xl font-black">{data.gameUpdate.away_score}</div>
                  </div>
                  <div className="text-center px-4">
                    <div className="text-sm opacity-75">VS</div>
                    <div className="text-xs">{data.gameUpdate.quarter ? `Q${data.gameUpdate.quarter}` : ''}</div>
                  </div>
                  <div className="text-center flex-1">
                    <div className="text-lg font-bold">{data.gameUpdate.home_team}</div>
                    <div className="text-3xl font-black">{data.gameUpdate.home_score}</div>
                  </div>
                </div>
                <div className="text-center text-sm opacity-90">
                  {data.gameUpdate.game_status.toUpperCase()}
                  {data.gameUpdate.time_remaining && ` • ${data.gameUpdate.time_remaining}`}
                </div>
              </div>
            </div>
          )}
        </div>
      )
    },
    {
      id: 'predictions',
      title: 'AI Predictions',
      icon: '🤖',
      component: ({ data }) => (
        <MobileStatsLayer
          type="predictions"
          data={data.prediction}
          title="AI Win Probability"
        />
      )
    },
    {
      id: 'odds',
      title: 'Live Odds',
      icon: '💰',
      component: ({ data }) => (
        <MobileStatsLayer
          type="odds"
          data={data.odds}
          title="Sportsbook Odds"
        />
      )
    },
    {
      id: 'field',
      title: 'Field View',
      icon: '📍',
      component: ({ data, gameId }) => (
        <ProgressiveFieldVisualizer
          gameData={data.gameUpdate}
          gameId={gameId}
          mobileOptimized={true}
        />
      )
    }
  ], []);

  // Swipe gesture handlers
  const { swipeHandlers } = useSwipeGestures({
    onSwipeLeft: () => {
      if (currentLayer < statsLayers.length - 1) {
        setCurrentLayer(prev => prev + 1);
      }
    },
    onSwipeRight: () => {
      if (currentLayer > 0) {
        setCurrentLayer(prev => prev - 1);
      }
    },
    onSwipeUp: () => {
      setIsLayerVisible(true);
    },
    onSwipeDown: () => {
      setIsLayerVisible(false);
    },
    threshold: 50,
    velocity: 0.3
  });

  // Handle game updates
  const handleGameUpdate = useCallback((data: GameUpdate) => {
    startTracking('game_update');

    setGameData(prev => {
      const newData = new Map(prev);
      const gameInfo = newData.get(data.game_id) || {};
      gameInfo.gameUpdate = data;
      newData.set(data.game_id, gameInfo);

      // Set active game if not set
      if (!activeGameId && data.game_status.toLowerCase() === 'live') {
        setActiveGameId(data.game_id);
      }

      return newData;
    });

    // Add haptic feedback for score changes
    if ('vibrate' in navigator && data.home_score !== data.away_score) {
      navigator.vibrate([50, 100, 50]);
    }

    // Add notification for significant events
    if (data.game_status === 'FINAL') {
      setNotifications(prev => [...prev.slice(-2), `🏁 ${data.home_team} vs ${data.away_team} Final!`]);
    } else if (data.home_score !== data.away_score) {
      setNotifications(prev => [...prev.slice(-2), `🏈 ${data.home_team} ${data.home_score} - ${data.away_score} ${data.away_team}`]);
    }

    stopTracking('game_update');
  }, [activeGameId, startTracking, stopTracking]);

  // Handle prediction updates
  const handlePredictionUpdate = useCallback((data: PredictionUpdate) => {
    setGameData(prev => {
      const newData = new Map(prev);
      const gameInfo = newData.get(data.game_id) || {};
      gameInfo.prediction = data;
      newData.set(data.game_id, gameInfo);
      return newData;
    });
  }, []);

  // Handle odds updates
  const handleOddsUpdate = useCallback((data: OddsUpdate) => {
    setGameData(prev => {
      const newData = new Map(prev);
      const gameInfo = newData.get(data.game_id) || {};
      if (!gameInfo.odds) gameInfo.odds = [];

      const existingIndex = gameInfo.odds.findIndex(odds => odds.sportsbook === data.sportsbook);
      if (existingIndex >= 0) {
        gameInfo.odds[existingIndex] = data;
      } else {
        gameInfo.odds.push(data);
      }

      newData.set(data.game_id, gameInfo);
      return newData;
    });
  }, []);

  // Set up WebSocket subscriptions
  useEffect(() => {
    if (!isConnected) return;

    if (gameId) {
      subscribe(`game_${gameId}`);
      subscribe(`predictions_${gameId}`);
      subscribe(`odds_${gameId}`);
      setActiveGameId(gameId);
    } else {
      subscribe('games');
      subscribe('predictions');
      subscribe('odds');
    }

    on<GameUpdate>(WebSocketEventType.GAME_UPDATE, handleGameUpdate);
    on<GameUpdate>(WebSocketEventType.SCORE_UPDATE, handleGameUpdate);
    on<PredictionUpdate>(WebSocketEventType.PREDICTION_UPDATE, handlePredictionUpdate);
    on<OddsUpdate>(WebSocketEventType.ODDS_UPDATE, handleOddsUpdate);

    return () => {
      if (gameId) {
        unsubscribe(`game_${gameId}`);
        unsubscribe(`predictions_${gameId}`);
        unsubscribe(`odds_${gameId}`);
      } else {
        unsubscribe('games');
        unsubscribe('predictions');
        unsubscribe('odds');
      }

      off<GameUpdate>(WebSocketEventType.GAME_UPDATE, handleGameUpdate);
      off<GameUpdate>(WebSocketEventType.SCORE_UPDATE, handleGameUpdate);
      off<PredictionUpdate>(WebSocketEventType.PREDICTION_UPDATE, handlePredictionUpdate);
      off<OddsUpdate>(WebSocketEventType.ODDS_UPDATE, handleOddsUpdate);
    };
  }, [isConnected, gameId, subscribe, unsubscribe, on, off, handleGameUpdate, handlePredictionUpdate, handleOddsUpdate]);

  // Auto-select most interesting game
  useEffect(() => {
    if (!activeGameId && gameData.size > 0) {
      const liveGames = Array.from(gameData.entries())
        .filter(([_, data]) => data.gameUpdate?.game_status.toLowerCase() === 'live')
        .sort(([_, a], [__, b]) => {
          const aScore = (a.gameUpdate?.home_score || 0) + (a.gameUpdate?.away_score || 0);
          const bScore = (b.gameUpdate?.home_score || 0) + (b.gameUpdate?.away_score || 0);
          return bScore - aScore; // Prefer higher scoring games
        });

      if (liveGames.length > 0) {
        setActiveGameId(liveGames[0][0]);
      } else {
        // Fallback to first available game
        setActiveGameId(Array.from(gameData.keys())[0]);
      }
    }
  }, [gameData, activeGameId]);

  const activeGame = activeGameId ? gameData.get(activeGameId) : null;

  if (!isConnected) {
    return (
      <div className={`mobile-live-game-disconnected ${className} min-h-screen flex items-center justify-center bg-gray-900 text-white`}>
        <div className="text-center p-8">
          <div className="text-6xl mb-4">📡</div>
          <div className="text-xl mb-2">Connecting to live games...</div>
          <div className="text-sm text-gray-400">Preparing your NFL experience</div>
          <div className="mt-6">
            <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`mobile-live-game-experience ${className} min-h-screen bg-gray-900 text-white relative overflow-hidden`}
      {...swipeHandlers}
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-gray-900 to-green-900 opacity-50" />

      {/* Notifications */}
      <AnimatePresence>
        {notifications.length > 0 && (
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            className="absolute top-4 left-4 right-4 z-50"
          >
            {notifications.slice(-1).map((notification, index) => (
              <div key={index} className="bg-black bg-opacity-80 text-white p-3 rounded-lg backdrop-blur-sm">
                {notification}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Game selector for multiple games */}
      {gameData.size > 1 && (
        <div className="absolute top-16 left-0 right-0 z-40">
          <div className="flex overflow-x-auto scrollbar-hide px-4 space-x-2">
            {Array.from(gameData.entries()).map(([gId, data]) => (
              <TouchOptimizedButton
                key={gId}
                onClick={() => setActiveGameId(gId)}
                className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  activeGameId === gId
                    ? 'bg-white text-gray-900'
                    : 'bg-black bg-opacity-50 text-white'
                }`}
              >
                {data.gameUpdate ? `${data.gameUpdate.away_team} @ ${data.gameUpdate.home_team}` : `Game ${gId.slice(-4)}`}
              </TouchOptimizedButton>
            ))}
          </div>
        </div>
      )}

      {/* Main game card */}
      {activeGame ? (
        <motion.div
          ref={cardRef}
          className="relative z-30 pt-32 pb-24 px-4"
          style={{ x, opacity: layerOpacity, scale: layerScale }}
          drag="x"
          dragConstraints={{ left: -100, right: 100 }}
          dragElastic={0.2}
          onDragEnd={(_, info: PanInfo) => {
            if (Math.abs(info.offset.x) > 100) {
              if (info.offset.x > 0 && currentLayer > 0) {
                setCurrentLayer(prev => prev - 1);
              } else if (info.offset.x < 0 && currentLayer < statsLayers.length - 1) {
                setCurrentLayer(prev => prev + 1);
              }
            }
            x.set(0);
          }}
        >
          {/* Current layer content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentLayer}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="bg-black bg-opacity-60 backdrop-blur-lg rounded-2xl p-6 border border-white border-opacity-20"
            >
              {React.createElement(statsLayers[currentLayer].component, {
                data: activeGame,
                gameId: activeGameId!
              })}
            </motion.div>
          </AnimatePresence>

          {/* Swipe indicators */}
          <div className="flex justify-center items-center mt-6 space-x-4">
            <SwipeIndicator direction="left" visible={currentLayer > 0} />
            <div className="flex space-x-1">
              {statsLayers.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentLayer ? 'bg-white' : 'bg-white bg-opacity-30'
                  }`}
                />
              ))}
            </div>
            <SwipeIndicator direction="right" visible={currentLayer < statsLayers.length - 1} />
          </div>
        </motion.div>
      ) : (
        <div className="relative z-30 pt-32 pb-24 px-4">
          <div className="bg-black bg-opacity-60 backdrop-blur-lg rounded-2xl p-8 text-center border border-white border-opacity-20">
            <div className="text-6xl mb-4">🏈</div>
            <div className="text-xl mb-2">Waiting for live games...</div>
            <div className="text-sm text-gray-400">Games will appear here when they start</div>
          </div>
        </div>
      )}

      {/* Bottom navigation */}
      <div className="absolute bottom-0 left-0 right-0 z-40 bg-black bg-opacity-80 backdrop-blur-sm">
        <div className="flex justify-around py-4">
          {statsLayers.map((layer, index) => (
            <TouchOptimizedButton
              key={layer.id}
              onClick={() => setCurrentLayer(index)}
              className={`flex flex-col items-center space-y-1 px-4 py-2 rounded-lg transition-all ${
                currentLayer === index
                  ? 'bg-white bg-opacity-20 text-white'
                  : 'text-gray-400'
              }`}
            >
              <span className="text-lg">{layer.icon}</span>
              <span className="text-xs font-medium">{layer.title}</span>
            </TouchOptimizedButton>
          ))}
        </div>

        {/* Performance indicator */}
        <div className="text-center pb-2">
          <div className="text-xs text-gray-500">
            FPS: {Math.round(1000 / (getMetrics().averageFrameTime || 16))} •
            {isConnected ? ' 🟢 Live' : ' 🔴 Offline'}
          </div>
        </div>
      </div>

      {/* Gesture hints */}
      <motion.div
        initial={{ opacity: 1 }}
        animate={{ opacity: 0 }}
        transition={{ delay: 3, duration: 1 }}
        className="absolute bottom-24 left-4 right-4 z-30 text-center"
      >
        <div className="bg-black bg-opacity-50 text-white text-sm py-2 px-4 rounded-lg backdrop-blur-sm">
          ← Swipe to explore stats layers →
        </div>
      </motion.div>
    </div>
  );
};

export default MobileLiveGameExperience;