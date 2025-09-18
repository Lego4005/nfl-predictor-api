import React, { memo } from 'react';
import { motion } from 'framer-motion';
import {
  Home, BarChart3, Radio, Target, Brain,
  TrendingUp, Activity, Zap, AlertTriangle
} from 'lucide-react';
import { PredictionCategory } from '../types/predictions';

interface CategoryTabsProps {
  activeCategory: PredictionCategory;
  onCategoryChange: (category: PredictionCategory) => void;
  predictionCounts: Record<PredictionCategory, number>;
  liveGameCount?: number;
  className?: string;
}

interface CategoryConfig {
  id: PredictionCategory;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  color: string;
  gradient: string;
}

const categoryConfigs: CategoryConfig[] = [
  {
    id: 'core',
    label: 'Core Predictions',
    icon: Home,
    description: 'Game winners, spreads, totals, and fundamental outcomes',
    color: 'blue',
    gradient: 'from-blue-500 to-blue-600'
  },
  {
    id: 'props',
    label: 'Player Props',
    icon: BarChart3,
    description: 'Individual player performance predictions and statistics',
    color: 'green',
    gradient: 'from-green-500 to-green-600'
  },
  {
    id: 'live',
    label: 'Live Game',
    icon: Radio,
    description: 'Real-time in-game predictions and momentum shifts',
    color: 'red',
    gradient: 'from-red-500 to-red-600'
  },
  {
    id: 'situational',
    label: 'Situational',
    icon: Target,
    description: 'Context-specific predictions based on game situations',
    color: 'purple',
    gradient: 'from-purple-500 to-purple-600'
  },
  {
    id: 'advanced',
    label: 'Advanced Analytics',
    icon: Brain,
    description: 'Complex metrics and advanced statistical models',
    color: 'orange',
    gradient: 'from-orange-500 to-orange-600'
  }
];

const CategoryTabs: React.FC<CategoryTabsProps> = memo(({
  activeCategory,
  onCategoryChange,
  predictionCounts,
  liveGameCount = 0,
  className = ''
}) => {
  const getCategoryStats = (categoryId: PredictionCategory) => {
    const count = predictionCounts[categoryId] || 0;
    return {
      count,
      hasLive: categoryId === 'live' && liveGameCount > 0,
      isActive: activeCategory === categoryId
    };
  };

  const getTabColorClasses = (config: CategoryConfig, isActive: boolean) => {
    if (isActive) {
      return {
        background: `bg-gradient-to-r ${config.gradient} text-white shadow-lg`,
        border: `border-${config.color}-500`,
        icon: 'text-white',
        count: 'bg-white/20 text-white'
      };
    }

    return {
      background: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
      border: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600',
      icon: `text-${config.color}-500`,
      count: `bg-${config.color}-100 dark:bg-${config.color}-900/30 text-${config.color}-700 dark:text-${config.color}-300`
    };
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Mobile Dropdown */}
      <div className="md:hidden">
        <select
          value={activeCategory}
          onChange={(e) => onCategoryChange(e.target.value as PredictionCategory)}
          className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {categoryConfigs.map((config) => {
            const stats = getCategoryStats(config.id);
            return (
              <option key={config.id} value={config.id}>
                {config.label} ({stats.count})
                {stats.hasLive && ' • LIVE'}
              </option>
            );
          })}
        </select>
      </div>

      {/* Desktop Tabs */}
      <div className="hidden md:block">
        <div className="flex flex-wrap gap-2 p-1 bg-gray-100 dark:bg-gray-900 rounded-xl">
          {categoryConfigs.map((config) => {
            const stats = getCategoryStats(config.id);
            const colorClasses = getTabColorClasses(config, stats.isActive);
            const IconComponent = config.icon;

            return (
              <motion.button
                key={config.id}
                onClick={() => onCategoryChange(config.id)}
                className={`
                  relative flex items-center space-x-3 px-4 py-3 rounded-lg border transition-all duration-200
                  ${colorClasses.background} ${colorClasses.border}
                  min-w-[160px] group
                `}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                layout
              >
                {/* Tab Content */}
                <div className="flex items-center space-x-3 flex-1">
                  <div className={`relative ${colorClasses.icon}`}>
                    <IconComponent className="w-5 h-5" />

                    {/* Live Indicator for Live Category */}
                    {stats.hasLive && config.id === 'live' && (
                      <motion.div
                        className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      >
                        <div className="w-full h-full bg-red-400 rounded-full animate-ping" />
                      </motion.div>
                    )}
                  </div>

                  <div className="flex-1 text-left">
                    <div className="font-medium text-sm">
                      {config.label}
                    </div>
                    <div className="text-xs opacity-75 hidden lg:block">
                      {config.description}
                    </div>
                  </div>

                  {/* Prediction Count Badge */}
                  <div className={`
                    px-2 py-1 rounded-full text-xs font-bold min-w-[2rem] text-center
                    ${colorClasses.count}
                  `}>
                    {stats.count}
                  </div>
                </div>

                {/* Active Indicator */}
                {stats.isActive && (
                  <motion.div
                    className="absolute bottom-0 left-1/2 w-12 h-1 bg-white rounded-full"
                    layoutId="activeTab"
                    initial={false}
                    style={{ x: '-50%' }}
                  />
                )}

                {/* Live Game Count for Live Category */}
                {config.id === 'live' && liveGameCount > 0 && (
                  <motion.div
                    className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full font-bold"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  >
                    {liveGameCount} LIVE
                  </motion.div>
                )}
              </motion.button>
            );
          })}
        </div>

        {/* Category Description */}
        <motion.div
          key={activeCategory}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="mt-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-start space-x-3">
            {(() => {
              const config = categoryConfigs.find(c => c.id === activeCategory);
              if (!config) return null;

              const IconComponent = config.icon;
              return (
                <>
                  <div className={`p-2 rounded-lg bg-gradient-to-r ${config.gradient} text-white`}>
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {config.label}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {config.description}
                    </p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-500">
                      <span>{predictionCounts[activeCategory] || 0} predictions available</span>
                      {activeCategory === 'live' && liveGameCount > 0 && (
                        <span className="flex items-center space-x-1 text-red-600 dark:text-red-400">
                          <Activity className="w-3 h-3" />
                          <span>{liveGameCount} live games</span>
                        </span>
                      )}
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </motion.div>
      </div>

      {/* Quick Stats Bar */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-2">
        {categoryConfigs.map((config) => {
          const count = predictionCounts[config.id] || 0;
          const isActive = activeCategory === config.id;

          return (
            <motion.div
              key={`${config.id}-stat`}
              className={`
                p-3 rounded-lg text-center transition-all duration-200
                ${isActive
                  ? `bg-gradient-to-r ${config.gradient} text-white shadow-md`
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                }
              `}
              whileHover={{ scale: 1.05 }}
            >
              <div className={`text-lg font-bold ${isActive ? 'text-white' : `text-${config.color}-600`}`}>
                {count}
              </div>
              <div className="text-xs opacity-80">
                {config.label.split(' ')[0]}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
});

CategoryTabs.displayName = 'CategoryTabs';

export default CategoryTabs;