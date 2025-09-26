import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertCircle, TrendingUp, TrendingDown, Users, Trophy, Target } from 'lucide-react'

interface CouncilMember {
  expert_id: string
  name: string
  weight: number
  rank: number
  accuracy: number
  recent_trend: string
}

interface ConsensusData {
  game_id: string
  council_members: CouncilMember[]
  consensus_predictions: Record<string, {
    value: any
    confidence: number
    agreement: number
    method: string
  }>
  explanations: {
    overall_summary: string
    expert_spotlight: string
    key_factors: string
  }
  consensus_metadata: {
    total_categories_predicted: number
    average_confidence: number
    average_agreement: number
    prediction_timestamp: string
  }
}

interface AICouncilDashboardProps {
  gameId?: string
  onRefresh?: () => void
}

const AICouncilDashboard: React.FC<AICouncilDashboardProps> = ({ 
  gameId = 'current',
  onRefresh 
}) => {
  const [consensusData, setConsensusData] = useState<ConsensusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchConsensusData()
  }, [gameId])

  const fetchConsensusData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Mock API call - replace with actual API
      const response = await fetch(`/api/ai-council/consensus/${gameId}`)
      if (!response.ok) throw new Error('Failed to fetch consensus data')
      
      const data = await response.json()
      setConsensusData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      // Set mock data for development
      setConsensusData(getMockConsensusData())
    } finally {
      setLoading(false)
    }
  }

  const getMockConsensusData = (): ConsensusData => ({
    game_id: 'chiefs_vs_bills_2024',
    council_members: [
      { expert_id: 'analyst', name: 'The Analyst', weight: 0.24, rank: 1, accuracy: 0.724, recent_trend: 'improving' },
      { expert_id: 'sharp', name: 'The Sharp', weight: 0.22, rank: 2, accuracy: 0.698, recent_trend: 'stable' },
      { expert_id: 'quant', name: 'The Quant', weight: 0.20, rank: 3, accuracy: 0.672, recent_trend: 'improving' },
      { expert_id: 'scholar', name: 'The Scholar', weight: 0.18, rank: 4, accuracy: 0.658, recent_trend: 'stable' },
      { expert_id: 'hunter', name: 'The Hunter', weight: 0.16, rank: 5, accuracy: 0.641, recent_trend: 'declining' }
    ],
    consensus_predictions: {
      winner_prediction: { value: 'Kansas City Chiefs', confidence: 0.78, agreement: 0.85, method: 'weighted_voting' },
      exact_score: { value: '28-24', confidence: 0.62, agreement: 0.71, method: 'weighted_average' },
      spread: { value: 'Chiefs -3.5', confidence: 0.74, agreement: 0.82, method: 'weighted_voting' },
      total: { value: 'Over 52.5', confidence: 0.68, agreement: 0.76, method: 'weighted_voting' }
    },
    explanations: {
      overall_summary: 'The AI Council strongly favors the Kansas City Chiefs with 78% confidence. The consensus reflects strong home field advantage and superior offensive capabilities.',
      expert_spotlight: 'The Analyst leads the council with 24% voting weight due to exceptional recent performance. The Sharp provides critical market insights.',
      key_factors: 'Key factors: Strong home field advantage, weather conditions favorable, no significant injuries reported.'
    },
    consensus_metadata: {
      total_categories_predicted: 12,
      average_confidence: 0.705,
      average_agreement: 0.785,
      prediction_timestamp: new Date().toISOString()
    }
  })

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'declining': return <TrendingDown className="w-4 h-4 text-red-500" />
      default: return <Target className="w-4 h-4 text-gray-500" />
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getAgreementColor = (agreement: number) => {
    if (agreement >= 0.8) return 'bg-green-500'
    if (agreement >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading AI Council consensus...</span>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span>Error loading consensus data: {error}</span>
          </div>
          <Button onClick={fetchConsensusData} className="mt-4" variant="outline">
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!consensusData) return null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
            <Users className="w-8 h-8 text-blue-600" />
            <span>AI Council Dashboard</span>
          </h1>
          <p className="text-gray-600 mt-1">
            Democratic AI consensus for game {consensusData.game_id}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={onRefresh} variant="outline">
            Refresh
          </Button>
          <Button onClick={fetchConsensusData}>
            Update Consensus
          </Button>
        </div>
      </div>

      {/* Council Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Trophy className="w-5 h-5 text-gold-500" />
              <div>
                <p className="text-sm text-gray-600">Council Size</p>
                <p className="text-2xl font-bold">{consensusData.council_members.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600">Avg Confidence</p>
                <p className="text-2xl font-bold">
                  {(consensusData.consensus_metadata.average_confidence * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">Avg Agreement</p>
                <p className="text-2xl font-bold">
                  {(consensusData.consensus_metadata.average_agreement * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm text-gray-600">Categories</p>
                <p className="text-2xl font-bold">
                  {consensusData.consensus_metadata.total_categories_predicted}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Consensus Predictions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="w-5 h-5" />
            <span>Consensus Predictions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(consensusData.consensus_predictions).map(([category, prediction]) => (
              <div key={category} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold capitalize">
                    {category.replace('_', ' ')}
                  </h3>
                  <Badge className={getConfidenceColor(prediction.confidence)}>
                    {(prediction.confidence * 100).toFixed(0)}% confident
                  </Badge>
                </div>
                
                <div className="mb-3">
                  <p className="text-lg font-bold text-gray-900">
                    {prediction.value}
                  </p>
                  <p className="text-sm text-gray-600">
                    Method: {prediction.method.replace('_', ' ')}
                  </p>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Council Agreement</span>
                    <span className="font-medium">
                      {(prediction.agreement * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getAgreementColor(prediction.agreement)}`}
                      style={{ width: `${prediction.agreement * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Council Members */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5" />
            <span>Council Members</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {consensusData.council_members.map((member, index) => (
              <div 
                key={member.expert_id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-blue-600">
                      #{member.rank}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-semibold">{member.name}</h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      {getTrendIcon(member.recent_trend)}
                      <span>Accuracy: {(member.accuracy * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm text-gray-600">Voting Weight</div>
                  <div className="font-bold text-lg">
                    {(member.weight * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Explanations */}
      <Card>
        <CardHeader>
          <CardTitle>AI Council Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Overall Summary</h3>
              <p className="text-gray-700">{consensusData.explanations.overall_summary}</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Expert Spotlight</h3>
              <p className="text-gray-700">{consensusData.explanations.expert_spotlight}</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Key Factors</h3>
              <p className="text-gray-700">{consensusData.explanations.key_factors}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AICouncilDashboard