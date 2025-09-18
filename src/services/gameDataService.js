/**
 * Game Data Service
 * Provides unified interface for game data from different sources
 * Handles data transformation and score extraction
 */

import { ExpertObservatoryAPI } from './api/expertObservatoryApi.js';
import { GameScoreService } from './gameScoreService.js';

export class GameDataService {
  constructor(dataSource = 'expert-observatory') {
    this.dataSource = dataSource;
    this.initializeAPI(dataSource);
  }

  /**
   * Initialize the appropriate API client based on data source
   * @param {string} dataSource - Data source identifier
   */
  initializeAPI(dataSource) {
    switch (dataSource) {
      case 'expert-observatory':
        this.api = new ExpertObservatoryAPI();
        break;
      case 'supabase':
        // Keep for fallback - would need to import SupabaseAPI
        this.api = null; // Implement if needed
        break;
      default:
        throw new Error(`Unsupported data source: ${dataSource}`);
    }
  }

  /**
   * Fetch games from the configured data source
   * @returns {Promise<Array>} Array of transformed game objects
   */
  async fetchGames() {
    try {
      const rawGames = await this.api.fetchGames();
      return this.transformGamesData(rawGames);
    } catch (error) {
      console.error(`❌ GameDataService: Failed to fetch games from ${this.dataSource}:`, error);
      throw error;
    }
  }

  /**
   * Transform raw game data to unified format for frontend
   * @param {Array} rawGames - Raw games from API
   * @returns {Array} Transformed games array
   */
  transformGamesData(rawGames) {
    if (!Array.isArray(rawGames)) {
      console.warn('GameDataService: Expected array of games, got:', typeof rawGames);
      return [];
    }

    return rawGames.map(game => this.transformGameData(game));
  }

  /**
   * Transform single game object to unified format
   * @param {Object} game - Raw game data
   * @returns {Object} Transformed game object
   */
  transformGameData(game) {
    const status = GameScoreService.determineGameStatus(game);
    const scoreData = GameScoreService.extractScoresFromExpertPredictions(game);
    const predictionData = GameScoreService.extractPredictionData(game);

    return {
      // Basic game info
      id: game.game_id,
      homeTeam: game.home_team,
      awayTeam: game.away_team,
      status: status,

      // Scores (only show for final games)
      homeScore: status === 'final' ? scoreData.homeScore : 0,
      awayScore: status === 'final' ? scoreData.awayScore : 0,

      // Timing info
      startTime: game.date,
      gameTime: game.date,
      quarter: 0, // Not available in Expert Observatory API
      clock: 0,
      time: status === 'final' ? 'FINAL' : 'TBD',

      // AI Predictions
      hasAIPrediction: predictionData.hasAIPrediction,
      homeWinProb: predictionData.homeWinProb,
      awayWinProb: predictionData.awayWinProb,
      prediction: predictionData.prediction,

      // Additional data for components
      aiPrediction: predictionData,
      consensus: scoreData.consensus,

      // Raw expert predictions for detailed analysis
      expertPredictions: game.expert_predictions || []
    };
  }

  /**
   * Health check for the current data source
   * @returns {Promise<boolean>} True if data source is healthy
   */
  async healthCheck() {
    try {
      if (this.api && typeof this.api.healthCheck === 'function') {
        return await this.api.healthCheck();
      }
      return true; // Assume healthy if no health check method
    } catch (error) {
      console.error(`GameDataService: Health check failed for ${this.dataSource}:`, error);
      return false;
    }
  }

  /**
   * Get data source information
   * @returns {Object} Data source metadata
   */
  getDataSourceInfo() {
    return {
      source: this.dataSource,
      apiClient: this.api?.constructor?.name || 'Unknown',
      features: this.getDataSourceFeatures()
    };
  }

  /**
   * Get features supported by current data source
   * @returns {Object} Feature availability
   */
  getDataSourceFeatures() {
    switch (this.dataSource) {
      case 'expert-observatory':
        return {
          realScores: true,
          expertPredictions: true,
          livegames: false,
          quarterClock: false,
          consensus: true
        };
      case 'supabase':
        return {
          realScores: false,
          expertPredictions: true,
          livegames: true,
          quarterClock: true,
          consensus: false
        };
      default:
        return {};
    }
  }
}

export default GameDataService;