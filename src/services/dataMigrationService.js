import fs from 'fs/promises';
import csv from 'csv-parser';
import { createReadStream } from 'fs';
import { supabase } from './supabaseClientNode.js';
import vectorSearchService from './vectorSearchServiceNode.js';
import { NFL_TEAMS } from '../data/nflTeams.js';

/**
 * Data Migration Service
 * Migrates historical data from local files to Supabase with vector embeddings
 */
class DataMigrationService {
  constructor() {
    this.basePath = './data';
    this.migrationLog = [];
  }

  /**
   * Migrate all data from local files to Supabase
   */
  async migrateAllData() {
    console.log('🚀 Starting comprehensive data migration to Supabase...\n');

    const startTime = Date.now();
    const results = {
      teams: { success: false, count: 0, error: null },
      historicalGames: { success: false, count: 0, error: null },
      playerStats: { success: false, count: 0, error: null },
      knowledgeBase: { success: false, count: 0, error: null }
    };

    try {
      // 1. Migrate NFL Teams data
      console.log('📊 Migrating NFL Teams data...');
      results.teams = await this.migrateNFLTeams();

      // 2. Migrate historical games
      console.log('\n🏈 Migrating historical games data...');
      results.historicalGames = await this.migrateHistoricalGames();

      // 3. Migrate player statistics
      console.log('\n👨‍💼 Migrating player statistics...');
      results.playerStats = await this.migratePlayerStats();

      // 4. Create knowledge base entries
      console.log('\n🧠 Creating knowledge base entries...');
      results.knowledgeBase = await this.createKnowledgeBaseEntries();

      const duration = Date.now() - startTime;

      console.log('\n✅ Data migration completed!');
      console.log(`⏱️  Duration: ${(duration / 1000).toFixed(2)}s`);
      console.log(`📈 Results:`);
      console.log(`   Teams: ${results.teams.count} migrated`);
      console.log(`   Games: ${results.historicalGames.count} migrated`);
      console.log(`   Player Stats: ${results.playerStats.count} migrated`);
      console.log(`   Knowledge Base: ${results.knowledgeBase.count} entries`);

      return {
        success: true,
        duration,
        results,
        migrationLog: this.migrationLog
      };

    } catch (error) {
      console.error('❌ Migration failed:', error);
      return {
        success: false,
        error: error.message,
        results,
        migrationLog: this.migrationLog
      };
    }
  }

