/**
 * useExpertMemories Hook
 * Fetch expert episodic memories for Memory Lane feature
 */

import { useQuery, useQueryClient } from '@tantml:react-query';
import { useEffect } from 'react';
import { supabase } from '../services/supabaseClient';
import type {
  ExpertMemory,
  MemoriesResponse,
  UseExpertMemoriesOptions,
  MemoryLaneFilters
} from '../types/confidencePool';

/**
 * Hook to fetch expert memories with filtering and pagination
 * @param options - Query options and filters
 */
export const useExpertMemories = (options: UseExpertMemoriesOptions = {}) => {
  const {
    expert_id,
    limit = 20,
    offset = 0,
    filters = {}
  } = options;

  const queryClient = useQueryClient();

  const query = useQuery<MemoriesResponse>({
    queryKey: ['expert-memories', expert_id, limit, offset, filters],
    queryFn: async () => {
      console.log('🧠 Fetching expert memories...');

      // Query expert_episodic_memories table
      let supabaseQuery = supabase
        .from('expert_episodic_memories')
        .select(`
          memory_id,
          expert_id,
          game_id,
          memory_type,
          content,
          emotional_valence,
          importance_score,
          recalled_count,
          created_at,
          last_recalled,
          tags,
          games (
            game_id,
            home_team,
            away_team,
            game_time,
            home_score,
            away_score,
            status
          )
        `, { count: 'exact' });

      // Apply filters
      if (expert_id) {
        supabaseQuery = supabaseQuery.eq('expert_id', expert_id);
      }

      if (filters.memory_type) {
        supabaseQuery = supabaseQuery.eq('memory_type', filters.memory_type);
      }

      if (filters.min_importance !== undefined) {
        supabaseQuery = supabaseQuery.gte('importance_score', filters.min_importance);
      }

      if (filters.emotional_filter && filters.emotional_filter !== 'all') {
        if (filters.emotional_filter === 'positive') {
          supabaseQuery = supabaseQuery.gt('emotional_valence', 0.2);
        } else if (filters.emotional_filter === 'negative') {
          supabaseQuery = supabaseQuery.lt('emotional_valence', -0.2);
        } else if (filters.emotional_filter === 'neutral') {
          supabaseQuery = supabaseQuery
            .gte('emotional_valence', -0.2)
            .lte('emotional_valence', 0.2);
        }
      }

      if (filters.time_range && filters.time_range !== 'all_time') {
        const now = new Date();
        let startDate: Date;

        switch (filters.time_range) {
          case 'week':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            break;
          case 'month':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            break;
          case 'season':
            startDate = new Date(now.getFullYear(), 8, 1); // Sept 1st
            break;
          default:
            startDate = new Date(0);
        }

        supabaseQuery = supabaseQuery.gte('created_at', startDate.toISOString());
      }

      // Order by importance and recency
      supabaseQuery = supabaseQuery
        .order('importance_score', { ascending: false })
        .order('created_at', { ascending: false })
        .range(offset, offset + limit - 1);

      const { data, error, count } = await supabaseQuery;

      if (error) {
        console.error('Error fetching expert memories:', error);
        throw error;
      }

      if (!data || data.length === 0) {
        return {
          memories: [],
          total_count: 0,
          pagination: {
            offset,
            limit,
            has_more: false
          }
        };
      }

      // Transform to ExpertMemory format
      const memories: ExpertMemory[] = data.map((row: any) => {
        // Parse tags if it's JSON
        let tags: string[] = [];
        if (row.tags) {
          if (typeof row.tags === 'string') {
            try {
              tags = JSON.parse(row.tags);
            } catch {
              tags = [row.tags];
            }
          } else if (Array.isArray(row.tags)) {
            tags = row.tags;
          }
        }

        // Format game details
        const gameData = row.games;
        let game_details = {
          teams: 'Unknown matchup',
          date: row.created_at,
          outcome: 'Unknown'
        };

        if (gameData) {
          game_details = {
            teams: `${gameData.away_team} @ ${gameData.home_team}`,
            date: gameData.game_time,
            outcome: gameData.status === 'final' ?
              `${gameData.away_team} ${gameData.away_score} - ${gameData.home_score} ${gameData.home_team}` :
              gameData.status
          };
        }

        return {
          memory_id: row.memory_id,
          expert_id: row.expert_id,
          game_id: row.game_id,
          game_details,
          memory_type: row.memory_type,
          content: row.content,
          emotional_valence: row.emotional_valence,
          importance_score: row.importance_score,
          recalled_count: row.recalled_count,
          created_at: row.created_at,
          last_recalled: row.last_recalled,
          tags
        };
      });

      console.log(`✅ Fetched ${memories.length} expert memories`);

      return {
        memories,
        total_count: count || memories.length,
        pagination: {
          offset,
          limit,
          has_more: (count || 0) > offset + limit
        }
      };
    },
    enabled: true,
    staleTime: 5 * 60 * 1000, // 5 minutes (memories don't change often)
    gcTime: 15 * 60 * 1000 // 15 minutes
  });

  return query;
};

/**
 * Hook to fetch a specific memory by ID
 */
export const useExpertMemory = (
  memoryId: string,
  options: { enabled?: boolean } = {}
) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['expert-memory', memoryId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('expert_episodic_memories')
        .select(`
          *,
          games (*)
        `)
        .eq('memory_id', memoryId)
        .single();

      if (error) throw error;

      return data;
    },
    enabled: enabled && !!memoryId,
    staleTime: 10 * 60 * 1000 // 10 minutes
  });
};

/**
 * Hook to fetch memory statistics for an expert
 */
export const useExpertMemoryStats = (
  expertId: string,
  options: { enabled?: boolean } = {}
) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['expert-memory-stats', expertId],
    queryFn: async () => {
      // Aggregate memory statistics
      const { data, error } = await supabase
        .rpc('get_expert_memory_stats', { expert_id_param: expertId });

      if (error) throw error;

      return data;
    },
    enabled: enabled && !!expertId,
    staleTime: 5 * 60 * 1000 // 5 minutes
  });
};

/**
 * Hook to fetch most impactful memories across all experts
 */
export const useTopMemories = (options: { limit?: number } = {}) => {
  const { limit = 10 } = options;

  return useQuery({
    queryKey: ['top-memories', limit],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('expert_episodic_memories')
        .select(`
          *,
          expert_models (name, emoji),
          games (home_team, away_team)
        `)
        .order('importance_score', { ascending: false })
        .order('recalled_count', { ascending: false })
        .limit(limit);

      if (error) throw error;

      return data || [];
    },
    staleTime: 10 * 60 * 1000 // 10 minutes
  });
};