/**
 * Agentuity ReflectionAgent
 *
 * Optional post-game reflection for expert learning and factor adjustment insights
 * Generates structured reflection JSON for storage in Neo4j write-behind
 */

import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";

interface ReflectionPayload {
  game_id: string;
  expert_id: string;
  game_outcome: any;
  expert_predictions: any;
}

interface ReflectionResult {
  expert_id: string;
  game_id: string;
  lessons_learned: string[];
  factor_adjustments: {
    factor_name: string;
    direction: 'increase' | 'decrease' | 'maintain';
    confidence: number;
    reasoning: string;
  }[];
  prediction_quality_assessment: {
    best_predictions: string[];
    worst_predictions: string[];
    surprise_outcomes: string[];
  };
  meta_insights: {
    overconfidence_detected: boolean;
    bias_patterns: string[];
    improvement_areas: string[];
  };
}

export default async function ReflectionAgent(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  try {
    const payload = await req.data.json() as ReflectionPayload;
    const { game_id, expert_id, game_outcome, expert_predictions } = payload;

    ctx.logger.info(`Generating reflection for expert ${expert_id} on game ${game_id}`);

    // Generate structured reflection
    const reflection = await generateReflection(
      expert_id,
      game_id,
      game_outcome,
      expert_predictions,
      ctx
    );

    ctx.logger.info(`Reflection completed for ${expert_id}`, {
      lessons_count: reflection.lessons_learned.length,
      factor_adjustments_count: reflection.factor_adjustments.length,
      overconfidence_detected: reflection.meta_insights.overconfidence_detected
    });

    return resp.json({
      success: true,
      reflection,
      generated_at: new Date().toISOString()
    });

  } catch (error) {
    ctx.logger.error('Reflection generation failed:', error);
    return resp.json({
      success: false,
      error: 'Reflection generation failed',
      message: error.message
    }, { status: 500 });
  }
}

async function generateReflection(
  expert_id: string,
  game_id: string,
  game_outcome: any,
  expert_predictions: any,
  ctx: AgentContext
): Promise<ReflectionResult> {
  const startTime = Date.now();
  const maxDuration = 30000; // 30 second timeout for reflection
  const maxToolCalls = 5;
  let toolCallCount = 0;

  try {
    // LangGraph flow for reflection: Draft → Critic/Repair (≤2 loops)
    let currentReflection = null;
    let finalReflection = null;
    let loopCount = 0;
    const maxLoops = 2;

    // Analyze prediction accuracy first
    const predictionAnalysis = analyzePredictionAccuracy(expert_predictions, game_outcome);

    while (loopCount < maxLoops && (Date.now() - startTime) < maxDuration) {
      loopCount++;

      // Step 1: Generate draft reflection
      ctx.logger.info(`Generating reflection draft ${loopCount} for ${expert_id}`);

      const reflectionPrompt = buildReflectionPrompt(expert_id, game_id, predictionAnalysis, currentReflection);
      const reflectionResponse = await callReflectionLLM(
        expert_id,
        reflectionPrompt,
        ctx,
        maxDuration - (Date.now() - startTime),
        maxToolCalls - toolCallCount
      );

      if (!reflectionResponse) {
        throw new Error('Reflection generation failed - timeout or budget exceeded');
      }

      toolCallCount++;
      currentReflection = reflectionResponse;

      // Step 2: Validate reflection structure
      const reflectionValidation = validateReflectionStructure(currentReflection);

      if (reflectionValidation.isValid) {
        finalReflection = currentReflection;
        ctx.logger.info(`Reflection validation passed on loop ${loopCount} for ${expert_id}`);
        break;
      }

      // Step 3: Critic/Repair if invalid and we have loops left
      if (loopCount < maxLoops && (Date.now() - startTime) < maxDuration - 3000) {
        ctx.logger.info(`Reflection validation failed, running critic/repair for ${expert_id}`);

        const criticPrompt = buildReflectionCriticPrompt(expert_id, currentReflection, reflectionValidation.errors);
        const criticResponse = await callReflectionLLM(
          expert_id,
          criticPrompt,
          ctx,
          maxDuration - (Date.now() - startTime),
          maxToolCalls - toolCallCount
        );

        if (criticResponse) {
          toolCallCount++;
          currentReflection = criticResponse;
        }
      }
    }

    // Fallback if no valid reflection after loops
    if (!finalReflection) {
      ctx.logger.warn(`Falling back to basic reflection for ${expert_id}`);
      finalReflection = generateBasicReflection(expert_id, game_id, predictionAnalysis);
    }

    const processingTime = Date.now() - startTime;

    return {
      expert_id,
      game_id,
      lessons_learned: finalReflection.lessons_learned || [],
      factor_adjustments: finalReflection.factor_adjustments || [],
      prediction_quality_assessment: finalReflection.prediction_quality_assessment || {
        best_predictions: [],
        worst_predictions: [],
        surprise_outcomes: []
      },
      meta_insights: finalReflection.meta_insights || {
        overconfidence_detected: false,
        bias_patterns: [],
        improvement_areas: []
      },
      processing_metadata: {
        loops_used: loopCount,
        tool_calls_used: toolCallCount,
        processing_time_ms: processingTime,
        degraded_mode: !finalReflection.lessons_learned
      }
    };

  } catch (error) {
    ctx.logger.error(`Reflection generation failed for ${expert_id}:`, error);

    // Return basic fallback reflection
    const predictionAnalysis = analyzePredictionAccuracy(expert_predictions, game_outcome);
    return generateBasicReflection(expert_id, game_id, predictionAnalysis);
  }
}

