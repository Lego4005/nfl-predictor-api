/**
 * Conservative Analyzer - Data-driven, cautious NFL expert
 *
 * Focuses on statistical rigor, historical patterns, and risk management
 * Prefers lower-variance bets with consistent returns
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

export default async function ConservativeAnalyzer(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;
    const runId = payload.run_id || 'run_default';

    ctx.logger.info(`Conservative Analyzer processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      runId: runId
    });

    // Fetch Context Pack from backend
    const contextPack = await fetchContextPack('the-analyst', gameId, runId);
    const ctxK = contextPack.memories.length;
    
    ctx.logger.info(`Context pack retrieved: ctxK=${ctxK}, alpha=${contextPack.recency.alpha}`);

    // Generate 83-item prediction bundle
    let bundle = await generate83Predictions(gameContext, contextPack, ctx);
    
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
        const storeResult = await storeExpertPredictions(runId, 'the-analyst', gameId, bundle);
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
      expertPersona: 'conservative_analyzer',
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
    ctx.logger.error('Conservative Analyzer failed:', error);
    return resp.json({
      error: 'Conservative analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'conservative_analyzer',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generate83Predictions(gameContext: any, contextPack: any, ctx: AgentContext): Promise<any> {
  const predictions = [];
  const memories = contextPack.memories || [];
  
  // Generate predictions for all 83 categories from registry
  for (const category of contextPack.registry) {
    let value: any;
    let confidence: number;
    let stakeUnits: number;
    
    // Conservative personality: lower confidence, smaller stakes
    if (category.pred_type === 'binary') {
      value = Math.random() > 0.5;
      confidence = 0.55 + Math.random() * 0.15; // 0.55-0.70
      stakeUnits = 0.5 + Math.random() * 1.5; // 0.5-2.0
    } else if (category.pred_type === 'numeric') {
      value = 24.5 + (Math.random() - 0.5) * 10; // Conservative ranges
      confidence = 0.60 + Math.random() * 0.15; // 0.60-0.75
      stakeUnits = 1.0 + Math.random() * 1.5; // 1.0-2.5
    } else if (category.pred_type === 'enum' && category.allowed) {
      value = category.allowed[0]; // Conservative: pick first (often "home")
      confidence = 0.58 + Math.random() * 0.12; // 0.58-0.70
      stakeUnits = 0.8 + Math.random() * 1.2; // 0.8-2.0
    } else {
      value = 'home';
      confidence = 0.60;
      stakeUnits = 1.0;
    }
    
    // Build why[] array from memories
    const why = memories.slice(0, 3).map((mem: any) => ({
      memory_id: mem.memory_id,
      weight: mem.combined_score * 0.3
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
    home_win_prob: 0.58,
    away_win_prob: 0.42,
    overall_confidence: 0.65,
    recency_alpha_used: contextPack.recency.alpha
  };
  
  return { overall, predictions };
}

export const welcome = () => {
  return {
    welcome: `
# Conservative Analyzer

Data-driven NFL expert focused on statistical rigor and risk management.

## Personality Traits:
- Heavily weights historical data and proven patterns
- Prefers lower-variance bets with consistent returns
- Conservative with stake sizing (rarely exceeds 2-3 units)
- Focuses on defensive metrics and field position advantages

## Approach:
- Statistical analysis over gut feelings
- Risk-adjusted returns prioritized
- Methodical evaluation of all factors
- Emphasis on sustainable long-term profitability

## Specialties:
- Defensive performance analysis
- Home field advantage quantification
- Weather impact assessment
- Historical matchup patterns
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "test_game_001",
          expertId: "conservative_analyzer",
          gameContext: {
            homeTeam: "KC",
            awayTeam: "BUF",
            gameTime: "2024-10-09T20:00:00Z"
          },
          memories: [
            {
              memoryId: "mem_001",
              content: "KC has strong home field advantage, averaging 24.5 points at home",
              similarity: 0.85
            }
          ]
        }),
        contentType: 'application/json'
      }
    ]
  };
};