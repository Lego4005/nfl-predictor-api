/**
 * Touch-optimized button component for mobile interactions
 * Features haptic feedback, larger touch targets, and smooth animations
 */

import React, { useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';

interface TouchOptimizedButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  onLongPress?: () => void;
  className?: string;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  hapticFeedback?: boolean;
  longPressDelay?: number;
}

const TouchOptimizedButton: React.FC<TouchOptimizedButtonProps> = ({
  children,
  onClick,
  onLongPress,
  className = '',
  disabled = false,
  variant = 'primary',
  size = 'md',
  hapticFeedback = true,
  longPressDelay = 500
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [isLongPressed, setIsLongPressed] = useState(false);
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);
  const pressStartTime = useRef<number>(0);

  // Haptic feedback function
  const triggerHapticFeedback = useCallback((type: 'light' | 'medium' | 'heavy' = 'light') => {
    if (!hapticFeedback || !('vibrate' in navigator)) return;

    const patterns = {
      light: [10],
      medium: [20],
      heavy: [30, 10, 30]
    };

    navigator.vibrate(patterns[type]);
  }, [hapticFeedback]);

  // Handle touch start
  const handleTouchStart = useCallback(() => {
    if (disabled) return;

    setIsPressed(true);
    pressStartTime.current = Date.now();
    triggerHapticFeedback('light');

    // Set up long press timer
    if (onLongPress) {
      longPressTimer.current = setTimeout(() => {
        setIsLongPressed(true);
        triggerHapticFeedback('heavy');
        onLongPress();
      }, longPressDelay);
    }
  }, [disabled, onLongPress, longPressDelay, triggerHapticFeedback]);

  // Handle touch end
  const handleTouchEnd = useCallback(() => {
    if (disabled) return;

    setIsPressed(false);

    // Clear long press timer
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }

    // If it wasn't a long press and we have an onClick handler
    if (!isLongPressed && onClick) {
      const pressDuration = Date.now() - pressStartTime.current;

      // Only trigger click if it was a quick press
      if (pressDuration < longPressDelay) {
        triggerHapticFeedback('medium');
        onClick();
      }
    }

    setIsLongPressed(false);
  }, [disabled, isLongPressed, onClick, longPressDelay, triggerHapticFeedback]);

  // Handle touch cancel
  const handleTouchCancel = useCallback(() => {
    setIsPressed(false);
    setIsLongPressed(false);

    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  // Handle mouse events for desktop compatibility
  const handleMouseDown = useCallback(() => {
    if (disabled) return;
    setIsPressed(true);
    pressStartTime.current = Date.now();
  }, [disabled]);

  const handleMouseUp = useCallback(() => {
    if (disabled) return;
    setIsPressed(false);

    if (!isLongPressed && onClick) {
      onClick();
    }
    setIsLongPressed(false);
  }, [disabled, isLongPressed, onClick]);

  const handleMouseLeave = useCallback(() => {
    setIsPressed(false);
    setIsLongPressed(false);

    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  // Variant styles
  const variantStyles = {
    primary: 'bg-blue-600 text-white border-blue-600',
    secondary: 'bg-gray-600 text-white border-gray-600',
    ghost: 'bg-transparent text-current border-transparent'
  };

  // Size styles
  const sizeStyles = {
    sm: 'px-3 py-2 text-sm min-h-[44px]', // 44px minimum for touch targets
    md: 'px-4 py-3 text-base min-h-[44px]',
    lg: 'px-6 py-4 text-lg min-h-[48px]'
  };

  // Disabled styles
  const disabledStyles = 'opacity-50 cursor-not-allowed';

  // Pressed styles
  const pressedStyles = 'scale-95 opacity-80';

  return (
    <motion.button
      className={`
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${disabled ? disabledStyles : ''}
        ${className}
        relative
        rounded-lg
        border
        font-medium
        transition-all
        duration-150
        touch-manipulation
        select-none
        active:outline-none
        focus:outline-none
        focus:ring-2
        focus:ring-blue-500
        focus:ring-opacity-50
      `}
      disabled={disabled}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchCancel}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      animate={{
        scale: isPressed ? 0.95 : 1,
        opacity: isPressed ? 0.8 : 1
      }}
      transition={{
        type: "spring",
        stiffness: 500,
        damping: 30
      }}
      whileTap={{
        scale: 0.95
      }}
    >
      {/* Ripple effect overlay */}
      {isPressed && (
        <motion.div
          className="absolute inset-0 bg-white bg-opacity-20 rounded-lg"
          initial={{ scale: 0, opacity: 1 }}
          animate={{ scale: 1, opacity: 0 }}
          transition={{ duration: 0.4 }}
        />
      )}

      {/* Button content */}
      <span className="relative z-10">
        {children}
      </span>

      {/* Long press indicator */}
      {isPressed && onLongPress && (
        <motion.div
          className="absolute inset-0 border-2 border-white border-opacity-50 rounded-lg"
          initial={{ scale: 1 }}
          animate={{ scale: 1.05 }}
          transition={{
            duration: longPressDelay / 1000,
            ease: "linear"
          }}
        />
      )}
    </motion.button>
  );
};

export default TouchOptimizedButton;