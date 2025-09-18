import { supabase, supabaseHelpers } from './supabaseClient.js';

/**
 * Real-time Service for live dashboard updates
 * Handles WebSocket connections and data subscriptions
 */
class RealtimeService {
  constructor() {
    this.subscriptions = new Map();
    this.isConnected = false;
    this.connectionRetryCount = 0;
    this.maxRetries = 5;
    this.retryDelay = 2000;

    // Event callbacks
    this.eventHandlers = {
      onGameUpdate: [],
      onPredictionUpdate: [],
      onExpertBetUpdate: [],
      onNewsUpdate: [],
      onOddsUpdate: [],
      onExpertResearchUpdate: [],
      onConnectionChange: []
    };

    // Initialize connection status monitoring
    this.initializeConnectionMonitoring();
  }

  /**
   * Initialize connection status monitoring
   */
  initializeConnectionMonitoring() {
    // Monitor Supabase realtime connection status
    supabase.realtime.onOpen(() => {
      console.log('🟢 Realtime connection established');
      this.isConnected = true;
      this.connectionRetryCount = 0;
      this.notifyConnectionChange('connected');
    });

    supabase.realtime.onClose(() => {
      console.log('🔴 Realtime connection closed');
      this.isConnected = false;
      this.notifyConnectionChange('disconnected');
      this.handleReconnection();
    });

    supabase.realtime.onError((error) => {
      console.error('❌ Realtime connection error:', error);
      this.isConnected = false;
      this.notifyConnectionChange('error', error);
    });
  }

  /**
   * Handle automatic reconnection
   */
  async handleReconnection() {
    if (this.connectionRetryCount >= this.maxRetries) {
      console.error('Max reconnection attempts reached');
      this.notifyConnectionChange('max_retries_reached');
      return;
    }

    this.connectionRetryCount++;
    console.log(`🔄 Attempting reconnection ${this.connectionRetryCount}/${this.maxRetries}...`);

    setTimeout(() => {
      this.reestablishSubscriptions();
    }, this.retryDelay * this.connectionRetryCount);
  }

