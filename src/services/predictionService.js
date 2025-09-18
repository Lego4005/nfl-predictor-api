import axios from 'axios';
import { supabase } from './supabaseClient.js';
import oddsService from './oddsService.js';
import newsService from './newsService.js';

// OpenRouter API configuration (optional - for advanced predictions)
const OPENROUTER_API_KEY = import.meta.env.VITE_OPENROUTER_API_KEY;
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

class PredictionService {
  constructor() {
    // Team strength ratings (basic ELO-style ratings)
    this.teamRatings = {
      'KC': 1650, 'BUF': 1620, 'SF': 1610, 'PHI': 1600, 'DAL': 1590,
      'CIN': 1580, 'BAL': 1570, 'MIA': 1560, 'DET': 1550, 'JAX': 1540,
      'LAC': 1530, 'MIN': 1520, 'SEA': 1510, 'PIT': 1500, 'NYJ': 1490,
      'GB': 1480, 'NO': 1470, 'CLE': 1460, 'TEN': 1450, 'NE': 1440,
      'ATL': 1430, 'WAS': 1420, 'TB': 1410, 'LAR': 1400, 'IND': 1390,
      'LV': 1380, 'CHI': 1370, 'DEN': 1360, 'NYG': 1350, 'HOU': 1340,
      'ARI': 1330, 'CAR': 1320
    };

    // Historical performance data (mock - in production, fetch from database)
    this.recentPerformance = {};

    // Weather impact factors
    this.weatherImpact = {
      'Clear': 0,
      'Indoor Stadium': 0,
      'Partly Cloudy': -0.5,
      'Cloudy': -1,
      'Light Rain': -2,
      'Rain': -3,
      'Heavy Rain': -5,
      'Snow': -4,
      'Heavy Snow': -7,
      'Wind': -2
    };
  }

  // Main prediction method
  async generatePrediction(game) {
    try {
      // 1. Gather all features
      const features = await this.extractFeatures(game);

      // 2. Calculate base prediction using multiple models
      const eloPrediction = this.calculateEloPrediction(features);
      const spreadPrediction = this.calculateSpreadPrediction(features);
      const momentumPrediction = this.calculateMomentumPrediction(features);
      const contextPrediction = await this.calculateContextPrediction(features);

      // 3. Ensemble the predictions
      const ensemblePrediction = this.ensemblePredictions({
        elo: eloPrediction,
        spread: spreadPrediction,
        momentum: momentumPrediction,
        context: contextPrediction
      });

      // 4. Calculate confidence score
      const confidence = this.calculateConfidence(ensemblePrediction, features);

      // 5. Generate final prediction
      const prediction = {
        game_id: game.id,
        model_version: 'v2.0-ensemble',
        prediction_type: 'comprehensive',
        home_win_prob: ensemblePrediction.homeWinProb,
        away_win_prob: ensemblePrediction.awayWinProb,
        predicted_spread: ensemblePrediction.spread,
        predicted_total: ensemblePrediction.total,
        confidence: confidence,
        ml_features: features,
        model_scores: {
          elo: eloPrediction,
          spread: spreadPrediction,
          momentum: momentumPrediction,
          context: contextPrediction
        },
        created_at: new Date().toISOString()
      };

      // 6. Store prediction in database
      const { error } = await supabase
        .from('predictions')
        .upsert(prediction, {
          onConflict: 'game_id'
        });

      if (error) throw error;

      return prediction;

    } catch (error) {
      console.error('Error generating prediction:', error);
      return this.generateFallbackPrediction(game);
    }
  }

