import axios from 'axios';
import { supabase } from './supabaseClient.js';
import modelCouncilService from './modelCouncilService.js';
import expertResearchService from './expertResearchService.js';

const OPENROUTER_API_KEY = import.meta.env.VITE_OPENROUTER_API_KEY;
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

/**
 * NFL Expert Panel System
 *
 * 15 AI "experts" with unique personalities who compete against each other
 * Top 5 experts form the council, with betting mechanics and point systems
 */
class ExpertPanelService {
  constructor() {
    // 15 AI Experts with personalities and specialties
    this.experts = [
      // COUNCIL TIER - Top 5 Active Experts
      {
        id: 'claude-the-analyst',
        name: 'Claude "The Analyst" Thompson',
        model: 'anthropic/claude-sonnet-4.5',
        personality: 'Methodical, data-driven, loves advanced metrics',
        specialty: 'Deep statistical analysis and trend identification',
        avatar: '🧠',
        points: 1500,
        councilRank: 1,
        catchphrase: "The numbers don't lie, folks.",
        betting_style: 'Conservative, high-confidence bets only',
        research_strategy: 'Advanced metrics: DVOA, EPA, success rate, red zone efficiency',
        data_sources: ['Pro Football Focus', 'Football Study Hall', 'Team drive charts']
      },
      {
        id: 'grok-the-maverick',
        name: 'Grok "The Maverick" Rodriguez',
        model: 'x-ai/grok-4-fast',
        personality: 'Bold, contrarian, loves upset picks',
        specialty: 'Finding value in underdog situations',
        avatar: '🚀',
        points: 1420,
        councilRank: 2,
        catchphrase: "When everyone zigs, I zag.",
        betting_style: 'Aggressive, loves long-shot multipliers'
      },
      {
        id: 'gemini-the-weatherman',
        name: 'Gemini "The Weatherman" Flash',
        model: 'google/gemini-2.5-flash-preview-09-2025',
        personality: 'Environmental expert, considers all conditions',
        specialty: 'Weather impact and outdoor game analysis',
        avatar: '🌪️',
        points: 1380,
        councilRank: 3,
        catchphrase: "It's not just the game, it's the elements.",
        betting_style: 'Medium-risk, weather-dependent confidence'
      },
      {
        id: 'deepseek-the-intuitive',
        name: 'DeepSeek "The Intuitive" Chen',
        model: 'deepseek/deepseek-chat-v3.1:free',
        personality: 'Intuitive, considers intangibles and momentum',
        specialty: 'Team chemistry and psychological factors',
        avatar: '🔮',
        points: 1350,
        councilRank: 4,
        catchphrase: "Sometimes you gotta feel the game.",
        betting_style: 'Intuition-based, variable confidence'
      },
      {
        id: 'gpt-the-historian',
        name: 'GPT "The Historian" Williams',
        model: 'openai/gpt-5',
        personality: 'Historical perspective, loves precedents',
        specialty: 'Historical matchups and playoff implications',
        avatar: '📚',
        points: 1320,
        councilRank: 5,
        catchphrase: "History has a way of repeating itself.",
        betting_style: 'Pattern-based, moderate risk'
      },

      // CHALLENGER TIER - Fighting for Council Spots
      {
        id: 'gemini-pro-the-perfectionist',
        name: 'Gemini Pro "The Perfectionist" Singh',
        model: 'google/gemini-2.5-pro',
        personality: 'Perfectionist, wants all the data',
        specialty: 'Comprehensive game breakdowns',
        avatar: '💎',
        points: 1280,
        councilRank: 6,
        catchphrase: "Every detail matters.",
        betting_style: 'Calculated precision bets'
      },
      {
        id: 'qwen-the-calculator',
        name: 'Qwen "The Calculator" Liu',
        model: 'z-ai/glm-4.6',
        personality: 'Math genius, probability focused',
        specialty: 'Advanced probability calculations',
        avatar: '🧮',
        points: 1250,
        councilRank: 7,
        catchphrase: "Probability is destiny.",
        betting_style: 'Mathematical precision'
      },
      {
        id: 'sonoma-the-rookie',
        name: 'Sonoma "The Rookie" Sky',
        model: 'google/gemini-2.5-flash',
        personality: 'Fresh perspective, eager to prove itself',
        specialty: 'Unbiased analysis without preconceptions',
        avatar: '⭐',
        points: 1200,
        councilRank: 8,
        catchphrase: "Fresh eyes see clear truths.",
        betting_style: 'Eager, sometimes overconfident'
      },
      {
        id: 'deepseek-free-the-underdog',
        name: 'DeepSeek Free "The Underdog" Park',
        model: 'deepseek/deepseek-chat-v3.1:free',
        personality: 'Scrappy, hungry to prove free can beat premium',
        specialty: 'Value finding and efficiency analysis',
        avatar: '🥊',
        points: 1150,
        councilRank: 9,
        catchphrase: "Don't need to be expensive to be right.",
        betting_style: 'All-in when confident'
      },
      {
        id: 'flash-the-speedster',
        name: 'Flash "The Speedster" Johnson',
        model: 'google/gemini-2.5-flash-preview-09-2025',
        personality: 'Quick decisions, trusts first instincts',
        specialty: 'Rapid-fire analysis and gut calls',
        avatar: '⚡',
        points: 1100,
        councilRank: 10,
        catchphrase: "First thought, best thought.",
        betting_style: 'Quick, instinctive bets'
      },

      // DEVELOPMENT LEAGUE - Trying to Break Through
      {
        id: 'claude-opus-the-veteran',
        name: 'Claude Opus "The Veteran" Davis',
        model: 'anthropic/claude-sonnet-4.5',
        personality: 'Old school, seen it all before',
        specialty: 'Veteran leadership and clutch situations',
        avatar: '👑',
        points: 1050,
        councilRank: 11,
        catchphrase: "Been there, done that.",
        betting_style: 'Experience-based, steady'
      },
      {
        id: 'mixtral-the-philosopher',
        name: 'Mixtral "The Philosopher" Dubois',
        model: 'z-ai/glm-4.6',
        personality: 'Philosophical, considers deeper meanings',
        specialty: 'Game narrative and storyline analysis',
        avatar: '🤔',
        points: 1000,
        councilRank: 12,
        catchphrase: "What story is this game trying to tell?",
        betting_style: 'Narrative-driven confidence'
      },
      {
        id: 'llama-the-consistent',
        name: 'Llama "The Consistent" Martinez',
        model: 'google/gemini-2.5-pro',
        personality: 'Steady, reliable, never flashy',
        specialty: 'Consistent baseline predictions',
        avatar: '🦙',
        points: 950,
        councilRank: 13,
        catchphrase: "Slow and steady wins the race.",
        betting_style: 'Conservative, reliable'
      },
      {
        id: 'o1-the-thinker',
        name: 'O1 "The Thinker" Watson',
        model: 'openai/gpt-5',
        personality: 'Deep thinker, takes time to analyze',
        specialty: 'Complex reasoning and edge cases',
        avatar: '🧐',
        points: 900,
        councilRank: 14,
        catchphrase: "Let me think about that...",
        betting_style: 'Thoughtful, well-reasoned bets'
      },
      {
        id: 'haiku-the-minimalist',
        name: 'Haiku "The Minimalist" Tanaka',
        model: 'anthropic/claude-sonnet-4.5',
        personality: 'Minimalist, cuts to the essence',
        specialty: 'Concise, essential insights only',
        avatar: '🎋',
        points: 850,
        councilRank: 15,
        catchphrase: "Less is more.",
        betting_style: 'Simple, focused bets'
      }
    ];

    // Weekly expert performance tracking
    this.weeklyPerformance = {};
    this.currentWeek = this.getCurrentWeek();

    // Initialize expert performance
    this.initializeExpertPerformance();
  }

