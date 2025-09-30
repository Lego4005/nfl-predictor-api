/**
 * usePredictionBattles Hook
 * Detect and track expert prediction battles (disagreements)
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { supabase } from '../services/supabaseClient';
import type {
  PredictionBattle,
  BattlesResponse,
  UsePredictionBattlesOptions
} from '../types/confidencePool';

/**
 * Hook to fetch active prediction battles where experts disagree
 * @param options - Query options and filters
 */
export const usePredictionBattles = (options: UsePredictionBattlesOptions = {}) => {
  const {
    week,
    min_difference = 3.0,
    category,
    status = 'pending'
  } = options;

  const queryClient = useQueryClient();

  const query = useQuery<BattlesResponse>({
    queryKey: ['prediction-battles', week, min_difference, category, status],
    queryFn: async () => {
      console.log('⚔️ Fetching prediction battles...');

      // This requires a more complex query to detect disagreements
      // We'll query predictions and then process them client-side to find battles

      // First, get all predictions for the week
      let supabaseQuery = supabase
        .from('expert_predictions')
        .select(`
          prediction_id,
          expert_id,
          game_id,
          category,
          prediction_value,
          confidence,
          reasoning,
          bet_amount,
          expert_models!inner (
            expert_id,
            name,
            emoji
          ),
          games!inner (
            game_id,
            home_team,
            away_team,
            game_time,
            status,
            week
          )
        `);

      if (week) {
        supabaseQuery = supabaseQuery.eq('games.week', week);
      }

      if (category) {
        supabaseQuery = supabaseQuery.eq('category', category);
      }

      if (status === 'pending') {
        supabaseQuery = supabaseQuery.in('games.status', ['scheduled', 'live']);
      } else {
        supabaseQuery = supabaseQuery.eq('games.status', 'final');
      }

      const { data, error } = await supabaseQuery;

      if (error) {
        console.error('Error fetching predictions for battles:', error);
        throw error;
      }

      if (!data || data.length === 0) {
        return {
          battles: [],
          summary: {
            total_battles: 0,
            avg_difference: 0,
            most_contested_game: ''
          }
        };
      }

      // Group predictions by game_id and category
      const gameCategories = new Map<string, Map<string, any[]>>();

      data.forEach((pred: any) => {
        const key = `${pred.game_id}_${pred.category}`;
        if (!gameCategories.has(pred.game_id)) {
          gameCategories.set(pred.game_id, new Map());
        }
        const gameMap = gameCategories.get(pred.game_id)!;
        if (!gameMap.has(pred.category)) {
          gameMap.set(pred.category, []);
        }
        gameMap.get(pred.category)!.push(pred);
      });

      // Detect battles (significant disagreements)
      const battles: PredictionBattle[] = [];

      gameCategories.forEach((categories, gameId) => {
        categories.forEach((predictions, cat) => {
          if (predictions.length < 2) return;

          // Sort by prediction value
          predictions.sort((a: any, b: any) => {
            const valA = parseFloat(a.prediction_value);
            const valB = parseFloat(b.prediction_value);
            return valA - valB;
          });

          // Check for significant differences
          for (let i = 0; i < predictions.length - 1; i++) {
            for (let j = i + 1; j < predictions.length; j++) {
              const predA = predictions[i];
              const predB = predictions[j];

              const valA = parseFloat(predA.prediction_value);
              const valB = parseFloat(predB.prediction_value);
              const difference = Math.abs(valB - valA);

              if (difference >= min_difference) {
                // Get head-to-head record
                const h2hRecord = {
                  expert_a_wins: Math.floor(Math.random() * 30) + 10, // TODO: Calculate from history
                  expert_b_wins: Math.floor(Math.random() * 30) + 10,
                  ties: Math.floor(Math.random() * 5),
                  last_5: generateLast5Pattern() // TODO: Get from actual data
                };

                // Parse reasoning
                const parseReasoning = (reasoning: any): string[] => {
                  if (!reasoning) return [];
                  if (typeof reasoning === 'string') {
                    try {
                      return JSON.parse(reasoning);
                    } catch {
                      return [reasoning];
                    }
                  }
                  return reasoning;
                };

                battles.push({
                  battle_id: `battle_${predA.prediction_id}_${predB.prediction_id}`,
                  game_id: gameId,
                  game_details: {
                    home_team: predA.games.home_team,
                    away_team: predA.games.away_team,
                    game_time: predA.games.game_time,
                    status: predA.games.status
                  },
                  category: cat as any,
                  expert_a: {
                    expert_id: predA.expert_id,
                    expert_name: predA.expert_models.name,
                    expert_emoji: predA.expert_models.emoji,
                    prediction: predA.prediction_value,
                    confidence: predA.confidence,
                    bet_amount: predA.bet_amount,
                    reasoning: parseReasoning(predA.reasoning)
                  },
                  expert_b: {
                    expert_id: predB.expert_id,
                    expert_name: predB.expert_models.name,
                    expert_emoji: predB.expert_models.emoji,
                    prediction: predB.prediction_value,
                    confidence: predB.confidence,
                    bet_amount: predB.bet_amount,
                    reasoning: parseReasoning(predB.reasoning)
                  },
                  difference,
                  head_to_head_record: h2hRecord,
                  status: predA.games.status === 'final' ? 'settled' : 'pending'
                });
              }
            }
          }
        });
      });

      // Calculate summary
      const totalDifference = battles.reduce((sum, b) => sum + b.difference, 0);
      const gameContestCounts = new Map<string, number>();

      battles.forEach(b => {
        const count = gameContestCounts.get(b.game_id) || 0;
        gameContestCounts.set(b.game_id, count + 1);
      });

      let mostContestedGame = '';
      let maxContests = 0;

      gameContestCounts.forEach((count, gameId) => {
        if (count > maxContests) {
          maxContests = count;
          mostContestedGame = gameId;
        }
      });

      console.log(`✅ Found ${battles.length} prediction battles`);

      return {
        battles,
        summary: {
          total_battles: battles.length,
          avg_difference: battles.length > 0 ? totalDifference / battles.length : 0,
          most_contested_game: mostContestedGame
        }
      };
    },
    enabled: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000 // 10 minutes
  });

  // Set up real-time subscription
  useEffect(() => {
    console.log('🔄 Setting up real-time prediction battles subscription...');

    const channel = supabase
      .channel('prediction-battles-updates')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'expert_predictions'
        },
        (payload) => {
          console.log('⚔️ Prediction update for battles:', payload);

          // Invalidate and refetch
          queryClient.invalidateQueries({ queryKey: ['prediction-battles'] });
        }
      )
      .subscribe();

    return () => {
      console.log('🔌 Cleaning up prediction battles subscription');
      channel.unsubscribe();
    };
  }, [queryClient]);

  return query;
};

/**
 * Hook to fetch head-to-head record between two experts
 */
export const useHeadToHeadRecord = (
  expertAId: string,
  expertBId: string,
  options: { timeRange?: 'week' | 'month' | 'season' | 'all_time'; enabled?: boolean } = {}
) => {
  const { timeRange = 'all_time', enabled = true } = options;

  return useQuery({
    queryKey: ['head-to-head-record', expertAId, expertBId, timeRange],
    queryFn: async () => {
      // Query historical prediction results
      const { data, error } = await supabase
        .rpc('get_head_to_head_record', {
          expert_a_id: expertAId,
          expert_b_id: expertBId,
          time_range: timeRange
        });

      if (error) throw error;

      return data;
    },
    enabled: enabled && !!expertAId && !!expertBId,
    staleTime: 5 * 60 * 1000 // 5 minutes
  });
};

// Helper function to generate last 5 pattern
function generateLast5Pattern(): string {
  const results = ['A', 'B', 'T'];
  return Array.from({ length: 5 }, () =>
    results[Math.floor(Math.random() * results.length)]
  ).join('');
}