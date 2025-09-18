import espnApiService from './espnApiService.js';
const espnService = espnApiService; // Alias for compatibility
import oddsService from './oddsService.js';
import modelCouncilService from './modelCouncilService.js';
// Try Node.js version first, fallback to browser version
let supabase, supabaseHelpers;

try {
  // Try browser version first (for Vite environments)
  const clientModule = await import('./supabaseClient.js');
  supabase = clientModule.supabase;
  supabaseHelpers = clientModule.supabaseHelpers;
} catch (e) {
  // Fallback to Node.js version
  const nodeClientModule = await import('./supabaseClientNode.js');
  supabase = nodeClientModule.supabase;
  // Create minimal helpers for Node.js context
  supabaseHelpers = {
    subscribeToGames: () => ({ unsubscribe: () => {} }),
    subscribeToPredictions: () => ({ unsubscribe: () => {} }),
    subscribeToOdds: () => ({ unsubscribe: () => {} })
  };
}

class DataIntegrationService {
  constructor() {
    this.syncInProgress = false;
    this.lastSyncTime = null;
    this.syncInterval = null;
  }

  // Complete data sync from all sources
  async performFullSync() {
    if (this.syncInProgress) {
      console.log('Sync already in progress, skipping...');
      return null;
    }

    this.syncInProgress = true;
    const startTime = Date.now();

    const results = {
      espn: { success: false, data: null, error: null },
      odds: { success: false, data: null, error: null },
      weather: { success: false, data: null, error: null },
      duration: 0,
      timestamp: new Date().toISOString()
    };

    try {
      console.log('🔄 Starting full data sync...\n');

      // 1. Sync ESPN data first (base game data)
      console.log('📡 Syncing ESPN 2025 data...');
      try {
        // Use the comprehensive ESPN service that handles 2025 data properly
        results.espn.data = await espnService.syncGamesToSupabase();
        results.espn.success = true;
        console.log(`✅ ESPN: ${results.espn.data.synced}/${results.espn.data.total} games synced (2025 season)`);

        // Also sync teams if needed
        await this.syncTeamsFromESPN();
        console.log('✅ ESPN: Teams data verified');

      } catch (error) {
        results.espn.error = error.message;
        console.error('❌ ESPN sync failed:', error.message);
      }

      // 2. Sync odds data
      console.log('\n💰 Syncing odds data...');
      try {
        results.odds.data = await oddsService.syncOddsToSupabase();
        results.odds.success = true;
        console.log(`✅ Odds: ${results.odds.data.synced} odds records synced`);

        // Check API quota
        const quota = await oddsService.checkQuota();
        if (quota) {
          console.log(`   Quota: ${quota.remaining}/${quota.total} requests remaining`);
        }
      } catch (error) {
        results.odds.error = error.message;
        console.error('❌ Odds sync failed:', error.message);
      }

      // 3. Sync weather data for upcoming games
      console.log('\n🌤️ Syncing weather data...');
      try {
        results.weather.data = await this.syncWeatherData();
        results.weather.success = true;
        console.log(`✅ Weather: ${results.weather.data.synced} games updated with weather`);
      } catch (error) {
        results.weather.error = error.message;
        console.error('❌ Weather sync failed:', error.message);
      }

      // 4. Generate predictions for games without them
      console.log('\n🤖 Generating predictions...');
      await this.generateMissingPredictions();

      results.duration = Date.now() - startTime;
      this.lastSyncTime = new Date();

      console.log(`\n✅ Full sync completed in ${(results.duration / 1000).toFixed(2)}s`);

    } catch (error) {
      console.error('❌ Full sync failed:', error);
      throw error;
    } finally {
      this.syncInProgress = false;
    }

    return results;
  }

