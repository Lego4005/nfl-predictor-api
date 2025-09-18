/**
 * Game Score Service
 * Handles extraction and calculation of game scores from various data sources
 */

export class GameScoreService {
  /**
   * Extract final scores from Expert Observatory game data
   * @param {Object} game - Raw game data from Expert Observatory API
   * @returns {Object} Extracted score data
   */
  static extractScoresFromExpertPredictions(game) {
    let homeScore = 0;
    let awayScore = 0;
    let consensus = null;

    if (game.expert_predictions && game.expert_predictions.length > 0) {
      // For final games, use the first expert's prediction as representative score
      // In a more sophisticated system, we might calculate consensus or use actual final scores
      const firstPrediction = game.expert_predictions[0];

      if (firstPrediction.prediction) {
        homeScore = firstPrediction.prediction.home_score || 0;
        awayScore = firstPrediction.prediction.away_score || 0;
      }

      // Calculate consensus data for additional insights
      consensus = this.calculateConsensus(game.expert_predictions);
    }

    return {
      homeScore,
      awayScore,
      consensus,
      hasScores: homeScore > 0 || awayScore > 0
    };
  }

  /**
   * Calculate consensus predictions from multiple experts
   * @param {Array} expertPredictions - Array of expert predictions
   * @returns {Object} Consensus data
   */
  static calculateConsensus(expertPredictions) {
    if (!expertPredictions || expertPredictions.length === 0) {
      return null;
    }

    const validPredictions = expertPredictions.filter(ep => ep.prediction);

    if (validPredictions.length === 0) {
      return null;
    }

    // Calculate averages
    const totalPredictions = validPredictions.length;
    const sums = validPredictions.reduce((acc, ep) => {
      const pred = ep.prediction;
      return {
        homeScore: acc.homeScore + (pred.home_score || 0),
        awayScore: acc.awayScore + (pred.away_score || 0),
        confidence: acc.confidence + (pred.confidence || 0),
        spread: acc.spread + (pred.spread || 0),
        total: acc.total + (pred.total || 0)
      };
    }, { homeScore: 0, awayScore: 0, confidence: 0, spread: 0, total: 0 });

    return {
      averageHomeScore: Math.round(sums.homeScore / totalPredictions),
      averageAwayScore: Math.round(sums.awayScore / totalPredictions),
      averageConfidence: sums.confidence / totalPredictions,
      averageSpread: sums.spread / totalPredictions,
      averageTotal: sums.total / totalPredictions,
      expertCount: totalPredictions
    };
  }

  /**
   * Determine game status based on date and existing status
   * @param {Object} game - Game data
   * @returns {string} Mapped status: 'live', 'scheduled', 'final'
   */
  static determineGameStatus(game) {
    const gameDate = new Date(game.date);
    const now = new Date();

    // Check explicit status first
    if (game.status === 'completed' || game.status === 'final') {
      return 'final';
    }

    if (game.is_live || game.status === 'live' || game.status === 'in_progress') {
      return 'live';
    }

    // Check if game is in the future
    if (gameDate > now) {
      return 'scheduled';
    }

    // Past games without explicit live status are considered final
    return 'final';
  }

  /**
   * Extract prediction data for game card display
   * @param {Object} game - Game data with expert predictions
   * @returns {Object} Prediction display data
   */
  static extractPredictionData(game) {
    if (!game.expert_predictions || game.expert_predictions.length === 0) {
      return {
        hasAIPrediction: false,
        homeWinProb: 50,
        awayWinProb: 50,
        prediction: {
          confidence: 0.5,
          line: 0,
          predictedTotal: null
        }
      };
    }

    const consensus = this.calculateConsensus(game.expert_predictions);
    const firstPrediction = game.expert_predictions[0];

    // Use consensus data if available, fallback to first expert
    const confidence = consensus?.averageConfidence || firstPrediction.prediction?.confidence || 0.5;
    const spread = consensus?.averageSpread || firstPrediction.prediction?.spread || 0;
    const total = consensus?.averageTotal || firstPrediction.prediction?.total || null;

    // Calculate win probabilities (simplified)
    // In a real system, this would be more sophisticated
    const homeWinProb = spread > 0 ? 60 : 40; // Home team favored if spread is positive
    const awayWinProb = 100 - homeWinProb;

    return {
      hasAIPrediction: true,
      homeWinProb,
      awayWinProb,
      prediction: {
        confidence: confidence,
        line: spread,
        predictedTotal: total
      }
    };
  }
}

export default GameScoreService;