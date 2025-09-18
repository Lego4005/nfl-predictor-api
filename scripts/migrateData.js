#!/usr/bin/env node

/**
 * Data Migration Script
 * Run with: node scripts/migrateData.js [options]
 */

import dataMigrationService from '../src/services/dataMigrationService.js';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const packageJson = require('../package.json');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  status: args.includes('--status'),
  clean: args.includes('--clean'),
  help: args.includes('--help') || args.includes('-h'),
  force: args.includes('--force')
};

async function main() {
  console.log(`\n🏈 NFL Predictor Data Migration Tool v${packageJson.version}\n`);

  if (options.help) {
    showHelp();
    return;
  }

  if (options.status) {
    await showMigrationStatus();
    return;
  }

  if (options.clean) {
    await cleanupData();
    return;
  }

  // Default: run migration
  await runMigration();
}

/**
 * Show help information
 */
function showHelp() {
  console.log(`Usage: node scripts/migrateData.js [options]

Options:
  --status     Show current migration status
  --clean      Clean up all migrated data (WARNING: destructive)
  --force      Force migration even if data exists
  --help, -h   Show this help message

Examples:
  node scripts/migrateData.js              # Run full migration
  node scripts/migrateData.js --status     # Check migration status
  node scripts/migrateData.js --clean      # Clean up data (use with caution)

Description:
  This script migrates historical NFL data from local files to Supabase:
  - NFL team information with colors and logos
  - Historical game data from CSV files
  - Player statistics with vector embeddings
  - Knowledge base entries for betting and NFL rules

The migration includes vector embeddings for semantic search capabilities.
`);
}

/**
 * Show current migration status
 */
async function showMigrationStatus() {
  console.log('📊 Checking migration status...\n');

  try {
    const result = await dataMigrationService.getMigrationStatus();

    if (result.success) {
      const { status } = result;

      console.log('Current Status:');
      console.log(`  📈 Teams in database: ${status.teams}`);
      console.log(`  🏈 Games in database: ${status.games}`);
      console.log(`  🧠 Knowledge base entries: ${status.knowledge}`);

      if (result.migrationLog && result.migrationLog.length > 0) {
        console.log('\nRecent Migration Log:');
        result.migrationLog.forEach(log => {
          console.log(`  ✅ ${log.stage}: ${log.count} items (${new Date(log.timestamp).toLocaleString()})`);
        });
      } else {
        console.log('\n⚠️  No migration history found');
      }

      // Recommendations
      if (status.teams === 0 && status.games === 0) {
        console.log('\n💡 Recommendation: Run full migration with: node scripts/migrateData.js');
      } else if (status.knowledge === 0) {
        console.log('\n💡 Recommendation: Knowledge base is empty, consider running migration to add base knowledge');
      } else {
        console.log('\n✅ Database appears to be populated with migrated data');
      }

    } else {
      console.error('❌ Failed to get migration status:', result.error);
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Error checking status:', error.message);
    process.exit(1);
  }
}

/**
 * Clean up migrated data
 */
async function cleanupData() {
  if (!options.force) {
    console.log('⚠️  WARNING: This will delete all migrated data from Supabase!');
    console.log('   Use --force flag to confirm: node scripts/migrateData.js --clean --force');
    return;
  }

  console.log('🧹 Cleaning up migrated data...\n');

  try {
    const result = await dataMigrationService.cleanupMigrationData();

    if (result.success) {
      console.log('✅ Cleanup completed successfully');
    } else {
      console.error('❌ Cleanup failed:', result.error);
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Error during cleanup:', error.message);
    process.exit(1);
  }
}

/**
 * Run the full migration
 */
async function runMigration() {
  console.log('🚀 Starting data migration to Supabase...\n');

  // Check status first
  const statusResult = await dataMigrationService.getMigrationStatus();
  if (statusResult.success) {
    const { status } = statusResult;
    const hasData = status.teams > 0 || status.games > 0 || status.knowledge > 0;

    if (hasData && !options.force) {
      console.log('⚠️  Database already contains migrated data:');
      console.log(`   Teams: ${status.teams}, Games: ${status.games}, Knowledge: ${status.knowledge}`);
      console.log('\n💡 Use --force flag to migrate anyway, or --status to see details');
      console.log('   Example: node scripts/migrateData.js --force');
      return;
    }
  }

  try {
    const result = await dataMigrationService.migrateAllData();

    if (result.success) {
      console.log('\n🎉 Migration completed successfully!');
      console.log(`⏱️  Total time: ${(result.duration / 1000).toFixed(2)} seconds`);

      // Show summary
      console.log('\nMigration Summary:');
      Object.entries(result.results).forEach(([stage, info]) => {
        const icon = info.success ? '✅' : '❌';
        const message = info.success ? `${info.count} items` : info.error;
        console.log(`  ${icon} ${stage}: ${message}`);
      });

      // Show next steps
      console.log('\n🔍 Next Steps:');
      console.log('  1. Test vector search: node testVectorSearchService.js');
      console.log('  2. Start the development server: npm run dev');
      console.log('  3. Check real-time dashboard at http://localhost:5173');

    } else {
      console.error('\n❌ Migration failed:', result.error);

      if (result.results) {
        console.log('\nPartial Results:');
        Object.entries(result.results).forEach(([stage, info]) => {
          if (info.success) {
            console.log(`  ✅ ${stage}: ${info.count} items migrated`);
          } else {
            console.log(`  ❌ ${stage}: ${info.error}`);
          }
        });
      }

      process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ Unexpected error during migration:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
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

// Run the script
main().catch(error => {
  console.error('\n❌ Script failed:', error.message);
  process.exit(1);
});