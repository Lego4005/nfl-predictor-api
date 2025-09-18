import axios from 'axios';
import newsService from './newsService.js';
import oddsService from './oddsService.js';
import { supabase } from './supabaseClient.js';
import vectorSearchService from './vectorSearchService.js';

/**
 * Expert Research Service
 * Each expert has unique research strategies and data sources
 */
class ExpertResearchService {
  constructor() {
    // Research strategies for each expert
    this.researchStrategies = {
      'claude-the-analyst': {
        strategy: 'Advanced Statistical Analysis',
        methods: ['DVOA analysis', 'EPA per play', 'Success rate trends', 'Red zone efficiency'],
        dataSources: ['team_stats', 'advanced_metrics', 'drive_charts'],
        researchDepth: 'deep',
        focusAreas: ['offensive efficiency', 'defensive rankings', 'situational football']
      },

      'grok-the-maverick': {
        strategy: 'Contrarian Value Hunting',
        methods: ['Public betting sentiment', 'Sharp vs square money', 'Trap game detection'],
        dataSources: ['betting_percentages', 'line_movement', 'public_sentiment'],
        researchDepth: 'market-focused',
        focusAreas: ['betting value', 'public perception', 'market inefficiencies']
      },

      'gemini-the-weatherman': {
        strategy: 'Environmental Impact Analysis',
        methods: ['Weather impact models', 'Dome vs outdoor splits', 'Wind effect on passing'],
        dataSources: ['weather_api', 'venue_data', 'historical_weather_games'],
        researchDepth: 'environmental',
        focusAreas: ['weather conditions', 'venue factors', 'playing surface impact']
      },

      'deepseek-the-intuitive': {
        strategy: 'Momentum & Psychology',
        methods: ['Team chemistry analysis', 'Locker room reports', 'Motivation factors'],
        dataSources: ['news_sentiment', 'social_media', 'injury_reports'],
        researchDepth: 'psychological',
        focusAreas: ['team morale', 'psychological edges', 'intangible factors']
      },

      'gpt-the-historian': {
        strategy: 'Historical Pattern Analysis',
        methods: ['Head-to-head records', 'Coach vs coach history', 'Playoff implication games'],
        dataSources: ['historical_matchups', 'coaching_records', 'playoff_scenarios'],
        researchDepth: 'historical',
        focusAreas: ['past matchups', 'coaching tendencies', 'situational precedents']
      },

      'gemini-pro-the-perfectionist': {
        strategy: 'Comprehensive Multi-Source Analysis',
        methods: ['All available data synthesis', 'Cross-validation checks', 'Outlier detection'],
        dataSources: ['ALL_SOURCES', 'data_quality_checks', 'model_ensemble'],
        researchDepth: 'comprehensive',
        focusAreas: ['data completeness', 'model accuracy', 'prediction confidence']
      },

      'qwen-the-calculator': {
        strategy: 'Mathematical Probability Models',
        methods: ['Bayesian inference', 'Monte Carlo simulations', 'Expected value calculations'],
        dataSources: ['statistical_models', 'probability_distributions', 'monte_carlo'],
        researchDepth: 'mathematical',
        focusAreas: ['probability math', 'expected outcomes', 'variance analysis']
      },

      'sonoma-the-rookie': {
        strategy: 'Fresh Eyes Analysis',
        methods: ['Unbiased observation', 'Trend reversal detection', 'Rookie perspective'],
        dataSources: ['basic_stats', 'recent_trends', 'simple_metrics'],
        researchDepth: 'surface',
        focusAreas: ['obvious patterns', 'recent form', 'simple logic']
      },

      'deepseek-free-the-underdog': {
        strategy: 'Value-First Analysis',
        methods: ['Cost-benefit analysis', 'Efficiency metrics', 'Undervalued team detection'],
        dataSources: ['value_metrics', 'efficiency_stats', 'market_prices'],
        researchDepth: 'value-focused',
        focusAreas: ['team efficiency', 'market value', 'underdog opportunities']
      },

      'flash-the-speedster': {
        strategy: 'Quick Hit Analysis',
        methods: ['First impression', 'Key stat focus', 'Gut instinct validation'],
        dataSources: ['headline_stats', 'recent_results', 'injury_updates'],
        researchDepth: 'shallow',
        focusAreas: ['obvious factors', 'recent performance', 'key injuries']
      }
    };

    // Mock external APIs (in production, these would be real APIs)
    this.externalAPIs = {
      draftKings: 'https://sportsbook-api.draftkings.com',
      espnStats: 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
      pff: 'https://api.profootballfocus.com', // Mock
      weather: 'https://api.openweathermap.org/data/2.5',
      twitter: 'https://api.twitter.com/2' // Mock
    };
  }

