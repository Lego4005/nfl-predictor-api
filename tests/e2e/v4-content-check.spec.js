import { test, expect } from '@playwright/test';

test('V4 Card Content and Data Display Check', async ({ page }) => {
  console.log('🔍 Checking V4 card content and data display...');

  // Navigate to the dashboard
  await page.goto('http://localhost:5174');
  await page.waitForSelector('#root', { timeout: 10000 });
  await page.waitForTimeout(3000); // Wait for data to load

  // Wait for V4 cards to load
  await page.waitForSelector('[data-testid="enhanced-game-card-v4"]', { timeout: 15000 });

  // Take screenshot for visual comparison
  await page.screenshot({
    path: 'tests/screenshots/v4-content-check.png',
    fullPage: true
  });

  // Get all V4 cards
  const v4Cards = await page.$$('[data-testid="enhanced-game-card-v4"]');
  console.log(`\n🎴 Found ${v4Cards.length} V4 Cards`);

  // Check content of first few cards
  for (let i = 0; i < Math.min(v4Cards.length, 3); i++) {
    console.log(`\n📋 CARD ${i + 1} ANALYSIS:`);

    const card = v4Cards[i];
    const cardText = await card.textContent();

    // Check for team names
    const teamElements = await card.$$('text=/[A-Z]{2,3}/ >> nth=0');
    if (teamElements.length > 0) {
      const teamText = await teamElements[0].textContent();
      console.log(`  🏈 Teams: ${teamText}`);
    }

    // Check for scores
    const scoreElements = await card.$$('.font-black, .text-xl, .text-2xl');
    for (let j = 0; j < Math.min(scoreElements.length, 2); j++) {
      const scoreText = await scoreElements[j].textContent();
      console.log(`  🎯 Score ${j + 1}: ${scoreText}`);
    }

    // Check for status badges
    const statusBadges = await card.$$('.bg-blue-500, .bg-red-600, .bg-gray-600');
    if (statusBadges.length > 0) {
      const statusText = await statusBadges[0].textContent();
      console.log(`  🚦 Status: ${statusText}`);
    }

    // Check overall layout structure
    const cardClasses = await card.getAttribute('class');
    console.log(`  🎨 Card classes: ${cardClasses?.substring(0, 100)}...`);

    // Check if content looks properly formatted (not concatenated)
    const hasProperSpacing = cardText.includes(' ') && !cardText.match(/[A-Z]{3,}[0-9]+[A-Z]{3,}/);
    console.log(`  ✅ Proper spacing: ${hasProperSpacing ? 'YES' : 'NO'}`);

    if (!hasProperSpacing) {
      console.log(`  ⚠️  Raw content: ${cardText.substring(0, 150)}...`);
    }
  }

  // Check grid layout
  const gridContainer = await page.$('.grid.gap-4.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3');
  if (gridContainer) {
    console.log('\n📊 GRID LAYOUT: ✅ 3-column grid found');
  } else {
    console.log('\n📊 GRID LAYOUT: ❌ 3-column grid NOT found');
  }

  // Check for visual issues
  const cardSizes = await page.evaluate(() => {
    const cards = document.querySelectorAll('[data-testid="enhanced-game-card-v4"]');
    return Array.from(cards).slice(0, 6).map((card, index) => {
      const rect = card.getBoundingClientRect();
      return {
        index,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        visible: rect.width > 0 && rect.height > 0
      };
    });
  });

  console.log('\n📐 CARD DIMENSIONS:');
  cardSizes.forEach(size => {
    console.log(`  Card ${size.index + 1}: ${size.width}x${size.height} (visible: ${size.visible})`);
  });

  // Basic assertions
  expect(v4Cards.length).toBeGreaterThan(0);
  expect(cardSizes.every(s => s.visible)).toBe(true);
});