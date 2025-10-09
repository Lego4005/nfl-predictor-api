import { Agent, AgentConfig } from '@agentuity/core';
import { z } from 'zod';

// Momentum Rider - Recency-heavy, trend surfing approach
const momentumRiderConfig: AgentConfig = {
  name: 'momentum-rider',
  description: 'Trend-focused expert who emphasizes recent performance and hot streaks',
  version: '1.0.0',

  // Model configuration - starts with DeepSeek for fast JSON
  model: {
    provider: 'deepseek',
    name: 'deepseek-chat-v3.1:free',
    temperature: 0.6, // Higher temperature for dynamic analysis
    maxTokens: 3500,
    timeout: 25000, // 25s budget for speed
  },

  // Input schema (same as conservative analyzer)
  inputSchema: z.object({
    gameId: z.string(),
    expertId: z.string(),
    gameContext: z.object({
      homeTeam: z.string(),
      awayTeam: z.string(),
      gameTime: z.string(),
      weather: z.object({
        temperature: z.number().optional(),
        windSpeed: z.number().optional(),
        precipitation: z.string().optional(),
      }).optional(),
      injuries: z.array(z.object({
        player: z.string(),
        position: z.string(),
        status: z.string(),
      })).optional(),
    }),
    memories: z.array(z.object({
      memoryId: z.string(),
      content: z.string(),
      similarity: z.number(),
      recencyWeight: z.number(),
    })),
    teamKnowledge: z.object({
      homeTeam: z.record(z.any()),
      awayTeam: z.record(z.any()),
    }),
    categoryRegistry: z.array(z.object({
      category: z.string(),
      subject: z.string(),
      predType: z.enum(['binary', 'enum', 'numeric']),
      description: z.string(),
    })),
    recencyAlpha: z.number(),
  }),

  // Output schema - 83 assertions + metadata
  outputSchema: z.object({
    predictions: z.array(z.object({
      category: z.string(),
      subject: z.string(),
      predType: z.enum(['binary', 'enum', 'numeric']),
      value: z.union([z.boolean(), z.string(), z.number()]),
      confidence: z.number().min(0).max(1),
      stakeUnits: z.number().min(0),
      odds: z.number().optional(),
      why: z.array(z.object({
        memoryId: z.string(),
        weight: z.number(),
      })),
    })).length(83),

    winnerTeamId: z.string(),
    homeWinProb: z.number().min(0).max(1),
    overallConfidence: z.number().min(0).max(1),
    recencyAlphaUsed: z.number(),
    expertPersona: z.literal('momentum_rider'),
    reasoningMode: z.enum(['deliberate', 'one-shot', 'degraded']),
    processingTimeMs: z.number(),
  }),

  // System prompt defining momentum-focused personality
  systemPrompt: `You are the Momentum Rider, an NFL expert who specializes in identifying and riding hot streaks and recent trends.

PERSONALITY TRAITS:
- Heavily weight the last 3-4 games over season-long averages
- Look for teams/players on hot or cold streaks
- Quick to identify momentum shifts and coaching adjustments
- Willing to take higher-variance bets on trending teams
- Aggressive with stake sizing when momentum is clear
- Love overs when offenses are clicking, unders when defenses peak

ANALYTICAL APPROACH:
- Prioritize recent game performance over historical averages
- Track week-over-week improvement/decline in key metrics
- Identify breakout players and emerging storylines
- Monitor coaching changes and scheme adjustments
- Factor in recent injury impacts and lineup changes
- Look for teams playing with desperation or confidence

DECISION FRAMEWORK:
- Bet bigger on clear momentum plays (3-5 units)
- Fade teams coming off emotional wins/losses
- Target player props for guys in hot streaks
- Love live betting scenarios with momentum swings
- Quick to pivot when trends reverse
- Trust gut feel when data shows momentum

RECENCY WEIGHTING:
- Last game: 40% weight
- 2 games ago: 30% weight
- 3 games ago: 20% weight
- 4+ games ago: 10% weight combined

OUTPUT REQUIREMENTS:
- Return exactly 83 predictions covering all betting categories
- Include confidence (0-1) and stake units (0-5) for each
- Reference specific memories showing recent trends
- Maintain coherence across related predictions
- Use JSON format only - no explanatory text outside the schema`,

  // Tools available to the agent
  tools: [
    {
      name: 'web_search',
      description: 'Search for recent NFL news, injuries, and momentum stories',
      maxCalls: 5, // More tool usage for trend research
    },
    {
      name: 'social_sentiment',
      description: 'Check social media sentiment and betting trends',
      maxCalls: 2,
    },
    {
      name: 'line_movement',
      description: 'Track recent line movements and sharp money',
      maxCalls: 2,
    }
  ],

  // Execution configuration
  execution: {
    maxIterations: 2, // Draft -> Critic/Repair -> Final
    timeoutMs: 40000, // 40s total budget
    retryOnFailure: true,
    fallbackToOneShot: true,
  },

  // Telemetry and monitoring
  telemetry: {
    trackLatency: true,
    trackTokenUsage: true,
    trackToolCalls: true,
    logLevel: 'info',
  },
};

