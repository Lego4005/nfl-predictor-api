/**
 * Popular Narrative Fader - The Fader
 *
 * Fades popular narratives and media storylines
 * Anti-narrative approach to betting
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
  expertPersona: 'popular_narrative_fader';
  processingTimeMs: number;
}

export default async function PopularNarrativeFader(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as unknown as PredictionPayload;
    const { gameId, expertId, gameContext, memories } = payload;

    ctx.logger.info(`Popular Narrative Fader processing game ${gameId}`, {
      homeTeam: gameContext.homeTeam,
      awayTeam: gameContext.awayTeam,
      memoriesCount: memories.length
    });

    const predictions = await generateFaderPredictions(gameContext, memories, ctx);

    const result: PredictionResult = {
      predictions,
      expertPersona: 'popular_narrative_fader',
      processingTimeMs: Date.now() - startTime
    };

    return resp.json(result);

  } catch (error) {
    ctx.logger.error('Popular Narrative Fader failed:', error);
    return resp.json({
      error: 'Narrative fading analysis failed',
      message: error instanceof Error ? error.message : String(error),
      expertPersona: 'popular_narrative_fader',
      processingTimeMs: Date.now() - startTime
    }, { status: 500 });
  }
}

async function generateFaderPredictions(
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

  // Fader approach: Against popular narratives
  predictions.push({
    category: 'game_winner',
    value: gameContext.awayTeam, // Fade popular home team narrative
    confidence: 0.76,
    stakeUnits: 3.2
  });

  predictions.push({
    category: 'total_points',
    value: 'under', // Fade popular over narrative
    confidence: 0.73,
    stakeUnits: 2.8
  });

  predictions.push({
    category: 'narrative_fade',
    value: 'against_media_storyline',
    confidence: 0.84,
    stakeUnits: 3.5
  });

  predictions.push({
    category: 'anti_hype',
    value: 'fade_popular_pick',
    confidence: 0.81,
    stakeUnits: 3.0
  });

  return predictions;
}

export const welcome = () => {
  return {
    welcome: `
# The Fader - Popular Narrative Fader

Fades popular narratives and media storylines in NFL betting.

## Personality:
- Anti-narrative approach to betting
- Skeptical of media hype and popular stories
- Moderate to high confidence in fading narratives
- Aggressive on clear narrative overreactions
    `,
    prompts: [
      {
        data: JSON.stringify({
          gameId: "fader_test",
          expertId: "popular_narrative_fader",
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
