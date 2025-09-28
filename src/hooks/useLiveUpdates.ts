import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import useWebSocket from './useWebSocket';
import type { 
  LiveUpdateMessage,
  ConsensusResult,
  ExpertPrediction,
  CouncilMember
} from '../types/aiCouncil';

interface UseLiveUpdatesOptions {
  gameId?: string;
  enablePredictionUpdates?: boolean;
  enableConsensusUpdates?: boolean;
  enableExpertUpdates?: boolean;
  enableGameUpdates?: boolean;
  updateThrottleMs?: number;
}

interface LiveUpdatesHookReturn {
  isConnected: boolean;
  lastUpdate: LiveUpdateMessage | null;
  latency: number;
  reconnectAttempts: number;
  requestUpdate: (type: string, data?: any) => void;
}

const useLiveUpdates = (options: UseLiveUpdatesOptions = {}): LiveUpdatesHookReturn => {
  const {
    gameId,
    enablePredictionUpdates = true,
    enableConsensusUpdates = true,
    enableExpertUpdates = true,
    enableGameUpdates = true,
    updateThrottleMs = 1000
  } = options;

  const queryClient = useQueryClient();
  const lastUpdateTime = useRef<number>(0);
  const pendingUpdates = useRef<Set<string>>(new Set());

  const { 
    connectionState, 
    sendMessage, 
    lastMessage, 
    subscribe 
  } = useWebSocket({
    gameId,
    autoReconnect: true,
    maxReconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000
  });

  // Throttled invalidation function
  const throttledInvalidate = useCallback((queryKeys: string[]) => {
    const now = Date.now();
    if (now - lastUpdateTime.current < updateThrottleMs) {
      // Add to pending updates
      queryKeys.forEach(key => pendingUpdates.current.add(key));
      return;
    }

    // Process current keys plus any pending
    const allKeys = [...queryKeys, ...Array.from(pendingUpdates.current)];
    pendingUpdates.current.clear();
    lastUpdateTime.current = now;

    // Invalidate queries
    allKeys.forEach(key => {
      queryClient.invalidateQueries({ queryKey: [key] });
    });
  }, [queryClient, updateThrottleMs]);

  // Handle prediction updates
  useEffect(() => {
    if (!enablePredictionUpdates) return;

    const unsubscribe = subscribe('PREDICTION_UPDATE', (data) => {
      console.log('Received prediction update:', data);
      
      // Update specific expert predictions
      if (data.expertId && gameId) {
        queryClient.setQueryData(
          ['expertPredictions', gameId],
          (oldData: ExpertPrediction[] | undefined) => {
            if (!oldData) return oldData;
            
            return oldData.map(prediction => 
              prediction.expertId === data.expertId
                ? { ...prediction, ...data.updates, lastUpdated: data.timestamp }
                : prediction
            );
          }
        );
      }
      
      // Invalidate related queries
      throttledInvalidate(['expertPredictions', 'predictionCategories']);
    });

    return unsubscribe;
  }, [subscribe, enablePredictionUpdates, queryClient, gameId, throttledInvalidate]);

  // Handle consensus updates
  useEffect(() => {
    if (!enableConsensusUpdates) return;

    const unsubscribe = subscribe('CONSENSUS_UPDATE', (data) => {
      console.log('Received consensus update:', data);
      
      // Update consensus data
      if (gameId) {
        queryClient.setQueryData(
          ['aiCouncil', gameId],
          (oldData: any) => {
            if (!oldData) return oldData;
            
            return {
              ...oldData,
              consensusResults: data.consensusResults || oldData.consensusResults,
              voteWeights: data.voteWeights || oldData.voteWeights,
              lastUpdated: data.timestamp
            };
          }
        );
      }
      
      // Invalidate related queries
      throttledInvalidate(['aiCouncil', 'consensus']);
    });

    return unsubscribe;
  }, [subscribe, enableConsensusUpdates, queryClient, gameId, throttledInvalidate]);

  // Handle expert performance updates
  useEffect(() => {
    if (!enableExpertUpdates) return;

    const unsubscribe = subscribe('EXPERT_UPDATE', (data) => {
      console.log('Received expert update:', data);
      
      // Update expert performance data
      queryClient.setQueryData(
        ['expertPerformance'],
        (oldData: CouncilMember[] | undefined) => {
          if (!oldData) return oldData;
          
          return oldData.map(expert => 
            expert.expertId === data.expertId
              ? { ...expert, ...data.updates }
              : expert
          );
        }
      );
      
      // Invalidate related queries
      throttledInvalidate(['expertPerformance', 'expertBattles']);
    });

    return unsubscribe;
  }, [subscribe, enableExpertUpdates, queryClient, throttledInvalidate]);

  // Handle game state updates
  useEffect(() => {
    if (!enableGameUpdates) return;

    const unsubscribe = subscribe('GAME_UPDATE', (data) => {
      console.log('Received game update:', data);
      
      // Update game data
      if (gameId) {
        queryClient.setQueryData(
          ['liveGame', gameId],
          (oldData: any) => ({
            ...oldData,
            ...data.gameState,
            lastUpdated: data.timestamp
          })
        );
      }
      
      // Invalidate related queries
      throttledInvalidate(['liveGame', 'games']);
    });

    return unsubscribe;
  }, [subscribe, enableGameUpdates, queryClient, gameId, throttledInvalidate]);

  // Handle market movement updates
  useEffect(() => {
    const unsubscribe = subscribe('MARKET_MOVEMENT', (data) => {
      console.log('Received market movement:', data);
      
      // Update betting markets data
      queryClient.setQueryData(
        ['bettingMarkets', gameId],
        (oldData: any) => ({
          ...oldData,
          movements: data.movements || oldData.movements,
          lastUpdated: data.timestamp
        })
      );
      
      // Invalidate related queries
      throttledInvalidate(['bettingMarkets', 'odds']);
    });

    return unsubscribe;
  }, [subscribe, queryClient, gameId, throttledInvalidate]);

  // Handle system status updates
  useEffect(() => {
    const unsubscribe = subscribe('SYSTEM_STATUS', (data) => {
      console.log('Received system status:', data);
      
      // Update system health data
      queryClient.setQueryData(
        ['systemHealth'],
        (oldData: any) => ({
          ...oldData,
          ...data.status,
          lastUpdated: data.timestamp
        })
      );
    });

    return unsubscribe;
  }, [subscribe, queryClient]);

  // Request specific updates
  const requestUpdate = useCallback((type: string, data?: any) => {
    sendMessage({
      type: 'REQUEST_UPDATE',
      updateType: type,
      gameId,
      data
    });
  }, [sendMessage, gameId]);

  // Process pending updates periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (pendingUpdates.current.size > 0) {
        const keys = Array.from(pendingUpdates.current);
        pendingUpdates.current.clear();
        lastUpdateTime.current = Date.now();
        
        keys.forEach(key => {
          queryClient.invalidateQueries({ queryKey: [key] });
        });
      }
    }, updateThrottleMs);

    return () => clearInterval(interval);
  }, [queryClient, updateThrottleMs]);

  return {
    isConnected: connectionState.connected,
    lastUpdate: lastMessage,
    latency: connectionState.latency,
    reconnectAttempts: connectionState.reconnectAttempts,
    requestUpdate
  };
};

export default useLiveUpdates;