import React from 'react';
import GameCard from '../game/GameCard';
import { Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function GameGrid({
  games = [],
  onGameClick,
  showLiveSeparately = true
}) {
  console.log('GameGrid received games:', games.length);

  if (!games || games.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No games available</p>
      </div>
    );
  }

  // Separate live and non-live games
  const liveGames = games.filter(g => g.status === 'live' || g.status === 'in_progress');
  const nonLiveGames = games.filter(g => g.status !== 'live' && g.status !== 'in_progress');

  console.log('Live games:', liveGames.length, 'Non-live games:', nonLiveGames.length);

  return (
    <div className="space-y-6">
      {/* Live Games Section */}
      {showLiveSeparately && liveGames.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Badge className="bg-red-600 text-white animate-pulse">
              <Activity className="w-3 h-3 mr-1" />
              LIVE NOW
            </Badge>
            <span className="text-sm font-semibold">
              {liveGames.length} Games In Progress
            </span>
          </div>
          <div className="grid grid-cols-1 gap-6">
            {liveGames.map(game => (
              <div
                key={game.id}
                onClick={() => onGameClick?.(game)}
                className={game.status === "scheduled" ? "cursor-pointer" : ""}
              >
                <GameCard game={game} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Other Games */}
      <div className="grid grid-cols-1 gap-6">
        {(showLiveSeparately ? nonLiveGames : games)
          .sort((a, b) => {
            // Sort: scheduled first (by time), then final
            if (a.status === 'scheduled' && b.status === 'scheduled') {
              return new Date(a.startTime || a.gameTime || 0) - new Date(b.startTime || b.gameTime || 0);
            }
            if (a.status === 'scheduled') return -1;
            if (b.status === 'scheduled') return 1;
            return 0;
          })
          .map(game => (
            <div
              key={game.id}
              onClick={() => onGameClick?.(game)}
              className={game.status === "scheduled" ? "cursor-pointer" : ""}
            >
              <GameCard game={game} />
            </div>
          ))}
      </div>

      {games.length === 0 && (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No games match the current filter</p>
        </div>
      )}
    </div>
  );
}