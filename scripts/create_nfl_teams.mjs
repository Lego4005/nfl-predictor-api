#!/usr/bin/env node

/**
 * Create and populate NFL teams table
 * Required before loading games data due to foreign key constraints
 */

import { createClient } from "@supabase/supabase-js";

// Supabase configuration
const supabaseUrl =
  process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  process.env.VITE_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

// NFL Teams data
const teams = [
  {
    team_id: "ARI",
    team_name: "Cardinals",
    team_city: "Arizona",
    team_full_name: "Arizona Cardinals",
    conference: "NFC",
    division: "West",
    // established_year: 1898,
  },
  {
    team_id: "ATL",
    team_name: "Falcons",
    team_city: "Atlanta",
    team_full_name: "Atlanta Falcons",
    conference: "NFC",
    division: "South",
    // established_year: 1965,
  },
  {
    team_id: "BAL",
    team_name: "Ravens",
    team_city: "Baltimore",
    team_full_name: "Baltimore Ravens",
    conference: "AFC",
    division: "North",
    // established_year: 1996,
  },
  {
    team_id: "BUF",
    team_name: "Bills",
    team_city: "Buffalo",
    team_full_name: "Buffalo Bills",
    conference: "AFC",
    division: "East",
    // established_year: 1960,
  },
  {
    team_id: "CAR",
    team_name: "Panthers",
    team_city: "Carolina",
    team_full_name: "Carolina Panthers",
    conference: "NFC",
    division: "South",
    // established_year: 1993,
  },
  {
    team_id: "CHI",
    team_name: "Bears",
    team_city: "Chicago",
    team_full_name: "Chicago Bears",
    conference: "NFC",
    division: "North",
    // established_year: 1919,
  },
  {
    team_id: "CIN",
    team_name: "Bengals",
    team_city: "Cincinnati",
    team_full_name: "Cincinnati Bengals",
    conference: "AFC",
    division: "North",
    // established_year: 1968,
  },
  {
    team_id: "CLE",
    team_name: "Browns",
    team_city: "Cleveland",
    team_full_name: "Cleveland Browns",
    conference: "AFC",
    division: "North",
    // established_year: 1946,
  },
  {
    team_id: "DAL",
    team_name: "Cowboys",
    team_city: "Dallas",
    team_full_name: "Dallas Cowboys",
    conference: "NFC",
    division: "East",
    // established_year: 1960,
  },
  {
    team_id: "DEN",
    team_name: "Broncos",
    team_city: "Denver",
    team_full_name: "Denver Broncos",
    conference: "AFC",
    division: "West",
    // established_year: 1960,
  },
  {
    team_id: "DET",
    team_name: "Lions",
    team_city: "Detroit",
    team_full_name: "Detroit Lions",
    conference: "NFC",
    division: "North",
    // established_year: 1930,
  },
  {
    team_id: "GB",
    team_name: "Packers",
    team_city: "Green Bay",
    team_full_name: "Green Bay Packers",
    conference: "NFC",
    division: "North",
    // established_year: 1919,
  },
  {
    team_id: "HOU",
    team_name: "Texans",
    team_city: "Houston",
    team_full_name: "Houston Texans",
    conference: "AFC",
    division: "South",
    // established_year: 2002,
  },
  {
    team_id: "IND",
    team_name: "Colts",
    team_city: "Indianapolis",
    team_full_name: "Indianapolis Colts",
    conference: "AFC",
    division: "South",
    // established_year: 1953,
  },
  {
    team_id: "JAX",
    team_name: "Jaguars",
    team_city: "Jacksonville",
    team_full_name: "Jacksonville Jaguars",
    conference: "AFC",
    division: "South",
    // established_year: 1993,
  },
  {
    team_id: "KC",
    team_name: "Chiefs",
    team_city: "Kansas City",
    team_full_name: "Kansas City Chiefs",
    conference: "AFC",
    division: "West",
    // established_year: 1960,
  },
  {
    team_id: "LAR",
    team_name: "Rams",
    team_city: "Los Angeles",
    team_full_name: "Los Angeles Rams",
    conference: "NFC",
    division: "West",
    // established_year: 1936,
  },
  {
    team_id: "LAC",
    team_name: "Chargers",
    team_city: "Los Angeles",
    team_full_name: "Los Angeles Chargers",
    conference: "AFC",
    division: "West",
    // established_year: 1960,
  },
  {
    team_id: "LV",
    team_name: "Raiders",
    team_city: "Las Vegas",
    team_full_name: "Las Vegas Raiders",
    conference: "AFC",
    division: "West",
    // established_year: 1960,
  },
  {
    team_id: "MIA",
    team_name: "Dolphins",
    team_city: "Miami",
    team_full_name: "Miami Dolphins",
    conference: "AFC",
    division: "East",
    // established_year: 1966,
  },
  {
    team_id: "MIN",
    team_name: "Vikings",
    team_city: "Minnesota",
    team_full_name: "Minnesota Vikings",
    conference: "NFC",
    division: "North",
    // established_year: 1961,
  },
  {
    team_id: "NE",
    team_name: "Patriots",
    team_city: "New England",
    team_full_name: "New England Patriots",
    conference: "AFC",
    division: "East",
    // established_year: 1960,
  },
  {
    team_id: "NO",
    team_name: "Saints",
    team_city: "New Orleans",
    team_full_name: "New Orleans Saints",
    conference: "NFC",
    division: "South",
    // established_year: 1967,
  },
  {
    team_id: "NYG",
    team_name: "Giants",
    team_city: "New York",
    team_full_name: "New York Giants",
    conference: "NFC",
    division: "East",
    // established_year: 1925,
  },
  {
    team_id: "NYJ",
    team_name: "Jets",
    team_city: "New York",
    team_full_name: "New York Jets",
    conference: "AFC",
    division: "East",
    // established_year: 1960,
  },
  {
    team_id: "OAK",
    team_name: "Raiders",
    team_city: "Oakland",
    team_full_name: "Oakland Raiders",
    conference: "AFC",
    division: "West",
    // established_year: 1960,
  },
  {
    team_id: "PHI",
    team_name: "Eagles",
    team_city: "Philadelphia",
    team_full_name: "Philadelphia Eagles",
    conference: "NFC",
    division: "East",
    // established_year: 1933,
  },
  {
    team_id: "PIT",
    team_name: "Steelers",
    team_city: "Pittsburgh",
    team_full_name: "Pittsburgh Steelers",
    conference: "AFC",
    division: "North",
    // established_year: 1933,
  },
  {
    team_id: "SD",
    team_name: "Chargers",
    team_city: "San Diego",
    team_full_name: "San Diego Chargers",
    conference: "AFC",
    division: "West",
    // established_year: 1960,
  },
  {
    team_id: "SEA",
    team_name: "Seahawks",
    team_city: "Seattle",
    team_full_name: "Seattle Seahawks",
    conference: "NFC",
    division: "West",
    // established_year: 1976,
  },
  {
    team_id: "SF",
    team_name: "49ers",
    team_city: "San Francisco",
    team_full_name: "San Francisco 49ers",
    conference: "NFC",
    division: "West",
    // established_year: 1946,
  },
  {
    team_id: "STL",
    team_name: "Rams",
    team_city: "St. Louis",
    team_full_name: "St. Louis Rams",
    conference: "NFC",
    division: "West",
    // established_year: 1936,
  },
  {
    team_id: "TB",
    team_name: "Buccaneers",
    team_city: "Tampa Bay",
    team_full_name: "Tampa Bay Buccaneers",
    conference: "NFC",
    division: "South",
    // established_year: 1974,
  },
  {
    team_id: "TEN",
    team_name: "Titans",
    team_city: "Tennessee",
    team_full_name: "Tennessee Titans",
    conference: "AFC",
    division: "South",
    // established_year: 1960,
  },
  {
    team_id: "WAS",
    team_name: "Commanders",
    team_city: "Washington",
    team_full_name: "Washington Commanders",
    conference: "NFC",
    division: "East",
    // established_year: 1932,
  },
];

