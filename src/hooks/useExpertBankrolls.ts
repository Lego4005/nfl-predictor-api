/**
 * useExpertBankrolls Hook
 * Real-time expert bankroll tracking with Supabase queries
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { supabase } from '../services/supabaseClient';
import type {
  ExpertBankroll,
  BankrollsResponse,
  UseExpertBankrollsOptions,
  BankrollUpdateEvent
} from '../types/confidencePool';

/**
 * Hook to fetch and track expert bankrolls in real-time
 * @param options - Query options and filters
 */
export const useExpertBankrolls = (options: UseExpertBankrollsOptions = {}) => {
  const {
    refetchInterval = 30000, // 30 seconds default
    enabled = true,
    sortBy = 'balance',
    filterByStatus
  } = options;

  const queryClient = useQueryClient();

  // Query for expert bankrolls
  const query = useQuery<BankrollsResponse>({
    queryKey: ['expert-bankrolls', sortBy, filterByStatus],
    queryFn: async () => {
      console.log('🏦 Fetching expert bankrolls...');

      // Query expert_virtual_bankrolls table
      let supabaseQuery = supabase
        .from('expert_virtual_bankrolls')
        .select(`
          expert_id,
          expert_name,
          expert_emoji,
          archetype,
          current_balance,
          starting_balance,
          peak_balance,
          lowest_balance,
          total_wagered,
          total_won,
          total_lost,
          last_updated
        `);

      // Apply filters
      if (filterByStatus && filterByStatus.length > 0) {
        // Filter by status (calculated client-side from balance)
        // Will be applied after fetching
      }

      // Apply sorting
      const orderColumn = sortBy === 'balance' ? 'current_balance' :
                         sortBy === 'roi' ? 'current_balance' : // Will calculate ROI client-side
                         sortBy === 'change' ? 'current_balance' : 'current_balance';

      supabaseQuery = supabaseQuery.order(orderColumn, { ascending: false });

      const { data, error } = await supabaseQuery;

      if (error) {
        console.error('Error fetching bankrolls:', error);
        throw error;
      }

      if (!data) {
        return {
          bankrolls: [],
          summary: {
            total_eliminated: 0,
            avg_balance: 0,
            total_wagered: 0,
            most_aggressive: '',
            safest: ''
          },
          timestamp: new Date().toISOString()
        };
      }

      // Transform and enrich data
      const bankrolls: ExpertBankroll[] = data.map(row => {
        const change_amount = row.current_balance - row.starting_balance;
        const change_percent = (change_amount / row.starting_balance) * 100;
        const roi = row.total_wagered > 0 ?
          ((row.total_won - row.total_lost) / row.total_wagered) * 100 : 0;

        // Determine status
        let status: ExpertBankroll['status'];
        if (row.current_balance <= 0) {
          status = 'eliminated';
        } else if (row.current_balance < row.starting_balance * 0.3) {
          status = 'danger';
        } else if (row.current_balance < row.starting_balance * 0.7) {
          status = 'warning';
        } else {
          status = 'safe';
        }

        // Determine risk level based on betting patterns
        const avgBetSize = row.total_wagered > 0 ?
          row.total_wagered / ((row.total_won + row.total_lost) / 2 || 1) : 0;
        const bankrollPercent = (avgBetSize / row.current_balance) * 100;

        let risk_level: ExpertBankroll['risk_level'];
        if (bankrollPercent > 40) {
          risk_level = 'extreme';
        } else if (bankrollPercent > 20) {
          risk_level = 'aggressive';
        } else if (bankrollPercent > 10) {
          risk_level = 'moderate';
        } else {
          risk_level = 'conservative';
        }

        return {
          expert_id: row.expert_id,
          expert_name: row.expert_name,
          expert_emoji: row.expert_emoji,
          archetype: row.archetype,
          current_balance: row.current_balance,
          starting_balance: row.starting_balance,
          peak_balance: row.peak_balance,
          lowest_balance: row.lowest_balance,
          total_wagered: row.total_wagered,
          total_won: row.total_won,
          total_lost: row.total_lost,
          change_percent,
          change_amount,
          status,
          risk_level,
          last_updated: row.last_updated
        };
      });

      // Apply status filter if provided
      let filteredBankrolls = bankrolls;
      if (filterByStatus && filterByStatus.length > 0) {
        filteredBankrolls = bankrolls.filter(b => filterByStatus.includes(b.status));
      }

      // Apply sorting
      if (sortBy === 'roi') {
        filteredBankrolls.sort((a, b) => {
          const roiA = a.total_wagered > 0 ? ((a.total_won - a.total_lost) / a.total_wagered) : 0;
          const roiB = b.total_wagered > 0 ? ((b.total_won - b.total_lost) / b.total_wagered) : 0;
          return roiB - roiA;
        });
      } else if (sortBy === 'risk') {
        const riskOrder = { extreme: 0, aggressive: 1, moderate: 2, conservative: 3 };
        filteredBankrolls.sort((a, b) => riskOrder[a.risk_level] - riskOrder[b.risk_level]);
      } else if (sortBy === 'change') {
        filteredBankrolls.sort((a, b) => b.change_percent - a.change_percent);
      }

      // Calculate summary statistics
      const summary = {
        total_eliminated: bankrolls.filter(b => b.status === 'eliminated').length,
        avg_balance: bankrolls.reduce((sum, b) => sum + b.current_balance, 0) / bankrolls.length,
        total_wagered: bankrolls.reduce((sum, b) => sum + b.total_wagered, 0),
        most_aggressive: filteredBankrolls.find(b => b.risk_level === 'extreme')?.expert_name || '',
        safest: filteredBankrolls.find(b => b.risk_level === 'conservative')?.expert_name || ''
      };

      console.log(`✅ Fetched ${filteredBankrolls.length} expert bankrolls`);

      return {
        bankrolls: filteredBankrolls,
        summary,
        timestamp: new Date().toISOString()
      };
    },
    enabled,
    staleTime: refetchInterval / 2,
    gcTime: refetchInterval * 2,
    refetchInterval
  });

  // Set up real-time subscription for bankroll updates
  useEffect(() => {
    if (!enabled) return;

    console.log('🔄 Setting up real-time bankroll subscription...');

    const channel = supabase
      .channel('expert-bankrolls-updates')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'expert_virtual_bankrolls'
        },
        (payload) => {
          console.log('💰 Bankroll update received:', payload);

          // Invalidate and refetch on any change
          queryClient.invalidateQueries({ queryKey: ['expert-bankrolls'] });

          // Optionally emit custom event for toast notifications
          if (payload.eventType === 'UPDATE') {
            const event = new CustomEvent('bankroll-updated', {
              detail: payload.new
            });
            window.dispatchEvent(event);
          }
        }
      )
      .subscribe();

    return () => {
      console.log('🔌 Cleaning up bankroll subscription');
      channel.unsubscribe();
    };
  }, [enabled, queryClient]);

  return query;
};

/**
 * Hook to fetch bankroll history for a specific expert
 */
export const useExpertBankrollHistory = (
  expertId: string,
  options: { enabled?: boolean; limit?: number } = {}
) => {
  const { enabled = true, limit = 50 } = options;

  return useQuery({
    queryKey: ['expert-bankroll-history', expertId, limit],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('expert_bankroll_history')
        .select('*')
        .eq('expert_id', expertId)
        .order('timestamp', { ascending: false })
        .limit(limit);

      if (error) throw error;

      return data || [];
    },
    enabled: enabled && !!expertId,
    staleTime: 5 * 60 * 1000 // 5 minutes
  });
};

/**
 * Hook to fetch risk metrics for an expert
 */
export const useExpertRiskMetrics = (
  expertId: string,
  options: { enabled?: boolean } = {}
) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['expert-risk-metrics', expertId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('expert_risk_metrics')
        .select('*')
        .eq('expert_id', expertId)
        .single();

      if (error) throw error;

      return data;
    },
    enabled: enabled && !!expertId,
    staleTime: 2 * 60 * 1000 // 2 minutes
  });
};