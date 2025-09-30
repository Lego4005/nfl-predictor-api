/**
 * useLiveBettingFeed Hook
 * Real-time betting feed with expert bets and live updates
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { supabase } from '../services/supabaseClient';
import type {
  LiveBet,
  BettingFeedResponse,
  UseLiveBettingFeedOptions,
  BetPlacedEvent,
  BetSettledEvent
} from '../types/confidencePool';

/**
 * Hook to fetch and track live betting feed in real-time
 * @param options - Query options and filters
 */
export const useLiveBettingFeed = (options: UseLiveBettingFeedOptions = {}) => {
  const {
    game_id,
    expert_id,
    status = 'pending',
    limit = 50,
    realtime = true
  } = options;

  const queryClient = useQueryClient();

  const query = useQuery<BettingFeedResponse>({
    queryKey: ['live-betting-feed', game_id, expert_id, status, limit],
    queryFn: async () => {
      console.log('🎲 Fetching live betting feed...');

      // Query expert_virtual_bets with joins
      let supabaseQuery = supabase
        .from('expert_virtual_bets')
        .select(`
          bet_id,
          expert_id,
          game_id,
          bet_type,
          prediction,
          bet_amount,
          vegas_odds,
          confidence,
          reasoning,
          potential_payout,
          placed_at,
          status,
          settled_at,
          actual_payout,
          expert_models!inner (
            expert_id,
            name,
            emoji,
            archetype
          ),
          games!inner (
            game_id,
            home_team,
            away_team
          )
        `);

      // Apply filters
      if (game_id) {
        supabaseQuery = supabaseQuery.eq('game_id', game_id);
      }

      if (expert_id) {
        supabaseQuery = supabaseQuery.eq('expert_id', expert_id);
      }

      if (status !== 'all') {
        supabaseQuery = supabaseQuery.eq('status', status);
      }

      // Order by most recent first
      supabaseQuery = supabaseQuery
        .order('placed_at', { ascending: false })
        .limit(limit);

      const { data, error } = await supabaseQuery;

      if (error) {
        console.error('Error fetching betting feed:', error);
        throw error;
      }

      if (!data || data.length === 0) {
        return {
          bets: [],
          summary: {
            total_at_risk: 0,
            potential_payout: 0,
            avg_confidence: 0,
            total_bets: 0,
            experts_active: 0
          },
          timestamp: new Date().toISOString()
        };
      }

      // Transform data to LiveBet format
      const bets: LiveBet[] = data.map((row: any) => {
        // Calculate bankroll percentage
        const bankrollPercentage = (row.bet_amount / 10000) * 100; // Assuming $10k starting bankroll

        // Determine risk level
        let risk_level: LiveBet['risk_level'];
        if (bankrollPercentage > 40) {
          risk_level = 'extreme';
        } else if (bankrollPercentage > 20) {
          risk_level = 'high';
        } else if (bankrollPercentage > 10) {
          risk_level = 'medium';
        } else {
          risk_level = 'low';
        }

        // Parse reasoning if it's a JSON string
        let reasoning: string[] = [];
        if (typeof row.reasoning === 'string') {
          try {
            reasoning = JSON.parse(row.reasoning);
          } catch {
            reasoning = [row.reasoning];
          }
        } else if (Array.isArray(row.reasoning)) {
          reasoning = row.reasoning;
        }

        return {
          bet_id: row.bet_id,
          expert_id: row.expert_id,
          expert_name: row.expert_models.name,
          expert_emoji: row.expert_models.emoji,
          game_id: row.game_id,
          home_team: row.games.home_team,
          away_team: row.games.away_team,
          bet_type: row.bet_type,
          prediction: row.prediction,
          bet_amount: row.bet_amount,
          bankroll_percentage: bankrollPercentage,
          vegas_odds: row.vegas_odds,
          confidence: row.confidence,
          risk_level,
          reasoning,
          potential_payout: row.potential_payout,
          placed_at: row.placed_at,
          status: row.status,
          settled_at: row.settled_at,
          actual_payout: row.actual_payout
        };
      });

      // Calculate summary statistics
      const pendingBets = bets.filter(b => b.status === 'pending');
      const uniqueExperts = new Set(bets.map(b => b.expert_id));

      const summary = {
        total_at_risk: pendingBets.reduce((sum, b) => sum + b.bet_amount, 0),
        potential_payout: pendingBets.reduce((sum, b) => sum + b.potential_payout, 0),
        avg_confidence: pendingBets.length > 0 ?
          pendingBets.reduce((sum, b) => sum + b.confidence, 0) / pendingBets.length : 0,
        total_bets: bets.length,
        experts_active: uniqueExperts.size
      };

      console.log(`✅ Fetched ${bets.length} bets from betting feed`);

      return {
        bets,
        summary,
        timestamp: new Date().toISOString()
      };
    },
    enabled: true,
    staleTime: 10 * 1000, // 10 seconds for near real-time
    gcTime: 60 * 1000, // 1 minute
    refetchInterval: status === 'pending' ? 15 * 1000 : undefined // Auto-refetch pending bets
  });

  // Set up real-time subscription for new bets
  useEffect(() => {
    if (!realtime) return;

    console.log('🔄 Setting up real-time betting feed subscription...');

    const channel = supabase
      .channel('live-betting-feed')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'expert_virtual_bets'
        },
        (payload) => {
          console.log('🎲 New bet placed:', payload);

          // Invalidate and refetch
          queryClient.invalidateQueries({ queryKey: ['live-betting-feed'] });

          // Emit custom event for notifications
          const event = new CustomEvent<BetPlacedEvent>('bet-placed', {
            detail: {
              type: 'bet_placed',
              bet: payload.new as any,
              bankroll_update: {
                expert_id: (payload.new as any).expert_id,
                old_balance: 0, // Will be populated by backend
                new_balance: 0
              }
            }
          });
          window.dispatchEvent(event);
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'expert_virtual_bets',
          filter: 'status=neq.pending'
        },
        (payload) => {
          console.log('✅ Bet settled:', payload);

          // Invalidate related queries
          queryClient.invalidateQueries({ queryKey: ['live-betting-feed'] });
          queryClient.invalidateQueries({ queryKey: ['expert-bankrolls'] });

          // Emit custom event
          const event = new CustomEvent<BetSettledEvent>('bet-settled', {
            detail: {
              type: 'bet_settled',
              bet_id: (payload.new as any).bet_id,
              expert_id: (payload.new as any).expert_id,
              result: (payload.new as any).status,
              payout: (payload.new as any).actual_payout || 0,
              bankroll_update: {
                old_balance: 0,
                new_balance: 0
              }
            }
          });
          window.dispatchEvent(event);
        }
      )
      .subscribe();

    return () => {
      console.log('🔌 Cleaning up betting feed subscription');
      channel.unsubscribe();
    };
  }, [realtime, queryClient]);

  return query;
};

/**
 * Hook to fetch bet history for a specific expert
 */
export const useExpertBetHistory = (
  expertId: string,
  options: { limit?: number; result?: 'won' | 'lost' | 'push' | 'all' } = {}
) => {
  const { limit = 50, result = 'all' } = options;

  return useQuery({
    queryKey: ['expert-bet-history', expertId, limit, result],
    queryFn: async () => {
      let query = supabase
        .from('expert_virtual_bets')
        .select('*')
        .eq('expert_id', expertId)
        .neq('status', 'pending')
        .order('settled_at', { ascending: false })
        .limit(limit);

      if (result !== 'all') {
        query = query.eq('status', result);
      }

      const { data, error } = await query;
      if (error) throw error;

      return data || [];
    },
    enabled: !!expertId,
    staleTime: 60 * 1000 // 1 minute
  });
};