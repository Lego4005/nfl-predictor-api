#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';

console.log('🔍 Testing predictions table schema...');

async function testPredictionsSchema() {
  try {
    // Get a real game ID first
    const { data: games, error: gamesError } = await supabase
      .from('games')
      .select('id, away_team, home_team')
      .limit(1);

    if (gamesError || !games.length) {
      console.error('No games found:', gamesError);
      return;
    }

    const game = games[0];
    console.log(`Using game: ${game.away_team} @ ${game.home_team} - ID: ${game.id}`);

    // Test minimal prediction
    const testData = {
      game_id: game.id,
      model_version: 'test-schema',
      prediction_type: 'schema-test',
      home_win_prob: 60.0,
      away_win_prob: 40.0,
      predicted_spread: -3.5,
      predicted_total: 47,
      confidence: 75
    };

    const { data, error } = await supabase
      .from('predictions')
      .insert(testData)
      .select();

    if (error) {
      console.error('❌ Error inserting basic prediction:', error.message);
      console.log('This tells us which columns are missing or invalid');
    } else {
      console.log('✅ Basic prediction successful!');
      console.log('Available columns:', Object.keys(data[0]));

      // Clean up test data
      await supabase
        .from('predictions')
        .delete()
        .eq('id', data[0].id);

      console.log('🧹 Test data cleaned up');
    }

  } catch (error) {
    console.error('❌ Schema test failed:', error);
  }
}

testPredictionsSchema().then(() => {
  console.log('\n🎉 Schema test completed!');
  process.exit(0);
}).catch(error => {
  console.error('\n💥 Schema test failed:', error);
  process.exit(1);
});