#!/usr/bin/env node

/**
 * Generate placeholder logo files for NFL teams
 * This creates SVG placeholders until actual logo files are added
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Team data with colors for placeholder generation
const teams = {
  // AFC East
  BUF: { name: 'Bills', colors: ['#00338D', '#C60C30'] },
  MIA: { name: 'Dolphins', colors: ['#008E97', '#FC4C02'] },
  NE: { name: 'Patriots', colors: ['#002244', '#C60C30'] },
  NYJ: { name: 'Jets', colors: ['#125740', '#000000'] },

  // AFC North
  BAL: { name: 'Ravens', colors: ['#241773', '#9E7C0C'] },
  CIN: { name: 'Bengals', colors: ['#FB4F14', '#000000'] },
  CLE: { name: 'Browns', colors: ['#311D00', '#FF3C00'] },
  PIT: { name: 'Steelers', colors: ['#FFB612', '#101820'] },

  // AFC South
  HOU: { name: 'Texans', colors: ['#03202F', '#A71930'] },
  IND: { name: 'Colts', colors: ['#002C5F', '#A2AAAD'] },
  JAX: { name: 'Jaguars', colors: ['#006778', '#D7A22A'] },
  TEN: { name: 'Titans', colors: ['#0C2340', '#4B92DB'] },

  // AFC West
  DEN: { name: 'Broncos', colors: ['#FB4F14', '#002244'] },
  KC: { name: 'Chiefs', colors: ['#E31837', '#FFB81C'] },
  LV: { name: 'Raiders', colors: ['#000000', '#A5ACAF'] },
  LAC: { name: 'Chargers', colors: ['#0080C6', '#FFC20E'] },

  // NFC East
  DAL: { name: 'Cowboys', colors: ['#041E42', '#869397'] },
  NYG: { name: 'Giants', colors: ['#0B2265', '#A71930'] },
  PHI: { name: 'Eagles', colors: ['#004C54', '#A5ACAF'] },
  WAS: { name: 'Commanders', colors: ['#5A1414', '#FFB612'] },

  // NFC North
  CHI: { name: 'Bears', colors: ['#0B162A', '#C83803'] },
  DET: { name: 'Lions', colors: ['#0076B6', '#B0B7BC'] },
  GB: { name: 'Packers', colors: ['#203731', '#FFB612'] },
  MIN: { name: 'Vikings', colors: ['#4F2683', '#FFC62F'] },

  // NFC South
  ATL: { name: 'Falcons', colors: ['#A71930', '#000000'] },
  CAR: { name: 'Panthers', colors: ['#0085CA', '#101820'] },
  NO: { name: 'Saints', colors: ['#D3BC8D', '#101820'] },
  TB: { name: 'Buccaneers', colors: ['#D50A0A', '#34302B'] },

  // NFC West
  ARI: { name: 'Cardinals', colors: ['#97233F', '#FFB612'] },
  LAR: { name: 'Rams', colors: ['#003594', '#FFA300'] },
  SF: { name: '49ers', colors: ['#AA0000', '#B3995D'] },
  SEA: { name: 'Seahawks', colors: ['#002244', '#69BE28'] }
};

/**
 * Generate SVG placeholder for a team
 */
function generateTeamSVG(abbr, team) {
  return `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradient-${abbr}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:${team.colors[0]};stop-opacity:1" />
      <stop offset="100%" style="stop-color:${team.colors[1]};stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="64" cy="64" r="60" fill="url(#gradient-${abbr})" stroke="#FFFFFF" stroke-width="3"/>
  <circle cx="64" cy="64" r="48" fill="none" stroke="#FFFFFF" stroke-width="1" opacity="0.3"/>
  <text x="64" y="72" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="18" font-weight="bold" style="text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">
    ${abbr}
  </text>
  <text x="64" y="88" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="8" font-weight="normal" opacity="0.8">
    ${team.name}
  </text>
</svg>`;
}

/**
 * Convert SVG to base64 data URL
 */
function svgToDataUrl(svg) {
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`;
}

/**
 * Create placeholder files
 */
function createPlaceholders() {
  const logosDir = path.join(path.dirname(__dirname), 'public', 'logos');

  // Ensure directory exists
  if (!fs.existsSync(logosDir)) {
    fs.mkdirSync(logosDir, { recursive: true });
  }

  // Generate placeholder for each team
  Object.entries(teams).forEach(([abbr, team]) => {
    const svg = generateTeamSVG(abbr, team);
    const svgPath = path.join(logosDir, `${abbr}.svg`);

    fs.writeFileSync(svgPath, svg);
    console.log(`✓ Created placeholder: ${abbr}.svg`);
  });

  // Create a generic NFL logo
  const nflSvg = `<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="nfl-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#013369;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#D50A0A;stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="64" cy="64" r="60" fill="url(#nfl-gradient)" stroke="#FFFFFF" stroke-width="3"/>
  <circle cx="64" cy="64" r="48" fill="none" stroke="#FFFFFF" stroke-width="1" opacity="0.3"/>
  <text x="64" y="72" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="16" font-weight="bold" style="text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">
    NFL
  </text>
</svg>`;

  fs.writeFileSync(path.join(logosDir, 'NFL.svg'), nflSvg);
  console.log('✓ Created NFL generic logo');

  console.log(`\n📁 All ${Object.keys(teams).length + 1} placeholder logos created in: ${logosDir}`);
  console.log('\n💡 Replace these SVG files with actual PNG logos when available');
}

// Run the script
if (import.meta.url === `file://${process.argv[1]}`) {
  createPlaceholders();
}

export { generateTeamSVG, svgToDataUrl, teams };