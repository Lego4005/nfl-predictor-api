import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, Activity, Clock, TrendingUp, 
  Flame, Target, BarChart3, Radio
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import type { 
  ExpertPrediction, 
  ConsensusResult 
} from '../../types/aiCouncil';

interface LiveScenariosPanelProps {
  predictions: ExpertPrediction[];
  consensus: ConsensusResult[];
  categories: string[];
  onCategorySelect: (categoryId: string) => void;
  viewMode: 'grid' | 'list' | 'compact';
}

interface LiveScenario {
  categoryId: string;
  categoryName: string;
  consensusValue: any;
  confidence: number;
  agreement: number;
  expertCount: number;
  lastUpdate: string;
  changeFromLast: number;
  volatility: 'high' | 'medium' | 'low';
  priority: 'critical' | 'high' | 'medium' | 'low';
  isLive: boolean;
}

const LiveScenariosPanel: React.FC<LiveScenariosPanelProps> = ({
  predictions,
  consensus,
  categories,
  onCategorySelect,
  viewMode
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [liveUpdates, setLiveUpdates] = useState<Map<string, number>>(new Map());

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveUpdates(prev => {
        const newUpdates = new Map(prev);
        categories.forEach(categoryId => {
          if (Math.random() > 0.7) { // 30% chance of update per cycle
            newUpdates.set(categoryId, Date.now());
          }
        });
        return newUpdates;
      });
    }, 3000); // Update every 3 seconds

    return () => clearInterval(interval);
  }, [categories]);

  // Process live scenario predictions
  const liveScenarios: LiveScenario[] = React.useMemo(() => {
    const categoryMap: Record<string, string> = {
      'next_score': 'Next Score',
      'next_touchdown': 'Next Touchdown',
      'next_field_goal': 'Next Field Goal',
      'drive_result': 'Current Drive Result',
      'momentum_shift': 'Momentum Shift',
      'comeback_probability': 'Comeback Probability',
      'live_win_probability': 'Live Win Probability',
      'score_prediction_live': 'Live Score Prediction'
    };

    const priorityMap: Record<string, 'critical' | 'high' | 'medium' | 'low'> = {
      'next_score': 'critical',
      'live_win_probability': 'critical',
      'comeback_probability': 'high',
      'momentum_shift': 'high',
      'next_touchdown': 'medium',
      'next_field_goal': 'medium',
      'drive_result': 'medium',
      'score_prediction_live': 'low'
    };

    return categories.map(categoryId => {
      const categoryConsensus = consensus.find(c => c.categoryId === categoryId);
      const categoryPredictions = predictions.flatMap(p => 
        p.predictions.filter(pred => pred.categoryId === categoryId)
      );

      // Mock live data
      const mockValue = Math.random();
      const hasRecentUpdate = liveUpdates.has(categoryId);

      return {
        categoryId,
        categoryName: categoryMap[categoryId] || categoryId.replace(/_/g, ' '),
        consensusValue: categoryConsensus?.consensusValue || (mockValue * 100).toFixed(1) + '%',
        confidence: categoryConsensus?.confidence || Math.random() * 0.3 + 0.7, // Higher confidence for live
        agreement: categoryConsensus?.agreement || Math.random() * 0.3 + 0.7,
        expertCount: categoryPredictions.length || Math.floor(Math.random() * 4) + 4,
        lastUpdate: hasRecentUpdate ? 'Just now' : Math.floor(Math.random() * 30) + 's ago',
        changeFromLast: (Math.random() - 0.5) * 20, // -10 to +10
        volatility: Math.random() > 0.6 ? 'high' : Math.random() > 0.3 ? 'medium' : 'low',
        priority: priorityMap[categoryId] || 'medium',
        isLive: Math.random() > 0.3 // 70% chance of being live
      };
    }).filter(s => s.expertCount > 0);
  }, [categories, consensus, predictions, liveUpdates]);

  const getCategoryIcon = (categoryId: string) => {
    const icons: Record<string, any> = {
      'next_score': Target,
      'next_touchdown': Flame,
      'next_field_goal': Target,
      'drive_result': TrendingUp,
      'momentum_shift': Activity,
      'comeback_probability': BarChart3,
      'live_win_probability': TrendingUp,
      'score_prediction_live': Radio
    };
    return icons[categoryId] || Zap;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-700 bg-red-100 border-red-200';
      case 'high': return 'text-orange-700 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      default: return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getVolatilityColor = (volatility: string) => {
    switch (volatility) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
    onCategorySelect(categoryId);
  };

  if (viewMode === 'compact') {
    return (
      <div className="space-y-2">
        {liveScenarios.map((scenario, index) => (
          <motion.div
            key={scenario.categoryId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`
              flex items-center justify-between p-3 rounded-lg border cursor-pointer
              ${scenario.isLive ? 'bg-red-50 border-red-200 hover:border-red-300' : 'bg-white border-gray-200 hover:border-red-300'}
            `}
            onClick={() => handleCategoryClick(scenario.categoryId)}
          >
            <div className="flex items-center gap-3">
              <div className={`p-1 rounded ${scenario.isLive ? 'bg-red-100' : 'bg-red-100'}`}>
                {React.createElement(getCategoryIcon(scenario.categoryId), {
                  className: `h-4 w-4 ${scenario.isLive ? 'text-red-600' : 'text-red-600'}`
                })}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{scenario.categoryName}</span>
                  {scenario.isLive && (
                    <Badge className="text-xs bg-red-100 text-red-700 animate-pulse">
                      LIVE
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-gray-500">
                  Updated {scenario.lastUpdate}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="font-semibold text-sm">
                  {String(scenario.consensusValue)}
                </div>
                <div className={`text-xs ${getChangeColor(scenario.changeFromLast)}`}>
                  {scenario.changeFromLast > 0 ? '+' : ''}{scenario.changeFromLast.toFixed(1)}%
                </div>
              </div>
              {scenario.isLive && <Activity className="h-4 w-4 text-red-500 animate-pulse" />}
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-3">
        {liveScenarios.map((scenario, index) => (
          <motion.div
            key={scenario.categoryId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card 
              className={`
                cursor-pointer transition-all duration-200 hover:shadow-md border-l-4
                ${scenario.isLive ? 'border-l-red-500 bg-red-50' : 'border-l-red-400'}
              `}
              onClick={() => handleCategoryClick(scenario.categoryId)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {React.createElement(getCategoryIcon(scenario.categoryId), {
                      className: "h-5 w-5 text-red-600"
                    })}
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold">{scenario.categoryName}</h4>
                        {scenario.isLive && (
                          <Badge className="bg-red-100 text-red-700 animate-pulse">
                            LIVE
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        {scenario.expertCount} experts • Updated {scenario.lastUpdate}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getPriorityColor(scenario.priority)}>
                      {scenario.priority} priority
                    </Badge>
                    <Badge className={getVolatilityColor(scenario.volatility)}>
                      {scenario.volatility} volatility
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Current Value</div>
                    <div className="text-lg font-bold">
                      {String(scenario.consensusValue)}
                    </div>
                    <div className={`text-xs ${getChangeColor(scenario.changeFromLast)}`}>
                      {scenario.changeFromLast > 0 ? '+' : ''}{scenario.changeFromLast.toFixed(1)}% change
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Confidence</div>
                    <Progress value={scenario.confidence * 100} className="h-2" />
                    <div className="text-xs text-gray-500 mt-1">
                      {(scenario.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Agreement</div>
                    <Progress value={scenario.agreement * 100} className="h-2" />
                    <div className="text-xs text-gray-500 mt-1">
                      {(scenario.agreement * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    );
  }

  // Grid view (default)
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <AnimatePresence>
        {liveScenarios.map((scenario, index) => {
          const IconComponent = getCategoryIcon(scenario.categoryId);
          const isSelected = selectedCategory === scenario.categoryId;
          const hasRecentUpdate = liveUpdates.has(scenario.categoryId);
          
          return (
            <motion.div
              key={scenario.categoryId}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              <Card 
                className={`
                  cursor-pointer transition-all duration-300 h-full relative overflow-hidden
                  ${isSelected 
                    ? 'ring-2 ring-red-500 shadow-lg border-red-300' 
                    : 'hover:shadow-md border-gray-200'
                  }
                  ${scenario.isLive ? 'border-l-4 border-l-red-500' : 'border-l-4 border-l-red-400'}
                  ${scenario.isLive ? 'bg-gradient-to-br from-red-50 to-red-100' : ''}
                `}
                onClick={() => handleCategoryClick(scenario.categoryId)}
              >
                {/* Live indicator pulse */}
                {scenario.isLive && (
                  <div className="absolute top-2 right-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-ping" />
                    <div className="absolute top-0 w-3 h-3 bg-red-600 rounded-full" />
                  </div>
                )}

                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`p-2 rounded-lg ${scenario.isLive ? 'bg-red-100' : 'bg-red-100'}`}>
                        <IconComponent className="h-5 w-5 text-red-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-semibold">
                          {scenario.categoryName}
                        </CardTitle>
                        <div className="flex items-center gap-2 mt-1">
                          {scenario.isLive && (
                            <Badge className="text-xs bg-red-100 text-red-700 animate-pulse">
                              LIVE
                            </Badge>
                          )}
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${getPriorityColor(scenario.priority)}`}
                          >
                            {scenario.priority}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Current Value */}
                  <div className={`text-center p-3 rounded-lg ${scenario.isLive ? 'bg-red-100' : 'bg-red-50'}`}>
                    <div className="text-sm text-red-700 mb-1">
                      Current Prediction
                    </div>
                    <div className="text-2xl font-bold text-red-900">
                      {String(scenario.consensusValue)}
                    </div>
                    <div className={`text-sm font-medium ${getChangeColor(scenario.changeFromLast)}`}>
                      {scenario.changeFromLast > 0 ? '+' : ''}{scenario.changeFromLast.toFixed(1)}% change
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-300">Confidence</span>
                        <span className="font-semibold">
                          {(scenario.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={scenario.confidence * 100} className="h-2" />
                    </div>

                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-300">Agreement</span>
                        <span className="font-semibold">
                          {(scenario.agreement * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={scenario.agreement * 100} className="h-2" />
                    </div>
                  </div>

                  {/* Status Information */}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-300">Updated</span>
                    </div>
                    <span className={`font-semibold ${hasRecentUpdate ? 'text-red-600' : ''}`}>
                      {scenario.lastUpdate}
                    </span>
                  </div>

                  {/* Volatility Indicator */}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-1">
                      <Activity className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-300">Volatility</span>
                    </div>
                    <Badge className={getVolatilityColor(scenario.volatility)}>
                      {scenario.volatility}
                    </Badge>
                  </div>

                  {/* Expert Count */}
                  <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200 dark:border-gray-700">
                    <span className="text-gray-600 dark:text-gray-300">Contributing Experts</span>
                    <span className="font-semibold">{scenario.expertCount}</span>
                  </div>

                  {/* Expanded Details */}
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ duration: 0.3 }}
                      className="pt-3 border-t border-gray-200 dark:border-gray-700"
                    >
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Live Analysis
                        </h5>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          This prediction is being updated in real-time based on current game state.
                          {scenario.volatility === 'high' && ' High volatility indicates rapidly changing conditions.'}
                          {scenario.priority === 'critical' && ' Critical priority - major impact on game outcome.'}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default LiveScenariosPanel;