function analyzePredictionAccuracy(predictions: any, outcome: any) {
  // Analyze which predictions were accurate vs inaccurate
  const analysis = {
    correct_predictions: [],
    incorrect_predictions: [],
    close_misses: [],
    major_errors: [],
    confidence_calibration: []
  };

  // TODO: Implement detailed prediction vs outcome analysis
  // This would compare each of the 83 predictions against actual results

  return analysis;
}

function generateLessonsLearned(analysis: any, expert_id: string): string[] {
  const lessons = [];

  // Generate persona-specific lessons based on analysis
  switch (expert_id) {
    case 'conservative_analyzer':
      if (analysis.major_errors.length > 0) {
        lessons.push("Conservative approach may have missed key risk factors");
      }
      if (analysis.correct_predictions.length > analysis.incorrect_predictions.length) {
        lessons.push("Methodical analysis approach validated by outcomes");
      }
      break;

    case 'risk_taking_gambler':
      if (analysis.close_misses.length > 0) {
        lessons.push("High-risk predictions showed potential but need refinement");
      }
      break;

    case 'contrarian_rebel':
      lessons.push("Contrarian positions should be evaluated against public sentiment accuracy");
      break;

    default:
      lessons.push("General prediction accuracy patterns identified for future improvement");
  }

  return lessons;
}

function suggestFactorAdjustments(analysis: any, expert_id: string) {
  const adjustments = [];

  // Example factor adjustments based on analysis
  if (analysis.incorrect_predictions.some(p => p.category === 'offensive_efficiency')) {
    adjustments.push({
      factor_name: 'offensive_efficiency',
      direction: 'decrease' as const,
      confidence: 0.7,
      reasoning: 'Offensive efficiency predictions showed systematic overestimation'
    });
  }

  if (analysis.correct_predictions.some(p => p.category === 'momentum')) {
    adjustments.push({
      factor_name: 'momentum',
      direction: 'increase' as const,
      confidence: 0.6,
      reasoning: 'Momentum-based predictions showed good accuracy'
    });
  }

  return adjustments;
}

function assessPredictionQuality(analysis: any) {
  return {
    best_predictions: analysis.correct_predictions.slice(0, 3).map(p => p.category),
    worst_predictions: analysis.major_errors.slice(0, 3).map(p => p.category),
    surprise_outcomes: analysis.close_misses.filter(p => p.confidence > 0.8).map(p => p.category)
  };
}

function generateMetaInsights(analysis: any, predictions: any) {
  const avgConfidence = predictions.predictions?.reduce((sum, p) => sum + p.confidence, 0) / (predictions.predictions?.length || 1);
  const actualAccuracy = analysis.correct_predictions.length / (analysis.correct_predictions.length + analysis.incorrect_predictions.length);

  return {
    overconfidence_detected: avgConfidence > actualAccuracy + 0.1,
    bias_patterns: identifyBiasPatterns(analysis),
    improvement_areas: identifyImprovementAreas(analysis)
  };
}

function identifyBiasPatterns(analysis: any): string[] {
  const patterns = [];

  // Look for systematic biases
  if (analysis.incorrect_predictions.filter(p => p.category.includes('total')).length > 2) {
    patterns.push('Systematic bias in total scoring predictions');
  }

  if (analysis.incorrect_predictions.filter(p => p.category.includes('home')).length > 2) {
    patterns.push('Potential home field advantage miscalibration');
  }

  return patterns;
}

