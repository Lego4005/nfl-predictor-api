/**
 * Cache Manager for NFL Dashboard
 * Provides caching strategies for improved performance
 */

class CacheManager {
  constructor() {
    this.cache = new Map();
    this.timeouts = new Map();
  }

  /**
   * Set a value in cache with expiration
   * @param {string} key - Cache key
   * @param {any} value - Value to cache
   * @param {number} ttl - Time to live in milliseconds (default: 5 minutes)
   */
  set(key, value, ttl = 300000) {
    // Clear existing timeout
    if (this.timeouts.has(key)) {
      clearTimeout(this.timeouts.get(key));
    }

    // Store value
    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      ttl
    });

    // Set expiration timeout
    const timeout = setTimeout(() => {
      this.cache.delete(key);
      this.timeouts.delete(key);
    }, ttl);

    this.timeouts.set(key, timeout);
  }

  /**
   * Get a value from cache
   * @param {string} key - Cache key
   * @returns {any|null} Cached value or null if not found/expired
   */
  get(key) {
    if (!this.cache.has(key)) {
      return null;
    }

    const item = this.cache.get(key);
    const now = Date.now();

    // Check if expired
    if (now - item.timestamp > item.ttl) {
      this.cache.delete(key);
      if (this.timeouts.has(key)) {
        clearTimeout(this.timeouts.get(key));
        this.timeouts.delete(key);
      }
      return null;
    }

    return item.value;
  }

  /**
   * Check if key exists in cache and is not expired
   * @param {string} key - Cache key
   * @returns {boolean} True if key exists and not expired
   */
  has(key) {
    if (!this.cache.has(key)) {
      return false;
    }

    const item = this.cache.get(key);
    return Date.now() - item.timestamp <= item.ttl;
  }

  /**
   * Delete a key from cache
   * @param {string} key - Cache key
   */
  delete(key) {
    this.cache.delete(key);
    if (this.timeouts.has(key)) {
      clearTimeout(this.timeouts.get(key));
      this.timeouts.delete(key);
    }
  }

  /**
   * Clear all cache entries
   */
  clear() {
    this.cache.clear();
    this.timeouts.forEach(timeout => clearTimeout(timeout));
    this.timeouts.clear();
  }

  /**
   * Get cache statistics
   * @returns {object} Cache statistics
   */
  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
      timeouts: this.timeouts.size
    };
  }

  /**
   * Get cache entry metadata
   * @param {string} key - Cache key
   * @returns {object|null} Entry metadata or null if not found
   */
  getMetadata(key) {
    if (!this.cache.has(key)) {
      return null;
    }

    const item = this.cache.get(key);
    const now = Date.now();
    const age = now - item.timestamp;
    const remaining = item.ttl - age;

    return {
      key,
      age,
      remaining,
      expired: remaining <= 0,
      ttl: item.ttl
    };
  }
}

// Create singleton instance
const cacheManager = new CacheManager();

// Export cache manager instance and class
export default cacheManager;
export { CacheManager };

// Utility functions for common caching patterns

/**
 * Cache expensive function calls
 * @param {Function} fn - Function to cache
 * @param {string} keyPrefix - Prefix for cache keys
 * @param {number} ttl - Time to live in milliseconds
 * @returns {Function} Memoized function
 */
export function memoize(fn, keyPrefix, ttl = 300000) {
  return function(...args) {
    const key = `${keyPrefix}:${JSON.stringify(args)}`;
    
    if (cacheManager.has(key)) {
      return cacheManager.get(key);
    }

    const result = fn.apply(this, args);
    cacheManager.set(key, result, ttl);
    return result;
  };
}

/**
 * Cache async function calls
 * @param {Function} fn - Async function to cache
 * @param {string} keyPrefix - Prefix for cache keys
 * @param {number} ttl - Time to live in milliseconds
 * @returns {Function} Memoized async function
 */
export function memoizeAsync(fn, keyPrefix, ttl = 300000) {
  return async function(...args) {
    const key = `${keyPrefix}:${JSON.stringify(args)}`;
    
    if (cacheManager.has(key)) {
      return cacheManager.get(key);
    }

    try {
      const result = await fn.apply(this, args);
      cacheManager.set(key, result, ttl);
      return result;
    } catch (error) {
      // Don't cache errors
      throw error;
    }
  };
}

/**
 * Cache API responses with appropriate TTL based on data type
 * @param {string} endpoint - API endpoint
 * @param {any} data - API response data
 * @param {string} dataType - Type of data (games, rankings, etc.)
 */
export function cacheApiResponse(endpoint, data, dataType) {
  let ttl;
  
  switch (dataType) {
    case 'games':
      // Games data changes frequently during live games
      ttl = 30000; // 30 seconds
      break;
    case 'rankings':
      // Rankings update less frequently
      ttl = 300000; // 5 minutes
      break;
    case 'experts':
      // Expert data is relatively stable
      ttl = 600000; // 10 minutes
      break;
    case 'performance':
      // Performance data updates periodically
      ttl = 900000; // 15 minutes
      break;
    default:
      ttl = 300000; // 5 minutes default
  }

  cacheManager.set(`api:${endpoint}`, data, ttl);
}

/**
 * Get cached API response
 * @param {string} endpoint - API endpoint
 * @returns {any|null} Cached data or null
 */
export function getCachedApiResponse(endpoint) {
  return cacheManager.get(`api:${endpoint}`);
}