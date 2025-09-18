import { test, expect } from '@playwright/test';

test('Enhanced Game Cards V3 - Complete Feature Test', async ({ page }) => {
  console.log('🚀 Testing Enhanced Game Card V3 features...');

  // Navigate to the dashboard
  await page.goto('http://localhost:5174');

  // Wait for React root to exist
  await page.waitForSelector('#root', { timeout: 10000 });

  // Wait for enhanced V4 cards to load
  await page.waitForSelector('[data-testid="enhanced-game-card-v4"]', { timeout: 15000 });

  // Take a screenshot for visual comparison
  await page.screenshot({
    path: 'tests/screenshots/enhanced-v3-cards.png',
    fullPage: true
  });
  console.log('✅ Screenshot saved');

  // Check Enhanced V3 cards are rendering
  const v3Cards = await page.$$('[data-testid="enhanced-game-card-v3"]');
  console.log(`🎴 Found ${v3Cards.length} Enhanced Game Card V3 elements`);
  expect(v3Cards.length).toBeGreaterThan(0);

  // Check for glassmorphism styling (backdrop-blur classes)
  const glassmorphCards = await page.$$('[class*="backdrop-blur"]');
  console.log(`✨ Found ${glassmorphCards.length} glassmorphism cards`);
  expect(glassmorphCards.length).toBeGreaterThan(0);

  // Test team gradient banners
  const teamGradients = await page.$$('.h-2.flex');
  console.log(`🌈 Found ${teamGradients.length} team gradient banners`);

  // Test different game states
  const allCards = await page.$$('[data-testid="enhanced-game-card-v3"]');
  let scheduledCount = 0;
  let liveCount = 0;
  let finalCount = 0;

  for (const card of allCards) {
    // Check for status badges
    const statusBadge = await card.$('.bg-blue-500, .bg-red-600, .bg-gray-600');
    if (statusBadge) {
      const badgeText = await statusBadge.textContent();
      if (badgeText.includes('Upcoming')) scheduledCount++;
      if (badgeText.includes('LIVE')) liveCount++;
      if (badgeText.includes('Final')) finalCount++;
    }

    // Check for team logos with glow
    const teamLogos = await card.$$('[class*="glow"], .w-8, .w-12');
    expect(teamLogos.length).toBeGreaterThanOrEqual(2); // Home and away teams
  }

  console.log(`📊 Game states: ${scheduledCount} scheduled, ${liveCount} live, ${finalCount} final`);

  // Test countdown timers for scheduled games
  if (scheduledCount > 0) {
    const countdownElements = await page.$$('text=/Kickoff in/');
    console.log(`⏰ Found ${countdownElements.length} countdown timers`);
  }

  // Test live game features
  if (liveCount > 0) {
    // Check for red zone alerts
    const redZoneAlerts = await page.$$('text=/RED ZONE/');
    console.log(`🔴 Found ${redZoneAlerts.length} red zone alerts`);

    // Check for field position visualizers
    const fieldPositions = await page.$$('.h-2.bg-gray-200, .h-2.bg-gray-700');
    console.log(`🏈 Found ${fieldPositions.length} field position visualizers`);

    // Check for quarter/time displays
    const gameClocks = await page.$$('text=/Q\\d/');
    console.log(`⏱️ Found ${gameClocks.length} game clocks`);
  }

  // Test final game features
  if (finalCount > 0) {
    // Check for trophy icons
    const trophyIcons = await page.$$('.text-yellow-500, .text-yellow-600');
    console.log(`🏆 Found ${trophyIcons.length} trophy/winner indicators`);

    // Check for top performers
    const topPerformers = await page.$$('text=/TOP PERFORMERS/');
    console.log(`⭐ Found ${topPerformers.length} top performer sections`);
  }

  // Test betting lines
  const bettingElements = await page.$$('text=/SPREAD/, text=/TOTAL/, text=/O\\/U/');
  console.log(`💰 Found ${bettingElements.length} betting line elements`);

  // Test weather information
  const weatherElements = await page.$$('text=/°F/');
  const weatherClasses = await page.$$('[class*="weather"]');
  const totalWeatherElements = weatherElements.length + weatherClasses.length;
  console.log(`🌤️ Found ${weatherElements.length} weather elements`);

  // Test AI predictions
  const aiPredictions = await page.$$('text=/AI Prediction/, text=/confident/');
  console.log(`🧠 Found ${aiPredictions.length} AI prediction elements`);

  // Test animations (check for framer-motion classes)
  const animatedElements = await page.$$('[class*="motion"], [style*="transform"]');
  console.log(`🎭 Found ${animatedElements.length} animated elements`);

  // Test responsive design elements
  const responsiveElements = await page.$$('[class*="sm:"], [class*="md:"], [class*="lg:"]');
  console.log(`📱 Found ${responsiveElements.length} responsive elements`);

  // Test hover interactions by hovering over a card
  if (allCards.length > 0) {
    await allCards[0].hover();
    await page.waitForTimeout(500); // Wait for hover animation
    console.log('✅ Hover interaction test completed');
  }

  // Check for team color customization
  const colorizedElements = await page.$$('[style*="--team-primary"], [style*="gradient"]');
  console.log(`🎨 Found ${colorizedElements.length} team-colored elements`);

  // Test accessibility features
  const accessibleElements = await page.$$('[role], [aria-label], [alt]');
  console.log(`♿ Found ${accessibleElements.length} accessibility elements`);

  // Final summary
  console.log(`
🎯 Enhanced Game Card V3 Test Summary:
   ✅ V3 Cards detected: ${v3Cards.length}
   ✨ Glassmorphism cards: ${glassmorphCards.length}
   🌈 Team gradients: ${teamGradients.length}
   📊 Game states: ${scheduledCount + liveCount + finalCount} total
   ⏰ Countdown timers: ${(await page.$$('text=/Kickoff in/')).length}
   🔴 Red zone alerts: ${(await page.$$('text=/RED ZONE/')).length}
   🏈 Field positions: ${(await page.$$('.h-2.bg-gray-200, .h-2.bg-gray-700')).length}
   🏆 Winner indicators: ${(await page.$$('.text-yellow-500, .text-yellow-600')).length}
   💰 Betting lines: ${bettingElements.length}
   🌤️ Weather info: ${totalWeatherElements}
   🧠 AI predictions: ${aiPredictions.length}
   🎭 Animations: ${animatedElements.length}
   📱 Responsive elements: ${responsiveElements.length}
   🎨 Team colors: ${colorizedElements.length}
  `);

  // Basic assertions
  expect(v3Cards.length).toBeGreaterThan(0);
  expect(glassmorphCards.length).toBeGreaterThan(0);
  expect(scheduledCount + liveCount + finalCount).toBeGreaterThan(0);
});