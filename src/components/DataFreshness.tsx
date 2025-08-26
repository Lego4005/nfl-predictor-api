import React from 'react';
import { DataFreshnessProps } from '../types/ui.types';
import { DataSource } from '../types/nfl.types';

const DataFreshness: React.FC<DataFreshnessProps> = ({
  timestamp,
  source,
  cached
}) => {
  const getTimeAgo = (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);

    if (diffMinutes < 1) {
      return 'just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    }
  };

  const getSourceDisplay = (source: DataSource): string => {
    const sourceNames = {
      [DataSource.ODDS_API]: 'Odds API',
      [DataSource.SPORTSDATA_IO]: 'SportsDataIO',
      [DataSource.ESPN_API]: 'ESPN',
      [DataSource.NFL_API]: 'NFL.com',
      [DataSource.RAPID_API]: 'RapidAPI',
      [DataSource.CACHE]: 'Cache',
      [DataSource.MOCK]: 'Mock Data'
    };
    
    return sourceNames[source] || source;
  };

  const getSourceColor = (source: DataSource): string => {
    if (source === DataSource.MOCK) {
      return '#f59e0b'; // amber
    } else if (cached) {
      return '#6b7280'; // gray
    } else {
      return '#10b981'; // green
    }
  };

  const getStatusIcon = (): string => {
    if (source === DataSource.MOCK) {
      return '🔧'; // mock data
    } else if (cached) {
      return '💾'; // cached
    } else {
      return '🔴'; // live
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '12px',
      color: '#6b7280',
      padding: '4px 8px',
      backgroundColor: '#f9fafb',
      borderRadius: '4px',
      border: '1px solid #e5e7eb'
    }}>
      <span>{getStatusIcon()}</span>
      
      <span style={{ color: getSourceColor(source) }}>
        {getSourceDisplay(source)}
      </span>
      
      <span>•</span>
      
      <span>
        {getTimeAgo(timestamp)}
      </span>

      {cached && (
        <>
          <span>•</span>
          <span style={{ color: '#6b7280' }}>
            cached
          </span>
        </>
      )}
    </div>
  );
};

export default DataFreshness;