/**
 * WebSocket Status Component
 * Shows connection status and provides manual connection controls
 */

import React from 'react';
import { useWebSocket, WebSocketEventType, websocketService } from '../services/websocketService';

interface WebSocketStatusProps {
  showControls?: boolean;
  className?: string;
}

const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
  showControls = true,
  className = ''
}) => {
  const { isConnected, isReconnecting, connectionId, reconnectCount } = useWebSocket();

  const handleConnect = () => {
    websocketService.connect().catch(console.error);
  };

  const handleDisconnect = () => {
    websocketService.disconnect();
  };

  const getStatusColor = () => {
    if (isConnected) return 'text-green-500';
    if (isReconnecting) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getStatusText = () => {
    if (isConnected) return 'Connected';
    if (isReconnecting) return `Reconnecting (${reconnectCount})`;
    return 'Disconnected';
  };

  const getStatusIcon = () => {
    if (isConnected) return '🟢';
    if (isReconnecting) return '🟡';
    return '🔴';
  };

  return (
    <div className={`websocket-status ${className}`}>
      <div className="flex items-center space-x-2">
        <span className="text-lg">{getStatusIcon()}</span>
        <div className="flex flex-col">
          <span className={`font-semibold ${getStatusColor()}`}>
            {getStatusText()}
          </span>
          {connectionId && (
            <span className="text-xs text-gray-500">
              ID: {connectionId.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>

      {showControls && (
        <div className="flex space-x-2 mt-2">
          <button
            onClick={handleConnect}
            disabled={isConnected || isReconnecting}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Connect
          </button>
          <button
            onClick={handleDisconnect}
            disabled={!isConnected && !isReconnecting}
            className="px-3 py-1 text-sm bg-red-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
};

export default WebSocketStatus;