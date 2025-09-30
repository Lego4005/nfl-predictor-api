-- Add Missing Views and Complete Migration 011
-- Run this if expert_memory_summary view doesn't exist

-- ========================================
-- 1. Expert Memory Summary View
-- ========================================

CREATE OR REPLACE VIEW expert_memory_summary AS
SELECT
    e.expert_id,
    e.name,
    COUNT(em.id) as total_memories,
    AVG(em.emotional_intensity) as avg_emotional_intensity,
    AVG(em.memory_vividness) as avg_memory_vividness,
    SUM(em.retrieval_count) as total_retrievals,
    COUNT(br.id) as total_revisions,
    AVG(br.impact_score) as avg_revision_impact
FROM expert_models e
LEFT JOIN expert_episodic_memories em ON e.expert_id = em.expert_id
LEFT JOIN expert_belief_revisions br ON e.expert_id = br.expert_id
GROUP BY e.expert_id, e.name;

-- ========================================
-- 2. Recent Memory Activity View
-- ========================================

CREATE OR REPLACE VIEW recent_memory_activity AS
SELECT
    expert_id,
    'memory' as activity_type,
    memory_type as activity_subtype,
    emotional_state as activity_detail,
    created_at
FROM expert_episodic_memories
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    expert_id,
    'revision' as activity_type,
    revision_type as activity_subtype,
    emotional_state as activity_detail,
    created_at
FROM expert_belief_revisions
WHERE created_at > NOW() - INTERVAL '7 days'

ORDER BY created_at DESC;

-- ========================================
-- 3. Add Missing Indexes (if not created)
-- ========================================

-- Belief revision indexes
CREATE INDEX IF NOT EXISTS idx_belief_revisions_revision_type ON expert_belief_revisions(revision_type);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_trigger_type ON expert_belief_revisions(trigger_type);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_emotional_state ON expert_belief_revisions(emotional_state);

-- Episodic memory indexes
CREATE INDEX IF NOT EXISTS idx_episodic_memories_memory_type ON expert_episodic_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_emotional_state ON expert_episodic_memories(emotional_state);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_vividness_desc ON expert_episodic_memories(memory_vividness DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_retrieval_composite ON expert_episodic_memories(expert_id, memory_vividness DESC, memory_decay DESC);

-- Time-based composite indexes
CREATE INDEX IF NOT EXISTS idx_episodic_memories_expert_time ON expert_episodic_memories(expert_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_expert_time ON expert_belief_revisions(expert_id, created_at DESC);

-- ========================================
-- 4. Reload Schema Cache
-- ========================================

NOTIFY pgrst, 'reload schema';

-- ========================================
-- 5. Verify Views Work
-- ========================================

-- Test expert_memory_summary
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO view_count FROM expert_memory_summary;
    RAISE NOTICE '✅ expert_memory_summary view works (% rows)', view_count;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '❌ expert_memory_summary view failed: %', SQLERRM;
END;
$$;

-- Test recent_memory_activity
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO view_count FROM recent_memory_activity;
    RAISE NOTICE '✅ recent_memory_activity view works (% rows)', view_count;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '❌ recent_memory_activity view failed: %', SQLERRM;
END;
$$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '════════════════════════════════════════';
    RAISE NOTICE '✅ Views created successfully!';
    RAISE NOTICE '✅ Indexes added!';
    RAISE NOTICE '✅ Schema cache reloaded!';
    RAISE NOTICE '════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Next step: Run tests';
    RAISE NOTICE '  bash scripts/run_memory_tests.sh';
END;
$$;