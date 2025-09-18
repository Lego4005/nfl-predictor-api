#!/usr/bin/env node

/**
 * Database Migration Runner
 * Runs SQL migration files against Supabase database
 */

import fs from 'fs/promises';
import path from 'path';
import { supabase } from '../src/services/supabaseClientNode.js';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const packageJson = require('../package.json');

const MIGRATIONS_DIR = './src/database/migrations';

async function main() {
  console.log(`\n🗄️  NFL Predictor Database Migration Runner v${packageJson.version}\n`);

  try {
    // Get all migration files
    const migrationFiles = await getMigrationFiles();

    if (migrationFiles.length === 0) {
      console.log('⚠️  No migration files found');
      return;
    }

    console.log(`📁 Found ${migrationFiles.length} migration files:\n`);
    migrationFiles.forEach(file => {
      console.log(`   📄 ${file}`);
    });

    // Run migrations in order
    console.log('\n🚀 Running migrations...\n');

    for (const file of migrationFiles) {
      await runMigration(file);
    }

    console.log('\n✅ All migrations completed successfully!\n');

  } catch (error) {
    console.error('\n❌ Migration failed:', error.message);
    process.exit(1);
  }
}

/**
 * Get migration files in order
 */
async function getMigrationFiles() {
  try {
    const files = await fs.readdir(MIGRATIONS_DIR);

    return files
      .filter(file => file.endsWith('.sql'))
      .sort(); // Sort by filename (numbered files will be in correct order)
  } catch (error) {
    console.error('Error reading migrations directory:', error);
    return [];
  }
}

/**
 * Run a single migration file
 */
async function runMigration(filename) {
  const filePath = path.join(MIGRATIONS_DIR, filename);

  try {
    console.log(`🔧 Running ${filename}...`);

    // Read the SQL file
    const sql = await fs.readFile(filePath, 'utf8');

    // Execute the SQL
    const { error } = await supabase.rpc('exec_sql', { sql_query: sql });

    if (error) {
      // If exec_sql RPC doesn't exist, try direct query
      if (error.message.includes('function exec_sql')) {
        // Split by semicolons and execute each statement
        const statements = sql
          .split(';')
          .map(stmt => stmt.trim())
          .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));

        for (const statement of statements) {
          const { error: stmtError } = await supabase.rpc('exec', { sql: statement });
          if (stmtError && !stmtError.message.includes('already exists')) {
            console.warn(`   ⚠️  Warning in ${filename}: ${stmtError.message}`);
          }
        }
      } else {
        throw error;
      }
    }

    console.log(`   ✅ ${filename} completed`);

  } catch (error) {
    console.error(`   ❌ Failed to run ${filename}:`, error.message);
    throw error;
  }
}

// Handle uncaught errors
process.on('unhandledRejection', (error) => {
  console.error('\n❌ Unhandled promise rejection:', error);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error('\n❌ Uncaught exception:', error);
  process.exit(1);
});

// Run the migration script
main().catch(error => {
  console.error('\n❌ Migration script failed:', error.message);
  process.exit(1);
});