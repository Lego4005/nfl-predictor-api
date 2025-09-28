import { useState, useEffect, useCallback } from 'react';
import cacheManager from '../utils/cacheManager';

/**
 * React hook for caching data with automatic expiration
 * @param {string} key - Cache key
 * @param {any} initialValue - Initial value if not in cache
 * @param {number} ttl - Time to live in milliseconds
 * @returns {[any, Function, Function]} [value, setValue, clearCache]
 */
export const useCache = (key, initialValue = null, ttl = 300000) => {
  const [value, setValue] = useState(() => {
    const cached = cacheManager.get(key);
    return cached !== null ? cached : initialValue;
  });

  const setCachedValue = useCallback((newValue) => {
    cacheManager.set(key, newValue, ttl);
    setValue(newValue);
  }, [key, ttl]);

  const clearCache = useCallback(() => {
    cacheManager.delete(key);
    setValue(initialValue);
  }, [key, initialValue]);

  // Update state when cache changes (for external updates)
  useEffect(() => {
    const checkCache = () => {
      const cached = cacheManager.get(key);
      if (cached !== null && cached !== value) {
        setValue(cached);
      }
    };

    // Check cache periodically
    const interval = setInterval(checkCache, 1000);
    return () => clearInterval(interval);
  }, [key, value]);

  return [value, setCachedValue, clearCache];
};

/**
 * React hook for caching API data with appropriate TTL
 * @param {string} endpoint - API endpoint
 * @param {string} dataType - Type of data (games, rankings, etc.)
 * @param {any} initialValue - Initial value
 * @returns {[any, Function, boolean, Function]} [data, setData, loading, refresh]
 */
export const useApiCache = (endpoint, dataType, initialValue = null) => {
  const [data, setData] = useCache(`api:${endpoint}`, initialValue, getTTLForDataType(dataType));
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from API
      // For now, we'll simulate with mock data
      const mockData = generateMockData(dataType);
      cacheManager.set(`api:${endpoint}`, mockData, getTTLForDataType(dataType));
      setData(mockData);
    } catch (error) {
      console.error('Error refreshing cache:', error);
    } finally {
      setLoading(false);
    }
  }, [endpoint, dataType, setData]);

  return [data, setData, loading, refresh];
};

/**
 * Get appropriate TTL for data type
 * @param {string} dataType - Type of data
 * @returns {number} TTL in milliseconds
 */
const getTTLForDataType = (dataType) => {
  switch (dataType) {
    case 'games':
      return 30000; // 30 seconds for live games
    case 'rankings':
      return 300000; // 5 minutes for rankings
    case 'experts':
      return 600000; // 10 minutes for experts
    case 'performance':
      return 900000; // 15 minutes for performance
    case 'tools':
      return 1800000; // 30 minutes for tools data
    default:
      return 300000; // 5 minutes default
  }
};

/**
 * Generate mock data for demonstration
 * @param {string} dataType - Type of data to generate
 * @returns {any} Mock data
 */
const generateMockData = (dataType) => {
  switch (dataType) {
    case 'games':
      return [
        {
          id: '2025_W1_GB_CHI',
          homeTeam: 'CHI',
          awayTeam: 'GB',
          startTime: '2025-09-07T13:00:00Z',
          status: 'scheduled',
          homeScore: 0,
          awayScore: 0,
          spread: -3.5,
          modelSpread: -2.5,
          spreadMovement: 1.0,
          overUnder: 45.5,
          modelTotal: 43.2,
          homeWinProb: 0.62,
          awayWinProb: 0.38,
          ev: 0.08,
          confidence: 0.72,
          weather: { temp: 72, wind: 8, humidity: 65 },
          venue: 'Soldier Field'
        }
      ];
    case 'rankings':
      return [
        { 
          team: 'KC', 
          rank: 1, 
          lastWeek: 1, 
          movement: 0, 
          record: '5-1', 
          elo: 1650, 
          trend: 'up',
          offensiveEPA: 0.25,
          defensiveEPA: -0.18,
          sos: 0.45
        }
      ];
    case 'experts':
      return [
        {
          expertId: 'expert_1',
          expertName: 'Statistical Sage',
          overallAccuracy: 0.72,
          recentTrend: 'improving',
          voteWeight: {
            expertId: 'expert_1',
            overallWeight: 0.85,
            accuracyComponent: 0.75,
            recentPerformanceComponent: 0.80,
            confidenceComponent: 0.70,
            councilTenureComponent: 0.90,
            normalizedWeight: 0.85
          },
          predictions: [],
          specialization: ['game_outcome', 'betting_markets'],
          joinDate: '2023-01-15',
          totalVotes: 142,
          consensusAlignment: 0.78
        }
      ];
    default:
      return null;
  }
};

/**
 * Hook for caching component state with session persistence
 * @param {string} key - Storage key
 * @param {any} initialValue - Initial value
 * @returns {[any, Function]} [value, setValue]
 */
export const usePersistentCache = (key, initialValue) => {
  const [value, setValue] = useState(() => {
    try {
      const cached = cacheManager.get(key);
      if (cached !== null) {
        return cached;
      }
      
      // Try localStorage as fallback
      const stored = localStorage.getItem(key);
      if (stored !== null) {
        const parsed = JSON.parse(stored);
        cacheManager.set(key, parsed, 86400000); // 24 hours
        return parsed;
      }
      
      return initialValue;
    } catch (error) {
      console.warn('Error reading from cache/storage:', error);
      return initialValue;
    }
  });

  const setCachedValue = useCallback((newValue) => {
    try {
      cacheManager.set(key, newValue, 86400000); // 24 hours
      localStorage.setItem(key, JSON.stringify(newValue));
      setValue(newValue);
    } catch (error) {
      console.warn('Error writing to cache/storage:', error);
      setValue(newValue);
    }
  }, [key]);

  return [value, setCachedValue];
};

/**
 * Hook for caching expensive calculations
 * @param {Function} computeFn - Function to compute value
 * @param {Array} dependencies - Dependencies array
 * @param {string} key - Cache key
 * @param {number} ttl - Time to live in milliseconds
 * @returns {any} Computed value
 */
export const useCachedComputation = (computeFn, dependencies, key, ttl = 300000) => {
  const [value, setValue] = useState(() => {
    const cached = cacheManager.get(key);
    return cached !== null ? cached : undefined;
  });

  useEffect(() => {
    const cached = cacheManager.get(key);
    if (cached !== null) {
      setValue(cached);
      return;
    }

    const computed = computeFn();
    cacheManager.set(key, computed, ttl);
    setValue(computed);
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  return value;
};

export default useCache;