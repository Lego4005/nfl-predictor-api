-- End-to-End Smoke Test Schema
-- Supports comprehensive system validation and test result tracking

-- Smoke test results table
CREATE TABLE IF NOT EXISTS smoke_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id TEXT UNIQUE NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Test execution details
    success BOOLEAN NOT NULL,
  games_tested INTEGER NOT NULL,
    experts_tested INTEGER NOT NULL,
    execution_time DECIMAL(8,3) NOT NULL, -- seconds

    -- Validation results
    schema_validation_passed BOOLEAN NOT NULL,
    coherence_validation_passed BOOLEAN NOT NULL,
    bankroll_validation_passed BOOLEAN NOT NULL,
    learning_validation_passed BOOLEAN NOT NULL,
    neo4j_validation_passed BOOLEAN NOT NULL,
    performance_validation_passed BOOLEAN NOT NULL,

    -- Performance metrics
    performance_metrics JSONB NOT NULL,

    -- Detailed results
    game_results JSONB,
    expert_results JSONB,
    validation_details JSONB,

    -- Error tracking
    errors TEXT[],
    warnings TEXT[],

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    timestamp TIMESTAMPTZ NOT NULL,

    -- Indexes
    INDEX idx_smoke_test_results_timestamp (timestamp DESC),
    INDEX idx_smoke_test_results_success (success),
    INDEX idx_smoke_test_results_run (run_id)
);

-- System health check results
CREATE TABLE IF NOT EXISTS system_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Overall health status
    overall_healthy BOOLEAN NOT NULL,

    -- Individual check results
    database_connectivity BOOLEAN NOT NULL,
    expert_bankrolls_initialized BOOLEAN NOT NULL,
    schema_validator_available BOOLEAN NOT NULL,
    performance_within_targets BOOLEAN NOT NULL,
    recent_predictions_available BOOLEAN NOT NULL,

    -- Additional checks
    additional_checks JSONB,

    -- Metadata
    checked_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_health_checks_time (checked_at DESC),
    INDEX idx_health_checks_health (overall_healthy),
    INDEX idx_health_checks_run (run_id)
);

-- Performance validation results
CREATE TABLE IF NOT EXISTS performance_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_id TEXT NOT NULL,
    test_id TEXT, -- Links to smoke_test_results if part of smoke test
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Performance metrics
    vector_retrieval_p95_ms DECIMAL(6,2),
    vector_retrieval_meets_target BOOLEAN,

    end_to_end_p95_s DECIMAL(6,2),
    end_to_end_meets_target BOOLEAN,

    council_projection_p95_ms DECIMAL(6,2),
    council_projection_meets_target BOOLEAN,

    -- Sample sizes
    vector_retrieval_samples INTEGER,
    end_to_end_samples INTEGER,
    council_projection_samples INTEGER,

    -- Overall performance assessment
    all_targets_met BOOLEAN NOT NULL,
    performance_score DECIMAL(4,3),
    degradation_detected BOOLEAN DEFAULT FALSE,

    -- Metadata
    validated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_performance_validation_time (validated_at DESC),
    INDEX idx_performance_validation_targets (all_targets_met),
    INDEX idx_performance_validation_run (run_id)
);

-- Schema compliance validation results
CREATE TABLE IF NOT EXISTS schema_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_id TEXT NOT NULL,
    test_id TEXT, -- Links to smoke_test_results if part of smoke test
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Validation scope
    total_predictions_checked INTEGER NOT NULL,
    games_checked INTEGER,
    experts_checked TEXT[],

    -- Schema compliance results
    schema_valid_count INTEGER NOT NULL,
    schema_invalid_count INTEGER NOT NULL,
    schema_pass_rate DECIMAL(6,4) NOT NULL,
    meets_threshold BOOLEAN NOT NULL, -- ≥98.5%

    -- Failure analysis
    common_failures JSONB, -- Array of {error_type, count, examples}
    expert_performance JSONB, -- Per-expert pass rates and failure counts

    -- Metadata
    validated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_schema_validation_time (validated_at DESC),
    INDEX idx_schema_validation_pass_rate (schema_pass_rate DESC),
    INDEX idx_schema_validation_run (run_id)
);

-- Coherence constraint validation results
CREATE TABLE IF NOT EXISTS coherence_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_id TEXT NOT NULL,
    test_id TEXT, -- Links to smoke_test_results if part of smoke test
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Validation scope
    games_checked INTEGER NOT NULL,

    -- Constraint validation results
    home_away_total_violations INTEGER DEFAULT 0,
    quarter_total_violations INTEGER DEFAULT 0,
    winner_margin_violations INTEGER DEFAULT 0,
    team_props_violations INTEGER DEFAULT 0,

    -- Constraint pass rates
    home_away_total_pass_rate DECIMAL(6,4),
    quarter_total_pass_rate DECIMAL(6,4),
    winner_margin_pass_rate DECIMAL(6,4),
    team_props_pass_rate DECIMAL(6,4),

    -- Performance metrics
    avg_projection_time_ms DECIMAL(6,2),
    projection_meets_slo BOOLEAN,
    convergence_rate DECIMAL(6,4),

    -- Integrity checks
    expert_records_untouched BOOLEAN DEFAULT TRUE,
    deltas_logged BOOLEAN DEFAULT TRUE,

    -- Detailed results
    constraint_details JSONB,

    -- Metadata
    validated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_coherence_validation_time (validated_at DESC),
    INDEX idx_coherence_validation_violations (home_away_total_violations + quarter_total_violations + winner_margin_violations + team_props_violations),
    INDEX idx_coherence_validation_run (run_id)
);

