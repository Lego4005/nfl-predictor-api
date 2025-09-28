import React from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, Target, BarChart3, TrendingUp, 
  Flame, Shield, Zap, Award
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Avatar, AvatarFallback } from '../ui/avatar';
import type { 
  CouncilMember,
  PredictionCategoryGroup 
} from '../../types/aiCouncil';

interface HeadToHeadComparisonProps {
  expert1: CouncilMember;
  expert2: CouncilMember;
  timeRange: 'week' | 'month' | 'season' | 'all_time';
}

interface BattleRecord {
  wins: number;
  losses: number;
  ties: number;
  winPercentage: number;
}

interface CategoryDominance {
  [key: string]: {
    expert1Wins: number;
    expert2Wins: number;
    ties: number;
  };
}

const HeadToHeadComparison: React.FC<HeadToHeadComparisonProps> = ({
  expert1,
  expert2,
  timeRange
}) => {
  // Mock battle data
  const battleRecord: BattleRecord = {
    wins: Math.floor(Math.random() * 15) + 5,
    losses: Math.floor(Math.random() * 12) + 3,
    ties: Math.floor(Math.random() * 3),
    winPercentage: Math.random() * 0.4 + 0.4 // 40-80%
  };

  const categoryDominance: CategoryDominance = {
    'game_outcome': {
      expert1Wins: Math.floor(Math.random() * 8) + 2,
      expert2Wins: Math.floor(Math.random() * 6) + 1,
      ties: Math.floor(Math.random() * 2)
    },
    'betting_markets': {
      expert1Wins: Math.floor(Math.random() * 6) + 1,
      expert2Wins: Math.floor(Math.random() * 8) + 2,
      ties: Math.floor(Math.random() * 2)
    },
    'live_scenarios': {
      expert1Wins: Math.floor(Math.random() * 5) + 1,
      expert2Wins: Math.floor(Math.random() * 5) + 1,
      ties: Math.floor(Math.random() * 3)
    },
    'player_props': {
      expert1Wins: Math.floor(Math.random() * 7) + 1,
      expert2Wins: Math.floor(Math.random() * 4) + 1,
      ties: Math.floor(Math.random() * 2)
    },
    'situational_analysis': {
      expert1Wins: Math.floor(Math.random() * 4) + 1,
      expert2Wins: Math.floor(Math.random() * 6) + 2,
      ties: Math.floor(Math.random() * 2)
    }
  };

  const recentForm = {
    expert1Streak: Math.floor(Math.random() * 10) - 5, // -5 to +5
    expert2Streak: Math.floor(Math.random() * 10) - 5,
    momentum: Math.random() > 0.6 ? 'expert1' : Math.random() > 0.3 ? 'expert2' : 'neutral'
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, any> = {
      'game_outcome': Trophy,
      'betting_markets': BarChart3,
      'live_scenarios': Zap,
      'player_props': Target,
      'situational_analysis': TrendingUp
    };
    return icons[category] || Trophy;
  };

  const getCategoryDisplayName = (category: string) => {
    const names: Record<string, string> = {
      'game_outcome': 'Game Outcome',
      'betting_markets': 'Betting Markets',
      'live_scenarios': 'Live Scenarios',
      'player_props': 'Player Props',
      'situational_analysis': 'Situational Analysis'
    };
    return names[category] || category.replace('_', ' ');
  };

  const getStreakColor = (streak: number) => {
    if (streak > 3) return 'text-green-600 bg-green-100';
    if (streak > 0) return 'text-green-500 bg-green-50';
    if (streak < -3) return 'text-red-600 bg-red-100';
    if (streak < 0) return 'text-red-500 bg-red-50';
    return 'text-gray-600 bg-gray-100';
  };

  const getMomentumIcon = (momentum: string) => {
    switch (momentum) {
      case 'expert1': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'expert2': return <TrendingUp className="h-4 w-4 text-blue-500" />;
      default: return <BarChart3 className="h-4 w-4 text-gray-500" />;
    }
  };

  const getDominanceWinner = (category: string) => {
    const stats = categoryDominance[category];
    if (stats.expert1Wins > stats.expert2Wins) return 'expert1';
    if (stats.expert2Wins > stats.expert1Wins) return 'expert2';
    return 'tie';
  };

  return (
    <div className="space-y-6">
      {/* Head-to-Head Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-bold text-center">
            Battle Arena: {timeRange.replace('_', ' ').toUpperCase()}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Expert 1 */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-center"
            >
              <Avatar className="h-20 w-20 mx-auto mb-4">
                <AvatarFallback className="bg-green-100 text-green-600 text-lg">
                  {expert1.expertName.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <h3 className="text-lg font-semibold mb-2">{expert1.expertName}</h3>
              <div className="space-y-2">
                <Badge className="bg-green-100 text-green-700">
                  {(expert1.overallAccuracy * 100).toFixed(1)}% accuracy
                </Badge>
                <div className="text-sm text-gray-600">
                  Vote Weight: {(expert1.voteWeight.normalizedWeight * 100).toFixed(1)}%
                </div>
                <Badge className={getStreakColor(recentForm.expert1Streak)}>
                  {recentForm.expert1Streak > 0 ? '+' : ''}{recentForm.expert1Streak} streak
                </Badge>
              </div>
            </motion.div>

            {/* Battle Record */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="text-center"
            >
              <div className="bg-gradient-to-br from-orange-100 to-red-100 rounded-xl p-6">
                <Trophy className="h-12 w-12 text-orange-600 mx-auto mb-4" />
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {battleRecord.wins} - {battleRecord.losses} - {battleRecord.ties}
                </div>
                <div className="text-sm text-gray-600 mb-3">
                  Win Rate: {(battleRecord.winPercentage * 100).toFixed(1)}%
                </div>
                <div className="flex items-center justify-center gap-2">
                  {getMomentumIcon(recentForm.momentum)}
                  <span className="text-sm font-medium">
                    {recentForm.momentum === 'expert1' ? expert1.expertName : 
                     recentForm.momentum === 'expert2' ? expert2.expertName : 
                     'Even'} has momentum
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Expert 2 */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="text-center"
            >
              <Avatar className="h-20 w-20 mx-auto mb-4">
                <AvatarFallback className="bg-blue-100 text-blue-600 text-lg">
                  {expert2.expertName.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <h3 className="text-lg font-semibold mb-2">{expert2.expertName}</h3>
              <div className="space-y-2">
                <Badge className="bg-blue-100 text-blue-700">
                  {(expert2.overallAccuracy * 100).toFixed(1)}% accuracy
                </Badge>
                <div className="text-sm text-gray-600">
                  Vote Weight: {(expert2.voteWeight.normalizedWeight * 100).toFixed(1)}%
                </div>
                <Badge className={getStreakColor(recentForm.expert2Streak)}>
                  {recentForm.expert2Streak > 0 ? '+' : ''}{recentForm.expert2Streak} streak
                </Badge>
              </div>
            </motion.div>
          </div>
        </CardContent>
      </Card>

      {/* Category Dominance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Category Dominance
          </CardTitle>
          <p className="text-sm text-gray-600">
            Head-to-head performance across prediction categories
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(categoryDominance).map(([category, stats], index) => {
              const IconComponent = getCategoryIcon(category);
              const winner = getDominanceWinner(category);
              const total = stats.expert1Wins + stats.expert2Wins + stats.ties;
              
              return (
                <motion.div
                  key={category}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-gray-100">
                        <IconComponent className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold">{getCategoryDisplayName(category)}</h4>
                        <p className="text-sm text-gray-600">
                          {total} battles • {stats.ties} ties
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {winner === 'expert1' && (
                        <Badge className="bg-green-100 text-green-700">
                          <Crown className="h-3 w-3 mr-1" />
                          {expert1.expertName} leads
                        </Badge>
                      )}
                      {winner === 'expert2' && (
                        <Badge className="bg-blue-100 text-blue-700">
                          <Crown className="h-3 w-3 mr-1" />
                          {expert2.expertName} leads
                        </Badge>
                      )}
                      {winner === 'tie' && (
                        <Badge className="bg-gray-100 text-gray-700">
                          <Shield className="h-3 w-3 mr-1" />
                          Even
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="text-lg font-bold text-green-700">
                        {stats.expert1Wins}
                      </div>
                      <div className="text-xs text-green-600">
                        {expert1.expertName}
                      </div>
                    </div>
                    
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-lg font-bold text-gray-700">
                        {stats.ties}
                      </div>
                      <div className="text-xs text-gray-600">
                        Ties
                      </div>
                    </div>
                    
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-lg font-bold text-blue-700">
                        {stats.expert2Wins}
                      </div>
                      <div className="text-xs text-blue-600">
                        {expert2.expertName}
                      </div>
                    </div>
                  </div>

                  {/* Visual Win/Loss Bar */}
                  <div className="mt-3">
                    <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
                      <div 
                        className="bg-green-500"
                        style={{ width: `${(stats.expert1Wins / total) * 100}%` }}
                      />
                      <div 
                        className="bg-gray-400"
                        style={{ width: `${(stats.ties / total) * 100}%` }}
                      />
                      <div 
                        className="bg-blue-500"
                        style={{ width: `${(stats.expert2Wins / total) * 100}%` }}
                      />
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Performance Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Accuracy Comparison
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>{expert1.expertName}</span>
                <span className="font-semibold">
                  {(expert1.overallAccuracy * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={expert1.overallAccuracy * 100} className="h-3" />
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>{expert2.expertName}</span>
                <span className="font-semibold">
                  {(expert2.overallAccuracy * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={expert2.overallAccuracy * 100} className="h-3" />
            </div>

            <div className="pt-3 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                Accuracy Difference: {Math.abs((expert1.overallAccuracy - expert2.overallAccuracy) * 100).toFixed(1)}%
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Vote Weight Comparison
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>{expert1.expertName}</span>
                <span className="font-semibold">
                  {(expert1.voteWeight.normalizedWeight * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={expert1.voteWeight.normalizedWeight * 100} className="h-3" />
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>{expert2.expertName}</span>
                <span className="font-semibold">
                  {(expert2.voteWeight.normalizedWeight * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={expert2.voteWeight.normalizedWeight * 100} className="h-3" />
            </div>

            <div className="pt-3 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                Weight Difference: {Math.abs((expert1.voteWeight.normalizedWeight - expert2.voteWeight.normalizedWeight) * 100).toFixed(1)}%
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HeadToHeadComparison;