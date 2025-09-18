/**
 * Game Detail Dialog - Shows expert predictions grid for a specific game
 * Part of the Expert Observatory admin dashboard
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  AlertTriangle,
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  Eye
} from 'lucide-react';

interface GamePrediction {
  game_id: string;
  date: string;
  home_team: string;
  away_team: string;
  consensus_winner: string;
  consensus_confidence: number;
  accuracy_rate: number;
  outlier_count: number;
  status: 'completed' | 'in_progress' | 'upcoming';
  expert_predictions: ExpertPrediction[];
}

interface ExpertPrediction {
  expert_id: string;
  expert_name: string;
  personality: string;
  brand_color: string;
  avatar_emoji: string;
  prediction: {
    winner: string;
    home_score: number;
    away_score: number;
    confidence: number;
  };
  reasoning_chain: ReasoningStep[];
  is_outlier: boolean;
  accuracy?: number; // Only available for completed games
}

interface ReasoningStep {
  factor: string;
  value: string;
  weight: number;
  confidence: number;
  source: string;
}

interface GameDetailDialogProps {
  game: GamePrediction;
  onClose: () => void;
  onExpertClick: (expert: ExpertPrediction) => void;
}

const GameDetailDialog: React.FC<GameDetailDialogProps> = ({
  game,
  onClose,
  onExpertClick
}) => {
  const [selectedView, setSelectedView] = useState<'grid' | 'consensus'>('grid');

  // Group experts by prediction for consensus view
  const predictionGroups = React.useMemo(() => {
    const groups: Record<string, ExpertPrediction[]> = {};
    game.expert_predictions.forEach(expert => {
      const key = expert.prediction.winner;
      if (!groups[key]) groups[key] = [];
      groups[key].push(expert);
    });
    return groups;
  }, [game.expert_predictions]);

  // Calculate statistics
  const stats = React.useMemo(() => {
    const predictions = game.expert_predictions;
    const avgConfidence = predictions.reduce((sum, p) => sum + p.prediction.confidence, 0) / predictions.length;
    const outliers = predictions.filter(p => p.is_outlier);
    const homeWinners = predictions.filter(p => p.prediction.winner === game.home_team);
    const awayWinners = predictions.filter(p => p.prediction.winner === game.away_team);

    return {
      avgConfidence,
      outlierCount: outliers.length,
      homeSupport: homeWinners.length,
      awaySupport: awayWinners.length,
      strongestConfidence: Math.max(...predictions.map(p => p.prediction.confidence)),
      weakestConfidence: Math.min(...predictions.map(p => p.prediction.confidence))
    };
  }, [game]);

  const getPerformanceBadge = (expert: ExpertPrediction) => {
    if (game.status !== 'completed' || expert.accuracy === undefined) {
      return null;
    }

    if (expert.accuracy >= 0.8) {
      return <Badge className="bg-green-100 text-green-800 text-xs">Correct</Badge>;
    } else if (expert.accuracy >= 0.5) {
      return <Badge className="bg-yellow-100 text-yellow-800 text-xs">Partial</Badge>;
    } else {
      return <Badge className="bg-red-100 text-red-800 text-xs">Incorrect</Badge>;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="text-2xl">
              {game.away_team} @ {game.home_team}
            </span>
            <Badge variant="outline">
              {new Date(game.date).toLocaleDateString()}
            </Badge>
            {game.status === 'completed' && (
              <Badge className={stats.avgConfidence > 0.7 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                {(game.accuracy_rate * 100).toFixed(0)}% Accurate
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            Expert predictions and reasoning analysis for this game
          </DialogDescription>
        </DialogHeader>

        {/* Game Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.homeSupport}</div>
              <div className="text-sm text-muted-foreground">{game.home_team} Picks</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-red-600">{stats.awaySupport}</div>
              <div className="text-sm text-muted-foreground">{game.away_team} Picks</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-green-600">
                {(stats.avgConfidence * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-muted-foreground">Avg Confidence</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.outlierCount}</div>
              <div className="text-sm text-muted-foreground">Outliers</div>
            </CardContent>
          </Card>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 mb-4">
          <Button
            variant={selectedView === 'grid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedView('grid')}
          >
            Expert Grid
          </Button>
          <Button
            variant={selectedView === 'consensus' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedView('consensus')}
          >
            Consensus View
          </Button>
        </div>

        {/* Expert Grid View */}
        {selectedView === 'grid' && (
          <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
            {game.expert_predictions.map((expert) => (
              <TooltipProvider key={expert.expert_id}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Card
                      className={`cursor-pointer transition-all duration-200 hover:shadow-lg border-2 ${
                        expert.is_outlier ? 'border-orange-200 bg-orange-50' : 'border-gray-200'
                      }`}
                      style={{
                        borderColor: expert.is_outlier ? '#fed7aa' : expert.brand_color + '40'
                      }}
                      onClick={() => onExpertClick(expert)}
                    >
                      <CardContent className="p-4">
                        {/* Expert Header */}
                        <div className="flex items-center gap-2 mb-3">
                          <span
                            className="text-2xl"
                            role="img"
                            aria-label={expert.expert_name}
                          >
                            {expert.avatar_emoji}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-sm truncate">
                              {expert.expert_name}
                            </div>
                            <div className="text-xs text-muted-foreground capitalize">
                              {expert.personality}
                            </div>
                          </div>
                          {expert.is_outlier && (
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                          )}
                        </div>

                        {/* Prediction */}
                        <div className="space-y-2">
                          <div className="text-center">
                            <Badge
                              style={{ backgroundColor: expert.brand_color + '20', color: expert.brand_color }}
                              className="text-xs font-medium"
                            >
                              {expert.prediction.winner}
                            </Badge>
                          </div>

                          <div className="text-center text-sm">
                            <span className="font-mono">
                              {expert.prediction.home_score}-{expert.prediction.away_score}
                            </span>
                          </div>

                          <div className="text-center">
                            <span className={`text-sm font-medium ${getConfidenceColor(expert.prediction.confidence)}`}>
                              {(expert.prediction.confidence * 100).toFixed(0)}%
                            </span>
                          </div>

                          {/* Performance Badge (for completed games) */}
                          <div className="text-center">
                            {getPerformanceBadge(expert)}
                          </div>

                          {/* Reasoning Preview */}
                          <div className="text-xs text-muted-foreground text-center">
                            {expert.reasoning_chain.length > 0 && (
                              <div className="truncate">
                                Top: {expert.reasoning_chain[0].factor}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Click Indicator */}
                        <div className="mt-2 flex justify-center">
                          <Eye className="h-3 w-3 text-muted-foreground" />
                        </div>
                      </CardContent>
                    </Card>
                  </TooltipTrigger>
                  <TooltipContent>
                    <div className="space-y-1">
                      <div className="font-medium">{expert.expert_name}</div>
                      <div className="text-sm">Confidence: {(expert.prediction.confidence * 100).toFixed(0)}%</div>
                      <div className="text-sm">Reasoning factors: {expert.reasoning_chain.length}</div>
                      {expert.is_outlier && (
                        <div className="text-sm text-orange-600">⚠ Outlier prediction</div>
                      )}
                      <div className="text-xs text-muted-foreground">Click for detailed analysis</div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ))}
          </div>
        )}

        {/* Consensus View */}
        {selectedView === 'consensus' && (
          <div className="space-y-4">
            {Object.entries(predictionGroups).map(([winner, experts]) => (
              <Card key={winner} className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Badge className="text-lg px-3 py-1">{winner}</Badge>
                    <span className="text-muted-foreground">
                      {experts.length} expert{experts.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Avg Confidence: {(experts.reduce((sum, e) => sum + e.prediction.confidence, 0) / experts.length * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {experts.map((expert) => (
                    <Button
                      key={expert.expert_id}
                      variant="outline"
                      size="sm"
                      className="h-8"
                      onClick={() => onExpertClick(expert)}
                    >
                      <span className="mr-1">{expert.avatar_emoji}</span>
                      {expert.expert_name}
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({(expert.prediction.confidence * 100).toFixed(0)}%)
                      </span>
                    </Button>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default GameDetailDialog;