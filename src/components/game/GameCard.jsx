import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getTeam } from '../../data/nflTeams';
import { Cloud, Wind, Droplets, Trophy, TrendingUp, Users, Volume2, Brain, Target } from 'lucide-react';
import TeamLogo from '../TeamLogo';

// Game Card with all the visual improvements - updated import paths
const GameCard = ({ game }) => {
  const homeTeam = getTeam(game.homeTeam);
  const awayTeam = getTeam(game.awayTeam);


  const isLive = game.status === 'live';
  const momentum = game.homeScore > game.awayScore ? 65 : 35; // Mock momentum

  // AI Prediction helpers
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return 'bg-green-500 text-white';
    if (confidence >= 0.5) return 'bg-yellow-500 text-white';
    return 'bg-red-500 text-white';
  };

  const getConfidenceText = (confidence) => {
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  const getPredictedWinner = () => {
    if (!game.hasAIPrediction) return null;
    return game.homeWinProb > game.awayWinProb ? homeTeam : awayTeam;
  };

  const getPredictedWinnerText = () => {
    if (!game.hasAIPrediction) return null;
    const winner = getPredictedWinner();
    const winProb = game.homeWinProb > game.awayWinProb ? game.homeWinProb : game.awayWinProb;
    return `${winner?.name || (game.homeWinProb > game.awayWinProb ? game.homeTeam : game.awayTeam)} (${winProb.toFixed(0)}%)`;
  };

  // Mock trends for live games (in real app, compare to previous values)
  const homeTrend = isLive ? (momentum > 50 ? 'up' : 'down') : null;
  const awayTrend = isLive ? (momentum <= 50 ? 'up' : 'down') : null;

  // Determine winners for final games
  const homeWon = game.status === 'final' && game.homeScore > game.awayScore;
  const awayWon = game.status === 'final' && game.awayScore > game.homeScore;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.03, y: -5 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.3 }}
      className="relative"
    >
      {/* Responsive Glassmorphism Card */}
      <Card className="card-mobile backdrop-blur-md bg-white/90 dark:bg-gray-900/90 border border-white/20 dark:border-gray-700/50 hover:shadow-2xl transition-all duration-300 min-h-[320px] sm:min-h-[400px] flex flex-col touch-friendly overflow-hidden">
        {/* TEAM COLOR GRADIENT BAR - Using team's predefined gradients */}
        <div className="h-3 w-full flex">
          <div
            className="flex-1"
            style={{
              background: awayTeam?.gradient || `linear-gradient(135deg, ${awayTeam?.primaryColor || '#3b82f6'} 0%, ${awayTeam?.secondaryColor || '#1d4ed8'} 100%)`
            }}
          />
          <div
            className="flex-1"
            style={{
              background: homeTeam?.gradient || `linear-gradient(135deg, ${homeTeam?.primaryColor || '#ef4444'} 0%, ${homeTeam?.secondaryColor || '#dc2626'} 100%)`
            }}
          />
        </div>

        {/* Live Badge */}
        <div className="relative">
          {isLive && (
            <div className="absolute left-1/2 transform -translate-x-1/2 -top-1">
              <div className="bg-red-600 text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1 shadow-md">
                <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                LIVE
              </div>
            </div>
          )}
        </div>

        <CardHeader className="pb-2 sm:pb-3 px-3 sm:px-6 pt-3 sm:pt-6">
          {/* Teams Section - Responsive Layout */}
          <div className="flex items-center justify-between gap-2">
            {/* Away Team - Mobile Optimized */}
            <motion.div
              className="flex items-center gap-2 sm:gap-3 flex-shrink-0"
              whileHover={{ x: -2 }}
            >
              <TeamLogo
                teamAbbr={game.awayTeam}
                size="medium"
                showGlow={true}
                className="w-8 h-8 sm:w-12 sm:h-12"
                style={{
                  '--team-primary': awayTeam?.primaryColor,
                  '--team-secondary': awayTeam?.secondaryColor
                }}
              />
              <div className="hidden sm:block">
                <div className="font-bold responsive-text-sm">{game.awayTeam}</div>
                <div className="responsive-text-xs text-muted-foreground">{awayTeam?.city}</div>
              </div>
              <div className="responsive-text-xl sm:text-2xl font-black">{game.awayScore || 0}</div>
            </motion.div>

            {/* VS & Mobile Team Names */}
            <div className="flex flex-col items-center gap-1 flex-1">
              <div className="responsive-text-xs text-muted-foreground font-medium">@</div>
              <div className="sm:hidden text-center">
                <div className="responsive-text-xs font-semibold">{game.awayTeam} @ {game.homeTeam}</div>
              </div>
            </div>

            {/* Home Team - Mobile Optimized */}
            <motion.div
              className="flex items-center gap-2 sm:gap-3 flex-shrink-0"
              whileHover={{ x: 2 }}
            >
              <div className="responsive-text-xl sm:text-2xl font-black">{game.homeScore || 0}</div>
              <div className="hidden sm:block text-right">
                <div className="font-bold responsive-text-sm">{game.homeTeam}</div>
                <div className="responsive-text-xs text-muted-foreground">{homeTeam?.city}</div>
              </div>
              <TeamLogo
                teamAbbr={game.homeTeam}
                size="medium"
                showGlow={true}
                className="w-8 h-8 sm:w-12 sm:h-12"
                style={{
                  '--team-primary': homeTeam?.primaryColor,
                  '--team-secondary': homeTeam?.secondaryColor
                }}
              />
            </motion.div>
          </div>

          {/* AI Prediction Banner - Mobile Optimized */}
          {game.hasAIPrediction && (
            <div className="mt-2 sm:mt-3 p-2 sm:p-3 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-200 dark:border-purple-700">
              {/* Confidence Bar Visual */}
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full transition-all duration-500 ${
                    game.prediction.confidence >= 0.7 ? 'bg-green-500' :
                    game.prediction.confidence >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${(game.prediction.confidence || 0.5) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-purple-600" />
                  <span className="responsive-text-xs font-medium text-purple-600 dark:text-purple-400">AI Pick</span>
                </div>
                <Badge className={`responsive-text-xs ${getConfidenceColor(game.prediction.confidence)}`}>
                  {getConfidenceText(game.prediction.confidence)} ({(game.prediction.confidence * 100).toFixed(0)}%)
                </Badge>
              </div>
              <div className="mt-1 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2">
                <div className="responsive-text-sm font-semibold">
                  {getPredictedWinnerText()}
                </div>
                {game.prediction.line !== 0 && (
                  <div className="flex items-center gap-1 responsive-text-xs text-muted-foreground">
                    <Target className="w-3 h-3" />
                    <span>Spread: {game.prediction.line > 0 ? '+' : ''}{game.prediction.line.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Game Status - Mobile Responsive */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0 mt-2 sm:mt-3 responsive-text-xs">
            {isLive ? (
              <>
                <div className="flex items-center gap-2">
                  <Badge variant="destructive" className="animate-pulse">
                    Q{game.quarter || 1} • {game.time || '15:00'}
                  </Badge>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Volume2 className="w-3 h-3" />
                    {[...Array(3)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="w-0.5 bg-green-500"
                        animate={{ height: [2, 8, 2] }}
                        transition={{ duration: 0.5, delay: i * 0.1, repeat: Infinity }}
                      />
                    ))}
                  </div>
                </div>
              </>
            ) : game.status === 'scheduled' ? (
              <div className="text-muted-foreground">
                Kickoff: {new Date(game.startTime).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
              </div>
            ) : (
              <Badge variant="secondary">FINAL</Badge>
            )}

            {/* Weather Widget - Mobile Optimized */}
            <div className="flex items-center gap-1 sm:gap-2 px-2 py-1 bg-blue-500/10 rounded-full self-start sm:self-auto">
              <Cloud className="w-3 h-3 text-blue-500" />
              <span className="responsive-text-xs">72°F</span>
              <Wind className="w-3 h-3 text-gray-500" />
              <span className="responsive-text-xs">8mph</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0 px-3 sm:px-6 pb-3 sm:pb-6 flex-1 flex flex-col">
          {/* Momentum/Winner Bar */}
          <div className="mb-3">
            {/* Always show bar - determine type based on game data */}
            {(game.homeScore && game.awayScore && game.homeScore !== game.awayScore) ? (
              <>
                {/* Winner Bar for games with final scores */}
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Winner</span>
                  <span className="font-medium flex items-center gap-1">
                    <Trophy className="w-3 h-3 text-yellow-500" />
                    {game.homeScore > game.awayScore ? homeTeam?.name : awayTeam?.name}
                  </span>
                </div>
                <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      background: game.homeScore > game.awayScore ? homeTeam?.gradient : awayTeam?.gradient,
                      width: '100%'
                    }}
                  />
                </div>
              </>
            ) : isLive ? (
              <>
                {/* Momentum Bar for live games */}
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Momentum</span>
                  <span className="font-medium">{momentum > 50 ? homeTeam?.name : awayTeam?.name}</span>
                </div>
                <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  {/* Away team gradient on left side */}
                  <div
                    className="absolute h-full left-0 rounded-full"
                    style={{
                      background: awayTeam?.gradient || `linear-gradient(135deg, ${awayTeam?.primaryColor || '#3b82f6'} 0%, ${awayTeam?.secondaryColor || '#1d4ed8'} 100%)`,
                      width: `${100 - momentum}%`
                    }}
                  />
                  {/* Home team gradient on right side */}
                  <div
                    className="absolute h-full right-0 rounded-full"
                    style={{
                      background: homeTeam?.gradient || `linear-gradient(135deg, ${homeTeam?.primaryColor || '#ef4444'} 0%, ${homeTeam?.secondaryColor || '#dc2626'} 100%)`,
                      width: `${momentum}%`
                    }}
                  />
                </div>
              </>
            ) : (
              <>
                {/* Default Bar for upcoming games - show 50/50 */}
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Matchup</span>
                  <span className="font-medium">Even</span>
                </div>
                <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  {/* Split 50/50 for upcoming games */}
                  <div
                    className="absolute h-full left-0 rounded-full"
                    style={{
                      background: awayTeam?.gradient || `linear-gradient(135deg, ${awayTeam?.primaryColor || '#3b82f6'} 0%, ${awayTeam?.secondaryColor || '#1d4ed8'} 100%)`,
                      width: '50%'
                    }}
                  />
                  <div
                    className="absolute h-full right-0 rounded-full"
                    style={{
                      background: homeTeam?.gradient || `linear-gradient(135deg, ${homeTeam?.primaryColor || '#ef4444'} 0%, ${homeTeam?.secondaryColor || '#dc2626'} 100%)`,
                      width: '50%'
                    }}
                  />
                </div>
              </>
            )}
          </div>

          {/* Win Probability - Mobile Optimized */}
          <div className="grid grid-cols-2 gap-2 sm:gap-3 mb-2 sm:mb-3">
            <div className={`text-center p-2 rounded-lg ${
              awayWon ? 'bg-green-100 dark:bg-green-900/30' :
              game.status === 'final' ? 'bg-red-100 dark:bg-red-900/30' :
              'bg-gray-100 dark:bg-gray-800'
            }`}>
              <div className="responsive-text-xs text-gray-600 dark:text-gray-300 mb-1 flex items-center justify-center gap-1">
                Win %
                {awayTrend === 'up' && <TrendingUp className="w-3 h-3 text-green-500" />}
                {awayTrend === 'down' && <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />}
                {awayWon && <Trophy className="w-3 h-3 text-yellow-500" />}
              </div>
              <div className={`responsive-text-lg font-bold ${
                awayWon ? 'text-green-600 dark:text-green-400' :
                game.status === 'final' ? 'text-red-600 dark:text-red-400' :
                awayTrend === 'up' ? 'text-green-600 dark:text-green-400' :
                awayTrend === 'down' ? 'text-red-600 dark:text-red-400' :
                'text-blue-600 dark:text-blue-400'
              }`}>
                {game.awayWinProb || 45}%
              </div>
            </div>
            <div className={`text-center p-2 rounded-lg ${
              homeWon ? 'bg-green-100 dark:bg-green-900/30' :
              game.status === 'final' ? 'bg-red-100 dark:bg-red-900/30' :
              'bg-gray-100 dark:bg-gray-800'
            }`}>
              <div className="responsive-text-xs text-gray-600 dark:text-gray-300 mb-1 flex items-center justify-center gap-1">
                Win %
                {homeTrend === 'up' && <TrendingUp className="w-3 h-3 text-green-500" />}
                {homeTrend === 'down' && <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />}
                {homeWon && <Trophy className="w-3 h-3 text-yellow-500" />}
              </div>
              <div className={`responsive-text-lg font-bold ${
                homeWon ? 'text-green-600 dark:text-green-400' :
                game.status === 'final' ? 'text-red-600 dark:text-red-400' :
                homeTrend === 'up' ? 'text-green-600 dark:text-green-400' :
                homeTrend === 'down' ? 'text-red-600 dark:text-red-400' :
                'text-blue-600 dark:text-blue-400'
              }`}>
                {game.homeWinProb || 55}%
              </div>
            </div>
          </div>

          {/* Betting Line - Mobile Stack Layout */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3 p-2 bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-lg">
            <div className="responsive-text-xs text-center sm:text-left">
              <span className="text-muted-foreground">Spread: </span>
              <span className="font-bold">
                {game.hasAIPrediction && game.prediction.line !== 0
                  ? `${game.homeTeam} ${game.prediction.line > 0 ? '+' : ''}${game.prediction.line.toFixed(1)}`
                  : `${homeTeam?.abbreviation} -3.5`
                }
              </span>
            </div>
            <div className="responsive-text-xs text-center">
              <span className="text-muted-foreground">O/U: </span>
              <span className="font-bold">
                {game.hasAIPrediction && game.prediction.predictedTotal
                  ? game.prediction.predictedTotal.toFixed(1)
                  : '48.5'
                }
              </span>
            </div>
            <div className="responsive-text-xs text-center sm:text-right">
              <span className="text-muted-foreground">ML: </span>
              <span className="font-bold">-150/+130</span>
            </div>
          </div>

          {/* Key Stats - Mobile Optimized */}
          <div className="mt-auto">
            {(isLive || game.status === 'final') ? (
              <div className="grid grid-cols-3 gap-1 sm:gap-2 text-center">
                <div className="p-1">
                  <div className="responsive-text-xs text-muted-foreground">Yards</div>
                  <div className="responsive-text-sm font-bold">245/312</div>
                </div>
                <div className="p-1">
                  <div className="responsive-text-xs text-muted-foreground">TOP</div>
                  <div className="responsive-text-sm font-bold">14:23/15:37</div>
                </div>
                <div className="p-1">
                  <div className="responsive-text-xs text-muted-foreground">Turnovers</div>
                  <div className="responsive-text-sm font-bold">1/0</div>
                </div>
              </div>
            ) : (
              <div className="h-[40px] sm:h-[52px]"></div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default GameCard;