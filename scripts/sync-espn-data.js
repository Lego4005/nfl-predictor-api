#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';

console.log('🔄 Syncing 2025 ESPN NFL Data to Supabase...\n');

async function syncESPNData() {
  const startTime = Date.now();

  try {
    // Fetch ESPN scoreboard data
    console.log('📡 Fetching ESPN scoreboard data...');
    const response = await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard');

    if (!response.ok) {
      throw new Error(`ESPN API error: ${response.status}`);
    }

    const data = await response.json();
    const events = data.events || [];

    console.log(`Found ${events.length} NFL games\n`);

    const results = {
      total: events.length,
      synced: 0,
      errors: []
    };

    // Process each game
    for (const event of events) {
      try {
        const competition = event.competitions[0];
        const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
        const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

        // Map ESPN status
        function mapESPNStatus(espnStatus) {
          const statusMap = {
            'STATUS_SCHEDULED': 'scheduled',
            'STATUS_IN_PROGRESS': 'live',
            'STATUS_FINAL': 'final',
            'STATUS_POSTPONED': 'postponed',
            'STATUS_CANCELED': 'canceled',
            'STATUS_HALFTIME': 'live',
            'STATUS_END_PERIOD': 'live'
          };
          return statusMap[espnStatus] || 'scheduled';
        }

        // Build game data object (matching actual DB schema)
        const gameData = {
          espn_game_id: event.id,
          home_team: homeTeam.team.abbreviation,
          away_team: awayTeam.team.abbreviation,
          home_score: parseInt(homeTeam.score) || 0,
          away_score: parseInt(awayTeam.score) || 0,
          game_time: new Date(event.date).toISOString(),
          week: event.week?.number || null,
          season: event.season?.year || new Date().getFullYear(),
          season_type: event.season?.type || 2,
          status: mapESPNStatus(competition.status.type.name),
          quarter: competition.status?.period || null,
          time_remaining: competition.status?.displayClock || null,
          venue: competition.venue?.fullName || null,
          venue_city: competition.venue?.address?.city || null,
          venue_state: competition.venue?.address?.state || null,
          weather_data: competition.weather ? {
            temperature: competition.weather.temperature,
            condition: competition.weather.displayValue,
            wind: competition.weather.wind
          } : null,
          odds_data: competition.odds && competition.odds.length > 0 ? {
            spread: competition.odds[0]?.details,
            overUnder: competition.odds[0]?.overUnder
          } : null,
          updated_at: new Date().toISOString()
        };

        console.log(`⚡ ${gameData.away_team} @ ${gameData.home_team} (${gameData.status}) - Week ${gameData.week}`);

        // Upsert to Supabase
        const { data: upsertData, error } = await supabase
          .from('games')
          .upsert(gameData, {
            onConflict: 'espn_game_id'
          });

        if (error) {
          console.log(`  ❌ Error: ${error.message}`);
          results.errors.push({ gameId: event.id, error: error.message });
        } else {
          console.log(`  ✅ Synced successfully`);
          results.synced++;
        }

      } catch (gameError) {
        console.log(`  ❌ Game error: ${gameError.message}`);
        results.errors.push({
          gameId: event.id,
          error: gameError.message
        });
      }
    }

    const duration = Date.now() - startTime;

    console.log('\n📊 Sync Results:');
    console.log('=' .repeat(40));
    console.log(`✅ Successfully synced: ${results.synced}/${results.total} games`);
    console.log(`❌ Errors: ${results.errors.length}`);
    console.log(`⏱️ Duration: ${(duration / 1000).toFixed(2)}s`);

    if (results.errors.length > 0) {
      console.log('\n❌ Errors:');
      results.errors.forEach(err => {
        console.log(`  - Game ${err.gameId}: ${err.error}`);
      });
    }

    // Verify data in database
    console.log('\n🔍 Verifying stored data...');
    const { data: storedGames, error: queryError } = await supabase
      .from('games')
      .select('id, home_team, away_team, status, season')
      .eq('season', 2025)
      .order('game_time', { ascending: true })
      .limit(10);

    if (queryError) {
      console.log('❌ Error verifying data:', queryError.message);
    } else {
      console.log(`✅ Found ${storedGames.length} games in database for 2025 season`);
      storedGames.forEach(game => {
        console.log(`  - ${game.away_team} @ ${game.home_team} (${game.status})`);
      });
    }

    return results;

  } catch (error) {
    console.error('❌ Sync failed:', error);
    throw error;
  }
}

// Run the sync
syncESPNData().then(() => {
  console.log('\n🎉 ESPN sync completed successfully!');
  process.exit(0);
}).catch(error => {
  console.error('\n💥 ESPN sync failed:', error);
  process.exit(1);
});