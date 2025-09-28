import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { nflAPI, APIError } from '../services/api';
import type {
  CouncilMember,
  ConsensusResult,
  ExpertPrediction,
  VoteWeight,
  ExpertPerformanceMetrics,
  SystemHealthMetrics
} from '../types/aiCouncil';

// Query key factory
export const queryKeys = {
  all: ['nfl-predictions'] as const,
  
  // AI Council
  aiCouncil: (gameId?: string) => [...queryKeys.all, 'ai-council', gameId] as const,
  councilMembers: () => [...queryKeys.all, 'council-members'] as const,
  consensusResults: (gameId: string) => [...queryKeys.all, 'consensus', gameId] as const,
  voteWeights: (expertIds?: string[]) => [...queryKeys.all, 'vote-weights', expertIds] as const,
  
  // Expert Predictions
  expertPredictions: (gameId: string) => [...queryKeys.all, 'expert-predictions', gameId] as const,
  expertByCategory: (gameId: string, categoryIds: string[]) => 
    [...queryKeys.all, 'expert-by-category', gameId, categoryIds] as const,
  
  // Expert Battles
  expertBattles: (expertIds: string[]) => [...queryKeys.all, 'expert-battles', expertIds] as const,
  headToHead: (expert1Id: string, expert2Id: string, timeRange: string) => 
    [...queryKeys.all, 'head-to-head', expert1Id, expert2Id, timeRange] as const,
  
  // Expert Performance
  expertPerformance: (expertId?: string, timeframe?: string) => 
    [...queryKeys.all, 'expert-performance', expertId, timeframe] as const,
  allExpertPerformance: (timeframe: string) => 
    [...queryKeys.all, 'all-expert-performance', timeframe] as const,
  
  // System & Games
  systemHealth: () => [...queryKeys.all, 'system-health'] as const,
  games: (status?: string, week?: number) => [...queryKeys.all, 'games', status, week] as const,
  game: (gameId: string) => [...queryKeys.all, 'game', gameId] as const,
  liveGames: () => [...queryKeys.all, 'live-games'] as const,
};

