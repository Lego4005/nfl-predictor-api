/**
 * Agentuity GameOrchestrator Agent
 *
 * Orchestrates parallel expert prediction generation while keeping hot path in Postgres/pgvector
 * This agent coordinates but does not store operational state
 */

import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";

interface OrchestrationPayload {
  game_id: string;
  expert_ids: string[];
  api_base_url: string;
  enable_shadow_runs: boolean;
  shadow_models: Record<string, string>;
  orchestration_id: string;
  run_id?: string;
}

interface ExpertResult {
  expert_id: string;
  success: boolean;
  duration_ms: number;
  schema_valid: boolean;
  error?: string;
  shadow_result?: any;
}

export default async function GameOrchestrator(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  const startTime = Date.now();

  try {
    const payload = await req.data.json() as OrchestrationPayload;
    const { game_id, expert_ids, api_base_url, enable_shadow_runs, shadow_models, orchestration_id, run_id } = payload;

    ctx.logger.info(`Starting orchestration ${orchestration_id} for game ${game_id} with ${expert_ids.length} experts`);

    // Process experts in parallel
    const expertPromises = expert_ids.map(expert_id =>
      processExpert(expert_id, game_id, api_base_url, enable_shadow_runs, shadow_models[expert_id], run_id, ctx)
    );

    const expertResults = await Promise.allSettled(expertPromises);

    // Aggregate results
    const results: ExpertResult[] = [];
    let totalRetrievalMs = 0;
    let totalLlmMs = 0;
    let totalValidationMs = 0;
    let schemaValidCount = 0;

    expertResults.forEach((result, index) => {
      const expert_id = expert_ids[index];

      if (result.status === 'fulfilled') {
        results.push(result.value);
        totalRetrievalMs += result.value.retrieval_ms || 0;
        totalLlmMs += result.value.llm_ms || 0;
        totalValidationMs += result.value.validation_ms || 0;
        if (result.value.schema_valid) schemaValidCount++;
      } else {
        results.push({
          expert_id,
          success: false,
          duration_ms: 0,
          schema_valid: false,
          error: result.reason?.message || 'Unknown error'
        });
        ctx.logger.error(`Expert ${expert_id} failed: ${result.reason}`);
      }
    });

    const totalDuration = Date.now() - startTime;
    const schemaComplianceRate = expert_ids.length > 0 ? schemaValidCount / expert_ids.length : 0;

    // Log telemetry
    ctx.logger.info(`Orchestration completed in ${totalDuration}ms`, {
      game_id,
      experts_processed: results.filter(r => r.success).length,
      experts_failed: results.filter(r => !r.success).length,
      schema_compliance_rate: schemaComplianceRate,
      avg_retrieval_ms: totalRetrievalMs / expert_ids.length,
      avg_llm_ms: totalLlmMs / expert_ids.length,
      avg_validation_ms: totalValidationMs / expert_ids.length
    });

    return resp.json({
      orchestration_id,
      game_id,
      experts_processed: results.filter(r => r.success).map(r => r.expert_id),
      experts_failed: results.filter(r => !r.success).map(r => r.expert_id),
      total_duration_ms: totalDuration,
      retrieval_duration_ms: totalRetrievalMs,
      llm_duration_ms: totalLlmMs,
      validation_duration_ms: totalValidationMs,
      schema_compliance_rate: schemaComplianceRate,
      shadow_results: enable_shadow_runs ? results.filter(r => r.shadow_result).map(r => ({
        expert_id: r.expert_id,
        shadow_result: r.shadow_result
      })) : null,
      expert_details: results
    });

  } catch (error) {
    ctx.logger.error('Orchestration failed:', error);
    return resp.json({
      error: 'Orchestration failed',
      message: error.message,
      duration_ms: Date.now() - startTime
    }, { status: 500 });
  }
}

