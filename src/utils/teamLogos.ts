/**
 * NFL Team Logo Mapping Utility
 * Maps team abbreviations to their corresponding SVG files
 */

import { Team } from '@/lib/nfl-data';

// Mapping of team abbreviations to SVG filenames
const TEAM_LOGO_MAP: Record<string, string> = {
  // AFC East
  'BUF': 'buffalo_bills.svg',
  'MIA': 'miami_dolphins.svg',
  'NE': 'new_england_patriots.svg',
  'NYJ': 'new_york_jets.svg',

  // AFC North
  'BAL': 'baltimore_ravens.svg',
  'CIN': 'cincinnati_bengals.svg',
  'CLE': 'cleveland_browns.svg',
  'PIT': 'pittsburgh_steelers.svg',

  // AFC South
  'HOU': 'houston_texans.svg',
  'IND': 'indianapolis_colts.svg',
  'JAX': 'jacksonville_jaguars.svg',
  'TEN': 'tennessee_titans.svg',

  // AFC West
  'DEN': 'denver_broncos.svg',
  'KC': 'kansas_city_chiefs.svg',
  'LAC': 'los_angeles_chargers.svg',
  'LV': 'las_vegas_raiders.svg',

  // NFC East
  'DAL': 'dallas_cowboys.svg',
  'NYG': 'new_york_giants.svg',
  'PHI': 'philadelphia_eagles.svg',
  'WAS': 'washington_commanders.svg',

  // NFC North
  'CHI': 'chicago_bears.svg',
  'DET': 'detroit_lions.svg',
  'GB': 'green_bay_packers.svg',
  'MIN': 'minnesota_vikings.svg',

  // NFC South
  'ATL': 'atlanta_falcons.svg',
  'CAR': 'carolina_panthers.svg',
  'NO': 'new_orleans_saints.svg',
  'TB': 'tampa_bay_buccaneers.svg',

  // NFC West
  'ARI': 'arizona_cardinals.svg',
  'LAR': 'los_angeles_rams.svg',
  'SF': 'san_francisco_49ers.svg',
  'SEA': 'seattle_seahawks.svg',

  // NFL Logo
  'NFL': 'nfl.svg',
};

// Alternate team name mappings (for flexibility)
const TEAM_NAME_MAP: Record<string, string> = {
  // Full names
  'Buffalo Bills': 'BUF',
  'Miami Dolphins': 'MIA',
  'New England Patriots': 'NE',
  'New York Jets': 'NYJ',
  'Baltimore Ravens': 'BAL',
  'Cincinnati Bengals': 'CIN',
  'Cleveland Browns': 'CLE',
  'Pittsburgh Steelers': 'PIT',
  'Houston Texans': 'HOU',
  'Indianapolis Colts': 'IND',
  'Jacksonville Jaguars': 'JAX',
  'Tennessee Titans': 'TEN',
  'Denver Broncos': 'DEN',
  'Kansas City Chiefs': 'KC',
  'Los Angeles Chargers': 'LAC',
  'Las Vegas Raiders': 'LV',
  'Dallas Cowboys': 'DAL',
  'New York Giants': 'NYG',
  'Philadelphia Eagles': 'PHI',
  'Washington Commanders': 'WAS',
  'Chicago Bears': 'CHI',
  'Detroit Lions': 'DET',
  'Green Bay Packers': 'GB',
  'Minnesota Vikings': 'MIN',
  'Atlanta Falcons': 'ATL',
  'Carolina Panthers': 'CAR',
  'New Orleans Saints': 'NO',
  'Tampa Bay Buccaneers': 'TB',
  'Arizona Cardinals': 'ARI',
  'Los Angeles Rams': 'LAR',
  'San Francisco 49ers': 'SF',
  'Seattle Seahawks': 'SEA',

  // Short names
  'Bills': 'BUF',
  'Dolphins': 'MIA',
  'Patriots': 'NE',
  'Jets': 'NYJ',
  'Ravens': 'BAL',
  'Bengals': 'CIN',
  'Browns': 'CLE',
  'Steelers': 'PIT',
  'Texans': 'HOU',
  'Colts': 'IND',
  'Jaguars': 'JAX',
  'Titans': 'TEN',
  'Broncos': 'DEN',
  'Chiefs': 'KC',
  'Chargers': 'LAC',
  'Raiders': 'LV',
  'Cowboys': 'DAL',
  'Giants': 'NYG',
  'Eagles': 'PHI',
  'Commanders': 'WAS',
  'Bears': 'CHI',
  'Lions': 'DET',
  'Packers': 'GB',
  'Vikings': 'MIN',
  'Falcons': 'ATL',
  'Panthers': 'CAR',
  'Saints': 'NO',
  'Buccaneers': 'TB',
  'Cardinals': 'ARI',
  'Rams': 'LAR',
  '49ers': 'SF',
  'Seahawks': 'SEA',
};

/**
 * Get the logo path for a team by abbreviation
 */
export function getTeamLogo(teamAbbr: string): string {
  const logoFile = TEAM_LOGO_MAP[teamAbbr.toUpperCase()];
  if (!logoFile) {
    console.warn(`No logo found for team: ${teamAbbr}`);
    return '/nfl_team_svgs/nfl.svg'; // Fallback to NFL logo
  }
  return `/nfl_team_svgs/${logoFile}`;
}

/**
 * Get the logo path for a team by full name or abbreviation
 */
