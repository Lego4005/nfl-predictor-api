/**
 * Enhanced Games Page
 * Polished NFL games display with advanced filtering and interactions
 */

import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar,
  Clock,
  Trophy,
  Tv,
  Filter,
  Grid3x3,
  List,
  LayoutGrid,
  Zap,
  Activity,
  TrendingUp,
  Star
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import EnhancedGameCard, { EnhancedGame } from './EnhancedGameCard';
import SmoothTab from '@/components/kokonutui/smooth-tab';
import AttractButton from '@/components/kokonutui/attract-button';
import BentoGrid from '@/components/kokonutui/bento-grid';
import GameFilters from './GameFilters';
import WeekNavigation from './WeekNavigation';

interface EnhancedGamesPageProps {
  currentWeek: number;
  setCurrentWeek: (week: number) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  statusFilter: string;
  setStatusFilter: (filter: string) => void;
  weekFilter: string;
  setWeekFilter: (filter: string) => void;
  viewDensity: string;
  setViewDensity: (density: string) => void;
  filteredGames: EnhancedGame[];
  gamesByDay: Record<string, EnhancedGame[]>;
  onGameClick: (gameId: string) => void;
}

export default function EnhancedGamesPage({
  currentWeek,
  setCurrentWeek,
  searchTerm,
  setSearchTerm,
  statusFilter,
  setStatusFilter,
  weekFilter,
  setWeekFilter,
  viewDensity,
  setViewDensity,
  filteredGames,
  gamesByDay,
  onGameClick
}: EnhancedGamesPageProps) {
  const [activeTab, setActiveTab] = useState('all-games');
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'compact'>('grid');

  // Calculate game statistics
  const gameStats = useMemo(() => {
    const liveGames = filteredGames.filter(g => g.status === 'LIVE' || g.status === 'OVERTIME' || g.status === 'HALFTIME');
    const upcomingGames = filteredGames.filter(g => g.status === 'SCHEDULED');
    const completedGames = filteredGames.filter(g => g.status === 'FINAL');
    const featuredGames = filteredGames.filter(g => g.featured);
    const primetimeGames = filteredGames.filter(g => g.primetime);

    return {
      total: filteredGames.length,
      live: liveGames.length,
      upcoming: upcomingGames.length,
      completed: completedGames.length,
      featured: featuredGames.length,
      primetime: primetimeGames.length
    };
  }, [filteredGames]);

  // Filter games by tab selection
  const displayedGames = useMemo(() => {
    switch (activeTab) {
      case 'live':
        return filteredGames.filter(g => g.status === 'LIVE' || g.status === 'OVERTIME' || g.status === 'HALFTIME');
      case 'featured':
        return filteredGames.filter(g => g.featured || g.primetime);
      case 'upcoming':
        return filteredGames.filter(g => g.status === 'SCHEDULED');
      case 'completed':
        return filteredGames.filter(g => g.status === 'FINAL');
      default:
        return filteredGames;
    }
  }, [activeTab, filteredGames]);

  // Group games by day for the selected tab
  const displayedGamesByDay = useMemo(() => {
    const grouped: Record<string, EnhancedGame[]> = {};
    displayedGames.forEach(game => {
      if (!grouped[game.day]) {
        grouped[game.day] = [];
      }
      grouped[game.day].push(game);
    });
    return grouped;
  }, [displayedGames]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Section */}
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-3xl font-bold text-foreground mb-2">
            🏈 NFL Games Center
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
            Week {currentWeek} • {gameStats.total} Games
            {gameStats.live > 0 && (
              <Badge className="ml-2 bg-red-500/20 text-red-400 animate-pulse">
                <Activity className="w-3 h-3 mr-1" />
                {gameStats.live} LIVE
              </Badge>
            )}
          </p>
        </motion.div>
      </div>

      {/* Quick Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 max-w-4xl mx-auto">
        <div className="text-center glass rounded-lg p-3">
          <div className="text-2xl font-bold text-blue-500">{gameStats.total}</div>
          <div className="text-xs text-gray-500">Total Games</div>
        </div>
        <div className="text-center glass rounded-lg p-3">
          <div className="text-2xl font-bold text-red-500">{gameStats.live}</div>
          <div className="text-xs text-gray-500">Live Now</div>
        </div>
        <div className="text-center glass rounded-lg p-3">
          <div className="text-2xl font-bold text-amber-500">{gameStats.upcoming}</div>
          <div className="text-xs text-gray-500">Upcoming</div>
        </div>
        <div className="text-center glass rounded-lg p-3">
          <div className="text-2xl font-bold text-green-500">{gameStats.completed}</div>
          <div className="text-xs text-gray-500">Completed</div>
        </div>
        <div className="text-center glass rounded-lg p-3">
          <div className="text-2xl font-bold text-gold-500">{gameStats.featured}</div>
          <div className="text-xs text-gray-500">Featured</div>
        </div>
        <div className="text-center glass rounded-lg p-3">
          <div className="text-2xl font-bold text-purple-500">{gameStats.primetime}</div>
          <div className="text-xs text-gray-500">Primetime</div>
        </div>
      </div>

      {/* Week Navigation */}
      <WeekNavigation
        currentWeek={currentWeek}
        setCurrentWeek={setCurrentWeek}
      />

      {/* Enhanced Tab Navigation */}
      <div className="flex justify-center mb-6">
        <SmoothTab
          items={[
            {
              id: 'all-games',
              title: `All Games (${gameStats.total})`,
              color: 'bg-blue-500 hover:bg-blue-600',
              cardContent: (
                <div className="p-6 h-full flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">All Week {currentWeek} Games</h3>
                    <p className="text-gray-300">Complete schedule with live updates</p>
                  </div>
                  <Calendar className="w-8 h-8 text-blue-400" />
                </div>
              )
            },
            {
              id: 'live',
              title: `Live (${gameStats.live})`,
              color: 'bg-red-500 hover:bg-red-600',
              cardContent: gameStats.live > 0 ? (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Games In Progress</h3>
                    <Activity className="w-6 h-6 text-red-400 animate-pulse" />
                  </div>
                  <div className="space-y-2">
                    {filteredGames
                      .filter(g => g.status === 'LIVE' || g.status === 'OVERTIME' || g.status === 'HALFTIME')
                      .slice(0, 3)
                      .map(game => (
                        <div key={game.id} className="flex justify-between items-center text-sm">
                          <span className="text-gray-300">
                            {game.awayTeam} @ {game.homeTeam}
                          </span>
                          <Badge className="bg-red-500/20 text-red-400">
                            {game.quarter || game.status}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </div>
              ) : (
                <div className="p-6 h-full flex items-center justify-center">
                  <div className="text-center">
                    <Activity className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                    <p className="text-gray-400">No live games</p>
                  </div>
                </div>
              )
            },
            {
              id: 'featured',
              title: `Featured (${gameStats.featured})`,
              color: 'bg-gold-500 hover:bg-gold-600',
              cardContent: (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Must-Watch Games</h3>
                    <Trophy className="w-6 h-6 text-gold-400" />
                  </div>
                  <p className="text-gray-300">Marquee matchups and primetime games</p>
                </div>
              )
            },
            {
              id: 'upcoming',
              title: `Upcoming (${gameStats.upcoming})`,
              color: 'bg-amber-500 hover:bg-amber-600',
              cardContent: (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Coming Up</h3>
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                  <p className="text-gray-300">Games scheduled to start</p>
                </div>
              )
            },
            {
              id: 'completed',
              title: `Final (${gameStats.completed})`,
              color: 'bg-green-500 hover:bg-green-600',
              cardContent: (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Completed Games</h3>
                    <Trophy className="w-6 h-6 text-green-400" />
                  </div>
                  <p className="text-gray-300">Final scores and results</p>
                </div>
              )
            }
          ]}
          defaultTabId={activeTab}
          onChange={setActiveTab}
          className="w-full max-w-4xl"
        />
      </div>

      {/* View Mode Toggle */}
      <div className="flex justify-between items-center">
        <GameFilters
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          weekFilter={weekFilter}
          setWeekFilter={setWeekFilter}
          viewDensity={viewDensity}
          setViewDensity={setViewDensity}
        />

        <div className="flex gap-2">
          <AttractButton
            onClick={() => setViewMode('grid')}
            className={cn(
              "px-3 py-1.5",
              viewMode === 'grid' ? "bg-primary text-primary-foreground" : "bg-secondary"
            )}
            particleCount={4}
            attractRadius={30}
          >
            <Grid3x3 className="w-4 h-4" />
          </AttractButton>
          <AttractButton
            onClick={() => setViewMode('list')}
            className={cn(
              "px-3 py-1.5",
              viewMode === 'list' ? "bg-primary text-primary-foreground" : "bg-secondary"
            )}
            particleCount={4}
            attractRadius={30}
          >
            <List className="w-4 h-4" />
          </AttractButton>
          <AttractButton
            onClick={() => setViewMode('compact')}
            className={cn(
              "px-3 py-1.5",
              viewMode === 'compact' ? "bg-primary text-primary-foreground" : "bg-secondary"
            )}
            particleCount={4}
            attractRadius={30}
          >
            <LayoutGrid className="w-4 h-4" />
          </AttractButton>
        </div>
      </div>

      {/* Games Display */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${activeTab}-${viewMode}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {viewMode === 'grid' && (
            <div className="grid grid-cols-1 xl:grid-cols-5 lg:grid-cols-3 md:grid-cols-2 gap-4">
              {Object.entries(displayedGamesByDay).map(([day, games]) => (
                <div key={day} className="space-y-3">
                  <h2 className="text-base font-semibold text-foreground text-center glass border border-border rounded-lg py-2 px-2">
                    {day}
                  </h2>
                  <div className="space-y-2">
                    {games.map((game, index) => (
                      <motion.div
                        key={game.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <EnhancedGameCard
                          game={game}
                          onGameClick={onGameClick}
                          density={viewDensity as 'compact' | 'cozy' | 'comfortable'}
                        />
                      </motion.div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {viewMode === 'list' && (
            <div className="space-y-2">
              {displayedGames.map((game, index) => (
                <motion.div
                  key={game.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                >
                  <EnhancedGameCard
                    game={game}
                    onGameClick={onGameClick}
                    density="compact"
                  />
                </motion.div>
              ))}
            </div>
          )}

          {viewMode === 'compact' && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {displayedGames.map((game, index) => (
                <motion.div
                  key={game.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.02 }}
                >
                  <EnhancedGameCard
                    game={game}
                    onGameClick={onGameClick}
                    density="compact"
                  />
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Empty State */}
      {displayedGames.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-xl p-12 text-center"
        >
          <span className="text-muted-foreground text-6xl mb-4 block">🔍</span>
          <h3 className="text-xl font-semibold text-foreground mb-2">No games found</h3>
          <p className="text-muted-foreground mb-4">
            {activeTab !== 'all-games'
              ? `No ${activeTab} games available for Week ${currentWeek}`
              : 'Try adjusting your search or filter criteria'}
          </p>
          {activeTab !== 'all-games' && (
            <AttractButton
              onClick={() => setActiveTab('all-games')}
              className="bg-primary text-primary-foreground"
              particleCount={6}
            >
              View All Games
            </AttractButton>
          )}
        </motion.div>
      )}
    </div>
  );
}