  /**
   * Generate predictions from all 15 experts with personalities and betting
   */
  async generateExpertPanel(game) {
    console.log(`🏈 Expert Panel convening for ${game.away_team} @ ${game.home_team}...`);

    const expertPredictions = [];

    // Get features for the game
    const features = await this.extractGameFeatures(game);

    // Get predictions from all 15 experts in parallel
    const promises = this.experts.map(async (expert) => {
      try {
        const prediction = await this.getExpertPrediction(expert, game, features);
        if (prediction) {
          // Expert places their bet based on confidence
          const bet = this.calculateExpertBet(expert, prediction);

          return {
            expertId: expert.id,
            expertName: expert.name,
            avatar: expert.avatar,
            catchphrase: expert.catchphrase,
            points: expert.points,
            councilRank: expert.councilRank,
            prediction: prediction,
            bet: bet,
            reasoning: prediction.reasoning,
            timestamp: new Date().toISOString()
          };
        }
      } catch (error) {
        console.error(`❌ ${expert.name} couldn't make prediction:`, error.message);
      }
      return null;
    });

    const results = await Promise.all(promises);
    const validPredictions = results.filter(r => r !== null);

    // Calculate council consensus (top 5)
    const council = validPredictions
      .filter(p => p.councilRank <= 5)
      .sort((a, b) => a.councilRank - b.councilRank);

    const consensus = this.calculateCouncilConsensus(council);

    // Store expert panel results
    const panelResult = {
      game_id: game.id,
      all_experts: validPredictions,
      council_members: council,
      consensus: consensus,
      total_experts: validPredictions.length,
      created_at: new Date().toISOString()
    };

    // Save to database
    await this.saveExpertPanel(panelResult);

    console.log(`✅ Expert Panel complete: ${validPredictions.length} experts, Council consensus: ${consensus.homeWinProb}% home`);

    return panelResult;
  }

