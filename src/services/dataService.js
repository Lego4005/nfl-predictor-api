/**
 * Data Service Layer for NFL Dashboard
 * Handles API calls, data transformation, and integration with caching layer
 */

import { DataTransformer } from '@/utils/dataTransformer';
import { cacheManager } from '@/utils/cacheManager';

/**
 * Base API configuration
 */
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:3001/api',
  timeout: 10000,
  retries: 3,
  retryDelay: 1000
};

/**
 * API endpoints configuration
 */
const ENDPOINTS = {
  games: '/games',
  rankings: '/rankings',
  experts: '/experts',
  performance: '/performance',
  weather: '/weather',
  odds: '/odds'
};

/**
 * HTTP client with retry logic
 */
class HTTPClient {
  static async request(url, options = {}) {
    const config = {
      timeout: API_CONFIG.timeout,
      ...options
    };

    let lastError;
    
    for (let attempt = 1; attempt <= API_CONFIG.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);

        const response = await fetch(url, {
          ...config,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
      } catch (error) {
        lastError = error;
        
        if (attempt < API_CONFIG.retries) {
          await this.delay(API_CONFIG.retryDelay * attempt);
        }
      }
    }

    throw lastError;
  }

  static async get(endpoint, params = {}) {
    const url = new URL(`${API_CONFIG.baseURL}${endpoint}`);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });

    return this.request(url.toString());
  }

  static async post(endpoint, data) {
    return this.request(`${API_CONFIG.baseURL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
  }

  static delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Data Service class
 */
export class DataService {
  /**
   * Fetch games for a specific season and week
   * @param {number} season - NFL season year
   * @param {number} week - Week number
   * @returns {Promise<Array>} Transformed games data
   */
  static async getGames(season, week) {
    const cacheKey = `games_${season}_${week}`;
    
    try {
      // Check cache first
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }

      // Fetch from API
      const rawData = await HTTPClient.get(ENDPOINTS.games, { season, week });
      
      // Transform data
      const transformedData = DataTransformer.transformGames(rawData.games || rawData);
      
      // Cache transformed data
      cacheManager.set(cacheKey, transformedData, 300000); // 5 minutes
      
      return transformedData;
    } catch (error) {
      console.error('Error fetching games:', error);
      
      // Return cached data if available, even if expired
      const staleData = cacheManager.get(cacheKey, true);
      if (staleData) {
        return staleData;
      }
      
      // Return mock data as fallback
      return this.getMockGames(season, week);
    }
  }

  /**
   * Fetch power rankings for a specific season and week
   * @param {number} season - NFL season year
   * @param {number} week - Week number
   * @returns {Promise<Array>} Transformed rankings data
   */
  static async getRankings(season, week) {
    const cacheKey = `rankings_${season}_${week}`;
    
    try {
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }

      const rawData = await HTTPClient.get(ENDPOINTS.rankings, { season, week });
      const transformedData = DataTransformer.transformRankings(rawData.rankings || rawData);
      
      cacheManager.set(cacheKey, transformedData, 600000); // 10 minutes
      
      return transformedData;
    } catch (error) {
      console.error('Error fetching rankings:', error);
      
      const staleData = cacheManager.get(cacheKey, true);
      if (staleData) {
        return staleData;
      }
      
      return this.getMockRankings();
    }
  }

  /**
   * Fetch AI experts data
   * @returns {Promise<Array>} Transformed experts data
   */
  static async getExperts() {
    const cacheKey = 'experts';
    
    try {
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }

      const rawData = await HTTPClient.get(ENDPOINTS.experts);
      const transformedData = DataTransformer.transformExperts(rawData.experts || rawData);
      
      cacheManager.set(cacheKey, transformedData, 900000); // 15 minutes
      
      return transformedData;
    } catch (error) {
      console.error('Error fetching experts:', error);
      
      const staleData = cacheManager.get(cacheKey, true);
      if (staleData) {
        return staleData;
      }
      
      return this.getMockExperts();
    }
  }

  /**
   * Fetch performance metrics
   * @returns {Promise<Object>} Performance data
   */
  static async getPerformance() {
    const cacheKey = 'performance';
    
    try {
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }

      const rawData = await HTTPClient.get(ENDPOINTS.performance);
      const transformedData = this.transformPerformance(rawData);
      
      cacheManager.set(cacheKey, transformedData, 1800000); // 30 minutes
      
      return transformedData;
    } catch (error) {
      console.error('Error fetching performance:', error);
      
      const staleData = cacheManager.get(cacheKey, true);
      if (staleData) {
        return staleData;
      }
      
      return this.getMockPerformance();
    }
  }

  /**
   * Fetch weather data for games
   * @param {Array} gameIds - Array of game IDs
   * @returns {Promise<Object>} Weather data by game ID
   */
  static async getWeather(gameIds) {
    const cacheKey = `weather_${gameIds.join('_')}`;
    
    try {
      const cachedData = cacheManager.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }

      const rawData = await HTTPClient.post(ENDPOINTS.weather, { gameIds });
      const transformedData = this.transformWeather(rawData);
      
      cacheManager.set(cacheKey, transformedData, 3600000); // 1 hour
      
      return transformedData;
    } catch (error) {
      console.error('Error fetching weather:', error);
      return {};
    }
  }

  /**
   * Batch fetch multiple data types
   * @param {Object} requests - Object with data type keys and parameters
   * @returns {Promise<Object>} Object with all requested data
   */
  static async batchFetch(requests) {
    const promises = {};
    
    if (requests.games) {
      promises.games = this.getGames(requests.games.season, requests.games.week);
    }
    
    if (requests.rankings) {
      promises.rankings = this.getRankings(requests.rankings.season, requests.rankings.week);
    }
    
    if (requests.experts) {
      promises.experts = this.getExperts();
    }
    
    if (requests.performance) {
      promises.performance = this.getPerformance();
    }

    try {
      const results = await Promise.allSettled(Object.entries(promises).map(
        async ([key, promise]) => [key, await promise]
      ));

      const data = {};
      results.forEach((result) => {
        if (result.status === 'fulfilled') {
          const [key, value] = result.value;
          data[key] = value;
        }
      });

      return data;
    } catch (error) {
      console.error('Error in batch fetch:', error);
      return {};
    }
  }

  /**
   * Transform performance data
   * @param {Object} rawData - Raw performance data
   * @returns {Object} Transformed performance data
   */
  static transformPerformance(rawData) {
    if (!rawData || typeof rawData !== 'object') {
      return this.getMockPerformance();
    }

    return {
      overallAccuracy: DataTransformer.sanitizeNumber(rawData.overallAccuracy, 0.68, 0, 1),
      correctPredictions: DataTransformer.sanitizeNumber(rawData.correctPredictions, 0),
      totalPredictions: DataTransformer.sanitizeNumber(rawData.totalPredictions, 0),
      roi: DataTransformer.sanitizeNumber(rawData.roi, 0),
      categories: Array.isArray(rawData.categories) ? rawData.categories.map(cat => ({
        name: DataTransformer.sanitizeString(cat.name, 'Unknown'),
        accuracy: DataTransformer.sanitizeNumber(cat.accuracy, 0.5, 0, 1),
        count: DataTransformer.sanitizeNumber(cat.count, 0),
        trend: DataTransformer.standardizeTrend(cat.trend),
        best: DataTransformer.sanitizeString(cat.best, 'N/A')
      })) : [],
      _metadata: {
        type: 'performance',
        transformedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }

  /**
   * Transform weather data
   * @param {Object} rawData - Raw weather data
   * @returns {Object} Transformed weather data
   */
  static transformWeather(rawData) {
    if (!rawData || typeof rawData !== 'object') {
      return {};
    }

    const transformed = {};
    
    Object.entries(rawData).forEach(([gameId, weather]) => {
      transformed[gameId] = DataTransformer.transformWeather(weather);
    });

    return transformed;
  }

  /**
   * Clear all cached data
   */
  static clearCache() {
    cacheManager.clear();
  }

  /**
   * Clear specific cache entries
   * @param {Array} keys - Cache keys to clear
   */
  static clearCacheKeys(keys) {
    keys.forEach(key => cacheManager.delete(key));
  }

  /**
   * Get cache status
   * @returns {Object} Cache statistics
   */
  static getCacheStatus() {
    return cacheManager.getStats();
  }

  // Mock data methods for fallback

  /**
   * Get mock games data
   * @param {number} season - Season year
   * @param {number} week - Week number
   * @returns {Array} Mock games
   */
  static getMockGames(season, week) {
    return [
      DataTransformer.transformGame({
        id: `${season}_W${week}_GB_CHI`,
        homeTeam: 'CHI',
        awayTeam: 'GB',
        startTime: new Date(Date.now() + 86400000).toISOString(),
        spread: -3.5,
        modelSpread: -2.5,
        overUnder: 45.5,
        modelTotal: 43.2,
        venue: 'Soldier Field',
        weather: { temp: 72, wind: 8, humidity: 65 }
      }),
      DataTransformer.transformGame({
        id: `${season}_W${week}_KC_BUF`,
        homeTeam: 'BUF',
        awayTeam: 'KC',
        startTime: new Date(Date.now() + 90000000).toISOString(),
        spread: -2.5,
        modelSpread: -4.0,
        overUnder: 48.5,
        modelTotal: 46.8,
        venue: 'Highmark Stadium',
        weather: { temp: 78, wind: 12, humidity: 55 }
      })
    ];
  }

  /**
   * Get mock rankings data
   * @returns {Array} Mock rankings
   */
  static getMockRankings() {
    return [
      DataTransformer.transformRanking({
        team: 'KC',
        rank: 1,
        lastWeek: 1,
        record: '5-1',
        elo: 1650,
        offensiveEPA: 0.25,
        defensiveEPA: -0.18,
        sos: 0.45
      }),
      DataTransformer.transformRanking({
        team: 'SF',
        rank: 2,
        lastWeek: 3,
        record: '4-2',
        elo: 1625,
        offensiveEPA: 0.22,
        defensiveEPA: -0.15,
        sos: 0.52
      }),
      DataTransformer.transformRanking({
        team: 'BUF',
        rank: 3,
        lastWeek: 2,
        record: '4-2',
        elo: 1615,
        offensiveEPA: 0.18,
        defensiveEPA: -0.20,
        sos: 0.48
      })
    ];
  }

  /**
   * Get mock experts data
   * @returns {Array} Mock experts
   */
  static getMockExperts() {
    return [
      DataTransformer.transformExpert({
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
        specialization: ['game_outcome', 'betting_markets'],
        joinDate: '2023-01-15',
        totalVotes: 142,
        consensusAlignment: 0.78
      }),
      DataTransformer.transformExpert({
        expertId: 'expert_2',
        expertName: 'Weather Wizard',
        overallAccuracy: 0.68,
        recentTrend: 'stable',
        voteWeight: {
          expertId: 'expert_2',
          overallWeight: 0.75,
          accuracyComponent: 0.70,
          recentPerformanceComponent: 0.65,
          confidenceComponent: 0.80,
          councilTenureComponent: 0.85,
          normalizedWeight: 0.75
        },
        specialization: ['situational_analysis'],
        joinDate: '2023-03-22',
        totalVotes: 98,
        consensusAlignment: 0.65
      })
    ];
  }

  /**
   * Get mock performance data
   * @returns {Object} Mock performance
   */
  static getMockPerformance() {
    return {
      overallAccuracy: 0.732,
      correctPredictions: 356,
      totalPredictions: 487,
      roi: 0.147,
      categories: [
        {
          name: 'Spread',
          accuracy: 0.685,
          count: 156,
          trend: 'up',
          best: 'Home Favorites'
        },
        {
          name: 'Totals',
          accuracy: 0.713,
          count: 145,
          trend: 'down',
          best: 'Unders in Wind'
        },
        {
          name: 'Moneyline',
          accuracy: 0.821,
          count: 186,
          trend: 'steady',
          best: 'Road Dogs'
        }
      ],
      _metadata: {
        type: 'performance',
        transformedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }
}

export default DataService;