// AI Council Hooks
export const useCouncilMembers = () => {
  return useQuery({
    queryKey: queryKeys.councilMembers(),
    queryFn: () => nflAPI.aiCouncil.getCouncilMembers(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useConsensusResults = (gameId: string) => {
  return useQuery({
    queryKey: queryKeys.consensusResults(gameId),
    queryFn: () => nflAPI.aiCouncil.getConsensusResults(gameId),
    enabled: !!gameId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useVoteWeights = (expertIds?: string[]) => {
  return useQuery({
    queryKey: queryKeys.voteWeights(expertIds),
    queryFn: () => nflAPI.aiCouncil.getVoteWeights(expertIds),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useAICouncilData = (gameId: string) => {
  return useQuery({
    queryKey: queryKeys.aiCouncil(gameId),
    queryFn: () => nflAPI.getDashboardData(gameId),
    enabled: !!gameId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Expert Predictions Hooks
export const useExpertPredictions = (gameId: string) => {
  return useQuery({
    queryKey: queryKeys.expertPredictions(gameId),
    queryFn: () => nflAPI.expertPredictions.getExpertPredictions(gameId),
    enabled: !!gameId,
    staleTime: 60 * 1000, // 1 minute
    cacheTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useExpertPredictionsByCategory = (gameId: string, categoryIds: string[]) => {
  return useQuery({
    queryKey: queryKeys.expertByCategory(gameId, categoryIds),
    queryFn: () => nflAPI.expertPredictions.getExpertPredictionsByCategory(gameId, categoryIds),
    enabled: !!gameId && categoryIds.length > 0,
    staleTime: 60 * 1000, // 1 minute
    cacheTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Expert Battle Hooks
export const useExpertBattleData = (expertIds: string[]) => {
  return useQuery({
    queryKey: queryKeys.expertBattles(expertIds),
    queryFn: () => nflAPI.getExpertBattleData(expertIds),
    enabled: expertIds.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useHeadToHeadComparison = (
  expert1Id: string,
  expert2Id: string,
  timeRange: 'week' | 'month' | 'season' | 'all_time' = 'all_time'
) => {
  return useQuery({
    queryKey: queryKeys.headToHead(expert1Id, expert2Id, timeRange),
    queryFn: () => nflAPI.expertBattles.getHeadToHeadRecord(expert1Id, expert2Id, timeRange),
    enabled: !!expert1Id && !!expert2Id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Expert Performance Hooks
export const useExpertPerformance = (
  expertId: string,
  timeframe: 'daily' | 'weekly' | 'monthly' | 'seasonal' = 'weekly'
) => {
  return useQuery({
    queryKey: queryKeys.expertPerformance(expertId, timeframe),
    queryFn: () => nflAPI.expertPerformance.getExpertPerformance(expertId, timeframe),
    enabled: !!expertId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useAllExpertPerformance = (
  timeframe: 'daily' | 'weekly' | 'monthly' | 'seasonal' = 'weekly'
) => {
  return useQuery({
    queryKey: queryKeys.allExpertPerformance(timeframe),
    queryFn: () => nflAPI.expertPerformance.getAllExpertPerformance(timeframe),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

// System Health Hooks
export const useSystemHealth = () => {
  return useQuery({
    queryKey: queryKeys.systemHealth(),
    queryFn: () => nflAPI.systemHealth.getSystemHealth(),
    staleTime: 30 * 1000, // 30 seconds
    cacheTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
};

// Games Hooks
export const useGames = (
  status?: 'scheduled' | 'live' | 'final',
  week?: number
) => {
  return useQuery({
    queryKey: queryKeys.games(status, week),
    queryFn: () => nflAPI.gameData.getGames(status, week),
    staleTime: status === 'live' ? 30 * 1000 : 5 * 60 * 1000, // 30s for live, 5min for others
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: status === 'live' ? 30 * 1000 : undefined, // Auto-refetch live games
  });
};

export const useGame = (gameId: string) => {
  return useQuery({
    queryKey: queryKeys.game(gameId),
    queryFn: () => nflAPI.gameData.getGame(gameId),
    enabled: !!gameId,
    staleTime: 60 * 1000, // 1 minute
    cacheTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useLiveGames = () => {
  return useQuery({
    queryKey: queryKeys.liveGames(),
    queryFn: () => nflAPI.gameData.getLiveGames(),
    staleTime: 15 * 1000, // 15 seconds
    cacheTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 15 * 1000, // Refetch every 15 seconds
  });
};

// Mutation Hooks
export const useUpdateConsensus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ 
      gameId, 
      categoryId, 
      consensusData 
    }: { 
      gameId: string; 
      categoryId: string; 
      consensusData: Partial<ConsensusResult> 
    }) => {
      return nflAPI.aiCouncil.updateConsensus(gameId, categoryId, consensusData);
    },
    onSuccess: (data, variables) => {
      // Invalidate and update related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.consensusResults(variables.gameId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.aiCouncil(variables.gameId) });
    },
  });
};

export const useUpdateExpertPrediction = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ 
      expertId, 
      gameId, 
      predictions 
    }: { 
      expertId: string; 
      gameId: string; 
      predictions: any[] 
    }) => {
      return nflAPI.expertPredictions.updateExpertPrediction(expertId, gameId, predictions);
    },
    onSuccess: (data, variables) => {
      // Invalidate and update related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.expertPredictions(variables.gameId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.aiCouncil(variables.gameId) });
    },
  });
};

export const useUpdateExpertPerformance = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ 
      expertId, 
      metrics 
    }: { 
      expertId: string; 
      metrics: Partial<ExpertPerformanceMetrics> 
    }) => {
      return nflAPI.expertPerformance.updateExpertPerformance(expertId, metrics);
    },
    onSuccess: (data, variables) => {
      // Invalidate and update related queries
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.expertPerformance(variables.expertId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.allExpertPerformance('weekly') 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.councilMembers() 
      });
    },
  });
};

// Error handling hook
export const useAPIError = () => {
  const handleError = (error: Error | APIError) => {
    if (error instanceof APIError) {
      console.error('API Error:', {
        message: error.message,
        status: error.status,
        code: error.code,
        details: error.details
      });
      
      // You could add toast notifications, error reporting, etc. here
      return {
        message: error.message,
        status: error.status,
        code: error.code,
        isAPIError: true
      };
    }
    
    console.error('Unexpected Error:', error);
    return {
      message: 'An unexpected error occurred',
      status: 500,
      code: 'UNKNOWN_ERROR',
      isAPIError: false
    };
  };

  return { handleError };
};