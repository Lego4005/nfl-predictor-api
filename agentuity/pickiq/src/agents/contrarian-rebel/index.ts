import { Agent, AgentConfig } from '@agentuity/core';
import { z } from 'zod';

// Contrarian Rebel - Fade public narratives and conventional wisdom
const contrarianRebelConfig: AConfig = {
  name: 'contrarian-rebel',
  description: 'Contrarian expert who fades public sentiment and challenges conventional wisdom',
  version: '1.0.0',

  // Model configuration - starts with Grok for contrarian analysis
  model: {
    provider: 'x-ai',
    name: 'grok-4-fast:free',
    temperature: 0.7, // Higher temperature for creative contrarian thinking
    maxTokens: 3500,
    timeout: 30000, // 30s budget
  },

  // Input schema (same structure as other experts)
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
    publicSentiment: z.object({
      favoriteTeam: z.string().optional(),
      publicBettingPct: z.number().optional(),
      mediaHype: z.array(z.string()).optional(),
    }).optional(),
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
    expertPersona: z.literal('contrarian_rebel'),
    reasoningMode: z.enum(['deliberate', 'one-shot', 'degraded']),
    processingTimeMs: z.number(),
    contrarianSignals: z.array(z.string()).optional(), // What we're fading
  }),

  // System prompt defining contrarian personality
  systemPrompt: `You are the Contrarian Rebel, an NFL expert who thrives on fading public sentiment and challenging conventional wisdom.

PERSONALITY TRAITS:
- Automatically skeptical of popular narratives and media hype
- Look for value in unpopular teams and overlooked factors
- Fade public betting percentages when they're extreme (>70%)
- Love betting against "sure thing" favorites and popular overs
- Willing to take big positions when public is clearly wrong
- Contrarian but not stubborn - data still matters

ANALYTICAL APPROACH:
- Identify what the public/media is overvaluing
- Look for regression candidates after big performances
- Find value in teams coming off embarrassing losses
- Target props where casual bettors create inefficiencies
- Fade emotional betting (revenge games, primetime hype)
- Love road underdogs in hostile environments

DECISION FRAMEWORK:
- Bigger bets when fading extreme public sentiment (4-5 units)
- Target unders when public loves high-scoring narratives
- Bet against teams getting too much media attention
- Look for "trap games" where favorites are overvalued
- Fade recency bias when public overreacts to last week
- Trust contrarian instincts over popular consensus

CONTRARIAN SIGNALS TO FADE:
- Public betting >75% on one side
- Media narratives about "must-win" games
- Revenge game storylines
- Teams coming off statement wins
- Popular "lock" picks from talking heads
- Primetime game overs with casual appeal

OUTPUT REQUIREMENTS:
- Return exactly 83 predictions covering all betting categories
- Include confidence (0-1) and stake units (0-5) for each
- Reference specific memories that contradict popular wisdom
- Maintain coherence across related predictions
- List contrarian signals you're fading in metadata
- Use JSON format only - no explanatory text outside the schema`,

  // Tools available to the agent
  tools: [
    {
      name: 'public_betting_data',
      description: 'Get public betting percentages and handle distribution',
      maxCalls: 3,
    },
    {
      name: 'media_sentiment',
      description: 'Analyze media coverage and narrative strength',
      maxCalls: 3,
    },
    {
      name: 'sharp_money_tracker',
      description: 'Identify where sharp money differs from public',
      maxCalls: 2,
    },
    {
      name: 'web_search',
      description: 'Search for contrarian angles and overlooked factors',
      maxCalls: 4,
    }
  ],

  // Execution configuration
  execution: {
    maxIterations: 2, // Draft -> Critic/Repair -> Final
    timeoutMs: 45000, // 45s total budget
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

export class ContrarianRebelAgent extends Agent {
  constructor() {
    super(contrarianRebelConfig);
  }

  async execute(input: any): Promise<any> {
    const startTime = Date.now();

    try {
      // Validate input
      const validatedInput = this.config.inputSchema.parse(input);

      // Execute deliberate contrarian reasoning
      const result = await this.deliberateReasoning(validatedInput);

      // Add processing metadata
      result.processingTimeMs = Date.now() - startTime;
      result.reasoningMode = 'deliberate';

      // Validate output
      return this.config.outputSchema.parse(result);

    } catch (error) {
      console.error('Contrarian Rebel execution failed:', error);

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
    // Draft phase - identify contrarian opportunities
    const draftPrompt = this.buildDraftPrompt(input);
    const draftResponse = await this.callModel(draftPrompt);

    // Critic phase - validate contrarian logic
    const criticPrompt = this.buildCriticPrompt(input, draftResponse);
    const criticResponse = await this.callModel(criticPrompt);

    // Repair phase - strengthen contrarian positions
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
    // Return contrarian-biased defaults when all else fails
    return {
      predictions: this.generateContrarianPredictions(input.categoryRegistry),
      winnerTeamId: input.gameContext.awayTeam, // Fade home field advantage
      homeWinProb: 0.45, // Contrarian bias against home teams
      overallConfidence: 0.35, // Lower confidence for degraded mode
      recencyAlphaUsed: input.recencyAlpha,
      expertPersona: 'contrarian_rebel',
      reasoningMode: 'degraded',
      processingTimeMs: Date.now() - startTime,
      contrarianSignals: ['degraded_mode_defaults'],
    };
  }

  private buildDraftPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT:
${JSON.stringify(input.gameContext, null, 2)}

CONTRARIAN MEMORY ANALYSIS:
${input.memories.map((m: any, i: number) =>
  `${i+1}. [${m.memoryId}] (sim: ${m.similarity.toFixed(3)}, recency: ${m.recencyWeight.toFixed(3)})
  ${m.content}

  CONTRARIAN ANGLE: What popular narrative does this contradict?`
).join('\n\n')}

TEAM KNOWLEDGE:
Home: ${JSON.stringify(input.teamKnowledge.homeTeam, null, 2)}
Away: ${JSON.stringify(input.teamKnowledge.awayTeam, null, 2)}

PUBLIC SENTIMENT (if available):
${input.publicSentiment ? JSON.stringify(input.publicSentiment, null, 2) : 'Not provided - use general contrarian principles'}

BETTING CATEGORIES (${input.categoryRegistry.length} total):
${input.categoryRegistry.map((cat: any) =>
  `- ${cat.category} (${cat.subject}): ${cat.description} [${cat.predType}]`
).join('\n')}

CONTRARIAN MISSION: Generate exactly 83 predictions that fade popular wisdom and find value where others don't look.

SPECIFIC CONTRARIAN TARGETS:
- If home team is heavily favored, look for road value
- If total is high due to offensive hype, consider under
- If player has media buzz, fade their props
- If team is coming off big win, expect regression
- If public loves a "sure thing," find the other side

Include your contrarian signals in the contrarianSignals array.

Respond with valid JSON matching the output schema.`;
  }

  private buildCriticPrompt(input: any, draft: any): string {
    return `Review the following contrarian predictions:

${JSON.stringify(draft, null, 2)}

CONTRARIAN VALIDATION CHECKLIST:
1. Are we truly fading popular sentiment or just being different?
2. Do stake sizes reflect conviction in contrarian thesis?
3. Are contrarian signals clearly identified and logical?
4. Do predictions have data support beyond just being contrarian?
5. Are we avoiding contrarian for contrarian's sake?
6. Is there value in the positions we're taking?

Standard checks:
- Exactly 83 predictions covering all categories
- Quarters sum to game total
- Winner consistent with margin predictions
- Stake units reflect contrarian conviction (0-5 range)
- Memory references support contrarian thesis

Respond with JSON: {"needsRepair": boolean, "issues": string[], "contrarianStrength": string[]}`;
  }

  private buildRepairPrompt(input: any, draft: any, critic: any): string {
    return `Strengthen the contrarian analysis in the draft predictions:

ISSUES IDENTIFIED:
${critic.issues.join('\n')}

CONTRARIAN STRENGTH NEEDED:
${critic.contrarianStrength.join('\n')}

ORIGINAL DRAFT:
${JSON.stringify(draft, null, 2)}

Focus on:
- Strengthening contrarian thesis with data
- Increasing stakes where contrarian edge is clear
- Adding more specific contrarian signals
- Ensuring we're not just being different for different's sake
- Finding real value in unpopular positions

Return the corrected predictions in valid JSON format.`;
  }

  private buildOneShotPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT: ${JSON.stringify(input.gameContext)}
MEMORIES: ${input.memories.length} available (look for contrarian angles)
CATEGORIES: ${input.categoryRegistry.length} required

Generate exactly 83 contrarian predictions that fade popular wisdom and find value in unpopular positions.

Key contrarian principles:
- Fade public favorites and popular overs
- Look for value in road underdogs
- Target regression after big performances
- Bet against media narratives

Respond with valid JSON only.`;
  }

  private generateContrarianPredictions(categoryRegistry: any[]): any[] {
    // Generate contrarian-biased predictions for degraded mode
    return categoryRegistry.map(cat => ({
      category: cat.category,
      subject: cat.subject,
      predType: cat.predType,
      value: this.getContrarianValue(cat.predType, cat.category),
      confidence: 0.35,
      stakeUnits: 1, // Moderate stakes in degraded mode
      why: [],
    }));
  }

  private getContrarianValue(predType: string, category: string): any {
    switch (predType) {
      case 'binary':
        // Contrarian bias toward unders and road teams
        if (category.includes('total') || category.includes('over')) return false;
        if (category.includes('home') || category.includes('favorite')) return false;
        return true;
      case 'enum':
        if (category.includes('total')) return 'under';
        if (category.includes('winner')) return 'away';
        return 'under'; // Default contrarian
      case 'numeric':
        return category.includes('total') ? -1 : 0; // Slight under bias
      default:
        return null;
    }
  }
}

export default ContrarianRebelAgent;
