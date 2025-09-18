import React, { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { supabaseHelpers } from "../services/supabaseClient";
import dataIntegrationService from "../services/dataIntegrationService";
import realtimeService from "../services/realtimeService";
import newsService from "../services/newsService";
import oddsService from "../services/oddsService";
import EnhancedGameCardV2 from "./EnhancedGameCardV2";
import GameDetailModal from "./GameDetailModal";
import SmartInsights from "./SmartInsights";
import NewsFeed from "./NewsFeed";
import PowerRankings from "./PowerRankings";
import ModelPerformance from "./ModelPerformance";
import DataTest from "./DataTest";

import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Moon,
  Sun,
  RefreshCw,
  Wifi,
  WifiOff,
  LineChart,
  Users,
  PlayCircle,
  Shield,
  Gauge,
  Zap,
  Database,
  Radio,
} from "lucide-react";

// shadcn/ui components
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function NFLDashboardLive() {
  // State management
  const [games, setGames] = useState([]);
  const [news, setNews] = useState([]);
  const [odds, setOdds] = useState({});
  const [loading, setLoading] = useState(true);
  const [showAdmin, setShowAdmin] = useState(false);
  const [error, setError] = useState(null);
  const [selectedGame, setSelectedGame] = useState(null);
  const [darkMode, setDarkMode] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [syncStatus, setSyncStatus] = useState({ inProgress: false, lastSync: null });
  const [liveCount, setLiveCount] = useState(0);
  const [subscriptions, setSubscriptions] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState({
    isConnected: false,
    activeSubscriptions: 0,
    retryCount: 0
  });
  const [expertBets, setExpertBets] = useState([]);
  const [expertResearch, setExpertResearch] = useState([]);

  // Initialize data on mount
  useEffect(() => {
    loadInitialData();
    setupRealtimeSubscriptions();

    // Start auto-sync if enabled
    if (autoRefresh) {
      dataIntegrationService.startAutoSync(5); // Every 5 minutes
    }

    return () => {
      // Cleanup subscriptions
      if (subscriptions?.realtime) {
        subscriptions.realtime.unsubscribeAll();
      }
      if (subscriptions?.dataIntegration) {
        subscriptions.dataIntegration.unsubscribeAll();
      }

      // Stop auto-sync
      dataIntegrationService.stopAutoSync();

      // Cleanup realtime service
      realtimeService.unsubscribeAll();
    };
  }, []);

  // Load initial data from Supabase
  const loadInitialData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch games with predictions and odds
      const { data: gamesData, error: gamesError } = await supabaseHelpers.getCurrentGames();

      if (gamesError) throw gamesError;

      // Transform games data to match component expectations
      const transformedGames = (gamesData || []).map(game => ({
        id: game.id,
        homeTeam: game.home_team,
        awayTeam: game.away_team,
        homeScore: game.home_score,
        awayScore: game.away_score,
        status: game.status,
        quarter: game.quarter,
        clock: game.time_remaining,
        startTime: new Date(game.game_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        venue: game.venue,
        weather: game.weather_data,
        odds: game.odds_data,
        espnId: game.espn_game_id,
        week: game.week,
        // Predictions will be fetched separately
        homePred: 50,
        awayPred: 50,
        confidence: 75
      }));

      setGames(transformedGames);

      // Count live games
      const liveGames = transformedGames.filter(g => g.status === 'live').length;
      setLiveCount(liveGames);

      // Fetch news data
      const { data: newsData } = await newsService.getTeamSentiment(['NFL']);
      if (newsData) {
        setNews(newsData.articles || []);
      }

      // Get sync status
      const status = dataIntegrationService.getSyncStatus();
      setSyncStatus(status);

    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data. Please try refreshing.');
    } finally {
      setLoading(false);
    }
  };

  // Setup real-time subscriptions
  const setupRealtimeSubscriptions = () => {
    // Enhanced real-time subscriptions using the new realtimeService
    const realtimeSubs = realtimeService.subscribeToAllUpdates({
      onGameUpdate: (payload) => {
        console.log('🏈 Real-time game update:', payload);

        if (payload.eventType === 'UPDATE' && payload.new) {
          // Update specific game in real-time
          setGames(prevGames => prevGames.map(game => {
            if (game.id === payload.new.id) {
              return {
                ...game,
                homeScore: payload.new.home_score || game.homeScore,
                awayScore: payload.new.away_score || game.awayScore,
                status: payload.new.status || game.status,
                quarter: payload.new.quarter || game.quarter,
                clock: payload.new.time_remaining || game.clock,
                weather: payload.new.weather_data || game.weather,
              };
            }
            return game;
          }));
        }
      },

      onPredictionUpdate: (payload) => {
        console.log('🤖 Real-time prediction update:', payload);

        if (payload.new) {
          updateGamePrediction(payload.new);
        }
      },

      onExpertBetUpdate: (payload) => {
        console.log('💰 Real-time expert bet update:', payload);

        if (payload.eventType === 'INSERT' && payload.new) {
          // Add new expert bet to the list
          setExpertBets(prevBets => [payload.new, ...prevBets.slice(0, 99)]); // Keep latest 100
        }
      },

      onNewsUpdate: (payload) => {
        console.log('📰 Real-time news update:', payload);

        if (payload.eventType === 'INSERT' && payload.new) {
          // Add new news article
          setNews(prevNews => [payload.new, ...prevNews.slice(0, 49)]); // Keep latest 50
        }
      },

      onOddsUpdate: (payload) => {
        console.log('💸 Real-time odds update:', payload);

        if (payload.new) {
          updateGameOdds(payload.new);
        }
      },

      onExpertResearchUpdate: (payload) => {
        console.log('🔍 Real-time expert research update:', payload);

        if (payload.eventType === 'INSERT' && payload.new) {
          // Add new expert research
          setExpertResearch(prevResearch => [payload.new, ...prevResearch.slice(0, 29)]); // Keep latest 30
        }
      },

      onConnectionChange: (status) => {
        console.log('🔌 Connection status change:', status);
        setConnectionStatus({
          isConnected: status.isConnected,
          activeSubscriptions: realtimeService.getConnectionStatus().activeSubscriptions,
          retryCount: status.error ? connectionStatus.retryCount + 1 : 0
        });
      }
    });

    // Also keep the original data integration subscriptions for compatibility
    const dataSubs = dataIntegrationService.subscribeToAllUpdates({
      onGameUpdate: (payload) => {
        console.log('🔄 Data integration game update:', payload);
      }
    });

    setSubscriptions({ realtime: realtimeSubs, dataIntegration: dataSubs });

    // Update connection status
    const status = realtimeService.getConnectionStatus();
    setConnectionStatus(status);
  };

  // Update a specific game's prediction
  const updateGamePrediction = (prediction) => {
    setGames(prevGames => prevGames.map(game => {
      if (game.id === prediction.game_id) {
        return {
          ...game,
          homePred: prediction.home_win_prob,
          awayPred: prediction.away_win_prob,
          confidence: prediction.confidence
        };
      }
      return game;
    }));
  };

  // Update a specific game's odds
  const updateGameOdds = (oddsUpdate) => {
    setGames(prevGames => prevGames.map(game => {
      if (game.id === oddsUpdate.game_id) {
        return {
          ...game,
          odds: {
            ...game.odds,
            spread: oddsUpdate.spread_home,
            total: oddsUpdate.total_over,
            updated: new Date().toISOString()
          }
        };
      }
      return game;
    }));
  };

  // Manual sync trigger
  const triggerManualSync = async () => {
    setSyncStatus({ ...syncStatus, inProgress: true });

    try {
      const result = await dataIntegrationService.performFullSync();
      console.log('Sync complete:', result);

      // Reload data after sync
      await loadInitialData();

      setSyncStatus({
        inProgress: false,
        lastSync: new Date(),
        result
      });
    } catch (error) {
      console.error('Sync failed:', error);
      setSyncStatus({
        inProgress: false,
        lastSync: new Date(),
        error: error.message
      });
    }
  };

  // Toggle auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      dataIntegrationService.startAutoSync(5);
    } else {
      dataIntegrationService.stopAutoSync();
    }
  }, [autoRefresh]);

  // Group games by status
  const gamesByStatus = useMemo(() => {
    const live = games.filter(g => g.status === 'live');
    const upcoming = games.filter(g => g.status === 'scheduled');
    const final = games.filter(g => g.status === 'final');

    return { live, upcoming, final };
  }, [games]);

  // Loading state
  if (loading) {
    return (
      <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <div className="space-y-4">
              <Skeleton className="h-12 w-48" />
              <Skeleton className="h-8 w-64" />
              <div className="flex gap-4">
                <Skeleton className="h-32 w-64" />
                <Skeleton className="h-32 w-64" />
                <Skeleton className="h-32 w-64" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'}`}>
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-800/50 backdrop-blur">
        <div className="container mx-auto p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
                NFL Predictor Live
              </h1>
              <Badge variant={liveCount > 0 ? "destructive" : "secondary"} className="animate-pulse">
                {liveCount > 0 ? `${liveCount} LIVE` : 'No Live Games'}
              </Badge>
            </div>

            <div className="flex items-center gap-4">
              {/* Sync Status */}
              <div className="flex items-center gap-2">
                {syncStatus.inProgress ? (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    Syncing...
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-xs">
                    {syncStatus.lastSync
                      ? `Last sync: ${new Date(syncStatus.lastSync).toLocaleTimeString()}`
                      : 'Not synced'}
                  </Badge>
                )}
              </div>

              {/* Manual Sync Button */}
              <Button
                size="sm"
                variant="outline"
                onClick={triggerManualSync}
                disabled={syncStatus.inProgress}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${syncStatus.inProgress ? 'animate-spin' : ''}`} />
                Sync Data
              </Button>

              {/* ADMIN DASHBOARD BUTTON */}
              <Button
                size="sm"
                className="bg-red-500 hover:bg-red-600 text-white font-bold"
                onClick={() => {
                  // Navigate to admin dashboard
                  window.location.href = '/?admin=true';
                }}
              >
                🧠 Expert Observatory
              </Button>

              {/* Auto Refresh Toggle */}
              <div className="flex items-center gap-2">
                <label htmlFor="auto-refresh" className="text-sm">Auto Refresh</label>
                <Switch
                  id="auto-refresh"
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                />
              </div>

              {/* Dark Mode Toggle */}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setDarkMode(!darkMode)}
              >
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <main className="container mx-auto p-6">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid grid-cols-8 w-full max-w-4xl mx-auto">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="live">
              Live {liveCount > 0 && `(${liveCount})`}
            </TabsTrigger>
            <TabsTrigger value="predictions">Predictions</TabsTrigger>
            <TabsTrigger value="betting">Betting</TabsTrigger>
            <TabsTrigger value="experts">
              Experts {expertBets.length > 0 && `(${expertBets.length})`}
            </TabsTrigger>
            <TabsTrigger value="news">News</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="data">Data Test</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Connection Status */}
            <div className="grid grid-cols-3 gap-4">
              <Card>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-green-500" />
                    <span className="font-medium">Database</span>
                  </div>
                  <Badge variant="success">Connected</Badge>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-2">
                    <Wifi className="w-5 h-5 text-blue-500" />
                    <span className="font-medium">APIs</span>
                  </div>
                  <Badge variant="success">3 Active</Badge>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-2">
                    {connectionStatus.isConnected ? (
                      <Radio className="w-5 h-5 text-green-500" />
                    ) : (
                      <Radio className="w-5 h-5 text-red-500" />
                    )}
                    <span className="font-medium">Real-time</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <Badge variant={connectionStatus.isConnected ? "success" : "destructive"}>
                      {connectionStatus.isConnected ? "Connected" : "Disconnected"}
                    </Badge>
                    <span className="text-xs text-muted-foreground mt-1">
                      {connectionStatus.activeSubscriptions} streams
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Smart Insights */}
            <SmartInsights games={games} />

            {/* Games Grid */}
            <div>
              <h2 className="text-xl font-semibold mb-4">All Games</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {games.map((game) => (
                  <EnhancedGameCardV2
                    key={game.id}
                    game={game}
                    onClick={() => setSelectedGame(game)}
                  />
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Live Tab */}
          <TabsContent value="live" className="space-y-6">
            {gamesByStatus.live.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {gamesByStatus.live.map((game) => (
                  <EnhancedGameCardV2
                    key={game.id}
                    game={game}
                    onClick={() => setSelectedGame(game)}
                    isLive
                  />
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-muted-foreground">No live games at the moment</p>
                  <p className="text-sm mt-2">Check back during game time!</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Predictions Tab */}
          <TabsContent value="predictions" className="space-y-6">
            <PowerRankings teams={games} />
            <ModelPerformance />
          </TabsContent>

          {/* Betting Tab */}
          <TabsContent value="betting" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {gamesByStatus.upcoming.slice(0, 6).map((game) => (
                <Card key={game.id}>
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <h3 className="font-semibold">
                        {game.awayTeam} @ {game.homeTeam}
                      </h3>
                      <Badge variant="outline">{game.startTime}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Spread</span>
                        <span className="font-mono">
                          {game.odds?.consensus_spread || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Total</span>
                        <span className="font-mono">
                          {game.odds?.consensus_total || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">ML Home</span>
                        <span className="font-mono">
                          {game.odds?.consensus_ml_home ? `+${game.odds.consensus_ml_home}` : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Experts Tab - Real-time Expert Activities */}
          <TabsContent value="experts" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Expert Bets */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Zap className="w-5 h-5" />
                      Live Expert Bets
                    </h3>
                    <Badge variant="outline">{expertBets.length} Active</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {expertBets.length > 0 ? (
                      expertBets.slice(0, 5).map((bet, index) => (
                        <div key={bet.id || index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-sm">{bet.expert_id}</span>
                              <Badge variant="outline" className="text-xs">
                                {bet.bet_type}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {bet.reasoning?.substring(0, 100)}...
                            </p>
                          </div>
                          <div className="text-right ml-4">
                            <div className="font-mono text-sm font-bold">
                              {bet.bet_value > 0 ? `+${bet.bet_value}` : bet.bet_value}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {bet.confidence_level}% conf
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-center text-muted-foreground py-8">
                        No expert bets yet. Experts will appear here when they make predictions.
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Expert Research Activity */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Activity className="w-5 h-5" />
                      Research Activity
                    </h3>
                    <Badge variant="outline">{expertResearch.length} Items</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {expertResearch.length > 0 ? (
                      expertResearch.slice(0, 5).map((research, index) => (
                        <div key={research.id || index} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-sm">{research.expert_id}</span>
                              <Badge variant="outline" className="text-xs">
                                {research.research_type}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {research.content?.substring(0, 120)}...
                            </p>
                            <span className="text-xs text-muted-foreground">
                              {research.created_at ? new Date(research.created_at).toLocaleTimeString() : 'Now'}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-center text-muted-foreground py-8">
                        No research activity yet. Expert analysis will appear here in real-time.
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Expert Performance Summary */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Expert Council Performance
                </h3>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{expertBets.filter(b => b.is_winner).length}</p>
                    <p className="text-sm text-muted-foreground">Winning Bets</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-600">{expertBets.filter(b => b.is_winner === false).length}</p>
                    <p className="text-sm text-muted-foreground">Losing Bets</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{expertBets.reduce((sum, b) => sum + (b.points_won || 0), 0)}</p>
                    <p className="text-sm text-muted-foreground">Total Points</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {expertBets.length > 0 ? Math.round((expertBets.filter(b => b.is_winner).length / expertBets.length) * 100) : 0}%
                    </p>
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* News Tab */}
          <TabsContent value="news" className="space-y-6">
            <NewsFeed />
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">System Analytics</h3>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Games</p>
                    <p className="text-2xl font-bold">{games.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">News Articles</p>
                    <p className="text-2xl font-bold">{news.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Predictions Made</p>
                    <p className="text-2xl font-bold">
                      {games.filter(g => g.confidence > 0).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Data Test Tab */}
          <TabsContent value="data" className="space-y-6">
            <DataTest />
          </TabsContent>
        </Tabs>
      </main>

      {/* Game Detail Modal */}
      {selectedGame && (
        <GameDetailModal
          game={selectedGame}
          isOpen={!!selectedGame}
          onClose={() => setSelectedGame(null)}
        />
      )}
    </div>
  );
}