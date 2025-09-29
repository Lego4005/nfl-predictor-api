/**
 * Performance Optimization Utilities
 * Tools for optimizing component performance and mobile responsiveness
 */

import { useCallback, useMemo, useRef, useEffect, useState } from 'react';
import { debounce, throttle } from 'lodash-es';

// Virtual scrolling for large lists
export interface VirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  data: any[];
}

export const useVirtualScroll = ({
  itemHeight,
  containerHeight,
  overscan = 5,
  data
}: VirtualScrollOptions) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight),
    data.length - 1
  );
  
  const startIndex = Math.max(0, visibleStart - overscan);
  const endIndex = Math.min(data.length - 1, visibleEnd + overscan);
  
  const visibleItems = data.slice(startIndex, endIndex + 1);
  
  const totalHeight = data.length * itemHeight;
  const offsetY = startIndex * itemHeight;
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    startIndex,
    endIndex,
    setScrollTop
  };
};

// Debounced search hook
export const useDebouncedSearch = (
  searchFn: (query: string) => void,
  delay: number = 300
) => {
  const debouncedFn = useCallback(
    debounce(searchFn, delay),
    [searchFn, delay]
  );
  
  useEffect(() => {
    return () => {
      debouncedFn.cancel();
    };
  }, [debouncedFn]);
  
  return debouncedFn;
};

// Throttled scroll handler
export const useThrottledScroll = (
  handler: (event: Event) => void,
  delay: number = 100
) => {
  const throttledHandler = useCallback(
    throttle(handler, delay),
    [handler, delay]
  );
  
  useEffect(() => {
    return () => {
      throttledHandler.cancel();
    };
  }, [throttledHandler]);
  
  return throttledHandler;
};

// Intersection Observer for lazy loading
export const useIntersectionObserver = (
  options: IntersectionObserverInit = {}
) => {
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const elementRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => setEntry(entry),
      options
    );
    
    observer.observe(element);
    
    return () => observer.disconnect();
  }, [options]);
  
  return { elementRef, entry };
};

// Memoized data filtering
export const useFilteredData = <T>(
  data: T[],
  filters: Record<string, any>,
  filterFn: (item: T, filters: Record<string, any>) => boolean
) => {
  return useMemo(() => {
    return data.filter(item => filterFn(item, filters));
  }, [data, filters, filterFn]);
};

// Performance monitoring hook
export const usePerformanceMonitor = (componentName: string) => {
  const renderCountRef = useRef(0);
  const mountTimeRef = useRef<number>(0);
  
  useEffect(() => {
    mountTimeRef.current = performance.now();
    
    return () => {
      const unmountTime = performance.now();
      const lifetime = unmountTime - mountTimeRef.current;
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Performance] ${componentName}: ${renderCountRef.current} renders, ${lifetime.toFixed(2)}ms lifetime`);
      }
    };
  }, [componentName]);
  
  useEffect(() => {
    renderCountRef.current += 1;
  });
  
  return {
    renderCount: renderCountRef.current,
    logPerformance: (operation: string, duration: number) => {
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Performance] ${componentName}.${operation}: ${duration.toFixed(2)}ms`);
      }
    }
  };
};

// Mobile responsive utilities
export const useMediaQuery = (query: string) => {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });
  
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const mediaQuery = window.matchMedia(query);
    const handleChange = () => setMatches(mediaQuery.matches);
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [query]);
  
  return matches;
};

// Responsive breakpoints
export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
} as const;

export const useBreakpoint = () => {
  const isSm = useMediaQuery(`(min-width: ${breakpoints.sm}px)`);
  const isMd = useMediaQuery(`(min-width: ${breakpoints.md}px)`);
  const isLg = useMediaQuery(`(min-width: ${breakpoints.lg}px)`);
  const isXl = useMediaQuery(`(min-width: ${breakpoints.xl}px)`);
  const is2Xl = useMediaQuery(`(min-width: ${breakpoints['2xl']}px)`);
  
  return {
    isSm,
    isMd,
    isLg,
    isXl,
    is2Xl,
    isMobile: !isSm,
    isTablet: isSm && !isLg,
    isDesktop: isLg
  };
};

// Image lazy loading
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const { elementRef, entry } = useIntersectionObserver({
    threshold: 0.1,
    rootMargin: '50px'
  });
  
  useEffect(() => {
    if (entry?.isIntersecting && !isLoaded && !isError) {
      const img = new Image();
      img.onload = () => {
        setImageSrc(src);
        setIsLoaded(true);
      };
      img.onerror = () => {
        setIsError(true);
      };
      img.src = src;
    }
  }, [entry, src, isLoaded, isError]);
  
  return {
    imageSrc,
    isLoaded,
    isError,
    ref: elementRef
  };
};

// Component size tracking
export const useElementSize = () => {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const elementRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    
    const resizeObserver = new ResizeObserver(entries => {
      const entry = entries[0];
      if (entry) {
        setSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });
    
    resizeObserver.observe(element);
    
    return () => resizeObserver.disconnect();
  }, []);
  
  return { size, ref: elementRef };
};

// Memory leak prevention
export const useComponentCleanup = () => {
  const timeoutsRef = useRef<NodeJS.Timeout[]>([]);
  const intervalsRef = useRef<NodeJS.Timeout[]>([]);
  const abortControllersRef = useRef<AbortController[]>([]);
  
  const addTimeout = useCallback((callback: () => void, delay: number) => {
    const timeout = setTimeout(callback, delay);
    timeoutsRef.current.push(timeout);
    return timeout;
  }, []);
  
  const addInterval = useCallback((callback: () => void, delay: number) => {
    const interval = setInterval(callback, delay);
    intervalsRef.current.push(interval);
    return interval;
  }, []);
  
  const createAbortController = useCallback(() => {
    const controller = new AbortController();
    abortControllersRef.current.push(controller);
    return controller;
  }, []);
  
  useEffect(() => {
    return () => {
      // Clear all timeouts
      timeoutsRef.current.forEach(clearTimeout);
      timeoutsRef.current = [];
      
      // Clear all intervals
      intervalsRef.current.forEach(clearInterval);
      intervalsRef.current = [];
      
      // Abort all pending requests
      abortControllersRef.current.forEach(controller => {
        if (!controller.signal.aborted) {
          controller.abort();
        }
      });
      abortControllersRef.current = [];
    };
  }, []);
  
  return {
    addTimeout,
    addInterval,
    createAbortController
  };
};

// Optimized list rendering
export interface OptimizedListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T, index: number) => string;
  onEndReached?: () => void;
  onEndReachedThreshold?: number;
}

export const OptimizedList = <T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  keyExtractor,
  onEndReached,
  onEndReachedThreshold = 0.8
}: OptimizedListProps<T>) => {
  const {
    visibleItems,
    totalHeight,
    offsetY,
    startIndex,
    setScrollTop
  } = useVirtualScroll({
    itemHeight,
    containerHeight,
    data: items
  });
  
  const handleScroll = useThrottledScroll((event: Event) => {
    const target = event.target as HTMLDivElement;
    const scrollTop = target.scrollTop;
    setScrollTop(scrollTop);
    
    // Check if near end for infinite loading
    if (onEndReached) {
      const scrollProgress = (scrollTop + containerHeight) / totalHeight;
      if (scrollProgress >= onEndReachedThreshold) {
        onEndReached();
      }
    }
  });
  
  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0
          }}
        >
          {visibleItems.map((item, index) => (
            <div
              key={keyExtractor(item, startIndex + index)}
              style={{ height: itemHeight }}
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Bundle size optimization utilities
export const lazyLoad = (importFn: () => Promise<any>) => {
  return React.lazy(importFn);
};

export const preloadComponent = (importFn: () => Promise<any>) => {
  importFn();
};

// Performance measurement utilities
export const measurePerformance = async <T,>(
  operation: () => Promise<T> | T,
  label: string
): Promise<{ result: T; duration: number }> => {
  const start = performance.now();
  const result = await operation();
  const end = performance.now();
  const duration = end - start;
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`);
  }
  
  return { result, duration };
};

export default {
  useVirtualScroll,
  useDebouncedSearch,
  useThrottledScroll,
  useIntersectionObserver,
  useFilteredData,
  usePerformanceMonitor,
  useMediaQuery,
  useBreakpoint,
  useLazyImage,
  useElementSize,
  useComponentCleanup,
  OptimizedList,
  measurePerformance
};