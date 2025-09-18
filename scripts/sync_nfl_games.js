#!/usr/bin/env node

/**
 * NFL Game Sync Script
 *
 * This script fetches current NFL games from ESPN API and syncs them to Supabase database.
 *
 * Features:
 * - Fetches current week NFL games from ESPN API
 * - Syncs to Supabase database (https://vaypgzvivahnfegnlinn.supabase.co)
 * - Handles both inserts and updates properly
 * - Maps ESPN status to database format
 * - Shows detailed sync results
 * - Verifies data after sync
 *
 * Usage:
 *   node scripts/sync_nfl_games.js
 *
 * Database columns supported:
 * - espn_game_id, home_team, away_team, home_score, away_score
 * - game_time, week, season, venue, status, updated_at
 *
 * Author: Claude Code
 * Date: September 2025
 */

import { createClient } from '@supabase/supabase-js';
import fetch from 'node-fetch';

// Supabase Configuration - Using the correct URL and key from .env
const SUPABASE_URL = 'https://vaypgzvivahnfegnlinn.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws';

// Create Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  },
});

console.log('🏈 NFL Game Sync Script - Week 2/3 September 2025\n');
console.log(`📡 Connecting to Supabase: ${SUPABASE_URL}`);
console.log('🔄 Fetching current NFL games from ESPN API...\n');

// Helper function to get current NFL week
function getCurrentNFLWeek() {
  const currentDate = new Date('2025-09-17'); // September 17, 2025
  const seasonStart = new Date('2025-09-05'); // Approximate NFL season start
  const daysDiff = Math.floor((currentDate - seasonStart) / (1000 * 60 * 60 * 24));
  return Math.max(1, Math.min(18, Math.floor(daysDiff / 7) + 1));
}

// Map ESPN status to our database format
function mapESPNStatus(espnStatus) {
  const statusMap = {
    'STATUS_SCHEDULED': 'scheduled',
    'STATUS_IN_PROGRESS': 'live',
    'STATUS_FINAL': 'final',
    'STATUS_POSTPONED': 'postponed',
    'STATUS_CANCELED': 'canceled',
    'STATUS_HALFTIME': 'live',
    'STATUS_END_PERIOD': 'live',
    'STATUS_DELAYED': 'delayed'
  };
  return statusMap[espnStatus] || 'scheduled';
}

// Get current week number
const currentWeek = getCurrentNFLWeek();
console.log(`📅 Current NFL Week: ${currentWeek}`);

