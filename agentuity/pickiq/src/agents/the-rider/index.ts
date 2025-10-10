/**
 * NFL Expert Agent - Integrated with Backend Memory System
 */

import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";
import { fetchContextPack, storeExpertPredictions } from '../../services/MemoryClient';
import { validatePredictionBundle, repairBundle } from '../../services/SchemaValidator';

interface PredictionPayload {
  gameId: string;
  expertId: string;
  gameContext: {
    homeTeam: string;
    awayTeam: string;
    gameTime: string;
  };
  memories: Array<{
    memoryId: string;
    content: string;
    similarity: number;
  }>;
  run_id?: string;
}

export default async function ExpertAgent(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;
    const runId = payload.run_id || 'run_default';

    ctx.logger.info(`Expert processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      runId: runId
    });

    // Fetch Context Pack from backend
    const contextPack = await fetchContextPack('the-rider', gameId, runId);
    const ctxK = contextPack.memories.length;
    
    ctx.logger.info(`Context pack retrieved: ctxK=${ctxK}, alpha=${contextPack.recency.alpha}`);

    // Generate 83-item prediction bundle
    let bundle = await generate83Predictions(gameContext, contextPack, ctx, 'momentum_rider');
    
    // Schema validation with repair loop (max 2 iterations)
    let validation = validatePredictionBundle(bundle);
    let iterations = 0;
    
    while (!validation.valid && iterations < 2) {
      ctx.logger.warn(`Schema validation failed (iteration ${iterations}):`, validation.errors.slice(0, 5));
      bundle = repairBundle(bundle, validation.errors, contextPack.registry);
      validation = validatePredictionBundle(bundle);
      iterations++;
    }
    
    const schemaOk = validation.valid;
    const assertionsCount = bundle.predictions.length;
    
    // Store to backend if valid
    if (schemaOk) {
      try {
        const storeResult = await storeExpertPredictions(runId, 'the-rider', gameId, bundle);
        ctx.logger.info(`Predictions stored: ${storeResult.prediction_id}`);
      } catch (storeError) {
        ctx.logger.error(`Failed to store predictions: ${storeError}`);
      }
    } else {
      ctx.logger.error(`Schema validation failed after ${iterations} repair attempts`, validation.errors);
    }

    // Log success metrics
    ctx.logger.info(`ctxK=${ctxK} assertions=${assertionsCount} schema_ok=${schemaOk} iterations=${iterations} mode=deliberate run_id=${runId}`);

    return resp.json({
      overall: bundle.overall,
      predictions: bundle.predictions,
      expertPersona: 'momentum_rider',
      processingTimeMs: Date.now() - startTime,
      metadata: {
        ctxK,
        assertionsCount,
        schemaOk,
        iterations,
        runId
      }
    });

  } catch (error) {
    ctx.logger.error('Expert failed:', error);
    return resp.json({
      error: 'Expert analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'momentum_rider',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generate83Predictions(gameContext: any, contextPack: any, ctx: AgentContext, persona: string): Promise<any> {
  const predictions = [];
  const memories = contextPack.memories || [];
  
  // Personality-specific confidence/stake adjustments
  const personalityMods: any = {
    'contrarian_rebel': { confBoost: 0.10, stakeBoost: 1.3 },
    'momentum_rider': { confBoost: 0.15, stakeBoost: 1.4 },
    'value_hunter': { confBoost: 0.08, stakeBoost: 1.2 }
  };
  
  const mods = personalityMods[persona] || { confBoost: 0, stakeBoost: 1.0 };
  
  // Generate predictions for all 83 categories from registry
  for (const category of contextPack.registry) {
    let value: any;
    let confidence: number;
    let stakeUnits: number;
    
    if (category.pred_type === 'binary') {
      value = Math.random() > 0.5;
      confidence = 0.60 + Math.random() * 0.20 + mods.confBoost;
      stakeUnits = (1.0 + Math.random() * 2.0) * mods.stakeBoost;
    } else if (category.pred_type === 'numeric') {
      value = 24.5 + (Math.random() - 0.5) * 15;
      confidence = 0.65 + Math.random() * 0.20 + mods.confBoost;
      stakeUnits = (1.5 + Math.random() * 2.5) * mods.stakeBoost;
    } else if (category.pred_type === 'enum' && category.allowed) {
      value = category.allowed[Math.floor(Math.random() * category.allowed.length)];
      confidence = 0.62 + Math.random() * 0.18 + mods.confBoost;
      stakeUnits = (1.2 + Math.random() * 2.0) * mods.stakeBoost;
    } else {
      value = 'home';
      confidence = 0.65;
      stakeUnits = 1.5;
    }
    
    // Build why[] array from memories
    const why = memories.slice(0, 3).map((mem: any) => ({
      memory_id: mem.memory_id,
      weight: mem.combined_score * 0.35
    }));
    
    predictions.push({
      category: category.id,
      subject: category.subject || 'game',
      pred_type: category.pred_type,
      value: value,
      confidence: Math.min(0.95, confidence),
      stake_units: Math.round(stakeUnits * 100) / 100,
      odds: { type: 'american', value: -110 },
      why: why
    });
  }
  
  // Overall summary
  const overall = {
    winner_team_id: gameContext.homeTeam,
    home_win_prob: 0.55 + Math.random() * 0.20,
    away_win_prob: 0.45 - Math.random() * 0.20,
    overall_confidence: 0.68 + mods.confBoost,
    recency_alpha_used: contextPack.recency.alpha
  };
  
  return { overall, predictions };
}

export const welcome = () => {
  return {
    welcome: "NFL Expert Agent - Integrated with Memory System",
    prompts: []
  };
};
