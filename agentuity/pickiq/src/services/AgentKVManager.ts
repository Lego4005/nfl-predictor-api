/**
 * Agent KV Manager - Manages agent-local state in Agentuity KV
 * 
 * KV Namespaces:
 * - kv:experts:{expert_id}:persona - Expert personality config
 * - kv:experts:{expert_id}:guardrails - Rate limits and constraints
 * - kv:orchestrator:policy - Model routing and eligibility gates
 * - kv:run:{run_id}:playbook - Run-specific configuration
 */

import type { AgentContext } from "@agentuity/sdk";

export interface ExpertPersona {
  expert_id: string;
  traits: string[];
  system_prompt: string;
  risk_profile: 'conservative' | 'moderate' | 'aggressive';
  base_confidence_range: [number, number];
  base_stake_range: [number, number];
  recency_alpha: number;
  tool_budget: {
    max_calls_per_game: number;
    max_time_ms: number;
  };
}

export interface Guardrails {
  time_ms_max: number;
  tool_calls_max: number;
  token_limit_input: number;
  token_limit_output: number;
  forbidden_sources: string[];
  stake_caps: {
    max_per_prediction: number;
    max_total_game: number;
  };
  rate_limits: {
    news_fetch: { per_minute: number; timeout_ms: number };
    market_poll: { interval_ms: number };
    live_updates: { min_interval_ms: number; max_per_game: number };
  };
}

export interface OrchestratorPolicy {
  model_routing_rules: {
    default_model: string;
    critic_model: string;
    eligibility_gates: {
      min_schema_pass_rate: number;
      max_p95_latency_ms: number;
    };
  };
  bandit_params: {
    algorithm: 'thompson' | 'ucb';
    min_exploration_rate: number;
  };
  dwell_time_sec: number;
  revert_on_harm_threshold: number;
}

export interface RunPlaybook {
  retrieval_K_default: number;
  recency_alpha_rules: {
    override_by_expert?: Record<string, number>;
    adjustment_by_week?: 'early_season' | 'mid_season' | 'late_season';
  };
  reflection_enabled: boolean;
  stakes_enabled: boolean;
  tools_enabled: boolean;
  live_mode: boolean;
}

export class AgentKVManager {
  
  static async getExpertPersona(ctx: AgentContext, expertId: string): Promise<ExpertPersona | null> {
    try {
      const result = await ctx.kv.get('expert-personas', expertId);
      if (!result.exists) return null;
      const data = await result.data.json();
      return data as unknown as ExpertPersona;
    } catch (error) {
      ctx.logger.warn(`Failed to get persona for ${expertId}:`, error);
      return null;
    }
  }

  static async setExpertPersona(ctx: AgentContext, expertId: string, persona: ExpertPersona): Promise<void> {
    await ctx.kv.set('expert-personas', expertId, persona, { ttl: 86400 * 30 }); // 30 days
  }

  static async getGuardrails(ctx: AgentContext, expertId: string): Promise<Guardrails | null> {
    try {
      const result = await ctx.kv.get('expert-guardrails', expertId);
      if (!result.exists) return null;
      const data = await result.data.json();
      return data as unknown as Guardrails;
    } catch (error) {
      ctx.logger.warn(`Failed to get guardrails for ${expertId}:`, error);
      return null;
    }
  }

  static async setGuardrails(ctx: AgentContext, expertId: string, guardrails: Guardrails): Promise<void> {
    await ctx.kv.set('expert-guardrails', expertId, guardrails, { ttl: 86400 * 30 });
  }

  static async getOrchestratorPolicy(ctx: AgentContext): Promise<OrchestratorPolicy | null> {
    try {
      const result = await ctx.kv.get('orchestrator', 'policy');
      if (!result.exists) return null;
      const data = await result.data.json();
      return data as unknown as OrchestratorPolicy;
    } catch (error) {
      ctx.logger.warn('Failed to get orchestrator policy:', error);
      return null;
    }
  }

  static async setOrchestratorPolicy(ctx: AgentContext, policy: OrchestratorPolicy): Promise<void> {
    await ctx.kv.set('orchestrator', 'policy', policy, { ttl: 86400 * 30 });
  }

  static async getRunPlaybook(ctx: AgentContext, runId: string): Promise<RunPlaybook | null> {
    try {
      const result = await ctx.kv.get('run-playbooks', runId);
      if (!result.exists) return null;
      const data = await result.data.json();
      return data as unknown as RunPlaybook;
    } catch (error) {
      ctx.logger.warn(`Failed to get playbook for ${runId}:`, error);
      return null;
    }
  }

  static async setRunPlaybook(ctx: AgentContext, runId: string, playbook: RunPlaybook): Promise<void> {
    await ctx.kv.set('run-playbooks', runId, playbook, { ttl: 86400 * 90 }); // 90 days
  }

