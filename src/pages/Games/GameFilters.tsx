import React from 'react'

interface GameFiltersProps {
  searchTerm: string
  setSearchTerm: (term: string) => void
  statusFilter: string
  setStatusFilter: (filter: string) => void
  weekFilter: string
  setWeekFilter: (filter: string) => void
  viewDensity: string
  setViewDensity: (density: string) => void
}

function GameFilters({
  searchTerm,
  setSearchTerm,
  statusFilter,
  setStatusFilter,
  weekFilter,
  setWeekFilter,
  viewDensity,
  setViewDensity
}: GameFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Search */}
      <div className="flex items-center space-x-2 px-3 py-2 glass border border-border rounded-lg flex-1 min-w-48">
        <span className="text-muted-foreground">🔍</span>
        <input
          type="text"
          placeholder="Search team (e.g., KC, Eagles)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-transparent text-foreground placeholder-muted-foreground flex-1 outline-none"
        />
      </div>

      {/* Status Filter */}
      <div className="flex items-center space-x-2">
        <span className="text-muted-foreground">🔄</span>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-background text-foreground border border-border rounded-lg px-3 py-2"
        >
          <option value="All" className="bg-background text-foreground">All</option>
          <option value="Scheduled" className="bg-background text-foreground">Scheduled</option>
          <option value="Live" className="bg-background text-foreground">Live</option>
          <option value="Final" className="bg-background text-foreground">Final</option>
        </select>
      </div>

      {/* Week Filter */}
      <select
        value={weekFilter}
        onChange={(e) => setWeekFilter(e.target.value)}
        className="bg-background text-foreground border border-border rounded-lg px-3 py-2"
      >
        {Array.from({ length: 18 }, (_, i) => (
          <option key={i + 1} value={`Week ${i + 1}`} className="bg-background text-foreground">
            Week {i + 1}
          </option>
        ))}
      </select>

      {/* View Density */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-muted-foreground">View</span>
        <select
          value={viewDensity}
          onChange={(e) => setViewDensity(e.target.value)}
          className="bg-background text-foreground border border-border rounded-lg px-3 py-2"
        >
          <option value="Compact" className="bg-background text-foreground">Compact</option>
          <option value="Cozy" className="bg-background text-foreground">Cozy</option>
          <option value="Comfortable" className="bg-background text-foreground">Comfortable</option>
        </select>
      </div>
    </div>
  )
}

export default GameFilters