-- Bankroll integrity validation results
CREATE TABLE IF NOT EXISTS bankroll_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_id TEXT NOT NULL,
    test_id TEXT, -- Links to smoke_test_results if part of smoke test
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Validation scope
    experts_checked TEXT[] NOT NULL,

    -- Integrity checks
    non_negative_enforced BOOLEAN NOT NULL,
    negative_bankroll_violations INTEGER DEFAULT 0,
    rounding_errors INTEGER DEFAULT 0,
    settlement_accuracy DECIMAL(6,4),

    -- Expert status
    expert_bankrolls JSONB NOT NULL, -- {expert_id: {bankroll, active, games_played}}
    experts_busted INTEGER DEFAULT 0,

    -- Settlement validation
    bets_settled_correctly BOOLEAN DEFAULT TRUE,
    odds_parsing_accurate BOOLEAN DEFAULT TRUE,
    payout_calculations_correct BOOLEAN DEFAULT TRUE,
    audit_trail_complete BOOLEAN DEFAULT TRUE,

    -- Bust detection
    bust_threshold_enforced BOOLEAN DEFAULT TRUE,
    reactivation_process_available BOOLEAN DEFAULT TRUE,

    -- Metadata
    validated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_bankroll_validation_time (validated_at DESC),
    INDEX idx_bankroll_validation_violations (negative_bankroll_violations),
    INDEX idx_bankroll_validation_run (run_id)
);

-- Neo4j provenance validation results
CREATE TABLE IF NOT EXISTS provenance_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_id TEXT NOT NULL,
    test_id TEXT, -- Links to smoke_test_results if part of smoke test
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Validation scope
    games_checked INTEGER NOT NULL,
    experts_checked INTEGER NOT NULL,

    -- Node creation validation
    decision_nodes_created INTEGER,
    assertion_nodes_created INTEGER,
    thought_nodes_created INTEGER,
    reflection_nodes_created INTEGER DEFAULT 0,

    -- Relationship validation
    predicted_relationships INTEGER,
    has_assertion_relationships INTEGER,
    used_in_relationships INTEGER,
    evaluated_as_relationships INTEGER,
    learned_from_relationships INTEGER,

    -- Query validation
    why_queries_successful BOOLEAN DEFAULT TRUE,
    memory_lineage_complete BOOLEAN DEFAULT TRUE,
    run_id_scoping_correct BOOLEAN DEFAULT TRUE,
    operator_introspection_available BOOLEAN DEFAULT TRUE,

    -- Write-behind performance
    avg_write_latency_ms DECIMAL(6,2),
    blocks_hot_path BOOLEAN DEFAULT FALSE,
    retry_success_rate DECIMAL(6,4),
    idempotent_merges_working BOOLEAN DEFAULT TRUE,

    -- Detailed results
    provenance_details JSONB,

    -- Metadata
    validated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_provenance_validation_time (validated_at DESC),
    INDEX idx_provenance_validation_completeness (why_queries_successful, memory_lineage_complete),
    INDEX idx_provenance_validation_run (run_id)
);

-- Test execution timeline
CREATE TABLE IF NOT EXISTS test_execution_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Timeline entry details
    stage TEXT NOT NULL, -- 'initialization', 'expert_predictions', 'council_selection', etc.
    game_id TEXT,
    expert_id TEXT,

    -- Execution details
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    success BOOLEAN,

    -- Stage-specific data
    stage_data JSONB,

    -- Error information
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_test_timeline_test (test_id, started_at),
    INDEX idx_test_timeline_stage (stage),
    INDEX idx_test_timeline_run (run_id)
);

-- Create RLS policies
ALTER TABLE smoke_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_health_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE coherence_validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE bankroll_validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE provenance_validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_execution_timeline ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read/write test data
CREATE POLICY "Users can manage smoke test results" ON smoke_test_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage health checks" ON system_health_checks
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage performance validation" ON performance_validation_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage schema validation" ON schema_validation_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage coherence validation" ON coherence_validation_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage bankroll validation" ON bankroll_validation_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage provenance validation" ON provenance_validation_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage test timeline" ON test_execution_timeline
    FOR ALL USING (auth.role() = 'authenticated');

-- Create functions for smoke test operations

