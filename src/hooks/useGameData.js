/**
 * useGameData Hook
 * Central hook for managing game data state and fetching
 * Replaces embedded data logic from NFLDashboard.jsx
 */

import { useState, useEffect, useRef } from 'react';
import { GameDataService } from '../services/gameDataService.js';

/**
 * Custom hook for managing game data
 * @param {Object} options - Configuration options
 * @param {string} options.dataSource - Data source to use ('expert-observatory' | 'supabase')
 * @param {boolean} options.autoRefresh - Whether to auto-refresh data
 * @param {number} options.refreshInterval - Refresh interval in milliseconds
 * @returns {Object} Game data state and actions
 */
export function useGameData(options = {}) {
  const {
    dataSource = 'expert-observatory',
    autoRefresh = true,
    refreshInterval = 30000 // 30 seconds
  } = options;

  // State
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [dataSourceInfo, setDataSourceInfo] = useState(null);

  // Refs
  const gameDataService = useRef(null);
  const intervalRef = useRef(null);
  const loadedRef = useRef(false);

  // Initialize game data service
  useEffect(() => {
    try {
      gameDataService.current = new GameDataService(dataSource);
      setDataSourceInfo(gameDataService.current.getDataSourceInfo());
      console.log(`🎯 useGameData: Initialized with ${dataSource} data source`);
    } catch (error) {
      console.error('❌ useGameData: Failed to initialize GameDataService:', error);
      setError(`Failed to initialize data source: ${error.message}`);
    }
  }, [dataSource]);

  /**
   * Fetch games data
   */
  const fetchGames = async () => {
    if (!gameDataService.current) {
      console.warn('useGameData: GameDataService not initialized');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const gamesData = await gameDataService.current.fetchGames();

      setGames(gamesData);
      setLastUpdated(new Date());

      console.log(`✅ useGameData: Loaded ${gamesData.length} games from ${dataSource}`);

    } catch (error) {
      console.error('❌ useGameData: Failed to fetch games:', error);
      setError(error.message);

      // Don't clear existing games on error, just show error state
      if (games.length === 0) {
        setGames([]);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Manual refresh trigger
   */
  const refreshGames = () => {
    console.log('🔄 useGameData: Manual refresh triggered');
    fetchGames();
  };

  /**
   * Health check for current data source
   */
  const checkDataSourceHealth = async () => {
    if (!gameDataService.current) return false;

    try {
      return await gameDataService.current.healthCheck();
    } catch (error) {
      console.error('useGameData: Health check failed:', error);
      return false;
    }
  };

  // Initial data load
  useEffect(() => {
    if (gameDataService.current && !loadedRef.current) {
      loadedRef.current = true;
      fetchGames();
    }
  }, [gameDataService.current]);

  // Set up auto-refresh interval
  useEffect(() => {
    if (autoRefresh && !loading && gameDataService.current) {
      intervalRef.current = setInterval(() => {
        console.log(`🔄 useGameData: Auto-refresh (${dataSource})`);
        fetchGames();
      }, refreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }
  }, [autoRefresh, refreshInterval, loading, dataSource]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Sort games by priority (live, scheduled, final)
  const sortedGames = games.sort((a, b) => {
    const statusPriority = { live: 0, scheduled: 1, final: 2 };
    const aPriority = statusPriority[a.status] ?? 3;
    const bPriority = statusPriority[b.status] ?? 3;

    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }

    // Within same status, sort by time
    if (a.status === 'scheduled' && b.status === 'scheduled') {
      return new Date(a.startTime || 0) - new Date(b.startTime || 0);
    }

    if (a.status === 'final' && b.status === 'final') {
      return new Date(b.startTime || 0) - new Date(a.startTime || 0);
    }

    return 0;
  });

  return {
    // Data
    games: sortedGames,
    loading,
    error,
    lastUpdated,
    dataSourceInfo,

    // Actions
    refreshGames,
    checkDataSourceHealth,

    // Status
    hasGames: games.length > 0,
    isHealthy: !error,

    // Metadata for debugging
    totalGames: games.length,
    gamesByStatus: {
      live: games.filter(g => g.status === 'live').length,
      scheduled: games.filter(g => g.status === 'scheduled').length,
      final: games.filter(g => g.status === 'final').length
    }
  };
}

export default useGameData;