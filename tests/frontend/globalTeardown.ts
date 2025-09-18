/**
 * Jest Global Teardown for NFL Predictor Platform
 * Runs once after all tests complete
 */

export default async function globalTeardown() {
  console.log('✅ NFL Predictor Test Suite Complete');

  // Clean up any global resources if needed
  // For example, close database connections, clear caches, etc.
}