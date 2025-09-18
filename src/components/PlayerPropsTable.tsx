import React, { memo, useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronUp, ChevronDown, Filter, Search, Download,
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  User, Target, BarChart3, Activity, Clock, Star,
  ArrowUpDown, Eye, Settings
} from 'lucide-react';
import { PlayerProp, ComprehensivePrediction, ConfidenceLevel } from '../types/predictions';

interface PlayerPropsTableProps {
  playerProps: PlayerProp[];
  predictions: ComprehensivePrediction[];
  loading?: boolean;
  onPropSelect?: (prop: PlayerProp) => void;
  onBetSelect?: (prop: PlayerProp, betType: 'over' | 'under') => void;
  className?: string;
  virtualScrolling?: boolean;
  itemHeight?: number;
}

interface SortConfig {
  key: keyof PlayerProp | 'expert_consensus' | 'value_rating' | 'recent_form';
  direction: 'asc' | 'desc';
}

interface FilterConfig {
  search: string;
  positions: string[];
  teams: string[];
  statTypes: string[];
  confidenceLevels: ConfidenceLevel[];
  injuryStatus: string[];
  minLine: number;
  maxLine: number;
  valueOnly: boolean;
  recentFormFilter: 'hot' | 'cold' | 'neutral' | 'all';
}

