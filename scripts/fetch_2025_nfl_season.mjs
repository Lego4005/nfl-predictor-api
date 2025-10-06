#!/usr/bin/env node

/**
 * Fetch Complete 2025 NFL Season Data from ESPN
 * Gets all past weeks we missed and future games, stores them in Supabase
 */

import { createClient } from "@supabase/supabase-js";
import fetch from "node-fetch";

// Supabase configuration
const supabaseUrl =
  process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  process.env.VITE_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

// ESPN API configuration
const ESPN_BASE_URL =
  "https://site.api.espn.com/apis/site/v2/sports/football/nfl";
const CURRENT_SEASON = 2025;
const TOTAL_WEEKS = 18; // NFL regular season weeks

/**
 * Add delay between API calls to be respectful to ESPN's servers
 */
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Fetch ESPN scoreboard data for a specific week
 */
async function fetchESPNWeekData(year, week) {
  const url = `${ESPN_BASE_URL}/scoreboard?seasontype=2&week=${week}&year=${year}`;

  try {
    console.log(`📡 Fetching ESPN data for ${year} Week ${week}...`);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(
        `ESPN API request failed: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    console.log(`✅ Found ${data.events?.length || 0} games for Week ${week}`);
    return data;
  } catch (error) {
    console.error(`❌ Error fetching Week ${week} data:`, error.message);
    throw error;
  }
}

/**
 * Process ESPN game data into Supabase format
 */
function processESPNGame(espnGame) {
  const competition = espnGame.competitions[0];
  const homeTeam = competition.competitors.find(
    (team) => team.homeAway === "home"
  );
  const awayTeam = competition.competitors.find(
    (team) => team.homeAway === "away"
  );

  // Determine winner
  let winner = null;
  if (espnGame.status.type.completed) {
    const winningTeam = competition.competitors.find((team) => team.winner);
    winner = winningTeam ? winningTeam.team.abbreviation : null;
  }

  // Extract TV network from broadcasts
  let network = "TBD";
  if (competition.broadcasts && competition.broadcasts.length > 0) {
    const broadcastNames = competition.broadcasts[0].names;
    if (broadcastNames && broadcastNames.length > 0) {
      network = broadcastNames[0];
    }
  }

  // Map ESPN status to our format
  let status = "scheduled";
  if (espnGame.status.type.completed) {
    status = "final";
  } else if (espnGame.status.type.state === "in") {
    status = "live";
  }

  // Format game time
  const gameTime = new Date(competition.date).toISOString();

  return {
    espn_game_id: espnGame.id,
    season: espnGame.season.year,
    week: espnGame.week.number,
    home_team: homeTeam?.team.abbreviation || "TBD",
    away_team: awayTeam?.team.abbreviation || "TBD",
    home_score: homeTeam?.score ? parseInt(homeTeam.score) : null,
    away_score: awayTeam?.score ? parseInt(awayTeam.score) : null,
    status,
    game_time: gameTime,
    venue: competition.venue?.fullName || "TBD",
    venue_city: competition.venue?.address?.city || "TBD",
    venue_state: competition.venue?.address?.state || "TBD",
    network,
    // winner field removed since column doesn't exist yet
    temperature: espnGame.weather?.temperature || null,
    weather_data: espnGame.weather ? JSON.stringify(espnGame.weather) : null,
    attendance: competition.attendance || null,
    season_type: "regular",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

/**
 * Store games in Supabase database
 */
async function storeGamesInDatabase(games) {
  if (games.length === 0) {
    console.log("📝 No games to store");
    return { stored: 0, updated: 0, errors: 0 };
  }

  let stored = 0;
  let updated = 0;
  let errors = 0;

  console.log(`💾 Storing ${games.length} games in database...`);

  for (const game of games) {
    try {
      // Check if game already exists
      const { data: existing } = await supabase
        .from("games")
        .select("id, status, home_score, away_score")
        .eq("espn_game_id", game.espn_game_id)
        .single();

      if (existing) {
        // Update existing game
        const { error: updateError } = await supabase
          .from("games")
          .update({
            ...game,
            updated_at: new Date().toISOString(),
          })
          .eq("espn_game_id", game.espn_game_id);

        if (updateError) {
          console.error(
            `❌ Error updating game ${game.espn_game_id}:`,
            updateError.message
          );
          errors++;
        } else {
          console.log(
            `🔄 Updated: ${game.away_team} @ ${game.home_team} (Week ${game.week})`
          );
          updated++;
        }
      } else {
        // Insert new game
        const { error: insertError } = await supabase
          .from("games")
          .insert(game);

        if (insertError) {
          console.error(
            `❌ Error inserting game ${game.espn_game_id}:`,
            insertError.message
          );
          errors++;
        } else {
          console.log(
            `➕ Added: ${game.away_team} @ ${game.home_team} (Week ${game.week})`
          );
          stored++;
        }
      }

      // Small delay to avoid overwhelming the database
      await delay(50);
    } catch (error) {
      console.error(
        `❌ Database error for game ${game.espn_game_id}:`,
        error.message
      );
      errors++;
    }
  }

  return { stored, updated, errors };
}

/**
 * Main function to fetch and store complete 2025 season
 */
async function fetchComplete2025Season() {
  console.log("🏈 Starting Complete 2025 NFL Season Data Fetch");
  console.log("=".repeat(60));

  const results = {
    totalGames: 0,
    stored: 0,
    updated: 0,
    errors: 0,
    weekResults: [],
  };

  try {
    // Fetch all weeks (1-18 for regular season)
    for (let week = 1; week <= TOTAL_WEEKS; week++) {
      try {
        console.log(`\n📅 Processing Week ${week}...`);

        // Fetch ESPN data for this week
        const espnData = await fetchESPNWeekData(CURRENT_SEASON, week);

        if (!espnData.events || espnData.events.length === 0) {
          console.log(`⚠️  No games found for Week ${week}`);
          continue;
        }

        // Process games
        const processedGames = espnData.events.map(processESPNGame);

        // Store in database
        const weekResults = await storeGamesInDatabase(processedGames);

        // Update totals
        results.totalGames += processedGames.length;
        results.stored += weekResults.stored;
        results.updated += weekResults.updated;
        results.errors += weekResults.errors;

        results.weekResults.push({
          week,
          games: processedGames.length,
          ...weekResults,
        });

        console.log(
          `✅ Week ${week} complete: ${processedGames.length} games, ${weekResults.stored} new, ${weekResults.updated} updated`
        );

        // Delay between weeks to be respectful to ESPN's API
        await delay(1000);
      } catch (error) {
        console.error(`❌ Failed to process Week ${week}:`, error.message);
        results.errors++;
      }
    }

    // Print final summary
    console.log("\n" + "=".repeat(60));
    console.log("🎉 2025 NFL Season Data Fetch Complete!");
    console.log("=".repeat(60));
    console.log(`📊 Total Games Processed: ${results.totalGames}`);
    console.log(`➕ New Games Added: ${results.stored}`);
    console.log(`🔄 Games Updated: ${results.updated}`);
    console.log(`❌ Errors: ${results.errors}`);

    console.log("\n📈 Week-by-Week Breakdown:");
    results.weekResults.forEach((week) => {
      const status = week.games > 0 ? "✅" : "⚠️";
      console.log(
        `   ${status} Week ${week.week}: ${week.games} games (${week.stored} new, ${week.updated} updated)`
      );
    });

    // Verify final database state
    console.log("\n🔍 Verifying database state...");
    const { data: finalCount, error: countError } = await supabase
      .from("games")
      .select("week", { count: "exact" })
      .eq("season", CURRENT_SEASON);

    if (!countError) {
      console.log(`✅ Total games in database for 2025: ${finalCount.length}`);

      // Show games by week
      const weekCounts = {};
      finalCount.forEach((game) => {
        weekCounts[game.week] = (weekCounts[game.week] || 0) + 1;
      });

      console.log("📅 Games per week in database:");
      for (let week = 1; week <= TOTAL_WEEKS; week++) {
        const count = weekCounts[week] || 0;
        const status = count > 0 ? "✅" : "❌";
        console.log(`   ${status} Week ${week}: ${count} games`);
      }
    }
  } catch (error) {
    console.error("💥 Fatal error during season fetch:", error);
    process.exit(1);
  }
}

// Run the script
fetchComplete2025Season()
  .then(() => {
    console.log("\n🎊 Script completed successfully!");
    process.exit(0);
  })
  .catch((error) => {
    console.error("💀 Script failed:", error);
    process.exit(1);
  });