async function processExpert(
  expert_id: string,
  game_id: string,
  api_base_url: string,
  enable_shadow_runs: boolean,
  shadow_model: string | undefined,
  run_id: string | undefined,
  ctx: AgentContext
): Promise<ExpertResult> {
  const expertStartTime = Date.now();

  try {
    // Step 1: Get memory context from our API with run_id
    const contextUrl = new URL(`${api_base_url}/context/${expert_id}/${game_id}`);
    if (run_id) {
      contextUrl.searchParams.set('run_id', run_id);
    }

    const contextResponse = await fetch(contextUrl.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!contextResponse.ok) {
      throw new Error(`Context fetch failed: ${contextResponse.status}`);
    }

    const contextData = await contextResponse.json();
    const retrievalMs = Date.now() - expertStartTime;

    // Step 2: Generate predictions via single LLM call
    const llmStartTime = Date.now();

    // Main prediction call
    const predictionPromise = generateExpertPredictions(expert_id, contextData, ctx);

    // Shadow run (if enabled)
    const shadowPromise = enable_shadow_runs && shadow_model
      ? generateShadowPredictions(expert_id, contextData, shadow_model, ctx)
      : Promise.resolve(null);

    const [predictions, shadowResult] = await Promise.all([predictionPromise, shadowPromise]);

    const llmMs = Date.now() - llmStartTime;

    // Step 3: Validate and store predictions
    const validationStartTime = Date.now();

    const storeResponse = await fetch(`${api_base_url}/expert/predictions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        expert_id,
        game_id,
        predictions,
        run_id: run_id || 'run_2025_pilot4',
        orchestration_metadata: {
          retrieval_ms: retrievalMs,
          llm_ms: llmMs,
          shadow_model: shadow_model || null
        }
      })
    });

    const validationMs = Date.now() - validationStartTime;

    if (!storeResponse.ok) {
      throw new Error(`Prediction storage failed: ${storeResponse.status}`);
    }

    const storeResult = await storeResponse.json();

    // Step 4: Store shadow predictions if available (separate storage, never used in hot path)
    if (shadowResult && shadowResult.success && shadowResult.predictions) {
      try {
        const shadowRunId = `shadow_${run_id || 'run_2025_pilot4'}_${Date.now()}`;
        const primaryModel = getModelForExpert(expert_id);

        const shadowStoreResponse = await fetch(`${api_base_url}/api/shadow/predictions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            shadow_run_id: shadowRunId,
            expert_id,
            game_id,
            main_run_id: run_id || 'run_2025_pilot4',
            shadow_model: shadowResult.shadow_model,
            primary_model: primaryModel,
            shadow_type: 'model_comparison',
            overall: shadowResult.predictions.overall || {},
            predictions: shadowResult.predictions.predictions || [],
            processing_time_ms: shadowResult.processing_time_ms,
            tokens_used: shadowResult.tokens_used,
            api_calls: 1,
            memory_retrievals: 1
          })
        });

        if (shadowStoreResponse.ok) {
          const shadowStoreResult = await shadowStoreResponse.json();
          ctx.logger.info(`Shadow prediction stored successfully`, {
            shadow_id: shadowStoreResult.shadow_id,
            shadow_run_id: shadowRunId,
            expert_id,
            shadow_model: shadowResult.shadow_model,
            schema_valid: shadowStoreResult.schema_valid
          });

          // Update shadow result with storage confirmation
          shadowResult.shadow_id = shadowStoreResult.shadow_id;
          shadowResult.shadow_run_id = shadowRunId;
          shadowResult.stored = true;
        } else {
          ctx.logger.error(`Shadow prediction storage failed: ${shadowStoreResponse.status}`);
          shadowResult.stored = false;
          shadowResult.storage_error = `HTTP ${shadowStoreResponse.status}`;
        }
      } catch (shadowError) {
        ctx.logger.error(`Shadow prediction storage error:`, shadowError);
        shadowResult.stored = false;
        shadowResult.storage_error = shadowError.message;
      }
    }

    return {
      expert_id,
      success: true,
      duration_ms: Date.now() - expertStartTime,
      schema_valid: storeResult.schema_valid || false,
      retrieval_ms: retrievalMs,
      llm_ms: llmMs,
      validation_ms: validationMs,
      shadow_result: shadowResult
    };

  } catch (error) {
    ctx.logger.error(`Expert ${expert_id} processing failed:`, error);
    return {
      expert_id,
      success: false,
      duration_ms: Date.now() - expertStartTime,
      schema_valid: false,
      error: error.message
    };
  }
}

