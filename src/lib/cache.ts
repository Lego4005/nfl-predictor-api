/**
 * Cache manager for NFL Predictor App
 * Implements TTL-based caching with different expiration times for different data types
 */

interface CacheEntry<T> {
  value: T
  timestamp: number
  ttl: number
  key: string
}

type CacheEventType = 'hit' | 'miss' | 'set' | 'delete' | 'clear' | 'expired'

interface CacheEvent<T> {
  type: CacheEventType
  key: string
  value?: T
  timestamp: number
}

class CacheManager {
  private cache = new Map<string, CacheEntry<any>>()
  private listeners = new Set<(event: CacheEvent<any>) => void>()
  private cleanupInterval: NodeJS.Timeout | null = null

  constructor() {
    // Run cleanup every 5 minutes
    this.cleanupInterval = setInterval(() => {
      this.cleanup()
    }, 5 * 60 * 1000)
  }

  /**
   * Get value from cache
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    
    if (!entry) {
      this.emit('miss', key)
      return null
    }

    const now = Date.now()
    
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      this.emit('expired', key, entry.value)
      return null
    }

    this.emit('hit', key, entry.value)
    return entry.value
  }

  /**
   * Set value in cache with TTL
   */
  set<T>(key: string, value: T, ttl: number = 5 * 60 * 1000): void {
    const entry: CacheEntry<T> = {
      value,
      timestamp: Date.now(),
      ttl,
      key
    }

    this.cache.set(key, entry)
    this.emit('set', key, value)
  }

  /**
   * Delete specific key from cache
   */
  delete(key: string): boolean {
    const existed = this.cache.has(key)
    if (existed) {
      const entry = this.cache.get(key)
      this.cache.delete(key)
      this.emit('delete', key, entry?.value)
    }
    return existed
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear()
    this.emit('clear', 'all')
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now()
    let validEntries = 0
    let expiredEntries = 0

    for (const entry of this.cache.values()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredEntries++
      } else {
        validEntries++
      }
    }

    return {
      totalEntries: this.cache.size,
      validEntries,
      expiredEntries,
      memoryUsage: this.estimateMemoryUsage()
    }
  }

  /**
   * Check if key exists and is valid
   */
  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) return false

    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return false
    }

    return true
  }

  /**
   * Get or set pattern (cache-aside)
   */
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T> | T,
    ttl: number = 5 * 60 * 1000
  ): Promise<T> {
    const cached = this.get<T>(key)
    
    if (cached !== null) {
      return cached
    }

    const value = await factory()
    this.set(key, value, ttl)
    return value
  }

  /**
   * Add event listener for cache events
   */
  addEventListener(listener: (event: CacheEvent<any>) => void): void {
    this.listeners.add(listener)
  }

  /**
   * Remove event listener
   */
  removeEventListener(listener: (event: CacheEvent<any>) => void): void {
    this.listeners.delete(listener)
  }

  /**
   * Clean up expired entries
   */
  private cleanup(): void {
    const now = Date.now()
    const keysToDelete: string[] = []

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        keysToDelete.push(key)
      }
    }

    keysToDelete.forEach(key => {
      this.cache.delete(key)
    })

    if (keysToDelete.length > 0 && process.env.NODE_ENV === 'development') {
      console.log(`Cache cleanup: removed ${keysToDelete.length} expired entries`)
    }
  }

  /**
   * Emit cache event to listeners
   */
  private emit<T>(type: CacheEventType, key: string, value?: T): void {
    const event: CacheEvent<T> = {
      type,
      key,
      value,
      timestamp: Date.now()
    }

    this.listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error('Error in cache event listener:', error)
      }
    })
  }

  /**
   * Estimate memory usage (rough approximation)
   */
  private estimateMemoryUsage(): number {
    let size = 0
    
    for (const entry of this.cache.values()) {
      // Rough estimate: JSON stringify length + overhead
      try {
        size += JSON.stringify(entry).length * 2 // UTF-16
      } catch {
        size += 1000 // Fallback estimate for non-serializable objects
      }
    }

    return size
  }

  /**
   * Destroy cache manager and cleanup
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval)
      this.cleanupInterval = null
    }
    this.clear()
    this.listeners.clear()
  }
}

// Singleton instance
const cacheManager = new CacheManager()

// Predefined TTL values for different data types
export const TTL = {
  GAMES: 5 * 60 * 1000,        // 5 minutes
  RANKINGS: 10 * 60 * 1000,    // 10 minutes
  PREDICTIONS: 15 * 60 * 1000, // 15 minutes
  TEAMS: 30 * 60 * 1000,       // 30 minutes
  STATIC: 60 * 60 * 1000,      // 1 hour
  SESSION: 24 * 60 * 60 * 1000 // 24 hours
} as const

// Cache key generators
export const CacheKeys = {
  games: (week: number) => `games:week:${week}`,
  game: (gameId: string) => `game:${gameId}`,
  team: (teamId: string) => `team:${teamId}`,
  rankings: (week?: number) => week ? `rankings:week:${week}` : 'rankings:current',
  predictions: (gameId: string) => `predictions:${gameId}`,
  performance: (timeframe: string) => `performance:${timeframe}`,
  user: (userId: string) => `user:${userId}`,
  filter: (type: string, params: Record<string, any>) => `filter:${type}:${JSON.stringify(params)}`
} as const

export default cacheManager
export { CacheManager, type CacheEvent, type CacheEventType }