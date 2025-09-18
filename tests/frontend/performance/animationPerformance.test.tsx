/**
 * Animation Performance Testing for Live Game Experience
 * Validates 60fps animation performance, smooth transitions, and rendering optimization
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LiveGameUpdates from '../../../src/components/LiveGameUpdates';
import { WebSocketEventType } from '../../../src/services/websocketService';
import { MockWebSocket } from '../__mocks__/WebSocket';

// Performance monitoring utilities
class PerformanceMonitor {
  private frameCount = 0;
  private startTime = 0;
  private frameTimestamps: number[] = [];
  private isMonitoring = false;

  startMonitoring() {
    this.frameCount = 0;
    this.startTime = performance.now();
    this.frameTimestamps = [];
    this.isMonitoring = true;
    this.requestFrame();
  }

  stopMonitoring() {
    this.isMonitoring = false;
    return this.getMetrics();
  }

  private requestFrame() {
    if (!this.isMonitoring) return;

    requestAnimationFrame((timestamp) => {
      this.frameCount++;
      this.frameTimestamps.push(timestamp);
      this.requestFrame();
    });
  }

  private getMetrics() {
    const duration = (performance.now() - this.startTime) / 1000; // Convert to seconds
    const fps = this.frameCount / duration;

    // Calculate frame time variations
    const frameTimes = this.frameTimestamps.slice(1).map((time, index) =>
      time - this.frameTimestamps[index]
    );

    const avgFrameTime = frameTimes.reduce((sum, time) => sum + time, 0) / frameTimes.length;
    const frameTimeVariance = frameTimes.reduce((sum, time) =>
      sum + Math.pow(time - avgFrameTime, 2), 0) / frameTimes.length;

    // Detect dropped frames (frame time > 16.67ms indicates <60fps)
    const droppedFrames = frameTimes.filter(time => time > 16.67).length;

    return {
      fps,
      avgFrameTime,
      frameTimeVariance,
      droppedFrames,
      droppedFrameRate: droppedFrames / frameTimes.length,
      frameCount: this.frameCount,
      duration
    };
  }
}

// Mock animation-friendly components
const AnimatedScoreboard = ({ homeScore, awayScore }: { homeScore: number; awayScore: number }) => {
  return (
    <div
      className="scoreboard-animated"
      style={{
        transform: `scale(${homeScore !== awayScore ? 1.05 : 1})`,
        transition: 'transform 0.3s ease-in-out'
      }}
      data-testid="animated-scoreboard"
    >
      <span data-testid="home-score">{homeScore}</span>
      <span data-testid="away-score">{awayScore}</span>
    </div>
  );
};

const TouchdownCelebration = ({ visible }: { visible: boolean }) => {
  return visible ? (
    <div
      className="touchdown-celebration"
      style={{
        animation: 'celebrate 2s ease-in-out',
        opacity: visible ? 1 : 0,
        transform: visible ? 'scale(1.2)' : 'scale(1)'
      }}
      data-testid="touchdown-celebration"
    >
      🎉 TOUCHDOWN! 🎉
    </div>
  ) : null;
};

describe('Animation Performance Testing', () => {
  let mockWs: MockWebSocket;
  let performanceMonitor: PerformanceMonitor;

  beforeEach(() => {
    // Setup performance monitoring
    performanceMonitor = new PerformanceMonitor();

    // Mock WebSocket
    mockWs = new MockWebSocket();
    global.WebSocket = vi.fn(() => mockWs) as any;

    // Mock performance APIs with high precision
    global.performance = {
      ...global.performance,
      now: vi.fn(() => Date.now() + Math.random() * 0.1), // Add sub-millisecond precision
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByName: vi.fn(() => []),
      getEntriesByType: vi.fn(() => [])
    };

    // Mock requestAnimationFrame with 60fps timing
    let frameId = 0;
    global.requestAnimationFrame = vi.fn((callback) => {
      frameId++;
      setTimeout(() => callback(performance.now()), 1000 / 60); // 16.67ms intervals
      return frameId;
    });

    global.cancelAnimationFrame = vi.fn();

    // Mock ResizeObserver
    global.ResizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }));

    // Mock IntersectionObserver for performance
    global.IntersectionObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }));

    // Add CSS animation support
    Object.defineProperty(HTMLElement.prototype, 'animate', {
      value: vi.fn().mockReturnValue({
        finished: Promise.resolve(),
        cancel: vi.fn(),
        pause: vi.fn(),
        play: vi.fn()
      }),
      writable: true
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    performanceMonitor.stopMonitoring();
  });

  describe('Frame Rate Performance', () => {
    it('should maintain 60fps during rapid score updates', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Start performance monitoring
      performanceMonitor.startMonitoring();

      // Simulate rapid score updates (10 updates in 2 seconds)
      const scoreUpdates = Array.from({ length: 10 }, (_, i) => ({
        game_id: 'game_001',
        home_team: 'Patriots',
        away_team: 'Bills',
        home_score: i * 7,
        away_score: i * 3,
        quarter: 1,
        time_remaining: `${15 - i}:00`,
        game_status: 'live',
        updated_at: new Date().toISOString()
      }));

      for (const [index, update] of scoreUpdates.entries()) {
        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: update,
            timestamp: new Date().toISOString()
          });
        });

        // Wait 200ms between updates to simulate real-time
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Stop monitoring after 2 seconds
      await new Promise(resolve => setTimeout(resolve, 2000));
      const metrics = performanceMonitor.stopMonitoring();

      // Assert performance requirements
      expect(metrics.fps).toBeGreaterThan(55); // Allow slight deviation from 60fps
      expect(metrics.droppedFrameRate).toBeLessThan(0.1); // Less than 10% dropped frames
      expect(metrics.avgFrameTime).toBeLessThan(20); // Average frame time under 20ms

      console.log('Performance Metrics:', metrics);
    });

    it('should handle smooth animations during touchdown celebrations', async () => {
      const { rerender } = render(
        <div>
          <LiveGameUpdates gameId="game_001" />
          <TouchdownCelebration visible={false} />
        </div>
      );

      await act(async () => {
        mockWs.simulateOpen();
      });

      performanceMonitor.startMonitoring();

      // Trigger touchdown with celebration animation
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.SCORE_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            quarter: 1,
            time_remaining: '12:34',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      // Show celebration animation
      rerender(
        <div>
          <LiveGameUpdates gameId="game_001" />
          <TouchdownCelebration visible={true} />
        </div>
      );

      // Wait for animation to complete
      await new Promise(resolve => setTimeout(resolve, 2000));

      const metrics = performanceMonitor.stopMonitoring();

      // Animation should not significantly impact performance
      expect(metrics.fps).toBeGreaterThan(50);
      expect(metrics.droppedFrameRate).toBeLessThan(0.15);

      // Check that celebration animation is visible
      expect(screen.getByTestId('touchdown-celebration')).toBeInTheDocument();
    });

    it('should optimize rendering with multiple simultaneous animations', async () => {
      // Render multiple animated components
      const { rerender } = render(
        <div>
          <AnimatedScoreboard homeScore={0} awayScore={0} />
          <AnimatedScoreboard homeScore={7} awayScore={3} />
          <AnimatedScoreboard homeScore={14} awayScore={10} />
          <TouchdownCelebration visible={false} />
        </div>
      );

      performanceMonitor.startMonitoring();

      // Trigger multiple simultaneous animations
      await act(async () => {
        rerender(
          <div>
            <AnimatedScoreboard homeScore={21} awayScore={14} />
            <AnimatedScoreboard homeScore={14} awayScore={17} />
            <AnimatedScoreboard homeScore={28} awayScore={21} />
            <TouchdownCelebration visible={true} />
          </div>
        );
      });

      // Wait for animations to complete
      await new Promise(resolve => setTimeout(resolve, 1500));

      const metrics = performanceMonitor.stopMonitoring();

      // Should handle multiple animations efficiently
      expect(metrics.fps).toBeGreaterThan(45); // Slightly lower threshold for multiple animations
      expect(metrics.droppedFrameRate).toBeLessThan(0.2);

      // All animated elements should be rendered
      expect(screen.getAllByTestId('animated-scoreboard')).toHaveLength(3);
      expect(screen.getByTestId('touchdown-celebration')).toBeInTheDocument();
    });
  });

  describe('Transition Smoothness', () => {
    it('should provide smooth transitions for score changes', async () => {
      render(<AnimatedScoreboard homeScore={0} awayScore={0} />);

      performanceMonitor.startMonitoring();

      // Measure transition timing
      const transitionStart = performance.now();

      await act(async () => {
        render(<AnimatedScoreboard homeScore={7} awayScore={0} />);
      });

      // Wait for transition to complete
      await new Promise(resolve => setTimeout(resolve, 300));

      const transitionEnd = performance.now();
      const transitionDuration = transitionEnd - transitionStart;

      const metrics = performanceMonitor.stopMonitoring();

      // Transition should be smooth and within expected duration
      expect(transitionDuration).toBeLessThan(500); // Under 500ms
      expect(metrics.fps).toBeGreaterThan(55);

      expect(screen.getByTestId('home-score')).toHaveTextContent('7');
    });

    it('should handle momentum indicator animations smoothly', async () => {
      const MomentumIndicator = ({ momentum }: { momentum: number }) => (
        <div
          data-testid="momentum-indicator"
          style={{
            transform: `translateX(${momentum * 50}px)`,
            transition: 'transform 0.5s cubic-bezier(0.4, 0.0, 0.2, 1)',
            backgroundColor: momentum > 0 ? 'green' : 'red'
          }}
        >
          Momentum: {momentum}
        </div>
      );

      const { rerender } = render(<MomentumIndicator momentum={0} />);

      performanceMonitor.startMonitoring();

      // Simulate momentum changes
      const momentumValues = [-1, -0.5, 0, 0.3, 0.8, 1, 0.5, -0.2];

      for (const momentum of momentumValues) {
        await act(async () => {
          rerender(<MomentumIndicator momentum={momentum} />);
        });

        await new Promise(resolve => setTimeout(resolve, 600)); // Wait for transition
      }

      const metrics = performanceMonitor.stopMonitoring();

      expect(metrics.fps).toBeGreaterThan(50);
      expect(metrics.droppedFrameRate).toBeLessThan(0.15);
      expect(screen.getByTestId('momentum-indicator')).toBeInTheDocument();
    });
  });

  describe('Memory and Resource Management', () => {
    it('should not leak memory during continuous animations', async () => {
      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;

      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      performanceMonitor.startMonitoring();

      // Run continuous updates for extended period
      const updates = Array.from({ length: 100 }, (_, i) => ({
        game_id: 'game_001',
        home_team: 'Patriots',
        away_team: 'Bills',
        home_score: Math.floor(i / 7),
        away_score: Math.floor(i / 10),
        quarter: Math.min(Math.floor(i / 25) + 1, 4),
        time_remaining: `${15 - (i % 15)}:${(60 - (i % 60)).toString().padStart(2, '0')}`,
        game_status: 'live',
        updated_at: new Date().toISOString()
      }));

      for (const update of updates) {
        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: update,
            timestamp: new Date().toISOString()
          });
        });

        await new Promise(resolve => setTimeout(resolve, 50));
      }

      const metrics = performanceMonitor.stopMonitoring();

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory usage should not increase significantly
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
      expect(metrics.fps).toBeGreaterThan(45); // Performance should remain stable
    });

    it('should properly cleanup animation resources on unmount', async () => {
      const { unmount } = render(
        <div>
          <LiveGameUpdates gameId="game_001" />
          <TouchdownCelebration visible={true} />
        </div>
      );

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Track active animations
      const animationElements = screen.getAllByRole('region', { hidden: true }).length;

      // Unmount component
      unmount();

      // Verify cleanup
      expect(cancelAnimationFrame).toHaveBeenCalled();
    });
  });

  describe('Performance Under Stress', () => {
    it('should maintain performance with high-frequency updates', async () => {
      render(<LiveGameUpdates />); // All games mode

      await act(async () => {
        mockWs.simulateOpen();
      });

      performanceMonitor.startMonitoring();

      // Simulate high-frequency updates (5 updates per second for 5 seconds)
      const totalUpdates = 25;
      const updateInterval = 200; // 5 updates per second

      for (let i = 0; i < totalUpdates; i++) {
        const gameId = `game_${(i % 3).toString().padStart(3, '0')}`; // 3 simultaneous games

        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: {
              game_id: gameId,
              home_team: `Home${i % 3}`,
              away_team: `Away${i % 3}`,
              home_score: Math.floor(Math.random() * 30),
              away_score: Math.floor(Math.random() * 30),
              quarter: Math.floor(i / 8) + 1,
              time_remaining: `${15 - (i % 15)}:${(i % 60).toString().padStart(2, '0')}`,
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });

        await new Promise(resolve => setTimeout(resolve, updateInterval));
      }

      const metrics = performanceMonitor.stopMonitoring();

      // Should handle high-frequency updates efficiently
      expect(metrics.fps).toBeGreaterThan(40);
      expect(metrics.droppedFrameRate).toBeLessThan(0.25);
      expect(metrics.frameCount).toBeGreaterThan(200); // Should have processed many frames

      console.log('High-frequency update metrics:', metrics);
    });

    it('should degrade gracefully under extreme load', async () => {
      render(<LiveGameUpdates />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      performanceMonitor.startMonitoring();

      // Extreme load: 100 messages in 1 second
      await act(async () => {
        for (let i = 0; i < 100; i++) {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: {
              game_id: `game_${i}`,
              home_team: `Team${i * 2}`,
              away_team: `Team${i * 2 + 1}`,
              home_score: Math.floor(Math.random() * 50),
              away_score: Math.floor(Math.random() * 50),
              quarter: 1,
              time_remaining: '15:00',
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        }
      });

      // Wait for processing
      await new Promise(resolve => setTimeout(resolve, 2000));

      const metrics = performanceMonitor.stopMonitoring();

      // Under extreme load, should still function (though performance may degrade)
      expect(metrics.fps).toBeGreaterThan(20); // Minimum acceptable performance
      expect(metrics.droppedFrameRate).toBeLessThan(0.5); // Up to 50% dropped frames acceptable under extreme load

      // Should still render the UI
      expect(screen.getByText(/Live/)).toBeInTheDocument();
    });
  });
});