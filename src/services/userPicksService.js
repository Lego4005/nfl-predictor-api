// User Picks Service - Handles API calls for user picks functionality

const API_BASE_URL = 'http://127.0.0.1:8084/api';

class UserPicksService {
  constructor() {
    this.userId = 'default_user'; // In a real app, this would come from auth
  }

  /**
   * Submit user picks to the backend
   * @param {Array} picks - Array of pick objects
   * @returns {Promise} Response from API
   */
  async submitPicks(picks) {
    try {
      const response = await fetch(`${API_BASE_URL}/user-picks/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          picks: picks,
          userId: this.userId
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting picks:', error);
      throw error;
    }
  }

  /**
   * Get all user picks
   * @returns {Promise} User picks data
   */
  async getUserPicks() {
    try {
      const response = await fetch(`${API_BASE_URL}/user-picks?user_id=${this.userId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.picks || [];
    } catch (error) {
      console.error('Error fetching user picks:', error);
      throw error;
    }
  }

  /**
   * Delete a specific pick
   * @param {string} pickId - ID of the pick to delete
   * @returns {Promise} Response from API
   */
  async deletePick(pickId) {
    try {
      const response = await fetch(`${API_BASE_URL}/user-picks/${pickId}?user_id=${this.userId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting pick:', error);
      throw error;
    }
  }

  /**
   * Get user picks statistics
   * @returns {Promise} Statistics data
   */
  async getPicksStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/user-picks/stats?user_id=${this.userId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.stats || {};
    } catch (error) {
      console.error('Error fetching picks stats:', error);
      throw error;
    }
  }

  /**
   * Check if the API server is reachable
   * @returns {Promise<boolean>} True if server is reachable
   */
  async checkServerHealth() {
    try {
      const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`, {
        method: 'GET',
        timeout: 5000
      });
      return response.ok;
    } catch (error) {
      console.warn('Server health check failed:', error);
      return false;
    }
  }

  /**
   * Set user ID (useful for multi-user scenarios)
   * @param {string} userId - User identifier
   */
  setUserId(userId) {
    this.userId = userId;
  }

  /**
   * Get current user ID
   * @returns {string} Current user ID
   */
  getUserId() {
    return this.userId;
  }

  /**
   * Validate picks before submission
   * @param {Array} picks - Array of picks to validate
   * @returns {Object} Validation result with errors if any
   */
  validatePicks(picks) {
    const errors = [];
    const confidenceLevels = picks.map(p => p.confidence);

    // Check for empty picks
    if (!picks || picks.length === 0) {
      errors.push('No picks provided');
      return { isValid: false, errors };
    }

    // Check for duplicate confidence levels
    const uniqueConfidences = new Set(confidenceLevels);
    if (confidenceLevels.length !== uniqueConfidences.size) {
      errors.push('Each game must have a unique confidence level');
    }

    // Check confidence range and required fields
    picks.forEach((pick, index) => {
      if (!pick.gameId) {
        errors.push(`Pick ${index + 1}: Game ID is required`);
      }
      if (!pick.winner) {
        errors.push(`Pick ${index + 1}: Winner selection is required`);
      }
      if (!pick.confidence || pick.confidence < 1 || pick.confidence > 10) {
        errors.push(`Pick ${index + 1}: Confidence must be between 1 and 10`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

// Create singleton instance
const userPicksService = new UserPicksService();

export default userPicksService;