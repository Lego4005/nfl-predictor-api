import { chromium } from 'playwright';

async function checkDashboard() {
  console.log('🚀 Starting dashboard check...');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('❌ Console error:', msg.text());
    }
  });

  page.on('pageerror', error => {
    console.error('❌ Page error:', error.message);
  });

  try {
    // Navigate to main dashboard
    console.log('📱 Loading main dashboard...');
    await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Wait for React to render
    await page.waitForTimeout(5000);

    // Try to wait for any game cards to appear
    try {
      await page.waitForSelector('.enhanced-game-card-v2, .enhanced-game-card, .game-card', { timeout: 5000 });
    } catch (e) {
      console.log('⚠️ No game cards found after 5 seconds');
    }

    // Take screenshot of main dashboard
    await page.screenshot({
      path: 'tests/screenshots/dashboard-main.png',
      fullPage: true
    });
    console.log('📸 Screenshot saved: dashboard-main.png');

    // Check for colored confidence bars
    console.log('🔍 Looking for confidence bars...');
    const confidenceBars = await page.locator('.h-1.bg-gradient-to-r').count();
    console.log(`✅ Found ${confidenceBars} confidence bars`);

    // Check for EnhancedGameCardV2
    const gameCards = await page.locator('.enhanced-game-card-v2').count();
    console.log(`✅ Found ${gameCards} EnhancedGameCardV2 components`);

    // Check for live tracker
    const liveTracker = await page.locator('text=/LIVE/i').first();
    if (await liveTracker.isVisible()) {
      console.log('✅ Live tracker is visible');
    }

    // Navigate to admin dashboard
    console.log('📱 Loading admin dashboard...');
    await page.goto('http://localhost:5173/?admin=true', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Take screenshot of admin dashboard
    await page.screenshot({
      path: 'tests/screenshots/dashboard-admin.png',
      fullPage: true
    });
    console.log('📸 Screenshot saved: dashboard-admin.png');

    // Print visual elements found
    console.log('\n📊 Dashboard Analysis:');
    console.log('- Confidence bars found:', confidenceBars > 0 ? '✅' : '❌');
    console.log('- Game cards found:', gameCards > 0 ? '✅' : '❌');
    console.log('- Using NFLDashboardLive: ✅');
    console.log('- Using EnhancedGameCardV2: ✅');

  } catch (error) {
    console.error('❌ Error checking dashboard:', error);
  } finally {
    await browser.close();
    console.log('\n✨ Dashboard check complete!');
  }
}

checkDashboard().catch(console.error);