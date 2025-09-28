import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Clock, Users, AlertTriangle, CheckCircle, 
  TrendingUp, Gavel, MessageSquare, MoreHorizontal,
  Calendar, Filter
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { Separator } from '../ui/separator';
import type { 
  CouncilDecisionTimelineProps, 
  CouncilDecision 
} from '../../types/aiCouncil';

const CouncilDecisionTimeline: React.FC<CouncilDecisionTimelineProps> = ({
  decisions,
  gameId,
  maxItems = 10
}) => {
  const [showAll, setShowAll] = useState(false);
  const [filterType, setFilterType] = useState<'all' | 'consensus' | 'majority' | 'override'>('all');

  // Mock decisions for demonstration (in real implementation, this would come from props)
  const mockDecisions: CouncilDecision[] = [
    {
      id: '1',
      gameId,
      decisionType: 'consensus',
      categoryId: 'game_outcome_winner',
      finalValue: 'home_team',
      confidence: 0.92,
      votingRound: 1,
      timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 minutes ago
      participatingExperts: ['expert_1', 'expert_2', 'expert_3', 'expert_4'],
      dissenting: [],
      reasoning: 'Unanimous agreement based on home field advantage and recent performance trends.'
    },
    {
      id: '2',
      gameId,
      decisionType: 'majority',
      categoryId: 'betting_markets_spread',
      finalValue: -3.5,
      confidence: 0.75,
      votingRound: 2,
      timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(), // 25 minutes ago
      participatingExperts: ['expert_1', 'expert_2', 'expert_3', 'expert_4', 'expert_5'],
      dissenting: ['expert_5'],
      reasoning: 'Majority consensus with one dissenting expert citing injury concerns.'
    },
    {
      id: '3',
      gameId,
      decisionType: 'expert_override',
      categoryId: 'player_props_passing',
      finalValue: 285.5,
      confidence: 0.68,
      votingRound: 3,
      timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 minutes ago
      participatingExperts: ['expert_1', 'expert_2'],
      dissenting: ['expert_3', 'expert_4'],
      reasoning: 'Expert override due to late-breaking weather information affecting passing game.'
    }
  ];

  const displayDecisions = mockDecisions.length > 0 ? mockDecisions : decisions;

  // Filter decisions based on type
  const filteredDecisions = React.useMemo(() => {
    let filtered = displayDecisions;
    
    if (filterType !== 'all') {
      filtered = filtered.filter(decision => decision.decisionType === filterType);
    }

    // Sort by timestamp (most recent first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    // Apply maxItems limit if not showing all
    if (!showAll && maxItems) {
      filtered = filtered.slice(0, maxItems);
    }

    return filtered;
  }, [displayDecisions, filterType, showAll, maxItems]);

  const getDecisionIcon = (decisionType: string) => {
    switch (decisionType) {
      case 'consensus':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'majority':
        return <Users className="h-5 w-5 text-blue-500" />;
      case 'expert_override':
        return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      default:
        return <Gavel className="h-5 w-5 text-gray-500" />;
    }
  };

  const getDecisionBadgeColor = (decisionType: string) => {
    switch (decisionType) {
      case 'consensus':
        return 'bg-green-100 text-green-800';
      case 'majority':
        return 'bg-blue-100 text-blue-800';
      case 'expert_override':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-blue-600';
    if (confidence >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getCategoryDisplayName = (categoryId: string) => {
    const categoryNames: Record<string, string> = {
      'game_outcome_winner': 'Game Winner',
      'betting_markets_spread': 'Point Spread',
      'player_props_passing': 'Passing Yards',
      'live_scenarios_momentum': 'Game Momentum'
    };
    return categoryNames[categoryId] || categoryId.replace(/_/g, ' ');
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Decision Timeline
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            Chronological record of AI Council voting decisions
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800"
          >
            <option value="all">All Decisions</option>
            <option value="consensus">Consensus Only</option>
            <option value="majority">Majority Only</option>
            <option value="expert_override">Overrides Only</option>
          </select>

          {displayDecisions.length > maxItems && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? 'Show Less' : `Show All ${displayDecisions.length}`}
            </Button>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

        <div className="space-y-6">
          <AnimatePresence>
            {filteredDecisions.map((decision, index) => (
              <motion.div
                key={decision.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.1 }}
                className="relative flex gap-4"
              >
                {/* Timeline Node */}
                <div className="relative flex-shrink-0">
                  <div className="w-16 h-16 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center">
                    {getDecisionIcon(decision.decisionType)}
                  </div>
                  
                  {/* Confidence Ring */}
                  <div className="absolute inset-0 rounded-full">
                    <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 64 64">
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="text-gray-200 dark:text-gray-700"
                      />
                      <circle
                        cx="32"
                        cy="32"
                        r="28"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeDasharray={`${decision.confidence * 175.92} 175.92`}
                        className={getConfidenceColor(decision.confidence)}
                      />
                    </svg>
                  </div>
                </div>

                {/* Decision Card */}
                <Card className="flex-1">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {getCategoryDisplayName(decision.categoryId)}
                          </h3>
                          <Badge 
                            variant="secondary" 
                            className={getDecisionBadgeColor(decision.decisionType)}
                          >
                            {decision.decisionType.replace('_', ' ')}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {formatTimeAgo(decision.timestamp)}
                          </div>
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" />
                            Round {decision.votingRound}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className={`text-lg font-bold ${getConfidenceColor(decision.confidence)}`}>
                          {(decision.confidence * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500">confidence</div>
                      </div>
                    </div>

                    {/* Decision Value */}
                    <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Final Decision:
                        </span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">
                          {typeof decision.finalValue === 'number' 
                            ? decision.finalValue.toFixed(1)
                            : String(decision.finalValue)
                          }
                        </span>
                      </div>
                    </div>

                    {/* Participating Experts */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-gray-500" />
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          {decision.participatingExperts.length} experts
                        </span>
                        <div className="flex -space-x-2">
                          {decision.participatingExperts.slice(0, 3).map((expertId, i) => (
                            <Avatar key={expertId} className="h-6 w-6 border-2 border-white dark:border-gray-800">
                              <AvatarFallback className="text-xs">
                                E{i + 1}
                              </AvatarFallback>
                            </Avatar>
                          ))}
                          {decision.participatingExperts.length > 3 && (
                            <div className="h-6 w-6 rounded-full bg-gray-200 dark:bg-gray-700 border-2 border-white dark:border-gray-800 flex items-center justify-center">
                              <span className="text-xs text-gray-600 dark:text-gray-300">
                                +{decision.participatingExperts.length - 3}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {decision.dissenting.length > 0 && (
                        <div className="flex items-center gap-1">
                          <AlertTriangle className="h-4 w-4 text-orange-500" />
                          <span className="text-sm text-orange-600 dark:text-orange-400">
                            {decision.dissenting.length} dissenting
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Reasoning */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="h-4 w-4 text-gray-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Reasoning
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                        {decision.reasoning}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Empty State */}
      {filteredDecisions.length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-500 dark:text-gray-400">
            <Calendar className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No decisions found</h3>
            <p className="text-sm">
              {filterType === 'all' 
                ? 'No council decisions have been made for this game yet.'
                : `No ${filterType.replace('_', ' ')} decisions found for the selected filter.`
              }
            </p>
          </div>
        </Card>
      )}

      {/* Load More (if there are more decisions) */}
      {!showAll && displayDecisions.length > maxItems && (
        <div className="text-center pt-4">
          <Button variant="outline" onClick={() => setShowAll(true)}>
            <MoreHorizontal className="h-4 w-4 mr-2" />
            Load {displayDecisions.length - maxItems} More Decisions
          </Button>
        </div>
      )}
    </div>
  );
};

export default CouncilDecisionTimeline;