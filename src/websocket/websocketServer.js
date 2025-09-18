/**
 * WebSocket Server for NFL Predictor - Real-time Game Updates
 * Integrates with Supabase realtime to broadcast live game data
 */

import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import { supabase } from '../services/supabaseClientNode.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const PORT = process.env.WS_PORT || 8080;
const HEARTBEAT_INTERVAL = 30000; // 30 seconds

class NFLWebSocketServer {
  constructor() {
    this.server = createServer();
    this.wss = new WebSocketServer({ server: this.server });
    this.clients = new Map(); // Store client connections with metadata
    this.channels = new Map(); // Track channel subscriptions
    this.supabaseSubscriptions = new Map(); // Track Supabase realtime subscriptions

    this.setupWebSocketServer();
    this.setupSupabaseRealtimeSubscriptions();
    this.startHeartbeat();
  }

  /**
   * Setup WebSocket server event handlers
   */
  setupWebSocketServer() {
    this.wss.on('connection', (ws, request) => {
      const clientId = this.generateClientId();
      const url = new URL(request.url, `http://${request.headers.host}`);
      const userId = url.searchParams.get('user_id');
      const token = url.searchParams.get('token');

      // Store client information
      this.clients.set(clientId, {
        ws,
        clientId,
        userId,
        token,
        channels: new Set(),
        lastPing: Date.now(),
        isAlive: true,
        connectedAt: new Date(),
      });

      console.log(`[${new Date().toISOString()}] New WebSocket connection: ${clientId} (User: ${userId || 'anonymous'})`);

      // Send connection acknowledgment
      this.sendToClient(clientId, {
        event_type: 'connection_ack',
        data: {
          connection_id: clientId,
          server_time: new Date().toISOString(),
          supported_events: [
            'game_started', 'game_ended', 'game_update', 'score_update', 'quarter_change',
            'prediction_update', 'prediction_refresh', 'model_update',
            'odds_update', 'line_movement',
            'connection_ack', 'heartbeat', 'error', 'notification',
            'user_subscription', 'user_unsubscription'
          ],
          heartbeat_interval: HEARTBEAT_INTERVAL / 1000, // Send in seconds
        },
        timestamp: new Date().toISOString(),
        message_id: this.generateMessageId(),
      });

      // Setup message handler
      ws.on('message', (data) => this.handleMessage(clientId, data));

      // Handle client disconnect
      ws.on('close', (code, reason) => {
        console.log(`[${new Date().toISOString()}] Client disconnected: ${clientId} (${code}: ${reason})`);
        this.handleClientDisconnect(clientId);
      });

      // Handle WebSocket errors
      ws.on('error', (error) => {
        console.error(`[${new Date().toISOString()}] WebSocket error for client ${clientId}:`, error);
        this.handleClientDisconnect(clientId);
      });

      // Setup ping/pong for connection health
      ws.on('pong', () => {
        const client = this.clients.get(clientId);
        if (client) {
          client.isAlive = true;
          client.lastPing = Date.now();
        }
      });
    });

    console.log(`WebSocket server setup complete`);
  }

  /**
   * Handle incoming messages from clients
   */
  handleMessage(clientId, data) {
    const client = this.clients.get(clientId);
    if (!client) return;

    try {
      const message = JSON.parse(data.toString());
      console.log(`[${new Date().toISOString()}] Message from ${clientId}:`, message.event_type);

      switch (message.event_type) {
        case 'user_subscription':
          this.handleChannelSubscription(clientId, message.data.channel);
          break;

        case 'user_unsubscription':
          this.handleChannelUnsubscription(clientId, message.data.channel);
          break;

        case 'heartbeat':
          this.handleHeartbeat(clientId, message.data);
          break;

        default:
          console.warn(`[${new Date().toISOString()}] Unknown event type: ${message.event_type}`);
      }
    } catch (error) {
      console.error(`[${new Date().toISOString()}] Error parsing message from ${clientId}:`, error);
      this.sendErrorToClient(clientId, 'Invalid message format');
    }
  }