  /**
   * Migrate NFL Teams data to Supabase
   */
  async migrateNFLTeams() {
    try {
      const teams = Object.values(NFL_TEAMS);
      let migratedCount = 0;

      for (const team of teams) {
        // Check if team already exists
        const { data: existing } = await supabase
          .from('teams')
          .select('id')
          .eq('abbreviation', team.abbreviation.toUpperCase())
          .single();

        if (existing) {
          console.log(`   ⏭️  ${team.city} ${team.name} already exists, skipping...`);
          continue;
        }

        // Insert team data
        const { data, error } = await supabase
          .from('teams')
          .insert({
            abbreviation: team.abbreviation.toUpperCase(),
            name: team.name,
            city: team.city,
            full_name: `${team.city} ${team.name}`,
            conference: team.conference,
            division: team.division,
            primary_color: team.primaryColor,
            secondary_color: team.secondaryColor,
            tertiary_color: team.tertiaryColor,
            logo_url: team.logo,
            gradient: team.gradient,
            created_at: new Date().toISOString()
          })
          .select()
          .single();

        if (error) {
          console.error(`   ❌ Failed to migrate ${team.city} ${team.name}:`, error.message);
          continue;
        }

        // Add team info to knowledge base
        const teamInfo = `${team.city} ${team.name} (${team.abbreviation}) is an NFL team in the ${team.conference} conference, ${team.division} division. Team colors: ${team.primaryColor}, ${team.secondaryColor}. The team plays professional football in the National Football League.`;

        await vectorSearchService.addKnowledge(
          'team_info',
          `${team.city} ${team.name} Team Information`,
          teamInfo,
          null,
          90 // High trust score for official team data
        );

        migratedCount++;
        console.log(`   ✅ Migrated: ${team.city} ${team.name}`);

        // Small delay to avoid overwhelming the database
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      this.migrationLog.push({
        stage: 'NFL Teams',
        count: migratedCount,
        timestamp: new Date().toISOString()
      });

      return {
        success: true,
        count: migratedCount,
        error: null
      };

    } catch (error) {
      console.error('NFL Teams migration failed:', error);
      return {
        success: false,
        count: 0,
        error: error.message
      };
    }
  }

  /**
   * Migrate historical games data
   */
  async migrateHistoricalGames() {
    try {
      const filePath = `${this.basePath}/historical/games/historical_games.csv`;

      // Check if file exists
      try {
        await fs.access(filePath);
      } catch {
        console.log('   ⚠️  Historical games file not found, skipping...');
        return { success: true, count: 0, error: null };
      }

      let migratedCount = 0;
      const batchSize = 50;
      let batch = [];

      return new Promise((resolve) => {
        createReadStream(filePath)
          .pipe(csv())
          .on('data', async (row) => {
            // Transform CSV row to Supabase format
            let gameTime = null;

            // Safe date parsing with validation
            if (row.game_date) {
              try {
                const parsedDate = new Date(row.game_date);
                if (!isNaN(parsedDate.getTime())) {
                  gameTime = parsedDate.toISOString();
                } else {
                  console.warn(`   ⚠️  Invalid date for game ${row.game_id}: ${row.game_date}`);
                  gameTime = new Date().toISOString(); // Fallback to current date
                }
              } catch (error) {
                console.warn(`   ⚠️  Error parsing date for game ${row.game_id}: ${row.game_date}`, error.message);
                gameTime = new Date().toISOString(); // Fallback to current date
              }
            } else {
              gameTime = new Date().toISOString(); // Fallback if no date provided
            }

            // Validate team references exist
            const homeTeam = row.home_team?.trim().toUpperCase();
            const awayTeam = row.away_team?.trim().toUpperCase();

            if (!homeTeam || !awayTeam) {
              console.warn(`   ⚠️  Skipping game ${row.game_id}: Missing team data`);
              return;
            }

            const gameData = {
              espn_game_id: row.game_id,
              home_team: homeTeam,
              away_team: awayTeam,
              home_score: parseInt(row.home_score) || null,
              away_score: parseInt(row.away_score) || null,
              game_time: gameTime,
              week: parseInt(row.week) || null,
              season: parseInt(row.season) || null,
              venue: row.venue || null,
              status: 'final',
              created_at: new Date().toISOString()
            };

            batch.push(gameData);

            if (batch.length >= batchSize) {
              await this.insertGamesBatch(batch);
              migratedCount += batch.length;
              console.log(`   📈 Migrated ${migratedCount} historical games...`);
              batch = [];
            }
          })
          .on('end', async () => {
            // Insert remaining batch
            if (batch.length > 0) {
              await this.insertGamesBatch(batch);
              migratedCount += batch.length;
            }

            this.migrationLog.push({
              stage: 'Historical Games',
              count: migratedCount,
              timestamp: new Date().toISOString()
            });

            resolve({
              success: true,
              count: migratedCount,
              error: null
            });
          })
          .on('error', (error) => {
            console.error('Error reading historical games CSV:', error);
            resolve({
              success: false,
              count: migratedCount,
              error: error.message
            });
          });
      });

    } catch (error) {
      console.error('Historical games migration failed:', error);
      return {
        success: false,
        count: 0,
        error: error.message
      };
    }
  }

  /**
   * Insert games batch into Supabase
   */
  async insertGamesBatch(games) {
    try {
      const { error } = await supabase
        .from('games')
        .insert(games);

      if (error && !error.message.includes('duplicate')) {
        console.error('Batch insert error:', error.message);
      }
    } catch (error) {
      console.error('Batch insert failed:', error);
    }
  }

  /**
   * Migrate player statistics
   */
  async migratePlayerStats() {
    try {
      const filePath = `${this.basePath}/historical/players/historical_player_stats.csv`;

      // Check if file exists
      try {
        await fs.access(filePath);
      } catch {
        console.log('   ⚠️  Player stats file not found, skipping...');
        return { success: true, count: 0, error: null };
      }

      let migratedCount = 0;
      const batchSize = 100;
      let batch = [];

      return new Promise((resolve) => {
        createReadStream(filePath)
          .pipe(csv())
          .on('data', async (row) => {
            // Create knowledge base entry for player performance
            const playerInfo = `${row.player_name} (${row.position}) played for ${row.team} in ${row.season}. Stats: ${row.yards || 0} yards, ${row.touchdowns || 0} TDs, ${row.receptions || 0} receptions. Performance level: ${row.performance_grade || 'N/A'}.`;

            await vectorSearchService.addKnowledge(
              'player_stats',
              `${row.player_name} ${row.season} Performance`,
              playerInfo,
              null,
              75 // Good trust score for historical stats
            );

            migratedCount++;

            if (migratedCount % 50 === 0) {
              console.log(`   📊 Processed ${migratedCount} player records...`);
            }
          })
          .on('end', () => {
            this.migrationLog.push({
              stage: 'Player Stats',
              count: migratedCount,
              timestamp: new Date().toISOString()
            });

            resolve({
              success: true,
              count: migratedCount,
              error: null
            });
          })
          .on('error', (error) => {
            console.error('Error reading player stats CSV:', error);
            resolve({
              success: false,
              count: migratedCount,
              error: error.message
            });
          });
      });

    } catch (error) {
      console.error('Player stats migration failed:', error);
      return {
        success: false,
        count: 0,
        error: error.message
      };
    }
  }

  /**
   * Create knowledge base entries from existing data
   */
  async createKnowledgeBaseEntries() {
    try {
      let createdCount = 0;

      // NFL general knowledge
      const nflKnowledge = [
        {
          category: 'nfl_rules',
          title: 'NFL Scoring System',
          content: 'NFL scoring: Touchdown = 6 points, Field Goal = 3 points, Safety = 2 points, Extra Point = 1 point, Two-Point Conversion = 2 points. Games consist of four 15-minute quarters.',
          trustScore: 95
        },
        {
          category: 'nfl_rules',
          title: 'NFL Season Structure',
          content: 'NFL regular season consists of 18 weeks with each team playing 17 games. Playoffs include Wild Card, Divisional, Conference Championships, and Super Bowl.',
          trustScore: 95
        },
        {
          category: 'betting_basics',
          title: 'Point Spread Betting',
          content: 'Point spread betting involves wagering on the margin of victory. The favorite must win by more than the spread, while the underdog can lose by less than the spread or win outright.',
          trustScore: 85
        },
        {
          category: 'betting_basics',
          title: 'Over/Under Betting',
          content: 'Over/Under (totals) betting involves wagering on whether the combined score of both teams will be over or under a set number determined by oddsmakers.',
          trustScore: 85
        },
        {
          category: 'weather_impact',
          title: 'Weather Effects on NFL Games',
          content: 'Weather significantly impacts NFL games. Wind affects passing and kicking, rain reduces ball control, snow slows the game and favors running, extreme cold affects player performance.',
          trustScore: 80
        },
        {
          category: 'home_advantage',
          title: 'NFL Home Field Advantage',
          content: 'Home teams in the NFL win approximately 57% of games. Advantages include crowd noise, familiar conditions, no travel fatigue, and referee bias. Some venues like Seattle and Kansas City have stronger home advantages.',
          trustScore: 85
        }
      ];

      for (const knowledge of nflKnowledge) {
        const result = await vectorSearchService.addKnowledge(
          knowledge.category,
          knowledge.title,
          knowledge.content,
          null,
          knowledge.trustScore
        );

        if (result.success) {
          createdCount++;
          console.log(`   📚 Added: ${knowledge.title}`);
        }

        // Small delay between insertions
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      this.migrationLog.push({
        stage: 'Knowledge Base',
        count: createdCount,
        timestamp: new Date().toISOString()
      });

      return {
        success: true,
        count: createdCount,
        error: null
      };

    } catch (error) {
      console.error('Knowledge base creation failed:', error);
      return {
        success: false,
        count: 0,
        error: error.message
      };
    }
  }

  /**
   * Get migration status
   */
  async getMigrationStatus() {
    try {
      const status = {
        teams: 0,
        games: 0,
        knowledge: 0,
        lastMigration: null
      };

      // Count teams
      const { count: teamsCount } = await supabase
        .from('teams')
        .select('*', { count: 'exact', head: true });

      // Count games
      const { count: gamesCount } = await supabase
        .from('games')
        .select('*', { count: 'exact', head: true });

      // Count knowledge base entries
      const { count: knowledgeCount } = await supabase
        .from('knowledge_base')
        .select('*', { count: 'exact', head: true });

      status.teams = teamsCount || 0;
      status.games = gamesCount || 0;
      status.knowledge = knowledgeCount || 0;

      return {
        success: true,
        status,
        migrationLog: this.migrationLog
      };

    } catch (error) {
      console.error('Error getting migration status:', error);
      return {
        success: false,
        error: error.message,
        status: null
      };
    }
  }

  /**
   * Clean up old migration data (use with caution)
   */
  async cleanupMigrationData() {
    console.log('🧹 Cleaning up migration data...');

    try {
      // Delete in order due to foreign key constraints
      await supabase.from('predictions').delete().neq('id', 0);
      await supabase.from('odds_history').delete().neq('id', 0);
      await supabase.from('games').delete().neq('id', 0);
      await supabase.from('teams').delete().neq('id', 0);
      await supabase.from('knowledge_base').delete().neq('id', 0);

      console.log('✅ Migration data cleaned up');
      return { success: true };

    } catch (error) {
      console.error('❌ Cleanup failed:', error);
      return { success: false, error: error.message };
    }
  }
}

// Create singleton instance
const dataMigrationService = new DataMigrationService();

export default dataMigrationService;