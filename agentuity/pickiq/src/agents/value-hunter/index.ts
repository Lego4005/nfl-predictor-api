import { Agent, AgentConfig } from '@agentuity/core';
import { z } from 'zod';

// Value Hunter - Line shopping and market efficiency focused
const valueHunterConfig: AgentConfig = {
  name: 'value-hunter',
  description: 'Market-focused expert who hunts for value through line shopping and efficiency analysis',
  version: '1.0.0',

  // Model configuration - starts with Claude Sonnet for analytical precision
  model: {
    provider: 'anthropic',
    name: 'claude-sonnet-4.5',
    temperature: 0.4, // Moderate temperature for analytical balance
    maxTokens: 4000,
    timeout: 35000, // 35s budget for thorough analysis
  },

  // Input schema with market data
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
    marketData: z.object({
      currentLines: z.record(z.number()).optional(),
      lineMovement: z.array(z.object({
        line: z.number(),
        timestamp: z.string(),
        volume: z.number().optional(),
      })).optional(),
      impliedProbabilities: z.record(z.number()).optional(),
      bestAvailableOdds: z.record(z.number()).optional(),
    }).optional(),
  }),

  // Output schema - 83 assertions + value analysis
  outputSchema: z.object({
    predictions: z.array(z.object({
      category: z.string(),
      subject: z.string(),
      predType: z.enum(['binary', 'enum', 'numeric']),
      value: z.union([z.boolean(), z.string(), z.number()]),
      confidence: z.number().min(0).max(1),
      stakeUnits: z.number().min(0),
      odds: z.number().optional(),
      impliedProb: z.number().optional(),
      expectedValue: z.number().optional(),
      why: z.array(z.object({
        memoryId: z.string(),
        weight: z.number(),
      })),
    })).length(83),

    winnerTeamId: z.string(),
    homeWinProb: z.number().min(0).max(1),
    overallConfidence: z.number().min(0).max(1),
    recencyAlphaUsed: z.number(),
    expertPersona: z.literal('value_hunter'),
    reasoningMode: z.enum(['deliberate', 'one-shot', 'degraded']),
    processingTimeMs: z.number(),
    valueOpportunities: z.array(z.object({
      category: z.string(),
      expectedValue: z.number(),
      reasoning: z.string(),
    })).optional(),
  }),

  // System prompt defining value-hunting personality
  systemPrompt: `You are the Value Hunter, an NFL expert who specializes in finding market inefficiencies and maximizing expected value.

PERSONALITY TRAITS:
- Obsessed with finding positive expected value (+EV) bets
- Compare your projections to market lines constantly
- Line shop across multiple sportsbooks for best odds
- Focus on market inefficiencies and mispriced lines
- Conservative with stakes unless edge is significant (>5%)
- Love arbitrage opportunities and middle bets

ANALYTICAL APPROACH:
- Calculate implied probabilities from all available lines
- Build your own probability models for comparison
- Track line movement to identify sharp vs public money
- Look for steam moves and reverse line movement
- Analyze closing line value as key performance metric
- Factor in vig and find the best available numbers

DECISION FRAMEWORK:
- Only bet when you have +EV (your prob > implied prob)
- Stake size based on Kelly Criterion and edge size
- Prefer bets with 7%+ edge for meaningful stakes
- Always consider the best available line, not just one book
- Track closing line value to validate market timing
- Love props where books have less sophisticated models

VALUE HUNTING PRIORITIES:
1. Player props (books often less sharp here)
2. Alt lines and derivatives (more pricing errors)
3. Live betting inefficiencies during games
4. Correlated parlays with positive correlation
5. Middle opportunities on line movement
6. Arbitrage across different sportsbooks

MARKET ANALYSIS:
- Compare your projections to consensus closing lines
- Identify which categories you have the biggest edge
- Look for books that are consistently off on certain bet types
- Track which props have the most line shopping value
- Monitor for steam moves that create temporary value

OUTPUT REQUIREMENTS:
- Return exactly 83 predictions covering all betting categories
- Include confidence, stake units, and expected value for each
- Calculate implied probabilities from available odds
- Reference memories that support your value thesis
- List top value opportunities in metadata
- Only recommend bets with positive expected value
- Use JSON format only - no explanatory text outside the schema`,

  // Tools available to the agent
  tools: [
    {
      name: 'odds_comparison',
      description: 'Compare odds across multiple sportsbooks',
      maxCalls: 5,
    },
    {
      name: 'line_movement_tracker',
      description: 'Track line movement and identify steam moves',
      maxCalls: 3,
    },
    {
      name: 'implied_probability_calculator',
      description: 'Calculate implied probabilities and remove vig',
      maxCalls: 4,
    },
    {
      name: 'kelly_calculator',
      description: 'Calculate optimal stake sizes using Kelly Criterion',
      maxCalls: 2,
    },
    {
      name: 'arbitrage_finder',
      description: 'Identify arbitrage opportunities across books',
      maxCalls: 2,
    }
  ],

  // Execution configuration
  execution: {
    maxIterations: 2, // Draft -> Critic/Repair -> Final
    timeoutMs: 50000, // 50s total budget for thorough market analysis
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

export class ValueHunterAgent extends Agent {
  constructor() {
    super(valueHunterConfig);
  }

  async execute(input: any): Promise<any> {
    const startTime = Date.now();

    try {
      // Validate input
      const validatedInput = this.config.inputSchema.parse(input);

      // Execute deliberate value hunting
      const result = await this.deliberateReasoning(validatedInput);

      // Add processing metadata
      result.processingTimeMs = Date.now() - startTime;
      result.reasoningMode = 'deliberate';

      // Validate output
      return this.config.outputSchema.parse(result);

    } catch (error) {
      console.error('Value Hunter execution failed:', error);

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
    // Draft phase - identify value opportunities
    const draftPrompt = this.buildDraftPrompt(input);
    const draftResponse = await this.callModel(draftPrompt);

    // Critic phase - validate value calculations
    const criticPrompt = this.buildCriticPrompt(input, draftResponse);
    const criticResponse = await this.callModel(criticPrompt);

    // Repair phase - optimize value positions
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
    // Return value-focused defaults when all else fails
    return {
      predictions: this.generateValuePredictions(input.categoryRegistry),
      winnerTeamId: input.gameContext.homeTeam, // Neutral default
      homeWinProb: 0.52, // Slight home field edge
      overallConfidence: 0.3, // Low confidence for degraded mode
      recencyAlphaUsed: input.recencyAlpha,
      expertPersona: 'value_hunter',
      reasoningMode: 'degraded',
      processingTimeMs: Date.now() - startTime,
      valueOpportunities: [],
    };
  }

  private buildDraftPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT:
${JSON.stringify(input.gameContext, null, 2)}

VALUE-FOCUSED MEMORY ANALYSIS:
${input.memories.map((m: any, i: number) =>
  `${i+1}. [${m.memoryId}] (sim: ${m.similarity.toFixed(3)}, recency: ${m.recencyWeight.toFixed(3)})
  ${m.content}

  VALUE ANGLE: What market inefficiency does this suggest?`
).join('\n\n')}

TEAM KNOWLEDGE:
Home: ${JSON.stringify(input.teamKnowledge.homeTeam, null, 2)}
Away: ${JSON.stringify(input.teamKnowledge.awayTeam, null, 2)}

MARKET DATA:
${input.marketData ? JSON.stringify(input.marketData, null, 2) : 'Limited market data - use general value principles'}

BETTING CATEGORIES (${input.categoryRegistry.length} total):
${input.categoryRegistry.map((cat: any) =>
  `- ${cat.category} (${cat.subject}): ${cat.description} [${cat.predType}]`
).join('\n')}

VALUE HUNTING MISSION: Generate exactly 83 predictions focused on positive expected value opportunities.

FOR EACH PREDICTION:
1. Calculate your true probability estimate
2. Compare to implied probability from available odds
3. Only recommend if you have +EV (your prob > implied prob)
4. Size stakes using Kelly Criterion based on edge size
5. Include expected value calculation in metadata

FOCUS AREAS FOR VALUE:
- Player props (often less efficiently priced)
- Alt lines and derivatives
- Live betting scenarios
- Correlated outcomes
- Line shopping opportunities

Include your top value opportunities in the valueOpportunities array.

Respond with valid JSON matching the output schema.`;
  }

  private buildCriticPrompt(input: any, draft: any): string {
    return `Review the following value-focused predictions:

${JSON.stringify(draft, null, 2)}

VALUE VALIDATION CHECKLIST:
1. Are expected value calculations accurate?
2. Do stake sizes reflect Kelly Criterion optimization?
3. Are we only betting positive EV opportunities?
4. Do implied probability calculations look correct?
5. Are value opportunities clearly identified and ranked?
6. Is line shopping considered for best available odds?

Standard checks:
- Exactly 83 predictions covering all categories
- Quarters sum to game total
- Winner consistent with margin predictions
- Stake units reflect value edge (0-5 range)
- Expected values are positive for recommended bets

Respond with JSON: {"needsRepair": boolean, "issues": string[], "valueOptimizations": string[]}`;
  }

  private buildRepairPrompt(input: any, draft: any, critic: any): string {
    return `Optimize the value analysis in the draft predictions:

ISSUES IDENTIFIED:
${critic.issues.join('\n')}

VALUE OPTIMIZATIONS NEEDED:
${critic.valueOptimizations.join('\n')}

ORIGINAL DRAFT:
${JSON.stringify(draft, null, 2)}

Focus on:
- Correcting expected value calculations
- Optimizing stake sizes using Kelly Criterion
- Ensuring only +EV bets are recommended
- Improving implied probability accuracy
- Ranking value opportunities by edge size
- Considering line shopping for best odds

Return the corrected predictions in valid JSON format.`;
  }

  private buildOneShotPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT: ${JSON.stringify(input.gameContext)}
MEMORIES: ${input.memories.length} available (focus on value angles)
MARKET DATA: ${input.marketData ? 'Available' : 'Limited'}
CATEGORIES: ${input.categoryRegistry.length} required

Generate exactly 83 value-focused predictions that maximize expected value.

Key value principles:
- Only bet positive EV opportunities
- Size stakes based on edge size
- Focus on player props and alt lines
- Consider line shopping value
- Calculate implied probabilities accurately

Respond with valid JSON only.`;
  }

  private generateValuePredictions(categoryRegistry: any[]): any[] {
    // Generate value-focused predictions for degraded mode
    return categoryRegistry.map(cat => ({
      category: cat.category,
      subject: cat.subject,
      predType: cat.predType,
      value: this.getValueDefault(cat.predType, cat.category),
      confidence: 0.3,
      stakeUnits: 0.5, // Conservative stakes in degraded mode
      expectedValue: 0.0, // Neutral EV for degraded mode
      why: [],
    }));
  }

  private getValueDefault(predType: string, category: string): any {
    switch (predType) {
      case 'binary':
        // Value hunter looks for props and alt lines
        return category.includes('prop') || category.includes('alt') ? true : false;
      case 'enum':
        return 'under'; // Conservative value default
      case 'numeric':
        return 0; // Neutral numeric default
      default:
        return null;
    }
  }
}

export default ValueHunterAgent;
