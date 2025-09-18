import React from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Sun, Moon, Zap, Wifi } from "lucide-react";
import WsBadge from "./WsBadge";

export function DashboardHeader({ dark, setDark, wide, setWide, connected, isLoading, demoMode, setDemoMode }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-4">
        <h1 className="text-3xl font-bold">NFL Prediction Dashboard</h1>
        <WsBadge connected={connected} />
        {/* Data mode indicator */}
        <div className={`flex items-center gap-2 px-3 py-1 rounded-lg border ${
          demoMode
            ? 'bg-amber-100 dark:bg-amber-900 border-amber-200 dark:border-amber-700'
            : 'bg-green-100 dark:bg-green-900 border-green-200 dark:border-green-700'
        }`}>
          <Zap className={`h-4 w-4 ${
            demoMode
              ? 'text-amber-600 dark:text-amber-400'
              : 'text-green-600 dark:text-green-400'
          }`} />
          <span className={`text-sm font-medium ${
            demoMode
              ? 'text-amber-800 dark:text-amber-200'
              : 'text-green-800 dark:text-green-200'
          }`}>
            {demoMode ? 'Demo Data' : 'Live 2025 NFL Data'}
          </span>
        </div>
        {isLoading && <Skeleton className="h-8 w-24" />}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.location.href = '/?admin=true'}
          className="bg-red-600 hover:bg-red-700 text-white border-red-700"
        >
          🧠 Admin
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setDemoMode(!demoMode)}
          className={demoMode ? 'bg-amber-600 hover:bg-amber-700 text-white border-amber-700' : ''}
        >
          {demoMode ? '📊 Demo' : '🔴 Live'}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setWide(!wide)}
        >
          {wide ? "Narrow" : "Wide"} Mode
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => setDark(!dark)}
        >
          {dark ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

export function LiveGamesBar({ games, connected }) {
  return (
    <div className="mb-4 p-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg border border-blue-200 dark:border-blue-800 overflow-hidden">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-white font-semibold text-sm">
              {games?.filter(g => g.status === 'live').length > 0 ? 'LIVE NFL UPDATES' : 'EXPERT PREDICTIONS'}
            </span>
          </div>

          {/* Scrolling content based on game status */}
          <div className="flex-1 min-w-0">
            {games?.filter(g => g.status === 'live').length > 0 ? (
              // Live games in progress
              <div className="text-white/90 text-sm">
                {games.filter(g => g.status === 'live').length} games in progress
              </div>
            ) : (
              // Expert predictions for upcoming games
              <div className="relative overflow-hidden h-5">
                <div className="animate-marquee flex space-x-8 whitespace-nowrap text-white/90 text-sm">
                  {games?.filter(g => g.status === 'scheduled').slice(0, 3).map((game, i) => (
                    <span key={game.id || i} className="flex-shrink-0">
                      <span className="font-medium">The Sharp Bettor:</span> {game.awayTeam} @ {game.homeTeam} -
                      <span className="text-yellow-300 ml-1">
                        {game.prediction?.homeWinProb > 0.5 ? `${game.homeTeam} ${(game.prediction.homeWinProb * 100).toFixed(0)}%` : `${game.awayTeam} ${(game.prediction.awayWinProb * 100).toFixed(0)}%`}
                      </span>
                    </span>
                  ))}
                  {games?.filter(g => g.status === 'scheduled').slice(0, 3).map((game, i) => (
                    <span key={`chaos-${game.id || i}`} className="flex-shrink-0">
                      <span className="font-medium">The Chaos Theory:</span> {game.awayTeam} @ {game.homeTeam} -
                      <span className="text-green-300 ml-1">Expect the unexpected!</span>
                    </span>
                  ))}
                  {games?.filter(g => g.status === 'scheduled').slice(0, 3).map((game, i) => (
                    <span key={`analyst-${game.id || i}`} className="flex-shrink-0">
                      <span className="font-medium">The Conservative Analyst:</span> {game.awayTeam} @ {game.homeTeam} -
                      <span className="text-blue-300 ml-1">Home field advantage matters</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 text-white/80 text-xs flex-shrink-0">
          <Wifi className="h-3 w-3" />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </div>
  );
}