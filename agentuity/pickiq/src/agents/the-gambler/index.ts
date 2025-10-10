/**
 * The Gambler - Risk Taking Gambler
 *
 * High-variance predictions and aggressive betting
 * Embraces risk for maximum reward potential
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
  expertPersona: 'risk_taking_gambler';
  processingTimeMs: number;
}

export default async function TheGambler(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`The Gambler processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateGamblerPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'risk_taking_gambler',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('The Gambler failed:', error);
    return resp.json({
      error: 'Gambler analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'risk_taking_gambler',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateGamblerPredictions(
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

  // Gambler approach: High risk, high reward
  predictions.push({
    category: 'game_winner',
    value: gameContext.awayTeam, // Risk on underdog
    confidence: 0.85, // Overconfident gambler
    stakeUnits: 5.0 // Max risk
  });

  predictions.push({
    category: 'total_points',
    value: 'over', // Gamblers love overs
    confidence: 0.80,
    stakeUnits: 4.5
  });

  predictions.push({
    category: 'exotic_prop',
    value: 'high_payout_bet',
    confidence: 0.75,
    stakeUnits: 3.0
  });

  predictions.push({
    category: 'parlay_opportunity',
    value: 'maximum_payout_combo',
    confidence: 0.90, // Overconfident in parlays
    stakeUnits: 5.0
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Gambler - Risk Taking Gambler

High-variance NFL expert who embraces risk for maximum reward potential.

## Personality:
- Loves high-risk, high-reward scenarios
- Aggressive with stake sizing (often max units)
- Drawn to exotic props and parlays
- Overconfident in big plays
- Prefers underdogs and overs

## Approach:
- Maximum variance betting
- Exotic prop specialization
- Parlay construction
- Contrarian underdog plays
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "gambler_test",
          expertId: "risk_taking_gambler",
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
