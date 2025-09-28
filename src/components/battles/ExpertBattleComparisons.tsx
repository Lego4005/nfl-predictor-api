import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sword, Users, BarChart3, TrendingUp, 
  Target, Award, AlertTriangle, Crown
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/tabs';
import { Avatar, AvatarFallback } from '../ui/avatar';
import HeadToHeadComparison from './HeadToHeadComparison';
import DisagreementAnalysis from './DisagreementAnalysis';
import ExpertSpecializationRadar from './ExpertSpecializationRadar';
import type { 
  ExpertBattleProps,
  CouncilMember,
  HeadToHeadComparison as H2HComparison,
  DisagreementAnalysis as DisagreementAnalysisType
} from '../../types/aiCouncil';

const ExpertBattleComparisons: React.FC<ExpertBattleProps> = ({
  expertIds,
  comparisonMetric,
  timeRange
}) => {
  const [selectedExperts, setSelectedExperts] = useState<string[]>(expertIds.slice(0, 2));
  const [activeTab, setActiveTab] = useState('head-to-head');
  const [sortBy, setSortBy] = useState<'winRate' | 'totalBattles' | 'recentForm'>('winRate');

  // Mock expert data
  const mockExperts: CouncilMember[] = [
    {
      expertId: 'expert_1',
      expertName: 'AI Prophet',
      overallAccuracy: 0.78,
      recentTrend: 'improving',
      voteWeight: {
        expertId: 'expert_1',
        overallWeight: 0.85,
        accuracyComponent: 0.82,
        recentPerformanceComponent: 0.89,
        confidenceComponent: 0.75,
        councilTenureComponent: 0.92,
        normalizedWeight: 0.85
      },
      predictions: [],
      specialization: ['game_outcome', 'betting_markets'],
      joinDate: '2023-01-01',
      totalVotes: 245,
      consensusAlignment: 0.73
    },
    {
      expertId: 'expert_2',
      expertName: 'Statistical Sage',
      overallAccuracy: 0.74,
      recentTrend: 'stable',
      voteWeight: {
        expertId: 'expert_2',
        overallWeight: 0.76,
        accuracyComponent: 0.74,
        recentPerformanceComponent: 0.72,
        confidenceComponent: 0.81,
        councilTenureComponent: 0.88,
        normalizedWeight: 0.76
      },
      predictions: [],
      specialization: ['player_props', 'situational_analysis'],
      joinDate: '2023-02-15',
      totalVotes: 198,
      consensusAlignment: 0.82
    },
    {
      expertId: 'expert_3',
      expertName: 'Game Theory Guru',
      overallAccuracy: 0.81,
      recentTrend: 'improving',
      voteWeight: {
        expertId: 'expert_3',
        overallWeight: 0.89,
        accuracyComponent: 0.91,
        recentPerformanceComponent: 0.87,
        confidenceComponent: 0.86,
        councilTenureComponent: 0.78,
        normalizedWeight: 0.89
      },
      predictions: [],
      specialization: ['live_scenarios', 'betting_markets'],
      joinDate: '2023-03-10',
      totalVotes: 167,
      consensusAlignment: 0.68
    },
    {
      expertId: 'expert_4',
      expertName: 'Data Dynamo',
      overallAccuracy: 0.72,
      recentTrend: 'declining',
      voteWeight: {
        expertId: 'expert_4',
        overallWeight: 0.71,
        accuracyComponent: 0.72,
        recentPerformanceComponent: 0.65,
        confidenceComponent: 0.78,
        councilTenureComponent: 0.85,
        normalizedWeight: 0.71
      },
      predictions: [],
      specialization: ['player_props', 'game_outcome'],
      joinDate: '2023-01-20',
      totalVotes: 223,
      consensusAlignment: 0.75
    }
  ];

  // Generate mock battle statistics
  const battleStats = useMemo(() => {
    return mockExperts.map(expert => ({
      expertId: expert.expertId,
      totalBattles: Math.floor(Math.random() * 50) + 20,
      wins: Math.floor(Math.random() * 30) + 15,
      losses: Math.floor(Math.random() * 25) + 10,
      ties: Math.floor(Math.random() * 5),
      winRate: Math.random() * 0.4 + 0.4, // 40-80%
      recentForm: Math.random() > 0.6 ? 'hot' : Math.random() > 0.3 ? 'warm' : 'cold',
      strongestCategory: expert.specialization[0],
      weakestCategory: expert.specialization[1] || 'situational_analysis'
    }));
  }, [mockExperts]);

  const availableExperts = mockExperts.filter(expert => 
    expertIds.includes(expert.expertId)
  );

  const getExpertById = (id: string) => 
    availableExperts.find(expert => expert.expertId === id);

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return 'text-green-600 bg-green-100';
      case 'declining': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getFormColor = (form: string) => {
    switch (form) {
      case 'hot': return 'text-red-600 bg-red-100';
      case 'warm': return 'text-yellow-600 bg-yellow-100';
      case 'cold': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const handleExpertSelection = (expertId: string) => {
    if (selectedExperts.includes(expertId)) {
      setSelectedExperts(prev => prev.filter(id => id !== expertId));
    } else if (selectedExperts.length < 2) {
      setSelectedExperts(prev => [...prev, expertId]);
    } else {
      setSelectedExperts([selectedExperts[1], expertId]);
    }
  };

  const sortedExperts = useMemo(() => {
    const expertsWithStats = availableExperts.map(expert => {
      const stats = battleStats.find(s => s.expertId === expert.expertId)!;
      return { ...expert, ...stats };
    });

    return expertsWithStats.sort((a, b) => {
      switch (sortBy) {
        case 'winRate':
          return b.winRate - a.winRate;
        case 'totalBattles':
          return b.totalBattles - a.totalBattles;
        case 'recentForm':
          const formScore = (form: string) => 
            form === 'hot' ? 3 : form === 'warm' ? 2 : form === 'cold' ? 1 : 0;
          return formScore(b.recentForm) - formScore(a.recentForm);
        default:
          return 0;
      }
    });
  }, [availableExperts, battleStats, sortBy]);

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-orange-100 dark:bg-orange-900/20 rounded-xl">
            <Sword className="h-8 w-8 text-orange-600 dark:text-orange-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Expert Battle Arena
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Head-to-head expert comparisons and performance analysis
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="winRate">Sort by Win Rate</option>
            <option value="totalBattles">Sort by Total Battles</option>
            <option value="recentForm">Sort by Recent Form</option>
          </select>
        </div>
      </div>

      {/* Expert Selection Grid */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Select Experts to Compare
          </CardTitle>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Choose up to 2 experts for head-to-head analysis
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {sortedExperts.map((expert) => {
              const isSelected = selectedExperts.includes(expert.expertId);
              const stats = battleStats.find(s => s.expertId === expert.expertId)!;
              
              return (
                <motion.div
                  key={expert.expertId}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Card 
                    className={`
                      cursor-pointer transition-all duration-200
                      ${isSelected 
                        ? 'ring-2 ring-orange-500 border-orange-300 bg-orange-50' 
                        : 'hover:shadow-md border-gray-200'
                      }
                    `}
                    onClick={() => handleExpertSelection(expert.expertId)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className="bg-orange-100 text-orange-600">
                            {expert.expertName.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm truncate">
                            {expert.expertName}
                          </h3>
                          <div className="flex items-center gap-2">
                            <Badge className={getTrendColor(expert.recentTrend)}>
                              {expert.recentTrend}
                            </Badge>
                            <Badge className={getFormColor(stats.recentForm)}>
                              {stats.recentForm}
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-600">Win Rate</span>
                          <span className="font-semibold">
                            {(stats.winRate * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={stats.winRate * 100} className="h-1.5" />
                        
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-600">Battles</span>
                          <span className="font-semibold">
                            {stats.wins}W-{stats.losses}L-{stats.ties}T
                          </span>
                        </div>
                        
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-600">Accuracy</span>
                          <span className="font-semibold">
                            {(expert.overallAccuracy * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Comparison Content */}
      {selectedExperts.length >= 2 && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="head-to-head">Head-to-Head</TabsTrigger>
            <TabsTrigger value="disagreements">Disagreements</TabsTrigger>
            <TabsTrigger value="specialization">Specialization</TabsTrigger>
          </TabsList>

          <TabsContent value="head-to-head" className="mt-6">
            <HeadToHeadComparison
              expert1={getExpertById(selectedExperts[0])!}
              expert2={getExpertById(selectedExperts[1])!}
              timeRange={timeRange}
            />
          </TabsContent>

          <TabsContent value="disagreements" className="mt-6">
            <DisagreementAnalysis
              expertIds={selectedExperts}
              timeRange={timeRange}
            />
          </TabsContent>

          <TabsContent value="specialization" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {selectedExperts.map(expertId => (
                <ExpertSpecializationRadar
                  key={expertId}
                  expert={getExpertById(expertId)!}
                />
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}

      {/* Quick Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <Crown className="h-6 w-6 text-yellow-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {sortedExperts[0]?.expertName || 'N/A'}
            </div>
            <div className="text-xs text-gray-500">Top Win Rate</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <BarChart3 className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {battleStats.reduce((sum, s) => sum + s.totalBattles, 0)}
            </div>
            <div className="text-xs text-gray-500">Total Battles</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <Target className="h-6 w-6 text-green-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {((battleStats.reduce((sum, s) => sum + s.winRate, 0) / battleStats.length) * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Avg Win Rate</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <TrendingUp className="h-6 w-6 text-purple-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {battleStats.filter(s => s.recentForm === 'hot').length}
            </div>
            <div className="text-xs text-gray-500">Hot Streak</div>
          </div>
        </Card>
      </div>

      {/* Empty State */}
      {selectedExperts.length < 2 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500 dark:text-gray-400">
            <Sword className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Select Experts to Begin Battle</h3>
            <p className="text-sm">
              Choose 2 experts from the grid above to start comparing their performance,
              accuracy, and head-to-head battle records.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ExpertBattleComparisons;