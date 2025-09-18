const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Listen for console messages
  page.on('console', msg => {
    console.log('Console:', msg.text());
  });

  await page.goto('http://localhost:5173');
  await page.waitForTimeout(3000);

  // Check for game cards
  const cards = await page.$$('.card-mobile, .game-card');
  console.log(`Found ${cards.length} game cards`);

  if (cards.length > 0) {
    // Check first 3 cards for detailed team and gradient info
    for (let i = 0; i < Math.min(3, cards.length); i++) {
      console.log(`\n=== Card ${i + 1} ===`);

      // Get team abbreviations from the card
      const teamInfo = await cards[i].evaluate(el => {
        // Look for team abbreviations in the card text
        const text = el.textContent || '';
        const teamAbbreviations = text.match(/[A-Z]{2,3}/g) || [];

        // Get any data attributes that might contain team info
        const dataAttrs = {};
        for (let attr of el.attributes) {
          if (attr.name.startsWith('data-')) {
            dataAttrs[attr.name] = attr.value;
          }
        }

        return {
          text: text.substring(0, 200), // First 200 chars
          teamAbbreviations,
          dataAttrs
        };
      });

      console.log('Team abbreviations found:', teamInfo.teamAbbreviations);
      console.log('Card text preview:', teamInfo.text);

      // Find gradient elements and get their actual styles
      const gradientDivs = await cards[i].$$('[style*="gradient"], [style*="background"]');
      console.log(`Found ${gradientDivs.length} elements with background/gradient styles`);

      for (let j = 0; j < gradientDivs.length; j++) {
        const elementInfo = await gradientDivs[j].evaluate(el => {
          const computed = window.getComputedStyle(el);
          const inline = el.style;

          return {
            tagName: el.tagName,
            className: el.className,
            inlineBackground: inline.background,
            inlineBackgroundImage: inline.backgroundImage,
            computedBackground: computed.background,
            computedBackgroundImage: computed.backgroundImage,
            height: computed.height,
            width: computed.width,
            textContent: el.textContent?.substring(0, 50) || ''
          };
        });

        console.log(`  Element ${j + 1}:`, {
          tag: elementInfo.tagName,
          class: elementInfo.className,
          inline: elementInfo.inlineBackground || elementInfo.inlineBackgroundImage,
          computed: elementInfo.computedBackgroundImage || elementInfo.computedBackground,
          text: elementInfo.textContent
        });
      }
    }
  }

  // Take screenshot
  await page.screenshot({ path: 'tests/screenshots/debug-gradients.png', fullPage: true });
  console.log('\nScreenshot saved to tests/screenshots/debug-gradients.png');

  await browser.close();
})();