import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wifi, WifiOff, Activity, Clock, 
  AlertTriangle, CheckCircle, Zap
} from 'lucide-react';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { Progress } from '../ui/progress';
import type { 
  WebSocketConnectionState, 
  LiveUpdateMessage 
} from '../../types/aiCouncil';

interface LiveUpdateIndicatorProps {
  connectionState: WebSocketConnectionState;
  lastUpdate: LiveUpdateMessage | null;
  className?: string;
  showDetails?: boolean;
}

const LiveUpdateIndicator: React.FC<LiveUpdateIndicatorProps> = ({
  connectionState,
  lastUpdate,
  className = '',
  showDetails = false
}) => {
  const getConnectionStatus = () => {
    if (!connectionState.connected) {
      if (connectionState.reconnectAttempts > 0) {
        return {
          status: 'reconnecting',
          color: 'text-yellow-600 bg-yellow-100',
          icon: Activity,
          message: `Reconnecting... (${connectionState.reconnectAttempts}/5)`
        };
      }
      return {
        status: 'disconnected',
        color: 'text-red-600 bg-red-100',
        icon: WifiOff,
        message: 'Disconnected'
      };
    }

    if (connectionState.latency > 1000) {
      return {
        status: 'poor',
        color: 'text-orange-600 bg-orange-100',
        icon: Wifi,
        message: `High Latency (${connectionState.latency}ms)`
      };
    }

    return {
      status: 'connected',
      color: 'text-green-600 bg-green-100',
      icon: Wifi,
      message: connectionState.latency > 0 ? `${connectionState.latency}ms` : 'Connected'
    };
  };

  const getUpdatePriority = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatUpdateType = (type: string) => {
    return type.replace(/_/g, ' ').toLowerCase()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getTimeSinceUpdate = () => {
    if (!lastUpdate) return null;
    
    const now = new Date();
    const updateTime = new Date(lastUpdate.timestamp);
    const diffMs = now.getTime() - updateTime.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    return `${Math.floor(diffSeconds / 3600)}h ago`;
  };

  const status = getConnectionStatus();
  const StatusIcon = status.icon;
  const timeSinceUpdate = getTimeSinceUpdate();

  if (!showDetails) {
    // Compact indicator
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="relative">
          <StatusIcon className={`h-4 w-4 ${status.color.split(' ')[0]}`} />
          {status.status === 'connected' && (
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          )}
        </div>
        <Badge variant="outline" className={status.color}>
          {status.message}
        </Badge>
        {lastUpdate && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex items-center gap-1"
          >
            <Zap className="h-3 w-3 text-blue-500" />
            <span className="text-xs text-gray-600">{timeSinceUpdate}</span>
          </motion.div>
        )}
      </div>
    );
  }

  // Detailed indicator
  return (
    <Card className={`${className}`}>
      <CardContent className="p-4">
        <div className="space-y-4">
          {/* Connection Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <StatusIcon className={`h-5 w-5 ${status.color.split(' ')[0]}`} />
                {status.status === 'connected' && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                )}
              </div>
              <div>
                <div className="font-medium text-sm">Live Connection</div>
                <div className="text-xs text-gray-600">{status.message}</div>
              </div>
            </div>
            <Badge className={status.color}>
              {status.status}
            </Badge>
          </div>

          {/* Connection Quality */}
          {connectionState.connected && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Connection Quality</span>
                <span className="font-medium">
                  {connectionState.latency < 200 ? 'Excellent' :
                   connectionState.latency < 500 ? 'Good' :
                   connectionState.latency < 1000 ? 'Fair' : 'Poor'}
                </span>
              </div>
              <Progress 
                value={Math.max(0, 100 - (connectionState.latency / 10))} 
                className="h-1.5"
              />
              <div className="text-xs text-gray-500">
                Latency: {connectionState.latency}ms
              </div>
            </div>
          )}

          {/* Last Update */}
          <AnimatePresence>
            {lastUpdate && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="border-t border-gray-200 pt-3"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">Latest Update</span>
                  </div>
                  <Badge className={getUpdatePriority(lastUpdate.priority)}>
                    {lastUpdate.priority}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600">Type</span>
                    <span className="font-medium">
                      {formatUpdateType(lastUpdate.type)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600">Time</span>
                    <span className="font-medium">{timeSinceUpdate}</span>
                  </div>
                  
                  {lastUpdate.affectedCategories.length > 0 && (
                    <div className="text-xs">
                      <span className="text-gray-600">Affected: </span>
                      <span className="font-medium">
                        {lastUpdate.affectedCategories.length} categories
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Reconnection Status */}
          {connectionState.reconnectAttempts > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 p-2 bg-yellow-50 rounded-lg"
            >
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <div className="text-sm">
                <div className="font-medium text-yellow-800">
                  Reconnection in progress
                </div>
                <div className="text-xs text-yellow-600">
                  Attempt {connectionState.reconnectAttempts} of 5
                </div>
              </div>
            </motion.div>
          )}

          {/* Heartbeat Status */}
          {connectionState.connected && (
            <div className="flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>Heartbeat</span>
              </div>
              <span>
                {new Date(connectionState.lastHeartbeat).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default LiveUpdateIndicator;