  /**
   * Conduct research for specific expert
   */
  async conductExpertResearch(expertId, game, baseFeatures) {
    const strategy = this.researchStrategies[expertId];
    if (!strategy) return baseFeatures;

    console.log(`🔍 ${expertId} conducting ${strategy.strategy}...`);

    const researchData = { ...baseFeatures };

    // Store research context for this expert
    const researchQuery = `${game.home_team} vs ${game.away_team} ${game.game_time}`;

    // Execute research based on expert's strategy
    switch (strategy.strategy) {
      case 'Advanced Statistical Analysis':
        researchData.advancedStats = await this.getAdvancedStats(game);
        researchData.dvoa = await this.getDVOAData(game);
        researchData.epaAnalysis = await this.getEPAAnalysis(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['team_stats', 'advanced_metrics']);
        break;

      case 'Contrarian Value Hunting':
        researchData.bettingPercentages = await this.getBettingPercentages(game);
        researchData.lineMovement = await this.getLineMovement(game);
        researchData.sharpMoney = await this.getSharpMoneyIndicators(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['betting_trends', 'market_inefficiencies']);
        break;

      case 'Environmental Impact Analysis':
        researchData.detailedWeather = await this.getDetailedWeather(game);
        researchData.venueFactors = await this.getVenueFactors(game);
        researchData.surfaceImpact = await this.getSurfaceImpact(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['weather_impact', 'venue_factors']);
        break;

      case 'Momentum & Psychology':
        researchData.teamChemistry = await this.getTeamChemistry(game);
        researchData.socialSentiment = await this.getSocialSentiment(game);
        researchData.motivationFactors = await this.getMotivationFactors(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['team_psychology', 'momentum']);
        break;

      case 'Historical Pattern Analysis':
        researchData.historicalH2H = await this.getHistoricalMatchups(game);
        researchData.coachingHistory = await this.getCoachingHistory(game);
        researchData.situationalTrends = await this.getSituationalTrends(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['historical_patterns', 'coaching_history']);
        break;

      case 'Comprehensive Multi-Source Analysis':
        // Get everything!
        researchData.comprehensive = await this.getComprehensiveData(game);
        researchData.vectorResearch = await this.getComprehensiveVectorResearch(expertId, researchQuery, game);
        break;

      case 'Mathematical Probability Models':
        researchData.probabilityModels = await this.getMathematicalModels(game);
        researchData.monteCarloSim = await this.getMonteCarloSimulation(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['probability_models', 'statistical_analysis']);
        break;

      case 'Fresh Eyes Analysis':
        researchData.obviousPatterns = await this.getObviousPatterns(game);
        researchData.recentTrends = await this.getRecentTrends(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['recent_trends', 'obvious_patterns']);
        break;

      case 'Value-First Analysis':
        researchData.valueMetrics = await this.getValueMetrics(game);
        researchData.efficiencyStats = await this.getEfficiencyStats(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['value_analysis', 'efficiency_metrics']);
        break;

      case 'Quick Hit Analysis':
        researchData.keyStats = await this.getKeyStats(game);
        researchData.headlineFactors = await this.getHeadlineFactors(game);
        researchData.vectorResearch = await this.getVectorResearch(expertId, researchQuery, ['key_stats', 'headline_news']);
        break;
    }

    // Store this research for future reference
    await this.storeExpertResearch(expertId, game, researchData);

    // Add research metadata
    researchData.researchStrategy = strategy.strategy;
    researchData.researchDepth = strategy.researchDepth;
    researchData.focusAreas = strategy.focusAreas;
    researchData.researchTimestamp = new Date().toISOString();

    console.log(`✅ ${expertId} research complete: ${Object.keys(researchData).length} data points`);

    return researchData;
  }

