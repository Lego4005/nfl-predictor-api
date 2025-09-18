import { chromium } from 'playwright';

async function checkApp() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Listen to console messages
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') {
      console.log('❌ Console Error:', text);
    } else if (text.includes('games') || text.includes('ESPN') || text.includes('Fetched')) {
      console.log('📋 Console:', text);
    }
  });

  // Listen to network requests
  page.on('response', response => {
    const url = response.url();
    if (url.includes('supabase') || url.includes('espn')) {
      console.log(`🌐 Network: ${response.status()} - ${url.substring(0, 80)}...`);
    }
  });

  console.log('📱 Opening NFL Dashboard...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });

  // Wait a bit for data to load
  await page.waitForTimeout(3000);

  // Check if games section exists
  const gamesSection = await page.$$('.mobile-grid > div');
  console.log(`\n🎮 Games found: ${gamesSection.length}`);

  // Get any error messages
  const errorText = await page.textContent('body');
  if (errorText.includes('error') || errorText.includes('Error')) {
    console.log('⚠️ Error text found on page');
  }

  // Check for specific elements
  const hasSmartInsights = await page.locator('text=Smart Insights').isVisible();
  console.log(`📊 Smart Insights visible: ${hasSmartInsights}`);

  // Check for game cards
  const gameCards = await page.$$('[class*="card"]');
  console.log(`🃏 Card elements found: ${gameCards.length}`);

  // Get page title and header
  const title = await page.title();
  const header = await page.textContent('h1');
  console.log(`\n📄 Page Title: ${title}`);
  console.log(`📝 Header: ${header}`);

  // Take a screenshot for debugging
  await page.screenshot({ path: 'dashboard-state.png', fullPage: true });
  console.log('\n📸 Screenshot saved as dashboard-state.png');

  await browser.close();
}

checkApp().catch(console.error);