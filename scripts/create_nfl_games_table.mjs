#!/usr/bin/env node

/**
 * Create nfl_games table in Supabase
 * Run this before the Python data loading script
 */

import { createClient } from "@supabase/supabase-js";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Supabase configuration from .env
const supabaseUrl =
  process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  process.env.VITE_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

async function createNflGamesTable() {
  console.log("🏈 Creating NFL Games Table");
  console.log("============================\n");

  try {
    // Test table creation with a simpler approach
    console.log("🔨 Creating nfl_games table...");

    // First, check if table already exists
    try {
      const { data, error } = await supabase
        .from("nfl_games")
        .select("id")
        .limit(1);

      if (!error) {
        console.log("✅ Table nfl_games already exists");
        return true;
      }
    } catch (checkError) {
      console.log("📝 Table does not exist, creating...");
    }

    // Since we can't use RPC, let's provide instructions for manual creation
    console.log(
      "\n📋 Please create the table manually in Supabase SQL Editor:"
    );
    console.log("1. Go to your Supabase dashboard");
    console.log("2. Navigate to SQL Editor");
    console.log("3. Copy and paste the following SQL:\n");

    const sqlPath = path.join(
      __dirname,
      "..",
      "supabase",
      "migrations",
      "032_nfl_games_table.sql"
    );
    try {
      const sql = await fs.readFile(sqlPath, "utf8");
      console.log("```sql");
      console.log(sql);
      console.log("```\n");
    } catch (sqlError) {
      console.log("SQL file not found, here is the table creation script:");
      console.log(`
CREATE TABLE IF NOT EXISTS nfl_games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id VARCHAR(100) UNIQUE NOT NULL,
    season INTEGER,
    week INTEGER, 
    game_type VARCHAR(20),
    game_date DATE,
    game_datetime TIMESTAMP WITH TIME ZONE,
    
    -- Teams
    home_team VARCHAR(10),
    away_team VARCHAR(10),
    home_score INTEGER,
    away_score INTEGER,
    
    -- Game Details
    overtime BOOLEAN DEFAULT false,
    stadium VARCHAR(100),
    roof VARCHAR(20),
    surface VARCHAR(20),
    weather_temperature INTEGER,
    weather_wind_mph INTEGER,
    
    -- Rest and Preparation
    away_rest INTEGER,
    home_rest INTEGER,
    
    -- Betting Lines
    spread_line DECIMAL(5,2),
    away_spread_odds INTEGER,
    home_spread_odds INTEGER,
    total_line DECIMAL(5,2),
    over_odds INTEGER,
    under_odds INTEGER,
    away_moneyline INTEGER,
    home_moneyline INTEGER,
    
    -- Personnel
    away_qb_id VARCHAR(20),
    away_qb_name VARCHAR(100),
    home_qb_id VARCHAR(20),
    home_qb_name VARCHAR(100),
    away_coach VARCHAR(100),
    home_coach VARCHAR(100),
    
    -- Additional Game Info
    div_game BOOLEAN DEFAULT false,
    result INTEGER,
    total INTEGER,
    location VARCHAR(10),
    weekday VARCHAR(15),
    referee VARCHAR(100),
    
    -- Legacy IDs and References
    old_game_id VARCHAR(50),
    gsis VARCHAR(50),
    nfl_detail_id VARCHAR(50),
    pfr VARCHAR(50),
    pff VARCHAR(50),
    espn VARCHAR(50),
    ftn VARCHAR(50),
    stadium_id VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nfl_games_game_id ON nfl_games(game_id);
CREATE INDEX IF NOT EXISTS idx_nfl_games_season_week ON nfl_games(season, week);
CREATE INDEX IF NOT EXISTS idx_nfl_games_teams ON nfl_games(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_nfl_games_date ON nfl_games(game_date);

-- Add Row Level Security (RLS) but allow public read access
ALTER TABLE nfl_games ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access
CREATE POLICY "Public read access" ON nfl_games FOR SELECT USING (true);
      `);
    }

    console.log("4. Run the SQL query");
    console.log("5. Then run the Python data loading script\n");

    return false; // Table not created yet, needs manual creation
  } catch (error) {
    console.error("❌ Error:", error);
    return false;
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  createNflGamesTable().then((success) => {
    if (success) {
      console.log("✅ Table is ready for data loading!");
    } else {
      console.log(
        "⚠️ Please create table manually then run data loading script"
      );
    }
  });
}

export default createNflGamesTable;