async function generateExpertPredictions(
  expert_id: string,
  contextData: any,
  ctx: AgentContext
): Promise<any> {
  const startTime = Date.now();
  const maxDuration = 45000; // 45 second timeout
  const maxToolCalls = 10;
  let toolCallCount = 0;

  try {
    // LangGraph flow: Draft → Critic/Repair (≤2 loops)
    let currentDraft = null;
    let finalPredictions = null;
    let loopCount = 0;
    const maxLoops = 2;

    while (loopCount < maxLoops && (Date.now() - startTime) < maxDuration) {
      loopCount++;

      // Step 1: Generate draft predictions
      ctx.logger.info(`Generating draft ${loopCount} for ${expert_id}`);

      const draftPrompt = buildDraftPrompt(expert_id, contextData, currentDraft);
      const draftResponse = await callLLMWithBudget(
        expert_id,
        draftPrompt,
        ctx,
        maxDuration - (Date.now() - startTime),
        maxToolCalls - toolCallCount
      );

      if (!draftResponse) {
        throw new Error('Draft generation failed - timeout or budget exceeded');
      }

      toolCallCount++;
      currentDraft = draftResponse;

      // Step 2: Validate schema compliance
      const schemaValidation = validatePredictionSchema(currentDraft);

      if (schemaValidation.isValid) {
        finalPredictions = currentDraft;
        ctx.logger.info(`Schema validation passed on loop ${loopCount} for ${expert_id}`);
        break;
      }

      // Step 3: Critic/Repair if schema invalid and we have loops left
      if (loopCount < maxLoops && (Date.now() - startTime) < maxDuration - 5000) {
        ctx.logger.info(`Schema validation failed, running critic/repair for ${expert_id}`);

        const criticPrompt = buildCriticPrompt(expert_id, currentDraft, schemaValidation.errors);
        const criticResponse = await callLLMWithBudget(
          expert_id,
          criticPrompt,
          ctx,
          maxDuration - (Date.now() - startTime),
          maxToolCalls - toolCallCount
        );

        if (criticResponse) {
          toolCallCount++;
          currentDraft = criticResponse;
        }
      }
    }

    // Fallback if no valid predictions after loops
    if (!finalPredictions) {
      ctx.logger.warn(`Falling back to degraded mode for ${expert_id}`);
      finalPredictions = generateDegradedPredictions(expert_id, contextData);
    }

    const processingTime = Date.now() - startTime;

    return {
      expert_id,
      game_id: contextData.game_id,
      overall: finalPredictions.overall || generateDefaultOverall(contextData),
      predictions: finalPredictions.predictions || [],
      processing_metadata: {
        loops_used: loopCount,
        tool_calls_used: toolCallCount,
        processing_time_ms: processingTime,
        degraded_mode: !finalPredictions.predictions || finalPredictions.predictions.length < 83,
        schema_valid: finalPredictions.predictions && finalPredictions.predictions.length === 83
      }
    };

  } catch (error) {
    ctx.logger.error(`Expert prediction generation failed for ${expert_id}:`, error);

    // Return degraded fallback
    return {
      expert_id,
      game_id: contextData.game_id,
      overall: generateDefaultOverall(contextData),
      predictions: generateDegradedPredictions(expert_id, contextData).predictions || [],
      processing_metadata: {
        loops_used: 0,
        tool_calls_used: toolCallCount,
        processing_time_ms: Date.now() - startTime,
        degraded_mode: true,
        schema_valid: false,
        error: error.message
      }
    };
  }
}

