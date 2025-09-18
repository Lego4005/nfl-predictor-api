#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';
import modelCouncilService from '../src/services/modelCouncilService.js';

console.log('🤖 Testing Model Council Prediction System...\n');

async function testModelCouncil() {
  try {
    // Get some games to test predictions on
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
      console.log('❌ No games found for predictions');
      return;
    }

    console.log(`Found ${games.length} games for testing:\n`);

    // Test predictions for each game
    for (const game of games) {
      console.log(`🏈 Testing prediction for: ${game.away_team} @ ${game.home_team}`);
      console.log(`   Status: ${game.status} | Week: ${game.week} | Time: ${new Date(game.game_time).toLocaleString()}`);

      try {
        // Check if prediction already exists
        const { data: existingPred } = await supabase
          .from('predictions')
          .select('*')
          .eq('game_id', game.id)
          .single();

        if (existingPred) {
          console.log(`   ✅ Prediction exists: ${existingPred.home_win_prob.toFixed(1)}% home win`);
          console.log(`      Spread: ${existingPred.predicted_spread} | Total: ${existingPred.predicted_total}`);
          console.log(`      Confidence: ${existingPred.confidence}% | Model: ${existingPred.model_version}\n`);
        } else {
          console.log(`   🎯 Generating new council prediction...`);

          const startTime = Date.now();
          const prediction = await modelCouncilService.generateCouncilPrediction(game);
          const duration = Date.now() - startTime;

          console.log(`   ✅ Council prediction complete in ${(duration/1000).toFixed(2)}s:`);
          console.log(`      Home Win: ${prediction.home_win_prob}%`);
          console.log(`      Away Win: ${prediction.away_win_prob}%`);
          console.log(`      Spread: ${prediction.predicted_spread}`);
          console.log(`      Total: ${prediction.predicted_total}`);
          console.log(`      Confidence: ${prediction.confidence}%`);

          if (prediction.model_scores?.individual_votes) {
            console.log(`      Council Size: ${prediction.model_scores.individual_votes.length} models`);
            const topVotes = prediction.model_scores.individual_votes
              .slice(0, 3)
              .map(v => `${v.modelName}: ${v.homeWinProb.toFixed(1)}%`)
              .join(', ');
            console.log(`      Top Votes: ${topVotes}`);
          }
          console.log('');
        }

      } catch (predError) {
        console.error(`   ❌ Error generating prediction:`, predError.message);
        console.log('');
      }
    }

    // Show council performance stats
    console.log('📈 Model Council Performance:');
    const bestModels = modelCouncilService.getBestModels(5);
    if (bestModels.length > 0) {
      bestModels.forEach((model, i) => {
        console.log(`   ${i + 1}. ${model.modelName}: ${model.accuracy.toFixed(1)}% (${model.predictions} predictions, ${(model.weight * 100).toFixed(1)}% weight)`);
      });
    } else {
      console.log('   No performance data available yet');
    }

  } catch (error) {
    console.error('❌ Council test failed:', error);
  }
}

// Run the test
testModelCouncil().then(() => {
  console.log('\n🎉 Model council test completed!');
  process.exit(0);
}).catch(error => {
  console.error('\n💥 Model council test failed:', error);
  process.exit(1);
});