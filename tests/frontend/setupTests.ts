/**
 * Frontend Test Setup for NFL Predictor Platform
 * Configures testing environment, mocks, and global utilities
 */

import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';
import { server } from './mocks/server';

// Polyfills for Node.js environment
Object.assign(global, { TextDecoder, TextEncoder });

// Mock global objects
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn((key: string) => {
    return localStorageMock.store[key] || null;
  }),
  setItem: jest.fn((key: string, value: string) => {
    localStorageMock.store[key] = value.toString();
  }),
  removeItem: jest.fn((key: string) => {
    delete localStorageMock.store[key];
  }),
  clear: jest.fn(() => {
    localStorageMock.store = {};
  }),
  store: {} as { [key: string]: string },
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock,
});

// Mock WebSocket
class MockWebSocket {
  public static readonly CONNECTING = 0;
  public static readonly OPEN = 1;
  public static readonly CLOSING = 2;
  public static readonly CLOSED = 3;

  public readonly CONNECTING = 0;
  public readonly OPEN = 1;
  public readonly CLOSING = 2;
  public readonly CLOSED = 3;

  public readyState = MockWebSocket.CONNECTING;
  public url: string;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 100);
  }

  public send(data: string | ArrayBuffer | SharedArrayBuffer | Blob | ArrayBufferView): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Mock send - in real tests you might want to trigger mock responses
  }

  public close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close', { code, reason }));
      }
    }, 10);
  }

  public addEventListener(type: string, listener: EventListener): void {
    // Mock implementation
    if (type === 'open' && this.onopen === null) {
      this.onopen = listener as (event: Event) => void;
    } else if (type === 'close' && this.onclose === null) {
      this.onclose = listener as (event: CloseEvent) => void;
    } else if (type === 'message' && this.onmessage === null) {
      this.onmessage = listener as (event: MessageEvent) => void;
    } else if (type === 'error' && this.onerror === null) {
      this.onerror = listener as (event: Event) => void;
    }
  }

  public removeEventListener(type: string, listener: EventListener): void {
    // Mock implementation
    if (type === 'open') {
      this.onopen = null;
    } else if (type === 'close') {
      this.onclose = null;
    } else if (type === 'message') {
      this.onmessage = null;
    } else if (type === 'error') {
      this.onerror = null;
    }
  }
}

global.WebSocket = MockWebSocket as any;

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  })
) as jest.Mock;

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    hostname: 'localhost',
    port: '3000',
    protocol: 'http:',
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    pathname: '/',
    search: '',
    hash: '',
    reload: jest.fn(),
    assign: jest.fn(),
    replace: jest.fn(),
  },
  writable: true,
});

// Mock console methods for cleaner test output
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Setup MSW server for API mocking
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Global test utilities
global.testUtils = {
  // Utility to wait for async operations
  waitForNextTick: () => new Promise(resolve => setTimeout(resolve, 0)),

  // Utility to mock async component loading
  mockAsyncComponent: (name: string) => {
    return jest.fn(() =>
      Promise.resolve({
        default: () => React.createElement('div', { 'data-testid': `mock-${name}` })
      })
    );
  },

  // Utility to create mock WebSocket events
  createMockWebSocketEvent: (type: string, data: any = {}) => {
    return {
      type,
      data: JSON.stringify({
        event_type: type,
        data,
        timestamp: new Date().toISOString(),
        message_id: Math.random().toString(36).substr(2, 9)
      })
    };
  },

  // Utility to simulate user interactions with delays
  simulateUserInteraction: async (element: Element, action: () => void) => {
    await new Promise(resolve => setTimeout(resolve, 100));
    action();
    await new Promise(resolve => setTimeout(resolve, 100));
  }
};

// Mock performance.now for consistent timing in tests
const mockPerformanceNow = jest.fn(() => Date.now());
Object.defineProperty(window, 'performance', {
  value: {
    now: mockPerformanceNow,
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByName: jest.fn(() => []),
    getEntriesByType: jest.fn(() => []),
  },
  writable: true,
});

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 0));
global.cancelAnimationFrame = jest.fn(id => clearTimeout(id));

// Mock Recharts components for chart testing
jest.mock('recharts', () => ({
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
  Cell: () => <div data-testid="cell" />,
}));

// Setup custom matchers
expect.extend({
  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () =>
          `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () =>
          `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },

  toHaveBeenCalledWithObjectContaining(received: jest.Mock, expected: object) {
    const pass = received.mock.calls.some(call =>
      call.some(arg =>
        typeof arg === 'object' &&
        Object.keys(expected).every(key => arg[key] === expected[key])
      )
    );

    return {
      message: () =>
        pass
          ? `expected function not to have been called with object containing ${JSON.stringify(expected)}`
          : `expected function to have been called with object containing ${JSON.stringify(expected)}`,
      pass,
    };
  }
});

// Type declarations for global utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeWithinRange(floor: number, ceiling: number): R;
      toHaveBeenCalledWithObjectContaining(expected: object): R;
    }
  }

  var testUtils: {
    waitForNextTick: () => Promise<void>;
    mockAsyncComponent: (name: string) => jest.Mock;
    createMockWebSocketEvent: (type: string, data?: any) => any;
    simulateUserInteraction: (element: Element, action: () => void) => Promise<void>;
  };
}

export {};