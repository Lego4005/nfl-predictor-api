import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Brain, TrendingUp, Target, Award, Zap,
  CheckCircle, XCircle, AlertTriangle, BarChart3
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
      pending: 12
    },
    categories: [
      { name: 'Spread', accuracy: 68.5, count: 156, trend: 'up', best: 'Home Favorites' },
      { name: 'Totals', accuracy: 71.3, count: 145, trend: 'down', best: 'Unders in Wind' },
      { name: 'Moneyline', accuracy: 82.1, count: 186, trend: 'steady', best: 'Road Dogs' },
      { name: 'Props', accuracy: 64.7, count: 98, trend: 'up', best: 'QB Passing Yards' }
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
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  return (
    <div className="space-y-4">
      {/* Main Performance Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              <h2 className="text-xl font-bold">ML Model Performance</h2>
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
              className="text-center p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-lg"
            >
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {performanceData.overall.accuracy}%
              </div>
              <div className="text-sm text-muted-foreground">Overall Accuracy</div>
              <div className="text-xs mt-1">
                {performanceData.overall.trend === 'up' ? '↑' : '↓'}
                {Math.abs(performanceData.overall.accuracy - performanceData.overall.lastWeek).toFixed(1)}% from last week
              </div>
            </motion.div>

            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-center p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-lg"
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
              className="text-center p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg"
            >
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                +14.7%
              </div>
              <div className="text-sm text-muted-foreground">ROI This Season</div>
              <div className="text-xs mt-1">
                $1,470 profit per $10k
              </div>
            </motion.div>
          </div>

          {/* Category Performance */}
          <div className="space-y-3 mb-6">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Performance by Category
            </h3>
            {performanceData.categories.map((cat, index) => (
              <motion.div
                key={cat.name}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: index * 0.1 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{cat.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {cat.count} picks
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {cat.accuracy}% {getTrendArrow(cat.trend)}
                    </Badge>
                  </div>
                </div>
                <Progress value={cat.accuracy} className="h-1.5" />
                <div className="text-xs text-muted-foreground">
                  Best: {cat.best}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Recent Picks */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Recent Predictions
            </h3>
            <div className="space-y-2">
              {performanceData.recentPicks.map((pick, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
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
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <h3 className="font-semibold flex items-center gap-2">
              <Award className="w-4 h-4 text-green-500" />
              Model Strengths
            </h3>
          </CardHeader>
          <CardContent className="space-y-2">
            {performanceData.strengths.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-green-50 dark:bg-green-900/20 rounded">
                <span className="text-sm">{item.category}</span>
                <div className="flex items-center gap-2">
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
            <h3 className="font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Areas to Avoid
            </h3>
          </CardHeader>
          <CardContent className="space-y-2">
            {performanceData.weaknesses.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded">
                <span className="text-sm">{item.category}</span>
                <div className="flex items-center gap-2">
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
    </div>
  );
};

export default ModelPerformance;