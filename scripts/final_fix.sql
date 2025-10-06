-- Final Fix: Reload Cache + Create Working Views
-- This works with your ACTUAL existing schema

-- ========================================
-- 1. RELOAD SCHEMA CACHE (CRITICAL)
-- ========================================

NOTIFY pgrst, 'reload schema';

-- Wait a moment for cache to refresh
SELECT pg_sleep(2);

-- ========================================
-- 2. Create Simplified Views
-- ========================================

-- Drop any broken views
DROP VIEW IF EXISTS expert_memory_summary CASCADE;
DROP VIEW IF EXISTS recent_memory_activity CASCADE;

-- Create working expert summary view
CREATE OR REPLACE VIEW expert_memory_summary AS
SELECT
    e.expert_id,
    e.name,
    COUNT(DISTINCT em.id) as total_memories,
    COUNT(DISTINCT br.id) as total_revisions,
    COUNT(DISTINCT lp.id) as total_principles
FROM expert_models e
LEFT JOIN expert_episodic_memories em ON e.expert_id = em.expert_id
LEFT JOIN expert_belief_revisions br ON e.expert_id = br.expert_id
LEFT JOIN expert_learned_principles lp ON e.expert_id = lp.expert_id
GROUP BY e.expert_id, e.name;

-- Create working activity view (minimal version)
CREATE OR REPLACE VIEW recent_memory_activity AS
SELECT
    expert_id,
    'memory' as activity_type,
    created_at
FROM expert_episodic_memories
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    expert_id,
    'revision' as activity_type,
    created_at
FROM expert_belief_revisions
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    expert_id,
    'principle' as activity_type,
    created_at
FROM expert_learned_principles
WHERE created_at > NOW() - INTERVAL '7 days'

ORDER BY created_at DESC;

-- ========================================
-- 3. Add Essential Indexes
-- ========================================

CREATE INDEX IF NOT EXISTS idx_episodic_memories_expert_id ON expert_episodic_memories(expert_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_created_at ON expert_episodic_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_expert_id ON expert_belief_revisions(expert_id);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_created_at ON expert_belief_revisions(created_at DESC);

-- ========================================
-- 4. Reload Cache Again
-- ========================================

NOTIFY pgrst, 'reload schema';

-- ========================================
-- 5. Verify Everything Works
-- ========================================

-- Test views
SELECT '✅ Testing expert_memory_summary...' as status;
SELECT COUNT(*) as row_count FROM expert_memory_summary;

SELECT '✅ Testing recent_memory_activity...' as status;
SELECT COUNT(*) as row_count FROM recent_memory_activity;

-- Test table access
SELECT '✅ Testing expert_episodic_memories...' as status;
SELECT COUNT(*) as row_count FROM expert_episodic_memories;

SELECT '✅ Testing expert_belief_revisions...' as status;
SELECT COUNT(*) as row_count FROM expert_belief_revisions;

-- Success message
SELECT '════════════════════════════════════════' as message
UNION ALL SELECT '✅ SCHEMA FIX COMPLETE!'
UNION ALL SELECT '✅ Views created successfully!'
UNION ALL SELECT '✅ Cache reloaded!'
UNION ALL SELECT '════════════════════════════════════════'
UNION ALL SELECT ''
UNION ALL SELECT 'Next step: Run tests'
UNION ALL SELECT '  bash scripts/run_memory_tests.sh';