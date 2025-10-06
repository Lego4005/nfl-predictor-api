#!/usr/bin/env node

import { createClient } from "@supabase/supabase-js";

// Use the environment variables from .env
const supabaseUrl = "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

async function analyzeGamesData() {
  console.log("🔍 Analyzing games data...\n");

  try {
    // Get total count
    const { count: totalCount, error: countError } = await supabase
      .from("games")
      .select("*", { count: "exact", head: true });

    if (countError) {
      console.error("❌ Error getting total count:", countError.message);
      return;
    }

    console.log(`📊 Total games in database: ${totalCount}`);

    // Get breakdown by season
    const { data: seasonData, error: seasonError } = await supabase
      .from("games")
      .select("season")
      .not("season", "is", null);

    if (!seasonError && seasonData) {
      const seasonCounts = seasonData.reduce((acc, game) => {
        acc[game.season] = (acc[game.season] || 0) + 1;
        return acc;
      }, {});

      console.log("\n📅 Games by season:");
      Object.entries(seasonCounts).forEach(([season, count]) => {
        console.log(`   ${season}: ${count} games`);
      });
    }

    // Get breakdown by week for current season (2025)
    const { data: weekData, error: weekError } = await supabase
      .from("games")
      .select("week")
      .eq("season", 2025)
      .not("week", "is", null);

    if (!weekError && weekData) {
      const weekCounts = weekData.reduce((acc, game) => {
        acc[game.week] = (acc[game.week] || 0) + 1;
        return acc;
      }, {});

      console.log("\n🏈 2025 Season - Games by week:");
      Object.entries(weekCounts)
        .sort(([a], [b]) => parseInt(a) - parseInt(b))
        .forEach(([week, count]) => {
          console.log(`   Week ${week}: ${count} games`);
        });
    }

    // Get recent games sample
    const { data: recentGames, error: recentError } = await supabase
      .from("games")
      .select("home_team, away_team, game_time, status, week, season")
      .order("game_time", { ascending: false })
      .limit(10);

    if (!recentError && recentGames) {
      console.log("\n📝 Most recent 10 games:");
      recentGames.forEach((game, i) => {
        const gameTime = new Date(game.game_time);
        const timeStr = gameTime.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        });
        console.log(
          `   ${i + 1}. ${game.away_team} @ ${game.home_team} - ${timeStr} (Week ${game.week}, ${game.season}) [${game.status}]`
        );
      });
    }

    // Check for duplicates or unusual patterns
    const { data: duplicateCheck, error: dupError } = await supabase
      .from("games")
      .select("home_team, away_team, game_time, season, week")
      .order("game_time", { ascending: true })
      .limit(50);

    if (!dupError && duplicateCheck) {
      const gameKeys = new Set();
      const duplicates = [];

      duplicateCheck.forEach((game) => {
        const key = `${game.season}-W${game.week}-${game.away_team}-${game.home_team}`;
        if (gameKeys.has(key)) {
          duplicates.push(key);
        }
        gameKeys.add(key);
      });

      if (duplicates.length > 0) {
        console.log("\n⚠️ Potential duplicates found:");
        duplicates.forEach((dup) => console.log(`   ${dup}`));
      } else {
        console.log("\n✅ No obvious duplicates in sample data");
      }
    }
  } catch (error) {
    console.error("❌ Analysis failed:", error.message);
  }
}

analyzeGamesData();
