import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, RealtimeUpdate, ComprehensivePrediction, LiveGameData } from '../types/predictions';

interface WebSocketOptions {
  url: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: WebSocketMessage | null;
  connectionAttempts: number;
  error: string | null;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connectionAttempts: number;
  sendMessage: (message: any) => void;
  disconnect: () => void;
  reconnect: () => void;
  subscribe: (event: string, callback: (data: any) => void) => () => void;
  unsubscribe: (event: string) => void;
}

export const useWebSocket = (options: WebSocketOptions): UseWebSocketReturn => {
  const {
    url,
    reconnectAttempts = 5,
    reconnectDelay = 5000,
    heartbeatInterval = 30000,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    connectionAttempts: 0,
    error: null
  });

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimer = useRef<NodeJS.Timeout | null>(null);
  const subscribers = useRef<Map<string, Set<(data: any) => void>>>(new Map());

  const clearTimers = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
    }

    heartbeatTimer.current = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN || state.isConnecting) {
      return;
    }

    setState(prev => ({
      ...prev,
      isConnecting: true,
      error: null
    }));

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          connectionAttempts: 0,
          error: null
        }));

        startHeartbeat();
        onConnect?.();

        console.log('WebSocket connected');
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          setState(prev => ({
            ...prev,
            lastMessage: message
          }));

          // Handle heartbeat response
          if (message.event === 'pong') {
            return;
          }

          // Notify subscribers
          const eventSubscribers = subscribers.current.get(message.event);
          if (eventSubscribers) {
            eventSubscribers.forEach(callback => callback(message.data));
          }

          // Notify all subscribers
          const allSubscribers = subscribers.current.get('*');
          if (allSubscribers) {
            allSubscribers.forEach(callback => callback(message));
          }

        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false
        }));

        clearTimers();
        onDisconnect?.();

        console.log('WebSocket disconnected:', event.code, event.reason);

        // Attempt to reconnect if enabled and not a manual close
        if (autoReconnect && event.code !== 1000 && state.connectionAttempts < reconnectAttempts) {
          setState(prev => ({
            ...prev,
            connectionAttempts: prev.connectionAttempts + 1
          }));

          const delay = reconnectDelay * Math.pow(1.5, state.connectionAttempts);
          console.log(`Reconnecting in ${delay}ms (attempt ${state.connectionAttempts + 1}/${reconnectAttempts})`);

          reconnectTimer.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (state.connectionAttempts >= reconnectAttempts) {
          setState(prev => ({
            ...prev,
            error: 'Max reconnection attempts reached'
          }));
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);

        setState(prev => ({
          ...prev,
          error: 'Connection error occurred',
          isConnecting: false
        }));

        onError?.(error);
      };

    } catch (error) {
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: 'Failed to create WebSocket connection'
      }));
      console.error('Failed to create WebSocket:', error);
    }
  }, [url, state.isConnecting, state.connectionAttempts, reconnectAttempts, reconnectDelay, autoReconnect, onConnect, onDisconnect, onError, startHeartbeat, clearTimers]);

  const disconnect = useCallback(() => {
    clearTimers();

    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      connectionAttempts: 0,
      error: null
    }));
  }, [clearTimers]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    if (!subscribers.current.has(event)) {
      subscribers.current.set(event, new Set());
    }

    subscribers.current.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      const eventSubscribers = subscribers.current.get(event);
      if (eventSubscribers) {
        eventSubscribers.delete(callback);
        if (eventSubscribers.size === 0) {
          subscribers.current.delete(event);
        }
      }
    };
  }, []);

  const unsubscribe = useCallback((event: string) => {
    subscribers.current.delete(event);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    setState(prev => ({ ...prev, connectionAttempts: 0 }));
    setTimeout(connect, 1000);
  }, [disconnect, connect]);

  // Initial connection
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [url]); // Only reconnect when URL changes

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimers();
      if (ws.current) {
        ws.current.close(1000, 'Component unmount');
      }
    };
  }, [clearTimers]);

  return {
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    error: state.error,
    connectionAttempts: state.connectionAttempts,
    sendMessage,
    disconnect,
    reconnect,
    subscribe,
    unsubscribe
  };
};

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