import React, { useState, useMemo } from 'react'
import { GAMES, TEAMS } from '../../lib/nfl-data'
import { classNames } from '../../lib/nfl-utils'
import TeamLogo from '../../components/TeamLogo'

function ConfidencePoolPage() {
  const [selectedWeek, setSelectedWeek] = useState(3)
  const [userPicks, setUserPicks] = useState<Record<string, { team: string; confidence: number }>>({})
  const [isSubmitted, setIsSubmitted] = useState(false)

  // Get games for selected week
  const weekGames = useMemo(() => {
    return GAMES.filter(g => g.week === selectedWeek && g.status === 'SCHEDULED').slice(0, 14)
  }, [selectedWeek])

  // Mock leaderboard data
  const leaderboard = [
    { rank: 1, name: "AI_Predictor_Pro", score: 127, totalGames: 14, accuracy: 78.6, avatar: "🤖" },
    { rank: 2, name: "GridironGuru", score: 119, totalGames: 14, accuracy: 71.4, avatar: "🏆" },
    { rank: 3, name: "StatMaster3000", score: 115, totalGames: 14, accuracy: 69.2, avatar: "📊" },
    { rank: 4, name: "DeepBlueBetting", score: 112, totalGames: 14, accuracy: 67.8, avatar: "🧠" },
    { rank: 5, name: "You", score: 108, totalGames: 14, accuracy: 64.3, avatar: "👤" },
    { rank: 6, name: "FootballFanatic", score: 104, totalGames: 14, accuracy: 62.1, avatar: "🏈" },
    { rank: 7, name: "NumberCruncher", score: 98, totalGames: 14, accuracy: 58.9, avatar: "🔢" },
    { rank: 8, name: "WeekendWarrior", score: 92, totalGames: 14, accuracy: 55.7, avatar: "⚔️" }
  ]

  const availableConfidences = useMemo(() => {
    const used = Object.values(userPicks).map(pick => pick.confidence)
    return Array.from({ length: weekGames.length }, (_, i) => i + 1).filter(n => !used.includes(n))
  }, [userPicks, weekGames.length])

  const totalConfidence = Object.values(userPicks).reduce((sum, pick) => sum + pick.confidence, 0)
  const maxPossibleScore = weekGames.reduce((sum, _, i) => sum + (i + 1), 0)

  const handleTeamSelect = (gameId: string, team: string) => {
    if (isSubmitted) return

    const currentPick = userPicks[gameId]
    if (currentPick?.team === team) {
      // Deselect if clicking same team
      const newPicks = { ...userPicks }
      delete newPicks[gameId]
      setUserPicks(newPicks)
    } else if (currentPick) {
      // Change team but keep confidence
      setUserPicks({
        ...userPicks,
        [gameId]: { team, confidence: currentPick.confidence }
      })
    } else {
      // New pick, need to assign confidence
      setUserPicks({
        ...userPicks,
        [gameId]: { team, confidence: 0 }
      })
    }
  }

  const handleConfidenceSelect = (gameId: string, confidence: number) => {
    if (isSubmitted) return

    const currentPick = userPicks[gameId]
    if (currentPick) {
      setUserPicks({
        ...userPicks,
        [gameId]: { ...currentPick, confidence }
      })
    }
  }

  const submitPicks = () => {
    if (Object.keys(userPicks).length === weekGames.length &&
      Object.values(userPicks).every(pick => pick.confidence > 0)) {
      setIsSubmitted(true)
    }
  }

  const resetPicks = () => {
    setUserPicks({})
    setIsSubmitted(false)
  }

  const GameCard: React.FC<{ game: typeof weekGames[0] }> = ({ game }) => {
    const homeTeam = TEAMS[game.home]
    const awayTeam = TEAMS[game.away]
    const userPick = userPicks[game.id]

    return (
      <div className="glass rounded-xl p-4 space-y-3">
        <div className="text-center text-xs text-muted-foreground">
          {new Date(game.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
        </div>

        <div className="space-y-2">
          <button
            onClick={() => handleTeamSelect(game.id, game.away)}
            disabled={isSubmitted}
            className={classNames(
              "w-full p-3 rounded-lg transition-all duration-200 hover:ring-2 hover:ring-primary/30",
              userPick?.team === game.away
                ? 'ring-2 ring-primary bg-primary/20'
                : 'bg-white/5 hover:bg-white/10'
            )}
          >
            <div className="flex items-center gap-3">
              <TeamLogo teamAbbr={game.away} size="medium" className="" />
              <div className="flex-1 text-left">
                <div className="text-sm font-medium text-foreground">{awayTeam?.name}</div>
                <div className="text-xs text-muted-foreground">@ {homeTeam?.name}</div>
              </div>
            </div>
          </button>

          <button
            onClick={() => handleTeamSelect(game.id, game.home)}
            disabled={isSubmitted}
            className={classNames(
              "w-full p-3 rounded-lg transition-all duration-200 hover:ring-2 hover:ring-primary/30",
              userPick?.team === game.home
                ? 'ring-2 ring-primary bg-primary/20'
                : 'bg-white/5 hover:bg-white/10'
            )}
          >
            <div className="flex items-center gap-3">
              <TeamLogo teamAbbr={game.home} size="medium" className="" />
              <div className="flex-1 text-left">
                <div className="text-sm font-medium text-foreground">{homeTeam?.name}</div>
                <div className="text-xs text-muted-foreground">vs {awayTeam?.name}</div>
              </div>
            </div>
          </button>
        </div>

        {userPick?.team && (
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground text-center">Confidence Level</div>
            <select
              value={userPick.confidence}
              onChange={(e) => handleConfidenceSelect(game.id, Number(e.target.value))}
              disabled={isSubmitted}
              className="w-full px-3 py-2 rounded-lg glass border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value={0}>Select confidence...</option>
              {[...availableConfidences, userPick.confidence].sort((a, b) => b - a).map(conf => (
                <option key={conf} value={conf}>{conf} points</option>
              ))}
            </select>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">🎯 NFL Confidence Pool</h1>
          <p className="text-sm text-muted-foreground mt-1">Pick winners and assign confidence points • Higher confidence = higher risk/reward</p>
        </div>
      </div>

      {/* Week Selector & Status */}
      <div className="flex items-center justify-between">
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

          <div className="glass rounded-lg px-3 py-2">
            <span className="text-sm text-muted-foreground">Games: </span>
            <span className="text-foreground font-medium">{weekGames.length}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="glass rounded-lg px-3 py-2">
            <span className="text-sm text-muted-foreground">Confidence Used: </span>
            <span className="text-foreground font-medium">{totalConfidence}/{maxPossibleScore}</span>
          </div>

          {isSubmitted ? (
            <button
              onClick={resetPicks}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-warning/20 text-warning hover:bg-warning/30 transition-colors"
            >
              <span>🔄</span>
              Edit Picks
            </button>
          ) : (
            <button
              onClick={submitPicks}
              disabled={Object.keys(userPicks).length !== weekGames.length ||
                !Object.values(userPicks).every(pick => pick.confidence > 0)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>⚡</span>
              Submit Picks
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Games Grid */}
        <div className="lg:col-span-3">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {weekGames.map(game => (
              <GameCard key={game.id} game={game} />
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Rules */}
          <div className="glass rounded-xl p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
              <span className="text-primary">🏆</span>
              How to Play
            </h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>• Pick the winner of each game</p>
              <p>• Assign confidence points (1-{weekGames.length})</p>
              <p>• Higher confidence = more points if correct</p>
              <p>• Each confidence level used once</p>
              <p>• Most total points wins!</p>
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="glass rounded-xl p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
              <span className="text-warning">⭐</span>
              AI Picks
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">High Confidence:</span>
                <span className="text-success">KC, BUF, SF</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Medium Risk:</span>
                <span className="text-warning">PHI, DET, BAL</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Coin Flips:</span>
                <span className="text-destructive">CIN, GB, LAR</span>
              </div>
            </div>
          </div>

          {/* Leaderboard Preview */}
          <div className="glass rounded-xl p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center gap-2">
              <span className="text-success">🥇</span>
              Leaderboard
            </h3>
            <div className="space-y-2">
              {leaderboard.slice(0, 5).map(player => (
                <div key={player.rank} className="flex items-center gap-2 text-sm">
                  <span className="w-6 text-muted-foreground">{player.rank}.</span>
                  <span className="text-lg">{player.avatar}</span>
                  <span className={classNames(
                    "flex-1 truncate",
                    player.name === "You" ? "text-primary font-medium" : "text-foreground"
                  )}>
                    {player.name}
                  </span>
                  <span className="text-success font-bold">{player.score}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfidencePoolPage