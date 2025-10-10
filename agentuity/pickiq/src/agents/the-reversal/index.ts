/**
 * Trend Reversal Specialist - The Reversal
 *
 * Mean-reversion specialist expecting trends to reverse
 * Believes in regression to the mean
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
  expertPersona: 'trend_reversal_specialist';
  processingTimeMs: number;
}

export default async function TrendReversalSpecialist(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Trend Reversal Specialist processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateReversalPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'trend_reversal_specialist',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Trend Reversal Specialist failed:', error);
    return resp.json({
      error: 'Trend reversal analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'trend_reversal_specialist',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateReversalPredictions(
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

  // Reversal approach: Expect mean reversion
  predictions.push({
    category: 'game_winner',
    value: gameContext.awayTeam, // Expect trend reversal
    confidence: 0.74,
    stakeUnits: 2.9
  });

  predictions.push({
    category: 'total_points',
    value: 'under', // Expect scoring to revert to mean
    confidence: 0.77,
    stakeUnits: 3.1
  });

  predictions.push({
    category: 'mean_reversion',
    value: 'expect_trend_reversal',
    confidence: 0.86,
    stakeUnits: 3.7
  });

  predictions.push({
    category: 'regression_to_mean',
    value: 'statistical_normalization',
    confidence: 0.82,
    stakeUnits: 3.4
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Reversal - Trend Reversal Specialist

Mean-reversion specialist who expects trends to reverse and regression to the mean.

## Personality:
- Believes in statistical mean reversion
- Expects hot/cold streaks to end
- High confidence in regression patterns
- Moderate to aggressive stake sizing on reversals
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "reversal_test",
          expertId: "trend_reversal_specialist",
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
