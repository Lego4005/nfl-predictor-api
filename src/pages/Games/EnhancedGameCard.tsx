/**
 * Enhanced Game Card Component
 * Polished game display with proper time formatting and interactive elements
 */

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  Tv,
  MapPin,
  TrendingUp,
  Activity,
  Calendar,
  Zap,
  Trophy,
  AlertCircle,
  Timer
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { TeamLogoMatchup } from '@/components/ui/TeamLogo';
import AttractButton from '@/components/kokonutui/attract-button';
import { format, parseISO, formatDistanceToNow, isAfter, isBefore, addHours } from 'date-fns';

export interface EnhancedGame {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeScore?: number;
  awayScore?: number;
  status: 'SCHEDULED' | 'LIVE' | 'FINAL' | 'HALFTIME' | 'OVERTIME';
  quarter?: string;
  timeRemaining?: string;
  network: string;
  venue: string;
  time: string; // ISO 8601 format
  gameType?: 'regular' | 'playoff' | 'championship';
  day: string;
  week: number;
  spread: {
    open: string;
    current: string;
    model: string;
  };
  homeSpread: string;
  awaySpread: string;
  overUnder?: {
    total: number;
    over: string;
    under: string;
  };
  featured?: boolean;
  primetime?: boolean;
}

interface EnhancedGameCardProps {
  game: EnhancedGame;
  onGameClick: (gameId: string) => void;
  density?: 'compact' | 'cozy' | 'comfortable';
}

