import { test, expect } from '@playwright/test';

test.describe('Desktop Regression Tests', () => {
  test('Desktop layout at 1440px', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: '/home/iris/code/experimental/nfl-predictor-api/tests/desktop-1440.png', fullPage: true });

    // Check sidebar visible
    const sidebar = page.locator('aside').first();
    await expect(sidebar).toBeVisible();

    // Check AI experts section
    const expertsSection = page.locator('text=Meet our top performing AI experts').locator('..');
    await expect(expertsSection).toBeVisible();

    // Check grid layout (not horizontal scroll)
    const expertsContainer = expertsSection.locator('+ div').first();
    const containerClass = await expertsContainer.getAttribute('class');
    console.log('Experts container classes:', containerClass);

    // Should be grid on desktop, not flex
    expect(containerClass).toContain('grid');
    expect(containerClass).not.toContain('flex-nowrap');
  });

  test('AI Experts Grid on Desktop at 1920px', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');

    // Find AI experts section
    const expertsGrid = page.locator('.experts-scroll').first();
    const classes = await expertsGrid.getAttribute('class');

    console.log('=== AI EXPERTS GRID CLASSES ===');
    console.log(classes);

    // Check computed styles
    const display = await expertsGrid.evaluate(el => getComputedStyle(el).display);
    const gridTemplateColumns = await expertsGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns);
    const overflowX = await expertsGrid.evaluate(el => getComputedStyle(el).overflowX);

    console.log('Display:', display);
    console.log('Grid columns:', gridTemplateColumns);
    console.log('Overflow X:', overflowX);

    // Should be grid with 5 columns on desktop
    expect(display).toBe('grid');
  });

  test('Detailed AI Experts Layout Analysis', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: '/home/iris/code/experimental/nfl-predictor-api/tests/desktop-experts-section.png', fullPage: false });

    // Find the AI experts container
    const expertsSection = page.locator('text=Meet our top performing AI experts');
    await expect(expertsSection).toBeVisible();

    // Get the parent container
    const parentContainer = expertsSection.locator('../..');
    const parentClass = await parentContainer.getAttribute('class');
    console.log('=== PARENT CONTAINER ===');
    console.log('Classes:', parentClass);

    // Get the grid/scroll container (should be the next sibling or child)
    const scrollContainer = page.locator('.experts-scroll').first();
    const scrollClass = await scrollContainer.getAttribute('class');
    console.log('=== SCROLL CONTAINER ===');
    console.log('Classes:', scrollClass);

    // Check all computed styles
    const styles = await scrollContainer.evaluate(el => {
      const computed = getComputedStyle(el);
      return {
        display: computed.display,
        gridTemplateColumns: computed.gridTemplateColumns,
        gridAutoFlow: computed.gridAutoFlow,
        overflowX: computed.overflowX,
        flexDirection: computed.flexDirection,
        flexWrap: computed.flexWrap,
        gap: computed.gap,
        width: computed.width
      };
    });

    console.log('=== COMPUTED STYLES ===');
    console.log(JSON.stringify(styles, null, 2));

    // Count visible expert cards
    const expertCards = await scrollContainer.locator('.expert-card, [class*="expert"]').count();
    console.log('Number of expert cards found:', expertCards);

    // Check if cards are overflowing horizontally
    const scrollWidth = await scrollContainer.evaluate(el => el.scrollWidth);
    const clientWidth = await scrollContainer.evaluate(el => el.clientWidth);
    console.log('Scroll width:', scrollWidth);
    console.log('Client width:', clientWidth);
    console.log('Is overflowing:', scrollWidth > clientWidth);
  });

  test('Full Page Desktop Screenshot', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: '/home/iris/code/experimental/nfl-predictor-api/tests/desktop-1920-full.png',
      fullPage: true
    });
  });

  test('Check Responsive Breakpoints', async ({ page }) => {
    const breakpoints = [
      { width: 1920, name: 'xl' },
      { width: 1440, name: 'lg' },
      { width: 1024, name: 'md' },
      { width: 768, name: 'sm' }
    ];

    for (const bp of breakpoints) {
      await page.setViewportSize({ width: bp.width, height: 900 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const expertsGrid = page.locator('.experts-scroll').first();
      const display = await expertsGrid.evaluate(el => getComputedStyle(el).display);
      const gridCols = await expertsGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns);

      console.log(`=== ${bp.name} (${bp.width}px) ===`);
      console.log('Display:', display);
      console.log('Grid columns:', gridCols);

      await page.screenshot({
        path: `/home/iris/code/experimental/nfl-predictor-api/tests/desktop-${bp.width}.png`,
        fullPage: false
      });
    }
  });
});
