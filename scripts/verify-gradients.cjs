const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console Error:', msg.text());
    }
  });

  await page.goto('http://localhost:5173');
  await page.waitForTimeout(2000);

  // Check for game cards
  const cards = await page.$$('.card-mobile, .game-card');
  console.log(`Found ${cards.length} game cards`);

  if (cards.length > 0) {
    // Check first 3 cards for gradient styles
    for (let i = 0; i < Math.min(3, cards.length); i++) {
      console.log(`\nCard ${i + 1}:`);

      // Find gradient elements within this card
      const gradientDivs = await cards[i].$$('[style*="gradient"], [style*="background"]');
      console.log(`  - Found ${gradientDivs.length} elements with background/gradient styles`);

      // Get the actual computed styles
      if (gradientDivs.length > 0) {
        for (let j = 0; j < Math.min(2, gradientDivs.length); j++) {
          const style = await gradientDivs[j].evaluate(el => {
            const computed = window.getComputedStyle(el);
            return {
              background: computed.background,
              backgroundColor: computed.backgroundColor,
              backgroundImage: computed.backgroundImage,
              height: computed.height,
              width: computed.width
            };
          });
          console.log(`    Element ${j + 1} computed styles:`, style.backgroundImage || style.backgroundColor);
        }
      }
    }
  }

  // Take screenshot
  await page.screenshot({ path: 'tests/screenshots/verified-gradients.png', fullPage: true });
  console.log('\nScreenshot saved to tests/screenshots/verified-gradients.png');

  await browser.close();
})();