async function generateShadowPredictions(
  expert_id: string,
  contextData: any,
  shadow_model: string,
  ctx: AgentContext
): Promise<any> {
  const shadowStartTime = Date.now();

  try {
    ctx.logger.info(`Running shadow model ${shadow_model} for expert ${expert_id}`);

    const openrouterApiKey = process.env.OPENROUTER_API_KEY;
    if (!openrouterApiKey) {
      throw new Error('OpenRouter API key not found for shadow model');
    }

    // Generate shadow predictions using alternate model via OpenRouter
    const shadowPrompt = buildDraftPrompt(expert_id, contextData);
    const shadowTemperature = getTemperatureForExpert(expert_id);

    // Call OpenRouter API for shadow model
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openrouterApiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/your-repo/nfl-predictor-api',
        'X-Title': 'NFL Expert Council Betting System - Shadow'
      },
      body: JSON.stringify({
        model: shadow_model,
        messages: [
          {
            role: 'system',
            content: getSystemPromptForExpert(expert_id) + '\n\nNOTE: This is a shadow run for A/B testing.'
          },
          {
            role: 'user',
            content: shadowPrompt
          }
        ],
        max_tokens: 4000,
        temperature: shadowTemperature,
        top_p: 0.9,
        stream: false
      })
    });

    if (!response.ok) {
      throw new Error(`Shadow model API error: ${response.status}`);
    }

    const data = await response.json();
    const shadowResponseText = data.choices[0].message.content;

    let shadowPredictions = null;
    try {
      // Try to parse JSON directly
      shadowPredictions = JSON.parse(shadowResponseText);
    } catch (parseError) {
      // Try to extract JSON from markdown if wrapped
      const jsonMatch = shadowResponseText.match(/```json\s*([\s\S]*?)\s*```/);
      if (jsonMatch) {
        shadowPredictions = JSON.parse(jsonMatch[1]);
      } else {
        throw parseError;
      }
    }

    const processingTime = Date.now() - shadowStartTime;

    // Validate shadow predictions
    const schemaValidation = validatePredictionSchema(shadowPredictions);

    return {
      shadow_model,
      expert_id,
      game_id: contextData.game_id,
      predictions: shadowPredictions,
      processing_time_ms: processingTime,
      schema_valid: schemaValidation.isValid,
      validation_errors: schemaValidation.errors,
      tokens_used: data.usage?.total_tokens || estimateTokenUsage(shadowPrompt, shadowResponseText),
      success: true
    };

  } catch (error) {
    ctx.logger.error(`Shadow model ${shadow_model} failed for ${expert_id}:`, error);

    return {
      shadow_model,
      expert_id,
      game_id: contextData.game_id,
      predictions: null,
      processing_time_ms: Date.now() - shadowStartTime,
      schema_valid: false,
      validation_errors: [error.message],
      tokens_used: 0,
      success: false,
      error: error.message
    };
  }
}

// OpenRouter LLM Integration and Budget Management
async function callLLMWithBudget(
  expert_id: string,
  prompt: string,
  ctx: AgentContext,
  timeoutMs: number,
  maxToolCalls: number
): Promise<any> {
  if (maxToolCalls <= 0 || timeoutMs <= 0) {
    return null;
  }

  try {
    const model = getModelForExpert(expert_id);
    const temperature = getTemperatureForExpert(expert_id);
    const openrouterApiKey = process.env.OPENROUTER_API_KEY;

    if (!openrouterApiKey) {
      ctx.logger.error(`OpenRouter API key not found for ${expert_id}`);
      return generateMockResponse(expert_id, prompt);
    }

    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('LLM call timeout')), timeoutMs)
    );

    // OpenRouter API call
    const llmPromise = fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openrouterApiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/your-repo/nfl-predictor-api',
        'X-Title': 'NFL Expert Council Betting System'
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: 'system',
            content: getSystemPromptForExpert(expert_id)
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 4000,
        temperature,
        top_p: 0.9,
        stream: false
      })
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error(`OpenRouter API error: ${response.status}`);
      }
      const data = await response.json();
      return data.choices[0].message.content;
    });

    const response = await Promise.race([llmPromise, timeoutPromise]);

    // Parse JSON response
    if (typeof response === 'string') {
      try {
        return JSON.parse(response);
      } catch (parseError) {
        ctx.logger.error(`JSON parse failed for ${expert_id}:`, parseError);
        // Try to extract JSON from response if it's wrapped in markdown
        const jsonMatch = response.match(/```json\s*([\s\S]*?)\s*```/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[1]);
        }
        throw parseError;
      }
    }

    return response;

  } catch (error) {
    ctx.logger.error(`OpenRouter LLM call failed for ${expert_id}:`, error);
    return null;
  }
}

