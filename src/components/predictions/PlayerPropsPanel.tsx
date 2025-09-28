import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  User, Target, TrendingUp, BarChart, 
  Award, Users, AlertTriangle, Activity
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Avatar, AvatarFallback } from '../ui/avatar';
import type { 
  ExpertPrediction, 
  ConsensusResult 
} from '../../types/aiCouncil';

interface PlayerPropsPanelProps {
  predictions: ExpertPrediction[];
  consensus: ConsensusResult[];
  categories: string[];
  onCategorySelect: (categoryId: string) => void;
  viewMode: 'grid' | 'list' | 'compact';
}

interface PlayerProp {
  categoryId: string;
  categoryName: string;
  playerName: string;
  position: string;
  team: string;
  consensusValue: number;
  line: number;
  confidence: number;
  agreement: number;
  expertCount: number;
  overPercentage: number;
  injuryStatus: 'healthy' | 'questionable' | 'doubtful';
  recentForm: 'hot' | 'warm' | 'cold';
  weatherImpact: 'none' | 'low' | 'medium' | 'high';
}

const PlayerPropsPanel: React.FC<PlayerPropsPanelProps> = ({
  predictions,
  consensus,
  categories,
  onCategorySelect,
  viewMode
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [filterBy, setFilterBy] = useState<'all' | 'qb' | 'rb' | 'wr' | 'defense'>('all');

  // Mock player data
  const players = [
    { name: 'Josh Allen', position: 'QB', team: 'BUF' },
    { name: 'Stefon Diggs', position: 'WR', team: 'BUF' },
    { name: 'James Cook', position: 'RB', team: 'BUF' },
    { name: 'Tua Tagovailoa', position: 'QB', team: 'MIA' },
    { name: 'Tyreek Hill', position: 'WR', team: 'MIA' },
    { name: 'Raheem Mostert', position: 'RB', team: 'MIA' }
  ];

  // Process player props predictions
  const playerProps: PlayerProp[] = React.useMemo(() => {
    const categoryMap: Record<string, string> = {
      'passing_yards': 'Passing Yards',
      'passing_touchdowns': 'Passing TDs',
      'rushing_yards': 'Rushing Yards',
      'rushing_touchdowns': 'Rushing TDs',
      'receiving_yards': 'Receiving Yards',
      'receiving_touchdowns': 'Receiving TDs',
      'field_goals_made': 'Field Goals',
      'extra_points': 'Extra Points',
      'defensive_sacks': 'Sacks',
      'interceptions': 'Interceptions'
    };

    return categories.map((categoryId, index) => {
      const categoryConsensus = consensus.find(c => c.categoryId === categoryId);
      const categoryPredictions = predictions.flatMap(p => 
        p.predictions.filter(pred => pred.categoryId === categoryId)
      );

      const player = players[index % players.length];
      const mockLine = Math.random() * 200 + 50; // 50-250 range
      const mockConsensus = mockLine + (Math.random() - 0.5) * 40; // ±20 from line

      return {
        categoryId,
        categoryName: categoryMap[categoryId] || categoryId.replace(/_/g, ' '),
        playerName: player.name,
        position: player.position,
        team: player.team,
        consensusValue: categoryConsensus?.consensusValue || mockConsensus,
        line: mockLine,
        confidence: categoryConsensus?.confidence || Math.random() * 0.3 + 0.6,
        agreement: categoryConsensus?.agreement || Math.random() * 0.3 + 0.6,
        expertCount: categoryPredictions.length || Math.floor(Math.random() * 4) + 3,
        overPercentage: Math.random() * 100,
        injuryStatus: Math.random() > 0.8 ? 'questionable' : Math.random() > 0.9 ? 'doubtful' : 'healthy',
        recentForm: Math.random() > 0.6 ? 'hot' : Math.random() > 0.3 ? 'warm' : 'cold',
        weatherImpact: Math.random() > 0.7 ? 'medium' : Math.random() > 0.9 ? 'high' : 'none'
      };
    }).filter(p => p.expertCount > 0);
  }, [categories, consensus, predictions]);

  const getCategoryIcon = (categoryId: string) => {
    const icons: Record<string, any> = {
      'passing_yards': Target,
      'passing_touchdowns': Award,
      'rushing_yards': TrendingUp,
      'rushing_touchdowns': Award,
      'receiving_yards': BarChart,
      'receiving_touchdowns': Award,
      'field_goals_made': Target,
      'extra_points': Target,
      'defensive_sacks': Activity,
      'interceptions': Activity
    };
    return icons[categoryId] || User;
  };

  const getPositionColor = (position: string) => {
    switch (position) {
      case 'QB': return 'text-blue-600 bg-blue-100';
      case 'RB': return 'text-green-600 bg-green-100';
      case 'WR': return 'text-purple-600 bg-purple-100';
      case 'TE': return 'text-orange-600 bg-orange-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getInjuryStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'questionable': return 'text-yellow-600 bg-yellow-100';
      case 'doubtful': return 'text-red-600 bg-red-100';
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

  const getOverUnderRecommendation = (consensusValue: number, line: number) => {
    const diff = consensusValue - line;
    if (Math.abs(diff) < 2) return { recommendation: 'neutral', color: 'text-gray-600' };
    return diff > 0 
      ? { recommendation: 'over', color: 'text-green-600' }
      : { recommendation: 'under', color: 'text-red-600' };
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
    onCategorySelect(categoryId);
  };

  // Filter props by position
  const filteredProps = React.useMemo(() => {
    if (filterBy === 'all') return playerProps;
    if (filterBy === 'defense') return playerProps.filter(p => 
      p.categoryId.includes('sacks') || p.categoryId.includes('interceptions')
    );
    return playerProps.filter(p => p.position.toLowerCase() === filterBy);
  }, [playerProps, filterBy]);

  if (viewMode === 'compact') {
    return (
      <div className="space-y-3">
        {/* Filter Controls */}
        <div className="flex gap-2 mb-4">
          {['all', 'qb', 'rb', 'wr', 'defense'].map(filter => (
            <button
              key={filter}
              onClick={() => setFilterBy(filter as any)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filterBy === filter 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {filter.toUpperCase()}
            </button>
          ))}
        </div>

        {filteredProps.map((prop, index) => (
          <motion.div
            key={prop.categoryId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border hover:border-purple-300 cursor-pointer"
            onClick={() => handleCategoryClick(prop.categoryId)}
          >
            <div className="flex items-center gap-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback className={getPositionColor(prop.position)}>
                  {prop.position}
                </AvatarFallback>
              </Avatar>
              <div>
                <div className="font-medium text-sm">{prop.playerName}</div>
                <div className="text-xs text-gray-500">
                  {prop.categoryName} • {prop.team}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="font-semibold text-sm">
                  {prop.consensusValue.toFixed(1)}
                </div>
                <div className="text-xs text-gray-500">
                  Line: {prop.line.toFixed(1)}
                </div>
              </div>
              <Badge className={getOverUnderRecommendation(prop.consensusValue, prop.line).color}>
                {getOverUnderRecommendation(prop.consensusValue, prop.line).recommendation}
              </Badge>
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-3">
        {/* Filter Controls */}
        <div className="flex gap-2 mb-4">
          {['all', 'qb', 'rb', 'wr', 'defense'].map(filter => (
            <button
              key={filter}
              onClick={() => setFilterBy(filter as any)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filterBy === filter 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {filter.toUpperCase()}
            </button>
          ))}
        </div>

        {filteredProps.map((prop, index) => (
          <motion.div
            key={prop.categoryId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card 
              className="cursor-pointer transition-all duration-200 hover:shadow-md border-l-4 border-l-purple-500"
              onClick={() => handleCategoryClick(prop.categoryId)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback className={getPositionColor(prop.position)}>
                        {prop.position}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h4 className="font-semibold">{prop.playerName}</h4>
                      <p className="text-sm text-gray-600">
                        {prop.categoryName} • {prop.team}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getInjuryStatusColor(prop.injuryStatus)}>
                      {prop.injuryStatus}
                    </Badge>
                    <Badge className={getFormColor(prop.recentForm)}>
                      {prop.recentForm}
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Consensus</div>
                    <div className="text-lg font-bold">
                      {prop.consensusValue.toFixed(1)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Line</div>
                    <div className="text-lg font-bold">
                      {prop.line.toFixed(1)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Over %</div>
                    <div className="text-lg font-bold">
                      {prop.overPercentage.toFixed(0)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Recommendation</div>
                    <Badge className={getOverUnderRecommendation(prop.consensusValue, prop.line).color}>
                      {getOverUnderRecommendation(prop.consensusValue, prop.line).recommendation}
                    </Badge>
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
    <div className="space-y-4">
      {/* Filter Controls */}
      <div className="flex gap-2">
        {['all', 'qb', 'rb', 'wr', 'defense'].map(filter => (
          <button
            key={filter}
            onClick={() => setFilterBy(filter as any)}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              filterBy === filter 
                ? 'bg-purple-100 text-purple-700' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {filter.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredProps.map((prop, index) => {
          const IconComponent = getCategoryIcon(prop.categoryId);
          const isSelected = selectedCategory === prop.categoryId;
          const recommendation = getOverUnderRecommendation(prop.consensusValue, prop.line);
          
          return (
            <motion.div
              key={prop.categoryId}
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
                    ? 'ring-2 ring-purple-500 shadow-lg border-purple-300' 
                    : 'hover:shadow-md border-gray-200'
                  }
                  border-l-4 border-l-purple-500
                `}
                onClick={() => handleCategoryClick(prop.categoryId)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-12 w-12">
                        <AvatarFallback className={getPositionColor(prop.position)}>
                          {prop.position}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <CardTitle className="text-base font-semibold">
                          {prop.playerName}
                        </CardTitle>
                        <p className="text-sm text-gray-600">
                          {prop.categoryName} • {prop.team}
                        </p>
                      </div>
                    </div>
                    <div className="p-2 rounded-lg bg-purple-100">
                      <IconComponent className="h-5 w-5 text-purple-600" />
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Prediction vs Line */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <div className="text-sm text-purple-700 dark:text-purple-300 mb-1">
                        Consensus
                      </div>
                      <div className="text-xl font-bold text-purple-900 dark:text-purple-100">
                        {prop.consensusValue.toFixed(1)}
                      </div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-300 mb-1">
                        Line
                      </div>
                      <div className="text-xl font-bold text-gray-900 dark:text-white">
                        {prop.line.toFixed(1)}
                      </div>
                    </div>
                  </div>

                  {/* Recommendation */}
                  <div className="text-center">
                    <Badge 
                      className={`text-lg py-2 px-4 ${recommendation.color} ${
                        recommendation.recommendation === 'over' ? 'bg-green-100' :
                        recommendation.recommendation === 'under' ? 'bg-red-100' : 'bg-gray-100'
                      }`}
                    >
                      {recommendation.recommendation.toUpperCase()}
                    </Badge>
                  </div>

                  {/* Player Status */}
                  <div className="flex justify-between items-center">
                    <div className="text-center">
                      <div className="text-xs text-gray-600 mb-1">Injury</div>
                      <Badge className={getInjuryStatusColor(prop.injuryStatus)}>
                        {prop.injuryStatus}
                      </Badge>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 mb-1">Form</div>
                      <Badge className={getFormColor(prop.recentForm)}>
                        {prop.recentForm}
                      </Badge>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 mb-1">Weather</div>
                      <Badge variant="outline">
                        {prop.weatherImpact}
                      </Badge>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-300">Confidence</span>
                        <span className="font-semibold">
                          {(prop.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={prop.confidence * 100} className="h-2" />
                    </div>

                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-300">Over Percentage</span>
                        <span className="font-semibold">
                          {prop.overPercentage.toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={prop.overPercentage} className="h-2" />
                    </div>
                  </div>

                  {/* Expert Count */}
                  <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-300">Experts</span>
                    </div>
                    <span className="font-semibold">{prop.expertCount}</span>
                  </div>

                  {/* Expanded Details */}
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ duration: 0.3 }}
                      className="pt-3 border-t border-gray-200 dark:border-gray-700"
                    >
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Analysis Summary
                        </h5>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Expert consensus suggests {recommendation.recommendation} the line of {prop.line.toFixed(1)}.
                          Player is currently {prop.recentForm} and {prop.injuryStatus}.
                          {prop.weatherImpact !== 'none' && ` Weather may have ${prop.weatherImpact} impact.`}
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
    </div>
  );
};

export default PlayerPropsPanel;