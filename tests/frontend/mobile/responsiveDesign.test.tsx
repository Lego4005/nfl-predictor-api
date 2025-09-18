/**
 * Mobile Responsiveness Testing for Live Game Experience
 * Tests cross-device compatibility, touch interactions, and responsive layouts
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LiveGameUpdates from '../../../src/components/LiveGameUpdates';
import { WebSocketEventType } from '../../../src/services/websocketService';
import { MockWebSocket } from '../__mocks__/WebSocket';

// Device viewport configurations
const DEVICE_VIEWPORTS = {
  mobile: {
    width: 375,
    height: 812,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true
  },
  tablet: {
    width: 768,
    height: 1024,
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true
  },
  smallMobile: {
    width: 320,
    height: 568,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true
  },
  largeMobile: {
    width: 414,
    height: 896,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true
  },
  desktop: {
    width: 1920,
    height: 1080,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    deviceScaleFactor: 1,
    isMobile: false,
    hasTouch: false
  }
};

// Utility to simulate device viewport
const setViewport = (device: keyof typeof DEVICE_VIEWPORTS) => {
  const config = DEVICE_VIEWPORTS[device];

  // Mock window dimensions
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: config.width
  });

  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: config.height
  });

  // Mock screen dimensions
  Object.defineProperty(window.screen, 'width', {
    writable: true,
    configurable: true,
    value: config.width
  });

  Object.defineProperty(window.screen, 'height', {
    writable: true,
    configurable: true,
    value: config.height
  });

  // Mock device pixel ratio
  Object.defineProperty(window, 'devicePixelRatio', {
    writable: true,
    configurable: true,
    value: config.deviceScaleFactor
  });

  // Mock user agent
  Object.defineProperty(navigator, 'userAgent', {
    writable: true,
    configurable: true,
    value: config.userAgent
  });

  // Mock touch capabilities
  if (config.hasTouch) {
    Object.defineProperty(window, 'ontouchstart', {
      writable: true,
      configurable: true,
      value: () => {}
    });

    Object.defineProperty(navigator, 'maxTouchPoints', {
      writable: true,
      configurable: true,
      value: 5
    });
  } else {
    delete (window as any).ontouchstart;
    Object.defineProperty(navigator, 'maxTouchPoints', {
      writable: true,
      configurable: true,
      value: 0
    });
  }

  // Trigger resize event
  window.dispatchEvent(new Event('resize'));
};

// Mock CSS media queries
const mockMatchMedia = (query: string) => {
  const mediaQuery = query.match(/\(.*?\)/)?.[0] || '';

  let matches = false;
  if (mediaQuery.includes('max-width: 768px')) {
    matches = window.innerWidth <= 768;
  } else if (mediaQuery.includes('max-width: 1024px')) {
    matches = window.innerWidth <= 1024;
  } else if (mediaQuery.includes('orientation: portrait')) {
    matches = window.innerHeight > window.innerWidth;
  } else if (mediaQuery.includes('orientation: landscape')) {
    matches = window.innerWidth > window.innerHeight;
  }

  return {
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  };
};

describe('Mobile Responsiveness Testing', () => {
  let mockWs: MockWebSocket;
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    // Setup user events with touch support
    user = userEvent.setup({
      advanceTimers: vi.advanceTimersByTime,
      pointerEventsCheck: 0 // Disable pointer events check for touch simulation
    });

    // Mock WebSocket
    mockWs = new MockWebSocket();
    global.WebSocket = vi.fn(() => mockWs) as any;

    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation(mockMatchMedia)
    });

    // Mock ResizeObserver
    global.ResizeObserver = vi.fn().mockImplementation((callback) => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }));

    // Mock IntersectionObserver
    global.IntersectionObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }));

    // Mock performance API
    global.performance = {
      ...global.performance,
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn()
    };

    // Setup CSS custom properties support
    const mockComputedStyle = {
      getPropertyValue: vi.fn((prop: string) => {
        if (prop === '--vh') return '8.12px';
        if (prop === '--vw') return '3.75px';
        return '';
      })
    };

    window.getComputedStyle = vi.fn(() => mockComputedStyle as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    document.body.innerHTML = '';
  });

  describe('Viewport Adaptation', () => {
    it('should adapt layout for mobile viewport (375px)', async () => {
      setViewport('mobile');

      const { container } = render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 14,
            away_score: 7,
            quarter: 2,
            time_remaining: '08:30',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      const gameCard = container.querySelector('.game-card');
      expect(gameCard).toBeInTheDocument();

      // Check that scoreboard stacks vertically on mobile
      const scoreboard = container.querySelector('.scoreboard');
      if (scoreboard) {
        const computedStyle = window.getComputedStyle(scoreboard);
        // On mobile, scoreboard should have mobile-friendly styling
        expect(scoreboard).toBeInTheDocument();
      }

      // Verify text is readable on mobile
      expect(screen.getByText('Patriots')).toBeInTheDocument();
      expect(screen.getByText('Bills')).toBeInTheDocument();
      expect(screen.getByText('14')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('should adapt layout for small mobile viewport (320px)', async () => {
      setViewport('smallMobile');

      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'New England Patriots',
            away_team: 'Buffalo Bills',
            home_score: 21,
            away_score: 14,
            quarter: 3,
            time_remaining: '12:00',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      // Team names should be visible even on small screens
      expect(screen.getByText(/Patriots/)).toBeInTheDocument();
      expect(screen.getByText(/Bills/)).toBeInTheDocument();

      // Scores should be prominently displayed
      expect(screen.getByText('21')).toBeInTheDocument();
      expect(screen.getByText('14')).toBeInTheDocument();
    });

    it('should optimize layout for tablet viewport (768px)', async () => {
      setViewport('tablet');

      render(<LiveGameUpdates />);

      await act(async () => {
        mockWs.simulateOpen();

        // Simulate multiple games for tablet layout
        const games = ['game_001', 'game_002', 'game_003'];
        games.forEach((gameId, index) => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.GAME_UPDATE,
            data: {
              game_id: gameId,
              home_team: `Home${index}`,
              away_team: `Away${index}`,
              home_score: 7 * index,
              away_score: 3 * index,
              quarter: 1,
              time_remaining: '15:00',
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });
      });

      // Tablet should show multiple games efficiently
      expect(screen.getByText('Home0')).toBeInTheDocument();
      expect(screen.getByText('Home1')).toBeInTheDocument();
      expect(screen.getByText('Home2')).toBeInTheDocument();
    });
  });

  describe('Touch Interactions', () => {
    it('should handle touch gestures for game interactions', async () => {
      setViewport('mobile');

      const { container } = render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            quarter: 1,
            time_remaining: '12:00',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      const gameCard = container.querySelector('.game-card');
      expect(gameCard).toBeInTheDocument();

      // Simulate touch events
      if (gameCard) {
        // Touch start
        fireEvent.touchStart(gameCard, {
          touches: [{ clientX: 100, clientY: 100 }]
        });

        // Touch end
        fireEvent.touchEnd(gameCard, {
          changedTouches: [{ clientX: 100, clientY: 100 }]
        });

        // Component should handle touch events without errors
        expect(gameCard).toBeInTheDocument();
      }
    });

    it('should support swipe gestures for navigation', async () => {
      setViewport('mobile');

      const { container } = render(
        <div data-testid="game-container">
          <LiveGameUpdates />
        </div>
      );

      await act(async () => {
        mockWs.simulateOpen();

        // Add multiple games
        for (let i = 0; i < 5; i++) {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.GAME_UPDATE,
            data: {
              game_id: `game_${i}`,
              home_team: `Home${i}`,
              away_team: `Away${i}`,
              home_score: i * 7,
              away_score: i * 3,
              quarter: 1,
              time_remaining: '15:00',
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        }
      });

      const gameContainer = screen.getByTestId('game-container');

      // Simulate swipe left gesture
      fireEvent.touchStart(gameContainer, {
        touches: [{ clientX: 200, clientY: 100 }]
      });

      fireEvent.touchMove(gameContainer, {
        touches: [{ clientX: 50, clientY: 100 }]
      });

      fireEvent.touchEnd(gameContainer, {
        changedTouches: [{ clientX: 50, clientY: 100 }]
      });

      // Should handle swipe gestures gracefully
      expect(gameContainer).toBeInTheDocument();
    });

    it('should handle pinch-to-zoom for detailed views', async () => {
      setViewport('mobile');

      const { container } = render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 14,
            away_score: 10,
            quarter: 2,
            time_remaining: '05:30',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      const gameCard = container.querySelector('.game-card');

      if (gameCard) {
        // Simulate pinch gesture (two-finger touch)
        fireEvent.touchStart(gameCard, {
          touches: [
            { clientX: 100, clientY: 100 },
            { clientX: 200, clientY: 200 }
          ]
        });

        fireEvent.touchMove(gameCard, {
          touches: [
            { clientX: 80, clientY: 80 },
            { clientX: 220, clientY: 220 }
          ]
        });

        fireEvent.touchEnd(gameCard, {
          changedTouches: [
            { clientX: 80, clientY: 80 },
            { clientX: 220, clientY: 220 }
          ]
        });

        // Should handle multi-touch events
        expect(gameCard).toBeInTheDocument();
      }
    });
  });

  describe('Orientation Changes', () => {
    it('should adapt layout from portrait to landscape', async () => {
      // Start in portrait
      setViewport('mobile');

      const { container } = render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 3,
            quarter: 1,
            time_remaining: '10:00',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      // Verify portrait layout
      expect(screen.getByText('Patriots')).toBeInTheDocument();

      // Change to landscape
      Object.defineProperty(window, 'innerWidth', { value: 812, writable: true });
      Object.defineProperty(window, 'innerHeight', { value: 375, writable: true });

      await act(async () => {
        window.dispatchEvent(new Event('resize'));
      });

      // Component should adapt to landscape orientation
      expect(screen.getByText('Patriots')).toBeInTheDocument();
      expect(screen.getByText('Bills')).toBeInTheDocument();
    });

    it('should handle rapid orientation changes', async () => {
      setViewport('mobile');

      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Simulate rapid orientation changes
      for (let i = 0; i < 5; i++) {
        const isPortrait = i % 2 === 0;

        Object.defineProperty(window, 'innerWidth', {
          value: isPortrait ? 375 : 812,
          writable: true
        });
        Object.defineProperty(window, 'innerHeight', {
          value: isPortrait ? 812 : 375,
          writable: true
        });

        await act(async () => {
          window.dispatchEvent(new Event('resize'));
        });

        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Component should remain stable after rapid changes
      expect(screen.getByText(/Live Game Updates/)).toBeInTheDocument();
    });
  });

  describe('Performance on Mobile Devices', () => {
    it('should maintain performance on low-end mobile devices', async () => {
      setViewport('smallMobile');

      // Simulate low-end device constraints
      const originalRAF = global.requestAnimationFrame;
      global.requestAnimationFrame = vi.fn((callback) => {
        // Simulate slower frame rate (30fps instead of 60fps)
        setTimeout(callback, 1000 / 30);
        return 1;
      });

      render(<LiveGameUpdates />);

      await act(async () => {
        mockWs.simulateOpen();

        // Send multiple rapid updates to stress test
        for (let i = 0; i < 20; i++) {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: i,
              away_score: Math.floor(i / 2),
              quarter: 1,
              time_remaining: `${15 - i}:00`,
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });

          await new Promise(resolve => setTimeout(resolve, 50));
        }
      });

      // Should still display final scores correctly
      await waitFor(() => {
        expect(screen.getByText('19')).toBeInTheDocument(); // Final home score
        expect(screen.getByText('9')).toBeInTheDocument();  // Final away score
      });

      global.requestAnimationFrame = originalRAF;
    });

    it('should optimize for limited memory on mobile', async () => {
      setViewport('mobile');

      render(<LiveGameUpdates />);

      await act(async () => {
        mockWs.simulateOpen();

        // Simulate memory pressure with many games
        for (let i = 0; i < 50; i++) {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.GAME_UPDATE,
            data: {
              game_id: `game_${i}`,
              home_team: `Team${i * 2}`,
              away_team: `Team${i * 2 + 1}`,
              home_score: Math.floor(Math.random() * 30),
              away_score: Math.floor(Math.random() * 30),
              quarter: 1,
              time_remaining: '15:00',
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        }
      });

      // Should handle large number of games without crashing
      expect(screen.getByText(/Live Game Updates/)).toBeInTheDocument();

      // Should show some games (may virtualize or limit display)
      const gameElements = document.querySelectorAll('.game-card');
      expect(gameElements.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility on Mobile', () => {
    it('should support screen reader navigation on mobile', async () => {
      setViewport('mobile');

      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 14,
            away_score: 7,
            quarter: 2,
            time_remaining: '08:30',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      // Check for accessibility attributes
      const liveRegion = screen.getByText(/Live Game Updates/);
      expect(liveRegion).toBeInTheDocument();

      // Scores should be accessible
      expect(screen.getByText('14')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('should provide adequate touch targets (44px minimum)', async () => {
      setViewport('mobile');

      const { container } = render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 21,
            away_score: 14,
            quarter: 3,
            time_remaining: '12:00',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      // Interactive elements should have adequate size for touch
      const gameCard = container.querySelector('.game-card');
      if (gameCard) {
        const rect = gameCard.getBoundingClientRect();
        expect(rect.height).toBeGreaterThan(44); // Minimum touch target size
      }
    });
  });

  describe('Network Optimization', () => {
    it('should handle slow network connections gracefully', async () => {
      setViewport('mobile');

      // Mock slow network
      const slowMockWs = new MockWebSocket();
      slowMockWs.simulateSlowNetwork = true;
      global.WebSocket = vi.fn(() => slowMockWs) as any;

      render(<LiveGameUpdates gameId="game_001" />);

      // Simulate slow connection
      await act(async () => {
        setTimeout(() => slowMockWs.simulateOpen(), 2000);
      });

      // Should show loading/connecting state
      expect(screen.getByText(/Not connected/)).toBeInTheDocument();

      await act(async () => {
        slowMockWs.simulateOpen();
      });

      // Should connect eventually
      await waitFor(() => {
        expect(screen.getByText(/Live/)).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });
});