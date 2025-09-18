import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertTriangle, Cloud, TrendingUp, Zap,
  ThermometerSun, DollarSign, Brain, Trophy
} from 'lucide-react';
import TeamLogo from './TeamLogo';

const SmartInsights = ({ games }) => {
  // Mock smart insights based on games data
  const generateInsights = () => {
    const insights = [];

    // Find potential upsets
    const upsets = games.filter(g =>
      g.status === 'scheduled' &&
      g.awayWinProb && g.awayWinProb > 30 && g.awayWinProb < 45
    ).slice(0, 1);

    if (upsets.length > 0) {
      const game = upsets[0];
      insights.push({
        type: 'upset',
        icon: AlertTriangle,
        gradient: 'from-red-500/10 to-orange-500/10',
        iconColor: 'text-orange-500',
        title: 'Upset Alert',
        main: `${game.awayTeam} @ ${game.homeTeam}`,
        detail: `${game.awayTeam} ${game.awayWinProb}% win prob but momentum shifting`,
        subDetail: 'Line moved 2.5 points toward underdog',
        teams: [game.awayTeam, game.homeTeam]
      });
    }

    // Weather impact games (mock)
    const weatherGames = games.filter(g => g.status === 'scheduled').slice(0, 1);
    if (weatherGames.length > 0) {
      const game = weatherGames[0];
      insights.push({
        type: 'weather',
        icon: Cloud,
        gradient: 'from-blue-500/10 to-cyan-500/10',
        iconColor: 'text-blue-500',
        title: 'Weather Factor',
        main: `${game.awayTeam} @ ${game.homeTeam}`,
        detail: '25mph winds expected',
        subDetail: 'Under has hit 73% in similar conditions',
        teams: [game.awayTeam, game.homeTeam]
      });
    }

    // High confidence picks
    const highConf = games.filter(g =>
      g.status === 'scheduled' &&
      (g.homeWinProb > 70 || g.awayWinProb > 70)
    ).slice(0, 1);

    if (highConf.length > 0) {
      const game = highConf[0];
      const favorite = game.homeWinProb > game.awayWinProb ? game.homeTeam : game.awayTeam;
      const prob = Math.max(game.homeWinProb, game.awayWinProb);
      insights.push({
        type: 'bestbet',
        icon: TrendingUp,
        gradient: 'from-green-500/10 to-emerald-500/10',
        iconColor: 'text-green-500',
        title: 'Best Bet',
        main: `${favorite} -3.5`,
        detail: `${prob}% confidence`,
        subDetail: '4-0 ATS in last 4 home games',
        teams: [favorite]
      });
    }

    // Prime time special
    insights.push({
      type: 'primetime',
      icon: Zap,
      gradient: 'from-purple-500/10 to-pink-500/10',
      iconColor: 'text-purple-500',
      title: 'Prime Time',
      main: 'KC vs BUF',
      detail: 'Sunday Night Special - total trending over',
      subDetail: 'Public: 78% on over 48.5',
      teams: ['KC', 'BUF']
    });

    return insights.slice(0, 4);
  };

  const insights = generateInsights();

  return (
    <div className="mb-4 sm:mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0 mb-3 sm:mb-4">
        <h2 className="responsive-text-xl font-bold flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Smart Insights
        </h2>
        <Badge variant="outline" className="animate-pulse self-start sm:self-auto">
          Live Analysis
        </Badge>
      </div>

      <div className="mobile-grid">
        {insights.map((insight, index) => (
          <motion.div
            key={insight.type}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className={`card-mobile bg-gradient-to-br ${insight.gradient} hover:shadow-lg transition-all duration-300 cursor-pointer hover:scale-105 touch-friendly`}>
              <CardHeader className="pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <insight.icon className={`w-4 h-4 sm:w-5 sm:h-5 ${insight.iconColor} flex-shrink-0`} />
                    <h3 className="font-semibold responsive-text-sm truncate">{insight.title}</h3>
                  </div>
                  {insight.type === 'upset' && (
                    <Badge className="bg-red-600 text-white responsive-text-xs animate-pulse flex-shrink-0">HOT</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
                <div className="mb-1">
                  {insight.teams && insight.teams.length > 0 ? (
                    <div className="font-medium responsive-text-sm flex items-center gap-1">
                      {(() => {
                        // Handle team display with proper logo placement
                        const parts = insight.main.split(/\s+(vs|@|v\.)\s+/gi);
                        if (parts.length >= 3 && insight.teams.length >= 2) {
                          // Format: TEAM1 vs/@ TEAM2
                          return (
                            <>
                              <span className="inline-flex items-center gap-1">
                                <TeamLogo
                                  teamAbbr={insight.teams[0]}
                                  size="small"
                                  showGlow={false}
                                  className="w-5 h-5 sm:w-6 sm:h-6"
                                />
                                <span>{parts[0]}</span>
                              </span>
                              <span>{parts[1]}</span>
                              <span className="inline-flex items-center gap-1">
                                <span>{parts[2]}</span>
                                <TeamLogo
                                  teamAbbr={insight.teams[1]}
                                  size="small"
                                  showGlow={false}
                                  className="w-5 h-5 sm:w-6 sm:h-6"
                                />
                              </span>
                            </>
                          );
                        } else if (insight.teams.length === 1) {
                          // Single team
                          return (
                            <span className="inline-flex items-center gap-1">
                              <TeamLogo
                                teamAbbr={insight.teams[0]}
                                size="small"
                                showGlow={false}
                                className="w-5 h-5 sm:w-6 sm:h-6"
                              />
                              <span>{insight.main}</span>
                            </span>
                          );
                        }
                        return insight.main;
                      })()}
                    </div>
                  ) : (
                    <p className="font-medium responsive-text-sm">{insight.main}</p>
                  )}
                </div>
                <p className="responsive-text-xs text-muted-foreground">{insight.detail}</p>
                <p className="responsive-text-xs text-muted-foreground mt-1 font-medium">
                  {insight.subDetail}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Quick Stats Bar - Mobile Responsive */}
      <div className="mt-3 sm:mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 responsive-text-sm">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-yellow-500 flex-shrink-0" />
          <span className="text-muted-foreground">Model Accuracy:</span>
          <span className="font-bold">73.2%</span>
          <span className="responsive-text-xs text-green-500">+2.1%</span>
        </div>
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-green-500 flex-shrink-0" />
          <span className="text-muted-foreground">ROI This Week:</span>
          <span className="font-bold">+12.4%</span>
        </div>
        <div className="flex items-center gap-2">
          <ThermometerSun className="w-4 h-4 text-orange-500 flex-shrink-0" />
          <span className="text-muted-foreground">Hot Streak:</span>
          <span className="font-bold">8-2 Last 10</span>
        </div>
      </div>
    </div>
  );
};

export default SmartInsights;