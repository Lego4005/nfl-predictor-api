import React, { memo, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy, TrendingUp, TrendingDown, Target, Award,
  BarChart3, Calendar, Clock, Star, Users, Zap,
  Filter, Download, Eye, Settings, ArrowUpDown,
  CheckCircle, XCircle, AlertTriangle, Activity
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadialBarChart, RadialBar
} from 'recharts';
import {
  Expert, PredictionPerformanceMetrics, ExpertRanking,
  CategoryStats, PredictionCategory, ConfidenceLevel
} from '../types/predictions';

interface PerformanceMetricsProps {
  experts: Expert[];
  performanceData: PredictionPerformanceMetrics[];
  timeRange?: 'week' | 'month' | 'season' | 'all_time';
  onTimeRangeChange?: (range: 'week' | 'month' | 'season' | 'all_time') => void;
  showLeaderboard?: boolean;
  showTrends?: boolean;
  showCategoryBreakdown?: boolean;
  className?: string;
}

interface MetricCard {
  title: string;
  value: string | number;
  change: number;
  trend: 'up' | 'down' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  format: 'percentage' | 'number' | 'currency' | 'rating';
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = memo(({
  experts,
  performanceData,
  timeRange = 'season',
  onTimeRangeChange,
  showLeaderboard = true,
  showTrends = true,
  showCategoryBreakdown = true,
  className = ''
}) => {
  const [selectedExpert, setSelectedExpert] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'overview' | 'detailed'>('overview');
  const [sortBy, setSortBy] = useState<'accuracy' | 'roi' | 'consistency'>('accuracy');

  // Calculate expert rankings and aggregated metrics
  const expertAnalysis = useMemo(() => {
    const rankings: ExpertRanking[] = experts.map(expert => {
      const performance = performanceData.find(p => p.expert_id === expert.id);
      if (!performance) {
        return {
          ...expert,
          rank: experts.length,
          score: 0
        };
      }

      // Calculate composite score
      const accuracyWeight = 0.4;
      const roiWeight = 0.3;
      const consistencyWeight = 0.3;

      const score = (
        performance.accuracy_metrics.overall_accuracy * accuracyWeight +
        Math.min(performance.betting_metrics.roi / 20, 1) * roiWeight + // Cap ROI at 20%
        performance.trend_analysis.consistency_score * consistencyWeight
      ) * 100;

      return {
        ...expert,
        rank: 0, // Will be set after sorting
        score: Math.round(score)
      };
    }).sort((a, b) => b.score - a.score).map((expert, index) => ({
      ...expert,
      rank: index + 1
    }));

    // Calculate category performance stats
    const categoryStats: CategoryStats = {
      core: { total: 0, accurate: 0, accuracy: 0, average_confidence: 0 },
      props: { total: 0, accurate: 0, accuracy: 0, average_confidence: 0 },
      live: { total: 0, accurate: 0, accuracy: 0, average_confidence: 0 },
      situational: { total: 0, accurate: 0, accuracy: 0, average_confidence: 0 },
      advanced: { total: 0, accurate: 0, accuracy: 0, average_confidence: 0 }
    };

    performanceData.forEach(performance => {
      Object.entries(performance.accuracy_metrics.category_accuracy).forEach(([category, accuracy]) => {
        const cat = category as PredictionCategory;
        if (categoryStats[cat]) {
          categoryStats[cat].total += 100; // Simulated total predictions
          categoryStats[cat].accurate += accuracy * 100;
          categoryStats[cat].accuracy = categoryStats[cat].accurate / categoryStats[cat].total;
        }
      });
    });

    // Calculate aggregated metrics
    const overallAccuracy = performanceData.length > 0
      ? performanceData.reduce((sum, p) => sum + p.accuracy_metrics.overall_accuracy, 0) / performanceData.length
      : 0;

    const overallROI = performanceData.length > 0
      ? performanceData.reduce((sum, p) => sum + p.betting_metrics.roi, 0) / performanceData.length
      : 0;

    const totalPredictions = performanceData.reduce((sum, p) => sum + 100, 0); // Simulated

    return {
      rankings,
      categoryStats,
      overallAccuracy,
      overallROI,
      totalPredictions,
      topPerformer: rankings[0],
      bottomPerformer: rankings[rankings.length - 1]
    };
  }, [experts, performanceData]);

  // Generate metric cards
  const metricCards: MetricCard[] = useMemo(() => [
    {
      title: 'Overall Accuracy',
      value: expertAnalysis.overallAccuracy,
      change: 5.2, // Simulated change
      trend: 'up',
      icon: Target,
      color: 'green',
      format: 'percentage'
    },
    {
      title: 'Average ROI',
      value: expertAnalysis.overallROI,
      change: -1.8, // Simulated change
      trend: 'down',
      icon: TrendingUp,
      color: 'blue',
      format: 'percentage'
    },
    {
      title: 'Total Predictions',
      value: expertAnalysis.totalPredictions,
      change: 12.3, // Simulated change
      trend: 'up',
      icon: BarChart3,
      color: 'purple',
      format: 'number'
    },
    {
      title: 'Active Experts',
      value: experts.length,
      change: 0,
      trend: 'neutral',
      icon: Users,
      color: 'orange',
      format: 'number'
    }
  ], [expertAnalysis, experts.length]);

  // Generate performance trend data
  const trendData = useMemo(() => {
    const weeks = Array.from({ length: 10 }, (_, i) => ({
      week: `Week ${i + 1}`,
      accuracy: 65 + Math.random() * 20,
      roi: -5 + Math.random() * 15,
      predictions: 80 + Math.random() * 40
    }));
    return weeks;
  }, []);

  const formatValue = (value: string | number, format: MetricCard['format']) => {
    if (typeof value === 'number') {
      switch (format) {
        case 'percentage':
          return `${value.toFixed(1)}%`;
        case 'currency':
          return `$${value.toFixed(2)}`;
        case 'rating':
          return `${value.toFixed(1)}/10`;
        default:
          return value.toLocaleString();
      }
    }
    return value;
  };

  const getTrendIcon = (trend: MetricCard['trend'], change: number) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Activity className="w-4 h-4 text-gray-500" />;
  };

  const getPerformanceColor = (accuracy: number) => {
    if (accuracy >= 0.75) return 'text-green-600 dark:text-green-400';
    if (accuracy >= 0.65) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getMomentumIcon = (momentum: string) => {
    switch (momentum) {
      case 'hot': return <Zap className="w-4 h-4 text-orange-500" />;
      case 'warm': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'cold': return <TrendingDown className="w-4 h-4 text-blue-500" />;
      case 'ice_cold': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const LeaderboardTable = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Expert Leaderboard
          </h3>
          <div className="flex items-center space-x-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-1 border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-sm"
            >
              <option value="accuracy">Sort by Accuracy</option>
              <option value="roi">Sort by ROI</option>
              <option value="consistency">Sort by Consistency</option>
            </select>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Rank
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Expert
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Accuracy
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                ROI
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Streak
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Momentum
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Score
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {expertAnalysis.rankings.slice(0, 10).map((expert) => {
              const performance = performanceData.find(p => p.expert_id === expert.id);
              return (
                <motion.tr
                  key={expert.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                  whileHover={{ backgroundColor: 'rgba(59, 130, 246, 0.05)' }}
                  onClick={() => setSelectedExpert(expert.id)}
                >
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {expert.rank <= 3 && (
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 ${
                          expert.rank === 1 ? 'bg-yellow-500' :
                          expert.rank === 2 ? 'bg-gray-400' : 'bg-orange-600'
                        }`}>
                          <span className="text-xs font-bold text-white">{expert.rank}</span>
                        </div>
                      )}
                      {expert.rank > 3 && (
                        <span className="text-sm font-medium text-gray-900 dark:text-white w-6">
                          {expert.rank}
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center mr-3">
                        {expert.avatar ? (
                          <img src={expert.avatar} alt={expert.name} className="w-8 h-8 rounded-full" />
                        ) : (
                          <Users className="w-4 h-4 text-gray-500" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {expert.name}
                          </span>
                          {expert.verified && (
                            <CheckCircle className="w-4 h-4 text-blue-500" />
                          )}
                        </div>
                        <div className="text-xs text-gray-500 capitalize">
                          {expert.type.replace('_', ' ')}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${getPerformanceColor(expert.accuracy_metrics.overall)}`}>
                      {(expert.accuracy_metrics.overall * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {expert.track_record.total_predictions} predictions
                    </div>
                  </td>

                  <td className="px-4 py-4 whitespace-nowrap">
                    {performance && (
                      <div className={`text-sm font-medium ${
                        performance.betting_metrics.roi > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {performance.betting_metrics.roi > 0 ? '+' : ''}{performance.betting_metrics.roi.toFixed(1)}%
                      </div>
                    )}
                  </td>

                  <td className="px-4 py-4 whitespace-nowrap">
                    {performance && (
                      <div className="flex items-center space-x-1">
                        <span className={`text-sm font-medium ${
                          performance.trend_analysis.recent_streak > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {performance.trend_analysis.recent_streak > 0 ? '+' : ''}
                          {performance.trend_analysis.recent_streak}
                        </span>
                      </div>
                    )}
                  </td>

                  <td className="px-4 py-4 whitespace-nowrap">
                    {performance && (
                      <div className="flex items-center space-x-1">
                        {getMomentumIcon(performance.trend_analysis.momentum)}
                        <span className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                          {performance.trend_analysis.momentum.replace('_', ' ')}
                        </span>
                      </div>
                    )}
                  </td>

                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <div className="text-sm font-bold text-gray-900 dark:text-white">
                        {expert.score}
                      </div>
                      {expert.rank <= 5 && (
                        <Star className="w-4 h-4 text-yellow-500" />
                      )}
                    </div>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  const PerformanceTrends = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Performance Trends
        </h3>
        <div className="flex items-center space-x-2">
          {['week', 'month', 'season', 'all_time'].map((range) => (
            <button
              key={range}
              onClick={() => onTimeRangeChange?.(range as any)}
              className={`
                px-3 py-1 text-xs rounded-full transition-colors
                ${timeRange === range
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }
              `}
            >
              {range.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="week" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(31 41 55)',
                border: 'none',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              name="Accuracy %"
            />
            <Line
              type="monotone"
              dataKey="roi"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
              name="ROI %"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const CategoryBreakdown = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        Category Performance
      </h3>

      <div className="space-y-4">
        {Object.entries(expertAnalysis.categoryStats).map(([category, stats]) => (
          <div key={category} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                {category} Predictions
              </span>
              <span className={`text-sm font-bold ${getPerformanceColor(stats.accuracy)}`}>
                {(stats.accuracy * 100).toFixed(1)}%
              </span>
            </div>

            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <motion.div
                className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-green-500"
                initial={{ width: 0 }}
                animate={{ width: `${stats.accuracy * 100}%` }}
                transition={{ duration: 1, delay: 0.2 }}
              />
            </div>

            <div className="flex justify-between text-xs text-gray-500">
              <span>{stats.accurate} correct</span>
              <span>{stats.total} total</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Performance Metrics
          </h2>
          <p className="text-sm text-gray-500">
            Expert performance analysis and tracking
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode(viewMode === 'overview' ? 'detailed' : 'overview')}
            className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-medium"
          >
            {viewMode === 'overview' ? 'Detailed View' : 'Overview'}
          </button>

          <button className="p-2 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:text-gray-700">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricCards.map((metric, index) => (
          <motion.div
            key={metric.title}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -2 }}
          >
            <div className="flex items-center justify-between">
              <div className={`p-2 rounded-lg bg-${metric.color}-100 dark:bg-${metric.color}-900/30`}>
                <metric.icon className={`w-5 h-5 text-${metric.color}-600 dark:text-${metric.color}-400`} />
              </div>
              {getTrendIcon(metric.trend, metric.change)}
            </div>

            <div className="mt-4">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatValue(metric.value, metric.format)}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {metric.title}
              </div>
              <div className={`text-xs mt-1 ${
                metric.trend === 'up' ? 'text-green-600' :
                metric.trend === 'down' ? 'text-red-600' : 'text-gray-500'
              }`}>
                {metric.change !== 0 && (
                  <>
                    {metric.change > 0 ? '+' : ''}{metric.change.toFixed(1)}% from last {timeRange}
                  </>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leaderboard */}
        {showLeaderboard && (
          <div className="lg:col-span-2">
            <LeaderboardTable />
          </div>
        )}

        {/* Category Breakdown */}
        {showCategoryBreakdown && (
          <div>
            <CategoryBreakdown />
          </div>
        )}
      </div>

      {/* Performance Trends */}
      {showTrends && (
        <PerformanceTrends />
      )}
    </div>
  );
});

PerformanceMetrics.displayName = 'PerformanceMetrics';

export default PerformanceMetrics;