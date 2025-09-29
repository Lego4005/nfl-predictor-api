#!/usr/bin/env node

import { createClient } from "@supabase/supabase-js";

// Use the environment variables from .env
const supabaseUrl = "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkDatabaseSchema() {
  console.log("🔍 Checking current database schema...\n");

  try {
    // Test a simple query first to see what columns exist
    console.log("📊 Testing current columns...");
    const { data, error } = await supabase.from("games").select("*").limit(1);

    if (error) {
      console.error("❌ Error querying games table:", error.message);
      return;
    }

    if (data && data.length > 0) {
      console.log("✅ Games table accessible");
      console.log("📋 Available columns:", Object.keys(data[0]));

      // Check if game_id column exists
      if ("game_id" in data[0]) {
        console.log("✅ game_id column exists");
      } else {
        console.log("❌ game_id column is missing");
        console.log("💡 Need to add game_id column to match API expectations");
      }
    } else {
      console.log("⚠️ Games table is empty");
    }

    // Test the problematic query that was failing
    console.log("\n🧪 Testing API query with game_id...");
    const { data: apiData, error: apiError } = await supabase
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
      .order("game_time", { ascending: true })
      .limit(1);

    if (apiError) {
      console.error("❌ API query failed:", apiError.message);
    } else {
      console.log("✅ API query successful with updated column names");
      if (apiData && apiData.length > 0) {
        console.log("📄 Sample game data:", apiData[0]);
      }
    }
  } catch (error) {
    console.error("❌ Database check failed:", error.message);
  }
}

checkDatabaseSchema();