  // Extract features for ML models
  async extractFeatures(game) {
    const features = {
      // Basic game info
      homeTeam: game.home_team,
      awayTeam: game.away_team,
      week: game.week,
      season: game.season,

      // Team ratings
      homeRating: this.teamRatings[game.home_team] || 1400,
      awayRating: this.teamRatings[game.away_team] || 1400,
      ratingDiff: 0,

      // Home field advantage
      homeFieldAdvantage: 3, // Standard 3 points

      // Weather impact
      weatherCondition: game.weather_data?.condition || 'Clear',
      weatherImpact: 0,
      temperature: game.weather_data?.temperature || 70,
      windSpeed: game.weather_data?.wind_speed || 0,

      // Betting market data
      marketSpread: game.odds_data?.consensus_spread || 0,
      marketTotal: game.odds_data?.consensus_total || 45,

      // Recent performance
      homeRecentForm: await this.getRecentForm(game.home_team),
      awayRecentForm: await this.getRecentForm(game.away_team),

      // Head to head
      h2hRecord: await this.getHeadToHead(game.home_team, game.away_team),

      // News sentiment
      homeSentiment: 0,
      awaySentiment: 0,

      // Time factors
      isThursdayGame: new Date(game.game_time).getDay() === 4,
      isMondayGame: new Date(game.game_time).getDay() === 1,
      isPrimeTime: this.isPrimeTime(game.game_time),
      isDivisional: this.isDivisionalGame(game.home_team, game.away_team)
    };

    // Calculate derived features
    features.ratingDiff = features.homeRating - features.awayRating;
    features.weatherImpact = this.weatherImpact[features.weatherCondition] || 0;

    // Get news sentiment
    const homeSentiment = await newsService.getTeamSentiment([game.home_team]);
    const awaySentiment = await newsService.getTeamSentiment([game.away_team]);

    if (homeSentiment) features.homeSentiment = homeSentiment.aggregateSentiment;
    if (awaySentiment) features.awaySentiment = awaySentiment.aggregateSentiment;

    return features;
  }

  // ELO-based prediction model
  calculateEloPrediction(features) {
    const K = 400; // K-factor for probability calculation

    // Adjust ratings for home field advantage
    const homeAdjusted = features.homeRating + (features.homeFieldAdvantage * 10);
    const awayAdjusted = features.awayRating;

    // Calculate expected score using ELO formula
    const expectedHome = 1 / (1 + Math.pow(10, (awayAdjusted - homeAdjusted) / K));
    const expectedAway = 1 - expectedHome;

    // Convert to spread
    const ratingSpread = (homeAdjusted - awayAdjusted) / 25; // 25 ELO points ≈ 1 point spread

    // Estimate total based on team strengths
    const avgRating = (features.homeRating + features.awayRating) / 2;
    const estimatedTotal = 35 + (avgRating - 1400) / 10; // Base 35, +1 point per 10 ELO

    return {
      homeWinProb: expectedHome * 100,
      awayWinProb: expectedAway * 100,
      spread: -ratingSpread, // Negative means home favored
      total: estimatedTotal
    };
  }

  // Spread-based prediction using market odds
  calculateSpreadPrediction(features) {
    // Use market spread as base
    const marketSpread = features.marketSpread || 0;

    // Adjust for weather
    const weatherAdjustment = features.weatherImpact * 0.5;

    // Adjust for sentiment
    const sentimentAdjustment = (features.homeSentiment - features.awaySentiment) * 2;

    // Final spread
    const adjustedSpread = marketSpread + weatherAdjustment + sentimentAdjustment;

    // Convert spread to probability (using normal distribution)
    const spreadProb = this.spreadToWinProbability(adjustedSpread);

    return {
      homeWinProb: spreadProb,
      awayWinProb: 100 - spreadProb,
      spread: adjustedSpread,
      total: features.marketTotal + weatherAdjustment
    };
  }

  // Momentum-based prediction
  calculateMomentumPrediction(features) {
    // Calculate momentum scores
    const homeMomentum = features.homeRecentForm.wins - features.homeRecentForm.losses;
    const awayMomentum = features.awayRecentForm.wins - features.awayRecentForm.losses;

    // Momentum difference
    const momentumDiff = homeMomentum - awayMomentum;

    // Convert to probability
    const momentumProb = 50 + (momentumDiff * 5); // Each win/loss difference = 5%

    // Estimate spread based on momentum
    const momentumSpread = -momentumDiff * 1.5;

    // Scoring trend affects total
    const avgRecent = (features.homeRecentForm.avgPoints + features.awayRecentForm.avgPoints);

    return {
      homeWinProb: Math.max(20, Math.min(80, momentumProb)),
      awayWinProb: Math.max(20, Math.min(80, 100 - momentumProb)),
      spread: momentumSpread,
      total: avgRecent
    };
  }

