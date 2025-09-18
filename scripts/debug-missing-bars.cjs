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
    // Check first card in detail
    console.log('\n=== DEBUGGING FIRST CARD ===');

    const cardContent = await cards[0].evaluate(el => {
      const text = el.textContent || '';

      // Look for specific text that should be in the momentum/winner section
      const hasWinnerText = text.includes('Winner');
      const hasMomentumText = text.includes('Momentum');
      const hasFinalText = text.includes('FINAL');
      const hasLiveText = text.includes('LIVE');

      // Get all elements with height = 8px (momentum bars)
      const allElements = el.querySelectorAll('*');
      let thinBars = [];

      allElements.forEach(elem => {
        const computed = window.getComputedStyle(elem);
        if (computed.height === '8px' || computed.height === '0.5rem') {
          thinBars.push({
            tagName: elem.tagName,
            className: elem.className,
            height: computed.height,
            background: computed.background || computed.backgroundImage,
            width: computed.width
          });
        }
      });

      return {
        hasWinnerText,
        hasMomentumText,
        hasFinalText,
        hasLiveText,
        textPreview: text.substring(0, 500),
        thinBars
      };
    });

    console.log('Card analysis:', cardContent);
  }

  await browser.close();
})();