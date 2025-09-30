/**
 * Confidence Pool Hooks Tests
 * Comprehensive test suite for all Confidence Pool hooks
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

import {
  useExpertBankrolls,
  useLiveBettingFeed,
  useCouncilPredictions,
  useExpertMemories,
  usePredictionBattles,
  useConfidencePoolWebSocket
} from '../../src/hooks/confidencePool';

// Mock Supabase client
vi.mock('../../src/services/supabaseClient', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          order: vi.fn(() => ({
            limit: vi.fn(() => ({
              data: [],
              error: null
            }))
          }))
        })),
        gte: vi.fn(() => ({
          order: vi.fn(() => ({
            limit: vi.fn(() => ({
              data: [],
              error: null
            }))
          }))
        })),
        order: vi.fn(() => ({
          limit: vi.fn(() => ({
            data: [],
            error: null
          }))
        }))
      }))
    })),
    channel: vi.fn(() => ({
      on: vi.fn(() => ({
        subscribe: vi.fn()
      })),
      unsubscribe: vi.fn()
    }))
  }
}));

// Create QueryClient wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0
      }
    }
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Confidence Pool Hooks', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0
        }
      }
    });
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('useExpertBankrolls', () => {
    it('should fetch expert bankrolls', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(() => useExpertBankrolls(), { wrapper });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.bankrolls).toBeInstanceOf(Array);
    });

    it('should apply sortBy filter', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(
        () => useExpertBankrolls({ sortBy: 'roi' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
    });

    it('should filter by status', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(
        () => useExpertBankrolls({ filterByStatus: ['safe', 'warning'] }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.bankrolls.forEach(bankroll => {
          expect(['safe', 'warning']).toContain(bankroll.status);
        });
      }
    });

    it('should support custom refetch interval', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(
        () => useExpertBankrolls({ refetchInterval: 10000 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
    });
  });

  describe('useLiveBettingFeed', () => {
    it('should fetch live betting feed', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(() => useLiveBettingFeed(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.bets).toBeInstanceOf(Array);
      expect(result.current.data?.summary).toBeDefined();
    });

    it('should filter by game_id', async () => {
      const wrapper = createWrapper();
      const gameId = '2025_05_KC_BUF';

      const { result } = renderHook(
        () => useLiveBettingFeed({ game_id: gameId }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.bets.forEach(bet => {
          expect(bet.game_id).toBe(gameId);
        });
      }
    });

    it('should filter by expert_id', async () => {
      const wrapper = createWrapper();
      const expertId = 'the-analyst';

      const { result } = renderHook(
        () => useLiveBettingFeed({ expert_id: expertId }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.bets.forEach(bet => {
          expect(bet.expert_id).toBe(expertId);
        });
      }
    });

    it('should filter by status', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(
        () => useLiveBettingFeed({ status: 'pending' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.bets.forEach(bet => {
          expect(bet.status).toBe('pending');
        });
      }
    });
  });

  describe('useCouncilPredictions', () => {
    it('should fetch council predictions', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(() => useCouncilPredictions(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.predictions).toBeInstanceOf(Array);
      expect(result.current.data?.weekly_data).toBeDefined();
    });

    it('should filter by week', async () => {
      const wrapper = createWrapper();
      const week = 5;

      const { result } = renderHook(
        () => useCouncilPredictions({ week }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        expect(result.current.data.weekly_data.week).toBe(week);
      }
    });

    it('should filter by min_confidence', async () => {
      const wrapper = createWrapper();
      const minConfidence = 0.75;

      const { result } = renderHook(
        () => useCouncilPredictions({ min_confidence: minConfidence }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.predictions.forEach(pred => {
          expect(pred.prediction.confidence).toBeGreaterThanOrEqual(minConfidence);
        });
      }
    });
  });

  describe('useExpertMemories', () => {
    it('should fetch expert memories', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(() => useExpertMemories(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.memories).toBeInstanceOf(Array);
      expect(result.current.data?.pagination).toBeDefined();
    });

    it('should filter by expert_id', async () => {
      const wrapper = createWrapper();
      const expertId = 'the-gambler';

      const { result } = renderHook(
        () => useExpertMemories({ expert_id: expertId }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.memories.forEach(memory => {
          expect(memory.expert_id).toBe(expertId);
        });
      }
    });

    it('should support pagination', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(
        () => useExpertMemories({ limit: 10, offset: 0 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        expect(result.current.data.memories.length).toBeLessThanOrEqual(10);
        expect(result.current.data.pagination.limit).toBe(10);
        expect(result.current.data.pagination.offset).toBe(0);
      }
    });

    it('should filter by memory_type', async () => {
      const wrapper = createWrapper();
      const memoryType = 'lesson_learned';

      const { result } = renderHook(
        () => useExpertMemories({
          filters: { memory_type: memoryType }
        }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.memories.forEach(memory => {
          expect(memory.memory_type).toBe(memoryType);
        });
      }
    });
  });

  describe('usePredictionBattles', () => {
    it('should fetch prediction battles', async () => {
      const wrapper = createWrapper();

      const { result } = renderHook(() => usePredictionBattles(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.battles).toBeInstanceOf(Array);
      expect(result.current.data?.summary).toBeDefined();
    });

    it('should filter by min_difference', async () => {
      const wrapper = createWrapper();
      const minDiff = 5.0;

      const { result } = renderHook(
        () => usePredictionBattles({ min_difference: minDiff }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.battles.forEach(battle => {
          expect(battle.difference).toBeGreaterThanOrEqual(minDiff);
        });
      }
    });

    it('should filter by category', async () => {
      const wrapper = createWrapper();
      const category = 'spread';

      const { result } = renderHook(
        () => usePredictionBattles({ category }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      if (result.current.data) {
        result.current.data.battles.forEach(battle => {
          expect(battle.category).toBe(category);
        });
      }
    });
  });

  describe('useConfidencePoolWebSocket', () => {
    it('should establish WebSocket connection', () => {
      const { result } = renderHook(() =>
        useConfidencePoolWebSocket({ autoReconnect: false })
      );

      expect(result.current.connectionState).toBeDefined();
      expect(result.current.isConnected).toBeDefined();
      expect(result.current.sendMessage).toBeInstanceOf(Function);
      expect(result.current.connect).toBeInstanceOf(Function);
      expect(result.current.disconnect).toBeInstanceOf(Function);
    });

    it('should handle event callbacks', () => {
      const onBetPlaced = vi.fn();
      const onBetSettled = vi.fn();

      const { result } = renderHook(() =>
        useConfidencePoolWebSocket({
          autoReconnect: false,
          onBetPlaced,
          onBetSettled
        })
      );

      expect(result.current).toBeDefined();
      expect(onBetPlaced).not.toHaveBeenCalled();
      expect(onBetSettled).not.toHaveBeenCalled();
    });

    it('should disconnect on unmount', () => {
      const { result, unmount } = renderHook(() =>
        useConfidencePoolWebSocket({ autoReconnect: false })
      );

      expect(result.current.disconnect).toBeInstanceOf(Function);

      unmount();

      // Connection should be cleaned up
      expect(result.current.connectionState.connected).toBe(false);
    });
  });
});