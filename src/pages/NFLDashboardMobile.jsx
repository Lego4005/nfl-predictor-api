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
  Users,
  Menu,
  X
} from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';
import AIExpertVisualization from '@/components/nfl-dashboard/AIExpertVisualization';
import { useApiCache } from '@/hooks/useCache';

const NFLDashboardMobile = () => {
  const [activeTab, setActiveTab] = useState('games');
  const [week, setWeek] = useState(1);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [screenWidth, setScreenWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

  // Use cached data instead of mock data
  const [games, setGames, gamesLoading, refreshGames] = useApiCache(
    `/games/2025/${week}`, 
    'games', 
    [
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
      }
    ]
  );

  const [powerRankings, setPowerRankings, rankingsLoading, refreshRankings] = useApiCache(
    `/rankings/2025/${week}`, 
    'rankings', 
    [
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
      }
    ]
  );

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Only show mobile version on small screens
  if (screenWidth >= 768) {
    return null;
  }

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

  const refreshAllData = () => {
    refreshGames();
    refreshRankings();
  };

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-2">
      {/* Header with menu button */}
      <div className="flex items-center justify-between mb-4 p-2">
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-2"
          >
            {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
          <h1 className="text-lg font-bold dashboard-text">NFL Dashboard</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <select 
            value={week} 
            onChange={(e) => setWeek(parseInt(e.target.value))}
            className="bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded px-2 py-1 text-sm dashboard-text"
          >
            {[...Array(18)].map((_, i) => (
              <option key={i + 1} value={i + 1} className="dashboard-bg">
                W{i + 1}
              </option>
            ))}
          </select>
          
          <Button variant="ghost" size="sm" className="p-2" onClick={refreshAllData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg"
        >
          <TabsList className="grid w-full grid-cols-5 bg-[hsl(var(--dashboard-bg))] mb-2">
            <TabsTrigger 
              value="games" 
              onClick={() => { setActiveTab('games'); setIsMenuOpen(false); }}
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              Games
            </TabsTrigger>
            <TabsTrigger 
              value="ev" 
              onClick={() => { setActiveTab('ev'); setIsMenuOpen(false); }}
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              EV
            </TabsTrigger>
            <TabsTrigger 
              value="experts" 
              onClick={() => { setActiveTab('experts'); setIsMenuOpen(false); }}
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              <Brain className="w-3 h-3 mx-auto" />
            </TabsTrigger>
            <TabsTrigger 
              value="performance" 
              onClick={() => { setActiveTab('performance'); setIsMenuOpen(false); }}
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              Perf
            </TabsTrigger>
            <TabsTrigger 
              value="rankings" 
              onClick={() => { setActiveTab('rankings'); setIsMenuOpen(false); }}
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              Rank
            </TabsTrigger>
          </TabsList>
        </motion.div>
      )}

      {/* Stats Overview - Condensed for mobile */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <div className="dashboard-stat-mobile">
          <Zap className="w-4 h-4 text-blue-400 mb-1" />
          <div className="text-xs font-bold dashboard-text">{games.length}</div>
          <div className="text-xs dashboard-muted">Games</div>
        </div>

        <div className="dashboard-stat-mobile">
          <BarChart3 className="w-4 h-4 text-green-400 mb-1" />
          <div className="text-xs font-bold dashboard-text">
            {games.filter(game => game.ev > 0.05).length}
          </div>
          <div className="text-xs dashboard-muted">EV+</div>
        </div>

        <div className="dashboard-stat-mobile">
          <Trophy className="w-4 h-4 text-purple-400 mb-1" />
          <div className="text-xs font-bold dashboard-text">68.2%</div>
          <div className="text-xs dashboard-muted">Acc</div>
        </div>

        <div className="dashboard-stat-mobile">
          <RefreshCw className="w-4 h-4 text-amber-400 mb-1" />
          <div className="text-xs font-bold dashboard-text">Now</div>
          <div className="text-xs dashboard-muted">Updated</div>
        </div>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        {!isMenuOpen && (
          <TabsList className="grid w-full grid-cols-5 bg-[hsl(var(--dashboard-surface))] mb-4">
            <TabsTrigger 
              value="games" 
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              Games
            </TabsTrigger>
            <TabsTrigger 
              value="ev" 
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              EV
            </TabsTrigger>
            <TabsTrigger 
              value="experts" 
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              <Brain className="w-3 h-3 mx-auto" />
            </TabsTrigger>
            <TabsTrigger 
              value="performance" 
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              Perf
            </TabsTrigger>
            <TabsTrigger 
              value="rankings" 
              className="data-[state=active]:bg-[hsl(var(--dashboard-primary))] data-[state=active]:text-white text-xs p-2"
            >
              Rank
            </TabsTrigger>
          </TabsList>
        )}

        <TabsContent value="games" className="mt-0">
          <div className="space-y-3">
            {games.map((game, index) => (
              <motion.div
                key={game.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="dashboard-card p-3"
              >
                {/* Game Header */}
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3 h-3 dashboard-muted" />
                    <span className="text-xs dashboard-muted">
                      {formatDate(game.startTime)}
                    </span>
                  </div>
                  <div className="px-2 py-1 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded text-xs">
                    {formatTime(game.startTime)}
                  </div>
                </div>

                {/* Teams */}
                <div className="flex items-center justify-between mb-3">
                  <div className="dashboard-team-info-mobile">
                    <TeamLogo 
                      teamAbbr={game.awayTeam} 
                      size="small" 
                      className="w-8 h-8"
                    />
                    <div className="font-semibold text-sm dashboard-text">
                      {game.awayTeam}
                    </div>
                    <div className="text-xs dashboard-muted">
                      {game.awayRecord || '0-0'}
                    </div>
                  </div>

                  <div className="text-center">
                    <div className="text-xs dashboard-muted">@</div>
                    <div className="text-xs dashboard-muted max-w-[60px] truncate">
                      {game.venue}
                    </div>
                  </div>

                  <div className="dashboard-team-info-mobile">
                    <TeamLogo 
                      teamAbbr={game.homeTeam} 
                      size="small" 
                      className="w-8 h-8"
                    />
                    <div className="font-semibold text-sm dashboard-text">
                      {game.homeTeam}
                    </div>
                    <div className="text-xs dashboard-muted">
                      {game.homeRecord || '0-0'}
                    </div>
                  </div>
                </div>

                {/* Mobile Spread Info */}
                <div className="dashboard-spread-mobile mb-3">
                  <div>
                    <div className="text-xs dashboard-muted">Spread</div>
                    <div className="flex items-center gap-1">
                      <span className="text-sm font-semibold dashboard-text">
                        {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
                      </span>
                      {getSpreadMovementIcon(game.spreadMovement)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs dashboard-muted">Model</div>
                    <div className="text-sm font-semibold dashboard-text">
                      {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
                    </div>
                  </div>
                </div>

                {/* Mobile EV and Confidence */}
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="text-xs dashboard-muted">EV</div>
                    <div className={`text-sm font-bold ${getEVColor(game.ev)}`}>
                      {(game.ev * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="text-xs dashboard-muted">Conf</div>
                    <div className="flex items-center gap-1">
                      <div className="w-full bg-gray-800 rounded-full h-1.5">
                        <div 
                          className={`h-1.5 rounded-full ${getConfidenceColor(game.confidence)}`}
                          style={{ width: `${game.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium dashboard-text">
                        {(game.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Win Probability */}
                <div className="flex justify-between">
                  <div className="text-center">
                    <div className="text-xs dashboard-muted">{game.awayTeam}</div>
                    <div className="text-sm font-semibold dashboard-text">
                      {(game.awayWinProb * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs dashboard-muted">Win Prob</div>
                    <div className="text-sm dashboard-muted">vs</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs dashboard-muted">{game.homeTeam}</div>
                    <div className="text-sm font-semibold dashboard-text">
                      {(game.homeWinProb * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="ev" className="mt-0">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-bold dashboard-text mb-2">
                High EV Plays
              </h2>
              <p className="text-xs dashboard-muted">
                Positive expected value games
              </p>
            </div>
            
            <div className="space-y-4">
              {games.filter(game => game.ev > 0.05).map((game, index) => (
                <motion.div
                  key={game.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="dashboard-card p-3"
                >
                  <div className="flex justify-between items-center mb-3">
                    <div className="font-semibold dashboard-text">
                      {game.awayTeam} @ {game.homeTeam}
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${getEVColor(game.ev)}`}>
                      EV: {(game.ev * 100).toFixed(1)}%
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbr={game.awayTeam} size="small" className="w-8 h-8" />
                      <div>
                        <div className="font-semibold text-sm dashboard-text">{game.awayTeam}</div>
                        <div className="text-xs dashboard-muted">{game.awayRecord || '0-0'}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 justify-end">
                      <div className="text-right">
                        <div className="font-semibold text-sm dashboard-text">{game.homeTeam}</div>
                        <div className="text-xs dashboard-muted">{game.homeRecord || '0-0'}</div>
                      </div>
                      <TeamLogo teamAbbr={game.homeTeam} size="small" className="w-8 h-8" />
                    </div>
                  </div>

                  <div className="dashboard-spread-mobile mb-3">
                    <div>
                      <div className="text-xs dashboard-muted">Spread</div>
                      <div className="text-sm font-semibold dashboard-text">
                        {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs dashboard-muted">Model</div>
                      <div className="text-sm font-semibold dashboard-text">
                        {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
                      </div>
                    </div>
                  </div>

                  <div className="p-2 bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded">
                    <div className="flex justify-between items-center">
                      <div className="text-xs dashboard-muted">Expected Units</div>
                      <div className="text-sm font-bold text-green-400">
                        +${(game.ev * 100).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="experts" className="mt-0">
          <AIExpertVisualization />
        </TabsContent>

        <TabsContent value="performance" className="mt-0">
          <div className="p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
            <h3 className="font-semibold dashboard-text mb-3">Model Performance</h3>
            <div className="space-y-3">
              <div className="p-3 bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded">
                <div className="text-lg font-bold text-green-400 text-center">
                  73.2%
                </div>
                <div className="text-xs dashboard-muted text-center">Overall Accuracy</div>
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 rounded">
                  <div className="text-sm font-bold text-blue-400 text-center">
                    356/487
                  </div>
                  <div className="text-xs dashboard-muted text-center">Correct</div>
                </div>
                
                <div className="p-2 bg-gradient-to-br from-purple-900/20 to-pink-900/20 rounded">
                  <div className="text-sm font-bold text-purple-400 text-center">
                    +14.7%
                  </div>
                  <div className="text-xs dashboard-muted text-center">ROI</div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="rankings" className="mt-0">
          <div className="space-y-3">
            {powerRankings.map((team, index) => (
              <motion.div
                key={team.team}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="dashboard-card p-3"
              >
                <div className="flex items-center gap-3">
                  <div className="text-lg font-bold w-6 text-center dashboard-text">
                    {team.rank}
                  </div>
                  
                  <TeamLogo
                    teamAbbr={team.team}
                    size="small"
                    className="w-8 h-8"
                  />
                  
                  <div className="flex-1">
                    <div className="font-semibold dashboard-text">{team.team}</div>
                    <div className="text-xs dashboard-muted">{team.record}</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm font-semibold dashboard-text">{Math.round(team.elo)}</div>
                    <div className="text-xs dashboard-muted">ELO</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NFLDashboardMobile;