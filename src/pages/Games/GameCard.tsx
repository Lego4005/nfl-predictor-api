import React from 'react'
import TeamLogo from '../../components/TeamLogo'

interface Game {
  id: string
  homeTeam: string
  awayTeam: string
  homeScore?: number
  awayScore?: number
  status: 'SCHEDULED' | 'LIVE' | 'FINAL'
  network: string
  venue: string
  time: string
  gameType?: string
  day: string
  spread: {
    open: string
    current: string
    model: string
  }
  homeSpread: string
  awaySpread: string
  pk?: string
}

interface GameCardProps {
  game: Game
  onGameClick: (gameId: string) => void
  density?: 'compact' | 'cozy' | 'comfortable'
}

function GameCard({ game, onGameClick, density = 'compact' }: GameCardProps) {
  // Add visual indicators for game status
  const isLive = game.status === 'LIVE'
  const isFinal = game.status === 'FINAL'

  // Determine winner for completed games
  const awayWon = isFinal && game.awayScore !== undefined && game.homeScore !== undefined && game.awayScore > game.homeScore
  const homeWon = isFinal && game.awayScore !== undefined && game.homeScore !== undefined && game.homeScore > game.awayScore
  const isTie = isFinal && game.awayScore !== undefined && game.homeScore !== undefined && game.awayScore === game.homeScore

  return (
    <button
      onClick={() => onGameClick(game.id)}
      className={`w-full text-left p-3 rounded-lg glass border transition-all duration-200 hover:shadow-lg relative overflow-hidden ${
        isFinal
          ? 'border-green-500/30 hover:border-green-500/50 hover:shadow-green-500/10'
          : 'border-border hover:border-primary/40 hover:shadow-primary/10'
      }`}
    >
      {/* Live indicator pulse */}
      {isLive && (
        <div className="absolute top-2 left-2 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
      )}

      {/* Final game indicator stripe */}
      {isFinal && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-green-500/50 via-green-400/50 to-green-500/50" />
      )}

      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-medium">{game.time}</span>
          {game.gameType && game.gameType !== 'regular' && (
            <span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded">
              {game.gameType}
            </span>
          )}
        </div>
        <span className="text-xs text-muted-foreground bg-secondary/50 px-2 py-0.5 rounded">
          {game.network}
        </span>
      </div>

      <div className="space-y-2">
        {/* Away Team */}
        <div className={`flex justify-between items-center rounded-md px-2 py-1 transition-all ${
          awayWon ? 'bg-green-500/10 ring-1 ring-green-500/30' : isFinal ? 'opacity-60' : ''
        }`}>
          <div className="flex items-center space-x-2 flex-1">
            <TeamLogo teamAbbr={game.awayTeam} size="small" className={awayWon ? 'ring-2 ring-green-400 rounded-full' : ''} />
            <span className={`font-semibold text-sm ${awayWon ? 'text-green-400' : 'text-foreground'}`}>
              {game.awayTeam}
              {awayWon && <span className="ml-1.5 text-xs">✓</span>}
            </span>
            {game.awayScore !== undefined && (
              <span className={`text-base font-bold ml-auto mr-2 ${awayWon ? 'text-green-400' : 'text-foreground'}`}>
                {game.awayScore}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <span className={`text-sm font-medium ${parseFloat(game.awaySpread) < 0 ? 'text-green-400' : parseFloat(game.awaySpread) > 0 ? 'text-red-400' : 'text-muted-foreground'}`}>
              {game.awaySpread}
            </span>
            {game.pk && <span className="text-xs text-muted-foreground">({game.pk})</span>}
          </div>
        </div>

        {/* Home Team */}
        <div className={`flex justify-between items-center rounded-md px-2 py-1 transition-all ${
          homeWon ? 'bg-green-500/10 ring-1 ring-green-500/30' : isFinal ? 'opacity-60' : ''
        }`}>
          <div className="flex items-center space-x-2 flex-1">
            <TeamLogo teamAbbr={game.homeTeam} size="small" className={homeWon ? 'ring-2 ring-green-400 rounded-full' : ''} />
            <span className={`font-semibold text-sm ${homeWon ? 'text-green-400' : 'text-foreground'}`}>
              {game.homeTeam}
              {homeWon && <span className="ml-1.5 text-xs">✓</span>}
            </span>
            {game.homeScore !== undefined && (
              <span className={`text-base font-bold ml-auto mr-2 ${homeWon ? 'text-green-400' : 'text-foreground'}`}>
                {game.homeScore}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <span className={`text-sm font-medium ${parseFloat(game.homeSpread) < 0 ? 'text-green-400' : parseFloat(game.homeSpread) > 0 ? 'text-red-400' : 'text-muted-foreground'}`}>
              {game.homeSpread}
            </span>
            {game.pk && <span className="text-xs text-muted-foreground">({game.pk})</span>}
          </div>
        </div>
      </div>

      {/* Venue Info - Only show when not compact */}
      {density !== 'compact' && game.venue && (
        <div className="mt-2 pt-2 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            📍 {game.venue}
          </p>
        </div>
      )}

      {/* Status Indicator */}
      {game.status === 'LIVE' && (
        <div className="mt-2 flex justify-center">
          <span className="bg-destructive/20 text-destructive text-xs px-2 py-1 rounded-full font-medium">
            LIVE
          </span>
        </div>
      )}

      {game.status === 'FINAL' && (
        <div className="mt-2 flex justify-center">
          <span className="bg-success/20 text-success text-xs px-2 py-1 rounded-full font-medium">
            FINAL
          </span>
        </div>
      )}

      {/* Betting Odds - Enhanced display */}
      {game.status === 'SCHEDULED' && density !== 'compact' && (
        <div className="mt-3 pt-2 border-t border-border/50">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-muted-foreground font-medium">Spread Movement</span>
            {game.spread.open !== game.spread.current && (
              <span className={`text-xs ${parseFloat(game.spread.current) < parseFloat(game.spread.open) ? 'text-green-400' : 'text-red-400'}`}>
                {parseFloat(game.spread.current) < parseFloat(game.spread.open) ? '↓' : '↑'}
              </span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-1 text-xs">
            <div className="text-center bg-secondary/30 rounded px-1 py-0.5">
              <div className="text-muted-foreground text-[10px]">Open</div>
              <div className="text-foreground font-medium">{game.spread.open}</div>
            </div>
            <div className="text-center bg-primary/20 rounded px-1 py-0.5">
              <div className="text-muted-foreground text-[10px]">Current</div>
              <div className="text-foreground font-bold">{game.spread.current}</div>
            </div>
            <div className="text-center bg-secondary/30 rounded px-1 py-0.5">
              <div className="text-muted-foreground text-[10px]">Model</div>
              <div className="text-foreground font-medium">{game.spread.model}</div>
            </div>
          </div>
        </div>
      )}

      {/* Compact betting display */}
      {game.status === 'SCHEDULED' && density === 'compact' && (
        <div className="mt-2 flex justify-center">
          <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded font-medium">
            Line: {game.spread.current}
          </span>
        </div>
      )}
    </button>
  )
}

export default GameCard
export type { Game }