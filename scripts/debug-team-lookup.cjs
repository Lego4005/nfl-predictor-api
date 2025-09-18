const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('http://localhost:5173');
  await page.waitForTimeout(3000);

  // Inject code to debug team lookup
  const debugInfo = await page.evaluate(() => {
    // Import the team data and getTeam function
    const teamModuleData = window.__TEAM_DEBUG_DATA__ || {};

    // Find a game card component and check its props
    const cards = document.querySelectorAll('.card-mobile, .game-card');
    let gameData = [];

    if (cards.length > 0) {
      // Try to get game data from React fiber (this is a hack but might work)
      for (let i = 0; i < Math.min(3, cards.length); i++) {
        const card = cards[i];
        const fiber = card._reactInternalFiber || card._reactInternals ||
                     Object.keys(card).find(key => key.startsWith('__reactInternalInstance'));

        if (fiber) {
          let currentFiber = typeof fiber === 'string' ? card[fiber] : fiber;
          while (currentFiber) {
            if (currentFiber.memoizedProps && currentFiber.memoizedProps.game) {
              const game = currentFiber.memoizedProps.game;
              gameData.push({
                homeTeam: game.homeTeam,
                awayTeam: game.awayTeam,
                status: game.status
              });
              break;
            }
            currentFiber = currentFiber.return;
          }
        }
      }
    }

    return {
      gameData,
      cardsFound: cards.length
    };
  });

  console.log('Game data extracted:', debugInfo);

  // Now let's test the team lookup directly
  await page.addScriptTag({
    content: `
      // Add debug data to window for team lookup testing
      window.__TEAM_LOOKUP_TEST__ = true;
    `
  });

  const teamLookupTest = await page.evaluate(() => {
    // Test common team abbreviations
    const testTeams = ['KC', 'BUF', 'WAS', 'GB', 'JAX', 'CIN'];
    const results = {};

    // Try to access the getTeam function through the module system
    try {
      // This won't work in browser but let's see what we can access
      results.moduleError = 'Cannot directly import modules in browser';

      // Check if team data is available in global scope
      results.globalData = typeof window.NFL_TEAMS !== 'undefined' ? 'Found' : 'Not found';

      return results;
    } catch (e) {
      return { error: e.message };
    }
  });

  console.log('Team lookup test:', teamLookupTest);

  await browser.close();
})();