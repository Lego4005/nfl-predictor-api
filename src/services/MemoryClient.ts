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
    game: any;
    recency: { alpha: number };
    memories: Memory[];
    team_knowledge: any;
    matchup_memory: any;
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
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Context API error: ${response.status}`);
    return await response.json() as ContextPack;
  }

  export async function storeExpertPredictions(
    runId: string,
    expertId: string,
    gameId: string,
    bundle: any,
    modelType: string = 'primary'
  ): Promise<{ status: string; prediction_id: string }> {
    const url = `${BACKEND_URL}/api/expert/predictions?run_id=${runId}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId, expert_id: expertId, game_id: gameId, bundle, timestamp: new Date().toISOString(), model_type: modelType })
    });
    if (!response.ok) throw new Error(`Predictions API error: ${response.status}`);
    return await response.json() as { status: string; prediction_id: string };
  }
Learn more
Unhandled exception
relative URL without a base
