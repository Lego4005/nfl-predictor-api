import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  DollarSign, TrendingUp, BarChart2, Calculator,
  Target, ArrowUpDown, Clock, AlertTriangle
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import type { 
  ExpertPrediction, 
  ConsensusResult 
} from '../../types/aiCouncil';

interface BettingMarketsPanelProps {
  predictions: ExpertPrediction[];
  consensus: ConsensusResult[];
  categories: string[];
  onCategorySelect: (categoryId: string) => void;
  viewMode: 'grid' | 'list' | 'compact';
}

interface BettingPrediction {
  categoryId: string;
  categoryName: string;
  consensusValue: any;
  confidence: number;
  agreement: number;
  expertCount: number;
  lineMovement: 'up' | 'down' | 'stable';
  marketValue: number;
  impliedProbability: number;
  bettingTrend: 'sharp' | 'public' | 'neutral';
}

const BettingMarketsPanel: React.FC<BettingMarketsPanelProps> = ({
  predictions,
  consensus,
  categories,
  onCategorySelect,
  viewMode
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Process betting market predictions
  const bettingPredictions: BettingPrediction[] = React.useMemo(() => {
    const categoryMap: Record<string, string> = {
      'point_spread': 'Point Spread',
      'total_over_under': 'Over/Under Total',
      'moneyline': 'Moneyline',
      'first_half_spread': 'First Half Spread',
      'first_half_total': 'First Half Total',
      'quarter_lines': 'Quarter Lines',
      'live_spread': 'Live Spread',
      'live_total': 'Live Total',
      'prop_bet_lines': 'Prop Bet Lines'
    };

    return categories.map(categoryId => {
      const categoryConsensus = consensus.find(c => c.categoryId === categoryId);
      const categoryPredictions = predictions.flatMap(p => 
        p.predictions.filter(pred => pred.categoryId === categoryId)
      );

      // Mock betting data
      const mockValue = Math.random() * 100 - 50; // Random value between -50 and 50
      const mockProbability = Math.random() * 0.4 + 0.3; // Between 30-70%

      return {
        categoryId,
        categoryName: categoryMap[categoryId] || categoryId.replace(/_/g, ' '),
        consensusValue: categoryConsensus?.consensusValue || mockValue.toFixed(1),
        confidence: categoryConsensus?.confidence || Math.random() * 0.4 + 0.6,
        agreement: categoryConsensus?.agreement || Math.random() * 0.4 + 0.6,
        expertCount: categoryPredictions.length || Math.floor(Math.random() * 5) + 3,
        lineMovement: Math.random() > 0.6 ? 'up' : Math.random() > 0.3 ? 'down' : 'stable',
        marketValue: mockValue,
        impliedProbability: mockProbability,
        bettingTrend: Math.random() > 0.6 ? 'sharp' : Math.random() > 0.3 ? 'public' : 'neutral'
      };
    }).filter(p => p.expertCount > 0);
  }, [categories, consensus, predictions]);

  const getCategoryIcon = (categoryId: string) => {
    const icons: Record<string, any> = {
      'point_spread': ArrowUpDown,
      'total_over_under': Calculator,
      'moneyline': DollarSign,
      'first_half_spread': Clock,
      'first_half_total': Clock,
      'quarter_lines': BarChart2,
      'live_spread': TrendingUp,
      'live_total': TrendingUp,
      'prop_bet_lines': Target
    };
    return icons[categoryId] || DollarSign;
  };

  const getLineMovementColor = (movement: string) => {
    switch (movement) {
      case 'up': return 'text-green-600 bg-green-100';
      case 'down': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getBettingTrendColor = (trend: string) => {
    switch (trend) {
      case 'sharp': return 'text-purple-600 bg-purple-100';
      case 'public': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getMovementIcon = (movement: string) => {
    return movement === 'up' ? <TrendingUp className="h-4 w-4 text-green-500" /> :
           movement === 'down' ? <TrendingUp className="h-4 w-4 text-red-500 rotate-180" /> :
           <ArrowUpDown className="h-4 w-4 text-gray-500" />;
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
    onCategorySelect(categoryId);
  };

  if (viewMode === 'compact') {
    return (
      <div className="space-y-2">
        {bettingPredictions.map((prediction, index) => (
          <motion.div
            key={prediction.categoryId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border hover:border-green-300 cursor-pointer"
            onClick={() => handleCategoryClick(prediction.categoryId)}
          >
            <div className="flex items-center gap-3">
              <div className="p-1 rounded bg-green-100">
                {React.createElement(getCategoryIcon(prediction.categoryId), {
                  className: "h-4 w-4 text-green-600"
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
                    ? (prediction.consensusValue > 0 ? '+' : '') + prediction.consensusValue.toFixed(1)
                    : String(prediction.consensusValue)}
                </div>
                <div className="text-xs text-gray-500">
                  {(prediction.impliedProbability * 100).toFixed(0)}%
                </div>
              </div>
              {getMovementIcon(prediction.lineMovement)}
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-3">
        {bettingPredictions.map((prediction, index) => (
          <motion.div
            key={prediction.categoryId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card 
              className="cursor-pointer transition-all duration-200 hover:shadow-md border-l-4 border-l-green-500"
              onClick={() => handleCategoryClick(prediction.categoryId)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {React.createElement(getCategoryIcon(prediction.categoryId), {
                      className: "h-5 w-5 text-green-600"
                    })}
                    <div>
                      <h4 className="font-semibold">{prediction.categoryName}</h4>
                      <p className="text-sm text-gray-600">
                        {prediction.expertCount} expert predictions
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getLineMovementColor(prediction.lineMovement)}>
                      {prediction.lineMovement} movement
                    </Badge>
                    <Badge className={getBettingTrendColor(prediction.bettingTrend)}>
                      {prediction.bettingTrend} money
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Consensus Line</div>
                    <div className="text-lg font-bold">
                      {typeof prediction.consensusValue === 'number' 
                        ? (prediction.consensusValue > 0 ? '+' : '') + prediction.consensusValue.toFixed(1)
                        : String(prediction.consensusValue)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Implied Probability</div>
                    <div className="text-lg font-bold">
                      {(prediction.impliedProbability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Confidence</div>
                    <Progress value={prediction.confidence * 100} className="h-2" />
                    <div className="text-xs text-gray-500 mt-1">
                      {(prediction.confidence * 100).toFixed(1)}%
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
      {bettingPredictions.map((prediction, index) => {
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
                  ? 'ring-2 ring-green-500 shadow-lg border-green-300' 
                  : 'hover:shadow-md border-gray-200'
                }
                border-l-4 border-l-green-500
              `}
              onClick={() => handleCategoryClick(prediction.categoryId)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-green-100">
                      <IconComponent className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-semibold">
                        {prediction.categoryName}
                      </CardTitle>
                      <Badge 
                        variant="secondary" 
                        className={`text-xs mt-1 ${getBettingTrendColor(prediction.bettingTrend)}`}
                      >
                        {prediction.bettingTrend} money
                      </Badge>
                    </div>
                  </div>
                  {getMovementIcon(prediction.lineMovement)}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Consensus Line */}
                <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-sm text-green-700 dark:text-green-300 mb-1">
                    Consensus Line
                  </div>
                  <div className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {typeof prediction.consensusValue === 'number' 
                      ? (prediction.consensusValue > 0 ? '+' : '') + prediction.consensusValue.toFixed(1)
                      : String(prediction.consensusValue)}
                  </div>
                </div>

                {/* Market Metrics */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-gray-600 dark:text-gray-300 mb-1">
                      Implied Probability
                    </div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {(prediction.impliedProbability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600 dark:text-gray-300 mb-1">
                      Market Value
                    </div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {(prediction.marketValue > 0 ? '+' : '') + prediction.marketValue.toFixed(1)}
                    </div>
                  </div>
                </div>

                {/* Confidence and Agreement */}
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

                {/* Line Movement Indicator */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">Line Movement</span>
                  </div>
                  <Badge className={getLineMovementColor(prediction.lineMovement)}>
                    {prediction.lineMovement}
                  </Badge>
                </div>

                {/* Expert Count */}
                <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200 dark:border-gray-700">
                  <span className="text-gray-600 dark:text-gray-300">Experts Contributing</span>
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
                        Market Analysis
                      </h5>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Current line shows {prediction.bettingTrend} money influence with {prediction.lineMovement} movement.
                        Expert consensus suggests {prediction.confidence > 0.7 ? 'strong' : 'moderate'} confidence
                        in this prediction.
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

export default BettingMarketsPanel;