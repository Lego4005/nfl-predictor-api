/**
 * Agent Vector Cache - Lightweight transient vector storage for live briefs
 * 
 * Collections:
 * - vec:live-briefs:{expert_id} - Short facts during live games
 * - vec:rules-snippets - Guardrail/rule reminders
 * 
 * NOTE: This is NOT the system of record - use for agent-local cache only
 * Main episodic memory stays in Postgres/pgvector
 */

import type { AgentContext } from "@agentuity/sdk";

export interface LiveBrief {
  brief_id: string;
  expert_id: string;
  game_id: string;
  event_type: 'score_change' | 'injury' | 'line_movement' | 'weather' | 'other';
  summary: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export class AgentVectorCache {
  
  /**
   * Cache a live brief for quick retrieval during game
   * NOTE: Transient cache only - not system of record
   */
  static async cacheLiveBrief(
    ctx: AgentContext,
    expertId: string,
    text: string,
    metadata: Record<string, any>
  ): Promise<void> {
    try {
      const briefId = `brief_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const collectionName = `live-briefs-${expertId}`;
      
      const document = {
        key: briefId,
        document: text,
        metadata: {
          ...metadata,
          expert_id: expertId,
          cached_at: new Date().toISOString()
        }
      };
      
      // Upsert into Agentuity vector store
      await ctx.vector.upsert(collectionName, document);
      
      ctx.logger.debug(`Cached live brief: ${briefId} for ${expertId}`);
    } catch (error) {
      ctx.logger.warn(`Failed to cache live brief:`, error);
    }
  }

  /**
   * Retrieve recent live briefs for an expert
   * Returns top-K most relevant briefs from cache
   */
  static async retrieveLiveBriefs(
    ctx: AgentContext,
    expertId: string,
    query: string,
    k: number = 5
  ): Promise<LiveBrief[]> {
    try {
      const collectionName = `live-briefs-${expertId}`;
      
      const results = await ctx.vector.search(collectionName, {
        query,
        limit: k,
        similarity: 0.6
      });
      
      return results.map((result: any) => ({
        brief_id: result.key,
        expert_id: result.metadata.expert_id,
        game_id: result.metadata.game_id || 'unknown',
        event_type: result.metadata.event_type || 'other',
        summary: result.document,
        timestamp: result.metadata.cached_at,
        metadata: result.metadata
      }));
    } catch (error) {
      ctx.logger.warn(`Failed to retrieve live briefs:`, error);
      return [];
    }
  }

  /**
   * Cache a guardrail/rule snippet for reinforcement
   */
  static async cacheRuleSnippet(
    ctx: AgentContext,
    ruleId: string,
    text: string,
    metadata: Record<string, any>
  ): Promise<void> {
    try {
      const document = {
        key: ruleId,
        document: text,
        metadata: {
          ...metadata,
          cached_at: new Date().toISOString()
        }
      };
      
      await ctx.vector.upsert('rules-snippets', document);
      ctx.logger.debug(`Cached rule snippet: ${ruleId}`);
    } catch (error) {
      ctx.logger.warn(`Failed to cache rule snippet:`, error);
    }
  }

  /**
   * Retrieve relevant rules for current context
   */
  static async retrieveRelevantRules(
    ctx: AgentContext,
    query: string,
    k: number = 3
  ): Promise<Array<{ rule_id: string; text: string }>> {
    try {
      const results = await ctx.vector.search('rules-snippets', {
        query,
        limit: k,
        similarity: 0.7
      });
      
      return results.map((result: any) => ({
        rule_id: result.key,
        text: result.document
      }));
    } catch (error) {
      ctx.logger.warn(`Failed to retrieve rules:`, error);
      return [];
    }
  }

  /**
   * Clear transient cache for an expert/game
   */
  static async clearLiveBriefs(
    ctx: AgentContext,
    expertId: string,
    briefIds: string[]
  ): Promise<void> {
    try {
      const collectionName = `live-briefs-${expertId}`;
      
      for (const briefId of briefIds) {
        await ctx.vector.delete(collectionName, briefId);
      }
      
      ctx.logger.info(`Cleared ${briefIds.length} live briefs for ${expertId}`);
    } catch (error) {
      ctx.logger.warn(`Failed to clear live briefs:`, error);
    }
  }
}
