/**
 * NFL Prediction Expert Personalities - Standardized Framework
 * Defines 15 personality-driven AI experts with consistent naming across all system components
 * This file aligns with the backend ML models in personality_driven_experts.py
 */

import { Expert, ExpertType, PredictionCategory } from "@/types/predictions";

export interface PersonalityTraits {
  risk_tolerance: number; // 0.0-1.0
  analytics_trust: number; // 0.0-1.0
  contrarian_tendency: number; // 0.0-1.0
  optimism: number; // 0.0-1.0
  chaos_comfort: number; // 0.0-1.0
  confidence_level: number; // 0.0-1.0
  market_trust: number; // 0.0-1.0
  value_seeking: number; // 0.0-1.0
}

export interface ExpertPersonality extends Expert {
  personality_traits: PersonalityTraits;
  decision_making_style: string;
  risk_tolerance: "conservative" | "moderate" | "aggressive";
  primary_expertise: PredictionCategory[];
  archetype: string;
  motto: string;
  analysis_approach: string;
  council_position?: number; // 1-5 for current council members, undefined for others
  council_weight?: number; // Voting weight in council (0.0-1.0)
  learning_rate: number;
  emoji: string;
}

// The standardized 15 personality-driven experts
// These IDs and names match exactly with the backend ML models
export const EXPERT_PERSONALITIES: ExpertPersonality[] = [
  // 1. THE ANALYST - Conservative data-driven expert
  {
    id: "conservative_analyzer",
    name: "The Analyst",
    type: "ai_model",
    specialization: ["core", "advanced"],
    archetype: "Data-driven Conservative",
    motto: "Numbers don't lie, emotions do",
    decision_making_style:
      "Methodical statistical analysis with heavy emphasis on historical trends",
    risk_tolerance: "conservative",
    primary_expertise: ["core", "advanced"],
    analysis_approach:
      "Comprehensive statistical modeling with risk-adjusted projections",
    personality_traits: {
      risk_tolerance: 0.2,
      analytics_trust: 0.9,
      contrarian_tendency: 0.1,
      optimism: 0.4,
      chaos_comfort: 0.2,
      confidence_level: 0.7,
      market_trust: 0.8,
      value_seeking: 0.6,
    },
    learning_rate: 0.03,
    emoji: "📊",
    accuracy_metrics: {
      overall: 0.724,
      by_category: {
        core: 0.782,
        props: 0.698,
        live: 0.645,
        situational: 0.712,
        advanced: 0.756,
      },
      by_prediction_type: {},
      recent_performance: 0.785,
      season_performance: 0.724,
    },
    confidence_calibration: 0.89,
    track_record: {
      total_predictions: 156,
      correct_predictions: 113,
      high_confidence_accuracy: 0.834,
      low_confidence_accuracy: 0.623,
    },
    bio: "A methodical AI that excels at finding patterns in large datasets and making conservative, well-researched predictions.",
    verified: true,
    council_position: 1,
    council_weight: 0.24,
  },

  // 2. THE GAMBLER - High-risk aggressive expert
  {
    id: "risk_taking_gambler",
    name: "The Gambler",
    type: "ai_model",
    specialization: ["core", "props"],
    archetype: "High-risk High-reward",
    motto: "Fortune favors the bold",
    decision_making_style:
      "Aggressive betting with focus on value and contrarian plays",
    risk_tolerance: "aggressive",
    primary_expertise: ["core", "props"],
    analysis_approach:
      "Market inefficiency identification with bold contrarian positions",
    personality_traits: {
      risk_tolerance: 0.9,
      analytics_trust: 0.3,
      contrarian_tendency: 0.7,
      optimism: 0.8,
      chaos_comfort: 0.9,
      confidence_level: 0.8,
      market_trust: 0.2,
      value_seeking: 0.5,
    },
    learning_rate: 0.08,
    emoji: "🎲",
    accuracy_metrics: {
      overall: 0.642,
      by_category: {
        core: 0.678,
        props: 0.734,
        live: 0.589,
        situational: 0.623,
        advanced: 0.587,
      },
      by_prediction_type: {},
      recent_performance: 0.567,
      season_performance: 0.642,
    },
    confidence_calibration: 0.64,
    track_record: {
      total_predictions: 189,
      correct_predictions: 121,
      high_confidence_accuracy: 0.723,
      low_confidence_accuracy: 0.534,
    },
    bio: "An aggressive AI that specializes in finding value bets and making bold predictions others won't.",
    verified: true,
  },

  // 3. THE REBEL - Contrarian expert
  {
    id: "contrarian_rebel",
    name: "The Rebel",
    type: "ai_model",
    specialization: ["core", "props"],
    archetype: "Against-the-grain Value Seeker",
    motto: "When everyone zigs, I zag",
    decision_making_style:
      "Contrarian analysis with public sentiment fade strategy",
    risk_tolerance: "aggressive",
    primary_expertise: ["core", "props"],
    analysis_approach:
      "Public sentiment analysis with contrarian position identification",
    personality_traits: {
      risk_tolerance: 0.6,
      analytics_trust: 0.4,
      contrarian_tendency: 0.95,
      optimism: 0.3,
      chaos_comfort: 0.8,
      confidence_level: 0.6,
      market_trust: 0.2,
      value_seeking: 0.7,
    },
    learning_rate: 0.06,
    emoji: "😈",
    accuracy_metrics: {
      overall: 0.618,
      by_category: {
        core: 0.634,
        props: 0.689,
        live: 0.578,
        situational: 0.598,
        advanced: 0.576,
      },
      by_prediction_type: {},
      recent_performance: 0.634,
      season_performance: 0.618,
    },
    confidence_calibration: 0.66,
    track_record: {
      total_predictions: 167,
      correct_predictions: 103,
      high_confidence_accuracy: 0.678,
      low_confidence_accuracy: 0.567,
    },
    bio: "A contrarian AI that thrives on going against public opinion and finding unique value.",
    verified: true,
    council_position: 2,
    council_weight: 0.22,
  },

  // 4. THE HUNTER - Value-seeking expert
  {
    id: "value_hunter",
    name: "The Hunter",
    type: "ai_model",
    specialization: ["props", "core"],
    archetype: "Value Identification Specialist",
    motto: "Hunt the value, avoid the traps",
    decision_making_style:
      "Market inefficiency hunting with disciplined value selection",
    risk_tolerance: "moderate",
    primary_expertise: ["props", "core"],
    analysis_approach:
      "Systematic value identification with market pricing analysis",
    personality_traits: {
      risk_tolerance: 0.4,
      analytics_trust: 0.8,
      contrarian_tendency: 0.6,
      optimism: 0.5,
      chaos_comfort: 0.3,
      confidence_level: 0.7,
      market_trust: 0.9,
      value_seeking: 0.95,
    },
    learning_rate: 0.04,
    emoji: "🎯",
    accuracy_metrics: {
      overall: 0.658,
      by_category: {
        core: 0.634,
        props: 0.745,
        live: 0.612,
        situational: 0.701,
        advanced: 0.598,
      },
      by_prediction_type: {},
      recent_performance: 0.641,
      season_performance: 0.658,
    },
    confidence_calibration: 0.74,
    track_record: {
      total_predictions: 128,
      correct_predictions: 84,
      high_confidence_accuracy: 0.701,
      low_confidence_accuracy: 0.589,
    },
    bio: "A value-focused AI that excels at identifying market inefficiencies and disciplined betting opportunities.",
    verified: true,
    council_position: 3,
    council_weight: 0.2,
  },

  // 5. THE RIDER - Momentum specialist
  {
    id: "momentum_rider",
    name: "The Rider",
    type: "ai_model",
    specialization: ["live", "core"],
    archetype: "Trend and Momentum Specialist",
    motto: "Momentum is everything",
    decision_making_style:
      "Real-time momentum analysis with psychological factor weighting",
    risk_tolerance: "aggressive",
    primary_expertise: ["live", "core"],
    analysis_approach:
      "Live momentum tracking with psychological and trend analysis",
    personality_traits: {
      risk_tolerance: 0.7,
      analytics_trust: 0.5,
      contrarian_tendency: 0.2,
      optimism: 0.8,
      chaos_comfort: 0.6,
      confidence_level: 0.8,
      market_trust: 0.6,
      value_seeking: 0.4,
    },
    learning_rate: 0.07,
    emoji: "🏇",
    accuracy_metrics: {
      overall: 0.635,
      by_category: {
        core: 0.623,
        props: 0.598,
        live: 0.756,
        situational: 0.612,
        advanced: 0.587,
      },
      by_prediction_type: {},
      recent_performance: 0.612,
      season_performance: 0.635,
    },
    confidence_calibration: 0.71,
    track_record: {
      total_predictions: 145,
      correct_predictions: 92,
      high_confidence_accuracy: 0.723,
      low_confidence_accuracy: 0.543,
    },
    bio: "A dynamic AI that specializes in tracking momentum shifts and real-time game flow.",
    verified: true,
    council_position: 4,
    council_weight: 0.18,
  },

  // 6. THE SCHOLAR - Research-driven fundamentalist
  {
    id: "fundamentalist_scholar",
    name: "The Scholar",
    type: "ai_model",
    specialization: ["advanced", "situational"],
    archetype: "Deep Research Fundamentalist",
    motto: "Knowledge is power, research is truth",
    decision_making_style:
      "Deep fundamental analysis with comprehensive research methodology",
    risk_tolerance: "conservative",
    primary_expertise: ["advanced", "situational"],
    analysis_approach:
      "Systematic fundamental analysis with comprehensive data evaluation",
    personality_traits: {
      risk_tolerance: 0.3,
      analytics_trust: 0.95,
      contrarian_tendency: 0.2,
      optimism: 0.6,
      chaos_comfort: 0.1,
      confidence_level: 0.9,
      market_trust: 0.7,
      value_seeking: 0.8,
    },
    learning_rate: 0.02,
    emoji: "📚",
    accuracy_metrics: {
      overall: 0.672,
      by_category: {
        core: 0.689,
        props: 0.656,
        live: 0.634,
        situational: 0.723,
        advanced: 0.734,
      },
      by_prediction_type: {},
      recent_performance: 0.695,
      season_performance: 0.672,
    },
    confidence_calibration: 0.82,
    track_record: {
      total_predictions: 134,
      correct_predictions: 90,
      high_confidence_accuracy: 0.789,
      low_confidence_accuracy: 0.612,
    },
    bio: "A research-focused AI that uses comprehensive fundamental analysis and deep data evaluation.",
    verified: true,
    council_position: 5,
    council_weight: 0.16,
  },

  // 7. THE CHAOS - Randomness and variance expert
  {
    id: "chaos_theory_believer",
    name: "The Chaos",
    type: "ai_model",
    specialization: ["live", "core"],
    archetype: "Randomness and Variance Specialist",
    motto: "Chaos is the only constant",
    decision_making_style: "Embraces randomness and high-variance scenarios",
    risk_tolerance: "aggressive",
    primary_expertise: ["live", "core"],
    analysis_approach: "Variance acceptance with chaos theory applications",
    personality_traits: {
      risk_tolerance: 0.8,
      analytics_trust: 0.2,
      contrarian_tendency: 0.9,
      optimism: 0.5,
      chaos_comfort: 0.95,
      confidence_level: 0.4,
      market_trust: 0.1,
      value_seeking: 0.3,
    },
    learning_rate: 0.12,
    emoji: "🌪️",
    accuracy_metrics: {
      overall: 0.541,
      by_category: {
        core: 0.567,
        props: 0.523,
        live: 0.612,
        situational: 0.534,
        advanced: 0.498,
      },
      by_prediction_type: {},
      recent_performance: 0.523,
      season_performance: 0.541,
    },
    confidence_calibration: 0.58,
    track_record: {
      total_predictions: 178,
      correct_predictions: 96,
      high_confidence_accuracy: 0.634,
      low_confidence_accuracy: 0.487,
    },
    bio: "A chaos-embracing AI that thrives in high-variance scenarios and unexpected outcomes.",
    verified: true,
  },

  // 8. THE INTUITION - Gut-feel specialist
  {
    id: "gut_instinct_expert",
    name: "The Intuition",
    type: "ai_model",
    specialization: ["props", "live"],
    archetype: "Intuitive Decision Maker",
    motto: "Trust the gut, feel the game",
    decision_making_style: "Intuition-based with minimal analytical processing",
    risk_tolerance: "moderate",
    primary_expertise: ["props", "live"],
    analysis_approach: "Intuitive pattern recognition with gut-feel emphasis",
    personality_traits: {
      risk_tolerance: 0.6,
      analytics_trust: 0.1,
      contrarian_tendency: 0.4,
      optimism: 0.7,
      chaos_comfort: 0.8,
      confidence_level: 0.9,
      market_trust: 0.3,
      value_seeking: 0.5,
    },
    learning_rate: 0.09,
    emoji: "🔮",
    accuracy_metrics: {
      overall: 0.589,
      by_category: {
        core: 0.578,
        props: 0.634,
        live: 0.612,
        situational: 0.567,
        advanced: 0.556,
      },
      by_prediction_type: {},
      recent_performance: 0.601,
      season_performance: 0.589,
    },
    confidence_calibration: 0.64,
    track_record: {
      total_predictions: 143,
      correct_predictions: 84,
      high_confidence_accuracy: 0.623,
      low_confidence_accuracy: 0.534,
    },
    bio: "An intuition-focused AI that relies on gut feelings and instinctive pattern recognition.",
    verified: true,
  },

  // 9. THE QUANT - Mathematical purist
  {
    id: "statistics_purist",
    name: "The Quant",
    type: "statistical_model",
    specialization: ["advanced", "props"],
    archetype: "Mathematical Precision",
    motto: "In mathematics we trust",
    decision_making_style:
      "Pure mathematical modeling with advanced statistical techniques",
    risk_tolerance: "conservative",
    primary_expertise: ["advanced", "props"],
    analysis_approach:
      "Advanced statistical modeling with Monte Carlo simulations",
    personality_traits: {
      risk_tolerance: 0.2,
      analytics_trust: 0.98,
      contrarian_tendency: 0.1,
      optimism: 0.5,
      chaos_comfort: 0.05,
      confidence_level: 0.8,
      market_trust: 0.9,
      value_seeking: 0.6,
    },
    learning_rate: 0.03,
    emoji: "🤖",
    accuracy_metrics: {
      overall: 0.672,
      by_category: {
        core: 0.689,
        props: 0.778,
        live: 0.634,
        situational: 0.623,
        advanced: 0.734,
      },
      by_prediction_type: {},
      recent_performance: 0.695,
      season_performance: 0.672,
    },
    confidence_calibration: 0.82,
    track_record: {
      total_predictions: 134,
      correct_predictions: 90,
      high_confidence_accuracy: 0.789,
      low_confidence_accuracy: 0.612,
    },
    bio: "A mathematically-focused AI that uses pure statistical models and quantitative analysis.",
    verified: true,
  },

  // 10. THE REVERSAL - Mean reversion specialist
  {
    id: "trend_reversal_specialist",
    name: "The Reversal",
    type: "ai_model",
    specialization: ["core", "advanced"],
    archetype: "Mean Reversion Specialist",
    motto: "What goes up must come down",
    decision_making_style:
      "Trend reversal identification with mean reversion focus",
    risk_tolerance: "moderate",
    primary_expertise: ["core", "advanced"],
    analysis_approach:
      "Statistical mean reversion with pattern break identification",
    personality_traits: {
      risk_tolerance: 0.5,
      analytics_trust: 0.7,
      contrarian_tendency: 0.8,
      optimism: 0.4,
      chaos_comfort: 0.6,
      confidence_level: 0.7,
      market_trust: 0.5,
      value_seeking: 0.8,
    },
    learning_rate: 0.05,
    emoji: "↩️",
    accuracy_metrics: {
      overall: 0.606,
      by_category: {
        core: 0.612,
        props: 0.578,
        live: 0.634,
        situational: 0.567,
        advanced: 0.645,
      },
      by_prediction_type: {},
      recent_performance: 0.623,
      season_performance: 0.606,
    },
    confidence_calibration: 0.75,
    track_record: {
      total_predictions: 125,
      correct_predictions: 76,
      high_confidence_accuracy: 0.701,
      low_confidence_accuracy: 0.534,
    },
    bio: "A mean reversion specialist that identifies trend breaks and pattern reversals.",
    verified: true,
  },

  // 11. THE FADER - Anti-narrative expert
  {
    id: "popular_narrative_fader",
    name: "The Fader",
    type: "ai_model",
    specialization: ["core", "situational"],
    archetype: "Narrative Resistance Specialist",
    motto: "Fade the story, find the truth",
    decision_making_style: "Anti-narrative analysis with story resistance",
    risk_tolerance: "aggressive",
    primary_expertise: ["core", "situational"],
    analysis_approach:
      "Narrative identification and systematic fading strategy",
    personality_traits: {
      risk_tolerance: 0.6,
      analytics_trust: 0.6,
      contrarian_tendency: 0.9,
      optimism: 0.3,
      chaos_comfort: 0.7,
      confidence_level: 0.8,
      market_trust: 0.2,
      value_seeking: 0.7,
    },
    learning_rate: 0.06,
    emoji: "🚫",
    accuracy_metrics: {
      overall: 0.594,
      by_category: {
        core: 0.612,
        props: 0.567,
        live: 0.589,
        situational: 0.634,
        advanced: 0.578,
      },
      by_prediction_type: {},
      recent_performance: 0.612,
      season_performance: 0.594,
    },
    confidence_calibration: 0.69,
    track_record: {
      total_predictions: 132,
      correct_predictions: 78,
      high_confidence_accuracy: 0.667,
      low_confidence_accuracy: 0.543,
    },
    bio: "An anti-narrative specialist that systematically fades popular storylines.",
    verified: true,
  },

  // 12. THE SHARP - Smart money follower
  {
    id: "sharp_money_follower",
    name: "The Sharp",
    type: "ai_model",
    specialization: ["core", "advanced"],
    archetype: "Professional Money Tracker",
    motto: "Follow the smart money",
    decision_making_style:
      "Professional betting pattern analysis with sharp money tracking",
    risk_tolerance: "moderate",
    primary_expertise: ["core", "advanced"],
    analysis_approach:
      "Line movement analysis with professional betting pattern identification",
    personality_traits: {
      risk_tolerance: 0.5,
      analytics_trust: 0.8,
      contrarian_tendency: 0.3,
      optimism: 0.6,
      chaos_comfort: 0.4,
      confidence_level: 0.9,
      market_trust: 0.95,
      value_seeking: 0.8,
    },
    learning_rate: 0.04,
    emoji: "💎",
    accuracy_metrics: {
      overall: 0.641,
      by_category: {
        core: 0.667,
        props: 0.623,
        live: 0.598,
        situational: 0.656,
        advanced: 0.689,
      },
      by_prediction_type: {},
      recent_performance: 0.656,
      season_performance: 0.641,
    },
    confidence_calibration: 0.78,
    track_record: {
      total_predictions: 119,
      correct_predictions: 76,
      high_confidence_accuracy: 0.723,
      low_confidence_accuracy: 0.578,
    },
    bio: "A professional money tracker that follows sharp betting patterns and line movements.",
    verified: true,
  },

  // 13. THE UNDERDOG - Upset specialist
  {
    id: "underdog_champion",
    name: "The Underdog",
    type: "ai_model",
    specialization: ["core", "props"],
    archetype: "Upset and Value Identification",
    motto: "Every dog has its day",
    decision_making_style:
      "Underdog value analysis with upset probability assessment",
    risk_tolerance: "aggressive",
    primary_expertise: ["core", "props"],
    analysis_approach:
      "Underdog analysis with value betting and upset identification",
    personality_traits: {
      risk_tolerance: 0.9,
      analytics_trust: 0.4,
      contrarian_tendency: 0.8,
      optimism: 0.9,
      chaos_comfort: 0.9,
      confidence_level: 0.6,
      market_trust: 0.3,
      value_seeking: 0.9,
    },
    learning_rate: 0.08,
    emoji: "🐕",
    accuracy_metrics: {
      overall: 0.561,
      by_category: {
        core: 0.578,
        props: 0.612,
        live: 0.534,
        situational: 0.567,
        advanced: 0.543,
      },
      by_prediction_type: {},
      recent_performance: 0.567,
      season_performance: 0.561,
    },
    confidence_calibration: 0.59,
    track_record: {
      total_predictions: 156,
      correct_predictions: 87,
      high_confidence_accuracy: 0.612,
      low_confidence_accuracy: 0.512,
    },
    bio: "An underdog-focused AI that specializes in identifying upset opportunities and long-shot value.",
    verified: true,
  },

  // 14. THE CONSENSUS - Crowd follower
  {
    id: "consensus_follower",
    name: "The Consensus",
    type: "ai_model",
    specialization: ["core", "situational"],
    archetype: "Crowd Wisdom Follower",
    motto: "Wisdom of the crowds",
    decision_making_style: "Public sentiment following with consensus tracking",
    risk_tolerance: "conservative",
    primary_expertise: ["core", "situational"],
    analysis_approach: "Public sentiment analysis with crowd wisdom emphasis",
    personality_traits: {
      risk_tolerance: 0.3,
      analytics_trust: 0.6,
      contrarian_tendency: 0.05,
      optimism: 0.6,
      chaos_comfort: 0.2,
      confidence_level: 0.5,
      market_trust: 0.8,
      value_seeking: 0.4,
    },
    learning_rate: 0.04,
    emoji: "👥",
    accuracy_metrics: {
      overall: 0.573,
      by_category: {
        core: 0.589,
        props: 0.556,
        live: 0.578,
        situational: 0.612,
        advanced: 0.567,
      },
      by_prediction_type: {},
      recent_performance: 0.589,
      season_performance: 0.573,
    },
    confidence_calibration: 0.67,
    track_record: {
      total_predictions: 127,
      correct_predictions: 73,
      high_confidence_accuracy: 0.634,
      low_confidence_accuracy: 0.523,
    },
    bio: "A consensus-following AI that tracks public sentiment and crowd wisdom.",
    verified: true,
  },

  // 15. THE EXPLOITER - Market inefficiency hunter
  {
    id: "market_inefficiency_exploiter",
    name: "The Exploiter",
    type: "ai_model",
    specialization: ["advanced", "core"],
    archetype: "Market Edge Identification",
    motto: "Find the edge, exploit the gap",
    decision_making_style:
      "Systematic market inefficiency identification and exploitation",
    risk_tolerance: "aggressive",
    primary_expertise: ["advanced", "core"],
    analysis_approach:
      "Market analysis with systematic edge identification and arbitrage seeking",
    personality_traits: {
      risk_tolerance: 0.7,
      analytics_trust: 0.9,
      contrarian_tendency: 0.7,
      optimism: 0.5,
      chaos_comfort: 0.5,
      confidence_level: 0.8,
      market_trust: 0.95,
      value_seeking: 0.98,
    },
    learning_rate: 0.05,
    emoji: "🔍",
    accuracy_metrics: {
      overall: 0.556,
      by_category: {
        core: 0.612,
        props: 0.534,
        live: 0.543,
        situational: 0.567,
        advanced: 0.589,
      },
      by_prediction_type: {},
      recent_performance: 0.543,
      season_performance: 0.556,
    },
    confidence_calibration: 0.72,
    track_record: {
      total_predictions: 149,
      correct_predictions: 83,
      high_confidence_accuracy: 0.645,
      low_confidence_accuracy: 0.498,
    },
    bio: "A market inefficiency specialist that systematically identifies and exploits edges.",
    verified: true,
  },
];

