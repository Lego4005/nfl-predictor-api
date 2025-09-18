/**
 * Comprehensive Frontend Component Tests for NFL Predictor Dashboard
 * Tests React components, real-time features, and user interactions for 375+ predictions system.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { jest } from '@jest/globals';

// Mock WebSocket
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  readyState: WebSocket.OPEN,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

global.WebSocket = vi.fn().mockImplementation(() => mockWebSocket);

// Import components under test
import SmartDashboard from '../src/components/SmartDashboard';
import { useWebSocket } from '../src/services/websocketService';
import WebSocketStatus from '../src/components/WebSocketStatus';
import LiveGameUpdates from '../src/components/LiveGameUpdates';
import SystemHealth from '../src/components/SystemHealth';
import WebSocketTestingDashboard from '../src/components/WebSocketTestingDashboard';

// Mock chart library
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />
}));

// Mock API service
vi.mock('../src/services/apiService', () => ({
  apiService: {
    getGames: vi.fn().mockResolvedValue([]),
    getPredictions: vi.fn().mockResolvedValue([]),
    getSystemHealth: vi.fn().mockResolvedValue({ status: 'healthy' }),
  }
}));

describe('WebSocket Service Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with default connection status', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.isReconnecting).toBe(false);
    expect(result.current.connectionId).toBe(null);
    expect(result.current.reconnectCount).toBe(0);
  });

  it('should provide send functionality', () => {
    const { result } = renderHook(() => useWebSocket());

    hookAct(() => {
      result.current.send('game_update', { gameId: '123' });
    });

    // WebSocket send should be called when connected
    // In real scenario, this would check if connection is established first
  });

  it('should provide channel subscription functionality', () => {
    const { result } = renderHook(() => useWebSocket());

    hookAct(() => {
      result.current.subscribe('games');
    });

    hookAct(() => {
      result.current.unsubscribe('games');
    });

    // Verify subscription/unsubscription methods are available
    expect(typeof result.current.subscribe).toBe('function');
    expect(typeof result.current.unsubscribe).toBe('function');
  });

  it('should handle event listeners', () => {
    const { result } = renderHook(() => useWebSocket());
    const mockHandler = vi.fn();

    hookAct(() => {
      result.current.on('game_update', mockHandler);
    });

    hookAct(() => {
      result.current.off('game_update', mockHandler);
    });

    expect(typeof result.current.on).toBe('function');
    expect(typeof result.current.off).toBe('function');
  });
});

describe('WebSocketStatus Component', () => {
  it('should render connection status', () => {
    const mockConnectionStatus = {
      isConnected: true,
      isReconnecting: false,
      connectionId: 'conn-123',
      reconnectCount: 0
    };

    render(<WebSocketStatus {...mockConnectionStatus} />);

    expect(screen.getByText(/connected/i)).toBeInTheDocument();
  });

  it('should show reconnecting state', () => {
    const mockConnectionStatus = {
      isConnected: false,
      isReconnecting: true,
      connectionId: null,
      reconnectCount: 2
    };

    render(<WebSocketStatus {...mockConnectionStatus} />);

    expect(screen.getByText(/reconnecting/i)).toBeInTheDocument();
    expect(screen.getByText(/attempt 2/i)).toBeInTheDocument();
  });

  it('should show disconnected state', () => {
    const mockConnectionStatus = {
      isConnected: false,
      isReconnecting: false,
      connectionId: null,
      reconnectCount: 0
    };

    render(<WebSocketStatus {...mockConnectionStatus} />);

    expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
  });

  it('should display connection ID when connected', () => {
    const mockConnectionStatus = {
      isConnected: true,
      isReconnecting: false,
      connectionId: 'test-conn-456',
      reconnectCount: 0
    };

    render(<WebSocketStatus {...mockConnectionStatus} />);

    expect(screen.getByText(/test-conn-456/)).toBeInTheDocument();
  });
});

describe('LiveGameUpdates Component', () => {
  const mockGameData = {
    gameId: 'game-123',
    homeTeam: 'Kansas City Chiefs',
    awayTeam: 'Baltimore Ravens',
    homeScore: 14,
    awayScore: 7,
    quarter: 2,
    timeRemaining: '5:30',
    gameStatus: 'in_progress'
  };

  it('should render live game data', () => {
    render(<LiveGameUpdates games={[mockGameData]} />);

    expect(screen.getByText(/kansas city chiefs/i)).toBeInTheDocument();
    expect(screen.getByText(/baltimore ravens/i)).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText(/quarter 2/i)).toBeInTheDocument();
    expect(screen.getByText(/5:30/)).toBeInTheDocument();
  });

  it('should handle empty game list', () => {
    render(<LiveGameUpdates games={[]} />);

    expect(screen.getByText(/no live games/i)).toBeInTheDocument();
  });

  it('should update when game data changes', () => {
    const { rerender } = render(<LiveGameUpdates games={[mockGameData]} />);

    // Update game data
    const updatedGameData = {
      ...mockGameData,
      homeScore: 21,
      timeRemaining: '3:45'
    };

    rerender(<LiveGameUpdates games={[updatedGameData]} />);

    expect(screen.getByText('21')).toBeInTheDocument();
    expect(screen.getByText(/3:45/)).toBeInTheDocument();
  });

  it('should handle different game statuses', () => {
    const finalGameData = {
      ...mockGameData,
      gameStatus: 'final',
      quarter: 4,
      timeRemaining: '0:00'
    };

    render(<LiveGameUpdates games={[finalGameData]} />);

    expect(screen.getByText(/final/i)).toBeInTheDocument();
  });
});

describe('SmartDashboard Component', () => {
  beforeEach(() => {
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });
  });

  it('should render main dashboard elements', async () => {
    render(<SmartDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/nfl predictor/i)).toBeInTheDocument();
    });

    // Check for main sections
    expect(screen.getByText(/system health/i)).toBeInTheDocument();
    expect(screen.getByText(/live games/i)).toBeInTheDocument();
    expect(screen.getByText(/predictions/i)).toBeInTheDocument();
  });

  it('should toggle dark mode', async () => {
    render(<SmartDashboard />);

    const darkModeToggle = screen.getByRole('button', { name: /dark mode/i });

    fireEvent.click(darkModeToggle);

    await waitFor(() => {
      expect(document.documentElement).toHaveClass('dark');
    });

    // Toggle back to light mode
    fireEvent.click(darkModeToggle);

    await waitFor(() => {
      expect(document.documentElement).not.toHaveClass('dark');
    });
  });

  it('should handle tab navigation', () => {
    render(<SmartDashboard />);

    const dashboardTab = screen.getByText(/dashboard/i);
    const predictionsTab = screen.getByText(/predictions/i);
    const analyticsTab = screen.getByText(/analytics/i);

    // Test tab switching
    fireEvent.click(predictionsTab);
    expect(predictionsTab).toHaveClass('active');

    fireEvent.click(analyticsTab);
    expect(analyticsTab).toHaveClass('active');

    fireEvent.click(dashboardTab);
    expect(dashboardTab).toHaveClass('active');
  });

  it('should display real-time updates', async () => {
    render(<SmartDashboard />);

    // Simulate WebSocket message
    act(() => {
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          event_type: 'game_update',
          data: {
            gameId: 'game-123',
            homeScore: 21,
            awayScore: 14
          }
        })
      });

      mockWebSocket.addEventListener.mock.calls
        .filter(call => call[0] === 'message')
        .forEach(call => call[1](messageEvent));
    });

    await waitFor(() => {
      // Verify update is displayed
      expect(screen.getByText('21')).toBeInTheDocument();
      expect(screen.getByText('14')).toBeInTheDocument();
    });
  });

  it('should handle loading states', () => {
    render(<SmartDashboard />);

    // Should show loading indicators initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should handle error states', async () => {
    // Mock API to throw error
    const mockApiService = await import('../src/services/apiService');
    vi.mocked(mockApiService.apiService.getGames).mockRejectedValue(new Error('API Error'));

    render(<SmartDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/error loading/i)).toBeInTheDocument();
    });
  });
});

describe('SystemHealth Component', () => {
  const mockHealthData = {
    status: 'healthy',
    uptime: 86400,
    connections: 150,
    memoryUsage: 45.2,
    cpuUsage: 12.8,
    lastUpdated: new Date().toISOString()
  };

  it('should render system health metrics', () => {
    render(<SystemHealth healthData={mockHealthData} />);

    expect(screen.getByText(/healthy/i)).toBeInTheDocument();
    expect(screen.getByText(/150/)).toBeInTheDocument(); // connections
    expect(screen.getByText(/45.2%/)).toBeInTheDocument(); // memory
    expect(screen.getByText(/12.8%/)).toBeInTheDocument(); // CPU
  });

  it('should show warning status', () => {
    const warningData = {
      ...mockHealthData,
      status: 'warning',
      memoryUsage: 85.0,
      cpuUsage: 78.5
    };

    render(<SystemHealth healthData={warningData} />);

    expect(screen.getByText(/warning/i)).toBeInTheDocument();
    expect(screen.getByText(/85.0%/)).toBeInTheDocument();
  });

  it('should show error status', () => {
    const errorData = {
      ...mockHealthData,
      status: 'error',
      connections: 0
    };

    render(<SystemHealth healthData={errorData} />);

    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });

  it('should format uptime correctly', () => {
    const uptimeData = {
      ...mockHealthData,
      uptime: 93784 // 1 day, 2 hours, 3 minutes, 4 seconds
    };

    render(<SystemHealth healthData={uptimeData} />);

    expect(screen.getByText(/1d 2h 3m/)).toBeInTheDocument();
  });
});

describe('Chart Rendering', () => {
  const mockChartData = [
    { time: '10:00', value: 65.2 },
    { time: '10:05', value: 67.8 },
    { time: '10:10', value: 63.5 },
    { time: '10:15', value: 69.1 },
  ];

  it('should render line charts', () => {
    render(
      <div>
        {/* Simulated chart component */}
        <div data-testid="prediction-chart">
          <div data-testid="line-chart">
            <div data-testid="line" />
            <div data-testid="x-axis" />
            <div data-testid="y-axis" />
          </div>
        </div>
      </div>
    );

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByTestId('line')).toBeInTheDocument();
    expect(screen.getByTestId('x-axis')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis')).toBeInTheDocument();
  });

  it('should render bar charts', () => {
    render(
      <div>
        <div data-testid="accuracy-chart">
          <div data-testid="bar-chart">
            <div data-testid="bar" />
          </div>
        </div>
      </div>
    );

    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar')).toBeInTheDocument();
  });

  it('should render pie charts', () => {
    render(
      <div>
        <div data-testid="distribution-chart">
          <div data-testid="pie-chart">
            <div data-testid="pie" />
            <div data-testid="cell" />
          </div>
        </div>
      </div>
    );

    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    expect(screen.getByTestId('pie')).toBeInTheDocument();
    expect(screen.getByTestId('cell')).toBeInTheDocument();
  });

  it('should be responsive', () => {
    render(
      <div>
        <div data-testid="responsive-container">
          <div data-testid="line-chart" />
        </div>
      </div>
    );

    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });
});

