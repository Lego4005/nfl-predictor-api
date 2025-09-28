import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Trophy, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ArrowUp, 
  ArrowDown, 
  Crown, 
  Target,
  Zap, 
  Shield, 
  Sword
} from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';
import { useApiCache } from '@/hooks/useCache';

const PowerRankingsPage = () => {
  const [sortConfig, setSortConfig] = useState({ key: 'rank', direction: 'asc' });
  const [week, setWeek] = useState(1);

  // Use cached data instead of mock data
  const [rankings, setRankings, loading, refreshRankings] = useApiCache(
    `/rankings/2025/${week}`, 
    'rankings', 
    [
      { 
        team: 'KC', 
        rank: 1, 
        lastWeek: 1, 
        movement: 0, 
        record: '5-1', 
        elo: 1650, 
        trend: 'up',
        offensiveEPA: 0.25,
        defensiveEPA: -0.18,
        sos: 0.45
      },
      { 
        team: 'SF', 
        rank: 2, 
        lastWeek: 3, 
        movement: 1, 
        record: '4-2', 
        elo: 1625, 
        trend: 'up',
        offensiveEPA: 0.22,
        defensiveEPA: -0.15,
        sos: 0.52
      },
      { 
        team: 'BUF', 
        rank: 3, 
        lastWeek: 2, 
        movement: -1, 
        record: '4-2', 
        elo: 1615, 
        trend: 'down',
        offensiveEPA: 0.18,
        defensiveEPA: -0.20,
        sos: 0.48
      },
      { 
        team: 'DAL', 
        rank: 4, 
        lastWeek: 5, 
        movement: 1, 
        record: '5-1', 
        elo: 1590, 
        trend: 'up',
        offensiveEPA: 0.20,
        defensiveEPA: -0.12,
        sos: 0.42
      },
      { 
        team: 'PHI', 
        rank: 5, 
        lastWeek: 4, 
        movement: -1, 
        record: '4-2', 
        elo: 1585, 
        trend: 'down',
        offensiveEPA: 0.19,
        defensiveEPA: -0.14,
        sos: 0.50
      },
      { 
        team: 'BAL', 
        rank: 6, 
        lastWeek: 7, 
        movement: 1, 
        record: '3-3', 
        elo: 1570, 
        trend: 'up',
        offensiveEPA: 0.15,
        defensiveEPA: -0.22,
        sos: 0.55
      },
      { 
        team: 'MIA', 
        rank: 7, 
        lastWeek: 6, 
        movement: -1, 
        record: '2-4', 
        elo: 1560, 
        trend: 'down',
        offensiveEPA: 0.17,
        defensiveEPA: -0.10,
        sos: 0.38
      },
      { 
        team: 'DET', 
        rank: 8, 
        lastWeek: 10, 
        movement: 2, 
        record: '5-1', 
        elo: 1545, 
        trend: 'up',
        offensiveEPA: 0.21,
        defensiveEPA: -0.13,
        sos: 0.44
      },
      { 
        team: 'CIN', 
        rank: 9, 
        lastWeek: 8, 
        movement: -1, 
        record: '3-3', 
        elo: 1530, 
        trend: 'down',
        offensiveEPA: 0.16,
        defensiveEPA: -0.16,
        sos: 0.47
      },
      { 
        team: 'JAX', 
        rank: 10, 
        lastWeek: 9, 
        movement: -1, 
        record: '2-4', 
        elo: 1520, 
        trend: 'steady',
        offensiveEPA: 0.14,
        defensiveEPA: -0.19,
        sos: 0.53
      }
    ]
  );

  const getMovementIcon = (movement) => {
    if (movement > 0) return <ArrowUp className="w-3 h-3 text-green-500" />;
    if (movement < 0) return <ArrowDown className="w-3 h-3 text-red-500" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  const getMovementColor = (movement) => {
    if (movement > 0) return 'text-green-400';
    if (movement < 0) return 'text-red-400';
    return 'text-gray-500';
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp className="w-3 h-3 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-3 h-3 text-red-500" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  const getEPAColor = (epa) => {
    if (epa > 0.2) return 'text-green-400';
    if (epa > 0.1) return 'text-blue-400';
    if (epa > 0) return 'text-yellow-400';
    return 'text-red-400';
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedRankings = [...rankings].sort((a, b) => {
    if (sortConfig.key === 'rank') {
      return sortConfig.direction === 'asc' ? a.rank - b.rank : b.rank - a.rank;
    }
    if (sortConfig.key === 'elo') {
      return sortConfig.direction === 'asc' ? a.elo - b.elo : b.elo - a.elo;
    }
    if (sortConfig.key === 'offensiveEPA') {
      return sortConfig.direction === 'asc' ? a.offensiveEPA - b.offensiveEPA : b.offensiveEPA - a.offensiveEPA;
    }
    if (sortConfig.key === 'defensiveEPA') {
      return sortConfig.direction === 'asc' ? a.defensiveEPA - b.defensiveEPA : b.defensiveEPA - a.defensiveEPA;
    }
    if (sortConfig.key === 'sos') {
      return sortConfig.direction === 'asc' ? a.sos - b.sos : b.sos - a.sos;
    }
    return a.rank - b.rank;
  });

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <span className="opacity-0">↕</span>; // Invisible placeholder
    }
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold dashboard-text">
              NFL Power Rankings
            </h1>
            <p className="dashboard-muted">
              Team rankings with EPA metrics and strength of schedule adjustments
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="dashboard-muted">Week:</span>
              <select 
                value={week} 
                onChange={(e) => setWeek(parseInt(e.target.value))}
                className="bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded-lg px-3 py-1 dashboard-text"
              >
                {[...Array(18)].map((_, i) => (
                  <option key={i + 1} value={i + 1} className="dashboard-bg">
                    {i + 1}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-[hsl(var(--dashboard-surface))] border-gray-700 text-xs dashboard-text">
                Week {week}
              </Badge>
              <Badge variant="outline" className="bg-[hsl(var(--dashboard-surface))] border-gray-700 text-xs dashboard-text">
                SOS Adjusted
              </Badge>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <Card className="dashboard-card">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-400" />
                <CardTitle className="dashboard-text">Power Rankings</CardTitle>
              </div>
              <div className="text-sm dashboard-muted">
                Sorted by Rank
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Table Header */}
            <div className="hidden md:grid grid-cols-12 gap-4 px-4 py-3 bg-[hsl(var(--dashboard-surface))] rounded-lg text-sm font-semibold dashboard-text border-b border-gray-700">
              <div 
                className="col-span-2 flex items-center gap-2 cursor-pointer hover:text-blue-400"
                onClick={() => handleSort('rank')}
              >
                <span>Rank</span>
                <span>{getSortIcon('rank')}</span>
              </div>
              <div className="col-span-2">Team</div>
              <div 
                className="col-span-2 flex items-center gap-2 cursor-pointer hover:text-blue-400"
                onClick={() => handleSort('elo')}
              >
                <span>ELO</span>
                <span>{getSortIcon('elo')}</span>
              </div>
              <div 
                className="col-span-2 flex items-center gap-2 cursor-pointer hover:text-blue-400"
                onClick={() => handleSort('offensiveEPA')}
              >
                <span>Off EPA</span>
                <span>{getSortIcon('offensiveEPA')}</span>
              </div>
              <div 
                className="col-span-2 flex items-center gap-2 cursor-pointer hover:text-blue-400"
                onClick={() => handleSort('defensiveEPA')}
              >
                <span>Def EPA</span>
                <span>{getSortIcon('defensiveEPA')}</span>
              </div>
              <div 
                className="col-span-2 flex items-center gap-2 cursor-pointer hover:text-blue-400"
                onClick={() => handleSort('sos')}
              >
                <span>SOS</span>
                <span>{getSortIcon('sos')}</span>
              </div>
            </div>

            {/* Table Body */}
            <div className="space-y-3 mt-4">
              {sortedRankings.map((team, index) => (
                <motion.div
                  key={team.team}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className={`flex flex-col md:grid md:grid-cols-12 gap-4 items-center p-4 rounded-lg ${
                    team.rank === 1 ? 'bg-gradient-to-r from-yellow-900/20 to-orange-900/20' : 'bg-[hsl(var(--dashboard-surface))]'
                  } border border-gray-700`}>
                    {/* Mobile View */}
                    <div className="md:hidden w-full">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2 min-w-[60px]">
                            <div className="text-lg font-bold w-6 text-center dashboard-text">
                              {team.rank}
                            </div>
                            <div className="flex flex-col items-center">
                              {getMovementIcon(team.movement)}
                              {team.movement !== 0 && (
                                <span className={`text-xs ${getMovementColor(team.movement)}`}>
                                  {Math.abs(team.movement)}
                                </span>
                              )}
                            </div>
                          </div>
                          <TeamLogo
                            teamAbbr={team.team}
                            size="medium"
                            className="w-10 h-10"
                          />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold dashboard-text">{team.team}</span>
                              {team.rank === 1 && <Crown className="w-4 h-4 text-yellow-400" />}
                            </div>
                            <div className="text-sm dashboard-muted">{team.record}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold dashboard-text">{Math.round(team.elo)} ELO</div>
                          <div className="flex items-center gap-1 justify-end">
                            {getTrendIcon(team.trend)}
                            <span className="text-xs dashboard-muted">Trend</span>
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-4 gap-2">
                        <div className="text-center p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <div className={`text-sm font-semibold ${getEPAColor(team.offensiveEPA)}`}>
                            +{team.offensiveEPA.toFixed(2)}
                          </div>
                          <div className="text-xs dashboard-muted">Off EPA</div>
                        </div>
                        <div className="text-center p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <div className={`text-sm font-semibold ${getEPAColor(-team.defensiveEPA)}`}>
                            {team.defensiveEPA.toFixed(2)}
                          </div>
                          <div className="text-xs dashboard-muted">Def EPA</div>
                        </div>
                        <div className="text-center p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <div className="text-sm font-semibold dashboard-text">
                            {(team.sos * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs dashboard-muted">SOS</div>
                        </div>
                        <div className="text-center p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <div className="text-sm font-semibold dashboard-text">
                            {team.record}
                          </div>
                          <div className="text-xs dashboard-muted">Record</div>
                        </div>
                      </div>
                    </div>

                    {/* Desktop View */}
                    <div className="hidden md:contents">
                      {/* Rank */}
                      <div className="col-span-2 flex items-center gap-3">
                        <div className="flex items-center gap-2 min-w-[60px]">
                          <div className="text-lg font-bold w-6 text-center dashboard-text">
                            {team.rank}
                          </div>
                          <div className="flex flex-col items-center">
                            {getMovementIcon(team.movement)}
                            {team.movement !== 0 && (
                              <span className={`text-xs ${getMovementColor(team.movement)}`}>
                                {Math.abs(team.movement)}
                              </span>
                            )}
                          </div>
                        </div>
                        <TeamLogo
                          teamAbbr={team.team}
                          size="medium"
                          className="w-10 h-10"
                        />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold dashboard-text">{team.team}</span>
                            {team.rank === 1 && <Crown className="w-4 h-4 text-yellow-400" />}
                          </div>
                          <div className="text-sm dashboard-muted">{team.record}</div>
                        </div>
                      </div>

                      {/* ELO */}
                      <div className="col-span-2">
                        <div className="text-sm font-semibold dashboard-text">{Math.round(team.elo)}</div>
                      </div>

                      {/* Offensive EPA */}
                      <div className="col-span-2">
                        <div className={`text-sm font-semibold ${getEPAColor(team.offensiveEPA)}`}>
                          +{team.offensiveEPA.toFixed(2)}
                        </div>
                      </div>

                      {/* Defensive EPA */}
                      <div className="col-span-2">
                        <div className={`text-sm font-semibold ${getEPAColor(-team.defensiveEPA)}`}>
                          {team.defensiveEPA.toFixed(2)}
                        </div>
                      </div>

                      {/* SOS */}
                      <div className="col-span-2">
                        <div className="text-sm font-semibold dashboard-text">
                          {(team.sos * 100).toFixed(0)}%
                        </div>
                      </div>

                      {/* Trend */}
                      <div className="col-span-2">
                        <div className="flex items-center gap-1">
                          {getTrendIcon(team.trend)}
                          <span className="text-xs dashboard-muted capitalize">{team.trend}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Footer Stats */}
            <div className="mt-6 p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-xs dashboard-muted mb-1">Biggest Rise</div>
                  <div className="font-semibold text-green-400 flex items-center justify-center gap-1">
                    <ArrowUp className="w-4 h-4" />
                    DET +2
                  </div>
                </div>
                <div>
                  <div className="text-xs dashboard-muted mb-1">Biggest Fall</div>
                  <div className="font-semibold text-red-400 flex items-center justify-center gap-1">
                    <ArrowDown className="w-4 h-4" />
                    BUF -1
                  </div>
                </div>
                <div>
                  <div className="text-xs dashboard-muted mb-1">Highest ELO</div>
                  <div className="font-semibold text-yellow-400 flex items-center justify-center gap-1">
                    <Zap className="w-4 h-4" />
                    KC 1650
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* EPA Statistics Explanation */}
        <Card className="dashboard-card mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 dashboard-text">
              <Target className="w-5 h-5" />
              EPA Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-900/20 rounded-lg">
                <h4 className="font-semibold mb-2 dashboard-text">Expected Points Added (EPA)</h4>
                <p className="text-sm dashboard-muted">
                  Measures the expected points contributed by each play. Positive values indicate plays that improved the team's position.
                </p>
              </div>
              <div className="p-4 bg-green-900/20 rounded-lg">
                <h4 className="font-semibold mb-2 dashboard-text">Offensive EPA</h4>
                <p className="text-sm dashboard-muted">
                  Average EPA per play for the offense. Higher values indicate more effective offensive performance.
                </p>
              </div>
              <div className="p-4 bg-red-900/20 rounded-lg">
                <h4 className="font-semibold mb-2 dashboard-text">Defensive EPA</h4>
                <p className="text-sm dashboard-muted">
                  Average EPA per play against the defense. Lower (more negative) values indicate stronger defensive performance.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PowerRankingsPage;