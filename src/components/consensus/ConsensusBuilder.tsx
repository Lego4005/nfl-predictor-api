/**
 * Real-time Consensus Building Visualization
 * Shows how AI Council members build consensus on predictions
 */

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Crown, 
  Users, 
  TrendingUp, 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  BarChart3,
  Zap,
  Clock,
  Target,
  Eye
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

import { ExpertPersonality, getCouncilMembers } from '@/data/expertPersonalities';
import { PredictionCategoryConfig, PREDICTION_CATEGORIES } from '@/data/predictionCategories';

export interface ConsensusPrediction {
  id: string;
  category: string;
  categoryConfig: PredictionCategoryConfig;
  gameId: string;
  question: string;
  options: ConsensusPredictionOption[];
  consensus: {
    strength: 'unanimous' | 'strong' | 'moderate' | 'weak' | 'divided';
    percentage: number;
    winningOption: string;
    confidence: number;
  };
  voting: {
    totalVotes: number;
    votesSubmitted: number;
    timeRemaining: number; // seconds
    isComplete: boolean;
  };
  expertVotes: ExpertVote[];
  lastUpdated: string;
}

export interface ConsensusPredictionOption {
  id: string;
  label: string;
  description?: string;
  votes: number;
  weightedVotes: number; // Votes weighted by expert performance
  percentage: number;
  confidence: number;
  supporters: string[]; // Expert IDs
}

export interface ExpertVote {
  expertId: string;
  expertName: string;
  optionId: string;
  confidence: number;
  weight: number; // Voting weight based on performance
  reasoning?: string;
  timestamp: string;
  isCouncilMember: boolean;
}

interface ConsensusBuilderProps {
  gameId: string;
  predictions?: ConsensusPrediction[];
  onPredictionSelect?: (predictionId: string) => void;
  showVotingProcess?: boolean;
  className?: string;
}