  static async logEffectiveConfig(
    ctx: AgentContext,
    expertId: string,
    runId: string,
    persona: ExpertPersona | null,
    guardrails: Guardrails | null,
    playbook: RunPlaybook | null
  ): Promise<void> {
    ctx.logger.info('=== Effective Agent Configuration ===', {
      expert_id: expertId,
      run_id: runId,
      persona_loaded: !!persona,
      guardrails_loaded: !!guardrails,
      playbook_loaded: !!playbook,
      recency_alpha: persona?.recency_alpha || 'default',
      tool_budget: persona?.tool_budget || 'default',
      stake_caps: guardrails?.stake_caps || 'default',
      retrieval_K: playbook?.retrieval_K_default || 'default',
      tools_enabled: playbook?.tools_enabled || false,
      live_mode: playbook?.live_mode || false
    });
  }
}

// Default configurations for the 4 experts
export const DEFAULT_PERSONAS: Record<string, ExpertPersona> = {
  'the-analyst': {
    expert_id: 'the-analyst',
    traits: ['conservative', 'data-driven', 'risk-averse', 'defensive-focused'],
    system_prompt: 'You are a conservative, data-driven NFL analyst who prioritizes statistical rigor and risk management. You prefer lower-variance bets with consistent returns.',
    risk_profile: 'conservative',
    base_confidence_range: [0.55, 0.70],
    base_stake_range: [0.5, 2.0],
    recency_alpha: 0.50,
    tool_budget: { max_calls_per_game: 8, max_time_ms: 3000 }
  },
  'the-rebel': {
    expert_id: 'the-rebel',
    traits: ['contrarian', 'anti-consensus', 'public-fade', 'value-seeking'],
    system_prompt: 'You are a contrarian NFL analyst who thrives on fading public sentiment and finding market inefficiencies. You go against popular opinion.',
    risk_profile: 'aggressive',
    base_confidence_range: [0.65, 0.80],
    base_stake_range: [1.5, 3.5],
    recency_alpha: 0.65,
    tool_budget: { max_calls_per_game: 10, max_time_ms: 4000 }
  },
  'the-rider': {
    expert_id: 'the-rider',
    traits: ['momentum', 'trend-following', 'recency-heavy', 'hot-hand'],
    system_prompt: 'You are a momentum-focused NFL analyst who heavily weights recent performance and streaks. You believe momentum is a powerful predictive force.',
    risk_profile: 'aggressive',
    base_confidence_range: [0.70, 0.85],
    base_stake_range: [2.0, 4.0],
    recency_alpha: 0.80,
    tool_budget: { max_calls_per_game: 10, max_time_ms: 3500 }
  },
  'the-hunter': {
    expert_id: 'the-hunter',
    traits: ['value-seeking', 'EV-focused', 'market-efficiency', 'arbitrage'],
    system_prompt: 'You are a value-focused NFL analyst who hunts for mispriced lines and positive expected value. You focus on market inefficiencies.',
    risk_profile: 'moderate',
    base_confidence_range: [0.62, 0.78],
    base_stake_range: [1.2, 3.0],
    recency_alpha: 0.55,
    tool_budget: { max_calls_per_game: 12, max_time_ms: 5000 }
  }
};

export const DEFAULT_GUARDRAILS: Guardrails = {
  time_ms_max: 30000,
  tool_calls_max: 10,
  token_limit_input: 8000,
  token_limit_output: 4000,
  forbidden_sources: ['twitter-unverified', 'reddit', 'discord'],
  stake_caps: {
    max_per_prediction: 5.0,
    max_total_game: 50.0
  },
  rate_limits: {
    news_fetch: { per_minute: 6, timeout_ms: 2000 },
    market_poll: { interval_ms: 60000 },
    live_updates: { min_interval_ms: 300000, max_per_game: 3 }
  }
};

export const DEFAULT_ORCHESTRATOR_POLICY: OrchestratorPolicy = {
  model_routing_rules: {
    default_model: 'claude-sonnet-4',
    critic_model: 'claude-sonnet-4',
    eligibility_gates: {
      min_schema_pass_rate: 0.985,
      max_p95_latency_ms: 5000
    }
  },
  bandit_params: {
    algorithm: 'thompson',
    min_exploration_rate: 0.15
  },
  dwell_time_sec: 300,
  revert_on_harm_threshold: 0.05
};

export const DEFAULT_RUN_PLAYBOOK: RunPlaybook = {
  retrieval_K_default: 12,
  recency_alpha_rules: {
    adjustment_by_week: 'mid_season'
  },
  reflection_enabled: false,
  stakes_enabled: true,
  tools_enabled: false,
  live_mode: false
};