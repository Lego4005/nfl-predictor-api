#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';

console.log('🤖 Testing Model Council System (Simplified)...\n');

async function testModelCouncilBasic() {
  try {
    // Get some games from the database
    console.log('📊 Fetching games from database...');
    const { data: games, error } = await supabase
      .from('games')
      .select('*')
      .in('status', ['scheduled', 'live'])
      .order('game_time', { ascending: true })
      .limit(3);

    if (error) {
      console.error('Error fetching games:', error);
      return;
    }

    if (!games || games.length === 0) {
      console.log('❌ No games found');
      return;
    }

    console.log(`Found ${games.length} games:\n`);
    games.forEach((game, i) => {
      console.log(`${i + 1}. ${game.away_team} @ ${game.home_team}`);
      console.log(`   Status: ${game.status} | Week: ${game.week} | ${new Date(game.game_time).toLocaleString()}`);
    });

    console.log('\n🔍 Checking for existing predictions...');

    // Check if any predictions exist
    const { data: predictions, error: predError } = await supabase
      .from('predictions')
      .select('*')
      .in('game_id', games.map(g => g.id));

    if (predError) {
      console.error('Error fetching predictions:', predError);
      return;
    }

    console.log(`Found ${predictions?.length || 0} existing predictions\n`);

    if (predictions && predictions.length > 0) {
      predictions.forEach(pred => {
        const game = games.find(g => g.id === pred.game_id);
        console.log(`✅ ${game.away_team} @ ${game.home_team}:`);
        console.log(`   Home Win: ${pred.home_win_prob}% | Away Win: ${pred.away_win_prob}%`);
        console.log(`   Spread: ${pred.predicted_spread} | Total: ${pred.predicted_total}`);
        console.log(`   Model: ${pred.model_version} | Confidence: ${pred.confidence}%`);

        if (pred.model_scores?.individual_votes) {
          console.log(`   Council Size: ${pred.model_scores.individual_votes.length} models`);
        }
        console.log('');
      });
    }

    // Test creating a simple prediction manually
    console.log('🧪 Testing simple prediction insert...');

    const testGame = games[0];
    const testPrediction = {
      game_id: testGame.id,
      model_version: 'v3.0-test',
      prediction_type: 'test',
      home_win_prob: 55.5,
      away_win_prob: 44.5,
      predicted_spread: -3.0,
      predicted_total: 47,
      confidence: 75,
      ml_features: {
        test: true,
        game_importance: 5,
        team_ratings: {
          home: 1500,
          away: 1450
        }
      },
      model_scores: {
        test: 'This is a test prediction',
        consensus: {
          homeWinProb: 55.5,
          spread: -3.0,
          total: 47
        }
      },
      created_at: new Date().toISOString()
    };

    // Try upsert
    const { data: insertData, error: insertError } = await supabase
      .from('predictions')
      .upsert(testPrediction, {
        onConflict: 'game_id'
      })
      .select()
      .single();

    if (insertError) {
      console.error('❌ Error inserting test prediction:', insertError);
    } else {
      console.log('✅ Test prediction inserted successfully!');
      console.log(`   ID: ${insertData.id} | Game: ${testGame.away_team} @ ${testGame.home_team}`);
      console.log(`   Prediction: ${insertData.home_win_prob}% home win`);
    }

    // Check environment variables for OpenRouter
    console.log('\n🔑 Checking environment variables...');
    const openRouterKey = process.env.VITE_OPENROUTER_API_KEY;
    console.log(`OpenRouter API Key: ${openRouterKey ? '✅ Present' : '❌ Missing'}`);

    if (openRouterKey) {
      console.log(`   Key length: ${openRouterKey.length} characters`);
      console.log(`   Key preview: ${openRouterKey.substring(0, 10)}...`);
    } else {
      console.log('   The model council will use statistical models only without AI predictions');
    }

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testModelCouncilBasic().then(() => {
  console.log('\n🎉 Basic model council test completed!');
  process.exit(0);
}).catch(error => {
  console.error('\n💥 Basic model council test failed:', error);
  process.exit(1);
});