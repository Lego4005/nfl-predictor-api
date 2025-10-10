/**
 * Game Orchestrator - Coordinates multiple expert agents
 *
 * Orchestrates the 4-expert pilot system for NFL game predictions
 * Manages expert invocation and result aggregation
 */

import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";

interface OrchestrationPayload {
  game_id: string;
  expert_ids: string[];
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
  run_id: string;
}

interface ExpertResult {
  expertId: string;
  predictions: Array<{
    category: string;
    value: boolean | string | number;
    confidence: number;
    stakeUnits: number;
  }>;
  expertPersona: string;
  processingTimeMs: number;
  success: boolean;
  error?: string;
}

interface OrchestrationResult {
  game_id: string;
  run_id: string;
  expert_results: ExpertResult[];
  orchestration_summary: {
    total_experts: number;
    successful_experts: number;
    failed_experts: number;
    total_predictions: number;
    avg_confidence: number;
    total_stake_units: number;
  };
  processingTimeMs: number;
}

async function GameOrchestrator(
  request: AgentRequest,
  response: AgentResponse,
  context: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await request.data.json() as unknown as OrchestrationPayload;
    const { game_id, expert_ids, gameContext, memories, run_id } = payload;

    context.logger.info(`Game Orchestrator processing game ${game_id}`, {
      expertCount: expert_ids.length,
      experts: expert_ids,
      runId: run_id,
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam
    });

    // Orchestrate expert predictions
    const expertResults = await orchestrateExperts(
      game_id,
      expert_ids,
      gameContext,
      memories,
      context
    );

    // Generate orchestration summary
    const summary = generateOrchestrationSummary(expertResults);

    const result: OrchestrationResult = {
      game_id,
      run_id,
      expert_results: expertResults,
      orchestration_summary: summary,
      processingTimeMs: Date.now() - startTime
    };

    context.logger.info(`Game orchestration completed`, {
      totalExperts: summary.total_experts,
      successfulExperts: summary.successful_experts,
      totalPredictions: summary.total_predictions,
      avgConfidence: summary.avg_confidence
    });

    return response.json(result);

  } catch (error) {
    context.logger.error('Game Orchestrator failed:', error);
    return response.json({
      error: 'Game orchestration failed',
      message: error instanceof Error ? error.message : String(error),
      game_id: (request.data as any).game_id || 'unknown',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function orchestrateExperts(
  game_id: string,
  expert_ids: string[],
  gameContext: any,
  memories: any[],
  context: AgentContext
): Promise<ExpertResult[]> {

  const expertResults: ExpertResult[] = [];

  // Process each expert in parallel
  const expertPromises = expert_ids.map(async (expertId) => {
    try {
      context.logger.info(`Invoking expert: ${expertId}`);

      // Get the expert agent
      const expertAgent = await context.getAgent({ name: expertId });

      // Prepare expert input
      const expertInput = {
        gameId: game_id,
        expertId: expertId,
        gameContext: gameContext,
        memories: memories
      };

      // Invoke the expert (wrap in InvocationArguments format)
      const expertResponse = await expertAgent.run({
        data: expertInput
      });

      // Parse expert response
      const expertData = await expertResponse.data.json() as any;

      const result: ExpertResult = {
        expertId: expertId,
        predictions: expertData?.predictions || [],
        expertPersona: expertData?.expertPersona || expertId,
        processingTimeMs: expertData?.processingTimeMs || 0,
        success: true
      };

      context.logger.info(`Expert ${expertId} completed successfully`, {
        predictionsCount: result.predictions.length,
        processingTime: result.processingTimeMs
      });

      return result;

    } catch (error) {
      context.logger.error(`Expert ${expertId} failed:`, error);

      const result: ExpertResult = {
        expertId: expertId,
        predictions: [],
        expertPersona: expertId,
        processingTimeMs: 0,
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };

      return result;
    }
  });

  // Wait for all experts to complete
  const results = await Promise.all(expertPromises);
  expertResults.push(...results);

  return expertResults;
}

function generateOrchestrationSummary(expertResults: ExpertResult[]) {
  const successful = expertResults.filter(r => r.success);
  const failed = expertResults.filter(r => !r.success);

  const allPredictions = successful.flatMap(r => r.predictions);
  const totalStakeUnits = allPredictions.reduce((sum, p) => sum + p.stakeUnits, 0);
  const avgConfidence = allPredictions.length > 0
    ? allPredictions.reduce((sum, p) => sum + p.confidence, 0) / allPredictions.length
    : 0;

  return {
    total_experts: expertResults.length,
    successful_experts: successful.length,
    failed_experts: failed.length,
    total_predictions: allPredictions.length,
    avg_confidence: Math.round(avgConfidence * 1000) / 1000, // Round to 3 decimals
    total_stake_units: Math.round(totalStakeUnits * 100) / 100 // Round to 2 decimals
  };
}

export const welcome = () => {
  return {
    welcome: `
# Game Orchestrator

Coordinates multiple expert agents for comprehensive NFL game analysis.

## Features:
- Parallel expert invocation
- Result aggregation and summary
- Error handling and fallback
- Performance monitoring
- Run isolation and tracking

## Supported Experts:
- the-analyst (data-driven, cautious)
- the-rebel (anti-consensus, contrarian)
- the-rider (trend-focused, recency-heavy)
- the-hunter (market efficiency, EV-focused)

## Usage:
Provide game context and expert list to get comprehensive predictions.
    `,
    prompts: [
      {
        data: JSON.stringify({
          game_id: "test_game_orchestration",
          expert_ids: ["the-analyst", "the-rebel", "the-rider", "the-hunter"],
          gameContext: {
            homeTeam: "KC",
            awayTeam: "BUF",
            gameTime: "2024-10-09T20:00:00Z"
          },
          memories: [
            {
              memoryId: "mem_orch_001",
              content: "KC vs BUF historical matchup data shows close games",
              similarity: 0.87
            }
          ],
          run_id: "run_2025_pilot4"
        }),
        contentType: 'application/json'
      }
    ]
  };
};

// Agent configuration
export const config = {
  name: "game-orchestrator",
  description: "Orchestrates parallel expert prediction generation for NFL games"
};

// Default export is required by Agentuity
export default GameOrchestrator;