  // RESEARCH METHODS - Each expert gets different data

  async getAdvancedStats(game) {
    // Mock advanced stats (in production, get from PFF, Football Study Hall, etc.)
    return {
      home_dvoa: (Math.random() - 0.5) * 0.4, // -0.2 to 0.2
      away_dvoa: (Math.random() - 0.5) * 0.4,
      home_epa_per_play: (Math.random() - 0.5) * 0.3,
      away_epa_per_play: (Math.random() - 0.5) * 0.3,
      home_success_rate: 0.35 + Math.random() * 0.3, // 35-65%
      away_success_rate: 0.35 + Math.random() * 0.3,
      home_red_zone_eff: 0.4 + Math.random() * 0.4, // 40-80%
      away_red_zone_eff: 0.4 + Math.random() * 0.4
    };
  }

  async getDVOAData(game) {
    return {
      offensive_dvoa: { home: Math.random() * 0.4 - 0.2, away: Math.random() * 0.4 - 0.2 },
      defensive_dvoa: { home: Math.random() * 0.4 - 0.2, away: Math.random() * 0.4 - 0.2 },
      special_teams_dvoa: { home: Math.random() * 0.2 - 0.1, away: Math.random() * 0.2 - 0.1 }
    };
  }

  async getEPAAnalysis(game) {
    return {
      passing_epa: { home: Math.random() * 0.3, away: Math.random() * 0.3 },
      rushing_epa: { home: Math.random() * 0.2 - 0.1, away: Math.random() * 0.2 - 0.1 },
      epa_allowed: { home: -Math.random() * 0.2, away: -Math.random() * 0.2 }
    };
  }

  async getBettingPercentages(game) {
    // Mock DraftKings/FanDuel style data
    return {
      public_bet_percentage: {
        home: Math.random() * 0.6 + 0.2, // 20-80%
        away: 0, // Will calculate as 1 - home
        spread_home: Math.random() * 0.7 + 0.15,
        total_over: Math.random() * 0.6 + 0.2
      },
      ticket_count: {
        home: Math.floor(Math.random() * 10000) + 1000,
        away: Math.floor(Math.random() * 10000) + 1000
      },
      money_percentage: {
        home: Math.random() * 0.8 + 0.1, // Can differ from bet %
        away: 0 // Calculate as 1 - home
      }
    };
  }

  async getLineMovement(game) {
    // Mock line movement data
    const openingLine = (Math.random() - 0.5) * 14;
    const currentLine = openingLine + (Math.random() - 0.5) * 4;

    return {
      opening_spread: openingLine,
      current_spread: currentLine,
      line_movement: currentLine - openingLine,
      movement_direction: currentLine > openingLine ? 'away' : 'home',
      steam_moves: Math.floor(Math.random() * 3), // 0-2 steam moves
      reverse_line_movement: Math.abs(currentLine - openingLine) > 2
    };
  }

  async getSharpMoneyIndicators(game) {
    return {
      sharp_percentage: Math.random() * 0.3 + 0.1, // 10-40%
      consensus_pick: Math.random() > 0.5 ? 'home' : 'away',
      contrarian_value: Math.random() * 0.4, // 0-40%
      trap_game_indicator: Math.random() > 0.85 // 15% chance
    };
  }

