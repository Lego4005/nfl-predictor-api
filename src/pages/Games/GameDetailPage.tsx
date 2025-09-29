import React from 'react'
import { GAMES, TEAMS } from '../../lib/nfl-data'
import { classNames, eloWinProb } from '../../lib/nfl-utils'
import TeamLogo from '../../components/TeamLogo'

interface GameDetailPageProps {
  gameId: string
  onBack: () => void
}

// Mock games data (this should match the structure from App.tsx)
const mockGames = [
  {
    id: '1',
    homeTeam: 'DET',
    awayTeam: 'SF',
    homeScore: 27,
    awayScore: 20,
    status: 'FINAL' as const,
    network: 'TNF',
    venue: "Levi's Stadium",
    time: '8:20 PM',
    day: 'Thursday Night',
    spread: { open: '+3', current: '+3.5', model: '+2' },
    homeSpread: '+3.5',
    awaySpread: '-3.5'
  },
  {
    id: '2',
    homeTeam: 'KC',
    awayTeam: 'BUF',
    status: 'SCHEDULED' as const,
    network: 'CBS',
    venue: 'GEHA Field at Arrowhead',
    time: '1:00 PM',
    day: 'Sunday Early',
    spread: { open: '+3', current: '+3.5', model: '+2' },
    homeSpread: '+3.5',
    awaySpread: '-3.5',
    pk: 'PK'
  },
  {
    id: '3',
    homeTeam: 'CIN',
    awayTeam: 'BAL',
    status: 'LIVE' as const,
    network: 'CBS',
    venue: 'Paycor Stadium',
    time: '1:00 PM',
    day: 'Sunday Early',
    spread: { open: '+1', current: '+0.5', model: '+0.5' },
    homeSpread: '+0.5',
    awaySpread: '-0.5',
    pk: 'PK',
    homeScore: 14,
    awayScore: 21
  }
]

