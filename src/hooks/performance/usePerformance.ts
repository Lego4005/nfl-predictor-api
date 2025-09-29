import { useCallback, useEffect, useMemo, useRef } from 'react'

/**
 * Performance monitoring and optimization hooks
 */

/**
 * Hook for debouncing values to prevent excessive re-renders
 * Useful for search inputs and filters
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Hook for throttling function calls
 * Useful for scroll events and resize handlers
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRun = useRef(Date.now())

  return useCallback(
    ((...args) => {
      if (Date.now() - lastRun.current >= delay) {
        callback(...args)
        lastRun.current = Date.now()
      }
    }) as T,
    [callback, delay]
  )
}

/**
 * Hook for memoizing expensive computations
 * Automatically handles dependencies and avoids unnecessary recalculations
 */
export function useExpensiveComputation<T>(
  computeFn: () => T,
  deps: React.DependencyList,
  shouldRecompute?: (prevDeps: React.DependencyList, nextDeps: React.DependencyList) => boolean
): T {
  const memoizedValue = useMemo(() => {
    // Log performance for development
    if (process.env.NODE_ENV === 'development') {
      const start = performance.now()
      const result = computeFn()
      const end = performance.now()
      console.log(`Expensive computation took ${end - start} milliseconds`)
      return result
    }
    return computeFn()
  }, deps)

  return memoizedValue
}

/**
 * Hook for lazy loading images and components
 */
export function useLazyLoad(options: IntersectionObserverInit = {}) {
  const [isIntersecting, setIsIntersecting] = React.useState(false)
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true)
          observer.disconnect()
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options
      }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [])

  return { ref, isIntersecting }
}

/**
 * Hook for performance monitoring
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCount = useRef(0)
  const lastRenderTime = useRef(Date.now())

  useEffect(() => {
    renderCount.current++
    const currentTime = Date.now()
    const timeSinceLastRender = currentTime - lastRenderTime.current
    lastRenderTime.current = currentTime

    if (process.env.NODE_ENV === 'development') {
      console.log(`${componentName} rendered ${renderCount.current} times. Time since last render: ${timeSinceLastRender}ms`)
    }
  })

  const markInteraction = useCallback((interactionName: string) => {
    const start = performance.now()
    return () => {
      const end = performance.now()
      if (process.env.NODE_ENV === 'development') {
        console.log(`${componentName} - ${interactionName} took ${end - start} milliseconds`)
      }
    }
  }, [componentName])

  return { renderCount: renderCount.current, markInteraction }
}

/**
 * Hook for managing component updates based on viewport visibility
 */
export function useVisibilityOptimization() {
  const [isVisible, setIsVisible] = React.useState(true)

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden)
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  return isVisible
}

/**
 * Hook for optimizing list rendering with virtualization hint
 */
export function useVirtualization<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) {
  const [scrollTop, setScrollTop] = React.useState(0)

  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight)
    const visibleCount = Math.ceil(containerHeight / itemHeight)
    const end = Math.min(start + visibleCount + 2, items.length) // +2 for buffer

    return { start, end }
  }, [scrollTop, itemHeight, containerHeight, items.length])

  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end).map((item, index) => ({
      item,
      index: visibleRange.start + index
    }))
  }, [items, visibleRange])

  const handleScroll = useThrottle((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop)
  }, 16) // ~60fps

  return {
    visibleItems,
    visibleRange,
    handleScroll,
    totalHeight: items.length * itemHeight,
    offsetY: visibleRange.start * itemHeight
  }
}

/**
 * Hook for caching expensive computations across component instances
 */
const globalCache = new Map<string, { value: any; timestamp: number; ttl: number }>()

export function useGlobalCache<T>(
  key: string,
  computeFn: () => T,
  ttl: number = 5 * 60 * 1000 // 5 minutes default
): T {
  return useMemo(() => {
    const cached = globalCache.get(key)
    const now = Date.now()

    if (cached && now - cached.timestamp < cached.ttl) {
      return cached.value
    }

    const value = computeFn()
    globalCache.set(key, { value, timestamp: now, ttl })

    // Clean up expired cache entries
    for (const [cacheKey, cacheEntry] of globalCache.entries()) {
      if (now - cacheEntry.timestamp >= cacheEntry.ttl) {
        globalCache.delete(cacheKey)
      }
    }

    return value
  }, [key, ttl])
}

// React import fix
import React from 'react'