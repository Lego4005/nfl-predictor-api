/**
 * Data Transformation Layer for NFL Dashboard
 * Handles transformation, validation, and normalization of data from various sources
 */

/**
 * Team abbreviation mappings and standardization
 */
const TEAM_MAPPINGS = {
  // Standard NFL team abbreviations
  'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF',
  'CAR': 'CAR', 'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE',
  'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GB': 'GB',
  'HOU': 'HOU', 'IND': 'IND', 'JAX': 'JAX', 'KC': 'KC',
  'LV': 'LV', 'LAC': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA',
  'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG',
  'NYJ': 'NYJ', 'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF',
  'SEA': 'SEA', 'TB': 'TB', 'TEN': 'TEN', 'WAS': 'WAS',
  
  // Alternative mappings
  'LAS': 'LV', 'OAK': 'LV', 'SD': 'LAC', 'STL': 'LAR',
  'WSH': 'WAS', 'GNB': 'GB', 'NWE': 'NE', 'NOR': 'NO',
  'SFO': 'SF', 'TAM': 'TB', 'JAC': 'JAX'
};

/**
 * Game status standardization
 */
const GAME_STATUS_MAPPINGS = {
  'scheduled': 'scheduled',
  'pregame': 'scheduled',
  'live': 'in_progress',
  'in-progress': 'in_progress',
  'inprogress': 'in_progress',
  'halftime': 'in_progress',
  'final': 'completed',
  'completed': 'completed',
  'finished': 'completed',
  'postponed': 'postponed',
  'cancelled': 'cancelled',
  'canceled': 'cancelled'
};

/**
 * Data validation schemas
 */
const VALIDATION_SCHEMAS = {
  game: {
    required: ['id', 'homeTeam', 'awayTeam', 'startTime'],
    optional: ['homeScore', 'awayScore', 'status', 'spread', 'overUnder', 'venue'],
    types: {
      id: 'string',
      homeTeam: 'string',
      awayTeam: 'string',
      startTime: 'string',
      homeScore: 'number',
      awayScore: 'number',
      spread: 'number',
      overUnder: 'number',
      venue: 'string'
    }
  },
  ranking: {
    required: ['team', 'rank', 'elo'],
    optional: ['record', 'movement', 'offensiveEPA', 'defensiveEPA', 'sos'],
    types: {
      team: 'string',
      rank: 'number',
      elo: 'number',
      movement: 'number',
      offensiveEPA: 'number',
      defensiveEPA: 'number',
      sos: 'number'
    }
  },
  expert: {
    required: ['expertId', 'expertName', 'overallAccuracy'],
    optional: ['recentTrend', 'voteWeight', 'specialization', 'totalVotes'],
    types: {
      expertId: 'string',
      expertName: 'string',
      overallAccuracy: 'number',
      recentTrend: 'string',
      totalVotes: 'number'
    }
  }
};

/**
 * Data transformation utilities
 */
export class DataTransformer {
  /**
   * Transform and validate game data
   * @param {Object} rawGame - Raw game data
   * @returns {Object} Transformed game data
   */
  static transformGame(rawGame) {
    try {
      // Validate required fields
      if (!this.validateObject(rawGame, VALIDATION_SCHEMAS.game)) {
        throw new Error('Invalid game data structure');
      }

      const transformed = {
        id: String(rawGame.id),
        homeTeam: this.standardizeTeam(rawGame.homeTeam),
        awayTeam: this.standardizeTeam(rawGame.awayTeam),
        startTime: this.standardizeDateTime(rawGame.startTime),
        status: this.standardizeGameStatus(rawGame.status || 'scheduled'),
        homeScore: this.sanitizeNumber(rawGame.homeScore, 0),
        awayScore: this.sanitizeNumber(rawGame.awayScore, 0),
        spread: this.sanitizeNumber(rawGame.spread),
        modelSpread: this.sanitizeNumber(rawGame.modelSpread),
        spreadMovement: this.calculateSpreadMovement(rawGame.spread, rawGame.modelSpread),
        overUnder: this.sanitizeNumber(rawGame.overUnder),
        modelTotal: this.sanitizeNumber(rawGame.modelTotal),
        venue: this.sanitizeString(rawGame.venue),
        weather: this.transformWeather(rawGame.weather),
        
        // Calculate derived fields
        homeWinProb: this.calculateWinProbability(rawGame, 'home'),
        awayWinProb: this.calculateWinProbability(rawGame, 'away'),
        ev: this.calculateExpectedValue(rawGame),
        confidence: this.calculateConfidence(rawGame)
      };

      return this.addMetadata(transformed, 'game');
    } catch (error) {
      console.error('Error transforming game data:', error);
      return this.createDefaultGame();
    }
  }

