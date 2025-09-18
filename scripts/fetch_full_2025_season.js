#!/usr/bin/env node

/**
 * Fetch Complete 2025 NFL Season (272 games)
 * Includes: 18 regular season weeks + playoffs + international games
 */

import { createClient } from '@supabase/supabase-js';
import fetch from 'node-fetch';

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://vaypgzvivahnfegnlinn.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws';

const supabase = createClient(supabaseUrl, supabaseKey);

// International game locations for 2025
const internationalGames = {
  'Brazil': ['São Paulo'],
  'Ireland': ['Dublin'],
  'Spain': ['Madrid'],
  'England': ['London'],
  'Germany': ['Munich', 'Berlin']
};

// Network assignments based on day/time
const getNetwork = (dayOfWeek, hour, week) => {
  if (dayOfWeek === 'Thursday') return 'Prime Video';
  if (dayOfWeek === 'Monday') return 'ESPN';
  if (dayOfWeek === 'Sunday') {
    if (hour >= 20) return 'NBC'; // Sunday Night Football
    if (hour >= 16) return week % 2 === 0 ? 'CBS' : 'FOX'; // Late afternoon
    return week % 2 === 0 ? 'FOX' : 'CBS'; // Early afternoon
  }
  if (dayOfWeek === 'Saturday') return 'NFL Network';
  return 'TBD';
};