  /**
   * Get prediction from individual expert with their unique research
   */
  async getExpertPrediction(expert, game, features) {
    // Conduct expert-specific research
    const researchData = await expertResearchService.conductExpertResearch(expert.id, game, features);

    // Get research summary for the expert
    const researchSummary = expertResearchService.getResearchSummary(expert.id, researchData);

    const prompt = this.buildExpertPrompt(expert, game, researchData, researchSummary);

    try {
      const response = await axios.post(OPENROUTER_URL, {
        model: expert.model,
        messages: [
          {
            role: 'system',
            content: `You are ${expert.name}, a NFL prediction expert.
                     Personality: ${expert.personality}
                     Specialty: ${expert.specialty}
                     Catchphrase: "${expert.catchphrase}"

                     Respond in character and provide predictions as JSON:
                     {
                       "homeWinProb": number (0-100),
                       "awayWinProb": number (0-100),
                       "spread": number (negative if home favored),
                       "total": number,
                       "confidence": number (1-10),
                       "reasoning": "your analysis in character",
                       "keyFactor": "most important factor"
                     }`
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.7, // Allow some personality variation
        max_tokens: 600
      }, {
        headers: {
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://nfl-predictor.app',
          'X-Title': 'NFL Expert Panel'
        }
      });

      const content = response.data.choices[0].message.content;
      const jsonMatch = content.match(/\{[\s\S]*\}/);

      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);

        // Ensure probabilities add to 100
        if (parsed.homeWinProb + parsed.awayWinProb !== 100) {
          parsed.awayWinProb = 100 - parsed.homeWinProb;
        }

        return parsed;
      }
    } catch (error) {
      console.error(`Error getting ${expert.name} prediction:`, error.message);
      return null;
    }
  }

  /**
   * Calculate how much expert bets based on confidence
   */
  calculateExpertBet(expert, prediction) {
    const basePoints = expert.points;
    const confidence = prediction.confidence; // 1-10 scale
    const maxBetPercent = this.getMaxBetPercent(expert.betting_style);

    // Calculate bet amount (percentage of total points)
    const betPercent = (confidence / 10) * maxBetPercent;
    const betAmount = Math.floor(basePoints * betPercent);

    // Calculate potential payout based on confidence
    const odds = this.confidenceToOdds(confidence);
    const potentialPayout = Math.floor(betAmount * odds);

    return {
      amount: betAmount,
      percentage: betPercent * 100,
      odds: odds,
      potentialPayout: potentialPayout,
      pick: prediction.homeWinProb > 50 ? 'home' : 'away',
      reasoning: `Betting ${betPercent.toFixed(1)}% (${betAmount} points) with ${confidence}/10 confidence`
    };
  }

  /**
   * Get max bet percentage based on betting style
   */
  getMaxBetPercent(bettingStyle) {
    const styleMap = {
      'Conservative, high-confidence bets only': 0.15, // 15% max
      'Aggressive, loves long-shot multipliers': 0.35, // 35% max
      'Medium-risk, weather-dependent confidence': 0.20, // 20% max
      'Intuition-based, variable confidence': 0.25, // 25% max
      'Pattern-based, moderate risk': 0.18, // 18% max
      'All-in when confident': 0.50, // 50% max (risky!)
      'Quick, instinctive bets': 0.12, // 12% max (frequent)
      'Conservative, reliable': 0.10 // 10% max (safe)
    };

    return styleMap[bettingStyle] || 0.20; // Default 20%
  }