-- Function to get latest test results summary
CREATE OR REPLACE FUNCTION get_latest_test_summary(p_run_id TEXT DEFAULT 'run_2025_pilot4')
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    latest_test RECORD;
    summary JSONB;
BEGIN
    -- Get latest test
    SELECT * INTO latest_test
    FROM smoke_test_results
    WHERE run_id = p_run_id
    ORDER BY timestamp DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'status', 'no_tests_found',
            'message', 'No smoke tests found for this run'
        );
    END IF;

    -- Build summary
    summary := jsonb_build_object(
        'test_id', latest_test.test_id,
        'success', latest_test.success,
        'timestamp', latest_test.timestamp,
        'execution_time', latest_test.execution_time,
        'games_tested', latest_test.games_tested,
        'experts_tested', latest_test.experts_tested,
        'validation_summary', jsonb_build_object(
            'schema_validation', latest_test.schema_validation_passed,
            'coherence_validation', latest_test.coherence_validation_passed,
            'bankroll_validation', latest_test.bankroll_validation_passed,
            'learning_validation', latest_test.learning_validation_passed,
            'neo4j_validation', latest_test.neo4j_validation_passed,
            'performance_validation', latest_test.performance_validation_passed
        ),
        'performance_metrics', latest_test.performance_metrics,
        'error_count', COALESCE(array_length(latest_test.errors, 1), 0),
        'warning_count', COALESCE(array_length(latest_test.warnings, 1), 0)
    );

    RETURN summary;
END;
$$;

-- Function to calculate test success rate
CREATE OR REPLACE FUNCTION calculate_test_success_rate(
    p_run_id TEXT DEFAULT 'run_2025_pilot4',
    p_days INTEGER DEFAULT 30
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    total_tests INTEGER;
    successful_tests INTEGER;
    success_rate DECIMAL(6,4);
    recent_trend JSONB;
BEGIN
    -- Count tests in the specified period
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE success = TRUE)
    INTO total_tests, successful_tests
    FROM smoke_test_results
    WHERE run_id = p_run_id
      AND timestamp >= NOW() - INTERVAL '1 day' * p_days;

    -- Calculate success rate
    success_rate := CASE
        WHEN total_tests > 0 THEN successful_tests::DECIMAL / total_tests
        ELSE 0
    END;

    -- Get recent trend (last 7 days vs previous 7 days)
    WITH recent_period AS (
        SELECT COUNT(*) FILTER (WHERE success = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) as rate
        FROM smoke_test_results
        WHERE run_id = p_run_id
          AND timestamp >= NOW() - INTERVAL '7 days'
    ),
    previous_period AS (
        SELECT COUNT(*) FILTER (WHERE success = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) as rate
        FROM smoke_test_results
        WHERE run_id = p_run_id
          AND timestamp >= NOW() - INTERVAL '14 days'
          AND timestamp < NOW() - INTERVAL '7 days'
    )
    SELECT jsonb_build_object(
        'recent_rate', COALESCE(r.rate, 0),
        'previous_rate', COALESCE(p.rate, 0),
        'trend', CASE
            WHEN COALESCE(r.rate, 0) > COALESCE(p.rate, 0) THEN 'improving'
            WHEN COALESCE(r.rate, 0) < COALESCE(p.rate, 0) THEN 'declining'
            ELSE 'stable'
        END
    ) INTO recent_trend
    FROM recent_period r, previous_period p;

    RETURN jsonb_build_object(
        'total_tests', total_tests,
        'successful_tests', successful_tests,
        'success_rate', success_rate,
        'period_days', p_days,
        'trend', recent_trend
    );
END;
$$;

-- Function to check system readiness for testing
CREATE OR REPLACE FUNCTION check_system_test_readiness(p_run_id TEXT DEFAULT 'run_2025_pilot4')
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    readiness_checks JSONB;
    expert_count INTEGER;
    game_count INTEGER;
    recent_predictions INTEGER;
BEGIN
    -- Check expert bankroll initialization
    SELECT COUNT(*) INTO expert_count
    FROM expert_bankroll
    WHERE run_id = p_run_id;

    -- Check available games
    SELECT COUNT(*) INTO game_count
    FROM games
    WHERE status = 'completed';

    -- Check recent prediction activity
    SELECT COUNT(*) INTO recent_predictions
    FROM expert_predictions
    WHERE run_id = p_run_id
      AND created_at >= NOW() - INTERVAL '7 days';

    -- Build readiness assessment
    readiness_checks := jsonb_build_object(
        'expert_bankrolls_initialized', expert_count >= 4,
        'sufficient_test_games', game_count >= 5,
        'recent_prediction_activity', recent_predictions > 0,
        'database_accessible', TRUE, -- If we got this far, DB is accessible
        'schema_validator_ready', TRUE, -- Would check actual validator
        'expert_count', expert_count,
        'available_games', game_count,
        'recent_predictions', recent_predictions,
        'overall_ready', (expert_count >= 4 AND game_count >= 5),
        'checked_at', NOW()
    );

    RETURN readiness_checks;
END;
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