export class MomentumRiderAgent extends Agent {
  constructor() {
    super(momentumRiderConfig);
  }

  async execute(input: any): Promise<any> {
    const startTime = Date.now();

    try {
      // Validate input
      const validatedInput = this.config.inputSchema.parse(input);

      // Execute deliberate reasoning with momentum focus
      const result = await this.deliberateReasoning(validatedInput);

      // Add processing metadata
      result.processingTimeMs = Date.now() - startTime;
      result.reasoningMode = 'deliberate';

      // Validate output
      return this.config.outputSchema.parse(result);

    } catch (error) {
      console.error('Momentum Rider execution failed:', error);

      // Fallback to one-shot if deliberate fails
      try {
        const fallbackResult = await this.oneShotReasoning(input);
        fallbackResult.processingTimeMs = Date.now() - startTime;
        fallbackResult.reasoningMode = 'one-shot';
        return this.config.outputSchema.parse(fallbackResult);
      } catch (fallbackError) {
        // Final degraded mode
        return this.degradedResponse(input, startTime);
      }
    }
  }

  private async deliberateReasoning(input: any): Promise<any> {
    // Draft phase - identify momentum trends
    const draftPrompt = this.buildDraftPrompt(input);
    const draftResponse = await this.callModel(draftPrompt);

    // Critic phase - validate momentum logic
    const criticPrompt = this.buildCriticPrompt(input, draftResponse);
    const criticResponse = await this.callModel(criticPrompt);

    // Repair phase - adjust based on momentum analysis
    if (criticResponse.needsRepair) {
      const repairPrompt = this.buildRepairPrompt(input, draftResponse, criticResponse);
      return await this.callModel(repairPrompt);
    }

    return draftResponse;
  }

  private async oneShotReasoning(input: any): Promise<any> {
    const prompt = this.buildOneShotPrompt(input);
    return await this.callModel(prompt);
  }

  private degradedResponse(input: any, startTime: number): any {
    // Return momentum-biased defaults when all else fails
    return {
      predictions: this.generateMomentumPredictions(input.categoryRegistry),
      winnerTeamId: input.gameContext.awayTeam, // Slight road bias for momentum
      homeWinProb: 0.48, // Fade home field for momentum plays
      overallConfidence: 0.4, // Moderate confidence for degraded mode
      recencyAlphaUsed: input.recencyAlpha,
      expertPersona: 'momentum_rider',
      reasoningMode: 'degraded',
      processingTimeMs: Date.now() - startTime,
    };
  }

