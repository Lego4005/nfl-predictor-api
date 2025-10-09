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

  // Analyze prediction accuracy vs outcomes
  const predictionAnalysis = analyzePredictionAccuracy(expert_predictions, game_outcome);

  // Generate lessons learned
  const lessons = generateLessonsLearned(predictionAnalysis, expert_id);

  // Suggest factor adjustments
  const factorAdjustments = suggestFactorAdjustments(predictionAnalysis, expert_id);

  // Assess prediction quality
  const qualityAssessment = assessPredictionQuality(predictionAnalysis);

  // Generate meta-insights
  const metaInsights = generateMetaInsights(predictionAnalysis, expert_predictions);

  return {
    expert_id,
    game_id,
    lessons_learned: lessons,
    factor_adjustments: factorAdjustments,
    prediction_quality_assessment: qualityAssessment,
    meta_insights: metaInsights
  };
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
