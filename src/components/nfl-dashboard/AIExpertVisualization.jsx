import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Brain, 
  Users, 
  TrendingUp, 
  Award, 
  Target, 
  BarChart3,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

const AIExpertVisualization = ({ experts = [], consensusData = [], gameId }) => {
  const [expandedExpert, setExpandedExpert] = useState(null);
  const [viewMode, setViewMode] = useState('overview'); // 'overview' or 'detailed'

  // Mock expert data if none provided
  const mockExperts = [
    {
      expertId: 'expert_1',
      expertName: 'Statistical Sage',
      overallAccuracy: 0.72,
      recentTrend: 'improving',
      voteWeight: {
        expertId: 'expert_1',
        overallWeight: 0.85,
        accuracyComponent: 0.75,
        recentPerformanceComponent: 0.80,
        confidenceComponent: 0.70,
        councilTenureComponent: 0.90,
        normalizedWeight: 0.85
      },
      predictions: [],
      specialization: ['game_outcome', 'betting_markets'],
      joinDate: '2023-01-15',
      totalVotes: 142,
      consensusAlignment: 0.78
    },
    {
      expertId: 'expert_2',
      expertName: 'Weather Wizard',
      overallAccuracy: 0.68,
      recentTrend: 'stable',
      voteWeight: {
        expertId: 'expert_2',
        overallWeight: 0.75,
        accuracyComponent: 0.70,
        recentPerformanceComponent: 0.65,
        confidenceComponent: 0.80,
        councilTenureComponent: 0.85,
        normalizedWeight: 0.75
      },
      predictions: [],
      specialization: ['situational_analysis'],
      joinDate: '2023-03-22',
      totalVotes: 98,
      consensusAlignment: 0.65
    },
    {
      expertId: 'expert_3',
      expertName: 'Injury Insider',
      overallAccuracy: 0.75,
      recentTrend: 'improving',
      voteWeight: {
        expertId: 'expert_3',
        overallWeight: 0.80,
        accuracyComponent: 0.80,
        recentPerformanceComponent: 0.75,
        confidenceComponent: 0.75,
        councilTenureComponent: 0.90,
        normalizedWeight: 0.80
      },
      predictions: [],
      specialization: ['player_props', 'situational_analysis'],
      joinDate: '2023-02-10',
      totalVotes: 126,
      consensusAlignment: 0.82
    },
    {
      expertId: 'expert_4',
      expertName: 'Momentum Master',
      overallAccuracy: 0.65,
      recentTrend: 'declining',
      voteWeight: {
        expertId: 'expert_4',
        overallWeight: 0.65,
        accuracyComponent: 0.60,
        recentPerformanceComponent: 0.55,
        confidenceComponent: 0.70,
        councilTenureComponent: 0.75,
        normalizedWeight: 0.65
      },
      predictions: [],
      specialization: ['live_scenarios'],
      joinDate: '2023-04-05',
      totalVotes: 87,
      consensusAlignment: 0.58
    }
  ];

  const expertsToDisplay = experts.length > 0 ? experts : mockExperts;

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'declining':
        return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />;
      default:
        return <BarChart3 className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'improving':
        return 'text-green-600 bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800';
      case 'declining':
        return 'text-red-600 bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700';
    }
  };

  const getWeightColor = (weight) => {
    if (weight >= 0.8) return 'bg-gradient-to-r from-purple-500 to-purple-600';
    if (weight >= 0.6) return 'bg-gradient-to-r from-blue-500 to-blue-600';
    if (weight >= 0.4) return 'bg-gradient-to-r from-green-500 to-green-600';
    if (weight >= 0.2) return 'bg-gradient-to-r from-yellow-500 to-yellow-600';
    return 'bg-gradient-to-r from-gray-400 to-gray-500';
  };

  const toggleExpert = (expertId) => {
    setExpandedExpert(expandedExpert === expertId ? null : expertId);
  };

  return (
    <div className="space-y-6">
      {/* Council Overview Card */}
      <Card className="dashboard-card">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" />
              <CardTitle className="dashboard-text">AI Council Overview</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-[hsl(var(--dashboard-surface))] border-gray-700 text-xs dashboard-text">
                {expertsToDisplay.length} Experts
              </Badge>
              <Badge variant="outline" className="bg-[hsl(var(--dashboard-surface))] border-gray-700 text-xs dashboard-text">
                Live Consensus
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg">
              <Users className="h-5 w-5 text-blue-400 mx-auto mb-1" />
              <div className="text-xl font-bold dashboard-text">
                {expertsToDisplay.length}
              </div>
              <div className="text-xs dashboard-muted">Active Experts</div>
            </div>
            
            <div className="text-center p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg">
              <Target className="h-5 w-5 text-green-400 mx-auto mb-1" />
              <div className="text-xl font-bold dashboard-text">
                {(expertsToDisplay.reduce((sum, e) => sum + e.overallAccuracy, 0) / expertsToDisplay.length * 100).toFixed(1)}%
              </div>
              <div className="text-xs dashboard-muted">Avg Accuracy</div>
            </div>
            
            <div className="text-center p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg">
              <BarChart3 className="h-5 w-5 text-purple-400 mx-auto mb-1" />
              <div className="text-xl font-bold dashboard-text">
                {(expertsToDisplay.reduce((sum, e) => sum + e.consensusAlignment, 0) / expertsToDisplay.length * 100).toFixed(1)}%
              </div>
              <div className="text-xs dashboard-muted">Consensus Alignment</div>
            </div>
            
            <div className="text-center p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg">
              <Award className="h-5 w-5 text-yellow-400 mx-auto mb-1" />
              <div className="text-xl font-bold dashboard-text">
                {(expertsToDisplay.reduce((sum, e) => sum + e.voteWeight.normalizedWeight, 0) / expertsToDisplay.length * 100).toFixed(1)}%
              </div>
              <div className="text-xs dashboard-muted">Avg Vote Weight</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Expert Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {expertsToDisplay.map((expert, index) => (
          <motion.div
            key={expert.expertId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card 
              className="dashboard-card cursor-pointer hover:opacity-90 transition-opacity"
              onClick={() => toggleExpert(expert.expertId)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                      <span className="text-white font-bold text-sm">
                        {expert.expertName.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </span>
                    </div>
                    
                    <div>
                      <h3 className="font-semibold dashboard-text">
                        {expert.expertName}
                      </h3>
                      <div className="flex items-center gap-1 mt-1">
                        {getTrendIcon(expert.recentTrend)}
                        <span className="text-xs dashboard-muted capitalize">
                          {expert.recentTrend}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Performance Badge */}
                  <Badge variant="outline" className={getTrendColor(expert.recentTrend)}>
                    {(expert.overallAccuracy * 100).toFixed(1)}%
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Vote Weight Visualization */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium dashboard-muted">
                      Vote Weight
                    </span>
                    <span className="text-xs font-bold dashboard-text">
                      {(expert.voteWeight.normalizedWeight * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="w-full bg-gray-800 rounded-full h-2.5">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${expert.voteWeight.normalizedWeight * 100}%` }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      className={`h-2.5 rounded-full ${getWeightColor(expert.voteWeight.normalizedWeight)}`}
                    />
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <Target className="h-3 w-3 text-green-400" />
                    <span className="dashboard-muted">Accuracy:</span>
                    <span className="font-semibold dashboard-text">{(expert.overallAccuracy * 100).toFixed(1)}%</span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Users className="h-3 w-3 text-blue-400" />
                    <span className="dashboard-muted">Votes:</span>
                    <span className="font-semibold dashboard-text">{expert.totalVotes}</span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <BarChart3 className="h-3 w-3 text-purple-400" />
                    <span className="dashboard-muted">Alignment:</span>
                    <span className="font-semibold dashboard-text">{(expert.consensusAlignment * 100).toFixed(0)}%</span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Award className="h-3 w-3 text-yellow-400" />
                    <span className="dashboard-muted">Since:</span>
                    <span className="font-semibold dashboard-text">
                      {new Date(expert.joinDate).getFullYear()}
                    </span>
                  </div>
                </div>

                {/* Specializations */}
                <div className="space-y-2">
                  <span className="text-xs font-medium dashboard-muted">
                    Specializations
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {expert.specialization.slice(0, 2).map((spec, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="text-xs py-0.5 px-2 bg-blue-900/20 text-blue-400 border-blue-800"
                      >
                        {spec.replace('_', ' ')}
                      </Badge>
                    ))}
                    {expert.specialization.length > 2 && (
                      <Badge variant="outline" className="text-xs py-0.5 px-2 dashboard-text border-gray-700">
                        +{expert.specialization.length - 2}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Expand/Collapse Indicator */}
                <div className="flex justify-center">
                  {expandedExpert === expert.expertId ? (
                    <ChevronUp className="h-4 w-4 dashboard-muted" />
                  ) : (
                    <ChevronDown className="h-4 w-4 dashboard-muted" />
                  )}
                </div>
              </CardContent>

              {/* Expanded Details */}
              {expandedExpert === expert.expertId && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="px-6 pb-6 border-t border-gray-700"
                >
                  <div className="space-y-3 pt-4">
                    {/* Vote Weight Components */}
                    <div className="space-y-2">
                      <span className="text-xs font-medium dashboard-muted">
                        Weight Breakdown
                      </span>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="dashboard-muted">Accuracy</span>
                          <span className="dashboard-text">{(expert.voteWeight.accuracyComponent * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="dashboard-muted">Recent Performance</span>
                          <span className="dashboard-text">{(expert.voteWeight.recentPerformanceComponent * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="dashboard-muted">Confidence</span>
                          <span className="dashboard-text">{(expert.voteWeight.confidenceComponent * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="dashboard-muted">Tenure</span>
                          <span className="dashboard-text">{(expert.voteWeight.councilTenureComponent * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Expert Prediction */}
                    <div className="p-3 bg-[hsl(var(--dashboard-surface))] rounded">
                      <h4 className="text-sm font-semibold dashboard-text mb-2">Latest Prediction</h4>
                      <p className="text-xs dashboard-muted">
                        Based on comprehensive analysis of team statistics, player performance, and situational factors.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Consensus Visualization */}
      {consensusData.length > 0 && (
        <Card className="dashboard-card">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-green-400" />
              <CardTitle className="dashboard-text">Consensus Analysis</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {consensusData.slice(0, 3).map((consensus, index) => (
                <div key={index} className="p-3 bg-[hsl(var(--dashboard-surface))] rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-semibold dashboard-text">
                      {consensus.categoryId.replace('_', ' ')}
                    </span>
                    <Badge variant="outline" className="text-xs dashboard-text border-gray-700">
                      {(consensus.confidence * 100).toFixed(1)}% Confidence
                    </Badge>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: `${consensus.confidence * 100}%` }}
                    />
                  </div>
                  <div className="mt-2 text-xs dashboard-muted">
                    Agreement: {consensus.agreement.toFixed(2)} | 
                    Experts: {consensus.totalExperts}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AIExpertVisualization;