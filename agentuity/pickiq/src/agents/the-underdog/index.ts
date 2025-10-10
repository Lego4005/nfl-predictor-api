/**
 * Underdog Champion - The Underdog
 *
 * Systematically backs underdogs and seeks upsets
 * Believes underdogs provide better value
 */

import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";

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
}

interface PredictionResult {
  predictions: Array<{
    category: string;
    value: boolean | string | number;
    confidence: number;
    stakeUnits: number;
  }>;
  expertPersona: 'underdog_champion';
  processingTimeMs: number;
}

export default async function UnderdogChampion(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Underdog Champion processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateUnderdogPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'underdog_champion',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Underdog Champion failed:', error);
    return resp.json({
      error: 'Underdog analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'underdog_champion',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateUnderdogPredictions(
  gameContext: any,
  memories: any[],
  ctx: AgentContext
): Promise<Array<{
  category: string;
  value: boolean | string | number;
  confidence: number;
  stakeUnits: number;
}>> {

  const predictions = [];

  // Underdog approach: Always back the underdog
  predictions.push({
    category: 'game_winner',
    value: gameContext.awayTeam, // Always back the underdog
    confidence: 0.79,
    stakeUnits: 3.5
  });

  predictions.push({
    category: 'point_spread',
    value: gameContext.awayTeam, // Take the points
    confidence: 0.82,
    stakeUnits: 3.8
  });

  predictions.push({
    category: 'upset_potential',
    value: 'high_underdog_value',
    confidence: 0.87,
    stakeUnits: 4.0
  });

  predictions.push({
    category: 'underdog_edge',
    value: 'systematic_advantage',
    confidence: 0.84,
    stakeUnits: 3.7
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Underdog - Underdog Champion

Systematically backs underdogs and seeks upset opportunities.

## Personality:
- Always looks for underdog value
- Believes underdogs are undervalued by market
- High confidence in upset potential
- Aggressive stake sizing on underdog plays
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "underdog_test",
          expertId: "underdog_champion",
          gameContext: {
            homeTeam: "KC",
            awayTeam: "BUF",
            gameTime: "2024-10-09T20:00:00Z"
          },
          memories: []
        }),
        contentType: 'application/json'
      }
    ]
  };
};