  /**
   * Convert confidence (1-10) to betting odds
   */
  confidenceToOdds(confidence) {
    // Higher confidence = lower odds (safer bet)
    // Confidence 10 = 1.1x payout, Confidence 1 = 5.0x payout
    return Math.max(1.1, 5.5 - (confidence * 0.4));
  }

  /**
   * Calculate council consensus from top 5 experts
   */
  calculateCouncilConsensus(council) {
    if (council.length === 0) return null;

    // Weight by inverse rank (rank 1 gets most weight)
    const weights = council.map(expert => 6 - expert.councilRank); // [5,4,3,2,1]
    const totalWeight = weights.reduce((sum, w) => sum + w, 0);

    let homeWinProb = 0;
    let spread = 0;
    let total = 0;

    council.forEach((expert, index) => {
      const weight = weights[index] / totalWeight;
      homeWinProb += expert.prediction.homeWinProb * weight;
      spread += expert.prediction.spread * weight;
      total += expert.prediction.total * weight;
    });

    return {
      homeWinProb: Math.round(homeWinProb * 10) / 10,
      awayWinProb: Math.round((100 - homeWinProb) * 10) / 10,
      spread: Math.round(spread * 2) / 2,
      total: Math.round(total),
      consensusStrength: this.calculateConsensusStrength(council),
      councilMembers: council.length
    };
  }

  /**
   * Calculate how much the council agrees (0-100%)
   */
  calculateConsensusStrength(council) {
    if (council.length < 2) return 100;

    const homeProbs = council.map(e => e.prediction.homeWinProb);
    const mean = homeProbs.reduce((sum, p) => sum + p, 0) / homeProbs.length;
    const variance = homeProbs.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / homeProbs.length;
    const stdDev = Math.sqrt(variance);

    // Convert to agreement percentage (lower stdDev = higher agreement)
    const agreement = Math.max(0, 100 - (stdDev * 2));
    return Math.round(agreement);
  }

