import React from 'react'
import GameCard, { Game } from './GameCard'
import GameFilters from './GameFilters'
import WeekNavigation from './WeekNavigation'

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
        {Object.entries(gamesByDay).map(([day, games]) => (
          <div key={day} className="space-y-3">
            <h2 className="text-base font-semibold text-foreground text-center glass border border-border rounded-lg py-2 px-2">
              {day}
            </h2>
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
        ))}
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