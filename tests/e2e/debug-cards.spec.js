import { test, expect } from '@playwright/test';

test('Debug card alignment and data issues', async ({ page }) => {
  console.log('🔍 Debugging card alignment and data issues...');

  // Navigate and wait for content
  await page.goto('http://localhost:5174');
  await page.waitForSelector('#root', { timeout: 10000 });
  await page.waitForTimeout(5000); // Wait for data to load

  // Take screenshot
  await page.screenshot({
    path: 'tests/screenshots/debug-cards.png',
    fullPage: true
  });

  // Check what card components are actually rendering
  console.log('\n📋 CARD COMPONENT ANALYSIS:');

  const v2Cards = await page.$$('[data-testid="enhanced-game-card-v2"]');
  const v3Cards = await page.$$('[data-testid="enhanced-game-card-v3"]');
  const v4Cards = await page.$$('[data-testid="enhanced-game-card-v4"]');
  const originalCards = await page.$$('.enhanced-game-card');
  const allGameCards = await page.$$('.game-card');

  console.log(`🎴 V2 Cards: ${v2Cards.length}`);
  console.log(`🎴 V3 Cards: ${v3Cards.length}`);
  console.log(`🎴 V4 Cards: ${v4Cards.length}`);
  console.log(`🎴 Original enhanced cards: ${originalCards.length}`);
  console.log(`🎴 All game cards: ${allGameCards.length}`);

  // Check data loading
  console.log('\n📊 DATA ANALYSIS:');
  const gamesDataLog = await page.evaluate(() => {
    return window.__GAMES_DEBUG_INFO || 'No debug info available';
  });
  console.log('Games data:', gamesDataLog);

  // Check for grid containers
  const gridContainers = await page.$$('[class*="grid"]');
  console.log(`📊 Grid containers: ${gridContainers.length}`);

  // Check for specific grid classes that might be causing alignment issues
  for (let i = 0; i < Math.min(gridContainers.length, 5); i++) {
    const classes = await gridContainers[i].getAttribute('class');
    console.log(`Grid ${i + 1}: ${classes}`);
  }

  // Check what's actually in the card content
  if (v3Cards.length > 0) {
    console.log('\n🎯 V3 CARD CONTENT ANALYSIS:');
    for (let i = 0; i < Math.min(v3Cards.length, 3); i++) {
      const cardText = await v3Cards[i].textContent();
      const cardClasses = await v3Cards[i].getAttribute('class');
      console.log(`V3 Card ${i + 1} classes: ${cardClasses}`);
      console.log(`V3 Card ${i + 1} content (first 100 chars): ${cardText?.substring(0, 100)}...`);
    }
  }

  // Check for any error messages or loading states
  const errorMessages = await page.$$('text=/error/i, text=/failed/i, text=/loading/i');
  console.log(`⚠️ Error/loading messages: ${errorMessages.length}`);

  // Check for CSS layout issues
  const cardSizes = await page.evaluate(() => {
    const cards = document.querySelectorAll('[data-testid="enhanced-game-card-v3"], .game-card');
    return Array.from(cards).slice(0, 5).map((card, index) => {
      const rect = card.getBoundingClientRect();
      return {
        index,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        x: Math.round(rect.x),
        y: Math.round(rect.y)
      };
    });
  });

  console.log('\n📐 CARD DIMENSIONS:');
  cardSizes.forEach(size => {
    console.log(`Card ${size.index}: ${size.width}x${size.height} at (${size.x}, ${size.y})`);
  });

  // Check for missing team data
  const teamLogos = await page.$$('[class*="team"], [alt*="logo"]');
  console.log(`🏈 Team logos: ${teamLogos.length}`);

  // Check for ESPN API data
  const espnDataIndicators = await page.$$('text=/ESPN/');
  console.log(`📡 ESPN data indicators: ${espnDataIndicators.length}`);

  // Check console for any JavaScript errors
  const logs = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      logs.push(msg.text());
    }
  });

  await page.waitForTimeout(1000);

  if (logs.length > 0) {
    console.log('\n❌ CONSOLE ERRORS:');
    logs.forEach(log => console.log(log));
  } else {
    console.log('\n✅ No console errors detected');
  }

  console.log('\n🎯 SUMMARY:');
  console.log(`- Cards detected: V2(${v2Cards.length}) V3(${v3Cards.length}) Generic(${allGameCards.length})`);
  console.log(`- Grid containers: ${gridContainers.length}`);
  console.log(`- Team logos: ${teamLogos.length}`);
  console.log(`- Console errors: ${logs.length}`);
});