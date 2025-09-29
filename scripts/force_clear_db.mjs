#!/usr/bin/env node

/**
 * Force Clear All Database Tables
 * Completely wipes all tables for fresh start
 */

import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";

// Load environment variables
dotenv.config();

const supabaseUrl =
  process.env.VITE_SUPABASE_URL || "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  process.env.VITE_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

async function forceDeleteAll() {
  console.log("🗑️  FORCE DELETING ALL DATA...");
  console.log("⚠️  This will permanently delete everything!\n");

  try {
    // Use raw SQL to delete everything
    console.log("Executing SQL TRUNCATE commands...");

    // Disable foreign key checks and truncate all tables
    const sqlCommands = [
      "TRUNCATE TABLE predictions RESTART IDENTITY CASCADE;",
      "TRUNCATE TABLE odds_history RESTART IDENTITY CASCADE;",
      "TRUNCATE TABLE user_picks RESTART IDENTITY CASCADE;",
      "TRUNCATE TABLE user_stats RESTART IDENTITY CASCADE;",
      "TRUNCATE TABLE games RESTART IDENTITY CASCADE;",
    ];

    for (const sql of sqlCommands) {
      console.log(`   Executing: ${sql}`);
      const { error } = await supabase.rpc("execute_sql", { sql_command: sql });

      if (error) {
        console.error(`❌ SQL Error: ${error.message}`);
      } else {
        console.log(`✅ Success`);
      }
    }

    console.log("\n✅ All tables cleared!\n");
    return true;
  } catch (error) {
    console.error("❌ Force delete failed:", error.message);

    // Try alternative method - delete by filtering
    console.log("\n🔄 Trying alternative deletion method...");

    const tables = [
      "predictions",
      "odds_history",
      "user_picks",
      "user_stats",
      "games",
    ];

    for (const table of tables) {
      try {
        console.log(`   Deleting all from ${table}...`);

        // Delete everything (using gt filters to match all records)
        const { error } = await supabase
          .from(table)
          .delete()
          .gt("created_at", "1900-01-01");

        if (error) {
          console.error(`❌ Error deleting from ${table}:`, error.message);
        } else {
          console.log(`✅ Cleared ${table}`);
        }
      } catch (tableError) {
        console.error(`❌ Table ${table} error:`, tableError.message);
      }
    }

    return false;
  }
}

async function verifyEmpty() {
  console.log("🔍 Verifying tables are empty...");

  const tables = [
    "games",
    "predictions",
    "odds_history",
    "user_picks",
    "user_stats",
  ];

  for (const table of tables) {
    try {
      const { count, error } = await supabase
        .from(table)
        .select("*", { count: "exact", head: true });

      if (error) {
        console.error(`❌ Error checking ${table}:`, error.message);
      } else {
        console.log(`   ${table}: ${count} records`);
      }
    } catch (error) {
      console.error(`❌ ${table} check failed:`, error.message);
    }
  }
}

async function main() {
  console.log("🧹 FORCE DATABASE CLEAR");
  console.log("======================\n");

  await forceDeleteAll();
  await verifyEmpty();

  console.log("\n✅ Database clearing complete!");
  console.log("Ready to run the reset script again.");
}

main().catch(console.error);
