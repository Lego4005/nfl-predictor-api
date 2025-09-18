/**
 * WebSocket Service for Real-time NFL Predictor Updates
 */

export enum WebSocketEventType {
  // Game Events
  GAME_STARTED = 'game_started',
  GAME_ENDED = 'game_ended',
  GAME_UPDATE = 'game_update',
  SCORE_UPDATE = 'score_update',
  QUARTER_CHANGE = 'quarter_change',

  // Prediction Events
  PREDICTION_UPDATE = 'prediction_update',
  PREDICTION_REFRESH = 'prediction_refresh',
  MODEL_UPDATE = 'model_update',

  // Odds Events
  ODDS_UPDATE = 'odds_update',
  LINE_MOVEMENT = 'line_movement',

  // System Events
  CONNECTION_ACK = 'connection_ack',
  HEARTBEAT = 'heartbeat',
  ERROR = 'error',
  NOTIFICATION = 'notification',

  // User Events
  USER_SUBSCRIPTION = 'user_subscription',
  USER_UNSUBSCRIPTION = 'user_unsubscription',
}

export interface WebSocketMessage<T = any> {
  event_type: WebSocketEventType;
  data: T;
  timestamp: string;
  message_id?: string;
  user_id?: string;
  channel?: string;
}

export interface GameUpdate {
  game_id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  quarter: number;
  time_remaining: string;
  game_status: string;
  updated_at: string;
}

export interface PredictionUpdate {
  game_id: string;
  home_team: string;
  away_team: string;
  home_win_probability: number;
  away_win_probability: number;
  predicted_spread: number;
  confidence_level: number;
  model_version: string;
  updated_at: string;
}

export interface OddsUpdate {
  game_id: string;
  sportsbook: string;
  home_team: string;
  away_team: string;
  spread: number;
  moneyline_home: number;
  moneyline_away: number;
  over_under: number;
  updated_at: string;
}

export interface SystemNotification {
  message: string;
  level: 'info' | 'warning' | 'error';
  title?: string;
  action_required: boolean;
}

export interface ConnectionAck {
  connection_id: string;
  server_time: string;
  supported_events: WebSocketEventType[];
  heartbeat_interval: number;
}

export type WebSocketEventHandler<T = any> = (data: T, message: WebSocketMessage<T>) => void;

