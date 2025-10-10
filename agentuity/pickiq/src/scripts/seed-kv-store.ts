/**
 * Seed KV Store with Initial Agent Configurations
 * Run with: bun run src/scripts/seed-kv-store.ts
 */

import {
  AgentKVManager,
  DEFAULT_PERSONAS,
  DEFAULT_GUARDRAILS,
  DEFAULT_ORCHESTRATOR_POLICY,
  DEFAULT_RUN_PLAYBOOK
} from '../services/AgentKVManager';

// Mock context for seeding (would use real context in actual agent)
const mockContext: any = {
  kv: {
    async set(namespace: string, key: string, value: any, options?: any) {
      console.log(`✓ Set ${namespace}:${key}`);
      return true;
    },
    async get(namespace: string, key: string) {
      return { exists: false, data: { json: null } };
    }
  },
  logger: {
    info: console.log,
    warn: console.warn,
    error: console.error
  }
};

async function seedKVStore() {
  console.log('🌱 Seeding Agentuity KV Store...\n');

  // Seed expert personas
  console.log('📝 Seeding Expert Personas:');
  for (const [expertId, persona] of Object.entries(DEFAULT_PERSONAS)) {
    await AgentKVManager.setExpertPersona(mockContext, expertId, persona);
  }

  // Seed guardrails for each expert
  console.log('\n🛡️  Seeding Expert Guardrails:');
  for (const expertId of Object.keys(DEFAULT_PERSONAS)) {
    await AgentKVManager.setGuardrails(mockContext, expertId, DEFAULT_GUARDRAILS);
  }

  // Seed orchestrator policy
  console.log('\n🎯 Seeding Orchestrator Policy:');
  await AgentKVManager.setOrchestratorPolicy(mockContext, DEFAULT_ORCHESTRATOR_POLICY);

  // Seed default run playbook
  console.log('\n📋 Seeding Default Run Playbook:');
  await AgentKVManager.setRunPlaybook(mockContext, 'run_2025_pilot4', DEFAULT_RUN_PLAYBOOK);

  console.log('\n✅ KV Store seeding complete!\n');
  console.log('Configuration Summary:');
  console.log('- 4 expert personas');
  console.log('- 4 expert guardrails');
  console.log('- 1 orchestrator policy');
  console.log('- 1 run playbook (run_2025_pilot4)');
}

// Run seeding
seedKVStore().catch(console.error);
