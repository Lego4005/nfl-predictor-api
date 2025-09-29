import { useQuery } from "@tanstack/react-query";
import { supabase } from "../services/supabaseClient";

/**
 * Custom hook to fetch game details by ID
 * Handles both primary key 'id' and 'espn_game_id' columns
 */
export const useGameDetail = (gameId: string) => {
  return useQuery({
    queryKey: ["game-detail", gameId],
    queryFn: async () => {
      console.log("🔍 Fetching game with ID:", gameId);

      // First try to find by primary key 'id'
      let { data, error } = await supabase
        .from("games")
        .select("*")
        .eq("id", gameId)
        .single();

      if (error && error.code === "PGRST116") {
        // No rows found, try by game_id column
        console.log("🔄 Trying to find by game_id column...");
        const result = await supabase
          .from("games")
          .select("*")
          .eq("game_id", gameId)
          .single();

        data = result.data;
        error = result.error;
      }

      if (error && error.code === "PGRST116") {
        // Still no rows found, try by espn_game_id column
        console.log("🔄 Trying to find by espn_game_id column...");
        const result = await supabase
          .from("games")
          .select("*")
          .eq("espn_game_id", gameId)
          .single();

        data = result.data;
        error = result.error;
      }

      if (error) {
        console.error("❌ Game fetch error:", error);
        throw new Error(`Game not found: ${error.message}`);
      }

      console.log("✅ Game found:", data);
      return data;
    },
    enabled: !!gameId,
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
};
