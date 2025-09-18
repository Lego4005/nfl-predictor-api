/**
 * NFL Week Calculator - Handles Tuesday-Monday weekly cycles
 * NFL weeks run Tuesday 3:00 AM ET through Monday 11:59 PM ET
 * This matches NFL's official schedule release and team preparation cycles
 */

/**
 * NFL Season configuration for 2025-2026
 */
const NFL_SEASON_2025 = {
  // First Tuesday of the 2025 season (week 1 starts)
  SEASON_START: new Date('2025-09-02T07:00:00Z'), // Tuesday, Sept 2, 2025 3:00 AM ET
  WEEK_1_FIRST_GAME: new Date('2025-09-04T23:15:00Z'), // Thursday, Sept 4, 2025 7:15 PM ET
  REGULAR_SEASON_WEEKS: 18,
  PLAYOFF_WEEKS: 5, // Wild Card, Divisional, Championship, Pro Bowl, Super Bowl
  SUPER_BOWL_DATE: new Date('2026-02-08T23:30:00Z'), // Sunday, Feb 8, 2026 6:30 PM ET
};

/**
 * Get the current NFL week number based on Tuesday-Monday cycles
 * @param {Date} currentDate - The date to calculate for (defaults to now)
 * @returns {Object} Week information
 */
export function getCurrentNFLWeek(currentDate = new Date()) {
  const now = new Date(currentDate);
  const seasonStart = NFL_SEASON_2025.SEASON_START;

  // Calculate milliseconds since season start
  const msSinceStart = now.getTime() - seasonStart.getTime();
  const daysSinceStart = Math.floor(msSinceStart / (1000 * 60 * 60 * 24));

  // Each NFL week is 7 days, starting on Tuesday
  const weekNumber = Math.floor(daysSinceStart / 7) + 1;

  // Determine week type and bounds
  let weekType, weekStart, weekEnd;

  if (weekNumber <= 0) {
    weekType = 'preseason';
    weekStart = new Date(seasonStart.getTime() - (7 * 24 * 60 * 60 * 1000));
    weekEnd = new Date(seasonStart.getTime() - 1);
  } else if (weekNumber <= NFL_SEASON_2025.REGULAR_SEASON_WEEKS) {
    weekType = 'regular';
    weekStart = new Date(seasonStart.getTime() + ((weekNumber - 1) * 7 * 24 * 60 * 60 * 1000));
    weekEnd = new Date(weekStart.getTime() + (7 * 24 * 60 * 60 * 1000) - 1);
  } else {
    weekType = 'playoff';
    const playoffWeek = weekNumber - NFL_SEASON_2025.REGULAR_SEASON_WEEKS;
    weekStart = new Date(seasonStart.getTime() + ((weekNumber - 1) * 7 * 24 * 60 * 60 * 1000));
    weekEnd = new Date(weekStart.getTime() + (7 * 24 * 60 * 60 * 1000) - 1);
  }

  return {
    weekNumber: Math.max(1, weekNumber),
    weekType,
    weekStart,
    weekEnd,
    isCurrentWeek: weekNumber === getCurrentWeekNumber(now),
    daysIntoWeek: daysSinceStart % 7,
    seasonProgress: Math.min(100, (weekNumber / NFL_SEASON_2025.REGULAR_SEASON_WEEKS) * 100)
  };
}

/**
 * Get the current week number (helper function)
 */
function getCurrentWeekNumber(date = new Date()) {
  const seasonStart = NFL_SEASON_2025.SEASON_START;
  const msSinceStart = date.getTime() - seasonStart.getTime();
  const daysSinceStart = Math.floor(msSinceStart / (1000 * 60 * 60 * 24));
  return Math.floor(daysSinceStart / 7) + 1;
}

/**
 * Get week boundaries for a specific week number
 * @param {number} weekNumber - The NFL week number
 * @returns {Object} Week boundaries
 */
export function getWeekBoundaries(weekNumber) {
  const seasonStart = NFL_SEASON_2025.SEASON_START;
  const weekStart = new Date(seasonStart.getTime() + ((weekNumber - 1) * 7 * 24 * 60 * 60 * 1000));
  const weekEnd = new Date(weekStart.getTime() + (7 * 24 * 60 * 60 * 1000) - 1);

  return {
    weekNumber,
    weekStart,
    weekEnd,
    isCurrentWeek: weekNumber === getCurrentWeekNumber(),
    weekType: getWeekType(weekNumber)
  };
}

/**
 * Determine if a game falls within the current NFL week
 * @param {Date|string} gameDate - The game date
 * @returns {boolean} True if game is in current week
 */
export function isGameInCurrentWeek(gameDate) {
  const game = new Date(gameDate);
  const currentWeek = getCurrentNFLWeek();

  return game >= currentWeek.weekStart && game <= currentWeek.weekEnd;
}

/**
 * Get all games for a specific NFL week
 * @param {Array} games - Array of game objects
 * @param {number} weekNumber - NFL week number (optional, defaults to current)
 * @returns {Array} Filtered games for the week
 */
export function getGamesForWeek(games, weekNumber = null) {
  const targetWeek = weekNumber ? getWeekBoundaries(weekNumber) : getCurrentNFLWeek();

  return games.filter(game => {
    const gameDate = new Date(game.date || game.commence_time);
    return gameDate >= targetWeek.weekStart && gameDate <= targetWeek.weekEnd;
  });
}

