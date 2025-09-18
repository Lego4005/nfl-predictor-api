/**
 * NFL Dashboard - Refactored Clean Architecture Version
 * Uses new useGameData hook with Expert Observatory API
 * Separated concerns and modular components
 */

import React, { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";

// Hooks
import { useGameData } from "../hooks/useGameData.js";
import { useNFLWeek, useNFLWeekReset } from "../hooks/useNFLWeek";

// Components
import GameCard from "./game/GameCard";
import GameDetailModal from "./GameDetailModal";
import GameGrid from "./dashboard/GameGrid";
import NFLWeekHeader from "./dashboard/NFLWeekHeader";

// UI Components
import { Card, CardHeader, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

// Icons
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Moon,
  Sun,
  RefreshCw,
  Wifi,
  WifiOff,
  Filter,
  Calendar,
  Clock,
  Zap
} from "lucide-react";

// Error Boundary (from original file)
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("Dashboard crashed:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] grid place-items-center p-8">
          <div className="text-center space-y-4">
            <AlertTriangle className="h-16 w-16 text-red-500 mx-auto" />
            <h2 className="text-2xl font-bold">Dashboard Error</h2>
            <p className="text-muted-foreground max-w-md">
              Something went wrong. Please refresh the page.
            </p>
            <Button onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Page
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// WebSocket Badge Component
function WsBadge({ connected }) {
  return connected ? (
    <Badge className="bg-emerald-600 dark:bg-emerald-700 hover:bg-emerald-600 dark:hover:bg-emerald-700 text-white">
      <Wifi className="h-3.5 w-3.5 mr-1" />
      Live
    </Badge>
  ) : (
    <Badge variant="secondary" className="bg-muted text-muted-foreground">
      <WifiOff className="h-3.5 w-3.5 mr-1" />
      Simulated
    </Badge>
  );
}

// Game Filter Component
function GameFilters({ gameFilter, setGameFilter, gamesCount }) {
  const filters = [
    { id: 'all', label: 'All Games', count: gamesCount.total },
    { id: 'live', label: 'Live', count: gamesCount.live },
    { id: 'today', label: 'Today', count: gamesCount.today },
    { id: 'thisWeek', label: 'This Week', count: gamesCount.thisWeek },
  ];

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Filter className="h-4 w-4 text-muted-foreground" />
      {filters.map(filter => (
        <Button
          key={filter.id}
          variant={gameFilter === filter.id ? "default" : "outline"}
          size="sm"
          onClick={() => setGameFilter(filter.id)}
          className="text-xs"
        >
          {filter.label}
          {filter.count > 0 && (
            <Badge variant="secondary" className="ml-1 text-xs">
              {filter.count}
            </Badge>
          )}
        </Button>
      ))}
    </div>
  );
}

// Main NFLDashboard Component
export default function NFLDashboard() {
  // Theme and layout state
  const [dark, setDark] = useState(false);
  const [wide, setWide] = useState(false);
  const [connected, setConnected] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Game selection and modal state
  const [selectedGame, setSelectedGame] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [gameFilter, setGameFilter] = useState('all');

  // Use our new clean data hook - switches to Expert Observatory API!
  const {
    games,
    loading,
    error,
    refreshGames,
    gamesByStatus,
    dataSourceInfo
  } = useGameData({
    dataSource: 'expert-observatory', // ✨ The magic switch!
    autoRefresh: true,
    refreshInterval: 30000
  });

  // NFL Week Management
  const nflWeek = useNFLWeek(games, {
    isMobile,
    autoRefresh: true,
    refreshInterval: 60000
  });

  // Week reset detection
  const weekReset = useNFLWeekReset(() => {
    console.log('NFL Week reset detected - refreshing data');
    refreshGames();
  });

  // Mobile detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Theme handling
  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  // Mock WebSocket for demo
  useEffect(() => {
    const timer = setTimeout(() => setConnected(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  // Game filtering logic
  const filteredGames = useMemo(() => {
    if (!games || games.length === 0) return [];

    const today = new Date();
    const todayDateString = today.toDateString();

    switch (gameFilter) {
      case 'live':
        return games.filter(g => g.status === 'live');
      case 'today':
        return games.filter(g => {
          if (g.status === 'live') return true;
          const gameDate = new Date(g.startTime || g.gameTime || 0);
          return gameDate.toDateString() === todayDateString;
        });
      case 'thisWeek':
        return games; // All games are this week in our data
      default:
        return games;
    }
  }, [games, gameFilter]);

  // Game counts for filter badges
  const gamesCount = useMemo(() => {
    const today = new Date().toDateString();
    return {
      total: games.length,
      live: gamesByStatus.live,
      today: games.filter(g => {
        if (g.status === 'live') return true;
        const gameDate = new Date(g.startTime || g.gameTime || 0);
        return gameDate.toDateString() === today;
      }).length,
      thisWeek: games.length
    };
  }, [games, gamesByStatus]);

  // Handle game card click
  const handleGameClick = (game) => {
    if (game.status === "scheduled") {
      setSelectedGame(game);
      setModalOpen(true);
    }
  };

  if (error) {
    return (
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50 dark:bg-neutral-900 grid place-items-center">
          <Card className="max-w-md">
            <CardHeader>
              <div className="flex items-center gap-2 text-red-600">
                <AlertTriangle className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Data Loading Error</h2>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">{error}</p>
              <div className="flex gap-2">
                <Button onClick={refreshGames} size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.location.reload()}
                >
                  Reload Page
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-neutral-900">
        <div className={`min-h-screen text-foreground ${wide ? "max-w-screen-2xl" : "max-w-7xl"} mx-auto p-4`}>

          {/* Header with clean components */}
          <NFLWeekHeader
            connected={connected}
            nflWeek={nflWeek}
            weekReset={weekReset}
            dataSource={dataSourceInfo}
          />

          {/* Controls */}
          <div className="flex items-center justify-between mb-6">
            <GameFilters
              gameFilter={gameFilter}
              setGameFilter={setGameFilter}
              gamesCount={gamesCount}
            />

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={refreshGames}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setDark(!dark)}
              >
                {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          {/* Main Content */}
          <Tabs defaultValue="games" className="w-full">
            <TabsList className="grid grid-cols-2 lg:grid-cols-4 w-full lg:w-auto">
              <TabsTrigger value="games">
                Games ({filteredGames.length})
              </TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="predictions">Predictions</TabsTrigger>
              <TabsTrigger value="insights">Insights</TabsTrigger>
            </TabsList>

            {/* Games Tab */}
            <TabsContent value="games" className="space-y-6">
              <div className="grid gap-6">
                {loading ? (
                  <div className="grid grid-cols-1 gap-6">
                    {[...Array(6)].map((_, i) => (
                      <Card key={i} className="animate-pulse">
                        <CardContent className="h-64 bg-muted/50" />
                      </Card>
                    ))}
                  </div>
                ) : (
                  <GameGrid
                    games={filteredGames}
                    onGameClick={handleGameClick}
                    showLiveSeparately={true}
                  />
                )}

                {/* Data Source Info */}
                {dataSourceInfo && (
                  <Card className="border-green-200 dark:border-green-800">
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                        <Zap className="h-4 w-4" />
                        <span>Using {dataSourceInfo.source} data source</span>
                        <Badge variant="outline" className="text-xs">
                          Real Scores: {dataSourceInfo.features.realScores ? '✅' : '❌'}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>

            {/* Other tabs - simplified for now */}
            <TabsContent value="analytics">
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Analytics Dashboard</h3>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Analytics features will be implemented in the next phase.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="predictions">
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Prediction Models</h3>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Prediction models dashboard coming soon.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="insights">
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Smart Insights</h3>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    AI-powered insights and recommendations.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Game Detail Modal */}
          <GameDetailModal
            game={selectedGame}
            isOpen={modalOpen}
            onClose={() => {
              setModalOpen(false);
              setSelectedGame(null);
            }}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}