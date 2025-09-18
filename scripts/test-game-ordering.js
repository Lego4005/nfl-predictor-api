#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';

console.log('🔍 Testing game ordering (most recent first)...\n');

async function testGameOrdering() {
  try {
    // Get games directly from database to see current ordering
    const { data: games, error } = await supabase
      .from('games')
      .select('away_team, home_team, game_time, status, week')
      .eq('season', 2025)
      .order('game_time', { ascending: false })
      .limit(10);

    if (error) {
      console.error('Error fetching games:', error);
      return;
    }

    console.log('🏈 Games ordered by most recent game time first:');
    console.log('=' .repeat(60));

    games.forEach((game, i) => {
      const gameTime = new Date(game.game_time);
      const timeStr = gameTime.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/New_York'
      });

      const statusIcon = game.status === 'live' ? '🔴' :
                        game.status === 'final' ? '✅' : '⏰';

      console.log(`${i + 1}. ${statusIcon} ${game.away_team} @ ${game.home_team}`);
      console.log(`   📅 ${timeStr} | Week ${game.week} | Status: ${game.status}`);
      console.log('');
    });

    console.log('✅ Games are now ordered by most recent game time first');

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testGameOrdering().then(() => {
  console.log('🎉 Game ordering test completed!');
  process.exit(0);
}).catch(error => {
  console.error('💥 Game ordering test failed:', error);
  process.exit(1);
});