  /**
   * Handle channel subscription
   */
  handleChannelSubscription(clientId, channel) {
    const client = this.clients.get(clientId);
    if (!client) return;

    // Add client to channel
    if (!this.channels.has(channel)) {
      this.channels.set(channel, new Set());
    }
    this.channels.get(channel).add(clientId);
    client.channels.add(channel);

    console.log(`[${new Date().toISOString()}] Client ${clientId} subscribed to channel: ${channel}`);

    // Send confirmation
    this.sendToClient(clientId, {
      event_type: 'notification',
      data: {
        message: `Subscribed to channel: ${channel}`,
        level: 'info',
        action_required: false,
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
      channel,
    });
  }

  /**
   * Handle channel unsubscription
   */
  handleChannelUnsubscription(clientId, channel) {
    const client = this.clients.get(clientId);
    if (!client) return;

    // Remove client from channel
    if (this.channels.has(channel)) {
      this.channels.get(channel).delete(clientId);
      if (this.channels.get(channel).size === 0) {
        this.channels.delete(channel);
      }
    }
    client.channels.delete(channel);

    console.log(`[${new Date().toISOString()}] Client ${clientId} unsubscribed from channel: ${channel}`);

    // Send confirmation
    this.sendToClient(clientId, {
      event_type: 'notification',
      data: {
        message: `Unsubscribed from channel: ${channel}`,
        level: 'info',
        action_required: false,
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
      channel,
    });
  }

  /**
   * Handle heartbeat from client
   */
  handleHeartbeat(clientId, data) {
    const client = this.clients.get(clientId);
    if (!client) return;

    client.lastPing = Date.now();
    client.isAlive = true;

    // Send heartbeat response
    this.sendToClient(clientId, {
      event_type: 'heartbeat',
      data: {
        timestamp: new Date().toISOString(),
        client_time: data.client_time,
        server_time: new Date().toISOString(),
        connection_id: clientId,
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
    });
  }

  /**
   * Handle client disconnect
   */
  handleClientDisconnect(clientId) {
    const client = this.clients.get(clientId);
    if (!client) return;

    // Remove from all channels
    client.channels.forEach(channel => {
      if (this.channels.has(channel)) {
        this.channels.get(channel).delete(clientId);
        if (this.channels.get(channel).size === 0) {
          this.channels.delete(channel);
        }
      }
    });

    // Remove client
    this.clients.delete(clientId);
    console.log(`[${new Date().toISOString()}] Cleaned up client: ${clientId}`);
  }

  /**
   * Setup Supabase realtime subscriptions for live data
   */
  setupSupabaseRealtimeSubscriptions() {
    console.log('Setting up Supabase realtime subscriptions...');

    // Subscribe to game updates
    const gamesSubscription = supabase
      .channel('games')
      .on('postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'games'
        },
        (payload) => this.handleGameUpdate(payload)
      )
      .subscribe((status) => {
        console.log(`[${new Date().toISOString()}] Games subscription status:`, status);
      });

    // Subscribe to predictions updates
    const predictionsSubscription = supabase
      .channel('predictions')
      .on('postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'predictions'
        },
        (payload) => this.handlePredictionUpdate(payload)
      )
      .subscribe((status) => {
        console.log(`[${new Date().toISOString()}] Predictions subscription status:`, status);
      });

    // Subscribe to odds updates
    const oddsSubscription = supabase
      .channel('odds')
      .on('postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'odds'
        },
        (payload) => this.handleOddsUpdate(payload)
      )
      .subscribe((status) => {
        console.log(`[${new Date().toISOString()}] Odds subscription status:`, status);
      });

    // Store subscriptions for cleanup
    this.supabaseSubscriptions.set('games', gamesSubscription);
    this.supabaseSubscriptions.set('predictions', predictionsSubscription);
    this.supabaseSubscriptions.set('odds', oddsSubscription);

    console.log('Supabase realtime subscriptions setup complete');
  }

