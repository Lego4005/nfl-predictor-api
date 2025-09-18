import { supabase } from './supabaseClientNode.js';
import espnApiService from './espnApiService.js';

/**
 * Scheduler Service for Automated NFL Data Updates
 *
 * Handles automatic synchronization of:
 * - Game data from ESPN API
 * - Live scores and status updates
 * - Future schedule updates
 */
class SchedulerService {
  constructor() {
    this.intervals = {};
    this.isRunning = false;
  }

  /**
   * Start the scheduler with different intervals for different data types
   */
  start() {
    if (this.isRunning) {
      console.log('⚠️ Scheduler already running');
      return;
    }

    console.log('🚀 Starting NFL Data Scheduler...');
    this.isRunning = true;

    // Live games: Update every 30 seconds during game time
    this.intervals.liveGames = setInterval(() => {
      this.syncLiveGames().catch(console.error);
    }, 30 * 1000);

    // All games: Update every 5 minutes for scores and status
    this.intervals.allGames = setInterval(() => {
      this.syncAllGames().catch(console.error);
    }, 5 * 60 * 1000);

    // Schedule: Update every hour for new games and time changes
    this.intervals.schedule = setInterval(() => {
      this.syncSchedule().catch(console.error);
    }, 60 * 60 * 1000);

    // Daily cleanup: Once per day at 6 AM ET
    this.intervals.cleanup = setInterval(() => {
      this.dailyCleanup().catch(console.error);
    }, 24 * 60 * 60 * 1000);

    console.log('✅ Scheduler started with intervals:');
    console.log('   📺 Live games: every 30 seconds');
    console.log('   🏈 All games: every 5 minutes');
    console.log('   📅 Schedule: every hour');
    console.log('   🧹 Cleanup: daily at 6 AM');

    // Run initial sync
    this.syncAllGames().catch(console.error);
  }

  /**
   * Stop all scheduled intervals
   */
  stop() {
    if (!this.isRunning) {
      console.log('⚠️ Scheduler not running');
      return;
    }

    console.log('🛑 Stopping NFL Data Scheduler...');

    Object.values(this.intervals).forEach(interval => {
      clearInterval(interval);
    });

    this.intervals = {};
    this.isRunning = false;

    console.log('✅ Scheduler stopped');
  }

  /**
   * Sync only live games (fast, frequent updates)
   */
  async syncLiveGames() {
    try {
      console.log('📺 Syncing live games...');

      // Get current live games from ESPN
      const espnResult = await espnApiService.getCurrentGames();
      if (!espnResult.success || !espnResult.games) return;

      const liveGames = espnResult.games.filter(game => game.is_live);

      if (liveGames.length === 0) {
        console.log('   No live games currently');
        return;
      }

      console.log(`   Found ${liveGames.length} live games`);

      // Update each live game
      for (const game of liveGames) {
        await this.updateGameInDatabase(game);
      }

      console.log(`✅ Live games sync completed`);

    } catch (error) {
      console.error('❌ Live games sync failed:', error);
    }
  }

  /**
   * Sync all games (comprehensive update)
   */
  async syncAllGames() {
    try {
      console.log('🏈 Syncing all games...');

      const espnResult = await espnApiService.getCurrentGames();
      if (!espnResult.success || !espnResult.games) {
        console.log('   No games available from ESPN');
        return;
      }

      console.log(`   Processing ${espnResult.games.length} games`);

      let updated = 0;
      let errors = 0;
      let predictionsGenerated = 0;

      // Process all games
      for (const game of espnResult.games) {
        try {
          await this.updateGameInDatabase(game);
          updated++;

          // Auto-generate predictions for scheduled games without predictions
          if (game.status === 'scheduled') {
            const { data: existingPrediction } = await supabase
              .from('predictions')
              .select('id')
              .eq('game_id', game.id)
              .single();

            if (!existingPrediction) {
              console.log(`   🤖 Generating AI prediction for ${game.away_team} @ ${game.home_team}`);
              try {
                // Dynamic import to avoid circular dependency
                const { default: modelCouncilService } = await import('./modelCouncilService.js');
                await modelCouncilService.generateCouncilPrediction(game);
                predictionsGenerated++;
              } catch (predError) {
                console.error(`   Failed to generate prediction:`, predError.message);
              }
            }
          }
        } catch (error) {
          console.error(`   Error updating game ${game.espn_game_id}:`, error.message);
          errors++;
        }
      }

      console.log(`✅ All games sync completed: ${updated} updated, ${predictionsGenerated} predictions generated, ${errors} errors`);

    } catch (error) {
      console.error('❌ All games sync failed:', error);
    }
  }

  /**
   * Sync schedule (new games, time changes)
   */
  async syncSchedule() {
    try {
      console.log('📅 Syncing schedule updates...');

      // Get full season schedule from ESPN
      const scheduleResult = await espnApiService.getSeasonSchedule();
      if (!scheduleResult.success) {
        console.log('   Schedule sync skipped - ESPN unavailable');
        return;
      }

      // Process new games or schedule changes
      let newGames = 0;
      let updatedGames = 0;

      for (const game of scheduleResult.games || []) {
        const { data: existingGame } = await supabase
          .from('games')
          .select('id, game_time, status')
          .eq('espn_game_id', game.espn_game_id)
          .single();

        if (!existingGame) {
          // New game
          await this.insertGameInDatabase(game);
          newGames++;
        } else if (existingGame.game_time !== game.game_time || existingGame.status !== game.status) {
          // Updated schedule
          await this.updateGameInDatabase(game);
          updatedGames++;
        }
      }

      console.log(`✅ Schedule sync completed: ${newGames} new, ${updatedGames} updated`);

    } catch (error) {
      console.error('❌ Schedule sync failed:', error);
    }
  }

