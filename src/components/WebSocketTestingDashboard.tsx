/**
 * WebSocket Testing Dashboard Component
 * Provides interactive controls for testing WebSocket functionality
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  useWebSocket,
  WebSocketEventType,
  websocketService,
  GameUpdate,
  PredictionUpdate,
  OddsUpdate
} from '../services/websocketService';
import WebSocketStatus from './WebSocketStatus';
import LiveGameUpdates from './LiveGameUpdates';

interface LogEntry {
  timestamp: string;
  type: 'sent' | 'received' | 'system';
  eventType?: WebSocketEventType;
  data: any;
  message?: string;
}

const WebSocketTestingDashboard: React.FC = () => {
  const {
    isConnected,
    isReconnecting,
    connectionId,
    reconnectCount,
    send,
    subscribe,
    unsubscribe,
    on,
    off
  } = useWebSocket({ autoConnect: true });

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<string>('games');
  const [subscribedChannels, setSubscribedChannels] = useState<Set<string>>(new Set());

  // Add log entry
  const addLog = useCallback((entry: Omit<LogEntry, 'timestamp'>) => {
    setLogs(prev => [
      ...prev.slice(-19), // Keep last 20 entries
      {
        ...entry,
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  // Handle all WebSocket events for logging
  useEffect(() => {
    const eventTypes = Object.values(WebSocketEventType);

    const handlers = eventTypes.map(eventType => {
      const handler = (data: any) => {
        addLog({
          type: 'received',
          eventType,
          data
        });
      };

      on(eventType, handler);
      return { eventType, handler };
    });

    return () => {
      handlers.forEach(({ eventType, handler }) => {
        off(eventType, handler);
      });
    };
  }, [on, off, addLog]);

  // Connection status logging
  useEffect(() => {
    if (isConnected) {
      addLog({
        type: 'system',
        data: null,
        message: `Connected to WebSocket (ID: ${connectionId?.slice(0, 8)}...)`
      });
    } else if (isReconnecting) {
      addLog({
        type: 'system',
        data: null,
        message: `Reconnecting... (Attempt ${reconnectCount})`
      });
    } else {
      addLog({
        type: 'system',
        data: null,
        message: 'Disconnected from WebSocket'
      });
    }
  }, [isConnected, isReconnecting, connectionId, reconnectCount, addLog]);

  // Test functions
  const sendTestGameUpdate = () => {
    const testData = {
      game_id: `test_game_${Date.now()}`,
      home_team: 'KC',
      away_team: 'BUF',
      home_score: Math.floor(Math.random() * 50),
      away_score: Math.floor(Math.random() * 50),
      quarter: Math.floor(Math.random() * 4) + 1,
      time_remaining: '12:34',
      game_status: 'live',
      updated_at: new Date().toISOString()
    };

    send(WebSocketEventType.GAME_UPDATE, testData);
    addLog({
      type: 'sent',
      eventType: WebSocketEventType.GAME_UPDATE,
      data: testData
    });
  };

  const sendTestPredictionUpdate = () => {
    const testData = {
      game_id: `test_game_${Date.now()}`,
      home_team: 'KC',
      away_team: 'BUF',
      home_win_probability: Math.random(),
      away_win_probability: Math.random(),
      predicted_spread: (Math.random() - 0.5) * 20,
      confidence_level: Math.random(),
      model_version: 'v1.2.0',
      updated_at: new Date().toISOString()
    };

    send(WebSocketEventType.PREDICTION_UPDATE, testData);
    addLog({
      type: 'sent',
      eventType: WebSocketEventType.PREDICTION_UPDATE,
      data: testData
    });
  };

  const sendTestOddsUpdate = () => {
    const testData = {
      game_id: `test_game_${Date.now()}`,
      sportsbook: 'DraftKings',
      home_team: 'KC',
      away_team: 'BUF',
      spread: (Math.random() - 0.5) * 20,
      moneyline_home: Math.floor(Math.random() * 400) - 200,
      moneyline_away: Math.floor(Math.random() * 400) - 200,
      over_under: 40 + Math.random() * 20,
      updated_at: new Date().toISOString()
    };

    send(WebSocketEventType.ODDS_UPDATE, testData);
    addLog({
      type: 'sent',
      eventType: WebSocketEventType.ODDS_UPDATE,
      data: testData
    });
  };

  const sendHeartbeat = () => {
    const testData = {
      timestamp: new Date().toISOString(),
      connection_id: connectionId,
      client_time: new Date().toISOString()
    };

    send(WebSocketEventType.HEARTBEAT, testData);
    addLog({
      type: 'sent',
      eventType: WebSocketEventType.HEARTBEAT,
      data: testData
    });
  };

  const handleChannelSubscription = () => {
    if (subscribedChannels.has(selectedChannel)) {
      unsubscribe(selectedChannel);
      setSubscribedChannels(prev => {
        const newSet = new Set(prev);
        newSet.delete(selectedChannel);
        return newSet;
      });

      addLog({
        type: 'system',
        data: null,
        message: `Unsubscribed from channel: ${selectedChannel}`
      });
    } else {
      subscribe(selectedChannel);
      setSubscribedChannels(prev => new Set([...prev, selectedChannel]));

      addLog({
        type: 'system',
        data: null,
        message: `Subscribed to channel: ${selectedChannel}`
      });
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const triggerServerUpdate = async (endpoint: string, data: any) => {
    try {
      const response = await fetch(`/api/websocket/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        addLog({
          type: 'system',
          data: null,
          message: `Server update triggered: ${endpoint}`
        });
      } else {
        addLog({
          type: 'system',
          data: null,
          message: `Server update failed: ${response.status}`
        });
      }
    } catch (error) {
      addLog({
        type: 'system',
        data: null,
        message: `Server update error: ${error}`
      });
    }
  };

  const getLogEntryStyle = (entry: LogEntry) => {
    switch (entry.type) {
      case 'sent':
        return 'bg-blue-50 border-l-4 border-blue-500 text-blue-800';
      case 'received':
        return 'bg-green-50 border-l-4 border-green-500 text-green-800';
      case 'system':
        return 'bg-gray-50 border-l-4 border-gray-500 text-gray-800';
      default:
        return 'bg-white border border-gray-200';
    }
  };

  return (
    <div className="websocket-testing-dashboard p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">WebSocket Testing Dashboard</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Connection Status */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
          <WebSocketStatus showControls={true} />

          {/* Connection Info */}
          {isConnected && (
            <div className="mt-4 space-y-2 text-sm text-gray-600">
              <div>Connection ID: {connectionId}</div>
              <div>Subscribed Channels: {Array.from(subscribedChannels).join(', ') || 'None'}</div>
            </div>
          )}
        </div>

        {/* Test Controls */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Test Controls</h2>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={sendTestGameUpdate}
              disabled={!isConnected}
              className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
            >
              Send Game Update
            </button>

            <button
              onClick={sendTestPredictionUpdate}
              disabled={!isConnected}
              className="px-4 py-2 bg-green-500 text-white rounded disabled:bg-gray-300"
            >
              Send Prediction
            </button>

            <button
              onClick={sendTestOddsUpdate}
              disabled={!isConnected}
              className="px-4 py-2 bg-purple-500 text-white rounded disabled:bg-gray-300"
            >
              Send Odds Update
            </button>

            <button
              onClick={sendHeartbeat}
              disabled={!isConnected}
              className="px-4 py-2 bg-yellow-500 text-white rounded disabled:bg-gray-300"
            >
              Send Heartbeat
            </button>
          </div>

          {/* Channel Subscription */}
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Channel Subscription</h3>
            <div className="flex space-x-2">
              <select
                value={selectedChannel}
                onChange={(e) => setSelectedChannel(e.target.value)}
                className="flex-1 p-2 border rounded"
              >
                <option value="games">games</option>
                <option value="odds">odds</option>
                <option value="predictions">predictions</option>
                <option value="game_test_123">game_test_123</option>
                <option value="custom">custom</option>
              </select>
              <button
                onClick={handleChannelSubscription}
                disabled={!isConnected}
                className={`px-4 py-2 rounded text-white disabled:bg-gray-300 ${
                  subscribedChannels.has(selectedChannel)
                    ? 'bg-red-500 hover:bg-red-600'
                    : 'bg-blue-500 hover:bg-blue-600'
                }`}
              >
                {subscribedChannels.has(selectedChannel) ? 'Unsubscribe' : 'Subscribe'}
              </button>
            </div>
          </div>

          {/* Server Triggers */}
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Server Triggers</h3>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => triggerServerUpdate('test-broadcast', {})}
                className="px-3 py-2 bg-indigo-500 text-white rounded text-sm"
              >
                Server Broadcast
              </button>

              <button
                onClick={() => triggerServerUpdate('system-notification', {
                  message: 'Test notification from server',
                  level: 'info'
                })}
                className="px-3 py-2 bg-orange-500 text-white rounded text-sm"
              >
                System Notification
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Message Logs */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Message Logs</h2>
            <button
              onClick={clearLogs}
              className="px-3 py-1 bg-gray-500 text-white rounded text-sm"
            >
              Clear Logs
            </button>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                No messages yet. Connect and interact to see logs here.
              </div>
            ) : (
              logs.map((entry, index) => (
                <div
                  key={index}
                  className={`p-3 rounded text-sm ${getLogEntryStyle(entry)}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="font-semibold">
                      {entry.type.toUpperCase()}
                      {entry.eventType && ` - ${entry.eventType}`}
                    </div>
                    <div className="text-xs opacity-75">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </div>
                  </div>

                  {entry.message && (
                    <div className="mt-1">{entry.message}</div>
                  )}

                  {entry.data && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-xs opacity-75">
                        Show Data
                      </summary>
                      <pre className="mt-1 text-xs bg-black bg-opacity-10 p-2 rounded overflow-x-auto">
                        {JSON.stringify(entry.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live Updates Display */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Live Updates</h2>
          <LiveGameUpdates
            showPredictions={true}
            showOdds={true}
            className="h-96 overflow-y-auto"
          />
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-6 bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Testing Instructions</h2>
        <div className="space-y-2 text-sm text-gray-700">
          <p><strong>1. Client Testing:</strong> Use the buttons above to send test messages and observe the logs.</p>
          <p><strong>2. Server Testing:</strong> Use "Server Broadcast" and "System Notification" to test server-initiated messages.</p>
          <p><strong>3. Channel Testing:</strong> Subscribe/unsubscribe from channels to test targeted messaging.</p>
          <p><strong>4. Connection Testing:</strong> Use connect/disconnect buttons to test reconnection logic.</p>
          <p><strong>5. API Testing:</strong> Use <code>curl</code> or Postman to test WebSocket API endpoints.</p>
        </div>

        <div className="mt-4 bg-white p-3 rounded border">
          <p className="font-semibold text-sm">Example API call:</p>
          <pre className="text-xs mt-2 bg-gray-100 p-2 rounded">
{`curl -X POST http://localhost:8000/api/websocket/game-update \\
  -H "Content-Type: application/json" \\
  -d '{
    "game_id": "api_test_game",
    "home_team": "API_HOME",
    "away_team": "API_AWAY",
    "home_score": 28,
    "away_score": 21,
    "game_status": "live"
  }'`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default WebSocketTestingDashboard;