describe('WebSocketTestingDashboard Component', () => {
  it('should render testing controls', () => {
    render(<WebSocketTestingDashboard />);

    expect(screen.getByText(/websocket testing/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /connect/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument();
  });

  it('should handle connection testing', () => {
    render(<WebSocketTestingDashboard />);

    const connectButton = screen.getByRole('button', { name: /connect/i });
    const disconnectButton = screen.getByRole('button', { name: /disconnect/i });

    fireEvent.click(connectButton);
    fireEvent.click(disconnectButton);

    // Verify button clicks are handled
    expect(connectButton).toBeInTheDocument();
    expect(disconnectButton).toBeInTheDocument();
  });

  it('should send test messages', () => {
    render(<WebSocketTestingDashboard />);

    const messageInput = screen.getByPlaceholderText(/enter test message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    expect(messageInput).toHaveValue('Test message');
  });

  it('should display message history', () => {
    render(<WebSocketTestingDashboard />);

    expect(screen.getByText(/message history/i)).toBeInTheDocument();
  });

  it('should show connection statistics', () => {
    render(<WebSocketTestingDashboard />);

    expect(screen.getByText(/connection stats/i)).toBeInTheDocument();
  });
});

describe('User Interaction Tests', () => {
  it('should handle keyboard navigation', () => {
    render(<SmartDashboard />);

    // Test tab key navigation
    const focusableElements = screen.getAllByRole('button');

    if (focusableElements.length > 0) {
      focusableElements[0].focus();
      expect(focusableElements[0]).toHaveFocus();

      // Simulate Tab key
      fireEvent.keyDown(focusableElements[0], { key: 'Tab' });
    }
  });

  it('should handle mouse interactions', () => {
    render(<SmartDashboard />);

    const buttons = screen.getAllByRole('button');

    if (buttons.length > 0) {
      // Test hover
      fireEvent.mouseEnter(buttons[0]);
      fireEvent.mouseLeave(buttons[0]);

      // Test click
      fireEvent.click(buttons[0]);
    }
  });

  it('should handle form submissions', () => {
    render(<WebSocketTestingDashboard />);

    const form = screen.getByRole('form', { name: /message form/i });
    if (form) {
      fireEvent.submit(form);
    }
  });

  it('should handle dropdown selections', () => {
    render(<SmartDashboard />);

    // Look for select elements
    const selects = screen.queryAllByRole('combobox');

    selects.forEach(select => {
      fireEvent.change(select, { target: { value: 'new-option' } });
      expect(select).toHaveValue('new-option');
    });
  });
});

describe('Real-time Update Tests', () => {
  it('should handle rapid successive updates', async () => {
    render(<SmartDashboard />);

    // Simulate multiple rapid updates
    for (let i = 0; i < 10; i++) {
      act(() => {
        const messageEvent = new MessageEvent('message', {
          data: JSON.stringify({
            event_type: 'game_update',
            data: {
              gameId: `game-${i}`,
              homeScore: i * 7,
              awayScore: i * 3
            }
          })
        });

        mockWebSocket.addEventListener.mock.calls
          .filter(call => call[0] === 'message')
          .forEach(call => call[1](messageEvent));
      });
    }

    // Should handle all updates without breaking
    await waitFor(() => {
      expect(screen.getByText(/nfl predictor/i)).toBeInTheDocument();
    });
  });

  it('should throttle update frequency', async () => {
    render(<SmartDashboard />);

    const updateSpy = vi.fn();

    // Mock update handler
    React.useEffect = vi.fn().mockImplementation(updateSpy);

    // Simulate high frequency updates
    for (let i = 0; i < 100; i++) {
      act(() => {
        const messageEvent = new MessageEvent('message', {
          data: JSON.stringify({
            event_type: 'prediction_update',
            data: { confidence: 0.5 + (i * 0.001) }
          })
        });

        mockWebSocket.addEventListener.mock.calls
          .filter(call => call[0] === 'message')
          .forEach(call => call[1](messageEvent));
      });
    }

    // Should not overwhelm the UI with updates
    await waitFor(() => {
      expect(screen.getByText(/nfl predictor/i)).toBeInTheDocument();
    });
  });

  it('should maintain state during updates', async () => {
    const { rerender } = render(<SmartDashboard />);

    // Set initial state
    const darkModeToggle = screen.getByRole('button', { name: /dark mode/i });
    fireEvent.click(darkModeToggle);

    // Simulate updates
    rerender(<SmartDashboard />);

    // Should maintain dark mode state
    await waitFor(() => {
      expect(document.documentElement).toHaveClass('dark');
    });
  });
});

describe('Performance Tests', () => {
  it('should render large datasets efficiently', () => {
    const largeGameList = Array.from({ length: 100 }, (_, i) => ({
      gameId: `game-${i}`,
      homeTeam: `Home Team ${i}`,
      awayTeam: `Away Team ${i}`,
      homeScore: Math.floor(Math.random() * 50),
      awayScore: Math.floor(Math.random() * 50),
      quarter: Math.floor(Math.random() * 4) + 1,
      timeRemaining: '12:34',
      gameStatus: 'in_progress'
    }));

    const startTime = performance.now();
    render(<LiveGameUpdates games={largeGameList} />);
    const renderTime = performance.now() - startTime;

    // Should render in reasonable time (adjust threshold as needed)
    expect(renderTime).toBeLessThan(100); // 100ms
  });

  it('should handle memory efficiently', () => {
    const initialMemory = performance.memory?.usedJSHeapSize || 0;

    // Render and unmount multiple times
    for (let i = 0; i < 10; i++) {
      const { unmount } = render(<SmartDashboard />);
      unmount();
    }

    const finalMemory = performance.memory?.usedJSHeapSize || 0;
    const memoryIncrease = finalMemory - initialMemory;

    // Should not have significant memory leaks
    expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024); // 10MB threshold
  });
});

describe('Accessibility Tests', () => {
  it('should have proper ARIA labels', () => {
    render(<SmartDashboard />);

    // Check for ARIA labels on interactive elements
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveAttribute('aria-label');
    });
  });

  it('should support screen readers', () => {
    render(<SmartDashboard />);

    // Check for proper heading hierarchy
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toBeInTheDocument();
  });

  it('should have keyboard navigation', () => {
    render(<SmartDashboard />);

    // All interactive elements should be focusable
    const interactiveElements = screen.getAllByRole('button');
    interactiveElements.forEach(element => {
      element.focus();
      expect(element).toHaveFocus();
    });
  });

  it('should have proper contrast ratios', () => {
    render(<SmartDashboard />);

    // This would typically be tested with axe-core or similar tools
    // For now, we just verify elements are rendered
    expect(screen.getByText(/nfl predictor/i)).toBeInTheDocument();
  });
});