import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

/**
 * Enhanced Team Logo Component with fallback support
 * Tries local logo first, then ESPN CDN, then generates placeholder
 */
const TeamLogo = ({
  teamAbbr,
  size = 'medium',
  className = '',
  style = {},
  showGlow = false,
  animated = false,
  alt,
  onError,
  ...props
}) => {
  const [currentSrc, setCurrentSrc] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasErrored, setHasErrored] = useState(false);

  // Size configurations
  const sizeMap = {
    small: { width: 32, height: 32 },
    medium: { width: 64, height: 64 },
    large: { width: 96, height: 96 },
    xlarge: { width: 128, height: 128 }
  };

  const dimensions = sizeMap[size] || sizeMap.medium;

  // Team name to abbreviation mapping
  const getTeamAbbr = (teamName) => {
    const teamMap = {
      'Packers': 'GB', 'Commanders': 'WSH', 'Bengals': 'CIN', 'Jaguars': 'JAX',
      'Cowboys': 'DAL', 'Giants': 'NYG', 'Lions': 'DET', 'Bears': 'CHI',
      'Titans': 'TEN', 'Rams': 'LAR', 'Dolphins': 'MIA', 'Patriots': 'NE',
      'Saints': 'NO', '49ers': 'SF', 'Jets': 'NYJ', 'Bills': 'BUF',
      'Steelers': 'PIT', 'Seahawks': 'SEA', 'Ravens': 'BAL', 'Browns': 'CLE',
      'Colts': 'IND', 'Broncos': 'DEN', 'Cardinals': 'ARI', 'Panthers': 'CAR',
      'Chiefs': 'KC', 'Eagles': 'PHI', 'Vikings': 'MIN', 'Falcons': 'ATL',
      'Texans': 'HOU', 'Buccaneers': 'TB', 'Raiders': 'LV', 'Chargers': 'LAC'
    };
    return teamMap[teamName] || teamName;
  };

  // Generate logo URLs - Prioritize ESPN logos
  const getLogoUrls = (abbr) => {
    if (!abbr) return { primary: null, fallback: null, placeholder: null };

    // Convert team name to abbreviation if needed
    const teamAbbr = getTeamAbbr(abbr);
    const abbrLower = teamAbbr.toLowerCase();
    const abbrUpper = teamAbbr.toUpperCase();

    return {
      // ESPN logos as primary (real team logos)
      primary: `https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/${abbrLower}.png&h=${dimensions.height}&w=${dimensions.width}`,
      // Alternative ESPN URL
      secondary: `https://a.espncdn.com/i/teamlogos/nfl/500/${abbrLower}.png`,
      // Local logos as fallback
      fallback: `/logos/${abbrUpper}.svg`,
      fallbackPng: `/logos/${abbrUpper}.png`,
      // Generated placeholder as last resort
      placeholder: generatePlaceholderSVG(abbrUpper)
    };
  };

  // Generate SVG placeholder
  const generatePlaceholderSVG = (abbr) => {
    const svg = `
      <svg width="${dimensions.width}" height="${dimensions.height}" viewBox="0 0 ${dimensions.width} ${dimensions.height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="gradient-${abbr}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#013369;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#D50A0A;stop-opacity:1" />
          </linearGradient>
        </defs>
        <circle cx="${dimensions.width/2}" cy="${dimensions.height/2}" r="${dimensions.width/2 - 2}" fill="url(#gradient-${abbr})" stroke="#FFFFFF" stroke-width="2"/>
        <text x="${dimensions.width/2}" y="${dimensions.height/2 + 6}" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="${Math.max(8, dimensions.width/8)}" font-weight="bold" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
          ${abbr}
        </text>
      </svg>
    `;
    return `data:image/svg+xml;base64,${btoa(svg)}`;
  };

  // Load logo with fallback chain
  useEffect(() => {
    if (!teamAbbr) {
      setCurrentSrc(generatePlaceholderSVG('NFL'));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setHasErrored(false);

    const urls = getLogoUrls(teamAbbr);

    // Try ESPN logo first (real team logos)
    const img1 = new Image();
    img1.onload = () => {
      setCurrentSrc(urls.primary);
      setIsLoading(false);
    };
    img1.onerror = () => {
      // Try alternative ESPN URL
      const img2 = new Image();
      img2.onload = () => {
        setCurrentSrc(urls.secondary);
        setIsLoading(false);
      };
      img2.onerror = () => {
        // Try local SVG fallback
        const img3 = new Image();
        img3.onload = () => {
          setCurrentSrc(urls.fallback);
          setIsLoading(false);
        };
        img3.onerror = () => {
          // Try local PNG fallback
          const img4 = new Image();
          img4.onload = () => {
            setCurrentSrc(urls.fallbackPng);
            setIsLoading(false);
          };
          img4.onerror = () => {
            // Use placeholder
            setCurrentSrc(urls.placeholder);
            setIsLoading(false);
            setHasErrored(true);
            onError && onError();
          };
          img4.src = urls.fallbackPng;
        };
        img3.src = urls.fallback;
      };
      img2.src = urls.secondary;
    };
    img1.src = urls.primary;
  }, [teamAbbr, size, dimensions.width, dimensions.height]);

  const logoElement = (
    <img
      src={currentSrc}
      alt={alt || `${teamAbbr} logo`}
      className={`object-contain transition-opacity duration-300 ${isLoading ? 'opacity-50' : 'opacity-100'} ${className}`}
      style={{
        width: dimensions.width,
        height: dimensions.height,
        ...style
      }}
      {...props}
    />
  );

  // Wrap with motion and glow effect if requested
  if (animated || showGlow) {
    return (
      <motion.div
        className="relative inline-block"
        whileHover={animated ? { rotate: 360 } : {}}
        transition={animated ? { duration: 0.6 } : {}}
      >
        {showGlow && (
          <div
            className="absolute inset-0 blur-2xl opacity-40"
            style={{
              background: `linear-gradient(135deg, var(--team-primary, #013369) 0%, var(--team-secondary, #D50A0A) 100%)`
            }}
          />
        )}
        <div className="relative">
          {logoElement}
        </div>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
          </div>
        )}
      </motion.div>
    );
  }

  return (
    <div className="relative inline-block">
      {logoElement}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
};

export default TeamLogo;