function getModelForExpert(expert_id: string): string {
  // Model routing based on expert personality - using OpenRouter models
  const modelMap = {
    'conservative_analyzer': process.env.CONSERVATIVE_ANALYZER_MODEL || 'anthropic/claude-3.5-sonnet',
    'momentum_rider': process.env.MOMENTUM_RIDER_MODEL || 'deepseek/deepseek-chat',
    'contrarian_rebel': process.env.CONTRARIAN_REBEL_MODEL || 'deepseek/deepseek-chat',
    'value_hunter': process.env.VALUE_HUNTER_MODEL || 'anthropic/claude-3.5-sonnet',
    'risk_taking_gambler': 'deepseek/deepseek-chat' // Legacy support
  };

  return modelMap[expert_id] || 'anthropic/claude-3.5-sonnet';
}

function getTemperatureForExpert(expert_id: string): number {
  // Temperature based on expert personality
  const temperatureMap = {
    'conservative_analyzer': 0.3,
    'momentum_rider': 0.5,
    'contrarian_rebel': 0.7,
    'value_hunter': 0.4,
    'risk_taking_gambler': 0.8 // Legacy support
  };

  return temperatureMap[expert_id] || 0.5;
}

function getSystemPromptForExpert(expert_id: string): string {
  const persona = getExpertPersona(expert_id);

  return `You are ${persona.name}, ${persona.description}.

PERSONALITY: ${persona.guidance}

CRITICAL INSTRUCTIONS:
- You MUST return ONLY valid JSON, no other text or markdown
- Generate exactly 83 NFL predictions
- Follow the exact schema structure provided
- Use only valid prediction categories
- Ensure pred_type matches value type (binary=boolean, numeric=number, enum=string)
- All confidence values must be between 0 and 1
- All stake_units must be ≥ 0
- Reference memory IDs in "why" arrays

Your expertise and personality should guide your predictions, but you must strictly follow the JSON format requirements.`;
}

// Prompt Building Functions
function buildDraftPrompt(expert_id: string, contextData: any, previousDraft?: any): string {
  const persona = getExpertPersona(expert_id);
  const memoryContext = formatMemoryContext(contextData);
  const gameContext = formatGameContext(contextData);

  let prompt = `You are ${persona.name}, ${persona.description}

GAME CONTEXT:
${gameContext}

MEMORY CONTEXT:
${memoryContext}

TASK: Generate exactly 83 NFL predictions for this game in valid JSON format.

RESPONSE FORMAT: You must return a JSON object with this exact structure:
{
  "overall": {
    "winner_team_id": "string (team abbreviation)",
    "home_win_prob": number (0-1),
    "away_win_prob": number (0-1),
    "overall_confidence": number (0-1),
    "recency_alpha_used": number (0-1)
  },
  "predictions": [
    // Exactly 83 prediction objects with this structure:
    {
      "category": "string (must be from valid categories)",
      "subject": "string",
      "pred_type": "binary|enum|numeric",
      "value": boolean|number|string (based on pred_type),
      "confidence": number (0-1),
      "stake_units": number (≥0),
      "odds": {"type": "american|decimal|fraction", "value": number|string},
      "why": [{"memory_id": "string", "weight": number}]
    }
  ]
}

PERSONALITY GUIDANCE:
${persona.guidance}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON, no other text
- Include exactly 83 predictions
- Use only valid categories from the schema
- Ensure pred_type matches value type (binary=boolean, numeric=number, enum=string)
- All confidence values between 0 and 1
- All stake_units ≥ 0
- Reference memory_ids from the context in "why" arrays`;

  if (previousDraft) {
    prompt += `\n\nPREVIOUS DRAFT (for improvement):\n${JSON.stringify(previousDraft, null, 2)}`;
  }

  return prompt;
}