  /**
   * Transform ranking data
   * @param {Object} rawRanking - Raw ranking data
   * @returns {Object} Transformed ranking data
   */
  static transformRanking(rawRanking) {
    try {
      if (!this.validateObject(rawRanking, VALIDATION_SCHEMAS.ranking)) {
        throw new Error('Invalid ranking data structure');
      }

      const transformed = {
        team: this.standardizeTeam(rawRanking.team),
        rank: this.sanitizeNumber(rawRanking.rank, 1),
        lastWeek: this.sanitizeNumber(rawRanking.lastWeek, rawRanking.rank),
        movement: this.calculateMovement(rawRanking.rank, rawRanking.lastWeek),
        record: this.standardizeRecord(rawRanking.record),
        elo: this.sanitizeNumber(rawRanking.elo, 1500),
        trend: this.standardizeTrend(rawRanking.trend),
        offensiveEPA: this.sanitizeNumber(rawRanking.offensiveEPA, 0),
        defensiveEPA: this.sanitizeNumber(rawRanking.defensiveEPA, 0),
        sos: this.sanitizeNumber(rawRanking.sos, 0.5, 0, 1)
      };

      return this.addMetadata(transformed, 'ranking');
    } catch (error) {
      console.error('Error transforming ranking data:', error);
      return this.createDefaultRanking();
    }
  }

  /**
   * Transform expert data
   * @param {Object} rawExpert - Raw expert data
   * @returns {Object} Transformed expert data
   */
  static transformExpert(rawExpert) {
    try {
      if (!this.validateObject(rawExpert, VALIDATION_SCHEMAS.expert)) {
        throw new Error('Invalid expert data structure');
      }

      const transformed = {
        expertId: String(rawExpert.expertId),
        expertName: this.sanitizeString(rawExpert.expertName),
        overallAccuracy: this.sanitizeNumber(rawExpert.overallAccuracy, 0.5, 0, 1),
        recentTrend: this.standardizeTrend(rawExpert.recentTrend),
        voteWeight: this.transformVoteWeight(rawExpert.voteWeight),
        predictions: Array.isArray(rawExpert.predictions) ? rawExpert.predictions : [],
        specialization: Array.isArray(rawExpert.specialization) ? rawExpert.specialization : [],
        joinDate: this.standardizeDateTime(rawExpert.joinDate),
        totalVotes: this.sanitizeNumber(rawExpert.totalVotes, 0),
        consensusAlignment: this.sanitizeNumber(rawExpert.consensusAlignment, 0.5, 0, 1)
      };

      return this.addMetadata(transformed, 'expert');
    } catch (error) {
      console.error('Error transforming expert data:', error);
      return this.createDefaultExpert();
    }
  }

  /**
   * Batch transform games
   * @param {Array} rawGames - Array of raw game data
   * @returns {Array} Array of transformed games
   */
  static transformGames(rawGames) {
    if (!Array.isArray(rawGames)) {
      return [];
    }

    return rawGames
      .map(game => this.transformGame(game))
      .filter(game => game !== null)
      .sort((a, b) => new Date(a.startTime) - new Date(b.startTime));
  }

  /**
   * Batch transform rankings
   * @param {Array} rawRankings - Array of raw ranking data
   * @returns {Array} Array of transformed rankings
   */
  static transformRankings(rawRankings) {
    if (!Array.isArray(rawRankings)) {
      return [];
    }

    return rawRankings
      .map(ranking => this.transformRanking(ranking))
      .filter(ranking => ranking !== null)
      .sort((a, b) => a.rank - b.rank);
  }

  /**
   * Batch transform experts
   * @param {Array} rawExperts - Array of raw expert data
   * @returns {Array} Array of transformed experts
   */
  static transformExperts(rawExperts) {
    if (!Array.isArray(rawExperts)) {
      return [];
    }

    return rawExperts
      .map(expert => this.transformExpert(expert))
      .filter(expert => expert !== null);
  }

  // Utility methods

  /**
   * Standardize team abbreviation
   * @param {string} team - Team abbreviation
   * @returns {string} Standardized team abbreviation
   */
  static standardizeTeam(team) {
    if (!team || typeof team !== 'string') return 'UNK';
    const normalized = team.toUpperCase().trim();
    return TEAM_MAPPINGS[normalized] || normalized;
  }

