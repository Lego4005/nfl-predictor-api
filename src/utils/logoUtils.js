/**
 * NFL Team Logo Utilities
 * Handles local logo loading with ESPN CDN fallback
 */

// ESPN CDN URLs for fallback
const ESPN_LOGO_BASE = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/';

/**
 * Get team logo URL with fallback support
 * @param {string} teamAbbr - Team abbreviation (e.g., 'KC', 'BUF')
 * @param {string} size - Logo size ('small', 'medium', 'large')
 * @returns {object} - Logo configuration with primary and fallback URLs
 */
export const getTeamLogo = (teamAbbr, size = 'medium') => {
  if (!teamAbbr) return getDefaultLogo();

  const abbr = teamAbbr.toLowerCase();

  // Size mapping
  const sizeMap = {
    small: { width: 32, height: 32 },
    medium: { width: 64, height: 64 },
    large: { width: 96, height: 96 },
    xlarge: { width: 128, height: 128 }
  };

  const dimensions = sizeMap[size] || sizeMap.medium;

  return {
    // Try local logo first
    primary: `/logos/${abbr.toUpperCase()}.svg`,
    primaryPng: `/logos/${abbr.toUpperCase()}.png`,
    // ESPN CDN fallback
    fallback: `${ESPN_LOGO_BASE}${abbr}.png&h=${dimensions.height}&w=${dimensions.width}`,
    // Generic fallback
    default: getDefaultLogoUrl(teamAbbr),
    alt: `${teamAbbr} logo`,
    dimensions
  };
};

/**
 * Get default/placeholder logo
 */
export const getDefaultLogo = () => ({
  primary: '/logos/NFL.svg',
  fallback: 'data:image/svg+xml;base64,' + btoa(getDefaultSVG()),
  default: 'data:image/svg+xml;base64,' + btoa(getDefaultSVG()),
  alt: 'NFL team logo',
  dimensions: { width: 64, height: 64 }
});

/**
 * Generate a default SVG logo placeholder
 */
const getDefaultSVG = (teamAbbr = 'NFL') => `
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="30" fill="#013369" stroke="#D50A0A" stroke-width="2"/>
  <text x="32" y="38" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="12" font-weight="bold">
    ${teamAbbr}
  </text>
</svg>
`;

/**
 * Get a team-specific default logo URL
 */
const getDefaultLogoUrl = (teamAbbr) => {
  return 'data:image/svg+xml;base64,' + btoa(getDefaultSVG(teamAbbr));
};

/**
 * Preload logo with fallback handling
 * @param {string} teamAbbr - Team abbreviation
 * @param {string} size - Logo size
 * @returns {Promise<string>} - Resolved logo URL
 */
export const preloadTeamLogo = (teamAbbr, size = 'medium') => {
  return new Promise((resolve) => {
    const logo = getTeamLogo(teamAbbr, size);

    // Try primary (local) first
    const img1 = new Image();
    img1.onload = () => resolve(logo.primary);
    img1.onerror = () => {
      // Try fallback (ESPN CDN)
      const img2 = new Image();
      img2.onload = () => resolve(logo.fallback);
      img2.onerror = () => resolve(logo.default);
      img2.src = logo.fallback;
    };
    img1.src = logo.primary;
  });
};

export default {
  getTeamLogo,
  getDefaultLogo,
  preloadTeamLogo
};