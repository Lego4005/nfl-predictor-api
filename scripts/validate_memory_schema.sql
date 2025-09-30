-- Validation Script for Episodic Memory System
-- Run this in Supabase SQL Editor to validate the migration

-- ========================================
-- 1. Validate Views Compile
-- ========================================

-- Test expert_memory_summary view
SELECT * FROM expert_memory_summary LIMIT 5;

-- Test recent_memory_activity view
SELECT * FROM recent_memory_activity LIMIT 10;

-- ========================================
-- 2. Add Helpful Indexes for New Columns
-- ========================================

-- Indexes for belief revisions (if not already created)
CREATE INDEX IF NOT EXISTS idx_belief_revisions_revision_type ON expert_belief_revisions(revision_type);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_trigger_type ON expert_belief_revisions(trigger_type);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_emotional_state ON expert_belief_revisions(emotional_state);

-- Indexes for episodic memories (if not already created)
CREATE INDEX IF NOT EXISTS idx_episodic_memories_memory_type ON expert_episodic_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_emotional_state ON expert_episodic_memories(emotional_state);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_vividness_desc ON expert_episodic_memories(memory_vividness DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_retrieval_composite ON expert_episodic_memories(expert_id, memory_vividness DESC, memory_decay DESC);

-- Composite index for time-based queries
CREATE INDEX IF NOT EXISTS idx_episodic_memories_expert_time ON expert_episodic_memories(expert_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_expert_time ON expert_belief_revisions(expert_id, created_at DESC);

-- ========================================
-- 3. Validate Table Structure
-- ========================================

-- Check expert_episodic_memories columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'expert_episodic_memories'
ORDER BY ordinal_position;

-- Check expert_belief_revisions columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'expert_belief_revisions'
ORDER BY ordinal_position;

-- ========================================
-- 4. Test Basic Operations
-- ========================================

-- Test insert into expert_episodic_memories
-- (Will fail if expert doesn't exist, but shows schema works)
-- INSERT INTO expert_episodic_memories (
--     memory_id, expert_id, game_id, memory_type, emotional_state,
--     prediction_data, actual_outcome, emotional_intensity, memory_vividness
-- ) VALUES (
--     'test_mem_001', 'test_expert', 'test_game', 'prediction_outcome', 'satisfaction',
--     '{"winner": "KC", "confidence": 0.75}', '{"winner": "KC", "score": "27-20"}',
--     0.8, 0.75
-- );

-- Test select
SELECT COUNT(*) as episodic_memory_count FROM expert_episodic_memories;
SELECT COUNT(*) as belief_revision_count FROM expert_belief_revisions;
SELECT COUNT(*) as learned_principles_count FROM expert_learned_principles;

-- ========================================
-- 5. Verify Functions Work
-- ========================================

-- Test decay function (safe to run, just updates old memories)
-- SELECT decay_episodic_memories();

-- Test calculate_revision_impact function
SELECT calculate_revision_impact(
    '{"winner": "KC", "confidence": 0.65}'::jsonb,
    '{"winner": "BAL", "confidence": 0.75}'::jsonb,
    'complete_reversal'
) as impact_score;

-- ========================================
-- 6. Summary Report
-- ========================================

SELECT
    'expert_episodic_memories' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT expert_id) as expert_count,
    MIN(created_at) as earliest_memory,
    MAX(created_at) as latest_memory
FROM expert_episodic_memories

UNION ALL

SELECT
    'expert_belief_revisions' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT expert_id) as expert_count,
    MIN(created_at) as earliest_revision,
    MAX(created_at) as latest_revision
FROM expert_belief_revisions

UNION ALL

SELECT
    'expert_learned_principles' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT expert_id) as expert_count,
    MIN(created_at) as earliest_principle,
    MAX(created_at) as latest_principle
FROM expert_learned_principles;

-- ========================================
-- 7. Reload Schema Cache
-- ========================================

-- Force PostgREST to reload schema
NOTIFY pgrst, 'reload schema';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Schema validation complete!';
    RAISE NOTICE '✅ Indexes created!';
    RAISE NOTICE '✅ Functions tested!';
    RAISE NOTICE '✅ PostgREST schema cache reloaded!';
    RAISE NOTICE '';
    RAISE NOTICE 'Next step: Run Python tests';
    RAISE NOTICE '  python3 tests/test_episodic_memory_system.py';
END;
$$;