/**
 * Featured Games Bento Grid Component
 * Showcase special games in an attractive grid layout
 */

import React from 'react';
import { motion } from 'framer-motion';
import {
  Trophy,
  Zap,
  Star,
  Crown,
  Flame,
  Target,
  TrendingUp,
  Award
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { TeamLogoMatchup } from '@/components/ui/TeamLogo';
import AttractButton from '@/components/kokonutui/attract-button';
import { EnhancedGame } from './EnhancedGameCard';

interface FeaturedGamesBentoProps {
  games: EnhancedGame[];
  onGameClick: (gameId: string) => void;
}

export default function FeaturedGamesBento({ games, onGameClick }: FeaturedGamesBentoProps) {
  // Separate games into categories
  const gameOfTheWeek = games.find(g => g.featured && g.primetime) || games[0];
  const primetimeGames = games.filter(g => g.primetime && g.id !== gameOfTheWeek?.id).slice(0, 2);
  const divisionalGames = games.filter(g => !g.primetime && g.featured).slice(0, 3);
  const upsetAlert = games.find(g => {
    const spread = Math.abs(parseFloat(g.homeSpread));
    return spread > 7 && g.status === 'SCHEDULED';
  });

  const BentoCard = ({
    game,
    size = 'normal',
    highlight = false,
    badge,
    icon: Icon = Trophy
  }: {
    game: EnhancedGame;
    size?: 'large' | 'normal' | 'small';
    highlight?: boolean;
    badge?: string;
    icon?: React.ElementType;
  }) => (
    <motion.div
      className={cn(
        "relative glass rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden",
        size === 'large' ? "col-span-2 row-span-2 p-6" : size === 'normal' ? "p-4" : "p-3",
        highlight ? "border-gold-500/50 bg-gradient-to-br from-gold-900/20 to-amber-900/20" : "border-border",
        "hover:shadow-lg hover:scale-[1.02]"
      )}
      onClick={() => onGameClick(game.id)}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.98 }}
    >
      {badge && (
        <Badge className="absolute top-3 right-3 bg-gradient-to-r from-gold-500 to-amber-500 text-white border-0">
          <Icon className="w-3 h-3 mr-1" />
          {badge}
        </Badge>
      )}

      <div className={cn("space-y-3", size === 'large' && "space-y-4")}>
        {/* Team Matchup */}
        <div className="flex justify-center">
          <TeamLogoMatchup
            awayTeam={game.awayTeam}
            homeTeam={game.homeTeam}
            size={size === 'large' ? 'lg' : size === 'normal' ? 'md' : 'sm'}
            showVs={true}
          />
        </div>

        {/* Team Names */}
        <div className="text-center space-y-1">
          <div className={cn(
            "font-bold text-foreground",
            size === 'large' ? "text-xl" : size === 'normal' ? "text-lg" : "text-base"
          )}>
            {game.awayTeam} @ {game.homeTeam}
          </div>
          <div className="text-sm text-muted-foreground">
            {game.day} • {game.time}
          </div>
        </div>

        {/* Game Info */}
        <div className="flex justify-center gap-2">
          <Badge variant="outline" className="text-xs">
            {game.network}
          </Badge>
          {game.spread.current && (
            <Badge variant="secondary" className="text-xs">
              {game.spread.current}
            </Badge>
          )}
        </div>

        {/* Venue for large cards */}
        {size === 'large' && game.venue && (
          <div className="text-center text-sm text-muted-foreground">
            📍 {game.venue}
          </div>
        )}

        {/* Special Indicators */}
        {game.status === 'LIVE' && (
          <div className="flex justify-center">
            <Badge className="bg-red-500/20 text-red-400 animate-pulse">
              <Zap className="w-3 h-3 mr-1" />
              LIVE NOW
            </Badge>
          </div>
        )}
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          🌟 Featured Games
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Don't miss these marquee matchups
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-6xl mx-auto">
        {/* Game of the Week - Large Feature */}
        {gameOfTheWeek && (
          <BentoCard
            game={gameOfTheWeek}
            size="large"
            highlight={true}
            badge="Game of the Week"
            icon={Crown}
          />
        )}

        {/* Primetime Games */}
        <div className="col-span-1 md:col-span-2 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-purple-500" />
            <h3 className="font-semibold text-foreground">Primetime Games</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {primetimeGames.map(game => (
              <BentoCard
                key={game.id}
                game={game}
                size="normal"
                badge="Primetime"
                icon={Zap}
              />
            ))}
          </div>
        </div>

        {/* Upset Alert */}
        {upsetAlert && (
          <div className="col-span-1">
            <div className="flex items-center gap-2 mb-2">
              <Flame className="w-5 h-5 text-red-500" />
              <h3 className="font-semibold text-foreground">Upset Alert</h3>
            </div>
            <BentoCard
              game={upsetAlert}
              size="normal"
              badge="Underdog Watch"
              icon={Target}
            />
          </div>
        )}

        {/* Divisional Matchups */}
        {divisionalGames.length > 0 && (
          <div className="col-span-full">
            <div className="flex items-center gap-2 mb-3">
              <Trophy className="w-5 h-5 text-gold-500" />
              <h3 className="font-semibold text-foreground">Key Divisional Battles</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {divisionalGames.map(game => (
                <BentoCard
                  key={game.id}
                  game={game}
                  size="normal"
                  badge="Division"
                  icon={Award}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* View All Button */}
      <div className="flex justify-center">
        <AttractButton
          onClick={() => {}}
          className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white"
          particleCount={10}
          attractRadius={50}
        >
          <Trophy className="w-4 h-4 mr-2" />
          View All Games
        </AttractButton>
      </div>
    </div>
  );
}