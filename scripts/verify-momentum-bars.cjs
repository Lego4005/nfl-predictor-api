const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('http://localhost:5173');
  await page.waitForTimeout(3000);

  // Check for game cards
  const cards = await page.$$('.card-mobile, .game-card');
  console.log(`Found ${cards.length} game cards`);

  if (cards.length > 0) {
    // Check all cards for momentum/winner bars
    for (let i = 0; i < cards.length; i++) {
      console.log(`\n=== Card ${i + 1} ===`);

      // Look for momentum or winner text
      const barInfo = await cards[i].evaluate(el => {
        const text = el.textContent || '';
        const hasMomentum = text.includes('Momentum');
        const hasWinner = text.includes('Winner');
        const hasFinal = text.includes('FINAL');
        const hasLive = text.includes('LIVE');

        return {
          hasMomentum,
          hasWinner,
          hasFinal,
          hasLive,
          gameStatus: hasFinal ? 'final' : hasLive ? 'live' : 'upcoming'
        };
      });

      console.log('Game status:', barInfo);

      // Find all gradient/background elements in this card
      const gradientElements = await cards[i].$$('[style*="gradient"], [style*="background"]');
      console.log(`Found ${gradientElements.length} gradient elements`);

      // Look specifically for momentum/winner bars (smaller height elements)
      for (let j = 0; j < gradientElements.length; j++) {
        const elementInfo = await gradientElements[j].evaluate(el => {
          const computed = window.getComputedStyle(el);
          const height = computed.height;
          const width = computed.width;
          const background = computed.backgroundImage || computed.background;

          return {
            height,
            width,
            background: background,
            isMomentumBar: height === '8px' || height === '6px', // momentum bars are thin
            className: el.className
          };
        });

        if (elementInfo.isMomentumBar || elementInfo.height === '8px') {
          console.log(`  Momentum/Winner bar:`, {
            height: elementInfo.height,
            width: elementInfo.width,
            background: elementInfo.background,
            className: elementInfo.className
          });
        }
      }

      if (i >= 4) break; // Check first 5 cards
    }
  }

  // Take screenshot
  await page.screenshot({ path: 'tests/screenshots/momentum-bars-verified.png', fullPage: true });
  console.log('\nScreenshot saved to tests/screenshots/momentum-bars-verified.png');

  await browser.close();
})();