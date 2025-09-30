/**
 * useCouncilPredictions Hook
 * Fetch AI Council predictions with weighted voting and consensus
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { supabase } from '../services/supabaseClient';
import type {
  CouncilPrediction,
  CouncilPredictionsResponse,
  UseCouncilPredictionsOptions,
  WeeklyCouncilData
} from '../types/confidencePool';

/**
 * Hook to fetch current week's council predictions
 * @param options - Query options and filters
 */
export const useCouncilPredictions = (options: UseCouncilPredictionsOptions = {}) => {
  const {
    week,
    season = 2025,
    expert_id,
    min_confidence = 0.5
  } = options;

  const queryClient = useQueryClient();

  const query = useQuery<CouncilPredictionsResponse>({
    queryKey: ['council-predictions', week, season, expert_id, min_confidence],
    queryFn: async () => {
      console.log('🏛️ Fetching council predictions...');

      // Query expert_predictions_comprehensive view
      let supabaseQuery = supabase
        .from('expert_predictions_comprehensive')
        .select(`
          expert_id,
          expert_name,
          expert_emoji,
          archetype,
          accuracy_overall,
          accuracy_recent,
          council_position,
          vote_weight,
          game_id,
          home_team,
          away_team,
          game_time,
          week,
          season,
          prediction_team,
          prediction_confidence,
          confidence_rank,
          reasoning,
          vote_components
        `);

      // Apply filters
      if (week) {
        supabaseQuery = supabaseQuery.eq('week', week);
      }

      supabaseQuery = supabaseQuery
        .eq('season', season)
        .gte('prediction_confidence', min_confidence)
        .not('council_position', 'is', null); // Only council members

      if (expert_id) {
        supabaseQuery = supabaseQuery.eq('expert_id', expert_id);
      }

      // Order by council position and confidence rank
      supabaseQuery = supabaseQuery.order('council_position', { ascending: true });

      const { data, error } = await supabaseQuery;

      if (error) {
        console.error('Error fetching council predictions:', error);
        throw error;
      }

      if (!data || data.length === 0) {
        return {
          predictions: [],
          weekly_data: {
            week: week || 1,
            season,
            council_members: [],
            total_predictions: 0,
            consensus_quality: 0
          },
          timestamp: new Date().toISOString()
        };
      }

      // Transform to CouncilPrediction format
      const predictions: CouncilPrediction[] = data.map((row: any) => {
        // Parse reasoning if it's JSON
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

        // Parse vote components
        let vote_components = {
          accuracy: 0,
          recent_performance: 0,
          confidence: 0,
          specialization: 0
        };

        if (row.vote_components) {
          if (typeof row.vote_components === 'string') {
            try {
              vote_components = JSON.parse(row.vote_components);
            } catch {
              // Use defaults
            }
          } else if (typeof row.vote_components === 'object') {
            vote_components = row.vote_components;
          }
        }

        return {
          expert_id: row.expert_id,
          expert_name: row.expert_name,
          expert_emoji: row.expert_emoji,
          archetype: row.archetype,
          accuracy_overall: row.accuracy_overall,
          accuracy_recent: row.accuracy_recent,
          council_position: row.council_position,
          vote_weight: row.vote_weight,
          game_id: row.game_id,
          game_details: {
            home_team: row.home_team,
            away_team: row.away_team,
            game_time: row.game_time,
            week: row.week
          },
          prediction: {
            team: row.prediction_team,
            team_name: row.prediction_team, // Could be enhanced with full name lookup
            confidence: row.prediction_confidence,
            confidence_rank: row.confidence_rank,
            reasoning
          },
          vote_components
        };
      });

      // Get unique council members
      const councilMembers = new Map();
      predictions.forEach(p => {
        if (!councilMembers.has(p.expert_id)) {
          councilMembers.set(p.expert_id, {
            expert_id: p.expert_id,
            rank: p.council_position,
            selection_score: p.vote_weight,
            reason_selected: `${(p.accuracy_overall * 100).toFixed(1)}% accuracy, ${p.archetype}`
          });
        }
      });

      // Calculate consensus quality (how much agreement exists)
      const gameGroups = new Map<string, CouncilPrediction[]>();
      predictions.forEach(p => {
        if (!gameGroups.has(p.game_id)) {
          gameGroups.set(p.game_id, []);
        }
        gameGroups.get(p.game_id)!.push(p);
      });

      let totalAgreement = 0;
      let gameCount = 0;

      gameGroups.forEach(gamePredictions => {
        // Group by predicted team
        const teamVotes = new Map<string, number>();
        gamePredictions.forEach(p => {
          const team = p.prediction.team;
          const currentVotes = teamVotes.get(team) || 0;
          teamVotes.set(team, currentVotes + p.vote_weight);
        });

        // Find max votes
        const maxVotes = Math.max(...Array.from(teamVotes.values()));
        const totalVotes = Array.from(teamVotes.values()).reduce((sum, v) => sum + v, 0);
        const agreement = totalVotes > 0 ? maxVotes / totalVotes : 0;

        totalAgreement += agreement;
        gameCount++;
      });

      const consensus_quality = gameCount > 0 ? totalAgreement / gameCount : 0;

      const weekly_data: WeeklyCouncilData = {
        week: week || predictions[0]?.game_details.week || 1,
        season,
        council_members: Array.from(councilMembers.values()),
        total_predictions: predictions.length,
        consensus_quality
      };

      console.log(`✅ Fetched ${predictions.length} council predictions`);

      return {
        predictions,
        weekly_data,
        timestamp: new Date().toISOString()
      };
    },
    enabled: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 30 * 1000 // Refetch every 30 seconds
  });

  // Set up real-time subscription for prediction updates
  useEffect(() => {
    console.log('🔄 Setting up real-time council predictions subscription...');

    const channel = supabase
      .channel('council-predictions-updates')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'expert_predictions'
        },
        (payload) => {
          console.log('🏛️ Council prediction update:', payload);

          // Invalidate and refetch
          queryClient.invalidateQueries({ queryKey: ['council-predictions'] });
        }
      )
      .subscribe();

    return () => {
      console.log('🔌 Cleaning up council predictions subscription');
      channel.unsubscribe();
    };
  }, [queryClient]);

  return query;
};

/**
 * Hook to fetch consensus for a specific game
 */
export const useGameConsensus = (gameId: string, options: { enabled?: boolean } = {}) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['game-consensus', gameId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('council_consensus')
        .select('*')
        .eq('game_id', gameId)
        .single();

      if (error && error.code !== 'PGRST116') { // Not found is ok
        throw error;
      }

      return data;
    },
    enabled: enabled && !!gameId,
    staleTime: 60 * 1000 // 1 minute
  });
};

/**
 * Hook to fetch top 5 council members for current week
 */
export const useTopCouncilMembers = (week?: number) => {
  return useQuery({
    queryKey: ['top-council-members', week],
    queryFn: async () => {
      let query = supabase
        .from('expert_council_rankings')
        .select('*')
        .order('rank', { ascending: true })
        .limit(5);

      if (week) {
        query = query.eq('week', week);
      }

      const { data, error } = await query;
      if (error) throw error;

      return data || [];
    },
    staleTime: 5 * 60 * 1000 // 5 minutes (council changes weekly)
  });
};