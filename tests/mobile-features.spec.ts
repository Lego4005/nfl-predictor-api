import { test, expect, devices } from '@playwright/test';

/**
 * Mobile Feature Test Suite
 *
 * Tests both hamburger menu and AI experts horizontal scroll
 * implementations across different viewport sizes.
 */

test.describe('Mobile Hamburger Menu & Drawer', () => {

  test('should show hamburger button on mobile viewports', async ({ page }) => {
    // Set mobile viewport (iPhone 12 - 390x844)
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check hamburger button is visible
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await expect(hamburgerButton).toBeVisible();

    // Verify it has the Menu icon
    await expect(hamburgerButton.locator('svg')).toBeVisible();
  });

  test('should hide hamburger button on desktop viewports', async ({ page }) => {
    // Set desktop viewport (1920x1080)
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');

    await page.waitForLoadState('networkidle');

    // Hamburger should be hidden (lg:hidden class)
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await expect(hamburgerButton).toBeHidden();
  });

  test('should open drawer when hamburger is clicked', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Drawer should be closed initially
    const drawer = page.locator('div.fixed.left-0.top-0.bottom-0').filter({ hasText: 'Navigation' });
    await expect(drawer).toBeHidden();

    // Click hamburger button
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await hamburgerButton.click();

    // Wait for animation
    await page.waitForTimeout(400);

    // Drawer should now be visible
    await expect(drawer).toBeVisible();

    // Check drawer content
    await expect(page.getByText('NFL Predictor')).toBeVisible();
    await expect(page.getByRole('button', { name: /home/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /games/i })).toBeVisible();
  });

  test('should close drawer when backdrop is clicked', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Open drawer
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await hamburgerButton.click();
    await page.waitForTimeout(400);

    // Verify drawer is open
    const drawer = page.locator('div.fixed.left-0.top-0.bottom-0').filter({ hasText: 'Navigation' });
    await expect(drawer).toBeVisible();

    // Click backdrop (the overlay)
    const backdrop = page.locator('div.fixed.inset-0.bg-black\\/60');
    await backdrop.click({ position: { x: 350, y: 400 } }); // Click on right side

    // Wait for animation
    await page.waitForTimeout(400);

    // Drawer should be closed
    await expect(drawer).toBeHidden();
  });

  test('should close drawer when ESC key is pressed', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Open drawer
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await hamburgerButton.click();
    await page.waitForTimeout(400);

    // Verify drawer is open
    const drawer = page.locator('div.fixed.left-0.top-0.bottom-0').filter({ hasText: 'Navigation' });
    await expect(drawer).toBeVisible();

    // Press ESC key
    await page.keyboard.press('Escape');

    // Wait for animation
    await page.waitForTimeout(400);

    // Drawer should be closed
    await expect(drawer).toBeHidden();
  });

  test('should close drawer when X button is clicked', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Open drawer
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await hamburgerButton.click();
    await page.waitForTimeout(400);

    // Click X button
    const closeButton = page.locator('button[aria-label="Close navigation menu"]');
    await closeButton.click();

    // Wait for animation
    await page.waitForTimeout(400);

    // Drawer should be closed
    const drawer = page.locator('div.fixed.left-0.top-0.bottom-0').filter({ hasText: 'Navigation' });
    await expect(drawer).toBeHidden();
  });

  test('should prevent body scroll when drawer is open', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Check body overflow style before opening
    const initialOverflow = await page.evaluate(() => document.body.style.overflow);
    expect(initialOverflow).not.toBe('hidden');

    // Open drawer
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await hamburgerButton.click();
    await page.waitForTimeout(400);

    // Check body overflow is set to hidden
    const overflowWhenOpen = await page.evaluate(() => document.body.style.overflow);
    expect(overflowWhenOpen).toBe('hidden');

    // Close drawer
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    // Check body overflow is restored
    const overflowWhenClosed = await page.evaluate(() => document.body.style.overflow);
    expect(overflowWhenClosed).not.toBe('hidden');
  });

  test('should navigate when drawer item is clicked', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Open drawer
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await hamburgerButton.click();
    await page.waitForTimeout(400);

    // Click on Games navigation item
    const gamesButton = page.locator('button').filter({ hasText: 'GamesGame schedules & scores' });
    await gamesButton.click();

    // Wait for navigation
    await page.waitForTimeout(500);

    // Drawer should close automatically
    const drawer = page.locator('div.fixed.left-0.top-0.bottom-0').filter({ hasText: 'Navigation' });
    await expect(drawer).toBeHidden();

    // Check that we navigated to Games page
    await expect(page.locator('h1')).toContainText('Games');
  });
});

