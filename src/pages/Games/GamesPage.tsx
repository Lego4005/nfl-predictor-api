import React from 'react'
import GameCard from './GameCard'
import GameFilters from './GameFilters'
import WeekNavigation from './WeekNavigation'

// Update Game interface to match the enhanced version
export interface Game {
  id: string
  homeTeam: string
  awayTeam: string
  homeScore?: number
  awayScore?: number
  status: 'SCHEDULED' | 'LIVE' | 'FINAL'
  network: string
  venue: string
  time: string
  gameTime?: Date
  day: string
  dayOrder: number
  spread: {
    open: string
    current: string
    model: string
  }
  homeSpread: string
  awaySpread: string
}

interface GamesPageProps {
  currentWeek: number
  setCurrentWeek: (week: number) => void
  searchTerm: string
  setSearchTerm: (term: string) => void
  statusFilter: string
  setStatusFilter: (filter: string) => void
  weekFilter: string
  setWeekFilter: (filter: string) => void
  viewDensity: string
  setViewDensity: (density: string) => void
  filteredGames: Game[]
  gamesByDay: Record<string, Game[]>
  onGameClick: (gameId: string) => void
}

function GamesPage({
  currentWeek,
  setCurrentWeek,
  searchTerm,
  setSearchTerm,
  statusFilter,
  setStatusFilter,
  weekFilter,
  setWeekFilter,
  viewDensity,
  setViewDensity,
  filteredGames,
  gamesByDay,
  onGameClick
}: GamesPageProps) {
  return (
    <div className="space-y-4 animate-fade-in">
      {/* Week Navigation */}
      <WeekNavigation
        currentWeek={currentWeek}
        setCurrentWeek={setCurrentWeek}
      />

      {/* Filters */}
      <GameFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        weekFilter={weekFilter}
        setWeekFilter={setWeekFilter}
        viewDensity={viewDensity}
        setViewDensity={setViewDensity}
      />

      {/* Games Section - Horizontal by Days, Vertical by Times */}
      <div className="grid grid-cols-1 xl:grid-cols-5 lg:grid-cols-3 md:grid-cols-2 gap-4">
        {Object.entries(gamesByDay).map(([day, games]) => {
          // Extract date from first game's actual date
          const getGameDate = (games: Game[]) => {
            try {
              if (!games.length) return ''
              const firstGame = games[0]
              // Use gameTime if available, otherwise parse time string
              const date = firstGame.gameTime || new Date(firstGame.time)
              if (!date || isNaN(date.getTime())) return ''
              return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            } catch {
              return ''
            }
          }

          const gameDate = getGameDate(games)

          return (
            <div key={day} className="space-y-3">
              <div className="text-center glass border border-border rounded-lg py-2 px-2">
                <h2 className="text-base font-semibold text-foreground">
                  {day}
                </h2>
                {gameDate && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {gameDate}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                {games.map(game => (
                  <GameCard
                    key={game.id}
                    game={game}
                    onGameClick={onGameClick}
                    density={viewDensity as 'compact' | 'cozy' | 'comfortable'}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty State */}
      {Object.keys(gamesByDay).length === 0 && (
        <div className="glass rounded-xl p-8 text-center">
          <span className="text-muted-foreground text-4xl mb-3 block">🔍</span>
          <h3 className="text-lg font-medium text-foreground mb-2">No games found</h3>
          <p className="text-sm text-muted-foreground">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  )
}

export default GamesPage