  /**
   * Standardize game status
   * @param {string} status - Game status
   * @returns {string} Standardized status
   */
  static standardizeGameStatus(status) {
    if (!status || typeof status !== 'string') return 'scheduled';
    const normalized = status.toLowerCase().trim();
    return GAME_STATUS_MAPPINGS[normalized] || 'scheduled';
  }

  /**
   * Standardize date/time
   * @param {string|Date} dateTime - Date/time value
   * @returns {string} ISO string
   */
  static standardizeDateTime(dateTime) {
    if (!dateTime) return new Date().toISOString();
    
    try {
      const date = new Date(dateTime);
      if (isNaN(date.getTime())) {
        return new Date().toISOString();
      }
      return date.toISOString();
    } catch {
      return new Date().toISOString();
    }
  }

  /**
   * Sanitize numeric values
   * @param {any} value - Value to sanitize
   * @param {number} defaultValue - Default if invalid
   * @param {number} min - Minimum allowed value
   * @param {number} max - Maximum allowed value
   * @returns {number} Sanitized number
   */
  static sanitizeNumber(value, defaultValue = 0, min = -Infinity, max = Infinity) {
    const num = Number(value);
    if (isNaN(num)) return defaultValue;
    return Math.max(min, Math.min(max, num));
  }

  /**
   * Sanitize string values
   * @param {any} value - Value to sanitize
   * @param {string} defaultValue - Default if invalid
   * @returns {string} Sanitized string
   */
  static sanitizeString(value, defaultValue = '') {
    if (typeof value !== 'string') return defaultValue;
    return value.trim() || defaultValue;
  }

  /**
   * Calculate spread movement
   * @param {number} market - Market spread
   * @param {number} model - Model spread
   * @returns {number} Movement value
   */
  static calculateSpreadMovement(market, model) {
    if (typeof market !== 'number' || typeof model !== 'number') return 0;
    return Number((market - model).toFixed(1));
  }

  /**
   * Calculate win probability
   * @param {Object} game - Game data
   * @param {string} team - 'home' or 'away'
   * @returns {number} Win probability
   */
  static calculateWinProbability(game, team) {
    // Simplified probability calculation
    const spread = this.sanitizeNumber(game.spread, 0);
    const homeProb = 0.5 + (spread * -0.03); // Rough conversion
    
    if (team === 'home') {
      return Math.max(0.1, Math.min(0.9, homeProb));
    } else {
      return Math.max(0.1, Math.min(0.9, 1 - homeProb));
    }
  }

  /**
   * Calculate expected value
   * @param {Object} game - Game data
   * @returns {number} Expected value
   */
  static calculateExpectedValue(game) {
    // Simplified EV calculation
    const spread = this.sanitizeNumber(game.spread, 0);
    const modelSpread = this.sanitizeNumber(game.modelSpread, spread);
    const difference = Math.abs(spread - modelSpread);
    
    return Math.max(0, Math.min(0.2, difference * 0.02));
  }

  /**
   * Calculate confidence
   * @param {Object} game - Game data
   * @returns {number} Confidence level
   */
  static calculateConfidence(game) {
    // Simplified confidence calculation
    const ev = this.calculateExpectedValue(game);
    return Math.max(0.3, Math.min(0.9, 0.6 + (ev * 2)));
  }

  /**
   * Transform weather data
   * @param {Object} weather - Weather data
   * @returns {Object} Transformed weather
   */
  static transformWeather(weather) {
    if (!weather || typeof weather !== 'object') {
      return { temp: 70, wind: 5, humidity: 50 };
    }

    return {
      temp: this.sanitizeNumber(weather.temp, 70, -20, 120),
      wind: this.sanitizeNumber(weather.wind, 5, 0, 50),
      humidity: this.sanitizeNumber(weather.humidity, 50, 0, 100)
    };
  }

  /**
   * Standardize record format
   * @param {string} record - Team record
   * @returns {string} Standardized record
   */
  static standardizeRecord(record) {
    if (!record || typeof record !== 'string') return '0-0';
    const cleaned = record.trim().replace(/[^\d-]/g, '');
    if (!/^\d+-\d+(-\d+)?$/.test(cleaned)) return '0-0';
    return cleaned;
  }

  /**
   * Standardize trend
   * @param {string} trend - Trend value
   * @returns {string} Standardized trend
   */
  static standardizeTrend(trend) {
    if (!trend || typeof trend !== 'string') return 'steady';
    const normalized = trend.toLowerCase().trim();
    if (['up', 'improving', 'rising'].includes(normalized)) return 'up';
    if (['down', 'declining', 'falling'].includes(normalized)) return 'down';
    return 'steady';
  }

