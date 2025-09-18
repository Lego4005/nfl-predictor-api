/**
 * Live Game Updates Component
 * Displays real-time game scores and updates via WebSocket
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  useWebSocket,
  WebSocketEventType,
  GameUpdate,
  PredictionUpdate,
  OddsUpdate
} from '../services/websocketService';

interface LiveGameUpdatesProps {
  gameId?: string;
  showPredictions?: boolean;
  showOdds?: boolean;
  className?: string;
}

interface GameData {
  gameUpdate?: GameUpdate;
  prediction?: PredictionUpdate;
  odds?: OddsUpdate[];
}

const LiveGameUpdates: React.FC<LiveGameUpdatesProps> = ({
  gameId,
  showPredictions = true,
  showOdds = true,
  className = ''
}) => {
  const { isConnected, subscribe, unsubscribe, on, off } = useWebSocket({ autoConnect: true });
  const [gameData, setGameData] = useState<Map<string, GameData>>(new Map());
  const [notifications, setNotifications] = useState<string[]>([]);

  // Handle game updates
  const handleGameUpdate = useCallback((data: GameUpdate) => {
    setGameData(prev => {
      const newData = new Map(prev);
      const gameInfo = newData.get(data.game_id) || {};
      gameInfo.gameUpdate = data;
      newData.set(data.game_id, gameInfo);
      return newData;
    });

    // Add notification for significant events
    if (data.game_status === 'FINAL') {
      setNotifications(prev => [...prev.slice(-4), `Game ${data.home_team} vs ${data.away_team} has ended!`]);
    } else if (data.home_score !== data.away_score) {
      setNotifications(prev => [...prev.slice(-4), `Score update: ${data.home_team} ${data.home_score} - ${data.away_score} ${data.away_team}`]);
    }
  }, []);

  // Handle prediction updates
  const handlePredictionUpdate = useCallback((data: PredictionUpdate) => {
    if (!showPredictions) return;

    setGameData(prev => {
      const newData = new Map(prev);
      const gameInfo = newData.get(data.game_id) || {};
      gameInfo.prediction = data;
      newData.set(data.game_id, gameInfo);
      return newData;
    });
  }, [showPredictions]);

  // Handle odds updates
  const handleOddsUpdate = useCallback((data: OddsUpdate) => {
    if (!showOdds) return;

    setGameData(prev => {
      const newData = new Map(prev);
      const gameInfo = newData.get(data.game_id) || {};
      if (!gameInfo.odds) gameInfo.odds = [];

      // Update or add odds for this sportsbook
      const existingIndex = gameInfo.odds.findIndex(odds => odds.sportsbook === data.sportsbook);
      if (existingIndex >= 0) {
        gameInfo.odds[existingIndex] = data;
      } else {
        gameInfo.odds.push(data);
      }

      newData.set(data.game_id, gameInfo);
      return newData;
    });
  }, [showOdds]);

  // Handle system notifications
  const handleNotification = useCallback((data: { message: string; level: string }) => {
    setNotifications(prev => [...prev.slice(-4), `[${data.level.toUpperCase()}] ${data.message}`]);
  }, []);

  // Set up WebSocket subscriptions and handlers
  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to channels
    if (gameId) {
      subscribe(`game_${gameId}`);
      subscribe(`predictions_${gameId}`);
      subscribe(`odds_${gameId}`);
    } else {
      subscribe('games');
      if (showPredictions) subscribe('predictions');
      if (showOdds) subscribe('odds');
    }

    // Set up event handlers
    on<GameUpdate>(WebSocketEventType.GAME_UPDATE, handleGameUpdate);
    on<GameUpdate>(WebSocketEventType.SCORE_UPDATE, handleGameUpdate);
    on<PredictionUpdate>(WebSocketEventType.PREDICTION_UPDATE, handlePredictionUpdate);
    on<OddsUpdate>(WebSocketEventType.ODDS_UPDATE, handleOddsUpdate);
    on(WebSocketEventType.NOTIFICATION, handleNotification);

    return () => {
      // Clean up subscriptions and handlers
      if (gameId) {
        unsubscribe(`game_${gameId}`);
        unsubscribe(`predictions_${gameId}`);
        unsubscribe(`odds_${gameId}`);
      } else {
        unsubscribe('games');
        if (showPredictions) unsubscribe('predictions');
        if (showOdds) unsubscribe('odds');
      }

      off<GameUpdate>(WebSocketEventType.GAME_UPDATE, handleGameUpdate);
      off<GameUpdate>(WebSocketEventType.SCORE_UPDATE, handleGameUpdate);
      off<PredictionUpdate>(WebSocketEventType.PREDICTION_UPDATE, handlePredictionUpdate);
      off<OddsUpdate>(WebSocketEventType.ODDS_UPDATE, handleOddsUpdate);
      off(WebSocketEventType.NOTIFICATION, handleNotification);
    };
  }, [isConnected, gameId, showPredictions, showOdds, subscribe, unsubscribe, on, off, handleGameUpdate, handlePredictionUpdate, handleOddsUpdate, handleNotification]);

  const formatTime = (timeString: string) => {
    try {
      const date = new Date(timeString);
      return date.toLocaleTimeString();
    } catch {
      return timeString;
    }
  };

  const getQuarterText = (quarter: number) => {
    const quarters = ['1st', '2nd', '3rd', '4th'];
    return quarter <= 4 ? quarters[quarter - 1] : `OT${quarter - 4}`;
  };

  const getGameStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'live':
      case 'in_progress':
        return 'text-red-500';
      case 'final':
        return 'text-gray-600';
      case 'scheduled':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  if (!isConnected) {
    return (
      <div className={`live-updates-disconnected ${className}`}>
        <div className="text-center py-8">
          <div className="text-gray-500 mb-2">🔌 Not connected to live updates</div>
          <div className="text-sm text-gray-400">Reconnecting...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`live-game-updates ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Live Game Updates</h3>
        <div className="flex items-center text-sm text-green-600">
          <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
          Live
        </div>
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="notifications mb-4">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-3 mb-3">
            <h4 className="text-sm font-semibold text-blue-800 mb-1">Recent Updates</h4>
            {notifications.slice(-3).map((notification, index) => (
              <div key={index} className="text-sm text-blue-700 mb-1">
                {notification}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Game Data */}
      {gameData.size === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="mb-2">📺 Waiting for game updates...</div>
          <div className="text-sm">Live scores will appear here when games are in progress</div>
        </div>
      ) : (
        <div className="space-y-4">
          {Array.from(gameData.entries()).map(([gameId, data]) => (
            <div key={gameId} className="game-card bg-white border rounded-lg p-4 shadow-sm">
              {/* Game Score */}
              {data.gameUpdate && (
                <div className="game-score mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <div className={`font-semibold ${getGameStatusColor(data.gameUpdate.game_status)}`}>
                      {data.gameUpdate.game_status.toUpperCase()}
                      {data.gameUpdate.game_status.toLowerCase() === 'live' && data.gameUpdate.quarter && (
                        <span className="ml-2 text-sm">
                          {getQuarterText(data.gameUpdate.quarter)} - {data.gameUpdate.time_remaining}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      Updated: {formatTime(data.gameUpdate.updated_at)}
                    </div>
                  </div>

                  <div className="scoreboard flex justify-between items-center bg-gray-50 p-3 rounded">
                    <div className="team flex-1">
                      <div className="font-semibold">{data.gameUpdate.home_team}</div>
                      <div className="text-2xl font-bold">{data.gameUpdate.home_score}</div>
                    </div>
                    <div className="vs text-gray-500 text-sm font-semibold">VS</div>
                    <div className="team flex-1 text-right">
                      <div className="font-semibold">{data.gameUpdate.away_team}</div>
                      <div className="text-2xl font-bold">{data.gameUpdate.away_score}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Predictions */}
              {data.prediction && showPredictions && (
                <div className="predictions mb-4 p-3 bg-blue-50 rounded">
                  <h5 className="font-semibold text-blue-800 mb-2">AI Prediction</h5>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Win Probability</div>
                      <div className="font-semibold">
                        {data.prediction.home_team}: {(data.prediction.home_win_probability * 100).toFixed(1)}%
                      </div>
                      <div className="font-semibold">
                        {data.prediction.away_team}: {(data.prediction.away_win_probability * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Predicted Spread</div>
                      <div className="font-semibold">{data.prediction.predicted_spread > 0 ? '+' : ''}{data.prediction.predicted_spread}</div>
                      <div className="text-xs text-gray-500">
                        Confidence: {(data.prediction.confidence_level * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Odds */}
              {data.odds && showOdds && data.odds.length > 0 && (
                <div className="odds">
                  <h5 className="font-semibold text-green-800 mb-2">Live Odds</h5>
                  <div className="space-y-2">
                    {data.odds.map((odds, index) => (
                      <div key={index} className="odds-row p-2 bg-green-50 rounded text-sm">
                        <div className="flex justify-between items-center">
                          <div className="font-semibold text-green-800">{odds.sportsbook}</div>
                          <div className="text-xs text-gray-500">
                            Updated: {formatTime(odds.updated_at)}
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-1">
                          <div>
                            <div className="text-xs text-gray-600">Spread</div>
                            <div className="font-semibold">{odds.spread > 0 ? '+' : ''}{odds.spread}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-600">Moneyline</div>
                            <div className="font-semibold">
                              {odds.moneyline_home > 0 ? '+' : ''}{odds.moneyline_home} / {odds.moneyline_away > 0 ? '+' : ''}{odds.moneyline_away}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-600">O/U</div>
                            <div className="font-semibold">{odds.over_under}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LiveGameUpdates;