/**
 * Agentuity GameOrchestrator Agent
 *
 * Orchestrates parallel expert prediction generation while keeping hot path in Postgres/pgvector
 * This agent coordinates but does not store operational state
 */

import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";

interface OrchestrationPayload {
  game_id: string;
  expert_ids: string[];
  api_base_url: string;
  enable_shadow_runs: boolean;
  shadow_models: Record<string, string>;
  orchestration_id: string;
}

interface ExpertResult {
  expert_id: string;
  success: boolean;
  duration_ms: number;
  schema_valid: boolean;
  error?: string;
  shadow_result?: any;
  retrieval_ms?: number;
  llm_ms?: number;
  validation_ms?: number;
}

export default async function GameOrchestrator(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as OrchestrationPayload;
    const { game_id, expert_ids, api_base_url, enable_shadow_runs, shadow_models, orchestration_id } = payload;

    ctx.logger.info(`Starting orchestration ${orchestration_id} for game ${game_id} with ${expert_ids.length} experts`);

    // Process experts in parallel
    const expertPromises = expert_ids.map(expert_id =>
      processExpert(expert_id, game_id, api_base_url, enable_shadow_runs, shadow_models[expert_id], ctx)
    );

    const expertResults = await Promise.allSettled(expertPromises);

    // Aggregate results
    const results: ExpertResult[] = [];
    let totalRetrievalMs = 0;
    let totalLlmMs = 0;
    let totalValidationMs = 0;
    let schemaValidCount = 0;

    expertResults.forEach((result, index) => {
      const expert_id = expert_ids[index];

      if (result.status === 'fulfilled') {
        results.push(result.value);
        totalRetrievalMs += result.value.retrieval_ms || 0;
        totalLlmMs += result.value.llm_ms || 0;
        totalValidationMs += result.value.validation_ms || 0;
        if (result.value.schema_valid) schemaValidCount++;
      } else {
        results.push({
          expert_id: expert_ids[index] || 'unknown',
          success: false,
          duration_ms: 0,
          schema_valid: false,
          error: result.reason?.message || 'Unknown error'
        });
        ctx.logger.error(`Expert ${expert_ids[index]} failed: ${result.reason}`);
      }
    });

    const totalDuration = Date.now() - startTime;
    const schemaComplianceRate = expert_ids.length > 0 ? schemaValidCount / expert_ids.length : 0;

    // Log telemetry
    ctx.logger.info(`Orchestration completed in ${totalDuration}ms`, {
      game_id,
      experts_processed: results.filter(r => r.success).length,
      experts_failed: results.filter(r => !r.success).length,
      schema_compliance_rate: schemaComplianceRate,
      avg_retrieval_ms: totalRetrievalMs / expert_ids.length,
      avg_llm_ms: totalLlmMs / expert_ids.length,
      avg_validation_ms: totalValidationMs / expert_ids.length
    });

    return resp.json({
      orchestration_id,
      game_id,
      experts_processed: results.filter(r => r.success).map(r => r.expert_id),
      experts_failed: results.filter(r => !r.success).map(r => r.expert_id),
      total_duration_ms: totalDuration,
      retrieval_duration_ms: totalRetrievalMs,
      llm_duration_ms: totalLlmMs,
      validation_duration_ms: totalValidationMs,
      schema_compliance_rate: schemaComplianceRate,
      shadow_results: enable_shadow_runs ? results.filter(r => r.shadow_result).map(r => ({
        expert_id: r.expert_id,
        shadow_result: r.shadow_result
      })) : null,
      expert_details: results
    });

  } catch (error) {
    ctx.logger.error('Orchestration failed:', error);
    return resp.json({
      error: 'Orchestration failed',
      message: error instanceof Error ? error.message : String(error),
      duration_ms: Date.now() - startTime
    }, { status: 500 });
  }
}