  /**
   * Calculate ranking movement
   * @param {number} current - Current rank
   * @param {number} previous - Previous rank
   * @returns {number} Movement
   */
  static calculateMovement(current, previous) {
    if (typeof current !== 'number' || typeof previous !== 'number') return 0;
    return previous - current; // Positive means moved up
  }

  /**
   * Transform vote weight data
   * @param {Object} voteWeight - Vote weight data
   * @returns {Object} Transformed vote weight
   */
  static transformVoteWeight(voteWeight) {
    if (!voteWeight || typeof voteWeight !== 'object') {
      return {
        expertId: '',
        overallWeight: 0.5,
        accuracyComponent: 0.5,
        recentPerformanceComponent: 0.5,
        confidenceComponent: 0.5,
        councilTenureComponent: 0.5,
        normalizedWeight: 0.5
      };
    }

    return {
      expertId: String(voteWeight.expertId || ''),
      overallWeight: this.sanitizeNumber(voteWeight.overallWeight, 0.5, 0, 1),
      accuracyComponent: this.sanitizeNumber(voteWeight.accuracyComponent, 0.5, 0, 1),
      recentPerformanceComponent: this.sanitizeNumber(voteWeight.recentPerformanceComponent, 0.5, 0, 1),
      confidenceComponent: this.sanitizeNumber(voteWeight.confidenceComponent, 0.5, 0, 1),
      councilTenureComponent: this.sanitizeNumber(voteWeight.councilTenureComponent, 0.5, 0, 1),
      normalizedWeight: this.sanitizeNumber(voteWeight.normalizedWeight, 0.5, 0, 1)
    };
  }

  /**
   * Validate object against schema
   * @param {Object} obj - Object to validate
   * @param {Object} schema - Validation schema
   * @returns {boolean} Is valid
   */
  static validateObject(obj, schema) {
    if (!obj || typeof obj !== 'object') return false;

    // Check required fields
    for (const field of schema.required) {
      if (!(field in obj)) return false;
    }

    // Check field types
    for (const [field, expectedType] of Object.entries(schema.types)) {
      if (field in obj) {
        const actualType = typeof obj[field];
        if (expectedType === 'number' && actualType !== 'number') {
          if (isNaN(Number(obj[field]))) return false;
        } else if (expectedType === 'string' && actualType !== 'string') {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * Add metadata to transformed object
   * @param {Object} obj - Object to add metadata to
   * @param {string} type - Object type
   * @returns {Object} Object with metadata
   */
  static addMetadata(obj, type) {
    return {
      ...obj,
      _metadata: {
        type,
        transformedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }

  /**
   * Create default game object
   * @returns {Object} Default game
   */
  static createDefaultGame() {
    return {
      id: 'default',
      homeTeam: 'TBD',
      awayTeam: 'TBD',
      startTime: new Date().toISOString(),
      status: 'scheduled',
      homeScore: 0,
      awayScore: 0,
      spread: 0,
      modelSpread: 0,
      spreadMovement: 0,
      overUnder: 45,
      modelTotal: 45,
      venue: 'TBD',
      weather: { temp: 70, wind: 5, humidity: 50 },
      homeWinProb: 0.5,
      awayWinProb: 0.5,
      ev: 0,
      confidence: 0.5,
      _metadata: {
        type: 'game',
        transformedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }

  /**
   * Create default ranking object
   * @returns {Object} Default ranking
   */
  static createDefaultRanking() {
    return {
      team: 'TBD',
      rank: 99,
      lastWeek: 99,
      movement: 0,
      record: '0-0',
      elo: 1500,
      trend: 'steady',
      offensiveEPA: 0,
      defensiveEPA: 0,
      sos: 0.5,
      _metadata: {
        type: 'ranking',
        transformedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }

  /**
   * Create default expert object
   * @returns {Object} Default expert
   */
  static createDefaultExpert() {
    return {
      expertId: 'default',
      expertName: 'Default Expert',
      overallAccuracy: 0.5,
      recentTrend: 'steady',
      voteWeight: this.transformVoteWeight({}),
      predictions: [],
      specialization: [],
      joinDate: new Date().toISOString(),
      totalVotes: 0,
      consensusAlignment: 0.5,
      _metadata: {
        type: 'expert',
        transformedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }
}

export default DataTransformer;