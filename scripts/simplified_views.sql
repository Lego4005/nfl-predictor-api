-- Simplified Views Without Missing Columns
-- This version works around potential column name differences

-- ========================================
-- 1. Simplified Expert Memory Summary View
-- ========================================

-- Drop existing view if it has errors
DROP VIEW IF EXISTS expert_memory_summary CASCADE;

-- Create simplified version that only uses guaranteed columns
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

-- ========================================
-- 2. Simplified Recent Activity View
-- ========================================

-- Drop existing view if it has errors
DROP VIEW IF EXISTS recent_memory_activity CASCADE;

-- Create simplified version
CREATE OR REPLACE VIEW recent_memory_activity AS
SELECT
    expert_id,
    'memory' as activity_type,
    memory_type as activity_subtype,
    created_at
FROM expert_episodic_memories
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    expert_id,
    'revision' as activity_type,
    revision_type as activity_subtype,
    created_at
FROM expert_belief_revisions
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    expert_id,
    'principle' as activity_type,
    category as activity_subtype,
    created_at
FROM expert_learned_principles
WHERE created_at > NOW() - INTERVAL '7 days'

ORDER BY created_at DESC;

-- ========================================
-- 3. Essential Indexes Only
-- ========================================

-- Core indexes that should always work
CREATE INDEX IF NOT EXISTS idx_episodic_memories_expert_id ON expert_episodic_memories(expert_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_created_at ON expert_episodic_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_expert_id ON expert_belief_revisions(expert_id);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_created_at ON expert_belief_revisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_learned_principles_expert_id ON expert_learned_principles(expert_id);
CREATE INDEX IF NOT EXISTS idx_learned_principles_created_at ON expert_learned_principles(created_at DESC);

-- ========================================
-- 4. Reload Schema Cache
-- ========================================

NOTIFY pgrst, 'reload schema';

-- ========================================
-- 5. Test Views
-- ========================================

-- Test expert_memory_summary
SELECT 'Testing expert_memory_summary...' as status;
SELECT * FROM expert_memory_summary LIMIT 3;

-- Test recent_memory_activity
SELECT 'Testing recent_memory_activity...' as status;
SELECT * FROM recent_memory_activity LIMIT 3;

-- Success
SELECT '✅ Views created and tested successfully!' as status;