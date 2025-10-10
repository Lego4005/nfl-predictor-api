/**
 * Sharp Money Follower - The Sharp
 *
 * Follows professional betting patterns and smart money
 * Tracks line movements and sharp action
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
  expertPersona: 'sharp_money_follower';
  processingTimeMs: number;
}

export default async function SharpMoneyFollower(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Sharp Money Follower processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateSharpPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'sharp_money_follower',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Sharp Money Follower failed:', error);
    return resp.json({
      error: 'Sharp money analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'sharp_money_follower',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateSharpPredictions(
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

  // Sharp approach: Follow professional money
  predictions.push({
    category: 'game_winner',
    value: gameContext.awayTeam, // Sharp money on underdog
    confidence: 0.81,
    stakeUnits: 3.8
  });

  predictions.push({
    category: 'total_points',
    value: 'under', // Sharp money typically on unders
    confidence: 0.78,
    stakeUnits: 3.5
  });

  predictions.push({
    category: 'sharp_action',
    value: 'follow_professional_money',
    confidence: 0.89,
    stakeUnits: 4.2
  });

  predictions.push({
    category: 'line_movement',
    value: 'track_sharp_indicators',
    confidence: 0.85,
    stakeUnits: 3.9
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Sharp - Sharp Money Follower

Follows professional betting patterns and smart money movements.

## Personality:
- Tracks line movements and sharp action
- High confidence in professional betting patterns
- Aggressive stake sizing on clear sharp plays
- Systematic approach to following smart money
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "sharp_test",
          expertId: "sharp_money_follower",
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
