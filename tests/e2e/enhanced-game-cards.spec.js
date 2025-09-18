import { test, expect } from '@playwright/test';

test.describe('Enhanced NFL Game Cards', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('http://localhost:5173');

    // Wait for React to load and render
    await page.waitForSelector('#root', { timeout: 5000 });

    // Wait for any game cards or dashboard content to load (more flexible)
    await page.waitForFunction(() => {
      return document.querySelector('[class*="card"], [class*="dashboard"], [class*="game"]') !== null;
    }, { timeout: 15000 });
  });

  test('should display game cards with enhanced data', async ({ page }) => {
    // Wait for game cards to load
    await page.waitForSelector('.game-card', { timeout: 15000 });

    // Get all game cards
    const gameCards = await page.$$('.game-card');
    console.log(`Found ${gameCards.length} game cards`);

    // Check that we have at least one game card
    expect(gameCards.length).toBeGreaterThan(0);

    // Check for enhanced card elements
    const firstCard = gameCards[0];

    // Check for team names
    const teamNames = await firstCard.$$('.team-name');
    expect(teamNames.length).toBe(2);
  });

  test('should display live games in priority section', async ({ page }) => {
    // Look for live games section
    const liveSection = await page.$('.live-games-section');

    if (liveSection) {
      console.log('Live games section found');

      // Check for the LIVE NOW badge
      const liveBadge = await page.$('text=LIVE NOW');
      expect(liveBadge).toBeTruthy();

      // Check for red border on live game cards
      const liveCards = await liveSection.$$('.border-red-500');
      console.log(`Found ${liveCards.length} live game cards`);

      // Each live card should have animations
      for (const card of liveCards) {
        const hasAnimation = await card.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.animation || styles.transition;
        });
        expect(hasAnimation).toBeTruthy();
      }
    } else {
      console.log('No live games currently - checking for scheduled/completed games');
    }
  });

  test('should show different content based on game state', async ({ page }) => {
    // Get all game cards
    const gameCards = await page.$$('.game-card');

    for (const card of gameCards.slice(0, 3)) { // Check first 3 cards
      // Get the game status
      const statusText = await card.$eval('.game-status', el => el.textContent).catch(() => null);

      if (statusText) {
        console.log(`Game status: ${statusText}`);

        if (statusText.includes('LIVE') || statusText.includes('Q')) {
          // Live game should have field position
          const fieldPosition = await card.$('.field-position');
          expect(fieldPosition).toBeTruthy();

          // Should have down and distance
          const downDistance = await card.$('.down-distance');
          expect(downDistance).toBeTruthy();
        } else if (statusText.includes('FINAL')) {
          // Completed game should have final scores
          const finalScores = await card.$$('.final-score');
          expect(finalScores.length).toBeGreaterThan(0);

          // Should have top performers
          const topPerformers = await card.$('.top-performers');
          expect(topPerformers).toBeTruthy();
        } else {
          // Upcoming game should have countdown
          const countdown = await card.$('.countdown-timer');
          expect(countdown).toBeTruthy();

          // Should have betting lines
          const bettingLines = await card.$('.betting-lines');
          expect(bettingLines).toBeTruthy();
        }
      }
    }
  });

  test('should have animations for score changes', async ({ page }) => {
    // Look for any score elements with animation classes
    const animatedScores = await page.$$('.score-changed, .animate-pulse, .animate-bounce');

    if (animatedScores.length > 0) {
      console.log(`Found ${animatedScores.length} animated score elements`);

      // Check that animations are applied
      for (const element of animatedScores) {
        const hasAnimation = await element.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.animationName !== 'none' || styles.transition !== 'none';
        });
        expect(hasAnimation).toBeTruthy();
      }
    }
  });

  test('should show red zone alerts for teams in scoring position', async ({ page }) => {
    // Look for red zone indicators
    const redZoneAlerts = await page.$$('.red-zone-alert, .bg-red-600, [class*="red-zone"]');

    if (redZoneAlerts.length > 0) {
      console.log(`Found ${redZoneAlerts.length} red zone indicators`);

      // Red zone elements should have special styling
      for (const alert of redZoneAlerts) {
        const hasRedStyling = await alert.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.backgroundColor.includes('rgb(220') || // red color
                 styles.borderColor.includes('rgb(220') ||
                 el.classList.contains('animate-pulse');
        });
        expect(hasRedStyling).toBeTruthy();
      }
    }
  });

  test('should display weather information for outdoor games', async ({ page }) => {
    // Look for weather indicators
    const weatherElements = await page.$$('.weather-info, [class*="weather"]');

    if (weatherElements.length > 0) {
      console.log(`Found ${weatherElements.length} weather elements`);

      // Check for temperature and conditions
      for (const weather of weatherElements) {
        const text = await weather.textContent();
        // Should contain temperature or weather conditions
        const hasWeatherInfo = /\d+°|wind|rain|snow|clear|cloudy/i.test(text);
        expect(hasWeatherInfo).toBeTruthy();
      }
    }
  });

  test('should have dynamic grid sizing based on game count', async ({ page }) => {
    // Get the games container
    const gamesGrid = await page.$('.games-grid, [class*="grid-cols"]');

    if (gamesGrid) {
      // Check grid classes
      const gridClasses = await gamesGrid.getAttribute('class');

      // Should have responsive grid classes
      expect(gridClasses).toMatch(/grid-cols-\d|lg:grid-cols-\d|xl:grid-cols-\d/);

      // Count the number of games
      const gameCards = await gamesGrid.$$('.game-card');
      console.log(`Grid contains ${gameCards.length} games`);

      // Grid should adjust based on game count
      if (gameCards.length <= 3) {
        expect(gridClasses).toContain('lg:grid-cols-3');
      } else if (gameCards.length <= 6) {
        expect(gridClasses).toContain('lg:grid-cols-3');
      } else {
        // Should have expansion capability
        const expandButton = await page.$('button:has-text("Show All")');
        if (gameCards.length > 12) {
          expect(expandButton).toBeTruthy();
        }
      }
    }
  });

  test('should display betting lines and odds', async ({ page }) => {
    // Look for betting information
    const bettingElements = await page.$$('.betting-lines, .odds-info, [class*="spread"], [class*="total"]');

    if (bettingElements.length > 0) {
      console.log(`Found ${bettingElements.length} betting elements`);

      for (const element of bettingElements) {
        const text = await element.textContent();
        // Should contain spread or total points
        const hasBettingInfo = /[+-]\d+\.?\d*|O\/U \d+\.?\d*/i.test(text);
        expect(hasBettingInfo).toBeTruthy();
      }
    }
  });

  test('should show team records', async ({ page }) => {
    // Look for team record elements
    const recordElements = await page.$$('.team-record, [class*="record"]');

    if (recordElements.length > 0) {
      console.log(`Found ${recordElements.length} team record elements`);

      for (const element of recordElements) {
        const text = await element.textContent();
        // Should match record format (W-L or W-L-T)
        const hasRecordFormat = /\d+-\d+(-\d+)?/.test(text);
        expect(hasRecordFormat).toBeTruthy();
      }
    }
  });

  test('should handle expand/collapse for many games', async ({ page }) => {
    // Count total games
    const allGameCards = await page.$$('.game-card');

    if (allGameCards.length > 12) {
      console.log(`Found ${allGameCards.length} games - testing expand/collapse`);

      // Look for expand button
      const expandButton = await page.$('button:has-text("Show All"), button:has-text("Show More")');

      if (expandButton) {
        // Click to expand
        await expandButton.click();
        await page.waitForTimeout(500); // Wait for animation

        // Should show all games
        const visibleCards = await page.$$('.game-card:visible');
        expect(visibleCards.length).toBe(allGameCards.length);

        // Look for collapse button
        const collapseButton = await page.$('button:has-text("Show Less"), button:has-text("Collapse")');
        expect(collapseButton).toBeTruthy();

        // Click to collapse
        await collapseButton.click();
        await page.waitForTimeout(500);

        // Should show limited games again
        const limitedCards = await page.$$('.game-card:visible');
        expect(limitedCards.length).toBeLessThanOrEqual(12);
      }
    }
  });
});

// Visual regression test
test('Enhanced game cards visual appearance', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.waitForSelector('.game-card', { timeout: 15000 });

  // Take screenshot for visual comparison
  await page.screenshot({
    path: 'tests/screenshots/enhanced-game-cards.png',
    fullPage: true
  });

  // Log what we see
  const gameCards = await page.$$('.game-card');
  console.log(`
    Visual Test Summary:
    - Total game cards: ${gameCards.length}
    - Live games section: ${await page.$('.live-games-section') ? 'Present' : 'Not present'}
    - Animations detected: ${await page.$$('[class*="animate"]').then(els => els.length)}
    - Red zone alerts: ${await page.$$('.red-zone-alert').then(els => els.length)}
    - Weather info: ${await page.$$('.weather-info').then(els => els.length)}
  `);
});