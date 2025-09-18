import { chromium } from 'playwright';

async function testWiderCards() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    console.log('🚀 Testing wider cards layout...');

    // Navigate to the dashboard
    await page.goto('http://localhost:5174');
    await page.waitForTimeout(3000); // Wait for data to load

    // Wait for games to load
    await page.waitForSelector('[data-testid="game-card"], .grid > div', { timeout: 10000 });

    // Check if games are displayed
    const gameCards = await page.locator('.grid > div').count();
    console.log(`📊 Found ${gameCards} game cards`);

    // Check grid layout - should be single column now
    const gridElement = await page.locator('.grid').first();
    const gridClasses = await gridElement.getAttribute('class');
    console.log(`🎨 Grid classes: ${gridClasses}`);

    // Verify it's single column layout (no lg:grid-cols-2 or lg:grid-cols-3)
    const isSingleColumn = !gridClasses.includes('lg:grid-cols-2') && !gridClasses.includes('lg:grid-cols-3');
    console.log(`📐 Single column layout: ${isSingleColumn ? '✅' : '❌'}`);

    // Check card width - should be wider now
    if (gameCards > 0) {
      const firstCard = await page.locator('.grid > div').first();
      const cardWidth = await firstCard.evaluate(el => el.offsetWidth);
      console.log(`📏 Card width: ${cardWidth}px`);

      // Check if card takes significant portion of screen width
      const viewportWidth = page.viewportSize().width;
      const widthPercentage = (cardWidth / viewportWidth) * 100;
      console.log(`📊 Card takes ${widthPercentage.toFixed(1)}% of viewport width`);

      const isWide = widthPercentage > 80; // Should take most of the width
      console.log(`📐 Cards are wide enough: ${isWide ? '✅' : '❌'}`);
    }

    // Check for any content that might be cut off or truncated
    const cardContents = await page.locator('.grid > div').all();
    for (let i = 0; i < Math.min(cardContents.length, 3); i++) {
      const card = cardContents[i];
      const hasOverflowHidden = await card.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.overflow === 'hidden' || styles.textOverflow === 'ellipsis';
      });
      console.log(`🔍 Card ${i + 1} overflow check: ${hasOverflowHidden ? '⚠️ May truncate' : '✅ No truncation'}`);
    }

    // Check for team names and scores visibility
    const teamNames = await page.locator('text=/Chiefs|Bills|Rams|49ers|Packers|Cowboys|Eagles|Steelers/').count();
    console.log(`🏈 Team names visible: ${teamNames}`);

    // Check for scores (final games)
    const scores = await page.locator('text=/\\d+\\s*-\\s*\\d+|\\d+\\s+\\d+/').count();
    console.log(`🎯 Scores visible: ${scores}`);

    // Test Expert Observatory API data
    const expertBadge = await page.locator('text=/Expert Observatory|Live 2025 NFL Data/').count();
    console.log(`🔬 Expert Observatory indicator: ${expertBadge > 0 ? '✅' : '❌'}`);

    // Check for any error messages
    const errorMessages = await page.locator('text=/error|failed|not found/i').count();
    console.log(`⚠️ Error messages: ${errorMessages}`);

    // Final assessment
    console.log('\n📋 SUMMARY:');
    console.log(`- Games loaded: ${gameCards > 0 ? '✅' : '❌'}`);
    console.log(`- Single column layout: ${isSingleColumn ? '✅' : '❌'}`);
    console.log(`- Team data visible: ${teamNames > 0 ? '✅' : '❌'}`);
    console.log(`- Expert Observatory API: ${expertBadge > 0 ? '✅' : '❌'}`);
    console.log(`- No errors: ${errorMessages === 0 ? '✅' : '❌'}`);

    // Take a screenshot
    await page.screenshot({
      path: 'tests/screenshots/wider-cards-test.png',
      fullPage: true
    });
    console.log('📸 Screenshot saved to tests/screenshots/wider-cards-test.png');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testWiderCards();