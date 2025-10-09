import { Agent, AgentConfig } from '@agentuity/c
rt { z } from 'zod';

// Conservative Analyzer - Data-driven, cautious approach
const conservativeAnalyzerConfig: AgentConfig = {
  name: 'conservative-analyzer',
  description: 'Data-driven expert focused on statistical analysis and risk management',
  version: '1.0.0',

  // Model configuration - starts with Claude Sonnet for reliability
  model: {
    provider: 'anthropic',
    name: 'claude-sonnet-4.5',
    temperature: 0.3, // Lower temperature for consistency
    maxTokens: 4000,
    timeout: 30000, // 30s budget
  },

  // Input schema for game context and memories
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
    })).length(83), // Exactly 83 predictions

    // Bundle metadata
    winnerTeamId: z.string(),
    homeWinProb: z.number().min(0).max(1),
    overallConfidence: z.number().min(0).max(1),
    recencyAlphaUsed: z.number(),
    expertPersona: z.literal('conservative_analyzer'),
    reasoningMode: z.enum(['deliberate', 'one-shot', 'degraded']),
    processingTimeMs: z.number(),
  }),

  // System prompt defining conservative personality
  systemPrompt: `You are the Conservative Analyzer, a data-driven NFL expert who prioritizes statistical rigor and risk management.

PERSONALITY TRAITS:
- Heavily weight historical data and proven statistical patterns
- Prefer lower-variance bets with consistent returns
- Skeptical of narratives without statistical backing
- Focus on defensive metrics and field position advantages
- Conservative with stake sizing - rarely exceed 2-3 units
- Favor unders and home favorites when data supports

ANALYTICAL APPROACH:
- Emphasize regression to the mean for outlier performances
- Weight recent games but not at expense of larger sample sizes
- Consider weather impact on scoring and turnovers
- Factor in rest advantages and travel fatigue
- Analyze coaching tendencies in key situations
- Use injury reports to adjust team strength ratings

DECISION FRAMEWORK:
- Require 55%+ confidence for any bet recommendation
- Scale stakes based on edge size and certainty level
- Avoid prop bets unless strong statistical edge exists
- Prefer game totals and spreads over exotic props
- Always provide statistical reasoning for predictions

OUTPUT REQUIREMENTS:
- Return exactly 83 predictions covering all betting categories
- Include confidence (0-1) and stake units (0-5) for each
- Reference specific memories that influenced decisions
- Maintain coherence across related predictions (quarters sum to game total, etc.)
- Use JSON format only - no explanatory text outside the schema`,

  // Tools available to the agent
  tools: [
    {
      name: 'web_search',
      description: 'Search for recent NFL news and injury updates',
      maxCalls: 3, // Limited tool usage for conservative approach
    },
    {
      name: 'weather_api',
      description: 'Get current weather conditions for game location',
      maxCalls: 1,
    }
  ],

  // Execution configuration
  execution: {
    maxIterations: 2, // Draft -> Critic/Repair -> Final
    timeoutMs: 45000, // 45s total budget
    retryOnFailure: true,
    fallbackToOneShot: true, // Fallback if deliberate mode fails
  },

  // Telemetry and monitoring
  telemetry: {
    trackLatency: true,
    trackTokenUsage: true,
    trackToolCalls: true,
    logLevel: 'info',
  },
};

export class ConservativeAnalyzerAgent extends Agent {
  constructor() {
    super(conservativeAnalyzerConfig);
  }

