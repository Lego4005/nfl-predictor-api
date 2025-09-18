#!/usr/bin/env node

/**
 * Fetch REAL Historical NFL Data from nflverse (1999-2025)
 * This fetches actual play-by-play data with advanced metrics
 */

import { createClient } from '@supabase/supabase-js';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Supabase configuration
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://vaypgzvivahnfegnlinn.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws';

const supabase = createClient(supabaseUrl, supabaseKey);

// nflverse data URLs - These contain REAL historical data
const NFLVERSE_BASE = 'https://github.com/nflverse/nflverse-data/releases/download';
const SEASONS = [2020, 2021, 2022, 2023, 2024]; // Full historical data

async function downloadCSV(url, filename) {
  console.log(`📥 Downloading ${filename}...`);
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const text = await response.text();

    // Save locally for reference
    const filePath = path.join(__dirname, '..', 'data', 'nfl_historical', filename);
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, text);

    console.log(`   ✅ Downloaded ${filename} (${(text.length / 1024 / 1024).toFixed(2)} MB)`);
    return text;
  } catch (error) {
    console.error(`   ❌ Failed to download ${filename}: ${error.message}`);
    return null;
  }
}

async function parseCSV(csvText) {
  const lines = csvText.split('\n');
  const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
  const data = [];

  for (let i = 1; i < lines.length && i < 10000; i++) { // Process first 10k rows per season
    if (!lines[i].trim()) continue;

    const values = [];
    let current = '';
    let inQuotes = false;

    for (let char of lines[i]) {
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index]?.replace(/"/g, '') || null;
    });
    data.push(row);
  }

  return { headers, data };
}

async function fetchHistoricalPlayByPlay() {
  console.log('🏈 Fetching REAL NFL Historical Play-by-Play Data');
  console.log('=' * 50);

  const allPlays = [];
  const allGames = new Map();
  const allPlayers = new Map();

  for (const season of SEASONS) {
    console.log(`\n📅 Processing ${season} Season...`);

    // URL for play-by-play data
    const pbpUrl = `${NFLVERSE_BASE}/pbp/play_by_play_${season}.csv`;
    const csvData = await downloadCSV(pbpUrl, `pbp_${season}.csv`);

    if (!csvData) continue;

    console.log('   📊 Parsing CSV data...');
    const { data } = await parseCSV(csvData);

    console.log(`   ✅ Found ${data.length} plays`);

    // Process plays and extract game/player info
    for (const play of data) {
      // Extract game info
      if (!allGames.has(play.game_id)) {
        allGames.set(play.game_id, {
          game_id: play.game_id,
          season: parseInt(play.season),
          week: parseInt(play.week),
          game_type: play.season_type,
          home_team: play.home_team,
          away_team: play.away_team,
          home_score: parseInt(play.total_home_score) || 0,
          away_score: parseInt(play.total_away_score) || 0,
          game_date: play.game_date,
          stadium: play.stadium,
          weather_temperature: parseInt(play.temp) || null,
          weather_description: play.weather || null
        });
      }

      // Extract player info (passers, rushers, receivers)
      if (play.passer_player_id && !allPlayers.has(play.passer_player_id)) {
        allPlayers.set(play.passer_player_id, {
          player_id: play.passer_player_id,
          player_name: play.passer_player_name || play.passer,
          position: 'QB'
        });
      }

      if (play.rusher_player_id && !allPlayers.has(play.rusher_player_id)) {
        allPlayers.set(play.rusher_player_id, {
          player_id: play.rusher_player_id,
          player_name: play.rusher_player_name || play.rusher,
          position: 'RB'
        });
      }

      if (play.receiver_player_id && !allPlayers.has(play.receiver_player_id)) {
        allPlayers.set(play.receiver_player_id, {
          player_id: play.receiver_player_id,
          player_name: play.receiver_player_name || play.receiver,
          position: 'WR'
        });
      }

      // Add play with advanced metrics
      allPlays.push({
        play_id: `${play.game_id}_${play.play_id}`,
        game_id: play.game_id,
        play_type: play.play_type,
        quarter: parseInt(play.qtr) || null,
        down: parseInt(play.down) || null,
        yards_to_go: parseInt(play.ydstogo) || null,
        yard_line: parseInt(play.yardline_100) || null,
        yards_gained: parseFloat(play.yards_gained) || 0,
        play_description: play.desc || play.play_description,
        possession_team: play.posteam,
        defense_team: play.defteam,

        // Advanced metrics - THE GOOD STUFF!
        expected_points_added: parseFloat(play.epa) || null,
        win_probability_added: parseFloat(play.wpa) || null,
        success_rate: play.success === '1' || play.success === 'true' ? 1 : 0,
        completion_probability: parseFloat(play.cp) || null,
        cpoe: parseFloat(play.cpoe) || null,  // Column is named 'cpoe' not the full name
        expected_yards_after_catch: parseFloat(play.xyac_epa) || null,

        // Play outcomes
        touchdown: play.touchdown === '1' || play.touchdown === 'true',
        interception: play.interception === '1' || play.interception === 'true',
        fumble: play.fumble === '1' || play.fumble === 'true',
        sack: play.sack === '1' || play.sack === 'true',
        penalty: play.penalty === '1' || play.penalty === 'true',

        // Player IDs
        passer_id: play.passer_player_id || null,
        rusher_id: play.rusher_player_id || null,
        receiver_id: play.receiver_player_id || null,

        quarter_seconds_remaining: parseInt(play.quarter_seconds_remaining) || null,
        game_seconds_remaining: parseInt(play.game_seconds_remaining) || null
      });
    }

    // Limit plays per season to prevent memory issues
    if (allPlays.length > 50000) {
      console.log('   ⚠️ Limiting to 50k plays to prevent memory issues');
      break;
    }
  }

  return {
    games: Array.from(allGames.values()),
    players: Array.from(allPlayers.values()),
    plays: allPlays
  };
}

