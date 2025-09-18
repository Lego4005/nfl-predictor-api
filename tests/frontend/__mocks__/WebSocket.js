/**
 * Mock WebSocket for Testing
 * Provides realistic WebSocket behavior for frontend testing
 */

class MockWebSocket extends EventTarget {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url, protocols) {
    super();
    this.url = url;
    this.protocols = protocols;
    this.readyState = MockWebSocket.CONNECTING;
    this.bufferedAmount = 0;
    this.extensions = '';
    this.protocol = '';
    this.binaryType = 'blob';

    // Internal state
    this._messageQueue = [];
    this._isSlowNetwork = false;
    this._shouldFailConnection = false;
    this._connectionDelay = 100;

    // Auto-connect unless configured otherwise
    if (!this.constructor._preventAutoConnect) {
      setTimeout(() => this.simulateOpen(), this._connectionDelay);
    }

    // Store instance for test access
    if (typeof window !== 'undefined') {
      window.__mockWebSocketInstance = this;
    } else if (typeof global !== 'undefined') {
      global.__mockWebSocketInstance = this;
    }
  }

  // Simulate connection opening
  simulateOpen() {
    if (this._shouldFailConnection) {
      this.simulateError(new Error('Connection failed'));
      return;
    }

    this.readyState = MockWebSocket.OPEN;
    this.dispatchEvent(new Event('open'));

    // Process queued messages
    this._processMessageQueue();
  }

  // Simulate connection closing
  simulateClose(code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      this.dispatchEvent(new CloseEvent('close', { code, reason }));
    }, 50);
  }

  // Simulate receiving a message
  simulateMessage(data) {
    if (this.readyState === MockWebSocket.OPEN) {
      const event = new MessageEvent('message', {
        data: typeof data === 'string' ? data : JSON.stringify(data)
      });

      if (this._isSlowNetwork) {
        setTimeout(() => this.dispatchEvent(event), Math.random() * 1000 + 500);
      } else {
        this.dispatchEvent(event);
      }
    } else {
      // Queue message if not connected
      this._messageQueue.push(data);
    }
  }

  // Simulate error
  simulateError(error) {
    this.dispatchEvent(new ErrorEvent('error', { error }));
  }

  // Mock send method
  send(data) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new DOMException('WebSocket is not open', 'InvalidStateError');
    }

    // Store sent data for test verification
    if (!this._sentMessages) {
      this._sentMessages = [];
    }
    this._sentMessages.push(data);

    // Simulate network delay
    if (this._isSlowNetwork) {
      setTimeout(() => {
        this.bufferedAmount = 0;
      }, Math.random() * 200 + 100);
    } else {
      this.bufferedAmount = 0;
    }
  }

  // Mock close method
  close(code = 1000, reason = '') {
    if (this.readyState === MockWebSocket.CLOSED || this.readyState === MockWebSocket.CLOSING) {
      return;
    }

    this.simulateClose(code, reason);
  }

  // Test helper methods
  getSentMessages() {
    return this._sentMessages || [];
  }

  getLastSentMessage() {
    const messages = this.getSentMessages();
    return messages.length > 0 ? messages[messages.length - 1] : null;
  }

  clearSentMessages() {
    this._sentMessages = [];
  }

  // Configuration methods for testing
  setSlowNetwork(enabled) {
    this._isSlowNetwork = enabled;
  }

  setShouldFailConnection(shouldFail) {
    this._shouldFailConnection = shouldFail;
  }

  setConnectionDelay(delay) {
    this._connectionDelay = delay;
  }

  // Process queued messages when connection opens
  _processMessageQueue() {
    while (this._messageQueue.length > 0) {
      const data = this._messageQueue.shift();
      this.simulateMessage(data);
    }
  }

  // Static methods for test configuration
  static preventAutoConnect() {
    this._preventAutoConnect = true;
  }

  static allowAutoConnect() {
    this._preventAutoConnect = false;
  }

  static resetMocks() {
    this._preventAutoConnect = false;
    if (typeof window !== 'undefined') {
      delete window.__mockWebSocketInstance;
    } else if (typeof global !== 'undefined') {
      delete global.__mockWebSocketInstance;
    }
  }
}

// Advanced mock for specific testing scenarios
class MockWebSocketServer {
  constructor() {
    this.connections = new Set();
    this.channels = new Map();
    this.messageHistory = [];
    this.isRunning = false;
  }

  start() {
    this.isRunning = true;
  }

  stop() {
    this.isRunning = false;
    this.connections.forEach(conn => conn.simulateClose());
    this.connections.clear();
  }

  addConnection(ws) {
    this.connections.add(ws);
  }

  removeConnection(ws) {
    this.connections.delete(ws);
  }

  broadcast(message) {
    this.messageHistory.push({ type: 'broadcast', message, timestamp: Date.now() });
    this.connections.forEach(ws => ws.simulateMessage(message));
  }

  sendToChannel(channel, message) {
    this.messageHistory.push({ type: 'channel', channel, message, timestamp: Date.now() });

    const subscribers = this.channels.get(channel) || new Set();
    subscribers.forEach(ws => ws.simulateMessage(message));
  }

  subscribeToChannel(ws, channel) {
    if (!this.channels.has(channel)) {
      this.channels.set(channel, new Set());
    }
    this.channels.get(channel).add(ws);
  }

  unsubscribeFromChannel(ws, channel) {
    const subscribers = this.channels.get(channel);
    if (subscribers) {
      subscribers.delete(ws);
      if (subscribers.size === 0) {
        this.channels.delete(channel);
      }
    }
  }

  getStats() {
    return {
      connections: this.connections.size,
      channels: this.channels.size,
      messageHistory: this.messageHistory.length,
      isRunning: this.isRunning
    };
  }
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MockWebSocket, MockWebSocketServer };
} else if (typeof window !== 'undefined') {
  window.MockWebSocket = MockWebSocket;
  window.MockWebSocketServer = MockWebSocketServer;
}

export { MockWebSocket, MockWebSocketServer };