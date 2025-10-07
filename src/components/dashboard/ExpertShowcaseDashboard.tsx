/**
 * Expert Showcase Dashboard
 * Main dashboard displaying all 15 experts with competitive dynamics using BentoGrid layout
 */

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Crown, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Award, 
  Star, 
  Zap,
  Activity,
  BarChart3,
  Filter,
  Eye,
  ChevronRight,
  Trophy,
  Medal,
  Flame
} from 'lucide-react';

import { BentoGrid } from '@/components/kokonutui/bento-grid';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import ExpertAvatar from '@/components/ui/ExpertAvatar';

import { 
  ExpertPersonality, 
  EXPERT_PERSONALITIES, 
  getCouncilMembers, 
  getNonCouncilExperts 
} from '@/data/expertPersonalities';
import { 
  CouncilMember, 
  getCurrentCouncil, 
  performCouncilSelection 
} from '@/services/councilSelection';

interface ExpertShowcaseDashboardProps {
  onExpertSelect?: (expertId: string) => void;
  onCouncilView?: () => void;
  className?: string;
}

interface ExpertCardProps {
  expert: ExpertPersonality;
  rank: number;
  isCouncilMember: boolean;
  onSelect: (expertId: string) => void;
  showDetailed?: boolean;
}

const ExpertCard: React.FC<ExpertCardProps> = ({ 
  expert, 
  rank, 
  isCouncilMember, 
  onSelect,
  showDetailed = false 
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.7) return 'text-green-500';
    if (accuracy >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getTrendIcon = (recent: number, overall: number) => {
    if (recent > overall + 0.02) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (recent < overall - 0.02) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Target className="w-4 h-4 text-gray-500" />;
  };

  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'aggressive': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300';
      case 'moderate': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'conservative': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300';
    }
  };

  return (
    <motion.div
      className={cn(
        "relative overflow-hidden rounded-xl border transition-all duration-300 cursor-pointer expert-card-mobile",
        isCouncilMember
          ? "border-gold-500/50 bg-gradient-to-br from-gold-50 to-amber-50 dark:from-gold-900/20 dark:to-amber-900/20"
          : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800",
        isHovered && "shadow-lg scale-[1.02]"
      )}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={() => onSelect(expert.id)}
    >
      {/* Council Member Crown */}
      {isCouncilMember && (
        <div className="absolute top-2 left-2 z-10">
          <Crown className="w-5 h-5 text-gold-500" />
        </div>
      )}

      {/* Rank Badge */}
      <div className={cn(
        "absolute top-2 right-2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
        rank <= 3 
          ? rank === 1 
            ? "bg-gold-500 text-white" 
            : rank === 2 
              ? "bg-silver-500 text-white" 
              : "bg-bronze-500 text-white"
          : isCouncilMember
            ? "bg-purple-500 text-white"
            : "bg-gray-500 text-white"
      )}>
        #{rank}
      </div>

      <CardContent className="p-4 space-y-3">
        {/* Expert Header */}
        <div className="flex items-start space-x-3">
          <ExpertAvatar
            expert={expert}
            size="lg"
            showCouncilBadge={false}
            showHoverEffect={false}
          />
          <div className="flex-1 space-y-1">
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white truncate">
              {expert.name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {expert.archetype}
            </p>
            <p className="text-xs text-gray-500 italic">
              "{expert.motto}"
            </p>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Accuracy</span>
            <div className="flex items-center space-x-1">
              <span className={cn("font-bold text-lg", getAccuracyColor(expert.accuracy_metrics.overall))}>
                {(expert.accuracy_metrics.overall * 100).toFixed(1)}%
              </span>
              {getTrendIcon(expert.accuracy_metrics.recent_performance, expert.accuracy_metrics.overall)}
            </div>
          </div>

          {/* Accuracy Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <motion.div
              className={cn(
                "h-2 rounded-full",
                expert.accuracy_metrics.overall >= 0.7 ? "bg-green-500" :
                expert.accuracy_metrics.overall >= 0.6 ? "bg-yellow-500" : "bg-red-500"
              )}
              initial={{ width: 0 }}
              animate={{ width: `${expert.accuracy_metrics.overall * 100}%` }}
              transition={{ duration: 1, delay: 0.2 }}
            />
          </div>
        </div>

        {/* Key Stats */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-500">Predictions</span>
            <div className="font-semibold">{expert.track_record.total_predictions}</div>
          </div>
          <div>
            <span className="text-gray-500">Confidence</span>
            <div className="font-semibold">{(expert.confidence_calibration * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Risk Profile */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">Risk Profile</span>
          <Badge className={cn("text-xs", getRiskBadgeColor(expert.risk_tolerance))}>
            {expert.risk_tolerance}
          </Badge>
        </div>

        {/* Specializations */}
        <div className="space-y-1">
          <span className="text-sm text-gray-600 dark:text-gray-400">Specializations</span>
          <div className="flex flex-wrap gap-1">
            {expert.primary_expertise.slice(0, 2).map((spec, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {spec}
              </Badge>
            ))}
            {expert.primary_expertise.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{expert.primary_expertise.length - 2}
              </Badge>
            )}
          </div>
        </div>

        {/* View Details Button */}
        <Button 
          variant="ghost" 
          size="sm" 
          className="w-full mt-2 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(expert.id);
          }}
        >
          <Eye className="w-4 h-4 mr-2" />
          View Details
        </Button>
      </CardContent>
    </motion.div>
  );
};