async function syncNFLGames() {
  const startTime = Date.now();
  const results = {
    total: 0,
    inserted: 0,
    updated: 0,
    errors: []
  };

  try {
    // Test Supabase connection first
    console.log('🔍 Testing Supabase connection...');
    const { data: testData, error: testError } = await supabase
      .from('games')
      .select('count')
      .limit(1);

    if (testError) {
      throw new Error(`Supabase connection failed: ${testError.message}`);
    }
    console.log('✅ Supabase connection successful\n');

    // Fetch games from ESPN API
    console.log('📡 Fetching NFL games from ESPN API...');
    const espnResponse = await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard');

    if (!espnResponse.ok) {
      throw new Error(`ESPN API error: ${espnResponse.status} ${espnResponse.statusText}`);
    }

    const espnData = await espnResponse.json();
    const games = espnData.events || [];

    console.log(`📊 Found ${games.length} NFL games from ESPN\n`);
    results.total = games.length;

    if (games.length === 0) {
      console.log('⚠️ No games found. This might be the off-season or API issues.');
      return results;
    }

    // Process each game
    for (const event of games) {
      try {
        const competition = event.competitions?.[0];
        if (!competition) {
          console.log(`⚠️ Skipping event ${event.id} - no competition data`);
          continue;
        }

        const homeTeam = competition.competitors?.find(c => c.homeAway === 'home');
        const awayTeam = competition.competitors?.find(c => c.homeAway === 'away');

        if (!homeTeam || !awayTeam) {
          console.log(`⚠️ Skipping game ${event.id} - missing team data`);
          continue;
        }

        // Build game data object - only include columns that exist in our schema
        const gameData = {
          espn_game_id: event.id.toString(),
          home_team: homeTeam.team.abbreviation,
          away_team: awayTeam.team.abbreviation,
          home_score: parseInt(homeTeam.score) || null,
          away_score: parseInt(awayTeam.score) || null,
          game_time: new Date(event.date).toISOString(),
          week: event.week?.number || currentWeek,
          season: event.season?.year || 2025,
          venue: competition.venue?.fullName || null,
          status: mapESPNStatus(competition.status?.type?.name),
          updated_at: new Date().toISOString()
        };

        console.log(`🏈 Processing: ${gameData.away_team} @ ${gameData.home_team}`);
        console.log(`   📅 ${new Date(gameData.game_time).toLocaleDateString()} ${new Date(gameData.game_time).toLocaleTimeString()}`);
        console.log(`   🏟️ ${gameData.venue || 'Venue TBD'}`);
        console.log(`   📊 Status: ${gameData.status} | Week: ${gameData.week} | Season: ${gameData.season}`);

        // Check if game already exists
        const { data: existingGame, error: checkError } = await supabase
          .from('games')
          .select('id, home_score, away_score, status')
          .eq('espn_game_id', gameData.espn_game_id)
          .single();

        if (checkError && checkError.code !== 'PGRST116') { // PGRST116 = no rows found
          console.log(`   ❌ Error checking existing game: ${checkError.message}`);
          results.errors.push({ gameId: event.id, error: checkError.message });
          continue;
        }

        let operation = 'insert';
        if (existingGame) {
          operation = 'update';
          console.log(`   🔄 Game exists, updating...`);
        } else {
          console.log(`   ➕ New game, inserting...`);
        }

        // Insert or update the game
        const { data: upsertData, error: upsertError } = await supabase
          .from('games')
          .upsert(gameData, {
            onConflict: 'espn_game_id',
            ignoreDuplicates: false
          })
          .select('id, home_team, away_team, status');

        if (upsertError) {
          console.log(`   ❌ Upsert error: ${upsertError.message}`);
          results.errors.push({
            gameId: event.id,
            error: upsertError.message,
            details: upsertError.details || upsertError.hint
          });
        } else {
          console.log(`   ✅ ${operation === 'insert' ? 'Inserted' : 'Updated'} successfully`);
          if (operation === 'insert') {
            results.inserted++;
          } else {
            results.updated++;
          }
        }

        console.log(''); // Empty line for readability

      } catch (gameError) {
        console.log(`   ❌ Game processing error: ${gameError.message}`);
        results.errors.push({
          gameId: event.id || 'unknown',
          error: gameError.message
        });
      }
    }

    // Display results
    const duration = Date.now() - startTime;
    console.log('\n📈 Sync Results Summary');
    console.log('=' .repeat(50));
    console.log(`📊 Total games processed: ${results.total}`);
    console.log(`➕ Games inserted: ${results.inserted}`);
    console.log(`🔄 Games updated: ${results.updated}`);
    console.log(`❌ Errors: ${results.errors.length}`);
    console.log(`⏱️ Duration: ${(duration / 1000).toFixed(2)} seconds`);

    if (results.errors.length > 0) {
      console.log('\n❌ Error Details:');
      results.errors.forEach((err, index) => {
        console.log(`   ${index + 1}. Game ${err.gameId}: ${err.error}`);
        if (err.details) {
          console.log(`      Details: ${err.details}`);
        }
      });
    }

    // Verify games in database
    console.log('\n🔍 Verification: Recent games in database');
    console.log('-' .repeat(50));

    const { data: verifyGames, error: verifyError } = await supabase
      .from('games')
      .select('id, espn_game_id, home_team, away_team, status, game_time, week, season')
      .gte('season', 2025)
      .order('game_time', { ascending: true })
      .limit(15);

    if (verifyError) {
      console.log('❌ Verification query failed:', verifyError.message);
    } else {
      console.log(`✅ Found ${verifyGames.length} games in database (2025 season)`);
      verifyGames.forEach((game, index) => {
        const gameTime = new Date(game.game_time);
        console.log(`   ${index + 1}. ${game.away_team} @ ${game.home_team} - ${game.status}`);
        console.log(`      📅 ${gameTime.toLocaleDateString()} ${gameTime.toLocaleTimeString()}`);
        console.log(`      🏷️ Week ${game.week} | ESPN ID: ${game.espn_game_id}`);
      });
    }

    return results;

  } catch (error) {
    console.error('\n💥 Critical error during sync:', error.message);
    if (error.stack) {
      console.error('Stack trace:', error.stack);
    }
    throw error;
  }
}

// Execute the sync
syncNFLGames()
  .then((results) => {
    console.log('\n🎉 NFL game sync completed successfully!');
    if (results.inserted > 0 || results.updated > 0) {
      console.log(`🎯 Successfully synced ${results.inserted + results.updated} games`);
    }
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n💥 NFL game sync failed:', error.message);
    process.exit(1);
  });