  /**
   * Subscribe to game updates (scores, status changes)
   */
  subscribeToGames(callback) {
    const subscription = supabase
      .channel('games-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'games'
      }, (payload) => {
        console.log('🏈 Game update:', payload);
        this.notifyGameUpdate(payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set('games', subscription);
    this.eventHandlers.onGameUpdate.push(callback);

    console.log('✅ Subscribed to game updates');
    return subscription;
  }

  /**
   * Subscribe to prediction updates
   */
  subscribeToPredictions(callback) {
    const subscription = supabase
      .channel('predictions-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'predictions'
      }, (payload) => {
        console.log('🤖 Prediction update:', payload);
        this.notifyPredictionUpdate(payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set('predictions', subscription);
    this.eventHandlers.onPredictionUpdate.push(callback);

    console.log('✅ Subscribed to prediction updates');
    return subscription;
  }

  /**
   * Subscribe to expert bet updates
   */
  subscribeToExpertBets(callback) {
    const subscription = supabase
      .channel('expert-bets-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'expert_bets'
      }, (payload) => {
        console.log('💰 Expert bet update:', payload);
        this.notifyExpertBetUpdate(payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set('expert_bets', subscription);
    this.eventHandlers.onExpertBetUpdate.push(callback);

    console.log('✅ Subscribed to expert bet updates');
    return subscription;
  }

  /**
   * Subscribe to news and sentiment updates
   */
  subscribeToNews(callback) {
    const subscription = supabase
      .channel('news-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'news_articles'
      }, (payload) => {
        console.log('📰 News update:', payload);
        this.notifyNewsUpdate(payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set('news_articles', subscription);
    this.eventHandlers.onNewsUpdate.push(callback);

    console.log('✅ Subscribed to news updates');
    return subscription;
  }

  /**
   * Subscribe to odds updates
   */
  subscribeToOdds(callback) {
    const subscription = supabase
      .channel('odds-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'odds_history'
      }, (payload) => {
        console.log('💸 Odds update:', payload);
        this.notifyOddsUpdate(payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set('odds_history', subscription);
    this.eventHandlers.onOddsUpdate.push(callback);

    console.log('✅ Subscribed to odds updates');
    return subscription;
  }

  /**
   * Subscribe to expert research updates
   */
  subscribeToExpertResearch(callback) {
    const subscription = supabase
      .channel('expert-research-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'expert_research'
      }, (payload) => {
        console.log('🔍 Expert research update:', payload);
        this.notifyExpertResearchUpdate(payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set('expert_research', subscription);
    this.eventHandlers.onExpertResearchUpdate.push(callback);

    console.log('✅ Subscribed to expert research updates');
    return subscription;
  }

  /**
   * Subscribe to all updates for dashboard
   */
  subscribeToAllUpdates(callbacks = {}) {
    const subscriptions = {};

    if (callbacks.onGameUpdate) {
      subscriptions.games = this.subscribeToGames(callbacks.onGameUpdate);
    }

    if (callbacks.onPredictionUpdate) {
      subscriptions.predictions = this.subscribeToPredictions(callbacks.onPredictionUpdate);
    }

    if (callbacks.onExpertBetUpdate) {
      subscriptions.expertBets = this.subscribeToExpertBets(callbacks.onExpertBetUpdate);
    }

    if (callbacks.onNewsUpdate) {
      subscriptions.news = this.subscribeToNews(callbacks.onNewsUpdate);
    }

    if (callbacks.onOddsUpdate) {
      subscriptions.odds = this.subscribeToOdds(callbacks.onOddsUpdate);
    }

    if (callbacks.onExpertResearchUpdate) {
      subscriptions.expertResearch = this.subscribeToExpertResearch(callbacks.onExpertResearchUpdate);
    }

    if (callbacks.onConnectionChange) {
      this.eventHandlers.onConnectionChange.push(callbacks.onConnectionChange);
    }

    console.log(`✅ Subscribed to ${Object.keys(subscriptions).length} data streams`);

    return {
      subscriptions,
      unsubscribeAll: () => this.unsubscribeAll()
    };
  }

  /**
   * Subscribe to specific game updates by ID
   */
  subscribeToGame(gameId, callback) {
    const channelName = `game-${gameId}`;

    const subscription = supabase
      .channel(channelName)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'games',
        filter: `id=eq.${gameId}`
      }, (payload) => {
        console.log(`🏈 Game ${gameId} update:`, payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set(channelName, subscription);

    console.log(`✅ Subscribed to game ${gameId} updates`);
    return subscription;
  }

  /**
   * Subscribe to expert-specific updates
   */
  subscribeToExpert(expertId, callback) {
    const channelName = `expert-${expertId}`;

    const subscription = supabase
      .channel(channelName)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'expert_bets',
        filter: `expert_id=eq.${expertId}`
      }, (payload) => {
        console.log(`👨‍💼 Expert ${expertId} update:`, payload);
        if (callback) callback(payload);
      })
      .subscribe();

    this.subscriptions.set(channelName, subscription);

    console.log(`✅ Subscribed to expert ${expertId} updates`);
    return subscription;
  }

  /**
   * Unsubscribe from specific subscription
   */
  async unsubscribe(subscriptionKey) {
    const subscription = this.subscriptions.get(subscriptionKey);
    if (subscription) {
      await supabase.removeChannel(subscription);
      this.subscriptions.delete(subscriptionKey);
      console.log(`❌ Unsubscribed from ${subscriptionKey}`);
    }
  }

  /**
   * Unsubscribe from all subscriptions
   */
  async unsubscribeAll() {
    for (const [key, subscription] of this.subscriptions.entries()) {
      try {
        await supabase.removeChannel(subscription);
        console.log(`❌ Unsubscribed from ${key}`);
      } catch (error) {
        console.error(`Error unsubscribing from ${key}:`, error);
      }
    }

    this.subscriptions.clear();
    this.clearEventHandlers();
    console.log('❌ Unsubscribed from all realtime updates');
  }

  /**
   * Reestablish all subscriptions after reconnection
   */
  async reestablishSubscriptions() {
    console.log('🔄 Reestablishing subscriptions...');

    const subscriptionKeys = Array.from(this.subscriptions.keys());

    // Clear existing subscriptions
    await this.unsubscribeAll();

    // Recreate subscriptions based on keys
    for (const key of subscriptionKeys) {
      try {
        if (key === 'games') {
          this.subscribeToGames();
        } else if (key === 'predictions') {
          this.subscribeToPredictions();
        } else if (key === 'expert_bets') {
          this.subscribeToExpertBets();
        } else if (key === 'news_articles') {
          this.subscribeToNews();
        } else if (key === 'odds_history') {
          this.subscribeToOdds();
        } else if (key === 'expert_research') {
          this.subscribeToExpertResearch();
        } else if (key.startsWith('game-')) {
          const gameId = key.replace('game-', '');
          this.subscribeToGame(gameId);
        } else if (key.startsWith('expert-')) {
          const expertId = key.replace('expert-', '');
          this.subscribeToExpert(expertId);
        }
      } catch (error) {
        console.error(`Error reestablishing subscription ${key}:`, error);
      }
    }
  }

  // Event notification methods
  notifyGameUpdate(payload) {
    this.eventHandlers.onGameUpdate.forEach(handler => {
      try {
        handler(payload);
      } catch (error) {
        console.error('Error in game update handler:', error);
      }
    });
  }

  notifyPredictionUpdate(payload) {
    this.eventHandlers.onPredictionUpdate.forEach(handler => {
      try {
        handler(payload);
      } catch (error) {
        console.error('Error in prediction update handler:', error);
      }
    });
  }

  notifyExpertBetUpdate(payload) {
    this.eventHandlers.onExpertBetUpdate.forEach(handler => {
      try {
        handler(payload);
      } catch (error) {
        console.error('Error in expert bet update handler:', error);
      }
    });
  }

  notifyNewsUpdate(payload) {
    this.eventHandlers.onNewsUpdate.forEach(handler => {
      try {
        handler(payload);
      } catch (error) {
        console.error('Error in news update handler:', error);
      }
    });
  }

  notifyOddsUpdate(payload) {
    this.eventHandlers.onOddsUpdate.forEach(handler => {
      try {
        handler(payload);
      } catch (error) {
        console.error('Error in odds update handler:', error);
      }
    });
  }

  notifyExpertResearchUpdate(payload) {
    this.eventHandlers.onExpertResearchUpdate.forEach(handler => {
      try {
        handler(payload);
      } catch (error) {
        console.error('Error in expert research update handler:', error);
      }
    });
  }

  notifyConnectionChange(status, error = null) {
    this.eventHandlers.onConnectionChange.forEach(handler => {
      try {
        handler({ status, error, isConnected: this.isConnected });
      } catch (error) {
        console.error('Error in connection change handler:', error);
      }
    });
  }

  /**
   * Clear all event handlers
   */
  clearEventHandlers() {
    Object.keys(this.eventHandlers).forEach(key => {
      this.eventHandlers[key] = [];
    });
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      activeSubscriptions: this.subscriptions.size,
      retryCount: this.connectionRetryCount,
      subscriptions: Array.from(this.subscriptions.keys())
    };
  }

  /**
   * Test connection with a simple query
   */
  async testConnection() {
    try {
      const { data, error } = await supabase
        .from('games')
        .select('id')
        .limit(1);

      return {
        success: !error,
        connected: this.isConnected,
        error: error?.message
      };
    } catch (error) {
      return {
        success: false,
        connected: false,
        error: error.message
      };
    }
  }
}

// Create singleton instance
const realtimeService = new RealtimeService();

export default realtimeService;