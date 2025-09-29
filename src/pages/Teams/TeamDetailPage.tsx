import React from 'react'
import { TEAMS } from '@/lib/nfl-data'
import TeamLogo from '../../components/TeamLogo'

interface TeamDetailPageProps {
  teamId: string
  onBack: () => void
}

function TeamDetailPage({ teamId, onBack }: TeamDetailPageProps) {
  // Find the team data
  const team = TEAMS[teamId]

  if (!team) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <h2 className="text-lg font-bold text-foreground mb-2">Team Not Found</h2>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
        >
          Back to Teams
        </button>
      </div>
    )
  }

  // Mock season data
  const seasonData = {
    record: "3-0",
    wins: 3,
    losses: 0,
    pointDiff: 5.0,
    epaPerPlay: 0.160,
    pointsFor: 37,
    pointsAgainst: 32,
    totalYards: 330.7,
    passingYards: 208,
    rushingYards: 122.7,
    totalYardsAllowed: 415
  }

  // Mock rankings data
  const rankings = {
    offEPAPerPlay: Math.floor(Math.random() * 32) + 1,
    epaPerPass: Math.floor(Math.random() * 32) + 1,
    epaPerRush: Math.floor(Math.random() * 32) + 1,
    defEPAPerPlay: Math.floor(Math.random() * 32) + 1,
    defEPAPerPass: Math.floor(Math.random() * 32) + 1,
    defEPAPerRush: Math.floor(Math.random() * 32) + 1
  }

  // Mock conversion stats
  const conversions = {
    thirdDownFor: 44,
    fourthDownFor: 50,
    redZoneFor: 55,
    thirdDownAgainst: 45,
    fourthDownAgainst: 71,
    redZoneAgainst: 79
  }

  // Mock turnover stats
  const turnovers = {
    committed: 0.7,
    created: 0.7,
    interceptionsThrown: 1.0,
    interceptionsCreated: 0.3,
    fumblesLost: 0.7,
    fumblesCreated: 0.3
  }

  // Mock schedule data (showing current season with bye weeks)
  const schedule = [
    {
      week: 3,
      opponent: "BUF",
      opponentName: "Buffalo Bills",
      isHome: true,
      result: "BYE WEEK",
      score: null,
      margin: null,
      spread: null,
      atsResult: null,
      eloChange: null
    },
    {
      week: 4,
      opponent: "DAL",
      opponentName: "Dallas Cowboys",
      isHome: false,
      result: "BYE WEEK",
      score: null,
      margin: null,
      spread: null,
      atsResult: null,
      eloChange: null
    }
  ]

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-white/10 hover:border-primary/30 transition-colors text-foreground"
      >
        <span>←</span>
        Back to Teams
      </button>

      {/* Team Header */}
      <div className="glass rounded-xl p-6">
        <div className="flex items-center gap-6">
          <div
            className="w-20 h-20 rounded-lg flex items-center justify-center text-foreground font-bold text-2xl"
            style={{ backgroundColor: team.color }}
          >
            {teamId}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-1">{team.name}</h1>
            <p className="text-muted-foreground">2025 Season</p>
          </div>
        </div>
      </div>

      {/* Season Overview */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-foreground mb-6">Season Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-sm text-muted-foreground mb-1">Record</div>
            <div className="text-2xl font-bold text-foreground">{seasonData.record}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
              <span>nfelo Rating</span>
              <span className="text-info">ℹ️</span>
            </div>
            <div className="text-2xl font-bold text-primary">{team.elo}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
              <span>Point Diff / Game</span>
              <span className="text-info">ℹ️</span>
            </div>
            <div className="flex items-center justify-center gap-1">
              <span className="text-2xl font-bold text-success">+{seasonData.pointDiff}</span>
              <span className="text-sm text-muted-foreground">pts</span>
            </div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
              <span>Net EPA / Play</span>
              <span className="text-info">ℹ️</span>
            </div>
            <div className="flex items-center justify-center gap-1">
              <span className="text-2xl font-bold text-success">+{seasonData.epaPerPlay.toFixed(3)}</span>
              <span className="text-sm text-muted-foreground">epa</span>
            </div>
          </div>
        </div>
      </div>

      {/* Schedule and Results */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-foreground mb-6">2025 Schedule and Results</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left p-3 text-sm text-muted-foreground font-medium">Week / Opponent</th>
                <th className="text-center p-3 text-sm text-muted-foreground font-medium">Result</th>
                <th className="text-center p-3 text-sm text-muted-foreground font-medium">Score</th>
                <th className="text-center p-3 text-sm text-muted-foreground font-medium">Margin</th>
                <th className="text-center p-3 text-sm text-muted-foreground font-medium">Spread</th>
                <th className="text-center p-3 text-sm text-muted-foreground font-medium">ATS Result</th>
                <th className="text-center p-3 text-sm text-muted-foreground font-medium">nfelo Change</th>
              </tr>
            </thead>
            <tbody>
              {schedule.map((game, index) => (
                <tr key={index} className="border-b border-white/5 hover:bg-white/5">
                  <td className="p-3">
                    <div className="flex items-center gap-3">
                      <span className="text-muted-foreground font-medium">{game.week}</span>
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center text-foreground font-bold text-xs"
                        style={{ backgroundColor: TEAMS[game.opponent]?.color || '#666' }}
                      >
                        {game.opponent}
                      </div>
                      <span className="text-foreground">{game.opponentName}</span>
                      {!game.isHome && <span className="text-muted-foreground">@</span>}
                    </div>
                  </td>
                  <td className="p-3 text-center text-muted-foreground">{game.result}</td>
                  <td className="p-3 text-center text-muted-foreground">-</td>
                  <td className="p-3 text-center text-muted-foreground">-</td>
                  <td className="p-3 text-center text-muted-foreground">-</td>
                  <td className="p-3 text-center text-muted-foreground">-</td>
                  <td className="p-3 text-center text-muted-foreground">-</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
        {/* Rankings */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-foreground mb-4">Ranks</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Off. EPA / Play</span>
              <span className="text-foreground font-medium">{rankings.offEPAPerPlay}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">EPA / Pass</span>
              <span className="text-foreground font-medium">{rankings.epaPerPass}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">EPA / Rush</span>
              <span className="text-foreground font-medium">{rankings.epaPerRush}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Def. EPA / Play</span>
              <span className="text-foreground font-medium">{rankings.defEPAPerPlay}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">EPA / Pass</span>
              <span className="text-foreground font-medium">{rankings.defEPAPerPass}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">EPA / Rush</span>
              <span className="text-foreground font-medium">{rankings.defEPAPerRush}</span>
            </div>
          </div>
        </div>

        {/* Point Differential */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-foreground mb-4">Point Differential</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Points For</span>
              <span className="text-foreground font-medium">{seasonData.pointsFor}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Points Against</span>
              <span className="text-foreground font-medium">{seasonData.pointsAgainst}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Total Yards</span>
              <span className="text-foreground font-medium">{seasonData.totalYards}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Passing Yards</span>
              <span className="text-foreground font-medium">{seasonData.passingYards}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Rushing Yards</span>
              <span className="text-foreground font-medium">{seasonData.rushingYards}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Total Yards Allowed</span>
              <span className="text-foreground font-medium">{seasonData.totalYardsAllowed}</span>
            </div>
          </div>
        </div>

        {/* Conversions */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-foreground mb-4">Conversions For</h3>
          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">3rd Down</span>
              <span className="text-foreground font-medium">{conversions.thirdDownFor}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">4th Down</span>
              <span className="text-foreground font-medium">{conversions.fourthDownFor}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Red Zone</span>
              <span className="text-foreground font-medium">{conversions.redZoneFor}%</span>
            </div>
          </div>

          <h4 className="text-sm font-bold text-foreground mb-3">Conversions Against</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">3rd Down</span>
              <span className="text-foreground font-medium">{conversions.thirdDownAgainst}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">4th Down</span>
              <span className="text-foreground font-medium">{conversions.fourthDownAgainst}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Red Zone</span>
              <span className="text-foreground font-medium">{conversions.redZoneAgainst}%</span>
            </div>
          </div>
        </div>

        {/* Turnovers */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-bold text-foreground mb-4">Turnovers / Game</h3>
          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Committed</span>
              <span className="text-foreground font-medium">{turnovers.committed}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Created</span>
              <span className="text-foreground font-medium">{turnovers.created}%</span>
            </div>
          </div>

          <h4 className="text-sm font-bold text-foreground mb-3">Interceptions</h4>
          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Thrown</span>
              <span className="text-foreground font-medium">{turnovers.interceptionsThrown}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Created</span>
              <span className="text-foreground font-medium">{turnovers.interceptionsCreated}%</span>
            </div>
          </div>

          <h4 className="text-sm font-bold text-foreground mb-3">Fumbles</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Lost</span>
              <span className="text-foreground font-medium">{turnovers.fumblesLost}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Created</span>
              <span className="text-foreground font-medium">{turnovers.fumblesCreated}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TeamDetailPage