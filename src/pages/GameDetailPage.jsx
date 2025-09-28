import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Calendar, 
  Clock, 
  Cloud, 
  Wind, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Target,
  BarChart3,
  Users,
  Shield,
  Sword,
  RefreshCw
} from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';
import { useApiCache } from '@/hooks/useCache';

const GameDetailPage = ({ gameId }) => {
  const [week, setWeek] = useState(1);
  
  // Use cached data instead of mock data
  const [game, setGame, loading, refreshGame] = useApiCache(
    `/games/2025/${week}/${gameId || 'GB_CHI'}`, 
    'games', 
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
      venue: 'Soldier Field',
      homeTeamStats: {
        record: '3-2',
        elo: 1580,
        offensiveEPA: 0.15,
        defensiveEPA: -0.12,
        sos: 0.48
      },
      awayTeamStats: {
        record: '4-1',
        elo: 1620,
        offensiveEPA: 0.22,
        defensiveEPA: -0.18,
        sos: 0.52
      },
      qbMatchup: {
        home: { name: 'Caleb Williams', rating: 85, epa: 0.18 },
        away: { name: 'Jordan Love', rating: 78, epa: 0.15 }
      },
      marketFactors: [
        'Home team rested well',
        'Away team playing on short rest',
        'Neutral weather conditions'
      ]
    }
  );

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

  const getEPAColor = (epa) => {
    if (epa > 0.2) return 'text-green-400';
    if (epa > 0.1) return 'text-blue-400';
    if (epa > 0) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="min-h-screen dashboard-bg dashboard-text p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold dashboard-text">
              Game Detail: {game.awayTeam} @ {game.homeTeam}
            </h1>
            <p className="dashboard-muted">
              Detailed analysis and predictions for this matchup
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="dashboard-muted">Week:</span>
              <select 
                value={week} 
                onChange={(e) => setWeek(parseInt(e.target.value))}
                className="bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded-lg px-3 py-1 dashboard-text"
              >
                {[...Array(18)].map((_, i) => (
                  <option key={i + 1} value={i + 1} className="dashboard-bg">
                    {i + 1}
                  </option>
                ))}
              </select>
            </div>
            
            <Button
              onClick={refreshGame}
              className="flex items-center gap-2 px-3 py-2 bg-[hsl(var(--dashboard-surface))] border border-gray-700 rounded-lg hover:opacity-80 transition-opacity"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="text-sm">Refresh</span>
            </Button>
            
            <Badge variant="outline" className="bg-[hsl(var(--dashboard-surface))] border-gray-700 text-xs dashboard-text">
              {formatDate(game.startTime)}
            </Badge>
            <Badge variant="outline" className="bg-[hsl(var(--dashboard-surface))] border-gray-700 text-xs dashboard-text">
              {formatTime(game.startTime)}
            </Badge>
          </div>
        </div>

        {/* Main Content - Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Model Projections and Win Probabilities */}
          <div className="space-y-6">
            {/* Game Info Card */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <Target className="w-5 h-5" />
                  Game Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                  <div className="flex items-center gap-3">
                    <TeamLogo 
                      teamAbbr={game.awayTeam} 
                      size="medium" 
                      className="w-12 h-12"
                    />
                    <div>
                      <div className="font-semibold dashboard-text text-lg">
                        {game.awayTeam}
                      </div>
                      <div className="text-sm dashboard-muted">
                        {game.awayTeamStats.record}
                      </div>
                    </div>
                  </div>

                  <div className="text-center">
                    <div className="text-xs dashboard-muted">@</div>
                    <div className="text-xs dashboard-muted">{game.venue}</div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="font-semibold dashboard-text text-lg">
                        {game.homeTeam}
                      </div>
                      <div className="text-sm dashboard-muted">
                        {game.homeTeamStats.record}
                      </div>
                    </div>
                    <TeamLogo 
                      teamAbbr={game.homeTeam} 
                      size="medium" 
                      className="w-12 h-12"
                    />
                  </div>
                </div>

                {/* Weather */}
                <div className="grid grid-cols-3 gap-3 mt-4">
                  <div className="flex items-center gap-2 p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <Cloud className="w-4 h-4 dashboard-muted" />
                    <div>
                      <div className="text-xs dashboard-muted">Temperature</div>
                      <div className="text-sm font-medium dashboard-text">
                        {game.weather?.temp}°F
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <Wind className="w-4 h-4 dashboard-muted" />
                    <div>
                      <div className="text-xs dashboard-muted">Wind</div>
                      <div className="text-sm font-medium dashboard-text">
                        {game.weather?.wind}mph
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div>
                      <div className="text-xs dashboard-muted">Humidity</div>
                      <div className="text-sm font-medium dashboard-text">
                        {game.weather?.humidity}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expected Value and Confidence */}
                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="text-xs dashboard-muted mb-1">Expected Value</div>
                    <div className={`text-lg font-bold px-2 py-1 rounded inline-block ${getEVColor(game.ev)}`}>
                      {(game.ev * 100).toFixed(1)}%
                    </div>
                  </div>
                  
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="text-xs dashboard-muted mb-1">Model Confidence</div>
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
              </CardContent>
            </Card>

            {/* Spread Analysis */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <BarChart3 className="w-5 h-5" />
                  Spread Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div>
                      <div className="text-sm dashboard-muted">Market Spread</div>
                      <div className="font-semibold dashboard-text">
                        {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getSpreadMovementIcon(game.spreadMovement)}
                      <span className="text-sm dashboard-muted">
                        {game.spreadMovement > 0 ? '+' : ''}{game.spreadMovement}
                      </span>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="text-sm dashboard-muted">Model Spread</div>
                    <div className="font-semibold dashboard-text">
                      {game.homeTeam} {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
                    </div>
                  </div>
                  
                  <div className="p-3 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded">
                    <div className="text-sm dashboard-muted">Value Opportunity</div>
                    <div className="font-semibold dashboard-text">
                      {Math.abs(game.spread - game.modelSpread).toFixed(1)} points difference
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Win Probability */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <Target className="w-5 h-5" />
                  Win Probability
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbr={game.awayTeam} size="small" className="w-8 h-8" />
                      <span className="dashboard-text">{game.awayTeam}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold dashboard-text">
                        {(game.awayWinProb * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-800 rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full"
                      style={{ width: `${game.awayWinProb * 100}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between">
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbr={game.homeTeam} size="small" className="w-8 h-8" />
                      <span className="dashboard-text">{game.homeTeam}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold dashboard-text">
                        {(game.homeWinProb * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Team Stats and Matchup Analysis */}
          <div className="space-y-6">
            {/* Team Stats Comparison */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <BarChart3 className="w-5 h-5" />
                  Team Stats Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-2 dashboard-text">Stat</th>
                        <th className="text-center py-2 dashboard-text">{game.awayTeam}</th>
                        <th className="text-center py-2 dashboard-text">{game.homeTeam}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-gray-700">
                        <td className="py-2 text-sm dashboard-muted">Record</td>
                        <td className="text-center py-2 dashboard-text">{game.awayTeamStats.record}</td>
                        <td className="text-center py-2 dashboard-text">{game.homeTeamStats.record}</td>
                      </tr>
                      <tr className="border-b border-gray-700">
                        <td className="py-2 text-sm dashboard-muted">ELO Rating</td>
                        <td className="text-center py-2 dashboard-text">{game.awayTeamStats.elo}</td>
                        <td className="text-center py-2 dashboard-text">{game.homeTeamStats.elo}</td>
                      </tr>
                      <tr className="border-b border-gray-700">
                        <td className="py-2 text-sm dashboard-muted">Offensive EPA</td>
                        <td className={`text-center py-2 font-semibold ${getEPAColor(game.awayTeamStats.offensiveEPA)}`}>
                          +{game.awayTeamStats.offensiveEPA.toFixed(2)}
                        </td>
                        <td className={`text-center py-2 font-semibold ${getEPAColor(game.homeTeamStats.offensiveEPA)}`}>
                          +{game.homeTeamStats.offensiveEPA.toFixed(2)}
                        </td>
                      </tr>
                      <tr className="border-b border-gray-700">
                        <td className="py-2 text-sm dashboard-muted">Defensive EPA</td>
                        <td className={`text-center py-2 font-semibold ${getEPAColor(-game.awayTeamStats.defensiveEPA)}`}>
                          {game.awayTeamStats.defensiveEPA.toFixed(2)}
                        </td>
                        <td className={`text-center py-2 font-semibold ${getEPAColor(-game.homeTeamStats.defensiveEPA)}`}>
                          {game.homeTeamStats.defensiveEPA.toFixed(2)}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-sm dashboard-muted">Strength of Schedule</td>
                        <td className="text-center py-2 dashboard-text">
                          {(game.awayTeamStats.sos * 100).toFixed(0)}%
                        </td>
                        <td className="text-center py-2 dashboard-text">
                          {(game.homeTeamStats.sos * 100).toFixed(0)}%
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* QB Matchup */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <Users className="w-5 h-5" />
                  Quarterback Matchup
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="flex items-center gap-2 mb-2">
                      <TeamLogo teamAbbr={game.awayTeam} size="small" className="w-6 h-6" />
                      <span className="font-semibold dashboard-text">{game.qbMatchup.away.name}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="dashboard-muted">Rating</span>
                        <span className="dashboard-text">{game.qbMatchup.away.rating}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="dashboard-muted">EPA</span>
                        <span className={`font-semibold ${getEPAColor(game.qbMatchup.away.epa)}`}>
                          +{game.qbMatchup.away.epa.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                    <div className="flex items-center gap-2 mb-2">
                      <TeamLogo teamAbbr={game.homeTeam} size="small" className="w-6 h-6" />
                      <span className="font-semibold dashboard-text">{game.qbMatchup.home.name}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="dashboard-muted">Rating</span>
                        <span className="dashboard-text">{game.qbMatchup.home.rating}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="dashboard-muted">EPA</span>
                        <span className={`font-semibold ${getEPAColor(game.qbMatchup.home.epa)}`}>
                          +{game.qbMatchup.home.epa.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Market Factors */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <TrendingUp className="w-5 h-5" />
                  Market Factors
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {game.marketFactors.map((factor, index) => (
                    <div key={index} className="flex items-start gap-2 p-2 bg-[hsl(var(--dashboard-surface))] rounded">
                      <div className="w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                      <span className="text-sm dashboard-text">{factor}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Betting Recommendation */}
            <Card className="dashboard-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 dashboard-text">
                  <Target className="w-5 h-5" />
                  Betting Recommendation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-4 bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold dashboard-text">Recommended Play</span>
                    <Badge variant="outline" className={`text-xs ${getEVColor(game.ev)}`}>
                      EV: {(game.ev * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <p className="text-sm dashboard-muted mb-3">
                    Based on our model analysis, this game presents a positive expected value opportunity.
                  </p>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-xs dashboard-muted">Expected Units</div>
                      <div className="text-lg font-bold text-green-400">
                        +${(game.ev * 100).toFixed(2)}
                      </div>
                    </div>
                    <Button className="dashboard-button-primary">
                      View Detailed Analysis
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameDetailPage;