import React from 'react';
import { motion } from 'framer-motion';
import { 
  Target, Trophy, BarChart3, Zap, 
  TrendingUp, Star, Award, Users
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Avatar, AvatarFallback } from '../ui/avatar';
import type { CouncilMember, PredictionCategoryGroup } from '../../types/aiCouncil';

interface ExpertSpecializationRadarProps {
  expert: CouncilMember;
}

interface CategoryProficiency {
  category: PredictionCategoryGroup;
  proficiencyScore: number; // 0-100
  sampleSize: number;
  rank: number; // Rank among all experts in this category
  trend: 'improving' | 'stable' | 'declining';
}

const ExpertSpecializationRadar: React.FC<ExpertSpecializationRadarProps> = ({
  expert
}) => {
  // Mock proficiency data
  const proficiencies: CategoryProficiency[] = [
    {
      category: 'game_outcome',
      proficiencyScore: Math.random() * 30 + 70, // 70-100
      sampleSize: Math.floor(Math.random() * 50) + 20,
      rank: Math.floor(Math.random() * 10) + 1,
      trend: 'improving'
    },
    {
      category: 'betting_markets',
      proficiencyScore: Math.random() * 40 + 50, // 50-90
      sampleSize: Math.floor(Math.random() * 40) + 15,
      rank: Math.floor(Math.random() * 15) + 1,
      trend: 'stable'
    },
    {
      category: 'live_scenarios',
      proficiencyScore: Math.random() * 50 + 40, // 40-90
      sampleSize: Math.floor(Math.random() * 30) + 10,
      rank: Math.floor(Math.random() * 20) + 1,
      trend: 'declining'
    },
    {
      category: 'player_props',
      proficiencyScore: Math.random() * 35 + 60, // 60-95
      sampleSize: Math.floor(Math.random() * 45) + 25,
      rank: Math.floor(Math.random() * 8) + 1,
      trend: 'improving'
    },
    {
      category: 'situational_analysis',
      proficiencyScore: Math.random() * 45 + 45, // 45-90
      sampleSize: Math.floor(Math.random() * 35) + 12,
      rank: Math.floor(Math.random() * 12) + 1,
      trend: 'stable'
    }
  ];

  const getCategoryIcon = (category: PredictionCategoryGroup) => {
    const icons = {
      game_outcome: Trophy,
      betting_markets: BarChart3,
      live_scenarios: Zap,
      player_props: Users,
      situational_analysis: TrendingUp
    };
    return icons[category] || Target;
  };

  const getCategoryDisplayName = (category: PredictionCategoryGroup) => {
    const names = {
      game_outcome: 'Game Outcome',
      betting_markets: 'Betting Markets',
      live_scenarios: 'Live Scenarios',
      player_props: 'Player Props',
      situational_analysis: 'Situational Analysis'
    };
    return names[category] || category.replace('_', ' ');
  };

  const getProficiencyColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 65) return 'text-blue-600 bg-blue-100';
    if (score >= 50) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return 'text-green-600 bg-green-100';
      case 'declining': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRankColor = (rank: number) => {
    if (rank <= 3) return 'text-yellow-600 bg-yellow-100';
    if (rank <= 8) return 'text-blue-600 bg-blue-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="h-3 w-3 text-green-500" />;
      case 'declining': return <TrendingUp className="h-3 w-3 text-red-500 rotate-180" />;
      default: return <TrendingUp className="h-3 w-3 text-gray-500" />;
    }
  };

  // Calculate overall versatility score
  const versatilityScore = proficiencies.reduce((sum, p) => sum + p.proficiencyScore, 0) / proficiencies.length;
  
  // Identify strongest and weakest categories
  const sortedByScore = [...proficiencies].sort((a, b) => b.proficiencyScore - a.proficiencyScore);
  const strongest = sortedByScore[0];
  const weakest = sortedByScore[sortedByScore.length - 1];

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12">
            <AvatarFallback className="bg-purple-100 text-purple-600">
              {expert.expertName.split(' ').map(n => n[0]).join('')}
            </AvatarFallback>
          </Avatar>
          <div>
            <CardTitle className="text-lg">{expert.expertName}</CardTitle>
            <p className="text-sm text-gray-600">Specialization Analysis</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Metrics */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-purple-50 rounded-lg">
            <Star className="h-5 w-5 text-purple-500 mx-auto mb-1" />
            <div className="text-lg font-bold text-purple-700">
              {versatilityScore.toFixed(1)}
            </div>
            <div className="text-xs text-purple-600">Versatility</div>
          </div>
          
          <div className="p-3 bg-yellow-50 rounded-lg">
            <Award className="h-5 w-5 text-yellow-500 mx-auto mb-1" />
            <div className="text-lg font-bold text-yellow-700">
              #{strongest.rank}
            </div>
            <div className="text-xs text-yellow-600">Best Rank</div>
          </div>
          
          <div className="p-3 bg-blue-50 rounded-lg">
            <Target className="h-5 w-5 text-blue-500 mx-auto mb-1" />
            <div className="text-lg font-bold text-blue-700">
              {proficiencies.reduce((sum, p) => sum + p.sampleSize, 0)}
            </div>
            <div className="text-xs text-blue-600">Total Predictions</div>
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-white">
            Category Performance
          </h4>
          
          {proficiencies.map((proficiency, index) => {
            const IconComponent = getCategoryIcon(proficiency.category);
            
            return (
              <motion.div
                key={proficiency.category}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gray-100">
                      <IconComponent className="h-4 w-4 text-gray-600" />
                    </div>
                    <div>
                      <h5 className="font-semibold text-sm">
                        {getCategoryDisplayName(proficiency.category)}
                      </h5>
                      <p className="text-xs text-gray-600">
                        {proficiency.sampleSize} predictions
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge className={getRankColor(proficiency.rank)}>
                      #{proficiency.rank}
                    </Badge>
                    <Badge className={getTrendColor(proficiency.trend)}>
                      {getTrendIcon(proficiency.trend)}
                      {proficiency.trend}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Proficiency Score</span>
                    <span className="font-semibold">
                      {proficiency.proficiencyScore.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={proficiency.proficiencyScore} className="h-2" />
                  
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Sample: {proficiency.sampleSize} games</span>
                    <span>Rank: #{proficiency.rank} overall</span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Trophy className="h-4 w-4 text-green-600" />
              <span className="font-semibold text-green-800">Strongest Area</span>
            </div>
            <div className="text-sm text-green-700">
              <div className="font-medium">
                {getCategoryDisplayName(strongest.category)}
              </div>
              <div className="text-xs">
                {strongest.proficiencyScore.toFixed(1)}% proficiency • Rank #{strongest.rank}
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-red-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="h-4 w-4 text-red-600" />
              <span className="font-semibold text-red-800">Growth Area</span>
            </div>
            <div className="text-sm text-red-700">
              <div className="font-medium">
                {getCategoryDisplayName(weakest.category)}
              </div>
              <div className="text-xs">
                {weakest.proficiencyScore.toFixed(1)}% proficiency • Rank #{weakest.rank}
              </div>
            </div>
          </div>
        </div>

        {/* Specialization Summary */}
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h5 className="font-semibold text-gray-900 dark:text-white mb-2">
            Specialization Summary
          </h5>
          <div className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
            <div>
              • <strong>Primary Strength:</strong> {getCategoryDisplayName(strongest.category)} 
              with {strongest.proficiencyScore.toFixed(1)}% proficiency
            </div>
            <div>
              • <strong>Versatility Score:</strong> {versatilityScore.toFixed(1)}% across all categories
            </div>
            <div>
              • <strong>Best Ranking:</strong> #{strongest.rank} in {getCategoryDisplayName(strongest.category)}
            </div>
            <div>
              • <strong>Improvement Areas:</strong> {
                proficiencies
                  .filter(p => p.proficiencyScore < 65)
                  .map(p => getCategoryDisplayName(p.category))
                  .join(', ') || 'None identified'
              }
            </div>
          </div>
        </div>

        {/* Performance Trends */}
        <div>
          <h5 className="font-semibold text-gray-900 dark:text-white mb-3">
            Performance Trends
          </h5>
          <div className="flex flex-wrap gap-2">
            {proficiencies.map((proficiency) => (
              <Badge
                key={proficiency.category}
                className={`${getTrendColor(proficiency.trend)} text-xs`}
              >
                {getTrendIcon(proficiency.trend)}
                {getCategoryDisplayName(proficiency.category)}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ExpertSpecializationRadar;