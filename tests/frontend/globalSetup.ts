/**
 * Jest Global Setup for NFL Predictor Platform
 * Runs once before all tests
 */

export default async function globalSetup() {
  // Setup test environment variables
  process.env.NODE_ENV = 'test';
  process.env.REACT_APP_API_URL = 'http://localhost:8000';
  process.env.REACT_APP_WS_URL = 'ws://localhost:8080';

  console.log('🚀 Starting NFL Predictor Test Suite');
  console.log(`Test Environment: ${process.env.NODE_ENV}`);
  console.log(`API URL: ${process.env.REACT_APP_API_URL}`);
  console.log(`WebSocket URL: ${process.env.REACT_APP_WS_URL}`);
}