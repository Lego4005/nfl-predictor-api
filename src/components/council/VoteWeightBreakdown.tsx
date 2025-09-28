import React from 'react';
import { motion } from 'framer-motion';
import { 
  Target, TrendingUp, Brain, Clock, Star, 
  BarChart3, Info, Award 
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import type { VoteWeightBreakdownProps } from '../../types/aiCouncil';

const VoteWeightBreakdown: React.FC<VoteWeightBreakdownProps> = ({
  voteWeight,
  showComponents = true,
  animated = true
}) => {
  const components = [
    {
      name: 'Accuracy',
      value: voteWeight.accuracyComponent,
      icon: Target,
      color: 'from-green-400 to-green-600',
      bgColor: 'bg-green-100',
      textColor: 'text-green-700',
      description: 'Historical prediction accuracy across all categories',
      weight: 35 // Percentage of total weight
    },
    {
      name: 'Recent Performance',
      value: voteWeight.recentPerformanceComponent,
      icon: TrendingUp,
      color: 'from-blue-400 to-blue-600',
      bgColor: 'bg-blue-100',
      textColor: 'text-blue-700',
      description: 'Performance in the last 30 days',
      weight: 25
    },
    {
      name: 'Consistency',
      value: voteWeight.confidenceComponent,
      icon: BarChart3,
      color: 'from-purple-400 to-purple-600',
      bgColor: 'bg-purple-100',
      textColor: 'text-purple-700',
      description: 'Reliability and consistency of predictions',
      weight: 20
    },
    {
      name: 'Council Tenure',
      value: voteWeight.councilTenureComponent,
      icon: Clock,
      color: 'from-amber-400 to-amber-600',
      bgColor: 'bg-amber-100',
      textColor: 'text-amber-700',
      description: 'Length of participation in the AI council',
      weight: 10
    },
    {
      name: 'Specialization',
      value: voteWeight.councilTenureComponent, // Using tenure as placeholder for specialization
      icon: Star,
      color: 'from-pink-400 to-pink-600',
      bgColor: 'bg-pink-100',
      textColor: 'text-pink-700',
      description: 'Expertise in specific prediction categories',
      weight: 10
    }
  ];

  // Get expert name from expertId (would typically come from a lookup)
  const expertName = voteWeight.expertId.replace(/[_-]/g, ' ').split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

  const getWeightTier = (weight: number) => {
    if (weight >= 0.8) return { tier: 'Elite', color: 'text-purple-600', bgColor: 'bg-purple-100' };
    if (weight >= 0.6) return { tier: 'High', color: 'text-blue-600', bgColor: 'bg-blue-100' };
    if (weight >= 0.4) return { tier: 'Medium', color: 'text-green-600', bgColor: 'bg-green-100' };
    if (weight >= 0.2) return { tier: 'Low', color: 'text-yellow-600', bgColor: 'bg-yellow-100' };
    return { tier: 'Minimal', color: 'text-gray-600', bgColor: 'bg-gray-100' };
  };

  const weightTier = getWeightTier(voteWeight.normalizedWeight);

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Award className="h-5 w-5 text-blue-500" />
            Vote Weight Analysis
          </CardTitle>
          <Badge 
            variant="outline" 
            className={`${weightTier.color} ${weightTier.bgColor} border-0`}
          >
            {weightTier.tier} Influence
          </Badge>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-300">
            {expertName}
          </span>
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(voteWeight.normalizedWeight * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">
              Overall Weight
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Weight Visualization */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Voting Influence
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {(voteWeight.overallWeight * 100).toFixed(1)}% (raw)
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <motion.div
              initial={animated ? { width: 0 } : false}
              animate={{ width: `${voteWeight.normalizedWeight * 100}%` }}
              transition={{ duration: animated ? 1.5 : 0, ease: "easeOut" }}
              className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
            />
          </div>
        </div>

        {/* Component Breakdown */}
        {showComponents && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Weight Components
              </span>
            </div>

            <div className="grid gap-4">
              {components.map((component, index) => {
                const IconComponent = component.icon;
                
                return (
                  <TooltipProvider key={component.name}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <motion.div
                          initial={animated ? { opacity: 0, x: -20 } : false}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ 
                            duration: animated ? 0.5 : 0, 
                            delay: animated ? index * 0.1 : 0 
                          }}
                          className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-help"
                        >
                          <div className={`p-2 rounded-lg ${component.bgColor}`}>
                            <IconComponent className={`h-4 w-4 ${component.textColor}`} />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {component.name}
                              </span>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500">
                                  {component.weight}% weight
                                </span>
                                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                                  {(component.value * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                            
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <motion.div
                                initial={animated ? { width: 0 } : false}
                                animate={{ width: `${component.value * 100}%` }}
                                transition={{ 
                                  duration: animated ? 1 : 0, 
                                  delay: animated ? index * 0.1 + 0.3 : 0 
                                }}
                                className={`h-2 rounded-full bg-gradient-to-r ${component.color}`}
                              />
                            </div>
                          </div>
                        </motion.div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs">{component.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                );
              })}
            </div>
          </div>
        )}

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {((voteWeight.accuracyComponent + voteWeight.recentPerformanceComponent) * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">
              Performance Score
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {(voteWeight.confidenceComponent * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">
              Reliability Score
            </div>
          </div>
        </div>

        {/* Weight Explanation */}
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-blue-800 dark:text-blue-300">
              <p className="font-medium mb-1">How vote weights are calculated:</p>
              <p>
                Weights are determined by a combination of historical accuracy (35%), 
                recent performance (25%), prediction consistency (20%), and council experience (20%). 
                Higher weights mean more influence in consensus decisions.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VoteWeightBreakdown;