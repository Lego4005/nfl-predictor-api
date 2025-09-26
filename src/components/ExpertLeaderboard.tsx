import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Trophy, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Medal,
  Filter,
  RefreshCw,
  BarChart3,
  Star,
  Crown
} from 'lucide-react'

interface ExpertRanking {
  expert_id: string
  name: string
  rank: number
  previous_rank: number
  overall_accuracy: number
  recent_accuracy: number
  leaderboard_score: number
  total_predictions: int
  correct_predictions: number
  recent_trend: 'improving' | 'stable' | 'declining'
  specialization: string[]
  confidence_calibration: number
  consistency_score: number
  personality_type: string
  is_council_member: boolean
  rank_change: number
}

interface LeaderboardFilters {
  timeframe: 'all_time' | 'recent' | 'last_week' | 'last_month'
  category: 'all' | 'game_outcome' | 'betting_markets' | 'player_props'
  sortBy: 'accuracy' | 'score' | 'consistency' | 'calibration'
}

interface ExpertLeaderboardProps {
  showCouncilOnly?: boolean
  maxEntries?: number
  enableFilters?: boolean
}

const ExpertLeaderboard: React.FC<ExpertLeaderboardProps> = ({
  showCouncilOnly = false,
  maxEntries = 15,
  enableFilters = true
}) => {
  const [rankings, setRankings] = useState<ExpertRanking[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState<LeaderboardFilters>({
    timeframe: 'all_time',
    category: 'all',
    sortBy: 'accuracy'
  })
  const [lastUpdated, setLastUpdated] = useState<string>('')

  useEffect(() => {
    fetchLeaderboard()
  }, [filters, showCouncilOnly])

  const fetchLeaderboard = async () => {
    try {
      setLoading(true)
      
      const params = new URLSearchParams({
        timeframe: filters.timeframe,
        category: filters.category,
        sortBy: filters.sortBy,
        councilOnly: showCouncilOnly.toString(),
        limit: maxEntries.toString()
      })
      
      // Mock API call - replace with actual API
      const response = await fetch(`/api/experts/leaderboard?${params}`)
      if (!response.ok) throw new Error('Failed to fetch leaderboard')
      
      const data = await response.json()
      setRankings(data.rankings)
      setLastUpdated(data.last_updated)
    } catch (error) {
      console.error('Error fetching leaderboard:', error)
      // Set mock data for development
      setRankings(getMockRankings())
      setLastUpdated(new Date().toISOString())
    } finally {
      setLoading(false)
    }
  }

  const getMockRankings = (): ExpertRanking[] => [
    {
      expert_id: 'analyst',
      name: 'The Analyst',
      rank: 1,
      previous_rank: 1,
      overall_accuracy: 0.724,
      recent_accuracy: 0.785,
      leaderboard_score: 89.2,
      total_predictions: 156,
      correct_predictions: 113,
      recent_trend: 'improving',
      specialization: ['Game Outcomes', 'Statistical Analysis'],
      confidence_calibration: 0.89,
      consistency_score: 0.82,
      personality_type: 'Data-Driven Analytical',
      is_council_member: true,
      rank_change: 0
    },
    {
      expert_id: 'sharp',
      name: 'The Sharp',
      rank: 2,
      previous_rank: 3,
      overall_accuracy: 0.698,
      recent_accuracy: 0.712,
      leaderboard_score: 85.6,
      total_predictions: 142,
      correct_predictions: 99,
      recent_trend: 'stable',
      specialization: ['Betting Markets', 'Line Movement'],
      confidence_calibration: 0.76,
      consistency_score: 0.79,
      personality_type: 'Market-Focused Sharp',
      is_council_member: true,
      rank_change: 1
    },
    {
      expert_id: 'quant',
      name: 'The Quant',
      rank: 3,
      previous_rank: 2,
      overall_accuracy: 0.672,
      recent_accuracy: 0.695,
      leaderboard_score: 82.4,
      total_predictions: 134,
      correct_predictions: 90,
      recent_trend: 'improving',
      specialization: ['Player Props', 'Advanced Metrics'],
      confidence_calibration: 0.82,
      consistency_score: 0.75,
      personality_type: 'Statistical Purist',
      is_council_member: true,
      rank_change: -1
    },
    {
      expert_id: 'scholar',
      name: 'The Scholar',
      rank: 4,
      previous_rank: 4,
      overall_accuracy: 0.658,
      recent_accuracy: 0.641,
      leaderboard_score: 79.8,
      total_predictions: 128,
      correct_predictions: 84,
      recent_trend: 'stable',
      specialization: ['Situational Analysis', 'Team Research'],
      confidence_calibration: 0.74,
      consistency_score: 0.81,
      personality_type: 'Research-Driven Scholar',
      is_council_member: true,
      rank_change: 0
    },
    {
      expert_id: 'hunter',
      name: 'The Hunter',
      rank: 5,
      previous_rank: 5,
      overall_accuracy: 0.641,
      recent_accuracy: 0.589,
      leaderboard_score: 76.3,
      total_predictions: 119,
      correct_predictions: 76,
      recent_trend: 'declining',
      specialization: ['Value Betting', 'Market Inefficiencies'],
      confidence_calibration: 0.68,
      consistency_score: 0.72,
      personality_type: 'Value Hunter',
      is_council_member: true,
      rank_change: 0
    }
    // Add more mock experts as needed
  ].slice(0, maxEntries)

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-gold-500 text-white'
    if (rank === 2) return 'bg-silver-500 text-white'
    if (rank === 3) return 'bg-bronze-500 text-white'
    if (rank <= 5) return 'bg-blue-500 text-white'
    if (rank <= 10) return 'bg-green-500 text-white'
    return 'bg-gray-500 text-white'
  }

  const getRankChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-500" />
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-500" />
    return <Target className="w-4 h-4 text-gray-500" />
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'declining': return <TrendingDown className="w-4 h-4 text-red-500" />
      default: return <Target className="w-4 h-4 text-gray-500" />
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading leaderboard...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="w-5 h-5 text-gold-500" />
            <span>Expert Leaderboard</span>
            {showCouncilOnly && (
              <Badge className="bg-blue-100 text-blue-800">
                <Crown className="w-3 h-3 mr-1" />
                Council Only
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchLeaderboard}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        
        {enableFilters && (
          <div className="flex items-center space-x-4 mt-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filters.timeframe}
                onChange={(e) => setFilters({...filters, timeframe: e.target.value as any})}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="all_time">All Time</option>
                <option value="recent">Recent</option>
                <option value="last_week">Last Week</option>
                <option value="last_month">Last Month</option>
              </select>
            </div>
            
            <select
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value as any})}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="all">All Categories</option>
              <option value="game_outcome">Game Outcomes</option>
              <option value="betting_markets">Betting Markets</option>
              <option value="player_props">Player Props</option>
            </select>
            
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters({...filters, sortBy: e.target.value as any})}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="accuracy">Accuracy</option>
              <option value="score">Overall Score</option>
              <option value="consistency">Consistency</option>
              <option value="calibration">Calibration</option>
            </select>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        {/* Leaderboard Table */}
        <div className="space-y-2">
          {rankings.map((expert, index) => (
            <div
              key={expert.expert_id}
              className={`p-4 border rounded-lg transition-all hover:shadow-sm ${
                expert.is_council_member ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between">
                {/* Left: Rank and Expert Info */}
                <div className="flex items-center space-x-4">
                  {/* Rank Badge */}
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${getRankBadgeColor(expert.rank)}`}>
                    {expert.rank <= 3 ? (
                      expert.rank === 1 ? <Medal className="w-5 h-5" /> :
                      expert.rank === 2 ? <Medal className="w-5 h-5" /> :
                      <Medal className="w-5 h-5" />
                    ) : (
                      `#${expert.rank}`
                    )}
                  </div>
                  
                  {/* Rank Change */}
                  <div className="flex flex-col items-center">
                    {getRankChangeIcon(expert.rank_change)}
                    {expert.rank_change !== 0 && (
                      <span className="text-xs text-gray-500">
                        {Math.abs(expert.rank_change)}
                      </span>
                    )}
                  </div>
                  
                  {/* Expert Details */}
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold">{expert.name}</h3>
                      {expert.is_council_member && (
                        <Crown className="w-4 h-4 text-gold-500" />
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <span>{expert.personality_type}</span>
                      <span>•</span>
                      <div className="flex items-center space-x-1">
                        {getTrendIcon(expert.recent_trend)}
                        <span>{expert.recent_trend}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3 text-xs text-gray-500 mt-1">
                      <span>{expert.total_predictions} predictions</span>
                      <span>•</span>
                      <span>{expert.specialization.join(', ')}</span>
                    </div>
                  </div>
                </div>
                
                {/* Right: Performance Metrics */}
                <div className="text-right">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-500">Accuracy</div>
                      <div className="font-bold text-lg">
                        {(expert.overall_accuracy * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        Recent: {(expert.recent_accuracy * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-gray-500">Score</div>
                      <div className="font-bold text-lg">
                        {expert.leaderboard_score.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">
                        Calibration: {(expert.confidence_calibration * 100).toFixed(0)}%
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-gray-500">Consistency</div>
                      <div className="font-bold text-lg">
                        {(expert.consistency_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {expert.correct_predictions}/{expert.total_predictions}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Performance Bars */}
              <div className="mt-3 grid grid-cols-3 gap-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Overall</span>
                    <span>{(expert.overall_accuracy * 100).toFixed(1)}%</span>
                  </div>
                  <Progress value={expert.overall_accuracy * 100} className="h-1" />
                </div>
                
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Recent</span>
                    <span>{(expert.recent_accuracy * 100).toFixed(1)}%</span>
                  </div>
                  <Progress value={expert.recent_accuracy * 100} className="h-1" />
                </div>
                
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Calibration</span>
                    <span>{(expert.confidence_calibration * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={expert.confidence_calibration * 100} className="h-1" />
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Summary Stats */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-4 gap-4 text-center text-sm">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {rankings.length}
              </div>
              <div className="text-gray-600">Total Experts</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {(rankings.reduce((sum, e) => sum + e.overall_accuracy, 0) / rankings.length * 100).toFixed(1)}%
              </div>
              <div className="text-gray-600">Avg Accuracy</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {rankings.filter(e => e.is_council_member).length}
              </div>
              <div className="text-gray-600">Council Members</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {rankings.reduce((sum, e) => sum + e.total_predictions, 0)}
              </div>
              <div className="text-gray-600">Total Predictions</div>
            </div>
          </div>
          
          {lastUpdated && (
            <div className="mt-4 text-center text-xs text-gray-500">
              Last updated: {new Date(lastUpdated).toLocaleString()}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default ExpertLeaderboard