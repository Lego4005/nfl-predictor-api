#!/usr/bin/env node

import { createClient } from "@supabase/supabase-js";

// Use the environment variables from .env
const supabaseUrl = "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

async function debugGamesAPI() {
  console.log("🔍 Debugging Games API Response...\n");

  try {
    // Test the exact same query the API uses
    const { data: gamesData, error } = await supabase
      .from("games")
      .select(
        `
        id,
        home_team,
        away_team,
        game_time,
        status,
        week,
        season,
        home_score,
        away_score,
        quarter,
        time_remaining
      `
      )
      .order("game_time", { ascending: true });

    if (error) {
      console.error("❌ API Error:", error.message);
      return;
    }

    console.log(`📊 Total games returned: ${gamesData?.length || 0}`);

    if (gamesData && gamesData.length > 0) {
      // Show first few games structure
      console.log("\n📋 Sample game structure:");
      console.log(JSON.stringify(gamesData[0], null, 2));

      // Week distribution
      const weekDistribution = gamesData.reduce((acc, game) => {
        const week = game.week || "null";
        acc[week] = (acc[week] || 0) + 1;
        return acc;
      }, {});

      console.log("\n📅 Games by week:");
      Object.entries(weekDistribution)
        .sort(([a], [b]) => {
          if (a === "null") return 1;
          if (b === "null") return -1;
          return parseInt(a) - parseInt(b);
        })
        .forEach(([week, count]) => {
          console.log(`   Week ${week}: ${count} games`);
        });

      // Current week games (Week 4)
      const week4Games = gamesData.filter((game) => game.week === 4);
      console.log(`\n🎯 Week 4 games: ${week4Games.length}`);

      if (week4Games.length > 0) {
        console.log("📝 Week 4 sample:");
        week4Games.slice(0, 3).forEach((game) => {
          console.log(
            `   ${game.away_team} @ ${game.home_team} - Week ${game.week}, Status: ${game.status}`
          );
        });
      }

      // Status distribution
      const statusDistribution = gamesData.reduce((acc, game) => {
        const status = game.status || "null";
        acc[status] = (acc[status] || 0) + 1;
        return acc;
      }, {});

      console.log("\n🔄 Games by status:");
      Object.entries(statusDistribution).forEach(([status, count]) => {
        console.log(`   ${status}: ${count} games`);
      });
    } else {
      console.log("❌ No games returned from API");
    }
  } catch (error) {
    console.error("❌ Debug failed:", error.message);
  }
}

debugGamesAPI();
