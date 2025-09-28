import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, Users, TrendingUp, Award, 
  Clock, BarChart3, Target, Zap 
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/tabs';
import CouncilMemberCard from './CouncilMemberCard';
import VoteWeightBreakdown from './VoteWeightBreakdown';
import ConsensusVisualization from './ConsensusVisualization';
import CouncilDecisionTimeline from './CouncilDecisionTimeline';
import type { 
  AICouncilDashboardProps, 
  CouncilMember,
  ConsensusResult,
  VoteWeight,
  CouncilDecision
} from '../../types/aiCouncil';

const AICouncilDashboard: React.FC<AICouncilDashboardProps> = ({
  gameId,
  councilMembers,
  consensusData,
  voteWeights,
  onExpertSelect,
  refreshInterval = 30000
}) => {
  const [selectedExpert, setSelectedExpert] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'comparison'>('overview');
  const [sortOrder, setSortOrder] = useState<'weight' | 'accuracy' | 'recent'>('weight');
  const [activeTab, setActiveTab] = useState('council');
  const [showWeightBreakdown, setShowWeightBreakdown] = useState(false);

  // Sort council members based on selected order
  const sortedMembers = React.useMemo(() => {
    return [...councilMembers].sort((a, b) => {
      switch (sortOrder) {
        case 'weight':
          return b.voteWeight.normalizedWeight - a.voteWeight.normalizedWeight;
        case 'accuracy':
          return b.overallAccuracy - a.overallAccuracy;
        case 'recent':
          // Sort by recent trend and then accuracy
          const trendScore = (trend: string) => 
            trend === 'improving' ? 2 : trend === 'stable' ? 1 : 0;
          return trendScore(b.recentTrend) - trendScore(a.recentTrend) ||
                 b.overallAccuracy - a.overallAccuracy;
        default:
          return 0;
      }
    });
  }, [councilMembers, sortOrder]);

  // Calculate council statistics
  const councilStats = React.useMemo(() => {
    const totalWeight = voteWeights.reduce((sum, w) => sum + w.normalizedWeight, 0);
    const avgAccuracy = councilMembers.reduce((sum, m) => sum + m.overallAccuracy, 0) / councilMembers.length;
    const consensusStrength = consensusData.reduce((sum, c) => sum + c.confidence, 0) / consensusData.length;
    
    return {
      totalMembers: councilMembers.length,
      avgAccuracy: avgAccuracy * 100,
      consensusStrength: consensusStrength * 100,
      totalWeight: totalWeight,
      activeExperts: councilMembers.filter(m => m.recentTrend !== 'declining').length
    };
  }, [councilMembers, voteWeights, consensusData]);

  const handleExpertSelect = (expertId: string) => {
    setSelectedExpert(expertId === selectedExpert ? null : expertId);
    onExpertSelect(expertId);
  };

  return (
    <div className="w-full space-y-6">
      {/* Header Section */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-xl">
            <Brain className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              AI Council Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Expert consensus and voting weight analysis
            </p>
          </div>
        </div>

        {/* Council Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg border">
            <Users className="h-5 w-5 text-blue-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {councilStats.totalMembers}
            </div>
            <div className="text-xs text-gray-500">Active Experts</div>
          </div>
          
          <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg border">
            <Target className="h-5 w-5 text-green-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {councilStats.avgAccuracy.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Avg Accuracy</div>
          </div>
          
          <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg border">
            <BarChart3 className="h-5 w-5 text-purple-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {councilStats.consensusStrength.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Consensus</div>
          </div>
          
          <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg border">
            <Zap className="h-5 w-5 text-orange-500 mx-auto mb-1" />
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {councilStats.activeExperts}
            </div>
            <div className="text-xs text-gray-500">Improving</div>
          </div>
        </div>
      </div>

      {/* Control Bar */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={viewMode === 'overview' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('overview')}
          >
            Overview
          </Button>
          <Button
            variant={viewMode === 'detailed' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('detailed')}
          >
            Detailed
          </Button>
          <Button
            variant={viewMode === 'comparison' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('comparison')}
          >
            Comparison
          </Button>
        </div>

        <div className="flex gap-2">
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="weight">Sort by Vote Weight</option>
            <option value="accuracy">Sort by Accuracy</option>
            <option value="recent">Sort by Recent Performance</option>
          </select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowWeightBreakdown(!showWeightBreakdown)}
          >
            {showWeightBreakdown ? 'Hide' : 'Show'} Weight Details
          </Button>
        </div>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="council">Council Members</TabsTrigger>
          <TabsTrigger value="consensus">Consensus View</TabsTrigger>
          <TabsTrigger value="weights">Vote Weights</TabsTrigger>
          <TabsTrigger value="timeline">Decision Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="council" className="space-y-4 mt-6">
          {/* Council Members Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {sortedMembers.map((member, index) => (
                <motion.div
                  key={member.expertId}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <CouncilMemberCard
                    member={member}
                    isSelected={selectedExpert === member.expertId}
                    onSelect={handleExpertSelect}
                    showDetailedMetrics={viewMode === 'detailed'}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Selected Expert Details */}
          {selectedExpert && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6"
            >
              <Card className="border-blue-200 dark:border-blue-800">
                <CardHeader className="bg-blue-50 dark:bg-blue-900/20">
                  <h3 className="text-lg font-semibold">
                    Expert Deep Dive: {
                      councilMembers.find(m => m.expertId === selectedExpert)?.expertName
                    }
                  </h3>
                </CardHeader>
                <CardContent className="p-6">
                  {showWeightBreakdown && (
                    <VoteWeightBreakdown
                      voteWeight={
                        voteWeights.find(w => w.expertId === selectedExpert)!
                      }
                      showComponents={true}
                      animated={true}
                    />
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </TabsContent>

        <TabsContent value="consensus" className="mt-6">
          <ConsensusVisualization
            consensusResults={consensusData}
            activeCategoryFilter="all"
            showConfidenceIndicators={true}
          />
        </TabsContent>

        <TabsContent value="weights" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {voteWeights.map((weight) => (
              <VoteWeightBreakdown
                key={weight.expertId}
                voteWeight={weight}
                showComponents={true}
                animated={false}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="mt-6">
          <CouncilDecisionTimeline
            decisions={[]} // This would come from props or API
            gameId={gameId}
            maxItems={10}
          />
        </TabsContent>
      </Tabs>

      {/* Live Update Indicator */}
      <div className="fixed bottom-4 right-4">
        <Badge
          variant="outline"
          className="bg-white dark:bg-gray-800 shadow-lg animate-pulse"
        >
          <Clock className="h-3 w-3 mr-1" />
          Live Updates: {refreshInterval / 1000}s
        </Badge>
      </div>
    </div>
  );
};

export default AICouncilDashboard;