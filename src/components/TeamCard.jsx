import React from 'react';
import { motion } from 'framer-motion';
import { getTeam } from '../data/nflTeams';
import { TrendingUp, TrendingDown, Users, Trophy, Activity } from 'lucide-react';
import TeamLogo from './TeamLogo';

const TeamCard = ({ teamAbbr, stats, isHome = false, score, isLive = false }) => {
  const team = getTeam(teamAbbr);

  if (!team) return null;

  return (
    <motion.div
      className="relative overflow-hidden rounded-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      {/* Gradient Background */}
      <div
        className="absolute inset-0 opacity-20 dark:opacity-10"
        style={{ background: team.gradient }}
      />

      {/* Glass Effect Overlay */}
      <div className="relative backdrop-blur-sm bg-white/80 dark:bg-gray-900/80 border border-white/20 dark:border-gray-700/50 p-3">
        {/* Team Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {/* Team Logo with Glow Effect */}
            <TeamLogo
              teamAbbr={teamAbbr}
              size="medium"
              showGlow={true}
              animated={true}
              style={{
                '--team-primary': team.primaryColor,
                '--team-secondary': team.secondaryColor
              }}
            />

            {/* Team Info */}
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2">
                {team.city}
                {isHome && (
                  <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-600 dark:text-green-400 rounded-full">
                    HOME
                  </span>
                )}
              </h3>
              <p className="text-2xl font-black" style={{ color: team.primaryColor }}>
                {team.name}
              </p>
            </div>
          </div>

          {/* Live Score */}
          {score !== undefined && (
            <div className="text-right">
              <div className="text-3xl font-black">{score}</div>
              {isLive && (
                <div className="flex items-center gap-1 text-xs text-red-500">
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  LIVE
                </div>
              )}
            </div>
          )}
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-3 gap-2 mt-4">
            <StatCard
              icon={Trophy}
              label="Record"
              value={`${stats.wins}-${stats.losses}`}
              trend={stats.streak}
              color={team.primaryColor}
            />
            <StatCard
              icon={Activity}
              label="Offense"
              value={`${stats.offenseRank}th`}
              trend={stats.offenseTrend}
              color={team.primaryColor}
            />
            <StatCard
              icon={Users}
              label="Defense"
              value={`${stats.defenseRank}th`}
              trend={stats.defenseTrend}
              color={team.primaryColor}
            />
          </div>
        )}

        {/* Team Colors Bar */}
        <div className="flex h-1 mt-4 rounded-full overflow-hidden">
          <div className="flex-1" style={{ backgroundColor: team.primaryColor }} />
          <div className="flex-1" style={{ backgroundColor: team.secondaryColor }} />
          {team.tertiaryColor && (
            <div className="flex-1" style={{ backgroundColor: team.tertiaryColor }} />
          )}
        </div>
      </div>
    </motion.div>
  );
};

const StatCard = ({ icon: Icon, label, value, trend, color }) => {
  const isPositive = trend > 0;

  return (
    <div className="bg-gray-50/50 dark:bg-gray-800/50 rounded-lg p-2">
      <div className="flex items-center justify-between mb-1">
        <Icon className="w-3 h-3 opacity-60" />
        {trend !== undefined && (
          <div className={`flex items-center ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          </div>
        )}
      </div>
      <div className="text-xs text-gray-600 dark:text-gray-400">{label}</div>
      <div className="font-bold" style={{ color: color }}>{value}</div>
    </div>
  );
};

export default TeamCard;