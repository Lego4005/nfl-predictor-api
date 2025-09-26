import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Crown, 
  Star, 
  Activity,
  BarChart3,
  Eye,
  Calendar
} from 'lucide-react'

interface CouncilMember {
  expert_id: string
  name: string
  rank: number
  overall_accuracy: number
  recent_accuracy: number
  voting_weight: number
  council_appearances: number
  recent_trend: 'improving' | 'stable' | 'declining'
  specialization_strength: Record<string, number>
  confidence_calibration: number
  total_predictions: number
  streak: {
    current: number
    type: 'winning' | 'losing'
  }
  personality_type: string
  last_updated: string
}

interface CouncilMembersPanelProps {
  members?: CouncilMember[]
  onMemberSelect?: (memberId: string) => void
  showDetailed?: boolean
}

const CouncilMembersPanel: React.FC<CouncilMembersPanelProps> = ({
  members,
  onMemberSelect,
  showDetailed = true
}) => {
  const [councilMembers, setCouncilMembers] = useState<CouncilMember[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMember, setSelectedMember] = useState<string | null>(null)

  useEffect(() => {
    if (members) {
      setCouncilMembers(members)
      setLoading(false)
    } else {
      fetchCouncilMembers()
    }
  }, [members])

  const fetchCouncilMembers = async () => {
    try {
      setLoading(true)
      
      // Mock API call - replace with actual API
      const response = await fetch('/api/ai-council/members')
      if (!response.ok) throw new Error('Failed to fetch council members')
      
      const data = await response.json()
      setCouncilMembers(data.members)
    } catch (error) {
      console.error('Error fetching council members:', error)
      // Set mock data for development
      setCouncilMembers(getMockCouncilMembers())
    } finally {
      setLoading(false)
    }
  }

  const getMockCouncilMembers = (): CouncilMember[] => [
    {
      expert_id: 'analyst',
      name: 'The Analyst',
      rank: 1,
      overall_accuracy: 0.724,
      recent_accuracy: 0.785,
      voting_weight: 0.24,
      council_appearances: 23,
      recent_trend: 'improving',
      specialization_strength: {
        'game_outcome': 0.82,
        'betting_markets': 0.78,
        'player_props': 0.65
      },
      confidence_calibration: 0.89,
      total_predictions: 156,
      streak: { current: 7, type: 'winning' },
      personality_type: 'Data-Driven Analytical',
      last_updated: new Date().toISOString()
    },
    {
      expert_id: 'sharp',
      name: 'The Sharp',
      rank: 2,
      overall_accuracy: 0.698,
      recent_accuracy: 0.712,
      voting_weight: 0.22,
      council_appearances: 19,
      recent_trend: 'stable',
      specialization_strength: {
        'betting_markets': 0.85,
        'game_outcome': 0.72,
        'situational': 0.68
      },
      confidence_calibration: 0.76,
      total_predictions: 142,
      streak: { current: 3, type: 'winning' },
      personality_type: 'Market-Focused Sharp',
      last_updated: new Date().toISOString()
    },
    {
      expert_id: 'quant',
      name: 'The Quant',
      rank: 3,
      overall_accuracy: 0.672,
      recent_accuracy: 0.695,
      voting_weight: 0.20,
      council_appearances: 15,
      recent_trend: 'improving',
      specialization_strength: {
        'player_props': 0.78,
        'game_outcome': 0.69,
        'betting_markets': 0.62
      },
      confidence_calibration: 0.82,
      total_predictions: 134,
      streak: { current: 2, type: 'losing' },
      personality_type: 'Statistical Purist',
      last_updated: new Date().toISOString()
    },
    {
      expert_id: 'scholar',
      name: 'The Scholar',
      rank: 4,
      overall_accuracy: 0.658,
      recent_accuracy: 0.641,
      voting_weight: 0.18,
      council_appearances: 12,
      recent_trend: 'stable',
      specialization_strength: {
        'situational': 0.81,
        'game_outcome': 0.67,
        'betting_markets': 0.58
      },
      confidence_calibration: 0.74,
      total_predictions: 128,
      streak: { current: 1, type: 'winning' },
      personality_type: 'Research-Driven Scholar',
      last_updated: new Date().toISOString()
    },
    {
      expert_id: 'hunter',
      name: 'The Hunter',
      rank: 5,
      overall_accuracy: 0.641,
      recent_accuracy: 0.589,
      voting_weight: 0.16,
      council_appearances: 8,
      recent_trend: 'declining',
      specialization_strength: {
        'betting_markets': 0.71,
        'situational': 0.66,
        'game_outcome': 0.59
      },
      confidence_calibration: 0.68,
      total_predictions: 119,
      streak: { current: 4, type: 'losing' },
      personality_type: 'Value Hunter',
      last_updated: new Date().toISOString()
    }
  ]

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-red-500" />
      default:
        return <Target className="w-4 h-4 text-gray-500" />
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return 'text-green-600 bg-green-50'
      case 'declining': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.7) return 'text-green-600'
    if (accuracy >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const handleMemberClick = (memberId: string) => {
    setSelectedMember(selectedMember === memberId ? null : memberId)
    onMemberSelect?.(memberId)
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading council members...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Crown className="w-5 h-5 text-gold-500" />
          <span>AI Council Members</span>
          <Badge variant="secondary" className="ml-2">
            Top {councilMembers.length}
          </Badge>
        </CardTitle>
        <p className="text-sm text-gray-600">
          Current council composition based on performance rankings
        </p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {councilMembers.map((member, index) => (
          <div key={member.expert_id} className="space-y-3">
            {/* Main Member Row */}
            <div 
              className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                selectedMember === member.expert_id ? 'border-blue-300 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleMemberClick(member.expert_id)}
            >
              <div className="flex items-center justify-between">
                {/* Left: Member Info */}
                <div className="flex items-center space-x-4">
                  {/* Rank Badge */}
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                    index === 0 ? 'bg-gold-500' : 
                    index === 1 ? 'bg-silver-500' : 
                    index === 2 ? 'bg-bronze-500' : 'bg-blue-500'
                  }`}>
                    #{member.rank}
                  </div>
                  
                  {/* Member Details */}
                  <div>
                    <h3 className="font-semibold text-lg">{member.name}</h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <span>{member.personality_type}</span>
                      <span>•</span>
                      <div className="flex items-center space-x-1">
                        {getTrendIcon(member.recent_trend)}
                        <span className={`px-2 py-1 rounded text-xs ${getTrendColor(member.recent_trend)}`}>
                          {member.recent_trend}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Right: Key Metrics */}
                <div className="text-right space-y-1">
                  <div className="flex items-center space-x-4">
                    <div>
                      <div className="text-xs text-gray-500">Voting Weight</div>
                      <div className="font-bold text-lg">
                        {(member.voting_weight * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Accuracy</div>
                      <div className={`font-bold text-lg ${getAccuracyColor(member.overall_accuracy)}`}>
                        {(member.overall_accuracy * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Quick Stats Row */}
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                <div className="flex items-center space-x-6 text-sm">
                  <div className="flex items-center space-x-1">
                    <Activity className="w-4 h-4 text-gray-400" />
                    <span>{member.total_predictions} predictions</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Crown className="w-4 h-4 text-gray-400" />
                    <span>{member.council_appearances} council terms</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-gray-400" />
                    <span className={member.streak.type === 'winning' ? 'text-green-600' : 'text-red-600'}>
                      {member.streak.current} {member.streak.type === 'winning' ? 'W' : 'L'} streak
                    </span>
                  </div>
                </div>
                
                <Button variant="ghost" size="sm">
                  <Eye className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            {/* Detailed View (Expandable) */}
            {showDetailed && selectedMember === member.expert_id && (
              <div className="ml-4 p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Performance Metrics */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4" />
                      <span>Performance Metrics</span>
                    </h4>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Overall Accuracy</span>
                          <span className="font-medium">
                            {(member.overall_accuracy * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={member.overall_accuracy * 100} className="h-2" />
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Recent Performance</span>
                          <span className="font-medium">
                            {(member.recent_accuracy * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={member.recent_accuracy * 100} className="h-2" />
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Confidence Calibration</span>
                          <span className="font-medium">
                            {(member.confidence_calibration * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={member.confidence_calibration * 100} className="h-2" />
                      </div>
                    </div>
                  </div>
                  
                  {/* Specialization Strengths */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center space-x-2">
                      <Target className="w-4 h-4" />
                      <span>Specialization Strengths</span>
                    </h4>
                    
                    <div className="space-y-3">
                      {Object.entries(member.specialization_strength).map(([category, strength]) => (
                        <div key={category}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="capitalize">
                              {category.replace('_', ' ')}
                            </span>
                            <span className="font-medium">
                              {(strength * 100).toFixed(0)}%
                            </span>
                          </div>
                          <Progress value={strength * 100} className="h-2" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                
                {/* Additional Info */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>
                        Last updated: {new Date(member.last_updated).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex space-x-4">
                      <span>ID: {member.expert_id}</span>
                      <span>Weight: {(member.voting_weight * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        
        {/* Council Summary */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {councilMembers.reduce((sum, m) => sum + m.total_predictions, 0)}
              </div>
              <div className="text-xs text-gray-600">Total Predictions</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {(councilMembers.reduce((sum, m) => sum + m.overall_accuracy, 0) / councilMembers.length * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600">Average Accuracy</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {councilMembers.reduce((sum, m) => sum + m.council_appearances, 0)}
              </div>
              <div className="text-xs text-gray-600">Council Appearances</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default CouncilMembersPanel