// Helper functions for expert management
export const getCouncilMembers = (): ExpertPersonality[] => {
  return EXPERT_PERSONALITIES.filter(
    (expert) => expert.council_position !== undefined
  ).sort((a, b) => (a.council_position || 0) - (b.council_position || 0));
};

export const getNonCouncilExperts = (): ExpertPersonality[] => {
  return EXPERT_PERSONALITIES.filter(
    (expert) => expert.council_position === undefined
  ).sort((a, b) => b.accuracy_metrics.overall - a.accuracy_metrics.overall);
};

export const getExpertById = (id: string): ExpertPersonality | undefined => {
  return EXPERT_PERSONALITIES.find((expert) => expert.id === id);
};

export const getExpertsByArchetype = (
  archetype: string
): ExpertPersonality[] => {
  return EXPERT_PERSONALITIES.filter((expert) =>
    expert.archetype.toLowerCase().includes(archetype.toLowerCase())
  );
};

export const getExpertsBySpecialization = (
  category: PredictionCategory
): ExpertPersonality[] => {
  return EXPERT_PERSONALITIES.filter((expert) =>
    expert.primary_expertise.includes(category)
  );
};

// Expert ID mapping for backward compatibility during migration
export const EXPERT_ID_MAPPING: Record<string, string> = {
  // Old IDs -> New standardized IDs
  "the-analyst": "conservative_analyzer",
  "the-gambler": "risk_taking_gambler",
  "the-veteran": "conservative_analyzer", // Maps to analyst
  "the-contrarian": "contrarian_rebel",
  "the-momentum-tracker": "momentum_rider",
  "the-scout": "value_hunter", // Maps to hunter
  "the-weather-expert": "chaos_theory_believer", // Maps to chaos
  "the-quant": "statistics_purist",
  "the-home-field-specialist": "popular_narrative_fader", // Maps to fader
  "the-playoff-prophet": "trend_reversal_specialist", // Maps to reversal
  "the-divisional-expert": "consensus_follower", // Maps to consensus
  "the-rookie-whisperer": "gut_instinct_expert", // Maps to intuition
  "the-primetime-performer": "sharp_money_follower", // Maps to sharp
  "the-underdog-champion": "underdog_champion",
  "the-total-predictor": "market_inefficiency_exploiter", // Maps to exploiter
};

// Reverse mapping for legacy support
export const LEGACY_EXPERT_MAPPING: Record<string, string> = Object.fromEntries(
  Object.entries(EXPERT_ID_MAPPING).map(([old, new_id]) => [new_id, old])
);
