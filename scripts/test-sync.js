#!/usr/bin/env node

import dataIntegrationService from '../src/services/dataIntegrationService.js';

console.log('🔄 Testing enhanced data integration service...');
console.log('This will sync 2025 NFL data from ESPN to Supabase\n');

dataIntegrationService.performFullSync().then(result => {
  console.log('\n📊 Full sync completed!');
  console.log('=' .repeat(50));

  if (result.espn.success) {
    console.log('✅ ESPN:', result.espn.data.synced + '/' + result.espn.data.total, 'games synced');
  } else {
    console.log('❌ ESPN: Failed -', result.espn.error);
  }

  if (result.odds.success) {
    console.log('✅ Odds:', result.odds.data.synced, 'odds records synced');
  } else {
    console.log('❌ Odds: Failed -', result.odds.error);
  }

  if (result.weather.success) {
    console.log('✅ Weather:', result.weather.data.synced, 'games updated with weather');
  } else {
    console.log('❌ Weather: Failed -', result.weather.error);
  }

  console.log('⏱️ Duration:', (result.duration / 1000).toFixed(2) + 's');
  console.log('🕐 Timestamp:', result.timestamp);

  process.exit(0);
}).catch(error => {
  console.error('❌ Full sync error:', error);
  process.exit(1);
});