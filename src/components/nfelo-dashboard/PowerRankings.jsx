import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Trophy, TrendingUp, TrendingDown, Minus,
  ArrowUp, ArrowDown, Crown, Target,
  Zap, Shield, Sword
} from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';

const PowerRankings = () => {
  // Mock power rankings data
  const rankings = [
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
  ];

  const getMovementIcon = (movement) => {
    if (movement > 0) return <ArrowUp className="w-3 h-3 text-green-500" />;
    if (movement < 0) return <ArrowDown className="w-3 h-3 text-red-500" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  const getMovementColor = (movement) => {
    if (movement > 0) return 'text-green-600 dark:text-green-400';
    if (movement < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-500';
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp className="w-3 h-3 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-3 h-3 text-red-500" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  const getEPAColor = (epa) => {
    if (epa > 0.2) return 'text-green-600 dark:text-green-400';
    if (epa > 0.1) return 'text-blue-600 dark:text-blue-400';
    if (epa > 0) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-500" />
              <CardTitle>Power Rankings</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">Week 6</Badge>
              <Badge variant="outline" className="text-xs">
                SOS Adjusted
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {rankings.map((team, index) => (
              <motion.div
                key={team.team}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <div className={`flex items-center justify-between p-4 rounded-lg hover:bg-muted/50 transition-all duration-200 ${
                  team.rank === 1 ? 'bg-gradient-to-r from-yellow-500/10 to-orange-500/10 dark:from-yellow-500/20 dark:to-orange-500/20' : 'bg-white dark:bg-gray-800'
                } border border-gray-200 dark:border-gray-700`}>
                  <div className="flex items-center gap-4">
                    {/* Rank */}
                    <div className="flex items-center gap-2 min-w-[60px]">
                      <div className="text-lg font-bold w-6 text-center">
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

                    {/* Team Info */}
                    <div className="flex items-center gap-3">
                      <TeamLogo
                        teamAbbr={team.team}
                        size="medium"
                        className="w-10 h-10"
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{team.team}</span>
                          {team.rank === 1 && <Crown className="w-4 h-4 text-yellow-500" />}
                        </div>
                        <div className="text-sm text-muted-foreground">{team.record}</div>
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="hidden md:grid grid-cols-4 gap-6">
                    {/* ELO */}
                    <div className="text-right">
                      <div className="text-sm font-semibold">{Math.round(team.elo)}</div>
                      <div className="text-xs text-muted-foreground">ELO</div>
                    </div>

                    {/* Offensive EPA */}
                    <div className="text-right">
                      <div className={`text-sm font-semibold ${getEPAColor(team.offensiveEPA)}`}>
                        +{team.offensiveEPA.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center justify-end gap-1">
                        <Sword className="w-3 h-3" />
                        Off EPA
                      </div>
                    </div>

                    {/* Defensive EPA */}
                    <div className="text-right">
                      <div className={`text-sm font-semibold ${getEPAColor(-team.defensiveEPA)}`}>
                        {team.defensiveEPA.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center justify-end gap-1">
                        <Shield className="w-3 h-3" />
                        Def EPA
                      </div>
                    </div>

                    {/* SOS */}
                    <div className="text-right">
                      <div className="text-sm font-semibold">
                        {(team.sos * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-muted-foreground">SOS</div>
                    </div>
                  </div>

                  {/* Mobile Stats */}
                  <div className="md:hidden text-right">
                    <div className="text-sm font-semibold">{Math.round(team.elo)} ELO</div>
                    <div className="flex items-center gap-1 justify-end">
                      {getTrendIcon(team.trend)}
                      <span className="text-xs text-muted-foreground">Trend</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Footer Stats */}
          <div className="mt-6 p-4 bg-muted dark:bg-gray-900 rounded-lg">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xs text-muted-foreground mb-1">Biggest Rise</div>
                <div className="font-semibold text-green-600 dark:text-green-400 flex items-center justify-center gap-1">
                  <ArrowUp className="w-4 h-4" />
                  DET +2
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Biggest Fall</div>
                <div className="font-semibold text-red-600 dark:text-red-400 flex items-center justify-center gap-1">
                  <ArrowDown className="w-4 h-4" />
                  BUF -1
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Highest ELO</div>
                <div className="font-semibold text-yellow-600 dark:text-yellow-400 flex items-center justify-center gap-1">
                  <Zap className="w-4 h-4" />
                  KC 1650
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* EPA Statistics Explanation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            EPA Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 className="font-semibold mb-2">Expected Points Added (EPA)</h4>
              <p className="text-sm text-muted-foreground">
                Measures the expected points contributed by each play. Positive values indicate plays that improved the team's position.
              </p>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h4 className="font-semibold mb-2">Offensive EPA</h4>
              <p className="text-sm text-muted-foreground">
                Average EPA per play for the offense. Higher values indicate more effective offensive performance.
              </p>
            </div>
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <h4 className="font-semibold mb-2">Defensive EPA</h4>
              <p className="text-sm text-muted-foreground">
                Average EPA per play against the defense. Lower (more negative) values indicate stronger defensive performance.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PowerRankings;