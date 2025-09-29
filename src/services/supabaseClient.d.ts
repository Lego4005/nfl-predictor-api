import type { SupabaseClient } from "@supabase/supabase-js";

export declare const supabase: SupabaseClient;

export declare const supabaseHelpers: {
  getCurrentGames(): Promise<any[]>;
  mapESPNStatus(status: any): string;
  getLiveGames(): Promise<any[]>;
  getGameWithPredictions(gameId: string): Promise<any>;
  getGameOdds(gameId: string): Promise<any[]>;
  subscribeToGames(callback: (payload: any) => void): any;
  subscribeToPredictions(callback: (payload: any) => void): any;
  subscribeToOdds(callback: (payload: any) => void): any;
  saveUserPick(pick: any): Promise<any>;
  getUserStats(userId: string): Promise<any>;
  getTeamSentiment(teams: string[]): Promise<any[]>;
  getModelPerformance(): Promise<any[]>;
};

export default supabase;
