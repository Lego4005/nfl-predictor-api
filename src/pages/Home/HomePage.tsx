import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crown,
  TrendingUp,
  Calendar,
  Target,
  BarChart3,
  Users,
  Zap,
  Trophy,
  ChevronRight,
  Star,
  Activity,
  Eye,
  Clock
} from 'lucide-react';

import SmoothTab from '@/components/kokonutui/smooth-tab';
import GradientButton from '@/components/kokonutui/gradient-button';
import BentoGrid from '@/components/kokonutui/bento-grid';
import AttractButton from '@/components/kokonutui/attract-button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import { getCouncilMembers, EXPERT_PERSONALITIES } from '@/data/expertPersonalities';
import { PREDICTION_GROUPS, getCategoryStats } from '@/data/predictionCategories';
import ExpertShowcaseDashboard from '@/components/dashboard/ExpertShowcaseDashboard';
import ExpertAvatar from '@/components/ui/ExpertAvatar';
import TeamLogo, { TeamLogoMatchup } from '@/components/ui/TeamLogo';

interface HomePageProps {
  onNavigate?: (pageId: string) => void
}

interface FeatureCard {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: string;
  stats?: {
    label: string;
    value: string | number;
    trend?: 'up' | 'down' | 'stable';
  }[];
  featured?: boolean;
  comingSoon?: boolean;
}

const getCurrentWeek = (): number => {
  // Mock current week - in real app, this would be calculated from current date
  return 3;
};

const getUpcomingGames = () => {
  // Mock upcoming games - in real app, this would come from API
  return [
    { id: '1', homeTeam: 'KC', awayTeam: 'BUF', time: 'Sunday 1:00 PM', network: 'CBS', featured: true },
    { id: '2', homeTeam: 'SF', awayTeam: 'DAL', time: 'Sunday 4:25 PM', network: 'FOX', featured: true },
    { id: '3', homeTeam: 'PHI', awayTeam: 'NYG', time: 'Monday 8:15 PM', network: 'ESPN', featured: false }
  ];
};

