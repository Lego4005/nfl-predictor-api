const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Listen for console messages
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  await page.goto('http://localhost:5173');
  await page.waitForTimeout(3000);

  // Check if games are loading
  const gameCards = await page.$$('.game-card, [data-testid="game-card"], .card-mobile');
  console.log('Found', gameCards.length, 'game cards');

  // Check if there are any loading indicators
  const loadingElements = await page.$$('[data-testid="skeleton"], .skeleton');
  console.log('Found', loadingElements.length, 'loading indicators');

  // Check for error messages
  const errorElements = await page.$$('[role="alert"], .error, .alert-destructive');
  console.log('Found', errorElements.length, 'error elements');

  // Check for any games data
  const textContent = await page.textContent('body');
  console.log('Page contains "games":', textContent.toLowerCase().includes('games'));
  console.log('Page contains "loading":', textContent.toLowerCase().includes('loading'));
  console.log('Page contains "error":', textContent.toLowerCase().includes('error'));

  await browser.close();
})();