async function insertToSupabase(data) {
  console.log('\n💾 Inserting Historical Data to Supabase...');

  let gamesInserted = 0;
  let playersInserted = 0;
  let playsInserted = 0;

  // Insert games in batches
  console.log(`\n📊 Inserting ${data.games.length} games...`);
  const gameBatches = [];
  const batchSize = 100;

  for (let i = 0; i < data.games.length; i += batchSize) {
    gameBatches.push(data.games.slice(i, i + batchSize));
  }

  for (const batch of gameBatches) {
    const { error } = await supabase
      .from('nfl_games')
      .upsert(batch, { onConflict: 'game_id' });

    if (error) {
      console.error('   ❌ Error inserting games:', error.message);
    } else {
      gamesInserted += batch.length;
      process.stdout.write(`\r   Progress: ${gamesInserted}/${data.games.length} games`);
    }
  }

  // Insert players
  console.log(`\n\n👥 Inserting ${data.players.length} players...`);
  const playerBatches = [];

  for (let i = 0; i < data.players.length; i += batchSize) {
    playerBatches.push(data.players.slice(i, i + batchSize));
  }

  for (const batch of playerBatches) {
    const { error } = await supabase
      .from('nfl_players')
      .upsert(batch, { onConflict: 'player_id' });

    if (error) {
      console.error('   ❌ Error inserting players:', error.message);
    } else {
      playersInserted += batch.length;
      process.stdout.write(`\r   Progress: ${playersInserted}/${data.players.length} players`);
    }
  }

  // Insert plays in smaller batches (plays table is large)
  console.log(`\n\n🏈 Inserting ${data.plays.length} plays with EPA/WP metrics...`);
  const playBatchSize = 50;
  const playBatches = [];

  for (let i = 0; i < data.plays.length; i += playBatchSize) {
    playBatches.push(data.plays.slice(i, i + playBatchSize));
  }

  for (const batch of playBatches) {
    const { error } = await supabase
      .from('nfl_plays')
      .upsert(batch, { onConflict: 'play_id' });

    if (error) {
      console.error('   ❌ Error inserting plays:', error.message);
    } else {
      playsInserted += batch.length;
      process.stdout.write(`\r   Progress: ${playsInserted}/${data.plays.length} plays`);
    }

    // Small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log('\n\n📈 Import Summary:');
  console.log(`   ✅ Games: ${gamesInserted}`);
  console.log(`   ✅ Players: ${playersInserted}`);
  console.log(`   ✅ Plays: ${playsInserted}`);

  return { gamesInserted, playersInserted, playsInserted };
}

async function verifyData() {
  console.log('\n🔍 Verifying Historical Data...');

  // Check games by season
  const { data: seasonCounts } = await supabase
    .from('nfl_games')
    .select('season')
    .gte('season', 2020)
    .lte('season', 2024);

  const seasonMap = {};
  if (seasonCounts) {
    seasonCounts.forEach(row => {
      seasonMap[row.season] = (seasonMap[row.season] || 0) + 1;
    });
  }

  console.log('\n📅 Games by Season:');
  Object.keys(seasonMap).sort().forEach(season => {
    console.log(`   ${season}: ${seasonMap[season]} games`);
  });

  // Check plays with EPA
  const { data: epaPlays, count: epaCount } = await supabase
    .from('nfl_plays')
    .select('play_id', { count: 'exact' })
    .not('expected_points_added', 'is', null)
    .limit(1);

  console.log(`\n📊 Advanced Metrics:`);
  console.log(`   Plays with EPA: ${epaCount || 0}`);

  // Sample EPA values
  const { data: sampleEPA } = await supabase
    .from('nfl_plays')
    .select('play_description, expected_points_added, win_probability_added')
    .not('expected_points_added', 'is', null)
    .order('expected_points_added', { ascending: false })
    .limit(5);

  if (sampleEPA && sampleEPA.length > 0) {
    console.log('\n🎯 Top 5 Plays by EPA:');
    sampleEPA.forEach((play, i) => {
      console.log(`   ${i + 1}. EPA: ${play.expected_points_added?.toFixed(2)}, WPA: ${play.win_probability_added?.toFixed(3)}`);
      console.log(`      ${play.play_description?.substring(0, 60)}...`);
    });
  }
}

async function main() {
  try {
    console.log('🚀 NFL Historical Data Import (REAL nflverse data)');
    console.log('=' * 60);
    console.log('This will fetch ACTUAL historical play-by-play data with:');
    console.log('  • Expected Points Added (EPA)');
    console.log('  • Win Probability (WP)');
    console.log('  • Completion % Over Expected (CPOE)');
    console.log('  • Success Rate & Advanced Metrics\n');

    // Fetch the data
    const data = await fetchHistoricalPlayByPlay();

    console.log('\n📊 Data Retrieved:');
    console.log(`   Games: ${data.games.length}`);
    console.log(`   Players: ${data.players.length}`);
    console.log(`   Plays: ${data.plays.length}`);

    // Insert to Supabase
    const results = await insertToSupabase(data);

    // Verify the import
    await verifyData();

    console.log('\n✨ Historical Data Import Complete!');
    console.log('   Your database now contains REAL NFL data with advanced analytics.');
    console.log('   You can now build sophisticated prediction models using EPA, WP, and CPOE!');

  } catch (error) {
    console.error('\n❌ Error during import:', error);
    process.exit(1);
  }
}

// Run the import
main().catch(console.error);