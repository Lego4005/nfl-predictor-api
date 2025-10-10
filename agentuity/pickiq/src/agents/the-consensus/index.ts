/**
 * Consensus Follower - The Consensus
 *
 * Follows crowd opinion and public sentiment
 * Believes the wisdom of crowds is usually correct
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
  expertPersona: 'consensus_follower';
  processingTimeMs: number;
}

export default async function ConsensusFollower(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Consensus Follower processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateConsensusPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'consensus_follower',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Consensus Follower failed:', error);
    return resp.json({
      error: 'Consensus analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'consensus_follower',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateConsensusPredictions(
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

  // Consensus approach: Follow popular opinion
  predictions.push({
    category: 'game_winner',
    value: gameContext.homeTeam, // Assume public likes home team
    confidence: 0.68,
    stakeUnits: 2.0
  });

  predictions.push({
    category: 'total_points',
    value: 'over', // Public usually likes overs
    confidence: 0.72,
    stakeUnits: 2.3
  });

  predictions.push({
    category: 'public_sentiment',
    value: 'follow_majority',
    confidence: 0.85,
    stakeUnits: 3.0
  });

  predictions.push({
    category: 'popular_pick',
    value: 'align_with_crowd',
    confidence: 0.80,
    stakeUnits: 2.8
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Consensus - Consensus Follower

Follows crowd opinion and believes in the wisdom of crowds.

## Personality:
- Trusts public sentiment and popular picks
- Believes the majority is usually right
- Moderate confidence in crowd wisdom
- Conservative stake sizing on consensus plays
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "consensus_test",
          expertId: "consensus_follower",
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