  // Context-based prediction (using AI if available)
  async calculateContextPrediction(features) {
    // If OpenRouter API is available, use it for advanced analysis
    if (OPENROUTER_API_KEY) {
      try {
        const prompt = this.buildPredictionPrompt(features);
        const aiPrediction = await this.getAIPrediction(prompt);
        if (aiPrediction) return aiPrediction;
      } catch (error) {
        console.error('AI prediction failed:', error);
      }
    }

    // Fallback to rule-based context analysis
    let homeBonus = 0;
    let awayBonus = 0;

    // Thursday games - road teams struggle
    if (features.isThursdayGame) homeBonus += 3;

    // Divisional games are closer
    if (features.isDivisional) {
      const diff = Math.abs(features.ratingDiff);
      if (diff > 100) {
        homeBonus -= 2;
        awayBonus -= 2;
      }
    }

    // Prime time performance (some teams better in spotlight)
    if (features.isPrimeTime) {
      // Teams like KC, DAL, SF perform better in primetime
      const primeTimeTeams = ['KC', 'DAL', 'SF', 'BUF', 'PHI'];
      if (primeTimeTeams.includes(features.homeTeam)) homeBonus += 2;
      if (primeTimeTeams.includes(features.awayTeam)) awayBonus += 2;
    }

    // Weather adjustments for specific teams
    if (features.weatherCondition.includes('Snow')) {
      const coldWeatherTeams = ['BUF', 'GB', 'NE', 'CHI', 'MIN'];
      const warmWeatherTeams = ['MIA', 'TB', 'ARI', 'LAC', 'JAX'];

      if (coldWeatherTeams.includes(features.homeTeam)) homeBonus += 3;
      if (warmWeatherTeams.includes(features.awayTeam)) awayBonus -= 3;
    }

    const contextProb = 50 + ((features.ratingDiff / 25) * 5) + homeBonus - awayBonus;

    return {
      homeWinProb: Math.max(25, Math.min(75, contextProb)),
      awayWinProb: Math.max(25, Math.min(75, 100 - contextProb)),
      spread: -(features.ratingDiff / 25 + (homeBonus - awayBonus) / 2),
      total: features.marketTotal - Math.abs(features.weatherImpact)
    };
  }

  // Ensemble multiple predictions
  ensemblePredictions(predictions) {
    // Weights for each model
    const weights = {
      elo: 0.25,
      spread: 0.35,  // Market data gets highest weight
      momentum: 0.20,
      context: 0.20
    };

    let homeWinProb = 0;
    let awayWinProb = 0;
    let spread = 0;
    let total = 0;

    for (const [model, prediction] of Object.entries(predictions)) {
      const weight = weights[model];
      homeWinProb += prediction.homeWinProb * weight;
      awayWinProb += prediction.awayWinProb * weight;
      spread += prediction.spread * weight;
      total += prediction.total * weight;
    }

    // Normalize probabilities
    const totalProb = homeWinProb + awayWinProb;
    homeWinProb = (homeWinProb / totalProb) * 100;
    awayWinProb = (awayWinProb / totalProb) * 100;

    return {
      homeWinProb: Math.round(homeWinProb * 10) / 10,
      awayWinProb: Math.round(awayWinProb * 10) / 10,
      spread: Math.round(spread * 2) / 2, // Round to nearest 0.5
      total: Math.round(total)
    };
  }

  // Calculate confidence score
  calculateConfidence(prediction, features) {
    let confidence = 70; // Base confidence

    // Agreement between models increases confidence
    const spreadVariance = this.calculateModelAgreement(prediction);
    confidence += (10 - spreadVariance); // Max +10 for perfect agreement

    // Market alignment increases confidence
    if (features.marketSpread) {
      const marketDiff = Math.abs(prediction.spread - features.marketSpread);
      if (marketDiff < 1) confidence += 5;
      else if (marketDiff > 3) confidence -= 5;
    }

    // Sample size (more historical data = higher confidence)
    if (features.homeRecentForm.games >= 5) confidence += 3;
    if (features.awayRecentForm.games >= 5) confidence += 3;

    // Weather uncertainty
    if (features.weatherCondition.includes('Rain') || features.weatherCondition.includes('Snow')) {
      confidence -= 5;
    }

    // Cap confidence between 40-95
    return Math.max(40, Math.min(95, confidence));
  }

