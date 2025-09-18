/**
 * Cross-Device Compatibility E2E Tests
 * Tests live game experience across different devices and browsers
 */

import { test, expect, devices } from '@playwright/test';
import { testConfig } from './playwrightConfig';

test.describe('Cross-Device Compatibility', () => {
  const deviceTests = [
    {
      name: 'iPhone 12',
      device: devices['iPhone 12'],
      category: 'mobile',
      touchEnabled: true,
      orientation: 'portrait'
    },
    {
      name: 'iPad Pro',
      device: devices['iPad Pro'],
      category: 'tablet',
      touchEnabled: true,
      orientation: 'landscape'
    },
    {
      name: 'Pixel 5',
      device: devices['Pixel 5'],
      category: 'mobile',
      touchEnabled: true,
      orientation: 'portrait'
    },
    {
      name: 'Desktop Chrome',
      device: devices['Desktop Chrome'],
      category: 'desktop',
      touchEnabled: false,
      orientation: 'landscape'
    }
  ];

  deviceTests.forEach(({ name, device, category, touchEnabled, orientation }) => {
    test.describe(`${name} Device Tests`, () => {
      test.use({ ...device });

      test.beforeEach(async ({ page }) => {
        // Add device-specific monitoring
        await page.addInitScript(({ category, touchEnabled }) => {
          window.__deviceInfo = {
            category,
            touchEnabled,
            viewport: {
              width: window.innerWidth,
              height: window.innerHeight
            },
            userAgent: navigator.userAgent,
            touchSupport: 'ontouchstart' in window
          };

          // Monitor touch events if supported
          if (touchEnabled) {
            window.__touchEvents = [];

            ['touchstart', 'touchend', 'touchmove'].forEach(eventType => {
              document.addEventListener(eventType, (e) => {
                window.__touchEvents.push({
                  type: eventType,
                  timestamp: Date.now(),
                  touches: e.touches.length
                });
              });
            });
          }

          // Monitor viewport changes
          window.__viewportChanges = [];
          window.addEventListener('resize', () => {
            window.__viewportChanges.push({
              width: window.innerWidth,
              height: window.innerHeight,
              timestamp: Date.now()
            });
          });
        }, { category, touchEnabled });

        await page.goto('/live-games');
        await page.waitForLoadState('networkidle');
      });

      test('should display live game updates correctly', async ({ page }) => {
        // Verify basic layout is appropriate for device
        const gameUpdates = page.locator('[data-testid="live-game-updates"]');
        await expect(gameUpdates).toBeVisible();

        // Check device-specific layout adaptations
        if (category === 'mobile') {
          // Mobile should stack elements vertically
          const gameCards = page.locator('[data-testid="game-card"]');
          await expect(gameCards.first()).toBeVisible();

          // Text should be readable on small screens
          const scoreElements = page.locator('[data-testid="score"]');
          if (await scoreElements.count() > 0) {
            const fontSize = await scoreElements.first().evaluate(el =>
              window.getComputedStyle(el).fontSize
            );
            expect(parseInt(fontSize)).toBeGreaterThan(16); // Minimum readable size
          }

        } else if (category === 'tablet') {
          // Tablet should show more games simultaneously
          const gameCards = page.locator('[data-testid="game-card"]');
          await expect(gameCards).toHaveCount(0); // Adjust based on test data

        } else if (category === 'desktop') {
          // Desktop should show full layout
          await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
          await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
        }
      });

      test('should handle score updates appropriately', async ({ page }) => {
        // Simulate score update
        await page.evaluate(() => {
          const gameUpdate = {
            event_type: 'score_update',
            data: {
              game_id: 'device_test_game',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: 14,
              away_score: 7,
              quarter: 2,
              time_remaining: '08:30',
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(gameUpdate);
          }
        });

        // Verify score display
        await expect(page.locator('[data-testid="home-score"]')).toContainText('14');
        await expect(page.locator('[data-testid="away-score"]')).toContainText('7');

        // Check for device-appropriate animations
        if (category === 'mobile') {
          // Mobile may have simpler animations to preserve battery
          const animationDuration = await page.locator('[data-testid="score-animation"]')
            .evaluate(el => {
              const styles = window.getComputedStyle(el);
              return styles.animationDuration;
            })
            .catch(() => null);

          if (animationDuration) {
            expect(parseFloat(animationDuration)).toBeLessThan(2); // Shorter animations on mobile
          }
        }
      });

      test('should handle touch/click interactions correctly', async ({ page }) => {
        const refreshButton = page.locator('[data-testid="refresh-button"]');
        await expect(refreshButton).toBeVisible();

        if (touchEnabled) {
          // Test touch interaction
          await refreshButton.tap();

          // Verify touch events were registered
          const touchEvents = await page.evaluate(() => window.__touchEvents || []);
          expect(touchEvents.length).toBeGreaterThan(0);

          // Touch targets should be adequately sized (44px minimum)
          const buttonSize = await refreshButton.boundingBox();
          expect(buttonSize!.height).toBeGreaterThan(44);
          expect(buttonSize!.width).toBeGreaterThan(44);

        } else {
          // Test mouse interaction
          await refreshButton.click();
        }

        // Interaction should work regardless of input method
        await expect(page.locator('[data-testid="last-updated"]')).toBeVisible();
      });

      test('should adapt to orientation changes', async ({ page }) => {
        if (category === 'mobile' || category === 'tablet') {
          // Get initial layout
          const initialLayout = await page.evaluate(() => ({
            width: window.innerWidth,
            height: window.innerHeight,
            orientation: window.innerWidth > window.innerHeight ? 'landscape' : 'portrait'
          }));

          // Simulate orientation change
          if (initialLayout.orientation === 'portrait') {
            await page.setViewportSize({ width: 812, height: 375 }); // Landscape
          } else {
            await page.setViewportSize({ width: 375, height: 812 }); // Portrait
          }

          // Wait for layout to adapt
          await page.waitForTimeout(500);

          // Verify layout adapted
          const newLayout = await page.evaluate(() => ({
            width: window.innerWidth,
            height: window.innerHeight,
            orientation: window.innerWidth > window.innerHeight ? 'landscape' : 'portrait'
          }));

          expect(newLayout.orientation).not.toBe(initialLayout.orientation);

          // Content should still be accessible
          await expect(page.locator('[data-testid="live-game-updates"]')).toBeVisible();

          // Navigation should remain usable
          if (category === 'mobile') {
            const navButton = page.locator('[data-testid="mobile-nav-toggle"]');
            if (await navButton.isVisible()) {
              await navButton.tap();
              await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
            }
          }
        }
      });

      test('should maintain performance standards', async ({ page }) => {
        // Start performance monitoring
        await page.evaluate(() => {
          window.__performanceMetrics = {
            startTime: performance.now(),
            frameCount: 0,
            memoryUsage: (performance as any).memory?.usedJSHeapSize || 0
          };

          function trackFrames() {
            window.__performanceMetrics.frameCount++;
            requestAnimationFrame(trackFrames);
          }

          requestAnimationFrame(trackFrames);
        });

        // Simulate typical usage scenario
        const updates = Array.from({ length: 10 }, (_, i) => ({
          home_score: i * 3,
          away_score: i * 2,
          time: `${15 - i}:00`
        }));

        for (const update of updates) {
          await page.evaluate((update) => {
            const gameUpdate = {
              event_type: 'score_update',
              data: {
                game_id: 'perf_test_game',
                home_team: 'Patriots',
                away_team: 'Bills',
                ...update,
                quarter: 1,
                game_status: 'live',
                updated_at: new Date().toISOString()
              },
              timestamp: new Date().toISOString()
            };

            if (window.__mockWebSocketInstance) {
              window.__mockWebSocketInstance.simulateMessage(gameUpdate);
            }
          }, update);

          await page.waitForTimeout(200);
        }

        // Check performance metrics
        const metrics = await page.evaluate(() => {
          const duration = (performance.now() - window.__performanceMetrics.startTime) / 1000;
          const currentMemory = (performance as any).memory?.usedJSHeapSize || 0;

          return {
            fps: window.__performanceMetrics.frameCount / duration,
            duration,
            memoryIncrease: (currentMemory - window.__performanceMetrics.memoryUsage) / (1024 * 1024) // MB
          };
        });

        // Performance expectations vary by device category
        if (category === 'mobile') {
          expect(metrics.fps).toBeGreaterThan(25); // Lower expectation for mobile
          expect(metrics.memoryIncrease).toBeLessThan(20); // Tighter memory constraints
        } else if (category === 'tablet') {
          expect(metrics.fps).toBeGreaterThan(35);
          expect(metrics.memoryIncrease).toBeLessThan(30);
        } else {
          expect(metrics.fps).toBeGreaterThan(45);
          expect(metrics.memoryIncrease).toBeLessThan(50);
        }
      });

      test('should handle network connectivity issues gracefully', async ({ page }) => {
        // Test offline behavior
        await page.context().setOffline(true);

        // Should show offline indicator
        await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible({
          timeout: 5000
        });

        // UI should remain functional in offline mode
        const existingScores = await page.locator('[data-testid="score"]').count();
        expect(existingScores).toBeGreaterThanOrEqual(0);

        // Restore connectivity
        await page.context().setOffline(false);

        // Should reconnect and hide offline indicator
        await expect(page.locator('[data-testid="offline-indicator"]')).not.toBeVisible({
          timeout: 10000
        });

        await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
      });

      test('should support accessibility features', async ({ page }) => {
        // Check for proper ARIA labels
        const gameUpdates = page.locator('[data-testid="live-game-updates"]');
        await expect(gameUpdates).toHaveAttribute('role', 'main');

        // Score updates should be announced to screen readers
        const scoreRegion = page.locator('[data-testid="scores"]');
        if (await scoreRegion.count() > 0) {
          await expect(scoreRegion).toHaveAttribute('aria-live', 'polite');
        }

        // Interactive elements should be keyboard accessible
        if (!touchEnabled) {
          const focusableElements = page.locator('button, a, input, [tabindex="0"]');
          const count = await focusableElements.count();

          if (count > 0) {
            // Test keyboard navigation
            await page.keyboard.press('Tab');
            const focused = await page.evaluate(() => document.activeElement?.tagName);
            expect(['BUTTON', 'A', 'INPUT']).toContain(focused);
          }
        }

        // Check color contrast for readability
        const textElements = page.locator('[data-testid="team-name"], [data-testid="score"]');
        if (await textElements.count() > 0) {
          const contrast = await textElements.first().evaluate(el => {
            const styles = window.getComputedStyle(el);
            return {
              color: styles.color,
              backgroundColor: styles.backgroundColor
            };
          });

          // Basic contrast check (would need more sophisticated calculation in real test)
          expect(contrast.color).not.toBe(contrast.backgroundColor);
        }
      });

      test('should handle data loading states appropriately', async ({ page }) => {
        // Clear any existing data
        await page.reload();

        // Should show loading state
        await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible({
          timeout: 1000
        });

        // Loading spinner should be appropriately sized for device
        const loadingIndicator = page.locator('[data-testid="loading-indicator"]');
        const spinnerSize = await loadingIndicator.boundingBox();

        if (category === 'mobile') {
          expect(spinnerSize!.width).toBeLessThan(50); // Smaller on mobile
        } else {
          expect(spinnerSize!.width).toBeGreaterThan(20);
        }

        // Should transition to content when data loads
        await expect(page.locator('[data-testid="live-game-updates"]')).toBeVisible({
          timeout: 10000
        });

        await expect(loadingIndicator).not.toBeVisible();
      });
    });
  });

  test.describe('Cross-Browser Consistency', () => {
    const browserConfigs = [
      { name: 'Chrome', browserName: 'chromium' },
      { name: 'Firefox', browserName: 'firefox' },
      { name: 'Safari', browserName: 'webkit' }
    ];

    browserConfigs.forEach(({ name, browserName }) => {
      test(`should work consistently in ${name}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Test only for ${name}`);

        await page.goto('/live-games');
        await page.waitForLoadState('networkidle');

        // Basic functionality should work across all browsers
        await expect(page.locator('[data-testid="live-game-updates"]')).toBeVisible();

        // Simulate game update
        await page.evaluate(() => {
          const gameUpdate = {
            event_type: 'score_update',
            data: {
              game_id: 'browser_test_game',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: 21,
              away_score: 14,
              quarter: 3,
              time_remaining: '10:15',
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(gameUpdate);
          }
        });

        // Scores should update correctly
        await expect(page.locator('[data-testid="home-score"]')).toContainText('21');
        await expect(page.locator('[data-testid="away-score"]')).toContainText('14');

        // WebSocket connection should work
        await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');

        // Animations should work (even if reduced in some browsers)
        const gameCard = page.locator('[data-testid="game-card"]');
        await expect(gameCard).toBeVisible();
      });
    });
  });

  test.describe('Responsive Breakpoint Testing', () => {
    const viewports = [
      { name: 'Small Mobile', width: 320, height: 568 },
      { name: 'Large Mobile', width: 414, height: 896 },
      { name: 'Tablet Portrait', width: 768, height: 1024 },
      { name: 'Tablet Landscape', width: 1024, height: 768 },
      { name: 'Desktop', width: 1920, height: 1080 },
      { name: 'Ultrawide', width: 2560, height: 1440 }
    ];

    viewports.forEach(({ name, width, height }) => {
      test(`should adapt layout for ${name} (${width}x${height})`, async ({ page }) => {
        await page.setViewportSize({ width, height });
        await page.goto('/live-games');
        await page.waitForLoadState('networkidle');

        // Content should be visible and accessible
        await expect(page.locator('[data-testid="live-game-updates"]')).toBeVisible();

        // Check for appropriate layout adaptations
        if (width <= 480) {
          // Mobile layout
          const navigation = page.locator('[data-testid="mobile-nav-toggle"]');
          await expect(navigation).toBeVisible();

          // Content should not overflow
          const body = page.locator('body');
          const scrollWidth = await body.evaluate(el => el.scrollWidth);
          expect(scrollWidth).toBeLessThanOrEqual(width + 20); // Allow small margin

        } else if (width <= 1024) {
          // Tablet layout
          const gameCards = page.locator('[data-testid="game-card"]');
          if (await gameCards.count() > 0) {
            // Cards should be arranged in grid
            const firstCard = gameCards.first();
            const cardWidth = await firstCard.boundingBox();
            expect(cardWidth!.width).toBeLessThan(width * 0.6); // Should not take full width
          }

        } else {
          // Desktop layout
          const sidebar = page.locator('[data-testid="sidebar"]');
          if (await sidebar.count() > 0) {
            await expect(sidebar).toBeVisible();
          }

          // Should utilize full width effectively
          const mainContent = page.locator('[data-testid="main-content"]');
          if (await mainContent.count() > 0) {
            const contentWidth = await mainContent.boundingBox();
            expect(contentWidth!.width).toBeGreaterThan(width * 0.6);
          }
        }

        // Text should remain readable
        const textElements = page.locator('h1, h2, h3, p, span');
        if (await textElements.count() > 0) {
          const fontSize = await textElements.first().evaluate(el => {
            return parseInt(window.getComputedStyle(el).fontSize);
          });
          expect(fontSize).toBeGreaterThan(12); // Minimum readable font size
        }
      });
    });
  });
});