import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  AlertTriangle, BarChart3, TrendingUp, Users, 
  Target, Zap, DollarSign, Activity
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Avatar, AvatarFallback } from '../ui/avatar';
import type { PredictionCategoryGroup } from '../../types/aiCouncil';

interface DisagreementAnalysisProps {
  expertIds: string[];
  timeRange: 'week' | 'month' | 'season' | 'all_time';
}

interface DisagreementData {
  categoryId: string;
  categoryName: string;
  group: PredictionCategoryGroup;
  conflictLevel: 'high' | 'medium' | 'low';
  expertPositions: Array<{
    expertId: string;
    expertName: string;
    position: any;
    confidence: number;
    reasoning: string[];
  }>;
  marketImplication: 'significant' | 'moderate' | 'minimal';
  disagreementScore: number; // 0-100
  volatility: number; // How much positions change over time
}

const DisagreementAnalysis: React.FC<DisagreementAnalysisProps> = ({
  expertIds,
  timeRange
}) => {
  const [filterBy, setFilterBy] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [sortBy, setSortBy] = useState<'conflict' | 'market_impact' | 'volatility'>('conflict');

  // Mock expert names
  const expertNames: Record<string, string> = {
    'expert_1': 'AI Prophet',
    'expert_2': 'Statistical Sage',
    'expert_3': 'Game Theory Guru',
    'expert_4': 'Data Dynamo'
  };

  // Mock disagreement data
  const disagreements: DisagreementData[] = [
    {
      categoryId: 'game_outcome_winner',
      categoryName: 'Game Winner',
      group: 'game_outcome',
      conflictLevel: 'high',
      expertPositions: expertIds.map((id, index) => ({
        expertId: id,
        expertName: expertNames[id] || `Expert ${index + 1}`,
        position: index % 2 === 0 ? 'Home Team' : 'Away Team',
        confidence: Math.random() * 0.3 + 0.6,
        reasoning: [
          index % 2 === 0 ? 'Strong home field advantage' : 'Superior road record',
          index % 2 === 0 ? 'Better recent form' : 'Favorable matchup conditions'
        ]
      })),
      marketImplication: 'significant',
      disagreementScore: 87,
      volatility: 0.72
    },
    {
      categoryId: 'betting_markets_spread',
      categoryName: 'Point Spread',
      group: 'betting_markets',
      conflictLevel: 'medium',
      expertPositions: expertIds.map((id, index) => ({
        expertId: id,
        expertName: expertNames[id] || `Expert ${index + 1}`,
        position: (Math.random() * 10 - 5).toFixed(1),
        confidence: Math.random() * 0.3 + 0.5,
        reasoning: [
          'Statistical model suggests different margin',
          'Injury reports impact assessment'
        ]
      })),
      marketImplication: 'moderate',
      disagreementScore: 64,
      volatility: 0.58
    },
    {
      categoryId: 'player_props_passing',
      categoryName: 'QB Passing Yards',
      group: 'player_props',
      conflictLevel: 'medium',
      expertPositions: expertIds.map((id, index) => ({
        expertId: id,
        expertName: expertNames[id] || `Expert ${index + 1}`,
        position: Math.floor(Math.random() * 100 + 250),
        confidence: Math.random() * 0.4 + 0.4,
        reasoning: [
          'Weather conditions factor differently',
          'Defensive matchup analysis varies'
        ]
      })),
      marketImplication: 'moderate',
      disagreementScore: 56,
      volatility: 0.43
    },
    {
      categoryId: 'live_scenarios_momentum',
      categoryName: 'Game Momentum',
      group: 'live_scenarios',
      conflictLevel: 'low',
      expertPositions: expertIds.map((id, index) => ({
        expertId: id,
        expertName: expertNames[id] || `Expert ${index + 1}`,
        position: index % 3 === 0 ? 'Neutral' : index % 3 === 1 ? 'Home' : 'Away',
        confidence: Math.random() * 0.3 + 0.7,
        reasoning: [
          'Recent play analysis',
          'Score situation impact'
        ]
      })),
      marketImplication: 'minimal',
      disagreementScore: 31,
      volatility: 0.29
    }
  ];

  const getCategoryIcon = (group: PredictionCategoryGroup) => {
    const icons = {
      game_outcome: Target,
      betting_markets: DollarSign,
      live_scenarios: Zap,
      player_props: Users,
      situational_analysis: TrendingUp
    };
    return icons[group] || BarChart3;
  };

  const getConflictColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-700 bg-red-100 border-red-200';
      case 'medium': return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-green-700 bg-green-100 border-green-200';
      default: return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getMarketImpactColor = (impact: string) => {
    switch (impact) {
      case 'significant': return 'text-purple-600 bg-purple-100';
      case 'moderate': return 'text-blue-600 bg-blue-100';
      case 'minimal': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getVolatilityIcon = (volatility: number) => {
    if (volatility > 0.6) return <Activity className="h-4 w-4 text-red-500" />;
    if (volatility > 0.4) return <Activity className="h-4 w-4 text-yellow-500" />;
    return <Activity className="h-4 w-4 text-green-500" />;
  };

  const filteredDisagreements = disagreements.filter(d => 
    filterBy === 'all' || d.conflictLevel === filterBy
  ).sort((a, b) => {
    switch (sortBy) {
      case 'conflict':
        return b.disagreementScore - a.disagreementScore;
      case 'market_impact':
        const impactScore = (impact: string) => 
          impact === 'significant' ? 3 : impact === 'moderate' ? 2 : 1;
        return impactScore(b.marketImplication) - impactScore(a.marketImplication);
      case 'volatility':
        return b.volatility - a.volatility;
      default:
        return 0;
    }
  });

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Expert Disagreement Analysis
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            Categories where experts have conflicting predictions
          </p>
        </div>

        <div className="flex gap-2">
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="all">All Conflicts</option>
            <option value="high">High Conflict</option>
            <option value="medium">Medium Conflict</option>
            <option value="low">Low Conflict</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="conflict">Sort by Conflict Level</option>
            <option value="market_impact">Sort by Market Impact</option>
            <option value="volatility">Sort by Volatility</option>
          </select>
        </div>
      </div>

      {/* Disagreement Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <AlertTriangle className="h-6 w-6 text-red-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {disagreements.filter(d => d.conflictLevel === 'high').length}
            </div>
            <div className="text-xs text-gray-500">High Conflicts</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <BarChart3 className="h-6 w-6 text-yellow-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {disagreements.filter(d => d.conflictLevel === 'medium').length}
            </div>
            <div className="text-xs text-gray-500">Medium Conflicts</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <DollarSign className="h-6 w-6 text-purple-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {disagreements.filter(d => d.marketImplication === 'significant').length}
            </div>
            <div className="text-xs text-gray-500">Market Impact</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <Activity className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(disagreements.reduce((sum, d) => sum + d.volatility, 0) / disagreements.length * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">Avg Volatility</div>
          </div>
        </Card>
      </div>

      {/* Disagreement Details */}
      <div className="space-y-4">
        {filteredDisagreements.map((disagreement, index) => {
          const IconComponent = getCategoryIcon(disagreement.group);
          
          return (
            <motion.div
              key={disagreement.categoryId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-red-100">
                        <IconComponent className="h-5 w-5 text-red-600" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">
                          {disagreement.categoryName}
                        </CardTitle>
                        <p className="text-sm text-gray-600">
                          {disagreement.group.replace('_', ' ')} category
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge className={getConflictColor(disagreement.conflictLevel)}>
                        {disagreement.conflictLevel} conflict
                      </Badge>
                      <Badge className={getMarketImpactColor(disagreement.marketImplication)}>
                        {disagreement.marketImplication} impact
                      </Badge>
                      {getVolatilityIcon(disagreement.volatility)}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Conflict Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Disagreement Score</div>
                      <div className="flex items-center gap-2">
                        <Progress value={disagreement.disagreementScore} className="h-2 flex-1" />
                        <span className="text-sm font-semibold">
                          {disagreement.disagreementScore}%
                        </span>
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-1">Volatility</div>
                      <div className="flex items-center gap-2">
                        <Progress value={disagreement.volatility * 100} className="h-2 flex-1" />
                        <span className="text-sm font-semibold">
                          {(disagreement.volatility * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-1">Market Significance</div>
                      <Badge className={getMarketImpactColor(disagreement.marketImplication)}>
                        {disagreement.marketImplication}
                      </Badge>
                    </div>
                  </div>

                  {/* Expert Positions */}
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                      Expert Positions
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {disagreement.expertPositions.map((position, i) => (
                        <div key={position.expertId} className="p-4 border border-gray-200 rounded-lg">
                          <div className="flex items-center gap-3 mb-3">
                            <Avatar className="h-8 w-8">
                              <AvatarFallback className="bg-blue-100 text-blue-600 text-xs">
                                E{i + 1}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <div className="font-semibold text-sm">
                                {position.expertName}
                              </div>
                              <div className="text-xs text-gray-600">
                                Confidence: {(position.confidence * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <div>
                              <div className="text-xs text-gray-600 mb-1">Position</div>
                              <div className="font-semibold text-sm">
                                {typeof position.position === 'number' 
                                  ? position.position.toFixed(1)
                                  : String(position.position)}
                              </div>
                            </div>

                            <div>
                              <div className="text-xs text-gray-600 mb-1">Key Reasoning</div>
                              <div className="space-y-1">
                                {position.reasoning.map((reason, j) => (
                                  <div key={j} className="text-xs text-gray-700 bg-gray-50 p-2 rounded">
                                    • {reason}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Impact Analysis */}
                  <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-orange-800 dark:text-orange-300">
                        <p className="font-medium mb-1">Disagreement Impact Analysis</p>
                        <p>
                          This {disagreement.conflictLevel} level disagreement has {disagreement.marketImplication} market implications.
                          The {(disagreement.volatility * 100).toFixed(0)}% volatility suggests 
                          {disagreement.volatility > 0.6 ? ' rapidly changing expert opinions' : 
                           disagreement.volatility > 0.4 ? ' moderate position shifts over time' : 
                           ' stable but divergent expert views'}.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredDisagreements.length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500 dark:text-gray-400">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No disagreements found</h3>
            <p className="text-sm">
              No expert disagreements match your current filter criteria.
              Try adjusting the conflict level or time range.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default DisagreementAnalysis;