export function getTeamLogoByName(teamName: string): string {
  // First check if it's already an abbreviation
  let abbr = teamName.toUpperCase();
  if (TEAM_LOGO_MAP[abbr]) {
    return getTeamLogo(abbr);
  }

  // Try to find the abbreviation from the full name
  const foundAbbr = TEAM_NAME_MAP[teamName];
  if (foundAbbr) {
    return getTeamLogo(foundAbbr);
  }

  console.warn(`No logo found for team name: ${teamName}`);
  return '/nfl_team_svgs/nfl.svg'; // Fallback to NFL logo
}

/**
 * Get team gradient colors based on team abbreviation
 */
export function getTeamGradient(teamAbbr: string): string {
  const gradients: Record<string, string> = {
    // AFC East
    'BUF': 'from-blue-600 to-red-600',
    'MIA': 'from-teal-500 to-orange-500',
    'NE': 'from-blue-900 to-red-700',
    'NYJ': 'from-green-700 to-white',

    // AFC North
    'BAL': 'from-purple-800 to-black',
    'CIN': 'from-orange-600 to-black',
    'CLE': 'from-orange-700 to-brown-800',
    'PIT': 'from-yellow-400 to-black',

    // AFC South
    'HOU': 'from-blue-900 to-red-700',
    'IND': 'from-blue-700 to-white',
    'JAX': 'from-teal-600 to-gold-500',
    'TEN': 'from-blue-800 to-red-600',

    // AFC West
    'DEN': 'from-orange-600 to-blue-800',
    'KC': 'from-red-700 to-yellow-500',
    'LAC': 'from-blue-500 to-yellow-400',
    'LV': 'from-black to-gray-400',

    // NFC East
    'DAL': 'from-blue-800 to-gray-400',
    'NYG': 'from-blue-700 to-red-600',
    'PHI': 'from-green-800 to-gray-300',
    'WAS': 'from-red-800 to-yellow-600',

    // NFC North
    'CHI': 'from-blue-900 to-orange-600',
    'DET': 'from-blue-600 to-gray-400',
    'GB': 'from-green-700 to-yellow-500',
    'MIN': 'from-purple-700 to-yellow-500',

    // NFC South
    'ATL': 'from-red-700 to-black',
    'CAR': 'from-blue-500 to-black',
    'NO': 'from-gold-500 to-black',
    'TB': 'from-red-700 to-gray-800',

    // NFC West
    'ARI': 'from-red-700 to-black',
    'LAR': 'from-blue-700 to-yellow-500',
    'SF': 'from-red-700 to-gold-500',
    'SEA': 'from-blue-600 to-green-600',
  };

  return gradients[teamAbbr.toUpperCase()] || 'from-gray-600 to-gray-800';
}

/**
 * Get team colors as an object
 */
export function getTeamColors(teamAbbr: string): { primary: string; secondary: string } {
  const colors: Record<string, { primary: string; secondary: string }> = {
    // AFC East
    'BUF': { primary: '#00338D', secondary: '#C60C30' },
    'MIA': { primary: '#008E97', secondary: '#FC4C02' },
    'NE': { primary: '#002244', secondary: '#C60C30' },
    'NYJ': { primary: '#125740', secondary: '#FFFFFF' },

    // AFC North
    'BAL': { primary: '#241773', secondary: '#000000' },
    'CIN': { primary: '#FB4F14', secondary: '#000000' },
    'CLE': { primary: '#311D00', secondary: '#FF3C00' },
    'PIT': { primary: '#FFB612', secondary: '#101820' },

    // AFC South
    'HOU': { primary: '#03202F', secondary: '#A71930' },
    'IND': { primary: '#002C5F', secondary: '#FFFFFF' },
    'JAX': { primary: '#006778', secondary: '#D7A22A' },
    'TEN': { primary: '#0C2340', secondary: '#C8102E' },

    // AFC West
    'DEN': { primary: '#FB4F14', secondary: '#002244' },
    'KC': { primary: '#E31837', secondary: '#FFB81C' },
    'LAC': { primary: '#0080C6', secondary: '#FFC20E' },
    'LV': { primary: '#000000', secondary: '#A5ACAF' },

    // NFC East
    'DAL': { primary: '#041E42', secondary: '#869397' },
    'NYG': { primary: '#0B2265', secondary: '#A71930' },
    'PHI': { primary: '#004C54', secondary: '#A5ACAF' },
    'WAS': { primary: '#5A1414', secondary: '#FFB612' },

    // NFC North
    'CHI': { primary: '#0B162A', secondary: '#C83803' },
    'DET': { primary: '#0076B6', secondary: '#B0B7BC' },
    'GB': { primary: '#203731', secondary: '#FFB612' },
    'MIN': { primary: '#4F2683', secondary: '#FFC62F' },

    // NFC South
    'ATL': { primary: '#A71930', secondary: '#000000' },
    'CAR': { primary: '#0085CA', secondary: '#101820' },
    'NO': { primary: '#D3BC8D', secondary: '#101820' },
    'TB': { primary: '#D50A0A', secondary: '#34302B' },

    // NFC West
    'ARI': { primary: '#97233F', secondary: '#000000' },
    'LAR': { primary: '#003594', secondary: '#FFA300' },
    'SF': { primary: '#AA0000', secondary: '#B3995D' },
    'SEA': { primary: '#002244', secondary: '#69BE28' },
  };

  return colors[teamAbbr.toUpperCase()] || { primary: '#666666', secondary: '#999999' };
}

/**
 * Check if team logo exists
 */
export function hasTeamLogo(teamAbbr: string): boolean {
  return !!TEAM_LOGO_MAP[teamAbbr.toUpperCase()];
}