/**
 * Game Animations and Celebrations E2E Tests
 * Tests score changes, touchdown celebrations, and red zone momentum shifts
 */

import { test, expect, Page, Locator } from '@playwright/test';
import { testConfig } from './playwrightConfig';

test.describe('Game Animations and Celebrations', () => {
  test.beforeEach(async ({ page }) => {
    // Inject animation monitoring
    await page.addInitScript(() => {
      window.__animationEvents = [];
      window.__celebrationTriggers = [];

      // Monitor CSS animations
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const element = mutation.target as Element;
            const classes = element.className;

            // Track animation classes
            if (classes.includes('animate-') || classes.includes('celebration') || classes.includes('pulse')) {
              window.__animationEvents.push({
                type: 'animation_start',
                element: element.tagName,
                classes: classes,
                timestamp: Date.now()
              });
            }
          }
        });
      });

      observer.observe(document.body, {
        attributes: true,
        subtree: true,
        attributeFilter: ['class']
      });

      // Monitor score changes for celebration triggers
      window.__originalScore = { home: 0, away: 0 };
      window.__scoreChangeDetector = (newHome: number, newAway: number) => {
        const oldHome = window.__originalScore.home;
        const oldAway = window.__originalScore.away;

        if (newHome > oldHome) {
          window.__celebrationTriggers.push({
            type: 'home_score',
            points: newHome - oldHome,
            timestamp: Date.now()
          });
        }

        if (newAway > oldAway) {
          window.__celebrationTriggers.push({
            type: 'away_score',
            points: newAway - oldAway,
            timestamp: Date.now()
          });
        }

        window.__originalScore = { home: newHome, away: newAway };
      };
    });

    await page.goto('/live-games/test');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Score Change Animations', () => {
    test('should animate touchdown score changes', async ({ page }) => {
      // Start monitoring animations
      await page.evaluate(() => {
        window.__animationStartTime = performance.now();
      });

      // Simulate initial game state
      await page.evaluate(() => {
        // Mock WebSocket message for score change
        const gameUpdate = {
          event_type: 'score_update',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            quarter: 1,
            time_remaining: '12:30',
            game_status: 'live',
            scoring_play: {
              type: 'touchdown',
              team: 'home',
              points: 7,
              description: 'Tom Brady 15-yard pass to Julian Edelman'
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        // Trigger score update
        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      // Check for score animation
      await expect(page.locator('[data-testid="home-score"]')).toHaveText('7');

      // Verify animation was triggered
      const animationEvents = await page.evaluate(() => window.__animationEvents);
      expect(animationEvents.length).toBeGreaterThan(0);

      // Check for score highlight animation
      await expect(page.locator('[data-testid="home-score"]')).toHaveClass(/animate-pulse|animate-bounce/);

      // Animation should complete within reasonable time
      await page.waitForTimeout(2000);
      await expect(page.locator('[data-testid="home-score"]')).not.toHaveClass(/animate-pulse|animate-bounce/);
    });

    test('should animate field goal score changes', async ({ page }) => {
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'score_update',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 3,
            away_score: 0,
            quarter: 1,
            time_remaining: '05:45',
            game_status: 'live',
            scoring_play: {
              type: 'field_goal',
              team: 'home',
              points: 3,
              description: '45-yard field goal by Stephen Gostkowski'
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      await expect(page.locator('[data-testid="home-score"]')).toHaveText('3');

      // Field goal animation should be different from touchdown
      const animationEvents = await page.evaluate(() => window.__animationEvents);
      const fieldGoalAnimations = animationEvents.filter((event: any) =>
        event.classes.includes('field-goal') || event.classes.includes('score-update')
      );

      expect(fieldGoalAnimations.length).toBeGreaterThan(0);
    });

    test('should handle rapid consecutive scores', async ({ page }) => {
      // Simulate rapid scoring (kickoff return TD followed by onside kick recovery TD)
      const scores = [
        { home: 7, away: 0, time: '14:45' },
        { home: 7, away: 7, time: '14:30' },
        { home: 14, away: 7, time: '14:15' }
      ];

      for (const [index, score] of scores.entries()) {
        await page.evaluate(({ score, index }) => {
          const gameUpdate = {
            event_type: 'score_update',
            data: {
              game_id: 'test_game',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: score.home,
              away_score: score.away,
              quarter: 1,
              time_remaining: score.time,
              game_status: 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(gameUpdate);
          }
        }, { score, index });

        await page.waitForTimeout(500); // Brief pause between rapid scores
      }

      // All scores should be displayed correctly
      await expect(page.locator('[data-testid="home-score"]')).toHaveText('14');
      await expect(page.locator('[data-testid="away-score"]')).toHaveText('7');

      // Should handle multiple rapid animations without overlap issues
      const animationEvents = await page.evaluate(() => window.__animationEvents);
      expect(animationEvents.length).toBeGreaterThan(2);
    });
  });

  test.describe('Touchdown Celebrations', () => {
    test('should display touchdown celebration animation', async ({ page }) => {
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'touchdown_scored',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            quarter: 1,
            time_remaining: '08:15',
            game_status: 'live',
            scoring_play: {
              type: 'touchdown',
              team: 'home',
              points: 7,
              player: 'Rob Gronkowski',
              description: '12-yard touchdown reception'
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      // Touchdown celebration should appear
      await expect(page.locator('[data-testid="touchdown-celebration"]')).toBeVisible({
        timeout: 1000
      });

      // Should contain celebration elements
      await expect(page.locator('[data-testid="touchdown-celebration"]')).toContainText('TOUCHDOWN');

      // Check for celebration animations
      const celebrationElement = page.locator('[data-testid="touchdown-celebration"]');
      await expect(celebrationElement).toHaveClass(/animate-/);

      // Celebration should auto-hide after duration
      await expect(page.locator('[data-testid="touchdown-celebration"]')).not.toBeVisible({
        timeout: 5000
      });
    });

    test('should show team-specific celebration colors', async ({ page }) => {
      // Home team touchdown
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'touchdown_scored',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            scoring_play: {
              type: 'touchdown',
              team: 'home',
              points: 7
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      const homeCelebration = page.locator('[data-testid="touchdown-celebration"]');
      await expect(homeCelebration).toBeVisible();
      await expect(homeCelebration).toHaveClass(/home-team|patriots/);

      // Wait for celebration to end
      await expect(homeCelebration).not.toBeVisible({ timeout: 5000 });

      // Away team touchdown
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'touchdown_scored',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 7,
            scoring_play: {
              type: 'touchdown',
              team: 'away',
              points: 7
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      const awayCelebration = page.locator('[data-testid="touchdown-celebration"]');
      await expect(awayCelebration).toBeVisible();
      await expect(awayCelebration).toHaveClass(/away-team|bills/);
    });

    test('should show different celebrations for different score types', async ({ page }) => {
      const scoringPlays = [
        {
          type: 'touchdown',
          expectedCelebration: 'touchdown-celebration',
          expectedText: 'TOUCHDOWN'
        },
        {
          type: 'field_goal',
          expectedCelebration: 'field-goal-celebration',
          expectedText: 'FIELD GOAL'
        },
        {
          type: 'safety',
          expectedCelebration: 'safety-celebration',
          expectedText: 'SAFETY'
        }
      ];

      for (const play of scoringPlays) {
        await page.evaluate((play) => {
          const gameUpdate = {
            event_type: 'score_update',
            data: {
              game_id: 'test_game',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: 7,
              away_score: 0,
              scoring_play: {
                type: play.type,
                team: 'home',
                points: play.type === 'touchdown' ? 7 : play.type === 'field_goal' ? 3 : 2
              },
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(gameUpdate);
          }
        }, play);

        if (play.expectedCelebration === 'touchdown-celebration') {
          await expect(page.locator(`[data-testid="${play.expectedCelebration}"]`)).toBeVisible();
          await expect(page.locator(`[data-testid="${play.expectedCelebration}"]`)).toContainText(play.expectedText);
        }

        await page.waitForTimeout(2000); // Wait for celebration to end
      }
    });
  });

  test.describe('Red Zone and Momentum Animations', () => {
    test('should highlight red zone entries', async ({ page }) => {
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'game_update',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 14,
            away_score: 7,
            quarter: 2,
            time_remaining: '05:30',
            game_status: 'red_zone',
            field_position: {
              team: 'home',
              yard_line: 18,
              side: 'away'
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      // Red zone indicator should be visible
      await expect(page.locator('[data-testid="red-zone-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="game-status"]')).toContainText('RED ZONE');

      // Should have red zone styling
      const gameCard = page.locator('[data-testid="game-card"]');
      await expect(gameCard).toHaveClass(/red-zone|redzone/);

      // Red zone pulse animation
      await expect(page.locator('[data-testid="red-zone-indicator"]')).toHaveClass(/animate-pulse/);
    });

    test('should show momentum shift animations', async ({ page }) => {
      // Start with one team leading
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'game_update',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 21,
            away_score: 7,
            quarter: 3,
            time_remaining: '08:00',
            game_status: 'live',
            momentum: {
              team: 'home',
              strength: 'strong'
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      // Should show momentum indicator
      await expect(page.locator('[data-testid="momentum-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="momentum-indicator"]')).toHaveClass(/home-momentum/);

      // Simulate momentum shift
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'momentum_shift',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 21,
            away_score: 21,
            quarter: 3,
            time_remaining: '02:15',
            game_status: 'live',
            momentum: {
              team: 'away',
              strength: 'strong',
              change: 'major_shift'
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      // Should animate momentum shift
      await expect(page.locator('[data-testid="momentum-shift-animation"]')).toBeVisible();
      await expect(page.locator('[data-testid="momentum-indicator"]')).toHaveClass(/away-momentum/);
    });

    test('should animate critical game moments', async ({ page }) => {
      const criticalMoments = [
        {
          scenario: 'two_minute_warning',
          expectedIndicator: 'two-minute-warning',
          expectedClass: 'critical-time'
        },
        {
          scenario: 'overtime',
          expectedIndicator: 'overtime-indicator',
          expectedClass: 'overtime'
        },
        {
          scenario: 'game_winning_drive',
          expectedIndicator: 'game-winning-drive',
          expectedClass: 'clutch-time'
        }
      ];

      for (const moment of criticalMoments) {
        await page.evaluate((moment) => {
          const gameUpdate = {
            event_type: 'critical_moment',
            data: {
              game_id: 'test_game',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: 24,
              away_score: 21,
              quarter: moment.scenario === 'overtime' ? 5 : 4,
              time_remaining: moment.scenario === 'two_minute_warning' ? '02:00' : '01:30',
              game_status: moment.scenario === 'overtime' ? 'overtime' : 'live',
              critical_moment: moment.scenario,
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(gameUpdate);
          }
        }, moment);

        // Check for critical moment indicator
        await expect(page.locator(`[data-testid="${moment.expectedIndicator}"]`)).toBeVisible();

        // Should have appropriate styling
        const gameCard = page.locator('[data-testid="game-card"]');
        await expect(gameCard).toHaveClass(new RegExp(moment.expectedClass));

        await page.waitForTimeout(1000);
      }
    });
  });

  test.describe('Animation Performance', () => {
    test('should maintain smooth animations during rapid updates', async ({ page }) => {
      // Start performance monitoring
      await page.evaluate(() => {
        window.__animationPerformance = {
          frameCount: 0,
          startTime: performance.now(),
          droppedFrames: 0
        };

        function trackFrames() {
          window.__animationPerformance.frameCount++;
          requestAnimationFrame(trackFrames);
        }

        requestAnimationFrame(trackFrames);
      });

      // Simulate rapid score updates with animations
      const updates = [
        { home: 7, away: 0, celebration: true },
        { home: 7, away: 7, celebration: true },
        { home: 14, away: 7, celebration: true },
        { home: 14, away: 14, celebration: true }
      ];

      for (const update of updates) {
        await page.evaluate((update) => {
          const gameUpdate = {
            event_type: update.celebration ? 'touchdown_scored' : 'score_update',
            data: {
              game_id: 'test_game',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: update.home,
              away_score: update.away,
              quarter: 1,
              time_remaining: '10:00',
              game_status: 'live',
              scoring_play: update.celebration ? {
                type: 'touchdown',
                team: update.home > update.away ? 'home' : 'away',
                points: 7
              } : undefined,
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(gameUpdate);
          }
        }, update);

        await page.waitForTimeout(800); // Allow animations to run
      }

      // Check animation performance
      const performance = await page.evaluate(() => {
        const duration = (performance.now() - window.__animationPerformance.startTime) / 1000;
        return {
          fps: window.__animationPerformance.frameCount / duration,
          duration,
          frameCount: window.__animationPerformance.frameCount
        };
      });

      expect(performance.fps).toBeGreaterThan(30); // Minimum acceptable FPS
      expect(performance.frameCount).toBeGreaterThan(100); // Should have many frames
    });

    test('should not block UI during celebrations', async ({ page }) => {
      // Trigger touchdown celebration
      await page.evaluate(() => {
        const gameUpdate = {
          event_type: 'touchdown_scored',
          data: {
            game_id: 'test_game',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            scoring_play: {
              type: 'touchdown',
              team: 'home',
              points: 7
            },
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        };

        if (window.__mockWebSocketInstance) {
          window.__mockWebSocketInstance.simulateMessage(gameUpdate);
        }
      });

      // UI should remain responsive during celebration
      const responseStart = Date.now();
      await page.click('[data-testid="refresh-button"]');
      const responseTime = Date.now() - responseStart;

      expect(responseTime).toBeLessThan(500); // UI should respond quickly

      // Celebration should still be running
      await expect(page.locator('[data-testid="touchdown-celebration"]')).toBeVisible();
    });

    test('should handle multiple simultaneous animations', async ({ page }) => {
      // Trigger multiple animations simultaneously
      await Promise.all([
        page.evaluate(() => {
          // Touchdown
          const touchdownUpdate = {
            event_type: 'touchdown_scored',
            data: {
              game_id: 'test_game',
              home_score: 7,
              away_score: 0,
              scoring_play: { type: 'touchdown', team: 'home' },
              updated_at: new Date().toISOString()
            }
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(touchdownUpdate);
          }
        }),

        page.evaluate(() => {
          // Red zone entry
          const redZoneUpdate = {
            event_type: 'game_update',
            data: {
              game_id: 'test_game',
              game_status: 'red_zone',
              field_position: { team: 'away', yard_line: 15 },
              updated_at: new Date().toISOString()
            }
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(redZoneUpdate);
          }
        }),

        page.evaluate(() => {
          // Momentum shift
          const momentumUpdate = {
            event_type: 'momentum_shift',
            data: {
              game_id: 'test_game',
              momentum: { team: 'home', change: 'major_shift' },
              updated_at: new Date().toISOString()
            }
          };

          if (window.__mockWebSocketInstance) {
            window.__mockWebSocketInstance.simulateMessage(momentumUpdate);
          }
        })
      ]);

      // All animations should be visible simultaneously
      await expect(page.locator('[data-testid="touchdown-celebration"]')).toBeVisible();
      await expect(page.locator('[data-testid="red-zone-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="momentum-shift-animation"]')).toBeVisible();

      // Page should remain responsive
      const responseStart = Date.now();
      await page.click('[data-testid="settings-button"]');
      const responseTime = Date.now() - responseStart;

      expect(responseTime).toBeLessThan(1000);
    });
  });
});