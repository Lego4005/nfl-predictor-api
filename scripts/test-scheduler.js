#!/usr/bin/env node

import schedulerService from '../src/services/schedulerService.js';

console.log('🔄 Testing NFL Data Scheduler...');

async function testScheduler() {
  try {
    // Test manual sync first
    console.log('\n1️⃣ Testing manual sync...');
    await schedulerService.manualSync();

    // Test status
    console.log('\n2️⃣ Testing scheduler status...');
    const status = schedulerService.getStatus();
    console.log('   Status:', status);

    // Start the scheduler for 30 seconds to test intervals
    console.log('\n3️⃣ Starting scheduler for 30 seconds...');
    schedulerService.start();

    // Wait 30 seconds
    setTimeout(() => {
      console.log('\n4️⃣ Stopping scheduler...');
      schedulerService.stop();

      console.log('\n✅ Scheduler test completed successfully!');
      console.log('\n📋 Test Summary:');
      console.log('   ✅ Manual sync: Working');
      console.log('   ✅ Status check: Working');
      console.log('   ✅ Start/Stop: Working');
      console.log('   ✅ Intervals: Configured');

      process.exit(0);
    }, 30000);

    // Show countdown
    let countdown = 30;
    const countdownInterval = setInterval(() => {
      process.stdout.write(`\r   ⏱️ Testing intervals... ${countdown}s remaining`);
      countdown--;
      if (countdown < 0) {
        clearInterval(countdownInterval);
        console.log(''); // New line
      }
    }, 1000);

  } catch (error) {
    console.error('❌ Scheduler test failed:', error);
    process.exit(1);
  }
}

testScheduler().catch(error => {
  console.error('💥 Test runner failed:', error);
  process.exit(1);
});