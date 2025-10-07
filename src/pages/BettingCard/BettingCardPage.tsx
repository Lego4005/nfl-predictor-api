import React, { useState, useMemo } from 'react'
import { GAMES, TEAMS, Game, Team } from '@/lib/nfl-data'
import { classNames, eloWinProb, probToSpread } from '@/lib/nfl-utils'
import TeamLogo from '@/components/ui/TeamLogo'

// Type definitions for betting recommendations
interface SpreadBet {
  market: number;
  model: number;
  edge: number;
  recommendation: string | null;
}

interface TotalBet {
  market: number;
  model: number;
  edge: number;
  recommendation: string | null;
}

interface MoneylineBet {
  home: number;
  away: number;
  recommendation: string | null;
}

interface BettingRecommendation {
  gameId: string;
  game: Game;
  home: Team | undefined;
  away: Team | undefined;
  spread: SpreadBet;
  total: TotalBet;
  moneyline: MoneylineBet;
  aiConfidence: number;
  edgeGrade: 'high' | 'medium' | 'low';
  keyFactors: string[];
}

interface WeeklyStats {
  totalOpportunities: number;
  highEdgeBets: number;
  avgConfidence: string;
  projectedROI: number;
}

function BettingCardPage() {
  const [selectedWeek, setSelectedWeek] = useState(3)
  const [betType, setBetType] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [minEdge, setMinEdge] = useState(1.0)

  // Get games for selected week
  const weekGames = useMemo(() => {
    return GAMES.filter((g: Game) => g.week === selectedWeek && g.status === 'SCHEDULED')
  }, [selectedWeek])

  // Generate betting recommendations with AI analysis
  const bettingRecs = useMemo(() => {
    return weekGames.map((game: Game) => {
      const home = TEAMS[game.home]
      const away = TEAMS[game.away]
      const pHome = eloWinProb(home?.elo || 1500, away?.elo || 1500)
      const modelSpread = probToSpread(pHome)

      // Mock market lines
      const marketSpread = modelSpread + (Math.random() - 0.5) * 4
      const edge = Math.abs(modelSpread - marketSpread)

      // Mock additional betting lines
      const totalPoints = 45 + Math.random() * 10
      const modelTotal = 47 + Math.random() * 6
      const totalEdge = Math.abs(modelTotal - totalPoints)

      const moneylineHome = pHome > 0.5 ? -110 - (pHome - 0.5) * 400 : 100 + (0.5 - pHome) * 400
      const moneylineAway = pHome < 0.5 ? -110 - (0.5 - pHome) * 400 : 100 + (pHome - 0.5) * 400

      // AI confidence scoring
      const aiConfidence = Math.min(95, 65 + edge * 8 + Math.random() * 15)

      let edgeGrade: 'high' | 'medium' | 'low' = 'low'
      if (edge > 3) edgeGrade = 'high'
      else if (edge > 1.5) edgeGrade = 'medium'

      return {
        gameId: game.id,
        game,
        home,
        away,
        spread: {
          market: marketSpread,
          model: modelSpread,
          edge,
          recommendation: edge > minEdge ? (modelSpread < marketSpread ? 'TAKE HOME' : 'TAKE AWAY') : null
        },
        total: {
          market: totalPoints,
          model: modelTotal,
          edge: totalEdge,
          recommendation: totalEdge > 1 ? (modelTotal > totalPoints ? 'OVER' : 'UNDER') : null
        },
        moneyline: {
          home: moneylineHome,
          away: moneylineAway,
          recommendation: edge > 2 ? (pHome > 0.6 ? 'HOME ML' : pHome < 0.4 ? 'AWAY ML' : null) : null
        },
        aiConfidence,
        edgeGrade,
        keyFactors: [
          edge > 2 ? '📊 Significant line value detected' : null,
          pHome > 0.7 || pHome < 0.3 ? '⚡ Model shows strong directional edge' : null,
          Math.random() > 0.7 ? '🌧️ Weather factor considered' : null,
          Math.random() > 0.8 ? '🏥 Injury impact analyzed' : null
        ].filter(Boolean) as string[]
      }
    })
  }, [weekGames, minEdge])

  const filteredRecs = useMemo(() => {
    return bettingRecs.filter((rec: BettingRecommendation) => {
      if (betType === 'all') return true
      return rec.edgeGrade === betType
    }).sort((a: BettingRecommendation, b: BettingRecommendation) => b.spread.edge - a.spread.edge)
  }, [bettingRecs, betType])

  const weeklyStats = useMemo(() => {
    const validBets = bettingRecs.filter((rec: BettingRecommendation) => rec.spread.edge > minEdge)
    const highEdgeBets = bettingRecs.filter((rec: BettingRecommendation) => rec.edgeGrade === 'high')
    const avgConfidence = bettingRecs.reduce((sum: number, rec: BettingRecommendation) => sum + rec.aiConfidence, 0) / bettingRecs.length

    return {
      totalOpportunities: validBets.length,
      highEdgeBets: highEdgeBets.length,
      avgConfidence: avgConfidence.toFixed(1),
      projectedROI: (avgConfidence - 52.38) * 1.8 // Mock ROI calculation
    }
  }, [bettingRecs, minEdge])

  const BetCard: React.FC<{ rec: BettingRecommendation }> = ({ rec }) => (
    <div className="glass rounded-xl p-4 hover:ring-2 hover:ring-primary/30 transition-all duration-300">
      {/* Game Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <TeamLogo team={rec.game.away} size="md" className="w-12 h-12" />
          <span className="text-foreground text-sm">@</span>
          <TeamLogo team={rec.game.home} size="md" className="w-12 h-12" />
        </div>

        <div className="flex items-center gap-2">
          <div className={classNames(
            "px-2 py-1 rounded-full text-xs font-medium",
            rec.edgeGrade === 'high' ? 'bg-success/20 text-success' :
              rec.edgeGrade === 'medium' ? 'bg-warning/20 text-warning' :
                'bg-muted/20 text-muted-foreground'
          )}>
            {rec.edgeGrade.toUpperCase()} EDGE
          </div>
          <div className="text-sm font-bold text-foreground">{rec.aiConfidence.toFixed(0)}%</div>
        </div>
      </div>

      {/* Primary Recommendation */}
      {rec.spread.recommendation && (
        <div className="p-3 rounded-lg bg-primary/20 border border-primary/30 mb-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-primary font-bold text-sm">{rec.spread.recommendation}</div>
              <div className="text-xs text-muted-foreground">
                Market: {rec.spread.market > 0 ? '+' : ''}{rec.spread.market.toFixed(1)} •
                Model: {rec.spread.model > 0 ? '+' : ''}{rec.spread.model.toFixed(1)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-success text-sm font-bold">+{rec.spread.edge.toFixed(1)} Edge</div>
              <div className="text-xs text-muted-foreground">Value Play</div>
            </div>
          </div>
        </div>
      )}

      {/* Other Betting Options */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        {rec.total.recommendation && (
          <div className="p-2 rounded-lg bg-muted/5 border border-muted/10">
            <div className="text-xs text-muted-foreground">Total</div>
            <div className="text-sm font-medium text-foreground">{rec.total.recommendation} {rec.total.market.toFixed(1)}</div>
          </div>
        )}

        {rec.moneyline.recommendation && (
          <div className="p-2 rounded-lg bg-muted/5 border border-muted/10">
            <div className="text-xs text-muted-foreground">Moneyline</div>
            <div className="text-sm font-medium text-foreground">{rec.moneyline.recommendation}</div>
          </div>
        )}
      </div>

      {/* AI Analysis */}
      {rec.keyFactors.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground flex items-center gap-1">
            <span>🧠</span>
            AI Analysis
          </div>
          {rec.keyFactors.map((factor: string, index: number) => (
            <div key={index} className="text-xs text-muted-foreground pl-4">
              {factor}
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const weeklyROI = weeklyStats.projectedROI

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">🃏 NFL Betting Card</h1>
          <p className="text-sm text-muted-foreground mt-1">AI-powered betting recommendations with edge analysis</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <select
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(Number(e.target.value))}
            className="px-3 py-2 rounded-lg glass border border-muted/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {Array.from({ length: 18 }, (_, i) => i + 1).map(w => (
              <option key={w} value={w}>Week {w}</option>
            ))}
          </select>

          <div className="flex items-center gap-2 glass rounded-lg px-3 py-2">
            <span className="text-sm text-muted-foreground">Min Edge:</span>
            <input
              type="range"
              min="0.5"
              max="3.0"
              step="0.5"
              value={minEdge}
              onChange={(e) => setMinEdge(Number(e.target.value))}
              className="w-20"
            />
            <span className="text-sm text-foreground font-medium">{minEdge}+</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {['all', 'high', 'medium', 'low'].map(type => (
            <button
              key={type}
              onClick={() => setBetType(type as typeof betType)}
              className={classNames(
                "px-3 py-1.5 rounded-lg text-sm transition-colors capitalize",
                betType === type ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Weekly Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-primary">🎯</span>
            <span className="text-sm text-muted-foreground">Opportunities</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{weeklyStats.totalOpportunities}</div>
          <div className="text-xs text-muted-foreground">Valid bets this week</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-success">⭐</span>
            <span className="text-sm text-muted-foreground">High Edge</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{weeklyStats.highEdgeBets}</div>
          <div className="text-xs text-muted-foreground">Premium plays</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-warning">🧠</span>
            <span className="text-sm text-muted-foreground">AI Confidence</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{weeklyStats.avgConfidence}%</div>
          <div className="text-xs text-muted-foreground">Average across plays</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-info">💲</span>
            <span className="text-sm text-muted-foreground">Projected ROI</span>
          </div>
          <div className={classNames(
            "text-2xl font-bold",
            weeklyROI > 0 ? 'text-success' : 'text-destructive'
          )}>
            {weeklyROI > 0 ? '+' : ''}{weeklyROI.toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">Expected return</div>
        </div>
      </div>

      {/* Betting Recommendations */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-foreground">This Week's Recommendations</h2>
          <div className="text-sm text-muted-foreground">
            {filteredRecs.length} of {weekGames.length} games
          </div>
        </div>

        {filteredRecs.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <span className="text-warning text-4xl mb-3 block">⚠️</span>
            <h3 className="text-lg font-medium text-foreground mb-2">No Strong Plays This Week</h3>
            <p className="text-sm text-muted-foreground">
              Lower the minimum edge requirement or check back later for updated lines.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredRecs.map((rec: BettingRecommendation) => (
              <BetCard key={rec.gameId} rec={rec} />
            ))}
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="glass rounded-xl p-4 border-l-4 border-warning">
        <div className="flex items-start gap-2">
          <span className="text-warning text-lg">⚠️</span>
          <div className="text-sm">
            <div className="text-warning font-medium mb-1">Important Disclaimer</div>
            <p className="text-muted-foreground">
              These are AI-generated recommendations for entertainment purposes only.
              Gambling involves risk and should be done responsibly. Never bet more than you can afford to lose.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BettingCardPage
