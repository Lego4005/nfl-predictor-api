import React, { useState } from 'react'
import { classNames } from '@/lib/nfl-utils'

function PerformancePage() {
  const [selectedSeason, setSelectedSeason] = useState('2024')
  const [selectedTimeframe, setSelectedTimeframe] = useState('season')
  const [selectedBetType, setSelectedBetType] = useState('all')

  // Mock performance data
  const performanceData = {
    overall: {
      accuracy: 68.7,
      totalPicks: 287,
      correctPicks: 197,
      roi: 15.3,
      sharpeRatio: 1.42,
      maxDrawdown: -8.7,
      avgEdge: 2.8,
      profitLoss: 153.4
    },
    byBetType: {
      spread: { accuracy: 69.2, roi: 12.4, count: 156 },
      total: { accuracy: 65.8, roi: 18.7, count: 89 },
      moneyline: { accuracy: 71.4, roi: 9.8, count: 42 }
    },
    recentForm: {
      last10: { wins: 7, losses: 3, accuracy: 70.0 },
      last20: { wins: 13, losses: 7, accuracy: 65.0 },
      last50: { wins: 34, losses: 16, accuracy: 68.0 }
    },
    monthlyPerformance: [
      { month: 'Sep', accuracy: 72.5, roi: 18.2, games: 64 },
      { month: 'Oct', accuracy: 66.8, roi: 14.1, games: 68 },
      { month: 'Nov', accuracy: 71.2, roi: 16.7, games: 72 },
      { month: 'Dec', accuracy: 64.3, roi: 11.8, games: 58 },
      { month: 'Jan', accuracy: 69.1, roi: 13.4, games: 25 }
    ]
  }

  // Recent predictions with detailed tracking
  const recentPredictions = [
    {
      id: 1,
      date: '2024-01-20',
      game: 'KC @ BUF',
      pick: 'BUF +3.5',
      betType: 'Spread',
      confidence: 87,
      edge: 3.2,
      odds: -110,
      result: 'WIN',
      actualMargin: 7,
      profit: 2.1
    },
    {
      id: 2,
      date: '2024-01-20',
      game: 'DAL @ SF',
      pick: 'UNDER 47.5',
      betType: 'Total',
      confidence: 73,
      edge: 1.8,
      odds: -115,
      result: 'WIN',
      actualTotal: 41,
      profit: 1.7
    },
    {
      id: 3,
      date: '2024-01-19',
      game: 'BAL @ HOU',
      pick: 'BAL -9.5',
      betType: 'Spread',
      confidence: 81,
      edge: 2.4,
      odds: -108,
      result: 'LOSS',
      actualMargin: 6,
      profit: -2.0
    },
    {
      id: 4,
      date: '2024-01-19',
      game: 'DET @ TB',
      pick: 'DET ML',
      betType: 'Moneyline',
      confidence: 65,
      edge: 1.2,
      odds: +145,
      result: 'WIN',
      actualMargin: 17,
      profit: 2.9
    },
    {
      id: 5,
      date: '2024-01-18',
      game: 'GB @ SF',
      pick: 'OVER 51.5',
      betType: 'Total',
      confidence: 79,
      edge: 2.1,
      odds: -105,
      result: 'LOSS',
      actualTotal: 48,
      profit: -2.0
    }
  ]

  const filteredPredictions = selectedBetType === 'all'
    ? recentPredictions
    : recentPredictions.filter(p => p.betType.toLowerCase() === selectedBetType)

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">📊 Model Performance</h1>
          <p className="text-sm text-muted-foreground mt-1">Comprehensive AI model analytics and prediction tracking</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        <select
          value={selectedSeason}
          onChange={(e) => setSelectedSeason(e.target.value)}
          className="px-3 py-2 rounded-lg glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="2024">2024 Season</option>
          <option value="2023">2023 Season</option>
          <option value="2022">2022 Season</option>
        </select>

        <div className="flex items-center gap-2">
          {['season', 'playoffs', 'last30'].map(timeframe => (
            <button
              key={timeframe}
              onClick={() => setSelectedTimeframe(timeframe)}
              className={classNames(
                "px-3 py-1.5 rounded-lg text-sm transition-colors capitalize",
                selectedTimeframe === timeframe ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {timeframe === 'last30' ? 'Last 30 Days' : timeframe}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-success">🎯</span>
            <span className="text-sm text-muted-foreground">Overall Accuracy</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{performanceData.overall.accuracy}%</div>
          <div className="text-xs text-muted-foreground">{performanceData.overall.correctPicks}/{performanceData.overall.totalPicks} picks</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-success">💰</span>
            <span className="text-sm text-muted-foreground">ROI</span>
          </div>
          <div className="text-2xl font-bold text-success">+{performanceData.overall.roi}%</div>
          <div className="text-xs text-muted-foreground">+{performanceData.overall.profitLoss} units</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-warning">📈</span>
            <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{performanceData.overall.sharpeRatio}</div>
          <div className="text-xs text-muted-foreground">Risk-adjusted returns</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-primary">⚡</span>
            <span className="text-sm text-muted-foreground">Avg Edge</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{performanceData.overall.avgEdge}%</div>
          <div className="text-xs text-muted-foreground">Value per pick</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance by Bet Type */}
        <div className="glass rounded-xl p-4">
          <h3 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
            <span className="text-primary">📊</span>
            By Bet Type
          </h3>
          <div className="space-y-3">
            {Object.entries(performanceData.byBetType).map(([type, stats]) => (
              <div key={type} className="p-3 rounded-lg bg-white/5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-foreground font-medium capitalize">{type}</span>
                  <span className="text-sm text-success">+{stats.roi}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{stats.accuracy}% accuracy</span>
                  <span className="text-muted-foreground">{stats.count} picks</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Form */}
        <div className="glass rounded-xl p-4">
          <h3 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
            <span className="text-warning">🔥</span>
            Recent Form
          </h3>
          <div className="space-y-3">
            {Object.entries(performanceData.recentForm).map(([period, stats]) => (
              <div key={period} className="p-3 rounded-lg bg-white/5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-foreground font-medium">{period.replace(/last/, 'Last ')}</span>
                  <span className="text-sm text-success">{stats.accuracy}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-success">{stats.wins}W</span>
                  <span className="text-destructive">{stats.losses}L</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Breakdown */}
        <div className="glass rounded-xl p-4">
          <h3 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
            <span className="text-info">📅</span>
            Monthly Breakdown
          </h3>
          <div className="space-y-2">
            {performanceData.monthlyPerformance.slice(-5).map((month) => (
              <div key={month.month} className="flex items-center justify-between py-2 text-sm">
                <span className="text-foreground">{month.month}</span>
                <div className="flex items-center gap-3">
                  <span className={classNames(
                    "font-medium",
                    month.accuracy > 67 ? 'text-success' : month.accuracy > 60 ? 'text-warning' : 'text-destructive'
                  )}>
                    {month.accuracy}%
                  </span>
                  <span className="text-muted-foreground text-xs">{month.games}g</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Predictions Table */}
      <div className="glass rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-foreground">Recent Predictions</h3>
          <div className="flex items-center gap-2">
            {['all', 'spread', 'total', 'moneyline'].map(type => (
              <button
                key={type}
                onClick={() => setSelectedBetType(type)}
                className={classNames(
                  "px-3 py-1.5 rounded-lg text-sm transition-colors capitalize",
                  selectedBetType === type ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-muted-foreground border-b border-white/10">
                <th className="pb-2">Date</th>
                <th className="pb-2">Game</th>
                <th className="pb-2">Pick</th>
                <th className="pb-2">Confidence</th>
                <th className="pb-2">Edge</th>
                <th className="pb-2">Odds</th>
                <th className="pb-2">Result</th>
                <th className="pb-2 text-right">P/L</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {filteredPredictions.map((pred) => (
                <tr key={pred.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-3 text-muted-foreground">
                    {new Date(pred.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </td>
                  <td className="py-3 text-foreground font-medium">{pred.game}</td>
                  <td className="py-3">
                    <div className="text-foreground">{pred.pick}</div>
                    <div className="text-xs text-muted-foreground">{pred.betType}</div>
                  </td>
                  <td className="py-3">
                    <div className={classNames(
                      "inline-flex px-2 py-1 rounded-full text-xs font-medium",
                      pred.confidence > 80 ? 'bg-success/20 text-success' :
                        pred.confidence > 70 ? 'bg-warning/20 text-warning' : 'bg-muted/20 text-muted-foreground'
                    )}>
                      {pred.confidence}%
                    </div>
                  </td>
                  <td className="py-3 text-primary">{pred.edge}%</td>
                  <td className="py-3 text-muted-foreground">{pred.odds > 0 ? '+' : ''}{pred.odds}</td>
                  <td className="py-3">
                    <span className={classNames(
                      "inline-flex px-2 py-1 rounded-full text-xs font-medium",
                      pred.result === 'WIN' ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'
                    )}>
                      {pred.result}
                    </span>
                  </td>
                  <td className={classNames(
                    "py-3 text-right font-medium",
                    pred.profit > 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {pred.profit > 0 ? '+' : ''}{pred.profit.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Risk Management Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-destructive">⚠️</span>
            <span className="text-sm text-muted-foreground">Max Drawdown</span>
          </div>
          <div className="text-2xl font-bold text-destructive">{performanceData.overall.maxDrawdown}%</div>
          <div className="text-xs text-muted-foreground">Worst losing streak</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-success">🎲</span>
            <span className="text-sm text-muted-foreground">Win Rate</span>
          </div>
          <div className="text-2xl font-bold text-success">{((performanceData.overall.correctPicks / performanceData.overall.totalPicks) * 100).toFixed(1)}%</div>
          <div className="text-xs text-muted-foreground">All predictions</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-info">📏</span>
            <span className="text-sm text-muted-foreground">Avg Odds</span>
          </div>
          <div className="text-2xl font-bold text-foreground">-108</div>
          <div className="text-xs text-muted-foreground">Betting efficiency</div>
        </div>
      </div>
    </div>
  )
}

export default PerformancePage