const PlayerPropsTable: React.FC<PlayerPropsTableProps> = memo(({
  playerProps,
  predictions,
  loading = false,
  onPropSelect,
  onBetSelect,
  className = '',
  virtualScrolling = false,
  itemHeight = 80
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'line', direction: 'desc' });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedProps, setSelectedProps] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  const [filters, setFilters] = useState<FilterConfig>({
    search: '',
    positions: [],
    teams: [],
    statTypes: [],
    confidenceLevels: [],
    injuryStatus: [],
    minLine: 0,
    maxLine: 1000,
    valueOnly: false,
    recentFormFilter: 'all'
  });

  // Calculate enhanced player prop data with expert predictions
  const enhancedProps = useMemo(() => {
    return playerProps.map(prop => {
      const propPredictions = predictions.filter(p =>
        p.type.includes(prop.stat_type.toLowerCase()) &&
        p.game_id && // Filter by game if needed
        p.predicted_value !== undefined
      );

      // Calculate expert consensus
      const overPredictions = propPredictions.filter(p =>
        typeof p.predicted_value === 'number' && p.predicted_value > prop.line
      );
      const underPredictions = propPredictions.filter(p =>
        typeof p.predicted_value === 'number' && p.predicted_value < prop.line
      );

      const expertConsensus = {
        over_percentage: propPredictions.length > 0 ? (overPredictions.length / propPredictions.length) * 100 : 0,
        under_percentage: propPredictions.length > 0 ? (underPredictions.length / propPredictions.length) * 100 : 0,
        total_experts: propPredictions.length,
        average_prediction: propPredictions.length > 0
          ? propPredictions.reduce((sum, p) => sum + (typeof p.predicted_value === 'number' ? p.predicted_value : 0), 0) / propPredictions.length
          : prop.line,
        confidence_weighted_average: propPredictions.length > 0
          ? propPredictions.reduce((sum, p) => {
              const weight = p.confidence_score / 100;
              return sum + (typeof p.predicted_value === 'number' ? p.predicted_value * weight : 0);
            }, 0) / propPredictions.reduce((sum, p) => sum + (p.confidence_score / 100), 0)
          : prop.line
      };

      // Calculate value rating
      const impliedProbOverLine = Math.abs(prop.over_odds) / (Math.abs(prop.over_odds) + 100);
      const impliedProbUnderLine = Math.abs(prop.under_odds) / (Math.abs(prop.under_odds) + 100);
      const expertProbOver = expertConsensus.over_percentage / 100;
      const expertProbUnder = expertConsensus.under_percentage / 100;

      const overValue = expertProbOver - impliedProbOverLine;
      const underValue = expertProbUnder - impliedProbUnderLine;
      const bestValue = Math.max(overValue, underValue);

      // Calculate recent form
      const recentGames = prop.recent_form || [];
      const recentAverage = recentGames.length > 0
        ? recentGames.reduce((sum, val) => sum + val, 0) / recentGames.length
        : prop.season_average;

      const formTrend = recentAverage > prop.season_average ? 'hot' :
                       recentAverage < prop.season_average ? 'cold' : 'neutral';

      return {
        ...prop,
        expert_consensus: expertConsensus,
        value_rating: bestValue,
        best_bet: bestValue > 0.05 ? (overValue > underValue ? 'over' : 'under') : null,
        recent_form_average: recentAverage,
        form_trend: formTrend,
        predictions: propPredictions
      };
    });
  }, [playerProps, predictions]);

  // Filter and sort props
  const filteredAndSortedProps = useMemo(() => {
    let filtered = enhancedProps.filter(prop => {
      // Search filter
      if (filters.search && !prop.player_name.toLowerCase().includes(filters.search.toLowerCase()) &&
          !prop.stat_type.toLowerCase().includes(filters.search.toLowerCase()) &&
          !prop.team.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }

      // Position filter
      if (filters.positions.length > 0 && !filters.positions.includes(prop.position)) {
        return false;
      }

      // Team filter
      if (filters.teams.length > 0 && !filters.teams.includes(prop.team)) {
        return false;
      }

      // Stat type filter
      if (filters.statTypes.length > 0 && !filters.statTypes.includes(prop.stat_type)) {
        return false;
      }

      // Injury status filter
      if (filters.injuryStatus.length > 0 && !filters.injuryStatus.includes(prop.injury_status)) {
        return false;
      }

      // Line range filter
      if (prop.line < filters.minLine || prop.line > filters.maxLine) {
        return false;
      }

      // Value only filter
      if (filters.valueOnly && prop.value_rating <= 0.05) {
        return false;
      }

      // Recent form filter
      if (filters.recentFormFilter !== 'all' && prop.form_trend !== filters.recentFormFilter) {
        return false;
      }

      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortConfig.key) {
        case 'expert_consensus':
          aValue = a.expert_consensus.total_experts;
          bValue = b.expert_consensus.total_experts;
          break;
        case 'value_rating':
          aValue = a.value_rating;
          bValue = b.value_rating;
          break;
        case 'recent_form':
          aValue = a.recent_form_average;
          bValue = b.recent_form_average;
          break;
        default:
          aValue = a[sortConfig.key as keyof PlayerProp];
          bValue = b[sortConfig.key as keyof PlayerProp];
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [enhancedProps, filters, sortConfig]);

  const handleSort = useCallback((key: SortConfig['key']) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  const getInjuryStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400';
      case 'questionable': return 'text-yellow-600 dark:text-yellow-400';
      case 'doubtful': return 'text-orange-600 dark:text-orange-400';
      case 'out': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getWeatherImpactIcon = (impact: string) => {
    switch (impact) {
      case 'high': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'medium': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'low': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <CheckCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getFormTrendIcon = (trend: string) => {
    switch (trend) {
      case 'hot': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'cold': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <BarChart3 className="w-4 h-4 text-gray-500" />;
    }
  };

  const SortableHeader = ({
    label,
    sortKey,
    className = ''
  }: {
    label: string;
    sortKey: SortConfig['key'];
    className?: string;
  }) => (
    <th
      className={`px-4 py-3 text-left cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${className}`}
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center space-x-1">
        <span className="font-medium text-gray-700 dark:text-gray-300">{label}</span>
        <ArrowUpDown className="w-3 h-3 text-gray-400" />
        {sortConfig.key === sortKey && (
          <div className="text-blue-500">
            {sortConfig.direction === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </div>
        )}
      </div>
    </th>
  );

  const PlayerPropRow = ({ prop }: { prop: any }) => (
    <motion.tr
      className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      whileHover={{ backgroundColor: 'rgba(59, 130, 246, 0.05)' }}
    >
      {/* Player Info */}
      <td className="px-4 py-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
            <User className="w-5 h-5 text-gray-500" />
          </div>
          <div>
            <div className="font-medium text-gray-900 dark:text-white">
              {prop.player_name}
            </div>
            <div className="text-sm text-gray-500">
              {prop.position} • {prop.team}
            </div>
          </div>
        </div>
      </td>

      {/* Stat Type */}
      <td className="px-4 py-4">
        <div className="font-medium text-gray-900 dark:text-white">
          {prop.stat_type}
        </div>
      </td>

      {/* Line & Odds */}
      <td className="px-4 py-4">
        <div className="text-center">
          <div className="text-lg font-bold text-gray-900 dark:text-white">
            {prop.line}
          </div>
          <div className="flex items-center justify-center space-x-2 text-xs">
            <span className="text-green-600 dark:text-green-400">
              O {prop.over_odds > 0 ? '+' : ''}{prop.over_odds}
            </span>
            <span className="text-red-600 dark:text-red-400">
              U {prop.under_odds > 0 ? '+' : ''}{prop.under_odds}
            </span>
          </div>
        </div>
      </td>

      {/* Expert Consensus */}
      <td className="px-4 py-4">
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span>Over: {prop.expert_consensus.over_percentage.toFixed(1)}%</span>
            <span>{prop.expert_consensus.total_experts} experts</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${prop.expert_consensus.over_percentage}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 text-center">
            Avg: {prop.expert_consensus.average_prediction.toFixed(1)}
          </div>
        </div>
      </td>

      {/* Season Average */}
      <td className="px-4 py-4 text-center">
        <div className="font-medium text-gray-900 dark:text-white">
          {prop.season_average.toFixed(1)}
        </div>
      </td>

      {/* Recent Form */}
      <td className="px-4 py-4">
        <div className="flex items-center space-x-2">
          {getFormTrendIcon(prop.form_trend)}
          <span className="font-medium text-gray-900 dark:text-white">
            {prop.recent_form_average.toFixed(1)}
          </span>
        </div>
      </td>

      {/* Value Rating */}
      <td className="px-4 py-4">
        <div className="flex items-center space-x-2">
          <div className={`
            px-2 py-1 rounded-full text-xs font-bold
            ${prop.value_rating > 0.1 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
              prop.value_rating > 0.05 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' :
              'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }
          `}>
            {prop.value_rating > 0 ? '+' : ''}{(prop.value_rating * 100).toFixed(1)}%
          </div>
          {prop.best_bet && (
            <span className={`
              text-xs font-bold px-2 py-1 rounded
              ${prop.best_bet === 'over' ? 'text-green-600' : 'text-red-600'}
            `}>
              {prop.best_bet.toUpperCase()}
            </span>
          )}
        </div>
      </td>

      {/* Status */}
      <td className="px-4 py-4">
        <div className="flex items-center space-x-2">
          <span className={`text-sm font-medium ${getInjuryStatusColor(prop.injury_status)}`}>
            {prop.injury_status}
          </span>
          {getWeatherImpactIcon(prop.weather_impact)}
        </div>
      </td>

      {/* Actions */}
      <td className="px-4 py-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPropSelect?.(prop)}
            className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
          >
            <Eye className="w-4 h-4" />
          </button>

          {prop.best_bet && (
            <button
              onClick={() => onBetSelect?.(prop, prop.best_bet)}
              className={`
                px-2 py-1 rounded text-xs font-bold transition-colors
                ${prop.best_bet === 'over'
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 hover:bg-green-200'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200'
                }
              `}
            >
              Bet {prop.best_bet}
            </button>
          )}
        </div>
      </td>
    </motion.tr>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header & Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Player Props ({filteredAndSortedProps.length})
          </h2>
          <p className="text-sm text-gray-500">
            Expert predictions and betting value analysis
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search players, stats..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
            />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`
              p-2 rounded-lg border transition-colors
              ${showFilters
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700'
              }
            `}
          >
            <Filter className="w-4 h-4" />
          </button>

          <button
            className="p-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Position
                </label>
                <select
                  multiple
                  value={filters.positions}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    positions: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                >
                  <option value="QB">QB</option>
                  <option value="RB">RB</option>
                  <option value="WR">WR</option>
                  <option value="TE">TE</option>
                  <option value="K">K</option>
                  <option value="DEF">DEF</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Injury Status
                </label>
                <select
                  multiple
                  value={filters.injuryStatus}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    injuryStatus: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                >
                  <option value="healthy">Healthy</option>
                  <option value="questionable">Questionable</option>
                  <option value="doubtful">Doubtful</option>
                  <option value="out">Out</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Recent Form
                </label>
                <select
                  value={filters.recentFormFilter}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    recentFormFilter: e.target.value as any
                  }))}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                >
                  <option value="all">All</option>
                  <option value="hot">Hot</option>
                  <option value="neutral">Neutral</option>
                  <option value="cold">Cold</option>
                </select>
              </div>

              <div>
                <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={filters.valueOnly}
                    onChange={(e) => setFilters(prev => ({ ...prev, valueOnly: e.target.checked }))}
                    className="rounded border-gray-300"
                  />
                  <span>Value bets only</span>
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <SortableHeader label="Player" sortKey="player_name" className="w-48" />
                <SortableHeader label="Stat" sortKey="stat_type" />
                <SortableHeader label="Line/Odds" sortKey="line" />
                <SortableHeader label="Expert Consensus" sortKey="expert_consensus" />
                <SortableHeader label="Season Avg" sortKey="season_average" />
                <SortableHeader label="Recent Form" sortKey="recent_form" />
                <SortableHeader label="Value" sortKey="value_rating" />
                <SortableHeader label="Status" sortKey="injury_status" />
                <th className="px-4 py-3 text-left">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filteredAndSortedProps.map((prop) => (
                  <PlayerPropRow key={`${prop.player_id}-${prop.stat_type}`} prop={prop} />
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {filteredAndSortedProps.length === 0 && (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No player props found
            </h3>
            <p className="text-gray-500">
              Try adjusting your filters to see more props.
            </p>
          </div>
        )}
      </div>
    </div>
  );
});

PlayerPropsTable.displayName = 'PlayerPropsTable';

export default PlayerPropsTable;