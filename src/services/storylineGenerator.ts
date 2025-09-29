/**
 * Expert Storyline Generation and Competitive Narrative System
 * Creates engaging narratives around expert competition and performance
 */

import { ExpertPersonality, EXPERT_PERSONALITIES, getCouncilMembers } from '@/data/expertPersonalities';
import { CouncilMember } from '@/services/councilSelection';

export interface ExpertStoryline {
  id: string;
  expertId: string;
  type: StorylineType;
  title: string;
  description: string;
  narrative: string;
  tags: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  duration: 'short' | 'medium' | 'long';
  metrics: StorylineMetrics;
}

export type StorylineType = 
  | 'promotion' | 'demotion' | 'hot_streak' | 'cold_streak'
  | 'upset_prediction' | 'rivalry' | 'comeback' | 'dominance'
  | 'specialization' | 'controversy' | 'milestone';

export interface StorylineMetrics {
  engagement_score: number;
  accuracy_change: number;
  rank_change: number;
  streak_length: number;
  confidence_level: number;
  impact_rating: number;
}

export interface StorylineContext {
  current_week: number;
  recent_performance: number[];
  rank_history: number[];
  council_status: boolean;
  recent_predictions: any[];
  competitor_experts: ExpertPersonality[];
  consensus_agreements: number;
  category_performance: Record<string, number>;
}

export class StorylineGenerator {
  private templates: Map<StorylineType, string[]> = new Map();

  constructor() {
    this.initializeTemplates();
  }

  private initializeTemplates() {
    this.templates.set('promotion', [
      '🎉 {expertName} Joins the AI Council!',
      'After weeks of exceptional performance, {expertName} has earned a coveted council seat with {accuracy}% accuracy.',
      'Outstanding {archetype} analysis has elevated {expertName} to council status.'
    ]);

    this.templates.set('hot_streak', [
      '🔥 {expertName} On Fire: {streakLength} Game Winning Streak!',
      '{expertName} has correctly predicted {streakLength} consecutive games, showcasing remarkable analytical prowess.',
      'The {archetype} expert\'s hot streak has boosted accuracy to {accuracy}%.'
    ]);

    this.templates.set('rivalry', [
      '⚔️ Epic Rivalry: {expertName} vs {rivalName}',
      'A fierce competition has emerged between {expertName} and {rivalName}, pushing both to new heights.',
      'These contrasting {archetype1} and {archetype2} approaches create compelling storylines.'
    ]);

    this.templates.set('specialization', [
      '🎯 {expertName}: Master of {category}',
      'With {categoryAccuracy}% accuracy in {category}, {expertName} has established specialist dominance.',
      'The {archetype} expert\'s focused approach has made them the go-to voice for {category} predictions.'
    ]);

    this.templates.set('milestone', [
      '🏆 Milestone Achievement: {expertName} Reaches {milestone}',
      '{expertName} has achieved {milestone}, joining an elite group of prediction masters.',
      'This {archetype} expert\'s consistency has earned historic recognition.'
    ]);
  }

  public generateStoryline(expert: ExpertPersonality, context: StorylineContext): ExpertStoryline | null {
    const storylineType = this.detectStorylineType(expert, context);
    if (!storylineType) return null;

    const templates = this.templates.get(storylineType);
    if (!templates) return null;

    const variables = this.extractVariables(expert, context, storylineType);
    const title = this.fillTemplate(templates[0], variables);
    const description = this.fillTemplate(templates[1], variables);
    const narrative = this.fillTemplate(templates[2], variables);

    return {
      id: `storyline_${expert.id}_${Date.now()}`,
      expertId: expert.id,
      type: storylineType,
      title,
      description,
      narrative,
      tags: this.generateTags(storylineType, expert),
      severity: this.calculateSeverity(storylineType, context),
      timestamp: new Date().toISOString(),
      duration: this.calculateDuration(storylineType),
      metrics: this.calculateMetrics(expert, context, storylineType)
    };
  }

  private detectStorylineType(expert: ExpertPersonality, context: StorylineContext): StorylineType | null {
    // Council promotion
    if (context.council_status && context.rank_history.length > 0 && context.rank_history[0] > 5) {
      return 'promotion';
    }

    // Hot streak detection
    if (context.recent_performance.filter(p => p > 0.8).length >= 3) {
      return 'hot_streak';
    }

    // Cold streak detection
    if (context.recent_performance.filter(p => p < 0.4).length >= 3) {
      return 'cold_streak';
    }

    // Specialization mastery
    const bestCategory = Object.entries(context.category_performance).reduce((a, b) => a[1] > b[1] ? a : b);
    if (bestCategory[1] > 0.8) {
      return 'specialization';
    }

    // Milestone achievement
    if (expert.track_record.total_predictions >= 100 && expert.accuracy_metrics.overall >= 0.7) {
      return 'milestone';
    }

    // Rivalry detection
    if (context.competitor_experts.length > 0) {
      const rival = context.competitor_experts[0];
      if (Math.abs(expert.accuracy_metrics.overall - rival.accuracy_metrics.overall) < 0.05) {
        return 'rivalry';
      }
    }

    return null;
  }