  async execute(input: any): Promise<any> {
    const startTime = Date.now();

    try {
      // Validate input
      const validatedInput = this.config.inputSchema.parse(input);

      // Execute deliberate reasoning (Draft -> Critic -> Repair)
      const result = await this.deliberateReasoning(validatedInput);

      // Add processing metadata
      result.processingTimeMs = Date.now() - startTime;
      result.reasoningMode = 'deliberate';

      // Validate output
      return this.config.outputSchema.parse(result);

    } catch (error) {
      console.error('Conservative Analyzer execution failed:', error);

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
    // Draft phase - initial predictions
    const draftPrompt = this.buildDraftPrompt(input);
    const draftResponse = await this.callModel(draftPrompt);

    // Critic phase - review and identify issues
    const criticPrompt = this.buildCriticPrompt(input, draftResponse);
    const criticResponse = await this.callModel(criticPrompt);

    // Repair phase - fix identified issues
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
    // Return minimal valid response when all else fails
    return {
      predictions: this.generateMinimalPredictions(input.categoryRegistry),
      winnerTeamId: input.gameContext.homeTeam, // Default to home team
      homeWinProb: 0.52, // Slight home field advantage
      overallConfidence: 0.3, // Low confidence for degraded mode
      recencyAlphaUsed: input.recencyAlpha,
      expertPersona: 'conservative_analyzer',
      reasoningMode: 'degraded',
      processingTimeMs: Date.now() - startTime,
    };
  }

  private buildDraftPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT:
${JSON.stringify(input.gameContext, null, 2)}

TOP MEMORIES (K=${input.memories.length}):
${input.memories.map((m: any, i: number) =>
  `${i+1}. [${m.memoryId}] (sim: ${m.similarity.toFixed(3)}, recency: ${m.recencyWeight.toFixed(3)})
  ${m.content}`
).join('\n\n')}

TEAM KNOWLEDGE:
Home: ${JSON.stringify(input.teamKnowledge.homeTeam, null, 2)}
Away: ${JSON.stringify(input.teamKnowledge.awayTeam, null, 2)}

BETTING CATEGORIES (${input.categoryRegistry.length} total):
${input.categoryRegistry.map((cat: any) =>
  `- ${cat.category} (${cat.subject}): ${cat.description} [${cat.predType}]`
).join('\n')}

TASK: Generate exactly 83 predictions using conservative, data-driven analysis. Focus on statistical edges and risk management. Reference specific memories in your reasoning.

Respond with valid JSON matching the output schema.`;
  }

  private buildCriticPrompt(input: any, draft: any): string {
    return `Review the following draft predictions for consistency and quality:

${JSON.stringify(draft, null, 2)}

Check for:
1. Exactly 83 predictions covering all categories
2. Quarters sum to game total
3. Winner consistent with margin predictions
4. Stake units reasonable (0-5 range)
5. Confidence levels match stake sizing
6. Memory references are valid

Respond with JSON: {"needsRepair": boolean, "issues": string[], "suggestions": string[]}`;
  }

  private buildRepairPrompt(input: any, draft: any, critic: any): string {
    return `Fix the following issues in the draft predictions:

ISSUES IDENTIFIED:
${critic.issues.join('\n')}

SUGGESTIONS:
${critic.suggestions.join('\n')}

ORIGINAL DRAFT:
${JSON.stringify(draft, null, 2)}

Return the corrected predictions in valid JSON format.`;
  }

  private buildOneShotPrompt(input: any): string {
    return `${this.config.systemPrompt}

GAME CONTEXT: ${JSON.stringify(input.gameContext)}
MEMORIES: ${input.memories.length} available
CATEGORIES: ${input.categoryRegistry.length} required

Generate exactly 83 predictions using conservative analysis. Respond with valid JSON only.`;
  }

  private generateMinimalPredictions(categoryRegistry: any[]): any[] {
    // Generate safe default predictions for degraded mode
    return categoryRegistry.map(cat => ({
      category: cat.category,
      subject: cat.subject,
      predType: cat.predType,
      value: this.getDefaultValue(cat.predType),
      confidence: 0.3,
      stakeUnits: 0, // No stakes in degraded mode
      why: [],
    }));
  }

  private getDefaultValue(predType: string): any {
    switch (predType) {
      case 'binary': return false;
      case 'enum': return 'under';
      case 'numeric': return 0;
      default: return null;
    }
  }
}

export default ConservativeAnalyzerAgent;