function HomePage({ onNavigate }: HomePageProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [councilMembers, setCouncilMembers] = useState(getCouncilMembers());
  const [categoryStats] = useState(getCategoryStats());
  const [currentWeek] = useState(getCurrentWeek());
  const [upcomingGames] = useState(getUpcomingGames());
  const [showExpertDashboard, setShowExpertDashboard] = useState(false);

  const featureCards: FeatureCard[] = [
    {
      id: 'expert-competition',
      title: 'AI Expert Competition',
      description: '15 AI experts competing for the top 5 council positions with real-time rankings',
      icon: <Crown className="w-8 h-8 text-gold-500" />,
      action: 'experts',
      stats: [
        { label: 'Active Experts', value: EXPERT_PERSONALITIES.length, trend: 'stable' },
        { label: 'Council Members', value: 5, trend: 'stable' },
        { label: 'Avg Accuracy', value: '68.2%', trend: 'up' }
      ],
      featured: true
    },
    {
      id: 'weekly-predictions',
      title: `Week ${currentWeek} Predictions`,
      description: `AI Council consensus predictions for all Week ${currentWeek} games`,
      icon: <Target className="w-8 h-8 text-blue-500" />,
      action: 'games',
      stats: [
        { label: 'Games This Week', value: upcomingGames.length, trend: 'stable' },
        { label: 'Predictions', value: categoryStats.total_categories, trend: 'up' },
        { label: 'Consensus Strength', value: '89%', trend: 'up' }
      ],
      featured: true
    },
    {
      id: 'live-tracking',
      title: 'Live Game Tracking',
      description: 'Real-time prediction updates and live game analysis',
      icon: <Zap className="w-8 h-8 text-yellow-500" />,
      action: 'live',
      stats: [
        { label: 'Live Categories', value: categoryStats.realtime_enabled, trend: 'stable' },
        { label: 'Update Frequency', value: '30s', trend: 'stable' }
      ]
    },
    {
      id: 'performance-analytics',
      title: 'Performance Analytics',
      description: 'Expert performance tracking and prediction accuracy metrics',
      icon: <BarChart3 className="w-8 h-8 text-green-500" />,
      action: 'performance',
      stats: [
        { label: 'Total Predictions', value: '2.4K', trend: 'up' },
        { label: 'Accuracy Rate', value: '67.8%', trend: 'up' }
      ]
    },
    {
      id: 'team-rankings',
      title: 'Team Power Rankings',
      description: 'AI-powered team strength analysis and ranking system',
      icon: <Trophy className="w-8 h-8 text-purple-500" />,
      action: 'rankings',
      stats: [
        { label: 'Teams Ranked', value: 32, trend: 'stable' },
        { label: 'Ranking Accuracy', value: '84%', trend: 'up' }
      ]
    },
    {
      id: 'betting-tools',
      title: 'Betting Analysis Tools',
      description: 'Advanced betting market analysis and value identification',
      icon: <Users className="w-8 h-8 text-orange-500" />,
      action: 'tools',
      stats: [
        { label: 'Value Bets', value: '12', trend: 'up' },
        { label: 'ROI This Week', value: '+8.4%', trend: 'up' }
      ]
    }
  ];

  const tabOptions = [
    { id: 'overview', label: 'Overview' },
    { id: 'this-week', label: 'This Week' },
    { id: 'expert-rankings', label: 'Expert Rankings' },
    { id: 'council-votes', label: 'Council Votes' }
  ];

  const handleFeatureClick = (action: string) => {
    if (action === 'experts') {
      setShowExpertDashboard(true);
    } else {
      onNavigate?.(action);
    }
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down': return <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />;
      default: return <Target className="w-3 h-3 text-gray-500" />;
    }
  };

  if (showExpertDashboard) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => setShowExpertDashboard(false)}
            className="mb-4"
          >
            ← Back to Home
          </Button>
        </div>
        <ExpertShowcaseDashboard
          onExpertSelect={(expertId) => {
            // Handle expert selection
            console.log('Selected expert:', expertId);
          }}
          onCouncilView={() => {
            // Handle council view
            console.log('View council');
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="text-center py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-4xl font-bold text-foreground mb-4">
            🏈 PickIQ May the Best Algorithm Win
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-6">
            15 AI experts competing for council positions • Real-time predictions • Advanced analytics
          </p>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{EXPERT_PERSONALITIES.length}</div>
              <div className="text-sm text-gray-500">AI Experts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{categoryStats.total_categories}+</div>
              <div className="text-sm text-gray-500">Predictions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">68.2%</div>
              <div className="text-sm text-gray-500">Avg Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gold-500">5</div>
              <div className="text-sm text-gray-500">Council Seats</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Top 5 Experts Section */}
      <div className="mb-6">
        <div className="text-center mb-4">
          <div className="flex items-center justify-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-foreground">🏆 Elite Expert Council</h2>
            <AttractButton
              onClick={() => handleFeatureClick('experts')}
              className="bg-gradient-to-r from-gold-500 to-amber-500 hover:from-gold-600 hover:to-amber-600 text-white border-gold-400/30 min-w-fit px-3 py-1.5"
              particleCount={8}
              attractRadius={40}
              defaultText="View Competition"
              attractingText="Entering Arena"
              showIcon={false}
            >
              <Trophy className="w-4 h-4" />
              View Competition
            </AttractButton>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Meet our top performing AI experts</p>
        </div>

        <div className="grid grid-cols-5 gap-6 max-w-4xl mx-auto">
          {EXPERT_PERSONALITIES.slice(0, 5).map((expert, index) => (
            <motion.div
              key={expert.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
              className="text-center group cursor-pointer"
              onClick={() => handleFeatureClick('experts')}
            >
              <div className="relative mb-3">
                <ExpertAvatar
                  expert={expert}
                  size="lg"
                  showCouncilBadge={index < 5}
                  className="mx-auto"
                />
                <div className="absolute -top-2 -right-2 bg-gold-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                  #{index + 1}
                </div>
              </div>

              <h3 className="font-bold text-sm text-foreground mb-1">
                {expert.name}
              </h3>

              <div className="text-lg font-bold text-green-600 mb-1">
                {(expert.accuracy_metrics.overall * 100).toFixed(1)}%
              </div>

              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-2 min-h-[3rem] flex items-center">
                <p className="text-xs text-gray-600 dark:text-gray-400 italic leading-tight">
                  "{expert.motto}"
                </p>
              </div>

              <div className="mt-2 text-xs text-gray-500">
                {expert.track_record.total_predictions} predictions
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex justify-center mb-8">
        <SmoothTab
          items={[
            {
              id: 'overview',
              title: 'Overview',
              color: 'bg-blue-500 hover:bg-blue-600',
              cardContent: (
                <div className="p-6 h-full flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2">Platform Overview</h3>
                    <p className="text-gray-300">
                      Real-time AI competition platform with {EXPERT_PERSONALITIES.length} experts competing for council positions
                    </p>
                  </div>
                  <div className="flex gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400">{EXPERT_PERSONALITIES.length}</div>
                      <div className="text-sm text-gray-400">Experts</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-400">68.2%</div>
                      <div className="text-sm text-gray-400">Accuracy</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-400">{categoryStats.total_categories}</div>
                      <div className="text-sm text-gray-400">Categories</div>
                    </div>
                  </div>
                </div>
              )
            },
            {
              id: 'this-week',
              title: 'This Week',
              color: 'bg-green-500 hover:bg-green-600',
              cardContent: (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Week {currentWeek} Highlights</h3>
                    <Badge variant="secondary" className="bg-green-500/20 text-green-400">
                      {upcomingGames.length} Games
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    {upcomingGames.slice(0, 3).map((game) => (
                      <div key={game.id} className="bg-background/50 rounded-lg p-3 flex flex-col items-center">
                        <TeamLogoMatchup
                          awayTeam={game.awayTeam}
                          homeTeam={game.homeTeam}
                          size="sm"
                          showVs={true}
                        />
                        <div className="text-xs text-gray-400 mt-2">{game.time}</div>
                        {game.featured && (
                          <Badge className="mt-1 bg-amber-500/20 text-amber-400 text-xs">Featured</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )
            },
            {
              id: 'expert-rankings',
              title: 'Expert Rankings',
              color: 'bg-purple-500 hover:bg-purple-600',
              cardContent: (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Top Performing Experts</h3>
                    <div className="flex items-center gap-2">
                      <Crown className="w-5 h-5 text-gold-500" />
                      <span className="text-sm text-gray-400">Council Leaders</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-5 gap-2">
                    {councilMembers.map((member, index) => (
                      <div key={member.id} className="text-center">
                        <ExpertAvatar
                          expert={member}
                          size="md"
                          showCouncilBadge={true}
                          className="mx-auto mb-1"
                        />
                        <div className="text-xs text-gray-300 truncate">{member.name.split(' ')[1]}</div>
                        <div className="text-xs text-green-400">{(member.accuracy_metrics.overall * 100).toFixed(0)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            },
            {
              id: 'council-votes',
              title: 'Council Votes',
              color: 'bg-amber-500 hover:bg-amber-600',
              cardContent: (
                <div className="p-6 h-full">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">Council Voting Power Distribution</h3>
                    <Badge variant="secondary" className="bg-amber-500/20 text-amber-400">
                      Live Weights
                    </Badge>
                  </div>
                  <div className="space-y-3">
                    {councilMembers.slice(0, 3).map((member) => (
                      <div key={member.id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <ExpertAvatar
                            expert={member}
                            size="sm"
                            showCouncilBadge={true}
                            showHoverEffect={false}
                          />
                          <span className="text-sm text-gray-300 font-medium">{member.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-700 rounded-full h-2">
                            <div
                              className="h-2 bg-gradient-to-r from-gold-500 to-amber-500 rounded-full"
                              style={{ width: `${member.council_weight! * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-amber-400 w-12 text-right font-bold">
                            {(member.council_weight! * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            }
          ]}
          defaultTabId={activeTab}
          onChange={setActiveTab}
          className="w-full max-w-2xl"
        />
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Bento Grid Section */}
              <div className="mb-12">
                <BentoGrid />
              </div>

              {/* Feature Cards Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {featureCards.map((card, index) => (
                  <motion.div
                    key={card.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className={cn(
                      "relative overflow-hidden",
                      card.featured && "md:col-span-2 lg:col-span-1"
                    )}
                  >
                    <Card
                      className={cn(
                        "h-full cursor-pointer transition-all duration-300 hover:shadow-lg hover:scale-[1.02]",
                        card.featured && "border-primary/50 bg-gradient-to-br from-primary/5 to-secondary/5",
                        card.comingSoon && "opacity-75"
                      )}
                      onClick={() => !card.comingSoon && handleFeatureClick(card.action)}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-3">
                            {card.icon}
                            <div>
                              <CardTitle className={cn(
                                "text-lg",
                                card.featured && "text-xl"
                              )}>
                                {card.title}
                              </CardTitle>
                              {card.featured && (
                                <Badge variant="secondary" className="mt-1">
                                  Featured
                                </Badge>
                              )}
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-gray-400" />
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-gray-600 dark:text-gray-400">
                          {card.description}
                        </p>
                        {card.stats && (
                          <div className="grid grid-cols-2 gap-3">
                            {card.stats.map((stat, idx) => (
                              <div key={idx} className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                <div className="flex items-center justify-center space-x-1">
                                  <span className="font-bold text-lg">{stat.value}</span>
                                  {getTrendIcon(stat.trend)}
                                </div>
                                <div className="text-xs text-gray-500">{stat.label}</div>
                              </div>
                            ))}
                          </div>
                        )}
                        {card.comingSoon && (
                          <Badge variant="outline" className="w-full justify-center">
                            Coming Soon
                          </Badge>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'this-week' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Calendar className="w-5 h-5" />
                    <span>Week {currentWeek} Schedule</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {upcomingGames.map((game) => (
                      <div key={game.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">
                        <div className="flex items-center space-x-3">
                          <TeamLogoMatchup
                            awayTeam={game.awayTeam}
                            homeTeam={game.homeTeam}
                            size="md"
                            showVs={true}
                          />
                          {game.featured && (
                            <Badge variant="secondary">Featured</Badge>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="font-medium">{game.time}</div>
                          <div className="text-sm text-gray-500">{game.network}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'expert-rankings' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Star className="w-5 h-5" />
                    <span>Current Expert Rankings</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {EXPERT_PERSONALITIES.slice(0, 10).map((expert, index) => (
                      <div key={expert.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">
                        <div className="flex items-center space-x-3">
                          <ExpertAvatar
                            expert={expert}
                            size="md"
                            showCouncilBadge={index < 5}
                          />
                          <div>
                            <div className="font-semibold">{expert.name}</div>
                            <div className="text-sm text-gray-500">{expert.archetype}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-green-600">
                            {(expert.accuracy_metrics.overall * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm text-gray-500">
                            {expert.track_record.total_predictions} predictions
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <Button
                    onClick={() => handleFeatureClick('experts')}
                    className="w-full mt-4"
                    variant="outline"
                  >
                    View Full Competition
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'council-votes' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Crown className="w-5 h-5 text-gold-500" />
                    <span>AI Council Voting Power</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {councilMembers.map((member, index) => (
                      <div key={member.id} className="p-4 border rounded-lg bg-gradient-to-r from-gold-50 to-amber-50 dark:from-gold-900/20 dark:to-amber-900/20">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <Crown className="w-5 h-5 text-gold-500" />
                            <span className="font-semibold">{member.name}</span>
                            <Badge variant="secondary">#{member.council_position}</Badge>
                          </div>
                          <div className="text-lg font-bold">
                            {(member.council_weight! * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="h-2 bg-gold-500 rounded-full transition-all duration-500"
                            style={{ width: `${member.council_weight! * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

export default HomePage