function identifyImprovementAreas(analysis: any): string[] {
  const areas = [];

  if (analysis.major_errors.length > 0) {
    areas.push('Confidence calibration needs adjustment');
  }

  if (analysis.close_misses.length > analysis.correct_predictions.length) {
    areas.push('Prediction precision could be improved');
  }

  return areas;
}

// LLM Integration for Reflection
async function callReflectionLLM(
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
    const model = 'anthropic/claude-3-5-sonnet-20241022'; // Use consistent model for reflection
    const temperature = 0.4; // Lower temperature for structured reflection

    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Reflection LLM call timeout')), timeoutMs)
    );

    // Make LLM call with timeout
    const llmPromise = ctx.llm?.generate({
      model,
      prompt,
      temperature,
      max_tokens: 2000,
      response_format: { type: "json_object" }
    });

    if (!llmPromise) {
      // Fallback if no LLM available
      ctx.logger.warn(`No LLM available for reflection ${expert_id}, using mock response`);
      return generateMockReflection(expert_id);
    }

    const response = await Promise.race([llmPromise, timeoutPromise]);

    // Parse JSON response
    if (typeof response === 'string') {
      return JSON.parse(response);
    } else if (response?.content) {
      return JSON.parse(response.content);
    }

    return response;

  } catch (error) {
    ctx.logger.error(`Reflection LLM call failed for ${expert_id}:`, error);
    return null;
  }
}

function buildReflectionPrompt(expert_id: string, game_id: string, analysis: any, previousReflection?: any): string {
  const persona = getReflectionPersona(expert_id);

  let prompt = `You are ${persona.name}, reflecting on your NFL prediction performance.

GAME: ${game_id}

PREDICTION ANALYSIS:
- Correct predictions: ${analysis.correct_predictions.length}
- Incorrect predictions: ${analysis.incorrect_predictions.length}
- Close misses: ${analysis.close_misses.length}
- Major errors: ${analysis.major_errors.length}

DETAILED ANALYSIS:
${JSON.stringify(analysis, null, 2)}

TASK: Generate a structured reflection in JSON format to improve future predictions.

RESPONSE FORMAT: Return ONLY valid JSON with this structure:
{
  "lessons_learned": [
    "string - specific lessons from this game"
  ],
  "factor_adjustments": [
    {
      "factor_name": "string",
      "direction": "increase|decrease|maintain",
      "confidence": number (0-1),
      "reasoning": "string"
    }
  ],
  "prediction_quality_assessment": {
    "best_predictions": ["category names"],
    "worst_predictions": ["category names"],
    "surprise_outcomes": ["category names"]
  },
  "meta_insights": {
    "overconfidence_detected": boolean,
    "bias_patterns": ["string descriptions"],
    "improvement_areas": ["string descriptions"]
  }
}

REFLECTION GUIDANCE:
${persona.guidance}

FOCUS AREAS:
- What patterns led to successful vs failed predictions?
- Which factors should be weighted differently?
- What biases or overconfidence patterns emerged?
- How can prediction accuracy be improved?`;

  if (previousReflection) {
    prompt += `\n\nPREVIOUS REFLECTION (for improvement):\n${JSON.stringify(previousReflection, null, 2)}`;
  }

  return prompt;
}

function buildReflectionCriticPrompt(expert_id: string, reflection: any, errors: string[]): string {
  return `You are ${getReflectionPersona(expert_id).name}, acting as a critic to fix your reflection.

VALIDATION ERRORS FOUND:
${errors.join('\n')}

CURRENT REFLECTION:
${JSON.stringify(reflection, null, 2)}

TASK: Fix the validation errors and return a corrected JSON reflection.

REQUIREMENTS:
- Fix all validation errors listed above
- Maintain the same analytical insights and reasoning
- Return ONLY valid JSON, no other text
- Ensure all required fields are present and properly formatted

Return the corrected JSON:`;
}

function getReflectionPersona(expert_id: string) {
  const personas = {
    'conservative_analyzer': {
      name: 'The Conservative Analyzer',
      guidance: 'Focus on systematic analysis of what statistical patterns held vs failed. Identify when conservative approach was validated or when it missed opportunities.'
    },
    'risk_taking_gambler': {
      name: 'The Risk Taking Gambler',
      guidance: 'Analyze which high-risk bets paid off vs failed. Look for patterns in upset detection and value identification. Assess risk calibration.'
    },
    'contrarian_rebel': {
      name: 'The Contrarian Rebel',
      guidance: 'Examine when contrarian positions were validated vs when conventional wisdom was correct. Identify market efficiency patterns.'
    },
    'value_hunter': {
      name: 'The Value Hunter',
      guidance: 'Focus on expected value accuracy. Analyze which value bets hit vs missed and why. Look for systematic mispricing patterns.'
    }
  };

  return personas[expert_id] || personas['conservative_analyzer'];
}

