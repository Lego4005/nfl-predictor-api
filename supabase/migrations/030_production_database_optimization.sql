-- Production Database Optimization Settings
-- These SQL commands optimize the database for production workloads
-- Run these in the Supabase SQL Editor or via migration

-- =====================================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- =====================================================

-- Set optimal shared memory and buffer settings
-- Note: In Supabase, these are managed at the instance level
-- These are reference settings for self-hosted PostgreSQL

-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';
-- ALTER SYSTEM SET work_mem = '4MB';
-- ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Connection and query optimization
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET statement_timeout = '30s';
ALTER SYSTEM SET lock_timeout = '10s';
ALTER SYSTEM SET idle_in_transaction_session_timeout = '60s';

-- Query planner optimization
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET seq_page_cost = 1.0;

-- Logging and monitoring
ALTER SYSTEM SET log_min_duration_statement = '1000'; -- Log queries > 1 second
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Auto-vacuum optimization
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '1min';
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;

-- =====================================================
-- OPTIMIZED INDEXES FOR EXPERT COMPETITION SYSTEM
-- =====================================================

-- Expert models performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_models_active_rank 
ON enhanced_expert_models(is_active, current_rank) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_models_performance_trend 
ON enhanced_expert_models(overall_accuracy DESC, recent_performance DESC, consistency_score DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_models_specialization 
ON enhanced_expert_models USING GIN(expertise_areas);

-- Expert predictions optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_game_expert 
ON expert_predictions_enhanced(game_id, expert_id, prediction_timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_confidence 
ON expert_predictions_enhanced(confidence_score DESC, accuracy_score DESC) 
WHERE accuracy_score IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_categories 
ON expert_predictions_enhanced(game_id) 
INCLUDE (winner_prediction, exact_score_home, exact_score_away, total_points_prediction);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_expert_predictions_recent 
ON expert_predictions_enhanced(prediction_timestamp DESC) 
WHERE prediction_timestamp > NOW() - INTERVAL '30 days';

-- AI Council selections optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_council_round_performance 
ON ai_council_selections(round_id, expert_performance_score DESC, selection_timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_council_active_experts 
ON ai_council_selections(expert_id, is_current_member) 
WHERE is_current_member = true;

-- AI Council voting optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_council_voting_round 
ON ai_council_voting(round_id, vote_timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_council_voting_expert_weight 
ON ai_council_voting(expert_id, weight DESC, vote_timestamp);

-- Performance analytics optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_analytics_expert_category 
ON expert_performance_analytics(expert_id, category, metric_type, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_analytics_recent 
ON expert_performance_analytics(timestamp DESC) 
WHERE timestamp > NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_analytics_trends 
ON expert_performance_analytics(expert_id, metric_type, timestamp) 
WHERE metric_type IN ('accuracy', 'confidence', 'roi');

-- Self-healing events optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_self_healing_events_type_time 
ON self_healing_events(trigger_type, event_timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_self_healing_recent 
ON self_healing_events(event_timestamp DESC) 
WHERE event_timestamp > NOW() - INTERVAL '24 hours';

-- Episodic memory optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_episodic_memory_expert_type 
ON episodic_memory(expert_id, memory_type, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_episodic_memory_importance 
ON episodic_memory(importance_score DESC, created_at DESC) 
WHERE importance_score > 0.7;

-- =====================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- =====================================================

-- Expert leaderboard materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_expert_leaderboard AS
SELECT 
    em.expert_id,
    em.expert_name,
    em.personality_type,
    em.current_rank,
    em.overall_accuracy,
    em.recent_performance,
    em.consistency_score,
    em.specialization_score,
    em.total_predictions,
    em.correct_predictions,
    COUNT(acs.expert_id) as council_selections,
    CASE WHEN acs.is_current_member THEN 'AI Council Member' ELSE 'Regular Expert' END as status,
    em.last_updated
FROM enhanced_expert_models em
LEFT JOIN ai_council_selections acs ON em.expert_id = acs.expert_id
WHERE em.is_active = true
GROUP BY em.expert_id, em.expert_name, em.personality_type, em.current_rank, 
         em.overall_accuracy, em.recent_performance, em.consistency_score,
         em.specialization_score, em.total_predictions, em.correct_predictions,
         acs.is_current_member, em.last_updated
ORDER BY em.current_rank ASC;

-- Create unique index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_expert_leaderboard_expert_id 
ON mv_expert_leaderboard(expert_id);

-- Expert performance trends materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_expert_performance_trends AS
SELECT 
    epa.expert_id,
    em.expert_name,
    epa.category,
    epa.metric_type,
    AVG(epa.metric_value) as avg_metric,
    MAX(epa.metric_value) as max_metric,
    MIN(epa.metric_value) as min_metric,
    COUNT(*) as data_points,
    MAX(epa.timestamp) as last_updated,
    -- Calculate trend direction
    CASE 
        WHEN 
            (SELECT metric_value FROM expert_performance_analytics epa2 
             WHERE epa2.expert_id = epa.expert_id 
             AND epa2.category = epa.category 
             AND epa2.metric_type = epa.metric_type 
             ORDER BY timestamp DESC LIMIT 1) >
            (SELECT metric_value FROM expert_performance_analytics epa3 
             WHERE epa3.expert_id = epa.expert_id 
             AND epa3.category = epa.category 
             AND epa3.metric_type = epa.metric_type 
             AND epa3.timestamp < NOW() - INTERVAL '7 days'
             ORDER BY timestamp DESC LIMIT 1)
        THEN 'improving'
        ELSE 'declining'
    END as trend_direction
FROM expert_performance_analytics epa
JOIN enhanced_expert_models em ON epa.expert_id = em.expert_id
WHERE epa.timestamp > NOW() - INTERVAL '30 days'
GROUP BY epa.expert_id, em.expert_name, epa.category, epa.metric_type;

-- Create index for performance trends view
CREATE INDEX IF NOT EXISTS idx_mv_performance_trends_expert_category 
ON mv_expert_performance_trends(expert_id, category, metric_type);

-- =====================================================
-- REFRESH FUNCTIONS FOR MATERIALIZED VIEWS
-- =====================================================

-- Function to refresh expert leaderboard
CREATE OR REPLACE FUNCTION refresh_expert_leaderboard()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_expert_leaderboard;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh performance trends
CREATE OR REPLACE FUNCTION refresh_performance_trends()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_expert_performance_trends;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_mv()
RETURNS void AS $$
BEGIN
    PERFORM refresh_expert_leaderboard();
    PERFORM refresh_performance_trends();
    
    -- Log refresh completion
    INSERT INTO system_logs (log_level, message, timestamp)
    VALUES ('INFO', 'All materialized views refreshed successfully', NOW());
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- AUTOMATED MAINTENANCE PROCEDURES
-- =====================================================

-- Function for automated database optimization
CREATE OR REPLACE FUNCTION optimize_database_performance()
RETURNS void AS $$
BEGIN
    -- Update table statistics
    ANALYZE enhanced_expert_models;
    ANALYZE expert_predictions_enhanced;
    ANALYZE ai_council_selections;
    ANALYZE ai_council_voting;
    ANALYZE expert_performance_analytics;
    ANALYZE self_healing_events;
    ANALYZE episodic_memory;
    
    -- Refresh materialized views
    PERFORM refresh_all_mv();
    
    -- Clean up old data (keep last 90 days of performance analytics)
    DELETE FROM expert_performance_analytics 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Clean up old self-healing events (keep last 30 days)
    DELETE FROM self_healing_events 
    WHERE event_timestamp < NOW() - INTERVAL '30 days';
    
    -- Clean up old episodic memories with low importance (keep last 60 days)
    DELETE FROM episodic_memory 
    WHERE created_at < NOW() - INTERVAL '60 days' 
    AND importance_score < 0.3;
    
    -- Log optimization completion
    INSERT INTO system_logs (log_level, message, timestamp)
    VALUES ('INFO', 'Database optimization completed successfully', NOW());
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PERFORMANCE MONITORING VIEWS
-- =====================================================

-- View for monitoring database performance
CREATE OR REPLACE VIEW v_database_performance AS
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND((n_dead_tup::float / NULLIF(n_live_tup, 0) * 100), 2) as dead_row_percentage,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY dead_row_percentage DESC;

-- View for monitoring slow queries
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    min_time,
    stddev_time,
    ROUND((total_time / calls), 2) as avg_time_ms
FROM pg_stat_statements
WHERE mean_time > 1000  -- Queries taking more than 1 second on average
ORDER BY mean_time DESC;

-- View for monitoring index usage
CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    CASE 
        WHEN idx_tup_read = 0 THEN 0
        ELSE ROUND((idx_tup_fetch::float / idx_tup_read * 100), 2)
    END as hit_ratio_percentage
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY hit_ratio_percentage DESC;

-- =====================================================
-- AUTOMATED JOBS (USING pg_cron extension if available)
-- =====================================================

-- Note: These require pg_cron extension which may not be available in all Supabase plans
-- Uncomment if pg_cron is available

-- -- Daily database optimization (runs at 2 AM)
-- SELECT cron.schedule('daily-optimization', '0 2 * * *', 'SELECT optimize_database_performance();');

-- -- Hourly materialized view refresh
-- SELECT cron.schedule('hourly-mv-refresh', '0 * * * *', 'SELECT refresh_all_mv();');

-- -- Weekly comprehensive vacuum
-- SELECT cron.schedule('weekly-vacuum', '0 3 * * 0', 'VACUUM ANALYZE;');

-- =====================================================
-- RELOAD CONFIGURATION
-- =====================================================

-- Reload configuration to apply settings
SELECT pg_reload_conf();

-- =====================================================
-- COMPLETION LOG
-- =====================================================

-- Log that optimization setup is complete
INSERT INTO system_logs (log_level, message, timestamp)
VALUES ('INFO', 'Production database optimization configuration completed', NOW());

-- Display optimization summary
SELECT 
    'Database optimization setup completed' as status,
    NOW() as completion_time,
    (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE schemaname = 'public') as total_indexes_created,
    (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND table_name LIKE 'mv_%') as materialized_views_created;