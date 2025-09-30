#!/usr/bin/env node

/**
 * Add missing historical NFL teams using service role key to bypass RLS
 */

import { createClient } from "@supabase/supabase-js";

const supabaseUrl =
  process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
// Try to use service role key if available, fallback to anon key
const supabaseKey =
  process.env.SUPABASE_SERVICE_ROLE_KEY ||
  process.env.VITE_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

const missingTeams = [
  { team_id: "LA" }, // Los Angeles Rams (historical)
  { team_id: "OAK" }, // Oakland Raiders (historical)
  { team_id: "SD" }, // San Diego Chargers (historical)
  { team_id: "STL" }, // St. Louis Rams (historical)
];

async function addMissingTeams() {
  console.log("🏈 Adding Missing Historical NFL Teams");
  console.log("====================================\n");

  try {
    console.log("📤 Adding missing teams: LA, OAK, SD, STL");

    const { data, error } = await supabase
      .from("nfl_teams")
      .upsert(missingTeams, { onConflict: "team_id" })
      .select();

    if (error) {
      console.error("❌ Error adding teams:", error);

      console.log("\n📋 Please run this SQL manually in Supabase SQL Editor:");
      console.log("\n```sql");
      console.log("INSERT INTO nfl_teams (team_id) VALUES");
      console.log("  ('LA'),   -- Los Angeles Rams (historical)");
      console.log("  ('OAK'),  -- Oakland Raiders (historical)");
      console.log("  ('SD'),   -- San Diego Chargers (historical)");
      console.log("  ('STL')   -- St. Louis Rams (historical)");
      console.log("ON CONFLICT (team_id) DO NOTHING;");
      console.log("```");
      return false;
    }

    console.log(`✅ Successfully added ${data?.length || 0} missing teams`);

    // Verify total count
    const { data: allTeams, error: countError } = await supabase
      .from("nfl_teams")
      .select("team_id", { count: "exact" });

    if (!countError) {
      console.log(`🔍 Total teams in database: ${allTeams.length}`);

      // Check if we have all the required teams
      const requiredTeams = ["LA", "OAK", "SD", "STL"];
      const existingTeamIds = allTeams.map((t) => t.team_id);
      const stillMissing = requiredTeams.filter(
        (t) => !existingTeamIds.includes(t)
      );

      if (stillMissing.length === 0) {
        console.log("✅ All required historical teams are now present!");
        console.log("\n🚀 You can now re-run the games loading script:");
        console.log("   python3 scripts/load_historical_games_simple.py");
      } else {
        console.log(`❌ Still missing: ${stillMissing.join(", ")}`);
      }
    }

    return true;
  } catch (error) {
    console.error("❌ Unexpected error:", error);
    return false;
  }
}

addMissingTeams().then((success) => {
  process.exit(success ? 0 : 1);
});
