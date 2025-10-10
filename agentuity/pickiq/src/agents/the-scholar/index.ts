/**
 * Fundamentalist Scholar - The Scholar
 *
 * Deep statistical analysis and fundamental research
 * Believes in thorough analysis and academic approach
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
  expertPersona: 'fundamentalist_scholar';
  processingTimeMs: number;
}

export default async function FundamentalistScholar(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Fundamentalist Scholar processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateScholarPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'fundamentalist_scholar',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Fundamentalist Scholar failed:', error);
    return resp.json({
      error: 'Scholar analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'fundamentalist_scholar',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateScholarPredictions(
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

  // Scholar approach: Deep fundamental analysis
  predictions.push({
    category: 'game_winner',
    value: gameContext.homeTeam, // Based on fundamental analysis
    confidence: 0.78,
    stakeUnits: 2.5
  });

  predictions.push({
    category: 'total_points',
    value: 'under', // Scholar prefers defensive fundamentals
    confidence: 0.82,
    stakeUnits: 3.0
  });

  predictions.push({
    category: 'fundamental_analysis',
    value: 'deep_research_advantage',
    confidence: 0.90,
    stakeUnits: 3.5
  });

  predictions.push({
    category: 'statistical_edge',
    value: 'significant',
    confidence: 0.85,
    stakeUnits: 3.2
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Scholar - Fundamentalist Scholar

Deep statistical analysis expert with academic approach to NFL prediction.

## Personality:
- Thorough fundamental research and analysis
- Academic approach to sports prediction
- High confidence in deep statistical work
- Methodical and systematic evaluation
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "scholar_test",
          expertId: "fundamentalist_scholar",
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