export interface WebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  userId?: string;
  token?: string;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private options: Required<WebSocketOptions>;
  private eventHandlers: Map<WebSocketEventType, Set<WebSocketEventHandler>> = new Map();
  private reconnectCount = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private connectionId: string | null = null;
  private isConnected = false;
  private isReconnecting = false;

  constructor(options: WebSocketOptions) {
    this.options = {
      autoConnect: true,
      reconnectAttempts: 5,
      reconnectInterval: 5000,
      heartbeatInterval: 30000,
      userId: '',
      token: '',
      ...options,
    };

    if (this.options.autoConnect) {
      this.connect();
    }
  }

  /**
   * Connect to WebSocket server
   */
  public async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket is already connected');
      return;
    }

    try {
      const url = this.buildWebSocketUrl();
      console.log('Connecting to WebSocket:', url);

      this.ws = new WebSocket(url);
      this.setupWebSocketHandlers();

      // Wait for connection to establish
      await new Promise<void>((resolve, reject) => {
        if (!this.ws) {
          reject(new Error('WebSocket not initialized'));
          return;
        }

        const onOpen = () => {
          this.ws?.removeEventListener('open', onOpen);
          this.ws?.removeEventListener('error', onError);
          resolve();
        };

        const onError = (error: Event) => {
          this.ws?.removeEventListener('open', onOpen);
          this.ws?.removeEventListener('error', onError);
          reject(error);
        };

        this.ws.addEventListener('open', onOpen);
        this.ws.addEventListener('error', onError);
      });

    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      this.handleReconnection();
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.isReconnecting = false;
    this.clearTimers();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.isConnected = false;
    this.connectionId = null;
    this.reconnectCount = 0;

    console.log('WebSocket disconnected');
  }

  /**
   * Send message to WebSocket server
   */
  public send(eventType: WebSocketEventType, data: any): void {
    if (!this.isConnected || !this.ws) {
      console.warn('WebSocket not connected. Message queued:', { eventType, data });
      return;
    }

    const message: WebSocketMessage = {
      event_type: eventType,
      data,
      timestamp: new Date().toISOString(),
      user_id: this.options.userId || undefined,
    };

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  /**
   * Subscribe to channel for targeted updates
   */
  public subscribeToChannel(channel: string): void {
    this.send(WebSocketEventType.USER_SUBSCRIPTION, { channel });
    console.log('Subscribed to channel:', channel);
  }

  /**
   * Unsubscribe from channel
   */
  public unsubscribeFromChannel(channel: string): void {
    this.send(WebSocketEventType.USER_UNSUBSCRIPTION, { channel });
    console.log('Unsubscribed from channel:', channel);
  }

  /**
   * Add event listener
   */
  public on<T = any>(eventType: WebSocketEventType, handler: WebSocketEventHandler<T>): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler as WebSocketEventHandler);
  }

  /**
   * Remove event listener
   */
  public off<T = any>(eventType: WebSocketEventType, handler: WebSocketEventHandler<T>): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler as WebSocketEventHandler);
    }
  }

  /**
   * Remove all event listeners for a specific event type
   */
  public removeAllListeners(eventType?: WebSocketEventType): void {
    if (eventType) {
      this.eventHandlers.delete(eventType);
    } else {
      this.eventHandlers.clear();
    }
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(): {
    isConnected: boolean;
    isReconnecting: boolean;
    connectionId: string | null;
    reconnectCount: number;
  } {
    return {
      isConnected: this.isConnected,
      isReconnecting: this.isReconnecting,
      connectionId: this.connectionId,
      reconnectCount: this.reconnectCount,
    };
  }

  /**
   * Build WebSocket URL with query parameters
   */
  private buildWebSocketUrl(): string {
    const url = new URL(this.options.url);

    if (this.options.userId) {
      url.searchParams.set('user_id', this.options.userId);
    }

    if (this.options.token) {
      url.searchParams.set('token', this.options.token);
    }

    return url.toString();
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupWebSocketHandlers(): void {
    if (!this.ws) return;

    this.ws.addEventListener('open', this.handleOpen.bind(this));
    this.ws.addEventListener('message', this.handleMessage.bind(this));
    this.ws.addEventListener('close', this.handleClose.bind(this));
    this.ws.addEventListener('error', this.handleError.bind(this));
  }

  /**
   * Handle WebSocket connection open
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.isConnected = true;
    this.isReconnecting = false;
    this.reconnectCount = 0;
    this.startHeartbeat();
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.dispatchEvent(message);

      // Handle special system events
      if (message.event_type === WebSocketEventType.CONNECTION_ACK) {
        this.handleConnectionAck(message.data);
      } else if (message.event_type === WebSocketEventType.HEARTBEAT) {
        this.handleHeartbeatResponse(message.data);
      }

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error, event.data);
    }
  }

  /**
   * Handle WebSocket connection close
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket connection closed:', event.code, event.reason);
    this.isConnected = false;
    this.clearTimers();

    // Handle reconnection unless explicitly closed by client
    if (event.code !== 1000 && this.reconnectCount < this.options.reconnectAttempts) {
      this.handleReconnection();
    }
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
    this.dispatchEvent({
      event_type: WebSocketEventType.ERROR,
      data: { error: 'WebSocket connection error' },
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Handle connection acknowledgment
   */
  private handleConnectionAck(data: ConnectionAck): void {
    this.connectionId = data.connection_id;
    this.options.heartbeatInterval = data.heartbeat_interval * 1000; // Convert to ms
    console.log('Connection established with ID:', this.connectionId);
  }

  /**
   * Handle heartbeat response
   */
  private handleHeartbeatResponse(data: any): void {
    // Heartbeat acknowledged by server
    console.debug('Heartbeat acknowledged:', data.timestamp);
  }

  /**
   * Start heartbeat mechanism
   */
  private startHeartbeat(): void {
    this.clearHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send(WebSocketEventType.HEARTBEAT, {
          timestamp: new Date().toISOString(),
          connection_id: this.connectionId,
          client_time: new Date().toISOString(),
        });
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnection(): void {
    if (this.isReconnecting || this.reconnectCount >= this.options.reconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.isReconnecting = true;
    this.reconnectCount++;

    console.log(`Attempting to reconnect (${this.reconnectCount}/${this.options.reconnectAttempts})...`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
        this.handleReconnection();
      });
    }, this.options.reconnectInterval);
  }

  /**
   * Dispatch event to registered handlers
   */
  private dispatchEvent(message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(message.event_type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message.data, message);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    this.clearHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Clear heartbeat timer
   */
  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

/**
 * WebSocket Hook for React Components
 */
export interface UseWebSocketResult {
  isConnected: boolean;
  isReconnecting: boolean;
  connectionId: string | null;
  reconnectCount: number;
  send: (eventType: WebSocketEventType, data: any) => void;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  on: <T = any>(eventType: WebSocketEventType, handler: WebSocketEventHandler<T>) => void;
  off: <T = any>(eventType: WebSocketEventType, handler: WebSocketEventHandler<T>) => void;
}

// Global WebSocket service instance
export const websocketService = new WebSocketService({
  url: `ws://localhost:8080`,
  autoConnect: false, // Manual connection control
  reconnectAttempts: 5,
  reconnectInterval: 5000,
  heartbeatInterval: 30000,
});

/**
 * React Hook for WebSocket functionality
 */
import { useState, useEffect, useCallback } from 'react';

export const useWebSocket = (options?: Partial<WebSocketOptions>): UseWebSocketResult => {
  const [connectionStatus, setConnectionStatus] = useState(() =>
    websocketService.getConnectionStatus()
  );

  // Update connection status when it changes
  useEffect(() => {
    const updateStatus = () => {
      setConnectionStatus(websocketService.getConnectionStatus());
    };

    // Set up listeners for connection status changes
    websocketService.on(WebSocketEventType.CONNECTION_ACK, updateStatus);
    websocketService.on(WebSocketEventType.ERROR, updateStatus);

    // Periodic status updates
    const statusInterval = setInterval(updateStatus, 1000);

    // Initial connection if specified
    if (options?.autoConnect !== false) {
      websocketService.connect().catch(console.error);
    }

    return () => {
      clearInterval(statusInterval);
      websocketService.off(WebSocketEventType.CONNECTION_ACK, updateStatus);
      websocketService.off(WebSocketEventType.ERROR, updateStatus);
    };
  }, [options?.autoConnect]);

  const send = useCallback((eventType: WebSocketEventType, data: any) => {
    websocketService.send(eventType, data);
  }, []);

  const subscribe = useCallback((channel: string) => {
    websocketService.subscribeToChannel(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    websocketService.unsubscribeFromChannel(channel);
  }, []);

  const on = useCallback(<T = any>(eventType: WebSocketEventType, handler: WebSocketEventHandler<T>) => {
    websocketService.on(eventType, handler);
  }, []);

  const off = useCallback(<T = any>(eventType: WebSocketEventType, handler: WebSocketEventHandler<T>) => {
    websocketService.off(eventType, handler);
  }, []);

  return {
    ...connectionStatus,
    send,
    subscribe,
    unsubscribe,
    on,
    off,
  };
};