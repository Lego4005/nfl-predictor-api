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
  return (
    <button
      onClick={() => onGameClick(game.id)}
      className="w-full text-left p-2 rounded-lg glass border border-border hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:shadow-primary/10"
    >
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs text-muted-foreground">{game.time}</span>
        <span className="text-xs text-muted-foreground">{game.network}</span>
      </div>

      <div className="space-y-1">
        {/* Away Team */}
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-1.5">
            <TeamLogo teamAbbr={game.awayTeam} size="small" className="" />
            <span className="font-medium text-foreground text-sm">{game.awayTeam}</span>
            {game.awayScore !== undefined && (
              <span className="text-sm font-bold text-white ml-auto">{game.awayScore}</span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <span className="text-sm font-medium text-muted-foreground">{game.awaySpread}</span>
            {game.pk && <span className="text-xs text-muted-foreground">{game.pk}</span>}
          </div>
        </div>

        {/* Home Team */}
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-1.5">
            <TeamLogo teamAbbr={game.homeTeam} size="small" className="" />
            <span className="font-medium text-foreground text-sm">{game.homeTeam}</span>
            {game.homeScore !== undefined && (
              <span className="text-sm font-bold text-white ml-auto">{game.homeScore}</span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <span className="text-sm font-medium text-muted-foreground">{game.homeSpread}</span>
            {game.pk && <span className="text-xs text-muted-foreground">{game.pk}</span>}
          </div>
        </div>
      </div>

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

      {/* Betting Odds */}
      {game.status === 'SCHEDULED' && (
        <div className="mt-2 flex justify-between text-xs">
          <div className="text-center">
            <div className="text-muted-foreground">Open</div>
            <div className="text-foreground font-medium">{game.spread.open}</div>
          </div>
          <div className="text-center">
            <div className="text-muted-foreground">Current</div>
            <div className="text-foreground font-medium">{game.spread.current}</div>
          </div>
          <div className="text-center">
            <div className="text-muted-foreground">Model</div>
            <div className="text-foreground font-medium">{game.spread.model}</div>
          </div>
        </div>
      )}
    </button>
  )
}

export default GameCard
export type { Game }