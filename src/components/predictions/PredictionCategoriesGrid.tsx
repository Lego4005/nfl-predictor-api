import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Grid, Filter, Search, BarChart3, 
  TrendingUp, Users, Target, Zap,
  ChevronDown, ChevronRight, Settings
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/tabs';
import GameOutcomePanel from './GameOutcomePanel';
import BettingMarketsPanel from './BettingMarketsPanel';
import LiveScenariosPanel from './LiveScenariosPanel';
import PlayerPropsPanel from './PlayerPropsPanel';
import SituationalAnalysisPanel from './SituationalAnalysisPanel';
import type { 
  PredictionCategoriesGridProps,
  CategoryDisplayConfig,
  PredictionCategoryGroup
} from '../../types/aiCouncil';

const PredictionCategoriesGrid: React.FC<PredictionCategoriesGridProps> = ({
  expertPredictions,
  consensusResults,
  activeCategoryFilter,
  onCategorySelect,
  showConfidenceIndicators
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'category' | 'confidence' | 'agreement' | 'expert_count'>('category');
  const [expandedGroups, setExpandedGroups] = useState<Set<PredictionCategoryGroup>>(new Set(['game_outcome']));
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'compact'>('grid');

  // Category group configurations
  const categoryConfigs: CategoryDisplayConfig[] = [
    {
      group: 'game_outcome',
      displayPriority: 'high',
      cardSize: 'large',
      categories: [
        'game_winner', 'final_score', 'margin_of_victory', 
        'first_half_winner', 'second_half_winner', 'quarter_winners',
        'exact_score', 'shutout_probability'
      ],
      defaultExpanded: true
    },
    {
      group: 'betting_markets',
      displayPriority: 'high',
      cardSize: 'medium',
      categories: [
        'point_spread', 'total_over_under', 'moneyline',
        'first_half_spread', 'first_half_total', 'quarter_lines',
        'live_spread', 'live_total', 'prop_bet_lines'
      ],
      defaultExpanded: false
    },
    {
      group: 'live_scenarios',
      displayPriority: 'medium',
      cardSize: 'medium',
      categories: [
        'next_score', 'next_touchdown', 'next_field_goal',
        'drive_result', 'momentum_shift', 'comeback_probability',
        'live_win_probability', 'score_prediction_live'
      ],
      defaultExpanded: false
    },
    {
      group: 'player_props',
      displayPriority: 'medium',
      cardSize: 'compact',
      categories: [
        'passing_yards', 'passing_touchdowns', 'rushing_yards', 
        'rushing_touchdowns', 'receiving_yards', 'receiving_touchdowns',
        'field_goals_made', 'extra_points', 'defensive_sacks', 'interceptions'
      ],
      defaultExpanded: false
    },
    {
      group: 'situational_analysis',
      displayPriority: 'low',
      cardSize: 'compact',
      categories: [
        'weather_impact', 'injury_impact', 'travel_fatigue',
        'rest_advantage', 'coaching_edge', 'home_field_advantage'
      ],
      defaultExpanded: false
    }
  ];

  // Calculate statistics for each category group
  const groupStats = useMemo(() => {
    const stats: Record<PredictionCategoryGroup, {
      totalPredictions: number;
      avgConfidence: number;
      avgAgreement: number;
      expertCount: number;
    }> = {} as any;

    categoryConfigs.forEach(config => {
      const groupPredictions = expertPredictions.flatMap(ep => 
        ep.predictions.filter(p => 
          config.categories.some(cat => p.categoryId.includes(cat))
        )
      );

      const groupConsensus = consensusResults.filter(cr =>
        config.categories.some(cat => cr.categoryId.includes(cat))
      );

      stats[config.group] = {
        totalPredictions: groupPredictions.length,
        avgConfidence: groupPredictions.length > 0 
          ? groupPredictions.reduce((sum, p) => sum + p.confidence, 0) / groupPredictions.length 
          : 0,
        avgAgreement: groupConsensus.length > 0
          ? groupConsensus.reduce((sum, c) => sum + c.agreement, 0) / groupConsensus.length
          : 0,
        expertCount: new Set(groupPredictions.map(p => p.categoryId)).size
      };
    });

    return stats;
  }, [expertPredictions, consensusResults, categoryConfigs]);

  // Filter categories based on search term and active filter
  const filteredConfigs = useMemo(() => {
    let filtered = categoryConfigs;

    if (activeCategoryFilter !== 'all') {
      filtered = filtered.filter(config => config.group === activeCategoryFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(config => 
        config.group.toLowerCase().includes(searchTerm.toLowerCase()) ||
        config.categories.some(cat => 
          cat.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    return filtered;
  }, [categoryConfigs, activeCategoryFilter, searchTerm]);

  const toggleGroupExpansion = (group: PredictionCategoryGroup) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(group)) {
      newExpanded.delete(group);
    } else {
      newExpanded.add(group);
    }
    setExpandedGroups(newExpanded);
  };

  const getGroupIcon = (group: PredictionCategoryGroup) => {
    const icons = {
      game_outcome: Target,
      betting_markets: BarChart3,
      live_scenarios: Zap,
      player_props: Users,
      situational_analysis: TrendingUp
    };
    return icons[group] || Grid;
  };

  const getGroupColor = (group: PredictionCategoryGroup) => {
    const colors = {
      game_outcome: 'from-blue-500 to-blue-600',
      betting_markets: 'from-green-500 to-green-600',
      live_scenarios: 'from-red-500 to-red-600',
      player_props: 'from-purple-500 to-purple-600',
      situational_analysis: 'from-yellow-500 to-yellow-600'
    };
    return colors[group] || 'from-gray-500 to-gray-600';
  };

  const getGroupDisplayName = (group: PredictionCategoryGroup) => {
    const names = {
      game_outcome: 'Game Outcome',
      betting_markets: 'Betting Markets',
      live_scenarios: 'Live Scenarios',
      player_props: 'Player Props',
      situational_analysis: 'Situational Analysis'
    };
    return names[group] || group.replace('_', ' ');
  };

  return (
    <div className="w-full space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Prediction Categories
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            Comprehensive analysis across 27+ prediction categories
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="category">Sort by Category</option>
            <option value="confidence">Sort by Confidence</option>
            <option value="agreement">Sort by Agreement</option>
            <option value="expert_count">Sort by Expert Count</option>
          </select>

          <div className="flex rounded-md border border-gray-300 dark:border-gray-600">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-r-none"
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-none border-x"
            >
              <Filter className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'compact' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('compact')}
              className="rounded-l-none"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {filteredConfigs.map(config => {
          const stats = groupStats[config.group];
          const IconComponent = getGroupIcon(config.group);
          
          return (
            <Card key={config.group} className="p-4">
              <div className="text-center">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${getGroupColor(config.group)} flex items-center justify-center mx-auto mb-2`}>
                  <IconComponent className="h-5 w-5 text-white" />
                </div>
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {stats.totalPredictions}
                </div>
                <div className="text-xs text-gray-500 mb-1">
                  {getGroupDisplayName(config.group)}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-300">
                  {(stats.avgConfidence * 100).toFixed(0)}% avg confidence
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Category Groups */}
      <div className="space-y-6">
        <AnimatePresence>
          {filteredConfigs.map((config, index) => {
            const isExpanded = expandedGroups.has(config.group);
            const stats = groupStats[config.group];
            const IconComponent = getGroupIcon(config.group);

            return (
              <motion.div
                key={config.group}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="overflow-hidden">
                  {/* Group Header */}
                  <CardHeader 
                    className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => toggleGroupExpansion(config.group)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg bg-gradient-to-r ${getGroupColor(config.group)}`}>
                          <IconComponent className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <CardTitle className="text-xl">
                            {getGroupDisplayName(config.group)}
                          </CardTitle>
                          <p className="text-sm text-gray-600 dark:text-gray-300">
                            {config.categories.length} categories • {stats.expertCount} predictions
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-sm font-semibold text-gray-900 dark:text-white">
                            {(stats.avgConfidence * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500">Confidence</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold text-gray-900 dark:text-white">
                            {(stats.avgAgreement * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500">Agreement</div>
                        </div>
                        {isExpanded ? 
                          <ChevronDown className="h-5 w-5 text-gray-400" /> : 
                          <ChevronRight className="h-5 w-5 text-gray-400" />
                        }
                      </div>
                    </div>
                  </CardHeader>

                  {/* Group Content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <CardContent className="pt-0">
                          {config.group === 'game_outcome' && (
                            <GameOutcomePanel
                              predictions={expertPredictions}
                              consensus={consensusResults}
                              categories={config.categories}
                              onCategorySelect={onCategorySelect}
                              viewMode={viewMode}
                            />
                          )}
                          
                          {config.group === 'betting_markets' && (
                            <BettingMarketsPanel
                              predictions={expertPredictions}
                              consensus={consensusResults}
                              categories={config.categories}
                              onCategorySelect={onCategorySelect}
                              viewMode={viewMode}
                            />
                          )}
                          
                          {config.group === 'live_scenarios' && (
                            <LiveScenariosPanel
                              predictions={expertPredictions}
                              consensus={consensusResults}
                              categories={config.categories}
                              onCategorySelect={onCategorySelect}
                              viewMode={viewMode}
                            />
                          )}
                          
                          {config.group === 'player_props' && (
                            <PlayerPropsPanel
                              predictions={expertPredictions}
                              consensus={consensusResults}
                              categories={config.categories}
                              onCategorySelect={onCategorySelect}
                              viewMode={viewMode}
                            />
                          )}
                          
                          {config.group === 'situational_analysis' && (
                            <SituationalAnalysisPanel
                              predictions={expertPredictions}
                              consensus={consensusResults}
                              categories={config.categories}
                              onCategorySelect={onCategorySelect}
                              viewMode={viewMode}
                            />
                          )}
                        </CardContent>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredConfigs.length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500 dark:text-gray-400">
            <Grid className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No categories found</h3>
            <p className="text-sm">
              No prediction categories match your current filters. Try adjusting your search terms.
            </p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => {
                setSearchTerm('');
                setActiveCategoryFilter('all');
              }}
            >
              Clear Filters
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PredictionCategoriesGrid;