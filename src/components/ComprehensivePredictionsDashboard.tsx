import React, { memo, useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Filter, Search, Download, Settings, Bell, BellOff,
  Grid3X3, List, BarChart3, Users, Target, Activity,
  RefreshCw, Maximize2, Minimize2, Eye, Star
} from 'lucide-react';

// Import our new components
import CategoryTabs from './CategoryTabs';
import ExpertGrid from './ExpertGrid';
import PlayerPropsTable from './PlayerPropsTable';
import LiveGameDashboard from './LiveGameDashboard';
import ConfidenceIndicators from './ConfidenceIndicators';
import PerformanceMetrics from './PerformanceMetrics';
import VirtualScrollContainer from './VirtualScrollContainer';

// Import hooks
import { usePredictionUpdates } from '../hooks/useWebSocket';

// Import types
import {
  PredictionCategory, ComprehensivePrediction, Expert, PlayerProp,
  LiveGameData, PredictionPerformanceMetrics, PredictionFilter,
  ExpertConsensus, PredictionSort
} from '../types/predictions';

interface ComprehensivePredictionsDashboardProps {
  className?: string;
}

interface DashboardState {
  activeCategory: PredictionCategory;
  selectedExperts: string[];
  showLiveOnly: boolean;
  expandedView: boolean;
  notificationsEnabled: boolean;
  viewMode: 'grid' | 'list' | 'detailed';
  sortConfig: PredictionSort;
  filters: PredictionFilter;
}

const ComprehensivePredictionsDashboard: React.FC<ComprehensivePredictionsDashboardProps> = memo(({
  className = ''
}) => {
  // Dashboard state
  const [state, setState] = useState<DashboardState>({
    activeCategory: 'core',
    selectedExperts: [],
    showLiveOnly: false,
    expandedView: false,
    notificationsEnabled: true,
    viewMode: 'grid',
    sortConfig: { field: 'confidence_score', direction: 'desc' },
    filters: {
      categories: ['core'],
      experts: [],
      confidence_levels: [],
      prediction_types: [],
      games: [],
      min_confidence: 0,
      max_confidence: 100,
      only_live: false,
      only_unlocked: false,
      has_betting_value: false,
      min_expected_value: 0,
      sort_by: 'confidence',
      sort_direction: 'desc'
    }
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [loading, setLoading] = useState(false);

  // WebSocket connection for real-time updates
  const {
    predictions,
    liveGames,
    realtimeUpdates,
    isConnected,
    isConnecting,
    error: wsError
  } = usePredictionUpdates();

  // Mock data - In a real app, this would come from API
  const [allPredictions] = useState<ComprehensivePrediction[]>([
    // This would be populated with 375+ predictions from API
    ...Array.from({ length: 375 }, (_, i) => ({
      id: `pred-${i}`,
      game_id: `game-${Math.floor(i / 25)}`,
      expert_id: `expert-${i % 15}`,
      category: ['core', 'props', 'live', 'situational', 'advanced'][i % 5] as PredictionCategory,
      type: 'game_winner' as any,
      predicted_value: Math.random() > 0.5,
      confidence: ['very_high', 'high', 'medium', 'low', 'very_low'][Math.floor(Math.random() * 5)] as any,
      confidence_score: 50 + Math.random() * 50,
      implied_probability: 0.5 + Math.random() * 0.3,
      expected_value: -5 + Math.random() * 15,
      reasoning: ['Strong historical performance', 'Favorable matchup', 'Home field advantage'],
      key_factors: ['Offense vs Defense', 'Weather conditions', 'Injury report'],
      historical_context: 'Based on last 5 meetings',
      matchup_analysis: 'Favorable spread',
      last_updated: new Date().toISOString(),
      created_at: new Date().toISOString(),
      live_updates: [],
      is_live: Math.random() > 0.8,
      locked: Math.random() > 0.7,
      tags: ['nfl', 'week15'],
      difficulty_rating: 1 + Math.random() * 9,
      market_movement: []
    }))
  ]);

  const [experts] = useState<Expert[]>([
    ...Array.from({ length: 15 }, (_, i) => ({
      id: `expert-${i}`,
      name: `Expert ${i + 1}`,
      type: ['ai_model', 'human_expert', 'statistical_model', 'composite'][i % 4] as any,
      specialization: [['core'], ['props'], ['live'], ['situational'], ['advanced']][i % 5],
      accuracy_metrics: {
        overall: 0.6 + Math.random() * 0.3,
        by_category: {
          core: 0.6 + Math.random() * 0.3,
          props: 0.6 + Math.random() * 0.3,
          live: 0.6 + Math.random() * 0.3,
          situational: 0.6 + Math.random() * 0.3,
          advanced: 0.6 + Math.random() * 0.3
        },
        by_prediction_type: {},
        recent_performance: 0.6 + Math.random() * 0.3,
        season_performance: 0.6 + Math.random() * 0.3
      },
      confidence_calibration: 0.7 + Math.random() * 0.3,
      track_record: {
        total_predictions: 100 + Math.random() * 500,
        correct_predictions: 60 + Math.random() * 200,
        high_confidence_accuracy: 0.8 + Math.random() * 0.2,
        low_confidence_accuracy: 0.4 + Math.random() * 0.3
      },
      verified: Math.random() > 0.3
    }))
  ]);

  const [playerProps] = useState<PlayerProp[]>([
    ...Array.from({ length: 50 }, (_, i) => ({
      player_id: `player-${i}`,
      player_name: `Player ${i + 1}`,
      position: ['QB', 'RB', 'WR', 'TE', 'K'][i % 5],
      team: ['KC', 'BUF', 'DAL', 'NE', 'SF'][i % 5],
      stat_type: 'passing_yards',
      line: 200 + Math.random() * 200,
      over_odds: -110 + Math.random() * 20,
      under_odds: -110 + Math.random() * 20,
      predictions: [],
      season_average: 180 + Math.random() * 100,
      recent_form: Array.from({ length: 5 }, () => 150 + Math.random() * 150),
      matchup_history: Array.from({ length: 3 }, () => 160 + Math.random() * 120),
      injury_status: ['healthy', 'questionable', 'doubtful', 'out'][Math.floor(Math.random() * 4)] as any,
      weather_impact: ['none', 'low', 'medium', 'high'][Math.floor(Math.random() * 4)] as any
    }))
  ]);

  const [performanceData] = useState<PredictionPerformanceMetrics[]>([
    ...experts.map(expert => ({
      expert_id: expert.id,
      time_period: 'season' as any,
      accuracy_metrics: {
        overall_accuracy: expert.accuracy_metrics.overall,
        category_accuracy: expert.accuracy_metrics.by_category,
        confidence_calibration: {
          very_high: { predicted: 0.9, actual: 0.85 },
          high: { predicted: 0.8, actual: 0.75 },
          medium: { predicted: 0.6, actual: 0.65 },
          low: { predicted: 0.4, actual: 0.45 },
          very_low: { predicted: 0.2, actual: 0.25 }
        }
      },
      betting_metrics: {
        roi: -5 + Math.random() * 20,
        units_won: Math.random() * 50,
        units_bet: 100 + Math.random() * 200,
        win_rate: 0.4 + Math.random() * 0.4,
        average_odds: -110 + Math.random() * 30,
        best_bet_categories: ['core', 'props']
      },
      trend_analysis: {
        recent_streak: -5 + Math.random() * 10,
        momentum: ['hot', 'warm', 'neutral', 'cold', 'ice_cold'][Math.floor(Math.random() * 5)] as any,
        improvement_rate: -10 + Math.random() * 20,
        consistency_score: 0.5 + Math.random() * 0.5
      }
    }))
  ]);

  // Calculate category counts
  const predictionCounts = useMemo(() => {
    return {
      core: allPredictions.filter(p => p.category === 'core').length,
      props: allPredictions.filter(p => p.category === 'props').length,
      live: allPredictions.filter(p => p.category === 'live').length,
      situational: allPredictions.filter(p => p.category === 'situational').length,
      advanced: allPredictions.filter(p => p.category === 'advanced').length
    };
  }, [allPredictions]);

  // Filter predictions based on current state
  const filteredPredictions = useMemo(() => {
    let filtered = allPredictions;

    // Category filter
    if (state.activeCategory) {
      filtered = filtered.filter(p => p.category === state.activeCategory);
    }

    // Expert filter
    if (state.selectedExperts.length > 0) {
      filtered = filtered.filter(p => state.selectedExperts.includes(p.expert_id));
    }

    // Live only filter
    if (state.showLiveOnly) {
      filtered = filtered.filter(p => p.is_live);
    }

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(p =>
        p.reasoning.some(r => r.toLowerCase().includes(searchQuery.toLowerCase())) ||
        p.key_factors.some(f => f.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Confidence filter
    filtered = filtered.filter(p =>
      p.confidence_score >= state.filters.min_confidence &&
      p.confidence_score <= state.filters.max_confidence
    );

    // Sort predictions
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (state.sortConfig.field) {
        case 'confidence_score':
          aValue = a.confidence_score;
          bValue = b.confidence_score;
          break;
        case 'expected_value':
          aValue = a.expected_value;
          bValue = b.expected_value;
          break;
        case 'last_updated':
          aValue = new Date(a.last_updated).getTime();
          bValue = new Date(b.last_updated).getTime();
          break;
        default:
          aValue = a.confidence_score;
          bValue = b.confidence_score;
      }

      if (aValue < bValue) return state.sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return state.sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [allPredictions, state, searchQuery]);

  // Handle category change
  const handleCategoryChange = useCallback((category: PredictionCategory) => {
    setState(prev => ({
      ...prev,
      activeCategory: category,
      filters: { ...prev.filters, categories: [category] }
    }));
  }, []);

  // Handle expert selection
  const handleExpertToggle = useCallback((expertId: string) => {
    setState(prev => ({
      ...prev,
      selectedExperts: prev.selectedExperts.includes(expertId)
        ? prev.selectedExperts.filter(id => id !== expertId)
        : [...prev.selectedExperts, expertId]
    }));
  }, []);

  // Handle refresh
  const handleRefresh = useCallback(async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLastUpdated(new Date());
    setLoading(false);
  }, []);

  // Update filters
  const updateFilters = useCallback((newFilters: Partial<PredictionFilter>) => {
    setState(prev => ({
      ...prev,
      filters: { ...prev.filters, ...newFilters }
    }));
  }, []);

  // Render prediction item for virtual scroll
  const renderPredictionItem = useCallback((prediction: ComprehensivePrediction, index: number, style: React.CSSProperties) => {
    const expert = experts.find(e => e.id === prediction.expert_id);

    return (
      <motion.div
        style={style}
        className="p-4 border-b border-gray-200 dark:border-gray-700"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: index * 0.01 }}
      >
        <div className="flex items-start space-x-4">
          {/* Confidence Indicator */}
          <div className="flex-shrink-0">
            <ConfidenceIndicators
              prediction={prediction}
              expert={expert}
              variant="minimal"
              size="sm"
            />
          </div>

          {/* Prediction Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {prediction.type.replace('_', ' ').toUpperCase()}
              </h3>
              <div className="flex items-center space-x-2">
                {prediction.is_live && (
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-xs text-red-600 dark:text-red-400">LIVE</span>
                  </div>
                )}
                {expert && (
                  <span className="text-xs text-gray-500">{expert.name}</span>
                )}
              </div>
            </div>

            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {prediction.reasoning.slice(0, 2).join(' • ')}
            </div>

            <div className="flex items-center space-x-4 text-xs">
              <span className={`font-medium ${
                prediction.expected_value > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                EV: {prediction.expected_value > 0 ? '+' : ''}{prediction.expected_value.toFixed(1)}%
              </span>
              <span className="text-gray-500">
                Updated: {new Date(prediction.last_updated).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }, [experts]);

  // Get live game count
  const liveGameCount = liveGames.length;

  return (
    <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                NFL Predictions Hub
              </h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-500">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search predictions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 w-64 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* View Mode Toggle */}
              <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                {[
                  { mode: 'grid', icon: Grid3X3 },
                  { mode: 'list', icon: List },
                  { mode: 'detailed', icon: BarChart3 }
                ].map(({ mode, icon: Icon }) => (
                  <button
                    key={mode}
                    onClick={() => setState(prev => ({ ...prev, viewMode: mode as any }))}
                    className={`p-2 rounded transition-colors ${
                      state.viewMode === mode
                        ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow'
                        : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </button>
                ))}
              </div>

              {/* Notifications */}
              <button
                onClick={() => setState(prev => ({ ...prev, notificationsEnabled: !prev.notificationsEnabled }))}
                className={`p-2 rounded-lg transition-colors ${
                  state.notificationsEnabled
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {state.notificationsEnabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
              </button>

              {/* Refresh */}
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>

              {/* Expand Toggle */}
              <button
                onClick={() => setState(prev => ({ ...prev, expandedView: !prev.expandedView }))}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg transition-colors"
              >
                {state.expandedView ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-6">
          {/* Category Navigation */}
          <CategoryTabs
            activeCategory={state.activeCategory}
            onCategoryChange={handleCategoryChange}
            predictionCounts={predictionCounts}
            liveGameCount={liveGameCount}
          />

          {/* Live Games Dashboard */}
          {state.activeCategory === 'live' && (
            <LiveGameDashboard
              liveGames={liveGames}
              livePredictions={filteredPredictions.filter(p => p.is_live)}
              autoRefresh={true}
            />
          )}

          {/* Player Props Table */}
          {state.activeCategory === 'props' && (
            <PlayerPropsTable
              playerProps={playerProps}
              predictions={filteredPredictions}
              loading={loading}
            />
          )}

          {/* Main Predictions View */}
          {state.activeCategory !== 'live' && state.activeCategory !== 'props' && (
            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              {/* Expert Grid */}
              <div className="xl:col-span-1">
                <ExpertGrid
                  experts={experts}
                  predictions={filteredPredictions}
                  selectedExperts={state.selectedExperts}
                  onExpertToggle={handleExpertToggle}
                  onExpertSelect={(expertId) => console.log('View expert details:', expertId)}
                  filterCategory={state.activeCategory}
                  viewMode="compact"
                />
              </div>

              {/* Predictions List */}
              <div className="xl:col-span-3">
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {state.activeCategory.charAt(0).toUpperCase() + state.activeCategory.slice(1)} Predictions
                        <span className="text-sm font-normal text-gray-500 ml-2">
                          ({filteredPredictions.length})
                        </span>
                      </h3>
                      <div className="flex items-center space-x-2">
                        <label className="flex items-center space-x-2 text-sm">
                          <input
                            type="checkbox"
                            checked={state.showLiveOnly}
                            onChange={(e) => setState(prev => ({ ...prev, showLiveOnly: e.target.checked }))}
                            className="rounded border-gray-300"
                          />
                          <span className="text-gray-600 dark:text-gray-400">Live only</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Virtual Scrolled Predictions */}
                  <VirtualScrollContainer
                    items={filteredPredictions}
                    renderItem={renderPredictionItem}
                    itemHeight={120}
                    containerHeight={600}
                    loading={loading}
                    className="h-[600px]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          {state.expandedView && (
            <PerformanceMetrics
              experts={experts}
              performanceData={performanceData}
              timeRange="season"
              showLeaderboard={true}
              showTrends={true}
              showCategoryBreakdown={true}
            />
          )}
        </div>
      </div>

      {/* Real-time Updates Notification */}
      <AnimatePresence>
        {realtimeUpdates.length > 0 && state.notificationsEnabled && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            className="fixed bottom-4 right-4 max-w-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-30"
          >
            <div className="p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="w-4 h-4 text-blue-500" />
                <span className="font-medium text-gray-900 dark:text-white">
                  Live Update
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {realtimeUpdates[0].type.replace('_', ' ')} detected
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

ComprehensivePredictionsDashboard.displayName = 'ComprehensivePredictionsDashboard';

export default ComprehensivePredictionsDashboard;