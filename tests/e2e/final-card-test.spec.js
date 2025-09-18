import { test, expect } from '@playwright/test';

test('Final Card Design Test - Original Enhanced vs Current', async ({ page }) => {
  console.log('🔍 Testing final card implementation...');

  await page.goto('http://localhost:5174');
  await page.waitForSelector('#root', { timeout: 10000 });
  await page.waitForTimeout(3000);

  // Take screenshot for comparison
  await page.screenshot({
    path: 'tests/screenshots/final-card-test.png',
    fullPage: true
  });

  // Check what cards are actually rendering
  const enhancedCards = await page.$$('.enhanced-game-card');
  const v2Cards = await page.$$('[data-testid="enhanced-game-card-v2"]');
  const v3Cards = await page.$$('[data-testid="enhanced-game-card-v3"]');
  const v4Cards = await page.$$('[data-testid="enhanced-game-card-v4"]');
  const anyCards = await page.$$('.game-card, [class*="game"], [class*="card"]');

  console.log(`\n📊 FINAL CARD COUNT:`);
  console.log(`  Enhanced cards: ${enhancedCards.length}`);
  console.log(`  V2 cards: ${v2Cards.length}`);
  console.log(`  V3 cards: ${v3Cards.length}`);
  console.log(`  V4 cards: ${v4Cards.length}`);
  console.log(`  Any cards: ${anyCards.length}`);

  // Check for 3-column grid
  const threeColGrid = await page.$('.grid.gap-4.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3');
  console.log(`  3-column grid: ${threeColGrid ? 'YES' : 'NO'}`);

  // Verify we have some cards rendering
  const totalCards = enhancedCards.length + v2Cards.length + v3Cards.length + v4Cards.length;
  expect(totalCards).toBeGreaterThan(0);
});