  // Helper: Calculate model agreement
  calculateModelAgreement(prediction) {
    // In real implementation, would check variance between individual model predictions
    // For now, return a mock value
    return Math.random() * 5 + 2; // 2-7 variance
  }

  // Helper: Convert spread to win probability
  spreadToWinProbability(spread) {
    // Using historical NFL data, approximate conversion
    // Home team favored by X points has Y% chance to win
    const spreadToProb = {
      '-17': 90, '-14': 85, '-10': 78, '-7': 70, '-6': 67,
      '-5': 64, '-4': 61, '-3': 58, '-2.5': 56, '-2': 54,
      '-1': 52, '0': 50, '1': 48, '2': 46, '2.5': 44,
      '3': 42, '4': 39, '5': 36, '6': 33, '7': 30,
      '10': 22, '14': 15, '17': 10
    };

    // Find closest spread
    let closest = 0;
    let minDiff = 100;
    for (const s in spreadToProb) {
      const diff = Math.abs(parseFloat(s) - spread);
      if (diff < minDiff) {
        minDiff = diff;
        closest = parseFloat(s);
      }
    }

    return spreadToProb[closest.toString()] || 50;
  }

  // Get recent form for a team
  async getRecentForm(team, games = 5) {
    try {
      const { data, error } = await supabase
        .from('games')
        .select('*')
        .or(`home_team.eq.${team},away_team.eq.${team}`)
        .eq('status', 'final')
        .order('game_time', { ascending: false })
        .limit(games);

      if (error || !data || data.length === 0) {
        return { wins: 0, losses: 0, avgPoints: 21, games: 0 };
      }

      let wins = 0;
      let losses = 0;
      let totalPoints = 0;

      data.forEach(game => {
        const isHome = game.home_team === team;
        const teamScore = isHome ? game.home_score : game.away_score;
        const oppScore = isHome ? game.away_score : game.home_score;

        if (teamScore > oppScore) wins++;
        else losses++;

        totalPoints += teamScore;
      });

      return {
        wins,
        losses,
        avgPoints: totalPoints / data.length,
        games: data.length
      };

    } catch (error) {
      console.error('Error getting recent form:', error);
      return { wins: 0, losses: 0, avgPoints: 21, games: 0 };
    }
  }

  // Get head-to-head record
  async getHeadToHead(team1, team2, seasons = 3) {
    try {
      const { data, error } = await supabase
        .from('games')
        .select('*')
        .or(`and(home_team.eq.${team1},away_team.eq.${team2}),and(home_team.eq.${team2},away_team.eq.${team1})`)
        .eq('status', 'final')
        .gte('season', new Date().getFullYear() - seasons)
        .order('game_time', { ascending: false });

      if (error || !data) {
        return { team1Wins: 0, team2Wins: 0, avgTotal: 45 };
      }

      let team1Wins = 0;
      let team2Wins = 0;
      let totalPoints = 0;

      data.forEach(game => {
        const team1Score = game.home_team === team1 ? game.home_score : game.away_score;
        const team2Score = game.home_team === team2 ? game.home_score : game.away_score;

        if (team1Score > team2Score) team1Wins++;
        else team2Wins++;

        totalPoints += team1Score + team2Score;
      });

      return {
        team1Wins,
        team2Wins,
        avgTotal: data.length > 0 ? totalPoints / data.length : 45
      };

    } catch (error) {
      console.error('Error getting H2H:', error);
      return { team1Wins: 0, team2Wins: 0, avgTotal: 45 };
    }
  }

  // Check if prime time game
  isPrimeTime(gameTime) {
    const date = new Date(gameTime);
    const hour = date.getHours();
    const day = date.getDay();

    // Sunday/Monday night (8PM ET) or Thursday night
    return (hour >= 20) || (day === 4 && hour >= 20);
  }

