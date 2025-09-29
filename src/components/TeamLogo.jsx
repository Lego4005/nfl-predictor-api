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

  // Map team abbreviations to SVG file names
  const getTeamSvgFileName = (abbr) => {
    const svgMap = {
      'BUF': 'buffalo_bills',
      'MIA': 'miami_dolphins',
      'NE': 'new_england_patriots',
      'NYJ': 'new_york_jets',
      'BAL': 'baltimore_ravens',
      'CIN': 'cincinnati_bengals',
      'CLE': 'cleveland_browns',
      'PIT': 'pittsburgh_steelers',
      'HOU': 'houston_texans',
      'IND': 'indianapolis_colts',
      'JAX': 'jacksonville_jaguars',
      'TEN': 'tennessee_titans',
      'DEN': 'denver_broncos',
      'KC': 'kansas_city_chiefs',
      'LV': 'las_vegas_raiders',
      'LAC': 'los_angeles_chargers',
      'DAL': 'dallas_cowboys',
      'NYG': 'new_york_giants',
      'PHI': 'philadelphia_eagles',
      'WSH': 'washington_commanders',
      'WAS': 'washington_commanders', // Alternative abbreviation
      'CHI': 'chicago_bears',
      'DET': 'detroit_lions',
      'GB': 'green_bay_packers',
      'MIN': 'minnesota_vikings',
      'ATL': 'atlanta_falcons',
      'CAR': 'carolina_panthers',
      'NO': 'new_orleans_saints',
      'TB': 'tampa_bay_buccaneers',
      'ARI': 'arizona_cardinals',
      'LAR': 'los_angeles_rams',
      'LA': 'los_angeles_rams', // Alternative for Rams
      'SF': 'san_francisco_49ers',
      'SEA': 'seattle_seahawks',
      'TBD': 'nfl', // For TBD games, use NFL logo
      'NFL': 'nfl' // Generic NFL logo
    };

    // Also check if the abbr is already uppercase
    const upperAbbr = abbr ? abbr.toUpperCase() : null;
    return svgMap[upperAbbr] || svgMap[abbr] || null;
  };

  // Generate logo URLs - Prioritize local SVGs
  const getLogoUrls = (abbr) => {
    if (!abbr) return { primary: null, fallback: null, placeholder: null };

    // Convert team name to abbreviation if needed
    const teamAbbr = getTeamAbbr(abbr);
    const abbrLower = teamAbbr.toLowerCase();
    const abbrUpper = teamAbbr.toUpperCase();
    const svgFileName = getTeamSvgFileName(abbrUpper);

    // Special handling for TBD
    if (abbrUpper === 'TBD' || abbrUpper === 'TBA') {
      return {
        primary: '/nfl_team_svgs/nfl.svg',
        secondary: null,
        fallback: null,
        placeholder: generatePlaceholderSVG('TBD')
      };
    }

    return {
      // Local SVGs as primary
      primary: svgFileName ? `/nfl_team_svgs/${svgFileName}.svg` : null,
      // ESPN logos as secondary fallback
      secondary: `https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/${abbrLower}.png&h=${dimensions.height}&w=${dimensions.width}`,
      // Alternative ESPN URL
      fallback: `https://a.espncdn.com/i/teamlogos/nfl/500/${abbrLower}.png`,
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

    // Debug: Log what team abbreviation we're getting
    console.log('TeamLogo: Loading logo for:', teamAbbr);

    setIsLoading(true);
    setHasErrored(false);

    const urls = getLogoUrls(teamAbbr);
    console.log('TeamLogo: URLs generated:', urls);

    // If we have a local SVG, try it first
    if (urls.primary) {
      const img1 = new Image();
      img1.onload = () => {
        console.log('TeamLogo: Successfully loaded local SVG for', teamAbbr);
        setCurrentSrc(urls.primary);
        setIsLoading(false);
      };
      img1.onerror = () => {
        console.log('TeamLogo: Failed to load local SVG for', teamAbbr, 'from', urls.primary);
        // Try ESPN as fallback
        const img2 = new Image();
        img2.onload = () => {
          setCurrentSrc(urls.secondary);
          setIsLoading(false);
        };
        img2.onerror = () => {
          // Try alternative ESPN URL
          const img3 = new Image();
          img3.onload = () => {
            setCurrentSrc(urls.fallback);
            setIsLoading(false);
          };
          img3.onerror = () => {
            console.log('TeamLogo: All sources failed for', teamAbbr, '- using placeholder');
            // Use placeholder
            setCurrentSrc(urls.placeholder);
            setIsLoading(false);
            setHasErrored(true);
            onError && onError();
          };
          img3.src = urls.fallback;
        };
        img2.src = urls.secondary;
      };
      img1.src = urls.primary;
    } else {
      console.log('TeamLogo: No local SVG mapping found for', teamAbbr);
      // No local SVG, try ESPN directly
      const img1 = new Image();
      img1.onload = () => {
        setCurrentSrc(urls.secondary);
        setIsLoading(false);
      };
      img1.onerror = () => {
        const img2 = new Image();
        img2.onload = () => {
          setCurrentSrc(urls.fallback);
          setIsLoading(false);
        };
        img2.onerror = () => {
          setCurrentSrc(urls.placeholder);
          setIsLoading(false);
          setHasErrored(true);
          onError && onError();
        };
        img2.src = urls.fallback;
      };
      img1.src = urls.secondary;
    }
  }, [teamAbbr, size, dimensions.width, dimensions.height]);

  // Skeleton loader element
  const skeletonElement = (
    <div
      className="animate-pulse bg-gradient-to-br from-gray-300 to-gray-200 dark:from-gray-700 dark:to-gray-600 rounded-lg"
      style={{
        width: dimensions.width,
        height: dimensions.height,
      }}
    />
  );

  const logoElement = (
    <img
      src={currentSrc}
      alt={alt || `${teamAbbr} logo`}
      className={`object-contain transition-opacity duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'} ${className}`}
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
          {isLoading && (
            <div className="absolute inset-0 z-10">
              {skeletonElement}
            </div>
          )}
          {logoElement}
        </div>
      </motion.div>
    );
  }

  return (
    <div className="relative inline-block">
      {isLoading && (
        <div className="absolute inset-0 z-10">
          {skeletonElement}
        </div>
      )}
      {logoElement}
    </div>
  );
};

export default TeamLogo;