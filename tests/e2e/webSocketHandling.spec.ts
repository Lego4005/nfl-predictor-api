/**
 * WebSocket Connection Handling E2E Tests
 * Tests WebSocket reliability, reconnection, and error handling
 */

import { test, expect, Page } from '@playwright/test';
import { testConfig } from './playwrightConfig';

test.describe('WebSocket Connection Handling', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Inject WebSocket monitoring
    await page.addInitScript(() => {
      window.__webSocketEvents = [];
      window.__webSocketInstances = [];

      // Monitor WebSocket events
      const OriginalWebSocket = window.WebSocket;

      class MonitoredWebSocket extends OriginalWebSocket {
        constructor(url: string, protocols?: string | string[]) {
          super(url, protocols);

          window.__webSocketInstances.push(this);

          // Monitor all events
          this.addEventListener('open', (event) => {
            window.__webSocketEvents.push({ type: 'open', timestamp: Date.now(), url });
          });

          this.addEventListener('close', (event) => {
            window.__webSocketEvents.push({
              type: 'close',
              timestamp: Date.now(),
              code: event.code,
              reason: event.reason,
              url
            });
          });

          this.addEventListener('error', (event) => {
            window.__webSocketEvents.push({ type: 'error', timestamp: Date.now(), url });
          });

          this.addEventListener('message', (event) => {
            window.__webSocketEvents.push({
              type: 'message',
              timestamp: Date.now(),
              data: event.data,
              url
            });
          });

          // Monitor state changes
          const originalSend = this.send;
          this.send = function(data) {
            window.__webSocketEvents.push({
              type: 'send',
              timestamp: Date.now(),
              data,
              readyState: this.readyState,
              url
            });
            return originalSend.call(this, data);
          };
        }
      }

      window.WebSocket = MonitoredWebSocket as any;
    });

    await page.goto('/live-games/test');
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('Connection Establishment', () => {
    test('should establish WebSocket connection on page load', async () => {
      // Wait for WebSocket connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      }, { timeout: 10000 });

      const events = await page.evaluate(() => window.__webSocketEvents);
      const openEvents = events.filter((event: any) => event.type === 'open');

      expect(openEvents).toHaveLength(1);
      expect(openEvents[0].url).toContain('ws://');

      // Verify connection status indicator
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
    });

    test('should handle connection timeout gracefully', async () => {
      // Simulate slow connection by blocking WebSocket requests
      await page.route('**/*', async (route) => {
        const url = route.request().url();
        if (url.startsWith('ws://')) {
          // Delay WebSocket connections
          await new Promise(resolve => setTimeout(resolve, 5000));
          route.continue();
        } else {
          route.continue();
        }
      });

      await page.reload();

      // Should show connecting state
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connecting');

      // Should eventually timeout and show error
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connection timeout', {
        timeout: 15000
      });
    });

    test('should retry connection on initial failure', async () => {
      // Block first connection attempt
      let connectionAttempts = 0;
      await page.route('**/*', async (route) => {
        const url = route.request().url();
        if (url.startsWith('ws://')) {
          connectionAttempts++;
          if (connectionAttempts === 1) {
            route.abort('failed');
          } else {
            route.continue();
          }
        } else {
          route.continue();
        }
      });

      await page.reload();

      // Should eventually connect after retry
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      }, { timeout: 20000 });

      const events = await page.evaluate(() => window.__webSocketEvents);
      const errorEvents = events.filter((event: any) => event.type === 'error');

      expect(errorEvents.length).toBeGreaterThan(0);
      expect(connectionAttempts).toBeGreaterThan(1);
    });
  });

  test.describe('Connection Loss and Reconnection', () => {
    test('should detect connection loss', async () => {
      // Wait for initial connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Simulate connection loss
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].close(1006, 'Connection lost');
        }
      });

      // Should detect disconnection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'close');
      });

      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Disconnected');
    });

    test('should automatically reconnect after connection loss', async () => {
      // Wait for initial connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      const initialOpenEvents = await page.evaluate(() =>
        window.__webSocketEvents.filter((event: any) => event.type === 'open').length
      );

      // Simulate connection loss
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].close(1006, 'Connection lost');
        }
      });

      // Wait for reconnection
      await page.waitForFunction(() => {
        const openEvents = window.__webSocketEvents.filter((event: any) => event.type === 'open');
        return openEvents.length > initialOpenEvents;
      }, { timeout: 15000 });

      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');

      const finalEvents = await page.evaluate(() => window.__webSocketEvents);
      const closeEvents = finalEvents.filter((event: any) => event.type === 'close');
      const openEvents = finalEvents.filter((event: any) => event.type === 'open');

      expect(closeEvents.length).toBeGreaterThan(0);
      expect(openEvents.length).toBe(2); // Initial + reconnection
    });

    test('should show reconnection progress', async () => {
      // Wait for initial connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Simulate connection loss
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].close(1006, 'Connection lost');
        }
      });

      // Should show reconnecting status
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Reconnecting');

      // May show attempt count
      await expect(page.locator('[data-testid="reconnection-attempts"]')).toBeVisible({ timeout: 5000 });
    });

    test('should handle multiple rapid disconnections', async () => {
      // Wait for initial connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Simulate multiple rapid disconnections
      for (let i = 0; i < 3; i++) {
        await page.evaluate(() => {
          const instances = window.__webSocketInstances;
          const lastInstance = instances[instances.length - 1];
          if (lastInstance && lastInstance.readyState === WebSocket.OPEN) {
            lastInstance.close(1006, 'Rapid disconnect');
          }
        });

        await page.waitForTimeout(1000);
      }

      // Should eventually stabilize connection
      await page.waitForFunction(() => {
        const events = window.__webSocketEvents;
        const recentEvents = events.slice(-10);
        return recentEvents.some((event: any) => event.type === 'open');
      }, { timeout: 20000 });

      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
    });
  });

  test.describe('Message Handling During Connection Issues', () => {
    test('should queue messages during disconnection', async () => {
      // Wait for initial connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Simulate disconnection
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].close(1006, 'Connection lost');
        }
      });

      // Try to subscribe to a channel while disconnected
      await page.click('[data-testid="subscribe-game"]');

      // Check that messages were queued
      const queuedMessages = await page.evaluate(() => {
        // This would depend on the actual implementation
        return window.__queuedWebSocketMessages || [];
      });

      // Should have queued subscription message
      expect(queuedMessages.length).toBeGreaterThan(0);
    });

    test('should process queued messages after reconnection', async () => {
      // Similar to above test but verify messages are sent after reconnection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Track sent messages
      const initialSentCount = await page.evaluate(() => {
        return window.__webSocketEvents.filter((event: any) => event.type === 'send').length;
      });

      // Disconnect and queue messages
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].close(1006, 'Connection lost');
        }
      });

      await page.click('[data-testid="subscribe-game"]');
      await page.click('[data-testid="subscribe-predictions"]');

      // Wait for reconnection
      await page.waitForFunction(() => {
        const openEvents = window.__webSocketEvents.filter((event: any) => event.type === 'open');
        return openEvents.length >= 2;
      }, { timeout: 15000 });

      // Check that queued messages were sent
      const finalSentCount = await page.evaluate(() => {
        return window.__webSocketEvents.filter((event: any) => event.type === 'send').length;
      });

      expect(finalSentCount).toBeGreaterThan(initialSentCount);
    });

    test('should handle message backlog after long disconnection', async () => {
      // Connect initially
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Simulate long disconnection (30 seconds of messages missed)
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].close(1006, 'Long disconnection');
        }
      });

      // Wait to simulate missed messages
      await page.waitForTimeout(3000);

      // Reconnect
      await page.waitForFunction(() => {
        const openEvents = window.__webSocketEvents.filter((event: any) => event.type === 'open');
        return openEvents.length >= 2;
      }, { timeout: 15000 });

      // Should request catch-up data or handle backlog
      await expect(page.locator('[data-testid="syncing-data"]')).toBeVisible({ timeout: 5000 });

      // Should eventually show current data
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
      await expect(page.locator('[data-testid="syncing-data"]')).not.toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Error Handling', () => {
    test('should handle WebSocket protocol errors', async () => {
      // Inject WebSocket error simulation
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          instances[0].dispatchEvent(new Event('error'));
        }
      });

      await expect(page.locator('[data-testid="connection-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Connection error');
    });

    test('should handle malformed message data', async () => {
      // Wait for connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Send malformed JSON
      await page.evaluate(() => {
        const instances = window.__webSocketInstances;
        if (instances.length > 0) {
          const event = new MessageEvent('message', {
            data: 'invalid json {'
          });
          instances[0].dispatchEvent(event);
        }
      });

      // Should handle error gracefully without crashing
      await expect(page.locator('[data-testid="live-game-updates"]')).toBeVisible();

      // Error should be logged but not displayed to user
      const errorLogs = await page.evaluate(() => {
        return window.__messageParsingErrors || [];
      });

      // Implementation would track parsing errors
    });

    test('should handle server-side disconnection codes', async () => {
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Test different disconnect codes
      const disconnectCodes = [
        { code: 1001, reason: 'Going away', shouldReconnect: true },
        { code: 1006, reason: 'Abnormal closure', shouldReconnect: true },
        { code: 1008, reason: 'Policy violation', shouldReconnect: false },
        { code: 1011, reason: 'Server error', shouldReconnect: true }
      ];

      for (const { code, reason, shouldReconnect } of disconnectCodes) {
        // Reset connection
        await page.reload();
        await page.waitForFunction(() => {
          return window.__webSocketEvents.some((event: any) => event.type === 'open');
        });

        // Simulate server disconnect
        await page.evaluate(({ code, reason }) => {
          const instances = window.__webSocketInstances;
          if (instances.length > 0) {
            instances[0].close(code, reason);
          }
        }, { code, reason });

        if (shouldReconnect) {
          // Should attempt reconnection
          await expect(page.locator('[data-testid="connection-status"]')).toContainText('Reconnecting');
        } else {
          // Should show permanent error
          await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connection failed');
        }
      }
    });
  });

  test.describe('Performance Under Connection Stress', () => {
    test('should maintain UI responsiveness during connection issues', async () => {
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      });

      // Start performance monitoring
      await page.evaluate(() => {
        window.__performanceStart = performance.now();
        window.__interactions = [];
      });

      // Simulate rapid connection issues
      for (let i = 0; i < 5; i++) {
        await page.evaluate(() => {
          const instances = window.__webSocketInstances;
          const lastInstance = instances[instances.length - 1];
          if (lastInstance) {
            lastInstance.close(1006, 'Stress test');
          }
        });

        // Try to interact with UI during reconnection
        const startTime = await page.evaluate(() => performance.now());
        await page.click('[data-testid="refresh-data"]');
        const endTime = await page.evaluate(() => performance.now());

        await page.evaluate((duration) => {
          window.__interactions.push(duration);
        }, endTime - startTime);

        await page.waitForTimeout(500);
      }

      // Check UI responsiveness
      const interactions = await page.evaluate(() => window.__interactions);
      const avgResponseTime = interactions.reduce((sum: number, time: number) => sum + time, 0) / interactions.length;

      expect(avgResponseTime).toBeLessThan(200); // UI should remain responsive (under 200ms)
    });

    test('should handle concurrent connection attempts', async () => {
      // Block initial connection
      await page.route('**/*', async (route) => {
        const url = route.request().url();
        if (url.startsWith('ws://')) {
          await new Promise(resolve => setTimeout(resolve, 2000));
          route.continue();
        } else {
          route.continue();
        }
      });

      // Trigger multiple connection attempts
      const promises = [];
      for (let i = 0; i < 3; i++) {
        promises.push(
          page.evaluate(() => {
            // This would trigger additional connection attempts
            window.dispatchEvent(new Event('online'));
          })
        );
      }

      await Promise.all(promises);

      // Should eventually establish only one connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      }, { timeout: 15000 });

      const events = await page.evaluate(() => window.__webSocketEvents);
      const openEvents = events.filter((event: any) => event.type === 'open');

      // Should not create duplicate connections
      expect(openEvents.length).toBe(1);
    });
  });

  test.describe('Network Condition Simulation', () => {
    test('should handle slow network conditions', async () => {
      // Simulate slow network
      await page.route('**/*', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        route.continue();
      });

      const startTime = Date.now();

      await page.reload();

      // Should eventually connect despite slow network
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      }, { timeout: 20000 });

      const connectionTime = Date.now() - startTime;
      expect(connectionTime).toBeGreaterThan(1000); // Should reflect slow network

      // Should show appropriate loading states
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
    });

    test('should handle intermittent connectivity', async () => {
      let requestCount = 0;

      await page.route('**/*', async (route) => {
        requestCount++;
        // Fail every 3rd request
        if (requestCount % 3 === 0) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      await page.reload();

      // Should eventually establish stable connection
      await page.waitForFunction(() => {
        return window.__webSocketEvents.some((event: any) => event.type === 'open');
      }, { timeout: 30000 });

      const events = await page.evaluate(() => window.__webSocketEvents);
      const errorEvents = events.filter((event: any) => event.type === 'error');

      // Should have encountered errors but eventually succeeded
      expect(errorEvents.length).toBeGreaterThan(0);
    });
  });
});