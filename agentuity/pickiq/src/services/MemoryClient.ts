/**
 * Memory Client - Fetches Context Pack from backend
 */

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8001';

export interface Memory {
  memory_id: string;
  combined_score: number;
  similarity: number;
  recency_score: number;
  summary: string;
  outcome?: string;
  margin?: number;
}

export interface ContextPack {
  game: {
    game_id: string;
    season: number;
    week: number;
    home: string;
    away: string;
    market: {
      spread_home: number;
      total: number;
      ml_home: number;
      ml_away: number;
    };
    env: {
      roof: string;
      surface: string;
      weather: any;
    };
  };
  recency: {
    alpha: number;
  };
  memories: Memory[];
  team_knowledge: {
    home: any;
    away: any;
  };
  matchup_memory: {
    role_aware: any;
    sorted_key: string;
  };
  registry: Array<{
    id: string;
    family: string;
    pred_type: string;
    subject: string;
    allowed?: string[];
    sigma?: number;
  }>;
  run_id?: string;
}

export async function fetchContextPack(
  expertId: string,
  gameId: string,
  runId: string
): Promise<ContextPack> {
  const url = `${BACKEND_URL}/api/context/${expertId}/${gameId}?run_id=${runId}`;
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Context API returned ${response.status}: ${response.statusText}`);
    }
    
    const contextPack = await response.json() as ContextPack;
    return contextPack;
  } catch (error) {
    console.error(`Failed to fetch context pack: ${error}`);
    throw error;
  }
}

export async function storeExpertPredictions(
  runId: string,
  expertId: string,
  gameId: string,
  bundle: any,
  modelType: string = 'primary'
): Promise<{ status: string; prediction_id: string }> {
  const url = `${BACKEND_URL}/api/expert/predictions?run_id=${runId}`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: runId,
        expert_id: expertId,
        game_id: gameId,
        bundle: bundle,
        timestamp: new Date().toISOString(),
        model_type: modelType
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Predictions API returned ${response.status}: ${JSON.stringify(error)}`);
    }
    
    return await response.json() as { status: string; prediction_id: string };
  } catch (error) {
    console.error(`Failed to store predictions: ${error}`);
    throw error;
  }
}