  /**
   * Daily cleanup and maintenance
   */
  async dailyCleanup() {
    try {
      console.log('🧹 Running daily cleanup...');

      // Clean up old predictions (keep last 30 days)
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

      const { error: cleanupError } = await supabase
        .from('predictions')
        .delete()
        .lt('created_at', thirtyDaysAgo.toISOString());

      if (cleanupError) {
        console.error('   Cleanup error:', cleanupError);
      } else {
        console.log('   ✅ Old predictions cleaned up');
      }

      // Update team ratings based on recent performance
      await this.updateTeamRatings();

      // Log system health
      await this.logSystemHealth();

      console.log('✅ Daily cleanup completed');

    } catch (error) {
      console.error('❌ Daily cleanup failed:', error);
    }
  }

  /**
   * Update a single game in the database
   */
  async updateGameInDatabase(espnGame) {
    // Build game data object (matching actual DB schema)
    const gameData = {
      espn_game_id: espnGame.espn_game_id || espnGame.id,
      home_team: espnGame.home_team,
      away_team: espnGame.away_team,
      home_score: espnGame.home_score || 0,
      away_score: espnGame.away_score || 0,
      game_time: new Date(espnGame.game_time).toISOString(),
      week: espnGame.week,
      season: espnGame.season || 2025,
      status: espnGame.status,
      status_detail: espnGame.status_detail,
      is_live: espnGame.is_live || false,
      venue: espnGame.venue || null,
      updated_at: new Date().toISOString()
    };

    // Update or insert
    const { error } = await supabase
      .from('games')
      .upsert(gameData, {
        onConflict: 'espn_game_id',
        ignoreDuplicates: false
      });

    if (error) {
      throw error;
    }
  }

  /**
   * Insert a new game in the database
   */
  async insertGameInDatabase(espnGame) {
    const gameData = {
      espn_game_id: espnGame.espn_game_id || espnGame.id,
      home_team: espnGame.home_team,
      away_team: espnGame.away_team,
      home_score: 0,
      away_score: 0,
      game_time: new Date(espnGame.game_time).toISOString(),
      week: espnGame.week,
      season: espnGame.season || 2025,
      status: espnGame.status || 'scheduled',
      status_detail: espnGame.status_detail || 'Scheduled',
      is_live: false,
      venue: espnGame.venue || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const { error } = await supabase
      .from('games')
      .insert(gameData);

    if (error) {
      throw error;
    }
  }

  /**
   * Update team ratings based on recent performance
   */
  async updateTeamRatings() {
    try {
      // Get recent completed games
      const { data: recentGames, error } = await supabase
        .from('games')
        .select('*')
        .eq('status', 'final')
        .gte('game_time', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString())
        .order('game_time', { ascending: false });

      if (error || !recentGames) return;

      // Calculate rating adjustments (simplified ELO)
      const ratingUpdates = {};

      for (const game of recentGames) {
        const homeWon = game.home_score > game.away_score;
        const margin = Math.abs(game.home_score - game.away_score);

        // Adjust ratings
        const kFactor = 20;
        const adjustment = kFactor * (margin > 14 ? 1.5 : 1.0);

        if (!ratingUpdates[game.home_team]) ratingUpdates[game.home_team] = 0;
        if (!ratingUpdates[game.away_team]) ratingUpdates[game.away_team] = 0;

        if (homeWon) {
          ratingUpdates[game.home_team] += adjustment;
          ratingUpdates[game.away_team] -= adjustment;
        } else {
          ratingUpdates[game.away_team] += adjustment;
          ratingUpdates[game.home_team] -= adjustment;
        }
      }

      console.log('   📊 Team rating updates:', Object.keys(ratingUpdates).length, 'teams');

    } catch (error) {
      console.error('   Rating update error:', error);
    }
  }

  /**
   * Log system health metrics
   */
  async logSystemHealth() {
    try {
      const healthMetrics = {
        timestamp: new Date().toISOString(),
        scheduler_running: this.isRunning,
        total_games: 0,
        live_games: 0,
        recent_predictions: 0
      };

      // Count games
      const { data: allGames } = await supabase
        .from('games')
        .select('status', { count: 'exact' })
        .eq('season', 2025);

      healthMetrics.total_games = allGames?.length || 0;
      healthMetrics.live_games = allGames?.filter(g => g.status === 'live').length || 0;

      // Count recent predictions
      const { data: predictions } = await supabase
        .from('predictions')
        .select('id', { count: 'exact' })
        .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

      healthMetrics.recent_predictions = predictions?.length || 0;

      console.log('   🏥 System health:', healthMetrics);

    } catch (error) {
      console.error('   Health logging error:', error);
    }
  }

  /**
   * Get scheduler status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      intervals: Object.keys(this.intervals),
      uptime: this.isRunning ? 'Active' : 'Stopped'
    };
  }

  /**
   * Manual sync trigger
   */
  async manualSync() {
    console.log('🔄 Manual sync triggered...');
    await this.syncAllGames();
    console.log('✅ Manual sync completed');
  }
}

// Create singleton instance
const schedulerService = new SchedulerService();

export default schedulerService;