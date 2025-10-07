import { test, expect } from '@playwright/test';

test.describe('AI Experts Section - Desktop & Mobile Responsive Tests', () => {

  test.describe('Desktop Layout Tests', () => {

    test('Desktop 1920x1080 - Grid layout with 5 columns', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      // Wait for experts section to be visible
      const expertsHeading = page.locator('text=Meet our top performing AI experts');
      await expect(expertsHeading).toBeVisible();

      // Find the desktop grid container (hidden on mobile, visible on desktop)
      const desktopGrid = page.locator('.hidden.sm\\:grid').first();
      await expect(desktopGrid).toBeVisible();

      // Verify it's a grid layout
      const display = await desktopGrid.evaluate(el => getComputedStyle(el).display);
      expect(display).toBe('grid');

      // Verify grid columns (should be 5 at this breakpoint)
      const gridTemplateColumns = await desktopGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns);
      console.log('1920px Grid columns:', gridTemplateColumns);

      // Should have 5 columns (repeat(5, minmax(0, 1fr)))
      const columnCount = gridTemplateColumns.split(' ').length;
      expect(columnCount).toBe(5);

      // Verify NO horizontal overflow
      const scrollWidth = await desktopGrid.evaluate(el => el.scrollWidth);
      const clientWidth = await desktopGrid.evaluate(el => el.clientWidth);
      console.log('1920px - scrollWidth:', scrollWidth, 'clientWidth:', clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1); // +1 for rounding

      // Verify overflow-x is NOT scroll/auto
      const overflowX = await desktopGrid.evaluate(el => getComputedStyle(el).overflowX);
      expect(overflowX).not.toBe('scroll');
      expect(overflowX).not.toBe('auto');

      // Count expert cards
      const expertCards = await desktopGrid.locator('> div').count();
      console.log('Expert cards visible:', expertCards);
      expect(expertCards).toBe(5);

      // Screenshot
      await page.screenshot({
        path: '/home/iris/code/experimental/nfl-predictor-api/tests/screenshots/desktop-1920-experts.png',
        fullPage: false
      });
    });

    test('Desktop 1440x900 - Grid layout with 4 columns', async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const desktopGrid = page.locator('.hidden.sm\\:grid').first();
      await expect(desktopGrid).toBeVisible();

      const display = await desktopGrid.evaluate(el => getComputedStyle(el).display);
      expect(display).toBe('grid');

      const gridTemplateColumns = await desktopGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns);
      console.log('1440px Grid columns:', gridTemplateColumns);

      // At 1440px (lg breakpoint), should have 5 columns
      const columnCount = gridTemplateColumns.split(' ').length;
      expect(columnCount).toBeGreaterThanOrEqual(4);

      // Verify NO horizontal overflow
      const scrollWidth = await desktopGrid.evaluate(el => el.scrollWidth);
      const clientWidth = await desktopGrid.evaluate(el => el.clientWidth);
      console.log('1440px - scrollWidth:', scrollWidth, 'clientWidth:', clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);

      await page.screenshot({
        path: '/home/iris/code/experimental/nfl-predictor-api/tests/screenshots/desktop-1440-experts.png',
        fullPage: false
      });
    });

    test('Desktop 1024x768 - Grid layout with 4 columns', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const desktopGrid = page.locator('.hidden.sm\\:grid').first();
      await expect(desktopGrid).toBeVisible();

      const display = await desktopGrid.evaluate(el => getComputedStyle(el).display);
      expect(display).toBe('grid');

      const gridTemplateColumns = await desktopGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns);
      console.log('1024px Grid columns:', gridTemplateColumns);

      // At 1024px (md breakpoint), should have 4 columns
      const columnCount = gridTemplateColumns.split(' ').length;
      expect(columnCount).toBe(4);

      // Verify NO horizontal overflow
      const scrollWidth = await desktopGrid.evaluate(el => el.scrollWidth);
      const clientWidth = await desktopGrid.evaluate(el => el.clientWidth);
      console.log('1024px - scrollWidth:', scrollWidth, 'clientWidth:', clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);

      await page.screenshot({
        path: '/home/iris/code/experimental/nfl-predictor-api/tests/screenshots/desktop-1024-experts.png',
        fullPage: false
      });
    });

    test('Desktop - Mobile container should be hidden', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      // Mobile container should be hidden on desktop
      const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();
      const isVisible = await mobileScroll.isVisible();
      expect(isVisible).toBe(false);
    });

    test('Desktop - Max width constraint (7xl)', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const desktopGrid = page.locator('.hidden.sm\\:grid').first();
      const maxWidth = await desktopGrid.evaluate(el => getComputedStyle(el).maxWidth);
      console.log('Max width:', maxWidth);

      // Should have max-width-7xl (80rem = 1280px)
      const classes = await desktopGrid.getAttribute('class');
      expect(classes).toContain('max-w-7xl');
    });
  });

  test.describe('Mobile Layout Tests', () => {

    test('Mobile 390x844 - Horizontal scroll layout', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      // Desktop grid should be hidden on mobile
      const desktopGrid = page.locator('.hidden.sm\\:grid').first();
      const isDesktopVisible = await desktopGrid.isVisible();
      expect(isDesktopVisible).toBe(false);

      // Mobile scroll container should be visible
      const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();
      await expect(mobileScroll).toBeVisible();

      // Verify it's a flex layout
      const display = await mobileScroll.evaluate(el => getComputedStyle(el).display);
      expect(display).toBe('flex');

      // Verify overflow-x is auto or scroll
      const overflowX = await mobileScroll.evaluate(el => getComputedStyle(el).overflowX);
      expect(['auto', 'scroll']).toContain(overflowX);

      // Verify snap behavior
      const scrollSnapType = await mobileScroll.evaluate(el => getComputedStyle(el).scrollSnapType);
      console.log('Scroll snap type:', scrollSnapType);
      expect(scrollSnapType).toContain('x');

      // Verify cards are scrollable (scrollWidth > clientWidth)
      const scrollWidth = await mobileScroll.evaluate(el => el.scrollWidth);
      const clientWidth = await mobileScroll.evaluate(el => el.clientWidth);
      console.log('Mobile - scrollWidth:', scrollWidth, 'clientWidth:', clientWidth);
      expect(scrollWidth).toBeGreaterThan(clientWidth);

      // Count expert cards
      const expertCards = await mobileScroll.locator('> div').count();
      expect(expertCards).toBe(5);

      // Verify card width (should be 280px each)
      const firstCard = mobileScroll.locator('> div').first();
      const cardWidth = await firstCard.evaluate(el => getComputedStyle(el).width);
      console.log('Card width:', cardWidth);
      expect(cardWidth).toBe('280px');

      await page.screenshot({
        path: '/home/iris/code/experimental/nfl-predictor-api/tests/screenshots/mobile-390-experts.png',
        fullPage: false
      });
    });

    test('Mobile 375x667 - Horizontal scroll layout', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();
      await expect(mobileScroll).toBeVisible();

      const display = await mobileScroll.evaluate(el => getComputedStyle(el).display);
      expect(display).toBe('flex');

      const scrollWidth = await mobileScroll.evaluate(el => el.scrollWidth);
      const clientWidth = await mobileScroll.evaluate(el => el.clientWidth);
      console.log('Mobile 375 - scrollWidth:', scrollWidth, 'clientWidth:', clientWidth);
      expect(scrollWidth).toBeGreaterThan(clientWidth);

      await page.screenshot({
        path: '/home/iris/code/experimental/nfl-predictor-api/tests/screenshots/mobile-375-experts.png',
        fullPage: false
      });
    });

    test('Mobile - Touch scroll simulation', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();

      // Get initial scroll position
      const initialScroll = await mobileScroll.evaluate(el => el.scrollLeft);

      // Simulate horizontal scroll
      await mobileScroll.evaluate(el => {
        el.scrollLeft = 300;
      });

      // Wait for scroll
      await page.waitForTimeout(100);

      const finalScroll = await mobileScroll.evaluate(el => el.scrollLeft);
      console.log('Scroll position - initial:', initialScroll, 'final:', finalScroll);

      expect(finalScroll).toBeGreaterThan(initialScroll);
    });

    test('Mobile - Snap points work correctly', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();

      // Verify snap-x and snap-mandatory classes
      const classes = await mobileScroll.getAttribute('class');
      expect(classes).toContain('snap-x');
      expect(classes).toContain('snap-mandatory');

      // Verify children have snap-start
      const firstCard = mobileScroll.locator('> div').first();
      const cardClasses = await firstCard.getAttribute('class');
      expect(cardClasses).toContain('snap-start');
    });

    test('Mobile - Smooth scroll behavior', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:5173');
      await page.waitForLoadState('networkidle');

      const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();

      const scrollBehavior = await mobileScroll.evaluate(el => getComputedStyle(el).scrollBehavior);
      console.log('Scroll behavior:', scrollBehavior);

      // Should have smooth scroll
      const classes = await mobileScroll.getAttribute('class');
      expect(classes).toContain('scroll-smooth');
    });
  });

  test.describe('Regression Verification', () => {

    test('Verify fix: Desktop uses grid NOT horizontal scroll', async ({ page }) => {
      const viewports = [
        { width: 1920, height: 1080, name: '1920x1080' },
        { width: 1440, height: 900, name: '1440x900' },
        { width: 1024, height: 768, name: '1024x768' }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.goto('http://localhost:5173');
        await page.waitForLoadState('networkidle');

        const desktopGrid = page.locator('.hidden.sm\\:grid').first();

        // Should be visible
        await expect(desktopGrid).toBeVisible();

        // Should be grid display
        const display = await desktopGrid.evaluate(el => getComputedStyle(el).display);
        expect(display, `${viewport.name} should use grid display`).toBe('grid');

        // Should NOT have horizontal overflow
        const scrollWidth = await desktopGrid.evaluate(el => el.scrollWidth);
        const clientWidth = await desktopGrid.evaluate(el => el.clientWidth);
        expect(scrollWidth, `${viewport.name} should not overflow horizontally`).toBeLessThanOrEqual(clientWidth + 1);

        // Should NOT be flex
        expect(display, `${viewport.name} should not use flex display`).not.toBe('flex');

        console.log(`✅ ${viewport.name}: Grid layout verified, no overflow`);
      }
    });

    test('Verify mobile still works: Touch-friendly horizontal scroll', async ({ page }) => {
      const viewports = [
        { width: 390, height: 844, name: '390x844' },
        { width: 375, height: 667, name: '375x667' }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.goto('http://localhost:5173');
        await page.waitForLoadState('networkidle');

        const mobileScroll = page.locator('.sm\\:hidden.flex.overflow-x-auto').first();

        // Should be visible
        await expect(mobileScroll).toBeVisible();

        // Should be flex display
        const display = await mobileScroll.evaluate(el => getComputedStyle(el).display);
        expect(display, `${viewport.name} should use flex display`).toBe('flex');

        // Should have horizontal overflow
        const scrollWidth = await mobileScroll.evaluate(el => el.scrollWidth);
        const clientWidth = await mobileScroll.evaluate(el => el.clientWidth);
        expect(scrollWidth, `${viewport.name} should have horizontal overflow`).toBeGreaterThan(clientWidth);

        // Should have snap behavior
        const classes = await mobileScroll.getAttribute('class');
        expect(classes, `${viewport.name} should have snap-x`).toContain('snap-x');

        console.log(`✅ ${viewport.name}: Horizontal scroll verified`);
      }
    });

    test('Full page screenshots - All breakpoints', async ({ page }) => {
      const breakpoints = [
        { width: 1920, height: 1080, name: 'desktop-1920' },
        { width: 1440, height: 900, name: 'desktop-1440' },
        { width: 1024, height: 768, name: 'desktop-1024' },
        { width: 390, height: 844, name: 'mobile-390' },
        { width: 375, height: 667, name: 'mobile-375' }
      ];

      for (const bp of breakpoints) {
        await page.setViewportSize({ width: bp.width, height: bp.height });
        await page.goto('http://localhost:5173');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
          path: `/home/iris/code/experimental/nfl-predictor-api/tests/screenshots/${bp.name}-full.png`,
          fullPage: true
        });

        console.log(`📸 Screenshot captured: ${bp.name}-full.png`);
      }
    });
  });
});
