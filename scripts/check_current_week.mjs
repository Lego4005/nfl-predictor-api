#!/usr/bin/env node

import { createClient } from "@supabase/supabase-js";

// Use the environment variables from .env
const supabaseUrl = "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

// Calculate current NFL week (assuming 2025 season started September 5th)
function getCurrentNFLWeek() {
  const seasonStart = new Date("2025-09-05"); // First Thursday of September 2025
  const now = new Date("2025-09-29"); // Current date from user context

  const diffTime = now.getTime() - seasonStart.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  const week = Math.ceil(diffDays / 7);

  return Math.max(1, Math.min(18, week)); // NFL has 18 weeks
}

async function showCurrentWeekGames() {
  console.log("🏈 NFL Current Week Games Analysis\n");

  const currentWeek = getCurrentNFLWeek();
  console.log(`📅 Current date: September 29, 2025`);
  console.log(`🎯 Current NFL Week: ${currentWeek}\n`);

  try {
    // Get games for current week only, no duplicates
    const { data: currentGames, error } = await supabase
      .from("games")
      .select("id, home_team, away_team, game_time, status, week, season")
      .eq("season", 2025)
      .eq("week", currentWeek)
      .order("game_time", { ascending: true });

    if (error) {
      console.error("❌ Error fetching current week games:", error.message);
      return;
    }

    console.log(`🎮 Week ${currentWeek} Games (should be ~16 games):`);
    console.log(`📊 Found ${currentGames?.length || 0} games\n`);

    if (currentGames && currentGames.length > 0) {
      // Organize by NFL game days according to project specifications
      const gamesByDay = {
        Thursday: [],
        "Sunday Early": [],
        "Sunday Late": [],
        "Sunday Night": [],
        "Monday Night": [],
      };

      currentGames.forEach((game) => {
        const gameTime = new Date(game.game_time);
        const dayOfWeek = gameTime.getDay(); // 0=Sunday, 1=Monday, 4=Thursday
        const hour = gameTime.getHours();

        if (dayOfWeek === 4) {
          // Thursday
          gamesByDay["Thursday"].push(game);
        } else if (dayOfWeek === 0) {
          // Sunday
          if (hour < 16) {
            gamesByDay["Sunday Early"].push(game);
          } else if (hour >= 20) {
            gamesByDay["Sunday Night"].push(game);
          } else {
            gamesByDay["Sunday Late"].push(game);
          }
        } else if (dayOfWeek === 1) {
          // Monday
          gamesByDay["Monday Night"].push(game);
        }
      });

      // Display games organized by day
      Object.entries(gamesByDay).forEach(([day, games]) => {
        if (games.length > 0) {
          console.log(`📺 ${day} (${games.length} games):`);
          games.forEach((game) => {
            const gameTime = new Date(game.game_time);
            const timeStr = gameTime.toLocaleTimeString("en-US", {
              hour: "numeric",
              minute: "2-digit",
              timeZone: "America/New_York",
            });
            const dateStr = gameTime.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
            console.log(
              `   ${game.away_team} @ ${game.home_team} - ${dateStr} ${timeStr} [${game.status}]`
            );
          });
          console.log("");
        }
      });

      // Check for potential duplicates in this week
      const gameSignatures = new Set();
      const duplicatesThisWeek = [];

      currentGames.forEach((game) => {
        const signature = `${game.away_team}-${game.home_team}`;
        if (gameSignatures.has(signature)) {
          duplicatesThisWeek.push(signature);
        }
        gameSignatures.add(signature);
      });

      if (duplicatesThisWeek.length > 0) {
        console.log("⚠️ Duplicate games found in current week:");
        duplicatesThisWeek.forEach((dup) => console.log(`   ${dup}`));
      } else {
        console.log("✅ No duplicates in current week");
      }
    } else {
      console.log("❌ No games found for current week");
    }

    // Get a reasonable range of games around current date
    const weekStart = new Date("2025-09-25"); // Thursday before
    const weekEnd = new Date("2025-10-01"); // Wednesday after

    const { data: dateRangeGames, error: rangeError } = await supabase
      .from("games")
      .select("id, home_team, away_team, game_time, status, week, season")
      .eq("season", 2025)
      .gte("game_time", weekStart.toISOString())
      .lte("game_time", weekEnd.toISOString())
      .order("game_time", { ascending: true });

    if (!rangeError && dateRangeGames) {
      console.log(
        `\n📆 Games in date range (Sep 25 - Oct 1, 2025): ${dateRangeGames.length}`
      );
      dateRangeGames.forEach((game) => {
        const gameTime = new Date(game.game_time);
        const timeStr = gameTime.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        });
        console.log(
          `   ${game.away_team} @ ${game.home_team} - ${timeStr} (Week ${game.week}) [${game.status}]`
        );
      });
    }
  } catch (error) {
    console.error("❌ Analysis failed:", error.message);
  }
}

showCurrentWeekGames();