test.describe('AI Experts Horizontal Scroll', () => {

  test('should show AI experts in grid on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Find AI experts section
    const expertsSection = page.locator('div.grid.grid-cols-5').first();

    // Should be visible and use grid layout
    await expect(expertsSection).toBeVisible();

    // Check that grid-cols-5 class is applied
    const classes = await expertsSection.getAttribute('class');
    expect(classes).toContain('grid-cols-5');

    // Verify no horizontal overflow
    const hasHorizontalScroll = await expertsSection.evaluate((el) => {
      return el.scrollWidth > el.clientWidth;
    });
    expect(hasHorizontalScroll).toBe(false);
  });

  test('AI experts section - check if mobile responsive classes exist', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Find AI experts section
    const expertsSection = page.locator('div.grid.grid-cols-5').first();

    // Check current implementation
    const classes = await expertsSection.getAttribute('class');
    console.log('Current classes:', classes);

    // This test will document whether horizontal scroll is implemented
    // Expected: Should have overflow-x-auto or similar on mobile
    const isHorizontalScrollEnabled = classes?.includes('overflow-x');

    console.log('Horizontal scroll enabled:', isHorizontalScrollEnabled);

    // Document findings
    if (!isHorizontalScrollEnabled) {
      console.log('❌ FINDING: AI experts section needs mobile horizontal scroll implementation');
      console.log('   Current: grid-cols-5 (fixed grid)');
      console.log('   Expected: overflow-x-auto with flex/grid on mobile');
    }
  });

  test('should verify sidebar visibility on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Desktop sidebar should be visible
    const sidebar = page.locator('aside').filter({ hasText: 'PickIQ' });
    await expect(sidebar).toBeVisible();

    // Hamburger should NOT be visible
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await expect(hamburgerButton).toBeHidden();
  });

  test('should verify sidebar hidden on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Desktop sidebar should be hidden (has lg:flex class)
    const sidebar = page.locator('aside').filter({ hasText: 'PickIQ' });
    await expect(sidebar).toBeHidden();

    // Hamburger SHOULD be visible
    const hamburgerButton = page.locator('button[aria-label="Toggle mobile menu"]');
    await expect(hamburgerButton).toBeVisible();
  });
});

test.describe('Desktop Regression Tests', () => {

  test('desktop layout unchanged - sidebar and navigation work', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Sidebar visible
    const sidebar = page.locator('aside').filter({ hasText: 'PickIQ' });
    await expect(sidebar).toBeVisible();

    // Navigation items in sidebar work
    const homeButton = sidebar.locator('button').filter({ hasText: 'Home' });
    await expect(homeButton).toBeVisible();

    // Click Games in sidebar
    const gamesButton = sidebar.locator('button').filter({ hasText: 'Games' });
    await gamesButton.click();

    // Should navigate
    await page.waitForTimeout(500);
    await expect(page.locator('h1')).toContainText('Games');

    // No layout shifts
    await expect(sidebar).toBeVisible();
  });

  test('desktop AI experts grid layout', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Experts should be in grid
    const expertsGrid = page.locator('div.grid.grid-cols-5').first();
    await expect(expertsGrid).toBeVisible();

    // Should show 5 experts in a row
    const expertCards = expertsGrid.locator('> div');
    const count = await expertCards.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });
});
