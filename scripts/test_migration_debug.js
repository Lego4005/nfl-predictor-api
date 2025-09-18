#!/usr/bin/env node

import { supabase } from '../src/services/supabaseClientNode.js';
import { NFL_TEAMS } from '../src/data/nflTeams.js';

console.log('🔍 Migration Debug Test\n');

async function testDatabaseConnection() {
  console.log('1. Testing database connection...');
  try {
    const { data, error } = await supabase.from('teams').select('count').single();
    if (error) {
      console.error('❌ Database connection failed:', error.message);
      return false;
    }
    console.log('✅ Database connection successful');
    return true;
  } catch (error) {
    console.error('❌ Connection error:', error.message);
    return false;
  }
}

async function testTableExists() {
  console.log('\n2. Testing if teams table exists...');
  try {
    const { error } = await supabase
      .from('teams')
      .select('id')
      .limit(1);

    if (error) {
      console.error('❌ Teams table error:', error.message);
      return false;
    }
    console.log('✅ Teams table exists');
    return true;
  } catch (error) {
    console.error('❌ Table test error:', error.message);
    return false;
  }
}

async function testSingleTeamInsert() {
  console.log('\n3. Testing single team insert...');
  try {
    const testTeam = Object.values(NFL_TEAMS)[0]; // Get first team
    console.log(`   Inserting test team: ${testTeam.city} ${testTeam.name}`);

    const { data, error } = await supabase
      .from('teams')
      .insert({
        abbreviation: testTeam.abbreviation.toUpperCase(),
        name: testTeam.name,
        city: testTeam.city,
        full_name: `${testTeam.city} ${testTeam.name}`,
        conference: testTeam.conference,
        division: testTeam.division,
        primary_color: testTeam.primaryColor,
        secondary_color: testTeam.secondaryColor,
        tertiary_color: testTeam.tertiaryColor,
        logo_url: testTeam.logo,
        gradient: testTeam.gradient,
        created_at: new Date().toISOString()
      })
      .select()
      .single();

    if (error) {
      console.error('❌ Insert failed:', error.message);
      console.error('❌ Error details:', JSON.stringify(error, null, 2));
      return false;
    }

    console.log('✅ Insert successful:', data?.abbreviation);
    return true;
  } catch (error) {
    console.error('❌ Insert error:', error.message);
    return false;
  }
}

async function testGameInsert() {
  console.log('\n4. Testing single game insert...');
  try {
    const testGame = {
      espn_game_id: 'test_game_12345',
      home_team: 'KC',
      away_team: 'BUF',
      home_score: 24,
      away_score: 21,
      game_time: '2024-01-15T20:00:00Z',
      week: 1,
      season: 2024,
      venue: 'Arrowhead Stadium',
      status: 'final',
      created_at: new Date().toISOString()
    };

    console.log(`   Inserting test game: ${testGame.away_team} @ ${testGame.home_team}`);

    const { data, error } = await supabase
      .from('games')
      .insert(testGame)
      .select()
      .single();

    if (error) {
      console.error('❌ Game insert failed:', error.message);
      console.error('❌ Error details:', JSON.stringify(error, null, 2));
      return false;
    }

    console.log('✅ Game insert successful:', data?.espn_game_id);
    return true;
  } catch (error) {
    console.error('❌ Game insert error:', error.message);
    return false;
  }
}

async function testDataQuery() {
  console.log('\n5. Testing data queries...');
  try {
    // Count teams
    const { count: teamsCount, error: teamsError } = await supabase
      .from('teams')
      .select('*', { count: 'exact', head: true });

    if (teamsError) {
      console.error('❌ Teams count error:', teamsError.message);
    } else {
      console.log(`📊 Teams in database: ${teamsCount}`);
    }

    // Count games
    const { count: gamesCount, error: gamesError } = await supabase
      .from('games')
      .select('*', { count: 'exact', head: true });

    if (gamesError) {
      console.error('❌ Games count error:', gamesError.message);
    } else {
      console.log(`🏈 Games in database: ${gamesCount}`);
    }

    // Sample recent data
    const { data: recentGames, error: recentError } = await supabase
      .from('games')
      .select('home_team, away_team, game_time, status')
      .order('created_at', { ascending: false })
      .limit(5);

    if (recentError) {
      console.error('❌ Recent games error:', recentError.message);
    } else {
      console.log(`📈 Recent games sample:`, recentGames);
    }

    return true;
  } catch (error) {
    console.error('❌ Query test error:', error.message);
    return false;
  }
}

async function runDebugTests() {
  console.log('Starting comprehensive migration debug tests...\n');

  const tests = [
    testDatabaseConnection,
    testTableExists,
    testSingleTeamInsert,
    testGameInsert,
    testDataQuery
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      const result = await test();
      if (result) {
        passed++;
      } else {
        failed++;
      }
    } catch (error) {
      console.error('Test execution error:', error.message);
      failed++;
    }

    // Small delay between tests
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log(`\n📊 Test Results:`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);

  if (failed === 0) {
    console.log('\n🎉 All tests passed! Database is working correctly.');
  } else {
    console.log('\n⚠️  Some tests failed. Check errors above.');
  }
}

// Run the debug tests
runDebugTests().catch(console.error);