  async getDetailedWeather(game) {
    // Enhanced weather beyond basic conditions
    return {
      temperature: Math.floor(Math.random() * 50) + 20, // 20-70°F
      feels_like: Math.floor(Math.random() * 50) + 20,
      wind_speed: Math.floor(Math.random() * 25), // 0-25 mph
      wind_direction: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.floor(Math.random() * 8)],
      precipitation_chance: Math.floor(Math.random() * 100),
      humidity: Math.floor(Math.random() * 60) + 30, // 30-90%
      pressure: Math.floor(Math.random() * 50) + 980, // 980-1030 mb
      uv_index: Math.floor(Math.random() * 10),
      visibility: Math.floor(Math.random() * 10) + 1 // 1-10 miles
    };
  }

  async getVenueFactors(game) {
    return {
      dome: Math.random() > 0.7, // 30% dome games
      surface_type: Math.random() > 0.8 ? 'artificial' : 'grass',
      altitude: Math.floor(Math.random() * 5000), // 0-5000 feet
      crowd_noise_factor: Math.random() * 0.3 + 0.7, // 70-100%
      home_field_advantage: Math.random() * 4 + 1 // 1-5 points
    };
  }

  async getSurfaceImpact(game) {
    return {
      surface_advantage: Math.random() > 0.5 ? 'home' : 'away',
      injury_risk_factor: Math.random() * 0.2, // 0-20% increased risk
      speed_impact: (Math.random() - 0.5) * 0.1 // -5% to +5% speed change
    };
  }

  async getTeamChemistry(game) {
    return {
      locker_room_reports: {
        home: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)],
        away: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)]
      },
      coaching_confidence: {
        home: Math.random() * 0.5 + 0.5, // 50-100%
        away: Math.random() * 0.5 + 0.5
      },
      team_unity_score: {
        home: Math.random() * 40 + 60, // 60-100
        away: Math.random() * 40 + 60
      }
    };
  }

  async getSocialSentiment(game) {
    // Mock Twitter/social media sentiment
    return {
      fan_confidence: {
        home: Math.random() * 0.6 + 0.2, // 20-80%
        away: Math.random() * 0.6 + 0.2
      },
      media_buzz: {
        home: Math.random() * 100, // 0-100 buzz score
        away: Math.random() * 100
      },
      social_mentions: {
        home: Math.floor(Math.random() * 50000) + 10000,
        away: Math.floor(Math.random() * 50000) + 10000
      }
    };
  }

  async getMotivationFactors(game) {
    return {
      playoff_implications: Math.random() > 0.6, // 40% have playoff implications
      revenge_game: Math.random() > 0.8, // 20% revenge games
      division_standings_impact: Math.random() > 0.5,
      coach_hot_seat: Math.random() > 0.9, // 10% hot seat games
      primetime_motivation: game.isPrimeTime ? Math.random() * 0.2 + 0.8 : 0.5
    };
  }

  async getHistoricalMatchups(game) {
    return {
      last_10_meetings: {
        home_wins: Math.floor(Math.random() * 11),
        away_wins: 0, // Calculate as 10 - home_wins
        average_total: Math.floor(Math.random() * 20) + 35 // 35-55
      },
      recent_trend: ['home', 'away', 'split'][Math.floor(Math.random() * 3)],
      playoff_history: Math.floor(Math.random() * 3), // 0-2 playoff meetings
      series_leader: Math.random() > 0.5 ? 'home' : 'away'
    };
  }

  async getCoachingHistory(game) {
    return {
      head_to_head_record: {
        wins: Math.floor(Math.random() * 5),
        losses: Math.floor(Math.random() * 5)
      },
      coaching_experience: {
        home_coach_years: Math.floor(Math.random() * 20) + 1,
        away_coach_years: Math.floor(Math.random() * 20) + 1
      },
      playoff_experience: {
        home: Math.floor(Math.random() * 10),
        away: Math.floor(Math.random() * 10)
      }
    };
  }

  async getSituationalTrends(game) {
    return {
      after_bye_week: Math.random() > 0.85, // 15% post-bye
      short_rest: Math.random() > 0.8, // 20% short rest
      long_road_trip: Math.random() > 0.9, // 10% long trips
      back_to_back_road: Math.random() > 0.85,
      primetime_record: {
        home: `${Math.floor(Math.random() * 10)}-${Math.floor(Math.random() * 10)}`,
        away: `${Math.floor(Math.random() * 10)}-${Math.floor(Math.random() * 10)}`
      }
    };
  }

  async getComprehensiveData(game) {
    // The perfectionist gets EVERYTHING
    return {
      data_sources_used: 25,
      models_consulted: 12,
      cross_validation_score: Math.random() * 0.3 + 0.7, // 70-100%
      data_completeness: Math.random() * 0.2 + 0.8, // 80-100%
      outlier_detection: Math.floor(Math.random() * 3), // 0-2 outliers found
      confidence_interval: [Math.random() * 0.1 + 0.4, Math.random() * 0.1 + 0.5] // 40-60% range
    };
  }

  async getMathematicalModels(game) {
    return {
      bayesian_prior: Math.random() * 0.4 + 0.3, // 30-70%
      monte_carlo_iterations: 10000,
      expected_value: (Math.random() - 0.5) * 2, // -1 to 1
      variance: Math.random() * 0.5, // 0-0.5
      confidence_interval: 0.95,
      probability_distribution: 'normal'
    };
  }

  async getMonteCarloSimulation(game) {
    return {
      simulations_run: 10000,
      home_win_percentage: Math.random() * 0.6 + 0.2, // 20-80%
      spread_distribution: {
        mean: (Math.random() - 0.5) * 10,
        std_dev: Math.random() * 5 + 2
      },
      total_distribution: {
        mean: Math.random() * 20 + 35, // 35-55
        std_dev: Math.random() * 8 + 5
      }
    };
  }

  async getObviousPatterns(game) {
    return {
      recent_form: 'obvious',
      key_injuries: Math.floor(Math.random() * 3), // 0-2 key injuries
      obvious_mismatch: Math.random() > 0.7 ? 'yes' : 'no',
      simple_logic: 'better team should win'
    };
  }

  async getRecentTrends(game) {
    return {
      last_3_games: {
        home: `${Math.floor(Math.random() * 4)}-${Math.floor(Math.random() * 4)}`,
        away: `${Math.floor(Math.random() * 4)}-${Math.floor(Math.random() * 4)}`
      },
      trending: Math.random() > 0.5 ? 'up' : 'down',
      momentum: Math.random() > 0.5 ? 'positive' : 'negative'
    };
  }

  async getValueMetrics(game) {
    return {
      efficiency_rating: {
        home: Math.random() * 40 + 60, // 60-100
        away: Math.random() * 40 + 60
      },
      cost_per_win: {
        home: Math.random() * 50 + 25, // 25-75 million
        away: Math.random() * 50 + 25
      },
      value_over_replacement: {
        home: (Math.random() - 0.5) * 4, // -2 to 2
        away: (Math.random() - 0.5) * 4
      }
    };
  }

  async getEfficiencyStats(game) {
    return {
      points_per_drive: {
        home: Math.random() * 2 + 1, // 1-3 points
        away: Math.random() * 2 + 1
      },
      yards_per_play: {
        home: Math.random() * 3 + 4, // 4-7 yards
        away: Math.random() * 3 + 4
      },
      time_of_possession: {
        home: Math.random() * 10 + 25, // 25-35 minutes
        away: 0 // Calculate as 60 - home
      }
    };
  }

  async getKeyStats(game) {
    return {
      turnover_differential: {
        home: Math.floor(Math.random() * 21) - 10, // -10 to +10
        away: Math.floor(Math.random() * 21) - 10
      },
      points_per_game: {
        home: Math.random() * 15 + 15, // 15-30
        away: Math.random() * 15 + 15
      },
      points_allowed: {
        home: Math.random() * 15 + 15, // 15-30
        away: Math.random() * 15 + 15
      }
    };
  }

  async getHeadlineFactors(game) {
    return {
      star_player_injured: Math.random() > 0.8, // 20% chance
      coach_controversy: Math.random() > 0.9, // 10% chance
      trade_deadline_move: Math.random() > 0.95, // 5% chance
      weather_concerns: Math.random() > 0.7, // 30% chance
      playoff_implications: Math.random() > 0.5 // 50% chance
    };
  }

  /**
   * Get research summary for expert
   */
  getResearchSummary(expertId, researchData) {
    const strategy = this.researchStrategies[expertId];
    if (!strategy) return 'No research strategy found';

    const keyFindings = [];

    // Extract key findings based on expert's focus
    strategy.focusAreas.forEach(area => {
      switch (area) {
        case 'offensive efficiency':
          if (researchData.advancedStats) {
            keyFindings.push(`Home EPA/play: ${researchData.advancedStats.home_epa_per_play.toFixed(3)}`);
          }
          break;
        case 'betting value':
          if (researchData.bettingPercentages) {
            keyFindings.push(`Public on home: ${(researchData.bettingPercentages.public_bet_percentage.home * 100).toFixed(1)}%`);
          }
          break;
        case 'weather conditions':
          if (researchData.detailedWeather) {
            keyFindings.push(`Wind: ${researchData.detailedWeather.wind_speed}mph ${researchData.detailedWeather.wind_direction}`);
          }
          break;
        // Add more cases as needed
      }
    });

    return {
      strategy: strategy.strategy,
      keyFindings: keyFindings,
      dataPoints: Object.keys(researchData).length,
      researchDepth: strategy.researchDepth,
      confidence: this.calculateResearchConfidence(strategy.researchDepth, keyFindings.length)
    };
  }

  /**
   * Calculate research confidence based on depth and findings
   */
  calculateResearchConfidence(depth, findingsCount) {
    const depthScore = {
      'shallow': 0.4,
      'surface': 0.5,
      'market-focused': 0.6,
      'environmental': 0.6,
      'psychological': 0.5,
      'historical': 0.7,
      'mathematical': 0.8,
      'value-focused': 0.6,
      'comprehensive': 0.9,
      'deep': 0.85
    };

    const baseConfidence = depthScore[depth] || 0.5;
    const findingsBonus = Math.min(0.2, findingsCount * 0.05);

    return Math.min(0.95, baseConfidence + findingsBonus);
  }

  // VECTOR-POWERED RESEARCH METHODS

  /**
   * Get vector-based research for expert
   */
  async getVectorResearch(expertId, query, categories) {
    try {
      const results = {
        knowledgeBase: [],
        expertResearch: [],
        newsArticles: [],
        similarBets: []
      };

      // Search knowledge base for categories
      for (const category of categories) {
        const knowledge = await vectorSearchService.searchKnowledgeBase(
          `${query} ${category}`,
          { matchThreshold: 0.7, matchCount: 3, categoryFilter: category }
        );
        results.knowledgeBase.push(...knowledge.results);
      }

      // Search previous expert research
      const expertResearch = await vectorSearchService.searchExpertResearch(
        query,
        { matchThreshold: 0.7, matchCount: 5, expertIdFilter: expertId }
      );
      results.expertResearch = expertResearch.results;

      // Search relevant news
      const newsSearch = await vectorSearchService.searchNewsArticles(
        query,
        { matchThreshold: 0.7, matchCount: 3 }
      );
      results.newsArticles = newsSearch.results;

      // Search similar betting patterns
      const similarBets = await vectorSearchService.searchSimilarBets(
        query,
        { matchThreshold: 0.6, matchCount: 3, expertIdFilter: expertId, onlyWinners: true }
      );
      results.similarBets = similarBets.results;

      console.log(`🤖 ${expertId} found ${Object.values(results).flat().length} vector insights`);

      return results;
    } catch (error) {
      console.error(`Vector research failed for ${expertId}:`, error);
      return {
        knowledgeBase: [],
        expertResearch: [],
        newsArticles: [],
        similarBets: [],
        error: error.message
      };
    }
  }

  /**
   * Comprehensive vector research for the perfectionist
   */
  async getComprehensiveVectorResearch(expertId, query, game) {
    try {
      // Multi-source semantic search
      const allContent = await vectorSearchService.searchAllContent(
        query,
        { matchThreshold: 0.6, matchCount: 50 }
      );

      // Team-specific searches
      const homeTeamResearch = await vectorSearchService.searchAllContent(
        game.home_team,
        { matchThreshold: 0.8, matchCount: 10 }
      );

      const awayTeamResearch = await vectorSearchService.searchAllContent(
        game.away_team,
        { matchThreshold: 0.8, matchCount: 10 }
      );

      // Historical prediction analysis
      const predictionAnalysis = await vectorSearchService.searchPredictionAnalysis(
        query,
        { matchThreshold: 0.7, matchCount: 10 }
      );

      return {
        allContent: allContent.results,
        sources: allContent.sources,
        homeTeamInsights: homeTeamResearch.results,
        awayTeamInsights: awayTeamResearch.results,
        historicalPredictions: predictionAnalysis.results,
        totalInsights: allContent.results.length + homeTeamResearch.results.length +
                       awayTeamResearch.results.length + predictionAnalysis.results.length
      };
    } catch (error) {
      console.error(`Comprehensive vector research failed:`, error);
      return {
        allContent: [],
        sources: {},
        homeTeamInsights: [],
        awayTeamInsights: [],
        historicalPredictions: [],
        totalInsights: 0,
        error: error.message
      };
    }
  }

  /**
   * Store expert research with vector embedding
   */
  async storeExpertResearch(expertId, game, researchData) {
    try {
      // Create research summary text
      const researchSummary = this.createResearchSummary(expertId, game, researchData);

      // Store in vector database
      const result = await vectorSearchService.storeExpertResearch(
        expertId,
        'game_analysis',
        researchSummary,
        {
          gameId: game.id,
          homeTeam: game.home_team,
          awayTeam: game.away_team,
          gameTime: game.game_time,
          researchStrategy: researchData.researchStrategy,
          dataPointsCount: Object.keys(researchData).length
        }
      );

      if (result.success) {
        console.log(`📚 Stored research for ${expertId}: ${researchSummary.length} chars`);
      }

      return result;
    } catch (error) {
      console.error(`Failed to store research for ${expertId}:`, error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Create text summary of research for embedding
   */
  createResearchSummary(expertId, game, researchData) {
    const strategy = this.researchStrategies[expertId];
    let summary = `Expert: ${expertId}\n`;
    summary += `Strategy: ${strategy?.strategy || 'Unknown'}\n`;
    summary += `Game: ${game.home_team} vs ${game.away_team}\n`;
    summary += `Research Focus: ${strategy?.focusAreas?.join(', ') || 'General'}\n\n`;

    // Add key findings based on research data
    if (researchData.advancedStats) {
      summary += `Advanced Stats: Home EPA ${researchData.advancedStats.home_epa_per_play}, Away EPA ${researchData.advancedStats.away_epa_per_play}\n`;
    }

    if (researchData.bettingPercentages) {
      summary += `Betting: ${(researchData.bettingPercentages.public_bet_percentage.home * 100).toFixed(1)}% on home team\n`;
    }

    if (researchData.detailedWeather) {
      summary += `Weather: ${researchData.detailedWeather.temperature}°F, Wind ${researchData.detailedWeather.wind_speed}mph\n`;
    }

    if (researchData.vectorResearch) {
      const totalInsights = Object.values(researchData.vectorResearch).flat().length;
      summary += `Vector Insights: ${totalInsights} relevant data points found\n`;
    }

    summary += `\nResearch Depth: ${strategy?.researchDepth || 'standard'}\n`;
    summary += `Total Data Points: ${Object.keys(researchData).length}\n`;

    return summary;
  }

  /**
   * Get expert's past research patterns
   */
  async getExpertResearchPatterns(expertId, limit = 10) {
    try {
      const patterns = await vectorSearchService.searchExpertResearch(
        'analysis patterns trends',
        {
          matchThreshold: 0.5,
          matchCount: limit,
          expertIdFilter: expertId
        }
      );

      return {
        success: true,
        patterns: patterns.results,
        totalFound: patterns.matchCount
      };
    } catch (error) {
      console.error(`Failed to get patterns for ${expertId}:`, error);
      return {
        success: false,
        error: error.message,
        patterns: [],
        totalFound: 0
      };
    }
  }

  /**
   * Find experts with similar research approaches
   */
  async findSimilarExperts(expertId, researchQuery) {
    try {
      const similarResearch = await vectorSearchService.searchExpertResearch(
        researchQuery,
        {
          matchThreshold: 0.7,
          matchCount: 20 // Get more to find different experts
        }
      );

      // Group by expert and count similarities
      const expertSimilarity = {};
      similarResearch.results.forEach(result => {
        if (result.expert_id !== expertId) {
          expertSimilarity[result.expert_id] = (expertSimilarity[result.expert_id] || 0) + result.similarity;
        }
      });

      // Sort by similarity
      const sortedExperts = Object.entries(expertSimilarity)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .map(([expert, similarity]) => ({ expert, similarity }));

      return {
        success: true,
        similarExperts: sortedExperts,
        totalResearched: similarResearch.matchCount
      };
    } catch (error) {
      console.error(`Failed to find similar experts:`, error);
      return {
        success: false,
        error: error.message,
        similarExperts: []
      };
    }
  }
}

// Create singleton instance
const expertResearchService = new ExpertResearchService();

export default expertResearchService;