function GameDetailPage({ gameId, onBack }: GameDetailPageProps) {
  // Find the game data
  const game = mockGames.find(g => g.id === gameId)

  if (!game) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <h2 className="text-lg font-bold text-white mb-2">Game Not Found</h2>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
        >
          Back to Games
        </button>
      </div>
    )
  }

  const homeTeam = TEAMS[game.homeTeam]
  const awayTeam = TEAMS[game.awayTeam]

  // Mock additional game data
  const gameDate = new Date()
  gameDate.setDate(gameDate.getDate() + (game.id === '1' ? -1 : 0))

  const projectedWinner = homeTeam?.elo > awayTeam?.elo ? 'home' : 'away'
  const modelSpread = eloWinProb(homeTeam?.elo || 1500, awayTeam?.elo || 1500)
  const winProbability = (modelSpread * 100).toFixed(1)

  // Mock detailed analytics
  const analytics = {
    homeFieldAdvantage: 65.5,
    baseHFA: 38.4,
    adjustedAdj: 27.1,
    homePerAdj: 120.0,
    awayPerAdj: -72.2,
    surfaceAdj: 12.4,
    timeAdj: 32.7,
    homeQBAdj: 96.3,
    awayQBAdj: -16.9,
    marketRegression: 64.3,
    modelSpreadValue: (Math.random() * 4 + 0.5).toFixed(1)
  }

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-white/10 hover:border-primary/30 transition-colors text-white"
      >
        <span>←</span>
        Back to Games
      </button>

      {/* Game Header */}
      <div className="glass rounded-xl p-6">
        {/* Game Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>📅</span>
              <span>{gameDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })} • {game.time}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>🏠</span>
              <span>{game.venue}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>📅</span>
              <span>Week 3</span>
            </div>
          </div>

          <div className="text-right">
            <span className="inline-block px-3 py-1 rounded-full bg-primary/20 text-primary text-sm font-medium">
              {game.network}
            </span>
          </div>
        </div>

        {/* Team Matchup */}
        <div className="grid grid-cols-3 gap-6 items-center">
          {/* Away Team */}
          <div className="text-center">
            <TeamLogo teamAbbr={game.awayTeam} size="xlarge" className="mx-auto mb-3" />
            <h2 className="text-xl font-bold text-white mb-1">{awayTeam?.name}</h2>
            <p className="text-sm text-muted-foreground">nfelo: {awayTeam?.elo}</p>
            <div className="text-2xl font-bold text-white mt-2">
              {game.awayScore ?? '—'}
            </div>
          </div>

          {/* Game Status */}
          <div className="text-center">
            <div className={classNames(
              "inline-block px-4 py-2 rounded-lg font-bold text-sm mb-2",
              game.status === 'LIVE' ? 'bg-destructive/20 text-destructive' :
                game.status === 'FINAL' ? 'bg-success/20 text-success' :
                  'bg-warning/20 text-warning'
            )}>
              {game.status}
            </div>
            {game.status === 'LIVE' && (
              <div className="text-sm text-muted-foreground">Q3 08:21</div>
            )}
          </div>

          {/* Home Team */}
          <div className="text-center">
            <TeamLogo teamAbbr={game.homeTeam} size="xlarge" className="mx-auto mb-3" />
            <h2 className="text-xl font-bold text-white mb-1">{homeTeam?.name}</h2>
            <p className="text-sm text-muted-foreground">nfelo: {homeTeam?.elo}</p>
            <div className="text-2xl font-bold text-white mt-2">
              {game.homeScore ?? '—'}
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model Predictions */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Model</h3>

          {/* Projected Winner */}
          <div className="mb-6">
            <div className="text-sm text-muted-foreground mb-2">Projected Winner</div>
            <div className="flex items-center gap-3">
              <TeamLogo teamAbbr={projectedWinner === 'home' ? game.homeTeam : game.awayTeam} size="medium" className="" />
              <div>
                <div className="text-white font-medium">
                  {projectedWinner === 'home' ? homeTeam?.name : awayTeam?.name}
                </div>
                <div className="text-sm text-primary">Favored</div>
              </div>
            </div>
          </div>

          {/* Spreads */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Opening</div>
              <div className="text-white font-bold">{game.spread.open}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Current</div>
              <div className="text-white font-bold">{game.spread.current}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Model</div>
              <div className="text-primary font-bold">{analytics.modelSpreadValue}</div>
            </div>
          </div>

          {/* Win Probability */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-white mb-3">Win Probability</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-xs text-muted-foreground">Market</div>
                <div className="text-white font-bold">{winProbability}%</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-muted-foreground">Model</div>
                <div className="text-white font-bold">{winProbability}%</div>
              </div>
            </div>
          </div>

          {/* Spread Risk */}
          <div>
            <h4 className="text-sm font-medium text-white mb-2">Spread Risk</h4>
            <div className="text-sm text-muted-foreground mb-1">No +EV spread bet identified</div>
            <div className="text-xs text-muted-foreground">Model finds no value in current line.</div>
          </div>
        </div>

        {/* Projection Detail */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Projection Detail</h3>

          {/* nfelo Difference */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-white mb-3">nfelo Difference</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Home nfelo</span>
                <span className="text-white">{homeTeam?.elo}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Away nfelo</span>
                <span className="text-white">{awayTeam?.elo}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Home Field</span>
                <span className="text-success">+{analytics.homeFieldAdvantage}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Base HFA</span>
                <span className="text-success">+{analytics.baseHFA}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Adjusted Adj</span>
                <span className="text-success">+{analytics.adjustedAdj}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Home Per Adj</span>
                <span className="text-success">+{analytics.homePerAdj}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Away Per Adj</span>
                <span className="text-destructive">{analytics.awayPerAdj}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Surface Adj</span>
                <span className="text-success">+{analytics.surfaceAdj}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time Adj</span>
                <span className="text-success">+{analytics.timeAdj}</span>
              </div>
            </div>
          </div>

          {/* Net QB Adjustment */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-white mb-3">Net QB Adjustment</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Home QB Adjustment</span>
                <span className="text-success">+{analytics.homeQBAdj}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Away QB Adjustment</span>
                <span className="text-destructive">{analytics.awayQBAdj}</span>
              </div>
            </div>
          </div>

          {/* Market Regression */}
          <div>
            <h4 className="text-sm font-medium text-white mb-2">Market Regression</h4>
            <div className="text-success font-bold">+{analytics.marketRegression}</div>
          </div>
        </div>

        {/* Quarterbacks */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Quarterbacks</h3>

          <div className="space-y-4">
            {/* Away QB */}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
                style={{ backgroundColor: awayTeam?.color || '#666' }}
              >
                QB
              </div>
              <div className="flex-1">
                <div className="text-white font-medium">Away QB</div>
                <div className="grid grid-cols-2 gap-4 mt-1 text-xs">
                  <div>
                    <div className="text-muted-foreground">Proj. Value</div>
                    <div className="text-white font-bold">+10</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Team Elo Adj</div>
                    <div className="text-white font-bold">{(awayTeam?.elo || 1500) - 500}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Home QB */}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
                style={{ backgroundColor: homeTeam?.color || '#666' }}
              >
                QB
              </div>
              <div className="flex-1">
                <div className="text-white font-medium">Home QB</div>
                <div className="grid grid-cols-2 gap-4 mt-1 text-xs">
                  <div>
                    <div className="text-muted-foreground">Proj. Value</div>
                    <div className="text-success font-bold">+185.3</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Team Elo Adj</div>
                    <div className="text-white font-bold">{(homeTeam?.elo || 1500) - 300}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Final Indication */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-white mb-2">Final Indication</h4>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-primary">{analytics.modelSpreadValue}</div>
              <div className="text-sm text-muted-foreground">Model Spread</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GameDetailPage