  /**
   * Build prompt for expert with their research
   */
  buildExpertPrompt(expert, game, researchData, researchSummary) {
    let prompt = `🏈 ${expert.name} here! ${expert.catchphrase}

    🎯 MY RESEARCH STRATEGY: ${researchSummary.strategy}
    📊 Data Points Analyzed: ${researchSummary.dataPoints}
    🔍 Research Depth: ${researchSummary.researchDepth}
    ✅ Research Confidence: ${(researchSummary.confidence * 100).toFixed(1)}%

    GAME: ${game.away_team} @ ${game.home_team} (Week ${game.week})

    📈 KEY FINDINGS FROM MY RESEARCH:`;

    // Add key findings
    researchSummary.keyFindings.forEach(finding => {
      prompt += `\n    • ${finding}`;
    });

    prompt += `

    📊 BASIC DATA:
    ${game.home_team}: ${researchData.homeRating} ELO
    ${game.away_team}: ${researchData.awayRating} ELO
    Recent Form - ${game.home_team}: ${researchData.homeRecentForm.wins}-${researchData.homeRecentForm.losses}
    Recent Form - ${game.away_team}: ${researchData.awayRecentForm.wins}-${researchData.awayRecentForm.losses}

    🌤️ CONDITIONS:
    Weather: ${researchData.weatherCondition}, ${researchData.temperature}°F
    Primetime: ${researchData.isPrimeTime ? 'Yes' : 'No'}
    Divisional: ${researchData.isDivisional ? 'Yes' : 'No'}

    💰 MARKET:
    Spread: ${game.home_team} ${researchData.marketSpread}
    Total: ${researchData.marketTotal}`;

    // Add specialized research based on expert
    if (researchData.advancedStats && expert.id === 'claude-the-analyst') {
      prompt += `\n\n🧠 MY ADVANCED METRICS:
      DVOA: Home ${(researchData.advancedStats.home_dvoa * 100).toFixed(1)}%, Away ${(researchData.advancedStats.away_dvoa * 100).toFixed(1)}%
      EPA/Play: Home ${researchData.advancedStats.home_epa_per_play.toFixed(3)}, Away ${researchData.advancedStats.away_epa_per_play.toFixed(3)}
      Red Zone: Home ${(researchData.advancedStats.home_red_zone_eff * 100).toFixed(1)}%, Away ${(researchData.advancedStats.away_red_zone_eff * 100).toFixed(1)}%`;
    }

    if (researchData.bettingPercentages && expert.id === 'grok-the-maverick') {
      prompt += `\n\n🚀 MY VALUE ANALYSIS:
      Public Bet %: Home ${(researchData.bettingPercentages.public_bet_percentage.home * 100).toFixed(1)}%
      Money %: Home ${(researchData.bettingPercentages.money_percentage.home * 100).toFixed(1)}%
      Sharp vs Square: ${researchData.bettingPercentages.public_bet_percentage.home !== researchData.bettingPercentages.money_percentage.home ? 'DISCORD!' : 'Aligned'}`;
    }

    if (researchData.detailedWeather && expert.id === 'gemini-the-weatherman') {
      prompt += `\n\n🌪️ MY WEATHER ANALYSIS:
      Wind: ${researchData.detailedWeather.wind_speed}mph ${researchData.detailedWeather.wind_direction}
      Feels Like: ${researchData.detailedWeather.feels_like}°F
      Precipitation: ${researchData.detailedWeather.precipitation_chance}% chance
      Humidity: ${researchData.detailedWeather.humidity}%`;
    }

    if (researchData.teamChemistry && expert.id === 'deepseek-the-intuitive') {
      prompt += `\n\n🔮 MY INTANGIBLES:
      Locker Room: Home ${researchData.teamChemistry.locker_room_reports.home}, Away ${researchData.teamChemistry.locker_room_reports.away}
      Team Unity: Home ${researchData.teamChemistry.team_unity_score.home.toFixed(0)}, Away ${researchData.teamChemistry.team_unity_score.away.toFixed(0)}
      Coaching Confidence: Home ${(researchData.teamChemistry.coaching_confidence.home * 100).toFixed(1)}%`;
    }

    if (researchData.historicalH2H && expert.id === 'gpt-the-historian') {
      prompt += `\n\n📚 MY HISTORICAL DATA:
      Last 10 Meetings: Home ${researchData.historicalH2H.home_wins}-${10 - researchData.historicalH2H.home_wins}
      Recent Trend: ${researchData.historicalH2H.recent_trend}
      Series Leader: ${researchData.historicalH2H.series_leader}`;
    }

    prompt += `\n\nAs your ${expert.specialty} specialist using ${researchSummary.strategy}, what's your prediction?

    Remember my betting style: ${expert.betting_style}

    Stay in character and explain your reasoning based on MY research!`;

    return prompt;
  }

  /**
   * Update expert rankings after game results
   */
  async updateExpertRankings(gameId) {
    try {
      // Get game result
      const { data: game } = await supabase
        .from('games')
        .select('*')
        .eq('id', gameId)
        .eq('status', 'final')
        .single();

      if (!game) return;

      // Get expert panel predictions
      const { data: panelData } = await supabase
        .from('expert_panels')
        .select('*')
        .eq('game_id', gameId)
        .single();

      if (!panelData) return;

      const actualHomeWon = game.home_score > game.away_score;
      const actualSpread = game.away_score - game.home_score;
      const actualTotal = game.home_score + game.away_score;

      // Update each expert's performance and points
      for (const expertPred of panelData.all_experts) {
        const expert = this.experts.find(e => e.id === expertPred.expertId);
        if (!expert) continue;

        // Check if expert was correct
        const predictedHomeWin = expertPred.prediction.homeWinProb > 50;
        const wasCorrect = predictedHomeWin === actualHomeWon;

        // Calculate spread and total accuracy
        const spreadError = Math.abs(expertPred.prediction.spread - actualSpread);
        const totalError = Math.abs(expertPred.prediction.total - actualTotal);

        // Calculate points earned/lost from bet
        let pointsChange = 0;
        if (wasCorrect) {
          // Win bet - gain payout
          pointsChange = expertPred.bet.potentialPayout - expertPred.bet.amount;
        } else {
          // Lose bet - lose bet amount
          pointsChange = -expertPred.bet.amount;
        }

        // Bonus/penalty for accuracy
        const accuracyBonus = wasCorrect ? 50 : -25;
        const spreadBonus = spreadError < 3 ? 25 : (spreadError > 7 ? -15 : 0);
        const totalBonus = totalError < 5 ? 20 : (totalError > 10 ? -10 : 0);

        const totalPointsChange = pointsChange + accuracyBonus + spreadBonus + totalBonus;

        // Update expert points
        expert.points = Math.max(100, expert.points + totalPointsChange);

        console.log(`📊 ${expert.name}: ${wasCorrect ? '✅' : '❌'} ${totalPointsChange > 0 ? '+' : ''}${totalPointsChange} points (now ${expert.points})`);
      }

      // Re-rank experts by points and update council
      this.reRankExperts();

      // Save updated rankings
      await this.saveExpertRankings();

    } catch (error) {
      console.error('Error updating expert rankings:', error);
    }
  }

