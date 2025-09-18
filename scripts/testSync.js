import espnService from '../src/services/espnService.js';

async function testSync() {
  console.log('Starting ESPN to Supabase sync test...');

  try {
    // Test ESPN API first
    console.log('\n1. Testing ESPN API connection...');
    const scoreboard = await espnService.getScoreboard();
    console.log(`✅ ESPN API connected! Found ${scoreboard.events?.length || 0} games`);

    // Now sync to Supabase
    console.log('\n2. Syncing games to Supabase...');
    const result = await espnService.syncGamesToSupabase();

    console.log('\n✅ Sync Complete!');
    console.log(`Total games: ${result.total}`);
    console.log(`Successfully synced: ${result.synced}`);
    console.log(`Errors: ${result.errors.length}`);

    if (result.errors.length > 0) {
      console.log('\n⚠️ Errors encountered:');
      result.errors.forEach(err => {
        console.log(`  - Game ${err.gameId}: ${err.error}`);
      });
    }

    // Test live updates
    console.log('\n3. Checking for live games...');
    const liveGames = await espnService.getLiveUpdates();
    console.log(`Found ${liveGames.length} live games`);

    if (liveGames.length > 0) {
      console.log('\nLive games:');
      liveGames.forEach(game => {
        console.log(`  - ${game.away_team} @ ${game.home_team}: ${game.away_score}-${game.home_score} (Q${game.quarter} ${game.time_remaining})`);
      });
    }

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testSync();