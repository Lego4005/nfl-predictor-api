import { useEffect, useRef, useState, useCallback } from 'react';
import type { 
  LiveUpdateMessage, 
  WebSocketConnectionState,
  ConsensusResult,
  ExpertPrediction 
} from '../types/aiCouncil';

interface UseWebSocketOptions {
  url?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  gameId?: string;
}

interface WebSocketHookReturn {
  connectionState: WebSocketConnectionState;
  sendMessage: (message: any) => void;
  lastMessage: LiveUpdateMessage | null;
  connect: () => void;
  disconnect: () => void;
  subscribe: (eventType: string, callback: (data: any) => void) => () => void;
}

const useWebSocket = (options: UseWebSocketOptions = {}): WebSocketHookReturn => {
  const {
    url = process.env.REACT_APP_WS_URL || 'ws://localhost:8080',
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    gameId
  } = options;

  const [connectionState, setConnectionState] = useState<WebSocketConnectionState>({
    connected: false,
    lastHeartbeat: new Date().toISOString(),
    reconnectAttempts: 0,
    latency: 0
  });

  const [lastMessage, setLastMessage] = useState<LiveUpdateMessage | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const heartbeatTimer = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const subscribers = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const pingTime = useRef<number>(0);

  const cleanup = useCallback(() => {
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
  }, []);

  const sendHeartbeat = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      pingTime.current = Date.now();
      ws.current.send(JSON.stringify({
        type: 'ping',
        timestamp: new Date().toISOString(),
        gameId
      }));
    }
  }, [gameId]);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);

      // Handle pong responses for latency calculation
      if (message.type === 'pong') {
        const latency = Date.now() - pingTime.current;
        setConnectionState(prev => ({
          ...prev,
          latency,
          lastHeartbeat: new Date().toISOString()
        }));
        return;
      }

      // Handle live update messages
      if (message.type && message.data) {
        const liveUpdate: LiveUpdateMessage = {
          type: message.type,
          gameId: message.gameId || gameId || '',
          data: message.data,
          timestamp: message.timestamp || new Date().toISOString(),
          affectedCategories: message.affectedCategories || [],
          priority: message.priority || 'medium'
        };

        setLastMessage(liveUpdate);

        // Notify subscribers
        const eventSubscribers = subscribers.current.get(message.type);
        if (eventSubscribers) {
          eventSubscribers.forEach(callback => callback(message.data));
        }

        // Also notify 'all' subscribers
        const allSubscribers = subscribers.current.get('all');
        if (allSubscribers) {
          allSubscribers.forEach(callback => callback(liveUpdate));
        }
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, [gameId]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setConnectionState(prev => ({
          ...prev,
          connected: true,
          reconnectAttempts: 0
        }));

        // Start heartbeat
        heartbeatTimer.current = setInterval(sendHeartbeat, heartbeatInterval);

        // Subscribe to game updates if gameId provided
        if (gameId) {
          ws.current?.send(JSON.stringify({
            type: 'subscribe',
            gameId,
            timestamp: new Date().toISOString()
          }));
        }
      };

      ws.current.onmessage = handleMessage;

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionState(prev => ({
          ...prev,
          connected: false
        }));

        cleanup();

        // Auto-reconnect if enabled and not a normal close
        if (autoReconnect && event.code !== 1000) {
          setConnectionState(prev => {
            const newAttempts = prev.reconnectAttempts + 1;
            
            if (newAttempts <= maxReconnectAttempts) {
              console.log(`Attempting to reconnect (${newAttempts}/${maxReconnectAttempts})...`);
              
              reconnectTimer.current = setTimeout(() => {
                connect();
              }, reconnectInterval);
              
              return {
                ...prev,
                reconnectAttempts: newAttempts
              };
            } else {
              console.log('Max reconnection attempts reached');
              return prev;
            }
          });
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }, [url, autoReconnect, maxReconnectAttempts, reconnectInterval, heartbeatInterval, gameId, sendHeartbeat, handleMessage, cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }
    setConnectionState(prev => ({
      ...prev,
      connected: false,
      reconnectAttempts: 0
    }));
  }, [cleanup]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        ...message,
        timestamp: new Date().toISOString(),
        gameId: message.gameId || gameId
      }));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, [gameId]);

  const subscribe = useCallback((eventType: string, callback: (data: any) => void): (() => void) => {
    if (!subscribers.current.has(eventType)) {
      subscribers.current.set(eventType, new Set());
    }
    
    const eventSubscribers = subscribers.current.get(eventType)!;
    eventSubscribers.add(callback);

    // Return unsubscribe function
    return () => {
      eventSubscribers.delete(callback);
      if (eventSubscribers.size === 0) {
        subscribers.current.delete(eventType);
      }
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [cleanup]);

  return {
    connectionState,
    sendMessage,
    lastMessage,
    connect,
    disconnect,
    subscribe
  };
};

export default useWebSocket;

// Specialized hooks for prediction updates
export const usePredictionUpdates = (gameIds?: string[]) => {
  const [predictions, setPredictions] = useState<ComprehensivePrediction[]>([]);
  const [liveGames, setLiveGames] = useState<LiveGameData[]>([]);
  const [realtimeUpdates, setRealtimeUpdates] = useState<RealtimeUpdate[]>([]);

  const websocket = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
    onConnect: () => {
      console.log('Connected to prediction updates');
    },
    onDisconnect: () => {
      console.log('Disconnected from prediction updates');
    }
  });

  // Subscribe to prediction updates
  useEffect(() => {
    const unsubscribePredictions = websocket.subscribe('prediction_update', (data: ComprehensivePrediction) => {
      setPredictions(prev => {
        const index = prev.findIndex(p => p.id === data.id);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = data;
          return updated;
        }
        return [...prev, data];
      });

      // Add to realtime updates
      setRealtimeUpdates(prev => [{
        type: 'prediction_update',
        timestamp: new Date().toISOString(),
        data,
        affected_predictions: [data.id],
        severity: 'medium'
      }, ...prev.slice(0, 49)]); // Keep last 50 updates
    });

    const unsubscribeGameState = websocket.subscribe('game_state', (data: LiveGameData) => {
      setLiveGames(prev => {
        const index = prev.findIndex(g => g.game_id === data.game_id);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = data;
          return updated;
        }
        return [...prev, data];
      });

      // Add to realtime updates
      setRealtimeUpdates(prev => [{
        type: 'game_event',
        timestamp: new Date().toISOString(),
        data,
        affected_predictions: [],
        severity: 'high'
      }, ...prev.slice(0, 49)]);
    });

    const unsubscribeExpertPerformance = websocket.subscribe('expert_performance', (data: any) => {
      setRealtimeUpdates(prev => [{
        type: 'expert_update',
        timestamp: new Date().toISOString(),
        data,
        affected_predictions: [],
        severity: 'low'
      }, ...prev.slice(0, 49)]);
    });

    return () => {
      unsubscribePredictions();
      unsubscribeGameState();
      unsubscribeExpertPerformance();
    };
  }, [websocket]);

  // Subscribe to specific games if provided
  useEffect(() => {
    if (gameIds && gameIds.length > 0 && websocket.isConnected) {
      websocket.sendMessage({
        type: 'subscribe_games',
        game_ids: gameIds
      });
    }
  }, [gameIds, websocket.isConnected, websocket.sendMessage]);

  return {
    predictions,
    liveGames,
    realtimeUpdates,
    isConnected: websocket.isConnected,
    isConnecting: websocket.isConnecting,
    error: websocket.error,
    subscribe: websocket.subscribe,
    sendMessage: websocket.sendMessage
  };
};

