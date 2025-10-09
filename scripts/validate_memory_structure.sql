-- Quick validation queries for the optimized memory structure
-- Paste these in your Supabase SQL editor to validate the migration

-- 1. Check that vectors are present & HNSW indexes exist
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('expert_episodic_memories','team_knowledge','matchup_memories')
AND indexdef LIKE '%hnsw%';

-- 2. Test the recency-aware RPC returns fast & blended results
SELECT * FROM search_expert_memories(
    p_expert_id := 'momentum_rider',
    p_query_embedding := (
        SELECT combined_embedding
        FROM expert_episodic_memories
        WHERE combined_embedding IS NOT NULL
        LIMIT 1
    ),
    p_match_threshold := 0.70,
    p_match_count := 7,
    p_alpha := 0.80
);

-- 3. Check matchup uniqueness constraint is working
SELECT expert_id, home_team, away_team, count(*) c
FROM matchup_memories
GROUP BY 1,2,3
HAVING count(*) > 1;

-- 4. Verify the compatibility view works
SELECT memory_id, expert_id, teams_involved, memory_type
FROM expert_memory_embeddings
LIMIT 5;

-- 5. Check that FK constraints are in place
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('team_knowledge', 'matchup_memories', 'expert_predictions');

-- 6. Check embedding status across all memories
SELECT
    COUNT(*) as total_memories,
    COUNT(CASE WHEN combined_embedding IS NOT NULL THEN 1 END) as with_embeddings,
    COUNT(CASE WHEN combined_embedding IS NOT NULL THEN 1 END)::float / COUNT(*) as embedding_rate
FROM expert_episodic_memories;

-- 7. Verify team_knowledge structure
SELECT
    expert_id,
    COUNT(*) as teams_analyzed,
    AVG(accuracy) as avg_accuracy,
    SUM(games_analyzed) as total_games
FROM team_knowledge
GROUP BY expert_id
ORDER BY total_games DESC;

-- 8. Verify matchup_memories structure and generated column
SELECT
    expert_id,
    home_team,
    away_team,
    matchup_key_sorted,
    accuracy,
    typical_margin
FROM matchup_memories
ORDER BY games_analyzed DESC
LIMIT 10;

-- 9. Test performance of vector search (should be < 100ms)
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM search_expert_memories(
    p_expert_id := 'conservative_analyzer',
    p_query_embedding := (
        SELECT combined_embedding
        FROM expert_episodic_memories
        WHERE combined_embedding IS NOT NULL
        LIMIT 1
    ),
    p_match_threshold := 0.70,
    p_match_count := 10
);

-- 10. Check that the readonly rule is in place (optional)
SELECT rulename, definition
FROM pg_rules
WHERE tablename = 'expert_memory_embeddings';
