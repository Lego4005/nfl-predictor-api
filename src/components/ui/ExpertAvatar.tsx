/**
 * ExpertAvatar Component
 * Displays expert images with council badges and fallbacks
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Crown, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ExpertPersonality } from '@/data/expertPersonalities';
import { getExpertImage, getExpertInitials, getExpertGradient } from '@/utils/expertImages';

interface ExpertAvatarProps {
  expert: ExpertPersonality | { name?: string; id?: string };
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCouncilBadge?: boolean;
  showHoverEffect?: boolean;
  className?: string;
  onClick?: () => void;
}

export default function ExpertAvatar({
  expert,
  size = 'md',
  showCouncilBadge = true,
  showHoverEffect = true,
  className,
  onClick,
}: ExpertAvatarProps) {
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  const sizeClasses = {
    sm: 'w-10 h-10',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
    xl: 'w-32 h-32',
  };

  const badgeSizes = {
    sm: 'w-4 h-4 -top-1 -right-1',
    md: 'w-6 h-6 -top-1 -right-1',
    lg: 'w-8 h-8 -top-2 -right-2',
    xl: 'w-10 h-10 -top-3 -right-3',
  };

  const fontSize = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-lg',
    xl: 'text-2xl',
  };

  const isCouncilMember = 'council_position' in expert && expert.council_position;
  const expertName = 'name' in expert ? expert.name : 'Expert';
  const initials = getExpertInitials(expertName || 'Expert');
  const gradient = 'council_position' in expert ? getExpertGradient(expert as ExpertPersonality) : 'from-gray-400 to-gray-600';
  const imageUrl = getExpertImage(expert);

  const handleImageError = () => {
    setImageError(true);
    setImageLoading(false);
  };

  const handleImageLoad = () => {
    setImageLoading(false);
  };

  return (
    <motion.div
      className={cn(
        'relative inline-block',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      whileHover={showHoverEffect ? { scale: 1.05 } : {}}
      whileTap={showHoverEffect && onClick ? { scale: 0.95 } : {}}
    >
      <div
        className={cn(
          'relative overflow-hidden rounded-full bg-gradient-to-br',
          sizeClasses[size],
          gradient,
          'shadow-lg'
        )}
      >
        {/* Loading skeleton */}
        {imageLoading && !imageError && (
          <div className="absolute inset-0 animate-pulse bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800" />
        )}

        {/* Expert Image */}
        {!imageError ? (
          <img
            src={imageUrl}
            alt={expertName}
            className={cn(
              'absolute inset-0 w-full h-full object-cover',
              imageLoading && 'opacity-0',
              !imageLoading && 'opacity-100 transition-opacity duration-300'
            )}
            onError={handleImageError}
            onLoad={handleImageLoad}
          />
        ) : (
          // Fallback to initials if image fails
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-600 to-gray-800">
            {initials ? (
              <span className={cn('font-bold text-white', fontSize[size])}>
                {initials}
              </span>
            ) : (
              <User className="w-1/2 h-1/2 text-white opacity-60" />
            )}
          </div>
        )}

        {/* Hover overlay */}
        {showHoverEffect && onClick && (
          <div className="absolute inset-0 bg-black opacity-0 hover:opacity-20 transition-opacity duration-200" />
        )}

        {/* Glow effect for council members */}
        {isCouncilMember && (
          <div className="absolute inset-0 rounded-full animate-pulse ring-2 ring-yellow-400/50" />
        )}
      </div>

      {/* Council Badge */}
      {showCouncilBadge && isCouncilMember && (
        <motion.div
          className={cn(
            'absolute flex items-center justify-center rounded-full',
            'bg-gradient-to-br from-yellow-400 to-amber-500',
            'shadow-lg border-2 border-white dark:border-gray-800',
            badgeSizes[size]
          )}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 500, damping: 15 }}
        >
          {expert.council_position === 1 ? (
            <Crown className="w-3/4 h-3/4 text-white" />
          ) : (
            <span className="text-white font-bold text-xs">
              {expert.council_position}
            </span>
          )}
        </motion.div>
      )}

      {/* Optional tooltip or name display */}
      {showHoverEffect && (
        <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 opacity-0 hover:opacity-100 transition-opacity pointer-events-none">
          <div className="bg-black/80 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
            {expertName}
          </div>
        </div>
      )}
    </motion.div>
  );
}