const ConsensusBuilder: React.FC<ConsensusBuilderProps> = ({
  gameId,
  predictions: externalPredictions,
  onPredictionSelect,
  showVotingProcess = true,
  className
}) => {
  const [predictions, setPredictions] = useState<ConsensusPrediction[]>([]);
  const [selectedPrediction, setSelectedPrediction] = useState<string | null>(null);
  const [councilMembers] = useState(getCouncilMembers());
  const [autoUpdate, setAutoUpdate] = useState(true);

  // Mock predictions data
  const mockPredictions: ConsensusPrediction[] = useMemo(() => [
    {
      id: 'game-winner-kc-buf',
      category: 'game_winner',
      categoryConfig: PREDICTION_CATEGORIES.find(c => c.id === 'game_winner')!,
      gameId,
      question: 'Which team will win the game?',
      options: [
        {
          id: 'kc-win',
          label: 'Kansas City Chiefs',
          votes: 4,
          weightedVotes: 0.82,
          percentage: 82,
          confidence: 0.76,
          supporters: ['the-analyst', 'the-veteran', 'the-quant', 'the-scout']
        },
        {
          id: 'buf-win',
          label: 'Buffalo Bills',
          votes: 1,
          weightedVotes: 0.18,
          percentage: 18,
          confidence: 0.68,
          supporters: ['the-weather-expert']
        }
      ],
      consensus: {
        strength: 'strong',
        percentage: 82,
        winningOption: 'kc-win',
        confidence: 0.76
      },
      voting: {
        totalVotes: 5,
        votesSubmitted: 5,
        timeRemaining: 0,
        isComplete: true
      },
      expertVotes: [
        {
          expertId: 'the-analyst',
          expertName: 'The Analyst',
          optionId: 'kc-win',
          confidence: 0.84,
          weight: 0.24,
          reasoning: 'Statistical advantage in key metrics',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-veteran',
          expertName: 'The Veteran',
          optionId: 'kc-win',
          confidence: 0.72,
          weight: 0.22,
          reasoning: 'Home field advantage and recent form',
          timestamp: new Date(Date.now() - 180000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-quant',
          expertName: 'The Quant',
          optionId: 'kc-win',
          confidence: 0.78,
          weight: 0.20,
          reasoning: 'Model projects 62% win probability',
          timestamp: new Date(Date.now() - 90000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-scout',
          expertName: 'The Scout',
          optionId: 'kc-win',
          confidence: 0.69,
          weight: 0.18,
          reasoning: 'Key player matchup advantages',
          timestamp: new Date(Date.now() - 240000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-weather-expert',
          expertName: 'The Weather Expert',
          optionId: 'buf-win',
          confidence: 0.68,
          weight: 0.16,
          reasoning: 'Weather conditions favor Bills style',
          timestamp: new Date(Date.now() - 60000).toISOString(),
          isCouncilMember: true
        }
      ],
      lastUpdated: new Date().toISOString()
    },
    {
      id: 'point-spread-kc-buf',
      category: 'point_spread',
      categoryConfig: PREDICTION_CATEGORIES.find(c => c.id === 'point_spread')!,
      gameId,
      question: 'Will Kansas City cover the -3.5 spread?',
      options: [
        {
          id: 'kc-cover',
          label: 'Chiefs Cover (-3.5)',
          votes: 3,
          weightedVotes: 0.64,
          percentage: 64,
          confidence: 0.71,
          supporters: ['the-analyst', 'the-quant', 'the-scout']
        },
        {
          id: 'buf-cover',
          label: 'Bills Cover (+3.5)',
          votes: 2,
          weightedVotes: 0.36,
          percentage: 36,
          confidence: 0.65,
          supporters: ['the-veteran', 'the-weather-expert']
        }
      ],
      consensus: {
        strength: 'moderate',
        percentage: 64,
        winningOption: 'kc-cover',
        confidence: 0.71
      },
      voting: {
        totalVotes: 5,
        votesSubmitted: 5,
        timeRemaining: 0,
        isComplete: true
      },
      expertVotes: [
        {
          expertId: 'the-analyst',
          expertName: 'The Analyst',
          optionId: 'kc-cover',
          confidence: 0.76,
          weight: 0.24,
          reasoning: 'Historical performance vs spread',
          timestamp: new Date(Date.now() - 150000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-veteran',
          expertName: 'The Veteran',
          optionId: 'buf-cover',
          confidence: 0.68,
          weight: 0.22,
          reasoning: 'Divisional games tend to be closer',
          timestamp: new Date(Date.now() - 200000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-quant',
          expertName: 'The Quant',
          optionId: 'kc-cover',
          confidence: 0.73,
          weight: 0.20,
          reasoning: 'Expected margin: 4.2 points',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-scout',
          expertName: 'The Scout',
          optionId: 'kc-cover',
          confidence: 0.65,
          weight: 0.18,
          reasoning: 'Offensive line advantage',
          timestamp: new Date(Date.now() - 180000).toISOString(),
          isCouncilMember: true
        },
        {
          expertId: 'the-weather-expert',
          expertName: 'The Weather Expert',
          optionId: 'buf-cover',
          confidence: 0.62,
          weight: 0.16,
          reasoning: 'Wind affects passing game',
          timestamp: new Date(Date.now() - 90000).toISOString(),
          isCouncilMember: true
        }
      ],
      lastUpdated: new Date().toISOString()
    }
  ], [gameId]);

  useEffect(() => {
    setPredictions(externalPredictions || mockPredictions);
  }, [externalPredictions, mockPredictions]);

  const getConsensusColor = (strength: string) => {
    switch (strength) {
      case 'unanimous': return 'text-green-600 bg-green-50 border-green-200';
      case 'strong': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'moderate': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'weak': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'divided': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getConsensusIcon = (strength: string) => {
    switch (strength) {
      case 'unanimous': return <CheckCircle className=\"w-4 h-4\" />;
      case 'strong': return <Target className=\"w-4 h-4\" />;
      case 'moderate': return <Activity className=\"w-4 h-4\" />;
      case 'weak': return <AlertTriangle className=\"w-4 h-4\" />;
      case 'divided': return <XCircle className=\"w-4 h-4\" />;
      default: return <Activity className=\"w-4 h-4\" />;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date().getTime();
    const time = new Date(timestamp).getTime();
    const diff = now - time;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes === 1) return '1 minute ago';
    if (minutes < 60) return `${minutes} minutes ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours === 1) return '1 hour ago';
    return `${hours} hours ago`;
  };

  const VotingProgress: React.FC<{ prediction: ConsensusPrediction }> = ({ prediction }) => (
    <div className=\"space-y-3\">
      <div className=\"flex items-center justify-between\">
        <span className=\"text-sm font-medium\">Voting Progress</span>
        <div className=\"flex items-center space-x-2\">
          {prediction.voting.isComplete ? (
            <Badge variant=\"secondary\" className=\"bg-green-100 text-green-700\">
              <CheckCircle className=\"w-3 h-3 mr-1\" />
              Complete
            </Badge>
          ) : (
            <Badge variant=\"secondary\" className=\"bg-yellow-100 text-yellow-700\">
              <Clock className=\"w-3 h-3 mr-1\" />
              In Progress
            </Badge>
          )}
        </div>
      </div>
      
      <div className=\"space-y-2\">
        <div className=\"flex justify-between text-sm text-gray-600\">
          <span>Votes: {prediction.voting.votesSubmitted}/{prediction.voting.totalVotes}</span>
          <span>Council Members</span>
        </div>
        <Progress 
          value={(prediction.voting.votesSubmitted / prediction.voting.totalVotes) * 100} 
          className=\"h-2\"
        />
      </div>
    </div>
  );

  const ExpertVotesList: React.FC<{ prediction: ConsensusPrediction }> = ({ prediction }) => (
    <div className=\"space-y-3\">
      <h4 className=\"font-medium flex items-center space-x-2\">
        <Users className=\"w-4 h-4\" />
        <span>Expert Votes</span>
      </h4>
      
      <div className=\"space-y-2\">
        {prediction.expertVotes
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .map((vote) => {
            const option = prediction.options.find(o => o.id === vote.optionId);
            return (
              <motion.div
                key={`${vote.expertId}-${vote.timestamp}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className=\"flex items-center justify-between p-3 border rounded-lg bg-gray-50 dark:bg-gray-800\"
              >
                <div className=\"flex items-center space-x-3\">
                  {vote.isCouncilMember && (
                    <Crown className=\"w-4 h-4 text-gold-500\" />
                  )}
                  <div>
                    <div className=\"font-medium text-sm\">{vote.expertName}</div>
                    <div className=\"text-xs text-gray-500\">Weight: {(vote.weight * 100).toFixed(1)}%</div>
                  </div>
                </div>
                
                <div className=\"text-right\">
                  <div className=\"font-medium text-sm\">{option?.label}</div>
                  <div className=\"text-xs text-gray-500\">
                    {(vote.confidence * 100).toFixed(0)}% confidence
                  </div>
                </div>
                
                <div className=\"text-xs text-gray-400\">
                  {formatTimeAgo(vote.timestamp)}
                </div>
              </motion.div>
            );
          })}
      </div>
    </div>
  );

  const PredictionCard: React.FC<{ prediction: ConsensusPrediction }> = ({ prediction }) => {
    const isSelected = selectedPrediction === prediction.id;
    
    return (
      <motion.div
        layout
        className={cn(
          \"cursor-pointer transition-all duration-200\",
          isSelected && \"ring-2 ring-blue-500\"
        )}
        onClick={() => {
          setSelectedPrediction(isSelected ? null : prediction.id);
          onPredictionSelect?.(prediction.id);
        }}
      >
        <Card className=\"hover:shadow-md\">
          <CardHeader className=\"pb-3\">
            <div className=\"flex items-center justify-between\">
              <CardTitle className=\"text-lg\">{prediction.question}</CardTitle>
              <div className=\"flex items-center space-x-2\">
                <Badge variant=\"outline\">
                  {prediction.categoryConfig.name}
                </Badge>
                {autoUpdate && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: \"linear\" }}
                  >
                    <Activity className=\"w-4 h-4 text-blue-500\" />
                  </motion.div>
                )}
              </div>
            </div>
            
            <div className={cn(
              \"inline-flex items-center space-x-2 px-3 py-1 rounded-full border text-sm\",
              getConsensusColor(prediction.consensus.strength)
            )}>
              {getConsensusIcon(prediction.consensus.strength)}
              <span className=\"capitalize\">{prediction.consensus.strength} Consensus</span>
              <span>({prediction.consensus.percentage}%)</span>
            </div>
          </CardHeader>
          
          <CardContent className=\"space-y-4\">
            {/* Options with voting results */}
            <div className=\"space-y-2\">
              {prediction.options.map((option) => (
                <div key={option.id} className=\"space-y-1\">
                  <div className=\"flex items-center justify-between\">
                    <span className=\"font-medium\">{option.label}</span>
                    <div className=\"flex items-center space-x-2\">
                      <span className=\"text-sm font-bold\">{option.percentage}%</span>
                      <Badge variant=\"secondary\" className=\"text-xs\">
                        {option.votes} votes
                      </Badge>
                    </div>
                  </div>
                  
                  <div className=\"relative\">
                    <div className=\"w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2\">
                      <motion.div
                        className={cn(
                          \"h-2 rounded-full transition-all duration-500\",
                          option.id === prediction.consensus.winningOption
                            ? \"bg-blue-500\"
                            : \"bg-gray-400\"
                        )}
                        initial={{ width: 0 }}
                        animate={{ width: `${option.percentage}%` }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                      />
                    </div>
                  </div>
                  
                  <div className=\"flex items-center justify-between text-xs text-gray-500\">
                    <span>Confidence: {(option.confidence * 100).toFixed(0)}%</span>
                    <span>Weight: {option.weightedVotes.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
            
            {showVotingProcess && (
              <VotingProgress prediction={prediction} />
            )}
            
            <AnimatePresence>
              {isSelected && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className=\"border-t pt-4\"
                >
                  <ExpertVotesList prediction={prediction} />
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  return (
    <div className={cn(\"space-y-6\", className)}>
      {/* Header */}
      <div className=\"flex items-center justify-between\">
        <div>
          <h2 className=\"text-2xl font-bold flex items-center space-x-2\">
            <BarChart3 className=\"w-6 h-6\" />
            <span>AI Council Consensus</span>
          </h2>
          <p className=\"text-gray-600 dark:text-gray-400\">
            Real-time voting and consensus building by expert council
          </p>
        </div>
        
        <div className=\"flex items-center space-x-2\">
          <Button
            variant={autoUpdate ? \"default\" : \"outline\"}
            size=\"sm\"
            onClick={() => setAutoUpdate(!autoUpdate)}
          >
            {autoUpdate ? (
              <>
                <Zap className=\"w-4 h-4 mr-2\" />
                Live Updates
              </>
            ) : (
              <>
                <Eye className=\"w-4 h-4 mr-2\" />
                Manual Updates
              </>
            )}
          </Button>
        </div>
      </div>
      
      {/* Council Overview */}
      <Card>
        <CardHeader>
          <CardTitle className=\"flex items-center space-x-2\">
            <Crown className=\"w-5 h-5 text-gold-500\" />
            <span>Council Voting Power</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3\">
            {councilMembers.map((member) => (
              <div key={member.id} className=\"text-center p-3 border rounded-lg\">
                <div className=\"font-semibold text-sm\">{member.name}</div>
                <div className=\"text-lg font-bold text-blue-600\">
                  {(member.council_weight! * 100).toFixed(1)}%
                </div>
                <div className=\"text-xs text-gray-500\">voting weight</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Predictions */}
      <div className=\"space-y-4\">
        <AnimatePresence>
          {predictions.map((prediction) => (
            <motion.div
              key={prediction.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <PredictionCard prediction={prediction} />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      
      {predictions.length === 0 && (
        <div className=\"text-center py-12\">
          <BarChart3 className=\"w-12 h-12 text-gray-400 mx-auto mb-4\" />
          <h3 className=\"text-lg font-medium text-gray-900 dark:text-white mb-2\">
            No predictions available
          </h3>
          <p className=\"text-gray-500\">
            The AI Council is currently building consensus on predictions.
          </p>
        </div>
      )}
    </div>
  );
};

export default ConsensusBuilder;"