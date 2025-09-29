/**
 * Expert Image Mapping Utility
 * Maps expert names to their corresponding image files
 */

import { ExpertPersonality } from '@/data/expertPersonalities';

// Mapping of expert names to image filenames
const EXPERT_IMAGE_MAP: Record<string, string> = {
  'The Analyst': 'named_01_the_analyst.png',
  'The Gambler': 'named_02_the_gambler.png',
  'The Rebel': 'named_03_the_rebel.png',
  'The Hunter': 'named_04_the_hunter.png',
  'The Rider': 'named_05_the_rider.png',
  'The Scholar': 'named_06_the_scholar.png',
  'The Chaos': 'named_07_the_chaos.png',
  'The Intuition': 'named_08_the_intuition.png',
  'The Quant': 'named_09_the_quant.png',
  'The Reversal': 'named_10_the_reversal.png',
  'The Fader': 'named_11_the_fader.png',
  'The Sharp': 'named_12_the_sharp.png',
  'The Underdog': 'named_13_the_underdog.png',
  'The Consensus': 'named_14_the_consensus.png',
  'The Exploiter': 'named_15_the_exploiter.png',
};

// Alternative mapping by expert ID
const EXPERT_ID_IMAGE_MAP: Record<string, string> = {
  'conservative_analyzer': 'named_01_the_analyst.png',
  'risk_taking_gambler': 'named_02_the_gambler.png',
  'contrarian_rebel': 'named_03_the_rebel.png',
  'value_hunter': 'named_04_the_hunter.png',
  'momentum_rider': 'named_05_the_rider.png',
  'statistical_scholar': 'named_06_the_scholar.png',
  'chaos_embracer': 'named_07_the_chaos.png',
  'intuitive_feeler': 'named_08_the_intuition.png',
  'quantitative_modeler': 'named_09_the_quant.png',
  'reversal_specialist': 'named_10_the_reversal.png',
  'fade_the_public': 'named_11_the_fader.png',
  'sharp_follower': 'named_12_the_sharp.png',
  'underdog_believer': 'named_13_the_underdog.png',
  'consensus_builder': 'named_14_the_consensus.png',
  'market_exploiter': 'named_15_the_exploiter.png',
};

/**
 * Get the image URL for an expert by name
 */
export function getExpertImageByName(name: string): string {
  const imagePath = EXPERT_IMAGE_MAP[name];
  if (!imagePath) {
    console.warn(`No image found for expert: ${name}`);
    return '/expert_images/default_expert.png'; // Fallback image
  }
  return `/expert_images/${imagePath}`;
}

/**
 * Get the image URL for an expert by ID
 */
export function getExpertImageById(id: string): string {
  const imagePath = EXPERT_ID_IMAGE_MAP[id];
  if (!imagePath) {
    console.warn(`No image found for expert ID: ${id}`);
    return '/expert_images/default_expert.png'; // Fallback image
  }
  return `/expert_images/${imagePath}`;
}

/**
 * Get the image URL for an expert object
 */
export function getExpertImage(expert: ExpertPersonality | { name?: string; id?: string }): string {
  if ('name' in expert && expert.name) {
    return getExpertImageByName(expert.name);
  }
  if ('id' in expert && expert.id) {
    return getExpertImageById(expert.id);
  }
  return '/expert_images/default_expert.png';
}

/**
 * Get initials from expert name (fallback for when images fail to load)
 */
export function getExpertInitials(name: string): string {
  const words = name.split(' ');
  if (words.length >= 2) {
    // For "The Analyst" -> "TA"
    return words.map(w => w[0]).join('').toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

/**
 * Get a color gradient based on expert's council position or archetype
 */
export function getExpertGradient(expert: ExpertPersonality): string {
  if (expert.council_position) {
    // Gold gradient for council members
    switch (expert.council_position) {
      case 1:
        return 'from-yellow-500 via-amber-500 to-yellow-600';
      case 2:
        return 'from-yellow-400 via-amber-400 to-yellow-500';
      case 3:
        return 'from-yellow-300 via-amber-300 to-yellow-400';
      case 4:
        return 'from-amber-400 via-yellow-400 to-amber-500';
      case 5:
        return 'from-amber-300 via-yellow-300 to-amber-400';
      default:
        return 'from-gray-400 to-gray-600';
    }
  }

  // Color based on risk tolerance for non-council members
  switch (expert.risk_tolerance) {
    case 'aggressive':
      return 'from-red-400 to-red-600';
    case 'moderate':
      return 'from-blue-400 to-blue-600';
    case 'conservative':
      return 'from-green-400 to-green-600';
    default:
      return 'from-gray-400 to-gray-600';
  }
}