#!/usr/bin/env node

/**
 * Re-fetch ALL 2025 games from ESPN with correct UTC timestamps
 * This fixes the timezone mess by getting fresh data from ESPN API
 */

import { createClient } from "@supabase/supabase-js";
import fetch from "node-fetch";

const supabaseUrl = process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);
const ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl";

async function fetchAndFixWeek(week) {
  // Use the events API instead of scoreboard to get ALL games (including completed)
  const eventsUrl = `https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/weeks/${week}/events`;

  console.log(`📡 Fetching Week ${week} events...`);
  const eventsResponse = await fetch(eventsUrl);
  const eventsData = await eventsResponse.json();

  if (!eventsData.items || eventsData.items.length === 0) {
    console.log(`⚠️  No games found for Week ${week}`);
    return;
  }

  console.log(`✅ Found ${eventsData.items.length} games for Week ${week}`);

  // Fetch detailed data for each game
  const gamePromises = eventsData.items.map(item => fetch(item.$ref).then(r => r.json()));
  const games = await Promise.all(gamePromises);

  // Transform to scoreboard format
  const data = {
    events: games.map(game => ({
      id: game.id,
      competitions: game.competitions,
      season: { year: 2025 },
      week: { number: week }
    }))
  };

  if (!data.events || data.events.length === 0) {
    console.log(`⚠️  No games found for Week ${week}`);
    return;
  }

  console.log(`✅ Found ${data.events.length} games for Week ${week}`);

  for (const event of data.events) {
    const competition = event.competitions[0];
    const gameDate = competition.date; // This is already in UTC ISO format

    const homeTeam = competition.competitors.find(t => t.homeAway === "home");
    const awayTeam = competition.competitors.find(t => t.homeAway === "away");

    // Handle team abbreviations - might be nested in team object
    const homeAbbr = homeTeam?.team?.abbreviation || homeTeam?.abbreviation;
    const awayAbbr = awayTeam?.team?.abbreviation || awayTeam?.abbreviation;

    // Update the game_time in database with correct UTC timestamp
    const { error } = await supabase
      .from('games')
      .update({
        game_time: gameDate,  // UTC ISO timestamp from ESPN
        updated_at: new Date().toISOString()
      })
      .eq('espn_game_id', event.id);

    if (error) {
      console.error(`❌ Error updating ${awayAbbr} @ ${homeAbbr}:`, error.message);
    } else {
      const utcDate = new Date(gameDate);
      const estDate = new Date(utcDate.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      console.log(`✅ Week ${week}: ${awayAbbr} @ ${homeAbbr}`);
      console.log(`   UTC: ${utcDate.toISOString()}`);
      console.log(`   EST: ${estDate.toLocaleString('en-US', { timeZone: 'America/New_York' })}`);
    }
  }

  // Small delay to be nice to ESPN's API
  await new Promise(resolve => setTimeout(resolve, 500));
}

async function main() {
  console.log('🚀 Starting game time correction...\n');

  // Process all 18 weeks
  for (let week = 1; week <= 18; week++) {
    await fetchAndFixWeek(week);
    console.log(''); // Blank line between weeks
  }

  console.log('✅ All game times updated!');
  console.log('\n📊 Verifying sample games...\n');

  // Verify a few games
  const { data: sampleGames } = await supabase
    .from('games')
    .select('week, home_team, away_team, game_time, timezone')
    .eq('season', 2025)
    .in('week', [1, 2, 3])
    .order('game_time')
    .limit(10);

  if (sampleGames) {
    sampleGames.forEach(game => {
      const utc = new Date(game.game_time);
      const est = new Date(utc.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      console.log(`Week ${game.week}: ${game.away_team} @ ${game.home_team}`);
      console.log(`  Stored: ${game.game_time}`);
      console.log(`  EST: ${est.toLocaleString('en-US', { timeZone: 'America/New_York' })}`);
      console.log('');
    });
  }
}

main().catch(console.error);