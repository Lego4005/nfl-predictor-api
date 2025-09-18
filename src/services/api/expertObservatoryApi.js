/**
 * Expert Observatory API Client
 * Handles communication with the Expert Observatory API on port 8003
 * Provides clean interface for fetching game predictions and scores
 */

export class ExpertObservatoryAPI {
  constructor(baseUrl = 'http://localhost:8003') {
    this.baseUrl = baseUrl;
  }

  /**
   * Fetch recent game predictions with expert analysis
   * @returns {Promise<Array>} Array of games with expert predictions
   */
  async fetchGames() {
    try {
      const response = await fetch(`${this.baseUrl}/api/predictions/recent`);

      if (!response.ok) {
        throw new Error(`Expert Observatory API error: ${response.status}`);
      }

      const games = await response.json();
      console.log(`✅ Expert Observatory API: Fetched ${games?.length || 0} games`);

      return games || [];
    } catch (error) {
      console.error('❌ Expert Observatory API error:', error);
      throw new Error(`Failed to fetch games from Expert Observatory: ${error.message}`);
    }
  }

  /**
   * Fetch expert predictions for specific game
   * @param {string} gameId - Game identifier
   * @returns {Promise<Object>} Game with expert predictions
   */
  async fetchGamePredictions(gameId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/predictions/game/${gameId}`);

      if (!response.ok) {
        throw new Error(`Expert Observatory API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Expert Observatory API error for game:', gameId, error);
      throw new Error(`Failed to fetch game predictions: ${error.message}`);
    }
  }

  /**
   * Fetch list of available experts
   * @returns {Promise<Array>} Array of expert profiles
   */
  async fetchExperts() {
    try {
      const response = await fetch(`${this.baseUrl}/api/experts`);

      if (!response.ok) {
        throw new Error(`Expert Observatory API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Expert Observatory API error fetching experts:', error);
      throw new Error(`Failed to fetch experts: ${error.message}`);
    }
  }

  /**
   * Health check for the Expert Observatory API
   * @returns {Promise<boolean>} True if API is healthy
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`, {
        method: 'GET',
        timeout: 5000
      });

      return response.ok;
    } catch (error) {
      console.warn('Expert Observatory API health check failed:', error);
      return false;
    }
  }
}

export default ExpertObservatoryAPI;