async function fetchWeekGames(week, seasonType = 2) {
  console.log(`📡 Fetching Week ${week} games...`);

  try {
    // ESPN API endpoint for NFL schedule
    const url = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week=${week}&year=2025&seasontype=${seasonType}`;
    const response = await fetch(url);

    if (!response.ok) {
      console.log(`   ⚠️ No data for Week ${week}`);
      return [];
    }

    const data = await response.json();

    if (!data.events || data.events.length === 0) {
      console.log(`   ⚠️ No games found for Week ${week}`);
      return [];
    }

    console.log(`   ✅ Found ${data.events.length} games`);

    return data.events.map(event => {
      const competition = event.competitions[0];
      const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
      const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

      const gameDate = new Date(event.date);
      const dayOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][gameDate.getDay()];
      const hour = gameDate.getHours();

      // Determine if it's primetime
      const isPrimetime =
        (dayOfWeek === 'Thursday' && hour >= 20) ||
        (dayOfWeek === 'Sunday' && hour >= 20) ||
        (dayOfWeek === 'Monday' && hour >= 20);

      // Check game status
      const statusType = competition.status?.type?.name || '';
      let status = 'scheduled';
      if (statusType === 'STATUS_IN_PROGRESS') status = 'live';
      else if (statusType === 'STATUS_FINAL') status = 'final';

      return {
        espn_game_id: event.id,
        home_team: homeTeam.team.abbreviation,
        away_team: awayTeam.team.abbreviation,
        home_score: parseInt(homeTeam.score) || 0,
        away_score: parseInt(awayTeam.score) || 0,
        game_time: event.date,
        week: week,
        season: 2025,
        season_type: seasonType === 2 ? 'regular' : seasonType === 3 ? 'playoff' : 'preseason',
        venue: competition.venue?.fullName || null,
        status: status,
        quarter: competition.status?.period || null,
        time_remaining: competition.status?.displayClock || null,
        day_of_week: dayOfWeek,
        network: getNetwork(dayOfWeek, hour, week),
        is_primetime: isPrimetime,
        is_playoff: seasonType === 3,
        temperature: competition.weather?.temperature || null,
        precipitation: competition.weather?.displayValue || null,
        attendance: competition.attendance || null
      };
    });
  } catch (error) {
    console.error(`   ❌ Error fetching Week ${week}:`, error.message);
    return [];
  }
}

async function fetchFullSeason() {
  console.log('🏈 NFL 2025 Full Season Fetch');
  console.log('=====================================');
  console.log('📅 Season: September 4, 2025 - February 8, 2026');
  console.log('🎯 Total games: 272 (including playoffs)');
  console.log('🌍 International games: 7 locations\n');

  const allGames = [];
  let totalProcessed = 0;
  let totalInserted = 0;
  let totalUpdated = 0;
  let totalErrors = 0;

  // Fetch regular season (Weeks 1-18)
  console.log('📊 Fetching Regular Season (Weeks 1-18)...\n');
  for (let week = 1; week <= 18; week++) {
    const games = await fetchWeekGames(week, 2); // seasontype 2 = regular
    allGames.push(...games);

    // Process games immediately to avoid memory issues
    for (const game of games) {
      totalProcessed++;

      // Check if game exists
      const { data: existing } = await supabase
        .from('games')
        .select('id')
        .eq('espn_game_id', game.espn_game_id)
        .single();

      if (existing) {
        // Update existing game
        const { error } = await supabase
          .from('games')
          .update(game)
          .eq('espn_game_id', game.espn_game_id);

        if (error) {
          console.error(`❌ Error updating game:`, error.message);
          totalErrors++;
        } else {
          totalUpdated++;
        }
      } else {
        // Insert new game
        const { error } = await supabase
          .from('games')
          .insert(game);

        if (error) {
          console.error(`❌ Error inserting game:`, error.message);
          totalErrors++;
        } else {
          totalInserted++;
        }
      }

      // Show progress
      process.stdout.write(`\r   Progress: ${totalProcessed} games | Inserted: ${totalInserted} | Updated: ${totalUpdated} | Errors: ${totalErrors}`);
    }

    // Small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log('\n');

  // Fetch playoffs (Wild Card, Divisional, Conference, Super Bowl)
  console.log('🏆 Fetching Playoffs...\n');

  // Wild Card Round (usually Week 19)
  const wildCard = await fetchWeekGames(1, 3); // seasontype 3 = playoff, week 1 = wild card
  console.log(`   Wild Card: ${wildCard.length} games`);
  allGames.push(...wildCard);

  // Divisional Round (Week 20)
  const divisional = await fetchWeekGames(2, 3);
  console.log(`   Divisional: ${divisional.length} games`);
  allGames.push(...divisional);

  // Conference Championships (Week 21)
  const conference = await fetchWeekGames(3, 3);
  console.log(`   Conference: ${conference.length} games`);
  allGames.push(...conference);

  // Super Bowl (Week 22)
  const superBowl = await fetchWeekGames(5, 3); // Super Bowl is typically week 5 of playoffs
  console.log(`   Super Bowl: ${superBowl.length} games`);
  allGames.push(...superBowl);

  // Process playoff games
  for (const game of [...wildCard, ...divisional, ...conference, ...superBowl]) {
    totalProcessed++;

    const { data: existing } = await supabase
      .from('games')
      .select('id')
      .eq('espn_game_id', game.espn_game_id)
      .single();

    if (existing) {
      const { error } = await supabase
        .from('games')
        .update(game)
        .eq('espn_game_id', game.espn_game_id);

      if (error) {
        totalErrors++;
      } else {
        totalUpdated++;
      }
    } else {
      const { error } = await supabase
        .from('games')
        .insert(game);

      if (error) {
        totalErrors++;
      } else {
        totalInserted++;
      }
    }

    process.stdout.write(`\r   Progress: ${totalProcessed} games | Inserted: ${totalInserted} | Updated: ${totalUpdated} | Errors: ${totalErrors}`);
  }

  console.log('\n\n📈 Final Summary');
  console.log('==================');
  console.log(`✅ Total games processed: ${totalProcessed}`);
  console.log(`➕ Games inserted: ${totalInserted}`);
  console.log(`🔄 Games updated: ${totalUpdated}`);
  console.log(`❌ Errors: ${totalErrors}`);

  // Verify data in database
  console.log('\n🔍 Verifying Database...');
  const { data: gameCount } = await supabase
    .from('games')
    .select('id', { count: 'exact' });

  const { data: weekBreakdown } = await supabase
    .from('games')
    .select('week, season_type')
    .order('week', { ascending: true });

  const weekStats = {};
  if (weekBreakdown) {
    weekBreakdown.forEach(game => {
      const key = `${game.season_type || 'regular'} Week ${game.week}`;
      weekStats[key] = (weekStats[key] || 0) + 1;
    });
  }

  console.log(`\n📊 Total games in database: ${gameCount?.length || 0}`);
  console.log('\n📅 Games by Week:');
  Object.entries(weekStats).forEach(([week, count]) => {
    console.log(`   ${week}: ${count} games`);
  });

  // Show sample games
  const { data: sampleGames } = await supabase
    .from('games')
    .select('week, game_time, away_team, home_team, network, is_primetime')
    .order('game_time', { ascending: true })
    .limit(5);

  console.log('\n🏈 Sample Games:');
  if (sampleGames) {
    sampleGames.forEach(game => {
      const primetime = game.is_primetime ? '⭐' : '';
      console.log(`   Week ${game.week}: ${game.away_team} @ ${game.home_team} on ${game.network} ${primetime}`);
    });
  }

  console.log('\n✨ Full 2025 NFL Season Import Complete!');
  console.log('   - Regular Season: Weeks 1-18');
  console.log('   - Playoffs: Wild Card, Divisional, Conference, Super Bowl');
  console.log('   - International Games: Included where available');
  console.log('   - Ready for predictions and analysis!\n');
}

// Run the import
console.log('Starting full 2025 NFL season import...\n');
fetchFullSeason().catch(console.error);