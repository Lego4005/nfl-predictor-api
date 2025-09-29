import React, { useState } from 'react'
import { TEAMS } from '@/lib/nfl-data'
import { classNames } from '@/lib/nfl-utils'
import TeamLogo from '../../components/TeamLogo'

// This is a placeholder component that would be extracted from the original App.tsx
// For now, it returns a basic structure

function RankingsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortField, setSortField] = useState<string>('elo')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  // Generate comprehensive team data with advanced metrics like the reference
  const generateAdvancedTeamData = () => {
    return Object.entries(TEAMS).map(([abbr, team], index) => {
      const wins = Math.floor(Math.random() * 8) + 6
      const losses = 17 - wins
      const pf = Math.floor(Math.random() * 150) + 300
      const pa = Math.floor(Math.random() * 150) + 250

      // Advanced metrics
      const eloChange = Math.floor(Math.random() * 40) - 20
      const qbValue = (Math.random() * 4 - 2).toFixed(2)
      const spread = (Math.random() * 3 + 11).toFixed(1)
      const ytdPerformance = (Math.random() * 2).toFixed(2)

      // EPA (Expected Points Added) metrics
      const offensiveEPAPlay = (Math.random() * 0.6 - 0.1).toFixed(2)
      const offensiveEPAPass = (Math.random() * 0.8 - 0.2).toFixed(2)
      const offensiveEPARush = (Math.random() * 0.6 - 0.2).toFixed(2)
      const defensiveEPAPlay = (Math.random() * 0.4 - 0.2).toFixed(2)
      const defensiveEPAPass = (Math.random() * 0.5 - 0.25).toFixed(2)
      const defensiveEPARush = (Math.random() * 0.4 - 0.2).toFixed(2)

      const epaTotal = (parseFloat(offensiveEPAPlay) - parseFloat(defensiveEPAPlay)).toFixed(2)
      const pointsFor = (pf / (wins + losses)).toFixed(1)
      const pointsAgainst = (pa / (wins + losses)).toFixed(1)
      const pointDiff = (parseFloat(pointsFor) - parseFloat(pointsAgainst)).toFixed(1)

      return {
        ...team,
        abbr,
        rank: index + 1,
        eloChange,
        qbValue: parseFloat(qbValue),
        spread: parseFloat(spread),
        ytd: parseFloat(ytdPerformance),
        wins,
        losses,
        pointsFor: parseFloat(pointsFor),
        pointsAgainst: parseFloat(pointsAgainst),
        pointDiff: parseFloat(pointDiff),
        offensiveEPA: {
          play: parseFloat(offensiveEPAPlay),
          pass: parseFloat(offensiveEPAPass),
          rush: parseFloat(offensiveEPARush)
        },
        defensiveEPA: {
          play: parseFloat(defensiveEPAPlay),
          pass: parseFloat(defensiveEPAPass),
          rush: parseFloat(defensiveEPARush)
        },
        epaTotal: parseFloat(epaTotal)
      }
    })
  }

  const teamsData = generateAdvancedTeamData()

  // Filter and sort teams
  const filteredAndSortedTeams = teamsData
    .filter(team =>
      team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      team.abbr.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let aVal, bVal

      switch (sortField) {
        case 'elo':
          aVal = a.elo
          bVal = b.elo
          break
        case 'eloChange':
          aVal = a.eloChange
          bVal = b.eloChange
          break
        case 'qbValue':
          aVal = a.qbValue
          bVal = b.qbValue
          break
        case 'spread':
          aVal = a.spread
          bVal = b.spread
          break
        case 'wins':
          aVal = a.wins
          bVal = b.wins
          break
        case 'losses':
          aVal = a.losses
          bVal = b.losses
          break
        case 'pointDiff':
          aVal = a.pointDiff
          bVal = b.pointDiff
          break
        case 'name':
          return sortDirection === 'asc'
            ? a.name.localeCompare(b.name)
            : b.name.localeCompare(a.name)
        default:
          aVal = a.elo
          bVal = b.elo
      }

      if (sortDirection === 'asc') {
        return aVal - bVal
      } else {
        return bVal - aVal
      }
    })
    .map((team, index) => ({ ...team, currentRank: index + 1 }))

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const SortButton = ({ field, children }: { field: string; children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 hover:text-primary transition-colors"
    >
      {children}
      {sortField === field && (
        <span className="text-primary">
          {sortDirection === 'asc' ? '↑' : '↓'}
        </span>
      )}
    </button>
  )

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">🏆 NFL Power Ratings & Stats</h1>
          <p className="text-sm text-muted-foreground mt-1">nfelo model ratings and advanced stats like EPA</p>
        </div>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
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
      </div>

      {/* Advanced Stats Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="name">Team</SortButton>
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="elo">nfelo</SortButton>
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="eloChange">Δ</SortButton>
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="qbValue">QB</SortButton>
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="spread">Spread</SortButton>
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="ytd">YTD</SortButton>
                </th>
                <th className="text-center p-2 text-xs text-muted-foreground font-medium" colSpan={3}>
                  Offensive EPA
                </th>
                <th className="text-center p-2 text-xs text-muted-foreground font-medium" colSpan={3}>
                  Defensive EPA
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  EPA
                </th>
                <th className="text-center p-2 text-xs text-muted-foreground font-medium" colSpan={3}>
                  Points / Game
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="wins">Wins</SortButton>
                </th>
                <th className="text-center p-4 text-sm text-muted-foreground font-medium">
                  <SortButton field="losses">Losses</SortButton>
                </th>
              </tr>
              <tr className="border-b border-white/5 text-xs text-muted-foreground">
                <td className="p-2"></td>
                <td className="text-center p-2">Adj</td>
                <td className="p-2"></td>
                <td className="text-center p-2">Value</td>
                <td className="text-center p-2">Weekly</td>
                <td className="text-center p-2">Play</td>
                <td className="text-center p-2">Play</td>
                <td className="text-center p-2">Pass</td>
                <td className="text-center p-2">Rush</td>
                <td className="text-center p-2">Play</td>
                <td className="text-center p-2">Pass</td>
                <td className="text-center p-2">Rush</td>
                <td className="text-center p-2">Play</td>
                <td className="text-center p-2">For</td>
                <td className="text-center p-2">Against</td>
                <td className="text-center p-2">Diff</td>
                <td className="p-2"></td>
                <td className="p-2"></td>
              </tr>
            </thead>
            <tbody>
              {filteredAndSortedTeams.map((team) => (
                <tr
                  key={team.abbr}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                >
                  {/* Team */}
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-muted-foreground w-6">{team.currentRank}</span>
                      <div
                        className="w-8 h-8 rounded flex items-center justify-center text-foreground font-bold text-xs"
                        style={{ backgroundColor: team.color }}
                      >
                        {team.abbr}
                      </div>
                      <span className="text-foreground font-medium">{team.name}</span>
                    </div>
                  </td>

                  {/* nfelo */}
                  <td className="text-center p-4 text-foreground font-bold">{team.elo}</td>

                  {/* Δ (Change) */}
                  <td className={classNames(
                    "text-center p-4 font-medium",
                    team.eloChange > 0 ? 'text-success' : team.eloChange < 0 ? 'text-destructive' : 'text-muted-foreground'
                  )}>
                    {team.eloChange > 0 ? '+' : ''}{team.eloChange}
                  </td>

                  {/* QB Value */}
                  <td className={classNames(
                    "text-center p-4 text-sm",
                    team.qbValue > 0 ? 'text-success' : team.qbValue < 0 ? 'text-destructive' : 'text-muted-foreground'
                  )}>
                    {team.qbValue.toFixed(2)}
                  </td>

                  {/* Spread */}
                  <td className="text-center p-4 text-sm text-foreground">{team.spread.toFixed(2)}</td>

                  {/* YTD */}
                  <td className="text-center p-4 text-sm text-foreground">{team.ytd.toFixed(2)}</td>

                  {/* Offensive EPA */}
                  <td className={classNames(
                    "text-center p-2 text-xs",
                    team.offensiveEPA.play > 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.offensiveEPA.play.toFixed(2)}
                  </td>
                  <td className={classNames(
                    "text-center p-2 text-xs",
                    team.offensiveEPA.pass > 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.offensiveEPA.pass.toFixed(2)}
                  </td>
                  <td className={classNames(
                    "text-center p-2 text-xs",
                    team.offensiveEPA.rush > 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.offensiveEPA.rush.toFixed(2)}
                  </td>

                  {/* Defensive EPA */}
                  <td className={classNames(
                    "text-center p-2 text-xs",
                    team.defensiveEPA.play < 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.defensiveEPA.play.toFixed(2)}
                  </td>
                  <td className={classNames(
                    "text-center p-2 text-xs",
                    team.defensiveEPA.pass < 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.defensiveEPA.pass.toFixed(2)}
                  </td>
                  <td className={classNames(
                    "text-center p-2 text-xs",
                    team.defensiveEPA.rush < 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.defensiveEPA.rush.toFixed(2)}
                  </td>

                  {/* EPA Total */}
                  <td className={classNames(
                    "text-center p-4 text-sm font-medium",
                    team.epaTotal > 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.epaTotal.toFixed(2)}
                  </td>

                  {/* Points */}
                  <td className="text-center p-2 text-xs text-foreground">{team.pointsFor.toFixed(2)}</td>
                  <td className="text-center p-2 text-xs text-foreground">{team.pointsAgainst.toFixed(2)}</td>
                  <td className={classNames(
                    "text-center p-2 text-xs font-medium",
                    team.pointDiff > 0 ? 'text-success' : 'text-destructive'
                  )}>
                    {team.pointDiff > 0 ? '+' : ''}{team.pointDiff}
                  </td>

                  {/* Record */}
                  <td className="text-center p-4 text-foreground font-medium">{team.wins}</td>
                  <td className="text-center p-4 text-foreground font-medium">{team.losses}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <h3 className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
            <span className="text-primary">🏆</span>
            Top nfelo
          </h3>
          <div className="text-xl font-bold text-foreground">{Math.max(...teamsData.map(t => t.elo))}</div>
          <div className="text-xs text-muted-foreground">{teamsData.find(t => t.elo === Math.max(...teamsData.map(t => t.elo)))?.name}</div>
        </div>

        <div className="glass rounded-xl p-4">
          <h3 className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
            <span className="text-success">📈</span>
            Best EPA
          </h3>
          <div className="text-xl font-bold text-success">+{Math.max(...teamsData.map(t => t.epaTotal)).toFixed(2)}</div>
          <div className="text-xs text-muted-foreground">{teamsData.find(t => t.epaTotal === Math.max(...teamsData.map(t => t.epaTotal)))?.name}</div>
        </div>

        <div className="glass rounded-xl p-4">
          <h3 className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
            <span className="text-warning">⚡</span>
            Most Improved
          </h3>
          <div className="text-xl font-bold text-warning">+{Math.max(...teamsData.map(t => t.eloChange))}</div>
          <div className="text-xs text-muted-foreground">{teamsData.find(t => t.eloChange === Math.max(...teamsData.map(t => t.eloChange)))?.name}</div>
        </div>

        <div className="glass rounded-xl p-4">
          <h3 className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
            <span className="text-info">🎯</span>
            Best Record
          </h3>
          <div className="text-xl font-bold text-foreground">{Math.max(...teamsData.map(t => t.wins))}-{Math.min(...teamsData.map(t => t.losses))}</div>
          <div className="text-xs text-muted-foreground">{teamsData.find(t => t.wins === Math.max(...teamsData.map(t => t.wins)))?.name}</div>
        </div>
      </div>
    </div>
  )
}

export default RankingsPage