/**
 * Get week type based on week number
 * @param {number} weekNumber - NFL week number
 * @returns {string} Week type
 */
function getWeekType(weekNumber) {
  if (weekNumber <= 0) return 'preseason';
  if (weekNumber <= NFL_SEASON_2025.REGULAR_SEASON_WEEKS) return 'regular';
  return 'playoff';
}

/**
 * Get priority-based game filtering for smart display
 * @param {Array} games - Array of game objects
 * @returns {Object} Categorized games by priority
 */
export function getPriorityGames(games) {
  const now = new Date();
  const currentWeek = getCurrentNFLWeek();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const tomorrow = new Date(today.getTime() + (24 * 60 * 60 * 1000));

  // Filter games for current week
  const weekGames = getGamesForWeek(games);

  const categorized = {
    live: [],
    today: [],
    tomorrow: [],
    thisWeek: [],
    nextWeek: []
  };

  const nextWeek = getWeekBoundaries(currentWeek.weekNumber + 1);

  weekGames.forEach(game => {
    const gameDate = new Date(game.date || game.commence_time);
    const gameDay = new Date(gameDate.getFullYear(), gameDate.getMonth(), gameDate.getDate());

    // Check if game is live
    if (game.status === 'live' || game.status === 'in_progress') {
      categorized.live.push(game);
    }
    // Check if game is today
    else if (gameDay.getTime() === today.getTime()) {
      categorized.today.push(game);
    }
    // Check if game is tomorrow
    else if (gameDay.getTime() === tomorrow.getTime()) {
      categorized.tomorrow.push(game);
    }
    // Check if game is in current week
    else if (gameDate >= currentWeek.weekStart && gameDate <= currentWeek.weekEnd) {
      categorized.thisWeek.push(game);
    }
    // Check if game is in next week
    else if (gameDate >= nextWeek.weekStart && gameDate <= nextWeek.weekEnd) {
      categorized.nextWeek.push(game);
    }
  });

  return categorized;
}

/**
 * Get the next Tuesday 3 AM ET (NFL week reset time)
 * @param {Date} fromDate - Starting date (defaults to now)
 * @returns {Date} Next Tuesday 3 AM ET
 */
export function getNextWeekReset(fromDate = new Date()) {
  const date = new Date(fromDate);

  // Convert to ET (UTC-5 or UTC-4 depending on DST)
  const etOffset = isDST(date) ? -4 : -5;
  const etDate = new Date(date.getTime() + (etOffset * 60 * 60 * 1000));

  // Find next Tuesday
  const daysUntilTuesday = (2 - etDate.getDay() + 7) % 7 || 7; // 2 = Tuesday
  const nextTuesday = new Date(etDate.getTime() + (daysUntilTuesday * 24 * 60 * 60 * 1000));

  // Set to 3 AM
  nextTuesday.setHours(3, 0, 0, 0);

  // Convert back to UTC
  return new Date(nextTuesday.getTime() - (etOffset * 60 * 60 * 1000));
}

/**
 * Check if a date is during Daylight Saving Time
 * @param {Date} date - Date to check
 * @returns {boolean} True if DST is in effect
 */
function isDST(date) {
  const year = date.getFullYear();
  // DST in US: 2nd Sunday in March to 1st Sunday in November
  const dstStart = new Date(year, 2, 14 - new Date(year, 2, 1).getDay()); // 2nd Sunday in March
  const dstEnd = new Date(year, 10, 7 - new Date(year, 10, 1).getDay()); // 1st Sunday in November

  return date >= dstStart && date < dstEnd;
}

/**
 * Get display configuration for responsive game cards
 * @param {boolean} isMobile - Whether display is mobile
 * @param {Array} games - Available games
 * @returns {Object} Display configuration
 */
export function getDisplayConfig(isMobile = false, games = []) {
  const priorityGames = getPriorityGames(games);
  const maxCards = isMobile ? 8 : 16;

  // Priority order: Live > Today > Tomorrow > This Week
  let displayGames = [
    ...priorityGames.live,
    ...priorityGames.today,
    ...priorityGames.tomorrow,
    ...priorityGames.thisWeek.slice(0, maxCards - priorityGames.live.length - priorityGames.today.length - priorityGames.tomorrow.length)
  ];

  // If we have room, add next week games
  if (displayGames.length < maxCards) {
    displayGames = [...displayGames, ...priorityGames.nextWeek.slice(0, maxCards - displayGames.length)];
  }

  return {
    games: displayGames.slice(0, maxCards),
    totalAvailable: games.length,
    showing: Math.min(displayGames.length, maxCards),
    hasMore: games.length > maxCards,
    categories: {
      live: priorityGames.live.length,
      today: priorityGames.today.length,
      tomorrow: priorityGames.tomorrow.length,
      thisWeek: priorityGames.thisWeek.length,
      nextWeek: priorityGames.nextWeek.length
    }
  };
}

export default {
  getCurrentNFLWeek,
  getWeekBoundaries,
  isGameInCurrentWeek,
  getGamesForWeek,
  getPriorityGames,
  getNextWeekReset,
  getDisplayConfig
};