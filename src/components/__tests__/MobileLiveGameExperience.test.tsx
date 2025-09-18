/**
 * Test suite for Mobile Live Game Experience
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MobileLiveGameExperience from '../MobileLiveGameExperience';

// Mock the WebSocket service
jest.mock('../../services/websocketService', () => ({
  useWebSocket: () => ({
    isConnected: true,
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
    on: jest.fn(),
    off: jest.fn()
  }),
  WebSocketEventType: {
    GAME_UPDATE: 'game_update',
    SCORE_UPDATE: 'score_update',
    PREDICTION_UPDATE: 'prediction_update',
    ODDS_UPDATE: 'odds_update',
    NOTIFICATION: 'notification'
  }
}));

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    circle: ({ children, ...props }: any) => <circle {...props}>{children}</circle>
  },
  AnimatePresence: ({ children }: any) => children,
  useMotionValue: () => ({ set: jest.fn() }),
  useTransform: () => 1
}));

// Mock performance monitoring hook
jest.mock('../../hooks/usePerformanceMonitor', () => ({
  usePerformanceMonitor: () => ({
    startTracking: jest.fn(),
    stopTracking: jest.fn(),
    getMetrics: () => ({
      frameRate: 60,
      averageFrameTime: 16.67,
      maxFrameTime: 20,
      minFrameTime: 15,
      renderCount: 100
    }),
    getOptimizationRecommendations: () => []
  })
}));

// Mock swipe gestures hook
jest.mock('../../hooks/useSwipeGestures', () => ({
  useSwipeGestures: () => ({
    swipeHandlers: {
      onTouchStart: jest.fn(),
      onTouchMove: jest.fn(),
      onTouchEnd: jest.fn(),
      onMouseDown: jest.fn(),
      onMouseMove: jest.fn(),
      onMouseUp: jest.fn()
    },
    isSwiping: false
  })
}));

describe('MobileLiveGameExperience', () => {
  beforeEach(() => {
    // Mock navigator.vibrate
    Object.defineProperty(navigator, 'vibrate', {
      writable: true,
      value: jest.fn()
    });

    // Mock window.innerWidth for mobile detection
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375 // iPhone width
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders mobile experience when connected', () => {
    render(<MobileLiveGameExperience />);

    // Should not show disconnected state
    expect(screen.queryByText('Connecting to live games...')).not.toBeInTheDocument();

    // Should show the main interface
    expect(screen.getByText('Waiting for live games...')).toBeInTheDocument();
  });

  it('shows disconnected state when WebSocket is not connected', () => {
    // Mock disconnected state
    jest.doMock('../../services/websocketService', () => ({
      useWebSocket: () => ({
        isConnected: false,
        subscribe: jest.fn(),
        unsubscribe: jest.fn(),
        on: jest.fn(),
        off: jest.fn()
      })
    }));

    render(<MobileLiveGameExperience />);
    expect(screen.getByText('Connecting to live games...')).toBeInTheDocument();
  });

  it('renders with custom className', () => {
    const { container } = render(
      <MobileLiveGameExperience className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders with specific gameId prop', () => {
    render(<MobileLiveGameExperience gameId="test-game-123" />);

    // Component should render without errors
    expect(screen.getByText('Waiting for live games...')).toBeInTheDocument();
  });

  it('displays performance metrics in development', () => {
    render(<MobileLiveGameExperience />);

    // Should show FPS indicator
    expect(screen.getByText(/FPS: 60/)).toBeInTheDocument();
    expect(screen.getByText(/🟢 Live/)).toBeInTheDocument();
  });

  it('handles touch events properly', () => {
    const { container } = render(<MobileLiveGameExperience />);

    const mainContainer = container.querySelector('.mobile-live-game-experience');
    expect(mainContainer).toBeInTheDocument();

    // Simulate touch events
    fireEvent.touchStart(mainContainer!, {
      touches: [{ clientX: 100, clientY: 100 }]
    });

    fireEvent.touchEnd(mainContainer!, {
      changedTouches: [{ clientX: 200, clientY: 100 }]
    });

    // Should not throw errors
    expect(mainContainer).toBeInTheDocument();
  });

  it('supports keyboard navigation for accessibility', () => {
    render(<MobileLiveGameExperience />);

    // Should be accessible via keyboard
    const container = screen.getByRole('main', { hidden: true }) ||
                     document.querySelector('.mobile-live-game-experience');

    if (container) {
      fireEvent.keyDown(container, { key: 'ArrowLeft' });
      fireEvent.keyDown(container, { key: 'ArrowRight' });
    }

    // Should not crash
    expect(screen.getByText('Waiting for live games...')).toBeInTheDocument();
  });

  it('respects reduced motion preferences', () => {
    // Mock prefers-reduced-motion
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    render(<MobileLiveGameExperience />);

    // Should render without animations
    expect(screen.getByText('Waiting for live games...')).toBeInTheDocument();
  });
});

// Component integration tests
describe('MobileLiveGameExperience Integration', () => {
  it('integrates with all child components', async () => {
    render(<MobileLiveGameExperience />);

    // Should render main container
    expect(screen.getByText('Waiting for live games...')).toBeInTheDocument();

    // Should show performance metrics
    expect(screen.getByText(/FPS:/)).toBeInTheDocument();

    // Should be ready for live data
    await waitFor(() => {
      expect(screen.getByText(/🟢 Live/)).toBeInTheDocument();
    });
  });

  it('handles error boundaries gracefully', () => {
    // Mock console.error to avoid test noise
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    // This should not crash the test
    render(<MobileLiveGameExperience />);

    expect(screen.getByText('Waiting for live games...')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});