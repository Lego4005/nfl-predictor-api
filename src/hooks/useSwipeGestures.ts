/**
 * Custom hook for handling swipe gestures on mobile devices
 * Optimized for touch interactions with configurable thresholds
 */

import { useCallback, useRef, useEffect } from 'react';

interface SwipeGesturesOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number; // Minimum distance for swipe
  velocity?: number; // Minimum velocity for swipe
  preventDefaultScroll?: boolean;
}

interface TouchData {
  startX: number;
  startY: number;
  startTime: number;
  element: EventTarget | null;
}

export const useSwipeGestures = ({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  velocity = 0.3,
  preventDefaultScroll = false
}: SwipeGesturesOptions) => {
  const touchData = useRef<TouchData | null>(null);
  const isSwipingRef = useRef(false);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touch = e.touches[0];
    touchData.current = {
      startX: touch.clientX,
      startY: touch.clientY,
      startTime: Date.now(),
      element: e.target
    };
    isSwipingRef.current = false;

    // Prevent default scroll behavior if enabled
    if (preventDefaultScroll) {
      e.preventDefault();
    }
  }, [preventDefaultScroll]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!touchData.current) return;

    const touch = e.touches[0];
    const deltaX = touch.clientX - touchData.current.startX;
    const deltaY = touch.clientY - touchData.current.startY;

    // Determine if this is a swipe gesture
    const isHorizontalSwipe = Math.abs(deltaX) > Math.abs(deltaY);
    const isVerticalSwipe = Math.abs(deltaY) > Math.abs(deltaX);

    // Prevent default scroll for swipe gestures
    if (preventDefaultScroll && (isHorizontalSwipe || isVerticalSwipe)) {
      e.preventDefault();
    }

    // Set swiping flag to prevent other interactions
    if ((Math.abs(deltaX) > threshold / 2) || (Math.abs(deltaY) > threshold / 2)) {
      isSwipingRef.current = true;
    }
  }, [threshold, preventDefaultScroll]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (!touchData.current) return;

    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchData.current.startX;
    const deltaY = touch.clientY - touchData.current.startY;
    const deltaTime = Date.now() - touchData.current.startTime;

    // Calculate velocity (pixels per millisecond)
    const velocityX = Math.abs(deltaX) / deltaTime;
    const velocityY = Math.abs(deltaY) / deltaTime;

    // Check if swipe meets threshold and velocity requirements
    const isHorizontalSwipe = Math.abs(deltaX) > threshold && velocityX > velocity;
    const isVerticalSwipe = Math.abs(deltaY) > threshold && velocityY > velocity;

    // Trigger appropriate swipe handler
    if (isHorizontalSwipe) {
      if (deltaX > 0) {
        onSwipeRight?.();
      } else {
        onSwipeLeft?.();
      }
    } else if (isVerticalSwipe) {
      if (deltaY > 0) {
        onSwipeDown?.();
      } else {
        onSwipeUp?.();
      }
    }

    // Reset touch data
    touchData.current = null;
    isSwipingRef.current = false;
  }, [threshold, velocity, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  // Mouse events for desktop testing
  const handleMouseDown = useCallback((e: MouseEvent) => {
    touchData.current = {
      startX: e.clientX,
      startY: e.clientY,
      startTime: Date.now(),
      element: e.target
    };
    isSwipingRef.current = false;
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!touchData.current || !e.buttons) return;

    const deltaX = e.clientX - touchData.current.startX;
    const deltaY = e.clientY - touchData.current.startY;

    if ((Math.abs(deltaX) > threshold / 2) || (Math.abs(deltaY) > threshold / 2)) {
      isSwipingRef.current = true;
    }
  }, [threshold]);

  const handleMouseUp = useCallback((e: MouseEvent) => {
    if (!touchData.current) return;

    const deltaX = e.clientX - touchData.current.startX;
    const deltaY = e.clientY - touchData.current.startY;
    const deltaTime = Date.now() - touchData.current.startTime;

    const velocityX = Math.abs(deltaX) / deltaTime;
    const velocityY = Math.abs(deltaY) / deltaTime;

    const isHorizontalSwipe = Math.abs(deltaX) > threshold && velocityX > velocity;
    const isVerticalSwipe = Math.abs(deltaY) > threshold && velocityY > velocity;

    if (isHorizontalSwipe) {
      if (deltaX > 0) {
        onSwipeRight?.();
      } else {
        onSwipeLeft?.();
      }
    } else if (isVerticalSwipe) {
      if (deltaY > 0) {
        onSwipeDown?.();
      } else {
        onSwipeUp?.();
      }
    }

    touchData.current = null;
    isSwipingRef.current = false;
  }, [threshold, velocity, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  // Return handlers for React components
  const swipeHandlers = {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
    onMouseDown: handleMouseDown,
    onMouseMove: handleMouseMove,
    onMouseUp: handleMouseUp,
    style: {
      touchAction: preventDefaultScroll ? 'none' : 'auto'
    }
  };

  return {
    swipeHandlers,
    isSwiping: isSwipingRef.current
  };
};