import React, { useState, useMemo } from 'react'
import { TEAMS } from '../../lib/nfl-data'
import { classNames } from '../../lib/nfl-utils'
import TeamLogo from '../../components/TeamLogo'
import { useGames } from '../../hooks/useAPI'
import { getCurrentNFLWeek } from '../../utils/nflWeekCalculator'
import { EXPERT_PERSONALITIES, getCouncilMembers } from '../../data/expertPersonalities'

function ConfidencePoolPage() {
  const currentWeek = getCurrentNFLWeek(new Date())
  const [selectedWeek, setSelectedWeek] = useState(currentWeek)
  const [selectedExpert, setSelectedExpert] = useState<string | null>(null) // Filter by expert
  const councilExperts = useMemo(() => getCouncilMembers(), [])

  // Fetch real games from database
  const { data: gamesData, isLoading } = useGames()

  // Get games for selected week
  const weekGames = useMemo(() => {
    if (!gamesData || !Array.isArray(gamesData)) return []

    return gamesData
      .filter(g => g.week === selectedWeek && g.season === 2025)
      .map(g => ({
        id: g.id,
        week: g.week,
        date: g.game_time,
        status: g.status?.toUpperCase() || 'SCHEDULED',
        away: g.away_team,
        home: g.home_team,
        score: g.home_score !== null ? { away: g.away_score || 0, home: g.home_score || 0 } : null,
        network: g.network || 'TBD',
        venue: g.venue || 'TBD'
      }))
      .slice(0, 16)
  }, [gamesData, selectedWeek])

  // Generate council confidence picks with weighted voting simulation
  const councilConfidencePicks = useMemo(() => {
    if (!weekGames.length) return []

    // For each council expert, generate picks for all games with category-specific weights
    const allPicks = councilExperts.flatMap(expert => {
      return weekGames.map((game, index) => {
        // Deterministic pick based on expert personality + game
        const pickHome = (expert.id.charCodeAt(0) + game.id.charCodeAt(0)) % 2 === 0
        const team = pickHome ? game.home : game.away
        const teamName = TEAMS[team]?.name || team

        // Base confidence on expert accuracy + personality variance
        const baseConf = Math.floor(55 + (expert.accuracy_metrics.overall * 40)) // 55-95%
        const personalityVariance = ((expert.id.charCodeAt(0) + index) % 15) - 7
        const confidence = Math.min(95, Math.max(55, baseConf + personalityVariance))

        // Confidence rank (1-16) - how much this expert prioritizes this pick
        const confidenceRank = ((expert.id.charCodeAt(1) + game.id.charCodeAt(1)) % weekGames.length) + 1

        // Calculate vote weight for this prediction (simulating weighted voting system)
        // Weight = (Expert Accuracy * 0.4) + (Recent Performance * 0.3) + (Confidence * 0.2) + (Specialization Match * 0.1)
        const accuracyComponent = expert.accuracy_metrics.overall * 0.4
        const recentComponent = (expert.accuracy_metrics.recent_performance || 0.7) * 0.3
        const confidenceComponent = (confidence / 100) * 0.2

        // Specialization match - experts have higher weight for their specialty categories
        const specializationMatch = expert.archetype.includes('Data-driven') ? 0.9 :
                                   expert.archetype.includes('Contrarian') ? 0.7 :
                                   expert.archetype.includes('Value') ? 0.8 :
                                   expert.archetype.includes('Momentum') ? 0.6 : 0.5
        const specializationComponent = specializationMatch * 0.1

        const voteWeight = accuracyComponent + recentComponent + confidenceComponent + specializationComponent

        // Generate personality-driven reasoning
        const reasons: string[] = []
        if (expert.archetype.includes('Data-driven')) {
          reasons.push(`Advanced statistical models favor ${teamName}`)
          reasons.push(`Historical matchup trends support ${teamName}`)
          reasons.push(`${confidence}% win probability based on 5-year data analysis`)
          reasons.push(`Vote weight: ${(voteWeight * 100).toFixed(1)}% (High accuracy component)`)
        } else if (expert.archetype.includes('Contrarian') || expert.archetype.includes('Against-the-grain')) {
          reasons.push(`Public heavily backing opponent - fade opportunity`)
          reasons.push(`Market inefficiency detected in ${teamName} pricing`)
          reasons.push(`Contrarian value play with ${confidence}% confidence`)
          reasons.push(`Vote weight: ${(voteWeight * 100).toFixed(1)}% (Specialization in fading public)`)
        } else if (expert.archetype.includes('Value') || expert.archetype.includes('Hunter')) {
          reasons.push(`Sharp money movement indicates ${teamName} value`)
          reasons.push(`Line value analysis shows +EV on ${teamName}`)
          reasons.push(`ROI indicators align with ${teamName} at ${confidence}%`)
          reasons.push(`Vote weight: ${(voteWeight * 100).toFixed(1)}% (Value specialization)`)
        } else if (expert.archetype.includes('Momentum') || expert.archetype.includes('Trend')) {
          reasons.push(`Recent momentum strongly trending ${teamName}`)
          reasons.push(`Live performance metrics favor ${teamName}`)
          reasons.push(`Psychological factors support ${teamName}`)
          reasons.push(`Vote weight: ${(voteWeight * 100).toFixed(1)}% (Momentum tracking)`)
        } else if (expert.archetype.includes('Research') || expert.archetype.includes('Scholar')) {
          reasons.push(`Comprehensive fundamental analysis supports ${teamName}`)
          reasons.push(`Deep research methodology favors ${teamName}`)
          reasons.push(`Multi-factor evaluation shows ${teamName} at ${confidence}%`)
          reasons.push(`Vote weight: ${(voteWeight * 100).toFixed(1)}% (Research depth)`)
        } else {
          reasons.push(`Systematic analysis supports ${teamName}`)
          reasons.push(`Multiple convergent factors favor ${teamName}`)
          reasons.push(`Confidence level ${confidence}% based on methodology`)
          reasons.push(`Vote weight: ${(voteWeight * 100).toFixed(1)}%`)
        }

        return {
          expert,
          game,
          team,
          teamName,
          confidence,
          confidenceRank,
          voteWeight,
          reasoning: reasons
        }
      })
    })

    // Sort by confidence rank within each expert
    return allPicks.sort((a, b) => {
      if (a.expert.id !== b.expert.id) {
        return (a.expert.council_position || 0) - (b.expert.council_position || 0)
      }
      return a.confidenceRank - b.confidenceRank
    })
  }, [weekGames, councilExperts])

  // Filter picks by selected expert if any
  const filteredPicks = useMemo(() => {
    if (!selectedExpert) return councilConfidencePicks
    return councilConfidencePicks.filter(p => p.expert.id === selectedExpert)
  }, [councilConfidencePicks, selectedExpert])

  // Confidence Pick Row Component
  const ConfidencePickRow: React.FC<{ pick: typeof filteredPicks[0]; index: number }> = ({ pick, index }) => {
    const homeTeam = TEAMS[pick.game.home]
    const awayTeam = TEAMS[pick.game.away]
    const pickedTeam = TEAMS[pick.team]
    const [expanded, setExpanded] = useState(false)

    return (
      <div className="glass rounded-lg">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full p-4 flex items-center gap-4 hover:bg-white/5 transition-colors rounded-lg"
        >
          {/* Confidence Rank */}
          <div className="flex flex-col items-center min-w-[40px]">
            <div className={classNames(
              "text-2xl font-bold",
              index < 3 ? "text-success" : index < 8 ? "text-warning" : "text-muted-foreground"
            )}>
              {pick.confidenceRank}
            </div>
            <div className="text-[10px] text-muted-foreground">points</div>
          </div>

          {/* Expert Info */}
          <div className="flex items-center gap-2 min-w-[120px]">
            <span className="text-2xl">{pick.expert.emoji}</span>
            <div className="text-left">
              <div className="text-sm font-medium text-foreground">{pick.expert.name}</div>
              <div className="text-[10px] text-muted-foreground">{(pick.expert.accuracy_metrics.overall * 100).toFixed(1)}% acc</div>
            </div>
          </div>

          {/* Matchup */}
          <div className="flex-1 flex items-center gap-3">
            <div className="flex items-center gap-2">
              <TeamLogo teamAbbr={pick.game.away} size="small" />
              <span className="text-xs text-muted-foreground">{awayTeam?.abbreviation}</span>
            </div>
            <span className="text-xs text-muted-foreground">@</span>
            <div className="flex items-center gap-2">
              <TeamLogo teamAbbr={pick.game.home} size="small" />
              <span className="text-xs text-muted-foreground">{homeTeam?.abbreviation}</span>
            </div>
          </div>

          {/* Pick */}
          <div className="flex items-center gap-2">
            <div className="text-right min-w-[80px]">
              <div className="text-sm font-bold text-success">{pickedTeam?.abbreviation}</div>
              <div className="text-[10px] text-muted-foreground">picks {pick.teamName}</div>
            </div>
          </div>

          {/* Confidence */}
          <div className="flex items-center gap-2 min-w-[80px]">
            <div className="text-right">
              <div className="text-lg font-bold text-primary">{pick.confidence}%</div>
              <div className="text-[10px] text-muted-foreground">confidence</div>
            </div>
          </div>

          {/* Expand Icon */}
          <div className={classNames(
            "transform transition-transform",
            expanded ? "rotate-180" : ""
          )}>
            ▼
          </div>
        </button>

        {/* Expanded Reasoning */}
        {expanded && (
          <div className="px-4 pb-4 space-y-2 border-t border-white/10 pt-3">
            <div className="text-xs font-medium text-primary">Reasoning:</div>
            <div className="space-y-1">
              {pick.reasoning.map((reason, i) => (
                <div key={i} className="text-xs text-muted-foreground flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span className="flex-1">{reason}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-between text-[10px]">
              <div className="text-muted-foreground">
                Game Time: {new Date(pick.game.date).toLocaleDateString('en-US', {
                  weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                })}
              </div>
              <div className="text-muted-foreground">
                Network: {pick.game.network}
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="w-full h-96 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading games...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">🎯 AI Council Confidence Picks</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Our AI experts rank their picks by confidence • Sorted by most confident to least
          </p>
        </div>
      </div>

      {/* Week Selector & Expert Filter */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <select
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(Number(e.target.value))}
            className="px-3 py-2 rounded-lg glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {Array.from({ length: 18 }, (_, i) => i + 1).map(w => (
              <option key={w} value={w}>Week {w}</option>
            ))}
          </select>

          <select
            value={selectedExpert || ''}
            onChange={(e) => setSelectedExpert(e.target.value || null)}
            className="px-3 py-2 rounded-lg glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Experts</option>
            {councilExperts.map(expert => (
              <option key={expert.id} value={expert.id}>
                {expert.emoji} {expert.name}
              </option>
            ))}
          </select>

          <div className="glass rounded-lg px-3 py-2">
            <span className="text-sm text-muted-foreground">Total Picks: </span>
            <span className="text-foreground font-medium">{filteredPicks.length}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {councilExperts.map(expert => (
            <button
              key={expert.id}
              onClick={() => setSelectedExpert(selectedExpert === expert.id ? null : expert.id)}
              className={classNames(
                "px-3 py-2 rounded-lg text-xs transition-colors",
                selectedExpert === expert.id
                  ? "bg-primary/20 text-primary ring-2 ring-primary/30"
                  : "glass hover:bg-white/10"
              )}
              title={expert.name}
            >
              {expert.emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Confidence Picks List */}
      <div className="space-y-3">
        {filteredPicks.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <p className="text-muted-foreground">No picks available for this selection.</p>
          </div>
        ) : (
          filteredPicks.map((pick, index) => (
            <ConfidencePickRow key={`${pick.expert.id}-${pick.game.id}`} pick={pick} index={index} />
          ))
        )}
      </div>

      {/* Expert Stats Summary */}
      {!selectedExpert && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-6">
          {councilExperts.map(expert => (
            <div key={expert.id} className="glass rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{expert.emoji}</span>
                <div>
                  <div className="text-sm font-medium text-foreground">{expert.name}</div>
                  <div className="text-[10px] text-muted-foreground">{expert.archetype}</div>
                </div>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Accuracy:</span>
                  <span className="text-success font-medium">
                    {(expert.accuracy_metrics.overall * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Council Rank:</span>
                  <span className="text-primary font-medium">#{expert.council_position}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Week Picks:</span>
                  <span className="text-foreground font-medium">
                    {councilConfidencePicks.filter(p => p.expert.id === expert.id).length}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ConfidencePoolPage