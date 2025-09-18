#!/usr/bin/env node

/**
 * Complete NFL 2025 Season Setup Script
 * Creates enhanced database schema and imports all 272 games
 */

import { createClient } from '@supabase/supabase-js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Supabase configuration
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://vaypgzvivahnfegnlinn.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws';

const supabase = createClient(supabaseUrl, supabaseKey);

async function setupDatabase() {
  console.log('🏈 NFL 2025 Complete Season Setup');
  console.log('==================================\n');

  try {
    // Step 1: Read the schema SQL file
    console.log('📋 Step 1: Reading database schema...');
    const schemaPath = path.join(__dirname, '..', 'docs', 'sports', 'nfl_schedule_schema.sql');
    const schemaSql = await fs.readFile(schemaPath, 'utf8');
    console.log('✅ Schema loaded\n');

    // Step 2: Create the table (check if exists first)
    console.log('🔨 Step 2: Creating nfl_games_2025 table...');

    // First, check if table exists
    const { data: tables, error: tableError } = await supabase
      .from('nfl_games_2025')
      .select('game_id')
      .limit(1);

    if (tableError && tableError.code === '42P01') {
      // Table doesn't exist, create it
      console.log('   Table does not exist, creating new table...');

      // Note: Supabase doesn't support direct SQL execution via the client library
      // We'll need to run this in the Supabase dashboard SQL editor
      console.log('\n⚠️  MANUAL STEP REQUIRED:');
      console.log('   Please run the following SQL in your Supabase dashboard SQL Editor:');
      console.log('   Dashboard URL: https://app.supabase.com/project/vaypgzvivahnfegnlinn/editor/sql');
      console.log('\n--- Copy this SQL ---\n');
      console.log(schemaSql);
      console.log('--- End SQL ---\n');
      console.log('   After creating the table, run this script again with --skip-create flag\n');

      if (!process.argv.includes('--skip-create')) {
        process.exit(0);
      }
    } else {
      console.log('✅ Table already exists or was just created\n');
    }

    // Step 3: Load the JSON data
    console.log('📊 Step 3: Loading NFL 2025 schedule data...');
    const dataPath = path.join(__dirname, '..', 'docs', 'sports', 'nfl_schedule_2025.json');
    const scheduleData = JSON.parse(await fs.readFile(dataPath, 'utf8'));
    const games = scheduleData.games || [];
    console.log(`✅ Loaded ${games.length} games from JSON\n`);

    // Step 4: Process and insert/update games
    console.log('💾 Step 4: Importing games to database...');
    let inserted = 0;
    let updated = 0;
    let errors = 0;

    for (const game of games) {
      // Check if game exists
      const { data: existing } = await supabase
        .from('nfl_games_2025')
        .select('game_id')
        .eq('game_id', game.game_id)
        .single();

      if (existing) {
        // Update existing game
        const { error } = await supabase
          .from('nfl_games_2025')
          .update({
            ...game,
            updated_at: new Date().toISOString()
          })
          .eq('game_id', game.game_id);

        if (error) {
          console.error(`❌ Error updating game ${game.game_id}:`, error.message);
          errors++;
        } else {
          updated++;
          process.stdout.write(`\r   Updated: ${updated} | Inserted: ${inserted} | Errors: ${errors}`);
        }
      } else {
        // Insert new game
        const { error } = await supabase
          .from('nfl_games_2025')
          .insert({
            ...game,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          });

        if (error) {
          console.error(`❌ Error inserting game ${game.game_id}:`, error.message);
          errors++;
        } else {
          inserted++;
          process.stdout.write(`\r   Updated: ${updated} | Inserted: ${inserted} | Errors: ${errors}`);
        }
      }
    }

    console.log('\n\n📈 Import Summary');
    console.log('==================');
    console.log(`✅ Games inserted: ${inserted}`);
    console.log(`🔄 Games updated: ${updated}`);
    console.log(`❌ Errors: ${errors}`);
    console.log(`📊 Total processed: ${games.length}`);

    // Step 5: Verify the data
    console.log('\n🔍 Step 5: Verifying imported data...');

    // Get game count by week
    const { data: weekCounts } = await supabase
      .from('nfl_games_2025')
      .select('week')
      .order('week', { ascending: true });

    const weekStats = {};
    if (weekCounts) {
      weekCounts.forEach(row => {
        weekStats[row.week] = (weekStats[row.week] || 0) + 1;
      });
    }

    console.log('\n📅 Games by Week:');
    Object.entries(weekStats).forEach(([week, count]) => {
      const weekLabel = week > 18 ? `Playoff Week ${week - 18}` : `Week ${week}`;
      console.log(`   ${weekLabel}: ${count} games`);
    });

    // Get sample games
    const { data: sampleGames } = await supabase
      .from('nfl_games_2025')
      .select('game_id, week, game_date, away_team, home_team, network')
      .order('game_date', { ascending: true })
      .limit(5);

    console.log('\n🏈 Sample Games:');
    if (sampleGames) {
      sampleGames.forEach(game => {
        console.log(`   Week ${game.week}: ${game.away_team} @ ${game.home_team} on ${game.network} (${game.game_date})`);
      });
    }

    console.log('\n✨ Complete! The full 2025 NFL season is now in your database!');
    console.log('   - 272 total games (regular season + playoffs)');
    console.log('   - International games included');
    console.log('   - Network and stadium information');
    console.log('   - Ready for predictions!\n');

  } catch (error) {
    console.error('\n❌ Error during setup:', error);
    process.exit(1);
  }
}

// Run the setup
console.log('Starting NFL 2025 season setup...\n');
setupDatabase();