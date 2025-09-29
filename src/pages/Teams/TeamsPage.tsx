import React, { useState, useMemo } from 'react'
import { TEAMS } from '@/lib/nfl-data'
import { classNames } from '@/lib/nfl-utils'
import TeamCard from './TeamCard'
import TeamFilters from './TeamFilters'

interface TeamsPageProps {
  onTeamClick: (teamId: string) => void
}

function TeamsPage({ onTeamClick }: TeamsPageProps) {
  const [selectedDivision, setSelectedDivision] = useState('All Divisions')
  const [sortBy, setSortBy] = useState<'name' | 'elo' | 'wins' | 'losses'>('elo')
  const [searchTerm, setSearchTerm] = useState('')

  // Enhanced team data with full NFL structure
  const teamData = useMemo(() => {
    return Object.entries(TEAMS).map(([abbr, team]) => {
      // Mock additional team data
      const wins = Math.floor(Math.random() * 3) + (team.elo > 1600 ? 2 : team.elo > 1550 ? 1 : 0)
      const losses = 3 - wins
      const playoffOdds = Math.min(95, Math.max(5, (team.elo - 1400) / 3.5 + Math.random() * 20))

      // Determine streak
      const isWinning = Math.random() > 0.4
      const streakLength = Math.floor(Math.random() * 3) + 1
      const streak = isWinning ? `W${streakLength}` : `L${streakLength}`

      // Determine conference and division
      const divisions = {
        'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
        'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
        'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
        'AFC West': ['DEN', 'KC', 'LAC', 'LV'],
        'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
        'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
        'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
        'NFC West': ['ARI', 'LAR', 'SF', 'SEA']
      }

      let division = 'AFC East'
      let conference: 'AFC' | 'NFC' = 'AFC'

      // Find team's division and conference
      for (const [div, teams] of Object.entries(divisions)) {
        if (teams.includes(abbr)) {
          division = div
          conference = div.startsWith('AFC') ? 'AFC' : 'NFC'
          break
        }
      }

      return {
        ...team,
        abbr,
        conference,
        division,
        record: `${wins}-${losses}`,
        wins,
        losses,
        playoffOdds: parseFloat(playoffOdds.toFixed(1)),
        streak
      }
    })
  }, [])

  // Filter teams
  const filteredTeams = useMemo(() => {
    return teamData.filter(team => {
      const matchesDivision = selectedDivision === 'All Divisions' || team.division === selectedDivision
      const matchesSearch = team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        team.abbr.toLowerCase().includes(searchTerm.toLowerCase())
      return matchesDivision && matchesSearch
    })
  }, [teamData, selectedDivision, searchTerm])

  // Sort teams
  const sortedTeams = useMemo(() => {
    return [...filteredTeams].sort((a, b) => {
      if (sortBy === 'elo') return b.elo - a.elo
      if (sortBy === 'wins') return b.wins - a.wins
      if (sortBy === 'losses') return a.losses - b.losses
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      return 0
    })
  }, [filteredTeams, sortBy])

  // Group teams by division for display
  const teamsByDivision = useMemo(() => {
    if (selectedDivision === 'All Divisions') {
      return sortedTeams.reduce((acc, team) => {
        if (!acc[team.division]) acc[team.division] = []
        acc[team.division].push(team)
        return acc
      }, {} as Record<string, typeof teamData>)
    } else {
      return { [selectedDivision]: sortedTeams }
    }
  }, [selectedDivision, sortedTeams])

  // Calculate summary stats
  const totalTeams = Object.keys(TEAMS).length
  const avgElo = Math.round(Object.values(TEAMS).reduce((sum, team) => sum + team.elo, 0) / totalTeams)
  const undefeatedTeams = teamData.filter(team => team.losses === 0).length
  const currentWeek = 3

  // Get unique divisions for filter
  const divisions = Array.from(new Set(teamData.map(team => team.division))).sort()

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">👥 NFL Teams</h1>
          <p className="text-sm text-muted-foreground mt-1">Complete team directory with stats and projections</p>
        </div>
      </div>

      {/* Filters */}
      <TeamFilters 
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        selectedDivision={selectedDivision}
        setSelectedDivision={setSelectedDivision}
        sortBy={sortBy}
        setSortBy={setSortBy}
        divisions={divisions}
      />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-primary">🏈</span>
            <span className="text-sm text-muted-foreground">Teams</span>
          </div>
          <div className="text-2xl font-bold text-white">{totalTeams}</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-info">📊</span>
            <span className="text-sm text-muted-foreground">Avg Elo</span>
          </div>
          <div className="text-2xl font-bold text-white">{avgElo}</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-success">🏆</span>
            <span className="text-sm text-muted-foreground">Undefeated</span>
          </div>
          <div className="text-2xl font-bold text-white">{undefeatedTeams}</div>
        </div>

        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-warning">📅</span>
            <span className="text-sm text-muted-foreground">Week</span>
          </div>
          <div className="text-2xl font-bold text-white">{currentWeek}</div>
        </div>
      </div>

      {/* Teams by Division */}
      <div className="space-y-6">
        {Object.entries(teamsByDivision).map(([divisionName, teams]) => (
          <div key={divisionName} className="space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              {divisionName}
              <span className="text-sm text-muted-foreground font-normal">{teams.length} teams</span>
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {teams.map((team) => (
                <TeamCard 
                  key={team.abbr}
                  team={team}
                  onClick={() => onTeamClick(team.abbr)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {Object.keys(teamsByDivision).length === 0 && (
        <div className="glass rounded-xl p-8 text-center">
          <span className="text-muted-foreground text-4xl mb-3 block">🔍</span>
          <h3 className="text-lg font-medium text-white mb-2">No teams found</h3>
          <p className="text-sm text-muted-foreground">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  )
}

export default TeamsPage