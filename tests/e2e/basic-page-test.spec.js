import { test, expect } from '@playwright/test';

test('NFL Dashboard loads and displays content', async ({ page }) => {
  console.log('🎯 Starting basic page test...');

  // Navigate to the dashboard
  await page.goto('http://localhost:5173');
  console.log('✅ Page loaded');

  // Wait for React root to exist
  await page.waitForSelector('#root', { timeout: 10000 });
  console.log('✅ React root found');

  // Wait a bit for content to load
  await page.waitForTimeout(3000);

  // Take a screenshot for manual inspection
  await page.screenshot({
    path: 'tests/screenshots/dashboard-current.png',
    fullPage: true
  });
  console.log('✅ Screenshot saved');

  // Check if any game-related content exists
  const gameElements = await page.$$('[class*="game"], [class*="card"], .game-card, [data-testid*="game"]');
  console.log(`🎮 Found ${gameElements.length} game-related elements`);

  // Check for enhanced card elements
  const enhancedElements = await page.$$('[class*="enhanced"], [class*="Enhanced"]');
  console.log(`✨ Found ${enhancedElements.length} enhanced elements`);

  // Check for any live game indicators
  const liveElements = await page.$$('[class*="live"], [class*="Live"], .bg-red-500, .border-red-500');
  console.log(`🔴 Found ${liveElements.length} live game indicators`);

  // Check for grid layout
  const gridElements = await page.$$('[class*="grid"]');
  console.log(`📊 Found ${gridElements.length} grid elements`);

  // Check for animations
  const animatedElements = await page.$$('[class*="animate"], [class*="motion"]');
  console.log(`🎭 Found ${animatedElements.length} animated elements`);

  // Get page title
  const title = await page.title();
  console.log(`📄 Page title: ${title}`);

  // Get all error messages in console
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // Check for specific Enhanced Game Card V2 elements
  const v2Cards = await page.$$('[class*="enhanced-game-card-v2"], [data-component="EnhancedGameCardV2"]');
  console.log(`🎴 Found ${v2Cards.length} Enhanced Game Card V2 elements`);

  // Log what we actually see on the page
  const allElements = await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    const classes = new Set();
    const ids = new Set();

    elements.forEach(el => {
      if (el.className && typeof el.className === 'string') {
        el.className.split(' ').forEach(cls => {
          if (cls.includes('game') || cls.includes('card') || cls.includes('dashboard') || cls.includes('enhanced')) {
            classes.add(cls);
          }
        });
      }
      if (el.id && (el.id.includes('game') || el.id.includes('card') || el.id.includes('dashboard'))) {
        ids.add(el.id);
      }
    });

    return {
      relevantClasses: Array.from(classes),
      relevantIds: Array.from(ids),
      totalElements: elements.length
    };
  });

  console.log(`
📋 Page Analysis:
   - Total elements: ${allElements.totalElements}
   - Relevant classes: ${allElements.relevantClasses.join(', ')}
   - Relevant IDs: ${allElements.relevantIds.join(', ')}
   - Console errors: ${consoleErrors.length}
  `);

  if (consoleErrors.length > 0) {
    console.log('❌ Console errors:', consoleErrors.slice(0, 3));
  }

  // Basic assertions
  expect(title).toContain('NFL');
  expect(allElements.totalElements).toBeGreaterThan(10);
});