const CouncilSpotlight: React.FC<{ 
  councilMembers: ExpertPersonality[], 
  onViewAll: () => void 
}> = ({ councilMembers, onViewAll }) => {
  return (
    <Card className="col-span-full lg:col-span-2 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Crown className="w-5 h-5 text-gold-500" />
          <span>AI Council - Top 5 Experts</span>
          <Badge variant="secondary">Current Session</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="gap-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 sm:flex sm:flex-nowrap sm:overflow-x-auto experts-scroll sm:pb-4 sm:-mx-4 sm:px-4">
          {councilMembers.map((member, index) => (
            <motion.div
              key={member.id}
              className="text-center p-3 rounded-lg bg-white dark:bg-gray-800 border relative expert-card-mobile"
              whileHover={{ scale: 1.05 }}
            >
              <div className="relative mb-2">
                <ExpertAvatar
                  expert={member}
                  size="md"
                  showCouncilBadge={false}
                  className="mx-auto"
                />
                <div className={cn(
                  "absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-white font-bold text-xs",
                  index === 0 ? "bg-gold-500" :
                  index === 1 ? "bg-silver-500" :
                  index === 2 ? "bg-bronze-500" : "bg-purple-500"
                )}>
                  #{index + 1}
                </div>
              </div>
              <h4 className="font-semibold text-sm truncate">{member.name}</h4>
              <p className="text-xs text-gray-500 truncate">{member.archetype}</p>
              <div className="text-lg font-bold text-green-600 mt-1">
                {(member.accuracy_metrics.overall * 100).toFixed(1)}%
              </div>
            </motion.div>
          ))}
        </div>
        
        <Button 
          onClick={onViewAll} 
          className="w-full mt-4"
          variant="outline"
        >
          View Council Details
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </CardContent>
    </Card>
  );
};

