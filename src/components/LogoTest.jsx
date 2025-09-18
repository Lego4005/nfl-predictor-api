import React from 'react';
import TeamLogo from './TeamLogo';
import { getTeam } from '../data/nflTeams';

/**
 * Simple test component to verify logo system
 */
const LogoTest = () => {
  const testTeams = ['KC', 'BUF', 'SF', 'DAL', 'GB', 'NE'];

  return (
    <div className="p-8 bg-gray-100 dark:bg-gray-900">
      <h2 className="text-2xl font-bold mb-6">NFL Team Logo Test</h2>

      <div className="grid grid-cols-3 md:grid-cols-6 gap-6 mb-8">
        {testTeams.map((teamAbbr) => {
          const team = getTeam(teamAbbr);
          return (
            <div key={teamAbbr} className="text-center">
              <TeamLogo
                teamAbbr={teamAbbr}
                size="large"
                showGlow={true}
                animated={true}
                style={{
                  '--team-primary': team?.primaryColor,
                  '--team-secondary': team?.secondaryColor
                }}
              />
              <p className="mt-2 text-sm font-medium">{teamAbbr}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {team?.city} {team?.name}
              </p>
            </div>
          );
        })}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Logo System Features:</h3>
        <ul className="space-y-2 text-sm">
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Local SVG logos with team colors (primary fallback)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            ESPN CDN logos as secondary fallback
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
            Generated SVG placeholders as final fallback
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
            Animation and glow effects support
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 bg-pink-500 rounded-full"></span>
            Responsive sizing (small, medium, large, xlarge)
          </li>
        </ul>
      </div>
    </div>
  );
};

export default LogoTest;