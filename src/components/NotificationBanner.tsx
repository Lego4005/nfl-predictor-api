import React from 'react';
import { NotificationBannerProps, UINotification } from '../types/ui.types';
import { DataSource } from '../types/nfl.types';

const NotificationBanner: React.FC<NotificationBannerProps> = ({
  notifications,
  onDismiss,
  maxVisible = 3
}) => {
  if (!notifications || notifications.length === 0) {
    return null;
  }

  const visibleNotifications = notifications.slice(0, maxVisible);

  const getNotificationStyle = (type: string) => {
    const baseStyle = {
      padding: '12px 16px',
      marginBottom: '8px',
      borderRadius: '6px',
      border: '1px solid',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      fontSize: '14px',
      lineHeight: '1.4'
    };

    switch (type) {
      case 'error':
        return {
          ...baseStyle,
          backgroundColor: '#fef2f2',
          borderColor: '#fecaca',
          color: '#dc2626'
        };
      case 'warning':
        return {
          ...baseStyle,
          backgroundColor: '#fffbeb',
          borderColor: '#fed7aa',
          color: '#d97706'
        };
      case 'success':
        return {
          ...baseStyle,
          backgroundColor: '#f0fdf4',
          borderColor: '#bbf7d0',
          color: '#16a34a'
        };
      case 'info':
      default:
        return {
          ...baseStyle,
          backgroundColor: '#eff6ff',
          borderColor: '#bfdbfe',
          color: '#2563eb'
        };
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'error':
        return '⚠️';
      case 'warning':
        return '⚡';
      case 'success':
        return '✅';
      case 'info':
      default:
        return 'ℹ️';
    }
  };

  const formatMessage = (notification: any) => {
    let message = notification.message;
    
    // Add source information if available
    if (notification.source && notification.source !== DataSource.MOCK) {
      const sourceNames = {
        [DataSource.ODDS_API]: 'The Odds API',
        [DataSource.SPORTSDATA_IO]: 'SportsDataIO',
        [DataSource.ESPN_API]: 'ESPN API',
        [DataSource.NFL_API]: 'NFL.com API',
        [DataSource.RAPID_API]: 'RapidAPI',
        [DataSource.CACHE]: 'Cache'
      };
      
      const sourceName = sourceNames[notification.source as DataSource] || notification.source;
      message = `${sourceName}: ${message}`;
    }

    return message;
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      {visibleNotifications.map((notification, index) => (
        <div key={index} style={getNotificationStyle(notification.type)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{getIcon(notification.type)}</span>
            <span>{formatMessage(notification)}</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {notification.retryable && (
              <button
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'inherit',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  fontSize: '12px',
                  padding: '0'
                }}
                onClick={() => window.location.reload()}
              >
                Retry
              </button>
            )}
            
            {onDismiss && (
              <button
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'inherit',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: '0',
                  lineHeight: '1'
                }}
                onClick={() => onDismiss(index)}
                aria-label="Dismiss notification"
              >
                ×
              </button>
            )}
          </div>
        </div>
      ))}
      
      {notifications.length > maxVisible && (
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          textAlign: 'center',
          padding: '4px'
        }}>
          +{notifications.length - maxVisible} more notifications
        </div>
      )}
    </div>
  );
};

export default NotificationBanner;