function buildCriticPrompt(expert_id: string, draft: any, errors: string[]): string {
  const persona = getExpertPersona(expert_id);

  return `You are ${persona.name}, acting as a critic to fix your prediction draft.

VALIDATION ERRORS FOUND:
${errors.join('\n')}

CURRENT DRAFT:
${JSON.stringify(draft, null, 2)}

TASK: Fix the validation errors and return a corrected JSON prediction bundle.

REQUIREMENTS:
- Fix all validation errors listed above
- Maintain the same prediction logic and reasoning
- Return ONLY valid JSON, no other text
- Ensure exactly 83 predictions with valid categories
- Keep the same overall structure and format

Return the corrected JSON:`;
}

function getExpertPersona(expert_id: string) {
  const personas = {
    'conservative_analyzer': {
      name: 'The Conservative Analyzer',
      description: 'a methodical expert who relies on statistical analysis and historical patterns',
      guidance: 'Focus on proven statistical trends, avoid high-risk predictions, emphasize data-driven decisions with moderate confidence levels.'
    },
    'risk_taking_gambler': {
      name: 'The Risk Taking Gambler',
      description: 'an aggressive expert who seeks high-reward opportunities and contrarian plays',
      guidance: 'Look for upset potential, high-value bets, and contrarian opportunities. Use higher stake units on confident predictions.'
    },
    'contrarian_rebel': {
      name: 'The Contrarian Rebel',
      description: 'an independent thinker who questions popular narratives and finds value in unpopular positions',
      guidance: 'Challenge conventional wisdom, look for market inefficiencies, and bet against public sentiment when data supports it.'
    },
    'value_hunter': {
      name: 'The Value Hunter',
      description: 'a disciplined expert focused on finding mispriced betting opportunities',
      guidance: 'Identify value bets where odds don\'t match true probability, focus on expected value over win rate.'
    }
  };

  return personas[expert_id] || personas['conservative_analyzer'];
}

function formatMemoryContext(contextData: any): string {
  const memories = contextData.episodic_memories || [];
  if (memories.length === 0) {
    return "No relevant memories found.";
  }

  return memories.slice(0, 5).map((mem, i) =>
    `Memory ${i+1} (ID: ${mem.memory_id}, Score: ${mem.combined_score}): ${mem.content}`
  ).join('\n\n');
}

function formatGameContext(contextData: any): string {
  return `Game: ${contextData.away_team} @ ${contextData.home_team}
Season: ${contextData.season}, Week: ${contextData.week}
Weather: ${contextData.weather || 'Unknown'}
Venue: ${contextData.venue || 'Unknown'}`;
}