export default function EnhancedGameCard({
  game,
  onGameClick,
  density = 'cozy'
}: EnhancedGameCardProps) {
  const [countdown, setCountdown] = useState<string>('');
  const [isLive, setIsLive] = useState(false);

  // Format game time properly
  const formatGameTime = (timeString: string) => {
    try {
      const date = parseISO(timeString);
      const now = new Date();

      // Check if game is starting soon (within 2 hours)
      const gameTime = new Date(timeString);
      const twoHoursFromNow = addHours(now, 2);

      if (isAfter(gameTime, now) && isBefore(gameTime, twoHoursFromNow)) {
        return {
          main: formatDistanceToNow(date, { addSuffix: true }),
          secondary: format(date, 'h:mm a'),
          isStartingSoon: true
        };
      }

      return {
        main: format(date, 'h:mm a'),
        secondary: format(date, 'MMM d'),
        isStartingSoon: false
      };
    } catch (e) {
      // Fallback for simple time strings
      return {
        main: game.time,
        secondary: game.day,
        isStartingSoon: false
      };
    }
  };

  const timeInfo = useMemo(() => formatGameTime(game.time), [game.time]);

  // Live game pulse animation
  useEffect(() => {
    setIsLive(game.status === 'LIVE' || game.status === 'HALFTIME' || game.status === 'OVERTIME');
  }, [game.status]);

  // Countdown for upcoming games
  useEffect(() => {
    if (game.status !== 'SCHEDULED') return;

    const updateCountdown = () => {
      try {
        const gameTime = new Date(game.time);
        const now = new Date();

        if (isAfter(gameTime, now)) {
          const hours = Math.floor((gameTime.getTime() - now.getTime()) / (1000 * 60 * 60));
          const minutes = Math.floor(((gameTime.getTime() - now.getTime()) % (1000 * 60 * 60)) / (1000 * 60));

          if (hours < 24) {
            setCountdown(`${hours}h ${minutes}m`);
          } else {
            const days = Math.floor(hours / 24);
            setCountdown(`${days}d ${hours % 24}h`);
          }
        }
      } catch (e) {
        setCountdown('');
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [game.time, game.status]);

  const getStatusColor = () => {
    switch (game.status) {
      case 'LIVE':
      case 'OVERTIME':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HALFTIME':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'FINAL':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const getSpreadColor = (spread: string) => {
    const value = parseFloat(spread);
    if (value > 0) return 'text-green-400';
    if (value < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <motion.div
      className={cn(
        "group relative overflow-hidden rounded-xl transition-all duration-300",
        density === 'compact' ? 'p-3' : density === 'cozy' ? 'p-4' : 'p-5',
        game.featured && "ring-2 ring-gold-500/30",
        game.primetime && "bg-gradient-to-br from-purple-900/20 to-indigo-900/20"
      )}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <button
        onClick={() => onGameClick(game.id)}
        className={cn(
          "w-full text-left rounded-lg glass border transition-all duration-200",
          "hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10",
          game.featured ? "border-gold-500/30" : "border-border",
          density === 'compact' ? 'p-3' : density === 'cozy' ? 'p-4' : 'p-5'
        )}
      >
        {/* Header with Time and Network */}
        <div className="flex justify-between items-start mb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              {timeInfo.isStartingSoon ? (
                <Badge variant="secondary" className="bg-amber-500/20 text-amber-400 animate-pulse">
                  <Timer className="w-3 h-3 mr-1" />
                  {timeInfo.main}
                </Badge>
              ) : (
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  <span className="font-medium">{timeInfo.main}</span>
                  <span className="text-xs">• {timeInfo.secondary}</span>
                </div>
              )}
              {countdown && game.status === 'SCHEDULED' && (
                <Badge variant="outline" className="text-xs">
                  {countdown}
                </Badge>
              )}
            </div>
            {game.venue && density !== 'compact' && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="w-3 h-3" />
                <span>{game.venue}</span>
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge variant="outline" className="text-xs">
              <Tv className="w-3 h-3 mr-1" />
              {game.network}
            </Badge>
            {game.primetime && (
              <Badge className="bg-purple-500/20 text-purple-400 text-xs">
                <Zap className="w-3 h-3 mr-1" />
                Primetime
              </Badge>
            )}
          </div>
        </div>

        {/* Teams Matchup */}
        <div className="space-y-3 mb-3">
          {/* Centered Team Logos */}
          <div className="flex justify-center mb-3">
            <TeamLogoMatchup
              awayTeam={game.awayTeam}
              homeTeam={game.homeTeam}
              size="md"
              showVs={true}
            />
          </div>

          {/* Team Names and Scores */}
          <div className="space-y-2">
            {/* Away Team */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">{game.awayTeam}</span>
                {game.awayScore !== undefined && (
                  <motion.span
                    key={game.awayScore}
                    initial={{ scale: 1.2, color: '#10b981' }}
                    animate={{ scale: 1, color: '#ffffff' }}
                    className="text-lg font-bold"
                  >
                    {game.awayScore}
                  </motion.span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className={cn("text-sm font-medium", getSpreadColor(game.awaySpread))}>
                  {game.awaySpread}
                </span>
              </div>
            </div>

            {/* Home Team */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">{game.homeTeam}</span>
                {game.homeScore !== undefined && (
                  <motion.span
                    key={game.homeScore}
                    initial={{ scale: 1.2, color: '#10b981' }}
                    animate={{ scale: 1, color: '#ffffff' }}
                    className="text-lg font-bold"
                  >
                    {game.homeScore}
                  </motion.span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className={cn("text-sm font-medium", getSpreadColor(game.homeSpread))}>
                  {game.homeSpread}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Game Status */}
        <AnimatePresence mode="wait">
          {isLive && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="mb-3"
            >
              <div className={cn(
                "flex items-center justify-center gap-2 px-3 py-1.5 rounded-full border",
                getStatusColor()
              )}>
                <Activity className="w-3 h-3 animate-pulse" />
                <span className="font-semibold text-xs uppercase">
                  {game.status}
                  {game.quarter && ` - ${game.quarter}`}
                  {game.timeRemaining && ` - ${game.timeRemaining}`}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {game.status === 'FINAL' && (
          <div className="flex justify-center mb-3">
            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
              <Trophy className="w-3 h-3 mr-1" />
              FINAL
            </Badge>
          </div>
        )}

        {/* Betting Information */}
        {game.status === 'SCHEDULED' && density !== 'compact' && (
          <div className="pt-3 border-t border-border/50 space-y-2">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-muted-foreground mb-1">Open</div>
                <Badge variant="outline" className="w-full justify-center">
                  {game.spread.open}
                </Badge>
              </div>
              <div className="text-center">
                <div className="text-muted-foreground mb-1">Current</div>
                <Badge variant="secondary" className="w-full justify-center">
                  {game.spread.current}
                </Badge>
              </div>
              <div className="text-center">
                <div className="text-muted-foreground mb-1">Model</div>
                <Badge className="w-full justify-center bg-primary/20">
                  {game.spread.model}
                </Badge>
              </div>
            </div>

            {game.overUnder && (
              <div className="flex justify-center gap-2 pt-2">
                <Badge variant="outline" className="text-xs">
                  O/U {game.overUnder.total}
                </Badge>
                <Badge variant="outline" className="text-xs text-green-400">
                  O {game.overUnder.over}
                </Badge>
                <Badge variant="outline" className="text-xs text-red-400">
                  U {game.overUnder.under}
                </Badge>
              </div>
            )}
          </div>
        )}

        {/* Featured Game Indicator */}
        {game.featured && (
          <div className="absolute top-2 left-2">
            <Badge className="bg-gold-500/20 text-gold-400 border-gold-500/30">
              <Trophy className="w-3 h-3 mr-1" />
              Featured
            </Badge>
          </div>
        )}
      </button>
    </motion.div>
  );
}