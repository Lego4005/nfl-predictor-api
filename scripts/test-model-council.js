#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';

async function testModelCouncilSchema() {
  console.log('🎯 Testing Model Council schema compatibility...');

  // Get a real game from database
  const { data: games, error } = await supabase
    .from('games')
    .select('*')
    .eq('season', 2025)
    .limit(1);

  if (error) {
    console.error('Error fetching games:', error);
    return;
  }

  if (!games || games.length === 0) {
    console.log('❌ No games found in database');
    return;
  }

  const game = games[0];
  console.log(`🏈 Testing with game: ${game.away_team} @ ${game.home_team}`);
  console.log(`   Game ID: ${game.id}`);

  // Test prediction schema without full council service
  const testPrediction = {
    game_id: game.id,
    model_version: 'v3.0-council-test',
    prediction_type: 'multi-model-council',
    home_win_prob: 55.0,
    away_win_prob: 45.0,
    predicted_spread: -3.0,
    predicted_total: 45,
    confidence: 75,
    ml_features: {
      council_size: 12,
      disagreement_index: 15.5,
      model_weights: { 'elo': 0.2, 'claude-4-sonnet': 0.3, 'gemini-2.5-flash': 0.25 },
      individual_votes: [
        { modelId: 'elo', modelName: 'ELO Rating', homeWinProb: 60, spread: -4 },
        { modelId: 'claude-4-sonnet', modelName: 'Claude 4 Sonnet', homeWinProb: 52, spread: -2 }
      ],
      consensus: { homeWinProb: 55.0, spread: -3.0 },
      explanation: 'Council prediction based on 12 models with 75% confidence'
    },
    created_at: new Date().toISOString()
  };

  try {
    // Delete any existing prediction for this game first
    await supabase
      .from('predictions')
      .delete()
      .eq('game_id', game.id);

    // Test insert
    console.log('🧪 Testing prediction insert...');
    const { error: insertError } = await supabase
      .from('predictions')
      .insert(testPrediction);

    if (insertError) {
      console.error('❌ Insert failed:', insertError.message);
      return;
    }

    console.log('✅ Prediction insert successful!');

    // Test retrieval
    const { data: storedPrediction, error: fetchError } = await supabase
      .from('predictions')
      .select('*')
      .eq('game_id', game.id)
      .single();

    if (fetchError) {
      console.log('❌ Error fetching stored prediction:', fetchError.message);
    } else {
      console.log('✅ Prediction successfully retrieved from database');
      console.log('📊 Results:');
      console.log(`   Home Win Prob: ${storedPrediction.home_win_prob}%`);
      console.log(`   Predicted Spread: ${storedPrediction.predicted_spread}`);
      console.log(`   Confidence: ${storedPrediction.confidence}%`);
      console.log('🔍 Council size:', storedPrediction.ml_features?.council_size);
      console.log('🤝 Model agreement index:', 100 - (storedPrediction.ml_features?.disagreement_index || 0));
      console.log('🎯 Schema compatibility: ✅ WORKING');
    }

  } catch (error) {
    console.error('❌ Schema test failed:', error.message);
    console.error('Full error:', error);
  }

  process.exit(0);
}

testModelCouncilSchema().then(() => {
  console.log('🎉 Model Council schema test completed!');
}).catch(error => {
  console.error('💥 Model Council schema test failed:', error);
  process.exit(1);
});