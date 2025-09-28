import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target, 
  Users, 
  Calendar,
  Cloud,
  Wind
} from 'lucide-react';
import TeamLogo from '@/components/TeamLogo';

const EVGameCard = ({ game }) => {
  const getEVColor = (ev) => {
    if (ev > 0.1) return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
    if (ev > 0.05) return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
    return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
  };

  const getConfidenceLevel = (confidence) => {
    if (confidence > 0.8) return 'High';
    if (confidence > 0.6) return 'Medium';
    if (confidence > 0.4) return 'Low';
    return 'Very Low';
  };

  const getBettingRecommendation = (ev, confidence) => {
    if (ev > 0.1 && confidence > 0.7) return 'Strong Buy';
    if (ev > 0.05 && confidence > 0.6) return 'Buy';
    if (ev > 0) return 'Consider';
    return 'Avoid';
  };

  const getBettingRecommendationColor = (ev, confidence) => {
    if (ev > 0.1 && confidence > 0.7) return 'bg-green-500 text-white';
    if (ev > 0.05 && confidence > 0.6) return 'bg-blue-500 text-white';
    if (ev > 0) return 'bg-yellow-500 text-white';
    return 'bg-gray-500 text-white';
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-all"
    >
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <span>{game.awayTeam} @ {game.homeTeam}</span>
            <Badge className="text-xs" variant="outline">
              {formatTime(game.startTime)}
            </Badge>
          </CardTitle>
          <Badge className={getEVColor(game.ev)}>
            <DollarSign className="w-3 h-3 mr-1" />
            EV: {(game.ev * 100).toFixed(1)}%
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Teams and Spread */}
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <div className="flex items-center gap-3">
            <TeamLogo teamAbbr={game.awayTeam} size="small" className="w-10 h-10" />
            <div>
              <div className="font-semibold">{game.awayTeam}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {game.awayRecord || '0-0'}
              </div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-sm text-gray-500 dark:text-gray-400">Spread</div>
            <div className="text-lg font-bold">
              {game.homeTeam} {game.spread > 0 ? '+' : ''}{game.spread}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Model: {game.modelSpread > 0 ? '+' : ''}{game.modelSpread}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="font-semibold">{game.homeTeam}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {game.homeRecord || '0-0'}
              </div>
            </div>
            <TeamLogo teamAbbr={game.homeTeam} size="small" className="w-10 h-10" />
          </div>
        </div>

        {/* Betting Recommendation */}
        <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h4 className="font-semibold">Betting Recommendation</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Based on EV and confidence analysis
              </p>
            </div>
            <Badge className={getBettingRecommendationColor(game.ev, game.confidence)}>
              {getBettingRecommendation(game.ev, game.confidence)}
            </Badge>
          </div>
          
          <div className="mt-3 grid grid-cols-2 gap-3">
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-900 rounded">
              <div className="text-xs text-gray-500 dark:text-gray-400">Confidence</div>
              <div className="font-semibold">{getConfidenceLevel(game.confidence)}</div>
              <div className="text-xs">{(game.confidence * 100).toFixed(0)}%</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-900 rounded">
              <div className="text-xs text-gray-500 dark:text-gray-400">Cover Probability</div>
              <div className="font-semibold">
                {game.spread > 0 ? 
                  (game.awayWinProb * 100).toFixed(0) : 
                  (game.homeWinProb * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>

        {/* Game Context */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded">
            <Calendar className="w-4 h-4 text-gray-500" />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Date</div>
              <div className="text-sm font-medium">{formatDate(game.startTime)}</div>
            </div>
          </div>
          
          <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded">
            <Cloud className="w-4 h-4 text-gray-500" />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Weather</div>
              <div className="text-sm font-medium">{game.weather?.temp}°F</div>
            </div>
          </div>
          
          <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded">
            <Wind className="w-4 h-4 text-gray-500" />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Wind</div>
              <div className="text-sm font-medium">{game.weather?.wind}mph</div>
            </div>
          </div>
        </div>

        {/* Expected Units */}
        <div className="p-3 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold flex items-center gap-2">
                <Target className="w-4 h-4" />
                Expected Units
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Per $100 bet
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                +${(game.ev * 100).toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                per $100 wagered
              </div>
            </div>
          </div>
        </div>

        <Button className="w-full">
          View Detailed Analysis
        </Button>
      </CardContent>
    </motion.div>
  );
};

const EVBettingCard = ({ games, loading, error }) => {
  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(2)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg" />
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
          Failed to load high EV games
        </div>
      </Card>
    );
  }

  if (!games || games.length === 0) {
    return (
      <Card className="p-8 text-center">
        <div className="text-gray-600 dark:text-gray-400">
          No high expected value plays available for this week
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Check back later as more data becomes available
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          High Expected Value Plays
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Games with positive expected value based on our model analysis
        </p>
      </div>
      
      <div className="space-y-6">
        {games.map((game) => (
          <EVGameCard key={game.id} game={game} />
        ))}
      </div>
    </div>
  );
};

export default EVBettingCard;