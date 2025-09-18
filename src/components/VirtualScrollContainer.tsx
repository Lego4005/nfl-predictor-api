import React, { memo, useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FixedSizeList as List, VariableSizeList, ListChildComponentProps } from 'react-window';
import { VirtualScrollConfig } from '../types/predictions';

interface VirtualScrollContainerProps<T> {
  items: T[];
  renderItem: (item: T, index: number, style: React.CSSProperties) => React.ReactNode;
  itemHeight?: number | ((index: number) => number);
  containerHeight?: number;
  overscan?: number;
  className?: string;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  onScroll?: (scrollTop: number, scrollDirection: 'up' | 'down') => void;
  onLoadMore?: () => void;
  hasNextPage?: boolean;
  threshold?: number;
  useVariableHeight?: boolean;
}

interface ScrollState {
  scrollTop: number;
  scrollDirection: 'up' | 'down';
  isScrolling: boolean;
  lastScrollTop: number;
}

const VirtualScrollContainer = <T,>({
  items,
  renderItem,
  itemHeight = 80,
  containerHeight = 600,
  overscan = 5,
  className = '',
  loading = false,
  loadingComponent,
  emptyComponent,
  onScroll,
  onLoadMore,
  hasNextPage = false,
  threshold = 0.8,
  useVariableHeight = false
}: VirtualScrollContainerProps<T>) => {
  const [scrollState, setScrollState] = useState<ScrollState>({
    scrollTop: 0,
    scrollDirection: 'down',
    isScrolling: false,
    lastScrollTop: 0
  });

  const listRef = useRef<any>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const itemHeightCache = useRef<Map<number, number>>(new Map());

  // Memoized item renderer for performance
  const ItemRenderer = useCallback(({ index, style }: ListChildComponentProps) => {
    if (index >= items.length) {
      return null;
    }

    const item = items[index];
    return (
      <div style={style}>
        {renderItem(item, index, style)}
      </div>
    );
  }, [items, renderItem]);

  // Loading item renderer for infinite scroll
  const LoadingItemRenderer = useCallback(({ index, style }: ListChildComponentProps) => {
    if (index < items.length) {
      return <ItemRenderer index={index} style={style} />;
    }

    return (
      <div style={style} className="flex items-center justify-center p-4">
        {loadingComponent || (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
            <span className="text-gray-500">Loading more...</span>
          </div>
        )}
      </div>
    );
  }, [items.length, ItemRenderer, loadingComponent]);

  // Variable height calculation
  const getItemHeight = useCallback((index: number) => {
    if (typeof itemHeight === 'function') {
      return itemHeight(index);
    }

    // Use cached height if available
    if (itemHeightCache.current.has(index)) {
      return itemHeightCache.current.get(index)!;
    }

    return typeof itemHeight === 'number' ? itemHeight : 80;
  }, [itemHeight]);

  // Handle scroll events
  const handleScroll = useCallback(({ scrollTop, scrollDirection }: { scrollTop: number; scrollDirection: 'forward' | 'backward' }) => {
    const direction = scrollDirection === 'forward' ? 'down' : 'up';

    setScrollState(prev => ({
      scrollTop,
      scrollDirection: direction,
      isScrolling: true,
      lastScrollTop: prev.scrollTop
    }));

    onScroll?.(scrollTop, direction);

    // Clear existing timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Set timeout to detect scroll end
    scrollTimeoutRef.current = setTimeout(() => {
      setScrollState(prev => ({
        ...prev,
        isScrolling: false
      }));
    }, 150);

    // Infinite scroll logic
    if (hasNextPage && onLoadMore && !loading) {
      const totalHeight = useVariableHeight
        ? items.reduce((sum, _, index) => sum + getItemHeight(index), 0)
        : items.length * (typeof itemHeight === 'number' ? itemHeight : 80);

      const scrollPercentage = (scrollTop + containerHeight) / totalHeight;

      if (scrollPercentage >= threshold) {
        onLoadMore();
      }
    }
  }, [onScroll, hasNextPage, onLoadMore, loading, threshold, containerHeight, items.length, getItemHeight, useVariableHeight, itemHeight]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Scroll to top function
  const scrollToTop = useCallback(() => {
    listRef.current?.scrollToItem(0, 'start');
  }, []);

  // Scroll to item function
  const scrollToItem = useCallback((index: number, align: 'start' | 'center' | 'end' = 'start') => {
    listRef.current?.scrollToItem(index, align);
  }, []);

  // Calculate total items including loading item
  const totalItems = hasNextPage && loading ? items.length + 1 : items.length;

  // Empty state
  if (items.length === 0 && !loading) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height: containerHeight }}>
        {emptyComponent || (
          <div className="text-center">
            <div className="text-gray-400 text-lg mb-2">No items found</div>
            <div className="text-gray-500 text-sm">Try adjusting your filters</div>
          </div>
        )}
      </div>
    );
  }

  // Render fixed height list
  if (!useVariableHeight) {
    return (
      <div className={`relative ${className}`}>
        <List
          ref={listRef}
          height={containerHeight}
          itemCount={totalItems}
          itemSize={typeof itemHeight === 'number' ? itemHeight : 80}
          onScroll={handleScroll}
          overscanCount={overscan}
          className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent hover:scrollbar-thumb-gray-400"
        >
          {hasNextPage ? LoadingItemRenderer : ItemRenderer}
        </List>

        {/* Scroll to top button */}
        <AnimatePresence>
          {scrollState.scrollTop > 200 && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={scrollToTop}
              className="absolute bottom-4 right-4 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors z-10"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Scroll indicator */}
        {scrollState.isScrolling && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute top-4 right-4 bg-black/75 text-white px-3 py-1 rounded-full text-sm z-10"
          >
            {Math.round((scrollState.scrollTop / (totalItems * (typeof itemHeight === 'number' ? itemHeight : 80))) * 100)}%
          </motion.div>
        )}
      </div>
    );
  }

  // Render variable height list
  return (
    <div className={`relative ${className}`}>
      <VariableSizeList
        ref={listRef}
        height={containerHeight}
        itemCount={totalItems}
        itemSize={getItemHeight}
        onScroll={handleScroll}
        overscanCount={overscan}
        className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent hover:scrollbar-thumb-gray-400"
      >
        {hasNextPage ? LoadingItemRenderer : ItemRenderer}
      </VariableSizeList>

      {/* Scroll to top button */}
      <AnimatePresence>
        {scrollState.scrollTop > 200 && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={scrollToTop}
            className="absolute bottom-4 right-4 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors z-10"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
};

// Performance optimized component wrapper
export default memo(VirtualScrollContainer) as typeof VirtualScrollContainer;

// Hook for managing virtual scroll state
export const useVirtualScroll = <T,>(items: T[], config?: Partial<VirtualScrollConfig>) => {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 0 });
  const [isScrolling, setIsScrolling] = useState(false);

  const configuration: VirtualScrollConfig = {
    item_height: 80,
    container_height: 600,
    buffer_size: 5,
    overscan: 5,
    ...config
  };

  const handleScroll = useCallback((scrollTop: number, direction: 'up' | 'down') => {
    const startIndex = Math.floor(scrollTop / configuration.item_height);
    const endIndex = Math.min(
      startIndex + Math.ceil(configuration.container_height / configuration.item_height) + configuration.overscan,
      items.length - 1
    );

    setVisibleRange({ start: startIndex, end: endIndex });
    setIsScrolling(true);

    // Debounce scroll end detection
    const timeoutId = setTimeout(() => {
      setIsScrolling(false);
    }, 150);

    return () => clearTimeout(timeoutId);
  }, [items.length, configuration]);

  const visibleItems = useMemo(() => {
    return items.slice(
      Math.max(0, visibleRange.start - configuration.buffer_size),
      Math.min(items.length, visibleRange.end + configuration.buffer_size)
    );
  }, [items, visibleRange, configuration.buffer_size]);

  return {
    visibleItems,
    visibleRange,
    isScrolling,
    handleScroll,
    configuration
  };
};

// Optimized list item component for better performance
export const OptimizedListItem = memo<{
  index: number;
  style: React.CSSProperties;
  children: React.ReactNode;
  className?: string;
}>(({ index, style, children, className = '' }) => {
  return (
    <div
      style={style}
      className={`${className} will-change-transform`}
      data-index={index}
    >
      {children}
    </div>
  );
});

OptimizedListItem.displayName = 'OptimizedListItem';

// Intersection observer hook for lazy loading
export const useIntersectionObserver = (
  callback: () => void,
  options: IntersectionObserverInit = {}
) => {
  const targetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const target = targetRef.current;
    if (!target) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        callback();
      }
    }, options);

    observer.observe(target);

    return () => {
      observer.unobserve(target);
    };
  }, [callback, options]);

  return targetRef;
};