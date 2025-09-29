/**
 * Test Suite for Expert Competition System
 * Tests expert personalities, council selection, and storyline generation
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { 
  EXPERT_PERSONALITIES, 
  getCouncilMembers, 
  getNonCouncilExperts, 
  getExpertById 
} from '@/data/expertPersonalities';
import { 
  CouncilSelectionAlgorithm, 
  councilSelector,
  getCurrentCouncil 
} from '@/services/councilSelection';
import { 
  storylineGenerator,
  generateExpertStorylines 
} from '@/services/storylineGenerator';
import { 
  PREDICTION_CATEGORIES,
  getCategoriesByGroup,
  getCategoryStats 
} from '@/data/predictionCategories';

describe('Expert Personalities System', () => {
  it('should have exactly 15 experts', () => {
    expect(EXPERT_PERSONALITIES).toHaveLength(15);
  });

  it('should have exactly 5 council members', () => {
    const councilMembers = getCouncilMembers();
    expect(councilMembers).toHaveLength(5);
  });

  it('should have 10 non-council experts', () => {
    const nonCouncilExperts = getNonCouncilExperts();
    expect(nonCouncilExperts).toHaveLength(10);
  });

  it('should have all experts with valid data', () => {
    EXPERT_PERSONALITIES.forEach(expert => {
      expect(expert.id).toBeTruthy();
      expect(expert.name).toBeTruthy();
      expect(expert.archetype).toBeTruthy();
      expect(expert.motto).toBeTruthy();
      expect(expert.accuracy_metrics.overall).toBeGreaterThan(0);
      expect(expert.accuracy_metrics.overall).toBeLessThanOrEqual(1);
      expect(expert.confidence_calibration).toBeGreaterThan(0);
      expect(expert.confidence_calibration).toBeLessThanOrEqual(1);
      expect(expert.track_record.total_predictions).toBeGreaterThan(0);
    });
  });

  it('should have council members with valid positions', () => {
    const councilMembers = getCouncilMembers();
    
    councilMembers.forEach((member, index) => {
      expect(member.council_position).toBe(index + 1);
      expect(member.council_weight).toBeGreaterThan(0);
      expect(member.council_weight).toBeLessThanOrEqual(1);
    });

    // Check that council weights sum to approximately 1
    const totalWeight = councilMembers.reduce((sum, member) => sum + member.council_weight!, 0);
    expect(totalWeight).toBeCloseTo(1, 1);
  });

  it('should find experts by ID', () => {
    const analyst = getExpertById('the-analyst');
    expect(analyst).toBeDefined();
    expect(analyst?.name).toBe('The Analyst');

    const nonExistent = getExpertById('non-existent');
    expect(nonExistent).toBeUndefined();
  });

  it('should have diverse risk tolerances', () => {
    const riskProfiles = EXPERT_PERSONALITIES.map(e => e.risk_tolerance);
    expect(riskProfiles).toContain('conservative');
    expect(riskProfiles).toContain('moderate');
    expect(riskProfiles).toContain('aggressive');
  });
});

describe('Council Selection Algorithm', () => {
  let algorithm: CouncilSelectionAlgorithm;

  beforeEach(() => {
    algorithm = new CouncilSelectionAlgorithm();
  });

  it('should select exactly 5 council members', () => {
    const selection = algorithm.selectCouncil();
    expect(selection.council_members).toHaveLength(5);
  });

  it('should assign proper voting weights', () => {
    const selection = algorithm.selectCouncil();
    
    selection.council_members.forEach((member, index) => {
      expect(member.rank).toBe(index + 1);
      expect(member.voting_weight).toBeGreaterThan(0);
      expect(member.voting_weight).toBeLessThanOrEqual(1);
    });

    // Higher ranked members should have higher weights
    for (let i = 0; i < selection.council_members.length - 1; i++) {
      expect(selection.council_members[i].voting_weight)
        .toBeGreaterThanOrEqual(selection.council_members[i + 1].voting_weight);
    }
  });

  it('should provide selection reasons', () => {
    const selection = algorithm.selectCouncil();
    
    selection.council_members.forEach(member => {
      expect(member.selection_reasons).toBeDefined();
      expect(member.selection_reasons.length).toBeGreaterThan(0);
      expect(member.selection_score).toBeGreaterThan(0);
    });
  });

  it('should calculate performance summary', () => {
    const selection = algorithm.selectCouncil();
    
    expect(selection.performance_summary.average_accuracy).toBeGreaterThan(0);
    expect(selection.performance_summary.total_predictions).toBeGreaterThan(0);
    expect(selection.performance_summary.confidence_calibration).toBeGreaterThan(0);
    expect(selection.performance_summary.specialization_coverage).toBeDefined();
  });

  it('should detect changes between selections', () => {
    const selection1 = algorithm.selectCouncil();
    const selection2 = algorithm.selectCouncil();
    
    // Changes array should exist (might be empty if no changes)
    expect(selection2.changes).toBeDefined();
    expect(Array.isArray(selection2.changes)).toBe(true);
  });
});

describe('Prediction Categories System', () => {
  it('should have 27+ prediction categories', () => {
    expect(PREDICTION_CATEGORIES.length).toBeGreaterThanOrEqual(27);
  });

  it('should have valid category configurations', () => {
    PREDICTION_CATEGORIES.forEach(category => {
      expect(category.id).toBeTruthy();
      expect(category.name).toBeTruthy();
      expect(category.description).toBeTruthy();
      expect(category.group).toBeDefined();
      expect(['easy', 'medium', 'hard', 'expert']).toContain(category.difficulty);
      expect(['high', 'medium', 'low']).toContain(category.betting_relevance);
      expect(typeof category.real_time_updates).toBe('boolean');
      expect(Array.isArray(category.expert_specializations)).toBe(true);
      expect(Array.isArray(category.data_requirements)).toBe(true);
      expect(Array.isArray(category.example_predictions)).toBe(true);
    });
  });

  it('should group categories correctly', () => {
    const gameOutcomeCategories = getCategoriesByGroup('game_outcome');
    expect(gameOutcomeCategories.length).toBeGreaterThan(0);
    
    gameOutcomeCategories.forEach(category => {
      expect(category.group.id).toBe('game_outcome');
    });
  });

  it('should provide accurate statistics', () => {
    const stats = getCategoryStats();
    
    expect(stats.total_categories).toBe(PREDICTION_CATEGORIES.length);
    expect(stats.realtime_enabled).toBeGreaterThan(0);
    expect(stats.by_difficulty.easy + stats.by_difficulty.medium + 
           stats.by_difficulty.hard + stats.by_difficulty.expert)
      .toBe(PREDICTION_CATEGORIES.length);
  });

  it('should have balanced difficulty distribution', () => {
    const stats = getCategoryStats();
    
    // Should have categories of each difficulty level
    expect(stats.by_difficulty.easy).toBeGreaterThan(0);
    expect(stats.by_difficulty.medium).toBeGreaterThan(0);
    expect(stats.by_difficulty.hard).toBeGreaterThan(0);
    expect(stats.by_difficulty.expert).toBeGreaterThan(0);
  });
});

describe('Storyline Generation System', () => {
  it('should generate storylines for experts', () => {
    const storylines = generateExpertStorylines(['the-analyst', 'the-gambler']);
    
    expect(Array.isArray(storylines)).toBe(true);
    storylines.forEach(storyline => {
      expect(storyline.id).toBeTruthy();
      expect(storyline.expertId).toBeTruthy();
      expect(storyline.title).toBeTruthy();
      expect(storyline.description).toBeTruthy();
      expect(storyline.narrative).toBeTruthy();
      expect(['low', 'medium', 'high', 'critical']).toContain(storyline.severity);
      expect(['short', 'medium', 'long']).toContain(storyline.duration);
      expect(Array.isArray(storyline.tags)).toBe(true);
    });
  });

  it('should generate top storylines', () => {
    const topStorylines = storylineGenerator.getTopStorylines(5);
    
    expect(topStorylines).toHaveLength(5);
    
    // Should be sorted by impact rating (descending)
    for (let i = 0; i < topStorylines.length - 1; i++) {
      expect(topStorylines[i].metrics.impact_rating)
        .toBeGreaterThanOrEqual(topStorylines[i + 1].metrics.impact_rating);
    }
  });

  it('should have valid storyline metrics', () => {
    const storylines = generateExpertStorylines();
    
    storylines.forEach(storyline => {
      const metrics = storyline.metrics;
      expect(metrics.engagement_score).toBeGreaterThanOrEqual(0);
      expect(metrics.engagement_score).toBeLessThanOrEqual(1);
      expect(metrics.impact_rating).toBeGreaterThanOrEqual(1);
      expect(metrics.impact_rating).toBeLessThanOrEqual(10);
      expect(metrics.confidence_level).toBeGreaterThanOrEqual(0);
      expect(metrics.confidence_level).toBeLessThanOrEqual(1);
    });
  });

  it('should generate diverse storyline types', () => {
    const storylines = storylineGenerator.getTopStorylines(15);
    const types = storylines.map(s => s.type);
    
    // Should have multiple different storyline types
    const uniqueTypes = new Set(types);
    expect(uniqueTypes.size).toBeGreaterThan(1);
  });
});

describe('System Integration', () => {
  it('should have consistent expert IDs across systems', () => {
    const expertIds = EXPERT_PERSONALITIES.map(e => e.id);
    const councilMembers = getCurrentCouncil();
    const storylines = generateExpertStorylines();
    
    // All council member IDs should exist in expert personalities
    councilMembers.forEach(member => {
      expect(expertIds).toContain(member.id);
    });
    
    // All storyline expert IDs should exist in expert personalities
    storylines.forEach(storyline => {
      expect(expertIds).toContain(storyline.expertId);
    });
  });

  it('should maintain data consistency', () => {
    const experts = EXPERT_PERSONALITIES;
    const categories = PREDICTION_CATEGORIES;
    
    // Check that expert specializations reference valid categories
    experts.forEach(expert => {
      expert.primary_expertise.forEach(expertise => {
        const validGroups = ['core', 'props', 'live', 'situational', 'advanced'];
        expect(validGroups).toContain(expertise);
      });
    });
    
    // Check that category expert specializations reference valid expert types
    categories.forEach(category => {
      expect(Array.isArray(category.expert_specializations)).toBe(true);
    });
  });

  it('should handle edge cases gracefully', () => {
    // Test with empty inputs
    expect(() => getExpertById('')).not.toThrow();
    expect(() => getCategoriesByGroup('non-existent')).not.toThrow();
    expect(() => generateExpertStorylines([])).not.toThrow();
    
    // Test with invalid inputs
    expect(getExpertById('invalid')).toBeUndefined();
    expect(getCategoriesByGroup('invalid')).toHaveLength(0);
  });
});