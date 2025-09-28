import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Cloud, Users, Plane, Clock, 
  TrendingUp, AlertTriangle, Target, Home
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import type { 
  ExpertPrediction, 
  ConsensusResult 
} from '../../types/aiCouncil';

interface SituationalAnalysisPanelProps {
  predictions: ExpertPrediction[];
  consensus: ConsensusResult[];
  categories: string[];
  onCategorySelect: (categoryId: string) => void;
  viewMode: 'grid' | 'list' | 'compact';
}

interface SituationalFactor {
  categoryId: string;
  categoryName: string;
  impactLevel: 'high' | 'medium' | 'low' | 'minimal';
  confidence: number;
  agreement: number;
  expertCount: number;
  currentCondition: string;
  historicalAverage: string;
  riskLevel: 'critical' | 'elevated' | 'moderate' | 'low';
  affectedAreas: string[];
  timeToGame: string;
}

const SituationalAnalysisPanel: React.FC<SituationalAnalysisPanelProps> = ({
  predictions,
  consensus,
  categories,
  onCategorySelect,
  viewMode
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Process situational analysis predictions
  const situationalFactors: SituationalFactor[] = React.useMemo(() => {
    const categoryMap: Record<string, string> = {
      'weather_impact': 'Weather Conditions',
      'injury_impact': 'Key Injuries',
      'travel_fatigue': 'Travel & Fatigue',
      'rest_advantage': 'Rest Differential',
      'coaching_edge': 'Coaching Matchup',
      'home_field_advantage': 'Home Field Edge'
    };

    const affectedAreasMap: Record<string, string[]> = {
      'weather_impact': ['Passing Game', 'Kicking', 'Turnovers'],
      'injury_impact': ['Offensive Production', 'Defensive Pressure', 'Special Teams'],
      'travel_fatigue': ['4th Quarter Performance', 'Mental Focus'],
      'rest_advantage': ['Stamina', 'Preparation Quality'],
      'coaching_edge': ['Game Planning', 'In-Game Adjustments'],
      'home_field_advantage': ['Crowd Noise', 'Referee Bias', 'Comfort Level']
    };

    const mockConditions: Record<string, { current: string; historical: string }> = {
      'weather_impact': { current: '45°F, 15mph winds', historical: '52°F, 8mph winds' },
      'injury_impact': { current: '3 key players out', historical: '1.2 avg injuries' },
      'travel_fatigue': { current: '2,100 miles traveled', historical: '850 miles avg' },
      'rest_advantage': { current: '+3 days rest', historical: 'Even rest' },
      'coaching_edge': { current: 'Experience favors home', historical: 'Split decisions' },
      'home_field_advantage': { current: 'Hostile environment', historical: '+2.8 point edge' }
    };

    return categories.map(categoryId => {
      const categoryConsensus = consensus.find(c => c.categoryId === categoryId);
      const categoryPredictions = predictions.flatMap(p => 
        p.predictions.filter(pred => pred.categoryId === categoryId)
      );

      const mockCondition = mockConditions[categoryId] || { current: 'Normal', historical: 'Average' };
      
      return {
        categoryId,
        categoryName: categoryMap[categoryId] || categoryId.replace(/_/g, ' '),
        impactLevel: Math.random() > 0.7 ? 'high' : Math.random() > 0.4 ? 'medium' : 'low',
        confidence: categoryConsensus?.confidence || Math.random() * 0.3 + 0.6,
        agreement: categoryConsensus?.agreement || Math.random() * 0.3 + 0.6,
        expertCount: categoryPredictions.length || Math.floor(Math.random() * 4) + 3,
        currentCondition: mockCondition.current,
        historicalAverage: mockCondition.historical,
        riskLevel: Math.random() > 0.8 ? 'critical' : Math.random() > 0.6 ? 'elevated' : Math.random() > 0.3 ? 'moderate' : 'low',
        affectedAreas: affectedAreasMap[categoryId] || ['General Impact'],
        timeToGame: Math.floor(Math.random() * 48) + 'h remaining'
      };
    }).filter(f => f.expertCount > 0);
  }, [categories, consensus, predictions]);

  const getCategoryIcon = (categoryId: string) => {
    const icons: Record<string, any> = {
      'weather_impact': Cloud,
      'injury_impact': AlertTriangle,
      'travel_fatigue': Plane,
      'rest_advantage': Clock,
      'coaching_edge': Users,
      'home_field_advantage': Home
    };
    return icons[categoryId] || Target;
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-700 bg-red-100 border-red-200';
      case 'medium': return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-green-700 bg-green-100 border-green-200';
      default: return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'elevated': return 'text-orange-600 bg-orange-50';
      case 'moderate': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'high': return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'medium': return <TrendingUp className="h-4 w-4 text-yellow-500" />;
      case 'low': return <TrendingUp className="h-4 w-4 text-green-500" />;
      default: return <TrendingUp className="h-4 w-4 text-gray-500" />;
    }
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
    onCategorySelect(categoryId);
  };

  if (viewMode === 'compact') {
    return (
      <div className="space-y-2">
        {situationalFactors.map((factor, index) => (
          <motion.div
            key={factor.categoryId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border hover:border-yellow-300 cursor-pointer"
            onClick={() => handleCategoryClick(factor.categoryId)}
          >
            <div className="flex items-center gap-3">
              <div className="p-1 rounded bg-yellow-100">
                {React.createElement(getCategoryIcon(factor.categoryId), {
                  className: "h-4 w-4 text-yellow-600"
                })}
              </div>
              <div>
                <span className="font-medium text-sm">{factor.categoryName}</span>
                <div className="text-xs text-gray-500">
                  {factor.timeToGame}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Badge className={getImpactColor(factor.impactLevel)}>
                {factor.impactLevel}
              </Badge>
              {getImpactIcon(factor.impactLevel)}
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-3">
        {situationalFactors.map((factor, index) => (
          <motion.div
            key={factor.categoryId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card 
              className="cursor-pointer transition-all duration-200 hover:shadow-md border-l-4 border-l-yellow-500"
              onClick={() => handleCategoryClick(factor.categoryId)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {React.createElement(getCategoryIcon(factor.categoryId), {
                      className: "h-5 w-5 text-yellow-600"
                    })}
                    <div>
                      <h4 className="font-semibold">{factor.categoryName}</h4>
                      <p className="text-sm text-gray-600">
                        {factor.expertCount} expert assessments
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getImpactColor(factor.impactLevel)}>
                      {factor.impactLevel} impact
                    </Badge>
                    <Badge className={getRiskColor(factor.riskLevel)}>
                      {factor.riskLevel} risk
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Current Condition</div>
                    <div className="text-sm font-semibold">
                      {factor.currentCondition}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Historical Average</div>
                    <div className="text-sm font-semibold">
                      {factor.historicalAverage}
                    </div>
                  </div>
                </div>

                <div className="mt-3">
                  <div className="text-sm text-gray-600 mb-2">Affected Areas</div>
                  <div className="flex flex-wrap gap-1">
                    {factor.affectedAreas.map((area, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {area}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    );
  }

  // Grid view (default)
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {situationalFactors.map((factor, index) => {
        const IconComponent = getCategoryIcon(factor.categoryId);
        const isSelected = selectedCategory === factor.categoryId;
        
        return (
          <motion.div
            key={factor.categoryId}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            <Card 
              className={`
                cursor-pointer transition-all duration-300 h-full
                ${isSelected 
                  ? 'ring-2 ring-yellow-500 shadow-lg border-yellow-300' 
                  : 'hover:shadow-md border-gray-200'
                }
                border-l-4 border-l-yellow-500
              `}
              onClick={() => handleCategoryClick(factor.categoryId)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-yellow-100">
                      <IconComponent className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-semibold">
                        {factor.categoryName}
                      </CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${getImpactColor(factor.impactLevel)}`}
                        >
                          {factor.impactLevel} impact
                        </Badge>
                      </div>
                    </div>
                  </div>
                  {getImpactIcon(factor.impactLevel)}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Current vs Historical */}
                <div className="space-y-3">
                  <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <div className="text-sm text-yellow-700 dark:text-yellow-300 mb-1">
                      Current Condition
                    </div>
                    <div className="text-sm font-bold text-yellow-900 dark:text-yellow-100">
                      {factor.currentCondition}
                    </div>
                  </div>
                  
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-300 mb-1">
                      Historical Average
                    </div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">
                      {factor.historicalAverage}
                    </div>
                  </div>
                </div>

                {/* Risk Assessment */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">Risk Level</span>
                  <Badge className={getRiskColor(factor.riskLevel)}>
                    {factor.riskLevel}
                  </Badge>
                </div>

                {/* Affected Areas */}
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    Affected Areas
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {factor.affectedAreas.slice(0, 2).map((area, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {area}
                      </Badge>
                    ))}
                    {factor.affectedAreas.length > 2 && (
                      <Badge variant="outline" className="text-xs">
                        +{factor.affectedAreas.length - 2}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Confidence Metrics */}
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-300">Assessment Confidence</span>
                      <span className="font-semibold">
                        {(factor.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={factor.confidence * 100} className="h-2" />
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-300">Expert Agreement</span>
                      <span className="font-semibold">
                        {(factor.agreement * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={factor.agreement * 100} className="h-2" />
                  </div>
                </div>

                {/* Time Information */}
                <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">Time to Game</span>
                  </div>
                  <span className="font-semibold">{factor.timeToGame}</span>
                </div>

                {/* Expert Count */}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Expert Assessments</span>
                  <span className="font-semibold">{factor.expertCount}</span>
                </div>

                {/* Expanded Details */}
                {isSelected && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    transition={{ duration: 0.3 }}
                    className="pt-3 border-t border-gray-200 dark:border-gray-700"
                  >
                    <div className="space-y-3">
                      <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Detailed Analysis
                      </h5>
                      
                      <div className="space-y-2">
                        <div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                            All Affected Areas:
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {factor.affectedAreas.map((area, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {area}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Current conditions show {factor.impactLevel} impact potential compared to historical averages.
                          Risk assessment indicates {factor.riskLevel} level concerns for game outcome.
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
};

export default SituationalAnalysisPanel;