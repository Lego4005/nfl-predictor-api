import axios from 'axios';
// Use Node.js version for server-side execution
import { supabase } from './supabaseClientNode.js';
import predictionService from './predictionService.js';

const OPENROUTER_API_KEY = process.env.VITE_OPENROUTER_API_KEY;
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

/**
 * Multi-Model Council Prediction System
 *
 * Uses multiple AI models and algorithms with dynamic weighting
 * based on historical accuracy for each model
 */
class ModelCouncilService {
  constructor() {
    // Available models for the council - TOP TIER MODELS
    this.councilModels = [
      // Statistical Models (keep these for baseline)
      { id: 'elo', name: 'ELO Rating System', type: 'statistical' },
      { id: 'spread', name: 'Market Spread Analyzer', type: 'statistical' },
      { id: 'momentum', name: 'Momentum Tracker', type: 'statistical' },
      { id: 'bayesian', name: 'Bayesian Inference', type: 'statistical' },

      // TOP AI Models (via OpenRouter) - REAL CURRENT LEADERBOARD
      { id: 'claude-4-sonnet', name: 'Claude 4 Sonnet', type: 'ai', model: 'anthropic/claude-4-sonnet-20250522' },
      { id: 'grok-code-fast', name: 'Grok Code Fast 1', type: 'ai', model: 'x-ai/grok-code-fast-1' },
      { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', type: 'ai', model: 'google/gemini-2.5-flash' },
      { id: 'gemini-2-flash-001', name: 'Gemini 2.0 Flash 001', type: 'ai', model: 'google/gemini-2.0-flash-001' },
      { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', type: 'ai', model: 'openai/gpt-4.1-mini-2025-04-14' },
      { id: 'deepseek-chat-v3', name: 'DeepSeek Chat v3', type: 'ai', model: 'deepseek/deepseek-chat-v3-0324' },
      { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', type: 'ai', model: 'google/gemini-2.5-pro' },
      { id: 'qwen3-30b', name: 'Qwen3 30B', type: 'ai', model: 'qwen/qwen3-30b-a3b-04-28' },
      { id: 'deepseek-chat-v3.1-free', name: 'DeepSeek Chat v3.1 Free', type: 'ai', model: 'deepseek/deepseek-chat-v3.1:free' },
      { id: 'sonoma-sky-alpha', name: 'Sonoma Sky Alpha', type: 'ai', model: 'openrouter/sonoma-sky-alpha' },

      // Ensemble Models
      { id: 'neural-net', name: 'Neural Network Ensemble', type: 'ml' },
      { id: 'random-forest', name: 'Random Forest', type: 'ml' }
    ];

    // Dynamic weights based on historical performance
    // These will be updated based on actual results
    this.modelWeights = {};
    this.initializeWeights();

    // Performance tracking
    this.modelPerformance = {};
    this.loadHistoricalPerformance();
  }

  // Initialize weights from database or defaults
  async initializeWeights() {
    try {
      // Try to load weights from database
      const { data, error } = await supabase
        .from('model_performance')
        .select('*')
        .order('evaluation_date', { ascending: false })
        .limit(1);

      if (data && data.length > 0 && data[0].metadata?.weights) {
        this.modelWeights = data[0].metadata.weights;
      } else {
        // Default equal weights
        this.councilModels.forEach(model => {
          this.modelWeights[model.id] = 1.0 / this.councilModels.length;
        });
      }
    } catch (error) {
      console.error('Error loading model weights:', error);
      // Use default weights
      this.councilModels.forEach(model => {
        this.modelWeights[model.id] = 1.0 / this.councilModels.length;
      });
    }
  }

  // Load historical performance metrics
  async loadHistoricalPerformance() {
    try {
      const { data, error } = await supabase
        .from('model_performance')
        .select('*')
        .order('evaluation_date', { ascending: false })
        .limit(30);

      if (data) {
        // Aggregate performance by model
        data.forEach(record => {
          if (record.metadata?.modelPerformance) {
            Object.entries(record.metadata.modelPerformance).forEach(([modelId, perf]) => {
              if (!this.modelPerformance[modelId]) {
                this.modelPerformance[modelId] = {
                  predictions: 0,
                  correct: 0,
                  totalError: 0,
                  recentAccuracy: []
                };
              }

              this.modelPerformance[modelId].predictions += perf.predictions || 0;
              this.modelPerformance[modelId].correct += perf.correct || 0;
              this.modelPerformance[modelId].totalError += perf.error || 0;
              this.modelPerformance[modelId].recentAccuracy.push(perf.accuracy || 0);
            });
          }
        });
      }
    } catch (error) {
      console.error('Error loading historical performance:', error);
    }
  }

  /**
   * Generate council prediction using multiple models
   */
  async generateCouncilPrediction(game) {
    console.log(`🎯 Council convening for ${game.away_team} @ ${game.home_team}...`);

    // 1. Gather features
    const features = await predictionService.extractFeatures(game);

    // 2. Get predictions from all council members
    const councilVotes = await this.gatherCouncilVotes(game, features);

    // 3. Calculate dynamic weights based on recent performance
    const dynamicWeights = this.calculateDynamicWeights(councilVotes);

    // 4. Aggregate predictions using weighted voting
    const consensus = this.calculateWeightedConsensus(councilVotes, dynamicWeights);

    // 5. Calculate confidence and disagreement metrics
    const confidence = this.calculateCouncilConfidence(councilVotes, consensus);
    const disagreement = this.calculateDisagreement(councilVotes);

    // 6. Generate explanation
    const explanation = this.generateExplanation(councilVotes, consensus, dynamicWeights);

    // 7. Store prediction
    const prediction = {
      game_id: game.id,
      model_version: 'v3.0-council',
      prediction_type: 'multi-model-council',
      home_win_prob: consensus.homeWinProb,
      away_win_prob: consensus.awayWinProb,
      predicted_spread: consensus.spread,
      predicted_total: consensus.total,
      confidence: confidence,
      ml_features: {
        ...features,
        council_size: councilVotes.length,
        disagreement_index: disagreement,
        model_weights: dynamicWeights,
        individual_votes: councilVotes,
        consensus: consensus,
        explanation: explanation
      },
      created_at: new Date().toISOString()
    };

    // Delete any existing prediction for this game first
    await supabase
      .from('predictions')
      .delete()
      .eq('game_id', game.id);

    // Store in database
    const { error } = await supabase
      .from('predictions')
      .insert(prediction);

    if (error) {
      console.error('Error storing council prediction:', error);
    }

    console.log(`✅ Council consensus: ${consensus.homeWinProb.toFixed(1)}% home win, Spread: ${consensus.spread.toFixed(1)}, Confidence: ${confidence}%`);

    return prediction;
  }

  /**
   * Gather predictions from council members
   * Uses tiered approach: fast/cheap models first, then expensive ones for important games
   */
  async gatherCouncilVotes(game, features) {
    const votes = [];

    // Determine game importance (primetime, playoffs, close matchup)
    const gameImportance = this.calculateGameImportance(game, features);

    // Select models based on importance and cost
    const selectedModels = this.selectModelsForGame(gameImportance);

    console.log(`📊 Using ${selectedModels.length} models for ${game.away_team} @ ${game.home_team} (Importance: ${gameImportance}/10)`);

    // Parallel execution for selected models
    const promises = selectedModels.map(async (model) => {
      try {
        let prediction;

        switch (model.type) {
          case 'statistical':
            prediction = await this.getStatisticalPrediction(model.id, features);
            break;
          case 'ai':
            prediction = await this.getAIPrediction(model, game, features);
            break;
          case 'ml':
            prediction = await this.getMLPrediction(model.id, features);
            break;
        }

        if (prediction) {
          return {
            modelId: model.id,
            modelName: model.name,
            ...prediction,
            timestamp: new Date().toISOString()
          };
        }
      } catch (error) {
        console.error(`Error getting prediction from ${model.name}:`, error);
      }
      return null;
    });

    const results = await Promise.all(promises);
    return results.filter(vote => vote !== null);
  }

  /**
   * Calculate game importance (0-10 scale)
   */
  calculateGameImportance(game, features) {
    let importance = 5; // Base importance

    // Primetime games are more important
    if (features.isPrimeTime) importance += 2;

    // Divisional games matter more
    if (features.isDivisional) importance += 1;

    // Close matchups (similar ratings) are more interesting
    if (Math.abs(features.ratingDiff) < 50) importance += 1;

    // Playoff implications (late season)
    if (game.week > 14) importance += 1;

    // High-profile teams
    const topTeams = ['KC', 'BUF', 'SF', 'PHI', 'DAL', 'MIA'];
    if (topTeams.includes(game.home_team) || topTeams.includes(game.away_team)) {
      importance += 1;
    }

    return Math.min(10, importance);
  }

  /**
   * Select models based on game importance and cost efficiency
   */
  selectModelsForGame(importance) {
    const selected = [];

    // Always include statistical models (free and fast)
    selected.push(...this.councilModels.filter(m => m.type === 'statistical'));
    selected.push(...this.councilModels.filter(m => m.type === 'ml'));

    // Add AI models based on importance
    const aiModels = this.councilModels.filter(m => m.type === 'ai');

    if (importance >= 8) {
      // Very important games: Use TOP 5 from actual OpenRouter leaderboard
      selected.push(
        aiModels.find(m => m.id === 'claude-4-sonnet'), // #1 most used
        aiModels.find(m => m.id === 'grok-code-fast'), // #2 X.AI's latest
        aiModels.find(m => m.id === 'gemini-2.5-flash'), // #3 Google's newest
        aiModels.find(m => m.id === 'gemini-2.5-pro'), // #7 Google's pro model
        aiModels.find(m => m.id === 'deepseek-chat-v3') // #6 DeepSeek's latest
      );
    } else if (importance >= 6) {
      // Important games: Use solid performers
      selected.push(
        aiModels.find(m => m.id === 'gemini-2-flash-001'), // #4 fast and good
        aiModels.find(m => m.id === 'gpt-4.1-mini'), // #5 OpenAI's latest mini
        aiModels.find(m => m.id === 'qwen3-30b'), // #8 Qwen's newest
        aiModels.find(m => m.id === 'sonoma-sky-alpha') // #10 OpenRouter's own
      );
    } else {
      // Regular games: Use free/efficient models
      selected.push(
        aiModels.find(m => m.id === 'deepseek-chat-v3.1-free'), // #9 FREE!
        aiModels.find(m => m.id === 'gemini-2-flash-001'), // Fast and good
        aiModels.find(m => m.id === 'grok-code-fast') // X.AI efficiency
      );
    }

    // Filter out any undefined models
    return selected.filter(m => m !== undefined);
  }

  /**
   * Get statistical model predictions
   */
  async getStatisticalPrediction(modelId, features) {
    switch (modelId) {
      case 'elo':
        return predictionService.calculateEloPrediction(features);

      case 'spread':
        return predictionService.calculateSpreadPrediction(features);

      case 'momentum':
        return predictionService.calculateMomentumPrediction(features);

      case 'bayesian':
        return this.calculateBayesianPrediction(features);

      default:
        return null;
    }
  }

  /**
   * Get AI model predictions via OpenRouter
   */
  async getAIPrediction(model, game, features) {
    if (!OPENROUTER_API_KEY) return null;

    try {
      const prompt = this.buildAIPrompt(game, features);

      const response = await axios.post(OPENROUTER_URL, {
        model: model.model,
        messages: [
          {
            role: 'system',
            content: `You are an expert NFL analyst. Analyze the game and provide predictions.
                     Return ONLY a JSON object with these exact fields:
                     { "homeWinProb": number (0-100), "awayWinProb": number (0-100),
                       "spread": number (negative if home favored), "total": number,
                       "reasoning": "brief explanation" }`
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3, // Lower temperature for more consistent predictions
        max_tokens: 500
      }, {
        headers: {
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://nfl-predictor.app',
          'X-Title': 'NFL Predictor Council'
        }
      });

      const content = response.data.choices[0].message.content;

      // Parse JSON from response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          homeWinProb: parsed.homeWinProb,
          awayWinProb: parsed.awayWinProb,
          spread: parsed.spread,
          total: parsed.total,
          reasoning: parsed.reasoning
        };
      }
    } catch (error) {
      console.error(`AI prediction error for ${model.name}:`, error.message);
    }

    return null;
  }

  /**
   * Get ML model predictions
   */
  async getMLPrediction(modelId, features) {
    // Simulate ML model predictions
    // In production, these would call actual trained models

    switch (modelId) {
      case 'neural-net':
        return this.simulateNeuralNetPrediction(features);

      case 'random-forest':
        return this.simulateRandomForestPrediction(features);

      default:
        return null;
    }
  }

  /**
   * Calculate Bayesian prediction
   */
  calculateBayesianPrediction(features) {
    // Prior probabilities based on historical data
    const prior = 0.5; // Assume 50% base probability

    // Likelihood based on features
    const ratingLikelihood = 1 / (1 + Math.exp(-(features.ratingDiff / 100)));
    const spreadLikelihood = predictionService.spreadToWinProbability(features.marketSpread) / 100;
    const momentumLikelihood = 0.5 + (features.homeRecentForm.wins - features.awayRecentForm.wins) * 0.1;

    // Combine using Bayes' theorem
    const posterior = (prior * ratingLikelihood * spreadLikelihood * momentumLikelihood) /
                     ((prior * ratingLikelihood * spreadLikelihood * momentumLikelihood) +
                      ((1 - prior) * (1 - ratingLikelihood) * (1 - spreadLikelihood) * (1 - momentumLikelihood)));

    const homeProb = posterior * 100;

    return {
      homeWinProb: Math.max(20, Math.min(80, homeProb)),
      awayWinProb: Math.max(20, Math.min(80, 100 - homeProb)),
      spread: -(features.ratingDiff / 25),
      total: features.marketTotal || 45
    };
  }

  /**
   * Simulate neural network prediction
   */
  simulateNeuralNetPrediction(features) {
    // Simulate a neural network with feature interactions
    const hidden1 = Math.tanh(
      features.ratingDiff * 0.01 +
      features.homeFieldAdvantage * 0.1 +
      features.weatherImpact * -0.05 +
      features.homeSentiment * 0.03
    );

    const hidden2 = Math.tanh(
      features.homeRecentForm.wins * 0.1 +
      features.awayRecentForm.losses * 0.1 +
      features.isPrimeTime * 0.05
    );

    const output = 1 / (1 + Math.exp(-(hidden1 + hidden2)));
    const homeProb = output * 100;

    return {
      homeWinProb: Math.max(25, Math.min(75, homeProb)),
      awayWinProb: Math.max(25, Math.min(75, 100 - homeProb)),
      spread: -(features.ratingDiff / 25 + features.homeFieldAdvantage),
      total: features.marketTotal - Math.abs(features.weatherImpact)
    };
  }

  /**
   * Simulate random forest prediction
   */
  simulateRandomForestPrediction(features) {
    // Simulate multiple decision trees
    const trees = [];

    for (let i = 0; i < 10; i++) {
      // Each tree focuses on different features
      let treeVote = 50;

      if (i % 3 === 0 && features.ratingDiff > 50) treeVote += 15;
      if (i % 3 === 1 && features.homeRecentForm.wins > features.awayRecentForm.wins) treeVote += 10;
      if (i % 3 === 2 && features.marketSpread < 0) treeVote += Math.abs(features.marketSpread) * 2;

      // Add randomness
      treeVote += (Math.random() - 0.5) * 10;

      trees.push(treeVote);
    }

    // Average the trees
    const homeProb = trees.reduce((a, b) => a + b, 0) / trees.length;

    return {
      homeWinProb: Math.max(30, Math.min(70, homeProb)),
      awayWinProb: Math.max(30, Math.min(70, 100 - homeProb)),
      spread: -(features.ratingDiff / 25),
      total: features.marketTotal
    };
  }

  /**
   * Calculate dynamic weights based on recent performance
   */
  calculateDynamicWeights(votes) {
    const weights = {};
    let totalWeight = 0;

    votes.forEach(vote => {
      const modelPerf = this.modelPerformance[vote.modelId];

      if (modelPerf && modelPerf.predictions > 10) {
        // Calculate weight based on recent accuracy
        const accuracy = modelPerf.correct / modelPerf.predictions;
        const recency = modelPerf.recentAccuracy.slice(-5).reduce((a, b) => a + b, 0) /
                       Math.min(5, modelPerf.recentAccuracy.length);

        // Combine overall and recent accuracy
        weights[vote.modelId] = (accuracy * 0.6 + recency * 0.4) || 0.1;
      } else {
        // Default weight for new models
        weights[vote.modelId] = 0.1;
      }

      totalWeight += weights[vote.modelId];
    });

    // Normalize weights to sum to 1
    Object.keys(weights).forEach(modelId => {
      weights[modelId] = weights[modelId] / totalWeight;
    });

    return weights;
  }

  /**
   * Calculate weighted consensus from all votes
   */
  calculateWeightedConsensus(votes, weights) {
    let homeWinProb = 0;
    let spread = 0;
    let total = 0;
    let totalWeight = 0;

    votes.forEach(vote => {
      const weight = weights[vote.modelId] || 0.1;
      homeWinProb += vote.homeWinProb * weight;
      spread += vote.spread * weight;
      total += vote.total * weight;
      totalWeight += weight;
    });

    // Normalize if weights don't sum to 1
    if (totalWeight > 0) {
      homeWinProb /= totalWeight;
      spread /= totalWeight;
      total /= totalWeight;
    }

    return {
      homeWinProb: Math.round(homeWinProb * 10) / 10,
      awayWinProb: Math.round((100 - homeWinProb) * 10) / 10,
      spread: Math.round(spread * 2) / 2,
      total: Math.round(total)
    };
  }

  /**
   * Calculate council confidence based on agreement
   */
  calculateCouncilConfidence(votes, consensus) {
    if (votes.length === 0) return 50;

    // Calculate variance in predictions
    const homeWinVariance = votes.reduce((sum, vote) => {
      return sum + Math.pow(vote.homeWinProb - consensus.homeWinProb, 2);
    }, 0) / votes.length;

    const spreadVariance = votes.reduce((sum, vote) => {
      return sum + Math.pow(vote.spread - consensus.spread, 2);
    }, 0) / votes.length;

    // Lower variance = higher confidence
    const probConfidence = Math.max(40, 100 - homeWinVariance);
    const spreadConfidence = Math.max(40, 100 - spreadVariance * 2);

    // Weight recent model performance
    const avgModelPerf = votes.reduce((sum, vote) => {
      const perf = this.modelPerformance[vote.modelId];
      return sum + (perf ? perf.correct / Math.max(1, perf.predictions) : 0.5);
    }, 0) / votes.length;

    const perfConfidence = avgModelPerf * 100;

    // Combine confidence metrics
    const confidence = (probConfidence * 0.4 + spreadConfidence * 0.3 + perfConfidence * 0.3);

    return Math.round(Math.max(40, Math.min(95, confidence)));
  }

  /**
   * Calculate disagreement index
   */
  calculateDisagreement(votes) {
    if (votes.length < 2) return 0;

    // Calculate standard deviation of home win probabilities
    const probs = votes.map(v => v.homeWinProb);
    const mean = probs.reduce((a, b) => a + b, 0) / probs.length;
    const variance = probs.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / probs.length;
    const stdDev = Math.sqrt(variance);

    // Normalize to 0-100 scale
    return Math.min(100, stdDev * 2);
  }

  /**
   * Generate explanation for the prediction
   */
  generateExplanation(votes, consensus, weights) {
    const topModels = votes
      .sort((a, b) => (weights[b.modelId] || 0) - (weights[a.modelId] || 0))
      .slice(0, 3);

    const explanations = [];

    // Consensus view
    explanations.push(`Council consensus: ${consensus.homeWinProb.toFixed(1)}% home win probability`);

    // Top model views
    topModels.forEach(model => {
      const weight = (weights[model.modelId] * 100).toFixed(1);
      explanations.push(`${model.modelName} (${weight}% weight): ${model.homeWinProb.toFixed(1)}% home`);
    });

    // Disagreement note
    const disagreement = this.calculateDisagreement(votes);
    if (disagreement > 30) {
      explanations.push(`Note: High model disagreement (${disagreement.toFixed(0)}/100)`);
    }

    return explanations.join('. ');
  }

  /**
   * Build prompt for AI models
   */
  buildAIPrompt(game, features) {
    return `NFL Game Analysis:

    Matchup: ${game.away_team} @ ${game.home_team}
    Week: ${game.week}, Season: ${game.season}

    Team Ratings:
    - ${game.home_team}: ${features.homeRating} ELO
    - ${game.away_team}: ${features.awayRating} ELO

    Recent Form:
    - ${game.home_team}: ${features.homeRecentForm.wins}-${features.homeRecentForm.losses}, Avg ${features.homeRecentForm.avgPoints.toFixed(1)} pts
    - ${game.away_team}: ${features.awayRecentForm.wins}-${features.awayRecentForm.losses}, Avg ${features.awayRecentForm.avgPoints.toFixed(1)} pts

    Market Data:
    - Spread: ${game.home_team} ${features.marketSpread}
    - Total: ${features.marketTotal}

    Conditions:
    - Weather: ${features.weatherCondition}, ${features.temperature}°F
    - Wind: ${features.windSpeed} mph
    - Venue: ${game.venue || 'Unknown'}

    Context:
    - Divisional Game: ${features.isDivisional ? 'Yes' : 'No'}
    - Prime Time: ${features.isPrimeTime ? 'Yes' : 'No'}
    - News Sentiment: ${game.home_team}: ${features.homeSentiment.toFixed(2)}, ${game.away_team}: ${features.awaySentiment.toFixed(2)}

    Provide your prediction with reasoning.`;
  }

  /**
   * Update model performance after game results
   */
  async updateModelPerformance(gameId) {
    try {
      // Get the game result
      const { data: game, error: gameError } = await supabase
        .from('games')
        .select('*')
        .eq('id', gameId)
        .eq('status', 'final')
        .single();

      if (gameError || !game) return;

      // Get the prediction
      const { data: prediction, error: predError } = await supabase
        .from('predictions')
        .select('*')
        .eq('game_id', gameId)
        .single();

      if (predError || !prediction) return;

      // Determine actual outcome
      const homeWon = game.home_score > game.away_score;
      const actualSpread = game.away_score - game.home_score;
      const actualTotal = game.home_score + game.away_score;

      // Update each model's performance
      if (prediction.ml_features?.individual_votes) {
        prediction.ml_features.individual_votes.forEach(vote => {
          if (!this.modelPerformance[vote.modelId]) {
            this.modelPerformance[vote.modelId] = {
              predictions: 0,
              correct: 0,
              totalError: 0,
              recentAccuracy: []
            };
          }

          const perf = this.modelPerformance[vote.modelId];
          perf.predictions++;

          // Check if model was correct
          const predictedHomeWin = vote.homeWinProb > 50;
          if (predictedHomeWin === homeWon) {
            perf.correct++;
          }

          // Calculate error
          const spreadError = Math.abs(vote.spread - actualSpread);
          const totalError = Math.abs(vote.total - actualTotal);
          perf.totalError += (spreadError + totalError) / 2;

          // Update recent accuracy
          const accuracy = perf.correct / perf.predictions;
          perf.recentAccuracy.push(accuracy);
          if (perf.recentAccuracy.length > 20) {
            perf.recentAccuracy.shift();
          }
        });
      }

      // Save updated performance to database
      await this.saveModelPerformance();

      // Update weights based on new performance
      await this.updateModelWeights();

    } catch (error) {
      console.error('Error updating model performance:', error);
    }
  }

  /**
   * Save model performance to database
   */
  async saveModelPerformance() {
    try {
      const performanceRecord = {
        model_version: 'v3.0-council',
        prediction_type: 'multi-model',
        total_predictions: Object.values(this.modelPerformance).reduce((sum, p) => sum + p.predictions, 0),
        correct_predictions: Object.values(this.modelPerformance).reduce((sum, p) => sum + p.correct, 0),
        accuracy: 0,
        roi: 0,
        evaluation_date: new Date().toISOString().split('T')[0],
        metadata: {
          modelPerformance: this.modelPerformance,
          weights: this.modelWeights
        }
      };

      if (performanceRecord.total_predictions > 0) {
        performanceRecord.accuracy = (performanceRecord.correct_predictions / performanceRecord.total_predictions) * 100;
      }

      await supabase
        .from('model_performance')
        .insert(performanceRecord);

    } catch (error) {
      console.error('Error saving model performance:', error);
    }
  }

  /**
   * Update model weights based on performance
   */
  async updateModelWeights() {
    const newWeights = {};
    let totalScore = 0;

    // Calculate scores for each model
    Object.entries(this.modelPerformance).forEach(([modelId, perf]) => {
      if (perf.predictions > 5) {
        // Score based on accuracy and recent trend
        const accuracy = perf.correct / perf.predictions;
        const recentAccuracy = perf.recentAccuracy.slice(-10).reduce((a, b) => a + b, 0) /
                              Math.min(10, perf.recentAccuracy.length);

        // Favor recent performance more
        const score = accuracy * 0.4 + recentAccuracy * 0.6;
        newWeights[modelId] = Math.max(0.05, score); // Minimum 5% weight
        totalScore += newWeights[modelId];
      }
    });

    // Normalize weights
    if (totalScore > 0) {
      Object.keys(newWeights).forEach(modelId => {
        this.modelWeights[modelId] = newWeights[modelId] / totalScore;
      });
    }

    console.log('Updated model weights:', this.modelWeights);
  }

  /**
   * Get best performing models
   */
  getBestModels(n = 3) {
    const modelStats = Object.entries(this.modelPerformance)
      .filter(([_, perf]) => perf.predictions > 10)
      .map(([modelId, perf]) => ({
        modelId,
        modelName: this.councilModels.find(m => m.id === modelId)?.name || modelId,
        accuracy: (perf.correct / perf.predictions) * 100,
        predictions: perf.predictions,
        weight: this.modelWeights[modelId] || 0
      }))
      .sort((a, b) => b.accuracy - a.accuracy);

    return modelStats.slice(0, n);
  }
}

// Create singleton instance
const modelCouncilService = new ModelCouncilService();

export default modelCouncilService;