async function processExpert(
  expert_id: string,
  game_id: string,
  api_base_url: string,
  enable_shadow_runs: boolean,
  shadow_model: string | undefined,
  ctx: AgentContext
): Promise<ExpertResult> {
  const expertStartTime = Date.now();

  try {
    // Step 1: Get memory context from our API
    const contextResponse = await fetch(`${api_base_url}/context/${expert_id}/${game_id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!contextResponse.ok) {
      throw new Error(`Context fetch failed: ${contextResponse.status}`);
    }

    const contextData = await contextResponse.json();
    const retrievalMs = Date.now() - expertStartTime;

    // Step 2: Generate predictions via single LLM call
    const llmStartTime = Date.now();

    // Main prediction call
    const predictionPromise = generateExpertPredictions(expert_id, contextData, ctx);

    // Shadow run (if enabled)
    const shadowPromise = enable_shadow_runs && shadow_model
      ? generateShadowPredictions(expert_id, contextData, shadow_model, ctx)
      : Promise.resolve(null);

    const [predictions, shadowResult] = await Promise.all([predictionPromise, shadowPromise]);

    const llmMs = Date.now() - llmStartTime;

    // Step 3: Validate and store predictions
    const validationStartTime = Date.now();

    const storeResponse = await fetch(`${api_base_url}/expert/predictions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        expert_id,
        game_id,
        predictions,
        orchestration_metadata: {
          retrieval_ms: retrievalMs,
          llm_ms: llmMs,
          shadow_model: shadow_model || null
        }
      })
    });

    const validationMs = Date.now() - validationStartTime;

    if (!storeResponse.ok) {
      throw new Error(`Prediction storage failed: ${storeResponse.status}`);
    }

    const storeResult = await storeResponse.json() as any;

    return {
      expert_id,
      success: true,
      duration_ms: Date.now() - expertStartTime,
      schema_valid: storeResult.schema_valid || false,
      retrieval_ms: retrievalMs,
      llm_ms: llmMs,
      validation_ms: validationMs,
      shadow_result: shadowResult
    };

  } catch (error) {
    ctx.logger.error(`Expert ${expert_id} processing failed:`, error);
    return {
      expert_id,
      success: false,
      duration_ms: Date.now() - expertStartTime,
      schema_valid: false,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

async function generateExpertPredictions(
  expert_id: string,
  contextData: any,
  ctx: AgentContext
): Promise<any> {
  // Route to appropriate expert agent based on personality
  let expertAgent;

  switch (expert_id) {
    case 'conservative_analyzer':
      expertAgent = new ConservativeAnalyzerAgent();
      break;
    case 'momentum_rider':
      expertAgent = new MomentumRiderAgent();
      break;
    case 'contrarian_rebel':
      expertAgent = new ContrarianRebelAgent();
      break;
    case 'value_hunter':
      expertAgent = new ValueHunterAgent();
      break;
    default:
      throw new Error(`Unknown expert: ${expert_id}`);
  }

  // Execute expert agent with context data
  const result = await expertAgent.execute(contextData);

  ctx.logger.info(`Expert ${expert_id} completed in ${result.processingTimeMs}ms with mode: ${result.reasoningMode}`);

  return result;
}

async function generateShadowPredictions(
  expert_id: string,
  contextData: any,
  shadow_model: string,
  ctx: AgentContext
): Promise<any> {
  // Shadow run with alternate model - results stored separately
  ctx.logger.info(`Running shadow model ${shadow_model} for expert ${expert_id}`);

  // TODO: Implement shadow model call
  return {
    shadow_model,
    predictions: [], // Shadow predictions
    comparison_metrics: {}
  };
}

// Import expert agents at the top
import ConservativeAnalyzerAgent from '../conservative-analyzer';
import MomentumRiderAgent from '../momentum-rider';
import ContrarianRebelAgent from '../contrarian-rebel';
import ValueHunterAgent from '../value-hunter';

export const welcome = () => {
  return {
    welcome: `
# GameOrchestrator Agent

This agent orchestrates parallel expert prediction generation for NFL games.

## Features:
- Parallel expert processing
- Memory context retrieval
- Schema validation
- Shadow model support
- Comprehensive telemetry

## Usage:
Send a JSON payload with game_id, expert_ids, and configuration options.
    `,
    prompts: [
      {
        data: JSON.stringify({
          game_id: "game_123",
          expert_ids: ["conservative_analyzer", "risk_taking_gambler"],
          api_base_url: "http://localhost:8000/api",
          enable_shadow_runs: false,
          shadow_models: {},
          orchestration_id: "test_orch_001"
        }),
        contentType: 'application/json'
      }
    ]
  };
};