async function createNflTeams() {
  console.log("🏈 Creating NFL Teams Table");
  console.log("============================\n");

  try {
    // Check if table exists and has data
    console.log("🔍 Checking existing teams...");
    const { data: existingTeams, error: checkError } = await supabase
      .from("nfl_teams")
      .select("team_id", { count: "exact" });

    if (checkError) {
      console.log("📋 Teams table does not exist yet, will create...");
    } else {
      console.log(`✅ Found ${existingTeams.length} existing teams`);
    }

    // Insert teams using upsert
    console.log("📤 Inserting/updating NFL teams...");
    const { data, error } = await supabase
      .from("nfl_teams")
      .upsert(teams, { onConflict: "team_id" });

    if (error) {
      console.error("❌ Error inserting teams:", error);

      // Provide manual SQL instructions
      console.log("\n📋 Please run this SQL manually in Supabase SQL Editor:");
      console.log("\n```sql");
      console.log("-- Create nfl_teams table");
      console.log("CREATE TABLE IF NOT EXISTS nfl_teams (");
      console.log("  team_id VARCHAR(3) PRIMARY KEY,");
      console.log("  team_name VARCHAR(50) NOT NULL,");
      console.log("  team_city VARCHAR(30) NOT NULL,");
      console.log("  team_full_name VARCHAR(80) NOT NULL,");
      console.log(
        "  conference VARCHAR(3) NOT NULL CHECK (conference IN ('AFC', 'NFC')),"
      );
      console.log("  division VARCHAR(10) NOT NULL");
      console.log(");");
      console.log("```");
      console.log("\nThen copy the SQL from scripts/create_nfl_teams.sql");
      return false;
    }

    // Verify insertion
    const { data: verifyData, error: verifyError } = await supabase
      .from("nfl_teams")
      .select("team_id", { count: "exact" });

    if (verifyError) {
      console.error("❌ Error verifying teams:", verifyError);
      return false;
    }

    console.log(
      `✅ Successfully created/updated ${verifyData.length} NFL teams`
    );

    // Show sample teams
    const { data: sampleTeams } = await supabase
      .from("nfl_teams")
      .select("*")
      .limit(5);

    if (sampleTeams) {
      console.log("\n📋 Sample teams:");
      sampleTeams.forEach((team) => {
        console.log(
          `   ${team.team_id}: ${team.team_full_name} (${team.conference} ${team.division})`
        );
      });
    }

    console.log("\n🎉 NFL teams table is ready!");
    console.log("   You can now load the historical games data.");

    return true;
  } catch (error) {
    console.error("❌ Unexpected error:", error);
    return false;
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  createNflTeams().then((success) => {
    process.exit(success ? 0 : 1);
  });
}

export default createNflTeams;
