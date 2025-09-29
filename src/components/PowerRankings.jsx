import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getTeam } from '../data/nflTeams';
import TeamLogo from "./TeamLogo";
import {
  Trophy, TrendingUp, TrendingDown, Minus,
  ArrowUp, ArrowDown, Crown, Target
} from 'lucide-react';

const PowerRankings = ({ analytics }) => {
  // Generate mock power rankings with movement
  const generateRankings = () => {
    if (!analytics || analytics.length === 0) {
      // Fallback mock data if no analytics
      return [
        { team: 'Chiefs', rank: 1, lastWeek: 1, movement: 0, record: '11-2', elo: 1650, trend: 'up' },
        { team: 'Eagles', rank: 2, lastWeek: 3, movement: 1, record: '10-3', elo: 1625, trend: 'up' },
        { team: 'Bills', rank: 3, lastWeek: 2, movement: -1, record: '10-3', elo: 1615, trend: 'down' },
        { team: '49ers', rank: 4, lastWeek: 5, movement: 1, record: '9-4', elo: 1590, trend: 'up' },
        { team: 'Cowboys', rank: 5, lastWeek: 4, movement: -1, record: '9-4', elo: 1585, trend: 'down' },
        { team: 'Ravens', rank: 6, lastWeek: 7, movement: 1, record: '9-4', elo: 1570, trend: 'up' },
        { team: 'Dolphins', rank: 7, lastWeek: 6, movement: -1, record: '8-5', elo: 1560, trend: 'down' },
        { team: 'Lions', rank: 8, lastWeek: 10, movement: 2, record: '8-5', elo: 1545, trend: 'up' },
        { team: 'Bengals', rank: 9, lastWeek: 8, movement: -1, record: '7-6', elo: 1530, trend: 'down' },
        { team: 'Jaguars', rank: 10, lastWeek: 9, movement: -1, record: '7-6', elo: 1520, trend: 'steady' }
      ];
    }

    // Sort by ELO and add rankings
    const sorted = [...analytics]
      .sort((a, b) => (b.elo || 1500) - (a.elo || 1500))
      .slice(0, 10)
      .map((team, index) => ({
        team: team.team,
        rank: index + 1,
        lastWeek: index + 1 + Math.floor(Math.random() * 3 - 1), // Mock last week
        movement: 0,
        record: `${team.wins || Math.floor(Math.random() * 10 + 3)}-${team.losses || Math.floor(Math.random() * 5)}`,
        elo: team.elo || 1500 + Math.random() * 200,
        trend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'steady',
        strengthOfSchedule: Math.random() * 0.3 + 0.35, // 0.35 to 0.65
        remainingStrength: Math.random() * 0.3 + 0.35
      }));

    // Calculate movement
    sorted.forEach(team => {
      team.movement = team.lastWeek - team.rank;
    });

    return sorted;
  };

  const rankings = generateRankings();

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

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            <h2 className="text-xl font-bold">Power Rankings</h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">Week 14</Badge>
            <Badge variant="outline" className="text-xs">
              SOS Adjusted
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {rankings.map((team, index) => {
            const teamData = getTeam(team.team);
            return (
              <motion.div
                key={team.team}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <div
                  className={`flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-all duration-200 ${
                    team.rank === 1
                      ? "bg-gradient-to-r from-yellow-500/10 to-orange-500/10"
                      : ""
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {/* Rank */}
                    <div className="flex items-center gap-2 min-w-[60px]">
                      <div className="text-lg font-bold w-6 text-center">
                        {team.rank}
                      </div>
                      <div className="flex flex-col items-center">
                        {getMovementIcon(team.movement)}
                        {team.movement !== 0 && (
                          <span
                            className={`text-xs ${getMovementColor(team.movement)}`}
                          >
                            {Math.abs(team.movement)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Team Info */}
                    <div className="flex items-center gap-3">
                      {teamData && (
                        <TeamLogo
                          teamAbbr={team.team}
                          size="medium"
                          className=""
                        />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{team.team}</span>
                          {team.rank === 1 && (
                            <Crown className="w-4 h-4 text-yellow-500" />
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {team.record}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4">
                    {/* ELO */}
                    <div className="text-right">
                      <div className="text-sm font-semibold">
                        {Math.round(team.elo)}
                      </div>
                      <div className="text-xs text-muted-foreground">ELO</div>
                    </div>

                    {/* SOS */}
                    <div className="text-right">
                      <div className="text-sm font-semibold">
                        {(team.strengthOfSchedule * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-muted-foreground">SOS</div>
                    </div>

                    {/* Trend */}
                    <div className="flex items-center gap-1">
                      {getTrendIcon(team.trend)}
                      <span className="text-xs text-muted-foreground">
                        Trend
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Footer Stats */}
        <div className="mt-4 p-3 bg-muted rounded-lg">
          <div className="grid grid-cols-3 gap-4 text-center text-sm">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Biggest Rise</div>
              <div className="font-semibold text-green-600 dark:text-green-400">
                Lions +2
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Biggest Fall</div>
              <div className="font-semibold text-red-600 dark:text-red-400">
                Bills -1
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">New Entry</div>
              <div className="font-semibold text-blue-600 dark:text-blue-400">
                Jaguars #10
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PowerRankings;