/**
 * Jest Configuration for NFL Predictor Platform Frontend Tests
 * Optimized for React, TypeScript, and modern frontend testing
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/tests/frontend/setupTests.ts'
  ],

  // Test file patterns
  testMatch: [
    '<rootDir>/tests/**/*.(test|spec).(js|jsx|ts|tsx)',
    '<rootDir>/src/**/__tests__/**/*.(js|jsx|ts|tsx)',
    '<rootDir>/src/**/?(*.)(test|spec).(js|jsx|ts|tsx)'
  ],

  // Module file extensions
  moduleFileExtensions: [
    'js',
    'jsx',
    'ts',
    'tsx',
    'json',
    'css',
    'scss',
    'sass'
  ],

  // Transform configuration
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
    '^.+\\.css$': 'jest-transform-css',
    '^.+\\.(png|jpg|jpeg|gif|webp|svg)$': 'jest-transform-file'
  },

  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(recharts|@recharts|d3-*)/)'
  ],

  // Module name mapping for absolute imports and assets
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@types/(.*)$': '<rootDir>/src/types/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@assets/(.*)$': '<rootDir>/src/assets/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/tests/frontend/__mocks__/fileMock.js'
  },

  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/__tests__/**',
    '!src/**/node_modules/**'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 85,
      lines: 90,
      statements: 90
    },
    './src/components/': {
      branches: 90,
      functions: 95,
      lines: 95,
      statements: 95
    },
    './src/services/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },

  // Coverage reporters
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json-summary',
    'clover'
  ],

  // Coverage directory
  coverageDirectory: '<rootDir>/coverage',

  // Global setup and teardown
  globalSetup: '<rootDir>/tests/frontend/globalSetup.ts',
  globalTeardown: '<rootDir>/tests/frontend/globalTeardown.ts',

  // Test timeout (30 seconds)
  testTimeout: 30000,

  // Snapshot serializers
  snapshotSerializers: [
    'enzyme-to-json/serializer'
  ],

  // Clear mocks between tests
  clearMocks: true,
  restoreMocks: true,
  resetMocks: false,

  // Verbose output
  verbose: true,

  // Maximum worker processes
  maxWorkers: '50%',

  // Error handling
  errorOnDeprecated: true,

  // Watch mode configuration
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/build/',
    '<rootDir>/coverage/'
  ],

  // Custom reporters
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: '<rootDir>/test-results',
        outputName: 'junit.xml',
        suiteName: 'NFL Predictor Frontend Tests',
        classNameTemplate: '{classname}',
        titleTemplate: '{title}',
        ancestorSeparator: ' › '
      }
    ],
    [
      'jest-html-reporters',
      {
        publicPath: '<rootDir>/test-results',
        filename: 'test-report.html',
        expand: true,
        hideIcon: false,
        pageTitle: 'NFL Predictor Test Report'
      }
    ]
  ],

  // Notify configuration
  notify: true,
  notifyMode: 'failure-change',

  // Bail configuration
  bail: 0,

  // Force exit
  forceExit: true,

  // Detect open handles
  detectOpenHandles: true,

  // Mock configuration
  mocks: {
    'WebSocket': '<rootDir>/tests/frontend/__mocks__/WebSocket.js',
    'localStorage': '<rootDir>/tests/frontend/__mocks__/localStorage.js',
    'IntersectionObserver': '<rootDir>/tests/frontend/__mocks__/IntersectionObserver.js'
  }
};