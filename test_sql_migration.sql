-- Test script for pgvector HNSW memory search migration
-- This can be run directly in Supabase SQL editor or psql

-- Test 1: Verify table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'expert_episodic_memories'
    AND column_name IN ('content_embedding', 'context_embedding', 'combined_embedding', 'run_id', 'content_text')
ORDER BY column_name;

-- Test 2: Verify HNSW indexes exist
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'expert_episodic_memories'
    AND indexname LIKE '%hnsw%';

-- Test 3: Test search_expert_memories function exists
SELECT
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines
WHERE routine_name = 'search_expert_memories';

-- Test 4: Test the RPC function with sample data
SELECT
    memory_id,
    similarity_score,
    recency_score,
    combined_score,
    LEFT(content, 50) as content_preview
FROM search_expert_memories(
    'conservative_analyzer',
    'Buffalo Bills',
    5,
    0.8,
    'run_2025_pilot4'
);

-- Test 5: Check sample memories were created
SELECT
    expert_id,
    COUNT(*) as memory_count,
    AVG(memory_vividness) as avg_vividness,
    AVG(memory_decay) as avg_decay
FROM expert_episodic_memories
WHERE run_id = 'run_2025_pilot4'
GROUP BY expert_id
ORDER BY memory_count DESC;

-- Test 6: Test performance function
SELECT * FROM test_memory_search_performance('conservative_analyzer', 'run_2025_pilot4');

-- Test 7: Test memory statistics
SELECT * FROM get_memory_search_stats('run_2025_pilot4');

-- Test 8: Verify vector dimensions
SELECT
    memory_id,
    array_length(content_embedding, 1) as content_dim,
    array_length(context_embedding, 1) as context_dim,
    array_length(combined_embedding, 1) as combined_dim
FROM expert_episodic_memories
WHERE content_embedding IS NOT NULL
LIMIT 3;
