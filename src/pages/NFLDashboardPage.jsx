import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Calendar, 
  RefreshCw, 
  BarChart3, 
  Trophy, 
  Zap, 
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Brain,
  Users
} from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';
import AIExpertVisualization from '@/components/nfl-dashboard/AIExpertVisualization';
import { useApiCache } from '@/hooks/useCache';
import { 
  SkipLink, 
  AccessibleCard, 
  ScreenReaderOnly, 
  LiveRegion,
  AccessibleButton
} from '@/components/accessibility/AccessibilityComponents';
import {
  getGameAccessibilityLabel,
  getSpreadAccessibilityLabel,
  getEVAccessibilityLabel,
  screenReaderUtils
} from '@/utils/accessibility';

const NFLDashboardPage = () => {
  const [activeTab, setActiveTab] = useState('games');
  const [week, setWeek] = useState(1);

  // Mock data for demonstration
  const mockGames = [
    {
      id: '2025_W1_GB_CHI',
      homeTeam: 'CHI',
      awayTeam: 'GB',
      startTime: '2025-09-07T13:00:00Z',
      status: 'scheduled',
      homeScore: 0,
      awayScore: 0,
      spread: -3.5,
      modelSpread: -2.5,
      spreadMovement: 1.0,
      overUnder: 45.5,
      modelTotal: 43.2,
      homeWinProb: 0.62,
      awayWinProb: 0.38,
      ev: 0.08,
      confidence: 0.72,
      weather: { temp: 72, wind: 8, humidity: 65 },
      venue: 'Soldier Field'
    },
    {
      id: '2025_W1_KC_BUF',
      homeTeam: 'BUF',
      awayTeam: 'KC',
      startTime: '2025-09-07T16:25:00Z',
      status: 'scheduled',
      homeScore: 0,
      awayScore: 0,
      spread: -2.5,
      modelSpread: -4.0,
      spreadMovement: -1.5,
      overUnder: 48.5,
      modelTotal: 46.8,
      homeWinProb: 0.58,
      awayWinProb: 0.42,
      ev: 0.12,
      confidence: 0.81,
      weather: { temp: 78, wind: 12, humidity: 55 },
      venue: 'Highmark Stadium'
    },
    {
      id: '2025_W1_SF_PIT',
      homeTeam: 'SF',
      awayTeam: 'PIT',
      startTime: '2025-09-07T20:20:00Z',
      status: 'scheduled',
      homeScore: 0,
      awayScore: 0,
      spread: -5.5,
      modelSpread: -4.0,
      spreadMovement: 1.5,
      overUnder: 42.5,
      modelTotal: 44.2,
      homeWinProb: 0.71,
      awayWinProb: 0.29,
      ev: 0.05,
      confidence: 0.65,
      weather: { temp: 68, wind: 5, humidity: 70 },
      venue: 'Levi\'s Stadium'
    }
  ];

  const mockPowerRankings = [
    { 
      team: 'KC', 
      rank: 1, 
      lastWeek: 1, 
      movement: 0, 
      record: '5-1', 
      elo: 1650, 
      trend: 'up',
      offensiveEPA: 0.25,
      defensiveEPA: -0.18,
      sos: 0.45
    },
    { 
      team: 'SF', 
      rank: 2, 
      lastWeek: 3, 
      movement: 1, 
      record: '4-2', 
      elo: 1625, 
      trend: 'up',
      offensiveEPA: 0.22,
      defensiveEPA: -0.15,
      sos: 0.52
    },
    { 
      team: 'BUF', 
      rank: 3, 
      lastWeek: 2, 
      movement: -1, 
      record: '4-2', 
      elo: 1615, 
      trend: 'down',
      offensiveEPA: 0.18,
      defensiveEPA: -0.20,
      sos: 0.48
    }
  ];

  const getEVColor = (ev) => {
    if (ev > 0.1) return 'text-green-400 bg-green-900/20';
    if (ev > 0.05) return 'text-blue-400 bg-blue-900/20';
    if (ev > 0) return 'text-yellow-400 bg-yellow-900/20';
    return 'text-gray-400 bg-gray-900/20';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return 'bg-blue-400';
    if (confidence > 0.6) return 'bg-yellow-400';
    if (confidence > 0.4) return 'bg-red-400';
    return 'bg-gray-400';
  };

  const getSpreadMovementIcon = (movement) => {
    if (movement > 0) return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (movement < 0) return <TrendingDown className="w-4 h-4 text-green-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const getMovementIcon = (movement) => {
    if (movement > 0) return <TrendingUp className="w-3 h-3 text-green-500" />;
    if (movement < 0) return <TrendingDown className="w-3 h-3 text-red-500" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  const getMovementColor = (movement) => {
    if (movement > 0) return 'text-green-400';
    if (movement < 0) return 'text-red-400';
    return 'text-gray-500';
  };

  const getEPAColor = (epa) => {
    if (epa > 0.2) return 'text-green-400';
    if (epa > 0.1) return 'text-blue-400';
    if (epa > 0) return 'text-yellow-400';
    return 'text-red-400';
  };

  // Check screen size for responsive design
  const [screenWidth, setScreenWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Announce data updates to screen readers
  useEffect(() => {
    if (games && games.length > 0) {
      screenReaderUtils.announce(
        `Dashboard updated with ${games.length} games for week ${week}`,
        'polite'
      );
    }
  }, [games, week]);

  // Render mobile version on small screens
  if (screenWidth < 768) {
    return (
      <div className="min-h-screen dashboard-bg dashboard-text p-2">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="dashboard-muted">Loading mobile version...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-4 md:p-6">
      <SkipLink targetId="main-content" />
      <LiveRegion id="live-region" priority="polite" />
      
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold dashboard-text">
              NFL Prediction Dashboard
            </h1>
            <p className="dashboard-muted">
              Data-driven predictions with expected value analysis
            </p>
            <ScreenReaderOnly>
              Navigate using tab key. Current view shows {games.length} games for week {week}.
            </ScreenReaderOnly>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <label htmlFor="week-select" className="dashboard-muted">Week:</label>
              <select 
                id="week-select"
                value={week} 
                onChange={(e) => setWeek(parseInt(e.target.value))}
                className="bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded-lg px-3 py-1 dashboard-text"
                aria-label="Select NFL week"
              >
                {[...Array(18)].map((_, i) => (
                  <option key={i + 1} value={i + 1} className="dashboard-bg">
                    {i + 1}
                  </option>
                ))}
              </select>
            </div>
            
            <AccessibleButton
              onClick={refreshGames}
              ariaLabel="Refresh dashboard data"
              className="flex items-center gap-2 px-3 py-2 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded-lg hover:opacity-80 transition-opacity"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              <span className="text-sm">Refresh</span>
            </AccessibleButton>
          </div>
        </header>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="dashboard-card p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-900/20 rounded-lg">
                <Zap className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-sm dashboard-muted">Games This Week</p>
                <p className="text-xl font-bold dashboard-text">{games.length}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="dashboard-card p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-900/20 rounded-lg">
                <BarChart3 className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <p className="text-sm dashboard-muted">High EV Plays</p>
                <p className="text-xl font-bold dashboard-text">
                  {games.filter(game => game.ev > 0.05).length}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="dashboard-card p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-900/20 rounded-lg">
                <Trophy className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-sm dashboard-muted">Model Accuracy</p>
                <p className="text-xl font-bold dashboard-text">68.2%</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="dashboard-card p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-900/20 rounded-lg">
                <RefreshCw className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-sm dashboard-muted">Last Updated</p>
                <p className="text-sm font-bold dashboard-text">
                  Just now
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Main Content Tabs */}
        <main id="main-content">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList 
              className="grid w-full grid-cols-5 mb-6 bg-[hsl(var(--dashboard-surface))]"
              role="tablist"
              aria-label="Dashboard navigation tabs"
            >
              <TabsTrigger 
                value="games" 
                className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white"
                role="tab"
                aria-controls="games-panel"
              >
                Games List
              </TabsTrigger>
              <TabsTrigger 
                value="ev" 
                className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white"
                role="tab"
                aria-controls="ev-panel"
              >
                EV Betting
              </TabsTrigger>
              <TabsTrigger 
                value="experts" 
                className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white"
                role="tab"
                aria-controls="experts-panel"
              >
                <Brain className="w-4 h-4 mr-2" aria-hidden="true" />
                AI Experts
              </TabsTrigger>
              <TabsTrigger 
                value="performance" 
                className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white"
                role="tab"
                aria-controls="performance-panel"
              >
                Performance
              </TabsTrigger>
              <TabsTrigger 
                value="rankings" 
                className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white"
                role="tab"
                aria-controls="rankings-panel"
              >
                Power Rankings
              </TabsTrigger>
            </TabsList>

          <TabsContent value="games" className="mt-0">
            <div className="space-y-4">
              {games.map((game, index) => (
                <motion.div
                  key={game.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="dashboard-card"
                >
                  <CardContent className="p-4">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                      {/* Game Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 dashboard-muted" />
                            <span className="text-sm dashboard-muted">
                              {formatDate(game.startTime)}
                            </span>
                          </div>
                          <div className="px-2 py-1 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded text-xs">
                            {formatTime(game.startTime)}
                          </div>
                        </div>

                        {/* Teams */}
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <TeamLogo 
                              teamAbbr={game.awayTeam} 
                              size="small" 
                              className="w-8 h-8"
                            />
                            <div>
                              <div className="font-semibold dashboard-text">
                                {game.awayTeam}
                              </div>
                              <div className="text-sm dashboard-muted">
                                {game.awayRecord || '0-0'}
                              </div>
                            </div>
                          </div>

                          <div className="text-center">
                            <div className="text-xs dashboard-muted">@</div>
                            <div className="text-xs dashboard-muted">{game.venue}</div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <div className="font-semibold dashboard-text">
                                {game.homeTeam}
                              </div>
                              <div className="text-sm dashboard-muted">
                                {game.homeRecord || '0-0'}
                              </div>
                            </div>
                            <TeamLogo 
                              teamAbbr={game.homeTeam} 
                              size="small" 
                              className="w-8 h-8"
                            />
                          </div>
                        </div>

                        {/* Weather */}
                        <div className="flex items-center gap-4 text-sm dashboard-muted">
                          <div className="flex items-center gap-1">
                            <span>{game.weather?.temp}°F</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span>{game.weather?.wind}mph</span>
                          </div>
                        </div>
                      </div>

                      {/* Spread Data */}
                      <div className="md:border-l md:border-gray-700 md:pl-4 min-w-[200px]">
                        <div className="space-y-3">
                          <div>
                            <div className="text-xs dashboard-muted mb-1">Market Spread</div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold dashboard-text">
                                {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
                              </span>
                              {getSpreadMovementIcon(game.spreadMovement)}
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-xs dashboard-muted mb-1">Model Spread</div>
                            <div className="font-semibold dashboard-text">
                              {game.homeTeam} {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Expected Value */}
                      <div className="md:border-l md:border-gray-700 md:pl-4 min-w-[150px]">
                        <div className="space-y-3">
                          <div>
                            <div className="text-xs dashboard-muted mb-1">Expected Value</div>
                            <div className={`text-lg font-bold px-2 py-1 rounded ${getEVColor(game.ev)}`}>
                              {(game.ev * 100).toFixed(1)}%
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-xs dashboard-muted mb-1">Confidence</div>
                            <div className="flex items-center gap-2">
                              <div className="w-full bg-gray-800 rounded-full h-2">
                                <div 
                                  className={`h-2 rounded-full ${getConfidenceColor(game.confidence)}`}
                                  style={{ width: `${game.confidence * 100}%` }}
                                />
                              </div>
                              <span className="text-xs font-medium dashboard-text">
                                {(game.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Win Probability */}
                      <div className="md:border-l md:border-gray-700 md:pl-4 min-w-[120px]">
                        <div className="space-y-3">
                          <div>
                            <div className="text-xs dashboard-muted mb-1">Win Probability</div>
                            <div className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span className="dashboard-text">{game.awayTeam}</span>
                                <span className="font-semibold dashboard-text">{(game.awayWinProb * 100).toFixed(0)}%</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="dashboard-text">{game.homeTeam}</span>
                                <span className="font-semibold dashboard-text">{(game.homeWinProb * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="ev" className="mt-0">
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold dashboard-text mb-2">
                  High Expected Value Plays
                </h2>
                <p className="dashboard-muted">
                  Games with positive expected value based on our model analysis
                </p>
              </div>
              
              <div className="space-y-6">
                {mockGames.filter(game => game.ev > 0.05).map((game, index) => (
                  <motion.div
                    key={game.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="dashboard-card"
                  >
                    <CardHeader className="pb-3">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <CardTitle className="text-lg flex items-center gap-2 dashboard-text">
                          <span>{game.awayTeam} @ {game.homeTeam}</span>
                          <div className="px-2 py-1 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded text-xs">
                            {formatTime(game.startTime)}
                          </div>
                        </CardTitle>
                        <div className={`px-2 py-1 rounded text-sm font-medium ${getEVColor(game.ev)}`}>
                          <span>EV: {(game.ev * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent className="space-y-4">
                      {/* Teams and Spread */}
                      <div className="flex items-center justify-between p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                        <div className="flex items-center gap-3">
                          <TeamLogo teamAbbr={game.awayTeam} size="small" className="w-10 h-10" />
                          <div>
                            <div className="font-semibold dashboard-text">{game.awayTeam}</div>
                            <div className="text-sm dashboard-muted">
                              {game.awayRecord || '0-0'}
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-center">
                          <div className="text-sm dashboard-muted">Spread</div>
                          <div className="text-lg font-bold dashboard-text">
                            {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
                          </div>
                          <div className="text-sm dashboard-muted">
                            Model: {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="font-semibold dashboard-text">{game.homeTeam}</div>
                            <div className="text-sm dashboard-muted">
                              {game.homeRecord || '0-0'}
                            </div>
                          </div>
                          <TeamLogo teamAbbr={game.homeTeam} size="small" className="w-10 h-10" />
                        </div>
                      </div>

                      {/* Betting Recommendation */}
                      <div className="p-3 rounded-lg border border-gray-700">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                          <div>
                            <h4 className="font-semibold dashboard-text">Betting Recommendation</h4>
                            <p className="text-sm dashboard-muted">
                              Based on EV and confidence analysis
                            </p>
                          </div>
                          <div className="px-3 py-1 bg-green-900/20 text-green-400 rounded">
                            {game.ev > 0.1 && game.confidence > 0.7 ? 'Strong Buy' : 
                             game.ev > 0.05 && game.confidence > 0.6 ? 'Buy' : 'Consider'}
                          </div>
                        </div>
                        
                        <div className="mt-3 grid grid-cols-2 gap-3">
                          <div className="text-center p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                            <div className="text-xs dashboard-muted">Confidence</div>
                            <div className="font-semibold dashboard-text">
                              {game.confidence > 0.8 ? 'High' : 
                               game.confidence > 0.6 ? 'Medium' : 
                               game.confidence > 0.4 ? 'Low' : 'Very Low'}
                            </div>
                            <div className="text-xs dashboard-muted">{(game.confidence * 100).toFixed(0)}%</div>
                          </div>
                          <div className="text-center p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                            <div className="text-xs dashboard-muted">Cover Probability</div>
                            <div className="font-semibold dashboard-text">
                              {game.spread > 0 ? 
                                (game.awayWinProb * 100).toFixed(0) : 
                                (game.homeWinProb * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Game Context */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div className="flex items-center gap-2 p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <Calendar className="w-4 h-4 dashboard-muted" />
                          <div>
                            <div className="text-xs dashboard-muted">Date</div>
                            <div className="text-sm font-medium dashboard-text">
                              {formatDate(game.startTime)}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <div>
                            <div className="text-xs dashboard-muted">Weather</div>
                            <div className="text-sm font-medium dashboard-text">
                              {game.weather?.temp}°F
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                          <div>
                            <div className="text-xs dashboard-muted">Wind</div>
                            <div className="text-sm font-medium dashboard-text">
                              {game.weather?.wind}mph
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Expected Units */}
                      <div className="p-3 bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold flex items-center gap-2 dashboard-text">
                              <Target className="w-4 h-4" />
                              Expected Units
                            </h4>
                            <p className="text-sm dashboard-muted">
                              Per $100 bet
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-green-400">
                              +${(game.ev * 100).toFixed(2)}
                            </div>
                            <div className="text-xs dashboard-muted">
                              per $100 wagered
                            </div>
                          </div>
                        </div>
                      </div>

                      <Button className="w-full dashboard-button-primary">
                        View Detailed Analysis
                      </Button>
                    </CardContent>
                  </motion.div>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="experts" className="mt-0">
            <AIExpertVisualization />
          </TabsContent>

          <TabsContent value="performance" className="mt-0">
            <div className="space-y-6">
              {/* Main Performance Card */}
              <Card className="dashboard-card">
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-purple-400" />
                      <CardTitle className="dashboard-text">ML Model Performance</CardTitle>
                    </div>
                    <div className="px-2 py-1 bg-purple-900/20 text-purple-400 rounded text-sm">
                      Neural Net v2.4
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Overall Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="text-center p-4 bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg"
                    >
                      <div className="text-3xl font-bold text-green-400">
                        73.2%
                      </div>
                      <div className="text-sm dashboard-muted">Overall Accuracy</div>
                      <div className="text-xs mt-1 flex items-center justify-center gap-1 dashboard-muted">
                        <TrendingUp className="w-3 h-3 text-green-500" />
                        1.4% from last week
                      </div>
                    </motion.div>

                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.1 }}
                      className="text-center p-4 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 rounded-lg"
                    >
                      <div className="text-3xl font-bold text-blue-400">
                        356/487
                      </div>
                      <div className="text-sm dashboard-muted">Correct Predictions</div>
                      <div className="text-xs mt-1 dashboard-muted">
                        12 pending
                      </div>
                    </motion.div>

                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.2 }}
                      className="text-center p-4 bg-gradient-to-br from-purple-900/20 to-pink-900/20 rounded-lg"
                    >
                      <div className="text-3xl font-bold text-purple-400">
                        +14.7%
                      </div>
                      <div className="text-sm dashboard-muted">ROI This Season</div>
                      <div className="text-xs mt-1 dashboard-muted">
                        $1,470 profit per $10k
                      </div>
                    </motion.div>
                  </div>

                  {/* Category Performance */}
                  <div className="space-y-4 mb-6">
                    <h3 className="text-lg font-semibold flex items-center gap-2 dashboard-text">
                      <BarChart3 className="w-5 h-5" />
                      Performance by Category
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        { name: 'Spread', accuracy: 68.5, count: 156, trend: 'up', best: 'Home Favorites' },
                        { name: 'Totals', accuracy: 71.3, count: 145, trend: 'down', best: 'Unders in Wind' },
                        { name: 'Moneyline', accuracy: 82.1, count: 186, trend: 'steady', best: 'Road Dogs' }
                      ].map((cat, index) => (
                        <motion.div
                          key={cat.name}
                          initial={{ y: 20, opacity: 0 }}
                          animate={{ y: 0, opacity: 1 }}
                          transition={{ delay: index * 0.1 }}
                          className="p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg border border-gray-700"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold dashboard-text">{cat.name}</h4>
                            <div className="flex items-center gap-1">
                              <span className="text-xs dashboard-muted">
                                {cat.count} picks
                              </span>
                              {cat.trend === 'up' ? 
                                <TrendingUp className="w-4 h-4 text-green-500" /> : 
                                cat.trend === 'down' ? 
                                <TrendingDown className="w-4 h-4 text-red-500" /> : 
                                <Minus className="w-4 h-4 text-gray-500" />
                              }
                            </div>
                          </div>
                          <div className="mb-2">
                            <div className="flex justify-between text-sm mb-1">
                              <span className="dashboard-muted">Accuracy</span>
                              <span className="font-semibold dashboard-text">{cat.accuracy}%</span>
                            </div>
                            <div className="w-full bg-gray-800 rounded-full h-2">
                              <div 
                                className="bg-blue-500 h-2 rounded-full" 
                                style={{ width: `${cat.accuracy}%` }}
                              />
                            </div>
                          </div>
                          <div className="text-xs dashboard-muted">
                            Best: {cat.best}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="rankings" className="mt-0">
            <div className="space-y-6">
              <Card className="dashboard-card">
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-yellow-400" />
                      <CardTitle className="dashboard-text">Power Rankings</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="px-2 py-1 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded text-xs dashboard-text">
                        Week 6
                      </div>
                      <div className="px-2 py-1 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded text-xs dashboard-text">
                        SOS Adjusted
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockPowerRankings.map((team, index) => (
                      <motion.div
                        key={team.team}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div className={`flex items-center justify-between p-4 rounded-lg ${
                          team.rank === 1 ? 'bg-gradient-to-r from-yellow-900/20 to-orange-900/20' : 'bg-[hsl(var(--dashboard-surface))]'
                        } border border-gray-700`}>
                          <div className="flex items-center gap-4">
                            {/* Rank */}
                            <div className="flex items-center gap-2 min-w-[60px]">
                              <div className="text-lg font-bold w-6 text-center dashboard-text">
                                {team.rank}
                              </div>
                              <div className="flex flex-col items-center">
                                {getMovementIcon(team.movement)}
                                {team.movement !== 0 && (
                                  <span className={`text-xs ${getMovementColor(team.movement)}`}>
                                    {Math.abs(team.movement)}
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Team Info */}
                            <div className="flex items-center gap-3">
                              <TeamLogo
                                teamAbbr={team.team}
                                size="medium"
                                className="w-10 h-10"
                              />
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold dashboard-text">{team.team}</span>
                                  {team.rank === 1 && <Trophy className="w-4 h-4 text-yellow-400" />}
                                </div>
                                <div className="text-sm dashboard-muted">{team.record}</div>
                              </div>
                            </div>
                          </div>

                          {/* Stats */}
                          <div className="hidden md:grid grid-cols-4 gap-6">
                            {/* ELO */}
                            <div className="text-right">
                              <div className="text-sm font-semibold dashboard-text">{Math.round(team.elo)}</div>
                              <div className="text-xs dashboard-muted">ELO</div>
                            </div>

                            {/* Offensive EPA */}
                            <div className="text-right">
                              <div className={`text-sm font-semibold ${getEPAColor(team.offensiveEPA)}`}>
                                +{team.offensiveEPA.toFixed(2)}
                              </div>
                              <div className="text-xs dashboard-muted">
                                Off EPA
                              </div>
                            </div>

                            {/* Defensive EPA */}
                            <div className="text-right">
                              <div className={`text-sm font-semibold ${getEPAColor(-team.defensiveEPA)}`}>
                                {team.defensiveEPA.toFixed(2)}
                              </div>
                              <div className="text-xs dashboard-muted">
                                Def EPA
                              </div>
                            </div>

                            {/* SOS */}
                            <div className="text-right">
                              <div className="text-sm font-semibold dashboard-text">
                                {(team.sos * 100).toFixed(0)}%
                              </div>
                              <div className="text-xs dashboard-muted">SOS</div>
                            </div>
                          </div>

                          {/* Mobile Stats */}
                          <div className="md:hidden text-right">
                            <div className="text-sm font-semibold dashboard-text">{Math.round(team.elo)} ELO</div>
                            <div className="flex items-center gap-1 justify-end">
                              {team.trend === 'up' ? 
                                <TrendingUp className="w-3 h-3 text-green-500" /> : 
                                team.trend === 'down' ? 
                                <TrendingDown className="w-3 h-3 text-red-500" /> : 
                                <Minus className="w-3 h-3 text-gray-400" />
                              }
                              <span className="text-xs dashboard-muted">Trend</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {/* Footer Stats */}
                  <div className="mt-6 p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-xs dashboard-muted mb-1">Biggest Rise</div>
                        <div className="font-semibold text-green-400 flex items-center justify-center gap-1">
                          <TrendingUp className="w-4 h-4" />
                          DET +2
                        </div>
                      </div>
                      <div>
                        <div className="text-xs dashboard-muted mb-1">Biggest Fall</div>
                        <div className="font-semibold text-red-400 flex items-center justify-center gap-1">
                          <TrendingDown className="w-4 h-4" />
                          BUF -1
                        </div>
                      </div>
                      <div>
                        <div className="text-xs dashboard-muted mb-1">Highest ELO</div>
                        <div className="font-semibold text-yellow-400 flex items-center justify-center gap-1">
                          <Zap className="w-4 h-4" />
                          KC 1650
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* EPA Statistics Explanation */}
              <Card className="dashboard-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 dashboard-text">
                    <Target className="w-5 h-5" />
                    EPA Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-900/20 rounded-lg">
                      <h4 className="font-semibold mb-2 dashboard-text">Expected Points Added (EPA)</h4>
                      <p className="text-sm dashboard-muted">
                        Measures the expected points contributed by each play. Positive values indicate plays that improved the team's position.
                      </p>
                    </div>
                    <div className="p-4 bg-green-900/20 rounded-lg">
                      <h4 className="font-semibold mb-2 dashboard-text">Offensive EPA</h4>
                      <p className="text-sm dashboard-muted">
                        Average EPA per play for the offense. Higher values indicate more effective offensive performance.
                      </p>
                    </div>
                    <div className="p-4 bg-red-900/20 rounded-lg">
                      <h4 className="font-semibold mb-2 dashboard-text">Defensive EPA</h4>
                      <p className="text-sm dashboard-muted">
                        Average EPA per play against the defense. Lower (more negative) values indicate stronger defensive performance.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
        </main>
      </div>
    </div>
  );
};

export default NFLDashboardPage;