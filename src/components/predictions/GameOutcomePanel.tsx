import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, Target, BarChart3, Clock, 
  TrendingUp, Users, Award, AlertCircle 
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import type { 
  ExpertPrediction, 
  ConsensusResult,
  CategoryPrediction 
} from '../../types/aiCouncil';

interface GameOutcomePanelProps {
  predictions: ExpertPrediction[];
  consensus: ConsensusResult[];
  categories: string[];
  onCategorySelect: (categoryId: string) => void;
  viewMode: 'grid' | 'list' | 'compact';
}

interface GameOutcomePrediction {
  categoryId: string;
  categoryName: string;
  consensusValue: any;
  confidence: number;
  agreement: number;
  expertCount: number;
  expertPredictions: Array<{
    expertId: string;
    value: any;
    confidence: number;
  }>;
  trend: 'up' | 'down' | 'stable';
  importance: 'high' | 'medium' | 'low';
}

const GameOutcomePanel: React.FC<GameOutcomePanelProps> = ({
  predictions,
  consensus,
  categories,
  onCategorySelect,
  viewMode
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Process game outcome predictions
  const gameOutcomePredictions: GameOutcomePrediction[] = React.useMemo(() => {
    const categoryMap: Record<string, string> = {
      'game_winner': 'Game Winner',
      'final_score': 'Final Score',
      'margin_of_victory': 'Margin of Victory',
      'first_half_winner': 'First Half Winner',
      'second_half_winner': 'Second Half Winner',
      'quarter_winners': 'Quarter Winners',
      'exact_score': 'Exact Score',
      'shutout_probability': 'Shutout Probability'
    };

    return categories.map(categoryId => {
      const categoryConsensus = consensus.find(c => c.categoryId === categoryId);
      const categoryPredictions = predictions.flatMap(p => 
        p.predictions.filter(pred => pred.categoryId === categoryId)
      );

      const expertPreds = categoryPredictions.map(pred => ({
        expertId: predictions.find(p => p.predictions.includes(pred))?.expertId || '',
        value: pred.expertValue,
        confidence: pred.confidence
      }));

      return {
        categoryId,
        categoryName: categoryMap[categoryId] || categoryId.replace(/_/g, ' '),
        consensusValue: categoryConsensus?.consensusValue || 'TBD',
        confidence: categoryConsensus?.confidence || 0,
        agreement: categoryConsensus?.agreement || 0,
        expertCount: expertPreds.length,
        expertPredictions: expertPreds,
        trend: Math.random() > 0.5 ? 'up' : 'down', // Mock trend data
        importance: ['game_winner', 'final_score', 'margin_of_victory'].includes(categoryId) ? 'high' : 'medium'
      };
    }).filter(p => p.expertCount > 0);
  }, [categories, consensus, predictions]);

  const getCategoryIcon = (categoryId: string) => {
    const icons: Record<string, any> = {
      'game_winner': Trophy,
      'final_score': Target,
      'margin_of_victory': BarChart3,
      'first_half_winner': Clock,
      'second_half_winner': Clock,
      'quarter_winners': Award,
      'exact_score': Target,
      'shutout_probability': AlertCircle
    };
    return icons[categoryId] || Trophy;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-blue-600 bg-blue-100';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'border-l-red-500 bg-red-50';
      case 'medium': return 'border-l-yellow-500 bg-yellow-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getTrendIcon = (trend: string) => {
    return trend === 'up' ? <TrendingUp className="h-4 w-4 text-green-500" /> :
           trend === 'down' ? <TrendingUp className="h-4 w-4 text-red-500 rotate-180" /> :
           <TrendingUp className="h-4 w-4 text-gray-500" />;
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
    onCategorySelect(categoryId);
  };

  if (viewMode === 'compact') {
    return (
      <div className="space-y-2">
        {gameOutcomePredictions.map((prediction, index) => (
          <motion.div
            key={prediction.categoryId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border hover:border-blue-300 cursor-pointer"
            onClick={() => handleCategoryClick(prediction.categoryId)}
          >
            <div className="flex items-center gap-3">
              <div className="p-1 rounded bg-blue-100">
                {React.createElement(getCategoryIcon(prediction.categoryId), {
                  className: "h-4 w-4 text-blue-600"
                })}
              </div>
              <div>
                <span className="font-medium text-sm">{prediction.categoryName}</span>
                <div className="text-xs text-gray-500">
                  {prediction.expertCount} experts
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="font-semibold text-sm">
                  {typeof prediction.consensusValue === 'number' 
                    ? prediction.consensusValue.toFixed(1)
                    : String(prediction.consensusValue)}
                </div>
                <div className="text-xs text-gray-500">
                  {(prediction.confidence * 100).toFixed(0)}%
                </div>
              </div>
              {getTrendIcon(prediction.trend)}
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-3">
        {gameOutcomePredictions.map((prediction, index) => (
          <motion.div
            key={prediction.categoryId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card 
              className={`cursor-pointer transition-all duration-200 hover:shadow-md border-l-4 ${getImportanceColor(prediction.importance)}`}
              onClick={() => handleCategoryClick(prediction.categoryId)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {React.createElement(getCategoryIcon(prediction.categoryId), {
                      className: "h-5 w-5 text-blue-600"
                    })}
                    <div>
                      <h4 className="font-semibold">{prediction.categoryName}</h4>
                      <p className="text-sm text-gray-600">
                        {prediction.expertCount} expert predictions
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getConfidenceColor(prediction.confidence)}>
                      {(prediction.confidence * 100).toFixed(0)}% confidence
                    </Badge>
                    {getTrendIcon(prediction.trend)}
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Consensus Prediction</div>
                    <div className="text-lg font-bold">
                      {typeof prediction.consensusValue === 'number' 
                        ? prediction.consensusValue.toFixed(1)
                        : String(prediction.consensusValue)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Expert Agreement</div>
                    <Progress value={prediction.agreement * 100} className="h-2" />
                    <div className="text-xs text-gray-500 mt-1">
                      {(prediction.agreement * 100).toFixed(1)}%
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
      {gameOutcomePredictions.map((prediction, index) => {
        const IconComponent = getCategoryIcon(prediction.categoryId);
        const isSelected = selectedCategory === prediction.categoryId;
        
        return (
          <motion.div
            key={prediction.categoryId}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            <Card 
              className={`
                cursor-pointer transition-all duration-300 h-full
                ${isSelected 
                  ? 'ring-2 ring-blue-500 shadow-lg border-blue-300' 
                  : 'hover:shadow-md border-gray-200'
                }
                ${prediction.importance === 'high' ? 'border-l-4 border-l-red-500' : ''}
              `}
              onClick={() => handleCategoryClick(prediction.categoryId)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-blue-100">
                      <IconComponent className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-semibold">
                        {prediction.categoryName}
                      </CardTitle>
                      {prediction.importance === 'high' && (
                        <Badge variant="secondary" className="text-xs mt-1">
                          High Priority
                        </Badge>
                      )}
                    </div>
                  </div>
                  {getTrendIcon(prediction.trend)}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Consensus Value */}
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-300 mb-1">
                    Consensus Prediction
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {typeof prediction.consensusValue === 'number' 
                      ? prediction.consensusValue.toFixed(1)
                      : String(prediction.consensusValue)}
                  </div>
                </div>

                {/* Metrics */}
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-300">Confidence</span>
                      <span className="font-semibold">
                        {(prediction.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={prediction.confidence * 100} className="h-2" />
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-300">Agreement</span>
                      <span className="font-semibold">
                        {(prediction.agreement * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={prediction.agreement * 100} className="h-2" />
                  </div>
                </div>

                {/* Expert Count */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">Experts</span>
                  </div>
                  <span className="font-semibold">{prediction.expertCount}</span>
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
                        Expert Breakdown
                      </h5>
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {prediction.expertPredictions.slice(0, 5).map((exp, i) => (
                          <div key={i} className="flex justify-between text-xs">
                            <span className="text-gray-600 dark:text-gray-300">
                              Expert {i + 1}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {typeof exp.value === 'number' 
                                  ? exp.value.toFixed(1)
                                  : String(exp.value)}
                              </span>
                              <span className="text-gray-500">
                                ({(exp.confidence * 100).toFixed(0)}%)
                              </span>
                            </div>
                          </div>
                        ))}
                        {prediction.expertPredictions.length > 5 && (
                          <div className="text-xs text-gray-500 text-center pt-1">
                            +{prediction.expertPredictions.length - 5} more experts
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
};

export default GameOutcomePanel;