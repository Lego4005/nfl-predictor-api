import React from 'react'
import { classNames } from '../../lib/nfl-utils'
import TeamLogo from '../../components/TeamLogo'

interface TeamData {
  abbr: string
  name: string
  color: string
  elo: number
  conference: 'AFC' | 'NFC'
  division: string
  record: string
  wins: number
  losses: number
  playoffOdds: number
  streak: string
}

interface TeamCardProps {
  team: TeamData
  onClick: () => void
}

function TeamCard({ team, onClick }: TeamCardProps) {
  return (
    <button
      onClick={onClick}
      className="glass rounded-xl p-4 hover:ring-2 hover:ring-primary/30 transition-all duration-300 text-left w-full"
    >
      <div className="flex items-center justify-between">
        {/* Team Info */}
        <div className="flex items-center gap-4">
          <TeamLogo teamAbbr={team.abbr} size="large" className="" />
          <div className="flex-1">
            <h3 className="font-bold text-foreground text-base">{team.name}</h3>
            <p className="text-sm text-muted-foreground">{team.division}</p>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-foreground">{team.record}</div>
            <div className={classNames(
              "text-sm font-medium",
              team.streak.startsWith('W') ? 'text-success' : 'text-destructive'
            )}>
              {team.streak}
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="flex flex-col gap-2 text-right">
          <div>
            <div className="text-xs text-muted-foreground">Elo Rating</div>
            <div className="text-lg font-bold text-primary">{team.elo}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Playoff Odds</div>
            <div className={classNames(
              "text-sm font-bold",
              team.playoffOdds > 70 ? 'text-success' :
                team.playoffOdds > 40 ? 'text-warning' : 'text-destructive'
            )}>
              {team.playoffOdds}%
            </div>
          </div>
        </div>
      </div>
    </button>
  )
}

export default TeamCard
export type { TeamData }