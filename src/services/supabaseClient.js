import { createClient } from '@supabase/supabase-js';

// Get environment variables - use import.meta.env for Vite (browser)
// Check if we're in browser or Node.js environment
const isBrowser = typeof window !== 'undefined';
const supabaseUrl = isBrowser
  ? (import.meta?.env?.VITE_SUPABASE_URL || 'https://nypbqzzfmckfadexltzk.supabase.co')
  : (process.env.VITE_SUPABASE_URL || 'https://nypbqzzfmckfadexltzk.supabase.co');
const supabaseAnonKey = isBrowser
  ? (import.meta?.env?.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im55cGJxenpmtWNrZmFkZXhsdHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYyMzA5MjcsImV4cCI6MjA1MTgwNjkyN30.7Bf7g7-9mDbTMBg8o-Y7Yqb-ovvQrJkzkNnHlKUWkMQ')
  : (process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im55cGJxenpmtWNrZmFkZXhsdHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYyMzA5MjcsImV4cCI6MjA1MTgwNjkyN30.7Bf7g7-9mDbTMBg8o-Y7Yqb-ovvQrJkzkNnHlKUWkMQ');

// Create Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
});

// Cache for ESPN API data
let gamesCache = null;
let lastFetch = null;
const CACHE_DURATION = 30000; // 30 seconds for live games

// Helper functions for common operations
export const supabaseHelpers = {
  // Get current week's games with caching and consistent ordering
  async getCurrentGames() {
    try {
      // Check cache first to prevent constant refreshing
      const now = Date.now();
      if (gamesCache && lastFetch && (now - lastFetch) < CACHE_DURATION) {
        return gamesCache;
      }

      // Use Expert API as primary data source since Supabase has DNS issues
      try {
        console.log('🔄 Fetching games from Expert API...');
        const response = await fetch('http://localhost:8003/api/predictions/recent');

        if (response.ok) {
          const expertData = await response.json();
          console.log(`✅ Found ${expertData?.length || 0} games from Expert API`);

          if (expertData && expertData.length > 0) {
            // Transform expert API data to expected format
            const realGames = expertData.map(game => ({
              id: game.game_id,
              home_team: game.home_team,
              away_team: game.away_team,
              home_score: 0, // Expert API doesn't have scores yet
              away_score: 0,
              game_time: game.date,
              status: game.status || 'scheduled',
              status_detail: game.status === 'completed' ? 'Final' : 'Scheduled',
              is_live: game.status === 'live',
              current_period: null,
              time_remaining: null
            }));

            gamesCache = realGames;
            lastFetch = now;
            return realGames;
          }
        } else {
          console.warn('Expert API error:', response.status);
        }
      } catch (error) {
        console.warn('Expert API connection error:', error);
      }

      // No real data available, return empty array
      console.warn('No games available from database');
      return [];

    } catch (error) {
      console.warn('All data sources failed:', error);
      return gamesCache || []; // Return cached data if available
    }
  },

  // Helper method to map ESPN status
  mapESPNStatus(status) {
    const statusType = status?.type?.name;
    switch (statusType) {
      case 'STATUS_SCHEDULED': return 'scheduled';
      case 'STATUS_IN_PROGRESS': return 'live';
      case 'STATUS_FINAL': return 'final';
      default: return 'unknown';
    }
  },

  // Get live games
  async getLiveGames() {
    const { data, error } = await supabase
      .from('games')
      .select('*')
      .eq('status', 'live')
      .order('game_time', { ascending: true });

    if (error) throw error;
    return data;
  },

  // Get game with predictions
  async getGameWithPredictions(gameId) {
    const { data, error } = await supabase
      .from('games')
      .select(`
        *,
        predictions (*)
      `)
      .eq('id', gameId)
      .single();

    if (error) throw error;
    return data;
  },

  // Get latest odds for a game
  async getGameOdds(gameId) {
    const { data, error } = await supabase
      .from('odds_history')
      .select('*')
      .eq('game_id', gameId)
      .order('recorded_at', { ascending: false })
      .limit(10);

    if (error) throw error;
    return data;
  },

  // Subscribe to live game updates
  subscribeToGames(callback) {
    return supabase
      .channel('games-channel')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'games' },
        callback
      )
      .subscribe();
  },

  // Subscribe to new predictions
  subscribeToPredictions(callback) {
    return supabase
      .channel('predictions-channel')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'predictions' },
        callback
      )
      .subscribe();
  },

  // Subscribe to odds changes
  subscribeToOdds(callback) {
    return supabase
      .channel('odds-channel')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'odds_history' },
        callback
      )
      .subscribe();
  },

  // User functions (if authenticated)
  async saveUserPick(pick) {
    const { data, error } = await supabase
      .from('user_picks')
      .insert([pick])
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async getUserStats(userId) {
    const { data, error } = await supabase
      .from('user_stats')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error) throw error;
    return data;
  },

  // Get news sentiment for teams
  async getTeamSentiment(teams) {
    const { data, error } = await supabase
      .from('news_sentiment')
      .select('*')
      .contains('teams_mentioned', teams)
      .order('published_at', { ascending: false })
      .limit(10);

    if (error) throw error;
    return data;
  },

  // Get model performance stats
  async getModelPerformance() {
    const { data, error } = await supabase
      .from('model_performance')
      .select('*')
      .order('evaluation_date', { ascending: false })
      .limit(30);

    if (error) throw error;
    return data;
  }
};

export default supabase;