// Schema Validation
function validatePredictionSchema(predictions: any): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  try {
    // Check overall structure
    if (!predictions.overall) {
      errors.push("Missing 'overall' field");
    }

    if (!predictions.predictions || !Array.isArray(predictions.predictions)) {
      errors.push("Missing or invalid 'predictions' array");
      return { isValid: false, errors };
    }

    // Check prediction count
    if (predictions.predictions.length !== 83) {
      errors.push(`Expected 83 predictions, got ${predictions.predictions.length}`);
    }

    // Validate each prediction
    predictions.predictions.forEach((pred, i) => {
      if (!pred.category) errors.push(`Prediction ${i}: missing category`);
      if (!pred.pred_type) errors.push(`Prediction ${i}: missing pred_type`);
      if (pred.confidence < 0 || pred.confidence > 1) errors.push(`Prediction ${i}: invalid confidence`);
      if (pred.stake_units < 0) errors.push(`Prediction ${i}: negative stake_units`);

      // Type validation
      if (pred.pred_type === 'binary' && typeof pred.value !== 'boolean') {
        errors.push(`Prediction ${i}: binary pred_type requires boolean value`);
      }
      if (pred.pred_type === 'numeric' && typeof pred.value !== 'number') {
        errors.push(`Prediction ${i}: numeric pred_type requires number value`);
      }
      if (pred.pred_type === 'enum' && typeof pred.value !== 'string') {
        errors.push(`Prediction ${i}: enum pred_type requires string value`);
      }
    });

  } catch (error) {
    errors.push(`Schema validation error: ${error.message}`);
  }

  return { isValid: errors.length === 0, errors };
}

// Fallback Functions
function generateDegradedPredictions(expert_id: string, contextData: any) {
  // Generate minimal valid predictions when LLM fails
  const predictions = [];

  // Create basic predictions for key categories
  const basicCategories = [
    'game_winner', 'spread_full_game', 'total_full_game', 'first_half_winner',
    'qb_passing_yards', 'rb_rushing_yards', 'weather_impact_score'
  ];

  basicCategories.forEach((category, i) => {
    predictions.push({
      category,
      subject: `Degraded prediction for ${category}`,
      pred_type: i % 3 === 0 ? 'binary' : (i % 3 === 1 ? 'numeric' : 'enum'),
      value: i % 3 === 0 ? true : (i % 3 === 1 ? 20 + i : 'option_a'),
      confidence: 0.5,
      stake_units: 0.5,
      odds: { type: 'american', value: -110 },
      why: []
    });
  });

  // Fill remaining slots to reach 83
  while (predictions.length < 83) {
    const i = predictions.length;
    predictions.push({
      category: `placeholder_${i}`,
      subject: `Placeholder prediction ${i}`,
      pred_type: 'binary',
      value: true,
      confidence: 0.5,
      stake_units: 0.1,
      odds: { type: 'american', value: -110 },
      why: []
    });
  }

  return { predictions };
}

function generateDefaultOverall(contextData: any) {
  return {
    winner_team_id: contextData.home_team || 'HOME',
    home_win_prob: 0.5,
    away_win_prob: 0.5,
    overall_confidence: 0.5,
    recency_alpha_used: 0.8
  };
}

function generateMockResponse(expert_id: string, prompt: string): any {
  // Mock response when no LLM is available
  return {
    overall: {
      winner_team_id: 'HOME',
      home_win_prob: 0.55,
      away_win_prob: 0.45,
      overall_confidence: 0.65,
      recency_alpha_used: 0.8
    },
    predictions: generateDegradedPredictions(expert_id, {}).predictions
  };
}

function estimateTokenUsage(prompt: string, response: any): number {
  // Rough token estimation (4 chars per token average)
  const promptTokens = Math.ceil(prompt.length / 4);
  const responseText = typeof response === 'string' ? response : JSON.stringify(response);
  const responseTokens = Math.ceil(responseText.length / 4);

  return promptTokens + responseTokens;
}

export const welcome = () => {
  return {
    welcome: `
# GameOrchestrator Agent

This agent orchestrates parallel expert prediction generation for NFL games.

## Features:
- Parallel expert processing
- Memory context retrieval
- Schema validation
- Shadow model support
- Comprehensive telemetry

## Usage:
Send a JSON payload with game_id, expert_ids, and configuration options.
    `,
    prompts: [
      {
        data: JSON.stringify({
          game_id: "game_123",
          expert_ids: ["conservative_analyzer", "risk_taking_gambler"],
          api_base_url: "http://localhost:8000/api",
          enable_shadow_runs: false,
          shadow_models: {},
          orchestration_id: "test_orch_001",
          run_id: "run_2025_pilot4"
        }),
        contentType: 'application/json'
      }
    ]
  };
};