const CompetitionMetrics: React.FC<{ experts: ExpertPersonality[] }> = ({ experts }) => {
  const totalPredictions = experts.reduce((sum, expert) => sum + expert.track_record.total_predictions, 0);
  const averageAccuracy = experts.reduce((sum, expert) => sum + expert.accuracy_metrics.overall, 0) / experts.length;
  const topPerformer = experts[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5" />
          <span>Competition Metrics</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">{experts.length}</div>
            <div className="text-sm text-gray-500">Active Experts</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">{totalPredictions.toLocaleString()}</div>
            <div className="text-sm text-gray-500">Total Predictions</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">{(averageAccuracy * 100).toFixed(1)}%</div>
            <div className="text-sm text-gray-500">Avg Accuracy</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gold-500">5</div>
            <div className="text-sm text-gray-500">Council Seats</div>
          </div>
        </div>

        <div className="pt-4 border-t">
          <h4 className="font-semibold mb-2 flex items-center space-x-2">
            <Trophy className="w-4 h-4 text-gold-500" />
            <span>Current Leader</span>
          </h4>
          <div className="flex items-center space-x-3">
            <div className="relative">
              <ExpertAvatar
                expert={topPerformer}
                size="md"
                showCouncilBadge={true}
                showHoverEffect={false}
              />
              <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-gold-500 flex items-center justify-center text-white font-bold text-xs">
                #1
              </div>
            </div>
            <div>
              <div className="font-semibold">{topPerformer.name}</div>
              <div className="text-sm text-gray-500">{topPerformer.archetype}</div>
              <div className="text-lg font-bold text-green-600">
                {(topPerformer.accuracy_metrics.overall * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const ExpertShowcaseDashboard: React.FC<ExpertShowcaseDashboardProps> = ({
  onExpertSelect,
  onCouncilView,
  className
}) => {
  const [filter, setFilter] = useState<'all' | 'council' | 'challengers'>('all');
  const [sortBy, setSortBy] = useState<'rank' | 'accuracy' | 'recent'>('rank');
  const [councilMembers, setCouncilMembers] = useState<ExpertPersonality[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize council members
    const members = getCouncilMembers();
    setCouncilMembers(members);
  }, []);

  const sortedExperts = useMemo(() => {
    let experts = [...EXPERT_PERSONALITIES];
    
    // Apply filter
    if (filter === 'council') {
      experts = experts.filter(expert => expert.council_position !== undefined);
    } else if (filter === 'challengers') {
      experts = experts.filter(expert => expert.council_position === undefined);
    }
    
    // Apply sort
    experts.sort((a, b) => {
      switch (sortBy) {
        case 'accuracy':
          return b.accuracy_metrics.overall - a.accuracy_metrics.overall;
        case 'recent':
          return b.accuracy_metrics.recent_performance - a.accuracy_metrics.recent_performance;
        case 'rank':
        default:
          // Council members first by position, then others by accuracy
          if (a.council_position && b.council_position) {
            return a.council_position - b.council_position;
          }
          if (a.council_position && !b.council_position) return -1;
          if (!a.council_position && b.council_position) return 1;
          return b.accuracy_metrics.overall - a.accuracy_metrics.overall;
      }
    });
    
    return experts;
  }, [filter, sortBy]);

  const handleExpertSelect = (expertId: string) => {
    onExpertSelect?.(expertId);
  };

  const handleCouncilRefresh = async () => {
    setLoading(true);
    try {
      // Simulate council selection process
      await new Promise(resolve => setTimeout(resolve, 1000));
      const selection = performCouncilSelection();
      setCouncilMembers(selection.council_members);
    } catch (error) {
      console.error('Error refreshing council:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Expert Competition Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            15 AI experts competing for the top 5 council positions
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="all">All Experts</option>
            <option value="council">Council Members</option>
            <option value="challengers">Challengers</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="rank">Sort by Rank</option>
            <option value="accuracy">Sort by Accuracy</option>
            <option value="recent">Sort by Recent</option>
          </select>

          <Button 
            variant="outline" 
            onClick={handleCouncilRefresh}
            disabled={loading}
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Activity className="w-4 h-4" />
              </motion.div>
            ) : (
              <Activity className="w-4 h-4" />
            )}
            Refresh Council
          </Button>
        </div>
      </div>

      {/* Council Spotlight & Competition Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <CouncilSpotlight 
          councilMembers={councilMembers}
          onViewAll={() => onCouncilView?.()}
        />
        <CompetitionMetrics experts={EXPERT_PERSONALITIES} />
      </div>

      {/* Expert Grid */}
      <div className="gap-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 sm:flex sm:flex-nowrap sm:overflow-x-auto experts-scroll sm:pb-4 sm:-mx-4 sm:px-4">
        <AnimatePresence>
          {sortedExperts.map((expert, index) => (
            <motion.div
              key={expert.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <ExpertCard
                expert={expert}
                rank={expert.council_position || (index + 1)}
                isCouncilMember={expert.council_position !== undefined}
                onSelect={handleExpertSelect}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {sortedExperts.length === 0 && (
        <div className="text-center py-12">
          <Filter className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No experts found
          </h3>
          <p className="text-gray-500">
            Try adjusting your filters to see more experts.
          </p>
        </div>
      )}
    </div>
  );
};

export default ExpertShowcaseDashboard;