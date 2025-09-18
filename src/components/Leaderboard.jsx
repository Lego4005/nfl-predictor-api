import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy,
  Medal,
  Award,
  TrendingUp,
  TrendingDown,
  Target,
  Flame,
  Crown,
  Star,
  Users,
  RefreshCw,
  Filter,
  Calendar,
  BarChart3
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

const Leaderboard = () => {
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [timeFilter, setTimeFilter] = useState('season'); // 'week', 'month', 'season', 'all'
  const [sortBy, setSortBy] = useState('accuracy'); // 'accuracy', 'wins', 'streak', 'total_picks'
  const [lastUpdated, setLastUpdated] = useState(null);

  // WebSocket connection for real-time updates
  const [wsConnected, setWsConnected] = useState(false);

  const fetchLeaderboardData = async (showRefreshing = false) => {
    try {
      if (showRefreshing) setRefreshing(true);
      setError(null);

      const response = await fetch(`http://127.0.0.1:8084/api/leaderboard?timeFilter=${timeFilter}&sortBy=${sortBy}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch leaderboard`);
      }

      const data = await response.json();
      setLeaderboardData(data.leaderboard || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      setError(error.message);
      
      // Fallback mock data for development
      setLeaderboardData(getMockLeaderboardData());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://127.0.0.1:8084/ws/leaderboard');
        
        ws.onopen = () => {
          console.log('Leaderboard WebSocket connected');
          setWsConnected(true);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'leaderboard_update') {
              setLeaderboardData(data.leaderboard);
              setLastUpdated(new Date());
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        ws.onclose = () => {
          console.log('Leaderboard WebSocket disconnected');
          setWsConnected(false);
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
        
        ws.onerror = (error) => {
          console.error('Leaderboard WebSocket error:', error);
          setWsConnected(false);
        };
        
        return ws;
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setWsConnected(false);
        return null;
      }
    };

    const ws = connectWebSocket();
    
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // Fetch data on component mount and when filters change
  useEffect(() => {
    fetchLeaderboardData();
  }, [timeFilter, sortBy]);

  // Auto-refresh every 30 seconds if WebSocket is not connected
  useEffect(() => {
    if (!wsConnected) {
      const interval = setInterval(() => {
        fetchLeaderboardData();
      }, 30000);
      
      return () => clearInterval(interval);
    }
  }, [wsConnected, timeFilter, sortBy]);

  const sortedLeaderboard = useMemo(() => {
    if (!leaderboardData.length) return [];
    
    return [...leaderboardData].sort((a, b) => {
      switch (sortBy) {
        case 'accuracy':
          return (b.accuracy || 0) - (a.accuracy || 0);
        case 'wins':
          return (b.wins || 0) - (a.wins || 0);
        case 'streak':
          return Math.abs(b.current_streak || 0) - Math.abs(a.current_streak || 0);
        case 'total_picks':
          return (b.total_picks || 0) - (a.total_picks || 0);
        default:
          return (b.accuracy || 0) - (a.accuracy || 0);
      }
    });
  }, [leaderboardData, sortBy]);

  const getRankIcon = (rank) => {
    switch (rank) {
      case 1:
        return <Trophy className="w-6 h-6 text-yellow-500" />;
      case 2:
        return <Medal className="w-6 h-6 text-gray-400" />;
      case 3:
        return <Award className="w-6 h-6 text-amber-600" />;
      default:
        return <span className="w-6 h-6 flex items-center justify-center text-sm font-bold text-gray-500">#{rank}</span>;
    }
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 70) return 'text-green-600 bg-green-50';
    if (accuracy >= 60) return 'text-blue-600 bg-blue-50';
    if (accuracy >= 50) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getStreakDisplay = (streak) => {
    if (streak > 0) {
      return (
        <div className="flex items-center space-x-1 text-green-600">
          <Flame className="w-4 h-4" />
          <span className="font-semibold">W{streak}</span>
        </div>
      );
    } else if (streak < 0) {
      return (
        <div className="flex items-center space-x-1 text-red-600">
          <TrendingDown className="w-4 h-4" />
          <span className="font-semibold">L{Math.abs(streak)}</span>
        </div>
      );
    }
    return <span className="text-gray-500">-</span>;
  };

  const getMockLeaderboardData = () => [
    {
      user_id: 'user1',
      username: 'GridironGuru',
      avatar: null,
      accuracy: 72.5,
      wins: 29,
      losses: 11,
      total_picks: 40,
      current_streak: 5,
      best_streak: 8,
      points: 145,
      rank: 1
    },
    {
      user_id: 'user2', 
      username: 'TouchdownTony',
      avatar: null,
      accuracy: 68.9,
      wins: 31,
      losses: 14,
      total_picks: 45,
      current_streak: -2,
      best_streak: 6,
      points: 142,
      rank: 2
    },
    {
      user_id: 'user3',
      username: 'PickMaster3000',
      avatar: null,
      accuracy: 66.7,
      wins: 24,
      losses: 12,
      total_picks: 36,
      current_streak: 3,
      best_streak: 7,
      points: 138,
      rank: 3
    },
    {
      user_id: 'user4',
      username: 'NFLOracle',
      avatar: null,
      accuracy: 64.2,
      wins: 27,
      losses: 15,
      total_picks: 42,
      current_streak: 1,
      best_streak: 5,
      points: 135,
      rank: 4
    },
    {
      user_id: 'user5',
      username: 'StatSavant',
      avatar: null,
      accuracy: 62.1,
      wins: 23,
      losses: 14,
      total_picks: 37,
      current_streak: -1,
      best_streak: 4,
      points: 128,
      rank: 5
    }
  ];

  const LeaderboardSkeleton = () => (
    <div className="space-y-4">
      {[...Array(10)].map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 bg-white rounded-lg border">
          <Skeleton className="w-8 h-8 rounded-full" />
          <Skeleton className="w-12 h-12 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
          <div className="text-right space-y-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="w-6 h-6 text-yellow-500" />
            <span>Leaderboard</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LeaderboardSkeleton />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="w-6 h-6 text-yellow-500" />
            <span>Leaderboard</span>
            {wsConnected && (
              <Badge variant="outline" className="ml-2 text-green-600 border-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
                Live
              </Badge>
            )}
          </CardTitle>
          
          <div className="flex items-center space-x-2">
            <Select value={timeFilter} onValueChange={setTimeFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="season">This Season</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="accuracy">Accuracy</SelectItem>
                <SelectItem value="wins">Total Wins</SelectItem>
                <SelectItem value="streak">Streak</SelectItem>
                <SelectItem value="total_picks">Total Picks</SelectItem>
              </SelectContent>
            </Select>
            
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => fetchLeaderboardData(true)}
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        
        {lastUpdated && (
          <p className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}
      </CardHeader>
      
      <CardContent>
        {error && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              {error} (Showing sample data)
            </p>
          </div>
        )}
        
        <Tabs defaultValue="rankings" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="rankings">Rankings</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
          </TabsList>
          
          <TabsContent value="rankings" className="space-y-4">
            <AnimatePresence>
              {sortedLeaderboard.map((user, index) => {
                const rank = index + 1;
                return (
                  <motion.div
                    key={user.user_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className={`flex items-center space-x-4 p-4 rounded-lg border transition-all hover:shadow-md ${
                      rank <= 3 ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200' : 'bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-center w-8">
                      {getRankIcon(rank)}
                    </div>
                    
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={user.avatar} alt={user.username} />
                      <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold">
                        {user.username?.substring(0, 2).toUpperCase() || 'U' + rank}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-gray-900">{user.username || `User ${user.user_id}`}</h3>
                        {rank === 1 && <Crown className="w-4 h-4 text-yellow-500" />}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>{user.wins || 0}W - {user.losses || 0}L</span>
                        <span>{user.total_picks || 0} picks</span>
                        {user.best_streak > 0 && (
                          <span className="text-orange-600">Best: {user.best_streak}</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-right space-y-1">
                      <Badge className={`${getAccuracyColor(user.accuracy || 0)} border-0`}>
                        {(user.accuracy || 0).toFixed(1)}%
                      </Badge>
                      <div className="text-sm">
                        {getStreakDisplay(user.current_streak || 0)}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900">{user.points || 0}</div>
                      <div className="text-xs text-gray-500">points</div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
            
            {sortedLeaderboard.length === 0 && (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
                <p className="text-gray-500">Make some predictions to see the leaderboard!</p>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="stats" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <Target className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Avg Accuracy</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {sortedLeaderboard.length > 0 
                          ? (sortedLeaderboard.reduce((sum, user) => sum + (user.accuracy || 0), 0) / sortedLeaderboard.length).toFixed(1)
                          : '0.0'
                        }%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Users className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Users</p>
                      <p className="text-2xl font-bold text-gray-900">{sortedLeaderboard.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <BarChart3 className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Picks</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {sortedLeaderboard.reduce((sum, user) => sum + (user.total_picks || 0), 0)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default Leaderboard;