function validateReflectionStructure(reflection: any): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  try {
    // Check required fields
    if (!reflection.lessons_learned || !Array.isArray(reflection.lessons_learned)) {
      errors.push("Missing or invalid 'lessons_learned' array");
    }

    if (!reflection.factor_adjustments || !Array.isArray(reflection.factor_adjustments)) {
      errors.push("Missing or invalid 'factor_adjustments' array");
    }

    if (!reflection.prediction_quality_assessment) {
      errors.push("Missing 'prediction_quality_assessment' object");
    }

    if (!reflection.meta_insights) {
      errors.push("Missing 'meta_insights' object");
    }

    // Validate factor adjustments structure
    if (reflection.factor_adjustments) {
      reflection.factor_adjustments.forEach((adj, i) => {
        if (!adj.factor_name) errors.push(`Factor adjustment ${i}: missing factor_name`);
        if (!['increase', 'decrease', 'maintain'].includes(adj.direction)) {
          errors.push(`Factor adjustment ${i}: invalid direction`);
        }
        if (adj.confidence < 0 || adj.confidence > 1) {
          errors.push(`Factor adjustment ${i}: invalid confidence`);
        }
      });
    }

  } catch (error) {
    errors.push(`Reflection validation error: ${error.message}`);
  }

  return { isValid: errors.length === 0, errors };
}

function generateBasicReflection(expert_id: string, game_id: string, analysis: any): ReflectionResult {
  // Generate basic reflection when LLM fails
  const correctCount = analysis.correct_predictions.length;
  const incorrectCount = analysis.incorrect_predictions.length;
  const accuracy = correctCount / (correctCount + incorrectCount);

  return {
    expert_id,
    game_id,
    lessons_learned: [
      `Achieved ${(accuracy * 100).toFixed(1)}% accuracy on ${game_id}`,
      correctCount > incorrectCount ?
        "Overall prediction approach was effective" :
        "Prediction approach needs refinement"
    ],
    factor_adjustments: [
      {
        factor_name: "confidence_calibration",
        direction: accuracy > 0.6 ? "maintain" : "decrease",
        confidence: 0.6,
        reasoning: `Based on ${(accuracy * 100).toFixed(1)}% accuracy rate`
      }
    ],
    prediction_quality_assessment: {
      best_predictions: analysis.correct_predictions.slice(0, 3).map(p => p.category || 'unknown'),
      worst_predictions: analysis.major_errors.slice(0, 3).map(p => p.category || 'unknown'),
      surprise_outcomes: analysis.close_misses.slice(0, 2).map(p => p.category || 'unknown')
    },
    meta_insights: {
      overconfidence_detected: accuracy < 0.5,
      bias_patterns: incorrectCount > correctCount ? ["Systematic prediction bias detected"] : [],
      improvement_areas: accuracy < 0.6 ? ["Confidence calibration", "Factor weighting"] : []
    }
  };
}

function generateMockReflection(expert_id: string): any {
  return {
    lessons_learned: [
      "Mock reflection generated due to LLM unavailability",
      "Need to analyze prediction patterns when LLM is available"
    ],
    factor_adjustments: [
      {
        factor_name: "mock_factor",
        direction: "maintain",
        confidence: 0.5,
        reasoning: "Mock adjustment for testing"
      }
    ],
    prediction_quality_assessment: {
      best_predictions: ["game_winner"],
      worst_predictions: ["total_full_game"],
      surprise_outcomes: ["spread_full_game"]
    },
    meta_insights: {
      overconfidence_detected: false,
      bias_patterns: [],
      improvement_areas: ["LLM integration"]
    }
  };
}

export const welcome = () => {
  return {
    welcome: `
# ReflectionAgent

This agent generates post-game reflections for expert learning and improvement.

## Features:
- Structured lesson extraction
- Factor adjustment suggestions
- Prediction quality assessment
- Meta-insight generation
- Bias pattern detection

## Usage:
Send game outcome and expert predictions to generate reflection insights.
    `,
    prompts: [
      {
        data: JSON.stringify({
          game_id: "game_123",
          expert_id: "conservative_analyzer",
          game_outcome: {
            home_score: 24,
            away_score: 17,
            winner: "home"
          },
          expert_predictions: {
            predictions: [
              {
                category: "game_winner",
                value: "home",
                confidence: 0.75
              }
            ]
          }
        }),
        contentType: 'application/json'
      }
    ]
  };
};
