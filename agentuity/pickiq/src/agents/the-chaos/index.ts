/**
 * Chaos Theory Believer - The Chaos
 *
 * Expects unpredictable outcomes and high variance
 * Believes in randomness and chaos theory in sports
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
  expertPersona: 'chaos_theory_believer';
  processingTimeMs: number;
}

export default async function ChaosTheoryBeliever(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Chaos Theory Believer processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateChaosPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'chaos_theory_believer',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Chaos Theory Believer failed:', error);
    return resp.json({
      error: 'Chaos analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'chaos_theory_believer',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateChaosPredictions(
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

  // Chaos approach: High variance, unpredictable outcomes
  const randomFactor = Math.random();

  predictions.push({
    category: 'game_winner',
    value: randomFactor > 0.5 ? gameContext.homeTeam : gameContext.awayTeam,
    confidence: 0.50 + Math.random() * 0.4, // Random confidence
    stakeUnits: 1 + Math.random() * 4 // Random stake 1-5
  });

  predictions.push({
    category: 'total_points',
    value: Math.random() > 0.5 ? 'over' : 'under',
    confidence: 0.45 + Math.random() * 0.5,
    stakeUnits: Math.random() * 3
  });

  predictions.push({
    category: 'chaos_factor',
    value: 'high_variance_expected',
    confidence: 0.85, // Very confident in chaos
    stakeUnits: 4.0
  });

  predictions.push({
    category: 'unexpected_outcome',
    value: 'likely',
    confidence: 0.80,
    stakeUnits: 3.5
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Chaos - Chaos Theory Believer

Expects unpredictable outcomes and embraces randomness in NFL games.

## Personality:
- Believes in chaos theory and butterfly effects
- Expects high variance and unpredictable outcomes
- Random confidence and stake sizing
- Thrives on uncertainty and disorder
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "chaos_test",
          expertId: "chaos_theory_believer",
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