  private buildDraftPrompt(input: any): string {
    // Sort memories by recency weight for momentum analysis
    const recentMemories = input.memories
      .sort((a: any, b: any) => b.recencyWeight - a.recencyWeight)
      .slice(0, 15); // Focus on most recent

    return `${this.config.systemPrompt}

GAME CONTEXT:
${JSON.stringify(input.gameContext, null, 2)}

RECENT MOMENTUM MEMORIES (sorted by recency):
${recentMemories.map((m: any, i: number) =>
  `${i+1}. [${m.memoryId}] (RECENCY: ${m.recencyWeight.toFixed(3)}, sim: ${m.similarity.toFixed(3)})
  ${m.content}`
).join('\n\n')}

TEAM KNOWLEDGE:
Home: ${JSON.stringify(input.teamKnowledge.homeTeam, null, 2)}
Away: ${JSON.stringify(input.teamKnowledge.awayTeam, null, 2)}

RECENCY ALPHA: ${input.recencyAlpha} (higher = more recent bias)

BETTING CATEGORIES (${input.categoryRegistry.length} total):
${input.categoryRegistry.map((cat: any) =>
  `- ${cat.category} (${cat.subject}): ${cat.description} [${cat.predType}]`
).join('\n')}

TASK: Generate exactly 83 predictions focusing on recent momentum and trends. Look for:
- Teams on hot/cold streaks (last 3-4 games)
- Players with recent breakout performances
- Coaching adjustments showing in recent games
- Line movement indicating sharp money
- Emotional momentum from recent wins/losses

Weight recent memories heavily and be aggressive with stakes when momentum is clear.

Respond with valid JSON matching the output schema.`;
  }

  private buildCriticPrompt(input: any, draft: any): string {
    return `Review the following momentum-based predictions:

${JSON.stringify(draft, null, 2)}

MOMENTUM VALIDATION CHECKLIST:
1. Are predictions consistent with recent team trends?
2. Do stake sizes reflect momentum confidence (higher for clear trends)?
3. Are player props aligned with recent performance patterns?
4. Do game totals reflect recent offensive/defensive momentum?
5. Is recency bias appropriately applied vs over-weighting?
6. Are there 83 predictions with proper coherence?

Check for:
- Exactly 83 predictions covering all categories
- Quarters sum to game total
- Winner consistent with margin predictions
- Stake units reflect momentum confidence (0-5 range)
- Memory references support momentum thesis

Respond with JSON: {"needsRepair": boolean, "issues": string[], "momentumAdjustments": string[]}`;
  }

  private buildRepairPrompt(input: any, draft: any, critic: any): string {
    return `Fix the momentum analysis issues in the draft predictions:

ISSUES IDENTIFIED:
${critic.issues.join('\n')}

MOMENTUM ADJUSTMENTS NEEDED:
${critic.momentumAdjustments.join('\n')}

ORIGINAL DRAFT:
${JSON.stringify(draft, null, 2)}

Focus on:
- Strengthening recent trend analysis
- Adjusting stakes based on momentum clarity
- Ensuring predictions reflect hot/cold streaks
- Maintaining coherence across related bets

Return the corrected predictions in valid JSON format.`;
  }

  private buildOneShotPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT: ${JSON.stringify(input.gameContext)}
RECENT MEMORIES: ${input.memories.length} available (focus on highest recency weights)
CATEGORIES: ${input.categoryRegistry.length} required

Generate exactly 83 predictions emphasizing recent momentum and trends. Be aggressive with stakes when trends are clear.

Respond with valid JSON only.`;
  }

  private generateMomentumPredictions(categoryRegistry: any[]): any[] {
    // Generate momentum-biased predictions for degraded mode
    return categoryRegistry.map(cat => ({
      category: cat.category,
      subject: cat.subject,
      predType: cat.predType,
      value: this.getMomentumValue(cat.predType, cat.category),
      confidence: 0.4,
      stakeUnits: 1, // Small stakes in degraded mode
      why: [],
    }));
  }

  private getMomentumValue(predType: string, category: string): any {
    switch (predType) {
      case 'binary':
        // Bias toward overs and road teams for momentum
        return category.includes('total') || category.includes('over') ? true : false;
      case 'enum':
        return category.includes('total') ? 'over' : 'away';
      case 'numeric':
        return category.includes('total') ? 1 : 0; // Slight over bias
      default:
        return null;
    }
  }
}

export default MomentumRiderAgent;