  /**
   * Re-rank experts by points and update council positions
   */
  reRankExperts() {
    // Sort by points (highest first)
    this.experts.sort((a, b) => b.points - a.points);

    // Update council ranks
    this.experts.forEach((expert, index) => {
      expert.councilRank = index + 1;
    });

    console.log('🏆 Updated Expert Rankings:');
    this.experts.slice(0, 10).forEach(expert => {
      const status = expert.councilRank <= 5 ? '👑 COUNCIL' : '🥊 CHALLENGER';
      console.log(`  ${expert.councilRank}. ${expert.name} - ${expert.points} pts ${status}`);
    });
  }

  /**
   * Get current expert standings
   */
  getExpertStandings() {
    return {
      council: this.experts.filter(e => e.councilRank <= 5),
      challengers: this.experts.filter(e => e.councilRank > 5 && e.councilRank <= 10),
      developmentLeague: this.experts.filter(e => e.councilRank > 10),
      lastUpdated: new Date().toISOString()
    };
  }

  /**
   * Save expert panel results to database
   */
  async saveExpertPanel(panelResult) {
    try {
      await supabase
        .from('expert_panels')
        .insert({
          game_id: panelResult.game_id,
          expert_predictions: panelResult.all_experts,
          council_consensus: panelResult.consensus,
          total_experts: panelResult.total_experts,
          created_at: panelResult.created_at
        });
    } catch (error) {
      console.error('Error saving expert panel:', error);
    }
  }

  /**
   * Save expert rankings to database
   */
  async saveExpertRankings() {
    try {
      await supabase
        .from('expert_rankings')
        .upsert({
          week: this.currentWeek,
          rankings: this.experts.map(e => ({
            id: e.id,
            name: e.name,
            points: e.points,
            rank: e.councilRank
          })),
          updated_at: new Date().toISOString()
        }, {
          onConflict: 'week'
        });
    } catch (error) {
      console.error('Error saving expert rankings:', error);
    }
  }

  /**
   * Initialize expert performance tracking
   */
  async initializeExpertPerformance() {
    // Load existing rankings if available
    try {
      const { data } = await supabase
        .from('expert_rankings')
        .select('*')
        .eq('week', this.currentWeek)
        .single();

      if (data?.rankings) {
        // Update expert points from database
        data.rankings.forEach(saved => {
          const expert = this.experts.find(e => e.id === saved.id);
          if (expert) {
            expert.points = saved.points;
            expert.councilRank = saved.rank;
          }
        });

        // Re-sort by current points
        this.experts.sort((a, b) => b.points - a.points);
      }
    } catch (error) {
      console.log('No existing rankings found, using defaults');
    }
  }

  // Helper methods
  getCurrentWeek() {
    const now = new Date();
    const start = new Date(now.getFullYear(), 8, 1); // Sept 1
    const weeksSinceStart = Math.floor((now - start) / (7 * 24 * 60 * 60 * 1000));
    return Math.max(1, Math.min(18, weeksSinceStart + 1));
  }

  async extractGameFeatures(game) {
    // Use simplified feature extraction for now
    return {
      homeRating: 1400 + Math.random() * 200,
      awayRating: 1400 + Math.random() * 200,
      homeRecentForm: { wins: Math.floor(Math.random() * 4) + 1, losses: Math.floor(Math.random() * 4) + 1 },
      awayRecentForm: { wins: Math.floor(Math.random() * 4) + 1, losses: Math.floor(Math.random() * 4) + 1 },
      weatherCondition: 'Clear',
      temperature: 65,
      isPrimeTime: Math.random() > 0.7,
      isDivisional: Math.random() > 0.75,
      marketSpread: (Math.random() - 0.5) * 14,
      marketTotal: 42 + Math.random() * 16
    };
  }
}

// Create singleton instance
const expertPanelService = new ExpertPanelService();

export default expertPanelService;
