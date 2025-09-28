import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Brain, TrendingUp, Target, Award, Zap,
  CheckCircle, XCircle, AlertTriangle, BarChart3,
  Calendar, TrendingDown
} from 'lucide-react';

const ModelPerformance = () => {
  // Mock performance data
  const performanceData = {
    overall: {
      accuracy: 73.2,
      lastWeek: 71.8,
      trend: 'up',
      totalPredictions: 487,
      correct: 356,
      pending: 12,
      roi: 14.7
    },
    categories: [
      { name: 'Spread', accuracy: 68.5, count: 156, trend: 'up', best: 'Home Favorites' },
      { name: 'Totals', accuracy: 71.3, count: 145, trend: 'down', best: 'Unders in Wind' },
      { name: 'Moneyline', accuracy: 82.1, count: 186, trend: 'steady', best: 'Road Dogs' }
    ],
    recentPicks: [
      { game: 'KC @ BUF', pick: 'KC -3.5', result: 'win', confidence: 87, actual: 'KC 27-24' },
      { game: 'DAL @ PHI', pick: 'Over 48.5', result: 'loss', confidence: 65, actual: '45 total' },
      { game: 'GB @ CHI', pick: 'GB ML', result: 'win', confidence: 78, actual: 'GB 24-17' },
      { game: 'SF @ SEA', pick: 'Under 44', result: 'win', confidence: 72, actual: '38 total' },
      { game: 'MIA @ NYJ', pick: 'MIA -7', result: 'pending', confidence: 69, actual: 'TBD' }
    ],
    strengths: [
      { category: 'Home Underdogs', winRate: 78.3, sample: 46 },
      { category: 'Division Games', winRate: 75.2, sample: 89 },
      { category: 'Prime Time Unders', winRate: 73.8, sample: 42 }
    ],
    weaknesses: [
      { category: 'Road Favorites -7+', winRate: 45.2, sample: 31 },
      { category: 'Weather Games', winRate: 52.1, sample: 48 },
      { category: 'Backup QB Starts', winRate: 48.9, sample: 27 }
    ],
    historical: [
      { week: 'Week 1', accuracy: 72.5, roi: 12.3 },
      { week: 'Week 2', accuracy: 69.8, roi: 8.7 },
      { week: 'Week 3', accuracy: 75.2, roi: 18.4 },
      { week: 'Week 4', accuracy: 71.6, roi: 10.2 },
      { week: 'Week 5', accuracy: 74.3, roi: 15.6 },
      { week: 'Week 6', accuracy: 73.2, roi: 14.7 }
    ]
  };

  const getResultIcon = (result) => {
    if (result === 'win') return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (result === 'loss') return <XCircle className="w-4 h-4 text-red-500" />;
    return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600 dark:text-green-400';
    if (confidence >= 70) return 'text-blue-600 dark:text-blue-400';
    if (confidence >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getTrendArrow = (trend) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <BarChart3 className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Main Performance Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              <CardTitle>ML Model Performance</CardTitle>
            </div>
            <Badge className="bg-purple-600 text-white">
              Neural Net v2.4
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Overall Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-center p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 dark:from-green-500/20 dark:to-emerald-500/20 rounded-lg"
            >
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {performanceData.overall.accuracy}%
              </div>
              <div className="text-sm text-muted-foreground">Overall Accuracy</div>
              <div className="text-xs mt-1 flex items-center justify-center gap-1">
                {performanceData.overall.trend === 'up' ? 
                  <TrendingUp className="w-3 h-3 text-green-500" /> : 
                  <TrendingDown className="w-3 h-3 text-red-500" />
                }
                {Math.abs(performanceData.overall.accuracy - performanceData.overall.lastWeek).toFixed(1)}% from last week
              </div>
            </motion.div>

            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-center p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 rounded-lg"
            >
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {performanceData.overall.correct}/{performanceData.overall.totalPredictions}
              </div>
              <div className="text-sm text-muted-foreground">Correct Predictions</div>
              <div className="text-xs mt-1">
                {performanceData.overall.pending} pending
              </div>
            </motion.div>

            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-center p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 rounded-lg"
            >
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                +{performanceData.overall.roi}%
              </div>
              <div className="text-sm text-muted-foreground">ROI This Season</div>
              <div className="text-xs mt-1">
                $1,470 profit per $10k
              </div>
            </motion.div>
          </div>

          {/* Category Performance */}
          <div className="space-y-4 mb-6">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Performance by Category
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {performanceData.categories.map((cat, index) => (
                <motion.div
                  key={cat.name}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">{cat.name}</h4>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-muted-foreground">
                        {cat.count} picks
                      </span>
                      {getTrendArrow(cat.trend)}
                    </div>
                  </div>
                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Accuracy</span>
                      <span className="font-semibold">{cat.accuracy}%</span>
                    </div>
                    <Progress value={cat.accuracy} className="h-2" />
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Best: {cat.best}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Recent Picks */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Recent Predictions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {performanceData.recentPicks.map((pick, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getResultIcon(pick.result)}
                    <div>
                      <div className="text-sm font-medium">{pick.game}</div>
                      <div className="text-xs text-muted-foreground">{pick.pick}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-bold ${getConfidenceColor(pick.confidence)}`}>
                      {pick.confidence}%
                    </div>
                    <div className="text-xs text-muted-foreground">{pick.actual}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strengths and Weaknesses */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5 text-green-500" />
              Model Strengths
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {performanceData.strengths.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded">
                <span className="font-medium">{item.category}</span>
                <div className="flex items-center gap-3">
                  <Badge className="bg-green-600 text-white text-xs">
                    {item.winRate}%
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    ({item.sample} games)
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Areas to Avoid
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {performanceData.weaknesses.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded">
                <span className="font-medium">{item.category}</span>
                <div className="flex items-center gap-3">
                  <Badge className="bg-red-600 text-white text-xs">
                    {item.winRate}%
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    ({item.sample} games)
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Historical Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Historical Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between text-sm font-medium">
              <span>Week</span>
              <span>Accuracy</span>
              <span>ROI</span>
            </div>
            {performanceData.historical.map((week, index) => (
              <div key={index} className="flex items-center gap-4">
                <span className="w-16">{week.week}</span>
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span>{week.accuracy}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full" 
                      style={{ width: `${week.accuracy}%` }}
                    />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span>+{week.roi}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: `${Math.min(100, week.roi + 50)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelPerformance;