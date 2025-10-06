#!/usr/bin/env node

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";
const supabase = createClient(supabaseUrl, supabaseKey);

// Just insert the minimal team IDs that are needed
const basicTeams = [
  'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
  'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
  'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
  'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS',
  'OAK', 'SD', 'STL'  // Historical teams
];

async function populateBasicTeams() {
  console.log("🏈 Populating Basic NFL Teams");
  console.log("============================\n");

  try {
    // Insert one by one to handle conflicts gracefully
    let inserted = 0;
    let existing = 0;

    for (const teamId of basicTeams) {
      try {
        const { data, error } = await supabase
          .from('nfl_teams')
          .insert({ team_id: teamId })
          .select();

        if (error) {
          if (error.code === '23505') { // Unique constraint violation
            existing++;
            console.log(`   ✓ ${teamId} already exists`);
          } else {
            console.error(`   ❌ Error inserting ${teamId}:`, error.message);
          }
        } else {
          inserted++;
          console.log(`   ✅ Inserted ${teamId}`);
        }
      } catch (err) {
        console.error(`   ❌ Error with ${teamId}:`, err.message);
      }
    }

    console.log(`\n📊 Summary:`);
    console.log(`   ✅ Inserted: ${inserted} teams`);
    console.log(`   ✓ Already existed: ${existing} teams`);
    console.log(`   🎯 Total: ${inserted + existing} teams ready`);

    // Verify
    const { data: allTeams, error: countError } = await supabase
      .from('nfl_teams')
      .select('team_id', { count: 'exact' });

    if (!countError) {
      console.log(`\n🔍 Verification: ${allTeams.length} total teams in database`);
    }

    return true;
  } catch (error) {
    console.error("❌ Unexpected error:", error);
    return false;
  }
}

populateBasicTeams().then(success => {
  process.exit(success ? 0 : 1);
});