  private extractVariables(expert: ExpertPersonality, context: StorylineContext, type: StorylineType): Record<string, string> {
    const variables: Record<string, string> = {
      expertName: expert.name,
      archetype: expert.archetype,
      accuracy: (expert.accuracy_metrics.overall * 100).toFixed(1),
      motto: expert.motto,
      specialization: expert.primary_expertise.join(', ')
    };

    switch (type) {
      case 'hot_streak':
        variables.streakLength = context.recent_performance.filter(p => p > 0.8).length.toString();
        break;
      case 'rivalry':
        if (context.competitor_experts.length > 0) {
          variables.rivalName = context.competitor_experts[0].name;
          variables.archetype1 = expert.archetype;
          variables.archetype2 = context.competitor_experts[0].archetype;
        }
        break;
      case 'specialization':
        const bestCategory = Object.entries(context.category_performance).reduce((a, b) => a[1] > b[1] ? a : b);
        variables.category = bestCategory[0];
        variables.categoryAccuracy = (bestCategory[1] * 100).toFixed(1);
        break;
      case 'milestone':
        variables.milestone = `${expert.track_record.total_predictions} Total Predictions`;
        break;
    }

    return variables;
  }

  private fillTemplate(template: string, variables: Record<string, string>): string {
    let result = template;
    for (const [key, value] of Object.entries(variables)) {
      result = result.replace(new RegExp(`{${key}}`, 'g'), value);
    }
    return result;
  }

  private generateTags(type: StorylineType, expert: ExpertPersonality): string[] {
    const baseTags = [expert.archetype.toLowerCase(), expert.risk_tolerance];
    
    switch (type) {
      case 'promotion':
        return [...baseTags, 'council', 'achievement', 'success'];
      case 'hot_streak':
        return [...baseTags, 'streak', 'performance', 'momentum'];
      case 'rivalry':
        return [...baseTags, 'competition', 'rivalry', 'battle'];
      case 'specialization':
        return [...baseTags, 'expertise', 'mastery', 'specialist'];
      default:
        return baseTags;
    }
  }

  private calculateSeverity(type: StorylineType, context: StorylineContext): 'low' | 'medium' | 'high' | 'critical' {
    switch (type) {
      case 'promotion':
      case 'milestone':
        return 'high';
      case 'hot_streak':
        return context.recent_performance.filter(p => p > 0.8).length >= 5 ? 'critical' : 'high';
      case 'rivalry':
        return 'medium';
      case 'specialization':
        return 'medium';
      default:
        return 'low';
    }
  }

  private calculateDuration(type: StorylineType): 'short' | 'medium' | 'long' {
    switch (type) {
      case 'promotion':
      case 'milestone':
        return 'long';
      case 'hot_streak':
      case 'cold_streak':
        return 'medium';
      case 'rivalry':
        return 'long';
      default:
        return 'short';
    }
  }

  private calculateMetrics(expert: ExpertPersonality, context: StorylineContext, type: StorylineType): StorylineMetrics {
    const baseMetrics = {
      engagement_score: 0.5,
      accuracy_change: expert.accuracy_metrics.recent_performance - expert.accuracy_metrics.overall,
      rank_change: 0,
      streak_length: 0,
      confidence_level: expert.confidence_calibration,
      impact_rating: 5
    };

    switch (type) {
      case 'promotion':
        return {
          ...baseMetrics,
          engagement_score: 0.9,
          rank_change: context.rank_history.length > 0 ? context.rank_history[0] - (expert.council_position || 1) : 0,
          impact_rating: 9
        };
      case 'hot_streak':
        const streak = context.recent_performance.filter(p => p > 0.8).length;
        return {
          ...baseMetrics,
          engagement_score: Math.min(1.0, 0.6 + (streak * 0.1)),
          streak_length: streak,
          impact_rating: Math.min(10, 6 + streak)
        };
      default:
        return baseMetrics;
    }
  }

  public generateMultipleStorylines(experts: ExpertPersonality[], contexts: Record<string, StorylineContext>): ExpertStoryline[] {
    const storylines: ExpertStoryline[] = [];
    
    for (const expert of experts) {
      const context = contexts[expert.id];
      if (context) {
        const storyline = this.generateStoryline(expert, context);
        if (storyline) {
          storylines.push(storyline);
        }
      }
    }

    return storylines.sort((a, b) => b.metrics.impact_rating - a.metrics.impact_rating);
  }

  public getTopStorylines(limit: number = 5): ExpertStoryline[] {
    // Mock implementation - in real app, this would fetch from database
    const mockContexts: Record<string, StorylineContext> = {};
    
    EXPERT_PERSONALITIES.forEach(expert => {
      mockContexts[expert.id] = {
        current_week: 3,
        recent_performance: [0.8, 0.7, 0.9, 0.6, 0.8],
        rank_history: [expert.council_position ? expert.council_position + 2 : 8],
        council_status: expert.council_position !== undefined,
        recent_predictions: [],
        competitor_experts: EXPERT_PERSONALITIES.filter(e => e.id !== expert.id).slice(0, 2),
        consensus_agreements: 0.7,
        category_performance: {
          'core': 0.8,
          'props': 0.7,
          'situational': 0.9
        }
      };
    });

    return this.generateMultipleStorylines(EXPERT_PERSONALITIES, mockContexts).slice(0, limit);
  }
}

// Export singleton instance
export const storylineGenerator = new StorylineGenerator();

// Utility functions
export const generateExpertStorylines = (expertIds?: string[]): ExpertStoryline[] => {
  const experts = expertIds 
    ? EXPERT_PERSONALITIES.filter(e => expertIds.includes(e.id))
    : EXPERT_PERSONALITIES;
    
  return storylineGenerator.getTopStorylines(experts.length);
};

export const getStorylinesByType = (type: StorylineType): ExpertStoryline[] => {
  return storylineGenerator.getTopStorylines(15).filter(s => s.type === type);
};

export const getExpertStorylines = (expertId: string): ExpertStoryline[] => {
  return storylineGenerator.getTopStorylines(15).filter(s => s.expertId === expertId);
};