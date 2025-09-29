import React, { useMemo } from "react";
import { StatusPill } from "./StatusPill";
import { Clock } from "../../lib/icons.tsx";
import { classNames, eloWinProb, fmtTime } from "../../lib/nfl-utils";
import { TEAMS, type Game } from "../../lib/nfl-data";
import TeamLogo from "./TeamLogos";

interface GameCardProps {
  game: Game;
  delayMs?: number;
  reducedMotion?: boolean;
  compact?: boolean;
  onOpen?: (game: Game) => void;
}

export const GameCard: React.FC<GameCardProps> = ({
  game,
  delayMs = 0,
  reducedMotion = false,
  compact = false,
  onOpen
}) => {
  const home = TEAMS[game.home];
  const away = TEAMS[game.away];
  const pHome = useMemo(() => eloWinProb(home?.elo ?? 1500, away?.elo ?? 1500), [home, away]);
  const modelSpread = 14 * (pHome - 0.5);

  // Mock spread data - in real app this would come from game object
  const openSpread = modelSpread + (Math.random() - 0.5) * 2;
  const currentSpread = openSpread + (Math.random() - 0.5) * 1;

  const spreadDiff = Math.abs(currentSpread - modelSpread);
  const hasEdge = spreadDiff > 1;
  const edgeClass = spreadDiff > 3 ? 'text-success' : spreadDiff > 1.5 ? 'text-info' : '';

  const formatSpread = (val: number) => {
    if (val === 0) return 'PK';
    const rounded = Math.round(val * 2) / 2;
    return rounded > 0 ? `+${rounded}` : `${rounded}`;
  };

  const getTime = () => {
    if (game.status === 'FINAL') return 'FINAL';
    return fmtTime(game.date);
  };

  if (compact) {
    return (
      <button
        onClick={() => onOpen?.(game)}
        className="group text-left rounded-xl glass glass-hover p-3 text-xs hover:ring-2 hover:ring-primary/50 transition-all duration-300 hover:-translate-y-1 relative overflow-hidden h-[140px] w-full flex flex-col"
        style={reducedMotion ? undefined : {
          animation: `card-in 420ms cubic-bezier(.2,.7,.2,1) both`,
          animationDelay: `${delayMs}ms`
        }}
      >
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        {/* Subtle border glow */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-sm -z-10" />

        {/* Game Header */}
        <div className="relative flex items-center justify-between mb-3 flex-shrink-0">
          <span className={classNames(
            "text-[11px] font-medium px-2 py-1 rounded-full",
            game.status === 'FINAL'
              ? 'text-muted-foreground bg-muted/20'
              : game.status === 'LIVE'
                ? 'text-success bg-success/20 animate-pulse'
                : 'text-foreground bg-primary/20'
          )}>
            {getTime()}
          </span>
          <span className="text-[10px] text-muted-foreground bg-muted/10 px-2 py-1 rounded-full">{game.network}</span>
        </div>

        {/* Teams - fixed spacing */}
        <div className="relative flex-1 flex flex-col justify-center">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <TeamLogo team={game.away} size="sm" className="transform group-hover:scale-110 transition-transform duration-200" />
                <span className="font-medium text-[12px] text-foreground truncate">{game.away}</span>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {game.status === 'FINAL' && (
                  <span className="font-bold text-[13px] text-foreground tabular-nums bg-accent/20 px-2 py-1 rounded">{game.score?.away}</span>
                )}
                <div className="text-right">
                  <div className={classNames(
                    "text-[11px] font-medium px-1.5 py-0.5 rounded",
                    modelSpread < 0 && hasEdge ? `${edgeClass} bg-success/20` : "text-muted-foreground"
                  )}>
                    {formatSpread(-currentSpread)}
                  </div>
                  {game.status === 'SCHEDULED' && (
                    <div className="text-[9px] text-muted-foreground/70 mt-0.5">
                      {formatSpread(modelSpread < 0 ? -modelSpread : 0)}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <TeamLogo team={game.home} size="sm" className="transform group-hover:scale-110 transition-transform duration-200" />
                <span className="font-medium text-[12px] text-foreground truncate">{game.home}</span>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {game.status === 'FINAL' && (
                  <span className="font-bold text-[13px] text-foreground tabular-nums bg-accent/20 px-2 py-1 rounded">{game.score?.home}</span>
                )}
                <div className="text-right">
                  <div className={classNames(
                    "text-[11px] font-medium px-1.5 py-0.5 rounded",
                    modelSpread > 0 && hasEdge ? `${edgeClass} bg-success/20` : "text-muted-foreground"
                  )}>
                    {formatSpread(currentSpread)}
                  </div>
                  {game.status === 'SCHEDULED' && (
                    <div className="text-[9px] text-muted-foreground/70 mt-0.5">
                      {formatSpread(modelSpread > 0 ? modelSpread : 0)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Spread Comparison Grid */}
        {game.status === 'SCHEDULED' && (
          <div className="relative mt-3 pt-2 border-t border-white/20 flex-shrink-0">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="text-[9px] p-1 rounded bg-muted/10 group-hover:bg-muted/20 transition-colors">
                <div className="text-muted-foreground/60 mb-0.5">Open</div>
                <div className="text-[10px] font-medium">{formatSpread(openSpread)}</div>
              </div>
              <div className="text-[9px] p-1 rounded bg-primary/10 group-hover:bg-primary/20 transition-colors">
                <div className="text-muted-foreground/60 mb-0.5">Current</div>
                <div className="text-[10px] font-medium">{formatSpread(currentSpread)}</div>
              </div>
              <div className="text-[9px] p-1 rounded bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
                <div className="text-muted-foreground/60 mb-0.5">Model</div>
                <div className={classNames(
                  "text-[10px] font-medium",
                  hasEdge ? edgeClass : "text-foreground"
                )}>
                  {formatSpread(modelSpread)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Hover indicator */}
        <div className="absolute bottom-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
        </div>
      </button>
    );
  }

  // Original larger card layout for non-compact mode
  return (
    <button
      onClick={() => onOpen?.(game)}
      className="text-left rounded-2xl glass glass-hover card-hover p-5 ring-1 ring-white/10 hover:ring-primary/40"
      style={reducedMotion ? undefined : {
        animation: `card-in 420ms cubic-bezier(.2,.7,.2,1) both`,
        animationDelay: `${delayMs}ms`
      }}
    >
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Clock className="w-4 h-4" />
          <span>{fmtTime(game.date)} • {game.network}</span>
          <span className="hidden 2xl:inline">• {game.venue}</span>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill status={game.status} />
          <span className="sr-only">Open details</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 items-center">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-8">AWY</span>
            <div className="flex items-center gap-3 min-w-0">
              <div
                className="w-9 h-9 rounded-full shrink-0"
                style={{ background: away?.color || '#999' }}
              />
              <div className="truncate">
                <div className="text-sm font-semibold truncate">{away?.name || game.away}</div>
                <div className="text-xs text-muted-foreground">Elo {away?.elo ?? '—'}</div>
              </div>
            </div>
            {game.status !== 'SCHEDULED' && (
              <span className="ml-auto font-semibold text-base">{game.score?.away ?? 0}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-8">HME</span>
            <div className="flex items-center gap-3 min-w-0">
              <div
                className="w-9 h-9 rounded-full shrink-0"
                style={{ background: home?.color || '#999' }}
              />
              <div className="truncate">
                <div className="text-sm font-semibold truncate">{home?.name || game.home}</div>
                <div className="text-xs text-muted-foreground">Elo {home?.elo ?? '—'}</div>
              </div>
            </div>
            {game.status !== 'SCHEDULED' && (
              <span className="ml-auto font-semibold text-base">{game.score?.home ?? 0}</span>
            )}
          </div>
        </div>

        <div>
          <div className="space-y-1">
            <div className="h-2.5 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full bg-gradient-primary"
                style={{ width: `${Math.round(pHome * 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-muted-foreground text-[11px]">
              <span>AWAY {Math.round((1 - pHome) * 100)}%</span>
              <span>HOME {Math.round(pHome * 100)}%</span>
            </div>
          </div>
          <div className="mt-2 text-xs text-foreground/70">
            <span className="font-medium">Model spread:</span> {modelSpread < 0 ? game.away : game.home} {Math.abs(modelSpread).toFixed(1)}
          </div>
        </div>

        <div className="flex lg:justify-end">
          {game.status === 'LIVE' ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full status-live animate-pulse-glow">
              <span className="inline-block w-2 h-2 rounded-full bg-live" />
              {game.quarter || 'LIVE'}
            </div>
          ) : game.status === 'FINAL' ? (
            <div className="px-3 py-1.5 rounded-full status-final text-sm">Final</div>
          ) : (
            <div className="px-3 py-1.5 rounded-full status-scheduled text-sm">Not started</div>
          )}
        </div>
      </div>
    </button>
  );
};