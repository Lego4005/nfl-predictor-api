#!/usr/bin/env node

/**
 * Enhance existing games table with additional fields
 * Adds network, stadium, city, state, timezone and other useful fields
 */

import { createClient } from '@supabase/supabase-js';
import fetch from 'node-fetch';

// Supabase configuration
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://vaypgzvivahnfegnlinn.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws';

const supabase = createClient(supabaseUrl, supabaseKey);

// Stadium data for each team
const stadiumData = {
  'ARI': { stadium: 'State Farm Stadium', city: 'Glendale', state: 'AZ', timezone: 'MST' },
  'ATL': { stadium: 'Mercedes-Benz Stadium', city: 'Atlanta', state: 'GA', timezone: 'EST' },
  'BAL': { stadium: 'M&T Bank Stadium', city: 'Baltimore', state: 'MD', timezone: 'EST' },
  'BUF': { stadium: 'Highmark Stadium', city: 'Orchard Park', state: 'NY', timezone: 'EST' },
  'CAR': { stadium: 'Bank of America Stadium', city: 'Charlotte', state: 'NC', timezone: 'EST' },
  'CHI': { stadium: 'Soldier Field', city: 'Chicago', state: 'IL', timezone: 'CST' },
  'CIN': { stadium: 'Paycor Stadium', city: 'Cincinnati', state: 'OH', timezone: 'EST' },
  'CLE': { stadium: 'Cleveland Browns Stadium', city: 'Cleveland', state: 'OH', timezone: 'EST' },
  'DAL': { stadium: 'AT&T Stadium', city: 'Arlington', state: 'TX', timezone: 'CST' },
  'DEN': { stadium: 'Empower Field at Mile High', city: 'Denver', state: 'CO', timezone: 'MST' },
  'DET': { stadium: 'Ford Field', city: 'Detroit', state: 'MI', timezone: 'EST' },
  'GB': { stadium: 'Lambeau Field', city: 'Green Bay', state: 'WI', timezone: 'CST' },
  'HOU': { stadium: 'NRG Stadium', city: 'Houston', state: 'TX', timezone: 'CST' },
  'IND': { stadium: 'Lucas Oil Stadium', city: 'Indianapolis', state: 'IN', timezone: 'EST' },
  'JAX': { stadium: 'TIAA Bank Field', city: 'Jacksonville', state: 'FL', timezone: 'EST' },
  'KC': { stadium: 'GEHA Field at Arrowhead Stadium', city: 'Kansas City', state: 'MO', timezone: 'CST' },
  'LAC': { stadium: 'SoFi Stadium', city: 'Inglewood', state: 'CA', timezone: 'PST' },
  'LAR': { stadium: 'SoFi Stadium', city: 'Inglewood', state: 'CA', timezone: 'PST' },
  'LV': { stadium: 'Allegiant Stadium', city: 'Las Vegas', state: 'NV', timezone: 'PST' },
  'MIA': { stadium: 'Hard Rock Stadium', city: 'Miami Gardens', state: 'FL', timezone: 'EST' },
  'MIN': { stadium: 'U.S. Bank Stadium', city: 'Minneapolis', state: 'MN', timezone: 'CST' },
  'NE': { stadium: 'Gillette Stadium', city: 'Foxborough', state: 'MA', timezone: 'EST' },
  'NO': { stadium: 'Caesars Superdome', city: 'New Orleans', state: 'LA', timezone: 'CST' },
  'NYG': { stadium: 'MetLife Stadium', city: 'East Rutherford', state: 'NJ', timezone: 'EST' },
  'NYJ': { stadium: 'MetLife Stadium', city: 'East Rutherford', state: 'NJ', timezone: 'EST' },
  'PHI': { stadium: 'Lincoln Financial Field', city: 'Philadelphia', state: 'PA', timezone: 'EST' },
  'PIT': { stadium: 'Acrisure Stadium', city: 'Pittsburgh', state: 'PA', timezone: 'EST' },
  'SEA': { stadium: 'Lumen Field', city: 'Seattle', state: 'WA', timezone: 'PST' },
  'SF': { stadium: "Levi's Stadium", city: 'Santa Clara', state: 'CA', timezone: 'PST' },
  'TB': { stadium: 'Raymond James Stadium', city: 'Tampa', state: 'FL', timezone: 'EST' },
  'TEN': { stadium: 'Nissan Stadium', city: 'Nashville', state: 'TN', timezone: 'CST' },
  'WAS': { stadium: 'FedExField', city: 'Landover', state: 'MD', timezone: 'EST' },
  'WSH': { stadium: 'FedExField', city: 'Landover', state: 'MD', timezone: 'EST' } // Alternative abbreviation
};

// Network assignments (simplified - in reality this would be based on the actual schedule)
const getNetwork = (homeTeam, dayOfWeek, gameTime) => {
  const hour = parseInt(gameTime?.split(':')[0] || '13');

  if (dayOfWeek === 'Thursday') return 'Prime Video';
  if (dayOfWeek === 'Monday') return 'ESPN';
  if (dayOfWeek === 'Sunday') {
    if (hour >= 20) return 'NBC'; // Sunday Night Football
    if (hour >= 16) return 'CBS/FOX'; // Late afternoon games
    return 'CBS/FOX'; // Early afternoon games
  }
  return 'NFL Network';
};

async function fetchAdditionalScheduleData() {
  console.log('🏈 Fetching additional 2025 NFL schedule data from ESPN...\n');

  try {
    // Fetch current season data from ESPN
    const response = await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2025&seasontype=2');
    const data = await response.json();

    if (data.events && data.events.length > 0) {
      console.log(`Found ${data.events.length} games from ESPN API\n`);
      return data.events;
    }

    // If no 2025 data, try to get the latest available
    const currentResponse = await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard');
    const currentData = await currentResponse.json();

    if (currentData.events) {
      console.log(`Found ${currentData.events.length} current games from ESPN API\n`);
      return currentData.events;
    }

    return [];
  } catch (error) {
    console.error('Error fetching ESPN data:', error);
    return [];
  }
}

async function enhanceGamesTable() {
  console.log('🚀 Enhancing NFL Games Table');
  console.log('================================\n');

  try {
    // Step 1: Get all existing games
    console.log('📊 Step 1: Fetching existing games...');
    const { data: existingGames, error: fetchError } = await supabase
      .from('games')
      .select('*')
      .order('game_time', { ascending: true });

    if (fetchError) {
      throw fetchError;
    }

    console.log(`✅ Found ${existingGames?.length || 0} existing games\n`);

    // Step 2: Fetch additional data from ESPN
    console.log('🔄 Step 2: Fetching additional schedule data...');
    const espnEvents = await fetchAdditionalScheduleData();

    // Step 3: Update games with enhanced data
    console.log('💾 Step 3: Enhancing game records...');
    let enhanced = 0;
    let errors = 0;

    if (existingGames) {
      for (const game of existingGames) {
        const homeTeam = game.home_team;
        const stadiumInfo = stadiumData[homeTeam] || stadiumData['WSH']; // Default fallback

        // Determine day of week from game_time
        const gameDate = new Date(game.game_time);
        const dayOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][gameDate.getDay()];
        const gameHour = gameDate.getHours();

        // Determine if it's a primetime game
        const isPrimetime = (dayOfWeek === 'Thursday' && gameHour >= 20) ||
                          (dayOfWeek === 'Sunday' && gameHour >= 20) ||
                          (dayOfWeek === 'Monday' && gameHour >= 20);

        // Build enhanced data
        const enhancedData = {
          stadium: stadiumInfo?.stadium,
          city: stadiumInfo?.city,
          state: stadiumInfo?.state,
          timezone: stadiumInfo?.timezone,
          network: getNetwork(homeTeam, dayOfWeek, `${gameHour}:00`),
          day_of_week: dayOfWeek,
          is_primetime: isPrimetime,
          is_playoff: game.week > 18 || game.game_type === 'playoff',
          is_international: false, // Would need specific data for international games
        };

        // Update the game record
        const { error: updateError } = await supabase
          .from('games')
          .update(enhancedData)
          .eq('id', game.id);

        if (updateError) {
          console.error(`❌ Error updating game ${game.id}:`, updateError.message);
          errors++;
        } else {
          enhanced++;
          process.stdout.write(`\r   Enhanced: ${enhanced} | Errors: ${errors}`);
        }
      }
    }

    console.log('\n\n📈 Enhancement Summary');
    console.log('======================');
    console.log(`✅ Games enhanced: ${enhanced}`);
    console.log(`❌ Errors: ${errors}`);

    // Step 4: Display sample enhanced games
    console.log('\n🔍 Sample Enhanced Games:');
    const { data: sampleGames } = await supabase
      .from('games')
      .select('*')
      .limit(5)
      .order('game_time', { ascending: true });

    if (sampleGames) {
      sampleGames.forEach(game => {
        console.log(`\n   📅 ${game.away_team} @ ${game.home_team}`);
        console.log(`      🏟️  ${game.stadium || 'N/A'} - ${game.city || 'N/A'}, ${game.state || 'N/A'}`);
        console.log(`      📺 ${game.network || 'TBD'} | ${game.day_of_week || 'N/A'}`);
        console.log(`      ⭐ Primetime: ${game.is_primetime ? 'Yes' : 'No'}`);
      });
    }

    console.log('\n✨ Enhancement complete!');
    console.log('   Games now include:');
    console.log('   - Stadium and location information');
    console.log('   - Network broadcasting data');
    console.log('   - Primetime game indicators');
    console.log('   - Day of week information\n');

  } catch (error) {
    console.error('\n❌ Error during enhancement:', error);
    process.exit(1);
  }
}

// Run the enhancement
enhanceGamesTable();