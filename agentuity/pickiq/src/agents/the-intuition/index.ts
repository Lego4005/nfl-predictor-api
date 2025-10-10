/**
 * Gut Instinct Expert - The Intuition
 *
 * Relies on gut feelings and intuitive analysis
 * Experience-based predictions over pure statistics
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
  expertPersona: 'gut_instinct_expert';
  processingTimeMs: number;
}

export default async function GutInstinctExpert(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Gut Instinct Expert processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateGutPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'gut_instinct_expert',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Gut Instinct Expert failed:', error);
    return resp.json({
      error: 'Gut instinct analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'gut_instinct_expert',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateGutPredictions(
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

  // Gut instinct approach: Intuitive feelings
  predictions.push({
    category: 'game_winner',
    value: gameContext.awayTeam, // Gut feeling on underdog
    confidence: 0.75,
    stakeUnits: 2.8
  });

  predictions.push({
    category: 'total_points',
    value: 'over', // Gut says high scoring
    confidence: 0.70,
    stakeUnits: 2.5
  });

  predictions.push({
    category: 'gut_feeling',
    value: 'strong_intuition',
    confidence: 0.88,
    stakeUnits: 3.5
  });

  predictions.push({
    category: 'experience_factor',
    value: 'trust_instincts',
    confidence: 0.82,
    stakeUnits: 3.0
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Intuition - Gut Instinct Expert

Relies on gut feelings and intuitive analysis over pure statistics.

## Personality:
- Trusts gut feelings and intuition
- Experience-based decision making
- High confidence in instinctive reads
- Moderate to aggressive stake sizing on strong feelings
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "intuition_test",
          expertId: "gut_instinct_expert",
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
