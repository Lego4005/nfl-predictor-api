/**
 * Load Testing for Multiple Simultaneous Live Games
 * Tests system performance under high concurrent game loads
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { WebSocketEventType } from '../../src/services/websocketService';

// Load testing configuration
const LOAD_TEST_CONFIG = {
  // Sunday afternoon typical load
  SUNDAY_PEAK_GAMES: 16,
  THURSDAY_NIGHT: 1,
  MONDAY_NIGHT: 1,
  PLAYOFF_WEEKEND: 4,
  SUPER_BOWL: 1,

  // Update frequencies (per second)
  SCORE_UPDATE_FREQUENCY: 0.1,      // Every 10 seconds
  PREDICTION_UPDATE_FREQUENCY: 0.5,  // Every 2 seconds
  ODDS_UPDATE_FREQUENCY: 2,          // Twice per second
  HEARTBEAT_FREQUENCY: 1/30,         // Every 30 seconds

  // Client simulation
  CONCURRENT_USERS_PER_GAME: 1000,
  PEAK_CONCURRENT_USERS: 50000,

  // Performance thresholds
  MAX_LATENCY_MS: 500,
  MAX_MEMORY_MB: 512,
  MIN_CPU_EFFICIENCY: 0.8,
  TARGET_UPTIME: 0.999 // 99.9%
};

// Mock WebSocket server for load testing
class MockWebSocketServer {
  private connections: Set<MockWebSocketConnection> = new Set();
  private messageQueue: any[] = [];
  private isRunning = false;
  private stats = {
    messagesProcessed: 0,
    connectionsHandled: 0,
    errorsEncountered: 0,
    averageLatency: 0,
    peakMemoryUsage: 0,
    cpuUsage: 0
  };

  startServer() {
    this.isRunning = true;
    this.processMessageQueue();
  }

  stopServer() {
    this.isRunning = false;
    this.connections.clear();
    this.messageQueue = [];
  }

  createConnection(): MockWebSocketConnection {
    const connection = new MockWebSocketConnection(this);
    this.connections.add(connection);
    this.stats.connectionsHandled++;
    return connection;
  }

  removeConnection(connection: MockWebSocketConnection) {
    this.connections.delete(connection);
  }

  broadcast(message: any) {
    this.messageQueue.push({
      type: 'broadcast',
      message,
      timestamp: performance.now()
    });
  }

  sendToChannel(channel: string, message: any) {
    this.messageQueue.push({
      type: 'channel',
      channel,
      message,
      timestamp: performance.now()
    });
  }

  private processMessageQueue() {
    if (!this.isRunning) return;

    const batchSize = 100;
    const messagesToProcess = this.messageQueue.splice(0, batchSize);

    messagesToProcess.forEach(item => {
      const latency = performance.now() - item.timestamp;
      this.stats.averageLatency = (this.stats.averageLatency + latency) / 2;

      if (item.type === 'broadcast') {
        this.connections.forEach(conn => {
          try {
            conn.receive(item.message);
            this.stats.messagesProcessed++;
          } catch (error) {
            this.stats.errorsEncountered++;
          }
        });
      } else if (item.type === 'channel') {
        this.connections.forEach(conn => {
          if (conn.isSubscribedTo(item.channel)) {
            try {
              conn.receive(item.message);
              this.stats.messagesProcessed++;
            } catch (error) {
              this.stats.errorsEncountered++;
            }
          }
        });
      }
    });

    // Simulate processing time based on load
    const processingDelay = Math.min(50, this.connections.size / 100);
    setTimeout(() => this.processMessageQueue(), processingDelay);
  }

  getStats() {
    return {
      ...this.stats,
      activeConnections: this.connections.size,
      queuedMessages: this.messageQueue.length,
      errorRate: this.stats.errorsEncountered / Math.max(this.stats.messagesProcessed, 1),
      messagesPerSecond: this.stats.messagesProcessed / (performance.now() / 1000)
    };
  }
}

class MockWebSocketConnection {
  private server: MockWebSocketServer;
  private subscribedChannels: Set<string> = new Set();
  private messageHandlers: Map<WebSocketEventType, Function[]> = new Map();
  private isConnected = true;

  constructor(server: MockWebSocketServer) {
    this.server = server;
  }

  subscribe(channel: string) {
    this.subscribedChannels.add(channel);
  }

  unsubscribe(channel: string) {
    this.subscribedChannels.delete(channel);
  }

  isSubscribedTo(channel: string): boolean {
    return this.subscribedChannels.has(channel);
  }

  on(eventType: WebSocketEventType, handler: Function) {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, []);
    }
    this.messageHandlers.get(eventType)!.push(handler);
  }

  receive(message: any) {
    if (!this.isConnected) return;

    const handlers = this.messageHandlers.get(message.event_type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data, message);
        } catch (error) {
          console.error('Handler error:', error);
        }
      });
    }
  }

  disconnect() {
    this.isConnected = false;
    this.server.removeConnection(this);
  }
}

// Game simulation utilities
class GameSimulator {
  private gameId: string;
  private state: any;
  private server: MockWebSocketServer;
  private isRunning = false;
  private intervals: NodeJS.Timeout[] = [];

  constructor(gameId: string, teams: { home: string, away: string }, server: MockWebSocketServer) {
    this.gameId = gameId;
    this.server = server;
    this.state = {
      game_id: gameId,
      home_team: teams.home,
      away_team: teams.away,
      home_score: 0,
      away_score: 0,
      quarter: 1,
      time_remaining: '15:00',
      game_status: 'scheduled',
      updated_at: new Date().toISOString()
    };
  }

  start() {
    this.isRunning = true;
    this.scheduleUpdates();
  }

  stop() {
    this.isRunning = false;
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals = [];
  }

  private scheduleUpdates() {
    // Score updates (every 10-30 seconds)
    const scoreInterval = setInterval(() => {
      if (!this.isRunning) return;

      if (Math.random() < 0.3) { // 30% chance of score change
        const isHomeTeam = Math.random() < 0.5;
        const points = Math.random() < 0.7 ? 7 : 3; // 70% touchdowns, 30% field goals

        if (isHomeTeam) {
          this.state.home_score += points;
        } else {
          this.state.away_score += points;
        }

        this.state.updated_at = new Date().toISOString();

        this.server.sendToChannel(`game_${this.gameId}`, {
          event_type: WebSocketEventType.SCORE_UPDATE,
          data: { ...this.state },
          timestamp: new Date().toISOString()
        });

        // Trigger prediction update after score change
        this.updatePrediction();
      }
    }, 10000 + Math.random() * 20000); // 10-30 seconds

    this.intervals.push(scoreInterval);

    // Time updates (every 1-2 seconds)
    const timeInterval = setInterval(() => {
      if (!this.isRunning) return;

      this.updateGameTime();
    }, 1000 + Math.random() * 1000);

    this.intervals.push(timeInterval);

    // Odds updates (every 0.5-2 seconds)
    const oddsInterval = setInterval(() => {
      if (!this.isRunning) return;

      this.updateOdds();
    }, 500 + Math.random() * 1500);

    this.intervals.push(oddsInterval);
  }

  private updateGameTime() {
    const [minutes, seconds] = this.state.time_remaining.split(':').map(Number);
    let totalSeconds = minutes * 60 + seconds;

    totalSeconds -= Math.floor(Math.random() * 5) + 1; // 1-5 seconds

    if (totalSeconds <= 0) {
      if (this.state.quarter < 4) {
        this.state.quarter++;
        this.state.time_remaining = '15:00';
      } else {
        this.state.game_status = 'final';
        this.state.time_remaining = '00:00';
        this.stop();
      }
    } else {
      const newMinutes = Math.floor(totalSeconds / 60);
      const newSeconds = totalSeconds % 60;
      this.state.time_remaining = `${newMinutes.toString().padStart(2, '0')}:${newSeconds.toString().padStart(2, '0')}`;
    }

    if (this.state.quarter > 0 && this.state.game_status === 'scheduled') {
      this.state.game_status = 'live';
    }

    this.state.updated_at = new Date().toISOString();

    this.server.sendToChannel(`game_${this.gameId}`, {
      event_type: WebSocketEventType.GAME_UPDATE,
      data: { ...this.state },
      timestamp: new Date().toISOString()
    });
  }

  private updatePrediction() {
    const scoreDiff = this.state.home_score - this.state.away_score;
    const quarterProgress = (this.state.quarter - 1) / 4;

    const baseWinProb = 0.5 + (scoreDiff * 0.02);
    const timeAdjustment = quarterProgress * 0.3;

    const homeWinProb = Math.max(0.05, Math.min(0.95, baseWinProb + timeAdjustment));

    this.server.sendToChannel(`predictions_${this.gameId}`, {
      event_type: WebSocketEventType.PREDICTION_UPDATE,
      data: {
        game_id: this.gameId,
        home_team: this.state.home_team,
        away_team: this.state.away_team,
        home_win_probability: homeWinProb,
        away_win_probability: 1 - homeWinProb,
        predicted_spread: scoreDiff + (Math.random() - 0.5) * 4,
        confidence_level: 0.7 + quarterProgress * 0.2,
        model_version: '2.1.0',
        updated_at: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    });
  }

  private updateOdds() {
    const sportsbooks = ['DraftKings', 'FanDuel', 'BetMGM', 'Caesars'];
    const sportsbook = sportsbooks[Math.floor(Math.random() * sportsbooks.length)];

    const scoreDiff = this.state.home_score - this.state.away_score;
    const baseSpread = -scoreDiff + (Math.random() - 0.5) * 6;

    this.server.sendToChannel(`odds_${this.gameId}`, {
      event_type: WebSocketEventType.ODDS_UPDATE,
      data: {
        game_id: this.gameId,
        sportsbook,
        home_team: this.state.home_team,
        away_team: this.state.away_team,
        spread: baseSpread,
        moneyline_home: baseSpread > 0 ? 100 + (baseSpread * 20) : -100 - (Math.abs(baseSpread) * 20),
        moneyline_away: baseSpread < 0 ? 100 + (Math.abs(baseSpread) * 20) : -100 - (baseSpread * 20),
        over_under: 45 + Math.random() * 10,
        updated_at: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    });
  }

  getState() {
    return { ...this.state };
  }
}

// Performance monitoring utilities
class PerformanceMonitor {
  private startTime = 0;
  private metrics = {
    messagesReceived: 0,
    averageLatency: 0,
    maxLatency: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    errorCount: 0
  };

  start() {
    this.startTime = performance.now();
    this.resetMetrics();
  }

  stop() {
    return {
      ...this.metrics,
      duration: performance.now() - this.startTime,
      messagesPerSecond: this.metrics.messagesReceived / ((performance.now() - this.startTime) / 1000)
    };
  }

  recordMessage(latency: number) {
    this.metrics.messagesReceived++;
    this.metrics.averageLatency = (this.metrics.averageLatency + latency) / 2;
    this.metrics.maxLatency = Math.max(this.metrics.maxLatency, latency);
  }

  recordError() {
    this.metrics.errorCount++;
  }

  updateResourceUsage() {
    // Simulate memory and CPU usage tracking
    this.metrics.memoryUsage = (performance as any).memory?.usedJSHeapSize / (1024 * 1024) || 0;
    this.metrics.cpuUsage = Math.random() * 0.3 + 0.1; // Simulated CPU usage
  }

  private resetMetrics() {
    this.metrics = {
      messagesReceived: 0,
      averageLatency: 0,
      maxLatency: 0,
      memoryUsage: 0,
      cpuUsage: 0,
      errorCount: 0
    };
  }
}

describe('Load Testing for Multiple Simultaneous Live Games', () => {
  let server: MockWebSocketServer;
  let performanceMonitor: PerformanceMonitor;
  let gameSimulators: GameSimulator[] = [];

  beforeEach(() => {
    server = new MockWebSocketServer();
    performanceMonitor = new PerformanceMonitor();
    gameSimulators = [];

    // Mock performance APIs
    global.performance = {
      ...global.performance,
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn()
    };

    vi.useFakeTimers();
  });

  afterEach(() => {
    server.stopServer();
    gameSimulators.forEach(sim => sim.stop());
    gameSimulators = [];
    vi.clearAllMocks();
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  describe('Sunday Peak Load Simulation', () => {
    it('should handle 16 simultaneous NFL games with 1000 users each', async () => {
      server.startServer();
      performanceMonitor.start();

      // Create 16 games (typical Sunday afternoon)
      const teams = [
        ['Patriots', 'Bills'], ['Chiefs', 'Broncos'], ['Cowboys', 'Giants'], ['Packers', 'Bears'],
        ['Steelers', 'Ravens'], ['Saints', 'Falcons'], ['49ers', 'Rams'], ['Seahawks', 'Cardinals'],
        ['Dolphins', 'Jets'], ['Colts', 'Titans'], ['Browns', 'Bengals'], ['Lions', 'Vikings'],
        ['Eagles', 'Commanders'], ['Buccaneers', 'Panthers'], ['Chargers', 'Raiders'], ['Texans', 'Jaguars']
      ];

      // Start all game simulations
      teams.forEach((teamPair, index) => {
        const gameId = `nfl_game_${index + 1}`;
        const simulator = new GameSimulator(gameId, { home: teamPair[0], away: teamPair[1] }, server);
        gameSimulators.push(simulator);
        simulator.start();
      });

      // Simulate 1000 concurrent users per game
      const connections: MockWebSocketConnection[] = [];
      const totalUsers = LOAD_TEST_CONFIG.SUNDAY_PEAK_GAMES * LOAD_TEST_CONFIG.CONCURRENT_USERS_PER_GAME;

      for (let i = 0; i < totalUsers; i++) {
        const connection = server.createConnection();
        connections.push(connection);

        // Subscribe to random games
        const gameIndex = Math.floor(Math.random() * LOAD_TEST_CONFIG.SUNDAY_PEAK_GAMES);
        const gameId = `nfl_game_${gameIndex + 1}`;

        connection.subscribe(`game_${gameId}`);
        connection.subscribe(`predictions_${gameId}`);
        connection.subscribe(`odds_${gameId}`);

        // Set up message handlers
        connection.on(WebSocketEventType.SCORE_UPDATE, (data: any) => {
          const latency = performance.now() - new Date(data.updated_at).getTime();
          performanceMonitor.recordMessage(latency);
        });

        connection.on(WebSocketEventType.PREDICTION_UPDATE, (data: any) => {
          const latency = performance.now() - new Date(data.updated_at).getTime();
          performanceMonitor.recordMessage(latency);
        });
      }

      // Run simulation for 60 seconds
      await vi.advanceTimersByTimeAsync(60000);

      const results = performanceMonitor.stop();
      const serverStats = server.getStats();

      console.log('Sunday Peak Load Results:', {
        ...results,
        ...serverStats
      });

      // Performance assertions
      expect(results.averageLatency).toBeLessThan(LOAD_TEST_CONFIG.MAX_LATENCY_MS);
      expect(results.maxLatency).toBeLessThan(LOAD_TEST_CONFIG.MAX_LATENCY_MS * 2);
      expect(results.messagesPerSecond).toBeGreaterThan(100);
      expect(serverStats.errorRate).toBeLessThan(0.01); // Less than 1% error rate
      expect(serverStats.activeConnections).toBe(totalUsers);

      // Clean up connections
      connections.forEach(conn => conn.disconnect());
    });

    it('should maintain performance during score update bursts', async () => {
      server.startServer();
      performanceMonitor.start();

      // Create 8 games with high activity
      const activeGames = Array.from({ length: 8 }, (_, index) => {
        const gameId = `burst_game_${index}`;
        const simulator = new GameSimulator(gameId,
          { home: `Home${index}`, away: `Away${index}` }, server);
        gameSimulators.push(simulator);
        simulator.start();
        return { gameId, simulator };
      });

      // Create connections
      const connections: MockWebSocketConnection[] = [];
      for (let i = 0; i < 5000; i++) {
        const connection = server.createConnection();
        connections.push(connection);

        // Subscribe to all games
        activeGames.forEach(({ gameId }) => {
          connection.subscribe(`game_${gameId}`);
          connection.subscribe(`predictions_${gameId}`);
        });

        connection.on(WebSocketEventType.SCORE_UPDATE, (data: any) => {
          performanceMonitor.recordMessage(performance.now());
        });
      }

      // Simulate score update burst (all games score simultaneously)
      await vi.advanceTimersByTimeAsync(30000);

      const results = performanceMonitor.stop();
      const serverStats = server.getStats();

      console.log('Score Burst Results:', {
        ...results,
        ...serverStats
      });

      // Should handle burst without degradation
      expect(results.averageLatency).toBeLessThan(1000); // Allow higher latency during bursts
      expect(serverStats.errorRate).toBeLessThan(0.05); // Less than 5% error rate during burst
      expect(results.messagesPerSecond).toBeGreaterThan(50);

      connections.forEach(conn => conn.disconnect());
    });
  });

  describe('Memory and Resource Management', () => {
    it('should not leak memory during extended operation', async () => {
      server.startServer();

      // Create moderate load
      const games = Array.from({ length: 4 }, (_, index) => {
        const gameId = `memory_test_${index}`;
        const simulator = new GameSimulator(gameId,
          { home: `Home${index}`, away: `Away${index}` }, server);
        gameSimulators.push(simulator);
        simulator.start();
        return simulator;
      });

      const connections: MockWebSocketConnection[] = [];
      for (let i = 0; i < 1000; i++) {
        const connection = server.createConnection();
        connections.push(connection);

        games.forEach((_, gameIndex) => {
          connection.subscribe(`game_memory_test_${gameIndex}`);
        });
      }

      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;

      // Run for extended period
      await vi.advanceTimersByTimeAsync(300000); // 5 minutes

      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const memoryIncrease = (finalMemory - initialMemory) / (1024 * 1024); // MB

      console.log(`Memory increase: ${memoryIncrease}MB`);

      // Memory usage should not increase significantly
      expect(memoryIncrease).toBeLessThan(LOAD_TEST_CONFIG.MAX_MEMORY_MB);

      connections.forEach(conn => conn.disconnect());
    });

    it('should efficiently handle connection churn', async () => {
      server.startServer();
      performanceMonitor.start();

      // Create one game
      const gameId = 'churn_test';
      const simulator = new GameSimulator(gameId, { home: 'HomeTeam', away: 'AwayTeam' }, server);
      gameSimulators.push(simulator);
      simulator.start();

      // Simulate rapid connection/disconnection
      for (let cycle = 0; cycle < 10; cycle++) {
        const connections: MockWebSocketConnection[] = [];

        // Connect 1000 users
        for (let i = 0; i < 1000; i++) {
          const connection = server.createConnection();
          connection.subscribe(`game_${gameId}`);
          connections.push(connection);
        }

        await vi.advanceTimersByTimeAsync(5000);

        // Disconnect all users
        connections.forEach(conn => conn.disconnect());

        await vi.advanceTimersByTimeAsync(1000);
      }

      const results = performanceMonitor.stop();
      const serverStats = server.getStats();

      console.log('Connection Churn Results:', {
        ...results,
        ...serverStats
      });

      // Should handle connection churn efficiently
      expect(serverStats.errorRate).toBeLessThan(0.02);
      expect(serverStats.activeConnections).toBe(0); // All should be disconnected
    });
  });

  describe('Scalability Testing', () => {
    it('should scale to handle playoff weekend load', async () => {
      server.startServer();
      performanceMonitor.start();

      // Playoff weekend: 4 games with higher intensity
      const playoffGames = Array.from({ length: 4 }, (_, index) => {
        const gameId = `playoff_${index}`;
        const simulator = new GameSimulator(gameId,
          { home: `Playoff${index * 2}`, away: `Playoff${index * 2 + 1}` }, server);
        gameSimulators.push(simulator);
        simulator.start();
        return { gameId, simulator };
      });

      // Higher user concentration per game
      const connections: MockWebSocketConnection[] = [];
      const usersPerGame = 5000; // Higher than regular season

      playoffGames.forEach(({ gameId }) => {
        for (let i = 0; i < usersPerGame; i++) {
          const connection = server.createConnection();
          connections.push(connection);

          connection.subscribe(`game_${gameId}`);
          connection.subscribe(`predictions_${gameId}`);
          connection.subscribe(`odds_${gameId}`);

          connection.on(WebSocketEventType.SCORE_UPDATE, (data: any) => {
            performanceMonitor.recordMessage(performance.now());
          });

          connection.on(WebSocketEventType.PREDICTION_UPDATE, (data: any) => {
            performanceMonitor.recordMessage(performance.now());
          });
        }
      });

      // Run playoff simulation
      await vi.advanceTimersByTimeAsync(120000); // 2 minutes

      const results = performanceMonitor.stop();
      const serverStats = server.getStats();

      console.log('Playoff Weekend Results:', {
        totalUsers: connections.length,
        ...results,
        ...serverStats
      });

      // Higher performance requirements for playoffs
      expect(results.averageLatency).toBeLessThan(300);
      expect(serverStats.errorRate).toBeLessThan(0.005); // Higher reliability for playoffs
      expect(results.messagesPerSecond).toBeGreaterThan(200);
      expect(serverStats.activeConnections).toBe(usersPerGame * 4);

      connections.forEach(conn => conn.disconnect());
    });

    it('should handle Super Bowl load with global audience', async () => {
      server.startServer();
      performanceMonitor.start();

      // Single Super Bowl game
      const superbowlId = 'superbowl_2024';
      const simulator = new GameSimulator(superbowlId,
        { home: 'AFC_Champion', away: 'NFC_Champion' }, server);
      gameSimulators.push(simulator);
      simulator.start();

      // Massive concurrent user load
      const connections: MockWebSocketConnection[] = [];
      const superbowlUsers = 100000; // Peak Super Bowl viewership online

      for (let i = 0; i < superbowlUsers; i++) {
        const connection = server.createConnection();
        connections.push(connection);

        connection.subscribe(`game_${superbowlId}`);
        connection.subscribe(`predictions_${superbowlId}`);
        connection.subscribe(`odds_${superbowlId}`);

        // Simulate different user behaviors
        if (i % 100 === 0) { // 1% power users
          connection.on(WebSocketEventType.SCORE_UPDATE, (data: any) => {
            performanceMonitor.recordMessage(performance.now());
          });
          connection.on(WebSocketEventType.PREDICTION_UPDATE, (data: any) => {
            performanceMonitor.recordMessage(performance.now());
          });
          connection.on(WebSocketEventType.ODDS_UPDATE, (data: any) => {
            performanceMonitor.recordMessage(performance.now());
          });
        } else { // Regular users
          connection.on(WebSocketEventType.SCORE_UPDATE, (data: any) => {
            performanceMonitor.recordMessage(performance.now());
          });
        }
      }

      // Run Super Bowl simulation
      await vi.advanceTimersByTimeAsync(180000); // 3 minutes

      const results = performanceMonitor.stop();
      const serverStats = server.getStats();

      console.log('Super Bowl Results:', {
        totalUsers: connections.length,
        ...results,
        ...serverStats
      });

      // Super Bowl performance requirements
      expect(results.averageLatency).toBeLessThan(800); // Allow higher latency for extreme load
      expect(serverStats.errorRate).toBeLessThan(0.01);
      expect(results.messagesPerSecond).toBeGreaterThan(1000);
      expect(serverStats.activeConnections).toBe(superbowlUsers);

      // Memory should not exceed limits even with 100k users
      expect(results.memoryUsage).toBeLessThan(LOAD_TEST_CONFIG.MAX_MEMORY_MB * 2);

      connections.forEach(conn => conn.disconnect());
    });
  });

  describe('Failure Recovery and Reliability', () => {
    it('should maintain service during partial system failures', async () => {
      server.startServer();
      performanceMonitor.start();

      // Create normal load
      const games = Array.from({ length: 8 }, (_, index) => {
        const gameId = `resilience_${index}`;
        const simulator = new GameSimulator(gameId,
          { home: `Home${index}`, away: `Away${index}` }, server);
        gameSimulators.push(simulator);
        simulator.start();
        return { gameId, simulator };
      });

      const connections: MockWebSocketConnection[] = [];
      for (let i = 0; i < 10000; i++) {
        const connection = server.createConnection();
        connections.push(connection);

        games.forEach(({ gameId }) => {
          connection.subscribe(`game_${gameId}`);
        });

        connection.on(WebSocketEventType.SCORE_UPDATE, (data: any) => {
          performanceMonitor.recordMessage(performance.now());
        });
      }

      // Run normally for 30 seconds
      await vi.advanceTimersByTimeAsync(30000);

      // Simulate partial failure - stop half the games
      const failedGames = games.slice(0, 4);
      failedGames.forEach(({ simulator }) => simulator.stop());

      // Continue for 30 more seconds
      await vi.advanceTimersByTimeAsync(30000);

      // Restart failed games
      failedGames.forEach(({ simulator }) => simulator.start());

      // Run for another 30 seconds
      await vi.advanceTimersByTimeAsync(30000);

      const results = performanceMonitor.stop();
      const serverStats = server.getStats();

      console.log('Failure Recovery Results:', {
        ...results,
        ...serverStats
      });

      // Should maintain service during partial failures
      expect(serverStats.errorRate).toBeLessThan(0.15); // Allow higher error rate during failures
      expect(results.messagesPerSecond).toBeGreaterThan(25); // Reduced but functional
      expect(serverStats.activeConnections).toBe(10000); // Connections should remain

      connections.forEach(conn => conn.disconnect());
    });

    it('should meet uptime SLA requirements', async () => {
      server.startServer();

      let uptimeSeconds = 0;
      let totalSeconds = 0;
      const uptimeInterval = setInterval(() => {
        totalSeconds++;
        const serverStats = server.getStats();
        if (serverStats.errorRate < 0.05) { // Consider "up" if error rate < 5%
          uptimeSeconds++;
        }
      }, 1000);

      // Simulate long-running operation with occasional issues
      for (let hour = 0; hour < 24; hour++) {
        // Normal operation for most of the hour
        await vi.advanceTimersByTimeAsync(55 * 60 * 1000); // 55 minutes

        // Brief disruption
        if (hour % 6 === 0) { // Every 6 hours
          server.stopServer();
          await vi.advanceTimersByTimeAsync(2 * 60 * 1000); // 2 minutes downtime
          server.startServer();
          await vi.advanceTimersByTimeAsync(3 * 60 * 1000); // 3 minutes recovery
        } else {
          await vi.advanceTimersByTimeAsync(5 * 60 * 1000); // 5 minutes normal
        }
      }

      clearInterval(uptimeInterval);

      const uptime = uptimeSeconds / totalSeconds;
      console.log(`System uptime: ${(uptime * 100).toFixed(3)}%`);

      // Should meet 99.9% uptime SLA
      expect(uptime).toBeGreaterThan(LOAD_TEST_CONFIG.TARGET_UPTIME);
    });
  });
});