// Hook for live game tracking
export const useLiveGameTracking = (gameId: string) => {
  const [gameData, setGameData] = useState<LiveGameData | null>(null);
  const [predictions, setPredictions] = useState<ComprehensivePrediction[]>([]);

  const websocket = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
  });

  useEffect(() => {
    if (!websocket.isConnected) return;

    // Subscribe to specific game
    websocket.sendMessage({
      type: 'subscribe_game',
      game_id: gameId
    });

    const unsubscribeGame = websocket.subscribe('game_state', (data: LiveGameData) => {
      if (data.game_id === gameId) {
        setGameData(data);
      }
    });

    const unsubscribePredictions = websocket.subscribe('prediction_update', (data: ComprehensivePrediction) => {
      if (data.game_id === gameId) {
        setPredictions(prev => {
          const index = prev.findIndex(p => p.id === data.id);
          if (index >= 0) {
            const updated = [...prev];
            updated[index] = data;
            return updated;
          }
          return [...prev, data];
        });
      }
    });

    return () => {
      unsubscribeGame();
      unsubscribePredictions();

      // Unsubscribe from game
      websocket.sendMessage({
        type: 'unsubscribe_game',
        game_id: gameId
      });
    };
  }, [gameId, websocket.isConnected, websocket.sendMessage, websocket.subscribe]);

  return {
    gameData,
    predictions,
    isConnected: websocket.isConnected,
    sendMessage: websocket.sendMessage
  };
};