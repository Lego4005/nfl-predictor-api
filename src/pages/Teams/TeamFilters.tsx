import React from 'react'
import { classNames } from '@/lib/nfl-utils'

interface TeamFiltersProps {
  searchTerm: string
  setSearchTerm: (term: string) => void
  selectedDivision: string
  setSelectedDivision: (division: string) => void
  sortBy: 'name' | 'elo' | 'wins' | 'losses'
  setSortBy: (sort: 'name' | 'elo' | 'wins' | 'losses') => void
  divisions: string[]
}

function TeamFilters({
  searchTerm,
  setSearchTerm,
  selectedDivision,
  setSelectedDivision,
  sortBy,
  setSortBy,
  divisions
}: TeamFiltersProps) {
  return (
    <div className="space-y-4">
      {/* Search and Division Filter */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative">
          <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">🔍</span>
          <input
            type="text"
            placeholder="Search teams..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-3 rounded-lg glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-80"
          />
        </div>

        <select
          value={selectedDivision}
          onChange={(e) => setSelectedDivision(e.target.value)}
          className="px-4 py-3 rounded-lg glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="All Divisions">All Divisions</option>
          {divisions.map(div => (
            <option key={div} value={div}>{div}</option>
          ))}
        </select>
      </div>

      {/* Sort Controls */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">Sort by:</span>
        {(['name', 'elo', 'wins', 'losses'] as const).map(option => (
          <button
            key={option}
            onClick={() => setSortBy(option)}
            className={classNames(
              "flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors capitalize",
              sortBy === option
                ? 'bg-primary/20 text-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {option}
            {sortBy === option && <span className="text-primary">↓</span>}
          </button>
        ))}
      </div>
    </div>
  )
}

export default TeamFilters