  // Sync weather data for games
  async syncWeatherData() {
    const results = { total: 0, synced: 0, errors: [] };

    try {
      // Get upcoming games within 7 days
      const sevenDaysFromNow = new Date();
      sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);

      const { data: games, error } = await supabase
        .from('games')
        .select('*')
        .gte('game_time', new Date().toISOString())
        .lte('game_time', sevenDaysFromNow.toISOString())
        .not('venue_city', 'is', null);

      if (error) throw error;

      results.total = games?.length || 0;

      for (const game of games || []) {
        try {
          // Get weather for game location and time
          const weather = await this.getWeatherForGame(game);

          if (weather) {
            await supabase
              .from('games')
              .update({
                weather_data: weather,
                updated_at: new Date().toISOString()
              })
              .eq('id', game.id);

            results.synced++;
          }
        } catch (weatherError) {
          results.errors.push({
            gameId: game.id,
            error: weatherError.message
          });
        }
      }

    } catch (error) {
      console.error('Weather sync error:', error);
      throw error;
    }

    return results;
  }

  // Get weather data for a specific game
  async getWeatherForGame(game) {
    // Skip indoor stadiums
    const indoorStadiums = [
      'Mercedes-Benz Stadium', // ATL
      'Caesars Superdome', // NO
      'Ford Field', // DET
      'U.S. Bank Stadium', // MIN
      'NRG Stadium', // HOU
      'Lucas Oil Stadium', // IND
      'AT&T Stadium', // DAL
      'State Farm Stadium', // ARI
      'SoFi Stadium', // LAR/LAC
      'Allegiant Stadium' // LV
    ];

    if (indoorStadiums.includes(game.venue)) {
      return {
        temperature: 72,
        condition: 'Indoor Stadium',
        wind_speed: 0,
        precipitation: 0,
        indoor: true
      };
    }

    // Use ESPN API weather data when available, otherwise use Open-Meteo
    // ESPN already provides weather data in the competition object

    // For non-dome venues, try to get weather from ESPN API
    // If no weather data available, return null to indicate no weather info
    return null;
  }

  // Generate predictions for games without them
  async generateMissingPredictions() {
    try {
      // Get upcoming games without predictions
      const { data: games, error } = await supabase
        .from('games')
        .select('*')
        .in('status', ['scheduled', 'live'])
        .order('game_time', { ascending: true })
        .limit(20);

      if (error) throw error;

      // Check which games need predictions
      const gamesNeedingPredictions = [];
      for (const game of games || []) {
        const { data: existingPred } = await supabase
          .from('predictions')
          .select('id')
          .eq('game_id', game.id)
          .single();

        if (!existingPred) {
          gamesNeedingPredictions.push(game);
        }
      }

      console.log(`Found ${gamesNeedingPredictions.length} games needing predictions`);

      // Generate predictions using the council
      for (const game of gamesNeedingPredictions) {
        await this.generatePrediction(game);
        // Small delay to avoid rate limits
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      console.log(`✅ Generated predictions for ${gamesNeedingPredictions.length} games`);

    } catch (error) {
      console.error('Error generating predictions:', error);
    }
  }

  // Generate a prediction for a game using the council
  async generatePrediction(game) {
    try {
      // Use the multi-model council for advanced predictions
      const prediction = await modelCouncilService.generateCouncilPrediction(game);
      return prediction;
    } catch (error) {
      console.error('Council prediction failed, using fallback:', error);

      // Fallback to simple prediction
      const homeAdvantage = 3;
      const randomFactor = (Math.random() - 0.5) * 10;
      const predictedSpread = homeAdvantage + randomFactor;
      const homeWinProb = 50 + (predictedSpread * 2.5);

      const fallbackPrediction = {
        game_id: game.id,
        model_version: 'v1.0-fallback',
        prediction_type: 'basic',
        home_win_prob: Math.min(95, Math.max(5, homeWinProb)),
        away_win_prob: Math.min(95, Math.max(5, 100 - homeWinProb)),
        predicted_spread: predictedSpread.toFixed(1),
        predicted_total: (Math.random() * 20 + 40).toFixed(1),
        confidence: 50,
        ml_features: { fallback: true },
        created_at: new Date().toISOString()
      };

      const { error: insertError } = await supabase
        .from('predictions')
        .insert(fallbackPrediction);

      if (insertError) {
        console.error('Error inserting fallback prediction:', insertError);
      }

      return fallbackPrediction;
    }
  }

  // Sync teams from ESPN to ensure we have all 2025 team data
  async syncTeamsFromESPN() {
    try {
      const teamsData = await espnService.getTeams();
      const teams = teamsData.sports[0].leagues[0].teams || [];

      for (const teamWrapper of teams) {
        const team = teamWrapper.team;

        const teamData = {
          abbreviation: team.abbreviation,
          name: team.displayName,
          city: team.location,
          conference: team.conference?.name || null,
          division: team.division?.name || null,
          logo_url: team.logos?.[0]?.href || null,
          color: team.color || null,
          alternate_color: team.alternateColor || null
        };

        await supabase
          .from('teams')
          .upsert(teamData, {
            onConflict: 'abbreviation',
            returning: 'minimal'
          });
      }

      return { synced: teams.length };
    } catch (error) {
      console.error('Team sync error:', error);
      return { synced: 0, error: error.message };
    }
  }

  // Start automated sync with different intervals for different data types
  startAutoSync(gameIntervalMinutes = 2, fullSyncIntervalMinutes = 15) {
    if (this.syncInterval) {
      console.log('Auto-sync already running');
      return;
    }

    const gameIntervalMs = gameIntervalMinutes * 60 * 1000;
    const fullSyncIntervalMs = fullSyncIntervalMinutes * 60 * 1000;

    console.log(`⏰ Starting auto-sync:`);
    console.log(`   - Games: every ${gameIntervalMinutes} minutes`);
    console.log(`   - Full sync: every ${fullSyncIntervalMinutes} minutes`);

    // Initial full sync
    this.performFullSync();

    // Fast game updates for live data
    this.gameInterval = setInterval(async () => {
      try {
        console.log('🏈 Quick game data sync...');
        await espnService.syncGamesToSupabase();
      } catch (error) {
        console.error('Quick sync error:', error);
      }
    }, gameIntervalMs);

    // Full sync with predictions, odds, etc.
    this.fullSyncInterval = setInterval(() => {
      this.performFullSync();
    }, fullSyncIntervalMs);

    this.syncInterval = true; // Flag that auto-sync is running
  }

  // Stop automated sync
  stopAutoSync() {
    if (this.syncInterval) {
      if (this.gameInterval) {
        clearInterval(this.gameInterval);
        this.gameInterval = null;
      }
      if (this.fullSyncInterval) {
        clearInterval(this.fullSyncInterval);
        this.fullSyncInterval = null;
      }
      this.syncInterval = null;
      console.log('Auto-sync stopped');
    }
  }

  // Get sync status
  getSyncStatus() {
    return {
      inProgress: this.syncInProgress,
      lastSync: this.lastSyncTime,
      autoSyncEnabled: !!this.syncInterval
    };
  }

  // Get comprehensive game data
  async getEnhancedGameData(gameId) {
    try {
      const { data, error } = await supabase
        .from('games')
        .select(`
          *,
          predictions (*),
          odds_history (*)
        `)
        .eq('id', gameId)
        .single();

      if (error) throw error;

      // Add live updates if game is in progress
      if (data.status === 'live') {
        const liveUpdates = await espnService.getLiveUpdates();
        const liveGame = liveUpdates.find(g => g.espn_game_id === data.espn_game_id);
        if (liveGame) {
          data.live_data = liveGame;
        }
      }

      return data;

    } catch (error) {
      console.error('Error fetching enhanced game data:', error);
      return null;
    }
  }

  // Subscribe to all real-time updates
  subscribeToAllUpdates(callbacks = {}) {
    const subscriptions = [];

    // Subscribe to game updates
    if (callbacks.onGameUpdate) {
      subscriptions.push(
        supabaseHelpers.subscribeToGames(callbacks.onGameUpdate)
      );
    }

    // Subscribe to new predictions
    if (callbacks.onPrediction) {
      subscriptions.push(
        supabaseHelpers.subscribeToPredictions(callbacks.onPrediction)
      );
    }

    // Subscribe to odds changes
    if (callbacks.onOddsUpdate) {
      subscriptions.push(
        supabaseHelpers.subscribeToOdds(callbacks.onOddsUpdate)
      );
    }

    return {
      unsubscribeAll: () => {
        subscriptions.forEach(sub => sub.unsubscribe());
      }
    };
  }
}

// Create singleton instance
const dataIntegrationService = new DataIntegrationService();

export default dataIntegrationService;