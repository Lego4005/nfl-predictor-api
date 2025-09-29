#!/usr/bin/env node

/**
 * Clear Database and Reset for 2025 NFL Season
 * This script will:
 * 1. Clear all existing games and related data
 * 2. Fetch fresh 2025 NFL schedule from ESPN
 * 3. Populate with correct game times and data
 */

import { createClient } from "@supabase/supabase-js";
import axios from "axios";
import dotenv from "dotenv";

// Load environment variables
dotenv.config();

const supabaseUrl =
  process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  process.env.VITE_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

async function clearDatabase() {
  console.log("🗑️  Clearing existing database...");

  try {
    // Clear in order due to foreign key constraints
    const tables = ["predictions", "odds_history", "user_picks", "games"];

    for (const table of tables) {
      console.log(`   Clearing ${table}...`);
      const { error } = await supabase
        .from(table)
        .delete()
        .neq("id", "impossible-id");

      if (error) {
        console.error(`❌ Error clearing ${table}:`, error.message);
      } else {
        console.log(`✅ Cleared ${table}`);
      }
    }

    console.log("✅ Database cleared successfully\n");
    return true;
  } catch (error) {
    console.error("❌ Error clearing database:", error.message);
    return false;
  }
}

async function fetch2025Schedule() {
  console.log("📡 Fetching 2025 NFL Schedule from ESPN...");

  try {
    // Fetch current scoreboard (this will have upcoming 2025 games)
    const response = await axios.get(
      "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    );
    const events = response.data.events || [];

    console.log(`   Found ${events.length} games from ESPN`);

    // Also fetch by weeks to get full season
    const allGames = [...events];

    // Fetch weeks 1-18 for 2025 season
    for (let week = 1; week <= 18; week++) {
      try {
        console.log(`   Fetching Week ${week}...`);
        const weekResponse = await axios.get(
          `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week=${week}&year=2025`
        );
        const weekEvents = weekResponse.data.events || [];

        // Add new games (avoid duplicates)
        for (const event of weekEvents) {
          if (!allGames.find((g) => g.id === event.id)) {
            allGames.push(event);
          }
        }

        // Small delay to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 200));
      } catch (weekError) {
        console.log(
          `   ⚠️  Could not fetch Week ${week}: ${weekError.message}`
        );
      }
    }

    console.log(`📊 Total games collected: ${allGames.length}`);
    return allGames;
  } catch (error) {
    console.error("❌ Error fetching schedule:", error.message);
    return [];
  }
}

function parseESPNGame(event) {
  try {
    const competition = event.competitions[0];
    const homeTeam = competition.competitors.find((c) => c.homeAway === "home");
    const awayTeam = competition.competitors.find((c) => c.homeAway === "away");

    // Parse date properly
    const gameDate = new Date(event.date);

    // Extract week and season from event
    const season = event.season?.year || 2025;
    const week = event.week?.number || 1;

    // Map status
    const statusMap = {
      STATUS_SCHEDULED: "scheduled",
      STATUS_IN_PROGRESS: "live",
      STATUS_FINAL: "final",
      STATUS_POSTPONED: "postponed",
    };

    const status = statusMap[competition.status.type.name] || "scheduled";

    // Get venue info
    const venue = competition.venue || {};

    return {
      espn_game_id: event.id,
      home_team: homeTeam.team.abbreviation,
      away_team: awayTeam.team.abbreviation,
      home_score: parseInt(homeTeam.score) || 0,
      away_score: parseInt(awayTeam.score) || 0,
      game_time: gameDate.toISOString(),
      week: week,
      season: season,
      season_type: "regular",
      status: status,
      quarter: competition.status.period || null,
      time_remaining: competition.status.displayClock || null,
      venue: venue.fullName || null,
      venue_city: venue.address?.city || null,
      venue_state: venue.address?.state || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  } catch (error) {
    console.error("Error parsing game:", error.message);
    return null;
  }
}

async function insertGames(games) {
  console.log(`💾 Inserting ${games.length} games into database...`);

  let inserted = 0;
  let errors = 0;

  for (const game of games) {
    try {
      const { error } = await supabase.from("games").insert(game);

      if (error) {
        console.error(
          `❌ Error inserting game ${game.espn_game_id}:`,
          error.message
        );
        errors++;
      } else {
        console.log(
          `✅ Inserted: ${game.away_team} @ ${game.home_team} (Week ${game.week})`
        );
        inserted++;
      }

      // Small delay to avoid overwhelming the database
      await new Promise((resolve) => setTimeout(resolve, 50));
    } catch (error) {
      console.error(`❌ Insert error:`, error.message);
      errors++;
    }
  }

  console.log(`\n📊 Insert Summary:`);
  console.log(`   Inserted: ${inserted}`);
  console.log(`   Errors: ${errors}`);

  return { inserted, errors };
}

async function verifyData() {
  console.log("\n🔍 Verifying inserted data...");

  try {
    // Count total games
    const { count: totalCount, error: countError } = await supabase
      .from("games")
      .select("*", { count: "exact", head: true });

    if (countError) {
      console.error("❌ Error counting games:", countError.message);
      return;
    }

    console.log(`📊 Total games in database: ${totalCount}`);

    // Get breakdown by week
    const { data: weekData, error: weekError } = await supabase
      .from("games")
      .select("week")
      .eq("season", 2025);

    if (!weekError && weekData) {
      const weekCounts = weekData.reduce((acc, game) => {
        acc[game.week] = (acc[game.week] || 0) + 1;
        return acc;
      }, {});

      console.log("\n📅 Games by week:");
      for (let week = 1; week <= 18; week++) {
        const count = weekCounts[week] || 0;
        console.log(`   Week ${week}: ${count} games`);
      }
    }

    // Show sample upcoming games
    const { data: upcomingGames, error: upcomingError } = await supabase
      .from("games")
      .select("*")
      .eq("season", 2025)
      .eq("status", "scheduled")
      .order("game_time", { ascending: true })
      .limit(5);

    if (!upcomingError && upcomingGames) {
      console.log("\n🎮 Next 5 upcoming games:");
      upcomingGames.forEach((game) => {
        const gameTime = new Date(game.game_time);
        console.log(
          `   ${game.away_team} @ ${game.home_team} - ${gameTime.toLocaleDateString()} ${gameTime.toLocaleTimeString()}`
        );
      });
    }
  } catch (error) {
    console.error("❌ Verification error:", error.message);
  }
}

async function main() {
  console.log("🏈 NFL 2025 Database Reset Script");
  console.log("==================================\n");

  try {
    // Step 1: Clear existing data
    const cleared = await clearDatabase();
    if (!cleared) {
      console.error("❌ Failed to clear database. Stopping.");
      return;
    }

    // Step 2: Fetch new 2025 schedule
    const rawGames = await fetch2025Schedule();
    if (rawGames.length === 0) {
      console.error("❌ No games fetched. Stopping.");
      return;
    }

    // Step 3: Parse games
    console.log("🔄 Parsing game data...");
    const parsedGames = rawGames.map(parseESPNGame).filter(Boolean);
    console.log(`   Parsed ${parsedGames.length} valid games`);

    // Step 4: Insert into database
    const { inserted, errors } = await insertGames(parsedGames);

    // Step 5: Verify data
    await verifyData();

    console.log("\n🎉 Database reset complete!");
    console.log(`   Successfully inserted ${inserted} games`);
    console.log(`   Errors: ${errors}`);

    if (errors === 0) {
      console.log(
        "\n✅ All games loaded successfully! Ready for 2025 NFL season."
      );
    } else {
      console.log("\n⚠️  Some errors occurred. Check logs above.");
    }
  } catch (error) {
    console.error("❌ Script failed:", error.message);
  }
}

// Run the script
main().catch(console.error);
