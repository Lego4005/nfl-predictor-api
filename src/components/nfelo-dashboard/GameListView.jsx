import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Calendar, Cloud, Wind } from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';

const GameRow = ({ game }) => {
  const getTeamColor = (teamAbbr) => {
    // In a real implementation, this would fetch team colors from a data source
    const colors = {
      'KC': { primary: '#E31837', secondary: '#FFB81C' },
      'BUF': { primary: '#00338D', secondary: '#C60C30' },
      'GB': { primary: '#203731', secondary: '#FFB612' },
      'CHI': { primary: '#0B162A', secondary: '#C83803' },
      'SF': { primary: '#AA0000', secondary: '#B3995D' },
      'PIT': { primary: '#FFB81C', secondary: '#000000' }
    };
    return colors[teamAbbr] || { primary: '#666666', secondary: '#CCCCCC' };
  };

  const getEVColor = (ev) => {
    if (ev > 0.1) return 'text-green-600 dark:text-green-400';
    if (ev > 0.05) return 'text-blue-600 dark:text-blue-400';
    if (ev > 0) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return 'bg-green-500';
    if (confidence > 0.6) return 'bg-blue-500';
    if (confidence > 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
    >
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          {/* Game Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {formatDate(game.startTime)}
                </span>
              </div>
              <Badge variant="outline" className="text-xs">
                {formatTime(game.startTime)}
              </Badge>
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
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {game.awayTeam}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {game.awayRecord || '0-0'}
                  </div>
                </div>
              </div>

              <div className="text-center">
                <div className="text-xs text-gray-500 dark:text-gray-400">@</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{game.venue}</div>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {game.homeTeam}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
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
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center gap-1">
                <Cloud className="w-4 h-4" />
                <span>{game.weather?.temp}°F</span>
              </div>
              <div className="flex items-center gap-1">
                <Wind className="w-4 h-4" />
                <span>{game.weather?.wind}mph</span>
              </div>
            </div>
          </div>

          {/* Spread Data */}
          <div className="md:border-l md:border-gray-200 dark:md:border-gray-700 md:pl-4 min-w-[200px]">
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Market Spread</div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">
                    {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
                  </span>
                  {getSpreadMovementIcon(game.spreadMovement)}
                </div>
              </div>
              
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Model Spread</div>
                <div className="font-semibold">
                  {game.homeTeam} {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
                </div>
              </div>
            </div>
          </div>

          {/* Expected Value */}
          <div className="md:border-l md:border-gray-200 dark:md:border-gray-700 md:pl-4 min-w-[150px]">
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Expected Value</div>
                <div className={`text-lg font-bold ${getEVColor(game.ev)}`}>
                  {(game.ev * 100).toFixed(1)}%
                </div>
              </div>
              
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Confidence</div>
                <div className="flex items-center gap-2">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getConfidenceColor(game.confidence)}`}
                      style={{ width: `${game.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">
                    {(game.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Win Probability */}
          <div className="md:border-l md:border-gray-200 dark:md:border-gray-700 md:pl-4 min-w-[120px]">
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Win Probability</div>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{game.awayTeam}</span>
                    <span className="font-semibold">{(game.awayWinProb * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>{game.homeTeam}</span>
                    <span className="font-semibold">{(game.homeWinProb * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </motion.div>
  );
};

const GameListView = ({ games, loading, error }) => {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-8 text-center">
        <div className="text-red-500 font-medium">Error: {error}</div>
        <div className="text-gray-600 dark:text-gray-400 mt-2">
          Failed to load games data
        </div>
      </Card>
    );
  }

  if (!games || games.length === 0) {
    return (
      <Card className="p-8 text-center">
        <div className="text-gray-600 dark:text-gray-400">
          No games available for this week
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {games.map((game) => (
        <GameRow key={game.id} game={game} />
      ))}
    </div>
  );
};

export default GameListView;