  // Check if divisional game
  isDivisionalGame(team1, team2) {
    const divisions = {
      'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
      'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
      'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
      'AFC West': ['DEN', 'KC', 'LV', 'LAC'],
      'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
      'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
      'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
      'NFC West': ['ARI', 'LAR', 'SF', 'SEA']
    };

    for (const division of Object.values(divisions)) {
      if (division.includes(team1) && division.includes(team2)) {
        return true;
      }
    }
    return false;
  }

  // Build prompt for AI prediction (if using OpenRouter)
  buildPredictionPrompt(features) {
    return `Analyze this NFL game and provide prediction:

      ${features.awayTeam} @ ${features.homeTeam} (Week ${features.week})

      Team Ratings: ${features.awayTeam}: ${features.awayRating}, ${features.homeTeam}: ${features.homeRating}
      Market Spread: ${features.homeTeam} ${features.marketSpread}
      Weather: ${features.weatherCondition}, ${features.temperature}°F, Wind: ${features.windSpeed}mph
      Recent Form: ${features.homeTeam}: ${features.homeRecentForm.wins}-${features.homeRecentForm.losses}, ${features.awayTeam}: ${features.awayRecentForm.wins}-${features.awayRecentForm.losses}
      Sentiment: ${features.homeTeam}: ${features.homeSentiment}, ${features.awayTeam}: ${features.awaySentiment}

      Provide: homeWinProb (0-100), awayWinProb (0-100), spread (negative if home favored), total points`;
  }

  // Get AI prediction from OpenRouter
  async getAIPrediction(prompt) {
    if (!OPENROUTER_API_KEY) return null;

    try {
      const response = await axios.post(OPENROUTER_URL, {
        model: 'anthropic/claude-3-haiku',
        messages: [
          {
            role: 'system',
            content: 'You are an NFL analytics expert. Provide predictions in JSON format only.'
          },
          {
            role: 'user',
            content: prompt
          }
        ]
      }, {
        headers: {
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      const content = response.data.choices[0].message.content;
      return JSON.parse(content);

    } catch (error) {
      console.error('OpenRouter API error:', error);
      return null;
    }
  }

  // Fallback prediction for errors
  generateFallbackPrediction(game) {
    const homeRating = this.teamRatings[game.home_team] || 1400;
    const awayRating = this.teamRatings[game.away_team] || 1400;
    const ratingDiff = homeRating - awayRating + 30; // +3 home field

    const homeProb = 50 + (ratingDiff / 10);

    return {
      game_id: game.id,
      model_version: 'v1.0-fallback',
      prediction_type: 'basic',
      home_win_prob: Math.max(20, Math.min(80, homeProb)),
      away_win_prob: Math.max(20, Math.min(80, 100 - homeProb)),
      predicted_spread: -(ratingDiff / 25),
      predicted_total: 45,
      confidence: 50,
      ml_features: { fallback: true },
      created_at: new Date().toISOString()
    };
  }

  // Batch predict for multiple games
  async generateBatchPredictions(games) {
    const predictions = [];

    for (const game of games) {
      const prediction = await this.generatePrediction(game);
      predictions.push(prediction);

      // Small delay to avoid rate limits
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return predictions;
  }

  // Update team ratings based on results (ELO update)
  async updateTeamRatings(game) {
    if (game.status !== 'final') return;

    const K = 32; // K-factor for rating updates
    const homeRating = this.teamRatings[game.home_team];
    const awayRating = this.teamRatings[game.away_team];

    // Expected scores
    const expectedHome = 1 / (1 + Math.pow(10, (awayRating - homeRating) / 400));
    const expectedAway = 1 - expectedHome;

    // Actual scores
    const homeWon = game.home_score > game.away_score ? 1 : 0;
    const awayWon = 1 - homeWon;

    // Update ratings
    this.teamRatings[game.home_team] = Math.round(homeRating + K * (homeWon - expectedHome));
    this.teamRatings[game.away_team] = Math.round(awayRating + K * (awayWon - expectedAway));

    console.log(`Updated ratings: ${game.home_team}: ${this.teamRatings[game.home_team]}, ${game.away_team}: ${this.teamRatings[game.away_team]}`);
  }
}

// Create singleton instance
const predictionService = new PredictionService();

export default predictionService;