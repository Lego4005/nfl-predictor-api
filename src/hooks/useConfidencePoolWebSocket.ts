/**
 * useConfidencePoolWebSocket Hook
 * Enhanced WebSocket hook specifically for Confidence Pool real-time events
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type {
  WebSocketEvent,
  BetPlacedEvent,
  BetSettledEvent,
  ExpertEliminatedEvent,
  LineMovementEvent,
  BankrollUpdateEvent
} from '../types/confidencePool';

interface UseConfidencePoolWebSocketOptions {
  url?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  onBetPlaced?: (event: BetPlacedEvent) => void;
  onBetSettled?: (event: BetSettledEvent) => void;
  onExpertEliminated?: (event: ExpertEliminatedEvent) => void;
  onLineMovement?: (event: LineMovementEvent) => void;
  onBankrollUpdate?: (event: BankrollUpdateEvent) => void;
}

interface ConnectionState {
  connected: boolean;
  reconnectAttempts: number;
  lastHeartbeat: string;
  latency: number;
}

/**
 * Enhanced WebSocket hook for Confidence Pool real-time updates
 */
export const useConfidencePoolWebSocket = (
  options: UseConfidencePoolWebSocketOptions = {}
) => {
  const {
    url = process.env.VITE_WS_URL || 'ws://localhost:8000/ws/updates',
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onBetPlaced,
    onBetSettled,
    onExpertEliminated,
    onLineMovement,
    onBankrollUpdate
  } = options;

  const queryClient = useQueryClient();
  const ws = useRef<WebSocket | null>(null);
  const heartbeatTimer = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const pingTime = useRef<number>(0);

  const [connectionState, setConnectionState] = useState<ConnectionState>({
    connected: false,
    reconnectAttempts: 0,
    lastHeartbeat: new Date().toISOString(),
    latency: 0
  });

  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);

  // Cleanup function
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

  // Send heartbeat
  const sendHeartbeat = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      pingTime.current = Date.now();
      ws.current.send(JSON.stringify({
        type: 'ping',
        timestamp: new Date().toISOString()
      }));
    }
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);

      // Handle pong for latency
      if (message.type === 'pong') {
        const latency = Date.now() - pingTime.current;
        setConnectionState(prev => ({
          ...prev,
          latency,
          lastHeartbeat: new Date().toISOString()
        }));
        return;
      }

      // Handle Confidence Pool events
      const wsEvent = message as WebSocketEvent;
      setLastEvent(wsEvent);

      switch (wsEvent.type) {
        case 'bet_placed':
          console.log('🎲 Bet placed:', wsEvent);
          onBetPlaced?.(wsEvent);
          // Invalidate betting feed and bankrolls
          queryClient.invalidateQueries({ queryKey: ['live-betting-feed'] });
          queryClient.invalidateQueries({ queryKey: ['expert-bankrolls'] });
          break;

        case 'bet_settled':
          console.log('✅ Bet settled:', wsEvent);
          onBetSettled?.(wsEvent);
          // Invalidate betting feed, bankrolls, and battles
          queryClient.invalidateQueries({ queryKey: ['live-betting-feed'] });
          queryClient.invalidateQueries({ queryKey: ['expert-bankrolls'] });
          queryClient.invalidateQueries({ queryKey: ['prediction-battles'] });
          break;

        case 'expert_eliminated':
          console.log('💀 Expert eliminated:', wsEvent);
          onExpertEliminated?.(wsEvent);
          // Invalidate all related queries
          queryClient.invalidateQueries({ queryKey: ['expert-bankrolls'] });
          queryClient.invalidateQueries({ queryKey: ['council-predictions'] });
          // Show notification
          showNotification(`${wsEvent.expert_emoji} ${wsEvent.expert_name} has been eliminated!`, 'error');
          break;

        case 'line_movement':
          console.log('📈 Line movement:', wsEvent);
          onLineMovement?.(wsEvent);
          // Invalidate relevant predictions
          queryClient.invalidateQueries({ queryKey: ['prediction-battles'] });
          break;

        case 'bankroll_updated':
          console.log('💰 Bankroll updated:', wsEvent);
          onBankrollUpdate?.(wsEvent);
          // Invalidate bankrolls
          queryClient.invalidateQueries({ queryKey: ['expert-bankrolls'] });
          break;

        default:
          console.log('Unknown event type:', message);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, [onBetPlaced, onBetSettled, onExpertEliminated, onLineMovement, onBankrollUpdate, queryClient]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      console.log('🔌 Connecting to WebSocket:', url);
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnectionState(prev => ({
          ...prev,
          connected: true,
          reconnectAttempts: 0
        }));

        // Start heartbeat
        heartbeatTimer.current = setInterval(sendHeartbeat, 30000); // Every 30 seconds

        // Subscribe to all Confidence Pool channels
        ws.current?.send(JSON.stringify({
          type: 'subscribe',
          channels: ['bets', 'lines', 'eliminations', 'bankrolls']
        }));
      };

      ws.current.onmessage = handleMessage;

      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setConnectionState(prev => ({
          ...prev,
          connected: false
        }));

        cleanup();

        // Auto-reconnect if enabled
        if (autoReconnect && event.code !== 1000) {
          setConnectionState(prev => {
            const newAttempts = prev.reconnectAttempts + 1;

            if (newAttempts <= maxReconnectAttempts) {
              console.log(`🔄 Attempting to reconnect (${newAttempts}/${maxReconnectAttempts})...`);

              reconnectTimer.current = setTimeout(() => {
                connect();
              }, reconnectInterval * newAttempts); // Exponential backoff

              return {
                ...prev,
                reconnectAttempts: newAttempts
              };
            } else {
              console.log('❌ Max reconnection attempts reached');
              showNotification('Connection lost. Please refresh the page.', 'error');
              return prev;
            }
          });
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }, [url, autoReconnect, maxReconnectAttempts, reconnectInterval, sendHeartbeat, handleMessage, cleanup]);

  // Disconnect from WebSocket
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

  // Send message
  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        ...message,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connectionState,
    lastEvent,
    sendMessage,
    connect,
    disconnect,
    isConnected: connectionState.connected
  };
};

// Helper function to show notifications
function showNotification(message: string, type: 'error' | 'info' | 'success' = 'info') {
  // This could be replaced with a toast library like react-hot-toast
  const event = new CustomEvent('show-notification', {
    detail: { message, type }
  });
  window.dispatchEvent(event);
}

export default useConfidencePoolWebSocket;