import React, { memo, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User, Bot, TrendingUp, TrendingDown, Award, Target,
  CheckCircle, XCircle, AlertCircle, Eye, Filter,
  Star, Zap, Brain, BarChart3, Activity, Trophy
} from 'lucide-react';
import { Expert, ComprehensivePrediction, ExpertType, PredictionCategory } from '../types/predictions';

interface ExpertGridProps {
  experts: Expert[];
  predictions: ComprehensivePrediction[];
  selectedExperts: string[];
  onExpertToggle: (expertId: string) => void;
  onExpertSelect: (expertId: string) => void;
  filterCategory?: PredictionCategory;
  sortBy?: 'accuracy' | 'confidence' | 'recent' | 'name';
  viewMode?: 'grid' | 'compact' | 'detailed';
  className?: string;
}

interface ExpertWithStats extends Expert {
  current_predictions: number;
  category_predictions: Record<PredictionCategory, number>;
  recent_accuracy: number;
  hot_streak: number;
  confidence_distribution: Record<string, number>;
  specialization_match: number;
}

const ExpertGrid: React.FC<ExpertGridProps> = memo(({
  experts,
  predictions,
  selectedExperts,
  onExpertToggle,
  onExpertSelect,
  filterCategory,
  sortBy = 'accuracy',
  viewMode = 'grid',
  className = ''
}) => {
  const [showFilters, setShowFilters] = useState(false);
  const [typeFilter, setTypeFilter] = useState<ExpertType | 'all'>('all');
  const [minAccuracy, setMinAccuracy] = useState(0);
  const [showOnlyVerified, setShowOnlyVerified] = useState(false);

  // Calculate expert statistics with predictions
  const expertsWithStats = useMemo((): ExpertWithStats[] => {
    return experts.map(expert => {
      const expertPredictions = predictions.filter(p => p.expert_id === expert.id);
      const categoryPredictions = expertPredictions.filter(p =>
        !filterCategory || p.category === filterCategory
      );

      // Calculate recent accuracy (last 10 predictions)
      const recentPredictions = expertPredictions
        .filter(p => p.is_correct !== undefined)
        .slice(-10);
      const recentAccuracy = recentPredictions.length > 0
        ? recentPredictions.filter(p => p.is_correct).length / recentPredictions.length
        : expert.accuracy_metrics.recent_performance;

      // Calculate hot streak
      let hotStreak = 0;
      const sortedPredictions = expertPredictions
        .filter(p => p.is_correct !== undefined)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

      for (const prediction of sortedPredictions) {
        if (prediction.is_correct) {
          hotStreak++;
        } else {
          break;
        }
      }

      // Calculate confidence distribution
      const confidenceDistribution = {
        very_high: 0,
        high: 0,
        medium: 0,
        low: 0,
        very_low: 0
      };

      categoryPredictions.forEach(p => {
        confidenceDistribution[p.confidence] = (confidenceDistribution[p.confidence] || 0) + 1;
      });

      // Calculate specialization match
      const specializationMatch = filterCategory
        ? expert.specialization.includes(filterCategory) ? 1 : 0.5
        : 1;

      return {
        ...expert,
        current_predictions: categoryPredictions.length,
        category_predictions: categoryPredictions.reduce((acc, p) => {
          acc[p.category] = (acc[p.category] || 0) + 1;
          return acc;
        }, {} as Record<PredictionCategory, number>),
        recent_accuracy: recentAccuracy,
        hot_streak: hotStreak,
        confidence_distribution: confidenceDistribution,
        specialization_match: specializationMatch
      };
    });
  }, [experts, predictions, filterCategory]);

  // Filter and sort experts
  const filteredAndSortedExperts = useMemo(() => {
    let filtered = expertsWithStats.filter(expert => {
      if (typeFilter !== 'all' && expert.type !== typeFilter) return false;
      if (expert.accuracy_metrics.overall < minAccuracy) return false;
      if (showOnlyVerified && !expert.verified) return false;
      return true;
    });

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'accuracy':
          const accuracyA = filterCategory
            ? a.accuracy_metrics.by_category[filterCategory] || 0
            : a.accuracy_metrics.overall;
          const accuracyB = filterCategory
            ? b.accuracy_metrics.by_category[filterCategory] || 0
            : b.accuracy_metrics.overall;
          return accuracyB - accuracyA;

        case 'confidence':
          return b.confidence_calibration - a.confidence_calibration;

        case 'recent':
          return b.recent_accuracy - a.recent_accuracy;

        case 'name':
          return a.name.localeCompare(b.name);

        default:
          return b.accuracy_metrics.overall - a.accuracy_metrics.overall;
      }
    });
  }, [expertsWithStats, typeFilter, minAccuracy, showOnlyVerified, sortBy, filterCategory]);

  const getExpertTypeIcon = (type: ExpertType) => {
    switch (type) {
      case 'ai_model': return Bot;
      case 'human_expert': return User;
      case 'statistical_model': return BarChart3;
      case 'composite': return Brain;
      default: return User;
    }
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.75) return 'text-green-600 dark:text-green-400';
    if (accuracy >= 0.65) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getStreakIcon = (streak: number) => {
    if (streak >= 5) return <Award className="w-4 h-4 text-yellow-500" />;
    if (streak >= 3) return <Trophy className="w-4 h-4 text-orange-500" />;
    if (streak >= 1) return <TrendingUp className="w-4 h-4 text-green-500" />;
    return <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  const ExpertCard = ({ expert }: { expert: ExpertWithStats }) => {
    const isSelected = selectedExperts.includes(expert.id);
    const TypeIcon = getExpertTypeIcon(expert.type);
    const accuracy = filterCategory
      ? expert.accuracy_metrics.by_category[filterCategory] || 0
      : expert.accuracy_metrics.overall;

    if (viewMode === 'compact') {
      return (
        <motion.div
          className={`
            flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-all duration-200
            ${isSelected
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }
            bg-white dark:bg-gray-800
          `}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onExpertToggle(expert.id)}
        >
          <div className="flex-shrink-0">
            {expert.avatar ? (
              <img
                src={expert.avatar}
                alt={expert.name}
                className="w-8 h-8 rounded-full"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                <TypeIcon className="w-4 h-4 text-gray-500" />
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-sm truncate">{expert.name}</h3>
              {expert.verified && <CheckCircle className="w-3 h-3 text-blue-500" />}
            </div>
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <span className={getAccuracyColor(accuracy)}>
                {(accuracy * 100).toFixed(1)}%
              </span>
              <span>{expert.current_predictions} predictions</span>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            {getStreakIcon(expert.hot_streak)}
            <span className="text-xs text-gray-500">{expert.hot_streak}</span>
          </div>
        </motion.div>
      );
    }

    return (
      <motion.div
        className={`
          relative p-4 rounded-xl border transition-all duration-200 cursor-pointer
          ${isSelected
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md'
          }
          bg-white dark:bg-gray-800
        `}
        whileHover={{ y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onExpertToggle(expert.id)}
        layout
      >
        {/* Expert Header */}
        <div className="flex items-start space-x-3 mb-3">
          <div className="flex-shrink-0 relative">
            {expert.avatar ? (
              <img
                src={expert.avatar}
                alt={expert.name}
                className="w-12 h-12 rounded-full"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                <TypeIcon className="w-6 h-6 text-white" />
              </div>
            )}

            {expert.verified && (
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                <CheckCircle className="w-3 h-3 text-white" />
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 dark:text-white truncate">
              {expert.name}
            </h3>
            <p className="text-sm text-gray-500 capitalize">
              {expert.type.replace('_', ' ')}
            </p>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onExpertSelect(expert.id);
            }}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>

        {/* Accuracy Metrics */}
        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Accuracy</span>
            <span className={`text-lg font-bold ${getAccuracyColor(accuracy)}`}>
              {(accuracy * 100).toFixed(1)}%
            </span>
          </div>

          {/* Accuracy Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <motion.div
              className={`h-2 rounded-full ${
                accuracy >= 0.75 ? 'bg-green-500' :
                accuracy >= 0.65 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${accuracy * 100}%` }}
              transition={{ duration: 1, delay: 0.2 }}
            />
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {expert.current_predictions}
            </div>
            <div className="text-xs text-gray-500">Predictions</div>
          </div>

          <div className="text-center">
            <div className="text-lg font-bold text-gray-900 dark:text-white flex items-center justify-center space-x-1">
              {getStreakIcon(expert.hot_streak)}
              <span>{expert.hot_streak}</span>
            </div>
            <div className="text-xs text-gray-500">Hot Streak</div>
          </div>
        </div>

        {/* Specializations */}
        {expert.specialization.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 mb-2">Specializations</div>
            <div className="flex flex-wrap gap-1">
              {expert.specialization.slice(0, 3).map((spec, index) => (
                <span
                  key={index}
                  className={`
                    px-2 py-1 rounded-full text-xs font-medium
                    ${filterCategory === spec
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                    }
                  `}
                >
                  {spec}
                </span>
              ))}
              {expert.specialization.length > 3 && (
                <span className="px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-500">
                  +{expert.specialization.length - 3}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Confidence Distribution */}
        {viewMode === 'detailed' && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 mb-2">Confidence Distribution</div>
            <div className="space-y-1">
              {Object.entries(expert.confidence_distribution).map(([level, count]) => {
                const percentage = expert.current_predictions > 0
                  ? (count / expert.current_predictions) * 100
                  : 0;

                return (
                  <div key={level} className="flex items-center space-x-2">
                    <div className="w-16 text-xs text-gray-500 capitalize">
                      {level.replace('_', ' ')}
                    </div>
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                      <div
                        className="h-1 bg-blue-500 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 w-8 text-right">
                      {count}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Selection Indicator */}
        {isSelected && (
          <motion.div
            className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          >
            <CheckCircle className="w-4 h-4 text-white" />
          </motion.div>
        )}
      </motion.div>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header & Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Expert Predictions ({filteredAndSortedExperts.length})
          </h2>
          <p className="text-sm text-gray-500">
            {selectedExperts.length} experts selected
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`
              p-2 rounded-lg border transition-colors
              ${showFilters
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }
            `}
          >
            <Filter className="w-4 h-4" />
          </button>

          <select
            value={sortBy}
            onChange={(e) => {/* Handle sort change */}}
            className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
          >
            <option value="accuracy">Sort by Accuracy</option>
            <option value="confidence">Sort by Confidence</option>
            <option value="recent">Sort by Recent</option>
            <option value="name">Sort by Name</option>
          </select>
        </div>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Expert Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as ExpertType | 'all')}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                >
                  <option value="all">All Types</option>
                  <option value="ai_model">AI Models</option>
                  <option value="human_expert">Human Experts</option>
                  <option value="statistical_model">Statistical Models</option>
                  <option value="composite">Composite Models</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Minimum Accuracy: {minAccuracy}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={minAccuracy}
                  onChange={(e) => setMinAccuracy(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={showOnlyVerified}
                    onChange={(e) => setShowOnlyVerified(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span>Verified experts only</span>
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Experts Grid */}
      <div className={`
        gap-4
        ${viewMode === 'compact'
          ? 'grid grid-cols-1'
          : viewMode === 'detailed'
            ? 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3'
            : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 sm:flex sm:flex-nowrap sm:overflow-x-auto experts-scroll sm:pb-4 sm:-mx-4 sm:px-4'
        }
      `}>
        <AnimatePresence>
          {filteredAndSortedExperts.map((expert) => (
            <ExpertCard key={expert.id} expert={expert} />
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredAndSortedExperts.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No experts found
          </h3>
          <p className="text-gray-500">
            Try adjusting your filters to see more experts.
          </p>
        </motion.div>
      )}
    </div>
  );
});

ExpertGrid.displayName = 'ExpertGrid';

export default ExpertGrid;