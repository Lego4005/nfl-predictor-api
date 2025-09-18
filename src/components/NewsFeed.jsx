import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Newspaper, TrendingUp, TrendingDown, AlertCircle,
  Heart, MessageCircle, Share2, ExternalLink,
  ThumbsUp, ThumbsDown, Zap, Clock
} from 'lucide-react';

const NewsFeed = ({ games }) => {
  const [filter, setFilter] = useState('all');

  // Mock news data with sentiment analysis
  const mockNews = [
    {
      id: 1,
      title: "Patrick Mahomes Returns to Practice After Ankle Scare",
      source: "ESPN",
      time: "2 hours ago",
      category: "injury",
      sentiment: "positive",
      sentimentScore: 0.75,
      impact: "+2.5 points",
      impactTeam: "Chiefs",
      summary: "Chiefs QB fully participated in Thursday's practice, clearing injury concerns ahead of Sunday's game.",
      reactions: { likes: 1240, comments: 89, shares: 45 },
      betImpact: "Line moved from KC -3 to KC -3.5 after news",
      url: "#"
    },
    {
      id: 2,
      title: "Bills' Defense Hit Hard: Three Starters Ruled Out",
      source: "NFL Network",
      time: "4 hours ago",
      category: "injury",
      sentiment: "negative",
      sentimentScore: -0.65,
      impact: "-3.0 points",
      impactTeam: "Bills",
      summary: "Buffalo will be without key defensive players for divisional matchup, significantly impacting their run defense.",
      reactions: { likes: 890, comments: 156, shares: 78 },
      betImpact: "Total dropped from 48.5 to 46.5",
      url: "#"
    },
    {
      id: 3,
      title: "Weather Alert: Storm System to Impact Sunday Games",
      source: "Weather Channel",
      time: "5 hours ago",
      category: "weather",
      sentiment: "neutral",
      sentimentScore: 0,
      impact: "Under favored",
      impactTeam: "Multiple",
      summary: "Heavy rain and 20+ mph winds expected for three outdoor games, historically favoring unders.",
      reactions: { likes: 456, comments: 34, shares: 123 },
      betImpact: "Totals dropping across affected games",
      url: "#"
    },
    {
      id: 4,
      title: "Cowboys Make Surprising QB Change for Prime Time",
      source: "NFL Insider",
      time: "6 hours ago",
      category: "roster",
      sentiment: "negative",
      sentimentScore: -0.45,
      impact: "-1.5 points",
      impactTeam: "Cowboys",
      summary: "Dallas announces backup QB will start on Sunday Night Football due to undisclosed injury to starter.",
      reactions: { likes: 2340, comments: 445, shares: 234 },
      betImpact: "Line moved from DAL -2.5 to DAL +1",
      url: "#"
    },
    {
      id: 5,
      title: "Betting Sharp Report: 78% of Money on Underdog Jets",
      source: "Action Network",
      time: "8 hours ago",
      category: "betting",
      sentiment: "neutral",
      sentimentScore: 0.15,
      impact: "Line movement",
      impactTeam: "Jets",
      summary: "Despite public backing favorites, sharp money flooding Jets +7, suggesting value on the underdog.",
      reactions: { likes: 567, comments: 78, shares: 45 },
      betImpact: "Line moved from +7.5 to +7",
      url: "#"
    }
  ];

  const filteredNews = filter === 'all'
    ? mockNews
    : mockNews.filter(item => item.category === filter);

  const getSentimentIcon = (sentiment) => {
    if (sentiment === 'positive') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (sentiment === 'negative') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <AlertCircle className="w-4 h-4 text-yellow-500" />;
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment === 'positive') return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
    if (sentiment === 'negative') return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
    return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
  };

  const getCategoryColor = (category) => {
    const colors = {
      injury: 'bg-red-600',
      weather: 'bg-blue-600',
      roster: 'bg-purple-600',
      betting: 'bg-green-600',
      general: 'bg-gray-600'
    };
    return colors[category] || colors.general;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Newspaper className="w-5 h-5" />
            <h2 className="text-xl font-bold">News Feed & Market Impact</h2>
          </div>
          <Badge variant="outline" className="animate-pulse">
            <Zap className="w-3 h-3 mr-1" />
            Live Updates
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid grid-cols-5 w-full mb-4">
            <TabsTrigger value="all" onClick={() => setFilter('all')}>All News</TabsTrigger>
            <TabsTrigger value="injury" onClick={() => setFilter('injury')}>Injuries</TabsTrigger>
            <TabsTrigger value="weather" onClick={() => setFilter('weather')}>Weather</TabsTrigger>
            <TabsTrigger value="roster" onClick={() => setFilter('roster')}>Roster</TabsTrigger>
            <TabsTrigger value="betting" onClick={() => setFilter('betting')}>Betting</TabsTrigger>
          </TabsList>

          <div className="space-y-4">
            {filteredNews.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group"
              >
                <Card className="hover:shadow-lg transition-all duration-300 overflow-hidden">
                  <div className="flex">
                    {/* Sentiment Indicator Bar */}
                    <div className={`w-1 ${getSentimentColor(item.sentiment).split(' ')[1]}`} />

                    <div className="flex-1 p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={`${getCategoryColor(item.category)} text-white text-xs`}>
                              {item.category.toUpperCase()}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {item.source} • {item.time}
                            </span>
                          </div>

                          <h3 className="font-semibold text-sm mb-2 group-hover:text-primary transition-colors">
                            {item.title}
                          </h3>

                          <p className="text-xs text-muted-foreground mb-3">
                            {item.summary}
                          </p>

                          {/* Impact Analysis */}
                          <div className="flex flex-wrap gap-3 mb-3">
                            <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${getSentimentColor(item.sentiment)}`}>
                              {getSentimentIcon(item.sentiment)}
                              <span className="font-medium">
                                {item.sentiment === 'positive' ? '+' : item.sentiment === 'negative' ? '-' : ''}
                                {Math.abs(item.sentimentScore * 100).toFixed(0)}% Sentiment
                              </span>
                            </div>

                            {item.impact && (
                              <div className="flex items-center gap-1 px-2 py-1 bg-muted rounded-full text-xs">
                                <TrendingUp className="w-3 h-3" />
                                <span className="font-medium">{item.impact}</span>
                                <span className="text-muted-foreground">impact on {item.impactTeam}</span>
                              </div>
                            )}
                          </div>

                          {/* Betting Impact */}
                          {item.betImpact && (
                            <div className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 p-2 rounded mb-3">
                              <strong>Market Impact:</strong> {item.betImpact}
                            </div>
                          )}

                          {/* Engagement Metrics */}
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <button className="flex items-center gap-1 hover:text-primary transition-colors">
                              <ThumbsUp className="w-3 h-3" />
                              {item.reactions.likes.toLocaleString()}
                            </button>
                            <button className="flex items-center gap-1 hover:text-primary transition-colors">
                              <MessageCircle className="w-3 h-3" />
                              {item.reactions.comments}
                            </button>
                            <button className="flex items-center gap-1 hover:text-primary transition-colors">
                              <Share2 className="w-3 h-3" />
                              {item.reactions.shares}
                            </button>
                            <a href={item.url} className="ml-auto flex items-center gap-1 hover:text-primary transition-colors">
                              <ExternalLink className="w-3 h-3" />
                              Read More
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </Tabs>

        {/* Quick Stats */}
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground">Last updated:</span>
              <span className="font-medium">2 minutes ago</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs">5 Positive</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full" />
                <span className="text-xs">3 Negative</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                <span className="text-xs">2 Neutral</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default NewsFeed;