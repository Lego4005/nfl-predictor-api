/**
 * Expert Reasoning Dialog - Deep dive into expert's chain-of-thought analysis
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import {
  Brain,
  Target,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Database,
  Clock,
  Zap
} from 'lucide-react';

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
  accuracy?: number;
  internal_monologue?: string;
  confidence_calibration?: number;
  past_similar_accuracy?: number;
}

interface ReasoningStep {
  factor: string;
  value: string;
  weight: number;
  confidence: number;
  source: string;
  category?: 'statistical' | 'situational' | 'historical' | 'learned' | 'intuitive';
  impact?: 'positive' | 'negative' | 'neutral';
}

interface ExpertReasoningDialogProps {
  expert: ExpertPrediction;
  onClose: () => void;
}

const ExpertReasoningDialog: React.FC<ExpertReasoningDialogProps> = ({
  expert,
  onClose
}) => {
  const [selectedTab, setSelectedTab] = useState<'reasoning' | 'analysis' | 'history'>('reasoning');

  // Process reasoning data for visualization
  const reasoningData = React.useMemo(() => {
    return expert.reasoning_chain.map((step, index) => ({
      ...step,
      index: index + 1,
      weightPercent: step.weight * 100,
      confidencePercent: step.confidence * 100,
      combinedScore: step.weight * step.confidence
    })).sort((a, b) => b.combinedScore - a.combinedScore);
  }, [expert.reasoning_chain]);

  // Categorize reasoning factors
  const categoryData = React.useMemo(() => {
    const categories: Record<string, { count: number; totalWeight: number; color: string }> = {
      statistical: { count: 0, totalWeight: 0, color: '#3B82F6' },
      situational: { count: 0, totalWeight: 0, color: '#10B981' },
      historical: { count: 0, totalWeight: 0, color: '#F59E0B' },
      learned: { count: 0, totalWeight: 0, color: '#8B5CF6' },
      intuitive: { count: 0, totalWeight: 0, color: '#EF4444' }
    };

    expert.reasoning_chain.forEach(step => {
      const category = step.category || 'statistical';
      categories[category].count++;
      categories[category].totalWeight += step.weight;
    });

    return Object.entries(categories)
      .filter(([_, data]) => data.count > 0)
      .map(([name, data]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: data.totalWeight,
        count: data.count,
        color: data.color
      }));
  }, [expert.reasoning_chain]);

  // Factor impact analysis
  const impactAnalysis = React.useMemo(() => {
    const positive = expert.reasoning_chain.filter(step => step.impact === 'positive');
    const negative = expert.reasoning_chain.filter(step => step.impact === 'negative');
    const neutral = expert.reasoning_chain.filter(step => !step.impact || step.impact === 'neutral');

    return {
      positive: {
        count: positive.length,
        totalWeight: positive.reduce((sum, step) => sum + step.weight, 0)
      },
      negative: {
        count: negative.length,
        totalWeight: negative.reduce((sum, step) => sum + step.weight, 0)
      },
      neutral: {
        count: neutral.length,
        totalWeight: neutral.reduce((sum, step) => sum + step.weight, 0)
      }
    };
  }, [expert.reasoning_chain]);

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'season_stats': return <Database className="h-4 w-4" />;
      case 'historical_pattern': return <Clock className="h-4 w-4" />;
      case 'learned_principle': return <Brain className="h-4 w-4" />;
      case 'real_time_data': return <Zap className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  const getImpactIcon = (impact?: string) => {
    switch (impact) {
      case 'positive': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'negative': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Target className="h-4 w-4 text-gray-500" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="text-2xl">{expert.avatar_emoji}</span>
            <span>{expert.expert_name}</span>
            <Badge
              style={{ backgroundColor: expert.brand_color + '20', color: expert.brand_color }}
              className="capitalize"
            >
              {expert.personality}
            </Badge>
            {expert.is_outlier && (
              <Badge variant="outline" className="text-orange-600">
                <AlertTriangle className="h-3 w-3 mr-1" />
                Outlier
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            Detailed reasoning analysis and chain-of-thought breakdown
          </DialogDescription>
        </DialogHeader>

        {/* Expert Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold" style={{ color: expert.brand_color }}>
                {expert.prediction.winner}
              </div>
              <div className="text-sm text-muted-foreground">Prediction</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {(expert.prediction.confidence * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">
                {expert.reasoning_chain.length}
              </div>
              <div className="text-sm text-muted-foreground">Factors</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-green-600">
                {expert.accuracy !== undefined ? (expert.accuracy * 100).toFixed(0) + '%' : 'TBD'}
              </div>
              <div className="text-sm text-muted-foreground">Accuracy</div>
            </CardContent>
          </Card>
        </div>

        <Tabs value={selectedTab} onValueChange={(value) => setSelectedTab(value as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="reasoning">
              <Brain className="h-4 w-4 mr-2" />
              Reasoning Chain
            </TabsTrigger>
            <TabsTrigger value="analysis">
              <Target className="h-4 w-4 mr-2" />
              Factor Analysis
            </TabsTrigger>
            <TabsTrigger value="history">
              <Clock className="h-4 w-4 mr-2" />
              Performance History
            </TabsTrigger>
          </TabsList>

          {/* Reasoning Chain Tab */}
          <TabsContent value="reasoning" className="space-y-4">
            {/* Internal Monologue */}
            {expert.internal_monologue && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Internal Monologue
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground italic bg-gray-50 p-4 rounded-lg">
                    "{expert.internal_monologue}"
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Reasoning Steps */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Reasoning Factors</CardTitle>
                <DialogDescription>
                  Ordered by combined weight and confidence score
                </DialogDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {reasoningData.map((step, index) => (
                  <div
                    key={index}
                    className="border rounded-lg p-4 space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm font-medium">
                            #{step.index}
                          </span>
                          {getSourceIcon(step.source)}
                          {getImpactIcon(step.impact)}
                        </div>
                        <div>
                          <h4 className="font-medium">{step.factor}</h4>
                          <p className="text-sm text-muted-foreground">{step.value}</p>
                        </div>
                      </div>
                      <Badge
                        className={`${getConfidenceColor(step.confidence)} border-0`}
                      >
                        {(step.confidence * 100).toFixed(0)}% confident
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Weight</span>
                          <span className="font-medium">{step.weightPercent.toFixed(1)}%</span>
                        </div>
                        <Progress value={step.weightPercent} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Combined Score</span>
                          <span className="font-medium">{(step.combinedScore * 100).toFixed(1)}</span>
                        </div>
                        <Progress value={step.combinedScore * 100} className="h-2" />
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Source: {step.source.replace('_', ' ')}</span>
                      {step.category && (
                        <span>Category: {step.category}</span>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Factor Analysis Tab */}
          <TabsContent value="analysis" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Category Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Factor Categories</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {categoryData.map((category) => (
                      <div key={category.name} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">{category.name}</span>
                          <Badge variant="outline">
                            {category.count} factor{category.count !== 1 ? 's' : ''}
                          </Badge>
                        </div>
                        <Progress
                          value={(category.value / Math.max(...categoryData.map(c => c.value))) * 100}
                          className="h-2"
                        />
                        <div className="text-xs text-muted-foreground">
                          Total weight: {(category.value * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Impact Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>Impact Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-green-600" />
                        <span className="text-green-800 font-medium">Positive Factors</span>
                      </div>
                      <div className="text-right">
                        <div className="text-green-800 font-bold">{impactAnalysis.positive.count}</div>
                        <div className="text-xs text-green-600">
                          {(impactAnalysis.positive.totalWeight * 100).toFixed(1)}% weight
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <TrendingDown className="h-4 w-4 text-red-600" />
                        <span className="text-red-800 font-medium">Negative Factors</span>
                      </div>
                      <div className="text-right">
                        <div className="text-red-800 font-bold">{impactAnalysis.negative.count}</div>
                        <div className="text-xs text-red-600">
                          {(impactAnalysis.negative.totalWeight * 100).toFixed(1)}% weight
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-gray-600" />
                        <span className="text-gray-800 font-medium">Neutral Factors</span>
                      </div>
                      <div className="text-right">
                        <div className="text-gray-800 font-bold">{impactAnalysis.neutral.count}</div>
                        <div className="text-xs text-gray-600">
                          {(impactAnalysis.neutral.totalWeight * 100).toFixed(1)}% weight
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Factor Weight Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Factor Weight Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={reasoningData.slice(0, 8)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="factor"
                        angle={-45}
                        textAnchor="end"
                        height={100}
                        fontSize={12}
                      />
                      <YAxis />
                      <Tooltip
                        formatter={(value: any, name: string) => [
                          `${(value * 100).toFixed(1)}%`,
                          name === 'weight' ? 'Weight' : 'Confidence'
                        ]}
                      />
                      <Bar dataKey="weight" fill={expert.brand_color} name="weight" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance History Tab */}
          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Expert Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">Confidence Calibration</div>
                    <div className="text-2xl font-bold">
                      {expert.confidence_calibration ? (expert.confidence_calibration * 100).toFixed(0) + '%' : 'N/A'}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      How well-calibrated this expert's confidence is
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">Similar Games Accuracy</div>
                    <div className="text-2xl font-bold">
                      {expert.past_similar_accuracy ? (expert.past_similar_accuracy * 100).toFixed(0) + '%' : 'N/A'}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Performance on similar game situations
                    </div>
                  </div>
                </div>

                {/* Placeholder for historical performance chart */}
                <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center text-muted-foreground">
                  Historical performance chart would go here
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

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

export default ExpertReasoningDialog;