/**
 * TeamLogo Component
 * Displays NFL team SVG logos with various styling options
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Team, TEAMS } from '@/lib/nfl-data';
import { getTeamLogo, getTeamGradient, getTeamColors } from '@/utils/teamLogos';

interface TeamLogoProps {
  team: string | Team; // Can be abbreviation string or Team object
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'gradient' | 'solid' | 'outline';
  showBackground?: boolean;
  showHoverEffect?: boolean;
  className?: string;
  onClick?: () => void;
}

export default function TeamLogo({
  team,
  size = 'md',
  variant = 'default',
  showBackground = false,
  showHoverEffect = true,
  className,
  onClick,
}: TeamLogoProps) {
  const [imageError, setImageError] = useState(false);
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const teamAbbr = typeof team === 'string' ? team : team.abbr;
  const teamData = typeof team === 'string' ? TEAMS[team] : team;
  const teamName = teamData?.name || teamAbbr;
  const logoPath = getTeamLogo(teamAbbr);
  const gradient = getTeamGradient(teamAbbr);
  const colors = getTeamColors(teamAbbr);

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-20 h-20',
    xl: 'w-32 h-32',
  };

  const containerSizes = {
    sm: 'w-10 h-10',
    md: 'w-14 h-14',
    lg: 'w-24 h-24',
    xl: 'w-36 h-36',
  };

  const paddingClasses = {
    sm: 'p-1',
    md: 'p-1.5',
    lg: 'p-2',
    xl: 'p-3',
  };

  // Load SVG content for inline rendering
  useEffect(() => {
    const loadSvg = async () => {
      try {
        const response = await fetch(logoPath);
        if (response.ok) {
          const text = await response.text();
          setSvgContent(text);
          setImageError(false);
        } else {
          setImageError(true);
        }
      } catch (error) {
        console.error('Failed to load SVG:', logoPath, error);
        setImageError(true);
      } finally {
        setLoading(false);
      }
    };

    loadSvg();
  }, [logoPath]);

  const renderLogo = () => {
    if (loading) {
      return (
        <div className="w-full h-full animate-pulse bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 rounded" />
      );
    }

    if (imageError || !svgContent) {
      // Fallback to shield icon with team abbreviation
      return (
        <div className="w-full h-full flex items-center justify-center">
          <Shield className="w-3/4 h-3/4 text-gray-400" />
          <span className="absolute text-xs font-bold text-gray-600 dark:text-gray-400">
            {teamAbbr}
          </span>
        </div>
      );
    }

    // Render SVG inline for better control
    return (
      <div
        className="w-full h-full flex items-center justify-center"
        dangerouslySetInnerHTML={{ __html: svgContent }}
        style={{
          '--team-primary': colors.primary,
          '--team-secondary': colors.secondary,
        } as React.CSSProperties}
      />
    );
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'gradient':
        return cn('bg-gradient-to-br', gradient);
      case 'solid':
        return 'bg-white dark:bg-gray-800';
      case 'outline':
        return 'border-2 border-current';
      default:
        return '';
    }
  };

  return (
    <motion.div
      className={cn(
        'relative inline-flex items-center justify-center',
        showBackground && containerSizes[size],
        showBackground && paddingClasses[size],
        showBackground && 'rounded-lg shadow-md',
        showBackground && getVariantClasses(),
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      whileHover={showHoverEffect ? { scale: 1.05 } : {}}
      whileTap={showHoverEffect && onClick ? { scale: 0.95 } : {}}
      title={teamName}
    >
      <div
        className={cn(
          'relative',
          sizeClasses[size],
          '[&_svg]:w-full [&_svg]:h-full [&_svg]:object-contain'
        )}
      >
        {renderLogo()}
      </div>

      {/* Hover overlay */}
      {showHoverEffect && onClick && (
        <div className="absolute inset-0 rounded-lg bg-black opacity-0 hover:opacity-10 transition-opacity duration-200" />
      )}
    </motion.div>
  );
}

/**
 * TeamLogoMatchup Component
 * Displays two team logos facing each other for game matchups
 */
interface TeamLogoMatchupProps {
  awayTeam: string;
  homeTeam: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showVs?: boolean;
  className?: string;
}

export function TeamLogoMatchup({
  awayTeam,
  homeTeam,
  size = 'md',
  showVs = true,
  className,
}: TeamLogoMatchupProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <TeamLogo
        team={awayTeam}
        size={size}
        showBackground
        variant="gradient"
      />
      {showVs && (
        <span className="text-gray-500 dark:text-gray-400 font-bold text-sm">
          @
        </span>
      )}
      <TeamLogo
        team={homeTeam}
        size={size}
        showBackground
        variant="gradient"
      />
    </div>
  );
}