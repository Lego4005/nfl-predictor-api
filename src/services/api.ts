import { createClient } from '@supabase/supabase-js';
import type {
  CouncilMember,
  ConsensusResult,
  ExpertPrediction,
  VoteWeight,
  CategoryPrediction,
  HeadToHeadComparison,
  ExpertPerformanceMetrics,
  SystemHealthMetrics
} from '../types/aiCouncil';

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// API Error handling
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Response wrapper type
interface APIResponse<T> {
  data: T | null;
  error: APIError | null;
  loading: boolean;
}

// Base API service class
class APIService {
  private handleError(error: any): APIError {
    if (error.message) {
      return new APIError(
        error.message,
        error.status || 500,
        error.code,
        error.details
      );
    }
    return new APIError('An unexpected error occurred', 500);
  }

  protected async request<T>(
    table: string,
    options: {
      select?: string;
      eq?: { column: string; value: any };
      in?: { column: string; values: any[] };
      gte?: { column: string; value: any };
      lte?: { column: string; value: any };
      order?: { column: string; ascending?: boolean };
      limit?: number;
      single?: boolean;
    } = {}
  ): Promise<T> {
    try {
      let query = supabase.from(table);
      
      if (options.select) {
        query = query.select(options.select);
      } else {
        query = query.select('*');
      }

      if (options.eq) {
        query = query.eq(options.eq.column, options.eq.value);
      }

      if (options.in) {
        query = query.in(options.in.column, options.in.values);
      }

      if (options.gte) {
        query = query.gte(options.gte.column, options.gte.value);
      }

      if (options.lte) {
        query = query.lte(options.lte.column, options.lte.value);
      }

      if (options.order) {
        query = query.order(options.order.column, { 
          ascending: options.order.ascending ?? true 
        });
      }

      if (options.limit) {
        query = query.limit(options.limit);
      }

      if (options.single) {
        query = query.single();
      }

      const { data, error } = await query;

      if (error) {
        throw this.handleError(error);
      }

      return data as T;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  protected async insert<T>(
    table: string,
    data: any,
    options: { select?: string } = {}
  ): Promise<T> {
    try {
      let query = supabase.from(table).insert(data);
      
      if (options.select) {
        query = query.select(options.select);
      }

      const { data: result, error } = await query;

      if (error) {
        throw this.handleError(error);
      }

      return result as T;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  protected async update<T>(
    table: string,
    updates: any,
    conditions: { column: string; value: any }[],
    options: { select?: string } = {}
  ): Promise<T> {
    try {
      let query = supabase.from(table).update(updates);
      
      conditions.forEach(condition => {
        query = query.eq(condition.column, condition.value);
      });

      if (options.select) {
        query = query.select(options.select);
      }

      const { data, error } = await query;

      if (error) {
        throw this.handleError(error);
      }

      return data as T;
    } catch (error) {
      throw this.handleError(error);
    }
  }
}

// AI Council API Service
export class AICouncilAPIService extends APIService {
  async getCouncilMembers(): Promise<CouncilMember[]> {
    return this.request<CouncilMember[]>('experts', {
      select: `
        expert_id,
        expert_name,
        overall_accuracy,
        recent_trend,
        specialization,
        join_date,
        total_votes,
        consensus_alignment,
        vote_weights (
          expert_id,
          overall_weight,
          accuracy_component,
          recent_performance_component,
          confidence_component,
          council_tenure_component,
          normalized_weight
        )
      `,
      order: { column: 'overall_accuracy', ascending: false }
    });
  }

  async getConsensusResults(gameId: string): Promise<ConsensusResult[]> {
    return this.request<ConsensusResult[]>('ai_council_consensus', {
      select: `
        game_id,
        category_id,
        consensus_value,
        confidence,
        agreement,
        total_experts,
        voting_breakdown,
        weighted_score,
        conflicting_experts,
        timestamp
      `,
      eq: { column: 'game_id', value: gameId },
      order: { column: 'confidence', ascending: false }
    });
  }

  async getVoteWeights(expertIds?: string[]): Promise<VoteWeight[]> {
    const options: any = {
      select: `
        expert_id,
        overall_weight,
        accuracy_component,
        recent_performance_component,
        confidence_component,
        council_tenure_component,
        normalized_weight
      `
    };

    if (expertIds && expertIds.length > 0) {
      options.in = { column: 'expert_id', values: expertIds };
    }

    return this.request<VoteWeight[]>('vote_weights', options);
  }

  async updateConsensus(
    gameId: string,
    categoryId: string,
    consensusData: Partial<ConsensusResult>
  ): Promise<ConsensusResult> {
    return this.update<ConsensusResult>(
      'ai_council_consensus',
      consensusData,
      [
        { column: 'game_id', value: gameId },
        { column: 'category_id', value: categoryId }
      ],
      { select: '*' }
    );
  }
}

// Expert Predictions API Service
export class ExpertPredictionsAPIService extends APIService {
  async getExpertPredictions(gameId: string): Promise<ExpertPrediction[]> {
    return this.request<ExpertPrediction[]>('expert_predictions', {
      select: `
        expert_id,
        game_id,
        predictions,
        overall_confidence,
        submission_time,
        last_updated,
        experts (
          expert_name,
          specialization,
          overall_accuracy
        )
      `,
      eq: { column: 'game_id', value: gameId },
      order: { column: 'overall_confidence', ascending: false }
    });
  }

  async getExpertPredictionsByCategory(
    gameId: string,
    categoryIds: string[]
  ): Promise<CategoryPrediction[]> {
    // This would typically require a more complex query or post-processing
    const predictions = await this.getExpertPredictions(gameId);
    
    return predictions.flatMap(prediction =>
      prediction.predictions.filter(p => 
        categoryIds.includes(p.categoryId)
      )
    );
  }

  async updateExpertPrediction(
    expertId: string,
    gameId: string,
    predictions: CategoryPrediction[]
  ): Promise<ExpertPrediction> {
    return this.update<ExpertPrediction>(
      'expert_predictions',
      { 
        predictions,
        last_updated: new Date().toISOString()
      },
      [
        { column: 'expert_id', value: expertId },
        { column: 'game_id', value: gameId }
      ],
      { select: '*' }
    );
  }
}

// Expert Battle API Service
export class ExpertBattleAPIService extends APIService {
  async getHeadToHeadRecord(
    expert1Id: string,
    expert2Id: string,
    timeRange: 'week' | 'month' | 'season' | 'all_time' = 'all_time'
  ): Promise<HeadToHeadComparison> {
    // This would typically involve a complex query across multiple tables
    // For now, return mock data structure
    const mockData: HeadToHeadComparison = {
      expert1: await this.getExpertById(expert1Id),
      expert2: await this.getExpertById(expert2Id),
      battleRecord: {
        wins: 0,
        losses: 0,
        ties: 0,
        winPercentage: 0
      },
      categoryDominance: {},
      recentForm: {
        expert1Streak: 0,
        expert2Streak: 0,
        momentum: 'neutral'
      }
    };

    return mockData;
  }

  private async getExpertById(expertId: string): Promise<CouncilMember> {
    return this.request<CouncilMember>('experts', {
      eq: { column: 'expert_id', value: expertId },
      single: true
    });
  }

  async getExpertBattleHistory(
    expertIds: string[],
    gameIds?: string[]
  ): Promise<any[]> {
    const options: any = {
      select: '*',
      in: { column: 'expert_id', values: expertIds }
    };

    if (gameIds && gameIds.length > 0) {
      options.in = { ...options.in, game_id: gameIds };
    }

    return this.request<any[]>('expert_battles', options);
  }
}

// Expert Performance API Service
export class ExpertPerformanceAPIService extends APIService {
  async getExpertPerformance(
    expertId: string,
    timeframe: 'daily' | 'weekly' | 'monthly' | 'seasonal' = 'weekly'
  ): Promise<ExpertPerformanceMetrics> {
    return this.request<ExpertPerformanceMetrics>('expert_performance', {
      select: `
        expert_id,
        timeframe,
        accuracy,
        confidence,
        betting,
        council_contribution
      `,
      eq: { column: 'expert_id', value: expertId },
      single: true
    });
  }

  async getAllExpertPerformance(
    timeframe: 'daily' | 'weekly' | 'monthly' | 'seasonal' = 'weekly'
  ): Promise<ExpertPerformanceMetrics[]> {
    return this.request<ExpertPerformanceMetrics[]>('expert_performance', {
      eq: { column: 'timeframe', value: timeframe },
      order: { column: 'accuracy', ascending: false }
    });
  }

  async updateExpertPerformance(
    expertId: string,
    metrics: Partial<ExpertPerformanceMetrics>
  ): Promise<ExpertPerformanceMetrics> {
    return this.update<ExpertPerformanceMetrics>(
      'expert_performance',
      metrics,
      [{ column: 'expert_id', value: expertId }],
      { select: '*' }
    );
  }
}

// System Health API Service
export class SystemHealthAPIService extends APIService {
  async getSystemHealth(): Promise<SystemHealthMetrics> {
    return this.request<SystemHealthMetrics>('system_health', {
      order: { column: 'timestamp', ascending: false },
      limit: 1,
      single: true
    });
  }

  async getSystemHealthHistory(
    hours: number = 24
  ): Promise<SystemHealthMetrics[]> {
    const since = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    return this.request<SystemHealthMetrics[]>('system_health', {
      gte: { column: 'timestamp', value: since.toISOString() },
      order: { column: 'timestamp', ascending: false }
    });
  }
}

// Game Data API Service
export class GameDataAPIService extends APIService {
  async getGames(
    status?: 'scheduled' | 'live' | 'final',
    week?: number
  ): Promise<any[]> {
    const options: any = {
      select: `
        game_id,
        home_team,
        away_team,
        game_time,
        status,
        week,
        season,
        home_score,
        away_score,
        quarter,
        time_remaining
      `,
      order: { column: 'game_time', ascending: true }
    };

    if (status) {
      options.eq = { column: 'status', value: status };
    }

    if (week) {
      if (options.eq) {
        // Would need to handle multiple conditions differently
        console.warn('Multiple conditions not fully supported in this simplified API');
      } else {
        options.eq = { column: 'week', value: week };
      }
    }

    return this.request<any[]>('games', options);
  }

  async getLiveGames(): Promise<any[]> {
    return this.getGames('live');
  }

  async getGame(gameId: string): Promise<any> {
    return this.request<any>('games', {
      eq: { column: 'game_id', value: gameId },
      single: true
    });
  }
}

// Combined API service
export class NFLPredictionAPIService {
  public readonly aiCouncil = new AICouncilAPIService();
  public readonly expertPredictions = new ExpertPredictionsAPIService();
  public readonly expertBattles = new ExpertBattleAPIService();
  public readonly expertPerformance = new ExpertPerformanceAPIService();
  public readonly systemHealth = new SystemHealthAPIService();
  public readonly gameData = new GameDataAPIService();

  // Combined methods for complex operations
  async getDashboardData(gameId: string) {
    try {
      const [
        councilMembers,
        consensusResults,
        expertPredictions,
        voteWeights
      ] = await Promise.all([
        this.aiCouncil.getCouncilMembers(),
        this.aiCouncil.getConsensusResults(gameId),
        this.expertPredictions.getExpertPredictions(gameId),
        this.aiCouncil.getVoteWeights()
      ]);

      return {
        councilMembers,
        consensusResults,
        expertPredictions,
        voteWeights,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      throw new APIError('Failed to load dashboard data', 500, 'DASHBOARD_ERROR', error);
    }
  }

  async getExpertBattleData(expertIds: string[]) {
    try {
      const [
        experts,
        performance,
        battleHistory
      ] = await Promise.all([
        Promise.all(expertIds.map(id => 
          this.expertPerformance.getExpertPerformance(id)
        )),
        this.expertPerformance.getAllExpertPerformance(),
        this.expertBattles.getExpertBattleHistory(expertIds)
      ]);

      return {
        experts,
        performance,
        battleHistory,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      throw new APIError('Failed to load expert battle data', 500, 'BATTLE_ERROR', error);
    }
  }
}

// Export singleton instance
export const nflAPI = new NFLPredictionAPIService();
export default nflAPI;