  /**
   * Handle game updates from Supabase
   */
  handleGameUpdate(payload) {
    console.log(`[${new Date().toISOString()}] Game update received:`, payload.eventType, payload.new?.id);

    const gameData = payload.new || payload.old;
    if (!gameData) return;

    let eventType = 'game_update';
    if (payload.eventType === 'INSERT') {
      eventType = 'game_started';
    } else if (payload.eventType === 'UPDATE' && gameData.status === 'FINAL') {
      eventType = 'game_ended';
    } else if (payload.eventType === 'UPDATE' && (payload.new.home_score !== payload.old?.home_score || payload.new.away_score !== payload.old?.away_score)) {
      eventType = 'score_update';
    } else if (payload.eventType === 'UPDATE' && payload.new.quarter !== payload.old?.quarter) {
      eventType = 'quarter_change';
    }

    const message = {
      event_type: eventType,
      data: {
        game_id: gameData.id,
        home_team: gameData.home_team,
        away_team: gameData.away_team,
        home_score: gameData.home_score || 0,
        away_score: gameData.away_score || 0,
        quarter: gameData.quarter || 1,
        time_remaining: gameData.time_remaining || '15:00',
        game_status: gameData.status || 'scheduled',
        updated_at: gameData.updated_at || new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
    };

    // Broadcast to relevant channels
    this.broadcastToChannel('games', message);
    this.broadcastToChannel(`game_${gameData.id}`, message);

    // Also send specific notifications for significant events
    if (eventType === 'score_update') {
      this.broadcastToChannel('games', {
        event_type: 'notification',
        data: {
          message: `Score Update: ${gameData.home_team} ${gameData.home_score} - ${gameData.away_score} ${gameData.away_team}`,
          level: 'info',
          title: 'Live Score Update',
          action_required: false,
        },
        timestamp: new Date().toISOString(),
        message_id: this.generateMessageId(),
      });
    }
  }

  /**
   * Handle prediction updates from Supabase
   */
  handlePredictionUpdate(payload) {
    console.log(`[${new Date().toISOString()}] Prediction update received:`, payload.eventType, payload.new?.id);

    const predictionData = payload.new || payload.old;
    if (!predictionData) return;

    const message = {
      event_type: 'prediction_update',
      data: {
        game_id: predictionData.game_id,
        home_team: predictionData.home_team,
        away_team: predictionData.away_team,
        home_win_probability: predictionData.home_win_probability || 0.5,
        away_win_probability: predictionData.away_win_probability || 0.5,
        predicted_spread: predictionData.predicted_spread || 0,
        confidence_level: predictionData.confidence_level || 0.5,
        model_version: predictionData.model_version || '1.0',
        updated_at: predictionData.updated_at || new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
    };

    // Broadcast to relevant channels
    this.broadcastToChannel('predictions', message);
    this.broadcastToChannel(`predictions_${predictionData.game_id}`, message);
  }

  /**
   * Handle odds updates from Supabase
   */
  handleOddsUpdate(payload) {
    console.log(`[${new Date().toISOString()}] Odds update received:`, payload.eventType, payload.new?.id);

    const oddsData = payload.new || payload.old;
    if (!oddsData) return;

    const message = {
      event_type: 'odds_update',
      data: {
        game_id: oddsData.game_id,
        sportsbook: oddsData.sportsbook || 'Unknown',
        home_team: oddsData.home_team,
        away_team: oddsData.away_team,
        spread: oddsData.spread || 0,
        moneyline_home: oddsData.moneyline_home || 100,
        moneyline_away: oddsData.moneyline_away || -100,
        over_under: oddsData.over_under || 45.5,
        updated_at: oddsData.updated_at || new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
    };

    // Broadcast to relevant channels
    this.broadcastToChannel('odds', message);
    this.broadcastToChannel(`odds_${oddsData.game_id}`, message);

    // Check for significant line movement
    if (payload.eventType === 'UPDATE' && payload.old) {
      const spreadChange = Math.abs((payload.new.spread || 0) - (payload.old.spread || 0));
      if (spreadChange >= 1.0) { // Significant line movement
        this.broadcastToChannel('odds', {
          event_type: 'line_movement',
          data: {
            message: `Significant line movement: ${oddsData.sportsbook} spread moved ${spreadChange} points`,
            game_id: oddsData.game_id,
            sportsbook: oddsData.sportsbook,
            old_spread: payload.old.spread,
            new_spread: payload.new.spread,
            change: spreadChange,
          },
          timestamp: new Date().toISOString(),
          message_id: this.generateMessageId(),
        });
      }
    }
  }

  /**
   * Broadcast message to all clients in a channel
   */
  broadcastToChannel(channel, message) {
    const subscribers = this.channels.get(channel);
    if (!subscribers || subscribers.size === 0) {
      console.log(`[${new Date().toISOString()}] No subscribers for channel: ${channel}`);
      return;
    }

    console.log(`[${new Date().toISOString()}] Broadcasting to channel ${channel} (${subscribers.size} subscribers)`);

    subscribers.forEach(clientId => {
      this.sendToClient(clientId, { ...message, channel });
    });
  }

  /**
   * Send message to specific client
   */
  sendToClient(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client || client.ws.readyState !== client.ws.OPEN) {
      console.warn(`[${new Date().toISOString()}] Cannot send message to client ${clientId}: connection not open`);
      return false;
    }

    try {
      client.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error(`[${new Date().toISOString()}] Error sending message to client ${clientId}:`, error);
      this.handleClientDisconnect(clientId);
      return false;
    }
  }

  /**
   * Send error message to client
   */
  sendErrorToClient(clientId, errorMessage) {
    this.sendToClient(clientId, {
      event_type: 'error',
      data: {
        error: errorMessage,
        timestamp: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
    });
  }

  /**
   * Start heartbeat mechanism to keep connections alive
   */
  startHeartbeat() {
    setInterval(() => {
      const now = Date.now();
      const staleThreshold = HEARTBEAT_INTERVAL * 2; // 2 missed heartbeats = stale

      this.clients.forEach((client, clientId) => {
        if (!client.isAlive || (now - client.lastPing > staleThreshold)) {
          console.log(`[${new Date().toISOString()}] Terminating stale connection: ${clientId}`);
          client.ws.terminate();
          this.handleClientDisconnect(clientId);
        } else {
          client.isAlive = false;
          try {
            client.ws.ping();
          } catch (error) {
            console.error(`[${new Date().toISOString()}] Error pinging client ${clientId}:`, error);
            this.handleClientDisconnect(clientId);
          }
        }
      });

      // Log connection stats
      console.log(`[${new Date().toISOString()}] Active connections: ${this.clients.size}, Active channels: ${this.channels.size}`);
    }, HEARTBEAT_INTERVAL);
  }

  /**
   * Generate unique client ID
   */
  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate unique message ID
   */
  generateMessageId() {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get server status
   */
  getStatus() {
    return {
      port: PORT,
      connectedClients: this.clients.size,
      activeChannels: this.channels.size,
      supabaseSubscriptions: this.supabaseSubscriptions.size,
      uptime: process.uptime(),
      startTime: new Date().toISOString(),
    };
  }

  /**
   * Start the server
   */
  start() {
    this.server.listen(PORT, () => {
      console.log(`🚀 NFL WebSocket Server started on port ${PORT}`);
      console.log(`   - WebSocket endpoint: ws://localhost:${PORT}`);
      console.log(`   - Heartbeat interval: ${HEARTBEAT_INTERVAL / 1000}s`);
      console.log(`   - Supabase integration: ${this.supabaseSubscriptions.size > 0 ? 'Active' : 'Inactive'}`);
      console.log(`   - Server started at: ${new Date().toISOString()}`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => this.shutdown());
    process.on('SIGINT', () => this.shutdown());
  }

  /**
   * Shutdown server gracefully
   */
  shutdown() {
    console.log('\n🛑 Shutting down NFL WebSocket Server...');

    // Close all WebSocket connections
    this.clients.forEach((client, clientId) => {
      client.ws.close(1000, 'Server shutdown');
    });

    // Unsubscribe from Supabase realtime
    this.supabaseSubscriptions.forEach((subscription, name) => {
      console.log(`   - Unsubscribing from ${name}...`);
      supabase.removeChannel(subscription);
    });

    // Close server
    this.server.close(() => {
      console.log('✅ NFL WebSocket Server shutdown complete');
      process.exit(0);
    });
  }
}

// Start the server if this file is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new NFLWebSocketServer();
  server.start();
}

export default NFLWebSocketServer;