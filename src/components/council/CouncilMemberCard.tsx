import React from 'react';
import { motion } from 'framer-motion';
import { 
  User, TrendingUp, TrendingDown, Minus, 
  Star, Award, Target, Brain, Shield 
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Avatar, AvatarImage, AvatarFallback } from '../ui/avatar';
import type { CouncilMemberCardProps } from '../../types/aiCouncil';

const CouncilMemberCard: React.FC<CouncilMemberCardProps> = ({
  member,
  isSelected,
  onSelect,
  showDetailedMetrics
}) => {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'declining':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'declining':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getWeightColor = (weight: number) => {
    if (weight >= 0.8) return 'bg-gradient-to-r from-purple-500 to-purple-600';
    if (weight >= 0.6) return 'bg-gradient-to-r from-blue-500 to-blue-600';
    if (weight >= 0.4) return 'bg-gradient-to-r from-green-500 to-green-600';
    if (weight >= 0.2) return 'bg-gradient-to-r from-yellow-500 to-yellow-600';
    return 'bg-gradient-to-r from-gray-400 to-gray-500';
  };

  const getSpecializationBadgeColor = (specialization: string) => {
    const colors: Record<string, string> = {
      'game_outcome': 'bg-blue-100 text-blue-800',
      'betting_markets': 'bg-green-100 text-green-800',
      'player_props': 'bg-purple-100 text-purple-800',
      'live_scenarios': 'bg-red-100 text-red-800',
      'situational_analysis': 'bg-yellow-100 text-yellow-800',
      'default': 'bg-gray-100 text-gray-800'
    };
    return colors[specialization] || colors.default;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      onClick={() => onSelect(member.expertId)}
      className="cursor-pointer"
    >
      <Card 
        className={`
          relative overflow-hidden transition-all duration-300
          ${isSelected 
            ? 'ring-2 ring-blue-500 shadow-lg border-blue-300' 
            : 'hover:shadow-md border-gray-200 dark:border-gray-700'
          }
          ${member.recentTrend === 'improving' ? 'bg-gradient-to-br from-green-50 to-green-100' : ''}
          ${member.recentTrend === 'declining' ? 'bg-gradient-to-br from-red-50 to-red-100' : ''}
        `}
      >
        {/* Selection Indicator */}
        {isSelected && (
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
        )}

        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="h-12 w-12">
                <AvatarImage src={`/avatars/${member.expertId}.png`} />
                <AvatarFallback className="bg-blue-100 text-blue-600 font-semibold">
                  {member.expertName.split(' ').map(n => n[0]).join('').toUpperCase()}
                </AvatarFallback>
              </Avatar>
              
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
                  {member.expertName}
                </h3>
                <div className="flex items-center gap-1 mt-1">
                  {getTrendIcon(member.recentTrend)}
                  <span className="text-xs text-gray-600 dark:text-gray-300 capitalize">
                    {member.recentTrend}
                  </span>
                </div>
              </div>
            </div>

            {/* Performance Badge */}
            <Badge variant="outline" className={getTrendColor(member.recentTrend)}>
              {(member.overallAccuracy * 100).toFixed(1)}%
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Vote Weight Visualization */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                Vote Weight
              </span>
              <span className="text-xs font-bold text-gray-900 dark:text-white">
                {(member.voteWeight.normalizedWeight * 100).toFixed(1)}%
              </span>
            </div>
            
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${member.voteWeight.normalizedWeight * 100}%` }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                className={`h-2.5 rounded-full ${getWeightColor(member.voteWeight.normalizedWeight)}`}
              />
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="flex items-center gap-1">
              <Target className="h-3 w-3 text-green-500" />
              <span className="text-gray-600 dark:text-gray-300">Accuracy:</span>
              <span className="font-semibold">{(member.overallAccuracy * 100).toFixed(1)}%</span>
            </div>
            
            <div className="flex items-center gap-1">
              <Brain className="h-3 w-3 text-blue-500" />
              <span className="text-gray-600 dark:text-gray-300">Votes:</span>
              <span className="font-semibold">{member.totalVotes}</span>
            </div>
            
            <div className="flex items-center gap-1">
              <Shield className="h-3 w-3 text-purple-500" />
              <span className="text-gray-600 dark:text-gray-300">Alignment:</span>
              <span className="font-semibold">{(member.consensusAlignment * 100).toFixed(0)}%</span>
            </div>
            
            <div className="flex items-center gap-1">
              <Star className="h-3 w-3 text-yellow-500" />
              <span className="text-gray-600 dark:text-gray-300">Since:</span>
              <span className="font-semibold">
                {new Date(member.joinDate).getFullYear()}
              </span>
            </div>
          </div>

          {/* Specializations */}
          <div className="space-y-2">
            <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Specializations
            </span>
            <div className="flex flex-wrap gap-1">
              {member.specialization.slice(0, 2).map((spec, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className={`text-xs py-0.5 px-2 ${getSpecializationBadgeColor(spec)}`}
                >
                  {spec.replace('_', ' ')}
                </Badge>
              ))}
              {member.specialization.length > 2 && (
                <Badge variant="outline" className="text-xs py-0.5 px-2">
                  +{member.specialization.length - 2}
                </Badge>
              )}
            </div>
          </div>

          {/* Detailed Metrics (conditional) */}
          {showDetailedMetrics && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.3 }}
              className="space-y-3 pt-3 border-t border-gray-200 dark:border-gray-700"
            >
              {/* Vote Weight Components */}
              <div className="space-y-2">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                  Weight Breakdown
                </span>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Accuracy</span>
                    <span>{(member.voteWeight.accuracyComponent * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Recent</span>
                    <span>{(member.voteWeight.recentPerformanceComponent * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Confidence</span>
                    <span>{(member.voteWeight.confidenceComponent * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Recent Predictions Count */}
              <div className="flex justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-300">Recent Predictions</span>
                <span className="font-semibold">{member.predictions.length}</span>
              </div>
            </motion.div>
          )}
        </CardContent>

        {/* Hover Effect Overlay */}
        {!isSelected && (
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 to-purple-500/0 hover:from-blue-500/5 hover:to-purple-500/5 transition-all duration-300 pointer-events-none" />
        )}
      </Card>
    </motion.div>
  );
};

export default CouncilMemberCard;