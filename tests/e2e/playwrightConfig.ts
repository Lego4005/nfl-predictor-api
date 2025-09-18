/**
 * Playwright E2E Testing Configuration for NFL Predictor Live Game Experience
 * Comprehensive end-to-end testing setup with cross-browser and device support
 */

import { defineConfig, devices } from '@playwright/test';

// Test environment configuration
const TEST_CONFIG = {
  // Base URL for testing
  baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',

  // WebSocket server for live data testing
  wsURL: process.env.E2E_WS_URL || 'ws://localhost:8080',

  // Test data API
  apiURL: process.env.E2E_API_URL || 'http://localhost:8000',

  // Timeouts
  testTimeout: 30000,
  navigationTimeout: 15000,
  actionTimeout: 10000,

  // Retry configuration
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : 4,

  // Video and screenshot settings
  video: 'retain-on-failure',
  screenshot: 'only-on-failure',
  trace: 'retain-on-failure'
};

export default defineConfig({
  testDir: './e2e',

  /* Maximum time one test can run for. */
  timeout: TEST_CONFIG.testTimeout,

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: TEST_CONFIG.retries,

  /* Opt out of parallel tests on CI. */
  workers: TEST_CONFIG.workers,

  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['line']
  ],

  /* Shared settings for all the projects below. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: TEST_CONFIG.baseURL,

    /* Collect trace when retrying the failed test. */
    trace: TEST_CONFIG.trace,

    /* Screenshots on failure */
    screenshot: TEST_CONFIG.screenshot,

    /* Video recording */
    video: TEST_CONFIG.video,

    /* Action and navigation timeouts */
    actionTimeout: TEST_CONFIG.actionTimeout,
    navigationTimeout: TEST_CONFIG.navigationTimeout,

    /* Ignore HTTPS errors for development */
    ignoreHTTPSErrors: true,

    /* Accept downloads */
    acceptDownloads: true,

    /* Viewport settings - will be overridden by specific projects */
    viewport: { width: 1280, height: 720 },

    /* Extra HTTP headers */
    extraHTTPHeaders: {
      'Accept-Language': 'en-US',
    },
  },

  /* Configure projects for major browsers and devices */
  projects: [
    // Desktop browsers
    {
      name: 'chromium-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: [
        '**/desktop/**/*.spec.ts',
        '**/cross-browser/**/*.spec.ts',
        '**/performance/**/*.spec.ts'
      ]
    },

    {
      name: 'firefox-desktop',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: [
        '**/desktop/**/*.spec.ts',
        '**/cross-browser/**/*.spec.ts'
      ]
    },

    {
      name: 'webkit-desktop',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: [
        '**/desktop/**/*.spec.ts',
        '**/cross-browser/**/*.spec.ts'
      ]
    },

    // Mobile devices
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        // Override with custom mobile settings for NFL app
        viewport: { width: 393, height: 851 },
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true
      },
      testMatch: [
        '**/mobile/**/*.spec.ts',
        '**/responsive/**/*.spec.ts',
        '**/touch/**/*.spec.ts'
      ]
    },

    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 12'],
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true
      },
      testMatch: [
        '**/mobile/**/*.spec.ts',
        '**/responsive/**/*.spec.ts',
        '**/touch/**/*.spec.ts'
      ]
    },

    // Tablet devices
    {
      name: 'tablet-chrome',
      use: {
        ...devices['iPad Pro'],
        viewport: { width: 1024, height: 1366 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true
      },
      testMatch: [
        '**/tablet/**/*.spec.ts',
        '**/responsive/**/*.spec.ts'
      ]
    },

    // Specific device testing
    {
      name: 'iphone-se',
      use: {
        ...devices['iPhone SE'],
        // Small screen testing
        viewport: { width: 375, height: 667 },
        deviceScaleFactor: 2
      },
      testMatch: [
        '**/mobile/**/*.spec.ts',
        '**/small-screen/**/*.spec.ts'
      ]
    },

    {
      name: 'android-galaxy',
      use: {
        ...devices['Galaxy S III'],
        // Updated to modern Android device
        viewport: { width: 360, height: 640 },
        deviceScaleFactor: 3,
        userAgent: 'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36'
      },
      testMatch: [
        '**/mobile/**/*.spec.ts',
        '**/android/**/*.spec.ts'
      ]
    },

    // Performance testing configurations
    {
      name: 'performance-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Disable images and CSS for performance testing
        launchOptions: {
          args: [
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-sandbox'
          ]
        }
      },
      testMatch: [
        '**/performance/**/*.spec.ts',
        '**/load/**/*.spec.ts'
      ]
    },

    // Accessibility testing
    {
      name: 'accessibility-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // High contrast for accessibility testing
        colorScheme: 'dark',
        reducedMotion: 'reduce'
      },
      testMatch: [
        '**/accessibility/**/*.spec.ts'
      ]
    },

    // Network simulation
    {
      name: 'slow-network',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        // Simulate slow 3G connection
        launchOptions: {
          args: ['--simulate-outdated-no-au', '--force-slow-connection']
        }
      },
      testMatch: [
        '**/network/**/*.spec.ts'
      ]
    }
  ],

  /* Global test setup and teardown */
  globalSetup: require.resolve('./e2e/globalSetup.ts'),
  globalTeardown: require.resolve('./e2e/globalTeardown.ts'),

  /* Run your local dev server before starting the tests */
  webServer: process.env.CI ? undefined : [
    {
      command: 'npm run dev',
      port: 3000,
      reuseExistingServer: !process.env.CI,
      timeout: 120000
    },
    {
      command: 'npm run start:ws-server',
      port: 8080,
      reuseExistingServer: !process.env.CI,
      timeout: 60000
    }
  ],

  /* Test output directory */
  outputDir: 'test-results/',

  /* Expect configuration */
  expect: {
    // Global timeout for assertions
    timeout: 10000,

    // Screenshot comparison
    threshold: 0.2,

    // Animation handling
    toHaveScreenshot: {
      animations: 'disabled'
    },

    // Custom matchers timeout
    toMatchAriaSnapshot: {
      timeout: 15000
    }
  },

  /* Test metadata */
  metadata: {
    testFramework: 'Playwright',
    platform: process.platform,
    browser: 'multi',
    environment: process.env.NODE_ENV || 'test',
    version: require('../../package.json').version
  }
});

// Export configuration for use in test files
export const testConfig = TEST_CONFIG;