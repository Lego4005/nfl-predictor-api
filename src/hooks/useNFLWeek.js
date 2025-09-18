import { useState, useEffect, useMemo } from 'react';
import {
  getCurrentNFLWeek,
  getPriorityGames,
  getDisplayConfig,
  getNextWeekReset,
  isGameInCurrentWeek
} from '../utils/nflWeekCalculator';

/**
 * Custom hook for NFL week management and game filtering
 * Handles Tuesday-Monday weekly cycles and priority-based game display
 */
export function useNFLWeek(games = [], options = {}) {
  const {
    isMobile = false,
    autoRefresh = true,
    refreshInterval = 60000, // 1 minute
    maxCards = isMobile ? 8 : 16
  } = options;

  const [currentWeek, setCurrentWeek] = useState(() => getCurrentNFLWeek());
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [nextReset, setNextReset] = useState(() => getNextWeekReset());

  // Update current week info periodically
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      const newWeek = getCurrentNFLWeek();
      const now = new Date();

      setCurrentWeek(newWeek);
      setLastRefresh(now);

      // Check if we need to update next reset time
      if (now >= nextReset) {
        setNextReset(getNextWeekReset(now));
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, nextReset]);

  // Memoized game processing
  const processedGames = useMemo(() => {
    if (!games || games.length === 0) {
      return {
        priorityGames: { live: [], today: [], tomorrow: [], thisWeek: [], nextWeek: [] },
        displayConfig: { games: [], totalAvailable: 0, showing: 0, hasMore: false, categories: {} },
        weekGames: []
      };
    }

    // Filter and categorize games
    const priorityGames = getPriorityGames(games);
    const displayConfig = getDisplayConfig(isMobile, games);

    // Get all games for current week
    const weekGames = games.filter(game => isGameInCurrentWeek(game.date || game.commence_time));

    return {
      priorityGames,
      displayConfig,
      weekGames
    };
  }, [games, isMobile]);

  // Helper functions
  const refreshWeek = () => {
    setCurrentWeek(getCurrentNFLWeek());
    setLastRefresh(new Date());
  };

  const getTimeUntilReset = () => {
    const now = new Date();
    const msUntilReset = nextReset.getTime() - now.getTime();

    if (msUntilReset <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0 };

    const days = Math.floor(msUntilReset / (1000 * 60 * 60 * 24));
    const hours = Math.floor((msUntilReset % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((msUntilReset % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((msUntilReset % (1000 * 60)) / 1000);

    return { days, hours, minutes, seconds };
  };

  const getWeekStatus = () => {
    const now = new Date();
    const dayOfWeek = now.getDay(); // 0 = Sunday, 1 = Monday, 2 = Tuesday, etc.
    const timeUntilReset = getTimeUntilReset();

    let status = 'mid-week';
    let message = '';

    if (dayOfWeek === 2 && now.getHours() < 3) {
      status = 'reset-pending';
      message = `Week ${currentWeek.weekNumber} ending soon - new games loading`;
    } else if (dayOfWeek === 2 && now.getHours() >= 3 && timeUntilReset.days === 6) {
      status = 'fresh-week';
      message = `Week ${currentWeek.weekNumber} just started - fresh games available`;
    } else if (timeUntilReset.days <= 1) {
      status = 'week-ending';
      message = `Week ${currentWeek.weekNumber} ending in ${timeUntilReset.days}d ${timeUntilReset.hours}h`;
    } else {
      status = 'mid-week';
      message = `Week ${currentWeek.weekNumber} - ${currentWeek.weekType} season`;
    }

    return { status, message, timeUntilReset };
  };

  return {
    // Week information
    currentWeek,
    weekStatus: getWeekStatus(),
    nextReset,
    lastRefresh,

    // Game data
    ...processedGames,

    // Utilities
    refreshWeek,
    getTimeUntilReset,

    // Computed values
    hasLiveGames: processedGames.priorityGames.live.length > 0,
    hasTodayGames: processedGames.priorityGames.today.length > 0,
    totalGamesThisWeek: processedGames.weekGames.length,

    // Display state
    isAutoRefreshing: autoRefresh,
    maxCards
  };
}

/**
 * Simplified hook for just getting current week info
 */
export function useCurrentNFLWeek() {
  const [currentWeek, setCurrentWeek] = useState(() => getCurrentNFLWeek());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentWeek(getCurrentNFLWeek());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  return currentWeek;
}

/**
 * Hook for tracking when the next NFL week reset occurs
 */
export function useNFLWeekReset(callback = null) {
  const [nextReset, setNextReset] = useState(() => getNextWeekReset());
  const [isNearReset, setIsNearReset] = useState(false);

  useEffect(() => {
    const checkReset = () => {
      const now = new Date();
      const timeUntilReset = nextReset.getTime() - now.getTime();

      // If reset has passed, update to next reset
      if (timeUntilReset <= 0) {
        const newReset = getNextWeekReset(now);
        setNextReset(newReset);

        // Call callback if provided
        if (callback) {
          callback(newReset);
        }
      }

      // Set near reset flag (within 2 hours)
      setIsNearReset(timeUntilReset <= 2 * 60 * 60 * 1000 && timeUntilReset > 0);
    };

    // Check immediately
    checkReset();

    // Then check every minute
    const interval = setInterval(checkReset, 60000);

    return () => clearInterval(interval);
  }, [nextReset, callback]);

  return {
    nextReset,
    isNearReset,
    timeUntilReset: Math.max(0, nextReset.getTime() - new Date().getTime())
  };
}

export default useNFLWeek;