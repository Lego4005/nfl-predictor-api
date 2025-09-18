/**
 * Swipe Indicator Component
 * Visual cues for swipe gestures on mobile devices
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface SwipeIndicatorProps {
  direction: 'left' | 'right' | 'up' | 'down';
  visible: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const SwipeIndicator: React.FC<SwipeIndicatorProps> = ({
  direction,
  visible,
  className = '',
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const getArrowPath = () => {
    switch (direction) {
      case 'left':
        return 'M15 18l-6-6 6-6';
      case 'right':
        return 'M9 18l6-6-6-6';
      case 'up':
        return 'M18 15l-6-6-6 6';
      case 'down':
        return 'M6 9l6 6 6-6';
      default:
        return 'M9 18l6-6-6-6';
    }
  };

  const getAnimationDirection = () => {
    switch (direction) {
      case 'left':
        return { x: [-5, 0, -5] };
      case 'right':
        return { x: [5, 0, 5] };
      case 'up':
        return { y: [-5, 0, -5] };
      case 'down':
        return { y: [5, 0, 5] };
      default:
        return { x: [5, 0, 5] };
    }
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className={`swipe-indicator ${sizeClasses[size]} ${className} flex items-center justify-center`}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{
            opacity: 1,
            scale: 1,
            ...getAnimationDirection()
          }}
          exit={{ opacity: 0, scale: 0.5 }}
          transition={{
            opacity: { duration: 0.2 },
            scale: { duration: 0.2 },
            x: {
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            },
            y: {
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }
          }}
        >
          <svg
            className="w-full h-full text-white opacity-70"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d={getArrowPath()} />
          </svg>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SwipeIndicator;