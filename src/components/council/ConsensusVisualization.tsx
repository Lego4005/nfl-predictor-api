import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, TrendingUp, AlertTriangle, CheckCircle, 
  Users, Target, Zap, Filter, Eye, EyeOff 
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/tabs';
import type { 
  ConsensusVisualizationProps, 
  ConsensusResult,
  PredictionCategoryGroup 
} from '../../types/aiCouncil';

const ConsensusVisualization: React.FC<ConsensusVisualizationProps> = ({
  consensusResults,
  activeCategoryFilter,
  showConfidenceIndicators
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'confidence' | 'agreement' | 'category'>('confidence');
  const [showLowConfidence, setShowLowConfidence] = useState(true);

  // Filter and sort consensus results
  const filteredResults = React.useMemo(() => {
    let filtered = consensusResults;

    // Filter by category group
    if (activeCategoryFilter !== 'all') {
      filtered = filtered.filter(result => 
        result.categoryId.startsWith(activeCategoryFilter)
      );
    }

    // Filter by confidence threshold
    if (!showLowConfidence) {
      filtered = filtered.filter(result => result.confidence >= 0.6);
    }

    // Sort results
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return b.confidence - a.confidence;
        case 'agreement':
          return b.agreement - a.agreement;
        case 'category':
          return a.categoryId.localeCompare(b.categoryId);
        default:
          return 0;
      }
    });
  }, [consensusResults, activeCategoryFilter, showLowConfidence, sortBy]);

  // Calculate overall consensus stats
  const consensusStats = React.useMemo(() => {
    const totalResults = filteredResults.length;
    const highConfidence = filteredResults.filter(r => r.confidence >= 0.8).length;
    const strongAgreement = filteredResults.filter(r => r.agreement >= 0.8).length;
    const avgConfidence = filteredResults.reduce((sum, r) => sum + r.confidence, 0) / totalResults;
    const avgAgreement = filteredResults.reduce((sum, r) => sum + r.agreement, 0) / totalResults;
    
    return {
      totalResults,
      highConfidence,
      strongAgreement,
      avgConfidence: avgConfidence || 0,
      avgAgreement: avgAgreement || 0,
      consensusQuality: (avgConfidence + avgAgreement) / 2
    };
  }, [filteredResults]);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-blue-600 bg-blue-100';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getAgreementIcon = (agreement: number) => {
    if (agreement >= 0.9) return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (agreement >= 0.7) return <Users className="h-4 w-4 text-blue-500" />;
    if (agreement >= 0.5) return <BarChart3 className="h-4 w-4 text-yellow-500" />;
    return <AlertTriangle className="h-4 w-4 text-red-500" />;
  };

  const getCategoryDisplayName = (categoryId: string) => {
    const categoryNames: Record<string, string> = {
      'game_outcome_winner': 'Game Winner',
      'game_outcome_score': 'Final Score',
      'game_outcome_margin': 'Margin of Victory',
      'betting_markets_spread': 'Point Spread',
      'betting_markets_total': 'Over/Under',
      'betting_markets_moneyline': 'Moneyline',
      'live_scenarios_next_score': 'Next Score',
      'live_scenarios_momentum': 'Game Momentum',
      'player_props_passing': 'Passing Props',
      'player_props_rushing': 'Rushing Props',
      'situational_weather': 'Weather Impact',
      'situational_injuries': 'Injury Impact'
    };
    return categoryNames[categoryId] || categoryId.replace(/_/g, ' ');
  };

  return (
    <div className="w-full space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Consensus Analysis
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            AI Council agreement levels across prediction categories
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="confidence">Sort by Confidence</option>
            <option value="agreement">Sort by Agreement</option>
            <option value="category">Sort by Category</option>
          </select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowLowConfidence(!showLowConfidence)}
            className="flex items-center gap-2"
          >
            {showLowConfidence ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            {showLowConfidence ? 'Hide Low' : 'Show All'}
          </Button>
        </div>
      </div>

      {/* Consensus Stats Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <BarChart3 className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {consensusStats.totalResults}
            </div>
            <div className="text-xs text-gray-500">Total Predictions</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <Target className="h-6 w-6 text-green-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {consensusStats.highConfidence}
            </div>
            <div className="text-xs text-gray-500">High Confidence</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <Users className="h-6 w-6 text-purple-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {consensusStats.strongAgreement}
            </div>
            <div className="text-xs text-gray-500">Strong Agreement</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <TrendingUp className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(consensusStats.avgConfidence * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Avg Confidence</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <Zap className="h-6 w-6 text-orange-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(consensusStats.consensusQuality * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Quality Score</div>
          </div>
        </Card>
      </div>

      {/* Consensus Results Grid */}
      <div className="grid gap-4">
        <AnimatePresence>
          {filteredResults.map((result, index) => (
            <motion.div
              key={result.categoryId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
              className="cursor-pointer"
              onClick={() => setSelectedCategory(
                selectedCategory === result.categoryId ? null : result.categoryId
              )}
            >
              <Card className={`
                transition-all duration-200 hover:shadow-md
                ${selectedCategory === result.categoryId ? 'ring-2 ring-blue-500 border-blue-300' : ''}
              `}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {getAgreementIcon(result.agreement)}
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {getCategoryDisplayName(result.categoryId)}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-300">
                          {result.totalExperts} experts participating
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge 
                        variant="outline" 
                        className={getConfidenceColor(result.confidence)}
                      >
                        {(result.confidence * 100).toFixed(0)}% confidence
                      </Badge>
                      <Badge variant="secondary">
                        {(result.agreement * 100).toFixed(0)}% agreement
                      </Badge>
                    </div>
                  </div>

                  {/* Consensus Value Display */}
                  <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Consensus Prediction:
                      </span>
                      <span className="text-lg font-bold text-gray-900 dark:text-white">
                        {typeof result.consensusValue === 'number' 
                          ? result.consensusValue.toFixed(1)
                          : String(result.consensusValue)
                        }
                      </span>
                    </div>
                  </div>

                  {/* Progress Bars */}
                  {showConfidenceIndicators && (
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>Confidence Level</span>
                          <span>{(result.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <Progress 
                          value={result.confidence * 100} 
                          className="h-2"
                        />
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span>Expert Agreement</span>
                          <span>{(result.agreement * 100).toFixed(1)}%</span>
                        </div>
                        <Progress 
                          value={result.agreement * 100} 
                          className="h-2"
                        />
                      </div>
                    </div>
                  )}

                  {/* Conflicting Experts (if any) */}
                  {result.conflictingExperts.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          {result.conflictingExperts.length} expert(s) dissenting
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Expanded Details */}
                  {selectedCategory === result.categoryId && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ duration: 0.3 }}
                      className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                            Voting Breakdown
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>Unanimous:</span>
                              <span>{result.votingBreakdown.unanimous}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Strong Majority:</span>
                              <span>{result.votingBreakdown.strongMajority}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Simple Majority:</span>
                              <span>{result.votingBreakdown.simpleMajority}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Split Decision:</span>
                              <span>{result.votingBreakdown.split}</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                            Additional Metrics
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>Weighted Score:</span>
                              <span>{result.weightedScore.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Last Updated:</span>
                              <span>{new Date(result.timestamp).toLocaleTimeString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredResults.length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500 dark:text-gray-400">
            <Filter className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No consensus data found</h3>
            <p className="text-sm">
              Try adjusting your filters or check back later for updated predictions.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ConsensusVisualization;