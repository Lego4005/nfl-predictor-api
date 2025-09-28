import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Bell, BellOff, AlertTriangle, 
  CheckCircle, Info, Zap, TrendingUp
} from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import type { LiveUpdateMessage } from '../../types/aiCouncil';

interface LiveUpdateNotificationsProps {
  updates: LiveUpdateMessage[];
  maxNotifications?: number;
  autoHideDelay?: number;
  onDismiss?: (updateId: string) => void;
  onDismissAll?: () => void;
  className?: string;
}

interface NotificationWithId extends LiveUpdateMessage {
  id: string;
  dismissed: boolean;
}

const LiveUpdateNotifications: React.FC<LiveUpdateNotificationsProps> = ({
  updates,
  maxNotifications = 5,
  autoHideDelay = 10000,
  onDismiss,
  onDismissAll,
  className = ''
}) => {
  const [notifications, setNotifications] = useState<NotificationWithId[]>([]);
  const [isEnabled, setIsEnabled] = useState(true);

  // Convert updates to notifications with IDs
  useEffect(() => {
    const newNotifications = updates
      .filter(update => isEnabled)
      .map(update => ({
        ...update,
        id: `${update.type}-${update.timestamp}-${Math.random()}`,
        dismissed: false
      }))
      .slice(-maxNotifications);

    setNotifications(prev => {
      const existing = prev.filter(n => !n.dismissed);
      const combined = [...existing, ...newNotifications];
      return combined.slice(-maxNotifications);
    });
  }, [updates, maxNotifications, isEnabled]);

  // Auto-hide notifications
  useEffect(() => {
    if (autoHideDelay <= 0) return;

    const timers = notifications.map(notification => {
      if (notification.dismissed) return null;
      
      return setTimeout(() => {
        handleDismiss(notification.id);
      }, autoHideDelay);
    });

    return () => {
      timers.forEach(timer => timer && clearTimeout(timer));
    };
  }, [notifications, autoHideDelay]);

  const handleDismiss = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n =>
        n.id === notificationId ? { ...n, dismissed: true } : n
      )
    );
    onDismiss?.(notificationId);
  };

  const handleDismissAll = () => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, dismissed: true }))
    );
    onDismissAll?.();
  };

  const getUpdateIcon = (type: string) => {
    switch (type) {
      case 'CONSENSUS_UPDATE':
        return CheckCircle;
      case 'PREDICTION_UPDATE':
        return TrendingUp;
      case 'EXPERT_UPDATE':
        return Info;
      case 'GAME_UPDATE':
        return Zap;
      case 'MARKET_MOVEMENT':
        return TrendingUp;
      default:
        return Bell;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-l-red-500 bg-red-50 text-red-800';
      case 'medium':
        return 'border-l-yellow-500 bg-yellow-50 text-yellow-800';
      case 'low':
        return 'border-l-blue-500 bg-blue-50 text-blue-800';
      default:
        return 'border-l-gray-500 bg-gray-50 text-gray-800';
    }
  };

  const formatUpdateMessage = (update: LiveUpdateMessage) => {
    switch (update.type) {
      case 'CONSENSUS_UPDATE':
        return 'AI Council consensus has been updated';
      case 'PREDICTION_UPDATE':
        return `Expert predictions updated for ${update.affectedCategories.length} categories`;
      case 'EXPERT_UPDATE':
        return 'Expert performance metrics updated';
      case 'GAME_UPDATE':
        return 'Live game data updated';
      case 'MARKET_MOVEMENT':
        return 'Betting market lines have moved';
      default:
        return 'New update received';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const updateTime = new Date(timestamp);
    const diffMs = now.getTime() - updateTime.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    
    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    return `${Math.floor(diffSeconds / 3600)}h ago`;
  };

  const activeNotifications = notifications.filter(n => !n.dismissed);

  if (!isEnabled || activeNotifications.length === 0) {
    return null;
  }

  return (
    <div className={`fixed top-4 right-4 z-50 space-y-2 ${className}`}>
      {/* Notification Controls */}
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsEnabled(!isEnabled)}
          className="bg-white shadow-md"
        >
          {isEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
        </Button>
        {activeNotifications.length > 1 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleDismissAll}
            className="bg-white shadow-md"
          >
            Clear All
          </Button>
        )}
      </div>

      {/* Notifications */}
      <AnimatePresence>
        {activeNotifications.map((notification, index) => {
          const IconComponent = getUpdateIcon(notification.type);
          const priorityClass = getPriorityColor(notification.priority);
          
          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 300, scale: 0.8 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 300, scale: 0.8 }}
              transition={{ 
                type: "spring", 
                stiffness: 300, 
                damping: 30,
                delay: index * 0.1 
              }}
              className="w-80"
            >
              <Card className={`border-l-4 ${priorityClass} shadow-lg`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="mt-0.5">
                        <IconComponent className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm mb-1">
                          {formatUpdateMessage(notification)}
                        </div>
                        
                        {notification.affectedCategories.length > 0 && (
                          <div className="text-xs opacity-75 mb-2">
                            Categories: {notification.affectedCategories.slice(0, 2).join(', ')}
                            {notification.affectedCategories.length > 2 && 
                              ` +${notification.affectedCategories.length - 2} more`
                            }
                          </div>
                        )}
                        
                        <div className="flex items-center gap-2">
                          <Badge 
                            variant="outline" 
                            className="text-xs"
                          >
                            {notification.priority}
                          </Badge>
                          <span className="text-xs opacity-60">
                            {formatTimeAgo(notification.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDismiss(notification.id)}
                      className="h-6 w-6 p-0 shrink-0"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* Notification Count Badge */}
      {activeNotifications.length > maxNotifications && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="fixed top-2 right-2 z-60"
        >
          <Badge className="bg-red-600 text-white text-xs px-2 py-1">
            +{activeNotifications.length - maxNotifications}
          </Badge>
        </motion.div>
      )}
    </div>
  );
};

export default LiveUpdateNotifications;