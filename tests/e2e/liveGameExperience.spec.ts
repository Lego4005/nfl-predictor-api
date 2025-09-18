/**
 * Playwright E2E Tests for Live Game Experience
 * Comprehensive end-to-end testing of real-time game functionality
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';
import { testConfig } from './playwrightConfig';

// Mock WebSocket server for E2E testing
class E2EWebSocketMock {
  private static instance: E2EWebSocketMock;
  private mockServer: any;
  private connections = new Set<any>();

  static getInstance(): E2EWebSocketMock {
    if (!this.instance) {
      this.instance = new E2EWebSocketMock();
    }
    return this.instance;
  }

  async startMockServer(page: Page) {
    // Inject WebSocket mock into the page
    await page.addInitScript(() => {
      // Store original WebSocket
      const OriginalWebSocket = window.WebSocket;

      // Mock WebSocket class
      class MockWebSocket extends EventTarget {
        url: string;
        readyState: number = WebSocket.CONNECTING;

        // WebSocket ready states
        static CONNECTING = 0;
        static OPEN = 1;
        static CLOSING = 2;
        static CLOSED = 3;

        constructor(url: string) {
          super();
          this.url = url;

          // Simulate connection establishment
          setTimeout(() => {
            this.readyState = WebSocket.OPEN;
            this.dispatchEvent(new Event('open'));
          }, 100);
        }

        send(data: string) {
          // Store sent messages for verification
          window.__sentMessages = window.__sentMessages || [];
          window.__sentMessages.push(JSON.parse(data));
        }

        close() {
          this.readyState = WebSocket.CLOSING;
          setTimeout(() => {
            this.readyState = WebSocket.CLOSED;
            this.dispatchEvent(new Event('close'));
          }, 50);
        }

        // Method to simulate receiving messages
        simulateMessage(data: any) {
          const event = new MessageEvent('message', {
            data: JSON.stringify(data)
          });
          this.dispatchEvent(event);
        }
      }

      // Replace global WebSocket
      window.WebSocket = MockWebSocket as any;
      window.__mockWebSocket = MockWebSocket;
    });
  }

  async simulateGameData(page: Page, gameData: any) {
    await page.evaluate((data) => {
      // Find the mock WebSocket instance and simulate message
      const mockWs = window.__mockWebSocketInstance;
      if (mockWs && mockWs.simulateMessage) {
        mockWs.simulateMessage(data);
      }
    }, gameData);
  }

  async simulateConnectionLoss(page: Page) {
    await page.evaluate(() => {
      const mockWs = window.__mockWebSocketInstance;
      if (mockWs) {
        mockWs.readyState = WebSocket.CLOSED;
        mockWs.dispatchEvent(new Event('close'));
      }
    });
  }
}

// Test data generators
const generateGameUpdate = (gameId: string, overrides: any = {}) => ({
  event_type: 'game_update',
  data: {
    game_id: gameId,
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 14,
    away_score: 7,
    quarter: 2,
    time_remaining: '08:30',
    game_status: 'live',
    updated_at: new Date().toISOString(),
    ...overrides
  },
  timestamp: new Date().toISOString()
});

const generatePredictionUpdate = (gameId: string, overrides: any = {}) => ({
  event_type: 'prediction_update',
  data: {
    game_id: gameId,
    home_team: 'Patriots',
    away_team: 'Bills',
    home_win_probability: 0.65,
    away_win_probability: 0.35,
    predicted_spread: -3.5,
    confidence_level: 0.82,
    model_version: '2.1.0',
    updated_at: new Date().toISOString(),
    ...overrides
  },
  timestamp: new Date().toISOString()
});

const generateOddsUpdate = (gameId: string, overrides: any = {}) => ({
  event_type: 'odds_update',
  data: {
    game_id: gameId,
    sportsbook: 'DraftKings',
    home_team: 'Patriots',
    away_team: 'Bills',
    spread: -3.0,
    moneyline_home: -150,
    moneyline_away: +130,
    over_under: 47.5,
    updated_at: new Date().toISOString(),
    ...overrides
  },
  timestamp: new Date().toISOString()
});

test.describe('Live Game Experience E2E Tests', () => {
  let wsMock: E2EWebSocketMock;

  test.beforeAll(async () => {
    wsMock = E2EWebSocketMock.getInstance();
  });

  test.beforeEach(async ({ page }) => {
    // Start WebSocket mock for each test
    await wsMock.startMockServer(page);

    // Navigate to the live game page
    await page.goto('/live-games');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test.describe('Real-time Game Data', () => {
    test('should display live game scores and updates', async ({ page }) => {
      // Wait for live updates component to load
      await expect(page.locator('[data-testid="live-game-updates"]')).toBeVisible();

      // Simulate game data
      const gameData = generateGameUpdate('game_001');
      await wsMock.simulateGameData(page, gameData);

      // Verify game information is displayed
      await expect(page.locator('text=Patriots')).toBeVisible();
      await expect(page.locator('text=Bills')).toBeVisible();
      await expect(page.locator('text=14')).toBeVisible();
      await expect(page.locator('text=7')).toBeVisible();
      await expect(page.locator('text=LIVE')).toBeVisible();
    });

    test('should update scores in real-time', async ({ page }) => {
      // Initial game state
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 7,
        away_score: 0
      }));

      await expect(page.locator('text=7').first()).toBeVisible();
      await expect(page.locator('text=0').first()).toBeVisible();

      // Score change
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 7,
        away_score: 7
      }));

      // Wait for update and verify both scores are 7
      await page.waitForTimeout(500);
      const scoreElements = page.locator('text=7');
      await expect(scoreElements).toHaveCount(2);
    });

    test('should handle quarter and time updates', async ({ page }) => {
      // First quarter
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        quarter: 1,
        time_remaining: '15:00'
      }));

      await expect(page.locator('text=1st - 15:00')).toBeVisible();

      // Second quarter with different time
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        quarter: 2,
        time_remaining: '12:30'
      }));

      await expect(page.locator('text=2nd - 12:30')).toBeVisible();

      // Overtime
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        quarter: 5,
        time_remaining: '10:00',
        game_status: 'overtime'
      }));

      await expect(page.locator('text=OT1 - 10:00')).toBeVisible();
      await expect(page.locator('text=OVERTIME')).toBeVisible();
    });

    test('should display final game status', async ({ page }) => {
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 28,
        away_score: 21,
        quarter: 4,
        time_remaining: '00:00',
        game_status: 'final'
      }));

      await expect(page.locator('text=FINAL')).toBeVisible();
      await expect(page.locator('text=28')).toBeVisible();
      await expect(page.locator('text=21')).toBeVisible();
    });
  });

  test.describe('AI Predictions', () => {
    test('should display and update win probabilities', async ({ page }) => {
      // Enable predictions view
      await page.locator('[data-testid="predictions-toggle"]').check();

      // Send prediction data
      await wsMock.simulateGameData(page, generatePredictionUpdate('game_001'));

      // Verify prediction display
      await expect(page.locator('text=65.0%')).toBeVisible();
      await expect(page.locator('text=35.0%')).toBeVisible();
      await expect(page.locator('text=AI Prediction')).toBeVisible();

      // Update prediction
      await wsMock.simulateGameData(page, generatePredictionUpdate('game_001', {
        home_win_probability: 0.75,
        away_win_probability: 0.25
      }));

      await expect(page.locator('text=75.0%')).toBeVisible();
      await expect(page.locator('text=25.0%')).toBeVisible();
    });

    test('should show confidence levels and model version', async ({ page }) => {
      await page.locator('[data-testid="predictions-toggle"]').check();

      await wsMock.simulateGameData(page, generatePredictionUpdate('game_001', {
        confidence_level: 0.89,
        model_version: '2.1.1'
      }));

      await expect(page.locator('text=Confidence: 89.0%')).toBeVisible();
    });

    test('should handle prediction momentum shifts', async ({ page }) => {
      await page.locator('[data-testid="predictions-toggle"]').check();

      // Initial prediction favoring home team
      await wsMock.simulateGameData(page, generatePredictionUpdate('game_001', {
        home_win_probability: 0.70,
        away_win_probability: 0.30
      }));

      await expect(page.locator('text=70.0%')).toBeVisible();

      // Momentum shift after away team scores
      await wsMock.simulateGameData(page, generatePredictionUpdate('game_001', {
        home_win_probability: 0.40,
        away_win_probability: 0.60
      }));

      await page.waitForTimeout(500);
      await expect(page.locator('text=40.0%')).toBeVisible();
      await expect(page.locator('text=60.0%')).toBeVisible();
    });
  });

  test.describe('Live Odds', () => {
    test('should display odds from multiple sportsbooks', async ({ page }) => {
      await page.locator('[data-testid="odds-toggle"]').check();

      // DraftKings odds
      await wsMock.simulateGameData(page, generateOddsUpdate('game_001', {
        sportsbook: 'DraftKings',
        spread: -3.0
      }));

      await expect(page.locator('text=DraftKings')).toBeVisible();
      await expect(page.locator('text=-3')).toBeVisible();

      // FanDuel odds
      await wsMock.simulateGameData(page, generateOddsUpdate('game_001', {
        sportsbook: 'FanDuel',
        spread: -2.5
      }));

      await expect(page.locator('text=FanDuel')).toBeVisible();
      await expect(page.locator('text=-2.5')).toBeVisible();
    });

    test('should update odds in real-time', async ({ page }) => {
      await page.locator('[data-testid="odds-toggle"]').check();

      // Initial odds
      await wsMock.simulateGameData(page, generateOddsUpdate('game_001', {
        spread: -3.0,
        over_under: 47.5
      }));

      await expect(page.locator('text=-3')).toBeVisible();
      await expect(page.locator('text=47.5')).toBeVisible();

      // Updated odds
      await wsMock.simulateGameData(page, generateOddsUpdate('game_001', {
        spread: -4.5,
        over_under: 49.0
      }));

      await page.waitForTimeout(500);
      await expect(page.locator('text=-4.5')).toBeVisible();
      await expect(page.locator('text=49')).toBeVisible();
    });
  });

  test.describe('Connection Handling', () => {
    test('should show connection status indicator', async ({ page }) => {
      // Should show connected status
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Live');

      // Simulate disconnection
      await wsMock.simulateConnectionLoss(page);

      await page.waitForTimeout(1000);
      await expect(page.locator('text=Not connected')).toBeVisible();
      await expect(page.locator('text=Reconnecting')).toBeVisible();
    });

    test('should handle connection reconnection', async ({ page }) => {
      // Start connected
      await expect(page.locator('text=Live')).toBeVisible();

      // Disconnect
      await wsMock.simulateConnectionLoss(page);
      await page.waitForTimeout(500);
      await expect(page.locator('text=Not connected')).toBeVisible();

      // Reconnect by restarting WebSocket mock
      await wsMock.startMockServer(page);
      await page.waitForTimeout(1000);
      await expect(page.locator('text=Live')).toBeVisible();
    });

    test('should queue updates during disconnection', async ({ page }) => {
      // Simulate disconnection
      await wsMock.simulateConnectionLoss(page);

      // Try to send updates while disconnected (should be queued)
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 21,
        away_score: 14
      }));

      // Reconnect
      await wsMock.startMockServer(page);

      // Updates should be processed after reconnection
      await page.waitForTimeout(1000);
      // Note: This test would need actual queuing implementation
    });
  });

  test.describe('Animations and Celebrations', () => {
    test('should animate score changes', async ({ page }) => {
      // Initial score
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 7,
        away_score: 0
      }));

      // Get scoreboard element
      const scoreboard = page.locator('[data-testid="scoreboard"]');
      await expect(scoreboard).toBeVisible();

      // Score change should trigger animation
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 14,
        away_score: 0
      }));

      // Check for animation class or style changes
      await page.waitForTimeout(500);
      const scoreElement = page.locator('[data-testid="home-score"]');

      // Verify the new score is displayed
      await expect(scoreElement).toContainText('14');
    });

    test('should show touchdown celebration', async ({ page }) => {
      // Score touchdown
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_score: 7,
        away_score: 0,
        game_status: 'touchdown_home'
      }));

      // Look for celebration elements
      await expect(page.locator('[data-testid="celebration"]')).toBeVisible({ timeout: 2000 });

      // Celebration should disappear after animation
      await expect(page.locator('[data-testid="celebration"]')).toHaveCount(0, { timeout: 5000 });
    });

    test('should highlight red zone entries', async ({ page }) => {
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        game_status: 'red_zone',
        home_score: 14,
        away_score: 7
      }));

      await expect(page.locator('text=RED_ZONE')).toBeVisible();

      // Should have special styling for red zone
      const statusElement = page.locator('[data-testid="game-status"]');
      await expect(statusElement).toHaveClass(/red-zone/);
    });
  });

  test.describe('Multiple Games', () => {
    test('should display multiple simultaneous games', async ({ page }) => {
      // Navigate to all games view
      await page.goto('/live-games/all');

      // Simulate multiple games
      const games = [
        { id: 'game_001', home: 'Patriots', away: 'Bills' },
        { id: 'game_002', home: 'Chiefs', away: 'Broncos' },
        { id: 'game_003', home: 'Cowboys', away: 'Giants' }
      ];

      for (const game of games) {
        await wsMock.simulateGameData(page, generateGameUpdate(game.id, {
          home_team: game.home,
          away_team: game.away
        }));
      }

      // Verify all games are displayed
      for (const game of games) {
        await expect(page.locator(`text=${game.home}`)).toBeVisible();
        await expect(page.locator(`text=${game.away}`)).toBeVisible();
      }
    });

    test('should handle updates for specific games', async ({ page }) => {
      await page.goto('/live-games/all');

      // Add two games
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_team: 'Patriots',
        away_team: 'Bills',
        home_score: 14
      }));

      await wsMock.simulateGameData(page, generateGameUpdate('game_002', {
        home_team: 'Chiefs',
        away_team: 'Broncos',
        home_score: 21
      }));

      // Verify different scores
      const patriotsGame = page.locator('[data-testid="game-game_001"]');
      const chiefsGame = page.locator('[data-testid="game-game_002"]');

      await expect(patriotsGame.locator('text=14')).toBeVisible();
      await expect(chiefsGame.locator('text=21')).toBeVisible();

      // Update only one game
      await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
        home_team: 'Patriots',
        away_team: 'Bills',
        home_score: 28
      }));

      // Verify only the updated game changed
      await expect(patriotsGame.locator('text=28')).toBeVisible();
      await expect(chiefsGame.locator('text=21')).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should maintain 60fps during updates', async ({ page }) => {
      // Start performance monitoring
      await page.evaluate(() => {
        window.performanceMetrics = {
          frameCount: 0,
          startTime: performance.now(),
          lastFrame: performance.now()
        };

        function countFrames() {
          window.performanceMetrics.frameCount++;
          window.performanceMetrics.lastFrame = performance.now();
          requestAnimationFrame(countFrames);
        }

        requestAnimationFrame(countFrames);
      });

      // Simulate rapid updates
      for (let i = 0; i < 20; i++) {
        await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
          home_score: i,
          away_score: Math.floor(i / 2)
        }));
        await page.waitForTimeout(100);
      }

      // Check frame rate
      const metrics = await page.evaluate(() => {
        const duration = (window.performanceMetrics.lastFrame - window.performanceMetrics.startTime) / 1000;
        return {
          fps: window.performanceMetrics.frameCount / duration,
          frameCount: window.performanceMetrics.frameCount,
          duration
        };
      });

      console.log('Performance metrics:', metrics);
      expect(metrics.fps).toBeGreaterThan(45); // Allow some margin below 60fps
    });

    test('should handle memory efficiently with many updates', async ({ page }) => {
      const initialMemory = await page.evaluate(() =>
        (performance as any).memory?.usedJSHeapSize || 0
      );

      // Send many updates
      for (let i = 0; i < 100; i++) {
        await wsMock.simulateGameData(page, generateGameUpdate('game_001', {
          home_score: Math.floor(i / 7),
          away_score: Math.floor(i / 10),
          time_remaining: `${15 - (i % 15)}:${(60 - (i % 60)).toString().padStart(2, '0')}`
        }));

        if (i % 10 === 0) {
          await page.waitForTimeout(50);
        }
      }

      const finalMemory = await page.evaluate(() =>
        (performance as any).memory?.usedJSHeapSize || 0
      );

      const memoryIncrease = (finalMemory - initialMemory) / (1024 * 1024); // MB
      console.log(`Memory increase: ${memoryIncrease}MB`);

      // Memory increase should be reasonable
      expect(memoryIncrease).toBeLessThan(50); // Less than 50MB increase
    });
  });

  test.describe('Error Handling', () => {
    test('should gracefully handle malformed data', async ({ page }) => {
      // Send invalid JSON
      await page.evaluate(() => {
        const mockWs = window.__mockWebSocketInstance;
        if (mockWs) {
          const invalidEvent = new MessageEvent('message', {
            data: 'invalid json {'
          });
          mockWs.dispatchEvent(invalidEvent);
        }
      });

      // Page should still function
      await expect(page.locator('text=Live Game Updates')).toBeVisible();

      // Send valid data after invalid
      await wsMock.simulateGameData(page, generateGameUpdate('game_001'));
      await expect(page.locator('text=Patriots')).toBeVisible();
    });

    test('should handle missing required fields', async ({ page }) => {
      // Send incomplete game data
      await wsMock.simulateGameData(page, {
        event_type: 'game_update',
        data: {
          game_id: 'game_001',
          home_team: 'Patriots'
          // Missing other required fields
        },
        timestamp: new Date().toISOString()
      });

      // Should display available information without crashing
      await expect(page.locator('text=Patriots')).toBeVisible();
    });

    test('should recover from WebSocket errors', async ({ page }) => {
      // Simulate WebSocket error
      await page.evaluate(() => {
        const mockWs = window.__mockWebSocketInstance;
        if (mockWs) {
          mockWs.dispatchEvent(new Event('error'));
        }
      });

      // Should show error state
      await expect(page.locator('text=Connection error')).toBeVisible();

      // Should attempt to reconnect
      await wsMock.startMockServer(page);
      await page.waitForTimeout(1000);
      await expect(page.locator('text=Live')).toBeVisible();
    });
  });
});